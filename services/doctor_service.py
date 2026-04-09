from models.main_models import Doctor, Department


def create_doctor(session, name, email, password, dob, contact, specialization, department_id):
    dep = session.get(Department, department_id)
    if not dep:
        raise ValueError("Department does not exist")

    return Doctor.create_user(
        session,
        name=name,
        email=email,
        password=password,
        dob=dob,
        contact=contact,
        specialization=specialization,
        department_id=department_id,
    )
