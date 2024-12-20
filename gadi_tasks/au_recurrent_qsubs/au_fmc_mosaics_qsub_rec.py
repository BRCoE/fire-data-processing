import os

if __name__ == "__main__":
    for year in range(2025,2026):
        print(year)
        os.system('qsub -v "year={0}" /g/data/wj98/AFMS/fire-data-processing/gadi_tasks/au_recurrent_qsubs/au_fmc_mosaics_rec.qsub'.format(year))
