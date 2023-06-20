# ==================================================================================================================

# DISSERTATION
# SECTION 01: Prepare Files
# Date: 2023-06-19
# Author: J Post

# ==================================================================================================================
# 0. IMPORT PACKAGES

import os
import sys
import json
import pandas as pd
import geopandas as gpd
import numpy as np

print('Packages imported.\n')


# ==================================================================================================================
# 1. DEFINE FILE PATHS

# Working directories
repository = 'C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp/'
datafolder = repository + 'Data/'
outputfolder = repository + 'Output/'

# Input files
boundaries_national =   datafolder + 'boundaries/gadm41_IND_0.shp'                        # GADM India boundaries shapefile
boundaries_state =      datafolder + 'boundaries/gadm41_IND_1.shp'                        # GADM India boundaries shapefile
boundaries_district =   datafolder + 'boundaries/gadm41_IND_2.shp'                        # GADM India boundaries shapefile
boundaries_subdist =    datafolder + 'boundaries/gadm41_IND_3.shp'                        # GADM India boundaries shapefile
locationcodes =         datafolder + 'census/CensusIndia2011_LocationDirectory.csv'       # State and district names and codes from Census
pop_tif =               datafolder + 'worldpop/ind_ppp_2011_1km_Aggregated_UNadj.tif'     # WorldPop UN adjusted 1km 2011 (adjust as necessary)
agland =                datafolder + 'dynamicworld/2020_dw_karnataka_cropland.tif'        # DynamicWorld extracted from GEE
ghsl =                  datafolder + ''

# Census statistics 
# Currently, this file loads just the data for the test state Karnataka (State Code 29).
# The file has been cleaned from the website download into a readable csv table.
agworkers_29 =          datafolder + 'census/CensusIndia2011_IndustrialCategory_Karnataka_DDW-B04-2900_cln.csv'

# Generated files
# These file paths store intermediate files generated during the analysis

# Output files
# These file paths store the final output files used in the Results section


# ==================================================================================================================
# 2. LOAD AND CLEAN DATA

loc_codes = pd.read_csv(locationcodes)
loc_codes.head()

# Create a df of state codes and names
state_codes = loc_codes[(loc_codes["District Code"]==0) &
                        (loc_codes["Sub District Code"]==0) & 
                        (loc_codes["Town-Village Code"]==0)].filter(items=["State Code", "Town-Village Name"])
state_codes

# Create a df of district codes and names
# Initially, this is just for the test state Karnataka
district_codes = loc_codes[(loc_codes["State Code"]==29) &
                           (loc_codes["Sub District Code"]==0) &
                           (loc_codes["Town-Village Code"]==0)].filter(items=["State Code", "District Code", "Town-Village Name"])
district_codes.head(10)

