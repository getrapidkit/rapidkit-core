import logging
from pathlib import Path
from typing import Any, Optional


logger = logging.getLogger("rapidkit.settings.custom_sources")

def load_from_yaml(settings_cls, file_path: Path, field_name: str, field: Any) -> Any:
    """
    Try to load a specific field from a YAML file if it exists.
    """
    try:
        if not file_path.exists():
            logger.debug("settings: YAML file %s missing for %s", file_path, field_name)
            return None
        from pydantic_settings import YamlConfigSettingsSource

        source = YamlConfigSettingsSource(settings_cls, file_path)
        value = source.get_field_value(field_name, field)
        if value is not None:
            logger.debug("settings: loaded %s from YAML %s", field_name, file_path)
        return value
    except Exception as exc:
        logger.warning(
            "settings: YAML load failed for %s on %s (%s)", file_path, field_name, exc
        )
        return None
    return None


def load_from_vault(vault_url: Optional[str], field_name: str) -> Any:
    """
    Resolve value from Vault (if hvac client available and URL configured).
    This is a simple example; adapt secret path conventions to your org.
    """
    if not vault_url:
        logger.debug("settings: skipping Vault lookup for %s (no URL)", field_name)
        return None
    try:
        import hvac
        client = hvac.Client(url=vault_url)
        if not client.is_authenticated():
            # In real setups, attach token via env VAULT_TOKEN or login method here.
            token = client.adapter.get_session().headers.get("X-Vault-Token") or None
            if not token:
                logger.debug("settings: Vault client unauthenticated for field %s", field_name)
                return None
        # Example: read from "secret/data/app/<field_name>"
        # Adjust for v2/v1 depending on your Vault mount.
        secret = client.read(f"secret/{field_name}")
        if secret and "data" in secret:
            data = secret["data"] or {}
            value = data.get(field_name)
            if value is not None:
                logger.debug("settings: resolved %s from Vault", field_name)
            return value
    except Exception as exc:
        logger.warning("settings: Vault lookup failed for %s (%s)", field_name, exc)
        return None
    return None


def load_from_aws_sm(region: Optional[str], field_name: str) -> Any:
    """
    Resolve value from AWS Secrets Manager (requires AWS creds in env/instance role).
    """
    if not region:
        logger.debug("settings: skipping AWS Secrets Manager lookup for %s (no region)", field_name)
        return None
    try:
        import boto3
        client = boto3.client("secretsmanager", region_name=region)
        resp = client.get_secret_value(SecretId=field_name)
        if "SecretString" in resp:
            logger.debug("settings: resolved %s from AWS Secrets Manager", field_name)
            return resp["SecretString"]
    except Exception as exc:
        logger.warning(
            "settings: AWS Secrets Manager lookup failed for %s (%s)", field_name, exc
        )
        return None
    return None


__all__ = [
    "load_from_yaml",
    "load_from_vault",
    "load_from_aws_sm",
]
