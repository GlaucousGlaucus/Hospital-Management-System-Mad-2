from __future__ import annotations

import enum
import random
from datetime import date, time, timedelta
from typing import List, Optional
from logging import getLogger

from sqlalchemy import Enum, ForeignKey, String, Text, create_engine, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

from utils.constants import DB_PATH

logger = getLogger(__name__)
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = scoped_session(sessionmaker(bind=engine))

def setup_db():
    if DB_PATH.exists():
        return

    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        admin = Admin(
            name="Admin",
            email="admin@admin.com",
            password=generate_password_hash("123"),
            age=40,
            contact="+91 9999999999",
        )
        session.add(admin)

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

        specializations = [
            "Cardiologist", "Neurologist", "Orthopedic Surgeon",
            "Pediatrician", "Dermatologist", "Oncologist",
            "Psychiatrist", "Radiologist", "ENT Specialist", "General Physician",
        ]
        doctors = []
        for i in range(30):
            dept = random.choice(departments)
            doc = Doctor(
                name=f"Dr. {random.choice(['John', 'Alex', 'Mira', 'Sara', 'Raj', 'Lina', 'Omar', 'Nina'])} {i}",
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

        medicine_names = [
            "Paracetamol", "Amoxicillin", "Ibuprofen", "Cetirizine",
            "Ranitidine", "Metformin", "Aspirin", "Azithromycin",
            "Cough Syrup", "Vitamin D", "Calcium Tablet"
        ]

        statuses = list(AppointmentStatus)
        visit_types = ["Checkup", "Follow-up", "Emergency"]
        tests_done = ["Blood Test", "X-Ray", "ECG", "MRI", "None"]

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
                        "Hypertension", "Migraine", "Fracture", "Allergy", "Diabetes", "Anxiety"
                    ]),
                    prescription=random.choice([
                        "Paracetamol 500mg", "Amoxicillin 250mg", "Ibuprofen 400mg", "Vitamin D supplement"
                    ]),
                    notes=random.choice([
                        "Follow-up required", "Patient improving", "Schedule recheck", "Prescribed rest"
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
        session.commit()


class Base(DeclarativeBase):
    pass

# TODO: Rescheduling
class AppointmentStatus(enum.Enum):
    BOOKED = "Booked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class UserMixin:
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password: Mapped[str] = mapped_column(String(128))
    age: Mapped[Optional[int]]
    contact: Mapped[Optional[str]] = mapped_column(String(50))

    @classmethod
    def create_user(cls, session: SessionLocal, **kwargs):
        user = cls(**kwargs)
        session.add(user)
        session.commit()
        return user

    def check_password(self, plain: str) -> bool:
        return check_password_hash(self.password, plain)

class Admin(UserMixin, Base):
    __tablename__ = "admins"

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]]
    doctors: Mapped[List[Doctor]] = relationship(back_populates="department")

class Doctor(UserMixin, Base):
    __tablename__ = "doctors"

    specialization: Mapped[Optional[str]] = mapped_column(String(100))

    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    department: Mapped[Optional[Department]] = relationship(back_populates="doctors")

    appointments: Mapped[List[Appointment]] = relationship(back_populates="doctor")
    availability: Mapped[list["DoctorAvailability"]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"{self.name} {self.email} ({self.specialization})"


class Patient(UserMixin, Base):
    __tablename__ = "patients"

    appointments: Mapped[List[Appointment]] = relationship(back_populates="patient")

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey(Patient.id))
    doctor_id: Mapped[int] = mapped_column(ForeignKey(Doctor.id))
    date: Mapped[date]
    time: Mapped[time]
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.BOOKED)
    visit_type: Mapped[Optional[str]]
    test_done: Mapped[Optional[str]]

    patient: Mapped[Patient] = relationship(back_populates="appointments")
    doctor: Mapped[Doctor] = relationship(back_populates="appointments")
    # TODO: There might be multiple treatments given to a single patient during a single appointment
    treatment: Mapped[Optional[Treatment]] = relationship(back_populates="appointment", uselist=False)

class Treatment(Base):
    __tablename__ = "treatments"

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"))
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    prescription: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    appointment: Mapped[Appointment] = relationship(back_populates="treatment")

    medicines: Mapped[List["Medicine"]] = relationship(
        back_populates="treatment",
        cascade="all, delete-orphan"
    )

class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(primary_key=True)
    treatment_id: Mapped[int] = mapped_column(ForeignKey("treatments.id"))

    name: Mapped[str] = mapped_column(String(255))
    morning: Mapped[int] = mapped_column(Integer, default=0)
    afternoon: Mapped[int] = mapped_column(Integer, default=0)
    night: Mapped[int] = mapped_column(Integer, default=0)

    treatment: Mapped["Treatment"] = relationship(back_populates="medicines")

class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    date: Mapped[date]
    slot: Mapped[str] = mapped_column(String(20))
    enabled: Mapped[bool] = mapped_column(default=False)

    doctor: Mapped[Doctor] = relationship(back_populates="availability")
