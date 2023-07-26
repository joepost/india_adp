# ==================================================================================================================

# DISSERTATION
# SECTION 03: Buffer calculations
#   This file picks up at the end of 02, setting an iterative buffer process to validate ADP estimates against census statistics.  

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
# from osgeo import gdal

from globals import *       # Imports the filepaths defined in globals.py

print('Packages imported.\n')

# Start timer
start_time = time.time()

# Set buffer increment
r_increment = 100


# COPIED BELOW DIRECTLY FROM SL SCRIPT ******************************

# Create a disctionary that contains the district name as key and the final buffer radius as values
buffer_r_dict = {}
# Initialise the dictionary with zero values:
for y in dist_filename:
    buffer_r_dict[y] = 0

while All_dist_pop_check==False:
    for y in district_codes['Town-Village Name']:
        buffer_radius = 100  # initial value in metres
        district_pop_check = False
        while district_pop_check == False:
            if pop_df.loc[pop_df['dist_names'] == y[3:], 'use_aglands?'].item() == 'too small':
                print('Creating ' + str(buffer_radius) + 'm buffers on ag lands for district: ' + y)
                print()
                buffer_r_dict[y] = buffer_radius
                # Buffer creation
                processing.run('native:buffer',
                                {'INPUT': ag_lands_only_path + y + '_ag_lands_only.shp',
                                'DISTANCE': buffer_radius * (0.00001/1.11), # buffer radius in deg
                                'SEGMENTS': 5,
                                'END_CAP_STYLE': 0,
                                'JOIN_STYLE': 0,
                                'MITER_LIMIT': 2,
                                'DISSOLVE': True,
                                'OUTPUT': buffer_path + y + '_ag_lands_' + str(buffer_radius) + 'm_buffer.shp'})

                # Clip the buffer to the district boundaries
                processing.run('native:clip',
                                {'INPUT': buffer_path + y + '_ag_lands_' + str(buffer_radius) + 'm_buffer.shp',
                                'OVERLAY': ind_dist_boundaries_filepath + 'ADM2_EN_' + y[3:] + '.shp',
                                'OUTPUT': buffer_path + y + '_' + str(buffer_radius) + 'm_buffer_clipped.shp'})

                processing.run('qgis:joinbylocationsummary',
                                {'INPUT': buffer_path + y + '_' + str(buffer_radius) + 'm_buffer_clipped.shp',
                                'JOIN': rur_points_shp,
                                'PREDICATE': [0,1,5],
                                'JOIN_FIELDS': ['pop_count_'],
                                'SUMMARIES': [5],
                                'DISCARD_NONMATCHING': False,
                                'OUTPUT': buffer_path + y + '_' + str(buffer_radius) + 'm_buffer_clipped_pop.shp'})

                # check value from HIES ag pop
                hies_pop_ag_dep = pop_df.loc[pop_df['dist_names'] == y[3:], 'hies_ag_dep_pop_%'].item() # ag dep pop for district y
                hies_dist_pop = pop_df.loc[pop_df['dist_names'] == y[3:], 'dist_pop'].item()  # tot pop of district y
                dist_rur_pop = pop_df.loc[pop_df['dist_names'] == y[3:], 'dist_rur_pop'].item() # rur pop of district y

                fn = buffer_path + y + '_' + str(buffer_radius) + 'm_buffer_clipped_pop.shp' # file name
                layer = QgsVectorLayer(fn, '', 'ogr') # arguments = file name, layer name, data provider
                # The following command gets the features of the layer (feature = row, attribute = column)
                # This layer should have only one feature, so features is a 1-element list
                features = layer.getFeatures()
                for feat in features:
                    buffer_pop_count = feat['pop_count_'] # buffer pop count

                if (buffer_pop_count / hies_dist_pop) - hies_pop_ag_dep > -threshold: # '> -threshold' means buffer ok
                    district_pop_check = True

                elif abs(buffer_pop_count - dist_rur_pop) < threshold:
                    # this is the condition in which the whole rural population is already contained in the buffer
                    # with a 5% (or different value of threshold) error acceptance
                    district_pop_check = True

                else: # 'difference < -threshold' means buffer too small
                    buffer_radius = buffer_radius + r_increment

            elif pop_df.loc[pop_df['dist_names'] == y[3:], 'use_aglands?'].item() == 'too big':
                print('Creating -' + str(buffer_radius) + 'm buffers on ag lands for district: ' + y)
                print()
                buffer_r_dict[y] = (-1) * buffer_radius # nevative value = inward buffer
                # Buffer creation
                processing.run('native:buffer',
                                {'INPUT': ag_lands_only_path + y + '_ag_lands_only.shp',
                                'DISTANCE': (-1) * buffer_radius * (0.00001 / 1.11),  # buffer radius in deg
                                'SEGMENTS': 5,
                                'END_CAP_STYLE': 0,
                                'JOIN_STYLE': 0,
                                'MITER_LIMIT': 2,
                                'DISSOLVE': True,
                                'OUTPUT': buffer_path + y + '_ag_lands_-' + str(buffer_radius) + 'm_buffer.shp'})

                # Clip the buffer to the district boundaries
                processing.run('native:clip',
                                {'INPUT': buffer_path + y + '_ag_lands_-' + str(buffer_radius) + 'm_buffer.shp',
                                'OVERLAY': ind_dist_boundaries_filepath + 'ADM2_EN_' + y[3:] + '.shp',
                                'OUTPUT': buffer_path + y + '_-' + str(buffer_radius) + 'm_buffer_clipped.shp'})

                processing.run('qgis:joinbylocationsummary',
                                {'INPUT': buffer_path + y + '_-' + str(buffer_radius) + 'm_buffer_clipped.shp',
                                'JOIN': rur_points_shp,
                                'PREDICATE': [0, 1, 5],
                                'JOIN_FIELDS': ['pop_count_'],
                                'SUMMARIES': [5],
                                'DISCARD_NONMATCHING': False,
                                'OUTPUT': buffer_path + y + '_-' + str(buffer_radius) + 'm_buffer_clipped_pop.shp'})

                # check value from HIES ag pop
                hies_pop_ag_dep = pop_df.loc[pop_df['dist_names'] == y[3:], 'hies_ag_dep_pop_%'].item()  # ag dep pop for district y
                hies_dist_pop = pop_df.loc[pop_df['dist_names'] == y[3:], 'dist_pop'].item()  # tot pop of district y
                dist_rur_pop = pop_df.loc[pop_df['dist_names'] == y[3:], 'dist_rur_pop'].item()  # rur pop of district y

                fn = buffer_path + y + '_-' + str(buffer_radius) + 'm_buffer_clipped_pop.shp'  # file name
                layer = QgsVectorLayer(fn, '', 'ogr')  # arguments = file name, layer name, data provider
                # The following command gets the features of the layer (feature = row, attribute = column)
                # This layer should have only one feature, so features is a 1-element list
                features = layer.getFeatures()
                for feat in features:
                    buffer_pop_count = feat['pop_count_']  # buffer pop count

                if (buffer_pop_count / hies_dist_pop) - hies_pop_ag_dep < threshold:  # '< threshold' means buffer ok
                    district_pop_check = True

                elif abs(buffer_pop_count - dist_rur_pop) < threshold:
                    # this is the condition in which the whole rural population is already contained in the buffer
                    district_pop_check = True

                else:  # 'difference > threshold' means buffer too big
                    buffer_radius = buffer_radius + r_increment

            elif pop_df.loc[pop_df['dist_names'] == y[3:], 'use_aglands?'].item() == 'OK':
                district_pop_check = True

            else: raise Exception('ERROR: something went wrong! Check the values of the use_aglands? column of pop counts csv file.')

    All_dist_pop_check = True




# ===============

print('\nScript complete.\n')
timestamp(start_time)