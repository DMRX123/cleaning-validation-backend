from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from ..models.user import User
from ..config import config

# Use simpler hashing for now
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

class AuthService:
    @staticmethod
    def verify_password(plain_password, hashed_password):
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except:
            # Fallback for development
            import hashlib
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    
    @staticmethod
    def get_password_hash(password):
        try:
            return pwd_context.hash(password)
        except:
            # Fallback for development
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str):
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
