"""
utils/validators.py
Input validation helpers for products, suppliers, purchases, sales, etc.
"""
import re
from datetime import datetime
from typing import Tuple, Optional

def validate_non_empty(val: str, field_name: str) -> Tuple[bool, Optional[str]]:
    if not val or not str(val).strip():
        return False, f"{field_name} cannot be empty."
    return True, None

def validate_positive_number(val, field_name: str, allow_zero: bool = True) -> Tuple[bool, Optional[str]]:
    try:
        num = float(val)
        if allow_zero and num < 0:
            return False, f"{field_name} cannot be negative."
        if not allow_zero and num <= 0:
            return False, f"{field_name} must be greater than zero."
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number."

def validate_positive_int(val, field_name: str, allow_zero: bool = True) -> Tuple[bool, Optional[str]]:
    try:
        num = int(val)
        if allow_zero and num < 0:
            return False, f"{field_name} cannot be negative."
        if not allow_zero and num <= 0:
            return False, f"{field_name} must be greater than zero."
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid integer."

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    if not email:
        return True, None # Optional in some forms, but if provided check format
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, email.strip()):
        return False, "Invalid email address format."
    return True, None

def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    if not phone:
        return True, None
    pattern = r"^[0-9\+\-\s\(\)]{7,20}$"
    if not re.match(pattern, phone.strip()):
        return False, "Invalid phone number format."
    return True, None

def validate_date_str(date_str: str, fmt: str = "%Y-%m-%d") -> Tuple[bool, Optional[str]]:
    try:
        datetime.strptime(date_str.strip(), fmt)
        return True, None
    except ValueError:
        return False, f"Date must follow the format {fmt}."
