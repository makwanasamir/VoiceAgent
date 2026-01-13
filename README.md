# 🎙️ Voice Agent - Azure OpenAI Realtime API (WebRTC)

A real-time voice assistant powered by **Azure OpenAI GPT-Realtime API** with **WebRTC** for ultra-low latency audio streaming and a local **RAG knowledge base**.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- 🎤 **Real-time voice conversation** via WebRTC (< 200ms latency)
- 🧠 **Local knowledge base** (FAISS + SentenceTransformers)
- 🔇 **Barge-in support** - interrupt the AI mid-response
- 🔐 **Ephemeral token auth** - API keys never exposed to browser
- 📊 **Comprehensive test suite** (32 tests)

## 🏗️ Architecture

```
┌─────────────────┐     WebRTC      ┌──────────────────────┐
│   Browser       │◄───────────────►│  Azure OpenAI        │
│   (Audio)       │     Audio       │  GPT-Realtime        │
└────────┬────────┘                 └──────────────────────┘
         │
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI Server │
│  ┌───────────┐  │
│  │ Token API │  │◄── /session (ephemeral tokens)
│  ├───────────┤  │
│  │ KB Search │  │◄── /search_kb (RAG queries)
│  └───────────┘  │
└─────────────────┘
```

## 📋 Prerequisites

- Python 3.13+
- Azure subscription (Pay-As-You-Go)
- Azure OpenAI resource in **Sweden Central** or **East US 2**

---

# 🚀 Azure OpenAI Realtime API Setup Guide

> **⚠️ Critical:** The Realtime API is **not** available in standard regions (like East US or West Europe). Follow this guide exactly to avoid `401 Unauthorized` errors.

📖 **Official Documentation:** [Microsoft - Use GPT Realtime API via WebRTC](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio-webrtc?view=foundry-classic)

## Step 1: Create the Azure OpenAI Resource

1. Log in to the [Azure Portal](https://portal.azure.com)
2. Search for **Azure OpenAI** → Click **Create**
3. Fill in the details:

| Field | Value |
|-------|-------|
| **Subscription** | Pay-As-You-Go (Free Trial often fails) |
| **Resource Group** | Select existing or create new |
| **Region** | 🇸🇪 **Sweden Central** (recommended) |
| **Name** | e.g., `openai-realtime-sweden` |
| **Pricing Tier** | Standard S0 |

4. Click **Review + create** → **Create**

## Step 2: Deploy the Model

1. Go to the resource overview → Click **"Go to Azure AI Foundry"**
2. In the left sidebar, click **Deployments**
3. Click **+ Deploy model** → **Deploy base model**
4. Search for and select: **`gpt-realtime`** (or `gpt-realtime-mini`)
5. Configuration:

| Setting | Value | Reason |
|---------|-------|--------|
| **Model Version** | `2025-08-28` | Latest Realtime support |
| **Deployment Type** | **Global Standard** | Required for Realtime API |
| **Deployment Name** | `gpt-realtime` | Used in code |

6. Click **Deploy**

## Step 3: Get Credentials

1. Return to the **Azure Portal** (not Foundry)
2. Go to your resource → **Resource Management** → **Keys and Endpoint**
3. Copy **KEY 1** and the **Endpoint** URL

## Step 4: Configure Environment

Create a `.env` file in the project root:

```ini
# Azure OpenAI Configuration

# Endpoint of your Sweden Central resource
AZURE_OPENAI_ENDPOINT= "https://openai-realtime-sweden.openai.azure.com/"

# API Key from "Keys and Endpoint"
AZURE_OPENAI_API_KEY= "your_key_here_xxxxxxxxxxxxxxxxx"

# Deployment name from Step 2
AZURE_OPENAI_DEPLOYMENT_NAME= "gpt-realtime"
```

---

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/voice-agent.git
cd voice-agent

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Step 4 above)
```

## ▶️ Running the Application

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start the server
python main.py
```

Open your browser to: **http://localhost:8000**

Click **Start Conversation** and start speaking!

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run security scan (SAST)
bandit -r main.py knowledge_base.py
```

### Test Results

| Category | Tests | Status |
|----------|-------|--------|
| Unit Tests | 8 | ✅ Pass |
| Integration Tests | 8 | ✅ Pass |
| Performance Tests | 4 | ✅ Pass |
| Security/SAST | 8 | ✅ Pass |
| Stress Tests | 4 | ✅ Pass |

---

## 📁 Project Structure

```
voice-agent/
├── main.py              # FastAPI server (token dispenser + KB API)
├── knowledge_base.py    # KB module (scans knowledge/ folder)
├── knowledge/           # Drop your .txt/.md files here
│   ├── README.md
│   └── (your-files.txt)
├── index.html           # WebRTC frontend
├── .env                 # Azure credentials (not committed)
├── .env.example         # Template for credentials
├── .gitignore
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
└── tests/               # Coprehensive test suite (pytest)
    ├── conftest.py          # Test configuration & fixtures
    ├── test_unit.py         # Unit tests
    ├── test_integration.py  # API integration tests
    ├── test_performance.py  # Latency & throughput tests
    ├── test_security.py     # SAST & security checks
    ├── test_stress.py       # Load & stress tests
    └── results/             # Test reports
```

---

## 🔧 Configuration

### Voice Options

Change the voice in `main.py`:

```python
"audio": {
    "output": {
        "voice": "shimmer"  # Options: alloy, echo, fable, onyx, nova, shimmer
    }
}
```

### Custom Instructions

Edit the `instructions` field in the session config:

```python
"instructions": "You are a helpful assistant..."
```

---

## 🐛 Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Wrong region or API key | Verify Sweden Central + correct key |
| `404 Resource not found` | Wrong deployment name | Check `AZURE_OPENAI_DEPLOYMENT_NAME` |
| `400 BadRequest` | Wrong API version | Use documented endpoint paths |
| No audio response | Browser permissions | Allow microphone access |

---

## 📚 References

- [Microsoft - GPT Realtime API via WebRTC](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio-webrtc?view=foundry-classic)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [OpenAI Realtime API Guide](https://platform.openai.com/docs/guides/realtime)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
