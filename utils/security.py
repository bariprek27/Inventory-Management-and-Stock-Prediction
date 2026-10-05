"""
utils/security.py
Security utilities: password hashing with bcrypt, role checking.
"""
import bcrypt

def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

class CurrentUser:
    """Session tracker for logged in user."""
    user_id: int = None
    username: str = None
    name: str = None
    role: str = None

    @classmethod
    def set_user(cls, user_id: int, username: str, name: str, role: str):
        cls.user_id = user_id
        cls.username = username
        cls.name = name
        cls.role = role

    @classmethod
    def clear(cls):
        cls.user_id = None
        cls.username = None
        cls.name = None
        cls.role = None

    @classmethod
    def is_admin(cls) -> bool:
        return cls.role == 'admin'

    @classmethod
    def is_authenticated(cls) -> bool:
        return cls.user_id is not None
