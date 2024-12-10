import os
import glob

tiles = glob.glob('/g/data/ub8/au/FMC/daily_lfmc/*.nc')
years = sorted(set([i.split('/')[-1].split('_')[2] for i in tiles]))

if __name__ == "__main__":
    for year in years:
        print(year)
        os.system('qsub -v "year={0}" /g/data/xc0/user/scortechini/github/fire-data-processing/gadi_tasks/au_one_time_qsubs/au_fmc_mosaics_different_path.qsub'.format(year))
