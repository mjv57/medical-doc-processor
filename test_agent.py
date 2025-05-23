import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_extract_structured():
    """Test the extraction of structured data from a raw text"""
    # Get a sample document first
    response = requests.get(f"{BASE_URL}/documents/1")
    document = response.json()
    
    # Send the document content for structured extraction
    data = {"text": document["content"]}
    
    response = requests.post(f"{BASE_URL}/extract_structured", json=data)
    print("\n=== Extract Structured Data ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")

def test_extract_structured_from_document():
    """Test the extraction of structured data from an existing document"""
    response = requests.post(f"{BASE_URL}/documents/2/extract_structured")
    print("\n=== Extract Structured Data from Document ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")

def run_all_tests():
    """Run all extraction agent tests"""
    print("Starting extraction agent tests...")
    
    # Test extract structured
    test_extract_structured()
    
    # Test extract structured from document
    test_extract_structured_from_document()
    
    print("\nAll extraction agent tests completed!")

if __name__ == "__main__":
    run_all_tests()
