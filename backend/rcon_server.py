#!/usr/bin/env python3

import os
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from mcrcon import MCRcon
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

RCON_HOST = os.getenv("RCON_HOST", "localhost")
RCON_PORT = int(os.getenv("RCON_PORT", 27015))  # Default Factorio RCON port
RCON_PASSWORD = os.getenv("RCON_PASSWORD", "")
API_KEY = os.getenv("API_KEY")

if not RCON_PASSWORD:
    raise ValueError("Please set RCON_PASSWORD environment variable")

if not API_KEY:
    raise ValueError("Please set API_KEY environment variable")

api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

class CommandRequest(BaseModel):
    command: str

@app.post("/execute_command")
async def execute_command(command_request: CommandRequest, api_key: str = Depends(get_api_key)):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(command_request.command)
        return {"result": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing command: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Factorio RCON Server is running. Use POST /execute_command to send commands."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
