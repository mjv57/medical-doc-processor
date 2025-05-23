import requests
import json
from time import sleep

BASE_URL = "http://127.0.0.1:8000"

def test_answer_question():
    """Test the answer_question endpoint with various questions"""
    questions = [
        "What was the patient's blood pressure in the annual check-up?",
        "What medications were prescribed for high cholesterol?",
        "What is the BMI of the patient who came for annual check-up?",
        "What are the symptoms of diabetes mentioned in the notes?",
        "What follow-up actions were recommended for the patient with high cholesterol?"
    ]
    
    for i, question in enumerate(questions):
        print(f"\n=== Question {i+1}: {question} ===")
        
        data = {"text": question}
        response = requests.post(f"{BASE_URL}/answer_question", json=data)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("\nAnswer:")
            print(result["answer"])
            
            print("\nSources:")
            for source in result["sources"]:
                print(f"- Document {source['id']}: {source['title']} (Score: {source['relevance_score']})")
        else:
            print(f"Error: {response.text}")
        
        # Sleep a bit between requests to not overwhelm the API
        sleep(1)

def test_get_questions():
    """Test retrieving previous questions and answers"""
    response = requests.get(f"{BASE_URL}/questions")
    
    print("\n=== Previous Questions and Answers ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        questions = response.json()
        print(f"Found {len(questions)} previous questions")
        
        # Show a few examples
        for i, q in enumerate(questions[:3]):  # Show up to 3 questions
            print(f"\nQ{i+1}: {q['question']}")
            print(f"A: {q['answer'][:200]}..." if len(q['answer']) > 200 else q['answer'])
    else:
        print(f"Error: {response.text}")

def run_all_tests():
    """Run all RAG API tests"""
    print("Starting RAG API tests...")
    
    # Test question answering
    test_answer_question()
    
    # Test getting previous questions
    test_get_questions()
    
    print("\nAll RAG API tests completed!")

if __name__ == "__main__":
    run_all_tests()
