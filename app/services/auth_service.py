from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password

def create_user(db: Session, user: UserCreate):
    # Check if email exists
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise ValueError("Email already registered.")

    # Check if username exists
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise ValueError("Username already taken.")

    hashed = hash_password(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed,
        dob=user.dob
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
