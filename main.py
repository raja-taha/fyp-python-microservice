from fastapi import FastAPI, HTTPException, Response, UploadFile, File, Form
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from typing import Dict, List, Optional, Tuple
import whisper
from googletrans import Translator
import os
import tempfile
import shutil
import traceback
import logging
import subprocess
import httpx
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Translation Microservice",
    description="A microservice for translating text between different languages",
    version="1.0.0"
)
model = whisper.load_model("base")  # or "small"/"medium" depending on accuracy/speed

class TranslationRequest(BaseModel):
    text: str
    target_language: str
    source_language: Optional[str] = None

class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    detected_language: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message"""
    return Response(content="Welcome to the Translation Microservice API!", media_type="text/plain")

@app.get("/languages", response_model=Dict[str, str])
async def get_supported_languages():
    """Get all supported languages and their codes"""
    return GoogleTranslator().get_supported_languages(as_dict=True)

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Translate text from source language to target language"""
    try:
        # If source language is not provided, use 'auto' for automatic detection
        source_lang = request.source_language if request.source_language else 'auto'
        
        translator = GoogleTranslator(
            source=source_lang,
            target=request.target_language
        )
        
        translated_text = translator.translate(request.text)
        
        # If source language was auto-detected, try to get the detected language
        detected_language = None
        if source_lang == 'auto':
            try:
                # Create a new translator instance to detect the language
                detector = GoogleTranslator(source='auto', target='en')
                detected_language = detector.detect(request.text).lang
            except:
                detected_language = "unknown"
        
        return TranslationResponse(
            translated_text=translated_text,
            source_language=source_lang,
            target_language=request.target_language,
            detected_language=detected_language
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def check_ffmpeg() -> Tuple[bool, str]:
    """Check if ffmpeg is installed and available in PATH"""
    try:
        # Run ffmpeg -version and capture output
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=False
        )
        if result.returncode == 0:
            version_info = result.stdout.strip().split('\n')[0]
            return True, version_info
        else:
            return False, f"ffmpeg check failed with code {result.returncode}: {result.stderr}"
    except FileNotFoundError:
        return False, "ffmpeg not found in PATH"
    except Exception as e:
        return False, f"Error checking ffmpeg: {str(e)}"

@app.get("/check-ffmpeg")
async def ffmpeg_status():
    """Check if ffmpeg is installed and available"""
    is_available, message = check_ffmpeg()
    if is_available:
        return {"status": "available", "message": message}
    else:
        return {"status": "unavailable", "message": message}

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), target_lang: str = Form(...)):
    """
    Transcribe audio and translate the transcription to the target language.
    Requires ffmpeg to be installed and available in the system path.
    """
    try:
        # Log request details
        logger.info(f"Received transcription request. File: {audio.filename}, Target language: {target_lang}")
        
        # Check if ffmpeg is available
        is_ffmpeg_available, ffmpeg_message = check_ffmpeg()
        if not is_ffmpeg_available:
            logger.error(f"ffmpeg check failed: {ffmpeg_message}")
            raise HTTPException(
                status_code=500, 
                detail=f"ffmpeg is required but not available: {ffmpeg_message}"
            )
        else:
            logger.info(f"ffmpeg check passed: {ffmpeg_message}")
        
        # Create a temporary directory to store the file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the uploaded file with the correct extension
            file_extension = os.path.splitext(audio.filename)[1] if audio.filename else ".wav"
            temp_audio_path = os.path.join(temp_dir, f"temp_audio{file_extension}")
            logger.info(f"Saving audio to temporary path: {temp_audio_path}")
            
            # Read and save the uploaded audio file
            audio_bytes = await audio.read()
            with open(temp_audio_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"Saved {len(audio_bytes)} bytes to temporary file")
            
            # Check if the file exists and log its size
            if os.path.exists(temp_audio_path):
                logger.info(f"File exists, size: {os.path.getsize(temp_audio_path)} bytes")
            else:
                logger.error("File was not created successfully")
                raise HTTPException(status_code=500, detail="Error saving audio file")
            
            # Transcribe with Whisper
            try:
                logger.info("Starting transcription with Whisper model")
                result = model.transcribe(temp_audio_path)
                text = result["text"]
                logger.info(f"Transcription successful: {text[:100]}...")
            except FileNotFoundError:
                logger.error("ffmpeg not found in PATH")
                raise HTTPException(
                    status_code=500, 
                    detail="ffmpeg not found. Please install ffmpeg and make sure it's in your system PATH."
                )
            except Exception as transcribe_error:
                logger.error(f"Transcription error: {str(transcribe_error)}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=500,
                    detail=f"Error during transcription: {str(transcribe_error)}"
                )
            
            # Use the actual /translate API endpoint via HTTP request
            try:
                logger.info(f"Calling /translate API to translate text to {target_lang}")
                
                # Determine the base URL (same as the current server)
                server_url = "http://127.0.0.1:8000"  # Default to localhost
                
                # Prepare the request payload
                translation_payload = {
                    "text": text,
                    "target_language": target_lang,
                    "source_language": None  # Use auto-detection
                }
                
                # Make HTTP request to the translate endpoint
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{server_url}/translate",
                        json=translation_payload
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Translation API returned status {response.status_code}: {response.text}")
                    
                    translation_data = response.json()
                    logger.info("Translation API call successful")
                
                return {
                    "transcript": text,
                    "translation": translation_data["translated_text"],
                    "source_language": translation_data["source_language"],
                    "target_language": translation_data["target_language"],
                    "detected_language": translation_data.get("detected_language")
                }
            except Exception as translate_error:
                logger.error(f"Translation error: {str(translate_error)}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=500,
                    detail=f"Error during translation: {str(translate_error)}"
                )
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


