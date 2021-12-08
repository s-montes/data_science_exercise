# Data science technical exercise

## Instructions

- The report containing the analysis can be found at `reports/report.md`
- In order to reproduce the results, the `setup.sh` script can be user:
  - Add `Data scientist exercise.db` to the `data` folder
  - `./setup.sh build_venv` : Creates a local Python environment from the `requirements.txt` file
  - `./setup.sh clean_data` : Cleans the data, prints general metrics for the dataset, and generates plots that are saved in `reports/figs/raw_logs_eda` and `reports/figs/clean_logs_eda`
  - `./setup.sh experiment_report` : Prints the results of the statistical experiments and generates plots for the bootstrapped distributions (`reports/figs/test`)
  - `./setup.sh estimate_percentage` : Prints the results of the percentage increase analysus and generates plots for the distributions (`reports/figs/percentage`)

## Content

- `data` : Folder for the SQLite database
- `docs` : Instructions
- `notebooks` : Scratchpad notebooks for simple experiments
- `reports` : Final report
- `src` : Python scripts
