import json
from typing import Any
from pathlib import Path
from pydantic import BaseSettings, DirectoryPath, FilePath, HttpUrl

def json_source(settings: BaseSettings) -> dict[str, Any]:
    return json.loads(Path("config.json").read_text())

class Settings(BaseSettings):
    rival_search_url: HttpUrl
    log_directory: DirectoryPath
    cookie_path: FilePath
    
    class Config:
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                json_source,
                env_settings,
                file_secret_settings,
            )
