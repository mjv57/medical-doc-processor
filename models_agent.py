# models_agent.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date

class Patient(BaseModel):
    id: str
    gender: Optional[str] = None
    age: Optional[int] = None

class VitalSigns(BaseModel):
    blood_pressure: Optional[str] = None
    heart_rate: Optional[str] = None
    respiratory_rate: Optional[str] = None
    temperature: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    bmi: Optional[float] = None

class Diagnosis(BaseModel):
    description: str
    icd_code: Optional[str] = None
    status: Optional[str] = None  # active, resolved, etc.

class Medication(BaseModel):
    name: str
    rxnorm_code: Optional[str] = None
    dosage: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None

class Treatment(BaseModel):
    description: str
    icd_procedure_code: Optional[str] = None

class FollowUp(BaseModel):
    description: str
    timeframe: Optional[str] = None

class StructuredMedicalData(BaseModel):
    patient: Patient
    encounter_date: Optional[date] = None
    vital_signs: Optional[VitalSigns] = None
    diagnoses: List[Diagnosis] = []
    medications: List[Medication] = []
    treatments: List[Treatment] = []
    lab_results: Dict[str, Any] = {}
    follow_up: List[FollowUp] = []
    raw_text: str  # Store the original raw_text