import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import math
import os

print("Generating high-resolution photorealistic Earth equirectangular texture...")

width = 2048
height = 1024

# Create coordinate grids
# lat: -pi/2 to +pi/2, lon: -pi to +pi
lats = np.linspace(math.pi/2, -math.pi/2, height)
lons = np.linspace(-math.pi, math.pi, width)
lon_grid, lat_grid = np.meshgrid(lons, lats)

# Convert lat/lon to degrees
lat_deg = np.degrees(lat_grid)
lon_deg = np.degrees(lon_grid)

# Fast 2D Fractal Brownian Motion for natural coastlines and terrain
def generate_fbm(h, w, octaves=6, persistence=0.5, scale=4.0):
    np.random.seed(42)
    noise = np.zeros((h, w), dtype=np.float32)
    current_scale = scale
    current_amp = 1.0
    for _ in range(octaves):
        # Generate low-res random grid and interpolate
        grid_h = max(2, int(h / current_scale))
        grid_w = max(2, int(w / current_scale))
        rand_grid = np.random.uniform(-1.0, 1.0, (grid_h, grid_w)).astype(np.float32)
        im = Image.fromarray(rand_grid)
        im_res = im.resize((w, h), Image.Resampling.BICUBIC)
        noise += np.array(im_res) * current_amp
        current_scale /= 2.0
        current_amp *= persistence
    # Normalize to [0, 1]
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    return noise

terrain_noise = generate_fbm(height, width, octaves=6, persistence=0.55, scale=64.0)
detail_noise = generate_fbm(height, width, octaves=4, persistence=0.5, scale=16.0)

# Continent shapes defined by ellipsoidal / polygonal distance fields
land_mask = np.zeros((height, width), dtype=np.float32)

def add_continent(lon_c, lat_c, r_lon, r_lat, weight=1.0):
    d = ((lon_deg - lon_c) / r_lon)**2 + ((lat_deg - lat_c) / r_lat)**2
    mask = np.clip(1.0 - d, 0.0, 1.0)
    return mask * weight

# 1. Africa
land_mask = np.maximum(land_mask, add_continent(20, 5, 22, 35, 1.0))
# 2. Eurasia
land_mask = np.maximum(land_mask, add_continent(80, 50, 65, 25, 1.0))
land_mask = np.maximum(land_mask, add_continent(30, 50, 30, 20, 1.0)) # Europe
land_mask = np.maximum(land_mask, add_continent(100, 30, 35, 20, 1.0)) # East Asia
land_mask = np.maximum(land_mask, add_continent(78, 20, 15, 15, 1.0)) # India
land_mask = np.maximum(land_mask, add_continent(45, 25, 18, 12, 1.0)) # Arabia
# 3. North America
land_mask = np.maximum(land_mask, add_continent(-100, 48, 45, 25, 1.0))
land_mask = np.maximum(land_mask, add_continent(-105, 30, 20, 18, 1.0)) # USA/Mexico
land_mask = np.maximum(land_mask, add_continent(-40, 72, 22, 12, 1.0)) # Greenland
# 4. South America
land_mask = np.maximum(land_mask, add_continent(-60, -18, 22, 35, 1.0))
# 5. Australia
land_mask = np.maximum(land_mask, add_continent(134, -26, 20, 16, 1.0))
# 6. Antarctica (South Pole)
antarctica_d = np.clip(( -lat_deg - 65.0 ) / 20.0, 0.0, 1.0)
land_mask = np.maximum(land_mask, antarctica_d)

# Combine macro shapes with fractal noise to generate realistic fractal coastlines
rough_land = land_mask * 0.7 + (terrain_noise - 0.45) * 0.65 + (detail_noise - 0.5) * 0.15
is_land = rough_land > 0.42

# Base Ocean Colors: Deep navy blue with coastal turquoise shelves
ocean_depth = np.clip((0.42 - rough_land) / 0.42, 0.0, 1.0)
ocean_r = np.clip(10.0 + (1.0 - ocean_depth) * 20.0, 0, 255)
ocean_g = np.clip(28.0 + (1.0 - ocean_depth) * 65.0, 0, 255)
ocean_b = np.clip(62.0 + (1.0 - ocean_depth) * 80.0, 0, 255)

# Biomes:
# Deserts (Sahara, Arabia, Australia, Gobi)
desert_prob = np.zeros_like(lat_deg)
# Sahara / Arabia (~ 15 to 32 N, -15 to 55 E)
desert_sahara = np.exp(-((lat_deg - 24)**2 / 70.0 + (lon_deg - 20)**2 / 600.0))
# Australia interior (-28 to -18 S, 120 to 140 E)
desert_aus = np.exp(-((lat_deg + 24)**2 / 50.0 + (lon_deg - 132)**2 / 120.0))
# Gobi (40N, 100E)
desert_gobi = np.exp(-((lat_deg - 42)**2 / 40.0 + (lon_deg - 100)**2 / 200.0))
desert_factor = np.clip(desert_sahara + desert_aus + desert_gobi, 0.0, 1.0)

# Ice / Snow (Antarctica < -65, Greenland, Arctic > 68)
polar_factor = np.clip((np.abs(lat_deg) - 62.0) / 12.0, 0.0, 1.0)
# High mountain snow (Himalayas, Andes, Rockies)
mountain_factor = np.clip((terrain_noise - 0.68) / 0.25, 0.0, 1.0) * is_land

# Land base colors:
# Lush vegetation green
veg_r = 38.0 + detail_noise * 20.0
veg_g = 85.0 + detail_noise * 30.0
veg_b = 32.0 + detail_noise * 15.0

# Desert ochre/sand
des_r = 195.0 + detail_noise * 25.0
des_g = 155.0 + detail_noise * 20.0
des_b = 105.0 + detail_noise * 15.0

# Ice pure white
ice_r = 238.0 + detail_noise * 15.0
ice_g = 244.0 + detail_noise * 10.0
ice_b = 252.0 + detail_noise * 3.0

# Blend biomes
land_r = veg_r * (1.0 - desert_factor) + des_r * desert_factor
land_g = veg_g * (1.0 - desert_factor) + des_g * desert_factor
land_b = veg_b * (1.0 - desert_factor) + des_b * desert_factor

land_r = land_r * (1.0 - polar_factor) + ice_r * polar_factor
land_g = land_g * (1.0 - polar_factor) + ice_g * polar_factor
land_b = land_b * (1.0 - polar_factor) + ice_b * polar_factor

land_r = land_r * (1.0 - mountain_factor) + ice_r * mountain_factor
land_g = land_g * (1.0 - mountain_factor) + ice_g * mountain_factor
land_b = land_b * (1.0 - mountain_factor) + ice_b * mountain_factor

# Composite Surface (Ocean + Land)
surface_r = np.where(is_land, land_r, ocean_r)
surface_g = np.where(is_land, land_g, ocean_g)
surface_b = np.where(is_land, land_b, ocean_b)

# 4. Realistic Cloud Layer (Swirling weather fronts and equatorial ITCZ)
cloud_noise1 = generate_fbm(height, width, octaves=5, persistence=0.55, scale=48.0)
cloud_noise2 = generate_fbm(height, width, octaves=4, persistence=0.5, scale=20.0)

# Equatorial convergence band (ITCZ at ~ 5 deg N)
itcz = np.exp(-((lat_deg - 5.0)**2) / 60.0) * 0.4
# Mid-latitude swirl bands (~ 40-55 N and S)
storm_bands = (np.exp(-((lat_deg - 48.0)**2) / 90.0) + np.exp(-((lat_deg + 48.0)**2) / 90.0)) * 0.35

cloud_density = (cloud_noise1 * 0.7 + cloud_noise2 * 0.3) + itcz + storm_bands
cloud_mask = np.clip((cloud_density - 0.48) / 0.35, 0.0, 0.88) # Soft translucent clouds

# Composite Clouds onto surface
final_r = np.clip(surface_r * (1.0 - cloud_mask) + 255.0 * cloud_mask, 0, 255).astype(np.uint8)
final_g = np.clip(surface_g * (1.0 - cloud_mask) + 255.0 * cloud_mask, 0, 255).astype(np.uint8)
final_b = np.clip(surface_b * (1.0 - cloud_mask) + 255.0 * cloud_mask, 0, 255).astype(np.uint8)

rgb = np.stack([final_r, final_g, final_b], axis=-1)
earth_img = Image.fromarray(rgb, 'RGB')

out_path = 'UnrealProject/Content/Earth/T_Earth_Day.png'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
earth_img.save(out_path, format='PNG')
print(f"Earth day texture successfully created at: {out_path} ({os.path.getsize(out_path)} bytes)")

