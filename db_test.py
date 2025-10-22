from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.main_models import Appointment, AppointmentStatus, Base, Department, Doctor, Patient, Treatment
from datetime import date, time

engine = create_engine("sqlite:///test.db", echo=True)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# ---------------------------------------------------------
# TEST TRANSACTIONS
# ---------------------------------------------------------
try:
    # 1. Create Department
    cardiology = Department(name="Cardiology", description="Heart-related treatments")
    session.add(cardiology)
    session.commit()
    print(f"Created Department: {cardiology.name}")

    # 2. Create Doctor
    doctor = Doctor(name="Dr. A. Smith", specialization="Cardiologist", email="asmith@hospital.com", department=cardiology)
    session.add(doctor)
    session.commit()
    print(f"Created Doctor: {doctor.name}")

    # 3. Create Patient
    patient = Patient(name="John Doe", age=45, contact="1234567890", email="john.doe@example.com")
    session.add(patient)
    session.commit()
    print(f"Created Patient: {patient.name}")

    # 4. Create Appointment
    appointment = Appointment(
        patient=patient,
        doctor=doctor,
        date=date.today(),
        time=time(10, 30),
        status=AppointmentStatus.BOOKED
    )
    session.add(appointment)
    session.commit()
    print(f"Appointment booked with {doctor.name} for {patient.name}")

    # 5. Add Treatment details
    treatment = Treatment(
        appointment=appointment,
        diagnosis="Hypertension",
        prescription="Amlodipine 5mg daily",
        notes="Monitor blood pressure regularly"
    )
    session.add(treatment)
    session.commit()
    print("Treatment record added.")

    # 6. Query back the data
    print("\n--- Query Results ---")
    appts = session.query(Appointment).all()
    for a in appts:
        print(f"Appointment #{a.id}: {a.patient.name} with {a.doctor.name} on {a.date} at {a.time}")
        if a.treatment:
            print(f"  Diagnosis: {a.treatment.diagnosis}")
            print(f"  Prescription: {a.treatment.prescription}")
            print(f"  Notes: {a.treatment.notes}")

finally:
    session.close()
