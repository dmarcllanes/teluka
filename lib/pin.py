"""
PIN hashing — Argon2id (primary) with transparent PBKDF2-SHA256 upgrade path.

hash_pin()   → always produces Argon2id hash
verify_pin() → returns (valid: bool, needs_rehash: bool)
               needs_rehash=True when stored hash is old PBKDF2 format;
               caller should re-hash and persist on next successful verify.
"""
import base64
import hashlib
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,   # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_pin(pin: str) -> str:
    """Hash a 4-digit PIN with Argon2id. Returns the encoded hash string."""
    return _ph.hash(pin)


def verify_pin(pin: str, stored: str) -> tuple[bool, bool]:
    """
    Verify a PIN against its stored hash.
    Returns (valid, needs_rehash).
    needs_rehash=True means the stored hash should be upgraded to current params.
    """
    if stored.startswith("$argon2"):
        try:
            _ph.verify(stored, pin)
            return True, _ph.check_needs_rehash(stored)
        except (VerifyMismatchError, InvalidHashError):
            return False, False
        except Exception:
            return False, False
    else:
        # Legacy PBKDF2-HMAC-SHA256 — verify then signal upgrade needed
        try:
            data   = base64.b64decode(stored.encode())
            salt   = data[:16]
            dk     = data[16:]
            new_dk = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 200_000)
            if hmac.compare_digest(dk, new_dk):
                return True, True   # valid — but must be re-hashed to Argon2id
            return False, False
        except Exception:
            return False, False


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
