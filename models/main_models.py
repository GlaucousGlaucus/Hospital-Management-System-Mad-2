from __future__ import annotations

import enum
from datetime import date, time, datetime
from typing import List, Optional
from logging import getLogger

from sqlalchemy import (
    Enum,
    ForeignKey,
    String,
    Text,
    create_engine,
    Integer,
    Boolean,
    UniqueConstraint,
    DateTime,
    event,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    scoped_session,
    sessionmaker
)
from werkzeug.security import check_password_hash, generate_password_hash

from utils.constants import DB_PATH

logger = getLogger(__name__)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# Enable foreign keys on SQLite
@event.listens_for(engine, "connect")
def enable_sqlite_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = scoped_session(sessionmaker(bind=engine))


class Base(DeclarativeBase):
    pass


class AppointmentStatus(enum.Enum):
    BOOKED = "Booked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class AvailabilitySlot(enum.Enum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    EVENING = "Evening"


class UserMixin:
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password: Mapped[str] = mapped_column(String(128))
    dob: Mapped[Optional[date]]
    contact: Mapped[Optional[str]] = mapped_column(String(50))
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def age(self) -> Optional[int]:
        if not self.dob:
            return None
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

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

    doctors: Mapped[List["Doctor"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan"
    )


class Doctor(UserMixin, Base):
    __tablename__ = "doctors"

    specialization: Mapped[Optional[str]] = mapped_column(String(100))

    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL")
    )

    department: Mapped[Optional[Department]] = relationship(back_populates="doctors")

    appointments: Mapped[List["Appointment"]] = relationship(
        back_populates="doctor",
        cascade="all, delete-orphan"
    )

    availability: Mapped[List["DoctorAvailability"]] = relationship(
        back_populates="doctor",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"{self.name} {self.email} ({self.specialization})"


class Patient(UserMixin, Base):
    __tablename__ = "patients"

    appointments: Mapped[List["Appointment"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan"
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE")
    )

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE")
    )

    date: Mapped[date]
    time: Mapped[time]

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.BOOKED
    )

    visit_type: Mapped[Optional[str]]
    test_done: Mapped[Optional[str]]

    original_date: Mapped[Optional[date]]
    original_time: Mapped[Optional[time]]
    reschedule_count: Mapped[int] = mapped_column(Integer, default=0)

    patient: Mapped[Patient] = relationship(back_populates="appointments")
    doctor: Mapped[Doctor] = relationship(back_populates="appointments")

    treatment: Mapped[Optional["Treatment"]] = relationship(
        back_populates="appointment",
        cascade="all, delete-orphan",
        uselist=False
    )


class Treatment(Base):
    __tablename__ = "treatments"

    id: Mapped[int] = mapped_column(primary_key=True)

    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE")
    )

    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    prescription: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    appointment: Mapped["Appointment"] = relationship(back_populates="treatment")

    medicines: Mapped[List["Medicine"]] = relationship(
        back_populates="treatment",
        cascade="all, delete-orphan"
    )


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(primary_key=True)

    treatment_id: Mapped[int] = mapped_column(
        ForeignKey("treatments.id", ondelete="CASCADE")
    )

    name: Mapped[str] = mapped_column(String(255))
    morning: Mapped[int] = mapped_column(Integer, default=0)
    afternoon: Mapped[int] = mapped_column(Integer, default=0)
    night: Mapped[int] = mapped_column(Integer, default=0)

    duration_days: Mapped[int] = mapped_column(Integer, default=1)
    instructions: Mapped[Optional[str]] = mapped_column(String(255))

    treatment: Mapped["Treatment"] = relationship(back_populates="medicines")


class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    __table_args__ = (
        UniqueConstraint("doctor_id", "date", "slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE")
    )

    date: Mapped[date]
    slot: Mapped[AvailabilitySlot] = mapped_column(Enum(AvailabilitySlot))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    doctor: Mapped[Doctor] = relationship(back_populates="availability")
