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


def _normalize_tier(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    aliases = {
        "premium": "paid",
        "pro": "paid",
        "commercial": "paid",
    }
    return aliases.get(raw, raw)


def _tier_allows(granted: Optional[str], required: Optional[str]) -> bool:
    req = _normalize_tier(required)
    if not req:
        return True
    got = _normalize_tier(granted)

    if req == "free":
        return True

    rank = {"free": 0, "paid": 1, "enterprise": 2}
    if got in rank and req in rank:
        return rank[got] >= rank[req]

    return got == req


def _matches_requested_name(licensed_name: str, requested_name: str) -> bool:
    if licensed_name == requested_name:
        return True

    licensed_leaf = licensed_name.split("/")[-1]
    requested_leaf = requested_name.split("/")[-1]
    return licensed_leaf == requested_leaf


def _extract_entitled_names(raw: Any) -> list[str]:
    names: list[str] = []
    if isinstance(raw, dict):
        names.extend(str(k) for k in raw)
    elif isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, str):
                names.append(entry)
            elif isinstance(entry, dict):
                for key in ("name", "slug", "module", "id"):
                    value = entry.get(key)
                    if isinstance(value, str) and value.strip():
                        names.append(value.strip())
                        break
    return names


def _extract_features(raw: Any) -> set[str]:
    if isinstance(raw, list):
        return {str(x) for x in raw if isinstance(x, (str, int, float))}
    if isinstance(raw, dict):
        return {str(k) for k, v in raw.items() if v}
    return set()


def _resolve_from_entitlements(
    license_data: Dict[str, Any],
    item_type: str,
    item_name: str,
) -> Optional[Dict[str, Any]]:
    direct = license_data.get(item_type)
    entitlements = license_data.get("entitlements")
    ent_raw = entitlements.get(item_type) if isinstance(entitlements, dict) else None

    # If direct section exists but not as per-item dict (e.g. modules: ["a", "b"]),
    # treat it as entitlement list.
    direct_names = _extract_entitled_names(direct)
    ent_names = _extract_entitled_names(ent_raw)
    names = direct_names + [n for n in ent_names if n not in direct_names]

    for entitled in names:
        if _matches_requested_name(entitled, item_name):
            return {
                "name": entitled,
                "tier": license_data.get("tier") or license_data.get("plan"),
                "expires_at": license_data.get("expires_at"),
                "features": sorted(
                    _extract_features(license_data.get("features"))
                    | _extract_features(
                        entitlements.get("features") if isinstance(entitlements, dict) else None
                    )
                ),
            }

    return None


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

    # Find the requested section (legacy per-item schema)
    section: Optional[Dict[str, Any]] = None
    section_root = license_data.get(item_type)
    if isinstance(section_root, dict):
        candidate = section_root.get(item_name)
        if candidate is None and "/" in item_name:
            candidate = section_root.get(item_name.split("/")[-1])
        if isinstance(candidate, dict):
            section = candidate

    # Entitlement schema fallback (modules/features at top-level or entitlements.*)
    if section is None:
        section = _resolve_from_entitlements(license_data, item_type, item_name)

    if not section:
        raise RuntimeError(f"No license found for {item_type} '{item_name}'.")

    # Optional tier check
    granted_tier = cast(Optional[str], section.get("tier") or license_data.get("tier"))
    if required_tier and not _tier_allows(granted_tier, required_tier):
        raise RuntimeError(
            f"Your license does not permit using this {item_type} ({required_tier})."
        )

    # Expiry check
    expires_at = section.get("expires_at") or license_data.get("expires_at")
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
        features |= _extract_features(license_data.get("features"))
        entitlements = license_data.get("entitlements")
        if isinstance(entitlements, dict):
            features |= _extract_features(entitlements.get("features"))
        missing = set(required_features) - features
        if missing:
            raise RuntimeError(
                f"License for {item_type} '{item_name}' missing required features: {', '.join(missing)}"
            )

    # License successfully validated
    return section
