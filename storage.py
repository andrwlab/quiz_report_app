"""Local snapshot adapter. Atomic replacement keeps the previous publication on failure."""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


class LocalStore:
    def __init__(self, directory=None):
        self.directory = Path(directory or os.environ.get('SABIS_DATA_DIR', 'private_data'))

    def read(self):
        path = self.directory / 'published.json'
        return json.loads(path.read_text()) if path.exists() else None

    def publish(self, records, roster):
        snapshot = dict(version=1, updated_at=datetime.now(ZoneInfo('America/Panama')).isoformat(), records=records, roster=roster)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, name = tempfile.mkstemp(dir=self.directory, suffix='.tmp')
        try:
            with os.fdopen(descriptor, 'w') as output:
                json.dump(snapshot, output, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, self.directory / 'published.json')
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return snapshot
