import xarray as xr
import os 

#opens a single .nc file in a given diretory
def opennc(dir, filename):
    file = dir + "/" + filename
    fileout = xr.open_dataset(file)
    return fileout

#combines all .nc files in a folder into one
def combinenc(folder_path, output_filename):
    nc_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith(".nc") and not file.startswith("._")]

    if not nc_files:
        raise FileNotFoundError("No valid NetCDF files found in the specified folder.")

    datasets = []

    for nc_file in nc_files:
        if os.path.basename(nc_file) == output_filename + ".nc":
            print("Chosen file name found in folder - files may already be merged")
            output_name = xr.open_dataset(nc_file)
            return output_name

    for nc_file in nc_files:
        try:
            ds = xr.open_dataset(nc_file, engine="netcdf4")
            datasets.append(ds)
        except OSError:
            print(f"Skipping invalid NetCDF file: {nc_file}") 
        

    if not datasets:
        raise ValueError("No valid NetCDF files could be opened.")

    
    merged_dataset = xr.merge(datasets)

    
    output_file = os.path.join(folder_path, output_filename + ".nc")
    merged_dataset.to_netcdf(output_file)

    
    for ds in datasets:
        ds.close()
    output_name = xr.open_dataset(output_file)
    return output_name
