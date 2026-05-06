#!/usr/bin/env bash
# KukiClaw One-Liner Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/what-if21/kukiclaw/main/install.sh | bash

set -e

echo "🤖 KūkiClaw Installer"
echo "===================="

# Check prerequisites
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Install from https://nodejs.org/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Install from https://python.org/"
    exit 1
fi

# Install OpenClaw
echo "📦 Installing OpenClaw..."
npm install -g openclaw

# Clone KukiClaw
echo "📦 Cloning KukiClaw..."
cd /tmp
git clone https://github.com/what-if21/kukiclaw.git kukiclaw-setup
cd kukiclaw

# Run setup wizard
echo "🤖 Starting setup wizard..."
cd setup
python3 setup_wizard.py

echo ""
echo "✅ KukiClaw installed successfully!"
echo "   Start with: cd /tmp/kukiclaw-setup && openclaw start"
