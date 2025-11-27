from __future__ import annotations
from __future__ import annotations

import random
from datetime import date, time, timedelta

from werkzeug.security import generate_password_hash

from models.main_models import SessionLocal, Department, Appointment, Doctor, Patient, AppointmentStatus, \
    DoctorAvailability, Medicine, Treatment, Admin


def create_dummy_data():
    with SessionLocal() as session:
        seed_admin(session)
        departments = seed_departments(session)
        doctors = seed_doctors(session, departments)
        patients = seed_patients(session)
        seed_availability(session, doctors)
        seed_appointments_with_treatments(session, doctors, patients)

        session.commit()

def seed_admin(session):
    admin = Admin(
        name="Admin",
        email="admin@admin.com",
        password=generate_password_hash("123"),
        age=40,
        contact="+91 9999999999",
    )
    session.add(admin)

def seed_departments(session):
    department_names = [
        "Cardiology", "Neurology", "Orthopedics", "Pediatrics",
        "Dermatology", "Oncology", "Psychiatry", "Radiology",
        "ENT", "General Medicine",
    ]

    departments = [
        Department(name=name, description=f"{name} Department")
        for name in department_names
    ]
    session.add_all(departments)
    session.flush()
    return departments


def seed_doctors(session, departments):
    specializations = [
        "Cardiologist", "Neurologist", "Orthopedic Surgeon",
        "Pediatrician", "Dermatologist", "Oncologist",
        "Psychiatrist", "Radiologist", "ENT Specialist", "General Physician",
    ]

    doctors = []
    for i in range(30):
        dept = random.choice(departments)
        doc = Doctor(
            name=f"Dr. {random.choice(['John','Alex','Mira','Sara','Raj','Lina','Omar','Nina'])} {i}",
            email=f"doctor{i}@hospital.com",
            password=generate_password_hash("123"),
            age=random.randint(30, 65),
            contact=f"+91 {random.randint(7000000000, 9999999999)}",
            specialization=random.choice(specializations),
            department_id=dept.id,
        )
        doctors.append(doc)

    session.add_all(doctors)
    session.flush()
    return doctors


def seed_patients(session):
    patients = []
    for i in range(100):
        patient = Patient(
            name=f"Patient {i}",
            email=f"patient{i}@example.com",
            password=generate_password_hash("123"),
            age=random.randint(10, 90),
            contact=f"+91 {random.randint(6000000000, 9999999999)}",
        )
        patients.append(patient)

    session.add_all(patients)
    session.flush()
    return patients


def seed_availability(session, doctors):
    slots = ["morning", "afternoon", "evening"]
    today = date.today()
    days = [today + timedelta(days=i) for i in range(7)]

    for doc in doctors:
        for d in days:
            for slot in slots:
                entry = DoctorAvailability(
                    doctor_id=doc.id,
                    date=d,
                    slot=slot,
                    enabled=random.choice([True, False])
                )
                session.add(entry)

    session.flush()


def seed_appointments_with_treatments(session, doctors, patients):
    medicine_names = [
        "Paracetamol", "Amoxicillin", "Ibuprofen", "Cetirizine",
        "Ranitidine", "Metformin", "Aspirin", "Azithromycin",
        "Cough Syrup", "Vitamin D", "Calcium Tablet"
    ]

    visit_types = ["Checkup", "Follow-up", "Emergency"]
    tests_done = ["Blood Test", "X-Ray", "ECG", "MRI", "None"]
    statuses = list(AppointmentStatus)

    for _ in range(120):
        patient = random.choice(patients)
        doctor = random.choice(doctors)

        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            date=date.today() - timedelta(days=random.randint(0, 30)),
            time=time(hour=random.randint(8, 17), minute=random.choice([0, 15, 30, 45])),
            status=random.choice(statuses),
            visit_type=random.choice(visit_types),
            test_done=random.choice(tests_done),
        )
        session.add(appt)
        session.flush()

        if appt.status in [AppointmentStatus.BOOKED, AppointmentStatus.COMPLETED]:
            treatment = Treatment(
                appointment_id=appt.id,
                diagnosis=random.choice([
                    "Hypertension", "Migraine", "Fracture", "Allergy",
                    "Diabetes", "Anxiety"
                ]),
                prescription=random.choice([
                    "Paracetamol 500mg", "Amoxicillin 250mg", "Ibuprofen 400mg",
                    "Vitamin D supplement"
                ]),
                notes=random.choice([
                    "Follow-up required", "Patient improving",
                    "Schedule recheck", "Prescribed rest"
                ]),
            )
            session.add(treatment)
            session.flush()

            for _ in range(random.randint(0, 3)):
                med = Medicine(
                    treatment_id=treatment.id,
                    name=random.choice(medicine_names),
                    morning=random.randint(0, 2),
                    afternoon=random.randint(0, 2),
                    night=random.randint(0, 2),
                )
                session.add(med)

    session.flush()
