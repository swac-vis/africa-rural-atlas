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
factor = 1000  # 1000x1000聚合
src_data[src_data == src_nodata] = np.nan  # 清除nodata

# === 计算输出栅格大小 ===
out_height = src_data.shape[0] // factor
out_width = src_data.shape[1] // factor

print(f"输入数据大小: {src_data.shape}")
print(f"聚合因子: {factor}")
print(f"输出数据大小: {out_height} x {out_width}")

# === 初始化输出数据 ===
pop_lt300 = np.full((out_height, out_width), np.nan)
pop_ge300 = np.full((out_height, out_width), np.nan)
area_lt300 = np.zeros((out_height, out_width))
area_ge300 = np.zeros((out_height, out_width))

# === 聚合处理 ===
print("开始聚合处理...")
for i in range(out_height):
    for j in range(out_width):
        # 获取当前1000x1000块
        start_i = i * factor
        end_i = (i + 1) * factor
        start_j = j * factor
        end_j = (j + 1) * factor
        
        block = src_data[start_i:end_i, start_j:end_j]
        block = block[~np.isnan(block)]

        if block.size == 0:
            continue

        # 分类统计
        lt = block[block < 300]  # 农村区域
        ge = block[block >= 300]  # 城市区域

        pop_lt300[i, j] = lt.sum() if lt.size > 0 else 0
        area_lt300[i, j] = lt.size

        pop_ge300[i, j] = ge.sum() if ge.size > 0 else 0
        area_ge300[i, j] = ge.size

    # 显示进度
    if (i + 1) % 10 == 0:
        print(f"处理进度: {i + 1}/{out_height} ({((i + 1) / out_height * 100):.1f}%)")

# === 设置新变换（缩小1000倍） ===
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

output_path = '../map/aggregated_1000km_africa.tif'
print(f"保存到: {output_path}")

with rasterio.open(output_path, 'w', **out_meta) as dst:
    dst.write(pop_lt300.astype(np.float32), 1)   # Band 1: pop < 300
    dst.write(area_lt300.astype(np.float32), 2)  # Band 2: area < 300
    dst.write(pop_ge300.astype(np.float32), 3)   # Band 3: pop ≥ 300
    dst.write(area_ge300.astype(np.float32), 4)  # Band 4: area ≥ 300

# === 输出统计信息 ===
print("\n=== 聚合统计信息 ===")
print(f"输出网格大小: {out_height} x {out_width}")
print(f"网格单元大小: {factor}km x {factor}km")

# 计算有效网格数量
valid_cells = np.sum(~np.isnan(pop_lt300 + pop_ge300))
print(f"有效网格数量: {valid_cells}")

# 计算总人口
total_pop = np.nansum(pop_lt300 + pop_ge300)
print(f"总人口: {total_pop:,.0f}")

# 计算城市/农村比例
urban_pop = np.nansum(pop_ge300)
rural_pop = np.nansum(pop_lt300)
print(f"城市人口: {urban_pop:,.0f} ({urban_pop/total_pop*100:.1f}%)")
print(f"农村人口: {rural_pop:,.0f} ({rural_pop/total_pop*100:.1f}%)")

print(f"\n数据已保存到: {output_path}") 