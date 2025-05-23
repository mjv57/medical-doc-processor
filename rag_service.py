# rag_service.py
from typing import Dict, List, Any, Optional
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from vector_store import VectorStore

class RAGService:
    def __init__(self, api_key: str = None):
        """Initialize the RAG service with vector store and LLM"""
        # Initialize vector store
        self.vector_store = VectorStore(api_key)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=api_key or None  # None will use environment variable
        )
    
    def initialize_from_documents(self, documents: List[Dict[str, Any]]):
        """Initialize or load the vector DB from documents"""
        self.vector_db = self.vector_store.load_or_create_vector_db(documents)
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using RAG methodology:
        1. Retrieve relevant documents
        2. Extract context from documents
        3. Generate an answer using the context
        """
        if not hasattr(self, 'vector_db'):
            raise ValueError("Vector database not initialized. Call initialize_from_documents first.")
        
        try:
            # Retrieve relevant documents
            results = self.vector_store.similarity_search(question)
            
            if not results:
                return {
                    "answer": "I couldn't find relevant information to answer this question.",
                    "sources": []
                }
            
            # Format the context from retrieved documents
            contexts = []
            sources = []
            
            for doc, score in results:
                if score > 0.7:  # Only use documents with high relevance
                    contexts.append(doc.page_content)
                    sources.append({
                        "id": doc.metadata.get("id"),
                        "title": doc.metadata.get("title"),
                        "source": doc.metadata.get("source"),
                        "relevance_score": round(score, 4),
                        "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    })
            
            if not contexts:
                return {
                    "answer": "I couldn't find relevant information to answer this question.",
                    "sources": []
                }
            
            # Create a prompt that includes the question and contexts
            prompt = PromptTemplate(
                template="""You are a medical assistant that answers questions based on the provided context.
                Use only the information from the context to answer the question.
                If the context doesn't contain the answer, say "I don't have enough information to answer this question based on the provided context."
                
                Context:
                {context}
                
                Question: {question}
                
                Answer:""",
                input_variables=["context", "question"]
            )
            
            # Combine the contexts
            combined_context = "\n\n".join(contexts)
            
            # Generate answer with LLM
            chain = prompt | self.llm
            answer = chain.invoke({"context": combined_context, "question": question})
            
            return {
                "answer": answer.content,
                "sources": sources
            }
        
        except Exception as e:
            print(f"Error in RAG process: {str(e)}")
            return {
                "answer": f"An error occurred while processing your question: {str(e)}",
                "sources": []
            }