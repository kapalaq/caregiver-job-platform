"""
Project: Database Management System Assignment 3
Made by: Ruslan Nagimov, Sayat Abdikul, Aitzhan kadyrov
"""
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from typing import Optional, List
from pathlib import Path
from datetime import date


from database.models import *

app = FastAPI(
    title="Caregiver App",
    description="Caregiver App API",
    version="1.0.0"
)

# Configure upload directory
UPLOAD_DIR = Path("database/photos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Mount static files
app.mount("/database", StaticFiles(directory="database"), name="database")

# Get database connection
def get_connection():
    """Get database connection from engine"""
    db = next(get_db())
    try:
        yield db.connection()
    finally:
        db.close()


# Caregiver route
caregiver_router = APIRouter(prefix="/api/caregivers", tags=["caregivers"])


@caregiver_router.get("", response_model=List[CaregiverListResponse])
def search_caregivers(
        caregiving_type: Optional[CaregivingType] = Query(None, description="Filter by caregiving type"),
        city: Optional[str] = Query(None, description="Filter by city"),
        gender: Optional[Gender] = Query(None, description="Filter by gender"),
        min_rate: Optional[float] = Query(None, ge=0, description="Minimum hourly rate"),
        max_rate: Optional[float] = Query(None, ge=0, description="Maximum hourly rate"),
        sort_by: Optional[str] = Query("hourly_rate", description="Sort by (hourly_rate, given_name)"),
        conn = Depends(get_connection)
):
    """
    Search and list caregivers with optional filters
    """
    # Build dynamic SQL query
    query = """
        SELECT 
            c.caregiver_user_id,
            u.given_name,
            u.surname,
            u.city,
            c.gender,
            c.caregiving_type,
            c.hourly_rate,
            c.photo,
            u.profile_description
        FROM CAREGIVER c
        JOIN USER u ON c.caregiver_user_id = u.user_id
        WHERE 1=1
    """

    params = {}

    # Apply filters
    if caregiving_type:
        query += " AND c.caregiving_type = :caregiving_type"
        params["caregiving_type"] = caregiving_type.value

    if city:
        query += " AND u.city LIKE :city"
        params["city"] = f"%{city}%"

    if gender:
        query += " AND c.gender = :gender"
        params["gender"] = gender.value

    if min_rate is not None:
        query += " AND c.hourly_rate >= :min_rate"
        params["min_rate"] = min_rate

    if max_rate is not None:
        query += " AND c.hourly_rate <= :max_rate"
        params["max_rate"] = max_rate

    # Apply sorting
    if sort_by == "given_name":
        query += " ORDER BY u.given_name ASC"
    else:
        query += " ORDER BY c.hourly_rate"

    # Execute query
    result = conn.execute(text(query), params)
    rows = result.fetchall()

    # Format response
    caregivers = []
    for row in rows:
        caregivers.append(CaregiverListResponse(
            caregiver_user_id=row.caregiver_user_id,
            given_name=row.given_name,
            surname=row.surname,
            city=row.city,
            gender=Gender(row.gender),
            caregiving_type=CaregivingType(row.caregiving_type),
            hourly_rate=float(row.hourly_rate),
            photo=row.photo,
            profile_description=row.profile_description
        ))

    return caregivers


@caregiver_router.get("/{caregiver_id}", response_model=CaregiverResponse)
def get_caregiver_profile(
        caregiver_id: int,
        conn = Depends(get_connection)
):
    """
    Get detailed profile of a specific caregiver
    """
    query = """
        SELECT 
            c.caregiver_user_id,
            c.gender,
            c.caregiving_type,
            c.hourly_rate,
            c.photo,
            u.email,
            u.given_name,
            u.surname,
            u.city,
            u.phone_number,
            u.profile_description,
            u.updated_at
        FROM CAREGIVER c
        JOIN USER u ON c.caregiver_user_id = u.user_id
        WHERE c.caregiver_user_id = :caregiver_id
    """

    result = conn.execute(text(query), {"caregiver_id": caregiver_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caregiver not found"
        )

    return CaregiverResponse(
        caregiver_user_id=row.caregiver_user_id,
        email=row.email,
        phone_number=row.phone_number,
        given_name=row.given_name,
        surname=row.surname,
        city=row.city,
        gender=Gender(row.gender),
        caregiving_type=CaregivingType(row.caregiving_type),
        hourly_rate=float(row.hourly_rate),
        photo=row.photo,
        profile_description=row.profile_description,
        updated_at=row.updated_at
    )


@caregiver_router.put("/me", response_model=CaregiverResponse)
def update_caregiver_profile(
        caregiver_id: int, # query parameter
        caregiver_update: CaregiverUpdate,
        conn = Depends(get_connection)
):
    """
    Update caregiver profile by caregiver_id
    """
    # Check if caregiver exists
    check_query = """
        SELECT caregiver_user_id 
        FROM CAREGIVER 
        WHERE caregiver_user_id = :caregiver_id
    """
    result = conn.execute(text(check_query), {"caregiver_id": caregiver_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caregiver not found"
        )

    # Build update queries dynamically
    caregiver_updates = []
    caregiver_params = {"caregiver_id": caregiver_id}

    if caregiver_update.gender is not None:
        caregiver_updates.append("gender = :gender")
        caregiver_params["gender"] = caregiver_update.gender.value

    if caregiver_update.caregiving_type is not None:
        caregiver_updates.append("caregiving_type = :caregiving_type")
        caregiver_params["caregiving_type"] = caregiver_update.caregiving_type.value

    if caregiver_update.hourly_rate is not None:
        caregiver_updates.append("hourly_rate = :hourly_rate")
        caregiver_params["hourly_rate"] = caregiver_update.hourly_rate

    # Update caregiver table if there are changes
    if caregiver_updates:
        update_caregiver_query = f"""
            UPDATE CAREGIVER 
            SET {", ".join(caregiver_updates)}
            WHERE caregiver_user_id = :caregiver_id
        """
        conn.execute(text(update_caregiver_query), caregiver_params)

    # Build user table updates
    user_updates = []
    user_params = {"user_id": caregiver_id}

    if caregiver_update.given_name is not None:
        user_updates.append("given_name = :given_name")
        user_params["given_name"] = caregiver_update.given_name

    if caregiver_update.surname is not None:
        user_updates.append("surname = :surname")
        user_params["surname"] = caregiver_update.surname

    if caregiver_update.city is not None:
        user_updates.append("city = :city")
        user_params["city"] = caregiver_update.city

    if caregiver_update.phone_number is not None:
        user_updates.append("phone_number = :phone_number")
        user_params["phone_number"] = caregiver_update.phone_number

    if caregiver_update.profile_description is not None:
        user_updates.append("profile_description = :profile_description")
        user_params["profile_description"] = caregiver_update.profile_description

    # Update user table if there are changes
    if user_updates:
        update_user_query = f"""
            UPDATE USER 
            SET {", ".join(user_updates)}
            WHERE user_id = :user_id
        """
        conn.execute(text(update_user_query), user_params)

    try:
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )

    # Fetch and return updated profile
    return get_caregiver_profile(caregiver_id, conn)


@caregiver_router.get("/me/applications", response_model=List[JobApplicationResponse])
def get_my_job_applications(
        caregiver_id: int, # query parameter
        conn = Depends(get_connection)
):
    """
    Get all job applications submitted by a caregiver
    """
    # Verify caregiver exists
    check_query = """
        SELECT caregiver_user_id 
        FROM CAREGIVER 
        WHERE caregiver_user_id = :caregiver_id
    """
    result = conn.execute(text(check_query), {"caregiver_id": caregiver_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caregiver not found"
        )

    query = """
        SELECT 
            ja.job_id,
            ja.date_applied,
            j.required_caregiving_type,
            j.other_requirements,
            j.date_posted,
            u.given_name,
            u.surname,
            u.city
        FROM JOB_APPLICATION ja
        JOIN JOB j ON ja.job_id = j.job_id
        JOIN MEMBER m ON j.member_user_id = m.member_user_id
        JOIN USER u ON m.member_user_id = u.user_id
        WHERE ja.caregiver_user_id = :caregiver_id
        ORDER BY ja.date_applied DESC
    """

    result = conn.execute(text(query), {"caregiver_id": caregiver_id})
    rows = result.fetchall()

    applications = []
    for row in rows:
        applications.append(
            JobApplicationResponse(
                job_id=row.job_id,
                date_applied=row.date_applied,
                required_caregiving_type=CaregivingType(row.required_caregiving_type),
                other_requirements=row.other_requirements,
                date_posted=row.date_posted,
                member_name=f"{row.given_name} {row.surname}",
                member_city=row.city
            )
        )

    return applications


@caregiver_router.get("/me/appointments", response_model=List[AppointmentResponse])
def get_my_appointments(
        caregiver_id: int, # query parameter
        status_filter: Optional[str] = Query(None, description="Filter by status"),
        conn = Depends(get_connection)
):
    """
    Get all appointments for a caregiver
    Can filter by appointment status
    """
    # Verify caregiver exists
    check_query = """
        SELECT caregiver_user_id 
        FROM CAREGIVER 
        WHERE caregiver_user_id = :caregiver_id
    """
    result = conn.execute(text(check_query), {"caregiver_id": caregiver_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caregiver not found"
        )

    # Build query with optional status filter
    query = """
        SELECT 
            a.appointment_id,
            a.appointment_date,
            a.appointment_time,
            a.work_hours,
            a.status,
            u.given_name,
            u.surname,
            u.phone_number,
            u.email,
            u.city
        FROM APPOINTMENT a
        JOIN USER u ON a.member_user_id = u.user_id
        WHERE a.caregiver_user_id = :caregiver_id
    """

    params = {
        "caregiver_id": caregiver_id,
    }

    # Apply status filter if provided
    if status_filter:
        try:
            status_enum = AppointmentStatus(status_filter)
            query += " AND a.status = :status"
            params["status"] = status_enum.value
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: pending, confirmed, declined, cancelled, completed"
            )

    query += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"

    result = conn.execute(text(query), params)
    rows = result.fetchall()

    appointments = []
    for row in rows:
        appointments.append(AppointmentResponse(
            appointment_id=row.appointment_id,
            appointment_date=row.appointment_date,
            appointment_time=row.appointment_time,
            work_hours=float(row.work_hours),
            status=AppointmentStatus(row.status),
            member_name=f"{row.given_name} {row.surname}",
            member_phone=row.phone_number,
            member_email=row.email,
            member_city=row.city
        ))

    return appointments



# Job route
job_router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@job_router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
        member_user_id: int, # query parameter
        job_data: JobCreate,
        db=Depends(get_db)
):
    """
    Create a new job advertisement
    """
    # Check if member exists
    check_query = text("""
        SELECT member_user_id FROM MEMBER WHERE member_user_id = :member_user_id
    """)
    result = db.execute(check_query, {"member_user_id": member_user_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    try:
        # Insert new job
        insert_query = text("""
            INSERT INTO job (member_user_id, required_caregiving_type, other_requirements, date_posted)
            VALUES (:member_user_id, :caregiving_type, :other_requirements, CURDATE())
        """)

        db.execute(insert_query, {
            "member_user_id": member_user_id,
            "caregiving_type": job_data.required_caregiving_type.value,
            "other_requirements": job_data.other_requirements
        })
        db.commit()

        # Get the last inserted ID
        result = db.execute(text("SELECT LAST_INSERT_ID()"))
        job_id = result.fetchone()[0]

        # Fetch and return the created job
        return get_job_by_id(job_id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating job: {str(e)}"
        )


@job_router.get("", response_model=List[JobListResponse])
def search_jobs(
        caregiving_type: Optional[CaregivingType] = Query(None, description="Filter by caregiving type"),
        city: Optional[str] = Query(None, description="Filter by city"),
        date_from: Optional[date] = Query(None, description="Filter jobs posted from this date"),
        date_to: Optional[date] = Query(None, description="Filter jobs posted until this date"),
        limit: int = Query(100, description="Number of results to return"),
        offset: int = Query(0, description="Number of results to skip"),
        db=Depends(get_db)
):
    """
    Search and list job advertisements
    """
    # Build WHERE clause dynamically
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if caregiving_type:
        where_clauses.append("j.required_caregiving_type = :caregiving_type")
        params['caregiving_type'] = caregiving_type.value

    if city:
        where_clauses.append("u.city LIKE :city")
        params['city'] = f"%{city}%"

    if date_from:
        where_clauses.append("j.date_posted >= :date_from")
        params['date_from'] = date_from

    if date_to:
        where_clauses.append("j.date_posted <= :date_to")
        params['date_to'] = date_to

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Execute query
    query = text(f"""
        SELECT 
            j.job_id,
            j.required_caregiving_type,
            j.other_requirements,
            j.date_posted,
            u.city as member_city
        FROM job j
        JOIN member m ON j.member_user_id = m.member_user_id
        JOIN user u ON m.member_user_id = u.user_id
        {where_sql}
        ORDER BY j.date_posted DESC
        LIMIT :limit OFFSET :offset
    """)

    result = db.execute(query, params)
    rows = result.fetchall()

    # Format response
    jobs = []
    for row in rows:
        row_dict = row_to_dict(row)
        jobs.append(JobListResponse(**row_dict))

    return jobs


@job_router.get("/{job_id}", response_model=JobResponse)
def get_job_by_id(
        job_id: int,
        db=Depends(get_db)
):
    """
    Get detailed information about a specific job
    """
    query = text("""
        SELECT 
            j.job_id,
            j.member_user_id,
            j.required_caregiving_type,
            j.other_requirements,
            j.date_posted,
            CONCAT(u.given_name, ' ', u.surname) as member_name,
            u.city as member_city,
            u.email as member_email,
            u.phone_number as member_phone
        FROM job j
        JOIN MEMBER m ON j.member_user_id = m.member_user_id
        JOIN USER u ON m.member_user_id = u.user_id
        WHERE j.job_id = :job_id
    """)

    result = db.execute(query, {"job_id": job_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    row_dict = row_to_dict(row)
    return JobResponse(**row_dict)


@job_router.put("/{job_id}", response_model=JobResponse)
def update_job(
        job_id: int,
        member_user_id: int,
        job_update: JobUpdate,
        db=Depends(get_db)
):
    """
    Update a job advertisement
    """
    # Check if job exists and belongs to the member
    check_query = text("""
        SELECT member_user_id FROM job WHERE job_id = :job_id
    """)
    result = db.execute(check_query, {"job_id": job_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if row[0] != member_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this job"
        )

    try:
        # Build update query
        updates = []
        params = {"job_id": job_id}

        if job_update.required_caregiving_type is not None:
            updates.append("required_caregiving_type = :caregiving_type")
            params['caregiving_type'] = job_update.required_caregiving_type.value

        if job_update.other_requirements is not None:
            updates.append("other_requirements = :other_requirements")
            params['other_requirements'] = job_update.other_requirements

        if not updates:
            # Nothing to update, just return current job
            return get_job_by_id(job_id, db)

        update_query = text(f"""
            UPDATE job 
            SET {', '.join(updates)}
            WHERE job_id = :job_id
        """)

        db.execute(update_query, params)
        db.commit()

        # Fetch and return updated job
        return get_job_by_id(job_id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating job: {str(e)}"
        )


@job_router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
        job_id: int,
        member_user_id: int,
        db=Depends(get_db)
):
    """
    Delete a job advertisement.
    Only the member who posted the job can delete it.
    Pass member_user_id as query parameter.
    """
    # Check if job exists and belongs to the member
    check_query = text("""
        SELECT member_user_id FROM job WHERE job_id = :job_id
    """)
    result = db.execute(check_query, {"job_id": job_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if row[0] != member_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this job"
        )

    try:
        # Delete job applications first (foreign key constraint)
        delete_applications_query = text("""
            DELETE FROM job_application WHERE job_id = :job_id
        """)
        db.execute(delete_applications_query, {"job_id": job_id})

        # Delete job
        delete_query = text("""
            DELETE FROM job WHERE job_id = :job_id
        """)
        db.execute(delete_query, {"job_id": job_id})
        db.commit()

        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job: {str(e)}"
        )


@job_router.get("/me/posted", response_model=List[JobResponse])
def get_my_posted_jobs(
        member_user_id: int,  # query parameter
        db=Depends(get_db)
):
    """
    Get all jobs posted by a specific member
    """
    # Check if member exists
    check_query = text("""
        SELECT member_user_id FROM MEMBER WHERE member_user_id = :member_user_id
    """)
    result = db.execute(check_query, {"member_user_id": member_user_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    query = text("""
        SELECT 
            j.job_id,
            j.member_user_id,
            j.required_caregiving_type,
            j.other_requirements,
            j.date_posted,
            CONCAT(u.given_name, ' ', u.surname) as member_name,
            u.city as member_city,
            u.email as member_email,
            u.phone_number as member_phone
        FROM job j
        JOIN MEMBER m ON j.member_user_id = m.member_user_id
        JOIN USER u ON m.member_user_id = u.user_id
        WHERE j.member_user_id = :member_user_id
        ORDER BY j.date_posted DESC
    """)

    result = db.execute(query, {
        "member_user_id": member_user_id,
    })
    rows = result.fetchall()

    jobs = []
    for row in rows:
        row_dict = row_to_dict(row)
        jobs.append(JobResponse(**row_dict))

    return jobs


@job_router.post("/{job_id}/apply", status_code=status.HTTP_201_CREATED)
def apply_to_job(
        job_id: int,
        caregiver_user_id: int,
        db=Depends(get_db)
):
    """
    Apply to a job as a caregiver
    """
    # Check if job exists
    job_check_query = text("""
        SELECT job_id FROM job WHERE job_id = :job_id
    """)
    result = db.execute(job_check_query, {"job_id": job_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Check if caregiver exists
    caregiver_check_query = text("""
        SELECT caregiver_user_id FROM CAREGIVER WHERE caregiver_user_id = :caregiver_user_id
    """)
    result = db.execute(caregiver_check_query, {"caregiver_user_id": caregiver_user_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caregiver not found"
        )

    # Check if already applied
    check_application_query = text("""
        SELECT caregiver_user_id FROM job_application 
        WHERE job_id = :job_id AND caregiver_user_id = :caregiver_user_id
    """)
    result = db.execute(check_application_query, {
        "job_id": job_id,
        "caregiver_user_id": caregiver_user_id
    })

    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this job"
        )

    try:
        # Insert application
        insert_query = text("""
            INSERT INTO job_application (caregiver_user_id, job_id, date_applied)
            VALUES (:caregiver_user_id, :job_id, CURDATE())
        """)

        db.execute(insert_query, {
            "caregiver_user_id": caregiver_user_id,
            "job_id": job_id
        })
        db.commit()

        return {"message": "Application submitted successfully", "job_id": job_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting application: {str(e)}"
        )


@job_router.delete("/{job_id}/apply", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_application(
        job_id: int,
        caregiver_user_id: int,
        db=Depends(get_db)
):
    """
    Withdraw an application from a job
    """
    # Check if application exists
    check_query = text("""
        SELECT caregiver_user_id FROM job_application 
        WHERE job_id = :job_id AND caregiver_user_id = :caregiver_user_id
    """)
    result = db.execute(check_query, {
        "job_id": job_id,
        "caregiver_user_id": caregiver_user_id
    })

    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    try:
        # Delete application
        delete_query = text("""
            DELETE FROM job_application 
            WHERE job_id = :job_id AND caregiver_user_id = :caregiver_user_id
        """)

        db.execute(delete_query, {
            "job_id": job_id,
            "caregiver_user_id": caregiver_user_id
        })
        db.commit()

        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error withdrawing application: {str(e)}"
        )


@job_router.get("/{job_id}/applications", response_model=List[ApplicantResponse])
def get_job_applications(
        job_id: int,
        member_user_id: int,
        db=Depends(get_db)
):
    """
    Get all applicants for a specific job
    """
    # Check if job exists and belongs to the member
    check_query = text("""
        SELECT member_user_id FROM job WHERE job_id = :job_id
    """)
    result = db.execute(check_query, {"job_id": job_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if row[0] != member_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view applications for this job"
        )

    query = text("""
        SELECT 
            c.caregiver_user_id,
            u.given_name,
            u.surname,
            u.email,
            u.phone_number,
            u.city,
            c.gender,
            c.caregiving_type,
            c.hourly_rate,
            c.photo,
            u.profile_description,
            ja.date_applied
        FROM job_application ja
        JOIN caregiver c ON ja.caregiver_user_id = c.caregiver_user_id
        JOIN USER u ON c.caregiver_user_id = u.user_id
        WHERE ja.job_id = :job_id
        ORDER BY ja.date_applied DESC
    """)

    result = db.execute(query, {
        "job_id": job_id,
    })
    rows = result.fetchall()

    applicants = []
    for row in rows:
        row_dict = row_to_dict(row)
        applicants.append(ApplicantResponse(**row_dict))

    return applicants


application_router = APIRouter(prefix="/api", tags=["applications"])


@application_router.post("/jobs/{job_id}/apply", status_code=status.HTTP_201_CREATED)
def apply_to_job_v2(
        job_id: int,
        caregiver_user_id: int,
        db=Depends(get_db)
):
    """
    Apply to a job as a caregiver
    """
    # Check if job exists
    job_check_query = text("""
        SELECT job_id FROM job WHERE job_id = :job_id
    """)
    result = db.execute(job_check_query, {"job_id": job_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Check if caregiver exists
    caregiver_check_query = text("""
        SELECT caregiver_user_id FROM caregiver WHERE caregiver_user_id = :caregiver_user_id
    """)
    result = db.execute(caregiver_check_query, {"caregiver_user_id": caregiver_user_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caregiver not found"
        )

    # Check if already applied
    check_application_query = text("""
        SELECT caregiver_user_id FROM job_application 
        WHERE job_id = :job_id AND caregiver_user_id = :caregiver_user_id
    """)
    result = db.execute(check_application_query, {
        "job_id": job_id,
        "caregiver_user_id": caregiver_user_id
    })

    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this job"
        )

    try:
        # Insert application
        insert_query = text("""
            INSERT INTO job_application (caregiver_user_id, job_id, date_applied)
            VALUES (:caregiver_user_id, :job_id, CURDATE())
        """)

        db.execute(insert_query, {
            "caregiver_user_id": caregiver_user_id,
            "job_id": job_id
        })
        db.commit()

        return {
            "message": "Application submitted successfully",
            "job_id": job_id,
            "caregiver_user_id": caregiver_user_id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting application: {str(e)}"
        )


@application_router.delete("/jobs/{job_id}/apply", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_application_v2(
        job_id: int,
        caregiver_user_id: int,
        db=Depends(get_db)
):
    """
    Withdraw an application from a job
    """
    # Check if application exists
    check_query = text("""
        SELECT caregiver_user_id FROM job_application 
        WHERE job_id = :job_id AND caregiver_user_id = :caregiver_user_id
    """)
    result = db.execute(check_query, {
        "job_id": job_id,
        "caregiver_user_id": caregiver_user_id
    })

    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    try:
        # Delete application
        delete_query = text("""
            DELETE FROM job_application 
            WHERE job_id = :job_id AND caregiver_user_id = :caregiver_user_id
        """)

        db.execute(delete_query, {
            "job_id": job_id,
            "caregiver_user_id": caregiver_user_id
        })
        db.commit()

        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error withdrawing application: {str(e)}"
        )


@application_router.get("/applications/{caregiver_user_id}/{job_id}", response_model=JobApplicationDetailResponse)
def get_application_details(
        caregiver_user_id: int,
        job_id: int,
        db=Depends(get_db)
):
    """
    Get details of a specific job application
    """
    query = text("""
        SELECT 
            ja.caregiver_user_id,
            ja.job_id,
            ja.date_applied,
            j.required_caregiving_type,
            j.other_requirements,
            j.date_posted,
            j.member_user_id,
            CONCAT(mu.given_name, ' ', mu.surname) as member_name,
            mu.city as member_city,
            mu.email as member_email,
            mu.phone_number as member_phone,
            CONCAT(cu.given_name, ' ', cu.surname) as caregiver_name,
            cu.email as caregiver_email,
            cu.phone_number as caregiver_phone,
            cu.city as caregiver_city,
            c.hourly_rate
        FROM job_application ja
        JOIN job j ON ja.job_id = j.job_id
        JOIN member m ON j.member_user_id = m.member_user_id
        JOIN user mu ON m.member_user_id = mu.user_id
        JOIN caregiver c ON ja.caregiver_user_id = c.caregiver_user_id
        JOIN user cu ON c.caregiver_user_id = cu.user_id
        WHERE ja.caregiver_user_id = :caregiver_user_id 
        AND ja.job_id = :job_id
    """)

    result = db.execute(query, {
        "caregiver_user_id": caregiver_user_id,
        "job_id": job_id
    })
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    row_dict = row_to_dict(row)
    return JobApplicationDetailResponse(**row_dict)


# Appointment router
appointment_router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@appointment_router.post("", response_model=AppointmentDetailResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
        member_user_id: int,  # query parameter
        appointment_data: AppointmentCreate,
        db=Depends(get_db)
):
    """
    Create a new appointment (by member)
    Member creates an appointment with a specific caregiver
    """
    # Check if member exists
    check_member_query = text("""
        SELECT member_user_id FROM MEMBER WHERE member_user_id = :member_user_id
    """)
    result = db.execute(check_member_query, {"member_user_id": member_user_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Check if caregiver exists
    check_caregiver_query = text("""
        SELECT caregiver_user_id FROM CAREGIVER 
        WHERE caregiver_user_id = :caregiver_user_id
    """)
    result = db.execute(check_caregiver_query, {"caregiver_user_id": appointment_data.caregiver_user_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caregiver not found"
        )

    # Validate appointment date (not in the past)
    if appointment_data.appointment_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment date cannot be in the past"
        )

    # Validate work hours
    if appointment_data.work_hours <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work hours must be greater than 0"
        )

    # Check for scheduling conflicts
    conflict_query = text("""
        SELECT appointment_id FROM APPOINTMENT
        WHERE caregiver_user_id = :caregiver_user_id
        AND appointment_date = :appointment_date
        AND appointment_time = :appointment_time
        AND status NOT IN ('cancelled', 'declined', 'completed')
    """)
    result = db.execute(conflict_query, {
        "caregiver_user_id": appointment_data.caregiver_user_id,
        "appointment_date": appointment_data.appointment_date,
        "appointment_time": appointment_data.appointment_time
    })

    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Caregiver already has an appointment at this date and time"
        )

    try:
        # Insert new appointment with 'pending' status
        insert_query = text("""
            INSERT INTO APPOINTMENT 
            (caregiver_user_id, member_user_id, appointment_date, appointment_time, work_hours, status)
            VALUES 
            (:caregiver_user_id, :member_user_id, :appointment_date, :appointment_time, :work_hours, 'pending')
        """)

        db.execute(insert_query, {
            "caregiver_user_id": appointment_data.caregiver_user_id,
            "member_user_id": member_user_id,
            "appointment_date": appointment_data.appointment_date,
            "appointment_time": appointment_data.appointment_time,
            "work_hours": appointment_data.work_hours
        })
        db.commit()

        # Get the last inserted ID
        result = db.execute(text("SELECT LAST_INSERT_ID()"))
        appointment_id = result.fetchone()[0]

        # Fetch and return the created appointment
        return get_appointment_by_id(appointment_id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating appointment: {str(e)}"
        )


@appointment_router.get("/{appointment_id}", response_model=AppointmentDetailResponse)
def get_appointment_by_id(
        appointment_id: int,
        db=Depends(get_db)
):
    """
    Get detailed information about a specific appointment
    """
    query = text("""
        SELECT 
            a.appointment_id,
            a.appointment_date,
            a.appointment_time,
            a.work_hours,
            a.status,
            a.caregiver_user_id,
            a.member_user_id,
            CONCAT(cu.given_name, ' ', cu.surname) as caregiver_name,
            cu.email as caregiver_email,
            cu.phone_number as caregiver_phone,
            cu.city as caregiver_city,
            c.hourly_rate,
            c.caregiving_type,
            CONCAT(mu.given_name, ' ', mu.surname) as member_name,
            mu.email as member_email,
            mu.phone_number as member_phone,
            mu.city as member_city
        FROM APPOINTMENT a
        JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
        JOIN USER cu ON c.caregiver_user_id = cu.user_id
        JOIN MEMBER m ON a.member_user_id = m.member_user_id
        JOIN USER mu ON m.member_user_id = mu.user_id
        WHERE a.appointment_id = :appointment_id
    """)

    result = db.execute(query, {"appointment_id": appointment_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    row_dict = row_to_dict(row)
    return AppointmentDetailResponse(**row_dict)


@appointment_router.put("/{appointment_id}", response_model=AppointmentDetailResponse)
def update_appointment(
        appointment_id: int,
        member_user_id: int, # query parameter
        appointment_update: AppointmentUpdate,
        db=Depends(get_db)
):
    """
    Update an appointment (by member)
    """
    # Check if appointment exists and belongs to the member
    check_query = text("""
        SELECT member_user_id, status, caregiver_user_id 
        FROM APPOINTMENT 
        WHERE appointment_id = :appointment_id
    """)
    result = db.execute(check_query, {"appointment_id": appointment_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    if row[0] != member_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this appointment"
        )

    if row[1] not in ['pending', 'confirmed']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update appointment with status: {row[1]}"
        )

    # Validate appointment date (not in the past) if being updated
    if appointment_update.appointment_date and appointment_update.appointment_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment date cannot be in the past"
        )

    # Validate work hours if being updated
    if appointment_update.work_hours is not None and appointment_update.work_hours <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work hours must be greater than 0"
        )

    # Check for scheduling conflicts if date or time is being changed
    if appointment_update.appointment_date or appointment_update.appointment_time:
        # Get current values
        current_query = text("""
            SELECT appointment_date, appointment_time 
            FROM APPOINTMENT 
            WHERE appointment_id = :appointment_id
        """)
        current = db.execute(current_query, {"appointment_id": appointment_id}).fetchone()

        new_date = appointment_update.appointment_date if appointment_update.appointment_date else current[0]
        new_time = appointment_update.appointment_time if appointment_update.appointment_time else current[1]

        conflict_query = text("""
            SELECT appointment_id FROM APPOINTMENT
            WHERE caregiver_user_id = :caregiver_user_id
            AND appointment_date = :appointment_date
            AND appointment_time = :appointment_time
            AND appointment_id != :appointment_id
            AND status NOT IN ('cancelled', 'declined', 'completed')
        """)
        result = db.execute(conflict_query, {
            "caregiver_user_id": row[2],
            "appointment_date": new_date,
            "appointment_time": new_time,
            "appointment_id": appointment_id
        })

        if result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Caregiver already has an appointment at this date and time"
            )

    try:
        # Build update query
        updates = []
        params = {"appointment_id": appointment_id}

        if appointment_update.appointment_date is not None:
            updates.append("appointment_date = :appointment_date")
            params['appointment_date'] = appointment_update.appointment_date

        if appointment_update.appointment_time is not None:
            updates.append("appointment_time = :appointment_time")
            params['appointment_time'] = appointment_update.appointment_time

        if appointment_update.work_hours is not None:
            updates.append("work_hours = :work_hours")
            params['work_hours'] = appointment_update.work_hours

        if not updates:
            # Nothing to update, just return current appointment
            return get_appointment_by_id(appointment_id, db)

        # If date/time changed, reset status to pending
        if appointment_update.appointment_date or appointment_update.appointment_time:
            updates.append("status = 'pending'")

        update_query = text(f"""
            UPDATE APPOINTMENT 
            SET {', '.join(updates)}
            WHERE appointment_id = :appointment_id
        """)

        db.execute(update_query, params)
        db.commit()

        # Fetch and return updated appointment
        return get_appointment_by_id(appointment_id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating appointment: {str(e)}"
        )


@appointment_router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(
        appointment_id: int,
        user_id: int, # query parameter
        db=Depends(get_db)
):
    """
    Cancel an appointment
    """
    # Check if appointment exists
    check_query = text("""
        SELECT member_user_id, caregiver_user_id, status 
        FROM APPOINTMENT 
        WHERE appointment_id = :appointment_id
    """)
    result = db.execute(check_query, {"appointment_id": appointment_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check if user has permission (either member or caregiver)
    if row[0] != user_id and row[1] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to cancel this appointment"
        )

    # Check if appointment can be cancelled
    if row[2] not in ['pending', 'confirmed']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel appointment with status: {row[2]}"
        )

    try:
        # Update status to cancelled instead of deleting
        cancel_query = text("""
            UPDATE APPOINTMENT 
            SET status = 'cancelled'
            WHERE appointment_id = :appointment_id
        """)
        db.execute(cancel_query, {"appointment_id": appointment_id})
        db.commit()

        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling appointment: {str(e)}"
        )


@appointment_router.patch("/{appointment_id}/confirm", response_model=AppointmentDetailResponse)
def confirm_appointment(
        appointment_id: int,
        caregiver_user_id: int, # query parameter
        db=Depends(get_db)
):
    """
    Confirm an appointment (by caregiver)
    """
    # Check if appointment exists and belongs to the caregiver
    check_query = text("""
        SELECT caregiver_user_id, status 
        FROM APPOINTMENT 
        WHERE appointment_id = :appointment_id
    """)
    result = db.execute(check_query, {"appointment_id": appointment_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    if row[0] != caregiver_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to confirm this appointment"
        )

    if row[1] != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm appointment with status: {row[1]}"
        )

    try:
        # Update status to confirmed
        confirm_query = text("""
            UPDATE APPOINTMENT 
            SET status = 'confirmed'
            WHERE appointment_id = :appointment_id
        """)
        db.execute(confirm_query, {"appointment_id": appointment_id})
        db.commit()

        # Fetch and return updated appointment
        return get_appointment_by_id(appointment_id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming appointment: {str(e)}"
        )


@appointment_router.patch("/{appointment_id}/decline", response_model=AppointmentDetailResponse)
def decline_appointment(
        appointment_id: int,
        caregiver_user_id: int, # query parameter
        db=Depends(get_db)
):
    """
    Decline an appointment (by caregiver)
    """
    # Check if appointment exists and belongs to the caregiver
    check_query = text("""
        SELECT caregiver_user_id, status 
        FROM APPOINTMENT 
        WHERE appointment_id = :appointment_id
    """)
    result = db.execute(check_query, {"appointment_id": appointment_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    if row[0] != caregiver_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to decline this appointment"
        )

    if row[1] != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot decline appointment with status: {row[1]}"
        )

    try:
        # Update status to declined
        decline_query = text("""
            UPDATE APPOINTMENT 
            SET status = 'declined'
            WHERE appointment_id = :appointment_id
        """)
        db.execute(decline_query, {"appointment_id": appointment_id})
        db.commit()

        # Fetch and return updated appointment
        return get_appointment_by_id(appointment_id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error declining appointment: {str(e)}"
        )


@appointment_router.patch("/{appointment_id}/complete", response_model=AppointmentDetailResponse)
def complete_appointment(
        appointment_id: int,
        user_id: int, # query parameter
        db=Depends(get_db)
):
    """
    Mark an appointment as completed
    """
    # Check if appointment exists
    check_query = text("""
        SELECT member_user_id, caregiver_user_id, status 
        FROM APPOINTMENT 
        WHERE appointment_id = :appointment_id
    """)
    result = db.execute(check_query, {"appointment_id": appointment_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Check if user has permission (either member or caregiver)
    if row[0] != user_id and row[1] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to complete this appointment"
        )

    if row[2] != 'confirmed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete appointment with status: {row[2]}"
        )

    try:
        # Update status to completed
        complete_query = text("""
            UPDATE APPOINTMENT 
            SET status = 'completed'
            WHERE appointment_id = :appointment_id
        """)
        db.execute(complete_query, {"appointment_id": appointment_id})
        db.commit()

        # Fetch and return updated appointment
        return get_appointment_by_id(appointment_id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing appointment: {str(e)}"
        )

@appointment_router.get("/member/{member_user_id}", response_model=List[AppointmentDetailResponse])
def get_member_appointments(
        member_user_id: int,
        status_filter: Optional[str] = None,
        db=Depends(get_db)
):
    """
    Get all appointments for a specific member
    """
    # Check if member exists
    check_query = text("""
        SELECT member_user_id FROM MEMBER WHERE member_user_id = :member_user_id
    """)
    result = db.execute(check_query, {"member_user_id": member_user_id})
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    query = """
        SELECT 
            a.appointment_id,
            a.appointment_date,
            a.appointment_time,
            a.work_hours,
            a.status,
            a.caregiver_user_id,
            a.member_user_id,
            CONCAT(cu.given_name, ' ', cu.surname) as caregiver_name,
            cu.email as caregiver_email,
            cu.phone_number as caregiver_phone,
            cu.city as caregiver_city,
            c.hourly_rate,
            c.caregiving_type,
            CONCAT(mu.given_name, ' ', mu.surname) as member_name,
            mu.email as member_email,
            mu.phone_number as member_phone,
            mu.city as member_city
        FROM APPOINTMENT a
        JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
        JOIN USER cu ON c.caregiver_user_id = cu.user_id
        JOIN MEMBER m ON a.member_user_id = m.member_user_id
        JOIN USER mu ON m.member_user_id = mu.user_id
        WHERE a.member_user_id = :member_user_id
    """

    params = {"member_user_id": member_user_id}

    if status_filter:
        try:
            status_enum = AppointmentStatus(status_filter)
            query += " AND a.status = :status"
            params["status"] = status_enum.value
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: pending, confirmed, declined, cancelled, completed"
            )

    query += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"

    result = db.execute(text(query), params)
    rows = result.fetchall()

    appointments = []
    for row in rows:
        row_dict = row_to_dict(row)
        appointments.append(AppointmentDetailResponse(**row_dict))

    return appointments


app.include_router(caregiver_router)
app.include_router(job_router)
app.include_router(application_router)
app.include_router(appointment_router)



@app.get("/")
def root():
    return {"message": "Caregiver Platform API", "version": "1.0.0"}


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


# Run
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)