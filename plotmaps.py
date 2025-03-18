import matplotlib.pyplot as plt
import cartopy as cart
import cartopy.crs as ccrs
import cartopy.feature as cf
from cartopy.util import add_cyclic_point
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.tri as tri





def fixLine(dataset: xr.Dataset) -> xr.Dataset:
       
    lon_name = "lon"

    dataset["_longitude_adjusted"] = xr.where(dataset[lon_name] > 180, dataset[lon_name] - 360, dataset[lon_name])
    dataset = (dataset.swap_dims({lon_name: "_longitude_adjusted"}).sel(**{"_longitude_adjusted": sorted(dataset._longitude_adjusted)}).drop_vars(lon_name))

    dataset = dataset.rename({"_longitude_adjusted": lon_name})
    return dataset

def plotMaps(dataset, plotTitle, label, level, colormap, extents, landmask):
    projection = ccrs.Robinson()
    crs = ccrs.PlateCarree()
    plt.figure(figsize=(16,9), dpi=300)
    ax = plt.axes(projection=projection, frameon=True)
    gl = ax.gridlines(crs=crs, draw_labels=True,
                    linewidth=.6, color='gray', alpha=0.5, linestyle='-.')
    gl.xlabel_style = {"size" : 7}
    gl.ylabel_style = {"size" : 7}
    ax.add_feature(cf.COASTLINE.with_scale("50m"), lw=0.5)
    ax.add_feature(cf.BORDERS.with_scale("50m"), lw=0.3)
    if landmask == "Mask":
        ax.add_feature(cart.feature.LAND, zorder=100, edgecolor='k')
    lon_min = -180
    lon_max = 180
    lat_min = -90
    lat_max = 90

    cbar_kwargs = {'orientation':'horizontal', 'shrink':0.6, "pad" : .05, 'aspect':40, 'label':label, }
    dataset.plot.contourf(ax=ax, transform=ccrs.PlateCarree(), cbar_kwargs=cbar_kwargs, cmap=colormap,extend=extents, levels=level)
    plt.title(plotTitle)

def map(data, title, label, level, colormap, extents, landmask):
    data_fixline = fixLine(data)
    plotMaps(data_fixline, title, label, level, colormap, extents, landmask)



def unstrucMap(file, dataset, plotTitle, label, levels=40):
    ds = xr.open_dataset(file)

    # Extract longitude, latitude, and data variable
    lon = ds['TLONG'].values.astype(np.float64)
    lat = ds['TLAT'].values.astype(np.float64)
    data = dataset.IRON_FLUX.values.astype(np.float64)  # Convert to NumPy array

    # Try to get a land mask (if it exists in the dataset)
    land_mask = None
    if 'MASK' in ds.variables:  # Example mask name
        land_mask = ds['MASK'].values.astype(np.float64)

    # Flatten arrays
    lon, lat, data = lon.ravel(), lat.ravel(), data.ravel()
    if land_mask is not None:
        land_mask = land_mask.ravel()

    # Remove NaN values
    valid_mask = ~np.isnan(lon) & ~np.isnan(lat) & ~np.isnan(data)

    # Apply land-sea mask if available (0 = land, 1 = ocean)
    if land_mask is not None:
        valid_mask &= (land_mask > 0)

    lon, lat, data = lon[valid_mask], lat[valid_mask], data[valid_mask]

    # Ensure unique (lon, lat) pairs
    coords = np.column_stack((lon, lat))
    unique_idx = np.unique(coords, axis=0, return_index=True)[1]
    lon, lat, data = lon[unique_idx], lat[unique_idx], data[unique_idx]

    # Ensure at least 3 valid points for triangulation
    if len(lon) < 3:
        raise ValueError("Not enough unique points for triangulation.")

    # Create triangulation for unstructured grid
    try:
        triang = tri.Triangulation(lon, lat)
        
        # **Mask triangles that include land** to prevent interpolation errors
        mask = np.any(np.isnan(data[triang.triangles]), axis=1)
        triang.set_mask(mask)

    except Exception as e:
        raise RuntimeError(f"Triangulation failed: {e}")

    # Create figure and axis with Robinson projection
    fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={'projection': ccrs.Robinson()})

    # Add map features
    ax.set_global()
    ax.add_feature(cf.LAND, color='lightgray', zorder=1)  # Ensures land is gray
    ax.add_feature(cf.COASTLINE, linewidth=0.8, zorder=2)
    ax.add_feature(cf.BORDERS, linestyle=':', linewidth=0.5, zorder=2)

    # Fix issue: Check if levels is an int or array
    if isinstance(levels, int):
        levels = np.linspace(data.min(), data.max(), num=levels)  # Generate contour levels dynamically

    # Plot data using tricontourf
    contour = ax.tricontourf(triang, data, levels=levels, transform=ccrs.PlateCarree(), cmap='viridis', zorder=3)

    # Add colorbar
    cbar = plt.colorbar(contour, ax=ax, orientation='horizontal', pad=0.05)
    cbar.set_label(label)

    # Set title
    ax.set_title(plotTitle)

    # Show plot
    plt.show()




def plotTS(dataset, variable, latitude, longitude, structured, years, title, label, scalefactor):
    years = years + 1
    areafile = "/Volumes/BackupDrive/Research/Undergrad Research/Spring 25/Files/Area/surfdata_1.9x2.5_c081023.nc"
    area = xr.open_dataset(areafile)
    if structured:
        lat = dataset.lat
        lon = dataset.lon
    elif not structured:
        lat = data.TLAT
        lon = data.TLONG
    time = dataset.time
    data = dataset[variable].sel(lon=longitude,lat=latitude,method="nearest")*scalefactor
    days_per_month = np.array([31,28,31,30,31,30,31,31,30,31,30,31])
    annualmean = np.zeros((years))
    for y in np.arange(years):
        ti = np.arange(12) + 12*(y)
        annualmean[y] = (data[ti]*days_per_month).sum(dim="time")/np.sum(days_per_month)
    time_annual = time[np.arange(5,12*years,12)]
    fig = plt.figure(1, figsize=(10, 5))
    data.plot(label = label)
    plt.plot(time_annual, annualmean,'-',linewidth=2.0, label = label + " annual mean")
    plt.xlabel('Year')
    plt.ylabel(label)
    plt.title(title)
    plt.legend()




def plotTSZone(dataset, variable, lat_min, lat_max, lon_min, lon_max, structured, years, title, label, scalefactor):
    years = years + 1
    areafile = "/Volumes/BackupDrive/Research/Undergrad Research/Spring 25/Files/Area/surfdata_1.9x2.5_c081023.nc"
    area = xr.open_dataset(areafile)

    if structured:
        lat = dataset.lat
        lon = dataset.lon
    else:
        lat = dataset.TLAT
        lon = dataset.TLONG

    time = dataset.time


    data = dataset[variable].sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max)) * scalefactor


    regional_mean = data.mean(dim=["lat", "lon"])


    days_per_month = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

    annualmean = np.zeros(years)
    for y in range(years):
        ti = np.arange(12) + 12 * y  


        monthly_data = regional_mean.isel(time=ti)

 
        weighted_sum = (monthly_data * days_per_month).sum(dim="time")

        annualmean[y] = weighted_sum.values / np.sum(days_per_month)


    time_annual = time.values[np.arange(5, 12 * years, 12)]


    plt.figure(2, figsize=(10, 5))
    regional_mean.plot(label=label)
    plt.plot(time_annual[:-1], annualmean[:-1], '-', linewidth=2.0, label=label + " annual mean")
    plt.xlabel('Year')
    plt.ylabel(label)
    plt.title(title)
    plt.legend()
    plt.show()
