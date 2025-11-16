# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import asyncio
import base64
import warnings
import logging

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first, before other imports
load_dotenv()

from google.genai.types import (
    Part,
    Content,
    Blob,
)

from google.adk.runners import InMemoryRunner, Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.genai import types

from fastapi import FastAPI, WebSocket, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.websockets import WebSocketDisconnect
import shutil
from google_search_agent.agent import live_agent
from rag_agent.agent import rag_agent
from rag_agent.knowledge_base import KnowledgeBaseManager

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", message="there are non-text parts in the response")

# Reduce ADK logging verbosity (suppress "non-text parts" warnings)
logging.getLogger('google.genai').setLevel(logging.ERROR)
logging.getLogger('google.adk').setLevel(logging.ERROR)

#
# ADK Streaming
#

APP_NAME = "FSM DEMO APP"

root_agent = live_agent


async def start_agent_session(user_id, is_audio=False):
    """Starts an agent session"""

    # Create a Runner (we'll reuse this for both live and detail agents)
    runner = InMemoryRunner(
        app_name=APP_NAME,
        agent=root_agent,
    )

    # Create a Session
    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,  # Replace with actual user ID
    )

    # Set response modalities - AUDIO only is sufficient for transcript
    if is_audio:
        modalities = ["AUDIO"]  # AUDIO modality with output_audio_transcription provides both audio and transcript
    else:
        modalities = ["TEXT"]  # Text only for text mode
    
    # Configure RunConfig with audio transcription
    
    run_config = RunConfig(
        response_modalities=modalities,
        # Enable transcription for agent's speech output
        output_audio_transcription=types.AudioTranscriptionConfig() if is_audio else None,
        # Enable transcription for user's speech input
        input_audio_transcription=types.AudioTranscriptionConfig() if is_audio else None,
    )

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Start agent session
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue, session, runner


async def agent_to_client_messaging(websocket, live_events, session, is_audio, runner):
    """Agent to client communication"""
    # Accumulators for full transcripts
    full_input_transcript = ""
    full_output_transcript = ""
    
    async for event in live_events:
        # Check for input transcription (transcript of user's audio speech)
        if event.input_transcription:
            # input_transcription might be an object with a 'text' attribute
            if hasattr(event.input_transcription, 'text'):
                input_text = event.input_transcription.text
            else:
                input_text = str(event.input_transcription)
            
            if input_text:
                # Accumulate full transcript
                full_input_transcript += input_text
                
                message = {
                    "mime_type": "text/plain",
                    "data": input_text,
                    "partial": event.partial,
                    "is_input_transcript": True
                }
                await websocket.send_text(json.dumps(message))
                print(f"[USER INPUT TRANSCRIPT]: {input_text}")
        
        # Check for output transcription (transcript of agent's audio speech)
        if event.output_transcription:
            # output_transcription might be an object with a 'text' attribute
            if hasattr(event.output_transcription, 'text'):
                transcript_text = event.output_transcription.text
            else:
                transcript_text = str(event.output_transcription)
            
            if transcript_text:
                # Accumulate full transcript
                full_output_transcript += transcript_text
                
                message = {
                    "mime_type": "text/plain",
                    "data": transcript_text,
                    "partial": event.partial,
                    "is_output_transcript": True
                }
                await websocket.send_text(json.dumps(message))
                print(f"[AGENT OUTPUT TRANSCRIPT]: {transcript_text}")

        # If the turn complete or interrupted, trigger detail agent
        if event.turn_complete or event.interrupted:
            message = {
                "turn_complete": event.turn_complete,
                "interrupted": event.interrupted,
            }
            await websocket.send_text(json.dumps(message))
            print(f"[AGENT TO CLIENT]: {message}")
            continue

        # Read the Content and its first Part
        part: Part = (
            event.content and event.content.parts and event.content.parts[0]
        )
        if not part:
            continue

        # If it's audio, send Base64 encoded audio data
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

        # If it's text (partial or complete), send it
        if part.text:
            message = {
                "mime_type": "text/plain",
                "data": part.text,
                "partial": event.partial,
                "is_transcript": False  # This is regular text, not transcript
            }
            await websocket.send_text(json.dumps(message))
            print(f"[AGENT TO CLIENT]: text/plain: {part.text[:100]}...")


async def client_to_agent_messaging(websocket, live_request_queue):
    """Client to agent communication"""
    try:
        while True:
            # Decode JSON message
            message_json = await websocket.receive_text()
            message = json.loads(message_json)
            mime_type = message["mime_type"]
            data = message["data"]

            # Send the message to the agent
            if mime_type == "text/plain":
                # Send a text message
                content = Content(role="user", parts=[Part.from_text(text=data)])
                live_request_queue.send_content(content=content)
                print(f"[CLIENT TO AGENT]: {data}")
            elif mime_type == "audio/pcm":
                # Send an audio data
                decoded_data = base64.b64decode(data)
                live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
            else:
                raise ValueError(f"Mime type not supported: {mime_type}")
    except WebSocketDisconnect:
        print("[CLIENT TO AGENT] WebSocket disconnected (normal)")
    except Exception as e:
        print(f"[CLIENT TO AGENT ERROR]: {e}")


#
# FastAPI web app
#

app = FastAPI()

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# knowledge_base = KnowledgeBaseManager()

# @app.post("/upload-pdf")
# async def upload_pdf(file: UploadFile = File(...)):
#     """Uploads a PDF document to the knowledge base."""
#     print(f"Received request to upload file: {file.filename}")
#     if file.content_type != "application/pdf":
#         print(f"Invalid file type: {file.content_type}")
#         return {"message": "Only PDF files are allowed."}, 400
#     try:
#         # Save the uploaded file to the downloads directory
#         file_path = os.path.join("app/downloads", file.filename)
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#         print(f"Saved file to {file_path}")

#         # Rebuild the knowledge base index
#         knowledge_base.build_index()
#         print("Knowledge base index rebuilt successfully.")

#         return {"message": f"File '{file.filename}' uploaded and indexed successfully."}
#     except Exception as e:
#         print(f"Error uploading file: {e}")
#         return {"message": f"Error uploading file: {e}"}, 500

@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, is_audio: str):
    """Client websocket endpoint"""

    # Wait for client connection
    await websocket.accept()
    print(f"Client #{user_id} connected, audio mode: {is_audio}")

    # Start agent session
    user_id_str = str(user_id)
    is_audio_mode = (is_audio == "true")
    live_events, live_request_queue, session, runner = await start_agent_session(user_id_str, is_audio_mode)

    # Start tasks
    agent_to_client_task = asyncio.create_task(
        agent_to_client_messaging(websocket, live_events, session, is_audio_mode, runner)
    )
    client_to_agent_task = asyncio.create_task(
        client_to_agent_messaging(websocket, live_request_queue)
    )

    # Wait until the websocket is disconnected or an error occurs
    try:
        tasks = [agent_to_client_task, client_to_agent_task]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Check if any task had an exception (other than WebSocketDisconnect)
        for task in done:
            try:
                task.result()
            except WebSocketDisconnect:
                # Normal disconnection, not an error
                pass
            except Exception as e:
                print(f"[WEBSOCKET ERROR] Task failed: {e}")
    finally:
        # Close LiveRequestQueue
        live_request_queue.close()
        
        # Disconnected
        print(f"Client #{user_id} disconnected")
