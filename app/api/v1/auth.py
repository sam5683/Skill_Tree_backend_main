from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import create_user, authenticate
from app.core.security import create_access_token, verify_password
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from app.models.user import User

router = APIRouter()
oauth = OAuth()

#  REGISTER
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = create_user(db, user)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# Authentication using http cookie jwt

@router.post("/auth/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate(db, form_data.username)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong password")

    token = create_access_token({"sub": str(user.id)})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure= False,   # True in production HTTPS
        samesite="lax",
        max_age=60 * 60 * 24
    )

    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@router.post("/auth/logout")
def logout(response: Response):

    response.delete_cookie(
        key="access_token"
    )

    return {
        "message": "Logged out successfully"
    }



oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)



@router.get("/auth/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )


@router.get("/auth/google/callback", name="google_callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    import random
    import re

    token = await oauth.google.authorize_access_token(request)

    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(
            status_code=400,
            detail="Google login failed"
        )

    email = user_info["email"]

    # -----------------------------------
    # CHECK IF USER EXISTS
    # -----------------------------------
    user = db.query(User).filter(
        User.email == email
    ).first()

    # -----------------------------------
    # CREATE USER IF NOT EXISTS
    # -----------------------------------
    if not user:

        # email prefix
        base_username = email.split("@")[0].lower()

        # remove invalid characters
        base_username = re.sub(
            r"[^a-zA-Z0-9_]",
            "",
            base_username
        )

        # fallback safety
        if not base_username:
            base_username = "user"

        # generate unique username
        while True:

            discriminator = random.randint(3000, 9999)

            username = f"{base_username}#{discriminator}"

            existing_user = db.query(User).filter(
                User.username == username
            ).first()

            if not existing_user:
                break

        user = User(
            email=email,
            username=username,
            hashed_password=""
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    # -----------------------------------
    # CREATE JWT
    # -----------------------------------
    access_token = create_access_token({
        "sub": str(user.id)
    })

    # -----------------------------------
    # REDIRECT TO FRONTEND
    # -----------------------------------
    response = RedirectResponse(
        url="https://skill-tree-mocha.vercel.app/dashboard.html",
        status_code=302
    )

    # -----------------------------------
    # STORE COOKIE
    # -----------------------------------
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,

        # LOCALHOST
        secure=True,
        samesite="none",

        # PRODUCTION LATER:
        # secure=True,
        # samesite="none",

        max_age=60 * 60 * 24,
        path="/"
    )

    return response