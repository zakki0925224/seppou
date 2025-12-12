import atexit
import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time
import tkinter as tk
from enum import Enum
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk
from typing import Dict, Optional


class ServiceStatus(Enum):
    STOPPED = "Stopped"
    STARTING = "Starting"
    RUNNING = "Running"
    STOPPING = "Stopping"
    ERROR = "Error"


class ServiceProcess:
    def __init__(self, name: str, command: list[str], cwd: Path):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.process: Optional[subprocess.Popen] = None
        self.status = ServiceStatus.STOPPED
        self.log_queue = queue.Queue()
        self.reader_thread: Optional[threading.Thread] = None
        self.stop_lock = threading.Lock()
        self.is_stopping = False

    def start(self) -> bool:
        """Start the process"""
        with self.stop_lock:
            # Do nothing if already running
            if self.process and self.process.poll() is None:
                return False

            # Wait if stop is in progress
            if self.is_stopping:
                self.log_queue.put(f"[{self.name}] Waiting for stop to complete...\n")
                return False

            try:
                self.status = ServiceStatus.STARTING

                # Clean up previous resources
                self._cleanup_resources()

                # Create process group and start (for Linux)
                if os.name == "posix":
                    self.process = subprocess.Popen(
                        self.command,
                        cwd=self.cwd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        start_new_session=True,  # Create new process group
                    )
                else:
                    self.process = subprocess.Popen(
                        self.command,
                        cwd=self.cwd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                        if os.name == "nt"
                        else 0,
                    )

                # Start output reading thread
                self.reader_thread = threading.Thread(
                    target=self._read_output, daemon=True, name=f"{self.name}_reader"
                )
                self.reader_thread.start()

                self.status = ServiceStatus.RUNNING
                self.log_queue.put(f"[{self.name}] Started (PID: {self.process.pid})\n")
                return True

            except Exception as e:
                self.status = ServiceStatus.ERROR
                self.log_queue.put(f"[{self.name}] Start error: {e}\n")
                self._cleanup_resources()
                return False

    def stop(self) -> bool:
        """Stop the process (asynchronous)"""
        if not self.process or self.process.poll() is not None:
            self.status = ServiceStatus.STOPPED
            return False

        # Do nothing if already stopping
        if self.is_stopping:
            return False

        self.status = ServiceStatus.STOPPING
        self.is_stopping = True

        # Execute stop process in thread
        stop_thread = threading.Thread(
            target=self._stop_process_internal,
            daemon=False,  # daemon=False to ensure complete shutdown
            name=f"{self.name}_stopper",
        )
        stop_thread.start()
        return True

    def _stop_process_internal(self):
        """Internal process stop implementation"""
        with self.stop_lock:
            try:
                if not self.process:
                    return

                pid = self.process.pid
                self.log_queue.put(f"[{self.name}] Stopping (PID: {pid})...\n")

                # Send termination signal to entire process group
                if os.name == "posix":
                    try:
                        # Send SIGTERM to process group
                        os.killpg(os.getpgid(pid), signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                else:
                    self.process.terminate()

                # Wait for termination
                try:
                    self.process.wait(timeout=3)
                    self.log_queue.put(f"[{self.name}] Stopped gracefully\n")
                except subprocess.TimeoutExpired:
                    # Force kill
                    self.log_queue.put(f"[{self.name}] Force killing...\n")
                    if os.name == "posix":
                        try:
                            os.killpg(os.getpgid(pid), signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    else:
                        self.process.kill()

                    self.process.wait(timeout=2)
                    self.log_queue.put(f"[{self.name}] Force killed\n")

                # Wait a bit for port to be released
                time.sleep(0.5)

            except Exception as e:
                self.log_queue.put(f"[{self.name}] Stop error: {e}\n")
            finally:
                self._cleanup_resources()
                self.status = ServiceStatus.STOPPED
                self.is_stopping = False

    def _cleanup_resources(self):
        """Clean up resources"""
        # Close stdout
        if self.process and self.process.stdout:
            try:
                self.process.stdout.close()
            except:
                pass

        # Wait for reader_thread to finish (short timeout)
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)

        self.process = None
        self.reader_thread = None

    def is_running(self) -> bool:
        """Check if process is running"""
        if self.process and self.process.poll() is None:
            return True
        if self.process and self.process.poll() is not None:
            if self.status == ServiceStatus.RUNNING:
                self.status = ServiceStatus.STOPPED
        return False

    def _read_output(self):
        """Read process output"""
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                # Check if process has terminated
                if not self.process or self.process.poll() is not None:
                    break

                try:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                    self.log_queue.put(line)
                except (ValueError, OSError):
                    break

        except Exception as e:
            self.log_queue.put(f"[{self.name}] Reader error: {e}\n")
        finally:
            # Update status when thread exits
            if self.process and self.process.poll() is not None:
                if self.status == ServiceStatus.RUNNING:
                    self.status = ServiceStatus.STOPPED
                    self.log_queue.put(f"[{self.name}] Process exited\n")


class ManagerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("seppou GUI Manager")
        self.root.geometry("1000x700")

        self.base_path = Path(__file__).parent

        service_configs = {
            "engi": {
                "command": ["go", "run", ".", "--config", "../config.toml"],
                "cwd": self.base_path / "engi",
                "port": 8080,
            },
            "shiki": {
                "command": ["uv", "run", "src/main.py", "../config.toml"],
                "cwd": self.base_path / "shiki",
                "port": 8000,
            },
            "zen": {
                "command": ["bun", "run", "dev"],
                "cwd": self.base_path / "zen",
                "port": 5173,
            },
        }

        self.services: Dict[str, ServiceProcess] = {}

        for name, config in service_configs.items():
            self.services[name] = ServiceProcess(name, config["command"], config["cwd"])

        self._create_widgets()
        self._update_logs()

    def _create_widgets(self):
        status_frame = ttk.LabelFrame(self.root, text="Service status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_labels = {}
        self.pid_labels = {}
        self.control_buttons = {}

        for idx, (name, service) in enumerate(self.services.items()):
            ttk.Label(status_frame, text=name, font=("Arial", 12, "bold")).grid(
                row=idx, column=0, padx=5, pady=5, sticky=tk.W
            )

            status_var = tk.StringVar(value=service.status.value)
            self.status_labels[name] = status_var
            status_label = ttk.Label(status_frame, textvariable=status_var, width=12)
            status_label.grid(row=idx, column=1, padx=5, pady=5)

            pid_var = tk.StringVar(value="")
            self.pid_labels[name] = pid_var
            pid_label = ttk.Label(status_frame, textvariable=pid_var, width=12)
            pid_label.grid(row=idx, column=2, padx=5, pady=5)

            start_btn = ttk.Button(
                status_frame,
                text="Start",
                command=lambda n=name: self._start_service(n),
            )
            start_btn.grid(row=idx, column=3, padx=5, pady=5)

            stop_btn = ttk.Button(
                status_frame,
                text="Stop",
                command=lambda n=name: self._stop_service(n),
                state=tk.DISABLED,
            )
            stop_btn.grid(row=idx, column=4, padx=5, pady=5)

            self.control_buttons[name] = {"start": start_btn, "stop": stop_btn}

        bulk_frame = ttk.Frame(status_frame)
        bulk_frame.grid(row=len(self.services), column=0, columnspan=5, pady=10)

        ttk.Button(bulk_frame, text="Start All", command=self._start_all).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Button(bulk_frame, text="Stop All", command=self._stop_all).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Button(
            bulk_frame, text="Clean DB Files", command=self._clean_db_files
        ).pack(side=tk.LEFT, padx=5)

        log_container = ttk.Frame(self.root)
        log_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_widgets = {}

        for idx, name in enumerate(self.services.keys()):
            column = ttk.LabelFrame(log_container, text=f"{name} Log", padding=5)
            column.grid(row=0, column=idx, sticky="nsew", padx=5, pady=5)

            log_container.columnconfigure(idx, weight=1)

        log_container.rowconfigure(0, weight=1)

        for idx, name in enumerate(self.services.keys()):
            column = log_container.grid_slaves(row=0, column=idx)[0]

            log_text = scrolledtext.ScrolledText(
                column, wrap=tk.WORD, font=("Courier", 9)
            )
            log_text.pack(fill=tk.BOTH, expand=True)

            clear_btn = ttk.Button(
                column, text="Clear", command=lambda w=log_text: w.delete(1.0, tk.END)
            )
            clear_btn.pack(pady=2)

            self.log_widgets[name] = log_text

    def _start_service(self, name: str):
        service = self.services[name]
        if service.start():
            self._update_button_state(name)

    def _stop_service(self, name: str):
        service = self.services[name]
        if service.stop():
            self._update_button_state(name)

    def _start_all(self):
        for name in self.services.keys():
            self._start_service(name)

    def _stop_all(self):
        for name in self.services.keys():
            self._stop_service(name)

    def _clean_db_files(self):
        db_json = self.base_path / "db.json"
        chroma_db = self.base_path / "chroma_db"

        deleted = []
        errors = []

        if db_json.exists():
            try:
                db_json.unlink()
                deleted.append("db.json")
            except Exception as e:
                errors.append(f"db.json: {e}")

        if chroma_db.exists():
            try:
                shutil.rmtree(chroma_db)
                deleted.append("chroma_db/")
            except Exception as e:
                errors.append(f"chroma_db: {e}")

        if deleted:
            messagebox.showinfo("Cleanup Complete", f"Deleted: {', '.join(deleted)}")
        elif errors:
            messagebox.showerror("Cleanup Error", "\n".join(errors))
        else:
            messagebox.showinfo("Cleanup", "No files to delete")

    def _update_button_state(self, name: str):
        service = self.services[name]
        buttons = self.control_buttons[name]

        if service.status == ServiceStatus.RUNNING:
            buttons["start"].config(state=tk.DISABLED)
            buttons["stop"].config(state=tk.NORMAL)
        elif service.status == ServiceStatus.STOPPING:
            buttons["start"].config(state=tk.DISABLED)
            buttons["stop"].config(state=tk.DISABLED)
        elif service.status == ServiceStatus.STARTING:
            buttons["start"].config(state=tk.DISABLED)
            buttons["stop"].config(state=tk.DISABLED)
        else:
            buttons["start"].config(state=tk.NORMAL)
            buttons["stop"].config(state=tk.DISABLED)

    def _update_logs(self):
        for name, service in self.services.items():
            # Retrieve and display logs
            while not service.log_queue.empty():
                try:
                    log_line = service.log_queue.get_nowait()
                    self.log_widgets[name].insert(tk.END, log_line)
                    self.log_widgets[name].see(tk.END)
                except queue.Empty:
                    break

            # Update status and PID
            if service.is_running():
                service.status = ServiceStatus.RUNNING
                if service.process:
                    self.pid_labels[name].set(f"PID: {service.process.pid}")
            else:
                if service.status not in [
                    ServiceStatus.STOPPING,
                    ServiceStatus.STARTING,
                ]:
                    self.pid_labels[name].set("")

            self.status_labels[name].set(service.status.value)
            self._update_button_state(name)

        self.root.after(100, self._update_logs)

    def cleanup(self):
        """Cleanup on application exit"""
        for service in self.services.values():
            if service.is_running():
                service.stop()

        # Wait a bit for all services to stop
        max_wait = 50  # 5 seconds
        for _ in range(max_wait):
            all_stopped = all(
                not service.is_running() and not service.is_stopping
                for service in self.services.values()
            )
            if all_stopped:
                break
            time.sleep(0.1)


def main():
    root = tk.Tk()
    app = ManagerGUI(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    # Handle window close button
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Handle Ctrl+C and kill signals
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, cleaning up...")
        app.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Register cleanup for atexit (catches most exit scenarios)
    atexit.register(app.cleanup)

    root.mainloop()


if __name__ == "__main__":
    main()
