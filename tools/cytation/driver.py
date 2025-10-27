import typing as t
import os
import datetime
import logging
import time
import traceback
import shutil
import xml.etree.ElementTree as ET
import queue
import threading
from tools.base_server import ABCToolDriver
from typing import Union, Optional
try:
    import pythoncom
    import win32com.client as win32
except Exception:
    # The driver will error if there's no pythoncom
    pass

DEFAULT_EXPERIMENT_DIR = "C:\\cytation_output"
DEFAULT_PROTOCOL_DIR = "C:\\cytation\\protocols"
CYTATION5_READER_TYPE = 21 #Default to Cytation 5


class CytationDriver(ABCToolDriver):
    def __init__(
        self,
        protocol_dir: str,
        experiment_dir: str,
        reader_type: Union[str,int] = CYTATION5_READER_TYPE,
    ) -> None:
        self.experiment_dir = experiment_dir
        self.protocol_dir = protocol_dir
        self.reader_type = reader_type
        self._command_lock: threading.Lock = threading.Lock()
        self.command_queue: queue.Queue = queue.Queue()
        self.command_response_queue: queue.Queue = queue.Queue()
        self.live: bool = False
        self.live_message: str = ""
        self.execution_thread: Optional[threading.Thread] = None
        self.start()

    def start(self) -> None:
        self.kill_processes("Gen5.exe")
        self.live = True
        self.live_message = ""
        self.execution_thread = threading.Thread(target=self.execute_cytation_commands)
        self.execution_thread.daemon = True
        self.execution_thread.start()

    

    def execute_cytation_commands(self) -> None:
        logging.info("Starting cytation command thread")

        try:
            # Required for running COM objects in threads.
            # https://mail.python.org/pipermail/python-win32/2008-June/007788.html
            pythoncom.CoInitialize()
            app = win32.Dispatch("Gen5.Application")
            app.ConfigureUSBReader(self.reader_type, "")
            while self.live:
                while not self.command_queue.empty() > 0:
                    with self._command_lock:
                        command_obj = self.command_queue.get()
                    response = self.execute_command(
                        app,
                        command_obj["command"],
                        command_obj["params"],
                    )
                    with self._command_lock:
                        self.command_response_queue.put(
                            {"command": command_obj["command"], "response": response}
                        )

                time.sleep(0.25)

        except Exception as e:
            logging.warning("Cytation command thread has errored")
            logging.error(traceback.format_exc())
            self.live = False
            self.live_message = str(e)
            pythoncom.CoUninitialize()

    def schedule_command(self, command: str, params: dict[str, t.Any] = {}) -> None:
        logging.info(f"Scheduling command {command}, {params}")
        with self._command_lock:
            self.command_queue.put({"command": command, "params": params})

    def save_picture_builders(self, plate: t.Any, experiment_name: str) -> None:
        logging.info("Saving picture builders...")
        # picture output (do we need this if we get raw tiff files?)
        picture_builder_names = win32.VARIANT(
            pythoncom.VT_VARIANT | pythoncom.VT_BYREF, []
        )
        plate.GetPictureExportNames(False, picture_builder_names)
        logging.info(f"Picture builder names: {picture_builder_names.value}")
        for picture_builder in picture_builder_names.value:
            logging.info(f"Picture builder name: {picture_builder}")
            # write to location defined in protcol
            xml_response = plate.PictureExport(picture_builder)
            # get location and move if not in experiment folder
            save_dir = ET.fromstring(xml_response).findall("Folder")[0].text
            image_name = ET.fromstring(xml_response).findall("Image")[0].text
            if save_dir:
                new_dir = f"{self.experiment_dir}\\{experiment_name}\\{image_name}"
                # check if dir exists
                if not os.path.exists(new_dir):
                    os.makedirs(new_dir)
                # move all files in save_dir that have experiment_name in their name to new_dir
                filenames = ET.fromstring(xml_response).findall("PictureFile")
                for file_element in filenames:
                    filename = file_element.text
                    shutil.move(f"{save_dir}\\{filename}", f"{new_dir}\\{filename}")
                # shutil.move(save_dir, new_dir)

    def save_export_builders(self, plate: t.Any, experiment_name: str) -> None:
        logging.info("Saving export builders...")
        # output exports (metadata and analysis results)
        export_builder_names = win32.VARIANT(
            pythoncom.VT_VARIANT | pythoncom.VT_BYREF, []
        )
        plate.GetFileExportNames(False, export_builder_names)
        logging.info(f"Export builder names: {export_builder_names.value}")
        # export data to location of our choosing
        for export_builder in export_builder_names.value:
            logging.info(f"Export builder name: {export_builder}")
            plate.FileExportEx(
                export_builder,
                f"{self.experiment_dir}\\{experiment_name}\\{experiment_name}_{export_builder}.csv",
            )

    def move_raw_data(self, plate: t.Any, experiment_name: str) -> None:
        logging.info("Raw data export...")
        raw_image_output_folders = win32.VARIANT(
            pythoncom.VT_VARIANT | pythoncom.VT_BYREF, []
        )
        plate.GetImageFolderPaths(raw_image_output_folders)
        image_exp_dirname = os.path.dirname(
            os.path.dirname(raw_image_output_folders.value[0])
        )
        logging.info("Protocol image export folder: " + image_exp_dirname)
        if image_exp_dirname != f"{self.experiment_dir}\\{experiment_name}":
            logging.info("Moving raw data to main experiment output folder...")
            folder_name = os.path.basename(
                os.path.dirname(raw_image_output_folders.value[0])
            )
            shutil.move(
                os.path.dirname(raw_image_output_folders.value[0]),
                f"{self.experiment_dir}\\{experiment_name}\\{folder_name}",
            )

    def execute_command(
        self, app: t.Any, command: str, command_params: dict[str, t.Any]
    ) -> Optional[int]:
        logging.info(f"Executing command {command}")

        if command == "start_read":
            protocol_file = command_params["protocol_file"]
            experiment_name = command_params["experiment_name"]
            well_addresses = command_params["well_addresses"]

            logging.info(f"Wells To Image: {well_addresses}")

            date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # create experiment name if blank
            if experiment_name == "":
                experiment_name = f"auto_{protocol_file}_{date}"
            # check if directory exists
            # if os.path.exists(os.path.join(self.experiment_dir, experiment_name)):
            #     experiment_name = f"{experiment_name}_{date}"
    
            protocol_path = f"{self.protocol_dir}\\{protocol_file}"
            logging.info(f"start_read called with file {protocol_path}")
            experiment_path = (
                f"{self.experiment_dir}\\{experiment_name}\\{experiment_name}.xpt"
            )
            if len(experiment_path) > 250:
                experiment_path= f"{experiment_path[:240]}.xpt"
            logging.info(f"Saving new experiment file to {experiment_path}")
            experiment = app.NewExperiment(protocol_path)
            experiment.SaveAs(experiment_path)
            plate = experiment.plates.GetPlate(1)

            if well_addresses is not None and len(well_addresses) > 0:
                logging.info(f"Setting wells to image to {well_addresses}")
                xml_string = '<BTIPartialPlate Version="1.00"><SingleBlock>No</SingleBlock><Wells>'
                for well_addy in well_addresses:
                    xml_string += f"<Well>{well_addy}</Well>"
                xml_string += "</Wells></BTIPartialPlate>"
                logging.info(f"XML string: {xml_string}")
                plate.SetPartialPlate(xml_string)

            logging.info("Starting read...")
            # We've seen this function call hang indefinitely, which is bad.
            # It's not easy to kill threads in Python, but we might want to look into it,
            # in case the execution thread hangs.
            monitor = plate.StartRead

            # Wait for a moment so the ReadInProgress flag has time to set itself.
            time.sleep(5)

            times = 0
            while monitor.ReadInProgress and self.live:
                if times % 60 == 0:
                    logging.info("Cytation read in progress...")
                times += 1
                time.sleep(1)

            logging.info("Cytation read complete...")

            # output picture builders (PNGs usually)
            self.save_picture_builders(plate, experiment_name)

            # output csvs with metadata and/or analysis results
            self.save_export_builders(plate, experiment_name)

            # move raw data to main experiment output folder if necessary
            # FOR NOW WE ARE NOT DOING THIS, WANT TO ADD IN MAKING IT OPTIONAL
            # self.move_raw_data(plate, experiment_name)

        elif command == "open_carrier":
            app.CarrierOut()
        elif command == "close_carrier":
            app.CarrierIn()
        elif command == "test_reader_communication":
            reader_state: int = app.TestReaderCommunication
            logging.info(f"Got reader state {reader_state}")
            return reader_state
        return None

    def wait_for_command(
        self, command: str, timeout:Optional[int] = None
    ) -> Optional[Union[str,int]]:
        times = 0
        start_time = time.time()

        while self.live:
            seconds_spent_waiting = int(time.time() - start_time)
            if timeout and seconds_spent_waiting > timeout:
                raise Exception(
                    f"Command {command} has timed out. Please reset the driver."
                )

            if not self.command_response_queue.empty() > 0:
                with self._command_lock:
                    command_obj: dict[str, str] = self.command_response_queue.get()
                    if command_obj["command"] == command:
                        logging.info(
                            f"Command {command} has completed. Waited for {seconds_spent_waiting} seconds"
                        )
                        return command_obj["response"]
                    else:
                        logging.warning(
                            f"Unexpected command {command_obj['command']} received"
                        )
            times += 1
            if not self.live:
                break

            if times % 60 == 0:
                logging.info(
                    f"Waiting for Cytation {command} command...({seconds_spent_waiting}s)"
                )
            time.sleep(1)

        if not self.live:
            raise Exception(
                f"Cytation driver has crashed. Please reset the driver. {self.live_message}"
            )
        return None

    def start_read(
        self,
        protocol_file: str,
        experiment_name: str = "",
        well_addresses: t.Optional[t.List[str]] = None,
    ) -> None:
        if not protocol_file.endswith(".prt"):
            protocol_file = f"{protocol_file}.prt"
        self.schedule_command(
            "start_read",
            {
                "protocol_file": protocol_file,
                "experiment_name": experiment_name,
                "well_addresses": well_addresses,
            },
        )

        self.wait_for_command("start_read")

    def open_carrier(self) -> None:
        self.schedule_command(
            "open_carrier",
        )
        self.wait_for_command("open_carrier")

    def close_carrier(self) -> None:
        self.schedule_command("close_carrier")
        self.wait_for_command("close_carrier")

    def close(self) -> None:
        self.live = False
        if self.execution_thread:
            self.execution_thread.join()

    """
        Test whether we can connect to the Cytation reader.
    """

    def _test_reader_communication(self) -> Optional[Union[str, int]]:
        self.schedule_command(
            "test_reader_communication",
        )
        return self.wait_for_command("test_reader_communication", timeout=8)

    def verify_reader_communication(self) -> None:
        reader_state: Optional[Union[str,int]] = self._test_reader_communication()

        if reader_state != 1:
            raise Exception(f"Expected reader state 1. Got {reader_state}")

    def __del__(self) -> None:
        """Disconnect from the device when the driver is destroyed."""
        self.close()
