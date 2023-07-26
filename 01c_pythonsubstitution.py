# ==================================================================================================================

# DISSERTATION
# SECTION 01C: Python replacement of QGIS operations
#   This script is designed to replace the QGIS internal operations used for the initial project method. 

# Author: J Post

# ==================================================================================================================
# 0. IMPORT PACKAGES

import os
import glob
import subprocess
import sys
import json 
import time
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal
import rasterstats as rs
from rasterstats import zonal_stats
import json
import rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterio.plot import show
from rasterio.features import shapes
from shapely.geometry import shape
from shapely.geometry import Point
from pygeos import Geometry

from globals import *       # Imports the filepaths defined in globals.py


print('Packages imported.\n')

# Start timer
start_time = time.time()



# ==================================================================================================================
# 2. QGIS PROCESSES: GHSL
time_ghsl = time.time()

# ===========
# 2.1 Merge GHSL inputs into single raster covering all of India
src_files_to_merge = []            # initialise empty list
for file in ghsl_to_merge:
    src = rasterio.open(file)
    src_files_to_merge.append(src)

merged, out_trans = merge(src_files_to_merge)

out_meta = src.meta.copy()
out_meta.update({"driver": "GTiff",
                 "height": merged.shape[1],
                 "width": merged.shape[2],
                 "transform": out_trans})

if not os.path.isfile(ghsl_merged):
    with rasterio.open(ghsl_merged         # output filepath
                    , "w"               # = overwrite existing files
                    , **out_meta        # set the file metadata 
                    ) as dest:
        dest.write(merged)
    print('GHSL inputs merged into a single raster file.\n')


# ===========
# 2.2 Convert the CRS of merged GHSL file
# target_crs = 'EPSG:4326'          # REMOVE if 2.2 code block works when run externally (anaconda prompt)
if not os.path.isfile(ghsl_merged_wgs84):
    with rasterio.open(ghsl_merged) as src:
        dst_crs = 'EPSG:4326'
        src_crs = src.crs
        transform, width, height = calculate_default_transform(
            src_crs, dst_crs, src.width, src.height, *src.bounds
        )

        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(ghsl_merged_wgs84, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest
                )
    print('GHSL raster converted to CRS EPSG:4326.\n')


# ===========
# 2.3 Clip to specified state boundary
# Read in vector boundaries
districts_29 = gpd.read_file(districts_29_filepath)

# Read in GHSL raster to be clipped
with rasterio.open(ghsl_merged_wgs84) as src:
    raster_meta = src.meta
    raster_crs = src.crs
    # Clip the raster using 'mask' function
    clipped_raster, out_transform = mask(dataset=src
                                        , shapes=districts_29.geometry
                                        , crop=True
                                        , nodata=0             # sets the value for pixels outside the vector boundaries
                                        , all_touched=True     # decides whether to consider all pixels that touch the vector features
                                        )

# Update the metadata of clipped file
clipped_meta = raster_meta.copy()
clipped_meta.update({
    'height': clipped_raster.shape[1],
    'width': clipped_raster.shape[2],
    'transform': out_transform,
    'crs': raster_crs
})

# Export clipped raster to .tif
if not os.path.isfile(ghsl_29_clipped):
    with rasterio.open(ghsl_29_clipped, 'w', **clipped_meta) as dst:
        dst.write(clipped_raster)
    print('GHSL raster clipped to state boundaries and exported as .tif.\n')


# ===========
# 2.4 Vectorise the GHSL raster layer
# Read in GHSL raster
with rasterio.open(ghsl_29_clipped) as src:
    raster_data = src.read(1                # Selects the 1st band in input file
                        #    , masked=True    # Mask out any 'NoData' values
                           )
    # Get the transformation matrix to convert pixel coordinates to geographic coordinates
    transform = src.transform
    raster_crs = src.crs

vector_features = []        # Initialise an empty list to store generated vector features in 
for geom, val in shapes(raster_data, transform=transform):
    if val in [11, 12, 13, 21]:         # GHSL rural area values
        geom = shape(geom)              # Create a shapely geometry from the raster feature
        vector_features.append(geom)    # Append the geometry to the list of vector features

gdf_ghsl = gpd.GeoDataFrame({'geometry': vector_features}, crs = raster_crs)            # Convert vector_features into a GeoDataFrame
gdf_ghsl['geometry'] = gdf_ghsl['geometry'].apply(lambda geom: shape(geom).buffer(0))   # Fix the geometries in GeoDataFrame (resolves self-intersections, overlapping polygons, etc.)

# Export the GeoDataFrame to shapefile
# NOTE: Can remove intermediate export step; unnecessary processing
# gdf_ghsl.to_file(ghsl_poly)

print('GHSL raster vectorised.\n')


# ===========
# 2.5 Dissolve geometries into a single feature
gdf_ghsl['dissolve_id'] = 1                                          # Create a new column with a constant value (ensures all dissolved into a single feature)
dissolved_gdf_ghsl = gdf_ghsl.dissolve(by='dissolve_id', as_index=False)
dissolved_gdf_ghsl.drop(columns='dissolve_id', inplace=True)         # Remove the 'dissolve_id' column (optional)
print('GHSL vector file dissolved into single feature.\n')

if not os.path.isfile(ghsl_poly_dissolved):
    dissolved_gdf_ghsl.to_feather(ghsl_poly_dissolved)
    print('GHSL vector file exported to .feather.\n')
    


print('GHSL processing complete.')
timestamp(time_ghsl)



# ==================================================================================================================
# 3. Agricultural Lands (Dynamic World)
time_cropland = time.time()

# ===========
# 3.1 Vectorise the DynamicWorld raster layer
# Read in GHSL raster
with rasterio.open(cropland) as src:
    raster_data = src.read(1)                # Selects the 1st band in input file
    # Get the transformation matrix to convert pixel coordinates to geographic coordinates
    transform = src.transform
    raster_crs = src.crs

vector_features = []        # Initialise an empty list to store generated vector features in 
for geom, val in shapes(raster_data, transform=transform):
    if val == 1:
         geom = shape(geom)              # Create a shapely geometry from the raster feature
         vector_features.append(geom)    # Append the geometry to the list of vector features

gdf_cropland = gpd.GeoDataFrame({'geometry': vector_features}, crs = raster_crs)                # Convert vector_features into a GeoDataFrame
gdf_cropland['geometry'] = gdf_cropland['geometry'].apply(lambda geom: shape(geom).buffer(0))   # Fix the geometries in GeoDataFrame (resolves self-intersections, overlapping polygons, etc.)

print('DynamicWorld raster vectorised.\n')


# ===========
# 2.5 Dissolve geometries into a single feature
# NOTE: dissolve process taking long processing time; consider whether dissolve can be skipped 
#       and WorldPop points joined directly to the complex vectorised object. 
gdf_cropland['dissolve_id'] = 1                                          # Create a new column with a constant value (ensures all dissolved into a single feature)
dissolved_gdf_cropland = gdf_cropland.dissolve(by='dissolve_id', as_index=False)
dissolved_gdf_cropland.drop(columns='dissolve_id', inplace=True)         # Remove the 'dissolve_id' column (optional)
print('DynamicWorld vector file dissolved into single feature.\n')


dissolved_gdf_cropland.to_feather(cropland_poly_dissolved)
print('DynamicWorld vector file exported to .feather.\n')


print('DynamicWorld processing complete.')
timestamp(time_cropland)



# ==================================================================================================================
# 4. WorldPop
time_worldpop = time.time()

# ===========
# 4.1 clip the boundaries of worldpop to state FIRST, and then generate point dataset
# Read in vector boundaries
districts_29 = gpd.read_file(districts_29_filepath)

# Read in WorldPop raster to be clipped
with rasterio.open(pop_tif) as src:
    raster_meta = src.meta
    raster_crs = src.crs
    # Clip the raster using 'mask' function
    clipped_raster, out_transform = mask(dataset=src
                                        , shapes=districts_29.geometry
                                        , crop=True
                                        , nodata=0             # sets the value for pixels outside the vector boundaries
                                        , all_touched=True     # decides whether to consider all pixels that touch the vector features
                                        )

# Update the metadata of clipped file
clipped_meta = raster_meta.copy()
clipped_meta.update({
    'height': clipped_raster.shape[1],
    'width': clipped_raster.shape[2],
    'transform': out_transform,
    'crs': raster_crs
})

# Export clipped raster to .tif
if not os.path.isfile(pop_tif_clipped):
    with rasterio.open(pop_tif_clipped, 'w', **clipped_meta) as dst:
        dst.write(clipped_raster)
    print('WorldPop raster clipped to state boundaries and exported as .tif.\n')


# ===========
# 4.2 Vectorise the WorldPop raster layer into points

with rasterio.open(pop_tif_clipped) as src:
    raster_data = src.read(1)  # Read the raster data and mask out any NoData values
    transform = src.transform  # Get the transformation matrix to convert pixel coordinates to geographic coordinates
    raster_crs = src.crs

num_rows, num_cols = raster_data.shape                      # Get the number of rows and columns in the raster
x_coords, y_coords = np.meshgrid(np.arange(0, num_cols),    # Create a regular grid of points based on the raster's extent and resolution
                                 np.arange(0, num_rows))    
points = np.c_[x_coords.ravel(), y_coords.ravel()]

# Transform the grid of points from pixel coordinates to geographic coordinates
lon, lat = rasterio.transform.xy(transform, points[:, 1], points[:, 0])

# Create a GeoDataFrame with the points and set the CRS to match the raster
geometry = [Point(lon[i], lat[i]) for i in range(len(lon))]
gdf_pop = gpd.GeoDataFrame({'geometry': geometry}, crs=raster_crs)


# NOTE: Currently not exporting WorldPop points as process takes too long.
#       Can remove this, but then locks in long processing time each time the process is run?
#   UPDATE 2023-07-26: Try exporting using geofeathers instead, to speed up processing time 
gdf_pop.to_feather(pop_points)
print('WorldPop raster converted into points and exported as .gpkg.\n')


print('WorldPop processing complete.')
timestamp(time_worldpop)


# ==================================================================================================================
# EXTRA. ZONAL STATISTICS
    

# Use zonal statistics
zs = zonal_stats(districts_29_filepath     # 1st argument: shapefile of polygons
                 , pop_tif_clipped         # 2nd argument: raster of pixels
                 , band = 1
                 , stats = ["sum"]
                 , all_touched = False      # Specifies inclusion criteria; any pixel that touches the polygon is counted 
                 , geojson_out = True
                 , prefix = 'pop_'
                 )

geojson_string = json.dumps({"type": "FeatureCollection", "features": zs})
gdf = gpd.read_file(geojson_string)

# gdf.plot()
# plt.show()

gdf.head()



# ===============

print('\nScript complete.\n')
timestamp(start_time)