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
        """Test connection to the OT-2 robot."""
        response = requests.get(
            url=f"{self.base_url}/health",
            headers=self.headers,
        )

        if response.status_code != 200:
            raise Exception(f"Ping failed with status {response.status_code}: {response.text}")
        else:
            logging.info("OT-2 ping successful")
    
    def toggle_light(self) -> None:
        """Toggle the OT-2 deck lights on/off."""
        try:
            # Get current light status
            light_status_response = requests.get(
                url=f"{self.base_url}/robot/lights",
                headers=self.headers,
            )
            if not light_status_response.ok:
                raise Exception(f"Failed to get light status: {light_status_response.text}")
            
            light_status: bool = light_status_response.json()['on']
            logging.info(f"Current light status: {'ON' if light_status else 'OFF'}")

            # Toggle light status
            toggle_light_response = requests.post(
                url=f"{self.base_url}/robot/lights",
                headers=self.headers,
                json={"on": not light_status}
            )
            if not toggle_light_response.ok:
                raise Exception(f"Failed to toggle lights: {toggle_light_response.text}")
            
            new_status = "ON" if not light_status else "OFF"
            logging.info(f"Lights toggled to: {new_status}")
            
        except Exception as e:
            logging.error(f"Error toggling lights: {e}")
            raise

    def upload_and_schedule_protocol(self, protocol_file: str) -> str:
        """Upload protocol file and create a scheduled run."""
        try:
            # Upload protocol
            with open(protocol_file, 'rb') as f:
                upload_response = requests.post(
                    url=f"{self.base_url}/protocols",
                    files={
                        "files": ('protocol.py', f, "text/x-python-script"),
                    },
                    headers=self.headers,
                )
            
            if not upload_response.ok:
                raise Exception(f"Protocol upload failed: {upload_response.text}")
                
            try:
                protocol_id = upload_response.json()['data']['id']
                logging.info(f"Protocol uploaded with ID: {protocol_id}")
            except KeyError:
                raise Exception(f"Invalid upload response format: {upload_response.text}")

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
            
            if not create_run_response.ok:
                raise Exception(f"Failed to create run: {create_run_response.text}")
                
            run_id: str = create_run_response.json()['data']['id']
            self.run_id = run_id
            logging.info(f'Created run with ID: {self.run_id}')
            
            return run_id
            
        except Exception as e:
            logging.error(f"Error uploading and scheduling protocol: {e}")
            raise

    def start_run(self, run_id: str) -> None:
        """Start a scheduled protocol run."""
        try:
            start_response = requests.post(
                url=f"{self.base_url}/runs/{run_id}/actions",
                headers=self.headers,
                json={"data": {"actionType": "play"}}
            )
            if not start_response.ok:
                raise Exception(f"Failed to start run: {start_response.text}")
            
            logging.info(f"Started run: {run_id}")
            
        except Exception as e:
            logging.error(f"Error starting run {run_id}: {e}")
            raise

    def pause_protocol(self) -> None:
        """Pause the currently running protocol."""
        if not self.run_id:
            logging.warning("No active run to pause")
            return
            
        try:
            pause_response = requests.post(
                url=f"{self.base_url}/runs/{self.run_id}/actions",
                headers=self.headers,
                json={"data": {"actionType": "pause"}}
            )
            if not pause_response.ok:
                raise Exception(f"Failed to pause run: {pause_response.text}")
            
            logging.info(f"Paused run: {self.run_id}")
            
        except Exception as e:
            logging.error(f"Error pausing run: {e}")
            raise
    
    def resume_protocol(self) -> None:
        """Resume a paused protocol."""
        if not self.run_id:
            logging.warning("No active run to resume")
            return
            
        try:
            resume_response = requests.post(
                url=f"{self.base_url}/runs/{self.run_id}/actions",
                headers=self.headers,
                json={"data": {"actionType": "play"}}
            )
            if not resume_response.ok:
                raise Exception(f"Failed to resume run: {resume_response.text}")
            
            logging.info(f"Resumed run: {self.run_id}")
            
        except Exception as e:
            logging.error(f"Error resuming run: {e}")
            raise
    
    def cancel_protocol(self) -> None:
        """Cancel and delete the currently running protocol."""
        if not self.run_id:
            logging.warning("No active run to cancel")
            return
            
        try:
            # Stop the run
            stop_response = requests.post(
                url=f"{self.base_url}/runs/{self.run_id}/actions",
                headers=self.headers,
                json={"data": {"actionType": "stop"}}
            )
            if not stop_response.ok:
                raise Exception(f"Failed to stop run: {stop_response.text}")
            
            # Delete the run
            delete_response = requests.delete(
                url=f"{self.base_url}/runs/{self.run_id}",
                headers=self.headers,
            )
            if not delete_response.ok:
                logging.warning(f"Failed to delete run: {delete_response.text}")
                # Don't raise exception here as the run is already stopped
            
            logging.info(f"Cancelled run: {self.run_id}")
            self.run_id = None
            
        except Exception as e:
            logging.error(f"Error cancelling run: {e}")
            raise
    
    def get_run_status(self, run_id: str) -> dict:
        """Get the current status of a protocol run."""
        try:
            response = requests.get(
                url=f"{self.base_url}/runs/{run_id}",
                headers=self.headers,
                timeout=30
            )
            if not response.ok:
                raise Exception(f"Failed to get run status: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logging.error(f"Error getting run status for {run_id}: {e}")
            raise

    def wait_for_completion(self, run_id: str, timeout: int = 1800) -> None:
        """Wait for a protocol run to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                run_data = self.get_run_status(run_id)
                status = run_data['data']['status']
                
                logging.info(f"Run {run_id} status: {status}")
                
                if status == 'succeeded':
                    logging.info(f"Run {run_id} completed successfully")
                    return
                elif status in ['stopped', 'failed', 'blocked-by-open-door']:
                    raise Exception(f"Run {run_id} failed with status: {status}")
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                if "failed with status" in str(e):
                    raise  # Re-raise status failures
                logging.warning(f"Error checking run status: {e}")
                time.sleep(5)  # Wait longer on communication errors
        
        raise TimeoutError(f"Run {run_id} did not complete within {timeout} seconds")

    def start_protocol(self, protocol_file: str, wait_for_completion: bool = True) -> None:
        """
        Execute a protocol file on the OT-2.
        
        Args:
            protocol_file: Path to the Python protocol file
            wait_for_completion: Whether to wait for the protocol to finish
        """
        try:
            logging.info(f"Starting protocol: {protocol_file}")
            
            # Upload and schedule the protocol
            run_id = self.upload_and_schedule_protocol(protocol_file)
            
            # Start the run
            self.start_run(run_id)
            
            # Wait for completion if requested
            if wait_for_completion:
                self.wait_for_completion(run_id)
                
            logging.info("Protocol execution completed successfully")
            
        except Exception as e:
            logging.error(f"Error executing protocol: {e}")
            raise
    
    def take_picture(self, name: str, directory: str) -> str:
        """
        Take a picture using the OT-2 camera and save it to the specified location.
        
        Args:
            name: Filename for the image
            directory: Directory to save the image
            
        Returns:
            Full path to the saved image file
        """
        try:
            # Take picture via API
            response = requests.post(
                url=f"{self.base_url}/camera/picture",
                headers=self.headers,
            )
            if not response.ok:
                raise Exception(f"Failed to take picture: {response.text}")
            
            # Process and save the image
            image = Image.open(io.BytesIO(response.content))
            rotated_image = image.rotate(180)  # OT-2 camera is upside down
            
            # Ensure directory exists
            os.makedirs(directory, exist_ok=True)
            
            # Save image
            file_path = os.path.join(directory, name)
            rotated_image.save(file_path, format="JPEG")
            
            logging.info(f"Picture saved: {file_path}")
            return file_path
            
        except Exception as e:
            logging.error(f"Error taking picture: {e}")
            raise

    def close(self) -> None:
        """Clean up resources and cancel any running protocols."""
        try:
            if self.run_id:
                logging.info("Cleaning up active run on close")
                self.cancel_protocol()
        except Exception as e:
            logging.warning(f"Error during cleanup: {e}")