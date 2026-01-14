# Ops Report: Network Subnet Scan (Thorough)
**Date:** 2026-01-14
**Task:** Scan subnets 192.168.0.0/24 and 192.168.8.0/24 (Improved discovery)

## Summary
Improved the network discovery process to match results from tools like "Angry IP Scanner". Switched from a basic ping scan to a multi-tool approach combining ARP, ICMP, and TCP/UDP discovery probes.

## Technical Details
- **Tools used:** `arp-scan`, `fping`, `nmap`
- **Subnets scanned:** `192.168.0.0/24`, `192.168.8.0/24`
- **Automation script:** `scripts/scan_subnets.sh` (v2 - Consolidated)
- **Scan duration:** ~40 seconds
- **Hosts discovered:** 11 unique hosts

## Discovered Hosts (Consolidated)
| IP Address | Hostname / Info | Discovery Method |
| --- | --- | --- |
| 192.168.0.1 | _gateway | ARP, fping, nmap |
| 192.168.0.198 | - | ARP, nmap |
| 192.168.0.229 | dxm-ROG-Zephyrus-G16-GA605WI | fping, nmap |
| 192.168.8.1 | homerouter.cpe | ARP, fping, nmap |
| 192.168.8.100 | dxm-ROG-Zephyrus-G16-GA605WI-GA605WI | fping, nmap |
| 192.168.8.101 | iPhone | ARP, fping |
| 192.168.8.109 | ADY-LX9 | fping, nmap |
| 192.168.8.114 | OpenWrt | fping |
| 192.168.8.149 | H88H | fping |
| 192.168.8.150 | NX779J | ARP, fping |
| 192.168.8.154 | yeelink-light-color2_miapfef9 | ARP, fping |

## Observations
- Some hosts (e.g., iPhone, ADY-LX9) only respond to specific discovery methods like ARP or persistent `fping` due to power-saving modes.
- Latencies for certain devices were observed as high as 2000ms+ in external tools, requiring higher timeouts (`--host-timeout 20s`) in our automation.
- `arp-scan` proved most reliable for local Layer 2 discovery.

## Files Created/Modified
- `scripts/scan_subnets.sh`: Updated with multi-tool logic.
- `network_scan_results_<timestamp>.txt`: Consolidated unique IP list.
- `logs/network_scan_<timestamp>.log`: Detailed multi-tool execution log.
