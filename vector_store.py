import os
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document as LangchainDocument

# Directory to store vector database
VECTOR_DB_DIR = "vector_db"

class VectorStore:
    def __init__(self, api_key: str = None):
        """Initialize the vector store with OpenAI embeddings"""
        # Use provided API key or load from environment
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        
        # Initialize embeddings model
        self.embeddings = OpenAIEmbeddings()
        
        # Create vector db directory if it doesn't exist
        os.makedirs(VECTOR_DB_DIR, exist_ok=True)
        
        # Initialize the vector store
        self.vector_db = None
    
    def load_or_create_vector_db(self, documents: List[Dict[str, Any]]):
        """Load existing vector DB or create a new one from documents"""
        if os.path.exists(f"{VECTOR_DB_DIR}/chroma.sqlite3") and os.listdir(VECTOR_DB_DIR):
            print("Loading existing vector database...")
            self.vector_db = Chroma(
                persist_directory=VECTOR_DB_DIR,
                embedding_function=self.embeddings
            )
            return self.vector_db
        
        # Convert documents to Langchain document format
        langchain_docs = []
        for doc in documents:
            langchain_docs.append(
                LangchainDocument(
                    page_content=doc["content"],
                    metadata={
                        "id": doc["id"],
                        "title": doc["title"],
                        "source": f"Document {doc['id']}: {doc['title']}"
                    }
                )
            )
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        chunks = text_splitter.split_documents(langchain_docs)
        print(f"Split {len(langchain_docs)} documents into {len(chunks)} chunks")
        
        # Create and persist the vector store
        self.vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=VECTOR_DB_DIR
        )
        
        # Persist the embeddings to disk
        self.vector_db.persist()
        print(f"Vector database created and saved to {VECTOR_DB_DIR}")
        
        return self.vector_db
    
    def similarity_search(self, query: str, k: int = 3):
        """Search for the most similar documents to the query"""
        if not self.vector_db:
            raise ValueError("Vector database not initialized. Call load_or_create_vector_db first.")
        
        return self.vector_db.similarity_search_with_relevance_scores(query, k=k)
