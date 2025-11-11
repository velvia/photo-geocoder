# denoise_evaluate_v2.py
import os
import argparse
from pathlib import Path

import torch
import torch.nn.functional as F
import torchvision.transforms as T
from torchvision.io import read_image, write_png
from torchvision.utils import save_image
import numpy as np
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim

# -------------------------------------------------
def load_dncnn(device: torch.device):
    """Download a pre‑trained DnCNN model from PyTorch Hub."""
    model = torch.hub.load('cszn/DnCNN', 'dncnn', pretrained=True, map_location=device)
    model.eval()
    return model

# -------------------------------------------------
def preprocess(img_tensor: torch.Tensor) -> torch.Tensor:
    """[0,255] uint8 → float32 [0,1] with batch dim."""
    img = img_tensor.float() / 255.0
    if img.dim() == 3:          # C×H×W → 1×C×H×W
        img = img.unsqueeze(0)
    return img

# -------------------------------------------------
def add_gaussian_noise(img: torch.Tensor, sigma: float) -> torch.Tensor:
    """
    Add zero‑mean Gaussian noise.
    *sigma* is the standard deviation **in the 0‑255 intensity scale**.
    """
    if sigma <= 0:
        return img
    noise = torch.randn_like(img) * (sigma / 255.0)
    return torch.clamp(img + noise, 0.0, 1.0)

# -------------------------------------------------
def evaluate(noisy, clean, denoised, out_path: Path):
    """Save images and print PSNR/SSIM."""
    for name, tensor in zip(['noisy', 'denoised'], [noisy, denoised]):
        save_image(tensor, out_path / f'{name}.png')

    # Convert to uint8 for metric calculation
    def to_uint8(t):
        return (t.squeeze().cpu().numpy() * 255).astype(np.uint8).transpose(1, 2, 0)

    noisy_np, clean_np, denoised_np = map(to_uint8, (noisy, clean, denoised))

    print(f'PSNR  noisy → clean: {psnr(clean_np, noisy_np, data_range=255):.2f} dB')
    print(f'PSNR denoised → clean: {psnr(clean_np, denoised_np, data_range=255):.2f} dB')
    print(f'SSIM  noisy → clean: {ssim(clean_np, noisy_np, multichannel=True, data_range=255):.4f}')
    print(f'SSIM denoised → clean: {ssim(clean_np, denoised_np, multichannel=True, data_range=255):.4f}')

# -------------------------------------------------
def main(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = load_dncnn(device)

    transform = T.Compose([
        T.Resize((args.size, args.size))   # optional uniform resize
    ])

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_dir = Path(args.clean) if args.clean else None

    for img_path in sorted(input_dir.glob('*.jpg')):
        name = img_path.stem
        print(f'--- {name} ---')

        img = read_image(str(img_path))
        img = transform(img)

        clean_tensor = preprocess(img).to(device)

        # ---------- Noise handling ----------
        if args.add_noise:
            noisy_tensor = add_gaussian_noise(clean_tensor, sigma=args.sigma)
        else:
            # Use the image as‑is (assumed already noisy)
            noisy_tensor = clean_tensor.clone()
        # -------------------------------------

        # DnCNN works on a single channel; convert if needed
        if noisy_tensor.shape[1] == 3:
            noisy_gray = noisy_tensor.mean(dim=1, keepdim=True)   # simple luminance
        else:
            noisy_gray = noisy_tensor

        with torch.no_grad():
            residual = model(noisy_gray)
            denoised_gray = torch.clamp(noisy_gray - residual, 0.0, 1.0)

        # Restore three channels for saving (optional)
        if img.shape[0] == 3:
            denoised = denoised_gray.repeat(1, 3, 1, 1)
        else:
            denoised = denoised_gray

        out_sub = output_dir / name
        out_sub.mkdir(exist_ok=True)

        if clean_dir:
            clean_ref = read_image(str(clean_dir / f'{name}.jpg'))
            clean_ref = transform(clean_ref)
            clean_ref = preprocess(clean_ref).to(device)
            evaluate(noisy_tensor, clean_ref, denoised, out_sub)
        else:
            save_image(noisy_tensor, out_sub / 'noisy.png')
            save_image(denoised, out_sub / 'denoised.png')
            print('Saved noisy & denoised images (no reference metrics).')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download DnCNN, optionally add Gaussian noise, and test on JPGs')
    parser.add_argument('--input', required=True, help='Folder with input JPGs')
    parser.add_argument('--output', default='output', help='Folder for results')
    parser.add_argument('--clean', help='Folder with clean reference JPGs (optional)')
    parser.add_argument('--add-noise', action='store_true',
                        help='If set, synthetic Gaussian noise will be added')
    parser.add_argument('--sigma', type=float, default=25.0,
                        help='Standard deviation of Gaussian noise (0‑255 scale). Ignored if --add-noise not set')
    parser.add_argument('--size', type=int, default=512,
                        help='Resize images to SIZE×SIZE (optional)')
    args = parser.parse_args()
    main(args)

