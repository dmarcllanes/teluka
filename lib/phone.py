"""
Philippine mobile number normalisation and validation.

PH mobile numbers follow the format: 09XXXXXXXXX (11 digits)
In E.164 format:                     +639XXXXXXXXX

Valid network prefixes (as of 2024):
  Globe / TM  : 0817, 0904–0906, 0915–0917, 0926–0927, 0935–0937, 0945, 0953–0956, 0965–0967, 0975–0977, 0978, 0994–0997, 0995, 0996
  Smart / TNT : 0908, 0911–0913, 0918–0919, 0920–0922, 0928–0930, 0938–0939, 0946–0948, 0949, 0950, 0961, 0963, 0968, 0969, 0973, 0998–0999
  DITO        : 0895–0899, 0991–0993
  SUN         : 0922–0925, 0931–0933, 0942–0943

Rather than maintaining a prefix allowlist (it changes), we just validate
the structural format: exactly 10 digits after the country code, first digit = 9.
"""
import re
from typing import NamedTuple


class PhoneValidationError(ValueError):
    """Raised when a phone number cannot be normalised."""


class NormalisedPhone(NamedTuple):
    e164: str        # +639XXXXXXXXX — always use this for storage and SMS
    display: str     # 0917 XXX XXXX — for UI display


# +639XXXXXXXXX  (13 chars total)
_E164_PH_RE = re.compile(r"^\+639\d{9}$")


def normalize_ph_phone(raw: str) -> NormalisedPhone:
    """
    Accept any common PH mobile format and return a NormalisedPhone.
    Raises PhoneValidationError if the number cannot be recognised.

    Accepted inputs (examples):
      09171234567       local format (11 digits)
      9171234567        without leading 0 (10 digits)
      639171234567      without + (12 digits)
      +639171234567     E.164 (13 chars)
      0917 123 4567     with spaces/dashes
    """
    # Strip all non-digit characters
    digits = re.sub(r"\D", "", raw)

    if len(digits) == 10 and digits.startswith("9"):
        # 9XXXXXXXXX → +639XXXXXXXXX
        e164 = f"+63{digits}"
    elif len(digits) == 11 and digits.startswith("09"):
        # 09XXXXXXXXX → +639XXXXXXXXX
        e164 = f"+63{digits[1:]}"
    elif len(digits) == 12 and digits.startswith("639"):
        # 639XXXXXXXXX → +639XXXXXXXXX
        e164 = f"+{digits}"
    elif len(digits) == 13 and digits.startswith("639"):
        # Already looks like E.164 digits
        e164 = f"+{digits[1:]}" if digits.startswith("6390") else f"+{digits}"
    else:
        raise PhoneValidationError(
            "Please enter a valid Philippine mobile number "
            "(e.g. 0917 123 4567)."
        )

    if not _E164_PH_RE.match(e164):
        raise PhoneValidationError(
            "That doesn't look like a Philippine mobile number. "
            "Mobile numbers start with 09."
        )

    # Build a human-friendly display: +63 917 123 4567
    local = e164[3:]            # 9XXXXXXXXX
    display = f"0{local[:3]} {local[3:6]} {local[6:]}"
    return NormalisedPhone(e164=e164, display=display)
