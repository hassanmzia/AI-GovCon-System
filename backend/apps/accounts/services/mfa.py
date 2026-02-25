"""Multi-factor authentication service using TOTP (RFC 6238)."""
import base64
import io
import logging
import os
import secrets
import time

logger = logging.getLogger("ai_deal_manager.accounts.mfa")

_TOTP_DIGITS = 6
_TOTP_PERIOD = 30  # seconds
_TOTP_ALGORITHM = "sha1"
_WINDOW = 1  # allow 1 period drift


# ── TOTP core ─────────────────────────────────────────────────────────────────

def generate_totp_secret() -> str:
    """Generate a random base32-encoded TOTP secret (160-bit)."""
    random_bytes = secrets.token_bytes(20)
    return base64.b32encode(random_bytes).decode("utf-8")


def _hotp(secret_b32: str, counter: int, digits: int = _TOTP_DIGITS) -> str:
    """Compute HMAC-based OTP for a given counter value."""
    import hmac
    import hashlib
    import struct

    key = base64.b32decode(secret_b32.upper().replace(" ", ""), casefold=True)
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10**digits)).zfill(digits)


def generate_totp(secret_b32: str, timestamp: float | None = None) -> str:
    """Generate a TOTP code for the current (or given) Unix timestamp."""
    ts = int(timestamp or time.time())
    counter = ts // _TOTP_PERIOD
    return _hotp(secret_b32, counter)


def verify_totp(secret_b32: str, code: str, timestamp: float | None = None) -> bool:
    """Verify a TOTP code, allowing ±_WINDOW period drift.

    Returns True if the code is valid.
    """
    if not code or not secret_b32:
        return False
    ts = int(timestamp or time.time())
    counter = ts // _TOTP_PERIOD
    for drift in range(-_WINDOW, _WINDOW + 1):
        if secrets.compare_digest(_hotp(secret_b32, counter + drift), code.strip()):
            return True
    return False


# ── QR code provisioning URI ──────────────────────────────────────────────────

def build_provisioning_uri(
    secret_b32: str,
    account_name: str,
    issuer: str = "AI Deal Manager",
) -> str:
    """Return an otpauth:// URI suitable for QR code generation."""
    from urllib.parse import quote

    label = quote(f"{issuer}:{account_name}", safe="")
    return (
        f"otpauth://totp/{label}"
        f"?secret={secret_b32}"
        f"&issuer={quote(issuer)}"
        f"&algorithm={_TOTP_ALGORITHM.upper()}"
        f"&digits={_TOTP_DIGITS}"
        f"&period={_TOTP_PERIOD}"
    )


def generate_qr_code_png(provisioning_uri: str) -> bytes:
    """Generate a PNG QR code image for the provisioning URI.

    Returns PNG bytes. Falls back to empty bytes if qrcode is unavailable.
    """
    try:
        import qrcode  # type: ignore

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        logger.warning("qrcode package not installed; cannot generate QR image")
        return b""


def generate_qr_code_base64(provisioning_uri: str) -> str:
    """Return a base64-encoded PNG QR code suitable for embedding in HTML."""
    png_bytes = generate_qr_code_png(provisioning_uri)
    if not png_bytes:
        return ""
    return base64.b64encode(png_bytes).decode("utf-8")


# ── Backup codes ──────────────────────────────────────────────────────────────

def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate one-time-use backup codes.

    Format: XXXX-XXXX (8 hex chars with dash for readability).
    """
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(4)
        codes.append(f"{raw[:4].upper()}-{raw[4:].upper()}")
    return codes


def hash_backup_code(code: str) -> str:
    """Return a SHA-256 hash of a backup code (for safe storage)."""
    import hashlib

    normalized = code.replace("-", "").upper()
    return hashlib.sha256(normalized.encode()).hexdigest()


def verify_backup_code(code: str, hashed_codes: list[str]) -> tuple[bool, str | None]:
    """Check if *code* matches any of the stored hashed codes.

    Returns (valid, matched_hash) so the caller can delete the used code.
    """
    normalized_hash = hash_backup_code(code)
    for stored_hash in hashed_codes:
        if secrets.compare_digest(normalized_hash, stored_hash):
            return True, stored_hash
    return False, None


# ── Django model helpers ───────────────────────────────────────────────────────

def setup_mfa_for_user(user_id: int) -> dict:
    """Provision MFA for a user – generates secret and QR code.

    Returns dict with: secret, provisioning_uri, qr_code_b64, backup_codes.
    Does NOT save to DB – caller should persist the secret and hashed backup codes.
    """
    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(pk=user_id)
        email = getattr(user, "email", str(user))
    except Exception:
        email = f"user_{user_id}"

    secret = generate_totp_secret()
    issuer = os.getenv("MFA_ISSUER", "AI Deal Manager")
    uri = build_provisioning_uri(secret, account_name=email, issuer=issuer)
    qr_b64 = generate_qr_code_base64(uri)
    backup_codes = generate_backup_codes(10)
    hashed_backups = [hash_backup_code(c) for c in backup_codes]

    return {
        "secret": secret,
        "provisioning_uri": uri,
        "qr_code_b64": qr_b64,
        "backup_codes": backup_codes,  # show these to user once
        "hashed_backup_codes": hashed_backups,  # store these in DB
    }
