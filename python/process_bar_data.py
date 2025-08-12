import pandas as pd
import json
import os
from collections import defaultdict

def process_bar_data():
    """处理bar文件夹中的CSV数据，生成堆叠条形图所需的JSON格式"""
    
    # 定义地区映射
    region_mapping = {
        'africa': 'Africa',
        'latin_america': 'Latin America', 
        'south_asia': 'South Asia'
    }
    
    # 定义距离区间
    distance_ranges = [
        (0, 10, "0-10km"),
        (10, 20, "10-20km"),
        (20, 30, "20-30km"),
        (30, 40, "30-40km"),
        (40, 50, "40-50km"),
        (50, 60, "50-60km"),
        (60, 70, "60-70km"),
        (70, 80, "70-80km"),
        (80, 90, "80-90km"),
        (90, 100, "90-100km")
    ]
    
    result = {}
    
    # 处理每个地区的数据
    for region_key, region_name in region_mapping.items():
        print(f"Processing {region_name}...")
        
        # 读取urban和rural数据
        urban_file = f"bar/{region_key}_urban.csv"
        rural_file = f"bar/{region_key}_rural.csv"
        
        if not (os.path.exists(urban_file) and os.path.exists(rural_file)):
            print(f"Warning: Missing files for {region_name}")
            continue
            
        # 读取数据
        urban_df = pd.read_csv(urban_file)
        rural_df = pd.read_csv(rural_file)
        
        # 初始化地区数据结构
        region_data = {}
        total_urban = 0
        total_rural = 0
        
        # 处理每个距离区间
        for start_dist, end_dist, range_name in distance_ranges:
            # 筛选该区间内的数据
            urban_mask = (urban_df['distance'] >= start_dist) & (urban_df['distance'] < end_dist)
            rural_mask = (rural_df['distance'] >= start_dist) & (rural_df['distance'] < end_dist)
            
            urban_pop = urban_df[urban_mask]['pop'].sum()
            rural_pop = rural_df[rural_mask]['pop'].sum()
            total_pop = urban_pop + rural_pop
            
            # 存储原始数据
            region_data[range_name] = {
                "rural": float(rural_pop),
                "urban": float(urban_pop),
                "total": float(total_pop)
            }
            
            total_urban += urban_pop
            total_rural += rural_pop
        
        # 计算share数据
        total_population = total_urban + total_rural
        share_data = {}
        
        for range_name in region_data:
            urban_pop = region_data[range_name]["urban"]
            rural_pop = region_data[range_name]["rural"]
            total_pop = region_data[range_name]["total"]
            
            share_data[range_name] = {
                "rural": float(rural_pop / total_population) if total_population > 0 else 0,
                "urban": float(urban_pop / total_population) if total_population > 0 else 0,
                "total": float(total_pop / total_population) if total_population > 0 else 0
            }
        
        # 构建最终的地区数据结构
        result[region_name] = {
            **region_data,
            "share": share_data
        }
    
    # 保存JSON文件
    output_file = "bar/bar_chart_data.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Data processed and saved to {output_file}")
    
    # 打印一些统计信息
    for region_name, data in result.items():
        print(f"\n{region_name}:")
        for range_name in ["0-10km", "10-20km", "20-30km"]:
            if range_name in data:
                print(f"  {range_name}: Urban={data[range_name]['urban']:.0f}, Rural={data[range_name]['rural']:.0f}")

if __name__ == "__main__":
    process_bar_data() 