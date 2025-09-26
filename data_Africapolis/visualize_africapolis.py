#!/usr/bin/env python3
"""
Africapolis Data Visualization Script
Creates multiple visualizations for rural, urban, and total population data
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_data():
    """Load all three datasets"""
    print("Loading data...")
    rural = pd.read_csv('africa_rural.csv')
    urban = pd.read_csv('africa_urban.csv')
    total = pd.read_csv('africa_total.csv')
    
    print(f"Rural data: {len(rural)} points")
    print(f"Urban data: {len(urban)} points") 
    print(f"Total data: {len(total)} points")
    
    return rural, urban, total

def verify_rural_urban_total(rural, urban, total):
    """Verify that Rural + Urban = Total"""
    print("🔍 Verifying Rural + Urban = Total relationship...")
    
    # Check if total population matches
    rural_total = rural['pop'].sum()
    urban_total = urban['pop'].sum()
    total_pop = total['pop'].sum()
    
    print(f"Rural total: {rural_total:,.0f}")
    print(f"Urban total: {urban_total:,.0f}")
    print(f"Rural + Urban: {rural_total + urban_total:,.0f}")
    print(f"Total: {total_pop:,.0f}")
    print(f"Difference: {abs((rural_total + urban_total) - total_pop):,.0f}")
    
    return abs((rural_total + urban_total) - total_pop) < 1000  # Allow small rounding differences

def create_scatter_plot(rural, urban, total):
    """Create scatter plot showing population vs distance"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Sample data for better visualization (too many points)
    rural_sample = rural.sample(min(5000, len(rural)))
    urban_sample = urban.sample(min(5000, len(urban)))
    
    ax.scatter(rural_sample['distance'], rural_sample['pop'], 
               alpha=0.6, s=20, label=f'Rural (n={len(rural):,})', color='green')
    ax.scatter(urban_sample['distance'], urban_sample['pop'], 
               alpha=0.6, s=20, label=f'Urban (n={len(urban):,})', color='blue')
    
    ax.set_xlabel('Distance from Roads (km)')
    ax.set_ylabel('Population (log scale)')
    ax.set_yscale('log')
    ax.set_title('Population Distribution by Distance from Roads\n(Africapolis Data)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('africapolis_scatter.svg', format='svg', bbox_inches='tight')
    plt.savefig('africapolis_scatter.pdf', format='pdf', bbox_inches='tight')
    plt.show()


def create_distance_bins_analysis(rural, urban, total):
    """Create analysis of population by distance bins"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create distance bins
    bins = np.arange(0, 1200, 50)
    bin_labels = [f'{b}-{b+50}' for b in bins[:-1]]
    
    # Calculate statistics for each bin
    rural_stats = []
    urban_stats = []
    
    for i in range(len(bins)-1):
        rural_bin = rural[(rural['distance'] >= bins[i]) & (rural['distance'] < bins[i+1])]
        urban_bin = urban[(urban['distance'] >= bins[i]) & (urban['distance'] < bins[i+1])]
        
        rural_stats.append({
            'count': len(rural_bin),
            'total_pop': rural_bin['pop'].sum(),
            'mean_pop': rural_bin['pop'].mean() if len(rural_bin) > 0 else 0
        })
        
        urban_stats.append({
            'count': len(urban_bin),
            'total_pop': urban_bin['pop'].sum(),
            'mean_pop': urban_bin['pop'].mean() if len(urban_bin) > 0 else 0
        })
    
    # Plot total population by distance bin
    rural_totals = [s['total_pop'] for s in rural_stats]
    urban_totals = [s['total_pop'] for s in urban_stats]
    
    x = np.arange(len(bin_labels))
    width = 0.35
    
    ax.bar(x - width/2, rural_totals, width, label='Rural', color='green', alpha=0.8)
    ax.bar(x + width/2, urban_totals, width, label='Urban', color='blue', alpha=0.8)
    
    ax.set_xlabel('Distance Range from Roads (km)')
    ax.set_ylabel('Total Population')
    ax.set_title('Total Population by Distance from Roads')
    ax.set_xticks(x)
    ax.set_xticklabels(bin_labels, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('africapolis_distance_bins.svg', format='svg', bbox_inches='tight')
    plt.savefig('africapolis_distance_bins.pdf', format='pdf', bbox_inches='tight')
    plt.show()

def create_summary_statistics(rural, urban, total):
    """Create summary statistics visualization"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Total population comparison
    categories = ['Rural', 'Urban']
    populations = [rural['pop'].sum(), urban['pop'].sum()]
    colors = ['green', 'blue']
    
    bars = ax1.bar(categories, populations, color=colors, alpha=0.8)
    ax1.set_ylabel('Total Population')
    ax1.set_title('Total Population Comparison')
    
    # Add value labels on bars
    for bar, pop in zip(bars, populations):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{pop/1e6:.1f}M', ha='center', va='bottom')
    
    # Data points comparison
    data_points = [len(rural), len(urban)]
    bars = ax2.bar(categories, data_points, color=colors, alpha=0.8)
    ax2.set_ylabel('Number of Data Points')
    ax2.set_title('Data Points Comparison')
    
    for bar, points in zip(bars, data_points):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{points:,}', ha='center', va='bottom')
    
    # Distance range comparison
    distance_ranges = [
        rural['distance'].max() - rural['distance'].min(),
        urban['distance'].max() - urban['distance'].min()
    ]
    
    bars = ax3.bar(categories, distance_ranges, color=colors, alpha=0.8)
    ax3.set_ylabel('Distance Range from Roads (km)')
    ax3.set_title('Distance Range Coverage')
    
    for bar, dist in zip(bars, distance_ranges):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{dist:.1f}', ha='center', va='bottom')
    
    # Average population per data point
    avg_populations = [
        rural['pop'].mean(),
        urban['pop'].mean()
    ]
    
    bars = ax4.bar(categories, avg_populations, color=colors, alpha=0.8)
    ax4.set_ylabel('Average Population per Data Point')
    ax4.set_title('Average Population Density')
    
    for bar, avg_pop in zip(bars, avg_populations):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{avg_pop/1e3:.1f}K', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('africapolis_summary.svg', format='svg', bbox_inches='tight')
    plt.savefig('africapolis_summary.pdf', format='pdf', bbox_inches='tight')
    plt.show()

def create_heatmap(rural, urban, total):
    """Create 2D heatmap of distance vs population"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create 2D histogram
    # Use total data for the heatmap
    H, xedges, yedges = np.histogram2d(
        total['distance'], 
        np.log10(total['pop'] + 1),
        bins=[50, 50]
    )
    
    # Create heatmap
    im = ax.imshow(H.T, origin='lower', aspect='auto', 
                   extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
                   cmap='viridis', interpolation='nearest')
    
    ax.set_xlabel('Distance from Roads (km)')
    ax.set_ylabel('Log10(Population + 1)')
    ax.set_title('Population Density Heatmap\n(Distance from Roads vs Population)')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Number of Data Points')
    
    plt.tight_layout()
    plt.savefig('africapolis_heatmap.svg', format='svg', bbox_inches='tight')
    plt.savefig('africapolis_heatmap.pdf', format='pdf', bbox_inches='tight')
    plt.show()

def main():
    """Main function to create all visualizations"""
    print("🌍 Africapolis Data Visualization")
    print("=" * 50)
    
    # Load data
    rural, urban, total = load_data()
    
    # Verify Rural + Urban = Total
    is_valid = verify_rural_urban_total(rural, urban, total)
    if is_valid:
        print("✅ Rural + Urban = Total relationship verified!")
    else:
        print("⚠️  Warning: Rural + Urban ≠ Total (check data)")
    
    print("\n📊 Creating visualizations...")
    
    # Create all visualizations
    create_scatter_plot(rural, urban, total)
    create_distance_bins_analysis(rural, urban, total)
    create_summary_statistics(rural, urban, total)
    create_heatmap(rural, urban, total)
    
    print("\n✅ All visualizations created successfully!")
    print("Generated files:")
    print("- africapolis_scatter.svg & .pdf")
    print("- africapolis_distance_bins.svg & .pdf")
    print("- africapolis_summary.svg & .pdf")
    print("- africapolis_heatmap.svg & .pdf")

if __name__ == "__main__":
    main()
