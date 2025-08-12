import rasterio
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from rasterio.features import rasterize
from rasterio.mask import mask
from scipy.ndimage import distance_transform_edt
import pandas as pd
import os
import glob
from shapely.geometry import box

# === 0. Load Africa Boundary ===
africa_fp = "../data/africaonly.shp"  # e.g., Natural Earth, GADM, or custom
africa = gpd.read_file(africa_fp)
africa = africa.to_crs("EPSG:4326")  # Match to WorldPop if necessary

# === 1. Load and Clip Roads ===
roads_fp = "../data/GRIP4_region3.shp"
roads = gpd.read_file(roads_fp)
roads = roads.to_crs(africa.crs)
roads = roads[roads['GP_RTP'].isin([1, 2])]
roads = gpd.overlay(roads, africa, how='intersection')

# === 2. Process Each Country File ===
output_dir = "../data/output_tif"
country_files = glob.glob(os.path.join(output_dir, "*.tif"))

# Remove .aux.xml files and get only .tif files
country_files = [f for f in country_files if f.endswith('.tif') and not f.endswith('.aux.xml')]

print(f"Found {len(country_files)} country files to process")

# Store results for all countries
all_results = []
all_detailed_results = []

for country_file in country_files:
    country_name = os.path.basename(country_file).replace('.tif', '')
    print(f"Processing {country_name}...")
    
    try:
        # Load country population raster
        with rasterio.open(country_file) as pop_src:
            # Get country boundary from the raster extent
            country_bounds = pop_src.bounds
            country_geom = gpd.GeoDataFrame(
                geometry=[box(*country_bounds)], 
                crs=pop_src.crs
            )
            
            # Clip roads to this country
            country_roads = gpd.overlay(roads, country_geom, how='intersection')
            
            # Read population data
            pop_data = pop_src.read(1)  # Read first band
            pop_transform = pop_src.transform
            pop_meta = pop_src.meta.copy()
            
        # Skip if no roads in this country
        if len(country_roads) == 0:
            print(f"No roads found in {country_name}, skipping...")
            continue
            
        # === 3. Rasterize Roads to Binary Mask ===
        print(f"Rasterizing roads for {country_name}...")
        road_mask = rasterize(
            [(geom, 1) for geom in country_roads.geometry],
            out_shape=pop_data.shape,
            transform=pop_transform,
            fill=0,
            dtype=np.uint8
        )
        
        # === 4. Compute Distance Transform ===
        print(f"Computing distance transform for {country_name}...")
        res = pop_meta['transform'][0]
        distance_raster = distance_transform_edt(road_mask == 0, sampling=[res, res])
        
        # === 5. Filter Population Cells and Get Distances ===
        valid_mask = (~np.isnan(pop_data)) & (pop_data > 0)
        valid_distances = distance_raster[valid_mask]
        valid_pop = pop_data[valid_mask]
        
        # Skip if no valid data
        if len(valid_pop) == 0:
            print(f"No valid population data in {country_name}, skipping...")
            continue
            
        # === 6. Data Cleaning ===
        valid_pop_df = pd.DataFrame(valid_pop)
        valid_distances_df = pd.DataFrame(valid_distances)
        
        # Remove most common value (likely invalid data)
        most_common = valid_pop_df.mode()[0][0]
        valid_distances_df = valid_distances_df[~(valid_pop_df == most_common).all(axis=1)]
        valid_pop_df = valid_pop_df[~(valid_pop_df == most_common).all(axis=1)]
        
        # Convert distances to kilometers
        valid_distances_km = 111.32 * valid_distances_df
        
        # Create detailed results dataframe (individual cells)
        df_detailed = pd.DataFrame({
            'country': country_name,
            'pop_density': valid_pop_df.iloc[:, 0],  # Population density per cell
            'distance': valid_distances_km.iloc[:, 0]
        })
        
        # Create aggregated results dataframe
        df_aggregated = df_detailed.groupby('distance')['pop_density'].sum().reset_index()
        df_aggregated['country'] = country_name
        
        all_results.append(df_aggregated)
        all_detailed_results.append(df_detailed)
        
        print(f"Completed {country_name}: {len(df_detailed)} valid cells")
        
    except Exception as e:
        print(f"Error processing {country_name}: {str(e)}")
        continue

# === 7. Combine All Results ===
if all_results:
    df_all = pd.concat(all_results, ignore_index=True)
    df_detailed_all = pd.concat(all_detailed_results, ignore_index=True)
    
    # Save combined results
    df_all.to_csv('../data/result_all_countries.csv', index=False)
    df_detailed_all.to_csv('../data/result_all_countries_detailed.csv', index=False)
    
    # Also save individual country results
    for result in all_results:
        country_name = result['country'].iloc[0]
        result.to_csv(f'../data/result_{country_name}.csv', index=False)
    
    # Save detailed individual country results
    for detailed_result in all_detailed_results:
        country_name = detailed_result['country'].iloc[0]
        detailed_result.to_csv(f'../data/result_{country_name}_detailed.csv', index=False)
    
    print(f"Processing complete. Results saved for {len(all_results)} countries.")
    print(f"Total valid cells processed: {len(df_all)}")
    print(f"Detailed data saved with individual cell information.")
else:
    print("No valid results generated.")
