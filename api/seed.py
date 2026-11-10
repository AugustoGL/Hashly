"""
Crea un usuario de demo y una API key para probar el API.

    python seed.py
"""

from auth.api_keys import generate_key
from auth.auth import password_hasher
from database.database import SessionLocal
from database.models import ApiKey, User


EMAIL = "demo@hashly.local"
PASSWORD = "demo-password"


def main() -> None:
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == EMAIL).first()

        if user is None:
            user = User(
                email=EMAIL,
                password_hash=password_hasher.hash(PASSWORD),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        key, prefix, key_hash = generate_key()

        db.add(
            ApiKey(
                user_id=user.id,
                name="demo",
                prefix=prefix,
                key_hash=key_hash,
            )
        )
        db.commit()

        print(f"Usuario: {EMAIL} / {PASSWORD}")
        print(f"API key: {key}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
