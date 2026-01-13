"""
Knowledge Base Module
Automatically loads all documents from the 'knowledge/' folder.
Supports: .txt, .md files
Includes persistence: Saves vector index to 'kb_index/' to speed up restarts.
Automatic updates: Rebuilds index if files have changed since last run.
"""
import os
import glob
import shutil
import json
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# Default folder for knowledge documents
KNOWLEDGE_FOLDER = "knowledge"
# Folder to store the persistent vector index
INDEX_FOLDER = "kb_index"
# File to store metadata about the index state
METADATA_FILE = os.path.join(INDEX_FOLDER, "metadata.json")

# Supported file extensions
SUPPORTED_EXTENSIONS = [".txt", ".md"]


class KnowledgeBase:
    def __init__(self, folder_path=KNOWLEDGE_FOLDER, index_path=INDEX_FOLDER):
        """
        Initialize Knowledge Base.
        
        Args:
            folder_path: Path to folder containing knowledge documents.
            index_path: Path to folder where vector index will be saved.
        """
        self.folder_path = folder_path
        self.index_path = index_path
        self.vector_db = None
        self.loaded_files = []
        self._initialize_kb()

    def _get_latest_modification_time(self):
        """Get the latest modification timestamp of any file in the knowledge folder."""
        latest_mod_time = 0.0
        
        if not os.path.exists(self.folder_path):
             return 0.0

        for ext in SUPPORTED_EXTENSIONS:
            pattern = os.path.join(self.folder_path, f"*{ext}")
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    mod_time = os.path.getmtime(file_path)
                    if mod_time > latest_mod_time:
                        latest_mod_time = mod_time
                except Exception:
                    continue
        
        return latest_mod_time

    def _should_rebuild_index(self):
        """Check if the index needs to be rebuilt based on file timestamps."""
        # If index doesn't exist, we must rebuild
        if not os.path.exists(self.index_path) or not os.path.exists(METADATA_FILE):
            return True, "Index or metadata missing"

        # Get the timestamp stored when we last built the index
        try:
            with open(METADATA_FILE, 'r') as f:
                metadata = json.load(f)
                last_build_time = metadata.get("last_build_time", 0.0)
        except Exception:
            return True, "Error reading metadata"

        # Get the latest timestamp of current files
        latest_file_time = self._get_latest_modification_time()

        # If files are newer than our build, we need to rebuild
        if latest_file_time > last_build_time:
            return True, "Files modified since last build"
        
        return False, "Index is up to date"

    def _get_all_documents(self):
        """Find all supported documents in the knowledge folder."""
        documents = []
        
        # Create folder if it doesn't exist
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
            print(f"Created knowledge folder: {self.folder_path}/")
            print("Add your .txt or .md files to this folder.")
            return documents
        
        # Find all supported files
        for ext in SUPPORTED_EXTENSIONS:
            pattern = os.path.join(self.folder_path, f"*{ext}")
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    loader = TextLoader(file_path, encoding='utf-8')
                    docs = loader.load()
                    documents.extend(docs)
                    self.loaded_files.append(os.path.basename(file_path))
                    print(f"  ✓ Loaded: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"  ✗ Error loading {file_path}: {e}")
        
        return documents

    def _initialize_kb(self):
        """Initialize the vector database: load if current, rebuild if changed."""
        print("Loading embedding model (all-MiniLM-L6-v2 on CPU)...")
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
        except Exception as e:
             print(f"❌ Error loading embedding model: {str(e)}")
             return

        # Check if we need to rebuild
        rebuild_needed, reason = self._should_rebuild_index()
        
        if not rebuild_needed:
            print(f"Found existing Knowledge Base index in '{self.index_path}/'. Checking validity...")
            try:
                self.vector_db = FAISS.load_local(
                    self.index_path, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                print(f"✅ Knowledge Base loaded from disk! ({reason})")
                return
            except Exception as e:
                print(f"⚠️  Could not load existing index: {e}. Rebuilding...")

        print(f"Initializing Knowledge Base from '{self.folder_path}/' folder ({reason})...")

        # Rebuild logic
        documents = self._get_all_documents()
        
        if not documents:
            print("⚠️  No documents found. Add .txt or .md files to the knowledge/ folder.")
            return
        
        # Split documents
        text_splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=150)
        docs = text_splitter.split_documents(documents)
        
        # Create vector store
        self.vector_db = FAISS.from_documents(docs, embeddings)
        
        # Save index AND metadata
        self.save_index()
        print(f"✅ Knowledge Base ready! Loaded {len(self.loaded_files)} file(s). Index updated.")

    def save_index(self):
        """Save the vector index metadata to disk."""
        if self.vector_db:
             self.vector_db.save_local(self.index_path)
             
             # Save metadata
             metadata = {
                 "last_build_time": self._get_latest_modification_time(),
                 "file_count": len(self.loaded_files)
             }
             with open(METADATA_FILE, 'w') as f:
                 json.dump(metadata, f)
                 
             print(f"Index saved to '{self.index_path}/'")

    def search(self, query, k=4):
        """Search the knowledge base for relevant content."""
        if not self.vector_db:
            return "Knowledge base not initialized. Add documents to the 'knowledge/' folder."
        results = self.vector_db.similarity_search(query, k=k)
        return "\n\n".join([res.page_content for res in results])
    
    def list_files(self):
        """Return list of loaded files (only populated on rebuild)."""
        return self.loaded_files
    
    def reload(self):
        """Force rebuild: delete index, reload documents, and save new index."""
        print("Reloading Knowledge Base...")
        if os.path.exists(self.index_path):
            shutil.rmtree(self.index_path) # Delete old index
        
        self.loaded_files = []
        self.vector_db = None
        self._initialize_kb() # Rebuilds since index is gone


if __name__ == "__main__":
    # Test
    kb = KnowledgeBase()
    if kb.vector_db:
        print("\nTest search: 'What is the baggage policy?'")
        print(kb.search("What is the baggage policy?"))