#!/usr/bin/env python3
"""
Convert Africa_all_healthsites.geojson to Shapefile format
Handles different geometry types and preserves all attributes
"""

import geopandas as gpd
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def convert_geojson_to_shapefile():
    """Convert the GeoJSON file to Shapefile format"""
    
    print("="*60)
    print("Converting Africa_all_healthsites.geojson to Shapefile")
    print("="*60)
    
    # Load the GeoJSON file
    print("Loading GeoJSON file...")
    try:
        gdf = gpd.read_file('data/Africa_all_healthsites.geojson')
        print(f"✓ GeoJSON loaded: {len(gdf)} facilities")
        print(f"CRS: {gdf.crs}")
        print(f"Columns: {list(gdf.columns)}")
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        return
    
    # Analyze geometry types
    print("\nAnalyzing geometry types...")
    geom_types = gdf.geometry.geom_type.value_counts()
    print("Geometry types:")
    for geom_type, count in geom_types.items():
        print(f"  {geom_type}: {count:,}")
    
    # Check for any problematic geometries
    print("\nChecking for problematic geometries...")
    valid_geometries = gdf[gdf.geometry.is_valid]
    invalid_geometries = gdf[~gdf.geometry.is_valid]
    
    print(f"Valid geometries: {len(valid_geometries):,}")
    print(f"Invalid geometries: {len(invalid_geometries):,}")
    
    if len(invalid_geometries) > 0:
        print("Warning: Found invalid geometries. Attempting to fix...")
        # Try to fix invalid geometries
        try:
            gdf_fixed = gdf.copy()
            gdf_fixed.geometry = gdf_fixed.geometry.buffer(0)
            valid_geometries = gdf_fixed[gdf_fixed.geometry.is_valid]
            print(f"After fixing: {len(valid_geometries):,} valid geometries")
            gdf = gdf_fixed
        except Exception as e:
            print(f"Could not fix geometries: {e}")
            print("Proceeding with original data...")
    
    # Create separate shapefiles for each geometry type
    print("\nCreating separate shapefiles by geometry type...")
    
    for geom_type in geom_types.index:
        if geom_type in ['Point', 'LineString', 'Polygon']:
            type_gdf = gdf[gdf.geometry.geom_type == geom_type]
            if len(type_gdf) > 0:
                type_output = f'data/Africa_healthsites_{geom_type.lower()}.shp'
                try:
                    type_gdf.to_file(type_output)
                    print(f"✓ {geom_type} shapefile saved: {type_output} ({len(type_gdf):,} features)")
                except Exception as e:
                    print(f"Error saving {geom_type} shapefile: {e}")
    
    # Try to save as a combined shapefile (this might fail with mixed geometries)
    print("\nAttempting to save combined shapefile...")
    output_shp = 'data/Africa_all_healthsites.shp'
    
    try:
        gdf.to_file(output_shp)
        print(f"✓ Combined shapefile saved: {output_shp}")
    except Exception as e:
        print(f"Warning: Could not save combined shapefile: {e}")
        print("This is expected with mixed geometry types.")
        print("Use the separate geometry type shapefiles instead.")
    
    # Create summary statistics
    print("\nCreating summary statistics...")
    
    # Country summary
    if 'country' in gdf.columns:
        country_summary = gdf['country'].value_counts()
        country_summary.to_csv('data/facilities_by_country_full.csv')
        print(f"✓ Country summary saved: {len(country_summary)} countries")
    
    # Amenity summary
    if 'amenity' in gdf.columns:
        amenity_summary = gdf['amenity'].value_counts()
        amenity_summary.to_csv('data/facilities_by_amenity.csv')
        print(f"✓ Amenity summary saved: {len(amenity_summary)} types")
    
    # Healthcare summary
    if 'healthcare' in gdf.columns:
        healthcare_summary = gdf['healthcare'].value_counts()
        healthcare_summary.to_csv('data/facilities_by_healthcare.csv')
        print(f"✓ Healthcare summary saved: {len(healthcare_summary)} types")
    
    # Geometry type summary
    geom_summary = gdf.geometry.geom_type.value_counts()
    geom_summary.to_csv('data/facilities_by_geometry_full.csv')
    print(f"✓ Geometry type summary saved: {len(geom_summary)} types")
    
    # Create a comprehensive summary
    print("\n" + "="*60)
    print("CONVERSION SUMMARY")
    print("="*60)
    print(f"Total facilities: {len(gdf):,}")
    print(f"Valid geometries: {len(valid_geometries):,}")
    print(f"Invalid geometries: {len(invalid_geometries):,}")
    print(f"CRS: {gdf.crs}")
    print(f"Output files:")
    print(f"  - Point facilities: data/Africa_healthsites_point.shp")
    print(f"  - Polygon facilities: data/Africa_healthsites_polygon.shp")
    print(f"  - Summary CSVs: data/facilities_by_*.csv")
    
    print("\nConversion completed successfully!")

if __name__ == "__main__":
    convert_geojson_to_shapefile()
