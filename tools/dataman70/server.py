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
  
  def Scan(self, params: Command.Scan) -> None:
    self.driver.scan_barcode(params.mapped_variable)
  
  def AssertBarcode(self, params: Command.AssertBarcode) -> None:
    self.driver.assert_barcode(params.barcode)

  def EstimateScan(self, params: Command.Scan) -> int:
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
