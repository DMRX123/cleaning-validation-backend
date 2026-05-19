#!/usr/bin/env python
"""Create admin user script"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal
from app.models.user import User
import hashlib


def create_admin_user():
    """Create admin user if not exists"""
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("⚠️ Admin user already exists!")
            print(f"   Username: {existing_admin.username}")
            return
        
        hashed = hashlib.sha256("admin".encode()).hexdigest()
        
        admin = User(
            username="admin",
            email="admin@cleaning-validation.com",
            hashed_password=hashed,
            is_active=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        
        print("=" * 50)
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print(f"   Username: admin")
        print(f"   Password: admin")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creating admin: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()