import os
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import Document
from models_llm import LLMResponse  # Import the new model

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Read SOAP notes from files
def read_soap_files():
    soap_notes = []
    
    # List all txt files in the current directory that start with "soap_"
    files = [f for f in os.listdir('.') if f.startswith('soap_') and f.endswith('.txt')]
    
    for filename in files:
        # Read the content of each file
        with open(filename, 'r') as file:
            content = file.read()
            
            # Create title from filename (e.g., "soap_01.txt" -> "SOAP Note 01")
            title = f"SOAP Note {filename.split('_')[1].split('.')[0]}"
            
            soap_notes.append({"title": title, "content": content})
    
    return soap_notes

# Seed database with SOAP notes
def seed_database():
    db = SessionLocal()
    try:
        # Check if database is already seeded
        existing_docs = db.query(Document).count()
        if existing_docs > 0:
            print("Database already contains documents, skipping seed")
            return
        
        # Get SOAP notes
        soap_notes = read_soap_files()
        
        # Insert documents
        for note in soap_notes:
            db_doc = Document(title=note["title"], content=note["content"])
            db.add(db_doc)
        
        db.commit()
        print(f"Database seeded with {len(soap_notes)} SOAP notes")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    seed_database()
