import os
import re
import glob
import datetime
import xarray as xr
import pandas as pd
import numpy as np

modis_band_map = {
    'Nadir_Reflectance_Band1': 'red_630_690',
    'Nadir_Reflectance_Band2': 'nir1_780_900',
    'Nadir_Reflectance_Band3': 'blue_450_520',
    'Nadir_Reflectance_Band4': 'green_530_610',
    'Nadir_Reflectance_Band5': 'nir2_1230_1250',
    'Nadir_Reflectance_Band6': 'swir1_1550_1750',
    'Nadir_Reflectance_Band7': 'swir2_2090_2350',
}


def add_tile_coords(tile, dataset):
    scale = 1111950.5196669996
    regex = re.compile('h\d+v\d+')
    matches = regex.findall(tile)
    extract = re.compile('\d+')
    h, v = extract.findall(matches[0])
    h = int(h)
    v = int(v)
    x_start = scale * (h - 18)
    x_end = scale * (h - 17)
    y_start = -scale * (v - 9)
    y_end = -scale * (v - 8)
    dataset['x'] = xr.IndexVariable('x', np.linspace(x_start, x_end, 2400))
    dataset['y'] = xr.IndexVariable('y', np.linspace(y_start, y_end, 2400))
    return dataset


def difference_index(a, b):
    """A common pattern, eg NDVI, NDII, etc."""
    return ((a - b) / (a + b)).astype('float32')


def get_reflectance(year, tile):
    global reflectance_file_cache
    if not reflectance_file_cache:
        reflectance_file_cache[:] = sorted(glob.glob(
            '/g/data/u39/public/data/modis/lpdaac-tiles-c6/MCD43A4.006/' +
            '{year}.??.??/MCD43A4.A{year}???.h??v??.006.*.hdf'
            .format(year=year)
        ))
    files = [f for f in reflectance_file_cache if tile in os.path.basename(f)]
    pattern = re.compile(r'MCD43A4.A\d{4}(?P<day>\d{3}).h\d\dv\d\d.006.\d+'
                         '.hdf')
    dates, parts = [], []
    for f in files:
        try:
            parts.append(xr.open_dataset(f, chunks=2400))
            day, = pattern.match(os.path.basename(f)).groups()
            dates.append(datetime.date(int(year), 1, 1) +
                         datetime.timedelta(days=int(day) - 1))
        except Exception:
            print('Could not read from ' + f)

    dates = pd.to_datetime(dates)
    dates.name = 'time'

    ds = xr.concat(parts, dates)
    out = xr.Dataset()
    for i in map(str, range(1, 8)):
        key = 'Nadir_Reflectance_Band' + i
        data_ok = ds['BRDF_Albedo_Band_Mandatory_Quality_Band' + i] == 0
        out[modis_band_map[key]] = ds[key].where(data_ok).astype('f4')
    out['ndvi_ok_mask'] = 0.15 < difference_index(
                                        out.nir1_780_900, out.red_630_690)
    out['ndii'] = difference_index(out.nir1_780_900, out.swir1_1550_1750)

    out.rename({'YDim:MOD_Grid_BRDF': 'y',
                'XDim:MOD_Grid_BRDF': 'x'}, inplace=True)
    out.time.encoding.update(dict(
        units='days since 1900-01-01', calendar='gregorian', dtype='i4'))
    return add_tile_coords(out)