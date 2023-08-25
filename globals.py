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
from re import sub


# ********************************************
# TODO: 
# 1. Set directory depending on user
repository = 'C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp' 

# 2. Set spatial scale for raster imports (DynamicWorld, WorldPop)
scale = '1km'
# scale = '100m'

# 3. Set state (or list of states) to work with 
state_code = '29'             # code taken from Census India

# 4. Set desired GHSL model to be used
ghsl_model = 'smod_e2030_1000'      #GHSL Settlement Model Grid,    R2023, Epoch 2030, 1km,     Mollweide
# ghsl_model = 'built_E2030_100'    #GHSL Built-up Surface,         R2023, Epoch 2030, 100m,    Mollweide

# 5. Set desired Worldpop model to be used
worldpop_model = 'Aggregated_UNadj'     # Population count, Top-down estimation, unconstrained, adjusted to match UN estimates 
# worldpop_model = 'Aggregated'         # Population count, Top-down estimation, unconstrained

# 6. Set output spatial file format
# sfmt = '.shp'      # shapefile
sfmt = '.feather'    # geofeather

# 7. Set whether to use Total, Rural or Urban counts from census population tables
tru_cat = 'Total'                   # Preference for using TOTAL count, due to disjunction between census and DW classifications of 'rural'
# tru_cat = 'Rural'
# tru_cat = 'Urban'

# 8. Set ADP definition for further analysis 
# ADPcn = 'ADPc3'
ADPcn = 'ADPc5'

# 9. Set maximum number of iterations for buffer process
iteration_max = 10
# ********************************************


# ==================================================================================================================
# FUNCTIONS

# Print the elapsed computation time of a section of code
def timestamp(initial_time):
    end_time = time.time()
    elapsed_time = end_time - initial_time
    if elapsed_time > 60:
        print('Elapsed time: ', round(elapsed_time/60, 1), ' minutes.\n')
    else:
        print('Elapsed time: ', round(elapsed_time, 1), ' seconds.\n')

# Convert a string into snake case (used for conversion of state names)
def snake_case(s):
  return '_'.join(
    sub('([A-Z][a-z]+)', r' \1',
    sub('([A-Z]+)', r' \1',
    s.replace('-', ' '))).split()).lower()

# For the initial classification of ADP results, categorise districts on whether a buffer is required, and in which direction
def categorise_buffer(row, column):
    if row[column] < -5:
        return 'subtract'
    elif row[column] > 5:
           return 'enlarge'
    else:
        return 'unchanged'

# For the iterative buffer process, classify if districts need:
def buffer_logic(row, need_buffer, revised_diff): 
    if row[need_buffer] == 'enlarge':
        if row[revised_diff] > 5:           #   1. To enlarge the buffer further (ADPa still too low)
            return 'enlarge'
        elif row[revised_diff] < -5:        #   2. To enlarge using a smaller buffer radius (revised ADPa too high)
            return 'overenlarged'
        else:
            return 'unchanged'
    elif row[need_buffer] == 'subtract':   #   3. To subtract the buffer further (ADPa still too high)
         if row[revised_diff] > 5:
            return 'oversubtracted'
         elif row[revised_diff] < -5:       #   4. To subtract using a smaller buffer radius (revised ADPa too low)
            return 'subtract'
         else:
            return 'unchanged'
    elif row[need_buffer] == 'unchanged':
        if row[revised_diff] > 5:           
            return 'enlarge'
        if row[revised_diff] < -5:
            return 'subtract'
        else:
            return 'unchanged'
    else:
        return 'unchanged'                  #   5. To complete the buffer iteration process (5% threshold reached)
  

# ==================================================================================================================
# FILE PATHS

# Working directories
datafolder = os.path.join(repository,'Data')
outputfolder = os.path.join(repository,'Output', scale)        # if needing to split folders by state: , f'{scale}_{state_code}_{state_snake}'
outputfinal = os.path.join(outputfolder, 'final')
outputintermediates = os.path.join(outputfolder, 'intermediates')

# Subfolders list
data_subfolders = ['boundaries', 'census', 'dynamicworld', 'ghsl', 'worldpop']
output_subfolders = ['100m', '1km']
output_scale_subfolders = ['intermediates', 'final']
final_subfolders = ['tables', 'figures', 'spatial_files']
intermediate_subfolders = ['boundaries_district', 'boundaries_state', 'census', 'dynamicworld', 'ghsl', 'worldpop']


# Input files
boundaries_national =   os.path.join(datafolder, 'boundaries', 'gadm41_IND_0.shp')                          # GADM India boundaries shapefile
boundaries_state =      os.path.join(datafolder, 'boundaries', 'gadm41_IND_1.shp')                          # GADM India boundaries shapefile
boundaries_district =   os.path.join(datafolder, 'boundaries', 'district.shp' )                         # GADM India boundaries shapefile
locationcodes =         os.path.join(datafolder, 'census', 'CensusIndia2011_LocationDirectory.csv')         # State and district names and codes from Census
# pop_tif =               os.path.join(datafolder, 'worldpop', f'ind_ppp_2011_{scale}_{worldpop_model}.tif')  # WorldPop UN adjusted 1km 2011 (adjust as necessary)
# NOTE: CURRENT TRIAL = 100m CROPLAND; 1km POPULATION. NOT COMPUTATIONALLY FEASIBLE TO USE 100m POP POINTS DATA. 
pop_tif =               os.path.join(datafolder, 'worldpop', f'ind_ppp_2011_100m_{worldpop_model}.tif')  # WorldPop UN adjusted 1km 2011 (adjust as necessary)
cropland =              os.path.join(datafolder, 'dynamicworld', f'2020_dw_{state_code}_cropland_{scale}.tif') # DynamicWorld extracted from GEE
agworkers_main =        os.path.join(datafolder, 'census', f'DDW-B04-{state_code}00.xls')              # Census B-04 = Main workers tables
agworkers_marginal =    os.path.join(datafolder, 'census', f'DDW-B06-{state_code}00.xls')              # Census B-06 = Marginal workers tables
census_population =     os.path.join(datafolder, 'census', 'CensusIndia2011_A-1_NO_OF_VILLAGES_TOWNS_HOUSEHOLDS_POPULATION_AND_AREA.xlsx')   # Census A-01 = district populations


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
ghsl_poly_dissolved =   os.path.join(outputfolder, 'intermediates', 'ghsl', f'ghsl_{state_code}_vector_dissolved{sfmt}')
ghsl_poly_shp =         os.path.join(outputfolder, 'intermediates', 'ghsl', f'ghsl_{state_code}_vector_dissolved.shp')
rural_area_path =       os.path.join(outputfolder, 'intermediates', 'ghsl', f'rural_{state_code}_area.csv')

state_filepath =     os.path.join(outputfolder, 'intermediates', 'boundaries_state', f'state_{state_code}.shp')         
districts_filepath = os.path.join(outputfolder, 'intermediates', 'boundaries_district', f'districts_{state_code}.shp')

agworkers_filepath =        os.path.join(outputfolder, 'intermediates', 'census', f'agworkers_{state_code}_{tru_cat}.csv')

cropland_poly_dissolved =   os.path.join(outputfolder, 'intermediates', 'dynamicworld', f'cropland_vector_{state_code}_dissolved{sfmt}')
cropland_area_path =        os.path.join(outputfolder, 'intermediates', 'dynamicworld', f'cropland_{state_code}_area.csv')

pop_tif_clipped =           os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_tif_{state_code}_clipped.tif')
pop_points =                os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points_{state_code}{sfmt}')
pop_points_rural_path =     os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points_{state_code}_rural{sfmt}')
pop_points_cropland_path =  os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points_{state_code}_cropland{sfmt}')

sum_pop_districts_path =    os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points_{state_code}_bydistrict{sfmt}')
sum_rupop_districts_path =  os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points_{state_code}_rural_bydistrict{sfmt}')
sum_crpop_districts_path =  os.path.join(outputfolder, 'intermediates', 'worldpop', f'pop_points_{state_code}_cropland_bydistrict{sfmt}')

# Output files
# These file paths store the final output files used in the Results section
masterdf_path =             os.path.join(outputfolder, 'final', 'tables', f'masterdf_{state_code}_{tru_cat}_{ADPcn}.csv')
ineligibledf_path =         os.path.join(outputfolder, 'final', 'tables', f'ineligibledf_{state_code}_{tru_cat}_{ADPcn}.csv')
ineligiblecombined_path =   os.path.join(outputfolder, 'final', 'tables', f'ineligibledf_COMBINED_{tru_cat}_{ADPcn}.csv')

buffergdf_path =        os.path.join(outputfolder, 'final', 'spatial_files', f'bufferdf_{state_code}_{tru_cat}_{ADPcn}{sfmt}')
buffer_poly_path =      os.path.join(outputfolder, 'final', 'spatial_files', f'buffer_polygon_{state_code}_{tru_cat}_{ADPcn}.shp')
bufferdf_path =         os.path.join(outputfolder, 'final', 'tables', f'bufferdf_{state_code}_{tru_cat}_{ADPcn}.csv')
buffermap_path =        os.path.join(outputfolder, 'final', 'spatial_files', f'bufferdf_{state_code}_{tru_cat}_{ADPcn}.shp')
buffercombined_path =   os.path.join(outputfolder, 'final', 'tables', f'bufferdf_COMBINED_{tru_cat}_{ADPcn}.csv')
buffercombined_map =    os.path.join(outputfolder, 'final', 'spatial_files', f'bufferdf_COMBINED_{tru_cat}_{ADPcn}.shp')

pop_tif_buffer_mask =   os.path.join(outputfolder, 'final', 'spatial_files', f'adptif_{state_code}_{tru_cat}_{ADPcn}.tif')
pop_tif_final =         os.path.join(outputfolder, 'final', 'spatial_files', f'adpfinal_{state_code}_{tru_cat}_{ADPcn}.tif')

# Figures
bplot_adp = os.path.join(outputfolder, 'final', 'figures', f'bplot_adp_{state_code}_{tru_cat}.png')
pointplot_adp = os.path.join(outputfolder, 'final', 'figures', f'pointplot_adp_{state_code}_{tru_cat}.png')

