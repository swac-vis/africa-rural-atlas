import rasterio
import numpy as np
import json
from rasterio.transform import xy

def process_aggregated_tif(tif_path, output_path):
    """
    Process aggregated TIF files and output as JSON format
    Each grid cell as a key, value contains geographic location and four band data
    """
    
    with rasterio.open(tif_path) as src:
        # Read all band data
        data = src.read()
        
        # Get geographic transformation information
        transform = src.transform
        crs = src.crs
        
        print(f"TIF file information:")
        print(f"  Shape: {src.shape}")
        print(f"  Number of bands: {src.count}")
        print(f"  Coordinate system: {crs}")
        print(f"  Transformation matrix: {transform}")
        
        # Initialize result dictionary
        grid_data = {}
        
        # Iterate through each grid cell
        for row in range(src.height):
            for col in range(src.width):
                # Calculate geographic coordinates (grid center point)
                # Use xy() function to get correct coordinates
                x, y = xy(transform, col, row)
                
                # Get four band data for this grid
                rural_population = float(data[0][row, col])  # Band 1: rural population
                rural_area = float(data[1][row, col])        # Band 2: rural area
                urban_population = float(data[2][row, col])  # Band 3: urban population
                urban_area = float(data[3][row, col])        # Band 4: urban area
                
                # Skip invalid data (nodata values)
                if rural_population == -9999 or np.isnan(rural_population):
                    continue
                
                # Create grid key (using row and column coordinates)
                grid_key = f"grid_{row}_{col}"
                
                # Store data - Note: x is longitude, y is latitude
                grid_data[grid_key] = {
                    "geographic_location": {
                        "longitude": x,  # Longitude
                        "latitude": y,   # Latitude
                        "row": row,
                        "col": col
                    },
                    "rural_population": rural_population,
                    "rural_area": rural_area,
                    "urban_population": urban_population,
                    "urban_area": urban_area
                }
        
        # Add metadata
        result = {
            "metadata": {
                "source_file": tif_path,
                "grid_size": f"{src.height}x{src.width}",
                "coordinate_system": str(crs),
                "transform": str(transform),
                "description": {
                    "band_1": "rural_population (population < 300)",
                    "band_2": "rural_area (area < 300)",
                    "band_3": "urban_population (population >= 300)",
                    "band_4": "urban_area (area >= 300)"
                }
            },
            "grid_data": grid_data
        }
        
        # Save as JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nProcessing complete:")
        print(f"  Valid grid count: {len(grid_data)}")
        print(f"  Output file: {output_path}")
        
        # Output statistics
        rural_pop_total = sum(item["rural_population"] for item in grid_data.values())
        urban_pop_total = sum(item["urban_population"] for item in grid_data.values())
        rural_area_total = sum(item["rural_area"] for item in grid_data.values())
        urban_area_total = sum(item["urban_area"] for item in grid_data.values())
        
        print(f"\nStatistics:")
        print(f"  Total rural population: {rural_pop_total:,.0f}")
        print(f"  Total urban population: {urban_pop_total:,.0f}")
        print(f"  Total rural area: {rural_area_total:,.0f}")
        print(f"  Total urban area: {urban_area_total:,.0f}")
        print(f"  Total population: {rural_pop_total + urban_pop_total:,.0f}")
        
        return result

if __name__ == "__main__":
    # Input and output file paths
    tif_file = "../map/data/tif/aggregated_1000km_africa.tif"
    output_file = "../map/data/aggregated_1000km_africa_fixed.json"
    
    # Process TIF file
    result = process_aggregated_tif(tif_file, output_file)
    
    # Display first few grid data as examples
    print(f"\nFirst 5 grid data examples:")
    for i, (key, value) in enumerate(list(result["grid_data"].items())[:5]):
        print(f"\n{key}:")
        print(f"  Location: Longitude={value['geographic_location']['longitude']:.4f}, Latitude={value['geographic_location']['latitude']:.4f}")
        print(f"  Rural population: {value['rural_population']:,.0f}")
        print(f"  Rural area: {value['rural_area']:,.0f}")
        print(f"  Urban population: {value['urban_population']:,.0f}")
        print(f"  Urban area: {value['urban_area']:,.0f}") 