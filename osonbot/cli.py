import logging
import sys
import time
import subprocess
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartOnChange(FileSystemEventHandler):
    """Restarts a subprocess when the target file is modified."""

    def __init__(self, file):
        self.file = str(Path(file).resolve())
        self.process = None
        self.run_file()

    def run_file(self):
        if self.process is not None and self.process.poll() is None:
            print(f"Terminating process {self.process.pid}...")
            self.process.terminate()
            self.process.wait()

        print(f"Running {self.file}...")
        try:
            self.process = subprocess.Popen([sys.executable, self.file])
        except Exception as e:
            print(f"Error running file: {e}", file=sys.stderr)
            self.process = None

    def on_modified(self, event):
        if str(Path(event.src_path).resolve()) == self.file:
            print(f"⚡ Change detected in {self.file}, restarting...")
            self.run_file()

def watcher(file: str):
    file_path = Path(file).resolve()
    path_to_watch = str(file_path.parent)

    logging.info(f"Watching {path_to_watch} for changes to {file_path.name}...")

    event_handler = RestartOnChange(file_path)

    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process and event_handler.process.poll() is None:
            print(f"Terminating final process {event_handler.process.pid}...")
            event_handler.process.terminate()
            event_handler.process.wait()
    
    observer.join()
    print("Watcher stopped")

def main():
    parser = argparse.ArgumentParser(
        description="Automatically restart a Python script when it's modified."
    )
    parser.add_argument(
        "file",
        metavar="FILE",
        type=str,
        help="The Python script to watch."
    )
    args = parser.parse_args()

    file_to_watch = Path(args.file)

    if not file_to_watch.exists():
        logging.error(f"Error: File not found at {file_to_watch.resolve()}", exc_info=True)
        sys.exit(1)
    
    if not file_to_watch.is_file():
        logging.error(f"Error: Path is not a file: {file_to_watch.resolve()}", exc_info=True)
        sys.exit(1)

    watcher(args.file)

if __name__ == "__main__":
    main()
