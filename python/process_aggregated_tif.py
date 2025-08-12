import rasterio
import numpy as np
import json
from rasterio.transform import xy

def process_aggregated_tif(tif_path, output_path):
    """
    处理聚合的TIF文件，输出为JSON格式
    每个格子作为一个key，value包含地理位置和四个波段的数据
    """
    
    with rasterio.open(tif_path) as src:
        # 读取所有波段数据
        data = src.read()
        
        # 获取地理变换信息
        transform = src.transform
        crs = src.crs
        
        print(f"TIF文件信息:")
        print(f"  形状: {src.shape}")
        print(f"  波段数: {src.count}")
        print(f"  坐标系统: {crs}")
        print(f"  变换矩阵: {transform}")
        
        # 初始化结果字典
        grid_data = {}
        
        # 遍历每个网格单元
        for row in range(src.height):
            for col in range(src.width):
                # 计算地理坐标（网格中心点）
                # 使用 xy() 函数获取正确的坐标
                x, y = xy(transform, col, row)
                
                # 获取该网格的四个波段数据
                rural_population = float(data[0][row, col])  # Band 1: rural population
                rural_area = float(data[1][row, col])        # Band 2: rural area
                urban_population = float(data[2][row, col])  # Band 3: urban population
                urban_area = float(data[3][row, col])        # Band 4: urban area
                
                # 跳过无效数据（nodata值）
                if rural_population == -9999 or np.isnan(rural_population):
                    continue
                
                # 创建网格键（使用行列坐标）
                grid_key = f"grid_{row}_{col}"
                
                # 存储数据 - 注意：x是经度，y是纬度
                grid_data[grid_key] = {
                    "geographic_location": {
                        "longitude": x,  # 经度
                        "latitude": y,   # 纬度
                        "row": row,
                        "col": col
                    },
                    "rural_population": rural_population,
                    "rural_area": rural_area,
                    "urban_population": urban_population,
                    "urban_area": urban_area
                }
        
        # 添加元数据
        result = {
            "metadata": {
                "source_file": tif_path,
                "grid_size": f"{src.height}x{src.width}",
                "coordinate_system": str(crs),
                "transform": str(transform),
                "description": {
                    "band_1": "rural_population (population < 300)",
                    "band_2": "rural_area (area < 300)",
                    "band_3": "urban_population (population >= 300)",
                    "band_4": "urban_area (area >= 300)"
                }
            },
            "grid_data": grid_data
        }
        
        # 保存为JSON文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n处理完成:")
        print(f"  有效网格数量: {len(grid_data)}")
        print(f"  输出文件: {output_path}")
        
        # 输出统计信息
        rural_pop_total = sum(item["rural_population"] for item in grid_data.values())
        urban_pop_total = sum(item["urban_population"] for item in grid_data.values())
        rural_area_total = sum(item["rural_area"] for item in grid_data.values())
        urban_area_total = sum(item["urban_area"] for item in grid_data.values())
        
        print(f"\n统计信息:")
        print(f"  总农村人口: {rural_pop_total:,.0f}")
        print(f"  总城市人口: {urban_pop_total:,.0f}")
        print(f"  总农村面积: {rural_area_total:,.0f}")
        print(f"  总城市面积: {urban_area_total:,.0f}")
        print(f"  总人口: {rural_pop_total + urban_pop_total:,.0f}")
        
        return result

if __name__ == "__main__":
    # 输入和输出文件路径
    tif_file = "map/aggregated_1000km_africa.tif"
    output_file = "map/aggregated_1000km_africa_fixed.json"
    
    # 处理TIF文件
    result = process_aggregated_tif(tif_file, output_file)
    
    # 显示前几个网格的数据作为示例
    print(f"\n前5个网格的数据示例:")
    for i, (key, value) in enumerate(list(result["grid_data"].items())[:5]):
        print(f"\n{key}:")
        print(f"  位置: 经度={value['geographic_location']['longitude']:.4f}, 纬度={value['geographic_location']['latitude']:.4f}")
        print(f"  农村人口: {value['rural_population']:,.0f}")
        print(f"  农村面积: {value['rural_area']:,.0f}")
        print(f"  城市人口: {value['urban_population']:,.0f}")
        print(f"  城市面积: {value['urban_area']:,.0f}") 