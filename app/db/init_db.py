from .session import Base, engine
from app.db.base import Base
from app.models import user, note, skill, memory_card

def init_db():
    Base.metadata.create_all(bind=engine)
