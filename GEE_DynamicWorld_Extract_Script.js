// DynamicWorld Extraction of LULC for ARUNACHAL PRADESH, India
// For MSc Urban Spatial Science Dissertation

// This is a Google Earth Engine script designed to extract DynamicWorld raster data for a specified Indian state.
// Note that the object 'table' is an imported dataset of Indian state names and boundaries.

// Part 1 ==============================================================
// Calculate the number of pixels for a single land cover class in a region 
//  as well as the distribution of pixel counts for all classes


// Part 1.1 =================================
// Import and display shapefile

//Define styling and determine the color of the shapefile 
var styling = {color: 'red', fillColor: '00000000'};

// NOTE: long runtime due to the size of the shapefile area.
// Is there a way to filter shapefile after importing? 
var district = table.filter(ee.Filter.eq('NAME_1', 'Arunachal Pradesh'));


//Display the shapefile into the interactive map
Map.addLayer(district);
//Display the view to the center of the screen and scale the view
Map.centerObject(district,10);

Map.addLayer(district.style(styling));


// Part 1.2 =================================
// Fraction of a single class
// (e.g. percentage of an area that is 'cropland')

var geometry = district.geometry()
Map.centerObject(geometry, 10);

var startDate = '2020-01-01';
var endDate = '2021-01-01';

var dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
             .filterDate(startDate, endDate)
             .filterBounds(geometry);

// Create a mode composite.
var classification = dw.select('label');
var dwComposite = classification.reduce(ee.Reducer.mode());

// Extract the crop class.
var cropArea = dwComposite.eq(4);    // see DW metadata for class values; crop = 4
  // The resulting cropArea image is a binary image
  // with pixel value 1 where the condition matched, and 0 elsewhere

// Add both the composite and binary mask to the visualisation 
var dwVisParams = {
  min: 0,
  max: 8,
  palette: [
    '#419BDF', '#397D49', '#88B053', '#7A87C6', '#E49635', '#DFC35A',
    '#C4281B', '#A59B8F', '#B39FE1'
  ]
};

// Clip the composite and add it to the Map.
// Map.addLayer(dwComposite.clip(geometry), dwVisParams, 'Classified Composite');
Map.addLayer(cropArea.clip(geometry), {}, 'Crop Areas');
  
// At this point, it is helpful to rename image bands, to keep track
// var dwComposite = dwComposite.rename(['classification']);
var cropArea = cropArea.rename(['crop_area']);


// Part 2 =================================
// Export the created image

// Run the script, then switch to the Tasks tab and click Run. 
// Upon confirmation, the task will start running and create a GeoTIFF file in your Google Drive

// 'toDrive' exports the image to Google Drive
Export.image.toDrive({
  image: cropArea.clip(geometry),    // exports the composite layer
  description: '2020_dw_12_cropland_1km',
  region: geometry,
  scale: 1000,
  crs: 'EPSG:4326',
  maxPixels: 1e10
});


Export.image.toDrive({
  image: cropArea.clip(geometry),    // exports the composite layer
  description: '2020_dw_12_cropland_100m',
  region: geometry,
  scale: 100,
  crs: 'EPSG:4326',
  maxPixels: 1e10
});