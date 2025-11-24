from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from typing import Optional
from .routers import members_me
from .db import get_connection

# Create FastAPI app
app = FastAPI(
    title="Caregiver Job Platform API",
    description="API for connecting caregivers with families seeking care services",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(members_me.router)


@app.get("/")
async def root():
    return {"message": "Caregiver Job Platform API is running", "status": "ok"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "caregiver-job-platform",
        "version": "1.0.0"
    }


@app.get("/web", response_class=HTMLResponse)
async def web_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Caregivers CRUD
@app.get("/web/caregivers", response_class=HTMLResponse)
async def list_caregivers(
    request: Request,
    caregiving_type: Optional[str] = None,
    city: Optional[str] = None,
    conn=Depends(get_connection)
):
    query = text("""
        SELECT c.caregiver_user_id, u.email, u.given_name, u.surname, u.city, 
               u.phone_number, c.gender, c.caregiving_type, c.hourly_rate
        FROM CAREGIVER c
        JOIN USER u ON c.caregiver_user_id = u.user_id
        WHERE (:type IS NULL OR c.caregiving_type = :type)
          AND (:city IS NULL OR u.city = :city)
        ORDER BY c.caregiver_user_id
    """)
    result = conn.execute(query, {"type": caregiving_type, "city": city})
    caregivers = [dict(zip(result.keys(), row)) for row in result.fetchall()]
    
    # Get distinct cities and types for filters
    cities_query = text("SELECT DISTINCT city FROM USER ORDER BY city")
    cities = [row[0] for row in conn.execute(cities_query).fetchall()]
    
    return templates.TemplateResponse("caregivers.html", {
        "request": request,
        "caregivers": caregivers,
        "cities": cities,
        "selected_type": caregiving_type,
        "selected_city": city
    })


@app.get("/web/caregivers/add", response_class=HTMLResponse)
async def add_caregiver_form(request: Request):
    return templates.TemplateResponse("caregiver_form.html", {"request": request, "caregiver": None})


@app.get("/web/caregivers/edit/{caregiver_id}", response_class=HTMLResponse)
async def edit_caregiver_form(request: Request, caregiver_id: int, conn=Depends(get_connection)):
    query = text("""
        SELECT c.caregiver_user_id, u.email, u.given_name, u.surname, u.city, 
               u.phone_number, u.profile_description, c.gender, c.caregiving_type, c.hourly_rate
        FROM CAREGIVER c
        JOIN USER u ON c.caregiver_user_id = u.user_id
        WHERE c.caregiver_user_id = :id
    """)
    result = conn.execute(query, {"id": caregiver_id})
    row = result.fetchone()
    
    if not row:
        return RedirectResponse(url="/web/caregivers", status_code=303)
    
    caregiver = dict(zip(result.keys(), row))
    return templates.TemplateResponse("caregiver_form.html", {"request": request, "caregiver": caregiver})


@app.post("/web/caregivers/edit/{caregiver_id}")
async def edit_caregiver(
    caregiver_id: int,
    email: str = Form(...),
    given_name: str = Form(...),
    surname: str = Form(...),
    city: str = Form(...),
    phone_number: str = Form(...),
    gender: str = Form(...),
    caregiving_type: str = Form(...),
    hourly_rate: float = Form(...),
    profile_description: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    conn=Depends(get_connection)
):
    with conn.begin():
        # Update USER table
        if password:
            user_query = text("""
                UPDATE USER SET email = :email, given_name = :given_name, surname = :surname,
                               city = :city, phone_number = :phone, profile_description = :profile,
                               password = :password
                WHERE user_id = :id
            """)
            conn.execute(user_query, {
                "email": email, "given_name": given_name, "surname": surname,
                "city": city, "phone": phone_number, "profile": profile_description,
                "password": password, "id": caregiver_id
            })
        else:
            user_query = text("""
                UPDATE USER SET email = :email, given_name = :given_name, surname = :surname,
                               city = :city, phone_number = :phone, profile_description = :profile
                WHERE user_id = :id
            """)
            conn.execute(user_query, {
                "email": email, "given_name": given_name, "surname": surname,
                "city": city, "phone": phone_number, "profile": profile_description,
                "id": caregiver_id
            })
        
        # Update CAREGIVER table
        caregiver_query = text("""
            UPDATE CAREGIVER SET gender = :gender, caregiving_type = :type, hourly_rate = :rate
            WHERE caregiver_user_id = :id
        """)
        conn.execute(caregiver_query, {
            "gender": gender, "type": caregiving_type, "rate": hourly_rate, "id": caregiver_id
        })
    
    return RedirectResponse(url="/web/caregivers", status_code=303)


@app.post("/web/caregivers/add")
async def add_caregiver(
    request: Request,
    email: str = Form(...),
    given_name: str = Form(...),
    surname: str = Form(...),
    city: str = Form(...),
    phone_number: str = Form(...),
    gender: str = Form(...),
    caregiving_type: str = Form(...),
    hourly_rate: float = Form(...),
    profile_description: Optional[str] = Form(None),
    password: str = Form(...),
    conn=Depends(get_connection)
):
    # phone validation
    if len(phone_number) != 11 or not phone_number.isdigit():
        return templates.TemplateResponse("caregiver_form.html", {
            "request": request,
            "caregiver": None,
            "error": "Phone number must be exactly 11 digits"
        }, status_code=400)
    
    try:
        with conn.begin():
            # Insert into USER table
            user_query = text("""
                INSERT INTO USER (email, given_name, surname, city, phone_number, profile_description, password)
                VALUES (:email, :given_name, :surname, :city, :phone, :profile, :password)
            """)
            result = conn.execute(user_query, {
                "email": email, "given_name": given_name, "surname": surname,
                "city": city, "phone": phone_number, "profile": profile_description,
                "password": password
            })
            user_id = result.lastrowid
            
            # Insert into CAREGIVER table
            caregiver_query = text("""
                INSERT INTO CAREGIVER (caregiver_user_id, gender, caregiving_type, hourly_rate)
                VALUES (:user_id, :gender, :type, :rate)
            """)
            conn.execute(caregiver_query, {
                "user_id": user_id, "gender": gender,
                "type": caregiving_type, "rate": hourly_rate
            })
    except Exception as e:
        return templates.TemplateResponse("caregiver_form.html", {
            "request": request,
            "caregiver": None,
            "error": f"Database error: {str(e)}"
        }, status_code=500)
    
    return RedirectResponse(url="/web/caregivers", status_code=303)


@app.get("/web/caregivers/delete/{caregiver_id}")
async def delete_caregiver(caregiver_id: int, conn=Depends(get_connection)):
    with conn.begin():
        # Delete from CAREGIVER first (foreign key)
        conn.execute(text("DELETE FROM CAREGIVER WHERE caregiver_user_id = :id"), {"id": caregiver_id})
        # Delete from USER
        conn.execute(text("DELETE FROM USER WHERE user_id = :id"), {"id": caregiver_id})
    
    return RedirectResponse(url="/web/caregivers", status_code=303)


# Members CRUD
@app.get("/web/members", response_class=HTMLResponse)
async def list_members(request: Request, conn=Depends(get_connection)):
    query = text("""
        SELECT m.member_user_id, u.email, u.given_name, u.surname, u.city, u.phone_number
        FROM MEMBER m
        JOIN USER u ON m.member_user_id = u.user_id
        ORDER BY m.member_user_id
    """)
    result = conn.execute(query)
    members = [dict(zip(result.keys(), row)) for row in result.fetchall()]
    return templates.TemplateResponse("members.html", {"request": request, "members": members})


@app.get("/web/members/add", response_class=HTMLResponse)
async def add_member_form(request: Request):
    return templates.TemplateResponse("member_form.html", {"request": request, "member": None})


@app.post("/web/members/add")
async def add_member(
    request: Request,
    email: str = Form(...),
    given_name: str = Form(...),
    surname: str = Form(...),
    city: str = Form(...),
    phone_number: str = Form(...),
    profile_description: Optional[str] = Form(None),
    house_rules: Optional[str] = Form(None),
    dependent_description: Optional[str] = Form(None),
    password: str = Form(...),
    conn=Depends(get_connection)
):
    # phone validation
    if len(phone_number) != 11 or not phone_number.isdigit():
        return templates.TemplateResponse("member_form.html", {
            "request": request,
            "member": None,
            "error": "Phone number must be exactly 11 digits"
        }, status_code=400)
    
    try:
        with conn.begin():
            # Insert into USER table
            user_query = text("""
                INSERT INTO USER (email, given_name, surname, city, phone_number, profile_description, password)
                VALUES (:email, :given_name, :surname, :city, :phone, :profile, :password)
            """)
            result = conn.execute(user_query, {
                "email": email, "given_name": given_name, "surname": surname,
                "city": city, "phone": phone_number, "profile": profile_description,
                "password": password
            })
            user_id = result.lastrowid
            
            # Insert into MEMBER table
            member_query = text("""
                INSERT INTO MEMBER (member_user_id, house_rules, dependent_description)
                VALUES (:user_id, :rules, :dependent)
            """)
            conn.execute(member_query, {
                "user_id": user_id, "rules": house_rules, "dependent": dependent_description
            })
    except Exception as e:
        return templates.TemplateResponse("member_form.html", {
            "request": request,
            "member": None,
            "error": f"Database error: {str(e)}"
        }, status_code=500)
    
    return RedirectResponse(url="/web/members", status_code=303)


@app.get("/web/members/edit/{member_id}", response_class=HTMLResponse)
async def edit_member_form(request: Request, member_id: int, conn=Depends(get_connection)):
    query = text("""
        SELECT m.member_user_id, u.email, u.given_name, u.surname, u.city, 
               u.phone_number, u.profile_description, m.house_rules, m.dependent_description
        FROM MEMBER m
        JOIN USER u ON m.member_user_id = u.user_id
        WHERE m.member_user_id = :id
    """)
    result = conn.execute(query, {"id": member_id})
    row = result.fetchone()
    
    if not row:
        return RedirectResponse(url="/web/members", status_code=303)
    
    member = dict(zip(result.keys(), row))
    return templates.TemplateResponse("member_form.html", {"request": request, "member": member})


@app.post("/web/members/edit/{member_id}")
async def edit_member(
    member_id: int,
    email: str = Form(...),
    given_name: str = Form(...),
    surname: str = Form(...),
    city: str = Form(...),
    phone_number: str = Form(...),
    profile_description: Optional[str] = Form(None),
    house_rules: Optional[str] = Form(None),
    dependent_description: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    conn=Depends(get_connection)
):
    with conn.begin():
        # Update USER table
        if password:
            user_query = text("""
                UPDATE USER SET email = :email, given_name = :given_name, surname = :surname,
                               city = :city, phone_number = :phone, profile_description = :profile,
                               password = :password
                WHERE user_id = :id
            """)
            conn.execute(user_query, {
                "email": email, "given_name": given_name, "surname": surname,
                "city": city, "phone": phone_number, "profile": profile_description,
                "password": password, "id": member_id
            })
        else:
            user_query = text("""
                UPDATE USER SET email = :email, given_name = :given_name, surname = :surname,
                               city = :city, phone_number = :phone, profile_description = :profile
                WHERE user_id = :id
            """)
            conn.execute(user_query, {
                "email": email, "given_name": given_name, "surname": surname,
                "city": city, "phone": phone_number, "profile": profile_description,
                "id": member_id
            })
        
        # Update MEMBER table
        member_query = text("""
            UPDATE MEMBER SET house_rules = :rules, dependent_description = :dependent
            WHERE member_user_id = :id
        """)
        conn.execute(member_query, {
            "rules": house_rules, "dependent": dependent_description, "id": member_id
        })
    
    return RedirectResponse(url="/web/members", status_code=303)


@app.get("/web/members/delete/{member_id}")
async def delete_member(member_id: int, conn=Depends(get_connection)):
    with conn.begin():
        conn.execute(text("DELETE FROM MEMBER WHERE member_user_id = :id"), {"id": member_id})
        conn.execute(text("DELETE FROM USER WHERE user_id = :id"), {"id": member_id})
    
    return RedirectResponse(url="/web/members", status_code=303)


# Appointments CRUD
@app.get("/web/appointments", response_class=HTMLResponse)
async def list_appointments(request: Request, conn=Depends(get_connection)):
    query = text("""
        SELECT a.appointment_id, a.appointment_date, a.appointment_time, 
               a.work_hours, a.status,
               CONCAT(cu.given_name, ' ', cu.surname) as caregiver_name,
               CONCAT(mu.given_name, ' ', mu.surname) as member_name
        FROM APPOINTMENT a
        JOIN USER cu ON a.caregiver_user_id = cu.user_id
        JOIN USER mu ON a.member_user_id = mu.user_id
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """)
    result = conn.execute(query)
    appointments = [dict(zip(result.keys(), row)) for row in result.fetchall()]
    return templates.TemplateResponse("appointments.html", {"request": request, "appointments": appointments})


@app.get("/web/appointments/add", response_class=HTMLResponse)
async def add_appointment_form(request: Request, conn=Depends(get_connection)):
    # Get list of caregivers
    caregivers_query = text("""
        SELECT c.caregiver_user_id, u.given_name, u.surname
        FROM CAREGIVER c
        JOIN USER u ON c.caregiver_user_id = u.user_id
        ORDER BY u.given_name, u.surname
    """)
    caregivers_result = conn.execute(caregivers_query)
    caregivers = [dict(zip(caregivers_result.keys(), row)) for row in caregivers_result.fetchall()]
    
    # Get list of members
    members_query = text("""
        SELECT m.member_user_id, u.given_name, u.surname
        FROM MEMBER m
        JOIN USER u ON m.member_user_id = u.user_id
        ORDER BY u.given_name, u.surname
    """)
    members_result = conn.execute(members_query)
    members = [dict(zip(members_result.keys(), row)) for row in members_result.fetchall()]
    
    return templates.TemplateResponse("appointment_form.html", {
        "request": request,
        "appointment": None,
        "caregivers": caregivers,
        "members": members
    })


@app.post("/web/appointments/add")
async def add_appointment(
    request: Request,
    caregiver_user_id: int = Form(...),
    member_user_id: int = Form(...),
    appointment_date: str = Form(...),
    appointment_time: str = Form(...),
    work_hours: float = Form(...),
    status: str = Form(...),
    conn=Depends(get_connection)
):
    # Validate work hours
    if work_hours <= 0 or work_hours > 24:
        # Get caregivers and members for the form
        caregivers_query = text("""
            SELECT c.caregiver_user_id, u.given_name, u.surname
            FROM CAREGIVER c
            JOIN USER u ON c.caregiver_user_id = u.user_id
            ORDER BY u.given_name, u.surname
        """)
        caregivers_result = conn.execute(caregivers_query)
        caregivers = [dict(zip(caregivers_result.keys(), row)) for row in caregivers_result.fetchall()]
        
        members_query = text("""
            SELECT m.member_user_id, u.given_name, u.surname
            FROM MEMBER m
            JOIN USER u ON m.member_user_id = u.user_id
            ORDER BY u.given_name, u.surname
        """)
        members_result = conn.execute(members_query)
        members = [dict(zip(members_result.keys(), row)) for row in members_result.fetchall()]
        
        return templates.TemplateResponse("appointment_form.html", {
            "request": request,
            "appointment": None,
            "caregivers": caregivers,
            "members": members,
            "error": "Work hours must be between 0.5 and 24 hours"
        }, status_code=400)
    
    try:
        with conn.begin():
            insert_query = text("""
                INSERT INTO APPOINTMENT (caregiver_user_id, member_user_id, appointment_date, 
                                         appointment_time, work_hours, status)
                VALUES (:caregiver_id, :member_id, :date, :time, :hours, :status)
            """)
            conn.execute(insert_query, {
                "caregiver_id": caregiver_user_id,
                "member_id": member_user_id,
                "date": appointment_date,
                "time": appointment_time,
                "hours": work_hours,
                "status": status
            })
    except Exception as e:
        # Get caregivers and members for the form
        caregivers_query = text("""
            SELECT c.caregiver_user_id, u.given_name, u.surname
            FROM CAREGIVER c
            JOIN USER u ON c.caregiver_user_id = u.user_id
            ORDER BY u.given_name, u.surname
        """)
        caregivers_result = conn.execute(caregivers_query)
        caregivers = [dict(zip(caregivers_result.keys(), row)) for row in caregivers_result.fetchall()]
        
        members_query = text("""
            SELECT m.member_user_id, u.given_name, u.surname
            FROM MEMBER m
            JOIN USER u ON m.member_user_id = u.user_id
            ORDER BY u.given_name, u.surname
        """)
        members_result = conn.execute(members_query)
        members = [dict(zip(members_result.keys(), row)) for row in members_result.fetchall()]
        
        return templates.TemplateResponse("appointment_form.html", {
            "request": request,
            "appointment": None,
            "caregivers": caregivers,
            "members": members,
            "error": f"Database error: {str(e)}"
        }, status_code=500)
    
    return RedirectResponse(url="/web/appointments", status_code=303)


@app.get("/web/appointments/edit/{appointment_id}", response_class=HTMLResponse)
async def edit_appointment_form(request: Request, appointment_id: int, conn=Depends(get_connection)):
    # Get appointment data
    appointment_query = text("""
        SELECT a.appointment_id, a.caregiver_user_id, a.member_user_id,
               a.appointment_date, a.appointment_time, a.work_hours, a.status
        FROM APPOINTMENT a
        WHERE a.appointment_id = :id
    """)
    result = conn.execute(appointment_query, {"id": appointment_id})
    row = result.fetchone()
    
    if not row:
        return RedirectResponse(url="/web/appointments", status_code=303)
    
    appointment = dict(zip(result.keys(), row))
    
    # Get list of caregivers
    caregivers_query = text("""
        SELECT c.caregiver_user_id, u.given_name, u.surname
        FROM CAREGIVER c
        JOIN USER u ON c.caregiver_user_id = u.user_id
        ORDER BY u.given_name, u.surname
    """)
    caregivers_result = conn.execute(caregivers_query)
    caregivers = [dict(zip(caregivers_result.keys(), row)) for row in caregivers_result.fetchall()]
    
    # Get list of members
    members_query = text("""
        SELECT m.member_user_id, u.given_name, u.surname
        FROM MEMBER m
        JOIN USER u ON m.member_user_id = u.user_id
        ORDER BY u.given_name, u.surname
    """)
    members_result = conn.execute(members_query)
    members = [dict(zip(members_result.keys(), row)) for row in members_result.fetchall()]
    
    return templates.TemplateResponse("appointment_form.html", {
        "request": request,
        "appointment": appointment,
        "caregivers": caregivers,
        "members": members
    })


@app.post("/web/appointments/edit/{appointment_id}")
async def edit_appointment(
    appointment_id: int,
    request: Request,
    caregiver_user_id: int = Form(...),
    member_user_id: int = Form(...),
    appointment_date: str = Form(...),
    appointment_time: str = Form(...),
    work_hours: float = Form(...),
    status: str = Form(...),
    conn=Depends(get_connection)
):
    # Validate work hours
    if work_hours <= 0 or work_hours > 24:
        # Get appointment data
        appointment_query = text("""
            SELECT a.appointment_id, a.caregiver_user_id, a.member_user_id,
                   a.appointment_date, a.appointment_time, a.work_hours, a.status
            FROM APPOINTMENT a
            WHERE a.appointment_id = :id
        """)
        result = conn.execute(appointment_query, {"id": appointment_id})
        row = result.fetchone()
        appointment = dict(zip(result.keys(), row)) if row else None
        
        # Get caregivers and members
        caregivers_query = text("""
            SELECT c.caregiver_user_id, u.given_name, u.surname
            FROM CAREGIVER c
            JOIN USER u ON c.caregiver_user_id = u.user_id
            ORDER BY u.given_name, u.surname
        """)
        caregivers_result = conn.execute(caregivers_query)
        caregivers = [dict(zip(caregivers_result.keys(), row)) for row in caregivers_result.fetchall()]
        
        members_query = text("""
            SELECT m.member_user_id, u.given_name, u.surname
            FROM MEMBER m
            JOIN USER u ON m.member_user_id = u.user_id
            ORDER BY u.given_name, u.surname
        """)
        members_result = conn.execute(members_query)
        members = [dict(zip(members_result.keys(), row)) for row in members_result.fetchall()]
        
        return templates.TemplateResponse("appointment_form.html", {
            "request": request,
            "appointment": appointment,
            "caregivers": caregivers,
            "members": members,
            "error": "Work hours must be between 0.5 and 24 hours"
        }, status_code=400)
    
    with conn.begin():
        update_query = text("""
            UPDATE APPOINTMENT 
            SET caregiver_user_id = :caregiver_id, member_user_id = :member_id,
                appointment_date = :date, appointment_time = :time,
                work_hours = :hours, status = :status
            WHERE appointment_id = :id
        """)
        conn.execute(update_query, {
            "caregiver_id": caregiver_user_id,
            "member_id": member_user_id,
            "date": appointment_date,
            "time": appointment_time,
            "hours": work_hours,
            "status": status,
            "id": appointment_id
        })
    
    return RedirectResponse(url="/web/appointments", status_code=303)


@app.get("/web/appointments/delete/{appointment_id}")
async def delete_appointment(appointment_id: int, conn=Depends(get_connection)):
    with conn.begin():
        conn.execute(text("DELETE FROM APPOINTMENT WHERE appointment_id = :id"), {"id": appointment_id})
    
    return RedirectResponse(url="/web/appointments", status_code=303)


# Jobs CRUD
@app.get("/web/jobs", response_class=HTMLResponse)
async def list_jobs(request: Request, conn=Depends(get_connection)):
    query = text("""
        SELECT j.job_id, j.required_caregiving_type, j.other_requirements, j.date_posted,
               j.status, j.dependent_age, j.preferred_time_start, j.preferred_time_end,
               j.frequency, j.duration,
               CONCAT(u.given_name, ' ', u.surname) as member_name, u.city
        FROM JOB j
        JOIN USER u ON j.member_user_id = u.user_id
        WHERE j.status = 'open'
        ORDER BY j.date_posted DESC
    """)
    result = conn.execute(query)
    jobs = [dict(zip(result.keys(), row)) for row in result.fetchall()]
    return templates.TemplateResponse("jobs.html", {"request": request, "jobs": jobs})


@app.get("/web/jobs/add", response_class=HTMLResponse)
async def add_job_form(request: Request, conn=Depends(get_connection)):
    # Get members for dropdown
    members_query = text("""
        SELECT m.member_user_id, u.given_name, u.surname
        FROM MEMBER m
        JOIN USER u ON m.member_user_id = u.user_id
        ORDER BY u.given_name, u.surname
    """)
    members_result = conn.execute(members_query)
    members = [dict(zip(members_result.keys(), row)) for row in members_result.fetchall()]
    
    return templates.TemplateResponse("job_form.html", {
        "request": request,
        "job": None,
        "members": members
    })


@app.post("/web/jobs/add")
async def add_job(
    request: Request,
    member_user_id: int = Form(...),
    required_caregiving_type: str = Form(...),
    dependent_age: int = Form(...),
    preferred_time_start: str = Form(...),
    preferred_time_end: str = Form(...),
    frequency: str = Form(...),
    duration: int = Form(...),
    other_requirements: Optional[str] = Form(None),
    conn=Depends(get_connection)
):
    try:
        with conn.begin():
            insert_query = text("""
                INSERT INTO JOB (member_user_id, required_caregiving_type, other_requirements,
                                date_posted, status, dependent_age, preferred_time_start,
                                preferred_time_end, frequency, duration)
                VALUES (:member_id, :type, :requirements, CURDATE(), 'open', :age,
                        :start_time, :end_time, :freq, :dur)
            """)
            conn.execute(insert_query, {
                "member_id": member_user_id,
                "type": required_caregiving_type,
                "requirements": other_requirements,
                "age": dependent_age,
                "start_time": preferred_time_start,
                "end_time": preferred_time_end,
                "freq": frequency,
                "dur": duration
            })
    except Exception as e:
        members_query = text("""
            SELECT m.member_user_id, u.given_name, u.surname
            FROM MEMBER m
            JOIN USER u ON m.member_user_id = u.user_id
            ORDER BY u.given_name, u.surname
        """)
        members_result = conn.execute(members_query)
        members = [dict(zip(members_result.keys(), row)) for row in members_result.fetchall()]
        
        return templates.TemplateResponse("job_form.html", {
            "request": request,
            "job": None,
            "members": members,
            "error": f"Database error: {str(e)}"
        }, status_code=500)
    
    return RedirectResponse(url="/web/jobs", status_code=303)


@app.get("/web/jobs/{job_id}/applicants", response_class=HTMLResponse)
async def view_job_applicants(request: Request, job_id: int, conn=Depends(get_connection)):
    # Get job details
    job_query = text("""
        SELECT j.job_id, j.required_caregiving_type, j.date_posted,
               CONCAT(u.given_name, ' ', u.surname) as member_name
        FROM JOB j
        JOIN USER u ON j.member_user_id = u.user_id
        WHERE j.job_id = :id
    """)
    job_result = conn.execute(job_query, {"id": job_id})
    job_row = job_result.fetchone()
    
    if not job_row:
        return RedirectResponse(url="/web/jobs", status_code=303)
    
    job = dict(zip(job_result.keys(), job_row))
    
    # Get applicants
    applicants_query = text("""
        SELECT ja.application_id, ja.application_date, ja.application_status, ja.cover_letter,
               c.caregiver_user_id, u.given_name, u.surname, u.email, u.phone_number, u.city,
               c.gender, c.caregiving_type, c.hourly_rate, c.rating
        FROM JOB_APPLICATION ja
        JOIN CAREGIVER c ON ja.caregiver_user_id = c.caregiver_user_id
        JOIN USER u ON c.caregiver_user_id = u.user_id
        WHERE ja.job_id = :id
        ORDER BY ja.application_date DESC
    """)
    applicants_result = conn.execute(applicants_query, {"id": job_id})
    applicants = [dict(zip(applicants_result.keys(), row)) for row in applicants_result.fetchall()]
    
    return templates.TemplateResponse("job_applicants.html", {
        "request": request,
        "job": job,
        "applicants": applicants
    })


@app.post("/web/jobs/apply/{job_id}")
async def apply_to_job(
    job_id: int,
    caregiver_user_id: int = Form(...),
    cover_letter: Optional[str] = Form(None),
    conn=Depends(get_connection)
):
    try:
        with conn.begin():
            insert_query = text("""
                INSERT INTO JOB_APPLICATION (job_id, caregiver_user_id, application_date,
                                            application_status, cover_letter)
                VALUES (:job_id, :caregiver_id, CURDATE(), 'pending', :cover)
            """)
            conn.execute(insert_query, {
                "job_id": job_id,
                "caregiver_id": caregiver_user_id,
                "cover": cover_letter
            })
    except Exception as e:
        return {"error": str(e)}
    
    return RedirectResponse(url="/web/jobs", status_code=303)


# Addresses CRUD
@app.get("/web/addresses", response_class=HTMLResponse)
async def list_addresses(request: Request, conn=Depends(get_connection)):
    query = text("""
        SELECT a.address_id, a.house_number, a.street, a.town,
               CONCAT(u.given_name, ' ', u.surname) as member_name
        FROM ADDRESS a
        JOIN USER u ON a.member_user_id = u.user_id
        ORDER BY a.address_id
    """)
    result = conn.execute(query)
    addresses = [dict(zip(result.keys(), row)) for row in result.fetchall()]
    return templates.TemplateResponse("addresses.html", {"request": request, "addresses": addresses})
