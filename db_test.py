from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.main_models import Base, Admin, Department, Doctor, Patient, Appointment, Treatment, AppointmentStatus

engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

cardiology = Department(name="Cardiology", description="Heart-related treatments")

doctor = Doctor(name="Dr. Smith", email="smith@example.com", specialization="Cardiology", department=cardiology)

patient = Patient(name="John Doe", age=40, contact="1234567890", email="john@example.com")

appointment = Appointment(patient=patient, doctor=doctor, date=date.today(), time=time(10, 0))

treatment = Treatment(appointment=appointment, diagnosis="Hypertension", prescription="Atenolol")

session.add_all([cardiology, doctor, patient, appointment, treatment])
session.commit()

# all_departments = session.query(Department).all()
# print("Departments:", all_departments)
#
# all_doctors = session.query(Doctor).all()
# print("Doctors:", all_doctors)
#
# appointments = session.query(Appointment).filter_by(status=AppointmentStatus.BOOKED).all()
# print("Appointments:", appointments)


# appointment = session.query(Appointment).first()
# appointment.status = AppointmentStatus.COMPLETED
# session.commit()
#
# doctor_to_remove = session.query(Doctor).filter_by(name="Dr. Smith").first()
# session.delete(doctor_to_remove)
# session.commit()
