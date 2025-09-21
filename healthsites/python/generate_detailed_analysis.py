#!/usr/bin/env python3
"""
Generate Detailed Pharmacy Accessibility Analysis
生成包含详细网格级数据的准确药房可及性分析
"""

import json
import numpy as np
import pandas as pd
from pharmacy_accessibility_analysis import PharmacyAccessibilityAnalyzer

def generate_detailed_analysis():
    """生成详细的分析数据"""
    
    print("="*60)
    print("生成详细的药房可及性分析数据")
    print("="*60)
    
    # 文件路径
    population_tif = "../../map_real/ghslpop_africa.tif"
    pharmacy_geojson = "../data/Africa_all_healthsites.geojson"
    output_json = "../data/pharmacy_accessibility_analysis_detailed.json"
    
    # 创建分析器并运行分析
    analyzer = PharmacyAccessibilityAnalyzer(population_tif, pharmacy_geojson)
    results = analyzer.run_analysis()
    
    # 添加额外的详细统计信息
    print("\n添加详细统计信息...")
    
    # 计算距离分布统计
    distances = [r["distance"] for r in results["grid_level_data"] if not np.isnan(r["distance"])]
    urban_distances = [r["distance"] for r in results["grid_level_data"] if r["population_original"] > 0 and not np.isnan(r["distance"])]
    rural_distances = [r["distance"] for r in results["grid_level_data"] if r["population_original"] < 0 and not np.isnan(r["distance"])]
    
    distance_stats = {
        "overall": {
            "min_distance": float(np.min(distances)),
            "max_distance": float(np.max(distances)),
            "mean_distance": float(np.mean(distances)),
            "median_distance": float(np.median(distances)),
            "std_distance": float(np.std(distances))
        },
        "urban": {
            "min_distance": float(np.min(urban_distances)) if urban_distances else 0,
            "max_distance": float(np.max(urban_distances)) if urban_distances else 0,
            "mean_distance": float(np.mean(urban_distances)) if urban_distances else 0,
            "median_distance": float(np.median(urban_distances)) if urban_distances else 0,
            "std_distance": float(np.std(urban_distances)) if urban_distances else 0
        },
        "rural": {
            "min_distance": float(np.min(rural_distances)) if rural_distances else 0,
            "max_distance": float(np.max(rural_distances)) if rural_distances else 0,
            "mean_distance": float(np.mean(rural_distances)) if rural_distances else 0,
            "median_distance": float(np.median(rural_distances)) if rural_distances else 0,
            "std_distance": float(np.std(rural_distances)) if rural_distances else 0
        }
    }
    
    # 计算人口分布统计
    populations = [r["population"] for r in results["grid_level_data"] if not np.isnan(r["population"])]
    urban_populations = [r["population"] for r in results["grid_level_data"] if r["population_original"] > 0 and not np.isnan(r["population"])]
    rural_populations = [r["population"] for r in results["grid_level_data"] if r["population_original"] < 0 and not np.isnan(r["population"])]
    
    population_stats = {
        "overall": {
            "total_population": int(sum(populations)),
            "mean_population": float(np.mean(populations)),
            "median_population": float(np.median(populations)),
            "max_population": int(np.max(populations)),
            "min_population": int(np.min(populations))
        },
        "urban": {
            "total_population": int(sum(urban_populations)) if urban_populations else 0,
            "mean_population": float(np.mean(urban_populations)) if urban_populations else 0,
            "median_population": float(np.median(urban_populations)) if urban_populations else 0,
            "max_population": int(np.max(urban_populations)) if urban_populations else 0,
            "min_population": int(np.min(urban_populations)) if urban_populations else 0
        },
        "rural": {
            "total_population": int(sum(rural_populations)) if rural_populations else 0,
            "mean_population": float(np.mean(rural_populations)) if rural_populations else 0,
            "median_population": float(np.median(rural_populations)) if rural_populations else 0,
            "max_population": int(np.max(rural_populations)) if rural_populations else 0,
            "min_population": int(np.min(rural_populations)) if rural_populations else 0
        }
    }
    
    # 计算距离类别分布
    distance_categories = {}
    for result in results["grid_level_data"]:
        category = result["distance_category"]
        if category not in distance_categories:
            distance_categories[category] = {"count": 0, "population": 0, "urban_count": 0, "rural_count": 0}
        
        distance_categories[category]["count"] += 1
        distance_categories[category]["population"] += result["population"]
        
        if result["population_original"] > 0:
            distance_categories[category]["urban_count"] += 1
        else:
            distance_categories[category]["rural_count"] += 1
    
    # 添加详细统计到结果中
    results["detailed_statistics"] = {
        "distance_statistics": distance_stats,
        "population_statistics": population_stats,
        "distance_category_distribution": distance_categories
    }
    
    # 更新元数据
    results["metadata"]["detailed_analysis"] = True
    results["metadata"]["grid_data_included"] = True
    results["metadata"]["pharmacy_locations_included"] = True
    results["metadata"]["statistical_summary_included"] = True
    
    # 保存详细结果
    print(f"\n保存详细分析结果到: {output_json}")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # 打印详细摘要
    print("\n" + "="*60)
    print("详细分析摘要")
    print("="*60)
    
    print(f"\n基本统计:")
    print(f"  总网格数: {results['metadata']['total_grids_analyzed']:,}")
    print(f"  健康设施位置: {results['metadata']['unique_pharmacy_locations']:,}")
    print(f"  总人口: {population_stats['overall']['total_population']:,}")
    print(f"  城市人口: {population_stats['urban']['total_population']:,}")
    print(f"  农村人口: {population_stats['rural']['total_population']:,}")
    
    print(f"\n距离统计:")
    print(f"  平均距离: {distance_stats['overall']['mean_distance']:.1f} km")
    print(f"  城市平均距离: {distance_stats['urban']['mean_distance']:.1f} km")
    print(f"  农村平均距离: {distance_stats['rural']['mean_distance']:.1f} km")
    print(f"  最大距离: {distance_stats['overall']['max_distance']:.1f} km")
    print(f"  最小距离: {distance_stats['overall']['min_distance']:.1f} km")
    
    print(f"\n距离类别分布:")
    for category, stats in distance_categories.items():
        print(f"  {category}: {stats['count']:,} 网格, {stats['population']:,} 人口")
    
    print(f"\n覆盖率:")
    coverage = results["urban_rural_gap"]["coverage_gap"]
    print(f"  城市1km覆盖率: {coverage['1km']['urban_coverage']:.1f}%")
    print(f"  农村1km覆盖率: {coverage['1km']['rural_coverage']:.1f}%")
    print(f"  城市5km覆盖率: {coverage['5km']['urban_coverage']:.1f}%")
    print(f"  农村5km覆盖率: {coverage['5km']['rural_coverage']:.1f}%")
    
    print(f"\n文件信息:")
    print(f"  输出文件: {output_json}")
    print(f"  包含网格级数据: 是")
    print(f"  包含药房位置: 是")
    print(f"  包含统计摘要: 是")
    
    return results

if __name__ == "__main__":
    generate_detailed_analysis()
