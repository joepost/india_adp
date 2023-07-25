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

from globals import *       # Imports the filepaths defined in globals.py


print('Packages imported.\n')

# Start timer
start_time = time.time()



# ==================================================================================================================
# 2. QGIS PROCESSES: GHSL


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

with rasterio.open(ghsl_merged         # output filepath
                   , "w"               # = overwrite existing files
                   , **out_meta        # set the file metadata 
                   ) as dest:
    dest.write(merged)


# # 2.2a Check the CRS of GHSL merged file
# # Open the GeoTIFF file
# with rasterio.open(ghsl_merged) as src:         # 'with rasterio.open' ensures a file is 'opened' and 'closed' automatically at end of block
#     crs = src.crs
#     print("CRS of the GeoTIFF:")
#     print(crs)


# 2.2 Convert the CRS of merged GHSL file
target_crs = 'EPSG:4326'
with rasterio.open(ghsl_merged) as src:
    src_crs = src.crs
    transform, width, height = calculate_default_transform(
        src_crs, target_crs, src.width, src.height, *src.bounds
    )

    kwargs = src.meta.copy()
    kwargs.update({
        'crs': target_crs,
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

# # Check the updated CRS is correct
# with rasterio.open(ghsl_merged_wgs84) as src:
#     # Access the CRS information
#     crs = src.crs
#     # Print the CRS information
#     print("CRS of the GeoTIFF:")
#     print(crs)


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
with rasterio.open(ghsl_29_clipped, 'w', **clipped_meta) as dst:
    dst.write(clipped_raster)


# 2.4 Vectorise the GHSL raster layer
# Read in GHSL raster
with rasterio.open(ghsl_29_clipped) as src:
    raster_data = src.read(1                # Selects the 1st band in input file
                           , masked=True    # Mask out any 'NoData' values
                           )
    # Get the transformation matrix to convert pixel coordinates to geographic coordinates
    transform = src.transform

vector_features = []
for geom, val in shapes(raster_data
                        # , mask=raster_data.mask       
                        , transform=transform):
    if val in [11, 12, 13, 21]:
        # Create a shapely geometry from the raster feature
        geom = shape(geom)
        # Append the geometry to the list of vector features
        vector_features.append(geom)

vector_features

# Create a GeoDataFrame from the vector features
gdf = gpd.GeoDataFrame({'geometry': vector_features})

gdf.shape
gdf.head()

# # Define the path to save the shapefile
# shapefile_output = 'path/to/output/vectorized_layer.shp'

# # Save the GeoDataFrame to a shapefile
# gdf.to_file(shapefile_output)



#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Read the raster file using rasterio:
with rasterio.open(ghsl_29_clipped) as src:
    # Read the raster data and mask out any NoData values
    raster_data = src.read(1, masked=True)
    # Get the transformation matrix to convert pixel coordinates to geographic coordinates
    transform = src.transform

# Print unique values in the raster data
print("Unique values in the raster data:", set(raster_data.flatten()))

# Visualize the raster data
plt.imshow(raster_data, cmap='gray')
plt.colorbar()
plt.show()

#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

gdf.plot()
plt.show()

gdf.head()



# ===============

print('\nScript complete.\n')
timestamp(start_time)