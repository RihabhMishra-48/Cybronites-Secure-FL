from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
import sqlite3
from Cybronites.server.db import get_db, settings
import uuid
import logging
import bcrypt

# Setup logging
logger = logging.getLogger("GuardianAuth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# --- Pydantic Models ---
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    # Support both username or email for login flexibly
    identity: str 
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserOut(UserBase):
    id: str
    is_verified: bool
    role: str
    created_at: str

# --- Direct Bcrypt Helpers (More reliable than passlib in some environments) ---
def get_password_hash(password: str) -> str:
    # bcrypt has a 72-byte limit on password length
    # We truncate manually to prevent library-level crashes
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8')[:72], 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification failure: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

# --- Endpoints ---
@router.post("/register")
async def register(user: UserCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (user.email, user.username))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Identity or Email already registered")
        
        hashed_password = get_password_hash(user.password)
        user_id = str(uuid.uuid4())
        
        # Auto-verify for institutional ease-of-use
        cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, is_verified, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, user.username, user.email, hashed_password, 1, 'Researcher'))
        
        conn.commit()
        
        return {
            "success": True, 
            "message": "User registered successfully",
            "user": {
                "id": user_id,
                "username": user.username,
                "email": user.email,
                "role": "Researcher"
            }
        }
    except Exception as e:
        logger.error(f"Registration Error: {e}")
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=f"Registration failure: {str(e)}")
    finally:
        conn.close()

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check both email and username for login
        cursor.execute("SELECT * FROM users WHERE email = ? OR username = ?", (credentials.identity, credentials.identity))
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"Login failed: Identity {credentials.identity} not found.")
            raise HTTPException(status_code=403, detail="Invalid Credentials")
        
        if not verify_password(credentials.password, user["password_hash"]):
            logger.warning(f"Login failed: Password mismatch for {credentials.identity}.")
            raise HTTPException(status_code=403, detail="Invalid Credentials")
        
        access_token = create_access_token(data={"sub": user["email"], "id": user["id"]})
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"]
            }
        }
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during login.")
    finally:
        conn.close()

@router.get("/me", response_model=UserOut)
async def get_current_user(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid session token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "is_verified": bool(user["is_verified"]),
            "role": user["role"],
            "created_at": str(user["created_at"])
        }
    finally:
        conn.close()
