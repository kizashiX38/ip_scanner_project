#!/bin/bash
# scan_subnets_enhanced.sh — Enhanced multi-tool scan with MAC, vendor, and port detection
# Created: 2026-01-14
# Usage: bash scripts/scan_subnets_enhanced.sh [threads] [timeout] [range1] [range2] ... [--debug]

set +e

# --- Configuration ---
THREADS="${1:-50}"
TIMEOUT="${2:-1000}"
DEBUG=false
SUBNETS=()
INTERFACES=("enxa453eed5dd26" "wlp99s0")
# Top 10 most common ports worldwide
TOP_PORTS="22,80,443,3389,3306,8080,21,25,110,143"

# Parse arguments
shift 2  # Skip threads and timeout
for arg in "$@"; do
    if [ "$arg" == "--debug" ] || [ "$arg" == "-d" ]; then
        DEBUG=true
    elif [[ "$arg" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$ ]]; then
        SUBNETS+=("$arg")
    fi
done

# Default subnets if none provided
if [ ${#SUBNETS[@]} -eq 0 ]; then
    SUBNETS=("192.168.0.0/24" "192.168.8.0/24")
fi

# Dynamic paths
BASE_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/enhanced_scan_$TIMESTAMP.log"
RAM_FILE="/dev/shm/discovered_hosts_$TIMESTAMP.txt"
ARP_DATA="/dev/shm/arp_data_$TIMESTAMP.txt"

# --- Logging Functions ---
log_info() {
    echo -e "[INFO] $(date +'%H:%M:%S') - $1" | tee -a "$LOG_FILE" 2>&1
}

log_debug() {
    if [ "$DEBUG" = true ]; then
        echo -e "[DEBUG] $(date +'%H:%M:%S') - $1" | tee -a "$LOG_FILE" 2>&1
    fi
}

log_error() {
    echo -e "[ERROR] $(date +'%H:%M:%S') - $1" | tee -a "$LOG_FILE" 2>&1
}

# --- Main Scan Execution ---
log_info "=== Enhanced Network Scan Started ==="
log_info "Configuration: Threads=$THREADS, Timeout=${TIMEOUT}ms, Ports=$TOP_PORTS"
[ "$DEBUG" = true ] && log_debug "Debug mode ENABLED"

START_TIME=$(date +%s)

# 1. ARP Scan for MAC addresses (Layer 2)
log_info "Running ARP Scan for MAC addresses..."
for i in "${!SUBNETS[@]}"; do
    subnet="${SUBNETS[$i]}"
    interface="${INTERFACES[$i]}"
    log_debug "ARP scanning $subnet on $interface"
    
    # Run arp-scan and save MAC data
    arp-scan --interface="$interface" "$subnet" 2>/dev/null | grep -E "^([0-9]{1,3}\.){3}[0-9]{1,3}" >> "$ARP_DATA" || true
done

# 2. Fast ping sweep with fping
log_info "Running fast ping sweep..."
for subnet in "${SUBNETS[@]}"; do
    log_debug "Pinging subnet $subnet"
    fping -a -g "$subnet" -r 2 -t "$TIMEOUT" 2>/dev/null >> "$RAM_FILE" || true
done

# 3. Nmap host discovery
log_info "Running Nmap host discovery..."
NMAP_OPTS="-sn -PE -PP -PA80,443 --max-retries 2 --host-timeout 15s -T4 --min-parallelism $THREADS"
[ "$DEBUG" = true ] && NMAP_OPTS="$NMAP_OPTS -v"

log_debug "Nmap options: $NMAP_OPTS"
nmap $NMAP_OPTS "${SUBNETS[@]}" -oG - 2>/dev/null | grep "Host: " | awk '{print $2}' >> "$RAM_FILE" || true

# --- Process Live Hosts ---
log_info "Processing discovered hosts..."
if [ -f "$RAM_FILE" ]; then
    sort -u "$RAM_FILE" -o "$RAM_FILE"
    HOSTS_UP=$(wc -l < "$RAM_FILE")
else
    HOSTS_UP=0
fi

log_info "Found $HOSTS_UP potential live hosts. Scanning ports and gathering details..."

# --- Enhanced Scan for Each Live Host ---
if [ -f "$RAM_FILE" ] && [ "$HOSTS_UP" -gt 0 ]; then
    while read -r ip; do
        [ -z "$ip" ] && continue
        
        log_debug "Scanning $ip for details..."
        
        # Get hostname
        hostname=$(getent hosts "$ip" 2>/dev/null | awk '{print $2}' | head -1)
        [ -z "$hostname" ] && hostname=$(nslookup "$ip" 2>/dev/null | grep "name =" | awk '{print $NF}' | sed 's/\.$//')
        [ -z "$hostname" ] && hostname="-"
        
        # Get MAC and vendor from ARP data
        mac="-"
        vendor="-"
        if [ -f "$ARP_DATA" ]; then
            arp_line=$(grep "^$ip" "$ARP_DATA" | head -1)
            if [ -n "$arp_line" ]; then
                mac=$(echo "$arp_line" | awk '{print $2}')
                vendor=$(echo "$arp_line" | cut -d$'\t' -f3- | sed 's/^[[:space:]]*//')
                [ -z "$vendor" ] && vendor="-"
            fi
        fi
        
        # Get ping time
        ping_time=$(ping -c 1 -W 1 "$ip" 2>/dev/null | grep "time=" | sed -n 's/.*time=\([0-9.]*\).*/\1/p')
        [ -z "$ping_time" ] && ping_time="-"
        [ -n "$ping_time" ] && ping_time="${ping_time}ms"
        
        # Quick port scan on top 10 common ports
        ports="-"
        open_ports=$(nmap -p "$TOP_PORTS" --open -T4 --max-retries 1 --host-timeout 3s "$ip" 2>/dev/null | grep "^[0-9]" | grep "open" | awk '{print $1}' | cut -d/ -f1 | tr '\n' ',' | sed 's/,$//')
        [ -n "$open_ports" ] && ports="$open_ports"
        
        # Output in parseable format with | delimiter: LIVE|IP|HOSTNAME|MAC|VENDOR|PORTS|PING
        echo "LIVE|$ip|$hostname|$mac|$vendor|$ports|$ping_time" | tee -a "$LOG_FILE" 2>&1
        
    done < "$RAM_FILE"
fi

# --- Cleanup ---
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

[ -f "$RAM_FILE" ] && rm "$RAM_FILE"
[ -f "$ARP_DATA" ] && rm "$ARP_DATA"

log_info "=== Scan Finished in $DURATION seconds ==="
