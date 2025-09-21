#!/usr/bin/env python3
"""
Facility Urban-Rural Distribution Analysis
统计非洲健康设施在城市和农村的分布情况

分析基于GHSL人口密度数据：
- 城市区域：人口密度 > 0
- 农村区域：人口密度 <= 0
"""

import json
import numpy as np
from shapely.geometry import Point
import rasterio
from rasterio.warp import transform_bounds
import geopandas as gpd
import pandas as pd
from collections import defaultdict
import os

class FacilityUrbanRuralAnalyzer:
    def __init__(self, population_tif_path, healthsites_geojson_path):
        """
        初始化分析器
        
        Args:
            population_tif_path: GHSL人口密度GeoTIFF文件路径
            healthsites_geojson_path: 健康设施GeoJSON文件路径
        """
        self.population_tif_path = population_tif_path
        self.healthsites_geojson_path = healthsites_geojson_path
        self.population_data = None
        self.healthsites_gdf = None
        self.results = {}
        
    def load_population_data(self):
        """加载人口密度数据"""
        try:
            with rasterio.open(self.population_tif_path) as src:
                self.population_data = src.read(1)  # 读取第一个波段
                self.transform = src.transform
                self.crs = src.crs
                self.bounds = src.bounds
                print(f"人口数据加载成功: {self.population_data.shape}")
                print(f"投影系统: {self.crs}")
                print(f"边界: {self.bounds}")
        except Exception as e:
            print(f"加载人口数据失败: {e}")
            return False
        return True
    
    def load_healthsites_data(self):
        """加载健康设施数据"""
        try:
            self.healthsites_gdf = gpd.read_file(self.healthsites_geojson_path)
            print(f"健康设施数据加载成功: {len(self.healthsites_gdf)} 个设施")
            print(f"列名: {list(self.healthsites_gdf.columns)}")
            
            # 检查是否有坐标列
            if 'geometry' in self.healthsites_gdf.columns:
                print("几何信息加载成功")
            else:
                print("警告: 没有找到几何信息")
                
        except Exception as e:
            print(f"加载健康设施数据失败: {e}")
            return False
        return True
    
    def identify_pharmacies(self):
        """识别药店设施"""
        if self.healthsites_gdf is None:
            return False
            
        # 尝试不同的列名来识别药店
        pharmacy_columns = ['amenity', 'healthcare', 'type', 'properties']
        
        for col in pharmacy_columns:
            if col in self.healthsites_gdf.columns:
                print(f"找到列: {col}")
                if col == 'properties':
                    # 如果properties是JSON字符串，需要解析
                    try:
                        # 检查properties列的内容
                        sample_props = self.healthsites_gdf[col].iloc[0]
                        print(f"Properties列示例: {sample_props}")
                    except:
                        pass
                else:
                    print(f"{col}列的唯一值: {self.healthsites_gdf[col].unique()[:10]}")
        
        # 基于列名和值来识别药店
        pharmacy_mask = None
        
        # 方法1: 直接检查amenity列
        if 'amenity' in self.healthsites_gdf.columns:
            pharmacy_mask = self.healthsites_gdf['amenity'] == 'pharmacy'
            
        # 方法2: 检查healthcare列
        elif 'healthcare' in self.healthsites_gdf.columns:
            pharmacy_mask = self.healthsites_gdf['healthcare'] == 'pharmacy'
            
        # 方法3: 检查type列
        elif 'type' in self.healthsites_gdf.columns:
            pharmacy_mask = self.healthsites_gdf['type'] == 'pharmacy'
            
        # 如果没有找到明确的药店标识，使用所有健康设施
        if pharmacy_mask is None or pharmacy_mask.sum() == 0:
            print("未找到明确的药店标识，使用所有健康设施")
            pharmacy_mask = pd.Series([True] * len(self.healthsites_gdf))
        else:
            print(f"找到 {pharmacy_mask.sum()} 个药店")
            
        self.pharmacies_gdf = self.healthsites_gdf[pharmacy_mask].copy()
        return True
    
    def get_population_at_location(self, lon, lat):
        """获取指定坐标的人口密度值"""
        if self.population_data is None:
            return None
            
        try:
            # 将地理坐标转换为像素坐标
            row, col = ~self.transform * (lon, lat)
            row, col = int(row), int(col)
            
            # 检查边界
            if 0 <= row < self.population_data.shape[0] and 0 <= col < self.population_data.shape[1]:
                return self.population_data[row, col]
            else:
                return None
        except:
            return None
    
    def analyze_facility_distribution(self):
        """分析设施在城市和农村的分布"""
        if self.pharmacies_gdf is None or self.population_data is None:
            print("数据未加载，无法进行分析")
            return False
            
        print("开始分析设施分布...")
        
        urban_facilities = []
        rural_facilities = []
        unknown_facilities = []
        
        total_facilities = len(self.pharmacies_gdf)
        
        for idx, facility in self.pharmacies_gdf.iterrows():
            try:
                # 获取设施坐标
                if hasattr(facility.geometry, 'x') and hasattr(facility.geometry, 'y'):
                    lon, lat = facility.geometry.x, facility.geometry.y
                elif hasattr(facility.geometry, 'coords'):
                    lon, lat = facility.geometry.coords[0]
                else:
                    unknown_facilities.append(facility)
                    continue
                
                # 获取人口密度
                population_density = self.get_population_at_location(lon, lat)
                
                if population_density is not None:
                    facility_info = {
                        'id': idx,
                        'lon': lon,
                        'lat': lat,
                        'population_density': population_density,
                        'type': 'urban' if population_density > 0 else 'rural'
                    }
                    
                    if population_density > 0:
                        urban_facilities.append(facility_info)
                    else:
                        rural_facilities.append(facility_info)
                else:
                    unknown_facilities.append(facility)
                    
            except Exception as e:
                print(f"处理设施 {idx} 时出错: {e}")
                unknown_facilities.append(facility)
        
        # 统计结果
        self.results = {
            'total_facilities': total_facilities,
            'urban_facilities': {
                'count': len(urban_facilities),
                'percentage': (len(urban_facilities) / total_facilities) * 100 if total_facilities > 0 else 0,
                'facilities': urban_facilities
            },
            'rural_facilities': {
                'count': len(rural_facilities),
                'percentage': (len(rural_facilities) / total_facilities) * 100 if total_facilities > 0 else 0,
                'facilities': rural_facilities
            },
            'unknown_facilities': {
                'count': len(unknown_facilities),
                'percentage': (len(unknown_facilities) / total_facilities) * 100 if total_facilities > 0 else 0
            },
            'summary': {
                'urban_rural_ratio': len(urban_facilities) / len(rural_facilities) if len(rural_facilities) > 0 else float('inf'),
                'urban_dominance': len(urban_facilities) > len(rural_facilities)
            }
        }
        
        return True
    
    def generate_detailed_analysis(self):
        """生成详细分析报告"""
        if not self.results:
            print("没有分析结果")
            return
            
        print("\n" + "="*50)
        print("设施城市-农村分布分析报告")
        print("="*50)
        
        print(f"\n总设施数量: {self.results['total_facilities']:,}")
        print(f"城市设施: {self.results['urban_facilities']['count']:,} ({self.results['urban_facilities']['percentage']:.1f}%)")
        print(f"农村设施: {self.results['rural_facilities']['count']:,} ({self.results['rural_facilities']['percentage']:.1f}%)")
        print(f"未知位置: {self.results['unknown_facilities']['count']:,} ({self.results['unknown_facilities']['percentage']:.1f}%)")
        
        print(f"\n城市/农村比例: {self.results['summary']['urban_rural_ratio']:.2f}")
        print(f"城市设施占优: {'是' if self.results['summary']['urban_dominance'] else '否'}")
        
        # 人口密度统计
        if self.results['urban_facilities']['facilities']:
            urban_densities = [f['population_density'] for f in self.results['urban_facilities']['facilities']]
            print(f"\n城市设施人口密度统计:")
            print(f"  平均值: {np.mean(urban_densities):.2f}")
            print(f"  中位数: {np.median(urban_densities):.2f}")
            print(f"  最大值: {np.max(urban_densities):.2f}")
            print(f"  最小值: {np.min(urban_densities):.2f}")
        
        if self.results['rural_facilities']['facilities']:
            rural_densities = [abs(f['population_density']) for f in self.results['rural_facilities']['facilities']]
            print(f"\n农村设施人口密度统计 (绝对值):")
            print(f"  平均值: {np.mean(rural_densities):.2f}")
            print(f"  中位数: {np.median(rural_densities):.2f}")
            print(f"  最大值: {np.max(rural_densities):.2f}")
            print(f"  最小值: {np.min(rural_densities):.2f}")
    
    def save_results(self, output_path):
        """保存分析结果到JSON文件"""
        if not self.results:
            print("没有结果可保存")
            return False
            
        try:
            # 准备保存的数据（移除numpy类型）
            save_data = {
                'total_facilities': self.results['total_facilities'],
                'urban_facilities': {
                    'count': self.results['urban_facilities']['count'],
                    'percentage': float(self.results['urban_facilities']['percentage']),
                    'facilities': [
                        {
                            'id': int(f['id']),
                            'lon': float(f['lon']),
                            'lat': float(f['lat']),
                            'population_density': float(f['population_density']),
                            'type': f['type']
                        }
                        for f in self.results['urban_facilities']['facilities']
                    ]
                },
                'rural_facilities': {
                    'count': self.results['rural_facilities']['count'],
                    'percentage': float(self.results['rural_facilities']['percentage']),
                    'facilities': [
                        {
                            'id': int(f['id']),
                            'lon': float(f['lon']),
                            'lat': float(f['lat']),
                            'population_density': float(f['population_density']),
                            'type': f['type']
                        }
                        for f in self.results['rural_facilities']['facilities']
                    ]
                },
                'unknown_facilities': {
                    'count': self.results['unknown_facilities']['count'],
                    'percentage': float(self.results['unknown_facilities']['percentage'])
                },
                'summary': {
                    'urban_rural_ratio': float(self.results['summary']['urban_rural_ratio']) if self.results['summary']['urban_rural_ratio'] != float('inf') else None,
                    'urban_dominance': self.results['summary']['urban_dominance']
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            print(f"\n结果已保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"保存结果失败: {e}")
            return False
    
    def run_analysis(self):
        """运行完整分析流程"""
        print("开始设施城市-农村分布分析...")
        
        # 1. 加载数据
        if not self.load_population_data():
            return False
            
        if not self.load_healthsites_data():
            return False
            
        # 2. 识别药店
        if not self.identify_pharmacies():
            return False
            
        # 3. 分析分布
        if not self.analyze_facility_distribution():
            return False
            
        # 4. 生成报告
        self.generate_detailed_analysis()
        
        # 5. 保存结果
        output_path = '../data/facility_urban_rural_distribution.json'
        self.save_results(output_path)
        
        return True

def main():
    """主函数"""
    # 文件路径
    population_tif = '../../map_real/ghslpop_africa.tif'
    healthsites_geojson = '../data/Africa_all_healthsites.geojson'
    
    # 检查文件是否存在
    if not os.path.exists(population_tif):
        print(f"错误: 人口密度文件不存在: {population_tif}")
        return
        
    if not os.path.exists(healthsites_geojson):
        print(f"错误: 健康设施文件不存在: {healthsites_geojson}")
        return
    
    # 创建分析器并运行分析
    analyzer = FacilityUrbanRuralAnalyzer(population_tif, healthsites_geojson)
    
    if analyzer.run_analysis():
        print("\n分析完成！")
    else:
        print("\n分析失败！")

if __name__ == "__main__":
    main()
