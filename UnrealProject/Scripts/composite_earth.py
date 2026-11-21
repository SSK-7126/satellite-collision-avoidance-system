from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os

print("Compositing authentic NASA Blue Marble Earth surface and cloud layer with RGBA fix...")

atmos_path = "UnrealProject/Content/Earth/earth_atmos_2048.jpg"
clouds_path = "UnrealProject/Content/Earth/earth_clouds_1024.png"
out_path = "UnrealProject/Content/Earth/T_Earth_Day.png"

atmos_img = Image.open(atmos_path).convert("RGB")
clouds_img = Image.open(clouds_path).convert("RGBA").resize(atmos_img.size, Image.Resampling.BILINEAR)

# Extract cloud alpha
clouds_r, clouds_g, clouds_b, clouds_a = clouds_img.split()
# Smooth slightly to remove any palette quantization
clouds_a = clouds_a.filter(ImageFilter.GaussianBlur(1.0))

clouds_arr = np.array(clouds_a, dtype=np.float32) / 255.0
cloud_intensity = np.clip(clouds_arr * 0.45, 0.0, 0.8)

atmos_arr = np.array(atmos_img, dtype=np.float32)

final_arr = np.zeros_like(atmos_arr)
for c in range(3):
    final_arr[..., c] = np.clip(atmos_arr[..., c] * (1.0 - cloud_intensity) + 255.0 * cloud_intensity, 0, 255)

final_img = Image.fromarray(final_arr.astype(np.uint8), "RGB")

enhancer = ImageEnhance.Color(final_img)
vibrant_img = enhancer.enhance(1.2)
contrast = ImageEnhance.Contrast(vibrant_img)
polished_img = contrast.enhance(1.05)

polished_img.save(out_path, format="PNG")
print(f"High-resolution Earth texture generated at {out_path} ({os.path.getsize(out_path)} bytes)")
