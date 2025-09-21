#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非洲健康设施数据分析脚本
分析下载的GeoJSON文件，统计各国健康设施数量和类型分布
"""

import json
import os
import glob
from collections import defaultdict, Counter
import pandas as pd

def analyze_healthsites_data():
    """分析健康设施数据"""
    
    # 获取所有GeoJSON文件
    geojson_dir = "africa_geojson"
    geojson_files = glob.glob(os.path.join(geojson_dir, "*.geojson"))
    
    if not geojson_files:
        print("❌ 未找到GeoJSON文件，请先运行下载脚本")
        return
    
    print(f"📁 找到 {len(geojson_files)} 个国家的数据文件")
    print("=" * 60)
    
    # 统计数据
    country_stats = {}
    facility_types = Counter()
    total_facilities = 0
    
    for file_path in geojson_files:
        country_name = os.path.basename(file_path).replace('.geojson', '')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get('features', [])
            facility_count = len(features)
            
            # 统计设施类型
            country_facility_types = Counter()
            for feature in features:
                properties = feature.get('properties', {})
                attributes = properties.get('attributes', {})
                amenity = attributes.get('amenity', 'unknown')
                healthcare = attributes.get('healthcare', 'unknown')
                
                # 主要类型
                if amenity in ['clinic', 'hospital', 'pharmacy']:
                    facility_types[amenity] += 1
                    country_facility_types[amenity] += 1
                elif healthcare in ['clinic', 'hospital', 'phinic']:
                    facility_types[healthcare] += 1
                    country_facility_types[healthcare] += 1
                else:
                    facility_types['other'] += 1
                    country_facility_types['other'] += 1
            
            country_stats[country_name] = {
                'total': facility_count,
                'types': dict(country_facility_types)
            }
            
            total_facilities += facility_count
            
            print(f"🇹🇿 {country_name}: {facility_count} 个设施")
            
        except Exception as e:
            print(f"❌ 处理 {country_name} 时出错: {e}")
    
    print("=" * 60)
    print(f"🌍 总计: {total_facilities} 个健康设施")
    
    # 按设施数量排序
    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1]['total'], reverse=True)
    
    print("\n📊 各国健康设施数量排名 (前15名):")
    print("-" * 40)
    for i, (country, stats) in enumerate(sorted_countries[:15], 1):
        print(f"{i:2d}. {country:25s}: {stats['total']:4d} 个")
    
    # 设施类型统计
    print(f"\n🏥 健康设施类型分布:")
    print("-" * 30)
    for facility_type, count in facility_types.most_common():
        percentage = (count / total_facilities) * 100
        print(f"  {facility_type:10s}: {count:5d} 个 ({percentage:5.1f}%)")
    
    # 保存统计结果
    stats_data = {
        'summary': {
            'total_countries': len(country_stats),
            'total_facilities': total_facilities,
            'facility_types': dict(facility_types)
        },
        'country_details': country_stats
    }
    
    with open('healthsites_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 统计结果已保存到: healthsites_statistics.json")
    
    # 创建CSV格式的详细统计
    csv_data = []
    for country, stats in country_stats.items():
        row = {'country': country, 'total': stats['total']}
        for facility_type, count in stats['types'].items():
            row[facility_type] = count
        csv_data.append(row)
    
    df = pd.DataFrame(csv_data)
    df = df.fillna(0)
    df = df.sort_values('total', ascending=False)
    
    csv_file = 'healthsites_country_stats.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"📊 详细统计已保存到: {csv_file}")
    
    return stats_data

if __name__ == "__main__":
    print("🔍 开始分析非洲健康设施数据...")
    print("=" * 60)
    
    try:
        stats = analyze_healthsites_data()
        print("\n✅ 数据分析完成!")
        
    except Exception as e:
        print(f"\n❌ 分析过程中出错: {e}")
        import traceback
        traceback.print_exc()
