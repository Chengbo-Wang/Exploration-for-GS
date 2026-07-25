
<div align="center">
  <h1 align="center">Exploration Matters for Escaping the Blur Trap in 3D Gaussian Splatting</h1>
  
  <p align="center">
    <a href="https://chengbo-wang.github.io/ExploreGS/"><img src="https://img.shields.io/badge/Project_Page-green" alt="Project Page"></a>
    <a href="https://arxiv.org/pdf/2607.17965" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/📄_Paper-PDF-b31b1b" alt="Paper PDF"></a>
    <a href="https://arxiv.org/abs/2607.17965"><img src="https://img.shields.io/badge/arXiv-2607.17965-b31b1b" alt="arXiv"></a>
  </p>

  <p align="center">
    <a href="https://chengbo-wang.github.io/"><strong>Chengbo Wang</strong></a>
    ·
    <a href="https://guozheng-ma.github.io/"><strong>Guozheng Ma</strong></a>
    ·
    <a href="https://github.com/Chengbo-Wang/Exploration-for-GS"><strong>Jinhong Wu</strong></a>
    ·
    <a href="https://github.com/Chengbo-Wang/Exploration-for-GS"><strong>Tie Ji</strong></a>
    ·
    <a href="https://yizhenlao.github.io/"><strong>Yizhen Lao</strong></a>
  </p>

  </div>


Official implementation of [Exploration Matters for Escaping the Blur Trap in 3D Gaussian Splatting](https://chengbo-wang.github.io/ExploreGS/).

## 💻Overview

![Overview](./assets/teaser.png)

<font color='#dd0000'>**We identify the Blur Trap as a fundamental limitation intrinsic to 3DGS, rooted in an inherent exploitation-only optimization bias.** </font> It manifests as two variants: the Far-Side Blur Trap triggered by depth-gradient deficiency and the Near-Side Blur Trap driven by 2D-gradient attenuation. To break this deadlock, we introduce minimal exploration operators: Random Seeding and Random Splitting. These straightforward interventions bypass gradient-dependent optimization, consistently recovering structural details and proving that simple explicit exploration is highly effective for escaping the Blur Trap without complex modifications.


## 🗒️Checklist

- [x] Release Exploration Code for `3DGS`
- [ ] Release Exploration Code for `gsplat`
- [ ] Release Blur Trap dataset


## 🎯 When to Explore: Seeding vs Splitting

> [!NOTE]
> Random Seeding and Random Splitting can be used **together or independently**, each targeting a different variant of the **Blur Trap**.

- ⛰️ **Random Seeding** (`seed_only` / `base`): Recommended for scenes dominated by ***distant structures — mountains, clouds, city skylines, or any expansive outdoor backdrop***. It places new Gaussians in under-covered distant regions, directly addressing the **Far-Side Blur Trap** caused by vanishing depth gradients.
- 🌿 **Random Splitting** (`split_only` / `base`):  Recommended for scenes with ***heavy near-field occlusions — gardens with dense foliage, cluttered tabletops, or any setting where foreground objects block the view***. It eagerly splits large Gaussians near the camera, countering the **Near-Side Blur Trap** where 2D gradients saturate.



## 🚀 Quick Start

### 🔧 Environment Setup

Clone the repository and set up a conda environment with Python 3.12:

```bash
git clone --depth 1 https://github.com/Chengbo-Wang/Exploration-for-GS.git
cd Exploration-for-GS
git submodule update --init --recursive
```

```bash
# Create and activate environment
conda create -n Explore4GS python=3.12
conda activate Explore4GS

# Install PyTorch (with CUDA support, choose version for your CUDA)
# See: https://pytorch.org/get-started/previous-versions/
pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu128

# Install other dependencies
pip install plyfile tqdm opencv-python joblib

# Install submodules
pip install submodules/diff-gaussian-rasterization --no-build-isolation
pip install submodules/simple-knn --no-build-isolation
pip install submodules/fused-ssim --no-build-isolation
```


### 📦 Data Preparation

This codebase follows the same dataset format as the original [3DGS](https://github.com/graphdeco-inria/gaussian-splatting). 


### 🧩 Exploration Operators

The **exploration operators** are controlled via the `--explore_cfg`. It accepts either a short name or a path to a YAML file in [config](./gaussian_exploration/configs/):

```bash
# single scene
python train.py -s <dataset>/scene -m output/scene --explore_cfg base

# or full eval
python full_eval.py \
    -m360 <mipnerf360 folder> \
    -tat <tanksandtemples folder> \
    -db <deepblending folder> \
    --explore_cfg base  # base / seed_only / split_only / none 
```

**Available presets:**

| Short name   | Mode            | Description                             |
| ------------ | --------------- | --------------------------------------- |
| `none`       | No exploration  | Pure original 3DGS behavior (baseline)  |
| `base`       | Seed + Split    | Full exploration (recommended)          |
| `seed_only`  | Seed only       | Random Seeding only                     |
| `split_only` | Split only      | Random Splitting only                   |

**Custom YAML reference:**

```yaml
explore_mode: both                  # "none" | "seed" | "split" | "both"

seed:
  enabled: true
  num: 100                          # Gaussians added per exploration step
  interval: 100                     # How often (in iterations) to explore
  until: 15000                      # Stop exploration after this iteration
  big_point_threshold: 10.0         # Prune if max scaling > this × scene extent

split:
  enabled: true
  num: 20                           # Gaussians to split per step
  interval: 1                       # Every iteration (dense exploration)
  until: 15000                      # Stop exploration after this iteration
```


## 📑 Citation

If you find this work useful for your research, please cite:

```bibtex
@article{wang2026exploration,
  title={Exploration Matters for Escaping the Blur Trap in 3D Gaussian Splatting},
  author={Wang, Chengbo and Ma, Guozheng and Wu, Jinhong and Ji, Tie and Lao, Yizhen},
  journal={arXiv preprint arXiv:2607.17965},
  year={2026}
}
```

## 🙏 Acknowledgement

This project builds upon the official [3D Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting) repository. We thank the authors for open-sourcing their work.
