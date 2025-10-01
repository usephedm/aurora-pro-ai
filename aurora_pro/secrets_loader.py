from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Optional


def _parse_env_file(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        if not line or line.strip().startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Resolve secret by precedence: env -> keyring -> .env -> default.

    Never logs the value; this function is safe to call in production code.
    """
    # 1) Environment
    if key in os.environ and os.environ[key]:
        return os.environ[key]

    # 2) OS keyring
    try:
        import keyring  # type: ignore
        v = keyring.get_password("aurora-pro", key)
        if v:
            return v
    except Exception:
        pass

    # 3) .env in project root
    cwd = Path.cwd()
    candidates = [
        cwd / ".env",
        cwd.parent / ".env",
    ]
    for p in candidates:
        try:
            data = _parse_env_file(p)
            if key in data and data[key]:
                return data[key]
        except Exception:
            continue

    return default


def set_secret(key: str, value: str) -> None:
    """Store secret into OS keyring under the 'aurora-pro' service.
    Does not write to files to avoid accidental leaks.
    """
    import keyring  # type: ignore

    keyring.set_password("aurora-pro", key, value)


def ensure_secrets(required: Dict[str, Dict[str, str]], write_env_path: Optional[Path] = None) -> None:
    """Interactively prompt for missing secrets and store in keyring.

    If write_env_path is provided, also write/update a local .env with keys (without values) as placeholders.
    """
    import getpass

    env_entries: Dict[str, str] = {}
    for key, meta in required.items():
        present = bool(get_secret(key))
        if present:
            continue
        if meta.get("required") == "true" or meta.get("required") is True:
            prompt = meta.get("description") or key
            val = getpass.getpass(f"Enter {prompt} for {key}: ")
            if not val:
                print(f"Warning: {key} left empty", file=sys.stderr)
            else:
                try:
                    set_secret(key, val)
                except Exception as e:
                    print(f"Failed to store {key} in keyring: {e}", file=sys.stderr)
        env_entries[key] = ""

    if write_env_path:
        try:
            lines = [f"{k}={env_entries.get(k, '')}" for k in env_entries]
            write_env_path.write_text("\n".join(lines) + "\n")
        except Exception:
            pass

