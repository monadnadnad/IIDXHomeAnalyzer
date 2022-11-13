# Infra
import json

with open("config.json") as f:
    config = json.load(f)

def rival_search_url() -> str:
    return config["rival_search_url"]

def log_directory() -> str:
    return config["log_directory"]

def cookie_path() -> str:
    return config["cookie_path"]