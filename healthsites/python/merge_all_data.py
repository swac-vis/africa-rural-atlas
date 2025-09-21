#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并所有非洲国家健康设施数据到一个统一文件
将所有GeoJSON文件合并为Africa_all_healthsites.geojson
"""

import json
import os
import glob
from pathlib import Path

def merge_all_healthsites_data():
    """合并所有健康设施数据"""
    
    print("🔗 开始合并所有非洲国家健康设施数据...")
    print("=" * 60)
    
    # 获取所有GeoJSON文件
    geojson_dir = "../data/africa_geojson"
    geojson_files = glob.glob(os.path.join(geojson_dir, "*.geojson"))
    
    if not geojson_files:
        print("❌ 未找到GeoJSON文件，请先运行下载脚本")
        return
    
    print(f"📁 找到 {len(geojson_files)} 个国家的数据文件")
    print("=" * 60)
    
    # 合并数据
    all_features = []
    country_stats = {}
    total_facilities = 0
    
    for file_path in geojson_files:
        country_name = os.path.basename(file_path).replace('.geojson', '')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get('features', [])
            facility_count = len(features)
            
            if facility_count > 0:
                # 为每个设施添加国家信息（如果还没有的话）
                for feature in features:
                    properties = feature.get('properties', {})
                    
                    # 确保有country字段
                    if 'country' not in properties:
                        properties['country'] = country_name
                    
                    # 添加数据源信息
                    properties['data_source'] = f"healthsites.io - {country_name}"
                    
                    # 添加文件来源信息
                    properties['source_file'] = os.path.basename(file_path)
                
                all_features.extend(features)
                country_stats[country_name] = facility_count
                total_facilities += facility_count
                
                print(f"✅ {country_name}: {facility_count} 个设施")
            else:
                print(f"⚠️ {country_name}: 0 个设施（跳过）")
                
        except Exception as e:
            print(f"❌ 处理 {country_name} 时出错: {e}")
    
    if not all_features:
        print("❌ 没有成功读取任何数据")
        return
    
    # 创建合并后的GeoJSON结构
    merged_geojson = {
        "type": "FeatureCollection",
        "name": "Africa All Healthsites",
        "description": f"Combined health facilities data from {len(country_stats)} African countries",
        "metadata": {
            "total_countries": len(country_stats),
            "total_facilities": total_facilities,
            "data_source": "healthsites.io",
            "merge_date": str(Path().cwd().name),
            "country_breakdown": country_stats
        },
        "features": all_features
    }
    
    # 保存合并后的文件
    output_file = "Africa_all_healthsites.geojson"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_geojson, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"🎉 数据合并完成！")
    print(f"📊 统计信息:")
    print(f"  - 国家数量: {len(country_stats)}")
    print(f"  - 总设施数: {total_facilities}")
    print(f"  - 输出文件: {output_file}")
    
    # 显示各国设施数量统计
    print(f"\n📈 各国健康设施数量:")
    print("-" * 40)
    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1], reverse=True)
    
    for i, (country, count) in enumerate(sorted_countries, 1):
        print(f"{i:2d}. {country:25s}: {count:4d} 个")
    
    # 保存统计信息
    stats_file = "Africa_merged_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_countries": len(country_stats),
                "total_facilities": total_facilities,
                "output_file": output_file
            },
            "country_details": country_stats,
            "merge_metadata": merged_geojson["metadata"]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 统计信息已保存到: {stats_file}")
    
    # 文件大小信息
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    print(f"📁 输出文件大小: {file_size:.2f} MB")
    
    return merged_geojson

def create_summary_report():
    """创建汇总报告"""
    print(f"\n📋 创建汇总报告...")
    
    report_file = "Africa_healthsites_summary.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("非洲健康设施数据汇总报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"生成时间: {Path().cwd().name}\n")
        f.write(f"数据来源: healthsites.io\n\n")
        
        # 读取统计信息
        try:
            with open("Africa_merged_statistics.json", 'r', encoding='utf-8') as stats_f:
                stats = json.load(stats_f)
            
            f.write(f"总体统计:\n")
            f.write(f"  - 覆盖国家: {stats['summary']['total_countries']} 个\n")
            f.write(f"  - 总设施数: {stats['summary']['total_facilities']} 个\n")
            f.write(f"  - 输出文件: {stats['summary']['output_file']}\n\n")
            
            f.write("各国设施数量排名:\n")
            f.write("-" * 30 + "\n")
            
            sorted_countries = sorted(stats['country_details'].items(), key=lambda x: x[1], reverse=True)
            for i, (country, count) in enumerate(sorted_countries, 1):
                f.write(f"{i:2d}. {country:25s}: {count:4d} 个\n")
                
        except Exception as e:
            f.write(f"读取统计信息时出错: {e}\n")
    
    print(f"📄 汇总报告已保存到: {report_file}")

if __name__ == "__main__":
    print("🌍 非洲健康设施数据合并工具")
    print("=" * 60)
    
    try:
        # 合并数据
        merged_data = merge_all_healthsites_data()
        
        if merged_data:
            # 创建汇总报告
            create_summary_report()
            
            print(f"\n✅ 所有操作完成！")
            print(f"🎯 你现在有了一个包含所有非洲国家健康设施的完整文件")
            
        else:
            print(f"\n❌ 数据合并失败")
            
    except Exception as e:
        print(f"\n❌ 处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
