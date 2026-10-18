# RESCUEGRID — Windows PC and IBM LinuxONE

## Windows PC setup

Requirements: Windows 10/11 64-bit and Python 3.11 or 3.12 from python.org. During Python setup, enable **Add Python to PATH**.

1. Extract this project ZIP to a folder such as `C:\Users\YourName\Projects\rescuegrid`.
2. Open the extracted `rescuegrid` folder.
3. Double-click `run_windows.bat`. On first run it creates `.venv`, installs packages from `requirements.txt`, and starts FastAPI.
4. Open `http://127.0.0.1:8000/` in your browser. API docs are at `http://127.0.0.1:8000/docs`; health check is `http://127.0.0.1:8000/health`.
5. Leave the terminal open while using the app. Press Ctrl+C in that terminal to stop it.

If the automatic install fails, open Command Prompt in the project folder and run:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The app's SQLite database is created under the project data directory. Keep that folder if you want to preserve local donations. The Windows database is separate from the LinuxONE database unless you explicitly move/export data.

## IBM LinuxONE setup

Use the existing server virtual environment and compatible `s390x` scientific packages. The LinuxONE system may need Ubuntu packages for NumPy/SciPy/scikit-learn instead of pip wheels. Do not force an incompatible build.

```bash
cd /home/linux1/shared/rescuegrid
source /home/linux1/rescuegrid/venv/bin/activate
python -c "import fastapi, sklearn, scipy, numpy; print(fastapi.__version__, sklearn.__version__, scipy.__version__, numpy.__version__)"
python -m pytest -v
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Notes

- The frontend is served by FastAPI. Do not open `frontend/index.html` directly from File Explorer.
- Windows x64 and LinuxONE `s390x` use different Python environments; the same source code is intended to run on both, but each environment must be tested.
- Keep `data/` and your existing database when updating the project. Do not put credentials or API keys in source files.
- The demo profiles are synthetic; food safety uses explicit rules and human review; urgency metrics are based on synthetic examples; demo sign-in is not production authentication.
- For an optional OpenAI-compatible assistant endpoint, configure `RESCUEGRID_LLM_BASE_URL`, `RESCUEGRID_LLM_MODEL`, and optionally `RESCUEGRID_LLM_API_KEY` as environment variables. Do not commit keys.
