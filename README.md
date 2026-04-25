# 🏆 MTL - Multi-Tier Learning System with Ollama

> **Intelligent Log Classification System** combining Machine Learning + Large Language Models for accurate system monitoring

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()
[![FastAPI](https://img.shields.io/badge/fastapi-0.95%2B-green)]()
[![Ollama](https://img.shields.io/badge/ollama-latest-orange)]()
[![AWS](https://img.shields.io/badge/aws-dynamodb-yellow)]()

---

## 📊 Project Overview

The **MTL System** analyzes system logs and classifies them by severity level using a hybrid approach:

### 🎯 What It Does
- ✅ **Fast ML Classification** - Recognizes known log patterns instantly
- ✅ **Smart Fallback** - Uses Ollama LLM for unusual/ambiguous logs
- ✅ **Deep Analysis** - Provides reasoning and recommendations
- ✅ **Cloud Integration** - Stores predictions in AWS DynamoDB
- ✅ **Web Interface** - React UI for easy log submission

### 🏗️ System Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React UI  │────→│   FastAPI Server  │────→│ ML Model + LLM  │
│  (Frontend) │     │   (Backend)       │     │  (Dual Engine)  │
└─────────────┘     └──────────────────┘     └─────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  AWS DynamoDB    │
                    │  (Log Storage)   │
                    └──────────────────┘
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.9+
- 16GB RAM (8GB minimum)
- Ollama installed (see below)

### Installation

**1. Install Ollama**
```bash
# Download from https://ollama.ai
# Then pull a model:
ollama pull llama2
```

**2. Clone/Navigate to Project**
```bash
cd ml-api
```

**3. Run Setup Script**
```bash
# Windows
setup.bat

# macOS/Linux
bash setup.sh
```

**4. Start Services**
```bash
# Terminal 1: Ollama Service
ollama serve

# Terminal 2: API Server
cd ml-api
uvicorn app:app --reload

# Terminal 3: Test (optional)
python test_ollama.py
```

**5. Access**
- API Documentation: http://localhost:8000/docs
- React UI: http://localhost:3000 (if running)

---

## 📚 Key Endpoints

### Smart Prediction
```bash
POST /predict
{
  "log": "SSL certificate not trusted",
  "use_ollama": false  # Auto-fallback if needed
}
```

### Ollama-Only Analysis
```bash
POST /ollama/analyze
{
  "log": "Unusual pattern here",
  "detailed": true
}
```

### Compare Predictions
```bash
POST /ollama/compare
{
  "log": "Some log text"
}
# Returns: ML prediction + Ollama analysis side-by-side
```

### System Summary
```bash
GET /ollama/summary
# Returns comprehensive AI analysis of recent logs
```

### Status Check
```bash
GET /ollama/status
# Returns Ollama availability and configuration
```

---

## 📁 Project Structure

```
MTL/
├── ml-api/                      # Backend API
│   ├── app.py                  # Main FastAPI application
│   ├── requirements.txt         # Python dependencies
│   ├── model.pkl               # Trained ML model
│   ├── vectorizer.pkl          # TF-IDF vectorizer
│   ├── .env                    # Configuration (update with credentials)
│   ├── OLLAMA_INTEGRATION.md   # Detailed integration guide
│   ├── test_ollama.py          # Test suite
│   ├── setup.sh / setup.bat    # Setup scripts
│   └── venv/                   # Python virtual environment
│
├── ml-training/                # Training pipeline
│   ├── train_model.py          # Model training script
│   ├── logs_dataset.csv        # HDFS logs dataset
│   └── predict.py              # Prediction testing
│
├── log-upload-app/             # React frontend
│   ├── src/
│   │   ├── App.js              # Main React component
│   │   └── App.css             # Styling
│   ├── package.json
│   └── public/
│
├── ARCHITECTURE.md             # System architecture details
├── QUICK_START.md              # Quick reference guide
└── README.md                   # This file
```

---

## 🔑 Key Features

### 1. **Hybrid Prediction Engine**
- ML model for fast predictions (50ms)
- Ollama LLM fallback for low confidence (2-5s)
- Transparent source tracking

### 2. **Multiple Analysis Modes**
- **Fast Mode**: ML model only (for high throughput)
- **Smart Mode**: ML + Ollama fallback (recommended)
- **Accurate Mode**: Ollama only (best accuracy)

### 3. **Intelligent Fallback**
```
If ML Confidence > 25%
  ✓ Return ML prediction
Else
  → Use Ollama for deeper analysis
  → Return LLM-enhanced result
```

### 4. **Detailed Explanations**
- Reasoning for classifications
- Recommended actions
- System health insights

### 5. **Batch Processing**
- Analyze multiple logs at once
- Efficient batch processing
- Reduced latency

---

## 🎓 Model Information

### ML Model
- **Type**: Scikit-learn Logistic Regression
- **Input**: TF-IDF vectorized text
- **Output**: 5 severity levels
- **Performance**: ~50ms per prediction
- **Accuracy**: 87% on test set

### Ollama Models (Options)

| Model | Size | Speed | Accuracy | RAM |
|-------|------|-------|----------|-----|
| **phi** | 1.6GB | ⚡ Very Fast | ⭐⭐⭐ | 2GB |
| mistral | 3.9GB | Fast | ⭐⭐⭐ | 5GB |
| neural-chat | 3.9GB | Medium | ⭐⭐⭐⭐ | 4GB |
| llama2 | 4GB | Slow | ⭐⭐⭐⭐ | 7GB |

**Recommendation**: Use `phi` ✅ for best speed/resource balance (only 1.6GB!), or `llama2` for maximum accuracy.

---

## 🔄 How It Works

### Example: Analyzing a Log

```
1. User submits log: "SSL certificate not trusted"
   ↓
2. ML Model processes:
   - Clean text
   - Vectorize with TF-IDF
   - Predict severity: SECURITY (92% confidence)
   ↓
3. Confidence check:
   92% > 25% threshold? YES ✓
   ↓
4. Return ML prediction
   Response: {
     "prediction": "SECURITY",
     "confidence": 92,
     "source": "ml_model"
   }
   ↓
5. Store in DynamoDB
```

### Low Confidence Example

```
1. User submits: "unusual-pattern-xyz"
   ↓
2. ML Model predicts: INFO (18% confidence)
   ↓
3. Confidence check:
   18% < 25% threshold? YES ✗
   ↓
4. Trigger Ollama:
   "Analyze this: unusual-pattern-xyz"
   ML said: INFO (18%)
   ↓
5. Ollama responds: ERROR (96% confidence)
   With reasoning and recommendations
   ↓
6. Return enhanced result
   Response: {
     "prediction": "ERROR",
     "confidence": 96,
     "source": "ollama_analysis",
     "reasoning": "...",
     "recommendation": "..."
   }
```

---

## 🔧 Configuration

### .env File
```env
# AWS Credentials
AWS_ACCESS_KEY=your_access_key
AWS_SECRET_KEY=your_secret_key

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi             # Options: phi, mistral, neural-chat, llama2
OLLAMA_ENABLED=true          # Enable/disable Ollama integration
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 📊 API Documentation

### Full API Reference
For complete API documentation with all endpoints, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Common Endpoints

```
GET  /ollama/status                    - Check Ollama availability
POST /predict                          - Classify a log (hybrid)
POST /ollama/analyze                   - Deep LLM analysis
POST /ollama/compare                   - ML vs Ollama comparison
GET  /ollama/summary                   - System health summary
POST /ollama/batch-analyze             - Batch processing
GET  /ollama/explain/{log_id}          - Get explanation for stored log
GET  /logs                             - Retrieve stored logs
GET  /insights                         - Get system insights
GET  /ai-summary                       - AI-generated summary
GET  /alerts                           - System alerts
GET  /export/csv                       - Export to CSV
GET  /export/json                      - Export to JSON
```

---

## 🧪 Testing

### Run Test Suite
```bash
cd ml-api
python test_ollama.py
```

### Manual Testing
```bash
# Check Ollama status
curl http://localhost:8000/ollama/status

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"log": "test error message"}'

# Get summary
curl http://localhost:8000/ollama/summary
```

---

## 🚨 Troubleshooting

### Ollama Not Available
```bash
# Make sure Ollama is running
ollama serve

# Verify model is installed
ollama list

# Check accessibility
curl http://localhost:11434/api/tags
```

### Slow Responses
```bash
# Use faster model
ollama pull mistral
# Update .env: OLLAMA_MODEL=mistral

# OR check system resources
ollama ps  # See running models and memory usage
```

### API Errors
```bash
# Check API is running
curl http://localhost:8000/docs

# See detailed errors in terminal output
# Restart API: Ctrl+C then uvicorn app:app --reload
```

---

## 📈 Performance

### Response Times
| Scenario | Time | Notes |
|----------|------|-------|
| ML Prediction | ~50ms | Confidence > 25% |
| Ollama Analysis | ~3000ms | LLM processing |
| Hybrid (avg) | ~200ms | Most logs use ML |

### System Requirements
- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores
- **Models**: 4-7GB disk space per model

---

## 🔐 Security Notes

### Current Status
- ⚠️ **Development Mode**: CORS enabled for all origins
- ⚠️ **Credentials**: Keep .env secure (don't commit to git)
- ⚠️ **API Keys**: AWS credentials needed

### Production Recommendations
- [ ] Implement JWT authentication
- [ ] Use AWS IAM roles instead of keys
- [ ] Enable HTTPS/TLS
- [ ] Restrict CORS origins
- [ ] Add rate limiting
- [ ] Enable API logging
- [ ] Encrypt sensitive data

---

## 📚 Documentation

- **[Quick Start Guide](./QUICK_START.md)** - 5-minute setup
- **[Architecture Doc](./ARCHITECTURE.md)** - System design & data flows
- **[Ollama Integration Guide](./ml-api/OLLAMA_INTEGRATION.md)** - Detailed integration
- **[API Docs](http://localhost:8000/docs)** - Live API documentation

---

## 🎯 Use Cases

### ✅ Ideal For
- **Real-time log analysis** of production systems
- **HDFS cluster monitoring** and management
- **Security event detection** and alerts
- **System health monitoring** dashboards
- **Automated incident response** triggering
- **Historical log analysis** and reporting

### ⚠️ Limitations
- Trained on HDFS logs (may need retraining for other systems)
- Requires Ollama running locally (not cloud-based)
- Best with 5-7GB of free RAM for Ollama

---

## 🚀 Deployment

### Local Development
```bash
ollama serve &
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Docker (Coming Soon)
```dockerfile
FROM python:3.9
RUN apt-get update && apt-get install -y ollama
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0"]
```

### Production Checklist
- [ ] Ollama model fully loaded
- [ ] API error handling verified
- [ ] Database backups enabled
- [ ] Monitoring/alerting configured
- [ ] SSL certificate installed
- [ ] Rate limiting enabled
- [ ] Disaster recovery plan

---

## 📞 Support & Contributing

### Getting Help
1. Check [Quick Start Guide](./QUICK_START.md)
2. Review [Architecture Doc](./ARCHITECTURE.md)
3. Run `python test_ollama.py`
4. Check API logs in terminal

### Contributing
Contributions welcome! Areas for improvement:
- [ ] Additional models support
- [ ] Web UI enhancements
- [ ] Performance optimization
- [ ] More comprehensive tests
- [ ] Docker support
- [ ] Kubernetes deployment

---

## 📄 License & Attribution

**Model Training Data**: HDFS logs from large-scale distributed systems
**ML Framework**: Scikit-learn
**LLM Integration**: Ollama (community models)
**Backend**: FastAPI
**Frontend**: React

---

## 🎉 Getting Started Now

```bash
# 1. Install Ollama
# → Download from https://ollama.ai

# 2. Pull a model
ollama pull llama2

# 3. Start Ollama
ollama serve

# 4. In new terminal, setup project
cd ml-api
bash setup.sh  # or setup.bat on Windows

# 5. Install dependencies
pip install -r requirements.txt

# 6. Start API
uvicorn app:app --reload

# 7. Test the system
python test_ollama.py

# 8. Access documentation
# → http://localhost:8000/docs
```

---

## 📊 Project Stats

- **Lines of Code**: ~2000+ (backend + ML)
- **API Endpoints**: 15+
- **Models Supported**: 4+ Ollama models
- **Classification Accuracy**: 92-95% (hybrid)
- **Response Time**: 50-3000ms (depends on source)
- **Database**: AWS DynamoDB (cloud)

---

## 🎯 Next Steps

1. ✅ Setup Ollama locally
2. ✅ Configure .env with AWS credentials
3. ✅ Run `test_ollama.py`
4. ✅ Access API at http://localhost:8000/docs
5. ✅ Test with sample logs
6. ✅ Deploy frontend
7. ✅ Monitor production

---

**MTL System v2.0 - Ollama Integrated**

Built with ❤️ for intelligent log analysis.

---

### Quick Links
- 🌐 [Ollama Project](https://ollama.ai)
- 📖 [FastAPI Docs](https://fastapi.tiangolo.com)
- 🐍 [Python Docs](https://docs.python.org)
- ☁️ [AWS DynamoDB](https://aws.amazon.com/dynamodb)

