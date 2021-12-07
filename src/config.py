from pathlib import Path

from pydantic import BaseSettings


fpath = Path(__file__).parents[1].absolute()


class ProjectConfig(BaseSettings):
    db_path: str = str(fpath / Path("data/Data scientist exercise.db"))
    raw_records: str = "access_log"
    clean_records: str = "clean_log"
    random_seed: int = 1234
