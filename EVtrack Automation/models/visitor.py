from pydantic import BaseModel, Field
from typing import Optional

class VehicleData(BaseModel):
    """Legacy vehicle data model for backward compatibility"""
    number_plate: Optional[str] = None
    vehicle_type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    colour: Optional[str] = None
    vin: Optional[str] = None
    engine_number: Optional[str] = None
    licence_disc_number: Optional[str] = None
    licence_expiry_date: Optional[str] = None
    document_number: Optional[str] = None
    comments: Optional[str] = None

class CredentialData(BaseModel):
    """Legacy credential data model for backward compatibility"""
    reader_type: Optional[str] = None  # Values like "CONTACTLESS_CARD", "PIN", "LPR", etc.
    unique_identifier: Optional[str] = None  # Card#/LPR/UID
    pin: Optional[str] = None
    active_date: Optional[str] = None  # Format: "YYYY-MM-DD" (date only)
    active_time: Optional[str] = None  # Format: "HH:MM" (time only)
    expiry_date: Optional[str] = None  # Format: "YYYY-MM-DD" (date only)
    expiry_time: Optional[str] = None  # Format: "HH:MM" (time only)
    use_limit: Optional[int] = None
    comments: Optional[str] = None
    status: Optional[str] = "ACTIVE"  # Default to ACTIVE
    access_control_lists: Optional[bool] = True  # Default to checked for visitor access

class VisitorData(BaseModel):
    """Legacy visitor data model for backward compatibility"""
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: Optional[str] = None
    nationality: str = Field(..., min_length=1)
    id_number: str = Field(..., min_length=1)
    gender: str = Field(..., min_length=1)
    company: Optional[str] = None
    phone: Optional[str] = None
    photo_path: Optional[str] = None
