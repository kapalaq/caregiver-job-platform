from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import date, time, datetime
from decimal import Decimal
import enum
import os

# SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/csci_341")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine():
    return engine

# Enums
class CaregivingType(str, enum.Enum):
    BABYSITTER = "babysitter"
    ELDERLY = "caregiver for elderly"
    PLAYMATE = "playmate for children"

class Gender(str, enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    PREFER_NOT_TO_SAY = "Prefer not to say"

class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# API Validation Schemas
class UserBase(BaseModel):
    email: EmailStr
    given_name: str
    surname: str
    city: str
    phone_number: str
    profile_description: Optional[str] = None

class UserResponse(UserBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class CaregiverBase(BaseModel):
    gender: Gender
    caregiving_type: CaregivingType
    hourly_rate: Decimal = Field(ge=0, decimal_places=2)

class CaregiverUpdate(BaseModel):
    gender: Optional[Gender] = None
    caregiving_type: Optional[CaregivingType] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    given_name: Optional[str] = None
    surname: Optional[str] = None
    city: Optional[str] = None
    phone_number: Optional[str] = None
    profile_description: Optional[str] = None

class CaregiverResponse(BaseModel):
    caregiver_user_id: int
    email: EmailStr
    phone_number: str
    given_name: str
    surname: str
    city: str
    gender: Gender
    caregiving_type: CaregivingType
    hourly_rate: Decimal
    photo: Optional[str] = None
    profile_description: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CaregiverListResponse(BaseModel):
    caregiver_user_id: int
    given_name: str
    surname: str
    city: str
    gender: Gender
    caregiving_type: CaregivingType
    hourly_rate: Decimal
    photo: Optional[str] = None
    profile_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobApplicationResponse(BaseModel):
    job_id: int
    date_applied: datetime
    required_caregiving_type: CaregivingType
    other_requirements: Optional[str] = None
    date_posted: datetime
    member_name: str
    member_city: str

    model_config = ConfigDict(from_attributes=True)

class AppointmentResponse(BaseModel):
    appointment_id: int
    appointment_date: date
    appointment_time: time
    work_hours: int
    status: AppointmentStatus
    member_name: str
    member_phone: str
    member_email: str
    member_city: str

    model_config = ConfigDict(from_attributes=True)

class PhotoUploadResponse(BaseModel):
    photo_url: str
    message: str
