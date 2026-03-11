from datetime import date

from werkzeug.security import generate_password_hash

from models.main_models import Base, engine, SessionLocal, Admin
from utils.constants import DB_PATH
from utils.sample_data import create_dummy_data


def setup_db():
    db_exists = DB_PATH.exists()
    Base.metadata.create_all(engine)

    if db_exists:
        return

    with SessionLocal() as session:
        session.add(Admin(
            name="Admin User",
            email="admin@admin.com",
            password=generate_password_hash("123"),
            dob=date(1980, 1, 1),
            contact="+91 9999999999",
            is_blacklisted=False
        ))
        session.commit()
    create_dummy_data()
