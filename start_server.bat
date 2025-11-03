@echo off
echo === Clara Server Startup ===
echo.
echo Location: D:\lean\clara-server (STANDALONE REPO)
echo.
cd /d "D:\lean\clara-server"
echo Starting Clara Server on port 3000...
uv run python -m uvicorn main:app --port 3000 --host 0.0.0.0 --reload
