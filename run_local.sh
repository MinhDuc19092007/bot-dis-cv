#!/bin/bash
# Script chạy bot local với .env file

echo "🚀 Starting Discord Bot (Local Mode)"
echo "===================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ File .env không tồn tại!"
    echo "📝 Hãy copy .env.example thành .env và điền thông tin:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Load .env
echo "✅ Loading environment variables from .env"
export $(cat .env | grep -v '^#' | xargs)

# Check if DISCORD_TOKEN is set
if [ -z "$DISCORD_TOKEN" ]; then
    echo "❌ DISCORD_TOKEN chưa được set trong .env!"
    exit 1
fi

echo "✅ DISCORD_TOKEN found"
echo "✅ ADMIN_IDS: $ADMIN_IDS"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python version: $PYTHON_VERSION"

# Check dependencies
echo "📦 Checking dependencies..."
pip3 list | grep -E "discord.py|psutil|requests" > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Dependencies chưa đầy đủ!"
    echo "📦 Installing requirements..."
    pip3 install -r requirements.txt
fi

# Run bot
echo "===================================="
echo "🤖 Starting bot..."
echo "===================================="
python3 discord_bot.py
