import openeo
from pystac import Catalog, Collection, Item
import pystac
import os
import re
import pystac.media_type
import rasterio
from shapely.geometry import Polygon, mapping
from datetime import datetime
from pystac.extensions.eo import Band, EOExtension
from tempfile import TemporaryDirectory

# Create a catalog
catalog = Catalog(id='sentinal_data', description='Sentinal Data Catalog')

# List of bands
bands = [Band.create(name='B04', common_name='red', center_wavelength=0.665, full_width_half_max=0.025, description='Red 665 nm'),Band.create(name='B08', common_name='nir', center_wavelength=0.842, full_width_half_max=0.145, description='Near-Infrared 842 nm')]

# List of collection item
collection_items = []

# Populate the collection with items
def add_item_to_collection(image_folder):
    files = os.listdir(image_folder)
    for file in files:
        if file.endswith('.tif'):
            bbox, footprint = get_bbox_and_footprint(os.path.join(image_folder, file))
            item = Item(id='Sentinel-2-Bolzano-' + extract_date(file), geometry=footprint, bbox=bbox, datetime=datetime.utcnow(), properties={})
            item.common_metadata.gsd = 10
            item.common_metadata.platform = 'Sentinel-2'
            item.common_metadata.instruments = ['MSI']
            # create asset to add to the item
            collection_asset = pystac.Asset(href=os.path.join(image_folder, file), media_type = pystac.MediaType.GEOTIFF)
            item.add_asset('image', collection_asset)
            # Apple EO extension to the asset
            eo = EOExtension.ext(item.assets['image'], add_if_missing = True)
            eo.apply(bands)
            collection_items.append(item)

def get_collection_interval(collection_item_list):
    sorted_list = sorted(collection_item_list, key=lambda x: x.datetime)
    return sorted_list

# Extract date from the file name
def extract_date(file_name):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', file_name)

    if match:
        extracted_date = match.group(1)  # Get the matched date
        return extracted_date
    else:
        return None


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

with TemporaryDirectory() as tmp_dir:

    connection = openeo.connect('https://openeo.dataspace.copernicus.eu').authenticate_oidc()

    spatial_extent =  {"west": 11.3, "south": 46.4, "east": 11.5, "north": 46.5}
    temporal_extent = ["2024-01-01", "2024-01-05"]

    # Load the sentinel-2 collecion
    s2cube =  connection.load_collection('SENTINEL2_L2A', spatial_extent=spatial_extent, temporal_extent=temporal_extent, bands=['B04', 'B08'])
    ndvi =  s2cube.ndvi(red='B04', nir='B08')

    ndvi_result = ndvi.save_result(format='GTiff')
    job = ndvi_result.create_job()
    job.start_and_wait()
    job.get_results().download_files(tmp_dir)

    list_files = os.listdir(tmp_dir)
    print(list_files)
    add_item_to_collection(tmp_dir)
    collection_interval = get_collection_interval(collection_items)

    # get tempral extent from collection items
    collection_interval = pystac.TemporalExtent(intervals=[collection_interval])
    # Collection extent
    collection_extent = pystac.Extent(spatial= [[11.3, 46.4], [11.5, 46.5]], temporal=[['2024-01-01', '2024-01-10']])

    # Create collection for Bolzano's sentinel-2 data
    collection = Collection(id='Sentinel-2-Bolzano', description='Sentinel-2 data for Bolzano', extent = collection_extent, license='CC-BY-SA-4.0')
    collection.add_items(collection_items)
    catalog.add_child(collection)
    catalog.describe()
    tmp_dir.cleanup()