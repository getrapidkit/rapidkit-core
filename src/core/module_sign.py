"""
Module signing and verification helpers (Ed25519, multi-signer, key rotation, pure Python).
"""

import base64
import binascii
import hashlib
from typing import Any, Dict, List, Optional, Tuple

try:
    import nacl.encoding
    import nacl.signing
except ImportError:  # pragma: no cover - optional dependency
    nacl = None  # type: ignore


def hash_manifest(manifest_json: str) -> str:
    """Return SHA256 hex digest of manifest JSON (canonicalized)."""
    h = hashlib.sha256()
    h.update(manifest_json.encode("utf-8"))
    return h.hexdigest()


def get_signer_id_from_private(private_key_b64: str) -> str:
    """Return signer_id (public key fingerprint, hex) from private key."""
    if nacl is None:
        raise ImportError("pynacl required: pip install pynacl")
    sk = nacl.signing.SigningKey(base64.b64decode(private_key_b64))
    pk = sk.verify_key
    # fingerprint: first 16 hex chars of sha256(pubkey)
    fp = hashlib.sha256(pk.encode()).hexdigest()[:16]
    return fp


def get_signer_id_from_public(public_key_b64: str) -> str:
    if nacl is None:
        raise ImportError("pynacl required: pip install pynacl")
    pk = nacl.signing.VerifyKey(base64.b64decode(public_key_b64))
    fp = hashlib.sha256(pk.encode()).hexdigest()[:16]
    return fp


def sign_manifest(
    manifest_json: str,
    private_key_b64: str,
    signature_version: str = "v1",
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Sign manifest JSON with Ed25519 private key (base64).
    Returns dict: {signature, signer_id, signature_version, ...}
    """
    if nacl is None:
        raise ImportError("pynacl required: pip install pynacl")
    sk = nacl.signing.SigningKey(base64.b64decode(private_key_b64))
    sig = sk.sign(manifest_json.encode("utf-8"))
    signature = base64.b64encode(sig.signature).decode("utf-8")
    signer_id = get_signer_id_from_private(private_key_b64)
    result = {
        "signature": signature,
        "signer_id": signer_id,
        "signature_version": signature_version,
    }
    if extra_fields:
        result.update(extra_fields)
    return result


def verify_manifest_multi(
    manifest_json: str,
    signature_obj: Dict[str, Any],
    public_keys: List[str],
    allowed_signer_ids: Optional[List[str]] = None,
    signature_version: str = "v1",
) -> bool:
    """
    Verify manifest signature against a list of public keys (multi-signer).
    signature_obj: dict with keys signature, signer_id, signature_version
    public_keys: list of base64 public keys
    allowed_signer_ids: optional allowlist of signer_id (fingerprint)
    """
    if nacl is None:
        raise ImportError("pynacl required: pip install pynacl")
    sig = signature_obj.get("signature")
    signer_id = signature_obj.get("signer_id")
    sig_ver = signature_obj.get("signature_version", "v1")
    if sig_ver != signature_version:
        return False
    if allowed_signer_ids is not None and signer_id not in allowed_signer_ids:
        return False
    if not isinstance(sig, (str, bytes)) or not isinstance(signer_id, str):
        return False
    try:
        sig_bytes = base64.b64decode(sig)
    except (ValueError, TypeError, binascii.Error):
        return False
    verified = False
    for pub in public_keys:
        if isinstance(pub, (str, bytes)):
            try:
                pk = nacl.signing.VerifyKey(base64.b64decode(pub))
            except (ValueError, TypeError, binascii.Error):
                pass  # skip invalid key
            else:
                if hashlib.sha256(pk.encode()).hexdigest()[:16] == signer_id:
                    try:
                        pk.verify(manifest_json.encode("utf-8"), sig_bytes)
                        verified = True
                    except (ValueError, TypeError, binascii.Error):
                        verified = False
                    break  # stop after first matching key
    return verified


def verify_manifest(manifest_json: str, signature_b64: str, public_key_b64: str) -> bool:
    """Legacy: verify Ed25519 signature (base64) of manifest JSON with public key (base64)."""
    if nacl is None:
        raise ImportError("pynacl required: pip install pynacl")
    if not isinstance(public_key_b64, (str, bytes)) or not isinstance(signature_b64, (str, bytes)):
        return False  # type: ignore[unreachable]
    try:
        vk = nacl.signing.VerifyKey(base64.b64decode(public_key_b64))
    except (ValueError, TypeError, binascii.Error):
        return False
    try:
        sig_bytes = base64.b64decode(signature_b64)
        vk.verify(manifest_json.encode("utf-8"), sig_bytes)
        return True
    except (ValueError, TypeError, binascii.Error):
        return False


def generate_ed25519_keypair() -> Tuple[str, str]:
    """Generate Ed25519 keypair, return (private_b64, public_b64)."""
    if nacl is None:
        raise ImportError("pynacl required: pip install pynacl")
    sk = nacl.signing.SigningKey.generate()
    pk = sk.verify_key
    return (
        base64.b64encode(sk.encode()).decode("utf-8"),
        base64.b64encode(pk.encode()).decode("utf-8"),
    )
