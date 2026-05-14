#!/usr/bin/env bash
# KukiClaw One-Liner Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/what-if-labs/KukiClaw/main/install.sh | bash
# Auto-installs all required packages on fresh Linux server

echo "🤖 KūkiClaw Installer"
echo "===================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
else
    echo "❌ Cannot detect operating system"
    exit 1
fi

echo "🖥️  Detected: $OS $OS_VERSION"

# Install Node.js 22.x if not present or wrong version
install_nodejs() {
    echo "📦 Installing Node.js 22.x..."
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        if ! command -v curl &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y curl
        fi
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - || {
            echo "⚠️  NodeSource setup failed, trying alternative..."
            sudo apt-get update && sudo apt-get install -y nodejs npm
        }
        sudo apt-get update && sudo apt-get install -y nodejs
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
        sudo yum install -y nodejs
    elif [ "$OS" = "amzn" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
        sudo yum install -y nodejs
    else
        echo "❌ Unsupported OS: $OS. Please install Node.js 22+ manually from https://nodejs.org/"
        exit 1
    fi
}

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
    if [ "$NODE_MAJOR" -lt 22 ]; then
        echo "⚠️  Node.js $NODE_VERSION found, but 22+ required"
        install_nodejs
    else
        echo "✅ Node.js $NODE_VERSION already installed"
    fi
else
    install_nodejs
fi

# Verify Node.js installation
if ! command -v node &> /dev/null; then
    echo "❌ Node.js installation failed. Please install manually:"
    echo "   curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -"
    echo "   sudo apt-get install -y nodejs"
    exit 1
fi

# Configure npm for global installs without sudo
NPM_PREFIX="$HOME/.npm-global"
mkdir -p "$NPM_PREFIX"
npm config set prefix "$NPM_PREFIX" 2>/dev/null || true

# Add to PATH for current session
export PATH="$NPM_PREFIX/bin:$PATH"

# Add to PATH permanently
if [ -f ~/.bashrc ] && ! grep -q 'export PATH="$HOME/.npm-global/bin:$PATH"' ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
fi

# Install Python 3 if not present
if ! command -v python3 &> /dev/null; then
    echo "📦 Installing Python 3..."
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        sudo yum install -y python3 python3-pip
    elif [ "$OS" = "amzn" ]; then
        sudo yum install -y python3 python3-pip
    fi
fi

# Install Git if not present
if ! command -v git &> /dev/null; then
    echo "📦 Installing Git..."
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        sudo apt-get update && sudo apt-get install -y git
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        sudo yum install -y git
    elif [ "$OS" = "amzn" ]; then
        sudo yum install -y git
    fi
fi

# Verify installations
echo ""
echo "✅ Checking installations..."
echo "   Node.js: $(node --version)"
echo "   npm: $(npm --version)"
echo "   Python: $(python3 --version)"
echo "   Git: $(git --version)"

# Install OpenClaw
echo ""
echo "📦 Installing OpenClaw v2026.4.22..."
cd ~
npm install -g openclaw@2026.4.22

# Verify OpenClaw is accessible
if ! command -v openclaw &> /dev/null; then
    echo "⚠️  OpenClaw not in PATH, adding to current session..."
    export PATH="$HOME/.npm-global/bin:$PATH"
fi

# Verify installation
if command -v openclaw &> /dev/null; then
    echo "✅ OpenClaw installed: $(openclaw --version 2>/dev/null || echo 'v2026.4.22')"
else
    echo "❌ OpenClaw installation failed"
    echo "   Try: source ~/.bashrc && openclaw --version"
    exit 1
fi

# Download and run setup wizard
echo ""
echo "📦 Downloading setup wizard..."
cd /tmp
rm -rf kukiclaw-setup
mkdir -p kukiclaw-setup/setup
curl -fsSL https://raw.githubusercontent.com/what-if-labs/KukiClaw/main/setup/setup_wizard.py > kukiclaw-setup/setup/setup_wizard.py

# Run setup wizard (reads from /dev/tty for terminal input)
echo ""
echo "🤖 Starting setup wizard..."
cd /tmp/kukiclaw-setup/setup
python3 setup_wizard.py < /dev/tty

# Check if setup was successful
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Setup wizard failed. Please check the errors above."
    exit 1
fi

echo ""
echo "✅ KūkiClaw installed successfully!"
echo "   Your OpenClaw config is at: ~/.openclaw/openclaw.json"
echo ""

# Ask if user wants to start OpenClaw now
echo "🚀 Would you like to start KūkiClaw now?"
read -p "   Start OpenClaw? (y/n) [y]: " start_now
start_now=${start_now:-y}

if [ "$start_now" = "y" ] || [ "$start_now" = "Y" ]; then
    echo ""
    echo "🚀 Starting KūkiClaw Gateway..."
    echo "   (Press Ctrl+C to stop)"
    echo ""
    cd ~
    # Source shell profile to get API keys
    if [ -f ~/.bashrc ]; then
        source ~/.bashrc 2>/dev/null || true
    fi
    if [ -f ~/.zshrc ]; then
        source ~/.zshrc 2>/dev/null || true
    fi
    if command -v openclaw &> /dev/null; then
        openclaw gateway start
    else
        ~/.npm-global/bin/openclaw gateway start
    fi
else
    echo ""
    echo "🚀 To start your IAQ companion agent later:"
    echo "   1. cd ~  (go to home directory)"
    echo "   2. source ~/.bashrc  (or open a NEW terminal)"
    echo "   3. openclaw gateway start"
    echo ""
    echo "   Or use full path:"
    echo "   cd ~ && ~/.npm-global/bin/openclaw gateway start"
fi

echo ""
echo "⚠️  IMPORTANT: Always run 'openclaw' from your home directory (~)"
echo "   Running from /tmp or deleted directories causes 'uv_cwd' errors"
echo ""
echo "📝 First time with OpenClaw? Run:"
echo "   cd ~ && ~/.npm-global/bin/openclaw configure"
