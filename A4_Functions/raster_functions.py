"""
Hexagonal Grid Functions

This module provides functions for generating and analyzing hexagonal grids based on a specified area of interest (AOI) and raster data.

This module requires the following libraries to be installed: `rasterio`, `geopandas`, `h3`, `shapely`, `rasterstats`, `pandas`, and `fiona`.

Functions
---------
hexagonal_tesselation(input_geojson, resolution_level, crs, output_name):
    Generate a hexagonal tessellation within a specified area of interest (AOI) using the H3 library.

mean_aggregation(input_geojson, raster, resolution_level, crs, output_name):
    Perform mean aggregation of a raster within hexagonal polygons defined by an input GeoJSON.

mean_aggregation_plot(input_geojson, column_name, cmap, output_name):
    Generate a plot of hexagons with colors based on a specified column in a GeoDataFrame.
"""

import rasterio
import geopandas as gpd
from geopandas import GeoSeries
import matplotlib.pyplot as plt
import h3
from shapely.geometry import Polygon
from rasterstats import zonal_stats
import pandas as pd
import fiona

def hexagonal_tesselation(input_geojson, resolution_level, crs, output_name):
    """
    Generate a hexagonal tessellation within a specified area of interest (AOI) using H3 library.
    
    Parameters
    ----------
    input_geojson : str
        File path or URL to the input GeoJSON file containing the AOI.
    resolution_level : int
        The desired resolution level of the hexagons. Higher values create smaller hexagons.
    crs : str
        Coordinate reference system (CRS) of the input GeoJSON and output GeoDataFrame.
    output_name : str
        The desired name for the output GeoJSON file (without the file extension).
    
    Returns
    -------
    None
    
    Notes
    -----
    This function requires the `geopandas`, `h3`, and `fiona` libraries to be installed.
    
    Examples
    --------
    >>> hexagonal_tesselation("Salzburg_AOI.geojson", 9, "EPSG:4326", "tesselation_level_9")
    """
    
    # Read input GeoJson
    AOI = gpd.read_file(input_geojson)

    # Generate hexagons within the AOI using H3 library
    hexagons = h3.polyfill(AOI.geometry[0].__geo_interface__, resolution_level, geo_json_conformant=True)

    # Define a lambda function to convert H3 hexagon IDs to Shapely Polygon objects
    def polygonise(hex_id):
        return Polygon(h3.h3_to_geo_boundary(hex_id, geo_json=True))

    # Create a GeoSeries of polygons from the hexagons, with hexagon IDs as index
    hexagons_geoseries = gpd.GeoSeries(list(map(polygonise, hexagons)), index=hexagons, crs=crs)

    # Reset the index of hexagons_geoseries, dropping the existing index
    hexagons_geoseries = hexagons_geoseries.reset_index(drop=True)

    # Extract the geometry column from hexagons_geoseries
    geometry = hexagons_geoseries

    # Create a GeoDataFrame from hexagons_geoseries with the specified CRS and using the extracted geometry column
    hexagons_statistics_gdf = gpd.GeoDataFrame(hexagons_geoseries, crs=crs, geometry=geometry)

    # Drop the '0' column which contains the geometry as string
    hexagons_statistics_gdf = hexagons_statistics_gdf.drop(0, axis=1)

    with fiona.Env(OSR_WKT_FORMAT="WKT2_2018"):
        # Save the GeoDataFrame as a GeoJSON file
        hexagons_statistics_gdf.to_file(output_name + ".geojson")


def mean_aggregation(input_geojson, raster, resolution_level, crs, output_name):
    """
    Perform mean aggregation of a raster within hexagonal polygons defined by an input GeoJSON.
    
    Parameters
    ----------
    input_geojson : str
        File path or URL to the input GeoJSON file containing the hexagonal polygon boundaries.
    raster : str
        File path or URL to the raster file.
    resolution_level : int
        The resolution level of the hexagons. Higher values create smaller hexagons.
    crs : str
        Coordinate reference system (CRS) of the input GeoJSON and output GeoDataFrame.
    output_name : str
        The desired name for the output GeoJSON file (without the file extension).
    
    Returns
    -------
    None
    
    Notes
    -----
    This function requires the `geopandas`, `h3`, `rasterio`, and `fiona` libraries to be installed.
    
    Examples
    --------
    >>> mean_aggregation("Salzburg_AOI.geojson", "Salzburg_Temperature_Composite.tif", 9, "EPSG:4326", "Salzburg_Mean_Temperature")
    """
    # Read input GeoJson
    AOI = gpd.read_file(input_geojson)

    # Generate hexagons within the AOI using H3 library
    hexagons = h3.polyfill(AOI.geometry[0].__geo_interface__, resolution_level, geo_json_conformant=True)

    # Define a lambda function to convert H3 hexagon IDs to Shapely Polygon objects
    def polygonise(hex_id):
        return Polygon(h3.h3_to_geo_boundary(hex_id, geo_json=True))

    # Create a GeoSeries of polygons from the hexagons, with hexagon IDs as index
    hexagons_geoseries = gpd.GeoSeries(list(map(polygonise, hexagons)), index=hexagons, crs=crs)

    # Calculate zonal statistics for the raster within each polygon in hexagons_geoseries
    statistics = zonal_stats(hexagons_geoseries, raster, stats="mean", nodata=-999)
    
    # Convert the statistics to a pandas DataFrame
    statistics = pd.DataFrame(statistics)

    # Reset the index of hexagons_geoseries, dropping the existing index
    hexagons_geoseries = hexagons_geoseries.reset_index(drop=True)

    # Concatenate hexagons_geoseries and statistics along the columns axis
    hexagons_statistics = pd.concat([hexagons_geoseries, statistics], axis=1)

    # Extract the first column as the geometry
    geometry = hexagons_statistics[0]

    # Create a GeoDataFrame from hexagons_statistics with the specified CRS and using the extracted geometry column
    hexagons_statistics_gdf = gpd.GeoDataFrame(hexagons_statistics, crs=crs, geometry=geometry)

    # Drop the '0' column which contains the geometry as string
    hexagons_statistics_gdf = hexagons_statistics_gdf.drop(0, axis=1)  

    with fiona.Env(OSR_WKT_FORMAT="WKT2_2018"):
        # Save the GeoDataFrame as a GeoJSON file
        hexagons_statistics_gdf.to_file(output_name + ".geojson")


def mean_aggregation_plot(input_geojson, column_name, cmap, output_name):
    """
    Generate a plot of hexagons with colors based on a specified column in a GeoDataFrame.
    
    Parameters
    ----------
    input_geojson : str
        File path or URL to the input GeoJSON file containing the hexagonal polygon boundaries and data.
    column_name : str
        The name of the column in the GeoDataFrame to use for coloring the hexagons.
    cmap : str or colormap object
        The colormap to use for coloring the hexagons.
    output_name : str
        The desired name for the output PNG image file (without the file extension).
    
    Returns
    -------
    None
    
    Notes
    -----
    This function requires the `geopandas` and `matplotlib` libraries to be installed.
    
    Examples
    --------
    >>> mean_aggregation_plot("data.geojson", "mean", "viridis", "Salzburg_Mean_Temperature_Plot")
    """
    
    import geopandas as gpd
    import matplotlib.pyplot as plt

    # Read the GeoJSON file
    hexagons_statistics_gdf = gpd.read_file(input_geojson)
    
    # Plot the hexagons with colors based on the specified column
    hexagons_statistics_gdf.plot(column=column_name, cmap=cmap, linewidth=0.8, edgecolor='black', legend=True)

    # Set plot title and axis labels
    plt.title('Hexagons with {} Values'.format(column_name))
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')

    # Save the plot as a PNG image
    plt.savefig(output_name + ".png", dpi=300)  # Specify the desired filename and DPI (dots per inch)
