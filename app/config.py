"""Settings for RESCUEGRID.

Right now the only setting is where the SQLite database file is stored.
"""

import os
from pathlib import Path

# BASE_DIR is the project folder (/home/linux1/rescuegrid).
BASE_DIR = Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    """Return the path of the SQLite database file.

    Normally it is <project>/data/rescuegrid.db.
    Tests set the RESCUEGRID_DB_PATH environment variable so they use a
    temporary file instead of the real one.
    """
    override = os.environ.get("RESCUEGRID_DB_PATH")
    if override:
        return Path(override)
    return BASE_DIR / "data" / "rescuegrid.db"