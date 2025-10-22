from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from models.main_models import Base
from logging import getLogger

from utils.constants import DB_PATH

logger = getLogger(__name__)

app = Flask(__name__)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

if not DB_PATH.exists():
    Base.metadata.create_all(engine)
    logger.info(f"DB created at {DB_PATH}")
else:
    logger.info(f"DB already exists at {DB_PATH}")

# Session factory
SessionLocal = scoped_session(sessionmaker(bind=engine))

@app.teardown_appcontext
def shutdown_session(exception=None):
    """
    Ensure the session is closed after each request.
    We don't want to leave any sessions open otherwise bad things can happen.
    """
    SessionLocal.remove()

@app.route('/')
def index():
    return render_template('index.html')

