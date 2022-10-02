# Infra
import json

with open("config.json") as f:
    config = json.load(f)

def user_agent() -> str:
    return config["user_agent"]

def rival_search_url() -> str:
    return config["rival_search_url"]

def log_directory() -> str:
    return config["log_directory"]
