from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FHIRConversionRequest(BaseModel):
    structured_data: Dict[str, Any]

class FHIRConversionResponse(BaseModel):
    fhir_resources: Dict[str, Any]
    is_valid: bool
