from pathlib import Path

from pydantic import BaseSettings

fpath = Path(__file__).parents[1].absolute()


class ProjectConfig(BaseSettings):
    db_path: Path = fpath / Path("data/Data scientist exercise.db")
    fig_path: Path = fpath / Path("reports/figs")
    raw_records: str = "access_log"
    clean_records: str = "clean_log"
    random_seed: int = 1234
