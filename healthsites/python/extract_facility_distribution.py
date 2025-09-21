#!/usr/bin/env python3
"""
Extract Facility Distribution from Existing Analysis
从现有分析结果中提取设施分布数据

This script reads the detailed analysis results and extracts facility distribution
by counting facilities in urban vs rural grid cells.
"""

import json
import numpy as np
import pandas as pd
import os

def extract_facility_distribution():
    """Extract facility distribution from detailed analysis results"""
    print("=== 从现有分析结果提取设施分布 ===")
    
    # Load the detailed analysis results
    detailed_file = '../data/pharmacy_accessibility_analysis_detailed.json'
    
    if not os.path.exists(detailed_file):
        print(f"错误: 详细分析文件不存在: {detailed_file}")
        return False
    
    print("正在加载详细分析数据...")
    with open(detailed_file, 'r') as f:
        data = json.load(f)
    
    # Check if we have grid level data
    if 'grid_level_data' not in data:
        print("错误: 没有找到网格级数据")
        return False
    
    grid_data = data['grid_level_data']
    print(f"加载了 {len(grid_data):,} 个网格的数据")
    
    # Count facilities by urban/rural classification
    urban_facilities = 0
    rural_facilities = 0
    total_grids_with_facilities = 0
    
    print("正在统计设施分布...")
    for grid in grid_data:
        facilities_count = grid.get('facilities_count', 0)
        population_original = grid.get('population_original', 0)
        
        if facilities_count > 0:
            total_grids_with_facilities += 1
            if population_original > 0:
                # Urban area (positive population density)
                urban_facilities += facilities_count
            else:
                # Rural area (negative or zero population density)
                rural_facilities += facilities_count
    
    total_facilities = urban_facilities + rural_facilities
    
    # Calculate percentages
    urban_percentage = (urban_facilities / total_facilities * 100) if total_facilities > 0 else 0
    rural_percentage = (rural_facilities / total_facilities * 100) if total_facilities > 0 else 0
    
    # Calculate urban-rural ratio
    urban_rural_ratio = urban_facilities / rural_facilities if rural_facilities > 0 else float('inf')
    
    # Determine urban dominance
    urban_dominance = urban_facilities > rural_facilities
    
    # Compile results
    results = {
        'total_facilities': total_facilities,
        'urban_facilities': {
            'count': urban_facilities,
            'percentage': round(urban_percentage, 1)
        },
        'rural_facilities': {
            'count': rural_facilities,
            'percentage': round(rural_percentage, 1)
        },
        'summary': {
            'urban_rural_ratio': round(urban_rural_ratio, 2),
            'urban_dominance': urban_dominance,
            'classification_method': 'GHSL population density data',
            'data_source': 'Real GHSL population raster data'
        },
        'note': '基于真实GHSL人口密度数据的分析结果。城市区域：人口密度 > 0，农村区域：人口密度 ≤ 0',
        'metadata': {
            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'GHSL population density raster',
            'facility_source': 'Africa_all_healthsites.geojson',
            'total_processed': total_facilities,
            'successfully_classified': total_facilities,
            'classification_rate': 100.0,
            'grids_with_facilities': total_grids_with_facilities
        }
    }
    
    print(f"设施分布分析完成：")
    print(f"  总设施数: {total_facilities:,}")
    print(f"  城市设施: {urban_facilities:,} ({urban_percentage:.1f}%)")
    print(f"  农村设施: {rural_facilities:,} ({rural_percentage:.1f}%)")
    print(f"  城市/农村比例: {urban_rural_ratio:.2f}")
    print(f"  城市占优: {urban_dominance}")
    print(f"  有设施的网格数: {total_grids_with_facilities:,}")
    
    # Save results
    output_path = '../data/facility_urban_rural_distribution.json'
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 结果已保存到: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ 保存文件时出错: {e}")
        return False

def main():
    """Main function"""
    if extract_facility_distribution():
        print("\n🎉 设施分布提取完成！")
        print("📊 基于真实GHSL人口密度数据生成了准确的设施城乡分布")
    else:
        print("\n❌ 设施分布提取失败！")

if __name__ == "__main__":
    main()
