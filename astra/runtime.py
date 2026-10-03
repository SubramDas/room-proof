"""Progress output must not abort a computation when a terminal disconnects."""
from pathlib import Path
import sys,threading


class ResilientLogStream:
    def __init__(self,stream,log):
        self.stream=stream;self.log=log;self.disconnected=False;self.lock=threading.Lock()
    @property
    def encoding(self):return getattr(self.stream,'encoding','utf-8')
    def write(self,text):
        with self.lock:
            self.log.write(text);self.log.flush()
            if not self.disconnected:
                try:self.stream.write(text);self.stream.flush()
                except (BrokenPipeError,ValueError):self.disconnected=True
        return len(text)
    def flush(self):
        self.log.flush()
        if not self.disconnected:
            try:self.stream.flush()
            except (BrokenPipeError,ValueError):self.disconnected=True
    def isatty(self):return False
    def fileno(self):return self.stream.fileno()


def install_progress_log(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    log=path.open('a',buffering=1)
    sys.stdout=ResilientLogStream(sys.stdout,log);sys.stderr=ResilientLogStream(sys.stderr,log)
