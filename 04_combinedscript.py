# ==================================================================================================================

# DISSERTATION
# SECTION 04: COMBINED SCRIPT
#   This script combines components 01, 01C & 02 into a single execution file. 
# Date created: 2023-08-16
# Author: J Post

# ==================================================================================================================

#*************************************************************************************************************************************
#                   SCRIPT 01_PREPAREFILES.PY
#*************************************************************************************************************************************

# ==================================================================================================================
# 0. IMPORT PACKAGES

import os
import glob
import subprocess
import sys
import json
import pandas as pd
import xlrd
import openpyxl
import time
import math

os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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

from globals import *       # Imports the filepaths defined in globals.py

print('Packages imported.\n')

# Start timer
start_time = time.time()

# ==================================================================================================================
# 1. CREATE REQUIRED SUBFOLDERS

for path in data_subfolders:
    subfolderpath = os.path.join(datafolder, path)
    if not os.path.exists(subfolderpath):
        print(f"Creating folder {subfolderpath}")
        os.makedirs(subfolderpath)

for path in output_subfolders:
    subfolderpath = os.path.join(repository,'Output', path)
    if not os.path.exists(subfolderpath):
        print(f"Creating folder {subfolderpath}")
        os.makedirs(subfolderpath)

for path in output_scale_subfolders:
    subfolderpath = os.path.join(outputfolder, path)
    if not os.path.exists(subfolderpath):
        print(f"Creating folder {subfolderpath}")
        os.makedirs(subfolderpath)

for path in intermediate_subfolders:
    subfolderpath = os.path.join(outputfolder, 'intermediates', path)
    if not os.path.exists(subfolderpath):
        print(f"Creating folder {subfolderpath}")
        os.makedirs(subfolderpath)

for path in final_subfolders:
    subfolderpath = os.path.join(outputfolder, 'final', path)
    if not os.path.exists(subfolderpath):
        print(f"Creating folder {subfolderpath}")
        os.makedirs(subfolderpath)    


# ==================================================================================================================
# 2. LOAD AND CLEAN DATA

# Read in the census data
b4_column_names = ['Table code', 'State code', 'District code', 'Area name', 'Total Rural Urban', 'Age group'
                   , 'Main workers P', 'Main workers M', 'Main workers F', 'Cultivators P', 'Cultivators M', 'Cultivators F'
                   , 'Agricultural labourers P', 'Agricultural labourers M', 'Agricultural labourers F'
                   , 'Primary sector other P', 'Primary sector other M', 'Primary sector other F' 
]
census_ag_main = pd.read_excel(agworkers_main
                               , sheet_name=0
                               , header = None
                               , names = b4_column_names
                               , dtype = {'State code':str, 'District code':str}
                               , usecols = 'A:R'
                               , skiprows = 8
                               , skipfooter = 24
                               )


b6_column_names = ['Table code', 'State code', 'District code', 'Area name', 'Total Rural Urban', 'Age group'
                   , 'marginal_6m_p', 'marginal_6m_m', 'marginal_6m_f'
                   , 'marginal_3m_p', 'marginal_3m_m', 'marginal_3m_f'
                   , 'Cultivators P', 'Cultivators M', 'Cultivators F'
                   , 'Agricultural labourers P', 'Agricultural labourers M', 'Agricultural labourers F'
                   , 'Primary sector other P', 'Primary sector other M', 'Primary sector other F' 
]
census_ag_marginal = pd.read_excel(agworkers_marginal
                               , sheet_name=0
                               , header = None
                               , names = b6_column_names
                               , dtype = {'State code':str, 'District code':str}
                               , usecols = 'A:U'
                               , skiprows = 8
                               , skipfooter = 24
                               )


a1_column_names = ['State Code',	'District Code',	'Sub District Code', 'Region',	'Name',	'Total Rural Urban'
                   ,	'Villages inhabited',	'Villages uninhabited',	'Number of towns',	'Number of households'
                   ,	'Population',	'Males',	'Females',	'Area sq km',	'Population per sq km'
                   ]
census_pop =            pd.read_excel(census_population
                                      , sheet_name=0
                                      , header = None
                                      , names = a1_column_names
                                      , dtype = {'State Code':str, 'District Code':str, 'Sub District Code':str}
                                      , usecols = 'A:O'
                                      , skiprows = 4
                                      , skipfooter = 28
                                      )


# Create dataframe of location codes
loc_codes = census_pop[['State Code', 'District Code', 'Sub District Code', 'Region', 'Name']]
state_codes = loc_codes[(loc_codes['Sub District Code']== '00000') & 
                        (loc_codes['District Code']=='000') &
                        (loc_codes['State Code']!='00')
                        ]
state_codes.drop_duplicates(subset='State Code', inplace=True)
district_codes = loc_codes[(loc_codes['Sub District Code']== '00000') & 
                        (loc_codes['District Code']!='000') &
                          (loc_codes['State Code']!='00')
                          ]
district_codes.drop_duplicates(subset='District Code', inplace=True)


# Define state name, given the state code provided in globals.py
state_name = state_codes.loc[state_codes['State Code'] == state_code, 'Name'].item()
state_snake = snake_case(state_name)


# Read in shapefile
states = gpd.read_file(boundaries_state)
districts = gpd.read_file(boundaries_district)

# Create shapefile of specified State
# state_shp = states[states["NAME_1"] == state_name]
districts_shp = districts[districts['pc11_s_id'] == state_code]          # 2023-07-12 Have changed input file to SHRUG source. Includes census coding, unlike GADM. 

# Export shapefiles
# if not os.path.isfile(state_filepath):
#   state_shp.to_file(state_filepath, mode="w")
if not os.path.isfile(districts_filepath):
  districts_shp.to_file(districts_filepath, mode="w")



# Filter Age, Rural/Urban status, and Gender
ag_main_cln = census_ag_main[(census_ag_main['Age group'] == 'Total') & (census_ag_main['Total Rural Urban'] == tru_cat)]
ag_main_cln = ag_main_cln[['State code', 'District code', 'Area name',
       'Total Rural Urban', 'Age group', 'Main workers P'
    #    , 'Main workers M', 'Main workers F'
    , 'Cultivators P'
    # , 'Cultivators M', 'Cultivators F'
    ,  'Agricultural labourers P'
    # , 'Agricultural labourers M', 'Agricultural labourers F'
    , 'Primary sector other P'
    #   , 'Primary sector other M', 'Primary sector other F'
       ]]
ag_marginal_cln = census_ag_marginal[(census_ag_marginal['Age group'] == 'Total') & (census_ag_marginal['Total Rural Urban'] == tru_cat)]
ag_marginal_cln = ag_marginal_cln[['District code', 'marginal_6m_p'
                                # , 'marginal_6m_m', 'marginal_6m_f' 
                                  , 'marginal_3m_p'
                                # , 'marginal_3m_m', 'marginal_3m_f'
                                  , 'Cultivators P'
                                # , 'Cultivators M', 'Cultivators F'
                                  , 'Agricultural labourers P'
                                # , 'Agricultural labourers M', 'Agricultural labourers F'
                                  , 'Primary sector other P'
                                # , 'Primary sector other M', 'Primary sector other F'
                                ]]

# Filter Total Population df
census_pop_cln = census_pop[(census_pop['Total Rural Urban'] == tru_cat) & 
                            (census_pop['State Code'] == state_code) &
                            (census_pop['Sub District Code'] == '00000')
                            ]
census_pop_cln = census_pop_cln[['District Code', 'Population', 'Area sq km', 'Population per sq km']]
census_pop_cln.rename(columns={'District Code':'District code'}, inplace=True)
census_pop_cln = census_pop_cln.astype({'Population':'int64'},
                                       {'Population per sq km':'float64'})

# Join marginal file to main
ag_workers = ag_main_cln.merge(ag_marginal_cln, how='left', on='District code', suffixes=('_main','_marg'))


# Join census population file to main
ag_workers = ag_workers.merge(census_pop_cln, how='left', on='District code')



# ==================================================================================================================
# 3. CALCULATE ADP

# Method 1: Main workers only (strict crops)
ag_workers["ADP1"] = ag_workers["Cultivators P_main"] + ag_workers["Agricultural labourers P_main"]

# Method 2: Main workers only (all primary sector)
ag_workers["ADP2"] = ag_workers["Cultivators P_main"] + ag_workers["Agricultural labourers P_main"] + ag_workers["Primary sector other P_main"]

# Method 3: Main + marginal workers (strict crops)
ag_workers["ADP3"] = ag_workers["Cultivators P_main"] + ag_workers["Agricultural labourers P_main"] \
    + ag_workers["Cultivators P_marg"] + ag_workers["Agricultural labourers P_marg"]

# Method 4: Main + marginal workers (all primary sector)
ag_workers["ADP4"] = ag_workers["Cultivators P_main"] + ag_workers["Agricultural labourers P_main"] + ag_workers["Primary sector other P_main"] \
    + ag_workers["Cultivators P_marg"] + ag_workers["Agricultural labourers P_marg"] + ag_workers["Primary sector other P_marg"]

# Method 5: Workers proportional to population ratio (based off Method 3)
ag_workers["Total workers"] = ag_workers["Main workers P"] + ag_workers["marginal_6m_p"] + ag_workers["marginal_3m_p"]
ag_workers["ADP5"] = ag_workers["ADP3"] * (ag_workers["Population"]/ag_workers["Total workers"])

ag_workers

# Export cleaned census data
ag_workers.to_csv(agworkers_filepath, mode="w", index=False)








#*************************************************************************************************************************************
#                   SCRIPT 01C_PYTHONSUBSTITUTION.PY
#*************************************************************************************************************************************

# ==================================================================================================================

# DISSERTATION
# SECTION 01C: Python replacement of QGIS operations
#   This script is designed to replace the QGIS internal operations used for the initial project method. 

# Author: J Post

# ==================================================================================================================

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



#*************************************************************************************************************************************
#                   SCRIPT 02_PYTHONPROCESSES.PY
#*************************************************************************************************************************************


# ==================================================================================================================

# DISSERTATION
# SECTION 02: Python processing
#   This script picks up at the end of 01B, and uses the output from the first set of QGIS process.
#   This script is intended to be run in full as a single python file. 

# Author: J Post

# ==================================================================================================================

# ==================================================================================================================
# 1. LOAD DATA

# Read in the output files from script 01B: 
#   1. WorldPop points
#   2. Landcover (cropland)
#   3. GHSL rural polygons

time_11s = time.time()

if sfmt == '.shp':
        gdf_pop = gpd.read_file(pop_points)
        gdf_crops = gpd.read_file(cropland_poly_dissolved)
        gdf_ghsl = gpd.read_file(ghsl_poly_dissolved)
elif sfmt == '.feather':
        gdf_pop = gpd.read_feather(pop_points)
        gdf_crops = gpd.read_feather(cropland_poly_dissolved)
        gdf_ghsl = gpd.read_feather(ghsl_poly_dissolved)
    
districts_shp = gpd.read_file(districts_filepath)

ag_workers = pd.read_csv(agworkers_filepath
                         , dtype = {'State code':str, 'District code':str}
                         ) 

print('Input data files loaded.\n')
timestamp(time_11s)


# ==================================================================================================================
# 2. JOIN WORLDPOP POINTS TO LAND COVER POLYGONS

# ===========
# 2.1 Join WorldPop to GHSL rural areas
time_21s = time.time()

# Join points to GHSL
pop_points_rural = gdf_pop.sjoin(gdf_ghsl, how = 'inner', predicate='within')
pop_points_rural = pop_points_rural.drop(columns='index_right')

# Export the filtered rural population
# pop_points_rural.to_feather(pop_points_rural_path)    
print(f'Rural population points gdf created.\n')

timestamp(time_21s)

# pop_points_rural.plot(column='raster_value')
# plt.show()

# ===========
# 2.2 Join WorldPop to DynamicWorld cropland areas
time_22s = time.time()

# Join points to cropland
pop_joined_dw = gdf_pop.sjoin(gdf_crops, how='inner', predicate='within')
# pop_points_cropland = pop_joined_dw.loc[pop_joined_dw['cropland']==1]     # remove here because now filtered in script 01C
pop_points_cropland = pop_joined_dw.drop(columns='index_right')
pop_points_cropland.to_feather(pop_points_cropland_path)
print(f'Cropland population points gdf created and exported to {sfmt}.\n')

timestamp(time_22s)

# pop_points_cropland.plot(column='raster_value')
# plt.show()


# ==================================================================================================================
# 3. CALCULATE DISTRICT LEVEL POPULATION

# Next steps:
# 1.    Break down state counts (Karnataka) into districts -> Need to decide if this is necessary? What is the most accurate?
# 2.    Sum point population estimates by district, to get a total district population estimate from WorldPop
# 3.    Sum rural point population estimates by district, to get a rural district population estimate from WorldPop
# 4.    Sum cropland point population estimates by district, to get a cropland population district estimate from WorldPop
# 5.    Sum rural-crop point population estimates by district, to get final ADP estimate -> Will this be any different than value in Step (4)?


# ===========
# 3.1 Join census agworkers to district boundaries
time_31s = time.time()

ag_workers_jn = districts_shp.merge(ag_workers, how='left', left_on='pc11_d_id', right_on='District code', sort=True
                                #    , indicator=True, validate='one_to_many'       # Creates a '_merge' column, for quality checking
                                   )
ag_workers_jn.head()

print('Census ADP counts joined to district boundaries.\n')
timestamp(time_31s)


# ===========
# 3.2 Join WorldPop points to district boundaries
time_32s = time.time()

# This joins the attributes of the points to the polygons they fall within
pop_jn_districts = gdf_pop.sjoin(districts_shp, how='inner', predicate='within')

# Dissolve points to calculate aggregated population for district
dissolve_df = pop_jn_districts[['raster_value', 'geometry', 'pc11_d_id', 'd_name']]
sum_pop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'raster_value':'sum',
                                                                                    'd_name':'first'})
sum_pop_districts['raster_value'] = sum_pop_districts['raster_value'].round()         # remove unnecessary decimals

# Export the worldpop points by district
sum_pop_districts.to_feather(sum_pop_districts_path)  

print(f'Pop points joined to district boundaries and exported to {sfmt}.\n')
timestamp(time_32s)


# ===========
# 3.3 Join WorldPop RURAL points to district boundaries
time_33s = time.time()

# This joins the attributes of the points to the polygons they fall within
rupop_jn_districts = pop_points_rural.sjoin(districts_shp, how='inner', predicate='within')

# Dissolve points to calculate aggregated population for district
dissolve_df = rupop_jn_districts[['raster_value', 'geometry', 'pc11_d_id', 'd_name']]
sum_rupop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'raster_value':'sum',
                                                                                      'd_name':'first'})
sum_rupop_districts['raster_value'] = sum_rupop_districts['raster_value'].round()

# Export the rural points by district
sum_rupop_districts.to_feather(sum_rupop_districts_path)  

print(f'Rural pop points joined to district boundaries and export to {sfmt}.\n')
timestamp(time_33s)

# ===========
# 3.4 Join WorldPop CROPLAND points to district boundaries
time_34s = time.time()

# This joins the attributes of the points to the polygons they fall within
crpop_jn_districts = pop_points_cropland.sjoin(districts_shp, how='inner', predicate='within')

# Dissolve points to calculate aggregated population for district
dissolve_df = crpop_jn_districts[['raster_value', 'geometry', 'pc11_d_id', 'd_name']]
sum_crpop_districts = dissolve_df.dissolve(by = 'pc11_d_id', as_index=False, aggfunc={'raster_value':'sum',
                                                                                      'd_name':'first'})
sum_crpop_districts['raster_value'] = sum_crpop_districts['raster_value'].round()

# Export the cropland points by district
sum_crpop_districts.to_feather(sum_crpop_districts_path)  

print(f'Cropland pop points joined to district boundaries and exported to {sfmt}.\n')
timestamp(time_34s)


# ==================================================================================================================
# 4. COLLATE OUTPUT INTO SINGLE GEODATAFRAME

# Input files:
#   1. Census population counts by district
#   2. Census agricultural workers by district  >>> use combo of first 2 to calculate Ag Workers Density (per km2)
#   3. WorldPop (all points) aggregated count by district
#   4. WorldPop (rural points) aggregated count by district
#   5. WorldPop (cropland points) aggregated count by district

masterdf = ag_workers_jn[['pc11_s_id', 'pc11_d_id', 'd_name', 'geometry', 'District code',
                                'Population', 'Area sq km', 'Population per sq km', 
                                'ADP1', 'ADP2', 'ADP3', 'ADP4', 'Total workers', 'ADP5']]

join_worldpop_all = sum_pop_districts[['pc11_d_id', 'raster_value']]
join_worldpop_all = join_worldpop_all.rename(columns={'raster_value':'worldpop'})
masterdf = masterdf.merge(join_worldpop_all, how='left', on=['pc11_d_id'])

join_worldpop_rural = sum_rupop_districts[['pc11_d_id', 'raster_value']]
join_worldpop_rural = join_worldpop_rural.rename(columns={'raster_value':'worldpop_rural'})
masterdf = masterdf.merge(join_worldpop_rural, how='left', on=['pc11_d_id'])

join_worldpop_crop = sum_crpop_districts[['pc11_d_id', 'raster_value']]
join_worldpop_crop = join_worldpop_crop.rename(columns={'raster_value':'worldpop_crop'})
masterdf = masterdf.merge(join_worldpop_crop, how='left', on=['pc11_d_id'])


# ==================================================================================================================
# 5. CALCULATE DIFFERENCE IN POPULATION ESTIMATES

# Columns to compute:
#   0. Difference between Worldpop total population and Census total population 
#   1. Difference between Worldpop cropland population and ADP1
#   2. Difference between Worldpop cropland population and ADP2
#   3. Difference between Worldpop cropland population and ADP3
#   4. Difference between Worldpop cropland population and ADP4
#   5. Difference between Worldpop cropland population and ADP5

# TODO: recalculate percentage changes to follow Sri Lanka method
#       1. Calculate the ADPc as a proportion of total population
#       2. Calculate the ADPa as a proportion of total population
#       3. Calculate the difference between [1] and [2]

# Calculate difference between Worldpop total population and Census total population
masterdf['d_poptotals'] = masterdf['worldpop'] - masterdf['Population']
masterdf['d_pc0'] = round(100 - masterdf['Population']/masterdf['worldpop']*100,2)

# NEW: 2023-08-07
masterdf['ADPa_pctotal'] = masterdf['worldpop_crop']/masterdf['Population']*100

# Calculate difference between Worldpop cropland population and ADP1
masterdf['ADPc1_pctotal'] = masterdf['ADP1']/masterdf['Population']*100
masterdf['d_pc1'] = masterdf['ADPc1_pctotal'] - masterdf['ADPa_pctotal']

# Calculate difference between Worldpop cropland population and ADP2
masterdf['ADPc2_pctotal'] = masterdf['ADP2']/masterdf['Population']*100
masterdf['d_pc2'] = masterdf['ADPc2_pctotal'] - masterdf['ADPa_pctotal']

# Calculate difference between Worldpop cropland population and ADP3
masterdf['ADPc3_pctotal'] = masterdf['ADP3']/masterdf['Population']*100
masterdf['d_pc3'] = masterdf['ADPc3_pctotal'] - masterdf['ADPa_pctotal']

# Calculate difference between Worldpop cropland population and ADP4
masterdf['ADPc4_pctotal'] = masterdf['ADP4']/masterdf['Population']*100
masterdf['d_pc4'] = masterdf['ADPc4_pctotal'] - masterdf['ADPa_pctotal']

# Calculate difference between Worldpop cropland population and ADP5
masterdf['ADPc5_pctotal'] = masterdf['ADP5']/masterdf['Population']*100
masterdf['d_pc5'] = masterdf['ADPc5_pctotal'] - masterdf['ADPa_pctotal']

# Calculate difference between ADPc5 and Rural population
#       If negative, then the estimated ADP surpasses entire rural population of district
masterdf['d_rural_adp'] = masterdf['worldpop_rural'] - masterdf['ADP5']

dlist = ['d_poptotals', 'd_pc1', 'd_pc2', 'd_pc3','d_pc4', 'd_pc5']

masterdf.drop(columns='geometry', inplace=True)

# masterdf.columns
masterdf.head()

# Add column to flag districts that need a buffer
# Use defined function with conditional rules: categorise_buffer

# Next apply conditional rows to each row of masterdf
if ADPcn == 'ADPc3':
        masterdf['need_buffer'] = masterdf.apply(lambda row: categorise_buffer(row, 'd_pc3'), axis=1)
elif ADPcn == 'ADPc5':
        masterdf['need_buffer'] = masterdf.apply(lambda row: categorise_buffer(row, 'd_pc5'), axis=1)


# Identify districts where the ADPc5 > worldpop_rural (more agricultural population than total rural population). 
#       or districts with no rural population (worldpop_rural = NaN)
masterdf["d_rural_adp"] = masterdf["d_rural_adp"].fillna(-999)
mask = (masterdf['d_rural_adp'] < 0)
masterdf['need_buffer'][mask] = 'ineligible'

# Remove ineligible districts and save in separate csv
ineligibledf = masterdf[masterdf['need_buffer'] == 'ineligible']
ineg_list = ineligibledf.index.values.tolist()
masterdf = masterdf.drop(index=ineg_list)

# Export masterdf to csv
masterdf.to_csv(masterdf_path, index=False)
ineligibledf.to_csv(ineligibledf_path, index=False)

print('Master results file exported to csv.\n')

# ==================================================================================================================
# 6. BUFFER ITERATION

# =====================
# 6.1 Define a function to create a buffer and recalculate the ADP estimate

# Where:
# 1. district_shp = districts_shp   
# 2. crops_shp = gdf_crops
# 3. rural_points = pop_points_rural
# 4. district_code = string format of district code
# 5. buffer_radius = set accordingly; default 50m
# 6. buffer_type = 'enlarge' or 'reduce'
def generate_buffer(districts_shp, crops_shp, rural_points, district_code, buffer_radius, buffer_type):
        time_buff = time.time()

        # Define district boundaries
        district_boundary = districts_shp.loc[districts_shp['pc11_d_id'] == district_code]
        crop_by_district_boundary = gpd.overlay(crops_shp, district_boundary, how='intersection')

        # Convert to a Geoseries
        district_series = crop_by_district_boundary['geometry']

        # Convert buffer metre input into degrees (WGS84)
        if buffer_type == 'enlarge':
                degrees = buffer_radius * (0.00001/1.11)
        elif buffer_type == 'subtract':
                buffer_radius = buffer_radius * -1              # negative buffer radius = reduction in size
                degrees = buffer_radius * (0.00001/1.11)       
        elif buffer_type == 'unchanged':
                degrees = 0                                     # No buffer required (type == 'unchanged')

        print('Creating ' + str(buffer_radius) + 'm buffers on crop lands for district: ' + district_code)  

        # Calculate buffer
        d_buffer = district_series.buffer(degrees)
        d_buffer.name = 'geometry'
        d_buffer_gdf = gpd.GeoDataFrame(d_buffer, crs="EPSG:4326", geometry='geometry')

        # Join rural points to buffer zone
        ru_points_buffer = rural_points.sjoin(d_buffer_gdf, how='inner', predicate='within')
        ru_points_buffer = ru_points_buffer.drop(columns='index_right')

        # Dissolve points to calculate aggregated population for district
        sum_buffer_points = ru_points_buffer.dissolve(as_index=False, aggfunc={'raster_value':'sum'})
        sum_buffer_points['raster_value'] = sum_buffer_points['raster_value'].round()

        # Add district code and buffer radius to geodataframe
        sum_buffer_points['pc11_d_id'] = district_code
        sum_buffer_points['buffer_r'] = buffer_radius

        print(f'Rural pop points joined to buffer area and new ADP calculated.')

        # Merge census data from masterdf
        if ADPcn == 'ADPc3':
                ADPcn_pctotal = 'ADPc3_pctotal'
        elif ADPcn == 'ADPc5':
                ADPcn_pctotal = 'ADPc5_pctotal'
        
        check_buffer = sum_buffer_points.merge(masterdf[['pc11_d_id', 'Population', ADPcn_pctotal, 'need_buffer']], how='left', on='pc11_d_id')

        check_buffer['buffered_pctotal'] = check_buffer['raster_value']/check_buffer['Population']*100
        check_buffer['d_bufferedpc'] = check_buffer[ADPcn_pctotal] - check_buffer['buffered_pctotal']

        # Next apply conditional rows to each row of masterdf
        check_buffer['revised_buffer'] = check_buffer.apply(lambda row: buffer_logic(row, 'need_buffer', 'd_bufferedpc'), axis=1)

        timestamp(time_buff)
        return check_buffer

# # TEST RUN
# sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, '583', 50, 'subtract')

# # TEST ZERO BUFFER
# sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, '582', 0, 'enlarge')

# # TEST INPUT 'UNCHANGED'
# sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, '582', 400, 'enlarge')


# =====================
# 6.2 Run function over set of districts and combine outputs into a single GeoDataframe
time_buffer = time.time()

# Create a dictionary of the districts
buffer_dict = dict(zip(masterdf['pc11_d_id'], masterdf['need_buffer']))

# TEST LOOP THROUGH DICTIONARY
# buffer_dict = {'572': 'subtract', '581': 'enlarge', '582': 'unchanged', '583': 'subtract', '584': 'enlarge'}



# Initialize a list to store individual GeoDataFrames
buffer_gdf_list = []

# 2. Run for loop (loop through each district)
for key, value in buffer_dict.items():
        buffer_radius = 50
        iteration_count = 0
        
        # Run initial buffer function 
        sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, key, buffer_radius, value)
        print('1st Run: District ' + key + ' value is ' + value + ' and result: ' + sum_buffer_gdf['revised_buffer'].item())
        print('d_bufferedpc: ' + str(round(sum_buffer_gdf['d_bufferedpc'].item(),2)))
        # 3. Run while loop (iterate over a single district until threshold is met)
        #       Iteration count is designed to present unseen errors from looping forever; buffer process will cut off after 5 runs
        while (abs(sum_buffer_gdf['d_bufferedpc'].item()) > 5) and (iteration_count <= 5):
                if value in ['unchanged', 'ineligible']:        # Ensures districts that are initially within threshold or are ineligible 
                        break                                   #  do not run through the buffer iteration process
                elif sum_buffer_gdf['revised_buffer'].item() in ['enlarge', 'subtract']:
                        buffer_radius = round(buffer_radius + (buffer_radius/2))
                        sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, key, buffer_radius, value)
                elif sum_buffer_gdf['revised_buffer'].item() == 'overenlarged': 
                        buffer_radius = round(buffer_radius - (buffer_radius/2))
                        sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, key, buffer_radius, 'enlarge')
                elif sum_buffer_gdf['revised_buffer'].item() == 'oversubtracted': 
                        buffer_radius = round(buffer_radius - (buffer_radius/2))
                        sum_buffer_gdf = generate_buffer(districts_shp, gdf_crops, pop_points_rural, key, buffer_radius, 'subtract')
                
                print('District ' + key + ' value is ' + value + ' and result: ' + sum_buffer_gdf['revised_buffer'].item())
                print('d_bufferedpc: ' + str(round(sum_buffer_gdf['d_bufferedpc'].item(),2)))
                iteration_count = iteration_count + 1

        # Append the single-row GeoDataFrame to the list
        buffer_gdf_list.append(sum_buffer_gdf)
        print('*** District ' + key + ' complete. ***\n Iterations: ' + str(iteration_count) + '\n')

timestamp(time_buffer)

# Concatenate all GeoDataFrames in the list
buffer_gdf = pd.concat(buffer_gdf_list)
# Drop duplicates based on 'pc11_d_id'
# buffer_gdf.drop_duplicates(subset='pc11_d_id', inplace=True)
# Reset index
buffer_gdf.reset_index(drop=True, inplace=True)
# Display the final GeoDataFrame
print(buffer_gdf)


# Export buffer_gdf to .feather
buffer_gdf.to_feather(buffergdf_path)

# Export buffer_df to csv
buffer_df = pd.DataFrame(buffer_gdf.drop(columns = 'geometry'))
buffer_df.to_csv(bufferdf_path, index=False)


# Join buffer radius values to district polygons
buffer_map = districts_shp.merge(buffer_df, on='pc11_d_id')

# Export buffer map to .shp (for QGIS mapping)
buffer_map.to_file(buffermap_path)


print('\nScript 04_combinedscript.py complete.\n')
timestamp(start_time)


