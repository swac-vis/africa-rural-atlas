#!/usr/bin/env python3
"""
Country-wise GHSL Population Analysis
分析GHSL人口数据，按国家分类处理城乡人口分布
正值代表城市人口，负值代表农村人口
"""

import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
import os
import json
from rasterio.mask import mask
from shapely.geometry import box
from shapely.ops import unary_union
import warnings
warnings.filterwarnings('ignore')

class CountryPopulationAnalyzer:
    def __init__(self, population_tif_path, country_boundaries_dir):
        """
        初始化分析器
        
        Args:
            population_tif_path: GHSL人口密度TIF文件路径
            country_boundaries_dir: 国家边界文件目录
        """
        self.population_tif_path = population_tif_path
        self.country_boundaries_dir = country_boundaries_dir
        self.results = {}
        self.ghsl_info = {}
        self.total_population_stats = {}
        
    def load_ghsl_info(self):
        """加载GHSL数据信息"""
        print("Loading GHSL data information...")
        with rasterio.open(self.population_tif_path) as src:
            self.ghsl_info = {
                'crs': src.crs,
                'bounds': src.bounds,
                'transform': src.transform,
                'shape': src.shape,
                'pixel_size_x': src.transform[0],
                'pixel_size_y': abs(src.transform[4])
            }
            
            # 创建GHSL数据范围的多边形
            ghsl_polygon = box(src.bounds[0], src.bounds[1], src.bounds[2], src.bounds[3])
            self.ghsl_info['area_km2'] = ghsl_polygon.area / 1e6  # 转换为平方公里
            self.ghsl_info['polygon'] = ghsl_polygon
            
            print(f"  GHSL数据信息:")
            print(f"    CRS: {src.crs}")
            print(f"    边界: {src.bounds}")
            print(f"    像素大小: {src.transform[0]:.0f} x {abs(src.transform[4]):.0f} 米")
            print(f"    总面积: {self.ghsl_info['area_km2']:,.0f} 平方公里")
        
    def load_country_boundaries(self):
        """加载所有国家边界数据"""
        print("Loading country boundaries...")
        country_files = [f for f in os.listdir(self.country_boundaries_dir) 
                        if f.endswith('.gpkg') and not f.startswith('.')]
        
        countries = {}
        for country_file in country_files:
            country_name = country_file.replace('.gpkg', '')
            if country_name == 'NULL':  # 跳过NULL文件
                continue
                
            try:
                country_path = os.path.join(self.country_boundaries_dir, country_file)
                gdf = gpd.read_file(country_path)
                countries[country_name] = gdf
                print(f"  ✓ Loaded {country_name}")
            except Exception as e:
                print(f"  ✗ Failed to load {country_name}: {e}")
                
        return countries
    
    def analyze_country_population(self, country_name, country_gdf):
        """分析单个国家的人口数据"""
        print(f"Analyzing {country_name}...")
        
        try:
            # 确保坐标系一致
            target_crs = self.ghsl_info['crs']
            
            # 转换国家边界到栅格坐标系
            country_gdf = country_gdf.to_crs(target_crs)
            
            # 计算国家面积和重叠验证
            country_geom = country_gdf.geometry.iloc[0] if len(country_gdf) > 0 else None
            if country_geom is None:
                print(f"  ✗ No valid geometry for {country_name}")
                return None
                
            country_area_km2 = country_geom.area / 1e6
            ghsl_polygon = self.ghsl_info['polygon']
            
            # 检查重叠情况
            if ghsl_polygon.intersects(country_geom):
                overlap_geom = ghsl_polygon.intersection(country_geom)
                overlap_area_km2 = overlap_geom.area / 1e6
                overlap_ratio = overlap_area_km2 / country_area_km2 * 100
                
                print(f"  Area: {country_area_km2:,.0f} km², Overlap: {overlap_ratio:.1f}%")
                
                if overlap_ratio < 50:
                    print(f"  ⚠️  Low overlap ratio, potential boundary issue")
                elif overlap_ratio < 90:
                    print(f"  ⚠️  Moderate overlap ratio")
                else:
                    print(f"  ✓ Good boundary alignment")
            else:
                print(f"  ✗ No overlap with GHSL data")
                return None
            
            # 使用mask提取国家范围内的人口数据
            with rasterio.open(self.population_tif_path) as src:
                try:
                    # 创建mask
                    country_geom = country_gdf.geometry.values[0] if len(country_gdf) > 0 else None
                    if country_geom is None:
                        print(f"  ✗ No valid geometry for {country_name}")
                        return None
                    
                    # 应用mask
                    masked_data, transform = mask(src, [country_geom], crop=True, nodata=np.nan)
                    population_data = masked_data[0]  # 获取第一个波段
                    
                except Exception as e:
                    print(f"  ✗ Masking failed for {country_name}: {e}")
                    return None
            
            # 分析人口数据
            valid_mask = ~np.isnan(population_data)
            valid_population = population_data[valid_mask]
            
            if len(valid_population) == 0:
                print(f"  ✗ No valid population data for {country_name}")
                return None
            
            # 分类：正值=城市，负值=农村
            urban_mask = valid_population > 0
            rural_mask = valid_population < 0
            
            urban_population = valid_population[urban_mask]
            rural_population = valid_population[rural_mask]
            
            # 使用绝对值进行计算
            urban_abs = np.abs(urban_population)
            rural_abs = np.abs(rural_population)
            
            # 计算统计信息
            urban_sum = float(np.sum(urban_abs))
            rural_sum = float(np.sum(rural_abs))
            total_sum = urban_sum + rural_sum
            
            stats = {
                'country': country_name,
                'area_km2': float(country_area_km2),
                'overlap_ratio': float(overlap_ratio),
                'total_cells': len(valid_population),
                'urban_cells': len(urban_population),
                'rural_cells': len(rural_population),
                'urban': urban_sum,
                'rural': rural_sum,
                'total': total_sum,
                'urban_population_mean': float(np.mean(urban_abs)) if len(urban_abs) > 0 else 0,
                'rural_population_mean': float(np.mean(rural_abs)) if len(rural_abs) > 0 else 0,
                'urban_share': float(urban_sum / total_sum) if total_sum > 0 else 0,
                'rural_share': float(rural_sum / total_sum) if total_sum > 0 else 0,
                'urban_density_stats': {
                    'min': float(np.min(urban_abs)) if len(urban_abs) > 0 else 0,
                    'max': float(np.max(urban_abs)) if len(urban_abs) > 0 else 0,
                    'std': float(np.std(urban_abs)) if len(urban_abs) > 0 else 0
                },
                'rural_density_stats': {
                    'min': float(np.min(rural_abs)) if len(rural_abs) > 0 else 0,
                    'max': float(np.max(rural_abs)) if len(rural_abs) > 0 else 0,
                    'std': float(np.std(rural_abs)) if len(rural_abs) > 0 else 0
                }
            }
            
            print(f"  ✓ {country_name}: Urban {stats['urban_cells']} cells, Rural {stats['rural_cells']} cells")
            print(f"    Urban: {stats['urban']:.0f} people ({stats['urban_share']:.1%})")
            print(f"    Rural: {stats['rural']:.0f} people ({stats['rural_share']:.1%})")
            print(f"    Total: {stats['total']:.0f} people")
            
            return stats
            
        except Exception as e:
            print(f"  ✗ Error analyzing {country_name}: {e}")
            return None
    
    def run_analysis(self):
        """运行完整分析"""
        print("="*60)
        print("Country-wise GHSL Population Analysis")
        print("="*60)
        
        # 加载GHSL数据信息
        self.load_ghsl_info()
        
        # 加载国家边界
        countries = self.load_country_boundaries()
        if not countries:
            print("No country boundaries loaded!")
            return None
        
        print(f"\nAnalyzing {len(countries)} countries...")
        
        # 分析每个国家
        all_results = []
        for country_name, country_gdf in countries.items():
            result = self.analyze_country_population(country_name, country_gdf)
            if result:
                all_results.append(result)
                self.results[country_name] = result
        
        # 计算总人口统计
        self.calculate_total_population_stats(all_results)
        
        print(f"\nAnalysis completed for {len(all_results)} countries")
        return all_results
    
    def calculate_total_population_stats(self, results):
        """计算总人口统计信息"""
        print("\n" + "="*60)
        print("TOTAL POPULATION STATISTICS")
        print("="*60)
        
        if not results:
            print("No results to calculate statistics")
            return
        
        # 计算总体统计
        total_urban = sum(r['urban'] for r in results)
        total_rural = sum(r['rural'] for r in results)
        total_population = sum(r['total'] for r in results)
        total_area = sum(r['area_km2'] for r in results)
        
        # 计算平均密度
        avg_urban_density = total_urban / total_area if total_area > 0 else 0
        avg_rural_density = total_rural / total_area if total_area > 0 else 0
        avg_total_density = total_population / total_area if total_area > 0 else 0
        
        # 计算城市化率
        urbanization_rate = total_urban / total_population if total_population > 0 else 0
        
        # 计算GHSL覆盖率
        ghsl_coverage = total_area / self.ghsl_info['area_km2'] if self.ghsl_info['area_km2'] > 0 else 0
        
        self.total_population_stats = {
            'total_countries': len(results),
            'total_population': total_population,
            'total_urban_population': total_urban,
            'total_rural_population': total_rural,
            'total_area_km2': total_area,
            'ghsl_area_km2': self.ghsl_info['area_km2'],
            'ghsl_coverage_ratio': ghsl_coverage,
            'urbanization_rate': urbanization_rate,
            'avg_urban_density': avg_urban_density,
            'avg_rural_density': avg_rural_density,
            'avg_total_density': avg_total_density
        }
        
        # 打印统计结果
        print(f"Total Countries Analyzed: {len(results)}")
        print(f"Total Population: {total_population:,.0f}")
        print(f"  Urban Population: {total_urban:,.0f} ({urbanization_rate:.1%})")
        print(f"  Rural Population: {total_rural:,.0f} ({(1-urbanization_rate):.1%})")
        print(f"Total Area Covered: {total_area:,.0f} km²")
        print(f"GHSL Data Area: {self.ghsl_info['area_km2']:,.0f} km²")
        print(f"GHSL Coverage: {ghsl_coverage:.1%}")
        print(f"Average Population Density: {avg_total_density:.1f} people/km²")
        print(f"  Urban Density: {avg_urban_density:.1f} people/km²")
        print(f"  Rural Density: {avg_rural_density:.1f} people/km²")
        
        # 找出最大和最小的国家
        if results:
            max_pop_country = max(results, key=lambda x: x['total'])
            min_pop_country = min(results, key=lambda x: x['total'])
            max_urban_country = max(results, key=lambda x: x['urban_share'])
            min_urban_country = min(results, key=lambda x: x['urban_share'])
            
            print(f"\nCountry Extremes:")
            print(f"  Largest Population: {max_pop_country['country']} ({max_pop_country['total']:,.0f})")
            print(f"  Smallest Population: {min_pop_country['country']} ({min_pop_country['total']:,.0f})")
            print(f"  Highest Urbanization: {max_urban_country['country']} ({max_urban_country['urban_share']:.1%})")
            print(f"  Lowest Urbanization: {min_urban_country['country']} ({min_urban_country['urban_share']:.1%})")
    
    def save_results(self, results, output_dir):
        """保存分析结果"""
        print(f"\nSaving results to {output_dir}...")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存汇总数据
        summary_df = pd.DataFrame(results)
        summary_file = os.path.join(output_dir, 'country_population_summary.csv')
        summary_df.to_csv(summary_file, index=False)
        print(f"  ✓ Summary saved: {summary_file}")
        
        # 创建合并的JSON文件，包含所有国家数据
        all_countries_data = {
            'metadata': {
                'total_countries': len(results),
                'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': 'GHSL Population Data',
                'coordinate_system': 'ESRI:54009 (World Mollweide)',
                'classification_rule': 'Positive values = Urban, Negative values = Rural',
                'calculation_method': 'All calculations use absolute values'
            },
            'countries': self.results
        }
        
        all_countries_file = os.path.join(output_dir, 'all_countries_population_data.json')
        with open(all_countries_file, 'w', encoding='utf-8') as f:
            json.dump(all_countries_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ All countries data saved: {all_countries_file}")
        
        # 生成统计报告
        self.generate_report(results, output_dir)
        
        # 删除中间文件
        self.cleanup_intermediate_files(output_dir)
        
        return True
    
    def cleanup_intermediate_files(self, output_dir):
        """删除中间文件"""
        print(f"\nCleaning up intermediate files...")
        
        # 删除各个国家的单独JSON文件
        deleted_count = 0
        for country_name in self.results.keys():
            country_file = os.path.join(output_dir, f'{country_name}_population.json')
            if os.path.exists(country_file):
                os.remove(country_file)
                deleted_count += 1
        
        print(f"  ✓ Deleted {deleted_count} individual country files")
        print(f"  ✓ Kept consolidated files: all_countries_population_data.json, country_population_summary.csv, analysis_report.txt")
    
    def generate_report(self, results, output_dir):
        """生成分析报告"""
        report_file = os.path.join(output_dir, 'analysis_report.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("GHSL Population Analysis Report\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Countries Analyzed: {len(results)}\n\n")
            
            # 总体统计
            total_urban = sum(r['urban'] for r in results)
            total_rural = sum(r['rural'] for r in results)
            total_population = sum(r['total'] for r in results)
            total_area = sum(r['area_km2'] for r in results)
            
            f.write("Overall Statistics:\n")
            f.write(f"  Total Population: {total_population:,.0f}\n")
            f.write(f"  Urban Population: {total_urban:,.0f} ({total_urban/total_population:.1%})\n")
            f.write(f"  Rural Population: {total_rural:,.0f} ({total_rural/total_population:.1%})\n")
            f.write(f"  Total Area Covered: {total_area:,.0f} km²\n")
            f.write(f"  GHSL Data Area: {self.ghsl_info['area_km2']:,.0f} km²\n")
            f.write(f"  GHSL Coverage: {(total_area/self.ghsl_info['area_km2']):.1%}\n")
            f.write(f"  Average Population Density: {total_population/total_area:.1f} people/km²\n\n")
            
            # 按国家排序
            sorted_results = sorted(results, key=lambda x: x['total'], reverse=True)
            
            f.write("Top 10 Countries by Total Population:\n")
            for i, result in enumerate(sorted_results[:10], 1):
                f.write(f"  {i:2d}. {result['country']:<25} {result['total']:>12,.0f}\n")
            
            f.write("\nUrban-Rural Distribution by Country:\n")
            f.write(f"{'Country':<25} {'Urban':<12} {'Rural':<12} {'Urban%':<8} {'Rural%':<8}\n")
            f.write("-" * 70 + "\n")
            
            for result in sorted_results:
                f.write(f"{result['country']:<25} {result['urban']:>11,.0f} "
                       f"{result['rural']:>11,.0f} {result['urban_share']:>7.1%} "
                       f"{result['rural_share']:>7.1%}\n")
        
        print(f"  ✓ Analysis report saved: {report_file}")

def main():
    """主函数"""
    # 文件路径
    population_tif = "../map_real/ghslpop_africa.tif"
    country_boundaries_dir = "../data_original/country"
    output_dir = "results"
    
    # 检查文件是否存在
    if not os.path.exists(population_tif):
        print(f"错误: 人口密度文件不存在: {population_tif}")
        return
        
    if not os.path.exists(country_boundaries_dir):
        print(f"错误: 国家边界目录不存在: {country_boundaries_dir}")
        return
    
    # 创建分析器并运行分析
    analyzer = CountryPopulationAnalyzer(population_tif, country_boundaries_dir)
    results = analyzer.run_analysis()
    
    if results:
        # 保存结果
        analyzer.save_results(results, output_dir)
        
        # 打印汇总信息
        print("\n" + "="*60)
        print("ANALYSIS SUMMARY")
        print("="*60)
        
        total_urban = sum(r['urban'] for r in results)
        total_rural = sum(r['rural'] for r in results)
        total_population = sum(r['total'] for r in results)
        
        print(f"Total Countries: {len(results)}")
        print(f"Total Population: {total_population:,.0f}")
        print(f"Urban Population: {total_urban:,.0f} ({total_urban/total_population:.1%})")
        print(f"Rural Population: {total_rural:,.0f} ({total_rural/total_population:.1%})")
        
        print(f"\nResults saved to: {output_dir}/")
    else:
        print("分析失败，没有生成结果")

if __name__ == "__main__":
    main()
