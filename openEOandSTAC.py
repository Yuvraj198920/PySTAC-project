from pystac import Catalog, Collection, Item
import os
import re
import rasterio
from shapely.geometry import Polygon, mapping

# Create a catalog
catalog =  Catalog(id='sentinal_data', description='Sentinal Data Catalog')

# Create collection for Bolzano's sentinel-2 data
collection = Collection(id='Sentinel-2-Bolzano', description='Sentinel-2 data for Bolzano',)

# Add spatial and temporal extent to the collection
collection.extent = {
    'spatial':[[11.3, 46.4], [11.5, 46.5]],
    'temporal':[['2024-01-01', '2024-01-31']]
}

catalog.add_collection(collection)

# Populate the collection with items
def add_item_to_collection(image_folder):
    files = os.listdir(image_folder)
    for file in files:
        if file.endswith('.tif'):
            print(image_folder+file)
        item = Item()

# Extract date from the file name
def extract_date(file_name):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', file_name)

    if match:
        extracted_date = match.group(1)  # Get the matched date
        print("Extracted Date:", extracted_date)
    else:
        print("No date found in the filename.")
    return extracted_date

# Get the bounding box and footprint of the raster file
def get_bbox_and_footprint(raster):
    with rasterio.open(raster) as r:
        bounds = r.bounds
        bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
        footprint = Polygon([
            [bounds.left, bounds.bottom],
            [bounds.left, bounds.top],
            [bounds.right, bounds.top],
            [bounds.right, bounds.bottom]
        ])
        
        return (bbox, mapping(footprint))