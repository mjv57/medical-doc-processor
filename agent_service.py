import re
import requests
from typing import Dict, List, Any, Optional
import os
import json
import time

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

class MedicalExtractionAgent:
    def __init__(self, api_key: str = None):
        """Initialize the medical extraction agent with LLM"""
        # Use provided API key or load from environment
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=api_key or None
        )
    
    def extract_structured_data(self, medical_text: str) -> Dict[str, Any]:
        """
        Extract structured data from medical text using LLM
        """
        prompt = ChatPromptTemplate.from_template(
            """You are a medical data extraction assistant. Extract the following information from the medical note below into a structured JSON format:
            
            1. Patient information: Extract as a nested object with fields: "id" (string), "gender" (string, if mentioned)
            2. Encounter date: Format as YYYY-MM-DD
            3. Vital signs: Extract as a nested object with fields: "blood_pressure", "heart_rate", "respiratory_rate", "temperature", "height", "weight", "bmi"
            4. Diagnoses: Extract as an array of objects, each with fields: "description" (string), "status" (active/resolved/etc.)
            5. Medications: Extract as an array of objects, each with fields: "name" (string), "dosage", "route", "frequency"
            6. Treatments: Extract as an array of objects, each with field: "description"
            7. Lab results: Extract as an object with test names as keys and values/results as values
            8. Follow up: Extract as an array of objects, each with fields: "description", "timeframe"
            
            Ensure the JSON structure is EXACTLY as described above, with lowercase field names and proper nesting.
            
            Medical Note:
            {medical_text}
            
            Return ONLY a valid JSON object with these fields. If information is not available, use null or empty arrays as appropriate.
            """
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            # Execute the extraction
            print("Extracting structured data from medical text...")
            json_result = chain.invoke({"medical_text": medical_text})
            
            # Parse the result to ensure it's valid JSON
            print("Parsing extraction result...")
            structured_data = json.loads(json_result)
            
            # Add the raw text
            structured_data["raw_text"] = medical_text
            
            print(f"Successfully extracted structured data with {len(structured_data.get('diagnoses', []))} diagnoses and {len(structured_data.get('medications', []))} medications")
            return structured_data
        except Exception as e:
            print(f"Error extracting structured data: {str(e)}")
            raise
    
    def lookup_icd_codes(self, diagnoses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Look up ICD-10 codes for diagnoses using NLM API
        """
        if not diagnoses:
            print("No diagnoses to lookup ICD codes for")
            return []
            
        print(f"Looking up ICD codes for {len(diagnoses)} diagnoses...")
        enriched_diagnoses = []
        
        for diagnosis in diagnoses:
            try:
                description = diagnosis["description"]
                print(f"  Looking up ICD code for: {description}")
                
                # First, try with clinicaltables.nlm.nih.gov API
                response = requests.get(
                    "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search",
                    params={"terms": description, "maxList": 5},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data[0] > 0 and len(data[3]) > 0:
                        # Extract the code and description
                        for i, result in enumerate(data[3]):
                            if i >= 3:  # Only check the top 3 results
                                break
                                
                            # The structure is typically [name, code]
                            if len(result) >= 2:
                                # Check if the description closely matches what we're looking for
                                result_desc = result[0].lower()
                                search_desc = description.lower()
                                
                                if (search_desc in result_desc or 
                                    result_desc in search_desc or 
                                    any(term in result_desc for term in search_desc.split())):
                                    icd_code = result[1]
                                    print(f"  ✓ Found ICD code: {icd_code} for '{description}'")
                                    diagnosis["icd_code"] = icd_code
                                    break
                        
                # If no code found, try with simple fallback mappings
                if "icd_code" not in diagnosis:
                    # Common diagnosis to ICD-10 mapping
                    common_mappings = {
                        "hypertension": "I10",
                        "type 2 diabetes": "E11.9",
                        "diabetes mellitus type 2": "E11.9",
                        "diabetes": "E11.9",
                        "overweight": "E66.3",
                        "obesity": "E66.9",
                        "hyperlipidemia": "E78.5",
                        "high cholesterol": "E78.0",
                        "influenza": "J11.1",
                        "flu": "J11.1",
                        "annual exam": "Z00.00",
                        "physical examination": "Z00.00",
                        "health checkup": "Z00.00",
                        "family history": "Z82.79",
                        "family history of heart disease": "Z82.49",
                        "family history of high cholesterol": "Z83.42",
                    }
                    
                    # Check for matches in the common mappings
                    for key, code in common_mappings.items():
                        if key.lower() in description.lower():
                            diagnosis["icd_code"] = code
                            print(f"  ✓ Found ICD code via mapping: {code} for '{description}'")
                            break
                
                # Still no code? Leave it null but inform
                if "icd_code" not in diagnosis:
                    print(f"  ✗ No ICD code found for: {description}")
                
                enriched_diagnoses.append(diagnosis)
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ✗ Error looking up ICD code for '{description}': {str(e)}")
                enriched_diagnoses.append(diagnosis)  # Keep original diagnosis even if lookup fails
        
        print(f"Completed ICD code lookup: {sum(1 for d in enriched_diagnoses if 'icd_code' in d)} codes found")
        return enriched_diagnoses
    
    def lookup_rxnorm_codes(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Look up RxNorm codes for medications using NIH RxNav API
        """
        if not medications:
            print("No medications to lookup RxNorm codes for")
            return []
            
        print(f"Looking up RxNorm codes for {len(medications)} medications...")
        enriched_medications = []
        
        for medication in medications:
            try:
                name = medication["name"].strip()
                print(f"  Looking up RxNorm code for: {name}")
                
                # Call the RxNav API to get RxNorm code
                response = requests.get(
                    "https://rxnav.nlm.nih.gov/REST/rxcui.json",
                    params={"name": name},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "idGroup" in data and "rxnormId" in data["idGroup"] and data["idGroup"]["rxnormId"]:
                        rxnorm_code = data["idGroup"]["rxnormId"][0]
                        print(f"  ✓ Found RxNorm code: {rxnorm_code} for '{name}'")
                        medication["rxnorm_code"] = rxnorm_code
                    else:
                        print(f"  - No RxNorm code found in primary lookup for: {name}")
                        
                        # Try an approximate match search
                        response = requests.get(
                            "https://rxnav.nlm.nih.gov/REST/approximateTerm.json",
                            params={"term": name, "maxEntries": 3},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            if "approximateGroup" in data and "candidate" in data["approximateGroup"]:
                                candidates = data["approximateGroup"]["candidate"]
                                if candidates:
                                    best_candidate = candidates[0]
                                    rxcui = best_candidate.get("rxcui")
                                    if rxcui:
                                        print(f"  ✓ Found approximate RxNorm code: {rxcui} for '{name}'")
                                        medication["rxnorm_code"] = rxcui
                
                # If still no code found, try with common medication mappings
                if "rxnorm_code" not in medication:
                    # Common medication to RxNorm mapping
                    common_mappings = {
                        "aspirin": "1191",
                        "lisinopril": "29046",
                        "metformin": "6809",
                        "atorvastatin": "83367",
                        "simvastatin": "36567",
                        "amlodipine": "17767",
                        "metoprolol": "6918",
                        "omeprazole": "7646",
                        "albuterol": "435",
                        "hydrochlorothiazide": "5487"
                    }
                    
                    # Check for matches in the common mappings
                    for key, code in common_mappings.items():
                        if key.lower() in name.lower():
                            medication["rxnorm_code"] = code
                            print(f"  ✓ Found RxNorm code via mapping: {code} for '{name}'")
                            break
                
                # Still no code? Log it
                if "rxnorm_code" not in medication:
                    print(f"  ✗ No RxNorm code found for: {name}")
                
                enriched_medications.append(medication)
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ✗ Error looking up RxNorm code for '{name}': {str(e)}")
                enriched_medications.append(medication)  # Keep original medication even if lookup fails
        
        print(f"Completed RxNorm code lookup: {sum(1 for m in enriched_medications if 'rxnorm_code' in m)} codes found")
        return enriched_medications
    
    def process_medical_note(self, medical_text: str) -> Dict[str, Any]:
        """
        Process a medical note end-to-end:
        1. Extract structured data
        2. Look up ICD codes for diagnoses
        3. Look up RxNorm codes for medications
        4. Return the structured and enriched data
        """
        try:
            print("\n==== PROCESSING MEDICAL NOTE ====")
            
            # Extract structured data
            structured_data = self.extract_structured_data(medical_text)
            
            print("\n--- NORMALIZATION AND ENRICHMENT ---")
            
            # Normalize field names (ensure they're all lowercase)
            normalized_data = {}
            for key, value in structured_data.items():
                normalized_key = key.lower()
                normalized_data[normalized_key] = value
            
            # Look up ICD codes for diagnoses
            if "diagnoses" in normalized_data and normalized_data["diagnoses"]:
                print("\n--- ICD CODE LOOKUP ---")
                normalized_data["diagnoses"] = self.lookup_icd_codes(normalized_data["diagnoses"])
            
            # Look up RxNorm codes for medications
            if "medications" in normalized_data and normalized_data["medications"]:
                print("\n--- RXNORM CODE LOOKUP ---")
                normalized_data["medications"] = self.lookup_rxnorm_codes(normalized_data["medications"])
            
            print("\n==== PROCESSING COMPLETE ====")
            return normalized_data
            
        except Exception as e:
            print(f"Error processing medical note: {str(e)}")
            raise
