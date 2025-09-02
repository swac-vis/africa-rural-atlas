#!/usr/bin/env python3
"""
Overlap Analysis between Africa Healthsites and GHSL Population Data
Converts healthsites to shapefile and analyzes overlap with population data
"""

import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd
from shapely.geometry import Point
import warnings
warnings.filterwarnings('ignore')

def analyze_overlap():
    """Analyze overlap between healthsites and GHSL population data"""
    
    print("Loading data...")
    
    # Load healthsites data
    try:
        healthsites_gdf = gpd.read_file('../data/Africa_all_healthsites.geojson')
        print(f"Healthsites loaded: {len(healthsites_gdf)} facilities")
        print(f"Healthsites CRS: {healthsites_gdf.crs}")
        print(f"Healthsites bounds: {healthsites_gdf.total_bounds}")
    except Exception as e:
        print(f"Error loading healthsites: {e}")
        return
    
    # Load GHSL population data
    try:
        with rasterio.open('../../map_real/ghslpop_africa.tif') as src:
            ghsl_bounds = src.bounds
            ghsl_crs = src.crs
            ghsl_shape = src.shape
            print(f"GHSL CRS: {ghsl_crs}")
            print(f"GHSL bounds: {ghsl_bounds}")
            print(f"GHSL shape: {ghsl_shape}")
    except Exception as e:
        print(f"Error loading GHSL data: {e}")
        return
    
    # Check CRS compatibility
    print(f"\nCRS Compatibility Check:")
    print(f"Healthsites CRS: {healthsites_gdf.crs}")
    print(f"GHSL CRS: {ghsl_crs}")
    
    # Convert healthsites to GHSL CRS if needed
    if healthsites_gdf.crs != ghsl_crs:
        print("Converting healthsites to GHSL CRS...")
        try:
            healthsites_gdf = healthsites_gdf.to_crs(ghsl_crs)
            print(f"Converted CRS: {healthsites_gdf.crs}")
        except Exception as e:
            print(f"CRS conversion failed: {e}")
            return
    
    # Check bounds overlap
    hs_bounds = healthsites_gdf.total_bounds
    print(f"\nBounds Check:")
    print(f"Healthsites bounds: {hs_bounds}")
    print(f"GHSL bounds: {ghsl_bounds}")
    
    # Calculate overlap
    overlap_x = (min(hs_bounds[2], ghsl_bounds[2]) - max(hs_bounds[0], ghsl_bounds[0]))
    overlap_y = (min(hs_bounds[3], ghsl_bounds[3]) - max(hs_bounds[1], ghsl_bounds[1]))
    
    if overlap_x > 0 and overlap_y > 0:
        print(f"✓ Overlap detected: {overlap_x:.2f} x {overlap_y:.2f} degrees")
    else:
        print("✗ No overlap detected")
        return
    
    # Filter healthsites within GHSL bounds
    print("\nFiltering healthsites within GHSL bounds...")
    within_bounds = healthsites_gdf.cx[
        ghsl_bounds[0]:ghsl_bounds[2], 
        ghsl_bounds[1]:ghsl_bounds[3]
    ]
    print(f"Healthsites within GHSL bounds: {len(within_bounds)}")
    
    # Filter only Point geometries for shapefile
    print("\nFiltering Point geometries for shapefile...")
    point_facilities = within_bounds[within_bounds.geometry.geom_type == 'Point']
    print(f"Point facilities: {len(point_facilities)}")
    
    # Save filtered data as shapefile (only points)
    output_shapefile = '../data/healthsites_ghsl_overlap.shp'
    try:
        point_facilities.to_file(output_shapefile)
        print(f"✓ Shapefile saved: {output_shapefile}")
    except Exception as e:
        print(f"Error saving shapefile: {e}")
    
    # Create a simple overlap analysis
    print("\nCreating overlap analysis...")
    
    # Sample some points to test overlap
    sample_size = min(1000, len(within_bounds))
    sample_points = within_bounds.sample(n=sample_size, random_state=42)
    
    overlap_results = []
    for idx, point in sample_points.iterrows():
        try:
            # Get coordinates
            if hasattr(point.geometry, 'x'):
                lon, lat = point.geometry.x, point.geometry.y
            else:
                lon, lat = point.geometry.coords[0]
            
            # Check if point is within raster bounds
            with rasterio.open('../../map_real/ghslpop_africa.tif') as src:
                row, col = src.index(lon, lat)
                if 0 <= row < src.height and 0 <= col < src.width:
                    population = src.read(1, window=((row, row+1), (col, col+1)))[0, 0]
                    overlap_results.append({
                        'facility_id': idx,
                        'longitude': lon,
                        'latitude': lat,
                        'population': population,
                        'has_population': population != 0
                    })
                else:
                    overlap_results.append({
                        'facility_id': idx,
                        'longitude': lon,
                        'latitude': lat,
                        'population': 0,
                        'has_population': False
                    })
        except Exception as e:
            print(f"Error processing point {idx}: {e}")
            continue
    
    # Analyze overlap results
    if overlap_results:
        df = pd.DataFrame(overlap_results)
        print(f"\nOverlap Analysis Results:")
        print(f"Total facilities tested: {len(df)}")
        print(f"Facilities with population data: {df['has_population'].sum()}")
        print(f"Facilities without population data: {(~df['has_population']).sum()}")
        print(f"Overlap percentage: {df['has_population'].mean()*100:.1f}%")
        
        # Save overlap analysis
        overlap_csv = '../data/overlap_analysis.csv'
        df.to_csv(overlap_csv, index=False)
        print(f"✓ Overlap analysis saved: {overlap_csv}")
    
    print("\nOverlap analysis completed!")

def create_visualization_data():
    """Create data for visualization of overlap"""
    
    print("\nCreating visualization data...")
    
    try:
        # Load the filtered healthsites
        healthsites = gpd.read_file('../data/healthsites_ghsl_overlap.shp')
        
        # Create a summary of facilities by country
        if 'country' in healthsites.columns:
            country_summary = healthsites['country'].value_counts()
            country_summary.to_csv('../data/facilities_by_country.csv')
            print(f"✓ Country summary saved: {len(country_summary)} countries")
        
        # Create a summary of facility types
        if 'amenity' in healthsites.columns:
            type_summary = healthsites['amenity'].value_counts()
            type_summary.to_csv('../data/facilities_by_type.csv')
            print(f"✓ Facility type summary saved: {len(type_summary)} types")
        
        # Create a summary of healthcare types
        if 'healthcare' in healthsites.columns:
            healthcare_summary = healthsites['healthcare'].value_counts()
            healthcare_summary.to_csv('../data/facilities_by_healthcare.csv')
            print(f"✓ Healthcare type summary saved: {len(healthcare_summary)} types")
        
        # Create a summary of geometry types
        geom_summary = healthsites.geometry.geom_type.value_counts()
        geom_summary.to_csv('../data/facilities_by_geometry.csv')
        print(f"✓ Geometry type summary saved: {len(geom_summary)} types")
        
    except Exception as e:
        print(f"Error creating visualization data: {e}")

if __name__ == "__main__":
    print("="*60)
    print("Africa Healthsites - GHSL Population Overlap Analysis")
    print("="*60)
    
    # Run overlap analysis
    analyze_overlap()
    
    # Create visualization data
    create_visualization_data()
    
    print("\n" + "="*60)
    print("Analysis completed!")
    print("="*60)
