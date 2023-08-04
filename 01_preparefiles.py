# ==================================================================================================================

# DISSERTATION
# SECTION 01: Prepare Files
# Date created: 2023-06-19
# Author: J Post

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

os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal


from globals import *       # Imports the filepaths defined in globals.py

print('Packages imported.\n')


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