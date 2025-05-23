# test_fhir.py
import requests
import json

# Base URL for your FastAPI server
BASE_URL = "http://127.0.0.1:8000"

def test_convert_to_fhir():
    """Test converting structured data to FHIR format"""
    # First, get structured data from a document
    response = requests.post(f"{BASE_URL}/documents/1/extract_structured")
    structured_data = response.json()
    
    # Then convert it to FHIR
    data = {"structured_data": structured_data}
    response = requests.post(f"{BASE_URL}/to_fhir", json=data)
    
    print("\n=== Convert to FHIR ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Is Valid FHIR: {result['is_valid']}")
        print("\nFHIR Resources:")
        print(json.dumps(result["fhir_resources"], indent=2))
    else:
        print(f"Error: {response.text}")

def test_document_to_fhir():
    """Test converting a document directly to FHIR"""
    response = requests.post(f"{BASE_URL}/documents/2/to_fhir")
    
    print("\n=== Document to FHIR ===")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Is Valid FHIR: {result['is_valid']}")
        
        # Count the number of resources by type
        resource_counts = {}
        for resource_type, resources in result["fhir_resources"].items():
            if isinstance(resources, list):
                resource_counts[resource_type] = len(resources)
            elif resources:
                resource_counts[resource_type] = 1
        
        print("\nFHIR Resource Counts:")
        for resource_type, count in resource_counts.items():
            print(f"  {resource_type}: {count}")
        
        # Show a sample condition
        if "conditions" in result["fhir_resources"] and result["fhir_resources"]["conditions"]:
            print("\nSample Condition Resource:")
            print(json.dumps(result["fhir_resources"]["conditions"][0], indent=2))
        
        # Show a sample observation
        if "observations" in result["fhir_resources"] and result["fhir_resources"]["observations"]:
            print("\nSample Observation Resource:")
            print(json.dumps(result["fhir_resources"]["observations"][0], indent=2))
    else:
        print(f"Error: {response.text}")

def run_all_tests():
    """Run all FHIR tests"""
    print("Starting FHIR conversion tests...")
    
    # Test convert to FHIR
    test_convert_to_fhir()
    
    # Test document to FHIR
    test_document_to_fhir()
    
    print("\nAll FHIR tests completed!")

if __name__ == "__main__":
    run_all_tests()