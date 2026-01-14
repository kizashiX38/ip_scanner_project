import asyncio
import os
import sys
import threading
import subprocess
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, DataTable, RichLog, Switch, Label, Input
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import work
from textual.message import Message
from rich.text import Text
import subprocess

class NetworkScannerTUI(App):
    """Enhanced TUI styled after Angry IP Scanner with port detection and device info."""
    
    def __init__(self):
        super().__init__()
        self._scan_active = False
        self._scan_paused = False
        self._scan_threads = []
        self._scan_process = None
        self._live_hosts = {}
        self._pending_actions = []  # Queue of pending button actions
        self._selected_ip = None  # Current selected IP
        self._selected_hostname = None
        self._selected_mac = None
        self._selected_ports = None

    CSS = """
    Screen {
        layout: vertical;
    }

    #toolbar {
        height: auto;
        background: $boost;
        border: solid $accent;
        padding: 1;
    }

    #toolbar-row {
        height: 3;
        align: left middle;
    }

    #ranges-section {
        height: auto;
        min-height: 10;
        background: $boost;
        border: double $accent;
        padding: 1;
        margin: 1;
    }

    #ranges-row {
        height: 3;
        align: left middle;
        width: 100%;
    }
    
    #ranges-row2 {
        height: 3;
        align: left middle;
        width: 100%;
        margin-top: 1;
    }
    
    .section-title {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    #results-section {
        height: 1fr;
        margin: 1;
    }
    
    #selected-ip-actions {
        height: auto;
        border: solid $accent;
        background: $boost;
        margin: 0 1;
        padding: 1;
    }
    
    #selected-ip-display {
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
        color: $accent;
    }
    
    #action-buttons {
        height: auto;
        width: 100%;
    }

    .network-container {
        height: auto;
        min-height: 10;
        margin-bottom: 1;
        border: solid $success;
        background: $surface;
    }

    .network-title {
        background: $primary;
        color: $text;
        text-style: bold;
        padding: 0 1;
        dock: top;
    }

    #log-container {
        height: 14;
        margin: 0 1 1 1;
        border: solid $warning;
        background: $panel;
    }
    
    .log-title {
        text-style: bold;
        color: $warning;
        padding: 0 1;
        background: $panel;
    }

    DataTable {
        height: auto;
    }

    RichLog {
        height: 1fr;
    }
    
    Input {
        width: 1fr;
        min-width: 25;
        margin: 0 1;
        background: $surface;
        height: 3;
    }
    
    Input:focus {
        border: tall $accent;
    }
    
    .range-input {
        width: 1fr;
        min-width: 30;
    }
    
    Label {
        padding: 0 1;
    }
    
    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "start_scan", "Start"),
        ("p", "pause_scan", "Pause"),
        ("r", "resume_scan", "Resume"),
        ("x", "stop_scan", "Stop"),
        ("d", "toggle_debug", "Debug"),
        ("c", "copy_selected_ip", "Copy"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        
        # Toolbar with controls
        with Container(id="toolbar"):
            with Horizontal(id="toolbar-row"):
                yield Button("▶ Start", variant="success", id="scan-btn")
                yield Button("⏸ Pause", variant="warning", id="pause-btn", disabled=True)
                yield Button("▶ Resume", variant="primary", id="resume-btn", disabled=True)
                yield Button("⏹ Stop", variant="error", id="stop-btn", disabled=True)
                yield Label(" │ Threads:")
                yield Input(value="50", placeholder="50", id="threads-input")
                yield Label("Timeout:")
                yield Input(value="1000", placeholder="1000", id="timeout-input")
                yield Label("Debug:")
                yield Switch(value=False, id="debug-switch")
        
        # IP Ranges section - BIG AUTO-RESIZING INPUTS
        with Container(id="ranges-section"):
            yield Static("═══ 📡 IP RANGES (CIDR NOTATION - Edit Below) ═══", classes="section-title")
            with Horizontal(id="ranges-row"):
                yield Label("🔸 Range 1:")
                yield Input(value="192.168.0.0/24", id="range1-input", classes="range-input")
                yield Label("🔸 Range 2:")
                yield Input(value="192.168.8.0/24", id="range2-input", classes="range-input")
            with Horizontal(id="ranges-row2"):
                yield Label("🔹 Range 3:")
                yield Input(value="", placeholder="Optional: e.g., 10.0.0.0/8", id="range3-input", classes="range-input")
                yield Label("🔹 Range 4:")
                yield Input(value="", placeholder="Optional: e.g., 172.16.0.0/12", id="range4-input", classes="range-input")
        
        # Selected IP Actions Section
        with Container(id="selected-ip-actions"):
            yield Static("🔍 Selected IP: (Click a row)", id="selected-ip-display")
            with Horizontal(id="action-buttons"):
                yield Button("📋 Copy IP", variant="primary", id="action-copy-btn")
                yield Button("🔔 Ping", variant="warning", id="action-ping-btn")
                yield Button("📋 Copy MAC", variant="default", id="action-copy-mac-btn")
                yield Button("📋 Copy Ports", variant="default", id="action-copy-ports-btn")
        
        # Results section - vertically stacked networks
        with VerticalScroll(id="results-section"):
            with Container(classes="network-container", id="network1-container"):
                yield Static("🌐 Network: 192.168.0.0/24", classes="network-title", id="network1-title")
                yield DataTable(id="results-table-1")
            with Container(classes="network-container", id="network2-container"):
                yield Static("🌐 Network: 192.168.8.0/24", classes="network-title", id="network2-title")
                yield DataTable(id="results-table-2")
        
        # Log section - BIGGER
        with Container(id="log-container"):
            yield Static("═══ 📋 SCAN LOG ═══", classes="log-title")
            yield RichLog(id="scan-log", wrap=True, highlight=True, markup=True)
        
        yield Footer()

    def on_mount(self) -> None:
        # Check if running as root
        if os.geteuid() != 0:
            self.log_message("⚠️  WARNING: Not running as root. Some scans may fail.", "error")
            self.log_message("   Run with: sudo bash scripts/run_tui.sh", "error")
        else:
            self.log_message("✓ Running with sudo privileges.", "success")
        
        # Setup tables with enhanced columns - Angry IP Scanner style
        for table_id in ["results-table-1", "results-table-2"]:
            table = self.query_one(f"#{table_id}", DataTable)
            # Add columns with specific widths
            table.add_column("IP", width=16)
            table.add_column("Ping", width=10)
            table.add_column("Hostname", width=25)
            table.add_column("MAC", width=18)
            table.add_column("Vendor", width=20)
            table.add_column("Ports", width=30)
            table.add_column("Copy", width=8)   # New copy column
            table.add_column("Ping", width=8)   # New ping column
            table.cursor_type = "row"  # Allow row selection
            table.show_header = True
            table.zebra_stripes = True
        
        self.log_message("✓ Scanner Ready. Configure ranges and press Start.", "success")
        self.log_message("📊 Scanning top 10 ports: 22,80,443,3389,3306,8080,21,25,110,143", "info")
        self.log_message("💡 Tip: Click IP row, then press 'c' to copy or Shift+P to ping", "info")

    def log_message(self, message: str, level: str = "info") -> None:
        """Log a message with appropriate styling based on level."""
        try:
            log = self.query_one("#scan-log", RichLog)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            text = Text()
            text.append(f"[{timestamp}] ", style="dim cyan")
            
            if "[DEBUG]" in message or level == "debug":
                text.append(message, style="dim italic")
            elif "WARNING" in message or "ERROR" in message or level == "error":
                text.append(message, style="bold red")
            elif "✓" in message or level == "success":
                text.append(message, style="bold green")
            else:
                text.append(message, style="white")
                
            log.write(text)
        except:
            pass

    def action_toggle_debug(self) -> None:
        switch = self.query_one("#debug-switch", Switch)
        switch.value = not switch.value
        self.log_message(f"🔧 Debug Mode {'Enabled' if switch.value else 'Disabled'}", "info")
    
    def action_copy_selected_ip(self) -> None:
        """Copy selected IP from active table to clipboard"""
        try:
            # Try to find focused table
            for table_id in ["results-table-1", "results-table-2"]:
                try:
                    table = self.query_one(f"#{table_id}", DataTable)
                    if table.rows:
                        # Get cursor row
                        row_idx = table.cursor_row
                        if row_idx >= 0 and row_idx < len(table.rows):
                            row_key = list(table.rows.keys())[row_idx]
                            ip_cell = table.get_row(row_key)[0]
                            ip = ip_cell.replace("🔗 ", "").strip()
                            self.copy_ip_to_clipboard(ip)
                            return
                except Exception as ex:
                    self.log_message(f"Table error: {ex}", "debug")
                    continue
            self.log_message("❌ No IP selected - click a table row first", "error")
        except Exception as e:
            self.log_message(f"❌ Copy error: {e}", "error")
    
    def action_ping_selected_ip(self) -> None:
        """Ping selected IP in external terminal"""
        try:
            # Try to find focused table
            for table_id in ["results-table-1", "results-table-2"]:
                try:
                    table = self.query_one(f"#{table_id}", DataTable)
                    if table.rows:
                        # Get cursor row
                        row_idx = table.cursor_row
                        if row_idx >= 0 and row_idx < len(table.rows):
                            row_key = list(table.rows.keys())[row_idx]
                            ip_cell = table.get_row(row_key)[0]
                            ip = ip_cell.replace("🔗 ", "").strip()
                            self.ping_ip_external(ip)
                            return
                except Exception as ex:
                    self.log_message(f"Table error: {ex}", "debug")
                    continue
            self.log_message("❌ No IP selected - click a table row first", "error")
        except Exception as e:
            self.log_message(f"❌ Ping error: {e}", "error")
    
    def action_on_row(self) -> None:
        """Handle Enter key on selected row - detect column and act"""
        try:
            for table_id in ["results-table-1", "results-table-2"]:
                try:
                    table = self.query_one(f"#{table_id}", DataTable)
                    if table.rows and table.cursor_row >= 0:
                        row_idx = table.cursor_row
                        col_idx = table.cursor_column if hasattr(table, 'cursor_column') else -1
                        
                        row_key = list(table.rows.keys())[row_idx]
                        ip_cell = table.get_row(row_key)[0]
                        ip = ip_cell.replace("🔗 ", "").strip()
                        
                        # Column 6 = Copy, Column 7 = Ping
                        if col_idx == 6:  # Copy column
                            self.copy_ip_to_clipboard(ip)
                        elif col_idx == 7:  # Ping column
                            self.ping_ip_external(ip)
                        return
                except:
                    continue
        except Exception as e:
            self.log_message(f"Error: {e}", "error")
    
    def action_pause_scan(self) -> None:
        """Pause the running scan by sending SIGSTOP to the process."""
        if not self._scan_active:
            self.log_message("⚠️ No scan is currently running.", "info")
            return
        
        if self._scan_paused:
            self.log_message("⚠️ Scan is already paused.", "info")
            return
        
        if not self._scan_process:
            self.log_message("❌ Scan process not available.", "error")
            self.update_buttons("idle")
            self._scan_active = False
            return
        
        # Check if process is still running
        if self._scan_process.poll() is not None:
            self.log_message("⚠️ Scan process has already finished.", "info")
            self._scan_active = False
            self._scan_paused = False
            self.update_buttons("idle")
            return
        
        try:
            self._scan_process.send_signal(19)  # SIGSTOP
            self._scan_paused = True
            self.log_message("⏸ Scan paused.", "info")
            self.update_buttons("paused")
        except ProcessLookupError:
            self.log_message("❌ Process not found - scan may have finished.", "error")
            self._scan_active = False
            self._scan_paused = False
            self.update_buttons("idle")
        except Exception as e:
            self.log_message(f"❌ Failed to pause scan: {e}", "error")
    
    def action_resume_scan(self) -> None:
        """Resume the paused scan by sending SIGCONT to the process."""
        if not self._scan_active:
            self.log_message("⚠️ No scan is currently active.", "info")
            return
        
        if not self._scan_paused:
            self.log_message("⚠️ Scan is not paused.", "info")
            return
        
        if not self._scan_process:
            self.log_message("❌ Scan process not available.", "error")
            self.update_buttons("idle")
            self._scan_active = False
            self._scan_paused = False
            return
        
        # Check if process is still running
        if self._scan_process.poll() is not None:
            self.log_message("⚠️ Scan process has already finished.", "info")
            self._scan_active = False
            self._scan_paused = False
            self.update_buttons("idle")
            return
        
        try:
            self._scan_process.send_signal(18)  # SIGCONT
            self._scan_paused = False
            self.log_message("▶ Scan resumed.", "info")
            self.update_buttons("scanning")
        except ProcessLookupError:
            self.log_message("❌ Process not found - scan may have finished.", "error")
            self._scan_active = False
            self._scan_paused = False
            self.update_buttons("idle")
        except Exception as e:
            self.log_message(f"❌ Failed to resume scan: {e}", "error")
    
    def action_stop_scan(self) -> None:
        """Stop the scan by terminating the process and cleaning up."""
        if not self._scan_active:
            self.log_message("⚠️ No scan is currently running.", "info")
            return
        
        self.log_message("⏹ Stopping scan...", "info")
        self._scan_active = False
        self._scan_paused = False
        
        # Update buttons immediately
        self.update_buttons("idle")
        
        # Terminate the process
        if self._scan_process:
            try:
                # If paused, resume first so we can terminate it properly
                if self._scan_paused:
                    try:
                        self._scan_process.send_signal(18)  # SIGCONT
                    except:
                        pass
                
                # Terminate the process
                self._scan_process.terminate()
                
                # Wait for it to finish (with timeout)
                try:
                    self._scan_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    try:
                        self._scan_process.kill()
                        self._scan_process.wait(timeout=1)
                    except:
                        pass
            except ProcessLookupError:
                # Process already finished
                pass
            except Exception as e:
                self.log_message(f"⚠️ Error stopping process: {e}", "error")
            finally:
                self._scan_process = None
        
        # Stop reading threads by setting flag (they check _scan_active)
        # Give threads a moment to finish
        if self._scan_threads:
            for thread in self._scan_threads:
                if thread.is_alive():
                    thread.join(timeout=1)
        
        self.log_message("✓ Scan stopped.", "success")
    
    def copy_ip_to_clipboard(self, ip: str) -> None:
        """Copy IP address to clipboard with multiple fallback methods"""
        if not ip:
            self.log_message("❌ No IP to copy", "error")
            return
        
        import subprocess
        import shutil
        
        # Method 1: Try xclip
        if shutil.which('xclip'):
            try:
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate(ip.encode(), timeout=2)
                if process.returncode == 0:
                    self.log_message(f"📋 Copied to clipboard (xclip): {ip}", "success")
                    return
            except Exception as e:
                self.log_message(f"⚠️ xclip failed: {str(e)[:30]}", "debug")
        
        # Method 2: Try xsel
        if shutil.which('xsel'):
            try:
                process = subprocess.Popen(['xsel', '-bi'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate(ip.encode(), timeout=2)
                if process.returncode == 0:
                    self.log_message(f"📋 Copied to clipboard (xsel): {ip}", "success")
                    return
            except Exception as e:
                self.log_message(f"⚠️ xsel failed: {str(e)[:30]}", "debug")
        
        # Method 3: Try wl-copy (Wayland)
        if shutil.which('wl-copy'):
            try:
                process = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate(ip.encode(), timeout=2)
                if process.returncode == 0:
                    self.log_message(f"📋 Copied to clipboard (wl-copy): {ip}", "success")
                    return
            except Exception as e:
                self.log_message(f"⚠️ wl-copy failed: {str(e)[:30]}", "debug")
        
        # Fallback: Save to temp file with instructions
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(ip)
                temp_path = f.name
            self.log_message(f"❌ No clipboard tool found. Saved to: {temp_path}", "error")
            self.log_message(f"📋 Value: {ip}", "info")
            self.log_message("💡 Install xclip: sudo apt install xclip", "info")
        except Exception as e:
            self.log_message(f"❌ Failed to copy {ip}: {str(e)[:50]}", "error")
    
    def ping_ip_external(self, ip: str) -> None:
        """Open external terminal and ping the IP"""
        try:
            # Try different terminal emulators
            terminals = [
                ['gnome-terminal', '--', 'ping', ip],
                ['xterm', '-e', 'ping', ip],
                ['konsole', '-e', 'ping', ip],
                ['xfce4-terminal', '-e', f'ping {ip}'],
            ]
            
            for terminal_cmd in terminals:
                try:
                    subprocess.Popen(terminal_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.log_message(f"🔔 Opened terminal for ping {ip}", "success")
                    return
                except FileNotFoundError:
                    continue
            
            self.log_message(f"❌ No terminal found to ping {ip}", "error")
        except Exception as e:
            self.log_message(f"❌ Error opening terminal: {e}", "error")

    def _safe_call_from_thread(self, func, *args, **kwargs):
        """Safely call a function from thread, checking if app is running."""
        try:
            if self.is_running and self._scan_active:
                self.call_from_thread(func, *args, **kwargs)
        except (RuntimeError, AttributeError):
            pass
    
    def _parse_scan_output(self, line: str):
        """Parse scan output and update tables."""
        if not line or not line.startswith("LIVE|"):
            return
        
        try:
            # Format: LIVE|IP|HOSTNAME|MAC|VENDOR|PORTS|PING
            # Using | delimiter to avoid issues with : in MAC addresses
            parts = line[5:].split("|")
            if len(parts) < 6:  # Need at least IP through PORTS
                self.log_message(f"⚠️ Incomplete data: {line[:50]}...", "debug")
                return
                
            ip = parts[0] if parts[0] else "-"
            hostname = parts[1] if parts[1] else "-"
            mac = parts[2] if parts[2] else "-"
            vendor = parts[3] if parts[3] else "-"
            ports = parts[4] if parts[4] else "-"  # PORTS - now correctly parsed!
            ping = parts[5] if len(parts) > 5 and parts[5] else "-"
            
            # Debug log to verify parsing
            debug_switch = self.query_one("#debug-switch", Switch)
            if debug_switch and debug_switch.value:
                self.log_message(f"🔍 {ip}: Ports=[{ports}] Ping={ping}", "debug")
            
            self._live_hosts[ip] = {
                "hostname": hostname,
                "mac": mac,
                "vendor": vendor,
                "ports": ports,
                "ping": ping
            }
            
            # Determine which table this IP belongs to
            if ip.startswith("192.168.0."):
                table_id = "results-table-1"
            elif ip.startswith("192.168.8."):
                table_id = "results-table-2"
            else:
                # Try to find the right table based on custom ranges
                table_id = "results-table-1"
            
            self._safe_call_from_thread(self.add_row, table_id, ip, ping, hostname, mac, vendor, ports)
            
        except Exception as e:
            self._safe_call_from_thread(self.log_message, f"⚠️ Parse error: {str(e)}", "error")

    def _read_stream(self, stream, is_stderr=False):
        """Read from a stream line by line and log messages."""
        try:
            while self._scan_active:
                line = stream.readline()
                if not line:
                    # EOF reached
                    break
                if not self._scan_active:
                    break
                line = line.strip()
                if line:
                    if is_stderr:
                        self._safe_call_from_thread(self.log_message, f"[STDERR] {line}", "error")
                    else:
                        if line.startswith("LIVE|"):
                            self._parse_scan_output(line)
                        else:
                            self._safe_call_from_thread(self.log_message, line)
        except Exception as e:
            if self._scan_active:
                self._safe_call_from_thread(self.log_message, f"Stream error: {str(e)}", "error")
        finally:
            try:
                stream.close()
            except:
                pass

    @work(exclusive=True, thread=True)
    async def run_scan(self) -> None:
        self._scan_active = True
        self._scan_paused = False
        self._live_hosts = {}
        
        # Get options
        try:
            threads = int(self.query_one("#threads-input", Input).value or "50")
            timeout = int(self.query_one("#timeout-input", Input).value or "1000")
        except ValueError:
            threads = 50
            timeout = 1000
        
        # Get IP ranges and update titles
        ranges = []
        for i in range(1, 5):
            range_val = self.query_one(f"#range{i}-input", Input).value.strip()
            if range_val:
                ranges.append(range_val)
                # Update network titles
                if i <= 2:
                    try:
                        title = self.query_one(f"#network{i}-title", Static)
                        title.update(f"🌐 Network: {range_val}")
                    except:
                        pass
        
        if not ranges:
            self.log_message("❌ Error: No IP ranges specified!", "error")
            self.update_buttons("idle")
            self._scan_active = False
            return
            
        debug_enabled = self.query_one("#debug-switch", Switch).value
        self.log_message(f"🚀 Starting scan: {', '.join(ranges)}", "info")
        self.log_message(f"⚙️ Config: {threads} threads, {timeout}ms timeout", "info")
        self.update_buttons("scanning")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "scan_subnets_enhanced.sh")
        
        if not os.path.exists(script_path):
            self.log_message(f"❌ Script not found: {script_path}", "error")
            self.update_buttons("idle")
            self._scan_active = False
            return
        
        cmd = ["bash", script_path, str(threads), str(timeout)] + ranges
        if debug_enabled:
            cmd.append("--debug")
            
        stdout_thread = None
        stderr_thread = None
        
        try:
            self._scan_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            process = self._scan_process
            
            stdout_thread = threading.Thread(target=self._read_stream, args=(process.stdout, False), daemon=True)
            stderr_thread = threading.Thread(target=self._read_stream, args=(process.stderr, True), daemon=True)
            
            self._scan_threads = [stdout_thread, stderr_thread]
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for process to complete (or be stopped)
            process.wait()
            
            # Wait for reading threads to finish
            if stdout_thread and stdout_thread.is_alive():
                stdout_thread.join(timeout=2)
            if stderr_thread and stderr_thread.is_alive():
                stderr_thread.join(timeout=2)
            
            # Only log completion if scan wasn't manually stopped
            if self._scan_active:
                live_count = len(self._live_hosts)
                if process.returncode == 0:
                    self._safe_call_from_thread(self.log_message, f"✓ Scan completed! Found {live_count} live hosts.", "success")
                elif process.returncode == -15:  # SIGTERM
                    self._safe_call_from_thread(self.log_message, f"⏹ Scan stopped by user. Found {live_count} hosts.", "info")
                else:
                    self._safe_call_from_thread(self.log_message, f"⚠️ Scan finished with errors. Found {live_count} hosts.", "error")
                
        except FileNotFoundError:
            if self._scan_active:
                self._safe_call_from_thread(self.log_message, "❌ Error: bash not found.", "error")
        except Exception as e:
            if self._scan_active:
                self._safe_call_from_thread(self.log_message, f"❌ Error: {str(e)}", "error")
        finally:
            # Clean up process if still running
            if self._scan_process:
                try:
                    # If paused, resume first
                    if self._scan_paused:
                        try:
                            self._scan_process.send_signal(18)  # SIGCONT
                        except:
                            pass
                    
                    # Check if still running
                    if self._scan_process.poll() is None:
                        self._scan_process.terminate()
                        try:
                            self._scan_process.wait(timeout=1)
                        except subprocess.TimeoutExpired:
                            try:
                                self._scan_process.kill()
                                self._scan_process.wait(timeout=1)
                            except:
                                pass
                except ProcessLookupError:
                    pass
                except Exception:
                    pass
                finally:
                    self._scan_process = None
            
            # Clean up threads
            if self._scan_threads:
                for thread in self._scan_threads:
                    if thread.is_alive():
                        thread.join(timeout=1)
                self._scan_threads = []
            
            # Reset state
            self._scan_active = False
            self._scan_paused = False
            
            # Update buttons
            self._safe_call_from_thread(self.update_buttons, "idle")

    def update_buttons(self, state: str) -> None:
        """Update button states: 'idle', 'scanning', 'paused'"""
        try:
            scan_btn = self.query_one("#scan-btn", Button)
            pause_btn = self.query_one("#pause-btn", Button)
            resume_btn = self.query_one("#resume-btn", Button)
            stop_btn = self.query_one("#stop-btn", Button)
            
            if state == "idle":
                scan_btn.disabled = False
                scan_btn.variant = "success"
                pause_btn.disabled = True
                resume_btn.disabled = True
                stop_btn.disabled = True
            elif state == "scanning":
                scan_btn.disabled = True
                scan_btn.variant = "default"
                pause_btn.disabled = False
                resume_btn.disabled = True
                stop_btn.disabled = False
            elif state == "paused":
                scan_btn.disabled = True
                pause_btn.disabled = True
                resume_btn.disabled = False
                stop_btn.disabled = False
        except Exception as e:
            self.log_message(f"Button update error: {e}", "error")

    def add_row(self, table_id: str, ip: str, ping: str, hostname: str, mac: str, vendor: str, ports: str) -> None:
        try:
            table = self.query_one(f"#{table_id}", DataTable)
            
            # Truncate long values to fit columns better
            hostname = hostname[:24] if len(hostname) > 24 else hostname
            vendor = vendor[:19] if len(vendor) > 19 else vendor
            
            # Add interactive buttons to IP column
            ip_display = f"🔗 {ip}"  # Add icon to indicate interactive
            
            # Action columns
            copy_action = "📋 Copy"   # Copy button
            ping_action = "🔔 Ping"   # Ping button
            
            # Check for duplicates
            for row_key in table.rows:
                row_data = table.get_row(row_key)
                # Compare without the icon
                if row_data[0].replace("🔗 ", "").strip() == ip:
                    # Update existing row
                    table.update_cell(row_key, "Ping", ping)
                    table.update_cell(row_key, "Hostname", hostname)
                    table.update_cell(row_key, "MAC", mac)
                    table.update_cell(row_key, "Vendor", vendor)
                    table.update_cell(row_key, "Ports", ports)
                    return
            # Add new row with IP and action columns
            table.add_row(ip_display, ping, hostname, mac, vendor, ports, copy_action, ping_action)
            self.log_message(f"✅ Found live host: {ip}", "success")
        except Exception as e:
            self.log_message(f"Error adding row: {e}", "error")

    def action_start_scan(self) -> None:
        """Start a new scan or resume if paused."""
        # If paused, resume instead of starting new scan
        if self._scan_active and self._scan_paused:
            self.action_resume_scan()
            return
        
        if self._scan_active and not self._scan_paused:
            self.log_message("⚠️ Scan already in progress.", "info")
            return
        
        # Clear previous scan state
        self._scan_active = False
        self._scan_paused = False
        self._scan_process = None
        self._scan_threads = []
        
        # Clear tables
        try:
            self.query_one("#results-table-1", DataTable).clear()
            self.query_one("#results-table-2", DataTable).clear()
        except:
            pass
        
        # Clear live hosts
        self._live_hosts = {}
        
        # Start new scan
        self.run_scan()
    
    def on_data_table_row_selected(self, event) -> None:
        """Handle row selection in data tables for copy/ping actions"""
        try:
            # Get the table and row
            table = event.data_table
            row_idx = event.cursor_row
            
            if row_idx < 0 or row_idx >= len(table.rows):
                return
            
            row_key = list(table.rows.keys())[row_idx]
            row_data = table.get_row(row_key)
            ip = row_data[0].replace("🔗 ", "").strip() if row_data[0] else None
            
            if not ip:
                return
            
            # Store selected IP data
            self._selected_ip = ip
            self._selected_hostname = row_data[2] if len(row_data) > 2 else "-"
            self._selected_mac = row_data[3] if len(row_data) > 3 else "-"
            self._selected_ports = row_data[5] if len(row_data) > 5 else "-"
            
            # Update display
            try:
                display = self.query_one("#selected-ip-display", Static)
                display.update(f"🔍 Selected IP: {ip} | MAC: {self._selected_mac} | Ports: {self._selected_ports}")
                self.log_message(f"✅ Selected: {ip}", "success")
            except:
                pass
            
        except Exception as e:
            self.log_message(f"Error in row selection: {e}", "debug")
    
    def _update_action_buttons(self) -> None:
        """Update action button states based on selection"""
        try:
            if hasattr(self, '_selected_ip') and self._selected_ip:
                copy_btn = self.query_one("#action-copy-btn", Button)
                ping_btn = self.query_one("#action-ping-btn", Button)
                copy_mac_btn = self.query_one("#action-copy-mac-btn", Button)
                copy_ports_btn = self.query_one("#action-copy-ports-btn", Button)
                
                copy_btn.disabled = False
                ping_btn.disabled = False
                copy_mac_btn.disabled = False if self._selected_mac != "-" else True
                copy_ports_btn.disabled = False if self._selected_ports != "-" else True
            else:
                # Disable all buttons if no selection
                for btn_id in ["#action-copy-btn", "#action-ping-btn", "#action-copy-mac-btn", "#action-copy-ports-btn"]:
                    try:
                        btn = self.query_one(btn_id, Button)
                        btn.disabled = True
                    except:
                        pass
        except:
            pass

    def action_copy_highlighted_ip(self) -> None:
        """Copy the highlighted/selected IP from table"""
        try:
            if hasattr(self, '_current_highlighted_ip') and self._current_highlighted_ip:
                self.copy_ip_to_clipboard(self._current_highlighted_ip)
            else:
                self.log_message("❌ No IP selected - click a row first", "error")
        except Exception as e:
            self.log_message(f"❌ Error: {e}", "error")
    
    def action_ping_highlighted_ip(self) -> None:
        """Ping the highlighted/selected IP in external terminal"""
        try:
            if hasattr(self, '_current_highlighted_ip') and self._current_highlighted_ip:
                self.ping_ip_external(self._current_highlighted_ip)
            else:
                self.log_message("❌ No IP selected - click a row first", "error")
        except Exception as e:
            self.log_message(f"❌ Error: {e}", "error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks with proper state management and debouncing"""
        try:
            button_id = event.button.id
            
            # Debounce: ignore if button is disabled
            if event.button.disabled:
                return
            
            # Main scan control buttons
            if button_id == "scan-btn":
                self.call_later(self.action_start_scan)
            elif button_id == "pause-btn":
                self.call_later(self.action_pause_scan)
            elif button_id == "resume-btn":
                self.call_later(self.action_resume_scan)
            elif button_id == "stop-btn":
                self.call_later(self.action_stop_scan)
            
            # Action buttons for selected IP
            elif button_id == "action-copy-btn":
                if hasattr(self, '_selected_ip') and self._selected_ip:
                    self.call_later(self.copy_ip_to_clipboard, self._selected_ip)
            elif button_id == "action-ping-btn":
                if hasattr(self, '_selected_ip') and self._selected_ip:
                    self.call_later(self.ping_ip_external, self._selected_ip)
            elif button_id == "action-copy-mac-btn":
                if hasattr(self, '_selected_mac') and self._selected_mac and self._selected_mac != "-":
                    self.call_later(self.copy_ip_to_clipboard, self._selected_mac)
            elif button_id == "action-copy-ports-btn":
                if hasattr(self, '_selected_ports') and self._selected_ports and self._selected_ports != "-":
                    self.call_later(self.copy_ip_to_clipboard, self._selected_ports)
        except Exception as e:
            self.log_message(f"❌ Button error: {str(e)[:50]}", "error")

if __name__ == "__main__":
    try:
        app = NetworkScannerTUI()
        app.run()
    except KeyboardInterrupt:
        pass
