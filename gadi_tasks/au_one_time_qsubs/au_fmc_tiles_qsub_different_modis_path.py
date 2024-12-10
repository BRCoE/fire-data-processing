# script for computing LFMC for selected dates
# to avoid

import os
import numpy as np
import xarray as xr
from datetime import datetime
import glob

if __name__=='__main__':

    au_tiles = ['h27v11', 'h27v12', 'h28v11', 'h28v12', 'h28v13', 
                'h29v10', 'h29v11', 'h29v12', 'h29v13', 'h30v10', 
                'h30v11', 'h30v12', 'h31v10', 'h31v11', 'h31v12', 
                'h32v10', 'h32v11']

    dates = [ '2024.10.02','2024.10.03','2024.10.04','2024.10.05','2024.10.07',
                   '2024.10.08','2024.10.10','2024.10.11','2024.10.12','2024.10.14']

    tot_years = sorted(set([i[:4] for i in dates])) # unique years

    for tile in au_tiles:
        for year in tot_years:

            os.system('qsub -v "year={0},tile={1}" /g/data/xc0/user/scortechini/github/fire-data-processing/gadi_tasks/au_one_time_qsubs/au_fmc_tiles_different_modis_path.qsub'.format(year, tile))   
                   
