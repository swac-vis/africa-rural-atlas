import rasterio
import numpy as np
from rasterio.transform import from_origin

# === 打开源栅格 ===
src_path = "../data/ppp_2020_1km_africa.tif"
with rasterio.open(src_path) as src:
    src_data = src.read(1)
    src_transform = src.transform
    src_crs = src.crs
    src_nodata = src.nodata if src.nodata is not None else -9999

# 设置聚合因子
factor = 100
src_data[src_data == src_nodata] = np.nan  # 清除nodata

# === 计算输出栅格大小 ===
out_height = src_data.shape[0] // factor
out_width = src_data.shape[1] // factor

# === 初始化输出数据 ===
pop_lt300 = np.full((out_height, out_width), np.nan)
pop_ge300 = np.full((out_height, out_width), np.nan)
area_lt300 = np.zeros((out_height, out_width))
area_ge300 = np.zeros((out_height, out_width))

# === 聚合处理 ===
for i in range(out_height):
    for j in range(out_width):
        block = src_data[i*factor:(i+1)*factor, j*factor:(j+1)*factor]
        block = block[~np.isnan(block)]

        if block.size == 0:
            continue

        lt = block[block < 300]
        ge = block[block >= 300]

        pop_lt300[i, j] = lt.sum() if lt.size > 0 else 0
        area_lt300[i, j] = lt.size

        pop_ge300[i, j] = ge.sum() if ge.size > 0 else 0
        area_ge300[i, j] = ge.size

# === 设置新变换（缩小100倍） ===
new_transform = src_transform * rasterio.Affine.scale(factor)

# === 写入新的多波段 GeoTIFF ===
out_meta = {
    'driver': 'GTiff',
    'height': out_height,
    'width': out_width,
    'count': 4,
    'dtype': 'float32',
    'crs': src_crs,
    'transform': new_transform,
    'nodata': -9999
}

with rasterio.open('../map/aggregated_100km_africa.tif', 'w', **out_meta) as dst:
    dst.write(pop_lt300.astype(np.float32), 1)   # Band 1: pop < 300
    dst.write(area_lt300.astype(np.float32), 2)  # Band 2: area < 300
    dst.write(pop_ge300.astype(np.float32), 3)   # Band 3: pop ≥ 300
    dst.write(area_ge300.astype(np.float32), 4)  # Band 4: area ≥ 300
