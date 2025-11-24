"""
Member self-service endpoints.
Allows authenticated members to manage their own profile, addresses, and appointments.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import text
from pydantic import BaseModel, Field
from datetime import date, time
from ..db import get_connection

router = APIRouter(prefix="/api/members/me", tags=["members.me"])


# Auth dependency (dev stub)
async def get_current_user_id(x_user_id: int | None = Header(default=None, alias="X-User-Id")) -> int:
    """
    Development auth stub: reads user ID from X-User-Id header.
    Replace with proper JWT/session auth in production.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    return x_user_id


# Pydantic schemas
class UserMini(BaseModel):
    user_id: int
    email: str
    given_name: str
    surname: str
    city: str
    phone_number: str
    profile_description: Optional[str] = None


class MemberCore(BaseModel):
    house_rules: Optional[str] = None
    dependent_description: Optional[str] = None


class MemberProfileOut(BaseModel):
    user: UserMini
    member: MemberCore


class MemberUpdateIn(BaseModel):
    city: Optional[str] = None
    phone_number: Optional[str] = None
    profile_description: Optional[str] = None
    house_rules: Optional[str] = None
    dependent_description: Optional[str] = None


class AddressIn(BaseModel):
    house_number: str = Field(..., min_length=1, max_length=10)
    street: str = Field(..., min_length=1, max_length=200)
    town: str = Field(..., min_length=1, max_length=100)


class AddressOut(AddressIn):
    address_id: int
    is_primary: bool


class AppointmentOut(BaseModel):
    appointment_id: int
    appointment_date: date
    appointment_time: time
    work_hours: float
    status: str
    total_cost: Optional[float] = None
    caregiver_user_id: int
    caregiver_name: str
    caregiver_surname: str


# Endpoints

@router.get("", response_model=MemberProfileOut)
async def get_member_profile(
    user_id: int = Depends(get_current_user_id),
    conn=Depends(get_connection)
):
    query = text("""
        SELECT u.user_id, u.email, u.given_name, u.surname, u.city, u.phone_number, u.profile_description,
               m.house_rules, m.dependent_description
        FROM USER u
        LEFT JOIN MEMBER m ON m.member_user_id = u.user_id
        WHERE u.user_id = :uid
    """)
    
    result = conn.execute(query, {"uid": user_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if member record exists
    if row[7] is None and row[8] is None:  # house_rules and dependent_description both NULL
        # User exists but not a member
        raise HTTPException(status_code=404, detail="Member profile not found")
    
    return MemberProfileOut(
        user=UserMini(
            user_id=row[0],
            email=row[1],
            given_name=row[2],
            surname=row[3],
            city=row[4],
            phone_number=row[5],
            profile_description=row[6]
        ),
        member=MemberCore(
            house_rules=row[7],
            dependent_description=row[8]
        )
    )


@router.put("", response_model=MemberProfileOut)
async def update_member_profile(
    data: MemberUpdateIn,
    user_id: int = Depends(get_current_user_id),
    conn=Depends(get_connection)
):
    with conn.begin():
        # create member if doesn't exist
        ensure_member = text("""
            INSERT INTO MEMBER(member_user_id)
            SELECT :uid
            WHERE NOT EXISTS (SELECT 1 FROM MEMBER WHERE member_user_id = :uid)
        """)
        conn.execute(ensure_member, {"uid": user_id})
        
        # Update USER table (only non-None fields)
        update_user = text("""
            UPDATE USER SET
                city = COALESCE(:city, city),
                phone_number = COALESCE(:phone, phone_number),
                profile_description = COALESCE(:prof, profile_description)
            WHERE user_id = :uid
        """)
        conn.execute(update_user, {
            "uid": user_id,
            "city": data.city,
            "phone": data.phone_number,
            "prof": data.profile_description
        })
        
        # Update MEMBER table
        update_member = text("""
            UPDATE MEMBER SET
                house_rules = COALESCE(:rules, house_rules),
                dependent_description = COALESCE(:dep, dependent_description)
            WHERE member_user_id = :uid
        """)
        conn.execute(update_member, {
            "uid": user_id,
            "rules": data.house_rules,
            "dep": data.dependent_description
        })
    
    # Fetch and return updated profile
    query = text("""
        SELECT u.user_id, u.email, u.given_name, u.surname, u.city, u.phone_number, u.profile_description,
               m.house_rules, m.dependent_description
        FROM USER u
        JOIN MEMBER m ON m.member_user_id = u.user_id
        WHERE u.user_id = :uid
    """)
    
    result = conn.execute(query, {"uid": user_id})
    row = result.fetchone()
    
    return MemberProfileOut(
        user=UserMini(
            user_id=row[0],
            email=row[1],
            given_name=row[2],
            surname=row[3],
            city=row[4],
            phone_number=row[5],
            profile_description=row[6]
        ),
        member=MemberCore(
            house_rules=row[7],
            dependent_description=row[8]
        )
    )


@router.get("/appointments", response_model=List[AppointmentOut])
async def get_my_appointments(
    user_id: int = Depends(get_current_user_id),
    conn=Depends(get_connection)
):
    query = text("""
        SELECT a.appointment_id, a.appointment_date, a.appointment_time, a.work_hours,
               a.status, a.total_cost, a.caregiver_user_id,
               cu.given_name AS caregiver_name, cu.surname AS caregiver_surname
        FROM APPOINTMENT a
        JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
        JOIN USER cu ON cu.user_id = c.caregiver_user_id
        WHERE a.member_user_id = :uid
        ORDER BY a.appointment_date, a.appointment_time
    """)
    
    result = conn.execute(query, {"uid": user_id})
    rows = result.fetchall()
    
    appointments = []
    for row in rows:
        appointments.append(AppointmentOut(
            appointment_id=row[0],
            appointment_date=row[1],
            appointment_time=row[2],
            work_hours=float(row[3]) if row[3] is not None else 0.0,
            status=row[4],
            total_cost=float(row[5]) if row[5] is not None else None,
            caregiver_user_id=row[6],
            caregiver_name=row[7],
            caregiver_surname=row[8]
        ))
    
    return appointments


@router.post("/address", response_model=AddressOut)
async def upsert_primary_address(
    data: AddressIn,
    user_id: int = Depends(get_current_user_id),
    conn=Depends(get_connection)
):
    with conn.begin():
        # check if primary exists
        check_query = text("""
            SELECT address_id FROM ADDRESS
            WHERE member_user_id = :uid AND is_primary = TRUE
        """)
        result = conn.execute(check_query, {"uid": user_id})
        existing = result.fetchone()
        
        if existing:
            # Update existing primary address
            address_id = existing[0]
            update_query = text("""
                UPDATE ADDRESS SET
                    house_number = :hn,
                    street = :st,
                    town = :tw
                WHERE address_id = :aid
            """)
            conn.execute(update_query, {
                "hn": data.house_number,
                "st": data.street,
                "tw": data.town,
                "aid": address_id
            })
        else:
            # Insert new primary address
            insert_query = text("""
                INSERT INTO ADDRESS(member_user_id, house_number, street, town, is_primary)
                VALUES (:uid, :hn, :st, :tw, TRUE)
            """)
            result = conn.execute(insert_query, {
                "uid": user_id,
                "hn": data.house_number,
                "st": data.street,
                "tw": data.town
            })
            address_id = result.lastrowid
    
    return AddressOut(
        address_id=address_id,
        house_number=data.house_number,
        street=data.street,
        town=data.town,
        is_primary=True
    )


@router.get("/address", response_model=AddressOut)
async def get_primary_address(
    user_id: int = Depends(get_current_user_id),
    conn=Depends(get_connection)
):
    query = text("""
        SELECT address_id, house_number, street, town, is_primary
        FROM ADDRESS
        WHERE member_user_id = :uid AND is_primary = TRUE
        LIMIT 1
    """)
    
    result = conn.execute(query, {"uid": user_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Primary address not found")
    
    return AddressOut(
        address_id=row[0],
        house_number=row[1],
        street=row[2],
        town=row[3],
        is_primary=row[4]
    )


@router.delete("/address", status_code=204)
async def delete_primary_address(
    user_id: int = Depends(get_current_user_id),
    conn=Depends(get_connection)
):
    with conn.begin():
        delete_query = text("""
            DELETE FROM ADDRESS
            WHERE member_user_id = :uid AND is_primary = TRUE
        """)
        conn.execute(delete_query, {"uid": user_id})
    
    return None
