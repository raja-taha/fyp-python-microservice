# Translation Microservice

A FastAPI-based microservice for translating text between different languages using Google Translate.

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

- Windows:

```bash
venv\Scripts\activate
```

- Unix/MacOS:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Service

Start the service with:

```bash
python main.py
```

The service will be available at `http://localhost:8000`

## API Endpoints

### 1. Get Supported Languages

- **GET** `/languages`
- Returns a dictionary of supported languages and their codes

### 2. Translate Text

- **POST** `/translate`
- Request body:

```json
{
  "text": "Hello, world!",
  "target_language": "es",
  "source_language": "en" // Optional, defaults to "auto"
}
```

- Response:

```json
{
  "translated_text": "¡Hola, mundo!",
  "source_language": "en",
  "target_language": "es"
}
```

## API Documentation

Once the service is running, you can access:

- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`
