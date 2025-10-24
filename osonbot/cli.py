import typer
import subprocess
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = typer.Typer()

class RestartOnChange(FileSystemEventHandler):
    def __init__(self, file):
        self.file = str(Path(file).resolve())
        self.process = None
        self.run_file()

    def run_file(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        print(f"▶️ Running {self.file}...")
        self.process = subprocess.Popen([sys.executable, self.file])

    def on_modified(self, event):
        if str(Path(event.src_path).resolve()) == self.file:
            print(f"⚡ Change detected in {self.file}, restarting...")
            self.run_file()


def watcher(file: str):
    file_path = Path(file).resolve()

    if not file_path.exists():
        typer.echo(f"❌ File not found: {file_path}")
        raise typer.Exit(code=1)

    event_handler = RestartOnChange(file_path)
    observer = Observer()
    observer.schedule(event_handler, str(file_path.parent), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process and event_handler.process.poll() is None:
            event_handler.process.terminate()
    observer.join()


@app.command()
def run(file: str = typer.Argument(..., help="Python file to run and watch for changes")):
    """Run the given Python file and restart it when changed."""
    typer.echo(f"🚀 Watching {file} for changes...")
    watcher(file)


if __name__ == "__main__":
    app()
