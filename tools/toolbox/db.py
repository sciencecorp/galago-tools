import json
import logging
from pathlib import Path
from typing import Any, Union

import appdirs  # type: ignore
import requests

APP_NAME = "galago"
APP_AUTHOR = "sciencecorp"
DATA_DIR = Path(appdirs.user_data_dir(APP_NAME, APP_AUTHOR))
CONFIG_FILE = DATA_DIR / "api_config.json"


class Db:
    _api_url = "http://localhost:8000/api"  # Default

    @classmethod
    def get_api_url(cls) -> str:
        """Get the current API URL from config file or use default"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r") as f:
                    config: dict[str, Any] = json.load(f)
                    url = config.get("api_url", cls._api_url)
                    return str(url) if url else cls._api_url
        except Exception as e:
            logging.warning(f"Failed to read API config: {e}")
        return cls._api_url

    @classmethod
    def set_api_url(cls, url: str) -> bool:
        """Save API URL to config file"""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump({"api_url": url}, f)
            cls._api_url = url
            logging.info(f"API URL updated to: {url}")
            return True
        except Exception as e:
            logging.error(f"Failed to save API config: {e}")
            return False

    @classmethod
    def check_connection(cls) -> bool:
        try:
            api_url = cls.get_api_url()
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            return False
        except requests.exceptions.Timeout:
            return False
        return False

    @classmethod
    def get_data(cls, model: str) -> Any:
        api_url = cls.get_api_url()
        response = requests.get(f"{api_url}/{model}")
        return response.json()

    @classmethod
    def get_by_id_or_name(cls, id: Union[int, str], model: str) -> Any:
        api_url = cls.get_api_url()
        response = requests.get(f"{api_url}/{model}/{id}")
        if response.status_code == 404:
            logging.warning(f"Resource with id/name {id} not found in {model}.")
            return None
        return response.json()

    @classmethod
    def post_data(cls, data: dict, model: str) -> Any:
        api_url = cls.get_api_url()
        response = requests.post(f"{api_url}/{model}", json=data)
        return response.json()

    @classmethod
    def delete_data(cls, id: Union[int, str], model: str) -> Any:
        api_url = cls.get_api_url()
        response = requests.delete(f"{api_url}/{model}/{id}")
        return response.json()

    @classmethod
    def update_data(cls, id: Union[str, int], data: dict, model: str) -> Any:
        api_url = cls.get_api_url()
        response = requests.put(f"{api_url}/{model}/{id}", json=data)
        return response.json()

    @classmethod
    def ping(cls, times: int) -> bool:
        api_url = cls.get_api_url()
        for i in range(times):
            try:
                response = requests.get(f"{api_url}/health", timeout=5)
                logging.info(f"Response status code: {response.status_code}")
                if response.status_code == 200:
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                continue
        return False
