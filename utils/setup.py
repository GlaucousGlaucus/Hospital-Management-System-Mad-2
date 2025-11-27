from models.main_models import Base, engine
from utils.constants import DB_PATH
from utils.sample_data import create_dummy_data


def setup_db():
    if DB_PATH.exists():
        return
    Base.metadata.create_all(engine)
    create_dummy_data()
