"""
PIN hashing and verification using stdlib PBKDF2-HMAC-SHA256.
A 4-digit PIN is hashed with a random 16-byte salt so brute-forcing
the stored hash is infeasible without the salt.
"""
import base64
import hashlib
import hmac
import os


def hash_pin(pin: str) -> str:
    """Hash a 4-digit PIN. Returns a base64-encoded salt+digest string."""
    salt = os.urandom(16)
    dk   = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000)
    return base64.b64encode(salt + dk).decode()


def verify_pin(pin: str, stored: str) -> bool:
    """Verify a PIN against its stored hash. Returns True on match."""
    try:
        data = base64.b64decode(stored.encode())
        salt, dk = data[:16], data[16:]
        new_dk   = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000)
        return hmac.compare_digest(dk, new_dk)
    except Exception:
        return False


def validate_pin(pin: str) -> str | None:
    """Returns an error string or None if valid."""
    if not pin.isdigit():
        return "PIN must contain digits only."
    if len(pin) != 4:
        return "PIN must be exactly 4 digits."
    if len(set(pin)) == 1:
        return "PIN cannot be all the same digit (e.g. 1111)."
    if pin in ("1234", "0000", "1111", "2222", "3333", "4444",
               "5555", "6666", "7777", "8888", "9999", "4321"):
        return "PIN is too common. Please choose a less predictable one."
    return None
