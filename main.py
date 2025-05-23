
from typing import List, Optional, Dict, Any
import hashlib
import json
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, engine, SessionLocal
from models import Document as DocumentModel
import models
from models_llm import LLMResponse
from models_rag import UserQuestion
from seed import create_tables, seed_database
from llm_service import LLMService
from rag_service import RAGService
from agent_service import MedicalExtractionAgent
from models_agent import StructuredMedicalData
from fhir_service import FHIRConverter
from models_fhir import FHIRConversionRequest, FHIRConversionResponse

# Create Pydantic models for request/response
class DocumentBase(BaseModel):
    title: str
    content: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int

    class Config:
        orm_mode = True

# Models for LLM operations
class NoteText(BaseModel):
    text: str
    use_cache: bool = True  # Option to bypass cache

class NoteId(BaseModel):
    document_id: int
    use_cache: bool = True  # Option to bypass cache

class LLMResult(BaseModel):
    result: Dict[str, Any]

# Add these Pydantic models for the RAG endpoint
class Question(BaseModel):
    text: str

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []


class MedicalNoteText(BaseModel):
    text: str

# Initialize FastAPI app
app = FastAPI()

# Initialize LLM service
llm_service = LLMService()

# Initialize Agent
medical_agent = MedicalExtractionAgent()

# Initialize RAG service
rag_service = None


# Initialize FHIR Conversion
fhir_converter = FHIRConverter()

# Create tables and seed database on startup
@app.on_event("startup")
async def startup_event():
    global rag_service
    
    # Create tables and seed database
    create_tables()
    seed_database()
    
    try:
        # Initialize RAG service with all documents
        db = SessionLocal()
        documents = db.query(DocumentModel).all()
        
        # Convert to dictionary format for the RAG service
        docs_list = [{"id": doc.id, "title": doc.title, "content": doc.content} for doc in documents]
        
        print(f"Initializing RAG service with {len(docs_list)} documents")
        
        # Create the RAG service
        rag_service = RAGService()
        rag_service.initialize_from_documents(docs_list)
        
        print("RAG service initialized successfully")
    except Exception as e:
        print(f"Error initializing RAG service: {str(e)}")
    finally:
        db.close()

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Get all documents
@app.get("/documents", response_model=List[Document])
def get_documents(db: Session = Depends(get_db)):
    documents = db.query(DocumentModel).all()
    return documents

# Get document by ID
@app.get("/documents/{document_id}", response_model=Document)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

# Create new document
@app.post("/documents", response_model=Document)
def create_document(document: DocumentCreate, db: Session = Depends(get_db)):
    db_document = DocumentModel(title=document.title, content=document.content)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

# Helper function to generate hash for caching
def generate_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

# Summarize a note using raw text
@app.post("/summarize_note", response_model=LLMResult)
async def summarize_note(note: NoteText, db: Session = Depends(get_db)):
    try:
        # Check cache if enabled
        if note.use_cache:
            text_hash = generate_hash(note.text)
            cached_response = db.query(LLMResponse).filter(
                LLMResponse.input_hash == text_hash,
                LLMResponse.operation_type == "summarize"
            ).first()
            
            if cached_response:
                return {"result": {"summary": cached_response.response_text, "cached": True}}
        
        # If not in cache or cache bypassed, call LLM
        summary_result = llm_service.summarize_medical_note(note.text)
        
        # Cache the result if caching is enabled
        if note.use_cache:
            text_hash = generate_hash(note.text)
            llm_response = LLMResponse(
                document_id=None,  # No document ID for raw text
                operation_type="summarize",
                input_hash=text_hash,
                response_text=summary_result["summary"]
            )
            db.add(llm_response)
            db.commit()
        
        return {"result": summary_result}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

# summarize a document by ID
@app.post("/documents/{document_id}/summarize", response_model=LLMResult)
async def summarize_document(
    document_id: int, 
    options: NoteId, 
    db: Session = Depends(get_db)
):
    document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Check cache if enabled
        if options.use_cache:
            cached_response = db.query(LLMResponse).filter(
                LLMResponse.document_id == document_id,
                LLMResponse.operation_type == "summarize"
            ).first()
            
            if cached_response:
                return {"result": {"summary": cached_response.response_text, "cached": True}}
        
        # If not in cache or cache bypassed, call LLM
        summary_result = llm_service.summarize_medical_note(document.content)
        
        # Cache the result if caching is enabled
        if options.use_cache:
            llm_response = LLMResponse(
                document_id=document_id,
                operation_type="summarize",
                input_hash=generate_hash(document.content),
                response_text=summary_result["summary"]
            )
            db.add(llm_response)
            db.commit()
        
        return {"result": summary_result}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

# extract patient info from a document
@app.post("/documents/{document_id}/extract_info", response_model=LLMResult)
async def extract_document_info(
    document_id: int, 
    options: NoteId, 
    db: Session = Depends(get_db)
):
    document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Check cache if enabled
        if options.use_cache:
            cached_response = db.query(LLMResponse).filter(
                LLMResponse.document_id == document_id,
                LLMResponse.operation_type == "extract_info"
            ).first()
            
            if cached_response:
                return {"result": {"patient_information": cached_response.response_text, "cached": True}}
        
        # If not in cache or cache bypassed, call LLM
        info_result = llm_service.extract_patient_info(document.content)
        
        # Cache the result if caching is enabled
        if options.use_cache:
            llm_response = LLMResponse(
                document_id=document_id,
                operation_type="extract_info",
                input_hash=generate_hash(document.content),
                response_text=info_result["patient_information"]
            )
            db.add(llm_response)
            db.commit()
        
        return {"result": info_result}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

# simplify a document for patient understanding
@app.post("/documents/{document_id}/simplify", response_model=LLMResult)
async def simplify_document(
    document_id: int, 
    options: NoteId, 
    db: Session = Depends(get_db)
):
    document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Check cache if enabled
        if options.use_cache:
            cached_response = db.query(LLMResponse).filter(
                LLMResponse.document_id == document_id,
                LLMResponse.operation_type == "simplify"
            ).first()
            
            if cached_response:
                return {"result": {"patient_friendly_note": cached_response.response_text, "cached": True}}
        
        # If not in cache or cache bypassed, call LLM
        simplify_result = llm_service.simplify_for_patient(document.content)
        
        # Cache the result if caching is enabled
        if options.use_cache:
            llm_response = LLMResponse(
                document_id=document_id,
                operation_type="simplify",
                input_hash=generate_hash(document.content),
                response_text=simplify_result["patient_friendly_note"]
            )
            db.add(llm_response)
            db.commit()
        
        return {"result": simplify_result}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

# RAG endpoint to answer questions
@app.post("/answer_question", response_model=AnswerResponse)
async def answer_question(question: Question, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Answer a question using RAG"""
    if not rag_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service not initialized yet. Please try again later."
        )
    
    try:
        # Get answer from RAG service
        result = rag_service.answer_question(question.text)
        
        # Save question and answer to database (as a background task)
        background_tasks.add_task(
            save_question_answer,
            db=db,
            question=question.text,
            answer=result["answer"],
            sources=result["sources"]
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )

# fet previous questions and answers
@app.get("/questions", response_model=List[Dict[str, Any]])
async def get_questions(db: Session = Depends(get_db)):
    """Get all previous questions and answers"""
    questions = db.query(UserQuestion).order_by(UserQuestion.created_at.desc()).all()
    
    return [
        {
            "id": q.id,
            "question": q.question,
            "answer": q.answer,
            "sources": q.sources,
            "created_at": q.created_at
        }
        for q in questions
    ]

# function to save question and answer to database
def save_question_answer(db: Session, question: str, answer: str, sources: List[Dict[str, Any]]):
    """Save a question and its answer to the database"""
    try:
        user_question = UserQuestion(
            question=question,
            answer=answer,
            sources=sources
        )
        db.add(user_question)
        db.commit()
    except Exception as e:
        print(f"Error saving question to database: {str(e)}")
        db.rollback()




# extract structured medical data 
@app.post("/extract_structured", response_model=Dict[str, Any])
async def extract_structured_data(note: MedicalNoteText):
    """Extract structured data from a medical note"""
    try:
        # Process the note with the agent
        structured_data = medical_agent.process_medical_note(note.text)
        return structured_data
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting structured data: {str(e)}"
        )

# endpoint to extract from existing document
@app.post("/documents/{document_id}/extract_structured", response_model=Dict[str, Any])
async def extract_structured_from_document(document_id: int, db: Session = Depends(get_db)):
    """Extract structured data from an existing document"""
    document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Process the document with the agent
        structured_data = medical_agent.process_medical_note(document.content)
        return structured_data
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting structured data: {str(e)}"
        )




# convert structured data to FHIR
@app.post("/to_fhir", response_model=FHIRConversionResponse)
async def convert_to_fhir(request: FHIRConversionRequest):
    """Convert structured data to FHIR format"""
    try:
        # Convert structured data to FHIR
        fhir_resources = fhir_converter.convert_to_fhir(request.structured_data)
        
        # Validate the FHIR resources
        is_valid = fhir_converter.validate_fhir(fhir_resources)
        
        return {
            "fhir_resources": fhir_resources,
            "is_valid": is_valid
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting to FHIR: {str(e)}"
        )

# endpoint to convert document directly to FHIR
@app.post("/documents/{document_id}/to_fhir", response_model=FHIRConversionResponse)
async def document_to_fhir(document_id: int, db: Session = Depends(get_db)):
    """Extract structured data from a document and convert to FHIR"""
    # First extract structured data
    document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Process the document with the agent
        structured_data = medical_agent.process_medical_note(document.content)
        
        # Convert to FHIR
        fhir_resources = fhir_converter.convert_to_fhir(structured_data)
        
        # Validate the FHIR resources
        is_valid = fhir_converter.validate_fhir(fhir_resources)
        
        return {
            "fhir_resources": fhir_resources,
            "is_valid": is_valid
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting to FHIR: {str(e)}"
        )
