import openeo

connection = openeo.connect('https://openeo.dataspace.copernicus.eu').authenticate_oidc()

spatial_extent =  {"west": 11.3, "south": 46.4, "east": 11.5, "north": 46.5}
temporal_extent = ["2024-01-01", "2024-01-31"]

# Load the sentinel-2 collecion
s2cube =  connection.load_collection('SENTINEL2_L2A', spatial_extent=spatial_extent, temporal_extent=temporal_extent, bands=['B04', 'B08'])
ndvi =  s2cube.ndvi(red='B04', nir='B08')

ndvi_result = ndvi.save_result(format='GTiff')
job = ndvi_result.create_job()
job.start_and_wait()
job.get_results().download_files('./ndvi_images/')