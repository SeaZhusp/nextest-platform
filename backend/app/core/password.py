import hashlib
import hmac


def hash_password(password: str) -> str:
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return f"sha256${digest}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False

    if stored_hash.startswith("sha256$"):
        expected = hash_password(plain_password)
        return hmac.compare_digest(expected, stored_hash)

    # Bootstrap compatibility: support legacy plain-text passwords in dev.
    return hmac.compare_digest(plain_password, stored_hash)
