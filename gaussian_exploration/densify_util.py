import torch, copy
from scene import GaussianModel
from utils.sh_utils import RGB2SH


def explore_random(gaussian_model: GaussianModel, num_explore=None, factor=1.0,
                   seed_samping_method="random_uniform", camera_extents=None):
    new_xyz = sampling_seed(gaussian_model.get_xyz, factor, num_explore,
                            seed_samping_method, camera_extents)
    new_features_dc = RGB2SH(torch.rand((num_explore,
                                         gaussian_model._features_dc.shape[1],
                                         gaussian_model._features_dc.shape[2]),
                                        device='cuda'))
    densify_points = new_gaussian_parameter(new_xyz, new_features_dc, num_explore,
                                            gaussian_model, camera_extents)
    return densify_points


def new_gaussian_parameter(new_xyz, new_features_dc, num_explore,
                           gaussian_model: GaussianModel, camera_extents,
                           scale_factor=1.0, opacity_factor=0.5):
    new_features_rest = torch.zeros((num_explore,
                                     gaussian_model._features_rest.shape[1],
                                     gaussian_model._features_rest.shape[2]),
                                    device='cuda')
    new_xyz_norm = torch.norm(new_xyz, dim=1).unsqueeze(1)
    G_xyz_norm = torch.norm(gaussian_model._xyz, dim=1).unsqueeze(1)
    scale_per_dist = torch.mean(gaussian_model.get_scaling / G_xyz_norm)

    new_scaling = torch.ones((num_explore, 3), device='cuda') * \
        gaussian_model.scaling_inverse_activation(
            scale_factor * scale_per_dist * new_xyz_norm)
    new_opacities = torch.ones((num_explore, 1), device='cuda') * \
        (new_xyz_norm / torch.max(new_xyz_norm)) * opacity_factor + 0.2
    new_opacities = gaussian_model.inverse_opacity_activation(new_opacities)
    new_rotation = torch.randn((num_explore, 4), device='cuda')

    densify_points = {
        "new_xyz": new_xyz, "new_opacities": new_opacities,
        "new_features_dc": new_features_dc, "new_features_rest": new_features_rest,
        "new_scaling": new_scaling, "new_rotation": new_rotation,
        "new_tmp_radii": torch.zeros((num_explore,), device='cuda')}
    return densify_points


def sampling_seed(mean_gaussians, factor=1.0, num_sample=80,
                  seed_samping_method="random_uniform", camera_extent=None,
                  prune_near=False, max_extent_factor=200.0):
    max_extent = torch.max(mean_gaussians * factor, dim=0).values
    min_extent = torch.min(mean_gaussians * factor, dim=0).values
    if camera_extent is not None:
        min_threshold = -torch.ones_like(min_extent) * max_extent_factor * float(camera_extent)
        max_threshold = torch.ones_like(max_extent) * max_extent_factor * float(camera_extent)
        min_extent = torch.max(min_extent, min_threshold)
        max_extent = torch.min(max_extent, max_threshold)

    extent = max_extent - min_extent
    if seed_samping_method == "random_uniform":
        position_seed = (torch.rand(num_sample, 3, device='cuda') - 0.5) * extent \
            + torch.mean(mean_gaussians, dim=0)
    elif seed_samping_method == "random_noise":
        position_seed = copy.deepcopy(
            mean_gaussians[torch.randperm(num_sample)]) \
            + torch.rand(num_sample, 3, device='cuda') * float(camera_extent) * 0.05 \
            if camera_extent else torch.rand(num_sample, 3, device='cuda') * 0.05
    else:
        raise ValueError(f"Invalid sampling method: {seed_samping_method}")
    if prune_near and camera_extent:
        position_seed = position_seed[torch.norm(position_seed, dim=1) > float(camera_extent)]
    return position_seed
