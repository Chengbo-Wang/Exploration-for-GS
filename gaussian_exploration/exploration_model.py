import torch
from tqdm import tqdm
from gaussian_exploration.densify_util import explore_random
from gaussian_exploration.config import ExploreConfig, ExploreMethodConfig
from utils.general_utils import build_rotation
from scene.gaussian_model import GaussianModel


class GaussianExploreModel(GaussianModel):

    def __init__(self, sh_degree, optimizer_type="default", model_path=None):
        super().__init__(sh_degree, optimizer_type)
        self.tmp_radii = None
        self._explore_cfg = ExploreConfig.load()
        
        if model_path is not None:
            import os
            self._explore_cfg.to_yaml(os.path.join(model_path, "explore_config.yaml"))

    def explore_step(self, iteration, densify_from_iter, camera_extents):
        
        cfg = self._explore_cfg

        if cfg.seed.enabled and self._check(iteration, densify_from_iter, cfg.seed):
            self.seed_explore(num_explore=cfg.seed.num,
                              camera_extents=camera_extents)

        if cfg.split.enabled and self._check(iteration, densify_from_iter, cfg.split):
            self.split_explore(num_explore=cfg.split.num)

    @staticmethod
    def _check(iteration: int, densify_from_iter: int, sub: ExploreMethodConfig) -> bool:
        return (
            iteration > densify_from_iter
            and iteration < sub.until
            and iteration % sub.interval == 0
        )

    def seed_explore(self, extent_factor=1.0, seed_sampling_method="random_uniform", camera_extents=None,
                    num_explore=100, percentage_densify=None):

        if num_explore is None:
            if percentage_densify is None:
                raise ValueError('Either num_explore or percentage_densify must be provided.')
            else:
                num_explore = int(self._opacity.shape[0] * percentage_densify)

        densify_points = explore_random(self, num_explore, extent_factor, seed_sampling_method, camera_extents)
    
        if (densify_points is not None) and (densify_points["new_xyz"].shape[0] > 0):
            if self.tmp_radii is None:
                self.tmp_radii = torch.zeros(self._xyz.shape[0], device="cuda")
            self.densification_postfix(**densify_points)
            densify_points = None

        max_memory = torch.cuda.max_memory_allocated() / (1024 ** 3)
        tqdm.write(f"[Seed Explore] {num_explore} new Gaussians added, shape: {self.get_xyz.shape}, max mem: {max_memory:.2f} GB")

    def split_explore(self, num_explore: int=100, percent_prune: float=0.1, N=2, sample_idx=None):
        
        # Only Sampling Big Gaussians
        if sample_idx is None:
            explore_score = torch.mean(self.get_scaling, dim=-1, keepdim=True) # [N, 1]
            explore_score = explore_score.clamp(min=1e-8)
            sample_p = explore_score / torch.sum(explore_score)
            sample_p = sample_p.squeeze()   # [N]
            sample_idx = torch.multinomial(sample_p, num_samples=num_explore, replacement=False, generator=None)    # [N]
        
        # Split
        selected_pts_mask = torch.zeros((self._xyz.shape[0]), dtype=torch.bool, device="cuda")
        selected_pts_mask[sample_idx] = True

        stds = self.get_scaling[selected_pts_mask].repeat(N,1)
        means =torch.zeros((stds.size(0), 3),device="cuda")
        samples = torch.normal(mean=means, std=stds)
        rots = build_rotation(self._rotation[selected_pts_mask]).repeat(N,1,1)
        new_xyz = torch.bmm(rots, samples.unsqueeze(-1)).squeeze(-1) + self.get_xyz[selected_pts_mask].repeat(N, 1)
        new_scaling = self.scaling_inverse_activation(self.get_scaling[selected_pts_mask].repeat(N,1) / (0.8*N))
        new_rotation = self._rotation[selected_pts_mask].repeat(N,1)
        new_features_dc = self._features_dc[selected_pts_mask].repeat(N,1,1)
        new_features_rest = self._features_rest[selected_pts_mask].repeat(N,1,1)
        new_opacity = self._opacity[selected_pts_mask].repeat(N,1)

        if self.tmp_radii is None:
            self.tmp_radii = torch.zeros(self._xyz.shape[0], device="cuda")
        new_tmp_radii = self.tmp_radii[selected_pts_mask].repeat(N)
        self.densification_postfix(new_xyz, new_features_dc, new_features_rest, new_opacity, new_scaling, new_rotation, new_tmp_radii)

        prune_filter = torch.cat((selected_pts_mask, torch.zeros(N * selected_pts_mask.sum(), device="cuda", dtype=bool)))
        self.prune_points(prune_filter)

        max_memory = torch.cuda.max_memory_allocated() / (1024 ** 3)
        tqdm.write(f"[Split Explore] {num_explore} Gaussians split, shape: {self.get_xyz.shape}, max mem: {max_memory:.2f} GB")

    def densify_and_prune(self, max_grad, min_opacity, extent, max_screen_size, radii):
        grads = self.xyz_gradient_accum / self.denom
        grads[grads.isnan()] = 0.0
        self.tmp_radii = radii
        self.densify_and_clone(grads, max_grad, extent)
        self.densify_and_split(grads, max_grad, extent)

        prune_mask = (self.get_opacity < min_opacity).squeeze()
        if max_screen_size:
            big_points_vs = self.max_radii2D > max_screen_size
            factor = self._explore_cfg.seed.big_point_threshold if self._explore_cfg.seed.enabled else 0.1
            big_points_ws = self.get_scaling.max(dim=1).values > factor * extent
            prune_mask = torch.logical_or(torch.logical_or(prune_mask, big_points_vs), big_points_ws)
        
        self.prune_points(prune_mask)
        self.tmp_radii = None
        
        torch.cuda.empty_cache()
