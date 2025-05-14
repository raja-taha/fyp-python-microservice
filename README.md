# Translation Microservice

A FastAPI-based microservice for translating text between different languages using Google Translate.

## Local Setup

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

## Running the Service Locally

Start the service with:

```bash
python main.py
```

The service will be available at `http://localhost:8000`

## Deployment

This project is set up for automatic deployment using GitHub Actions and Docker. The deployment pipeline:

1. Builds a Docker image
2. Pushes the image to Docker Hub
3. Deploys the container to an AWS EC2 instance

### Required GitHub Secrets

Set up these secrets in your GitHub repository:

- `DOCKER_HUB_USERNAME`: Your Docker Hub username
- `DOCKER_HUB_PASSWORD`: Your Docker Hub password
- `SERVER_URL`: URL for the server (e.g., http://localhost:8000)

### Manual Deployment

To manually deploy the service:

1. Build the Docker image:

```bash
docker build -t rajataha/fyp-python-microservice .
```

2. Run the container:

```bash
docker run -d -p 5000:8000 --name fyp-python-microservice-container -e PORT=8000 -e HOST=0.0.0.0 -e SERVER_URL='http://localhost:8000' rajataha/fyp-python-microservice
```

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

### 3. Transcribe Audio

- **POST** `/transcribe`
- Form data:
  - `audio`: Audio file
  - `target_lang`: Target language code

## API Documentation

Once the service is running, you can access:

- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`
