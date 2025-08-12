import rasterio
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from rasterio.features import rasterize
from rasterio.mask import mask
from scipy.ndimage import distance_transform_edt

# === 0. Load Africa Boundary ===
africa_fp = "africaonly.shp"  # e.g., Natural Earth, GADM, or custom
africa = gpd.read_file(africa_fp)
africa = africa.to_crs("EPSG:4326")  # Match to WorldPop if necessary

# === 1. Load and Clip Population Raster ===
pop_fp = "ppp_2000_1km_Aggregated.tif"
with rasterio.open(pop_fp) as pop_src:
    africa = africa.to_crs(pop_src.crs)  # Reproject Africa shapefile to raster CRS
    pop_data, pop_transform = mask(pop_src, africa.geometry, crop=True)
    pop_meta = pop_src.meta.copy()
    pop_meta.update({"height": pop_data.shape[1], "width": pop_data.shape[2], "transform": pop_transform})

pop_data = pop_data[0]  # Extract single band
shape = pop_data.shape
res = pop_meta['transform'][0]

# === 2. Load and Clip Roads ===
roads_fp = "GRIP4_region3.shp"
roads = gpd.read_file(roads_fp)
roads = roads.to_crs(africa.crs)
roads = roads[roads['GP_RTP'].isin([1, 2])]
roads = gpd.overlay(roads, africa, how='intersection')

# === 3. Rasterize Roads to Binary Mask ===
print("Rasterizing roads...")
road_mask = rasterize(
    [(geom, 1) for geom in roads.geometry],
    out_shape=shape,
    transform=pop_transform,
    fill=0,
    dtype=np.uint8
)

# === 4. Compute Distance Transform ===
print("Computing distance transform...")
distance_raster = distance_transform_edt(road_mask == 0, sampling=[res, res])

# === 5. Filter Population Cells and Get Distances ===
valid_mask = (~np.isnan(pop_data)) & (pop_data > 0)
valid_distances = distance_raster[valid_mask]
valid_pop = pop_data[valid_mask]



import pandas as pd
pd.DataFrame(valid_pop,valid_distances)

valid_pop = pd.DataFrame(valid_pop)
valid_distances = pd.DataFrame(valid_distances)

most_common = valid_pop.mode()[0][0]

# Drop rows where 'region' == most frequent value

valid_distances = valid_distances[~(valid_pop == most_common).all(axis=1)]
valid_pop = valid_pop[~(valid_pop == most_common).all(axis=1)]

valid_distances = 111.32 * valid_distances


# rural_threshold = 300
# valid_distances_rural = valid_distances[valid_pop[0]<rural_threshold]
# valid_pop_rural = [valid_pop[0]<rural_threshold]
# valid_distances_urban = valid_distances[valid_pop[0]>=rural_threshold]
# valid_pop_urban = [valid_pop[0]>=rural_threshold]
# valid_distances_total = valid_distances
# valid_pop_total = valid_pop 




# df_rural = pd.DataFrame({'pop':valid_pop_rural[0],'distance':valid_distances_rural[0]})
# df_urban = pd.DataFrame({'pop':valid_pop_urban[0],'distance':valid_distances_urban[0]})
# df_total = pd.DataFrame({'pop':valid_pop_total[0],'distance':valid_distances_total[0]})


# df_rural.groupby('distance')['pop'].sum().reset_index().to_csv('result_rural.csv')
# df_urban.groupby('distance')['pop'].sum().reset_index().to_csv('result_urban.csv')
# df_total.groupby('distance')['pop'].sum().reset_index().to_csv('result_total.csv')
