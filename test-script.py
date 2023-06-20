# ===================================================
# Test script: installation of anaconda, using virtual environment,and connection to VS code
# Date: 2023-04-25
# ===================================================

# import packages
import sys
import os
import numpy as np
import matplotlib.pyplot as plt


print(sys.version)

d = 'testvar'
b = ' into sentence'

db = d + b
print(db)


# Test geopackages
import geopandas as gpd

# set filepath  
# wdpath = "N:\Documents\Dissertation\Data"         # sets working path to read data from UCL drive
# filepath = "\india_shapefiles\IND_shp_diva-gis\IND_adm2.shp"   # file path to pair with N: UCL drive

wdpath = r"C:\Users\joepo\Documents\Uni\UCL CASA\Dissertation\india_adp"
filepath = r"\Data\boundaries\gadm41_IND_3.shp"

os.chdir(wdpath)

gdf = gpd.read_file(wdpath + filepath)

print(gdf.head())


# plot the map

fig, ax = plt.subplots()
gdf.plot(ax = ax, color='green').set_axis_off()
plt.show()      # use 'show' to bring up a viz window

# inspect the columns

gdf.info