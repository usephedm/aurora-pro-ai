from __future__ import annotations

import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class PersistentStateManager:
    def __init__(self, state_dir: str = "aurora_pro/state") -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_system_state(self, state: Dict) -> None:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = self.state_dir / f"checkpoint_{ts}.pkl"
        with checkpoint_path.open("wb") as fh:
            pickle.dump(state, fh)
        print(f"[STATE] Saved checkpoint: {checkpoint_path}")

    def restore_latest_state(self) -> Optional[Dict]:
        checkpoints = sorted(self.state_dir.glob("checkpoint_*.pkl"))
        if not checkpoints:
            return None
        latest = checkpoints[-1]
        with latest.open("rb") as fh:
            state: Dict = pickle.load(fh)
        print(f"[STATE] Restored from: {latest}")
        return state

