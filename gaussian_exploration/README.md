# Gaussian Exploration

Exploration-based densification for 3D Gaussian Splatting. Two operators:

- **Random Seed** — samples new Gaussians within the bounding box of existing points.
- **Random Split** — selects large Gaussians by scaling and splits each into smaller ones.

## Integration

Replace `GaussianModel` with `GaussianExploreModel`. Everything else is automatic:

```python
from gaussian_exploration import GaussianExploreModel

gaussians = GaussianExploreModel(sh_degree, optimizer_type, model_path)
# In the training loop:
gaussians.explore_step(iteration, densify_from_iter, camera_extents)
```

Config is auto-loaded from `sys.argv` via `--explore_cfg`. The model saves the effective config to `{model_path}/explore_config.yaml` on construction.

## Configuration

Each method has its own sub-config in YAML. All fields are optional — omitted fields use defaults.

```bash
python train.py --explore_cfg base
python train.py --explore_cfg gaussian_exploration/configs/base.yaml
```

### Available configs

| Short name | Mode | File |
|------------|------|------|
| `none` | No exploration (original 3DGS) | [configs/none.yaml](configs/none.yaml) |
| `base` | Both seed and split | [configs/base.yaml](configs/base.yaml) |
| `seed_only` | Only seed exploration | [configs/seed_only.yaml](configs/seed_only.yaml) |
| `split_only` | Only random split | [configs/split_only.yaml](configs/split_only.yaml) |

### YAML reference

```yaml
# gaussian_exploration/configs/seed_only.yaml
explore_mode: seed                  # "none" | "seed" | "split" | "both"
seed:
  enabled: true
  num: 100                          # Gaussians added per step
  interval: 100                     # frequency (iterations)
  until: 10000                      # stop iteration
  big_point_threshold: 10.0         # prune if max scaling > this × scene extent
split:                              # same fields, but usually disabled
  enabled: false
```

### Python API

```python
from gaussian_exploration import ExploreConfig

cfg = ExploreConfig.load()                # auto from sys.argv
cfg = ExploreConfig.from_yaml("base")     # explicit YAML path / short name

cfg.seed.num          # → 200
cfg.split.enabled     # → False
cfg.seed.big_point_threshold  # → 10.0

cfg.to_yaml("out.yaml")                   # log effective config
```

## Seed Exploration

New Gaussians are initialized at random positions (uniform in the bounding box of existing points), with random RGB colors and size/opacity modulated by depth. When seed is active, the big-point pruning threshold is raised to `10.0 × scene extent` to avoid pruning newly added large Gaussians.

## Split Exploration

Sampling probability per Gaussian is proportional to `mean(scaling)`. Selected Gaussians are split into two smaller ones, with position, scaling, and feature preserved. The original is removed (net addition: +N per step).
