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
wdpath = "N:\Documents\Dissertation\Data"         # sets working path to read data from UCL drive
filepath = "\india_shapefiles\IND_shp_diva-gis"

os.chdir(wdpath)

gdf = gpd.read_file(wdpath + filepath + "\IND_adm2.shp")

print(gdf.head())

plt.plot(gdf, color='green')
plt.show()      # use 'show' to bring up a viz window