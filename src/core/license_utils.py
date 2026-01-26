import base64
import binascii
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

# Pre-declare names with a permissive type so optional cryptography imports
# don't make mypy complain about later assignments to None.
hashes: Any = None
serialization: Any = None
padding: Any = None
InvalidSignature: Any = None

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
except ImportError:  # pragma: no cover - optional dependency
    # keep names as None
    pass


def validate_license_for_item(
    license_path: str,
    item_type: str,
    item_name: str,
    required_tier: Optional[str] = None,
    required_features: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate a license section for a kit/module/addon.

    Returns the license section dict on success or raises RuntimeError on failure.
    """
    path = Path(license_path)
    if not path.exists():
        raise RuntimeError("license.json not found.")

    # Load license JSON
    with open(path, "r", encoding="utf-8") as f:
        license_data: Dict[str, Any] = json.load(f)

    # Optional digital signature verification if public_key.pem exists
    pubkey_path = Path("public_key.pem")
    if pubkey_path.exists():
        if serialization is None:
            raise RuntimeError("cryptography package required for license signature verification")
        try:
            with open(pubkey_path, "rb") as pkf:
                public_key = serialization.load_pem_public_key(pkf.read())
            signature = license_data.get("signature")
            if not signature:
                raise RuntimeError("License file missing digital signature.")
            if not isinstance(signature, (str, bytes)):
                raise RuntimeError("Invalid signature value in license file")
            sig_bytes = base64.b64decode(signature)

            # Remove signature for verification
            license_copy = dict(license_data)
            license_copy.pop("signature", None)
            license_bytes = json.dumps(license_copy, sort_keys=True).encode("utf-8")

            try:
                cast_pub: Any = public_key
                cast_pub.verify(sig_bytes, license_bytes, padding.PKCS1v15(), hashes.SHA256())
            except InvalidSignature as e:
                raise RuntimeError("License digital signature verification failed") from e
        except (ValueError, TypeError, binascii.Error) as e:
            raise RuntimeError(
                "Invalid public key or signature data for license verification"
            ) from e

    # Find the requested section
    section = license_data.get(item_type, {}).get(item_name)
    if not section:
        raise RuntimeError(f"No license found for {item_type} '{item_name}'.")

    # Optional tier check
    if required_tier and section.get("tier") != required_tier:
        raise RuntimeError(
            f"Your license does not permit using this {item_type} ({required_tier})."
        )

    # Expiry check
    expires_at = section.get("expires_at")
    if expires_at:
        try:
            expires_s = str(expires_at)
            if expires_s.endswith("Z"):
                expiry = datetime.fromisoformat(expires_s.replace("Z", "+00:00"))
            else:
                expiry = datetime.fromisoformat(expires_s)
        except ValueError as e:
            raise RuntimeError("Invalid expires_at format. Use ISO8601.") from e
        now = datetime.now(timezone.utc)
        if expiry < now:
            raise RuntimeError(f"Your license for {item_type} '{item_name}' has expired.")

    # Features check
    if required_features:
        features = set(section.get("features", []))
        missing = set(required_features) - features
        if missing:
            raise RuntimeError(
                f"License for {item_type} '{item_name}' missing required features: {', '.join(missing)}"
            )

    # License successfully validated
    return cast(Dict[str, Any], section)
