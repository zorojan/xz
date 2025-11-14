# Simple main.py without RAG functionality for testing
import os
import json
import asyncio
import base64
import warnings
import logging

from pathlib import Path
from dotenv import load_dotenv

from google.genai.types import (
    Part,
    Content,
    Blob,
)

from google.adk.runners import InMemoryRunner, Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.genai import types

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.websockets import WebSocketDisconnect

from google_search_agent.agent import live_agent

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", message="there are non-text parts in the response")

# Reduce ADK logging verbosity (suppress "non-text parts" warnings)
logging.getLogger('google.genai').setLevel(logging.ERROR)
logging.getLogger('google.adk').setLevel(logging.ERROR)

# Load Gemini API Key
load_dotenv()

APP_NAME = "ADK STREAMING APP"

root_agent = live_agent

async def start_agent_session(user_id, is_audio=False):
    """Starts an agent session"""
    runner = InMemoryRunner(
        app_name=APP_NAME,
        agent=root_agent,
    )

    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
    )

    if is_audio:
        modalities = ["AUDIO"]
    else:
        modalities = ["TEXT"]
    
    run_config = RunConfig(
        response_modalities=modalities,
        output_audio_transcription=types.AudioTranscriptionConfig() if is_audio else None,
        input_audio_transcription=types.AudioTranscriptionConfig() if is_audio else None,
    )

    live_request_queue = LiveRequestQueue()

    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue, session, runner

async def agent_to_client_messaging(websocket, live_events, session, is_audio, runner):
    """Agent to client communication"""
    async for event in live_events:
        if event.input_transcription:
            if hasattr(event.input_transcription, 'text'):
                input_text = event.input_transcription.text
            else:
                input_text = str(event.input_transcription)
            
            if input_text:
                message = {
                    "mime_type": "text/plain",
                    "data": input_text,
                    "partial": event.partial,
                    "is_input_transcript": True
                }
                await websocket.send_text(json.dumps(message))
                print(f"[USER INPUT TRANSCRIPT]: {input_text}")
        
        if event.output_transcription:
            if hasattr(event.output_transcription, 'text'):
                transcript_text = event.output_transcription.text
            else:
                transcript_text = str(event.output_transcription)
            
            if transcript_text:
                message = {
                    "mime_type": "text/plain",
                    "data": transcript_text,
                    "partial": event.partial,
                    "is_output_transcript": True
                }
                await websocket.send_text(json.dumps(message))
                print(f"[AGENT OUTPUT TRANSCRIPT]: {transcript_text}")

        if event.turn_complete or event.interrupted:
            message = {
                "turn_complete": event.turn_complete,
                "interrupted": event.interrupted,
            }
            await websocket.send_text(json.dumps(message))
            print(f"[AGENT TO CLIENT]: {message}")
            continue

        part: Part = (
            event.content and event.content.parts and event.content.parts[0]
        )
        if not part:
            continue

        is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
        if is_audio:
            audio_data = part.inline_data and part.inline_data.data
            if audio_data:
                message = {
                    "mime_type": "audio/pcm",
                    "data": base64.b64encode(audio_data).decode("ascii")
                }
                await websocket.send_text(json.dumps(message))
                print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")
                continue

        if part.text:
            message = {
                "mime_type": "text/plain",
                "data": part.text,
                "partial": event.partial,
                "is_transcript": False
            }
            await websocket.send_text(json.dumps(message))
            print(f"[AGENT TO CLIENT]: text/plain: {part.text[:100]}...")

async def client_to_agent_messaging(websocket, live_request_queue):
    """Client to agent communication"""
    try:
        while True:
            message_json = await websocket.receive_text()
            message = json.loads(message_json)
            mime_type = message["mime_type"]
            data = message["data"]

            if mime_type == "text/plain":
                content = Content(role="user", parts=[Part.from_text(text=data)])
                live_request_queue.send_content(content=content)
                print(f"[CLIENT TO AGENT]: {data}")
            elif mime_type == "audio/pcm":
                decoded_data = base64.b64decode(data)
                live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
            else:
                raise ValueError(f"Mime type not supported: {mime_type}")
    except WebSocketDisconnect:
        print("[CLIENT TO AGENT] WebSocket disconnected (normal)")
    except Exception as e:
        print(f"[CLIENT TO AGENT ERROR]: {e}")

# FastAPI web app
app = FastAPI()

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, is_audio: str):
    """Client websocket endpoint"""
    await websocket.accept()
    print(f"Client #{user_id} connected, audio mode: {is_audio}")

    user_id_str = str(user_id)
    is_audio_mode = (is_audio == "true")
    live_events, live_request_queue, session, runner = await start_agent_session(user_id_str, is_audio_mode)

    agent_to_client_task = asyncio.create_task(
        agent_to_client_messaging(websocket, live_events, session, is_audio_mode, runner)
    )
    client_to_agent_task = asyncio.create_task(
        client_to_agent_messaging(websocket, live_request_queue)
    )

    try:
        tasks = [agent_to_client_task, client_to_agent_task]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        for task in done:
            try:
                task.result()
            except WebSocketDisconnect:
                pass
            except Exception as e:
                print(f"[WEBSOCKET ERROR] Task failed: {e}")
    finally:
        live_request_queue.close()
        print(f"Client #{user_id} disconnected")