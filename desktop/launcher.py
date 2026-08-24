from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path


def _bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])).resolve()


def _install_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _data_root() -> Path:
    configured = os.environ.get("FINCOMPILER_DATA_DIR")
    path = Path(configured).resolve() if configured else _install_root() / "FinCompiler Data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _server_command(port: int) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--server", str(port)]
    return [sys.executable, str(Path(__file__).resolve()), "--server", str(port)]


def _available_port() -> int:
    for port in range(8511, 8531):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            try:
                candidate.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No local port is available between 8511 and 8530.")


def _server_ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
            return response.status == 200
    except OSError:
        return False


def _run_server(port: int) -> int:
    resource_root = _bundle_root()
    data_root = _data_root()
    log_path = data_root / "fincompiler-server.log"
    log_handle = log_path.open("a", encoding="utf-8", buffering=1)
    sys.stdout = log_handle
    sys.stderr = log_handle
    os.environ["FINCOMPILER_RESOURCE_DIR"] = str(resource_root)
    os.environ["FINCOMPILER_DATA_DIR"] = str(data_root)
    os.chdir(resource_root)
    app = resource_root / "apps" / "web.py"
    sys.argv = [
        "streamlit",
        "run",
        str(app),
        "--global.developmentMode=false",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--server.headless=true",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]
    from streamlit.web import cli as streamlit_cli

    return int(streamlit_cli.main() or 0)


class Launcher:
    def __init__(self) -> None:
        import tkinter as tk
        from tkinter import messagebox

        self.tk = tk
        self.messagebox = messagebox
        self.root = tk.Tk()
        self.root.title("FinCompiler")
        self.root.geometry("430x230")
        self.root.resizable(False, False)
        self.process: subprocess.Popen | None = None
        self.port: int | None = None
        self.url: str | None = None
        self.status = tk.StringVar(value="Starting the local Finance workspace…")
        tk.Label(self.root, text="FinCompiler", font=("Segoe UI", 22, "bold")).pack(pady=(24, 4))
        tk.Label(self.root, text="Local-first month-end reconciliation", font=("Segoe UI", 10)).pack()
        tk.Label(self.root, textvariable=self.status, wraplength=380, justify="center", font=("Segoe UI", 10)).pack(pady=18)
        self.open_button = tk.Button(self.root, text="Open FinCompiler", width=20, state="disabled", command=self.open_browser)
        self.open_button.pack()
        tk.Button(self.root, text="Stop and close", width=20, command=self.close).pack(pady=8)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self) -> None:
        try:
            self.port = _available_port()
            self.url = f"http://127.0.0.1:{self.port}"
            env = dict(os.environ)
            env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
            env["FINCOMPILER_RESOURCE_DIR"] = str(_bundle_root())
            env["FINCOMPILER_DATA_DIR"] = str(_data_root())
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.process = subprocess.Popen(
                _server_command(self.port),
                cwd=_install_root(),
                env=env,
                creationflags=creation_flags,
            )
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError(f"The local server stopped with code {self.process.returncode}.")
                if _server_ready(self.port):
                    self.root.after(0, self.ready)
                    return
                time.sleep(0.25)
            raise RuntimeError("FinCompiler did not become ready within 45 seconds.")
        except Exception as exc:
            self.root.after(0, lambda: self.failed(str(exc)))

    def ready(self) -> None:
        self.status.set(f"Ready on this computer · {self.url}\nClosing this window will stop FinCompiler.")
        self.open_button.config(state="normal")
        self.open_browser()

    def failed(self, message: str) -> None:
        self.status.set("FinCompiler could not start. No source files were changed.")
        self.messagebox.showerror("FinCompiler", f"{message}\n\nSee 'FinCompiler Data\\fincompiler-server.log' for details.")

    def open_browser(self) -> None:
        if self.url:
            webbrowser.open(self.url, new=2)

    def close(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--server":
        return _run_server(int(sys.argv[2]))
    Launcher().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
