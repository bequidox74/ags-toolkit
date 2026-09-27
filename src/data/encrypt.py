ENCODING = "latin-1"
ENCRYPTION_KEY = b"Avis Durgan"


def encrypt(s: str) -> bytes:
    b = bytearray(s, encoding=ENCODING)
    for i in range(len(b)):  # pylint: disable=consider-using-enumerate
        b[i] = (b[i] + ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]) & 0xFF
    return bytes(b)


def decrypt(b: bytes) -> str:
    s = bytearray(len(b))
    for i in range(len(b)):  # pylint: disable=consider-using-enumerate
        s[i] = (b[i] - ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]) % 256
    return s.rstrip(b"\x00").decode(ENCODING)
