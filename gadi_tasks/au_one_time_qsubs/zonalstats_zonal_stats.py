import os

if __name__ == "__main__":
    for area in ['lga']: #['lga','fwa']:
        for var in ['fmc','flam']:
            for year in range(2001,2024):
    
               print(area,var,year)
               os.system('qsub -v "area={0},var={1},year={2}" /g/data/xc0/user/scortechini/github/fire-data-processing/gadi_tasks/au_one_time_qsubs/zonalstats_zonal_stats_relative.qsub'.format(area,var,year))
               os.system('qsub -v "area={0},var={1},year={2}" /g/data/xc0/user/scortechini/github/fire-data-processing/gadi_tasks/au_one_time_qsubs/zonalstats_zonal_stats_absolute.qsub'.format(area,var,year))
