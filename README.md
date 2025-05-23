# Medical Document Processor

A comprehensive FastAPI application that processes medical documents using Large Language Models (LLMs), extracts structured data, implements Retrieval-Augmented Generation (RAG), and converts data to FHIR format.

## Features

- **Document Management**: Store and retrieve medical documents with SQLAlchemy
- **LLM Integration**: Summarize medical notes and extract patient information using OpenAI
- **RAG Pipeline**: Question answering system using vector embeddings and ChromaDB
- **Structured Data Extraction**: Extract patient data, diagnoses, medications with ICD/RxNorm codes
- **FHIR Conversion**: Convert structured data to FHIR-compatible format
- **Containerized Deployment**: Full Docker support for easy deployment

## Architecture

This application demonstrates a complete medical document processing pipeline:

1. **FastAPI Backend** - RESTful API with automatic documentation
2. **LLM Integration** - OpenAI GPT models for text processing
3. **RAG System** - Vector-based document retrieval and question answering
4. **Medical Code Lookup** - Integration with public health APIs (ICD-10, RxNorm)
5. **FHIR Compliance** - Healthcare data format standardization
6. **Docker Containerization** - Production-ready deployment

## Prerequisites

- Docker and Docker Compose
- OpenAI API key

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

**Option 1: Using command line**

```bash
cat > .env << EOF
OPENAI_API_KEY=your-openai-api-key-here
APP_ENV=production
LOG_LEVEL=info
EOF
```



**Option 2: Manually create with below:



OPENAI_API_KEY=your-openai-api-key-here
APP_ENV=production
LOG_LEVEL=info


### 3. Build and Start the Application


#### A. Navigate to project directory

```bash
cd /path/to/your/project
```

#### B. Build the Docker image

```bash
docker build --platform linux/amd64 -t medical-document-processor .
```

#### C. Start the application
```bash
docker-compose up -d
```

#### D. View logs (optional)
```bash
docker-compose logs -f
```

### 4. Access the Application

Once running, the API will be available at:
- **API Base URL**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 5. Example Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Summarize a Document 
```bash
curl -X POST "http://localhost:8000/documents/1/summarize" \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1, "use_cache": true}'
```


### Ask a Question (RAG)
```bash
curl -X POST "http://localhost:8000/answer_question" \
  -H "Content-Type: application/json" \
  -d '{"text": "What was the patient blood pressure?"}'
```



### Extract Structured Data
```bash
curl -X POST "http://localhost:8000/documents/1/extract_structured"
```


### Convert to FHIR Format
```bash
curl -X POST "http://localhost:8000/documents/1/to_fhir"
```

## 6. Stopping the Application
```bash
# Stop the Docker containers
docker-compose down
```
# Remove containers and volumes (optional)

```bash
docker-compose down -v
```

## Troubleshooting
```bash
# View application logs
docker-compose logs -f
```
```bash
docker-compose logs app
```
