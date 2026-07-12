"""
Short code generation.

Two common approaches, worth knowing both for an interview:

1) Random string (what we do here): generate a random base62 string,
   check the DB for a collision, retry on the rare clash. Simple, works
   fine at moderate scale since base62^7 is ~3.5 trillion possibilities.

2) Base62-encode an auto-increment ID: guarantees no collisions and no
   retries, but leaks how many URLs exist (id=1042 tells you you're the
   1042nd link created) and makes links guessable/enumerable.

We pick (1) deliberately for the same reason we hide the internal `id`
in models.py - it doesn't leak information about the system.
"""

import random
import string

ALPHABET = string.ascii_letters + string.digits  # 62 chars
CODE_LENGTH = 7


def generate_short_code(length: int = CODE_LENGTH) -> str:
    return "".join(random.choices(ALPHABET, k=length))
