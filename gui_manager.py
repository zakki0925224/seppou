import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import queue
from pathlib import Path
from enum import Enum
from typing import Optional, Dict
import shutil


class ServiceStatus(Enum):
    STOPPED = "Stopped"
    RUNNING = "Running"
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

    def start(self) -> bool:
        if self.process and self.process.poll() is None:
            return False

        try:
            self.process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self.reader_thread.start()

            self.status = ServiceStatus.RUNNING
            return True
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.log_queue.put(f"Start error: {e}\n")
            return False

    def stop(self) -> bool:
        if not self.process or self.process.poll() is not None:
            return False

        try:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.status = ServiceStatus.STOPPED
            return True
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.status = ServiceStatus.STOPPED
            return True
        except Exception as e:
            self.log_queue.put(f"Stop error: {e}\n")
            return False

    def is_running(self) -> bool:
        if self.process and self.process.poll() is None:
            return True
        if self.process and self.process.poll() is not None:
            self.status = ServiceStatus.STOPPED
        return False

    def _read_output(self):
        if not self.process or not self.process.stdout:
            return

        for line in iter(self.process.stdout.readline, ""):
            if line:
                self.log_queue.put(line)

        if self.process.poll() is not None:
            self.status = ServiceStatus.STOPPED


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
            status_label = ttk.Label(status_frame, textvariable=status_var, width=10)
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
            self.log_widgets[name].insert(tk.END, f"[{name}] Started\n")
            self.log_widgets[name].see(tk.END)
            self._update_button_state(name)

    def _stop_service(self, name: str):
        service = self.services[name]
        if service.stop():
            self.log_widgets[name].insert(tk.END, f"[{name}] Stopped\n")
            self.log_widgets[name].see(tk.END)
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

        if service.is_running():
            buttons["start"].config(state=tk.DISABLED)
            buttons["stop"].config(state=tk.NORMAL)
        else:
            buttons["start"].config(state=tk.NORMAL)
            buttons["stop"].config(state=tk.DISABLED)

    def _update_logs(self):
        for name, service in self.services.items():
            while not service.log_queue.empty():
                try:
                    log_line = service.log_queue.get_nowait()
                    self.log_widgets[name].insert(tk.END, log_line)
                    self.log_widgets[name].see(tk.END)
                except queue.Empty:
                    break

            if service.is_running():
                service.status = ServiceStatus.RUNNING
                if service.process:
                    self.pid_labels[name].set(f"PID: {service.process.pid}")
            else:
                self.pid_labels[name].set("")
            self.status_labels[name].set(service.status.value)
            self._update_button_state(name)

        self.root.after(100, self._update_logs)

    def cleanup(self):
        for service in self.services.values():
            service.stop()


def main():
    root = tk.Tk()
    app = ManagerGUI(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
