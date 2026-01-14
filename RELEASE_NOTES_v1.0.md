# IP Scanner Project v1.0.0 Release Notes

**Release Date:** January 14, 2026  
**Version:** 1.0.0

## 🎉 First Stable Release

This is the first stable release of the Network IP Scanner with Enhanced TUI. This release includes a fully functional network discovery tool with a modern text-based user interface.

## ✨ Key Features

### User Interface
- **Modern TUI**: Beautiful Textual-based interface with real-time updates
- **Separate Network Views**: Side-by-side tables for different subnets
- **Interactive Controls**: Start, Pause, Resume, Stop scan operations
- **Copy to Clipboard**: One-click copy of IPs, MACs, and port lists
- **External Ping**: Launch ping commands in external terminal
- **Real-time Logging**: Live scan log with color-coded messages
- **Keyboard Shortcuts**: Full keyboard navigation support

### Network Discovery
- **Multi-Subnet Scanning**: Scan multiple IP ranges simultaneously
- **Live Host Detection**: Fast discovery using ARP, ICMP, and TCP/UDP probes
- **MAC Address Detection**: Automatic MAC address resolution
- **Vendor Identification**: OUI lookup for device manufacturers
- **Port Scanning**: Scans top 10 most common ports
- **Hostname Resolution**: DNS and hosts file lookup

### Performance & Configuration
- **Configurable Threading**: Adjustable parallelism (default: 50 threads)
- **Custom Timeouts**: Per-host timeout configuration (default: 1000ms)
- **Debug Mode**: Verbose logging for troubleshooting
- **Editable IP Ranges**: Configure up to 4 custom network ranges
- **Auto-detection**: Automatic network interface detection

## 📦 Installation

### Quick Install
```bash
# Clone the repository
git clone https://github.com/kizashiX38/ip_scanner_project.git
cd ip_scanner_project

# Run installation script
sudo bash install.sh

# Launch the scanner
sudo bash scripts/run_tui.sh
```

### Manual Install
See [README.md](README.md) for detailed installation instructions.

## 🚀 Usage

### TUI Mode (Recommended)
```bash
sudo bash scripts/run_tui.sh
```

### CLI Mode
```bash
sudo bash scripts/scan_subnets_enhanced.sh [threads] [timeout] [range1] [range2] ... [--debug]
```

## 📋 Requirements

- Linux (tested on Ubuntu/Debian)
- Root/sudo privileges
- Python 3.8+
- System tools: arp-scan, fping, nmap

## 🔧 What's Included

- `scripts/tui_scanner.py` - Main TUI application
- `scripts/scan_subnets_enhanced.sh` - Enhanced scanning engine
- `scripts/scan_subnets.sh` - Basic scanning script
- `scripts/run_tui.sh` - TUI launcher
- `install.sh` - Installation script
- Comprehensive documentation

## 🐛 Known Issues

- Clipboard functionality requires xclip, xsel, or wl-clipboard
- Some terminals may not display colors correctly
- Scanning very large networks (>1000 hosts) may be slow

## 🙏 Acknowledgments

- Inspired by [Angry IP Scanner](https://angryip.org/)
- Built with [Textual](https://textual.textualize.io/)
- Uses [Rich](https://rich.readthedocs.io/) for terminal formatting

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Repository**: https://github.com/kizashiX38/ip_scanner_project
- **Issues**: https://github.com/kizashiX38/ip_scanner_project/issues
- **Documentation**: See README.md

---

**Thank you for using IP Scanner Project!**
