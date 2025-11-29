from __future__ import annotations

import random
from datetime import date, time, timedelta, datetime
from werkzeug.security import generate_password_hash

from models.main_models import (
    SessionLocal, Department, Appointment, Doctor, Patient,
    AppointmentStatus, DoctorAvailability, Medicine, Treatment, Admin, AvailabilitySlot
)

# ----------------------------------------------------------
# Helper — random DOB in age range
# ----------------------------------------------------------
def random_dob(min_age: int, max_age: int) -> date:
    today = date.today()
    age = random.randint(min_age, max_age)
    year = today.year - age
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


# ----------------------------------------------------------
# Name pools
# ----------------------------------------------------------
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Kabir", "Krishna", "Arjun",
    "Sarah", "Mira", "Priya", "Anika", "John", "Alex", "Maya",
    "Riya", "Zoya", "Omar", "Fatima", "Neha", "Lina"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Singh", "Khan", "Kapoor",
    "Nair", "Iyer", "Banerjee", "Gupta", "Mishra", "Das", "Roy"
]

SPECIALIZATION_MAP = {
    "Cardiology": "Cardiologist",
    "Neurology": "Neurologist",
    "Orthopedics": "Orthopedic Surgeon",
    "Pediatrics": "Pediatrician",
    "Dermatology": "Dermatologist",
    "Oncology": "Oncologist",
    "Psychiatry": "Psychiatrist",
    "Radiology": "Radiologist",
    "ENT": "ENT Specialist",
    "General Medicine": "General Physician",
}

DIAGNOSES = {
    "Cardiologist": ["Hypertension", "Arrhythmia", "Chest Pain"],
    "Neurologist": ["Migraine", "Epilepsy", "Neuropathy"],
    "Orthopedic Surgeon": ["Fracture", "Arthritis", "Back Pain"],
    "Pediatrician": ["Fever", "Common Cold", "Infection"],
    "Dermatologist": ["Allergy", "Eczema", "Rash"],
    "Oncologist": ["Cancer Check", "Chemotherapy Review"],
    "Psychiatrist": ["Anxiety", "Depression", "Insomnia"],
    "Radiologist": ["X-Ray Review", "MRI Report"],
    "ENT Specialist": ["Ear Infection", "Sinusitis"],
    "General Physician": ["Flu", "Weakness", "Checkup"],
}

MEDICINE_OPTIONS = {
    "Hypertension": ["Amlodipine 5mg", "Losartan 50mg"],
    "Migraine": ["Ibuprofen 400mg", "Sumatriptan 50mg"],
    "Fracture": ["Calcium 500mg", "Vitamin D3"],
    "Eczema": ["Cetirizine", "Hydrocortisone Cream"],
    "Allergy": ["Cetrizine", "Allegra"],
    "Anxiety": ["Escitalopram", "Clonazepam"],
    "Fever": ["Paracetamol 500mg"],
    "Chest Pain": ["Aspirin 75mg"],
    "Flu": ["Cough Syrup", "Dolo 650"],
}

INSTRUCTIONS = [
    "Take after meals",
    "Take before breakfast",
    "Do not skip doses",
    "Drink plenty of water"
]

VISIT_TYPES = ["Checkup", "Follow-up", "Emergency"]
TESTS = ["Blood Test", "X-Ray", "ECG", "MRI", "None"]


# ----------------------------------------------------------
# Create All Dummy Data
# ----------------------------------------------------------
def create_dummy_data():
    with SessionLocal() as session:
        seed_admin(session)
        departments = seed_departments(session)
        doctors = seed_doctors(session, departments)
        patients = seed_patients(session)
        seed_availability(session, doctors)
        seed_appointments(session, doctors, patients)
        session.commit()


# ----------------------------------------------------------
# Admin
# ----------------------------------------------------------
def seed_admin(session):
    session.add(Admin(
        name="Admin User",
        email="admin@admin.com",
        password=generate_password_hash("123"),
        dob=date(1980, 1, 1),
        contact="+91 9999999999",
        is_blacklisted=False
    ))


# ----------------------------------------------------------
# Departments
# ----------------------------------------------------------
def seed_departments(session):
    dept_objs = []
    desc = "Specialized department offering diagnostic and therapeutic healthcare."

    for dept_name in SPECIALIZATION_MAP.keys():
        dept_objs.append(
            Department(name=dept_name, description=desc)
        )

    session.add_all(dept_objs)
    session.flush()
    return dept_objs


# ----------------------------------------------------------
# Doctors
# ----------------------------------------------------------
def seed_doctors(session, departments):
    doctors = []
    counter = 1

    for dept in departments:
        for _ in range(3):  # 3 per department = 30 doctors
            f = random.choice(FIRST_NAMES)
            l = random.choice(LAST_NAMES)

            doc = Doctor(
                name=f"{f} {l}",
                email=f"doc{counter}@h.com",   # 🔥 simple predictable email
                password=generate_password_hash("123"),
                dob=random_dob(30, 60),
                contact=f"+91 {random.randint(7000000000,9999999999)}",
                specialization=SPECIALIZATION_MAP[dept.name],
                department_id=dept.id,
                is_blacklisted=False,
            )
            session.add(doc)
            doctors.append(doc)
            counter += 1

    session.flush()
    return doctors


# ----------------------------------------------------------
# Patients
# ----------------------------------------------------------
def seed_patients(session):
    patients = []

    for i in range(1, 101):
        f = random.choice(FIRST_NAMES)
        l = random.choice(LAST_NAMES)

        p = Patient(
            name=f"{f} {l}",
            email=f"pat{i}@h.com",      # 🔥 simple email
            password=generate_password_hash("123"),
            dob=random_dob(10, 85),
            contact=f"+91 {random.randint(6000000000,9999999999)}",
            is_blacklisted=False
        )
        session.add(p)
        patients.append(p)

    session.flush()
    return patients


# ----------------------------------------------------------
# Availability — current week only (Mon–Sun)
# ----------------------------------------------------------
def seed_availability(session, doctors):

    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_days = [week_start + timedelta(days=i) for i in range(7)]  # Mon–Sun

    slots = [
        AvailabilitySlot.MORNING,
        AvailabilitySlot.AFTERNOON,
        AvailabilitySlot.EVENING
    ]

    for doc in doctors:
        for d in week_days:
            for slot in slots:

                probability = {
                    AvailabilitySlot.MORNING: 0.7,
                    AvailabilitySlot.AFTERNOON: 0.6,
                    AvailabilitySlot.EVENING: 0.3,
                }[slot]

                session.add(DoctorAvailability(
                    doctor_id=doc.id,
                    date=d,
                    slot=slot,
                    enabled=random.random() < probability,
                ))


# ----------------------------------------------------------
# Appointments + Treatments
# ----------------------------------------------------------
def seed_appointments(session, doctors, patients):

    for _ in range(120):
        patient = random.choice(patients)
        doctor = random.choice(doctors)

        # 60% upcoming BOOKED, 40% past COMPLETED
        if random.random() < 0.6:
            appt_date = date.today() + timedelta(days=random.randint(1, 20))
            status = AppointmentStatus.BOOKED
        else:
            appt_date = date.today() - timedelta(days=random.randint(1, 30))
            status = AppointmentStatus.COMPLETED

        appt_time = time(
            hour=random.choice([9, 10, 11, 14, 15, 16]),
            minute=random.choice([0, 15, 30, 45])
        )

        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            date=appt_date,
            time=appt_time,
            status=status,
            visit_type=random.choice(VISIT_TYPES),
            test_done=random.choice(TESTS),
            original_date=None,
            original_time=None,
            reschedule_count=0,
        )
        session.add(appt)
        session.flush()

        if status == AppointmentStatus.COMPLETED:
            diagnosis = random.choice(DIAGNOSES[doctor.specialization])

            treatment = Treatment(
                appointment_id=appt.id,
                diagnosis=diagnosis,
                prescription=random.choice(MEDICINE_OPTIONS.get(diagnosis, ["Paracetamol 500mg"])),
                notes=random.choice([
                    "Follow-up required",
                    "Patient improving",
                    "Prescribed rest",
                    "Review in 1 week"
                ]),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(treatment)
            session.flush()

            for _ in range(random.randint(1, 3)):
                session.add(Medicine(
                    treatment_id=treatment.id,
                    name=random.choice(MEDICINE_OPTIONS.get(diagnosis, ["Paracetamol"])),
                    morning=random.randint(0, 1),
                    afternoon=random.randint(0, 1),
                    night=random.randint(0, 1),
                    duration_days=random.randint(3, 14),
                    instructions=random.choice(INSTRUCTIONS)
                ))

    session.flush()
