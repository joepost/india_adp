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


# Working directories
repository = 'C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp'     # Update as necessary depending on user
datafolder = os.path.join(repository,'Data')
outputfolder = os.path.join(repository,'Output')


# Input files
boundaries_national =   os.path.join(datafolder, 'boundaries', 'gadm41_IND_0.shp')                        # GADM India boundaries shapefile
boundaries_state =      os.path.join(datafolder, 'boundaries', 'gadm41_IND_1.shp')                        # GADM India boundaries shapefile
boundaries_district =   os.path.join(datafolder, 'boundaries', 'gadm41_IND_2.shp' )                       # GADM India boundaries shapefile
boundaries_subdist =    os.path.join(datafolder, 'boundaries', 'gadm41_IND_3.shp')                        # GADM India boundaries shapefile
locationcodes =         os.path.join(datafolder, 'census', 'CensusIndia2011_LocationDirectory.csv')       # State and district names and codes from Census
pop_tif =               os.path.join(datafolder, 'worldpop', 'ind_ppp_2011_1km_Aggregated_UNadj.tif')     # WorldPop UN adjusted 1km 2011 (adjust as necessary)
agland =                os.path.join(datafolder, 'dynamicworld', '2020_dw_karnataka_cropland.tif')        # DynamicWorld extracted from GEE


# Census statistics 
# Currently, this file loads just the data for the test state Karnataka (State Code 29).
# The file has been cleaned from the website download into a readable csv table.
agworkers_29 =          os.path.join(datafolder, 'census', 'CensusIndia2011_IndustrialCategory_Karnataka_DDW-B04-2900_cln.csv')


# GHSL component files
# Selected files cover India 
# creates a list containing all the files in folder that match criteria
# ********
# TODO: Specify desired GHSL folder (depending on product, scale, projection). Comment out alternatives. 
ghslfolder = os.path.join(datafolder, 'ghsl', 'smod_e2030_1000')     #GHSL Settlement Model Grid,    R2023, Epoch 2030, 1km,     Mollweide
# ghslfolder = os.path.join(datafolder, 'ghsl', 'built_E2030_100')   #GHSL Built-up Surface,         R2023, Epoch 2030, 100m,    Mollweide
# ********
ghsl_to_merge = glob.glob(os.path.join(ghslfolder, '*.tif'))    


# Generated files
# These file paths store intermediate files generated during the analysis
ghsl_merged =           os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india.tif')
ghsl_merged_wgs84 =     os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_wgs84.tif')         # CRS reprojected to WGS84
ghsl_poly =             os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_vector.shp')        # GHSL converted to shapefile (vector)
ghsl_poly_fixed =       os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_vector_fixed.shp')  # Shapefile with fixed geometries
ghsl_india_clipped =    os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_india_vector_clipped.shp')

state_29_filepath =     os.path.join(outputfolder, 'intermediates', 'boundaries_state', 'state_29.shp')
districts_29_filepath = os.path.join(outputfolder, 'intermediates', 'boundaries_district', 'districts_29.shp')
ghsl_29_clipped =       os.path.join(outputfolder, 'intermediates', 'ghsl', 'ghsl_29_clipped.tif')



# Output files
# These file paths store the final output files used in the Results section


