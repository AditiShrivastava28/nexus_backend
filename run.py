"""
NexusHR Application Runner.

This script starts the uvicorn server to run the NexusHR FastAPI application.
"""

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
