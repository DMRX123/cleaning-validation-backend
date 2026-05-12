#!/usr/bin/env python
"""Create admin user script"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.services.auth import AuthService

def create_admin_user():
    """Create admin user if not exists"""
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("⚠️ Admin user already exists!")
            print(f"   Username: {existing_admin.username}")
            print("   To reset password, delete the user and run this script again.")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@cleaning-validation.com",
            hashed_password=AuthService.get_password_hash("Admin@123"),
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        
        print("=" * 50)
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print(f"   Username: admin")
        print(f"   Password: Admin@123")
        print("=" * 50)
        print("⚠️  IMPORTANT: Please change password on first login!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creating admin: {str(e)}")
        db.rollback()
    finally:
        db.close()

def reset_admin_password():
    """Reset admin password"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            admin.hashed_password = AuthService.get_password_hash("Admin@123")
            db.commit()
            print("✅ Admin password reset successfully!")
            print("   New password: Admin@123")
        else:
            print("❌ Admin user not found. Run without --reset flag to create.")
    except Exception as e:
        print(f"❌ Error resetting password: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_admin_password()
    else:
        create_admin_user()