import typing as t
import logging
from tools.base_server import ABCToolDriver
import requests
import time
from typing import Optional 
from PIL import Image
import io
import os 

class Ot2Driver(ABCToolDriver):
    def __init__(self, robot_ip: str, robot_port: int = 31950) -> None:
        self.robot_ip: str = robot_ip
        self.robot_port: int = robot_port

        self.run_id: Optional[str] = None

        self.base_url = f"http://{robot_ip}:{robot_port}"
        self.headers = {"Opentrons-Version": "2"}

    def ping(self) -> None:
        response = requests.get(
            url=f"{self.base_url}/health",
            headers=self.headers,
        )

        if response.status_code != 200:
            raise Exception("ping failed")
        else:
            logging.info("ping finished")
    
    def toggle_light(self) -> None:
        # Toggle opentrons light
        light_status_response = requests.get(
            url=f"{self.base_url}/robot/lights",
            headers=self.headers,
        )
        if not light_status_response.ok:
            raise Exception(f"get light status failed: {light_status_response.text}")
        light_status: bool = light_status_response.json()['on']

        toggle_light_response = requests.post(
            url=f"{self.base_url}/robot/lights",
            headers=self.headers,
            json={"on": not light_status}
        )
        if not toggle_light_response.ok:
            raise Exception("toggle light failed")


    def schedule_run(self, protocol_file: str) -> str:
        with open(protocol_file, 'rb') as F:
            upload_protocol_response = requests.post(
                url=f"{self.base_url}/protocols",
                files={
                    "files": ('json_program.py', F, "text/x-python-script"),
                },
                headers=self.headers,
            )
        try:
            protocol_id = upload_protocol_response.json()['data']['id']
        except KeyError:
            raise Exception(f"protocol upload failed: {upload_protocol_response.text}")

        # Create a run for the protocol
        create_run_response = requests.post(
            url=f"{self.base_url}/runs",
            json={
                "data": {
                    "protocolId": protocol_id
                }
            },
            headers=self.headers,
        )
        run_id: str = create_run_response.json()['data']['id']
        self.run_id = run_id
        logging.info(f'Created run with id: {self.run_id}')

        # Start run
        start_run_response = requests.post(
            url=f"{self.base_url}/runs/{self.run_id}/actions",
            headers=self.headers,
            json={"data": {"actionType": "play"}}
        )
        if not start_run_response.ok:
            raise Exception("run failed to start")
        
        return run_id

    def pause_protocol(self) -> None:
        if self.run_id:
            pause_run_response = requests.post(
                url=f"{self.base_url}/runs/{self.run_id}/actions",
                headers=self.headers,
                json={"data": {"actionType": "pause"}}
            )
            if not pause_run_response.ok:
                raise Exception("run failed to pause")
    
    def resume_protocol(self) -> None:
        if self.run_id:
            resume_run_response = requests.post(
                url=f"{self.base_url}/runs/{self.run_id}/actions",
                headers=self.headers,
                json={"data": {"actionType": "play"}}
            )
            if not resume_run_response.ok:
                raise Exception("run failed to resume")
    
    def cancel_protocol(self) -> None:
        if self.run_id:
            stop_run_response = requests.post(
                url=f"{self.base_url}/runs/{self.run_id}/actions",
                headers=self.headers,
                json={"data": {"actionType": "stop"}}
            )
            if not stop_run_response.ok:
                raise Exception("run failed to stop")
            delete_run_response = requests.delete(
                url=f"{self.base_url}/runs/{self.run_id}",
                headers=self.headers,
            )
            if not delete_run_response.ok:
                raise Exception("run failed to delete")
            self.run_id = None
    
    def get_run(self, run_id: str) -> t.Any:
        get_run_response = requests.get(
            url=f"{self.base_url}/runs/{run_id}",
            headers=self.headers,
            timeout=30
        )
        if not get_run_response.ok:
            raise Exception(f"get run failed: {get_run_response.text}")
        return get_run_response.json()

    def wait_for_command(self, run_id: str, timeout: int = 1800) -> None:
        seconds: int = 0
        run_status: str = self.get_run(run_id)['data']['status']
        while run_status != 'succeeded':
            if seconds > timeout:
                raise TimeoutError(
                    f"OT Run {run_id} did not complete in {timeout} seconds"
                )
            run_status = self.get_run(run_id)['data']['status']
            logging.info(f"OT Run {run_id} status: {run_status}")
            if run_status in ['stopped', 'failed', 'blocked-by-open-door']:
                raise Exception(f"OT Run {run_id} failed")
            if run_status in ['succeeded']:
                return None
            time.sleep(1)
            seconds += 1

    def start_protocol(self, protocol_file: str) -> None:
        logging.info(f"starting protocol {protocol_file}")
        run_id = self.schedule_run(protocol_file=protocol_file)
        self.wait_for_command(run_id)
        time.sleep(2)
    
    def take_picture(self, name:str, directory:str) -> None:
        response = requests.post(
            url=f"{self.base_url}/camera/picture",
            headers=self.headers,
        )
        if not response.ok:
            raise Exception("Failed to take picture")
        
        image = Image.open(io.BytesIO(response.content))
        rotated_image = image.rotate(180)
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_path : str = os.path.join(directory,name)
        rotated_image.save(file_path, format="JPEG")

