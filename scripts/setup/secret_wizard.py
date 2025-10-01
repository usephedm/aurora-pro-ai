#!/usr/bin/env python3
from __future__ import annotations

import sys
import yaml
from pathlib import Path

from aurora_pro.secrets_loader import ensure_secrets


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    req_file = repo_root / "configs" / "required_secrets.yaml"
    if not req_file.exists():
        print(f"Required secrets spec not found: {req_file}", file=sys.stderr)
        return 2
    data = yaml.safe_load(req_file.read_text())
    required = {item["key"]: {k: v for k, v in item.items() if k != "key"} for item in data.get("secrets", [])}
    env_out = repo_root / ".env"
    ensure_secrets(required, write_env_path=env_out)
    print("Secrets ensured. Values stored in OS keyring; placeholders written to .env.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

