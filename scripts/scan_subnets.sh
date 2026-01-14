#!/bin/bash
# scan_subnets.sh — Multi-tool thorough scan of subnets for live hosts
# Created: 2026-01-14
# Updated: 2026-01-14 (Added structured logging and debug mode)
# Usage: sudo bash scripts/scan_subnets.sh [--debug]

# Don't exit on error - we handle failures gracefully with || true
set +e
# Ensure output is unbuffered for real-time TUI display (bash doesn't buffer by default, but be explicit)
stdbuf -oL -eL bash -c "true" 2>/dev/null || true

# --- Configuration & Initialization ---
DEBUG=false
SUBNETS=("192.168.0.0/24" "192.168.8.0/24")
INTERFACES=("enxa453eed5dd26" "wlp99s0")
BASE_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$LOG_DIR/network_scan_$TIMESTAMP.log"
RAM_FILE="/dev/shm/all_discovered_hosts_$TIMESTAMP.txt"

# Parse arguments
for arg in "$@"; do
    if [ "$arg" == "--debug" ] || [ "$arg" == "-d" ]; then
        DEBUG=true
    fi
done

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
log_info "=== Network Subnet Scan Started ==="
log_info "Target subnets: ${SUBNETS[*]}"
[ "$DEBUG" = true ] && log_debug "Debug mode ENABLED. Increased verbosity."

START_TIME=$(date +%s)

# 1. ARP Scan (Layer 2)
log_info "Running ARP Scan (Layer 2)..."
for i in "${!SUBNETS[@]}"; do
    subnet="${SUBNETS[$i]}"
    interface="${INTERFACES[$i]}"
    log_debug "Scanning $subnet on interface $interface"
    
    # Run arp-scan and capture output for debug if needed
    if [ "$DEBUG" = true ]; then
        arp-scan --interface="$interface" "$subnet" 2>&1 | tee -a "$LOG_FILE" | grep -E "^([0-9]{1,3}\.){3}[0-9]{1,3}" | awk '{print $1}' >> "$RAM_FILE" || true
    else
        arp-scan --interface="$interface" "$subnet" 2>/dev/null | grep -E "^([0-9]{1,3}\.){3}[0-9]{1,3}" | awk '{print $1}' >> "$RAM_FILE" || true
    fi
done

# 2. fping Scan (ICMP)
log_info "Running fping Scan (ICMP)..."
for subnet in "${SUBNETS[@]}"; do
    log_debug "Pinging subnet $subnet"
    fping -a -g "$subnet" -r 3 -t 1000 2>>"$LOG_FILE" >> "$RAM_FILE" || true
done

# 3. Thorough Nmap Scan (Layer 3/4)
log_info "Running Thorough Nmap Scan (L3/L4)..."
NMAP_OPTS="-sn -PE -PP -PS22,80,443,3389,8080,5000,8000 -PA80,443 -PU53,67,137,161,1900 --max-retries 3 --host-timeout 20s -T4"
[ "$DEBUG" = true ] && NMAP_OPTS="$NMAP_OPTS -v"

log_debug "Nmap options: $NMAP_OPTS"
nmap $NMAP_OPTS "${SUBNETS[@]}" -oG - | tee -a "$LOG_FILE" | grep "Host: " | awk '{print $2}' >> "$RAM_FILE" || true

# --- Post-Processing ---
log_info "Processing results..."
if [ -f "$RAM_FILE" ]; then
    sort -u "$RAM_FILE" -o "$RAM_FILE"
    HOSTS_UP=$(wc -l < "$RAM_FILE")
else
    HOSTS_UP=0
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log_info "Scan completed in $DURATION seconds."
log_info "Total unique hosts discovered: $HOSTS_UP"

# Move results to permanent storage
RESULTS_DIR="$BASE_DIR/results"
mkdir -p "$RESULTS_DIR"
FINAL_RESULTS="$RESULTS_DIR/network_scan_results_$TIMESTAMP.txt"
[ -f "$RAM_FILE" ] && cp "$RAM_FILE" "$FINAL_RESULTS"

# Display Detailed Summary
echo "" | tee -a "$LOG_FILE" 2>&1
log_info "[Consolidated Live Hosts List]"
if [ -f "$RAM_FILE" ]; then
    while read -r ip; do
        [ -z "$ip" ] && continue
        host_info=$(getent hosts "$ip" 2>/dev/null || echo "$ip")
        echo "- $host_info" | tee -a "$LOG_FILE" 2>&1
    done < "$RAM_FILE"
fi

# Cleanup
[ -f "$RAM_FILE" ] && rm "$RAM_FILE"

log_info "=== Scan Finished ==="
