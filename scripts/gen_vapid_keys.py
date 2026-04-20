"""
Run this once to generate VAPID keys for Web Push.

Usage:
    python scripts/gen_vapid_keys.py

Then add the output lines to your .env file.
"""
from py_vapid import Vapid

v = Vapid()
v.generate_keys()

private_pem = v.private_pem().decode().strip()
public_key  = v.public_key.decode().strip()

print("# Add these to your .env file:")
print(f'VAPID_PRIVATE_KEY="{private_pem}"')
print(f'VAPID_PUBLIC_KEY="{public_key}"')
print('VAPID_EMAIL="admin@yourdomain.com"')
