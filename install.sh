#!/bin/bash
# install.sh - Easy installation script for IP Scanner Project
# Usage: bash install.sh

set -e

echo "=========================================="
echo "  IP Scanner Project - Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script requires sudo privileges for installing system packages."
    echo "   Please run: sudo bash install.sh"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ Cannot detect OS. Please install dependencies manually."
    exit 1
fi

echo "📦 Detected OS: $OS"
echo ""

# Install system dependencies
echo "🔧 Installing system dependencies..."
case $OS in
    ubuntu|debian)
        apt-get update
        apt-get install -y \
            arp-scan \
            fping \
            nmap \
            iputils-ping \
            net-tools \
            python3 \
            python3-venv \
            python3-pip \
            xclip || true  # xclip is optional
        ;;
    fedora|rhel|centos)
        dnf install -y \
            arp-scan \
            fping \
            nmap \
            iputils \
            net-tools \
            python3 \
            python3-pip \
            xclip || true
        ;;
    arch|manjaro)
        pacman -S --noconfirm \
            arp-scan \
            fping \
            nmap \
            iputils \
            net-tools \
            python \
            python-pip \
            xclip || true
        ;;
    *)
        echo "⚠️  Unsupported OS. Please install dependencies manually:"
        echo "   - arp-scan"
        echo "   - fping"
        echo "   - nmap"
        echo "   - python3"
        echo "   - python3-venv"
        ;;
esac

echo ""
echo "✅ System dependencies installed"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate and install Python packages
echo "📚 Installing Python packages..."
source "$PROJECT_DIR/venv/bin/activate"
pip install --upgrade pip
pip install textual rich

echo ""
echo "✅ Python packages installed"
echo ""

# Make scripts executable
echo "🔐 Setting script permissions..."
chmod +x "$PROJECT_DIR/scripts/run_tui.sh"
chmod +x "$PROJECT_DIR/scripts/scan_subnets.sh"
chmod +x "$PROJECT_DIR/scripts/scan_subnets_enhanced.sh"
chmod +x "$PROJECT_DIR/install.sh"

echo "✅ Scripts are now executable"
echo ""

# Create directories
echo "📁 Creating project directories..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/results"
echo "✅ Directories created"
echo ""

echo "=========================================="
echo "  ✅ Installation Complete!"
echo "=========================================="
echo ""
echo "📖 Quick Start:"
echo "   sudo bash $PROJECT_DIR/scripts/run_tui.sh"
echo ""
echo "📚 For more information, see README.md"
echo ""
