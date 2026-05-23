Set-Location "$PSScriptRoot\.."
.\.venv\Scripts\python -m uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000
