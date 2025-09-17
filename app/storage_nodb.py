# storage_nodb.py — drop-in replacement for app/storage.py (NO DATABASE)
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import threading
import time

# In-memory "DB". This resets on process restart.
_lock = threading.RLock()
_users_by_id: Dict[int, "Account"] = {}
_users_by_name: Dict[str, "Account"] = {}
_next_id = 1

@dataclass
class Account:
    id: int
    name: str
    password_hash: str  # store bcrypt hash; do not store plaintext
    contact_number: Optional[str] = None
    avatar_img: Optional[str] = None  # could hold a URL or base64, if you like
    # Add any fields you need later

# --- Init & helpers ---
def _reserve_id() -> int:
    global _next_id
    with _lock:
        nid = _next_id
        _next_id += 1
        return nid

def init_with_admin(name: str = "admin", password_hash: str = "") -> None:
    """
    Seed an admin account if it doesn't exist yet.
    Pass a bcrypt hash if you want a non-empty password.
    """
    with _lock:
        if name in _users_by_name:
            return
        uid = _reserve_id()
        acc = Account(id=uid, name=name, password_hash=password_hash, contact_number=None)
        _users_by_id[uid] = acc
        _users_by_name[name] = acc

# --- Core account ops (match old signatures expected by main.py) ---
def create_account(name: str, password_hash: str) -> Account:
    with _lock:
        if name in _users_by_name:
            raise ValueError("username already exists")
        uid = _reserve_id()
        acc = Account(id=uid, name=name, password_hash=password_hash, contact_number=None)
        _users_by_id[uid] = acc
        _users_by_name[name] = acc
        return acc

def get_account_by_name(name: str) -> Optional[Account]:
    with _lock:
        return _users_by_name.get(name)

def get_account_by_id(user_id: int) -> Optional[Account]:
    with _lock:
        return _users_by_id.get(user_id)

# Backward-compat: old code used email; treat it as username
def get_user_by_email(email_or_name: str) -> Optional[Account]:
    return get_account_by_name(email_or_name)

# --- Emergency contact / contacts (simple per-user single number) ---
def set_emergency_contact(user_id: int, phone: Optional[str]) -> None:
    with _lock:
        acc = _users_by_id.get(user_id)
        if not acc:
            raise ValueError("user not found")
        acc.contact_number = phone

def get_emergency_contact(user_id: int) -> Optional[str]:
    with _lock:
        acc = _users_by_id.get(user_id)
        return acc.contact_number if acc else None

# Some code might call these names:
def get_contact(user_id: int) -> Optional[str]:
    return get_emergency_contact(user_id)

def upsert_contact(user_id: int, phone: Optional[str]) -> None:
    set_emergency_contact(user_id, phone)
