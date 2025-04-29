from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from typing import Dict, List, Optional

app = FastAPI(
    title="Translation Microservice",
    description="A microservice for translating text between different languages",
    version="1.0.0"
)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


