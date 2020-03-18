from osgeo import gdal
import numpy as np
import netCDF4
from glob import glob
import json
import os
from datetime import datetime
import xarray as xr

#mcd12q1_path = "/g/data/u39/public/data/modis/lpdaac-tiles-c5/MCD12Q1.051"
mcd12q1_path = "/g/data/u39/public/data/modis/lpdaac-tiles-c6/MCD12Q1.006"

def get_vegmask(tile_id, tile_date):
    mask_paths = sorted(glob("{}/*".format(mcd12q1_path)))[::-1]

    # Find the most recent mask for the FMC data
    for mask_path in mask_paths:
        msk_date =  datetime.strptime(mask_path.split("/")[-1], '%Y.%m.%d')
        if msk_date > tile_date:
            continue
          
        files = glob("{0}/MCD12Q1.A{1}{2:03d}.{3}.006.*.hdf".format(mask_path, msk_date.year, msk_date.timetuple().tm_yday, tile_id))
        if len(files) == 1:
            veg_mask = xr.open_dataset(files[0]).LC_Type1[:].data

            veg_mask[veg_mask == 1] = 3
            veg_mask[veg_mask == 2] = 3
            veg_mask[veg_mask == 3] = 3
            veg_mask[veg_mask == 4] = 3
            veg_mask[veg_mask == 5] = 3
            veg_mask[veg_mask == 6] = 2
            veg_mask[veg_mask == 7] = 2
            veg_mask[veg_mask == 8] = 3
            veg_mask[veg_mask == 9] = 3
            veg_mask[veg_mask == 10] = 1
            veg_mask[veg_mask == 11] = 0
            veg_mask[veg_mask == 12] = 1
            veg_mask[veg_mask == 13] = 0
            veg_mask[veg_mask == 14] = 0
            veg_mask[veg_mask == 15] = 0
            veg_mask[veg_mask == 16] = 0
            veg_mask[veg_mask == 17] = 0
            veg_mask[veg_mask == 254] = 0
            veg_mask[veg_mask == 255] = 0
            
            return veg_mask
    
    return None

def pack_fmc(hdf_file, date, median_arr, std_arr, q_mask, dest):
    
    with netCDF4.Dataset(dest, 'w', format='NETCDF4_CLASSIC') as ds:
        with open('nc_metadata.json') as data_file:
            attrs = json.load(data_file)
            for key in attrs:
                setattr(ds, key, attrs[key])
        setattr(ds, "date_created", datetime.now().strftime("%Y%m%dT%H%M%S"))
        
        rast = gdal.Open('HDF4_EOS:EOS_GRID:"{}":MOD_Grid_BRDF:Nadir_Reflectance_Band1'.format(hdf_file))
        proj_wkt = rast.GetProjection()
        geot = rast.GetGeoTransform()
        
        t_dim = ds.createDimension("time", 1)
        x_dim = ds.createDimension("x", rast.RasterXSize)
        y_dim = ds.createDimension("y", rast.RasterYSize)

        var = ds.createVariable("time", "f8", ("time",))
        var.units = "seconds since 1970-01-01 00:00:00.0"
        var.calendar = "standard"
        var.long_name = "Time, unix time-stamp"
        var.standard_name = "time"
        var[:] = netCDF4.date2num([date], units="seconds since 1970-01-01 00:00:00.0", calendar="standard")

        var = ds.createVariable("x", "f8", ("x",))
        var.units = "m"
        var.long_name = "x coordinate of projection"
        var.standard_name = "projection_x_coordinate"
        var[:] = np.linspace(geot[0], geot[0]+(geot[1]*rast.RasterXSize), rast.RasterXSize)
        
        var = ds.createVariable("y", "f8", ("y",))
        var.units = "m"
        var.long_name = "y coordinate of projection"
        var.standard_name = "projection_y_coordinate"
        var[:] = np.linspace(geot[3], geot[3]+(geot[5]*rast.RasterYSize), rast.RasterYSize)
        
        var = ds.createVariable("lfmc", 'f4', ("time", "y", "x"), fill_value=-9999.9)
        var.long_name = "Live Fuel Moisture Content"
        var.units = '%'
        var.grid_mapping = "sinusoidal"
        var[:] = median_arr[None,...]

        var = ds.createVariable("lfmc_uncertainty", 'f4', ("time", "y", "x"), fill_value=-9999.9)
        var.long_name = "Live Fuel Moisture Content Uncertainty"
        var.units = '%'
        var.grid_mapping = "sinusoidal"
        var[:] = std_arr[None,...]
        
        var = ds.createVariable("quality_mask", 'i1', ("time", "y", "x"), fill_value=0)
        var.long_name = "Combined Bands Quality Mask"
        var.units = 'Cat'
        var.grid_mapping = "sinusoidal"
        var[:] = q_mask.astype(np.int8)[None,...]

        var = ds.createVariable("sinusoidal", 'S1', ())
        var.grid_mapping_name = "sinusoidal"
        var.false_easting = 0.0
        var.false_northing = 0.0
        var.longitude_of_central_meridian = 0.0
        var.longitude_of_prime_meridian = 0.0
        var.semi_major_axis = 6371007.181
        var.inverse_flattening = 0.0
        var.spatial_ref = proj_wkt
        var.GeoTransform = "{} {} {} {} {} {} ".format(*[geot[i] for i in range(6)])


def pack_flammability(fmc_file, date, flam, q_mask, dest):
    
    with netCDF4.Dataset(dest, 'w', format='NETCDF4_CLASSIC') as ds:
        with open('nc_metadata.json') as data_file:
            attrs = json.load(data_file)
            for key in attrs:
                setattr(ds, key, attrs[key])
        setattr(ds, "date_created", datetime.now().strftime("%Y%m%dT%H%M%S"))
        
        rast = gdal.Open('NETCDF:"{}":lfmc_mean'.format(fmc_file))
        proj_wkt = rast.GetProjection()
        geot = rast.GetGeoTransform()
        
        t_dim = ds.createDimension("time", 1)
        x_dim = ds.createDimension("x", rast.RasterXSize)
        y_dim = ds.createDimension("y", rast.RasterYSize)

        var = ds.createVariable("time", "f8", ("time",))
        var.units = "seconds since 1970-01-01 00:00:00.0"
        var.calendar = "standard"
        var.long_name = "Time, unix time-stamp"
        var.standard_name = "time"
        var[:] = netCDF4.date2num([date], units="seconds since 1970-01-01 00:00:00.0", calendar="standard")

        var = ds.createVariable("x", "f8", ("x",))
        var.units = "m"
        var.long_name = "x coordinate of projection"
        var.standard_name = "projection_x_coordinate"
        var[:] = np.linspace(geot[0], geot[0]+(geot[1]*rast.RasterXSize), rast.RasterXSize)
        
        var = ds.createVariable("y", "f8", ("y",))
        var.units = "m"
        var.long_name = "y coordinate of projection"
        var.standard_name = "projection_y_coordinate"
        var[:] = np.linspace(geot[3], geot[3]+(geot[5]*rast.RasterYSize), rast.RasterYSize)
        
        var = ds.createVariable("flammability", 'f4', ("time", "y", "x"), fill_value=-9999.9)
        var.long_name = "Flammability Index"
        var.units = '%'
        var.grid_mapping = "sinusoidal"
        var[:] = flam[None,...]
        
        var = ds.createVariable("quality_mask", 'i1', ("time", "y", "x"), fill_value=0)
        var.long_name = "Combined Bands Quality Mask"
        var.units = 'Cat'
        var.grid_mapping = "sinusoidal"
        var[:] = q_mask.astype(np.int8)[None,...]

        var = ds.createVariable("sinusoidal", 'S1', ())
        var.grid_mapping_name = "sinusoidal"
        var.false_easting = 0.0
        var.false_northing = 0.0
        var.longitude_of_central_meridian = 0.0
        var.longitude_of_prime_meridian = 0.0
        var.semi_major_axis = 6371007.181
        var.inverse_flattening = 0.0
        var.spatial_ref = proj_wkt
        var.GeoTransform = "{} {} {} {} {} {} ".format(*[geot[i] for i in range(6)])

wgs84_wkt = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'

def pack_fmc_mosaic(date, fmc_median, fmc_stdv, q_mask, dest):
    lat0 = -10.
    lat1 = -44.
    lon0 = 113.
    lon1 = 154.
    res = 0.005
    
    x_size = int((lon1 - lon0)/res)
    y_size = int((lat1 - lat0)/(-1*res))
    geot = [lon0, res, 0., lat0, 0., -1*res]
    
    with netCDF4.Dataset(dest, 'w', format='NETCDF4_CLASSIC') as ds:
        with open('nc_metadata.json') as data_file:
            attrs = json.load(data_file)
            for key in attrs:
                setattr(ds, key, attrs[key])
        setattr(ds, "date_created", datetime.now().strftime("%Y%m%dT%H%M%S"))
        
        t_dim = ds.createDimension("time", 1)
        x_dim = ds.createDimension("longitude", fmc_mean.shape[1])
        y_dim = ds.createDimension("latitude", fmc_mean.shape[0])

        var = ds.createVariable("time", "f8", ("time",))
        var.units = "seconds since 1970-01-01 00:00:00.0"
        var.calendar = "standard"
        var.long_name = "Time, unix time-stamp"
        var.standard_name = "time"
        var[:] = netCDF4.date2num([date], units="seconds since 1970-01-01 00:00:00.0", calendar="standard")

        var = ds.createVariable("longitude", "f8", ("longitude",))
        var.units = "degrees"
        var.long_name = "longitude"
        var.standard_name = "longitude"
        var[:] = np.linspace(lon0, lon1-res, num=x_size)
        
        var = ds.createVariable("latitude", "f8", ("latitude",))
        var.units = "degrees"
        var.long_name = "latitude"
        var.standard_name = "latitude"
        var[:] = np.linspace(lat0, lat1+res, num=y_size)
        
        var = ds.createVariable("lfmc", 'f4', ("time", "latitude", "longitude"), fill_value=-9999.9)
        var.long_name = "Live Fuel Moisture Content"
        var.units = '%'
        var[:] = fmc_mean[None,...]

        var = ds.createVariable("lfmc_uncertainty", 'f4', ("time", "latitude", "longitude"), fill_value=-9999.9)
        var.long_name = "Live Fuel Moisture Content Uncertainty"
        var.units = '%'
        var[:] = fmc_stdv[None,...]
        
        var = ds.createVariable("quality_mask", 'i1', ("time", "latitude", "longitude"), fill_value=0)
        var.long_name = "Quality Mask"
        var.units = 'Cat'
        var[:] = q_mask[None,...]


def pack_flammability_mosaic(date, flam, q_mask, dest):
    lat0 = -10.
    lat1 = -44.
    lon0 = 113.
    lon1 = 154.
    res = 0.005
    
    x_size = int((lon1 - lon0)/res)
    y_size = int((lat1 - lat0)/(-1*res))
    geot = [lon0, res, 0., lat0, 0., -1*res]
    
    with netCDF4.Dataset(dest, 'w', format='NETCDF4_CLASSIC') as ds:
        with open('nc_metadata.json') as data_file:
            attrs = json.load(data_file)
            for key in attrs:
                setattr(ds, key, attrs[key])
        setattr(ds, "date_created", datetime.now().strftime("%Y%m%dT%H%M%S"))
        
        t_dim = ds.createDimension("time", 1)
        x_dim = ds.createDimension("longitude", flam.shape[1])
        y_dim = ds.createDimension("latitude", flam.shape[0])

        var = ds.createVariable("time", "f8", ("time",))
        var.units = "seconds since 1970-01-01 00:00:00.0"
        var.calendar = "standard"
        var.long_name = "Time, unix time-stamp"
        var.standard_name = "time"
        var[:] = netCDF4.date2num([date], units="seconds since 1970-01-01 00:00:00.0", calendar="standard")

        var = ds.createVariable("longitude", "f8", ("longitude",))
        var.units = "degrees"
        var.long_name = "longitude"
        var.standard_name = "longitude"
        var[:] = np.linspace(lon0, lon1-res, num=x_size)
        
        var = ds.createVariable("latitude", "f8", ("latitude",))
        var.units = "degrees"
        var.long_name = "latitude"
        var.standard_name = "latitude"
        var[:] = np.linspace(lat0, lat1+res, num=y_size)
        
        var = ds.createVariable("flammability", 'f4', ("time", "latitude", "longitude"), fill_value=-9999.9)
        var.long_name = "Flammability Index"
        var.units = '%'
        var[:] = flam[None,...]

        var = ds.createVariable("quality_mask", 'i1', ("time", "latitude", "longitude"), fill_value=0)
        var.long_name = "Quality Mask"
        var.units = 'Cat'
        var[:] = q_mask[None,...]


def get_fmc_functor():
    # Load FMC table
    fmc = np.load("./FMC.npy")
    
    def get_fmc(idxs, fmc=fmc):
        # Select Veg type subset from LUT table
        #mean = np.einsum('i->', fmc[idxs])/idxs.shape[0]
        median = np.median(fmc[idxs])
        return median, np.sqrt(np.einsum('i->',(fmc[idxs]-median)**2)/idxs.shape[0])

    return get_fmc


def get_vegtype_idx(veg_type):
    if veg_type == 1.:
        return (0, 2563)
    elif veg_type == 2.:
        return (2563, 4226)
    elif veg_type == 3.:
        return (4226, 8708)


def get_top_n_functor():
    # Read the LUT table
    lut = np.load("./LUT.npy")
    lut = lut[:, [0,1,3,5,6,7]]

    # This term is sqrt(sum(v^2)) in the FMC equation's denominator and is constant (precomputed)
    lut_sq = np.sqrt(np.einsum('ij,ij->i',lut, lut))

    def get_top_n(mb, veg_type, top_n, mat=lut, smat=lut_sq):
        idx = get_vegtype_idx(veg_type)

        # Select Veg type subset from LUT table
        vmat = mat[idx[0]:idx[1], :]
        vsmat = smat[idx[0]:idx[1]]

        # This is a computational trick that results in a +2x speedup of the code
        # arccos is a decreaing function in the [-1,1] range so we can replace this
        # with a constant linear function as we are only interested in the relative values.
        #err = np.arccos(np.einsum('ij,j->i', vmat, mb)/(np.einsum('i,i->', mb, mb)**.5*vsmat))

        err = -1*np.einsum('ij,j->i', vmat, mb)/(np.einsum('i,i->', mb, mb)**.5*vsmat)

        idxs = np.argpartition(err, top_n)[:top_n] + idx[0]

        return idxs

    return get_top_n
