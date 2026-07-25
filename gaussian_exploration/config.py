
import os
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ExploreMethodConfig:
    enabled: bool = True
    num: int = 100
    interval: int = 100
    until: int = 15_000
    big_point_threshold: float = 0.1  # prune if max scaling > threshold * extent

class ExploreConfig:

    def __init__(self, seed: Optional[ExploreMethodConfig] = None,
                 split: Optional[ExploreMethodConfig] = None):
        self.seed = seed or ExploreMethodConfig()
        self.split = split or ExploreMethodConfig()

    @classmethod
    def load(cls) -> "ExploreConfig":
        """Auto-detect ``--explore_cfg`` from ``sys.argv`` and load YAML.

        Falls back to defaults (explore_mode=both) when no ``--explore_cfg``
        is present.  This is the method used by ``GaussianExploreModel``.
        """
        cfg_path = _detect_cfg_from_argv()
        return cls.from_yaml(cfg_path) if cfg_path else cls()

    @classmethod
    def from_yaml(cls, path: str) -> "ExploreConfig":
        """Load config from a YAML file (short name or full path)."""
        import yaml
        resolved = _resolve_path(path)
        if resolved is None:
            raise FileNotFoundError(
                f"Explore config not found: {path}. "
                f"Use a full path or short name (base, none, seed_only, split_only)."
            )
        with open(resolved) as f:
            raw = yaml.safe_load(f) or {}
        cfg = cls(
            seed=ExploreMethodConfig(**raw.get("seed", {})),
            split=ExploreMethodConfig(**raw.get("split", {})),
        )
        mode = raw.get("explore_mode")
        if mode is not None:
            cfg.seed.enabled = mode in ("seed", "both")
            cfg.split.enabled = mode in ("split", "both")
        return cfg

    def to_yaml(self, path: str) -> None:
        import yaml
        with open(path, "w") as f:
            yaml.dump({"seed": asdict(self.seed), "split": asdict(self.split)},
                      f, default_flow_style=False)


# -- Config-path resolution ---------------------------------------------------

def _resolve_path(path: str) -> Optional[str]:
    """Resolve a short name or full path to an existing YAML."""
    if os.path.isfile(path):
        return path
    if "/" not in path and "\\" not in path:
        candidate = os.path.join(os.path.dirname(__file__), "configs", f"{path}.yaml")
        if os.path.isfile(candidate):
            return candidate
    return None


def _detect_cfg_from_argv() -> Optional[str]:
    """Extract ``--explore_cfg`` from ``sys.argv`` without registering anything."""
    import sys
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--explore_cfg" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None
