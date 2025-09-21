#!/usr/bin/env python3
"""
Population Analysis Visualization Script
生成各种图表来展示人口分析结果
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from pathlib import Path

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")

class PopulationVisualizer:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
    def load_data(self):
        """加载分析结果数据"""
        json_file = self.results_dir / 'all_countries_population_data.json'
        
        if not json_file.exists():
            raise FileNotFoundError(f"Results file not found: {json_file}")
            
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.countries_data = data['countries']
        self.metadata = data['metadata']
        
        # 转换为DataFrame便于处理
        self.df = pd.DataFrame.from_dict(self.countries_data, orient='index')
        
        print(f"Loaded data for {len(self.df)} countries")
        return self.df
    
    def create_urban_rural_distribution(self):
        """创建城乡分布图"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 城乡人口分布饼图
        total_urban = self.df['urban'].sum()
        total_rural = self.df['rural'].sum()
        
        ax1.pie([total_urban, total_rural], 
                labels=['Urban', 'Rural'],
                autopct='%1.1f%%',
                colors=['#3498db', '#e67e22'],
                startangle=90)
        ax1.set_title('Total Population Distribution', fontsize=14, fontweight='bold')
        
        # 城市化率分布直方图
        ax2.hist(self.df['urban_share'] * 100, bins=20, alpha=0.7, color='#3498db', edgecolor='black')
        ax2.set_xlabel('Urbanization Rate (%)')
        ax2.set_ylabel('Number of Countries')
        ax2.set_title('Urbanization Rate Distribution', fontsize=14, fontweight='bold')
        ax2.axvline(self.df['urban_share'].mean() * 100, color='red', linestyle='--', 
                   label=f'Mean: {self.df["urban_share"].mean()*100:.1f}%')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'urban_rural_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Urban-rural distribution chart saved")
    
    def create_population_density_distribution(self):
        """创建人口密度分布图"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 总人口密度分布
        total_density = self.df['total'] / self.df['area_km2']
        ax1.hist(total_density, bins=20, alpha=0.7, color='#2ecc71', edgecolor='black')
        ax1.set_xlabel('Population Density (people/km²)')
        ax1.set_ylabel('Number of Countries')
        ax1.set_title('Total Population Density Distribution', fontsize=14, fontweight='bold')
        ax1.set_yscale('log')
        
        # 城市人口密度 vs 农村人口密度
        urban_density = self.df['urban'] / self.df['area_km2']
        rural_density = self.df['rural'] / self.df['area_km2']
        
        ax2.scatter(urban_density, rural_density, alpha=0.7, s=60)
        ax2.set_xlabel('Urban Density (people/km²)')
        ax2.set_ylabel('Rural Density (people/km²)')
        ax2.set_title('Urban vs Rural Density', fontsize=14, fontweight='bold')
        ax2.set_xscale('log')
        ax2.set_yscale('log')
        
        # 添加对角线
        max_val = max(ax2.get_xlim()[1], ax2.get_ylim()[1])
        ax2.plot([1, max_val], [1, max_val], 'r--', alpha=0.5, label='Equal density line')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'population_density_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Population density distribution chart saved")
    
    def create_urbanization_scatter(self):
        """创建城市化散点图"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 按总人口大小设置点的大小
        scatter = ax.scatter(self.df['area_km2'], 
                           self.df['urban_share'] * 100,
                           s=self.df['total'] / 1000000,  # 按百万人口缩放
                           alpha=0.6,
                           c=self.df['total'],
                           cmap='viridis',
                           edgecolors='black',
                           linewidth=0.5)
        
        ax.set_xlabel('Area (km²)', fontsize=12)
        ax.set_ylabel('Urbanization Rate (%)', fontsize=12)
        ax.set_title('Urbanization Rate vs Area by Country\n(Bubble size = Total Population)', 
                    fontsize=14, fontweight='bold')
        ax.set_xscale('log')
        
        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Total Population', fontsize=12)
        
        # 标注几个重要国家
        important_countries = ['Nigeria', 'Egypt', 'Ethiopia', 'South Africa', 'Kenya']
        for country in important_countries:
            if country in self.df.index:
                row = self.df.loc[country]
                ax.annotate(country, 
                           (row['area_km2'], row['urban_share'] * 100),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=9, alpha=0.8)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'urbanization_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Urbanization scatter plot saved")
    
    def create_summary_statistics(self):
        """创建汇总统计图"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 前10个国家总人口
        top10 = self.df.nlargest(10, 'total')
        bars1 = ax1.barh(range(len(top10)), top10['total'] / 1e6, color='#3498db')
        ax1.set_yticks(range(len(top10)))
        ax1.set_yticklabels(top10['country'], fontsize=10)
        ax1.set_xlabel('Total Population (Millions)')
        ax1.set_title('Top 10 Countries by Total Population', fontweight='bold')
        
        # 添加数值标签
        for i, bar in enumerate(bars1):
            width = bar.get_width()
            ax1.text(width + 1, bar.get_y() + bar.get_height()/2, 
                    f'{width:.1f}M', ha='left', va='center', fontsize=9)
        
        # 城市化率最高的10个国家
        top_urban = self.df.nlargest(10, 'urban_share')
        bars2 = ax2.barh(range(len(top_urban)), top_urban['urban_share'] * 100, color='#e67e22')
        ax2.set_yticks(range(len(top_urban)))
        ax2.set_yticklabels(top_urban['country'], fontsize=10)
        ax2.set_xlabel('Urbanization Rate (%)')
        ax2.set_title('Top 10 Countries by Urbanization Rate', fontweight='bold')
        
        # 添加数值标签
        for i, bar in enumerate(bars2):
            width = bar.get_width()
            ax2.text(width + 1, bar.get_y() + bar.get_height()/2, 
                    f'{width:.1f}%', ha='left', va='center', fontsize=9)
        
        # 面积 vs 人口密度散点图
        density = self.df['total'] / self.df['area_km2']
        ax3.scatter(self.df['area_km2'], density, alpha=0.7, s=60, color='#2ecc71')
        ax3.set_xlabel('Area (km²)')
        ax3.set_ylabel('Population Density (people/km²)')
        ax3.set_title('Area vs Population Density', fontweight='bold')
        ax3.set_xscale('log')
        ax3.set_yscale('log')
        
        # 城乡人口比例箱线图
        urban_rates = self.df['urban_share'] * 100
        rural_rates = self.df['rural_share'] * 100
        
        box_data = [urban_rates, rural_rates]
        box_labels = ['Urban Rate (%)', 'Rural Rate (%)']
        
        bp = ax4.boxplot(box_data, labels=box_labels, patch_artist=True)
        bp['boxes'][0].set_facecolor('#3498db')
        bp['boxes'][1].set_facecolor('#e67e22')
        
        ax4.set_title('Urban vs Rural Rate Distribution', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'summary_statistics.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Summary statistics chart saved")
    
    def generate_visualization_summary(self):
        """生成可视化总结报告"""
        summary_file = self.results_dir / 'visualization_summary.txt'
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("Population Analysis Visualization Summary\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Analysis Date: {self.metadata['analysis_date']}\n")
            f.write(f"Total Countries: {len(self.df)}\n")
            f.write(f"Data Source: {self.metadata['data_source']}\n")
            f.write(f"Coordinate System: {self.metadata['coordinate_system']}\n\n")
            
            f.write("Generated Visualizations:\n")
            f.write("-" * 30 + "\n")
            f.write("1. urban_rural_distribution.png - Urban vs rural population distribution\n")
            f.write("2. population_density_distribution.png - Population density analysis\n")
            f.write("3. urbanization_scatter.png - Urbanization rate vs area scatter plot\n")
            f.write("4. summary_statistics.png - Comprehensive statistical overview\n\n")
            
            f.write("Key Statistics:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Population: {self.df['total'].sum():,.0f}\n")
            f.write(f"Urban Population: {self.df['urban'].sum():,.0f} ({self.df['urban'].sum()/self.df['total'].sum()*100:.1f}%)\n")
            f.write(f"Rural Population: {self.df['rural'].sum():,.0f} ({self.df['rural'].sum()/self.df['total'].sum()*100:.1f}%)\n")
            f.write(f"Average Urbanization Rate: {self.df['urban_share'].mean()*100:.1f}%\n")
            f.write(f"Average Population Density: {(self.df['total']/self.df['area_km2']).mean():.1f} people/km²\n")
            
            f.write(f"\nTop 5 Countries by Population:\n")
            top5 = self.df.nlargest(5, 'total')
            for i, (country, row) in enumerate(top5.iterrows(), 1):
                f.write(f"{i}. {country}: {row['total']:,.0f}\n")
            
            f.write(f"\nTop 5 Countries by Urbanization Rate:\n")
            top_urban = self.df.nlargest(5, 'urban_share')
            for i, (country, row) in enumerate(top_urban.iterrows(), 1):
                f.write(f"{i}. {country}: {row['urban_share']*100:.1f}%\n")
        
        print(f"✓ Visualization summary saved: {summary_file}")
    
    def run_all_visualizations(self):
        """运行所有可视化"""
        print("Generating population analysis visualizations...")
        
        # 加载数据
        self.load_data()
        
        # 生成各种图表
        self.create_urban_rural_distribution()
        self.create_population_density_distribution()
        self.create_urbanization_scatter()
        self.create_summary_statistics()
        
        # 生成总结报告
        self.generate_visualization_summary()
        
        print("\n" + "="*50)
        print("VISUALIZATION COMPLETE")
        print("="*50)
        print(f"All charts saved to: {self.results_dir}")
        print("Generated files:")
        print("- urban_rural_distribution.png")
        print("- population_density_distribution.png") 
        print("- urbanization_scatter.png")
        print("- summary_statistics.png")
        print("- visualization_summary.txt")

def main():
    """主函数"""
    visualizer = PopulationVisualizer()
    visualizer.run_all_visualizations()

if __name__ == "__main__":
    main()
