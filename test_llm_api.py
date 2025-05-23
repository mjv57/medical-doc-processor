# test_llm_api.py
import requests
import json

# Base URL for your FastAPI server
BASE_URL = "http://127.0.0.1:8000"

def test_summarize_note():
    """Test the summarize note endpoint with raw text"""
    # Get a sample note first
    response = requests.get(f"{BASE_URL}/documents/1")
    document = response.json()
    
    # Now send the note content to be summarized
    data = {
        "text": document["content"],
        "use_cache": False  # Bypass cache for testing
    }
    
    response = requests.post(f"{BASE_URL}/summarize_note", json=data)
    print("\n=== Summarize Note ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Summary:")
        print(result["result"]["summary"])
    else:
        print(f"Error: {response.text}")

def test_summarize_document():
    """Test summarizing a document by ID"""
    data = {
        "document_id": 1,
        "use_cache": True  # Use cache if available
    }
    
    response = requests.post(f"{BASE_URL}/documents/1/summarize", json=data)
    print("\n=== Summarize Document by ID ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Summary:")
        print(result["result"]["summary"])
        if "cached" in result["result"]:
            print(f"(Cached result: {result['result']['cached']})")
    else:
        print(f"Error: {response.text}")

def test_extract_patient_info():
    """Test extracting patient information from a document"""
    data = {
        "document_id": 2,  # Using a different document
        "use_cache": True
    }
    
    response = requests.post(f"{BASE_URL}/documents/2/extract_info", json=data)
    print("\n=== Extract Patient Information ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Patient Information:")
        print(result["result"]["patient_information"])
    else:
        print(f"Error: {response.text}")

def test_simplify_document():
    """Test simplifying a document for patient understanding"""
    data = {
        "document_id": 3,  # Using a different document
        "use_cache": True
    }
    
    response = requests.post(f"{BASE_URL}/documents/3/simplify", json=data)
    print("\n=== Simplify for Patient ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Patient-Friendly Version:")
        print(result["result"]["patient_friendly_note"])
    else:
        print(f"Error: {response.text}")

def run_all_tests():
    """Run all LLM API tests"""
    print("Starting LLM API tests...")
    
    # Test summarize note endpoint
    test_summarize_note()
    
    # Test summarize document endpoint
    test_summarize_document()
    
    # Test extract patient info endpoint
    test_extract_patient_info()
    
    # Test simplify document endpoint
    test_simplify_document()
    
    print("\nAll LLM API tests completed!")

if __name__ == "__main__":
    run_all_tests()