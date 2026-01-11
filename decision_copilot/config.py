# coding: utf-8
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    sqlite_path: Path = Path(os.environ.get("DECISION_COPILOT_DB"))
