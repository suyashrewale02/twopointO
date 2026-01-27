import subprocess
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CodeReloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_app()
    
    def start_app(self):
        """Start the query app."""
        if self.process:
            self.process.terminate()
            self.process.wait()
        self.process = subprocess.Popen([sys.executable, "-c", 
            "from api.query import run_query_loop; run_query_loop()"])
    
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"\n[Reloading: {event.src_path}]\n")
            self.start_app()

def main():
    """Watch for code changes and reload."""
    handler = CodeReloadHandler()
    observer = Observer()
    observer.schedule(handler, path=".", recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if handler.process:
            handler.process.terminate()
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
