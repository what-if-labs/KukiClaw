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

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js 20.x..."
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        # Install curl if needed
        if ! command -v curl &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y curl
        fi
        # Download and run NodeSource setup script
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - || {
            echo "❌ Failed to add NodeSource repository"
            echo "   Trying alternative installation method..."
            sudo apt-get update && sudo apt-get install -y nodejs npm
        }
        sudo apt-get update && sudo apt-get install -y nodejs
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        sudo yum install -y nodejs
    elif [ "$OS" = "amzn" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        sudo yum install -y nodejs
    else
        echo "❌ Unsupported OS: $OS. Please install Node.js manually from https://nodejs.org/"
        exit 1
    fi
fi

# Verify Node.js installation
if ! command -v node &> /dev/null; then
    echo "❌ Node.js installation failed. Please install manually:"
    echo "   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -"
    echo "   sudo apt-get install -y nodejs"
    exit 1
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

# Clone KukiClaw
echo "📦 Cloning KukiClaw..."
cd /tmp
rm -rf kukiclaw-setup
git clone https://github.com/what-if-labs/KukiClaw.git kukiclaw-setup
cd kukiclaw-setup

# Run setup wizard
echo ""
echo "🤖 Starting setup wizard..."
cd setup
python3 setup_wizard.py

echo ""
echo "✅ KūkiClaw installed successfully!"
echo "   Start with: cd /tmp/kukiclaw-setup && openclaw start"
