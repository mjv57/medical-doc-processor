# fhir_service.py
from typing import Dict, List, Any
import json
from datetime import datetime

class FHIRConverter:
    """
    Service to convert structured medical data into FHIR-compatible format
    """
    
    def __init__(self):
        """Initialize the FHIR converter"""
        pass
    
    def convert_to_fhir(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert structured medical data to FHIR resources
        """
        # Initialize FHIR Bundle to hold resources
        fhir_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": []
        }
        
        # Create unique identifiers
        patient_id = self._get_patient_id(structured_data)
        encounter_id = f"encounter-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Convert each resource type
        patient_resource = self._create_patient_resource(structured_data, patient_id)
        encounter_resource = self._create_encounter_resource(structured_data, encounter_id, patient_id)
        condition_resources = self._create_condition_resources(structured_data, patient_id, encounter_id)
        observation_resources = self._create_observation_resources(structured_data, patient_id, encounter_id)
        medication_resources = self._create_medication_resources(structured_data, patient_id, encounter_id)
        procedure_resources = self._create_procedure_resources(structured_data, patient_id, encounter_id)
        appointment_resources = self._create_appointment_resources(structured_data, patient_id)
        
        # Add resources to bundle
        if patient_resource:
            fhir_bundle["entry"].append({"resource": patient_resource})
        
        if encounter_resource:
            fhir_bundle["entry"].append({"resource": encounter_resource})
        
        for resource in condition_resources:
            fhir_bundle["entry"].append({"resource": resource})
            
        for resource in observation_resources:
            fhir_bundle["entry"].append({"resource": resource})
            
        for resource in medication_resources:
            fhir_bundle["entry"].append({"resource": resource})
            
        for resource in procedure_resources:
            fhir_bundle["entry"].append({"resource": resource})
            
        for resource in appointment_resources:
            fhir_bundle["entry"].append({"resource": resource})
        
        # Create a simplified representation for the API response
        simplified_response = {
            "patient": patient_resource,
            "encounter": encounter_resource,
            "conditions": condition_resources,
            "observations": observation_resources,
            "medications": medication_resources,
            "procedures": procedure_resources,
            "appointments": appointment_resources
        }
        
        return simplified_response
    
    def _get_patient_id(self, data: Dict[str, Any]) -> str:
        """Extract or create a patient ID"""
        if "patient" in data and "id" in data["patient"] and data["patient"]["id"]:
            # Clean up the ID to make it FHIR-compatible
            return data["patient"]["id"].replace("--", "-").replace(" ", "-")
        return f"patient-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _create_patient_resource(self, data: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Create a FHIR Patient resource"""
        patient = {
            "resourceType": "Patient",
            "id": patient_id
        }
        
        # Add gender if available
        if "patient" in data and "gender" in data["patient"] and data["patient"]["gender"]:
            patient["gender"] = data["patient"]["gender"].lower()
        
        return patient
    
    def _create_encounter_resource(self, data: Dict[str, Any], encounter_id: str, patient_id: str) -> Dict[str, Any]:
        """Create a FHIR Encounter resource"""
        encounter = {
            "resourceType": "Encounter",
            "id": encounter_id,
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            }
        }
        
        # Add encounter date if available
        if "encounter_date" in data and data["encounter_date"]:
            encounter["period"] = {
                "start": data["encounter_date"]
            }
        
        return encounter
    
    def _create_condition_resources(self, data: Dict[str, Any], patient_id: str, encounter_id: str) -> List[Dict[str, Any]]:
        """Create FHIR Condition resources"""
        conditions = []
        
        if "diagnoses" in data and data["diagnoses"]:
            for i, diagnosis in enumerate(data["diagnoses"]):
                condition = {
                    "resourceType": "Condition",
                    "id": f"condition-{i+1}",
                    "subject": {
                        "reference": f"Patient/{patient_id}"
                    },
                    "encounter": {
                        "reference": f"Encounter/{encounter_id}"
                    }
                }
                
                # Add code if ICD code is available
                if "icd_code" in diagnosis and diagnosis["icd_code"]:
                    condition["code"] = {
                        "coding": [
                            {
                                "system": "http://hl7.org/fhir/sid/icd-10",
                                "code": diagnosis["icd_code"],
                                "display": diagnosis["description"]
                            }
                        ],
                        "text": diagnosis["description"]
                    }
                else:
                    condition["code"] = {
                        "text": diagnosis["description"]
                    }
                
                # Add clinical status if available
                if "status" in diagnosis and diagnosis["status"]:
                    status_map = {
                        "active": "active",
                        "resolved": "resolved",
                        "inactive": "inactive",
                        "remission": "remission"
                    }
                    status = diagnosis["status"].lower()
                    condition["clinicalStatus"] = {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": status_map.get(status, "active")
                            }
                        ]
                    }
                
                conditions.append(condition)
        
        return conditions
    
    def _create_observation_resources(self, data: Dict[str, Any], patient_id: str, encounter_id: str) -> List[Dict[str, Any]]:
        """Create FHIR Observation resources for vital signs and lab results"""
        observations = []
        
        # Process vital signs
        if "vital_signs" in data and data["vital_signs"]:
            vital_signs = data["vital_signs"]
            
            # Blood Pressure
            if "blood_pressure" in vital_signs and vital_signs["blood_pressure"]:
                bp_parts = vital_signs["blood_pressure"].split("/")
                if len(bp_parts) == 2:
                    try:
                        systolic = int(bp_parts[0].strip().split()[0])
                        diastolic = int(bp_parts[1].strip().split()[0])
                        
                        bp_observation = {
                            "resourceType": "Observation",
                            "id": f"observation-bp",
                            "status": "final",
                            "category": [
                                {
                                    "coding": [
                                        {
                                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                            "code": "vital-signs",
                                            "display": "Vital Signs"
                                        }
                                    ]
                                }
                            ],
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://loinc.org",
                                        "code": "85354-9",
                                        "display": "Blood pressure panel"
                                    }
                                ],
                                "text": "Blood Pressure"
                            },
                            "subject": {
                                "reference": f"Patient/{patient_id}"
                            },
                            "encounter": {
                                "reference": f"Encounter/{encounter_id}"
                            },
                            "component": [
                                {
                                    "code": {
                                        "coding": [
                                            {
                                                "system": "http://loinc.org",
                                                "code": "8480-6",
                                                "display": "Systolic blood pressure"
                                            }
                                        ]
                                    },
                                    "valueQuantity": {
                                        "value": systolic,
                                        "unit": "mmHg",
                                        "system": "http://unitsofmeasure.org",
                                        "code": "mm[Hg]"
                                    }
                                },
                                {
                                    "code": {
                                        "coding": [
                                            {
                                                "system": "http://loinc.org",
                                                "code": "8462-4",
                                                "display": "Diastolic blood pressure"
                                            }
                                        ]
                                    },
                                    "valueQuantity": {
                                        "value": diastolic,
                                        "unit": "mmHg",
                                        "system": "http://unitsofmeasure.org",
                                        "code": "mm[Hg]"
                                    }
                                }
                            ]
                        }
                        observations.append(bp_observation)
                    except (ValueError, IndexError):
                        pass
            
            # Heart Rate
            if "heart_rate" in vital_signs and vital_signs["heart_rate"]:
                hr_text = vital_signs["heart_rate"]
                try:
                    hr_value = int(hr_text.split()[0])
                    hr_observation = {
                        "resourceType": "Observation",
                        "id": "observation-hr",
                        "status": "final",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": "vital-signs",
                                        "display": "Vital Signs"
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "8867-4",
                                    "display": "Heart rate"
                                }
                            ],
                            "text": "Heart Rate"
                        },
                        "subject": {
                            "reference": f"Patient/{patient_id}"
                        },
                        "encounter": {
                            "reference": f"Encounter/{encounter_id}"
                        },
                        "valueQuantity": {
                            "value": hr_value,
                            "unit": "beats/minute",
                            "system": "http://unitsofmeasure.org",
                            "code": "/min"
                        }
                    }
                    observations.append(hr_observation)
                except (ValueError, IndexError):
                    pass
            
            # Weight
            if "weight" in vital_signs and vital_signs["weight"]:
                weight_text = vital_signs["weight"]
                try:
                    weight_value = float(weight_text.split()[0])
                    weight_observation = {
                        "resourceType": "Observation",
                        "id": "observation-weight",
                        "status": "final",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": "vital-signs",
                                        "display": "Vital Signs"
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "29463-7",
                                    "display": "Body weight"
                                }
                            ],
                            "text": "Weight"
                        },
                        "subject": {
                            "reference": f"Patient/{patient_id}"
                        },
                        "encounter": {
                            "reference": f"Encounter/{encounter_id}"
                        },
                        "valueQuantity": {
                            "value": weight_value,
                            "unit": "lbs",
                            "system": "http://unitsofmeasure.org",
                            "code": "[lb_av]"
                        }
                    }
                    observations.append(weight_observation)
                except (ValueError, IndexError):
                    pass
            
            # BMI
            if "bmi" in vital_signs and vital_signs["bmi"]:
                try:
                    bmi_value = float(vital_signs["bmi"])
                    bmi_observation = {
                        "resourceType": "Observation",
                        "id": "observation-bmi",
                        "status": "final",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": "vital-signs",
                                        "display": "Vital Signs"
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "39156-5",
                                    "display": "Body mass index (BMI)"
                                }
                            ],
                            "text": "BMI"
                        },
                        "subject": {
                            "reference": f"Patient/{patient_id}"
                        },
                        "encounter": {
                            "reference": f"Encounter/{encounter_id}"
                        },
                        "valueQuantity": {
                            "value": bmi_value,
                            "unit": "kg/m2",
                            "system": "http://unitsofmeasure.org",
                            "code": "kg/m2"
                        }
                    }
                    observations.append(bmi_observation)
                except (ValueError, TypeError):
                    pass
        
        # Lab results (only placeholders since the values aren't available)
        if "lab_results" in data and data["lab_results"]:
            for i, (test_name, test_value) in enumerate(data["lab_results"].items()):
                if test_name:
                    lab_observation = {
                        "resourceType": "Observation",
                        "id": f"observation-lab-{i+1}",
                        "status": "registered",  # Not 'final' since these are just ordered
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": "laboratory",
                                        "display": "Laboratory"
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "text": test_name
                        },
                        "subject": {
                            "reference": f"Patient/{patient_id}"
                        },
                        "encounter": {
                            "reference": f"Encounter/{encounter_id}"
                        }
                    }
                    
                    # Add value if available
                    if test_value:
                        lab_observation["valueString"] = str(test_value)
                    
                    observations.append(lab_observation)
        
        return observations
    
    def _create_medication_resources(self, data: Dict[str, Any], patient_id: str, encounter_id: str) -> List[Dict[str, Any]]:
        """Create FHIR MedicationRequest resources"""
        medication_requests = []
        
        if "medications" in data and data["medications"]:
            for i, medication in enumerate(data["medications"]):
                med_request = {
                    "resourceType": "MedicationRequest",
                    "id": f"medication-{i+1}",
                    "status": "active",
                    "intent": "order",
                    "subject": {
                        "reference": f"Patient/{patient_id}"
                    },
                    "encounter": {
                        "reference": f"Encounter/{encounter_id}"
                    }
                }
                
                # Add medication code if RxNorm code is available
                if "rxnorm_code" in medication and medication["rxnorm_code"]:
                    med_request["medicationCodeableConcept"] = {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": medication["rxnorm_code"],
                                "display": medication["name"]
                            }
                        ],
                        "text": medication["name"]
                    }
                else:
                    med_request["medicationCodeableConcept"] = {
                        "text": medication["name"]
                    }
                
                # Add dosage if available
                dosage_instructions = []
                if "dosage" in medication and medication["dosage"]:
                    dosage_instructions.append(medication["dosage"])
                if "route" in medication and medication["route"]:
                    dosage_instructions.append(f"Route: {medication['route']}")
                if "frequency" in medication and medication["frequency"]:
                    dosage_instructions.append(f"Frequency: {medication['frequency']}")
                
                if dosage_instructions:
                    med_request["dosageInstruction"] = [
                        {
                            "text": "; ".join(dosage_instructions)
                        }
                    ]
                
                medication_requests.append(med_request)
        
        return medication_requests
    
    def _create_procedure_resources(self, data: Dict[str, Any], patient_id: str, encounter_id: str) -> List[Dict[str, Any]]:
        """Create FHIR Procedure resources"""
        procedures = []
        
        if "treatments" in data and data["treatments"]:
            for i, treatment in enumerate(data["treatments"]):
                # Check if this is a procedure and not just advice
                description = treatment.get("description", "").lower()
                procedure_keywords = ["administered", "performed", "given", "vaccine", "injection"]
                
                if any(keyword in description for keyword in procedure_keywords):
                    procedure = {
                        "resourceType": "Procedure",
                        "id": f"procedure-{i+1}",
                        "status": "completed",
                        "category": {
                            "text": "Prevention"
                        },
                        "code": {
                            "text": treatment["description"]
                        },
                        "subject": {
                            "reference": f"Patient/{patient_id}"
                        },
                        "encounter": {
                            "reference": f"Encounter/{encounter_id}"
                        }
                    }
                    
                    # Add ICD procedure code if available
                    if "icd_procedure_code" in treatment and treatment["icd_procedure_code"]:
                        procedure["code"]["coding"] = [
                            {
                                "system": "http://hl7.org/fhir/sid/icd-10-pcs",
                                "code": treatment["icd_procedure_code"],
                                "display": treatment["description"]
                            }
                        ]
                    
                    procedures.append(procedure)
        
        return procedures
    
    def _create_appointment_resources(self, data: Dict[str, Any], patient_id: str) -> List[Dict[str, Any]]:
        """Create FHIR Appointment resources"""
        appointments = []
        
        if "follow_up" in data and data["follow_up"]:
            for i, follow_up in enumerate(data["follow_up"]):
                appointment = {
                    "resourceType": "Appointment",
                    "id": f"appointment-{i+1}",
                    "status": "proposed",
                    "description": follow_up.get("description", "Follow-up appointment"),
                    "participant": [
                        {
                            "actor": {
                                "reference": f"Patient/{patient_id}"
                            },
                            "status": "accepted"
                        }
                    ]
                }
                
                # Add timeframe if available
                if "timeframe" in follow_up and follow_up["timeframe"]:
                    appointment["comment"] = f"Timeframe: {follow_up['timeframe']}"
                
                appointments.append(appointment)
        
        return appointments
    
    def validate_fhir(self, fhir_data: Dict[str, Any]) -> bool:
        """
        Perform basic validation of FHIR data
        """
        try:
            # Check if the data is valid JSON
            json.dumps(fhir_data)
            
            # Check if resourceType is present in each resource
            resources = []
            for resource_type, resource_list in fhir_data.items():
                if isinstance(resource_list, list):
                    resources.extend(resource_list)
                elif isinstance(resource_list, dict):
                    resources.append(resource_list)
            
            for resource in resources:
                if isinstance(resource, dict) and "resourceType" not in resource:
                    return False
            
            return True
        except Exception:
            return False