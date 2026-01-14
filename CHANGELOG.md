# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-14

### Added
- **Enhanced TUI Scanner**: Modern Textual-based user interface inspired by Angry IP Scanner
- **Multi-Subnet Scanning**: Support for multiple IP ranges with CIDR notation
- **MAC Address Detection**: Automatic MAC address resolution via ARP tables
- **Vendor Identification**: OUI lookup for device manufacturer identification
- **Port Scanning**: Scans top 10 most common ports (SSH, HTTP, HTTPS, RDP, MySQL, etc.)
- **Hostname Resolution**: DNS and hosts file lookup
- **Scan Controls**: Start, Pause, Resume, and Stop functionality
- **Copy to Clipboard**: One-click copy of IPs, MACs, and port lists
- **External Ping**: Launch ping commands in external terminal
- **Real-time Logging**: Live scan log with color-coded messages
- **Keyboard Shortcuts**: Full keyboard navigation support
- **Configurable Threading**: Adjustable parallelism for performance tuning
- **Custom Timeouts**: Per-host timeout configuration
- **Debug Mode**: Verbose logging for troubleshooting
- **Editable IP Ranges**: Configure up to 4 custom network ranges
- **Auto-detection**: Automatic network interface detection
- **Installation Script**: Easy setup script for dependencies

### Technical
- Multi-layered scanning approach (ARP, ICMP, TCP/UDP)
- Process management with proper signal handling (SIGSTOP/SIGCONT)
- Thread-safe UI updates from background scanning threads
- Comprehensive error handling and state management
- Results persistence to files

### Documentation
- Comprehensive README with installation and usage instructions
- Operational documentation in `ops/` directory
- MIT License
- Proper .gitignore configuration

### Fixed
- Start/Pause/Resume/Stop button state management
- Process cleanup and thread management
- Stream reading and parsing
- Button state updates during scan operations

## [Unreleased]

### Planned
- Export results to CSV/JSON
- Save/load scan configurations
- Custom port list configuration
- Network topology visualization
- Historical scan comparison
- Web interface option
- Docker container support
