import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from google.adk.cli.fast_api import get_fast_api_app

app = get_fast_api_app(
    agents_dir=os.path.dirname(os.path.abspath(__file__)),
    session_service_uri=os.environ.get("SESSION_SERVICE_URI"),
    web=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fix: prevents /openapi.json crash caused by httpx.Client schema issue
def custom_openapi():
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Competitive Intelligence A2A Host",
            "version": "1.0.0",
        },
        "paths": {},
    }

app.openapi = custom_openapi

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
    
