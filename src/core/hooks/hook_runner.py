# src / core / hooks / hook_runner.py
import importlib
import importlib.util
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class HookRunner:
    """Flexible runner for both file-based and dotted-path kit hooks."""

    @staticmethod
    def run(
        kit_path: Path,
        hook_ref: str,
        variables: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> None:
        """
        Run hook function from either a local file (hooks.py) or a dotted path.

        :param kit_path: Path to the kit directory
        :param hook_ref: Function name or dotted path (e.g. `pre_generate` or `kits.xxx.hooks.pre_generate`)
        :param variables: Variables to pass to the hook
        :param output_path: For post_generate
        """
        try:
            if "." in hook_ref:
                # Case 1: dotted import path
                module_path, func_name = hook_ref.rsplit(".", 1)
                module = importlib.import_module(module_path)
            else:
                # Case 2: local hook in hooks.py in kit_path
                hook_file = kit_path / "hooks.py"
                if not hook_file.exists():
                    return  # No local hook defined
                spec = importlib.util.spec_from_file_location("kit_hooks", hook_file)
                if spec and spec.loader:  # defensive none guard
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                else:
                    raise ImportError("Failed to load kit_hooks spec")
                func_name = hook_ref

            hook_func: Callable[..., Any] = getattr(module, func_name)

            if output_path is not None:
                hook_func(output_path, variables)
            else:
                hook_func(variables)

        except (AttributeError, ImportError, FileNotFoundError) as e:
            raise RuntimeError(f"❌ Failed to run hook '{hook_ref}': {e}") from e
