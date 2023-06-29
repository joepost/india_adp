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
# plt.show()      # use 'show' to bring up a viz window

# inspect the columns

gdf.info




# ===========================================================================
# SECTION 2: TEST GDAL FUNCTIONING

from osgeo import gdal

ghslfile = 'C:/Users/joepo/Documents/Uni/UCL CASA/Dissertation/india_adp/Data/ghsl/GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0_R6_C25.tif'
dataset = gdal.Open(ghslfile, gdal.GA_ReadOnly)

# Print metadata
print("Driver: {}/{}".format(dataset.GetDriver().ShortName,
                            dataset.GetDriver().LongName))
print("Size is {} x {} x {}".format(dataset.RasterXSize,
                                    dataset.RasterYSize,
                                    dataset.RasterCount))
print("Projection is {}".format(dataset.GetProjection()))
geotransform = dataset.GetGeoTransform()
if geotransform:
    print("Origin = ({}, {})".format(geotransform[0], geotransform[3]))
    print("Pixel Size = ({}, {})".format(geotransform[1], geotransform[5]))
# print("Number of bands is {}".format(dataset.GetRasterCount()))

band = dataset.GetRasterBand(1)
print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))

min = band.GetMinimum()
max = band.GetMaximum()
if not min or not max:
    (min,max) = band.ComputeRasterMinMax(True)
print("Min={:.3f}, Max={:.3f}".format(min,max))

if band.GetOverviewCount() > 0:
    print("Band has {} overviews".format(band.GetOverviewCount()))

if band.GetRasterColorTable():
    print("Band has a color table with {} entries".format(band.GetRasterColorTable().GetCount()))

dataset.GDALClose()