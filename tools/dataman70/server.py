import logging

from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.dataman70_pb2 import Command, Config

from .driver import Dataman70Driver
import argparse

class Dataman70Server(ToolServer):
  toolType = "dataman70"
  driver: Dataman70Driver
  config: Config

  def __init__(self) -> None:
    super().__init__()
  
  def _configure(self, config: Config) -> None:
    self.config = config
    if self.driver:
      self.driver.close()
    self.driver = Dataman70Driver(self.config.com_port)
    self.driver.barcode_listeners.append(self._on_barcode)
    self.driver.power_on()
  
  def _on_barcode(self, barcode: str) -> None:
    logging.debug(f"Barcode detected! {barcode}")
    self.driver.live = False
  
  def Reset(self, params: Command.Reset) -> None:
    self.driver.power_off()
    self.driver.power_on()

  def AssertBarcode(self, params: Command.AssertBarcode) -> None:
    self.driver.live = True
    barcode = self.driver.read_barcode()
    # Dataman70Driver adds a leading 0 to the barcode because it outputs EAN-13 barcodes
    # barcodes are UPC-A, which are 12 digits long
    # We add a leading 0 to the UPC-A barcode to correctly match the barcode scanned
    logging.debug(f"Barcode scanned: {barcode}")
    if barcode != '0'+params.barcode:
      raise Exception(f"Expected barcode {params.barcode}, got {barcode}")
    return None
  
  def EstimateReset(self, params: Command.Reset) -> int:
    return 5
  
  def EstimateAssertBarcode(self, params: Command.AssertBarcode) -> int:
    return 5

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
        raise RuntimeWarning("Port must be provided...")
    serve(Dataman70Server(), str(args.port))
