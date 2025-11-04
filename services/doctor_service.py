from werkzeug.security import generate_password_hash

from models.main_models import Department, Doctor


def create_doctor(session, name, email, password, age, contact, specialization, department_id):
    """Creates and commits a new Doctor record."""
    # Validate department
    dep = session.get(Department, department_id)
    if not dep:
        raise ValueError("Department does not exist")

    hashed_pw = generate_password_hash(password)
    doctor = Doctor(
        name=name,
        email=email,
        password=hashed_pw,
        age=int(age),
        contact=contact,
        specialization=specialization,
        department_id=department_id,
    )
    session.add(doctor)
    session.commit()
    return doctor