# app/human_pose_estimator/utils.py
from typing import Callable
import torch
from torchvision import transforms
from .types import RGBFrame


def create_image_preprocessor(
    input_size: tuple[int, int] = (768, 1024),
    mean: list[float] = [0.485, 0.456, 0.406],
    std: list[float] = [0.229, 0.224, 0.225]
) -> Callable[[RGBFrame], torch.Tensor]:
    """
    Create a preprocessor for Sapiens-based estimation models.

    Converts a uint8 image array into a normalized float32 tensor
    resized to the model's expected input dimensions and adds a batch dimension.

    Parameters
    ----------
    input_size : tuple[int, int]
        Target input size as `(height, width)`. Sapiens models typically
        expect images of size `(768, 1024)` (H, W). Default is `(768, 1024)`.
    mean : list[float], optional
        Mean values for ImageNet-style normalization across RGB channels.
        Default is `[0.485, 0.456, 0.406]`.
    std : list[float], optional
        Standard deviations for ImageNet-style normalization across RGB channels.
        Default is `[0.229, 0.224, 0.225]`.

    Returns
    -------
    Callable[[RGBFrame], torch.Tensor]
        A callable preprocessing pipeline that takes a `(H, W, 3)` uint8 image
        and returns a normalized `(1, 3, H_out, W_out)` float32 tensor.
    """
    
    return transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((input_size[1], input_size[0])),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
        transforms.Lambda(lambda x: x.unsqueeze(0))
    ])