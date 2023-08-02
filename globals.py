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
import time

# ********************************************
# TODO: 
# 1. Set directory depending on user
repository = 'C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp' 

# 2. Set spatial scale for raster imports (DynamicWorld, WorldPop)
scale = '1km'
# scale = '100m'

# 3. Set state (or list of states) to work with 
# state_name = 'Karnataka'    
# state_snake = 'karnataka'   # snake case
# state_code = 29             # code taken from Census India

state_name = 'Kerala'    
state_snake = 'kerala'   # snake case
state_code = 32             # code taken from Census India

# 4. Set desired GHSL model to be used
ghsl_model = 'smod_e2030_1000'      #GHSL Settlement Model Grid,    R2023, Epoch 2030, 1km,     Mollweide
# ghsl_model = 'built_E2030_100'    #GHSL Built-up Surface,         R2023, Epoch 2030, 100m,    Mollweide

# 5. Set desired Worldpop model to be used
worldpop_model = 'Aggregated_UNadj'     # Population count, Top-down estimation, unconstrained, adjusted to match UN estimates 
# worldpop_model = 'Aggregated'         # Population count, Top-down estimation, unconstrained

# 6. Set output spatial file format
# sfmt = '.shp'      # shapefile
sfmt = '.feather'    # geofeather
# ********************************************


# Working directories
datafolder = os.path.join(repository,'Data')
outputfolder = os.path.join(repository,'Output', f'{scale}_{state_code}_{state_snake}')
outputfinal = os.path.join(outputfolder, 'final')
outputintermediates = os.path.join(outputfolder, 'intermediates')

# Subfolders list
data_subfolders = ['boundaries', 'census', 'dynamicworld', 'ghsl', 'worldpop']
output_subfolders = ['intermediates', 'final']
final_subfolders = ['tables', 'figures', 'spatial_files']
intermediate_subfolders = ['boundaries_district', 'boundaries_state', 'census', 'dynamicworld', 'ghsl', 'worldpop']


# Input files
# boundaries_national =   os.path.join(datafolder, 'boundaries', 'gadm41_IND_0.shp')                          # GADM India boundaries shapefile
boundaries_state =      os.path.join(datafolder, 'boundaries', 'gadm41_IND_1.shp')                          # GADM India boundaries shapefile
boundaries_district =   os.path.join(datafolder, 'boundaries', 'district.shp' )                         # GADM India boundaries shapefile
# boundaries_subdist =    os.path.join(datafolder, 'boundaries', 'gadm41_IND_3.shp')                          # GADM India boundaries shapefile
locationcodes =         os.path.join(datafolder, 'census', 'CensusIndia2011_LocationDirectory.csv')         # State and district names and codes from Census
pop_tif =               os.path.join(datafolder, 'worldpop', f'ind_ppp_2011_{scale}_{worldpop_model}.tif')  # WorldPop UN adjusted 1km 2011 (adjust as necessary)
cropland =              os.path.join(datafolder, 'dynamicworld', f'2020_dw_{state_snake}_cropland_{scale}.tif') # DynamicWorld extracted from GEE

# Census statistics 
# The file has been cleaned from the website download into a readable csv table.
agworkers_main =         os.path.join(datafolder, 'census', f'DDW-B04-{state_code}00.xls')          # B-04 = Main workers tables
agworkers_marginal =     os.path.join(datafolder, 'census', f'DDW-B06-{state_code}00.xls')          # B-06 = Marginal workers tables
census_population =      os.path.join(datafolder, 'census', 'CensusIndia2011_A-1_Population_cln.csv')


# GHSL component files
# Selected files cover India 
# creates a list containing all the files in folder that match criteria
ghslfolder = os.path.join(datafolder, 'ghsl', ghsl_model)     
ghsl_to_merge = glob.glob(os.path.join(ghslfolder, '*.tif'))    


# Generated files
# These file paths store intermediate files generated during the analysis
ghsl_merged =           os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india.tif')
ghsl_merged_wgs84 =     os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_wgs84.tif')         # CRS reprojected to WGS84
ghsl_clipped =          os.path.join(outputfolder, 'intermediates', 'ghsl', f'ghsl_{state_code}_clipped.tif')
# ghsl_poly =             os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_vector.shp')        # GHSL converted to shapefile (vector)
# ghsl_poly_fixed =       os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_vector_fixed.shp')  # Shapefile with fixed geometries
# ghsl_india_clipped =    os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_vector_clipped.shp')
ghsl_poly_dissolved =       os.path.join(outputfolder, 'intermediates', 'ghsl', f'ghsl_india_vector_dissolved{sfmt}')

# state_29_filepath =     os.path.join(outputfolder, 'intermediates', 'boundaries_state', 'state_29.shp')         # Specific to Karnataka, for test run through
# districts_29_filepath = os.path.join(outputfolder, 'intermediates', 'boundaries_district', 'districts_29.shp')
# ghsl_29_clipped =       os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_29_clipped.tif')

state_filepath =     os.path.join(outputfolder, 'intermediates', 'boundaries_state', f'state_{state_code}.shp')         
districts_filepath = os.path.join(outputfolder, 'intermediates', 'boundaries_district', f'districts_{state_code}.shp')

agworkers_filepath =        os.path.join(outputfolder, 'intermediates', 'census', 'agworkers.csv')
# agworkers_jn_filepath =     os.path.join(outputfolder, 'intermediates', 'census', 'agworkers_jn.shp')
# agworkers_jn_filepath_t =   os.path.join(outputfolder, 'intermediates', 'census', 'agworkers_jn_t.shp')
# agworkers_jn_filepath_r =   os.path.join(outputfolder, 'intermediates', 'census', 'agworkers_jn_r.shp')
# agworkers_jn_filepath_u =   os.path.join(outputfolder, 'intermediates', 'census', 'agworkers_jn_u.shp')

# census_jn_filepath =        os.path.join(outputfolder, 'intermediates', 'census', 'census_jn.shp')
# census_jn_filepath_t =        os.path.join(outputfolder, 'intermediates', 'census', 'census_jn_t.shp')
# census_jn_filepath_r =        os.path.join(outputfolder, 'intermediates', 'census', 'census_jn_r.shp')
# census_jn_filepath_u =        os.path.join(outputfolder, 'intermediates', 'census', 'census_jn_u.shp')

# cropland_poly =             os.path.join(outputfolder, 'intermediates', 'dynamicworld', 'cropland_vector.shp')
# cropland_poly =             os.path.join(outputfolder, 'intermediates', 'dynamicworld', 'cropland_vector.gpkg')
# cropland_poly_fixed =       os.path.join(outputfolder, 'intermediates', 'dynamicworld', 'cropland_vector_fixed.gpkg')
# cropland_poly_clipped =     os.path.join(outputfolder, 'intermediates', 'dynamicworld', 'cropland_vector_clipped.gpkg')
cropland_poly_dissolved =   os.path.join(outputfolder, 'intermediates', 'dynamicworld', f'cropland_vector_dissolved{sfmt}')

pop_tif_clipped =           os.path.join(outputfolder, 'intermediates', 'worldpop', 'pop_tif_clipped.tif')
pop_points =                os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points{sfmt}')
# pop_points_gpkg =           os.path.join(outputfolder, 'intermediates', 'worldpop', 'pop_points.gpkg')
# pop_points_clipped =        os.path.join(outputfolder, 'intermediates', 'worldpop', 'pop_points_clipped.shp')
pop_joined_ghsl =           os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points_ghsl_shp{sfmt}')  # joined shapefile of WorldPop + GHSL
pop_points_rural_path =     os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points_rural{sfmt}')
pop_points_cropland_path =  os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points_cropland{sfmt}')
# pop_jn_district_path =      os.path.join(outputfolder, 'intermediates', 'worldpop', 'pop_jn_district.shp')
# rupop_jn_district_path =    os.path.join(outputfolder, 'intermediates', 'worldpop', 'rupop_jn_district.shp')
# crpop_jn_district_path =    os.path.join(outputfolder, 'intermediates', 'worldpop', 'crpop_jn_district.shp')


# Output files
# These file paths store the final output files used in the Results section
masterdf_path =      os.path.join(outputfolder, 'final', 'tables', 'masterdf.csv')
bplot_adp = os.path.join(outputfolder, 'final', 'figures', f'bplot_adp_{state_code}.png')

# ==================================================================================================================
# FUNCTIONS

def timestamp(initial_time):
    end_time = time.time()
    elapsed_time = end_time - initial_time
    if elapsed_time > 60:
        print('Elapsed time: ', round(elapsed_time/60, 1), ' minutes.\n')
    else:
        print('Elapsed time: ', round(elapsed_time, 1), ' seconds.\n')

