#!/bin/bash
# Quick setup script for Ollama + API integration

echo "🚀 MTL Project - Ollama Integration Setup"
echo "=========================================="

# Check Python
echo "✓ Checking Python..."
python --version

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check Ollama
echo ""
echo "🤖 Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"
    ollama --version
else
    echo "❌ Ollama not found. Please install from https://ollama.ai"
    echo "Then run: ollama pull llama2"
    exit 1
fi

# Check Ollama models
echo ""
echo "📚 Available Ollama models:"
ollama list

# Create/check .env file
echo ""
echo "⚙️  Checking .env configuration..."
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
AWS_ACCESS_KEY=your_key_here
AWS_SECRET_KEY=your_secret_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_ENABLED=true
EOF
    echo "✓ .env created (update with your AWS credentials)"
else
    echo "✓ .env already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Start Ollama: ollama serve"
echo "2. In new terminal, start API: uvicorn app:app --reload"
echo "3. Test: curl http://localhost:8000/ollama/status"
echo ""
