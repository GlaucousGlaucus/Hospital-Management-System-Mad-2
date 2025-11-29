from models.main_models import Doctor, Department

def create_doctor(session, name, email, password, dob, contact, specialization, department_id):
    """Creates and commits a new Doctor record."""

    dep = session.get(Department, department_id)
    if not dep:
        raise ValueError("Department does not exist")

    doctor = Doctor.create_user(
        session,
        name=name,
        email=email,
        password=password,
        dob=dob,
        contact=contact,
        specialization=specialization,
        department_id=department_id,
    )

    return doctor
