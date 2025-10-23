from __future__ import annotations

import enum
from datetime import date, time
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

# TODO: Rescheduling
class AppointmentStatus(enum.Enum):
    BOOKED = "Booked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password: Mapped[str] = mapped_column(String(128))

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]]
    doctors: Mapped[List[Doctor]] = relationship(back_populates="department")

class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password: Mapped[str] = mapped_column(String(128))
    specialization: Mapped[Optional[str]] = mapped_column(String(100))

    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    department: Mapped[Optional[Department]] = relationship(back_populates="doctors")

    appointments: Mapped[List[Appointment]] = relationship(back_populates="doctor")

    def __repr__(self):
        return f"{self.name} {self.email} ({self.specialization})"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    age: Mapped[Optional[int]]
    contact: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True)
    password: Mapped[str] = mapped_column(String(128))

    appointments: Mapped[List[Appointment]] = relationship(back_populates="patient")

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey(Patient.id))
    doctor_id: Mapped[int] = mapped_column(ForeignKey(Doctor.id))
    date: Mapped[date]
    time: Mapped[time]
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.BOOKED)

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
