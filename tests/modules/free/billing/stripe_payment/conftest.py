"""Shared pytest fixtures for Stripe Payment module tests."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

MODULE_IMPORT_PATH = "src.modules.free.billing.stripe_payment"


@pytest.fixture(scope="session")
def module_generate() -> ModuleType:
    return importlib.import_module(f"{MODULE_IMPORT_PATH}.generate")


@pytest.fixture(scope="session")
def stripe_payment_generator(module_generate: ModuleType):
    return module_generate.StripePaymentModuleGenerator()


@pytest.fixture(scope="session")
def module_root(module_generate: ModuleType) -> Path:
    return Path(module_generate.__file__).resolve().parent


@pytest.fixture(scope="session")
def module_config(module_generate: ModuleType) -> dict[str, object]:
    return dict(module_generate.load_module_config())


@pytest.fixture(scope="session")
def module_docs(module_config: dict[str, object]) -> dict[str, object]:
    documentation = module_config.get("documentation", {})
    if isinstance(documentation, dict):
        return dict(documentation)
    return {}


def _load_generated_module(module_name: str, module_path: Path) -> ModuleType:
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generated Stripe Payment runtime from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def rendered_stripe_payment(
    stripe_payment_generator,
    module_config,
    tmp_path: Path,
) -> dict[str, object]:
    renderer = stripe_payment_generator.create_renderer()
    context = stripe_payment_generator.apply_base_context_overrides(
        stripe_payment_generator.build_base_context(module_config)
    )

    stripe_payment_generator.generate_vendor_files(module_config, tmp_path, renderer, context)
    vendor_path = (
        tmp_path
        / ".rapidkit"
        / "vendor"
        / str(context["rapidkit_vendor_module"])
        / str(context["rapidkit_vendor_version"])
        / "src"
        / "modules"
        / "free"
        / "billing"
        / "stripe_payment"
        / "stripe_payment.py"
    )

    return {
        "root": tmp_path,
        "runtime": _load_generated_module("generated_stripe_payment_vendor", vendor_path),
    }
