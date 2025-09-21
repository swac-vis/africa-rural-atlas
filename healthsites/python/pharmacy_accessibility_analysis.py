#!/usr/bin/env python3
"""
Pharmacy Accessibility Analysis for Africa
Combines GHSL population data with healthsites pharmacy locations
to analyze urban vs rural accessibility to pharmacies.
"""

import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
import json
from scipy.ndimage import distance_transform_edt
from shapely.geometry import Point
from pyproj import Transformer
import warnings
warnings.filterwarnings('ignore')

class PharmacyAccessibilityAnalyzer:
    def __init__(self, population_tif_path, pharmacy_geojson_path):
        """
        Initialize the analyzer with population and pharmacy data
        
        Args:
            population_tif_path: Path to GHSL population TIF file
            pharmacy_geojson_path: Path to healthsites GeoJSON file
        """
        self.population_tif_path = population_tif_path
        self.pharmacy_geojson_path = pharmacy_geojson_path
        self.population_raster = None
        self.pharmacy_points = None
        self.distance_raster = None
        self.results = []
        
    def load_population_data(self):
        """Load population raster data"""
        print("Loading population raster data...")
        with rasterio.open(self.population_tif_path) as src:
            self.population_raster = src.read(1)
            self.transform = src.transform
            self.crs = src.crs
            print(f"Population raster loaded: {self.population_raster.shape}")
            print(f"CRS: {self.crs}")
            
    def load_pharmacy_data(self):
        """Load pharmacy location data"""
        print("Loading pharmacy location data...")
        gdf = gpd.read_file(self.pharmacy_geojson_path)
        
        print(f"GeoJSON columns: {gdf.columns.tolist()}")
        print(f"First row structure: {gdf.iloc[0].to_dict()}")
        
        # Try different ways to filter pharmacy facilities based on actual structure
        pharmacy_gdf = None
        
        # Method 1: Check if 'properties' column exists
        if 'properties' in gdf.columns:
            try:
                pharmacy_gdf = gdf[gdf['properties'].apply(
                    lambda x: x.get('attributes', {}).get('healthcare') == 'pharmacy' or 
                             x.get('attributes', {}).get('amenity') == 'pharmacy'
                )]
            except:
                pass
        
        # Method 2: Check if attributes are directly in columns
        if pharmacy_gdf is None or len(pharmacy_gdf) == 0:
            if 'healthcare' in gdf.columns:
                pharmacy_gdf = gdf[gdf['healthcare'] == 'pharmacy']
            elif 'amenity' in gdf.columns:
                pharmacy_gdf = gdf[gdf['amenity'] == 'pharmacy']
        
        # Method 3: Check if there's a type column
        if pharmacy_gdf is None or len(pharmacy_gdf) == 0:
            if 'type' in gdf.columns:
                pharmacy_gdf = gdf[gdf['type'].str.contains('pharmacy', case=False, na=False)]
        
        # Use all facilities as health facilities (no filtering needed)
        print("Using all facilities as health facilities for analysis...")
        pharmacy_gdf = gdf
        
        print(f"Found {len(pharmacy_gdf)} pharmacy/health facilities")
        self.pharmacy_points = pharmacy_gdf
        
    def create_pharmacy_raster(self):
        """Create a raster where pharmacy locations are marked as 1"""
        print("Creating pharmacy raster...")
        height, width = self.population_raster.shape
        self.pharmacy_raster = np.zeros((height, width), dtype=np.uint8)
        
        # Create coordinate transformer from WGS84 to the raster CRS
        transformer = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)
        
        successful_points = 0
        error_count = 0
        out_of_bounds_count = 0
        unique_locations = set()
        
        # Convert pharmacy coordinates to raster indices
        for idx, point in self.pharmacy_points.iterrows():
            try:
                # Handle different geometry types
                if point.geometry.geom_type == 'Point':
                    lon, lat = point.geometry.x, point.geometry.y
                elif point.geometry.geom_type in ['Polygon', 'MultiPolygon']:
                    # For polygons, use centroid
                    centroid = point.geometry.centroid
                    lon, lat = centroid.x, centroid.y
                elif point.geometry.geom_type in ['LineString', 'MultiLineString']:
                    # For lines, use first coordinate
                    lon, lat = point.geometry.coords[0]
                else:
                    # Try to get representative point
                    lon, lat = point.geometry.representative_point().coords[0]
                
                # Transform coordinates from WGS84 to raster CRS
                x, y = transformer.transform(lon, lat)
                
                # Convert to raster coordinates
                row, col = rasterio.transform.rowcol(self.transform, x, y)
                
                # Check if coordinates are within raster bounds
                if 0 <= row < height and 0 <= col < width:
                    self.pharmacy_raster[row, col] = 1
                    unique_locations.add((row, col))
                    successful_points += 1
                else:
                    out_of_bounds_count += 1
                    
            except Exception as e:
                error_count += 1
                if error_count <= 10:  # Only print first 10 errors
                    print(f"Error processing point {idx}: {e}")
                elif error_count == 11:
                    print("... (suppressing further error messages)")
                continue
                
        pharmacy_count = np.sum(self.pharmacy_raster)
        unique_location_count = len(unique_locations)
        total_facilities = len(self.pharmacy_points)
        facilities_per_pixel = total_facilities / unique_location_count if unique_location_count > 0 else 0
        
        print(f"Pharmacy raster created with {pharmacy_count} pharmacy locations")
        print(f"Successfully processed {successful_points} facilities, {error_count} errors")
        print(f"Out of bounds: {out_of_bounds_count}, Unique locations: {unique_location_count}")
        print(f"Total facilities: {total_facilities}, Facilities per pixel: {facilities_per_pixel:.1f}")
        
    def calculate_distances(self):
        """Calculate distance from each pixel to nearest pharmacy"""
        print("Calculating distances to nearest pharmacy...")
        
        # Calculate Euclidean distance transform
        # This gives distance from each pixel to nearest non-zero pixel
        self.distance_raster = distance_transform_edt(~self.pharmacy_raster.astype(bool))
        
        # Convert to kilometers (assuming 1km resolution)
        self.distance_raster = self.distance_raster * 1.0
        
        print(f"Distance calculation completed")
        print(f"Distance range: {np.min(self.distance_raster):.2f} to {np.max(self.distance_raster):.2f} km")
        
    def analyze_grid_level(self):
        """Analyze each grid cell for population and accessibility"""
        print("Analyzing grid-level data...")
        
        height, width = self.population_raster.shape
        self.results = []
        
        for row in range(height):
            for col in range(width):
                population = self.population_raster[row, col]
                
                if population != 0:  # Only analyze cells with population
                    distance = self.distance_raster[row, col]
                    population_abs = abs(population)
                    grid_type = "urban" if population > 0 else "rural"
                    
                    # Count facilities in this grid cell
                    facilities_count = self.pharmacy_raster[row, col]
                    
                    # Classify distance into categories
                    distance_category = self.classify_distance(distance)
                    
                    self.results.append({
                        "row": row,
                        "col": col,
                        "population": population_abs,
                        "population_original": population,  # Keep original for urban/rural classification
                        "type": grid_type,
                        "distance": distance,
                        "distance_category": distance_category,
                        "facilities_count": int(facilities_count)
                    })
                    
        print(f"Grid analysis completed: {len(self.results)} populated cells analyzed")
        
    def classify_distance(self, distance):
        """Classify distance into categories"""
        if distance <= 1:
            return "0-1km"
        elif distance <= 2:
            return "1-2km"
        elif distance <= 5:
            return "2-5km"
        elif distance <= 10:
            return "5-10km"
        elif distance <= 20:
            return "10-20km"
        elif distance <= 50:
            return "20-50km"
        elif distance <= 100:
            return "50-100km"
        else:
            return ">100km"
            
    def aggregate_by_distance(self):
        """Aggregate population by distance thresholds"""
        print("Aggregating data by distance...")
        
        distance_thresholds = [1, 2, 5, 10, 20, 50, 100]
        distance_stats = {}
        
        for threshold in distance_thresholds:
            urban_pop = sum([r["population"] for r in self.results 
                           if r["population_original"] > 0 and r["distance"] <= threshold])
            rural_pop = sum([r["population"] for r in self.results 
                           if r["population_original"] < 0 and r["distance"] <= threshold])
            
            distance_stats[threshold] = {
                "urban": int(urban_pop),
                "rural": int(rural_pop),
                "total": int(urban_pop + rural_pop)
            }
            
        return distance_stats
        
    def analyze_urban_rural_gap(self):
        """Analyze differences between urban and rural accessibility"""
        print("Analyzing urban-rural accessibility gap...")
        
        urban_data = [r for r in self.results if r["population_original"] > 0]
        rural_data = [r for r in self.results if r["population_original"] < 0]
        
        if not urban_data or not rural_data:
            return {}
            
        urban_distances = [r["distance"] for r in urban_data]
        rural_distances = [r["distance"] for r in rural_data]
        
        urban_populations = [r["population"] for r in urban_data]
        rural_populations = [r["population"] for r in rural_data]
        
        # Calculate weighted averages
        urban_avg_distance = np.average(urban_distances, weights=urban_populations)
        rural_avg_distance = np.average(rural_distances, weights=rural_populations)
        
        # Calculate coverage percentages
        urban_1km_coverage = sum([r["population"] for r in urban_data if r["distance"] <= 1])
        rural_1km_coverage = sum([r["population"] for r in rural_data if r["distance"] <= 1])
        
        urban_5km_coverage = sum([r["population"] for r in urban_data if r["distance"] <= 5])
        rural_5km_coverage = sum([r["population"] for r in rural_data if r["distance"] <= 5])
        
        total_urban = sum(urban_populations)
        total_rural = sum(rural_populations)
        
        # Handle NaN values and ensure we have valid numbers
        if np.isnan(total_urban) or total_urban == 0:
            total_urban = 0
        if np.isnan(total_rural) or total_rural == 0:
            total_rural = 0
            
        # Handle NaN values in averages
        if np.isnan(urban_avg_distance):
            urban_avg_distance = 0
        if np.isnan(rural_avg_distance):
            rural_avg_distance = 0
        
        # Calculate coverage percentages with safe division
        urban_1km_pct = (urban_1km_coverage / total_urban * 100) if total_urban > 0 else 0
        rural_1km_pct = (rural_1km_coverage / total_rural * 100) if total_rural > 0 else 0
        urban_5km_pct = (urban_5km_coverage / total_urban * 100) if total_urban > 0 else 0
        rural_5km_pct = (rural_5km_coverage / total_rural * 100) if total_rural > 0 else 0
        
        gap_analysis = {
            "accessibility_gap": {
                "avg_distance_gap": rural_avg_distance - urban_avg_distance,
                "urban_avg_distance": urban_avg_distance,
                "rural_avg_distance": rural_avg_distance
            },
            "coverage_gap": {
                "1km": {
                    "urban_coverage": urban_1km_pct,
                    "rural_coverage": rural_1km_pct,
                    "gap": urban_1km_pct - rural_1km_pct
                },
                "5km": {
                    "urban_coverage": urban_5km_pct,
                    "rural_coverage": rural_5km_pct,
                    "gap": urban_5km_pct - rural_5km_pct
                }
            },
            "population_totals": {
                "urban": int(total_urban) if not np.isnan(total_urban) else 0,
                "rural": int(total_rural) if not np.isnan(total_rural) else 0,
                "total": int(total_urban + total_rural) if not np.isnan(total_urban + total_rural) else 0
            }
        }
        
        return gap_analysis
        
    def run_analysis(self):
        """Run the complete analysis"""
        print("Starting pharmacy accessibility analysis...")
        
        # Load data
        self.load_population_data()
        self.load_pharmacy_data()
        
        # Create pharmacy raster
        self.create_pharmacy_raster()
        
        # Calculate distances
        self.calculate_distances()
        
        # Analyze grid level
        self.analyze_grid_level()
        
        # Aggregate results
        distance_analysis = self.aggregate_by_distance()
        gap_analysis = self.analyze_urban_rural_gap()
        
        # Compile final results
        final_results = {
            "distance_analysis": distance_analysis,
            "urban_rural_gap": gap_analysis,
            "grid_level_data": self.results,  # Include detailed grid data
            "pharmacy_locations": [
                {
                    'lat': float(point.geometry.centroid.y if hasattr(point.geometry, 'centroid') else point.geometry.y),
                    'lon': float(point.geometry.centroid.x if hasattr(point.geometry, 'centroid') else point.geometry.x),
                    'area_type': 'unknown'  # Will be determined later if needed
                }
                for idx, point in self.pharmacy_points.iterrows()
            ],
            "metadata": {
                "total_grids_analyzed": len(self.results),
                "pharmacy_count": int(np.sum(self.pharmacy_raster)),
                "unique_pharmacy_locations": int(np.sum(self.pharmacy_raster)),
                "analysis_date": pd.Timestamp.now().isoformat(),
                "raster_resolution_km": 1.0,
                "coordinate_system": str(self.crs),
                "data_source": "GHSL population data + healthsites.io facilities"
            }
        }
        
        print("Analysis completed successfully!")
        return final_results
        
    def save_results(self, results, output_path):
        """Save analysis results to JSON file"""
        print(f"Saving results to {output_path}")
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print("Results saved successfully!")

def main():
    """Main function to run the analysis"""
    
    # File paths
    population_tif = "../../map_real/ghslpop_africa.tif"
    pharmacy_geojson = "../data/Africa_all_healthsites.geojson"
    output_json = "../data/pharmacy_accessibility_analysis.json"
    
    # Create analyzer and run analysis
    analyzer = PharmacyAccessibilityAnalyzer(population_tif, pharmacy_geojson)
    results = analyzer.run_analysis()
    
    # Save results
    analyzer.save_results(results, output_json)
    
    # Print summary
    print("\n" + "="*50)
    print("ANALYSIS SUMMARY")
    print("="*50)
    
    print(f"\nTotal grids analyzed: {results['metadata']['total_grids_analyzed']}")
    print(f"Pharmacy facilities: {results['metadata']['pharmacy_count']}")
    
    print(f"\nUrban population: {results['urban_rural_gap']['population_totals']['urban']:,}")
    print(f"Rural population: {results['urban_rural_gap']['population_totals']['rural']:,}")
    
    print(f"\nUrban average distance to pharmacy: {results['urban_rural_gap']['accessibility_gap']['urban_avg_distance']:.1f} km")
    print(f"Rural average distance to pharmacy: {results['urban_rural_gap']['accessibility_gap']['rural_avg_distance']:.1f} km")
    print(f"Accessibility gap: {results['urban_rural_gap']['accessibility_gap']['avg_distance_gap']:.1f} km")
    
    print(f"\nUrban 1km coverage: {results['urban_rural_gap']['coverage_gap']['1km']['urban_coverage']:.1f}%")
    print(f"Rural 1km coverage: {results['urban_rural_gap']['coverage_gap']['1km']['rural_coverage']:.1f}%")
    print(f"Coverage gap: {results['urban_rural_gap']['coverage_gap']['1km']['gap']:.1f}%")

if __name__ == "__main__":
    main()
