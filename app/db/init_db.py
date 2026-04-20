from .session import Base, engine
from app.models import user, note, skill, memory_card

def init_db():
    Base.metadata.create_all(bind=engine)
