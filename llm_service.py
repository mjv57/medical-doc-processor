# llm_service.py
import os
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.cache import SQLiteCache
import langchain

# Set up caching to avoid redundant API calls
langchain.llm_cache = SQLiteCache(database_path=".langchain.db")

class LLMService:
    def __init__(self):
        # Load API key from file (or use environment variable as fallback)
        api_key = self._load_api_key()
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=api_key,
        )
    
    def _load_api_key(self) -> str:
        """Load OpenAI API key from file or environment variable"""
        # First try environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key
            
        # If not found, try to read from file with your specific filename
        try:
            with open("medical_doc_parser_openai_apikey.txt", "r") as f:
                api_key = f.read().strip()
                # Set environment variable for future use
                os.environ["OPENAI_API_KEY"] = api_key
                return api_key
        except Exception as e:
            raise ValueError("Failed to load OpenAI API key. Please ensure 'medical_doc_parser_openai_apikey.txt' exists or set OPENAI_API_KEY environment variable.") from e

    def summarize_medical_note(self, note_text: str) -> Dict[str, str]:
        """Summarize a medical note using the LLM"""
        prompt = ChatPromptTemplate.from_template(
            """You are a medical professional assistant. 
            Summarize the following medical note in a concise but comprehensive way. 
            Include the most important clinical information.
            
            Medical Note:
            {note_text}
            
            Summary:"""
        )
        
        # Create the chain
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            # Execute the chain
            summary = chain.invoke({"note_text": note_text})
            return {"summary": summary}
        except Exception as e:
            # Log the error (in a production app, use proper logging)
            print(f"Error during LLM processing: {str(e)}")
            # Re-raise the exception for the API endpoint to handle
            raise

    def extract_patient_info(self, note_text: str) -> Dict[str, str]:
        """Extract key patient information from medical note"""
        prompt = ChatPromptTemplate.from_template(
            """You are a medical professional assistant.
            Extract and list the key patient information from the following medical note.
            Include demographics, vital signs, diagnoses, and treatment plan.
            Format the output in a structured way.
            
            Medical Note:
            {note_text}
            
            Key Patient Information:"""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({"note_text": note_text})
            return {"patient_information": result}
        except Exception as e:
            print(f"Error during patient info extraction: {str(e)}")
            raise

    def simplify_for_patient(self, note_text: str) -> Dict[str, str]:
        """Simplify medical note for patient understanding"""
        prompt = ChatPromptTemplate.from_template(
            """You are a medical professional who excels at explaining complex medical information in simple terms.
            Rewrite the following medical note in language that a patient with no medical background could easily understand.
            Avoid jargon, use plain language, and focus on what the patient needs to know.
            
            Medical Note:
            {note_text}
            
            Patient-Friendly Version:"""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({"note_text": note_text})
            return {"patient_friendly_note": result}
        except Exception as e:
            print(f"Error during note simplification: {str(e)}")
            raise