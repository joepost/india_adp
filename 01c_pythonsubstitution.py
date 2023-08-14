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

os.environ['USE_PYGEOS'] = '0'
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
from rasterio.crs import CRS
from shapely.geometry import shape
from shapely.geometry import Point
from shapely.geometry import box

# from pygeos import Geometry

from globals import *       # Imports the filepaths defined in globals.py


print('Packages imported.\n')

# Start timer
start_time = time.time()


# ==================================================================================================================
# 2. QGIS PROCESSES: GHSL
time_ghsl = time.time()

# ===========
# 2.1 Merge GHSL inputs into single raster covering all of India
time_21s = time.time()

if not os.path.isfile(ghsl_merged):
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
        with rasterio.open(ghsl_merged          # output filepath
                        , "w"                   # = overwrite existing files
                        , **out_meta            # set the file metadata 
                        ) as dest:
            dest.write(merged)
print('GHSL inputs merged into a single raster file.\n')
timestamp(time_21s)


# # ===========
# 2.2 Convert the CRS of merged GHSL file
time_22s = time.time()

if not os.path.isfile(ghsl_merged_wgs84):
    dst_crs = 'EPSG:4326'
    with rasterio.open(ghsl_merged) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
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
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)

print('GHSL raster converted to CRS EPSG:4326.\n')
timestamp(time_22s)


# ===========
# 2.3 Clip to specified state boundary
time_23s = time.time()
# Read in vector boundaries
districts_shp = gpd.read_file(districts_filepath)

if not os.path.isfile(ghsl_clipped):
    # Read in GHSL raster to be clipped
    with rasterio.open(ghsl_merged_wgs84) as src:
        raster_meta = src.meta
        raster_crs = src.crs
        # Clip the raster using 'mask' function
        clipped_raster, out_transform = mask(dataset=src
                                            , shapes=districts_shp.geometry
                                            , crop=True            # crops the raster to the mask geometry
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
    with rasterio.open(ghsl_clipped, 'w', **clipped_meta) as dst:
        dst.write(clipped_raster)

print('GHSL raster clipped to state boundaries and exported as .tif.\n')
timestamp(time_23s)

# ===========
# 2.5 Vectorise the GHSL raster layer

if not os.path.isfile(ghsl_poly_dissolved):
    time_24s = time.time()

    # Read in GHSL raster
    with rasterio.open(ghsl_clipped) as src:
        raster_data = src.read(1).astype(np.float32)    # use 'astype' to ensure values are in a format that can be used by shapely
        transform = src.transform                       # Get the transformation matrix to convert pixel coordinates to geographic coordinates
        raster_crs = src.crs

    # Filter out the target class values during shape generation
    target_classes = [11, 12, 13, 21]
    vector_features = (shape(geom).buffer(0) for geom, val in shapes(raster_data, transform=transform) if val in target_classes)

    # Create a GeoDataFrame directly from the shapes iterator
    gdf_ghsl = gpd.GeoDataFrame({'geometry': vector_features}, crs=raster_crs)

    gdf_ghsl['geometry'] = gdf_ghsl['geometry'].apply(lambda geom: shape(geom).buffer(0))   # Fix the geometries in GeoDataFrame (resolves self-intersections, overlapping polygons, etc.)

    print('GHSL raster vectorised.\n')
    timestamp(time_24s)
    
    # Dissolve geometries into a single feature
    time_25s = time.time()

    gdf_ghsl['dissolve_id'] = 1                                          # Create a new column with a constant value (ensures all dissolved into a single feature)
    dissolved_gdf_ghsl = gdf_ghsl.dissolve(by='dissolve_id', as_index=False)
    dissolved_gdf_ghsl.drop(columns='dissolve_id', inplace=True)         # Remove the 'dissolve_id' column (optional)
    print('GHSL vector file dissolved into single feature.\n')

    dissolved_gdf_ghsl.to_feather(ghsl_poly_dissolved)
    print(f'GHSL vector file exported to {sfmt}.\n')
    timestamp(time_25s)

print('GHSL processing complete.')
timestamp(time_ghsl)

# dissolved_gdf_ghsl.plot()
# plt.show()

# ==================================================================================================================
# 3. Agricultural Lands (Dynamic World)
time_cropland = time.time()

# ===========
# 3.1 Vectorise the DynamicWorld raster layer

if not os.path.isfile(cropland_poly_dissolved):
    # Read in GHSL raster
    with rasterio.open(cropland) as src:
        raster_data = src.read(1)                # Selects the 1st band in input file
        # Get the transformation matrix to convert pixel coordinates to geographic coordinates
        transform = src.transform
        raster_crs = src.crs

    # Filter out the target class values during shape generation
    target_classes = [1]
    vector_features = (shape(geom).buffer(0) for geom, val in shapes(raster_data, transform=transform) if val in target_classes)

    # Create a GeoDataFrame directly from the shapes iterator
    gdf_cropland = gpd.GeoDataFrame({'geometry': vector_features}, crs=raster_crs)

    gdf_cropland['geometry'] = gdf_cropland['geometry'].apply(lambda geom: shape(geom).buffer(0))   # Fix the geometries in GeoDataFrame (resolves self-intersections, overlapping polygons, etc.)

    print('DynamicWorld raster vectorised.\n')
    
    # Dissolve geometries into a single feature
    gdf_cropland['dissolve_id'] = 1                                          # Create a new column with a constant value (ensures all dissolved into a single feature)
    dissolved_gdf_cropland = gdf_cropland.dissolve(by='dissolve_id', as_index=False)
    dissolved_gdf_cropland.drop(columns='dissolve_id', inplace=True)         # Remove the 'dissolve_id' column (optional)
    print('DynamicWorld vector file dissolved into single feature.\n')

    dissolved_gdf_cropland.to_feather(cropland_poly_dissolved)
    print(f'DynamicWorld vector file exported to {sfmt}.\n')


print('DynamicWorld processing complete.')
timestamp(time_cropland)

# dissolved_gdf_cropland.plot()
# plt.show()

# ==================================================================================================================
# 4. WorldPop
time_worldpop = time.time()

# ===========
# 4.1 clip the boundaries of worldpop to state FIRST, and then generate point dataset
time_41s = time.time()

if not os.path.isfile(pop_tif_clipped):
    # Read in WorldPop raster to be clipped
    with rasterio.open(pop_tif) as src:
        raster_meta = src.meta
        raster_crs = src.crs
        # Clip the raster using 'mask' function
        clipped_raster, out_transform = mask(dataset=src
                                            , shapes=districts_shp.geometry
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
    with rasterio.open(pop_tif_clipped, 'w', **clipped_meta) as dst:
        dst.write(clipped_raster)

print('WorldPop raster clipped to state boundaries and exported as .tif.\n')
timestamp(time_41s)


# ===========
# 4.2 Vectorise the WorldPop raster layer into points

if not os.path.isfile(pop_points):
    time_42s = time.time()

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

    # Get the raster values at each point location
    raster_values = raster_data.ravel()

    # Create a GeoDataFrame with the points and set the CRS to match the raster
    geometry = [Point(lon[i], lat[i]) for i in range(len(lon))]
    gdf_pop = gpd.GeoDataFrame({'geometry': geometry, 'raster_value': raster_values}, crs=raster_crs)
    print('Worldpop raster converted into points')

    gdf_pop.to_feather(pop_points)
    print(f'WorldPop points exported as {sfmt}.\n')
    timestamp(time_42s)


print('WorldPop processing complete.')
timestamp(time_worldpop)


# gdf_pop.plot(column='raster_value')
# plt.show()


# ==================================================================================================================
# EXTRA. ZONAL STATISTICS
    
# NOTE: as of 2023-08-02, not certain whether to use the below functions. Remove if not actioned. 

# # Use zonal statistics
# zs = zonal_stats(districts_filepath     # 1st argument: shapefile of polygons
#                  , pop_tif_clipped         # 2nd argument: raster of pixels
#                  , band = 1
#                  , stats = ["sum"]
#                  , all_touched = False      # Specifies inclusion criteria; any pixel that touches the polygon is counted 
#                  , geojson_out = True
#                  , prefix = 'pop_'
#                  )

# geojson_string = json.dumps({"type": "FeatureCollection", "features": zs})
# gdf = gpd.read_file(geojson_string)

# # gdf.plot()
# # plt.show()

# gdf.head()



# ===============

print('\nScript complete.\n')
timestamp(start_time)