import os

if __name__ == "__main__":
    for year in range(2001,2020):
        print(year)
        os.system('qsub -v "year={0}" /g/data/xc0/user/scortechini/github/fire-data-processing/gadi_tasks/au_fmc_mosaics.qsub'.format(year))
