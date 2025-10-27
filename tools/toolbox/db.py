import requests
from typing import Union, Any
import logging

API_URL = "http://localhost:8000/api"

class Db:
    @staticmethod
    def check_connection() -> bool:
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            return False
        return False
    
    @staticmethod
    def get_data(model:str) -> Any:
        response = requests.get(f"{API_URL}/{model}")
        return response.json()

    @staticmethod
    def get_by_id_or_name(id:Union[int,str], model:str) -> Any:
        response = requests.get(f"{API_URL}/{model}/{id}")
        if response.status_code == 404:
            logging.warning(f"Resource with id/name {id} not found in {model}.")
            return None
        return response.json()
    
    @staticmethod
    def post_data(data:dict, model:str) -> Any:
        response = requests.post(f"{API_URL}/{model}", json=data)
        return response.json()

    @staticmethod
    def delete_data(id:Union[int,str], model:str) -> Any:
        response = requests.delete(f"{API_URL}/{model}/{id}")
        return response.json()
    
    @staticmethod
    def update_data(id:Union[str,int], data:dict, model:str) -> Any:
        response = requests.put(f"{API_URL}/{model}/{id}", json=data)
        return response.json()
    
    @staticmethod
    def ping(times:int) -> bool:
        for i in range(times):
            try:
                response = requests.get(f"{API_URL}/health")
                logging.info(f"Response status code: {response.status_code}")
                if response.status_code == 200:
                    return True
            except requests.exceptions.ConnectionError:
                continue
        logging.error("Could not establish connection to database...")
        return False
    