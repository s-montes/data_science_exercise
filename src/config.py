from pydantic import BaseSettings


class ProjectConfig(BaseSettings):
    db_path: str = "../data/Data scientist exercise.db"
    raw_records: str = "access_log"
    clean_records: str = "clean_log"
