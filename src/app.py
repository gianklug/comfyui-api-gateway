#!/usr/bin/env python3

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import logging
import httpx
import os
import secrets
import json
import websocket
import urllib
import random
import base64

app = FastAPI()
security = HTTPBasic()
logging.basicConfig(level=logging.DEBUG)

# Authentication
USER = os.environ.get("USERNAME", "default")
PASSWORD = os.environ.get("PASSWORD", secrets.token_urlsafe(20))
logging.info(f"API credentials: {USER}:{PASSWORD}")

# ComfyUI related things
WORKFLOW_PATH = os.environ.get("WORKFLOW_PATH", "workflow_demo.json")
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://localhost:8188")
CLIENT_ID = os.environ.get("CLIENT_ID", "comfyui")
# Workflow config
POSITIVE_PROMPT_INPUT_ID = os.environ.get("POSITIVE_PROMPT_INPUT_ID", "6")
NEGATIVE_PROMPT_INPUT_ID = os.environ.get("NEGATIVE_PROMPT_INPUT_ID", "7")
SEEED_PROMPT_INPUT_ID    = os.environ.get("SEED_PROMPT_INPUT_ID", "3")

# Loading the workflow
if not os.path.isfile(WORKFLOW_PATH):
    raise Exception(f"Workflow file not found: {WORKFLOW_PATH}")
try:
    WORKFLOW = json.load(open(WORKFLOW_PATH, "r"))
except json.JSONDecodeError:
    raise Exception(f"Workflow file is not valid JSON: {WORKFLOW_PATH}")

# Basic auth
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USER or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# Generate route
@app.post("/generate")
async def generate(positive_prompt: str, negative_prompt: str = "text, watermark", seed: int = -1, authenticated: bool = Depends(verify_credentials)):
    if not authenticated:
        raise HTTPException(status_code=401, detail="Unauthenticated.")
    # Seeding
    if seed == -1:
        seed = random.randint(0, 1000000)
    # Set up prompt config
    WORKFLOW[POSITIVE_PROMPT_INPUT_ID]["inputs"]["text"] = positive_prompt
    WORKFLOW[NEGATIVE_PROMPT_INPUT_ID]["inputs"]["text"] = negative_prompt
    WORKFLOW[SEEED_PROMPT_INPUT_ID]["inputs"]["seed"] = seed
    logging.debug(f"Prompt config: {WORKFLOW}")
    # Request generation
    queue = httpx.post(f"{COMFYUI_URL}/prompt", json={"prompt": WORKFLOW}).json()
    # Wait for generation to complete
    ws = websocket.WebSocket()
    ws.connect(f"{COMFYUI_URL.replace('http','ws')}/ws?clientId={CLIENT_ID}")
    while True:
        result = ws.recv()
        if not isinstance(result, str):
            continue
        logging.debug(f"Received: {result}")
        result = json.loads(result)
        if result["type"] == "status":
            if result["data"]["status"]["exec_info"]["queue_remaining"] == 0:
                break
        if result["type"] != "executing":
            continue
        data = result["data"]
        if data["node"] is None and data["prompt_id"] == queue["prompt_id"]:
            break
    # Get history
    history = httpx.get(f"{COMFYUI_URL}/history/{queue['prompt_id']}").json()[queue["prompt_id"]]
    logging.debug(history)
    for node_id in history["outputs"]:
        node_output = history["outputs"][node_id]
        if 'images' not in node_output:
            continue
        images_output = []
        # Get images
        for image in node_output["images"]:
            data = {"filename": image["filename"], "subfolder": image["subfolder"], "type": image["type"]}
            url_values = urllib.parse.urlencode(data)
            image_data = httpx.get(f"{COMFYUI_URL}/view?{url_values}").content
            images_output.append(base64.b64encode(image_data))
    return {"images": images_output}
