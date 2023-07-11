# ==================================================================================================================

# DISSERTATION
# SECTION 00: Globals
#   This script contains the input and output file paths to be used in the main python scripts.

# Author: Joe Post
# Developed from F Lopane, S Ayling Sri Lanka Tanks project
# [ADD GITHUB LINK]

# ==================================================================================================================

import os
import glob

# ********************************************
# TODO: 
# 1. Set directory depending on user
repository = 'C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp' 

# 2. Set spatial scale for raster imports (DynamicWorld, WorldPop)
scale = '1km'
# scale = '100m'

# 3. Set flag for working with single state or whole of India
# [TO BE DONE]

# 4. Set desired GHSL model to be used
ghsl_model = 'smod_e2030_1000'      #GHSL Settlement Model Grid,    R2023, Epoch 2030, 1km,     Mollweide
# ghsl_model = 'built_E2030_100'    #GHSL Built-up Surface,         R2023, Epoch 2030, 100m,    Mollweide

# 5. Set desired Worldpop model to be used
worldpop_model = 'Aggregated_UNadj'     # Population count, Top-down estimation, unconstrained, adjusted to match UN estimates 
# worldpop_model = 'Aggregated'         # Population count, Top-down estimation, unconstrained
# ********************************************


# Working directories
datafolder = os.path.join(repository,'Data')
outputfolder = os.path.join(repository,'Output')

# Subfolders list
data_subfolders = ['boundaries', 'census', 'dynamicworld', 'ghsl', 'worldpop']
output_subfolders = ['boundaries_district', 'boundaries_state', 'dynamicworld', 'ghsl', 'worldpop']


# Input files
boundaries_national =   os.path.join(datafolder, 'boundaries', 'gadm41_IND_0.shp')                          # GADM India boundaries shapefile
boundaries_state =      os.path.join(datafolder, 'boundaries', 'gadm41_IND_1.shp')                          # GADM India boundaries shapefile
boundaries_district =   os.path.join(datafolder, 'boundaries', 'gadm41_IND_2.shp' )                         # GADM India boundaries shapefile
boundaries_subdist =    os.path.join(datafolder, 'boundaries', 'gadm41_IND_3.shp')                          # GADM India boundaries shapefile
locationcodes =         os.path.join(datafolder, 'census', 'CensusIndia2011_LocationDirectory.csv')         # State and district names and codes from Census
pop_tif =               os.path.join(datafolder, 'worldpop', f'ind_ppp_2011_{scale}_{worldpop_model}.tif')  # WorldPop UN adjusted 1km 2011 (adjust as necessary)
cropland =              os.path.join(datafolder, 'dynamicworld', f'2020_dw_karnataka_cropland_{scale}.tif') # DynamicWorld extracted from GEE


# Census statistics 
# Currently, this file loads just the data for the test state Karnataka (State Code 29).
# The file has been cleaned from the website download into a readable csv table.
agworkers_29 =          os.path.join(datafolder, 'census', 'CensusIndia2011_IndustrialCategory_Karnataka_DDW-B04-2900_cln.csv')


# GHSL component files
# Selected files cover India 
# creates a list containing all the files in folder that match criteria
ghslfolder = os.path.join(datafolder, 'ghsl', ghsl_model)     
ghsl_to_merge = glob.glob(os.path.join(ghslfolder, '*.tif'))    


# Generated files
# These file paths store intermediate files generated during the analysis
ghsl_merged =           os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india.tif')
ghsl_merged_wgs84 =     os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_wgs84.tif')         # CRS reprojected to WGS84
ghsl_poly =             os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_vector.shp')        # GHSL converted to shapefile (vector)
ghsl_poly_fixed =       os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_vector_fixed.shp')  # Shapefile with fixed geometries
ghsl_india_clipped =    os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_vector_clipped.shp')

state_29_filepath =     os.path.join(outputfolder, 'intermediates', 'boundaries_state', 'state_29.shp')         # Specific to Karnataka, for test run through
districts_29_filepath = os.path.join(outputfolder, 'intermediates', 'boundaries_district', 'districts_29.shp')
ghsl_29_clipped =       os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_29_clipped.tif')

cropland_poly =             os.path.join(outputfolder, 'intermediates', 'dynamicworld', 'cropland_vector.shp')
cropland_poly_fixed =       os.path.join(outputfolder, 'intermediates', 'dynamicworld', 'cropland_vector_fixed.shp')
cropland_poly_clipped =     os.path.join(outputfolder, 'intermediates', 'dynamicworld', 'cropland_vector_clipped.shp')
cropland_poly_dissolved =   os.path.join(outputfolder, 'intermediates', 'dynamicworld', 'cropland_vector_dissolved.shp')

pop_points =            os.path.join(outputfolder, 'intermediates', 'worldpop', 'pop_points.shp')
pop_points_clipped =    os.path.join(outputfolder, 'intermediates', 'worldpop', 'pop_points_clipped.shp')
pop_joined_ghsl =       os.path.join(outputfolder, 'intermediates', 'worldpop', 'pop_points_ghsl_shp.shp')  # joined shapefile of WorldPop + GHSL
pop_points_rural_path = os.path.join(outputfolder, 'intermediates', 'worldpop', 'pop_points_rural.shp')


# Output files
# These file paths store the final output files used in the Results section


