from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import get_db
from ..models.user import User
from ..config import config
from pydantic import BaseModel, EmailStr
import logging
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool


# ============================================
# PUBLIC ENDPOINTS - NO AUTHENTICATION
# ============================================

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user - PUBLIC"""
    try:
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Simple SHA256 hashing (no bcrypt for simplicity)
        hashed_password = hashlib.sha256(user_data.password.encode()).hexdigest()
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=False
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            is_active=new_user.is_active,
            is_admin=new_user.is_admin
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/token", response_model=Token)
def login(db: Session = Depends(get_db)):
    """Login - PUBLIC (returns dummy token)"""
    # Ensure admin exists
    admin = db.query(User).filter(User.username == 'admin').first()
    if not admin:
        hashed = hashlib.sha256('admin'.encode()).hexdigest()
        admin = User(
            username='admin',
            email='admin@cleaning-validation.com',
            hashed_password=hashed,
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
    
    return {"access_token": "dummy_token_for_development", "token_type": "bearer"}


@router.post("/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    """Setup admin user - PUBLIC"""
    try:
        admin = db.query(User).filter(User.username == 'admin').first()
        hashed = hashlib.sha256('admin'.encode()).hexdigest()
        
        if admin:
            admin.hashed_password = hashed
            db.commit()
            return {
                "success": True,
                "message": "Admin password reset successfully",
                "username": "admin",
                "password": "admin"
            }
        else:
            new_admin = User(
                username='admin',
                email='admin@cleaning-validation.com',
                hashed_password=hashed,
                is_active=True,
                is_admin=True
            )
            db.add(new_admin)
            db.commit()
            return {
                "success": True,
                "message": "Admin user created successfully",
                "username": "admin",
                "password": "admin"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    """Get all users - PUBLIC"""
    try:
        users = db.query(User).all()
        return {
            "success": True,
            "count": len(users),
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "is_active": u.is_active,
                    "is_admin": u.is_admin
                }
                for u in users
            ]
        }
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete user by ID - PUBLIC"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent deleting the last admin
        if user.is_admin:
            admin_count = db.query(User).filter(User.is_admin == True).count()
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot delete the last admin user")
        
        db.delete(user)
        db.commit()
        return {"success": True, "message": "User deleted successfully", "id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DUMMY DEPENDENCIES FOR COMPATIBILITY
# ============================================

async def get_current_user(request: Request = None, db: Session = Depends(get_db)):
    """Return dummy admin user - NO AUTHENTICATION"""
    user = db.query(User).filter(User.username == 'admin').first()
    if not user:
        hashed = hashlib.sha256('admin'.encode()).hexdigest()
        user = User(
            username='admin',
            email='admin@system.com',
            hashed_password=hashed,
            is_active=True,
            is_admin=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    return current_user