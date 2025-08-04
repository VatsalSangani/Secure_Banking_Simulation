from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.schemas.user import UserCreate, UserOut, LoginRequest
from app.schemas.token import Token
from app.services.auth_service import register_user, authenticate_user
from app.core.security import decode_access_token, create_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.utils.otp import create_and_store_otp, verify_otp, send_otp_email
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/verify")  # or just dummy endpoint

router = APIRouter()

# ────────────────────────────────
# Utilities
# ────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ────────────────────────────────
# Register
# ────────────────────────────────
@router.post("/register", response_model=UserOut)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, user_data)

# ────────────────────────────────
# Login Step 1: Send OTP
# ────────────────────────────────
@router.post("/login")
def login_for_otp(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    otp = create_and_store_otp(user.id)
    send_otp_email(user.email, otp)
    return {"msg": "OTP sent to your email. Please verify to complete login."}

# ────────────────────────────────
# Login Step 2: Verify OTP and Issue Token
# ────────────────────────────────
class OTPVerifyRequest(BaseModel):
    username: str
    otp_code: str

@router.post("/login/verify", response_model=Token)
def verify_login_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_otp(user.id, payload.otp_code):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# ────────────────────────────────
# Authenticated User Info
# ────────────────────────────────
@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
