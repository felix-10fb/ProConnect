import uvicorn
import os
import sys

# Configure UTF-8 encoding for Windows console
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print("================================================================")
    print(">>> DTM-CHATSPACE AI-INTEGRATED COMMUNICATION PLATFORM STARTING")
    print(f">>> Server URL: http://localhost:{port}")
    print(f">>> API Documentation: http://localhost:{port}/docs")
    print("================================================================")
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)
