from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from ..models.user import User
from ..config import config
import bcrypt
import hashlib
import logging

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        try:
            if not plain_password or not hashed_password:
                logger.warning("Empty password or hash provided")
                return False
            
            logger.info(f"Verifying password - Hash starts with: {hashed_password[:20]}...")
            
            # Check if it's a bcrypt hash (starts with $2b$)
            if hashed_password.startswith('$2b$'):
                try:
                    result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
                    logger.info(f"Bcrypt verification result: {result}")
                    return result
                except Exception as e:
                    logger.error(f"Bcrypt verification error: {str(e)}")
            
            # Check if it's a simple SHA256 hash (for development)
            if len(hashed_password) == 64 and all(c in '0123456789abcdef' for c in hashed_password):
                result = hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
                logger.info(f"SHA256 verification result: {result}")
                return result
            
            # Fallback for temporary hash
            if hashed_password == 'admin_temp_hash' and plain_password == 'Admin@123':
                logger.info("Using temporary admin hash")
                return True
                
            logger.warning("No matching password verification method found")
            return False
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password using bcrypt"""
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            logger.info(f"Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"Password hashing error: {str(e)}")
            # Fallback to SHA256 if bcrypt fails
            return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str):
        """Authenticate a user"""
        try:
            logger.info(f"Attempting to authenticate user: {username}")
            
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User not found: {username}")
                return None
            
            logger.info(f"User found: {username}, hashed_password exists: {bool(user.hashed_password)}")
            
            is_valid = AuthService.verify_password(password, user.hashed_password)
            
            if not is_valid:
                logger.warning(f"Invalid password for user: {username}")
                return None
            
            logger.info(f"User authenticated successfully: {username}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def create_access_token(data: dict):
        """Create a JWT access token"""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode.update({"exp": expire})
            token = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
            logger.info(f"Token created for user: {data.get('sub', 'unknown')}")
            return token
        except Exception as e:
            logger.error(f"Token creation error: {str(e)}")
            raise