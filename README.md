# Network IP Scanner - Enhanced TUI Edition

A powerful, feature-rich network discovery tool with a modern Textual-based TUI (Text User Interface) inspired by Angry IP Scanner. Discover live hosts, MAC addresses, vendor information, open ports, and more across your local network.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

## 🚀 Features

### Core Functionality
- **Multi-Subnet Scanning**: Scan multiple IP ranges simultaneously with CIDR notation support
- **Live Host Detection**: Fast discovery using ARP, ICMP (ping), and TCP/UDP probes
- **MAC Address Detection**: Automatic MAC address resolution via ARP tables
- **Vendor Identification**: OUI (Organizationally Unique Identifier) lookup for device manufacturers
- **Port Scanning**: Scans top 10 most common ports (SSH, HTTP, HTTPS, RDP, MySQL, etc.)
- **Hostname Resolution**: DNS and hosts file lookup for friendly names

### User Interface
- **Modern TUI**: Beautiful Textual-based interface with real-time updates
- **Separate Network Views**: Side-by-side tables for different subnets
- **Interactive Controls**: Start, Pause, Resume, Stop scan operations
- **Copy to Clipboard**: One-click copy of IPs, MACs, and port lists
- **External Ping**: Launch ping commands in external terminal
- **Real-time Logging**: Live scan log with color-coded messages
- **Keyboard Shortcuts**: Full keyboard navigation support

### Advanced Features
- **Configurable Threading**: Adjustable parallelism for faster scans
- **Custom Timeouts**: Per-host timeout configuration
- **Debug Mode**: Verbose logging for troubleshooting
- **Editable IP Ranges**: Configure up to 4 custom network ranges
- **Results Persistence**: Automatic saving of scan results

## 📋 Requirements

### System Requirements
- Linux (tested on Ubuntu/Debian)
- Root/sudo privileges (for raw socket operations)
- Python 3.8 or higher

### Required Tools
The scanner uses multiple network tools for comprehensive discovery:

```bash
# Install required tools on Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    arp-scan \
    fping \
    nmap \
    iputils-ping \
    net-tools \
    xclip  # For clipboard support (optional)
```

### Python Dependencies
```bash
pip install textual rich
```

Or use the provided setup:
```bash
python3 -m venv venv
source venv/bin/activate
pip install textual rich
```

## 🛠️ Installation

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/ip_scanner_project.git
cd ip_scanner_project
```

2. **Set up Python environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install textual rich
```

3. **Install system dependencies:**
```bash
sudo apt-get install -y arp-scan fping nmap iputils-ping net-tools xclip
```

4. **Run the scanner:**
```bash
bash scripts/run_tui.sh
```

The script will automatically request sudo privileges if needed.

## 📖 Usage

### TUI Mode (Recommended)

Launch the interactive interface:
```bash
bash scripts/run_tui.sh
```

#### TUI Controls

**Toolbar Buttons:**
- **▶ Start**: Begin scanning configured IP ranges
- **⏸ Pause**: Pause running scan (SIGSTOP)
- **▶ Resume**: Resume paused scan (SIGCONT)
- **⏹ Stop**: Terminate scan immediately

**Keyboard Shortcuts:**
- `s` - Start scan
- `p` - Pause scan
- `r` - Resume scan
- `x` - Stop scan
- `c` - Copy selected IP
- `d` - Toggle debug mode
- `q` - Quit application

**Configuration:**
- **Threads**: Number of parallel scanning threads (default: 50)
- **Timeout**: Per-host timeout in milliseconds (default: 1000)
- **Debug**: Enable verbose logging
- **IP Ranges**: Up to 4 editable CIDR notation ranges (e.g., `192.168.1.0/24`)

**IP Range Examples:**
```
192.168.0.0/24      # Single subnet
10.0.0.0/8          # Large network
172.16.0.0/12       # Private network range
192.168.100.0/24    # Custom subnet
```

**Table Actions:**
- Click any row to select an IP
- Use action buttons to copy IP, MAC, or ports
- Click "Ping" to open external terminal with ping command
- Copy buttons in table rows for quick access

### CLI Mode

Run the scanning engine directly:
```bash
sudo bash scripts/scan_subnets_enhanced.sh [threads] [timeout] [range1] [range2] ... [--debug]
```

**Examples:**
```bash
# Default scan (50 threads, 1000ms timeout, default ranges)
sudo bash scripts/scan_subnets_enhanced.sh

# Custom configuration
sudo bash scripts/scan_subnets_enhanced.sh 100 500 192.168.1.0/24 10.0.0.0/24

# With debug output
sudo bash scripts/scan_subnets_enhanced.sh 50 1000 192.168.0.0/24 --debug
```

## 🔍 Scanning Methods

The scanner uses a multi-layered approach for comprehensive network discovery:

1. **ARP Scan** (Layer 2)
   - Fastest method for local network discovery
   - Provides MAC addresses immediately
   - Requires root privileges

2. **ICMP Ping** (Layer 3)
   - Uses `fping` for parallel ICMP probes
   - Detects hosts that respond to ping
   - Works across subnets

3. **TCP/UDP Probes** (Layer 4)
   - Nmap SYN and UDP scans
   - Discovers hosts even if ICMP is blocked
   - Provides port information

4. **Port Scanning**
   - Scans top 10 ports: 22, 80, 443, 3389, 3306, 8080, 21, 25, 110, 143
   - Quick scan for common services
   - Identifies running services

## 📊 Output Format

### TUI Display
Each discovered host shows:
- **IP Address**: Device IP with clickable link
- **Ping**: Response time in milliseconds
- **Hostname**: Resolved DNS name or `-`
- **MAC Address**: Physical address
- **Vendor**: Device manufacturer from MAC OUI
- **Ports**: Comma-separated list of open ports
- **Actions**: Copy and Ping buttons

### CLI Output
The CLI outputs results in the format:
```
LIVE|IP|HOSTNAME|MAC|VENDOR|PORTS|PING
```

Example:
```
LIVE|192.168.1.100|router.local|aa:bb:cc:dd:ee:ff|TP-Link|80,443|2.5ms
```

## 📁 Project Structure

```
ip_scanner_project/
├── scripts/
│   ├── tui_scanner.py          # Main TUI application
│   ├── scan_subnets_enhanced.sh # Enhanced scanning engine
│   ├── scan_subnets.sh         # Basic scanning script
│   └── run_tui.sh              # TUI launcher with sudo
├── results/                    # Scan result files
├── logs/                       # Detailed execution logs
├── ops/                        # Operational documentation
├── venv/                       # Python virtual environment
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## 🔧 Configuration

### Customizing Network Interfaces

Edit `scripts/scan_subnets_enhanced.sh`:
```bash
INTERFACES=("enxa453eed5dd26" "wlp99s0")  # Your network interfaces
```

Find your interfaces:
```bash
ip link show
# or
ifconfig
```

### Adjusting Ports

Modify the `TOP_PORTS` variable:
```bash
TOP_PORTS="22,80,443,3389,3306,8080,21,25,110,143"
```

### Performance Tuning

- **Threads**: Higher values = faster scans but more network load
  - Recommended: 50-100 for home networks
  - Use 100+ for enterprise networks with permission

- **Timeout**: Lower values = faster but may miss slow hosts
  - Recommended: 1000ms for most networks
  - Use 2000-5000ms for slow or congested networks

## 🐛 Troubleshooting

### "Permission Denied" Errors
**Solution**: Run with sudo:
```bash
sudo bash scripts/run_tui.sh
```

### "Command not found" Errors
**Solution**: Install missing tools:
```bash
sudo apt-get install arp-scan fping nmap
```

### No Results Found
**Possible causes:**
1. Wrong IP range - verify your network subnet
2. Firewall blocking scans - check firewall rules
3. Network interface not specified - update INTERFACES in script
4. Hosts blocking ICMP - normal, scanner uses multiple methods

### TUI Not Displaying Correctly
**Solution**: 
- Ensure terminal supports colors (most modern terminals do)
- Try resizing terminal window
- Check Python version: `python3 --version` (needs 3.8+)

### Clipboard Not Working
**Solution**: Install clipboard tool:
```bash
sudo apt-get install xclip  # X11
# or
sudo apt-get install xsel    # Alternative
# or
sudo apt-get install wl-clipboard  # Wayland
```

## 🔒 Security & Privacy

- **Root Privileges**: Required for raw socket operations and ARP scanning
- **Network Scanning**: Only scans networks you have permission to scan
- **No Data Collection**: All scanning is local, no external communication
- **Respectful Scanning**: Uses appropriate timeouts and thread limits

**⚠️ Important**: Only scan networks you own or have explicit permission to scan. Unauthorized network scanning may be illegal in your jurisdiction.

## 📝 Development

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run scanner in debug mode
python3 scripts/tui_scanner.py
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use descriptive commit messages
- Document new features in README

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by [Angry IP Scanner](https://angryip.org/)
- Built with [Textual](https://textual.textualize.io/) for the TUI
- Uses [Rich](https://rich.readthedocs.io/) for terminal formatting

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the `ops/` directory for operational documentation
- Review logs in `logs/` directory for troubleshooting

## 🗺️ Roadmap

- [ ] Export results to CSV/JSON
- [ ] Save/load scan configurations
- [ ] Custom port list configuration
- [ ] Network topology visualization
- [ ] Historical scan comparison
- [ ] Web interface option
- [ ] Docker container support

---

**Made with ❤️ for network administrators and security professionals**
