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
        # Install curl if needed
        if ! command -v curl &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y curl
        fi
        # Download and run NodeSource setup script for Node.js 22
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
if [ -z "$NPM_CONFIG_PREFIX" ]; then
    NPM_PREFIX="$HOME/.npm-global"
    mkdir -p "$NPM_PREFIX"
    npm config set prefix "$NPM_PREFIX"
    
    # Add to PATH for current session
    export PATH="$NPM_PREFIX/bin:$PATH"
    
    # Add to PATH permanently
    if ! grep -q 'export PATH="$HOME/.npm-global/bin:$PATH"' ~/.bashrc 2>/dev/null; then
        echo "" >> ~/.bashrc
        echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
    fi
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

# Download setup wizard directly
echo "📦 Downloading setup wizard..."
cd /tmp
rm -rf kukiclaw-setup
mkdir -p kukiclaw-setup/setup
curl -fsSL https://raw.githubusercontent.com/what-if-labs/KukiClaw/main/setup/setup_wizard.py > kukiclaw-setup/setup/setup_wizard.py

# Run setup wizard
echo ""
echo "🤖 Starting setup wizard..."
cd kukiclaw-setup/setup
# Redirect stdin from /dev/tty so wizard can accept user input
# (when run via curl | bash, stdin is consumed by the pipe)
python3 setup_wizard.py < /dev/tty

echo ""
echo "✅ KūkiClaw installed successfully!"
echo "   Your OpenClaw config is at: ~/.openclaw/openclaw.json"
echo ""
echo "🚀 To start your IAQ companion agent:"
echo "   1. source ~/.bashrc  (or open a new terminal)"
echo "   2. openclaw start"
echo ""
echo "   Or use full path: ~/.npm-global/bin/openclaw start"
