from pydantic import BaseModel, EmailStr
from datetime import date
class UserBase(BaseModel):
    username: str
    email: EmailStr
    dob: date 
    
class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int

    model_config = {
        "from_attributes": True
    }
