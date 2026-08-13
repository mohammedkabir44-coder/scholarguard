"""
Create Admin Account Script
Run: python create_admin.py
Creates admin@scholarguard.com with password Admin123!
"""

import hashlib
import bcrypt

from database import SessionLocal, init_db
from models import User

ADMIN_EMAIL = "admin@scholarguard.com"
ADMIN_PASSWORD = "Admin123!"


def get_password_hash(password: str) -> str:
    """Exact same hashing logic as main.py"""
    pwd_bytes = hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def main():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            print(f"Admin already exists: {ADMIN_EMAIL}")
            return

        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            full_name="Administrator",
            phone_number="000-000-0000",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"SUCCESS: Admin created! Email: {ADMIN_EMAIL} | Password: {ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()