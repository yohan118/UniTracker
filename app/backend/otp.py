"""
otp.py
------
Makes the verification codes. That's the whole job now.

We used to email these out, but for this version we just hand the code back to
the website and it shows up in a popup on screen. No email account, no phone
numbers, nothing to set up - it just works the moment you run the server.
"""

import random


def generate_otp():
    # A plain 6-digit code. Big enough to not guess, small enough to type.
    return str(random.randint(100000, 999999))
