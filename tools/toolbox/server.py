import logging
from tools.base_server import ToolServer, serve
from tools.grpc_interfaces.toolbox_pb2 import Command, Config
from tools.app_config import Config as GlobalConfig
from .data import Data 
from tools.grpc_interfaces.tool_base_pb2 import ExecuteCommandReply
import argparse 
from tools.toolbox.slack import Slack 
from google.protobuf.struct_pb2 import Struct
from tools.grpc_interfaces.tool_base_pb2 import  SUCCESS, ERROR_FROM_TOOL
from tools.grpc_interfaces import tool_base_pb2
from tools.toolbox.python_subprocess import run_python_script

class ToolBoxServer(ToolServer):
     toolType = "toolbox"

     def __init__(self) -> None:
          super().__init__()
          self.app_config = GlobalConfig()
          self.app_config.load_workcell_config()
          self.slack = Slack(self.app_config)
          self.setStatus(tool_base_pb2.READY)

     def _configure(self, request:Config) -> None:
          return
     
     # def SlackMessage(self, params:Command.SlackMessage) -> None:
     #      if self.app_config.app_config.slack_workcell_channel:
     #           self.slack.slack_message(message=params.message, recipient=self.app_config.app_config.slack_workcell_channel)

     def LogMediaExchange(self, params:Command.LogMediaExchange) -> None: 
         #Data.log_media_exchange(params.source_barcode, params.destination_name, params.destination_barcode,params.source_wells, params.percent_exchange,params.new_tips)
          return None 
     
     def GetWorkcells(self, params:Command.GetWorkcells) -> ExecuteCommandReply:
          s  = Struct()
          response = ExecuteCommandReply()
          response.return_reply = True
          response.response = SUCCESS
          try:
               workcells = Data.get_workcells()
               if workcells:
                    s.update({'workcells':workcells})
               else:
                   s.update({'workcells':[]})
               response.meta_data.CopyFrom(s)
          except Exception as exc:
               logging.exception(exc)
               response.response = ERROR_FROM_TOOL

          return response
     
     def GetLiconicSensorData(self, params:Command.GetLiconicSensorData) -> None:
          return None 
          # s  = Struct()
          # response = ExecuteCommandReply()
          # response.return_reply = True
          # response.response = SUCCESS
          # try:
          #      data = Data.get_liconic_sensor_data(params.tool_id, params.date)
          #      if data:
          #           s.update(data)
          #      else:
          #           s.update({'times':[],'co2_values':[]})
          #      response.meta_data.CopyFrom(s)
          # except Exception as exc:
          #      logging.exception(exc)
          #      response.response = ERROR_FROM_TOOL

          # return response

     
     def GetOT2ImagesByDate(self, params:Command.GetOT2ImagesByDate) -> None:
          return None 
          #s  = Struct()
          # response = ExecuteCommandReply()
          # response.return_reply = True
          # response.response = SUCCESS
          # try:
          #      data = Data.get_ot2_images_by_date(params.date)
          #      if data:
          #           logging.info("Result should be "+str(data))
          #           s.update({'images':data})
          #      else:
          #           s.update({'images':[]})
          #      response.meta_data.CopyFrom(s)
          # except Exception as exc:
          #      logging.exception(exc)
          #      response.response = ERROR_FROM_TOOL
          # return response
     
     def GetOT2ImageBytes(self, params:Command.GetOT2ImageBytes) -> None:
          return None 
          # s  = Struct()
          # response = ExecuteCommandReply()
          # response.return_reply = True
          # response.response = SUCCESS
          # try:
          #      data = Data.get_ot2_image_bites_by_file_name(params.date, params.image_file)
          #      if data:
          #           s.update(data)
          #      else:
          #          s.update({'created_on':'','img_bytes':''})
          #      response.meta_data.CopyFrom(s)
          # except Exception as exc:
          #      logging.exception(exc)
          #      response.response = ERROR_FROM_TOOL
          # return response
     
     def RunScript(self, params:Command.RunScript) -> ExecuteCommandReply:
          s  = Struct()
          response = ExecuteCommandReply()
          response.return_reply = True
          response.response = SUCCESS
          try:
               result = run_python_script(params.script_content,blocking=True)
               logging.info(f"Script result is {result}")
               if response:
                    s.update({'response':result})
               else:
                    s.update({'response':''})
               response.meta_data.CopyFrom(s)
          except Exception as exc:
               logging.exception(exc)
               response.response = ERROR_FROM_TOOL
               response.error_message = str(exc)
          return response
     
     # def SendSlackAlert(self, params:Command.SendSlackAlert) -> None:
     #      if self.app_config.app_config.slack_error_channel:
     #           self.slack.send_alert_slack(params.workcell, params.tool, params.protocol, params.error_message, self.app_config.app_config.slack_error_channel)
     
     def ClearLastSlackAlert(self, params:Command.ClearLastSlackAlert) -> None:
          # if self.app_config.app_config.slack_error_channel:
          #      self.slack.clear_last_error(self.app_config.app_config.slack_error_channel)
          return None 
     
     def GetLogMediaExchangeByDate(self, params:Command.GetLogMediaExchangeByDate) -> None:
          return None 
          # s  = Struct()
          # response = ExecuteCommandReply()
          # response.return_reply = True
          # response.response = SUCCESS
          # try:
          #      data = Data.get_media_exchange_logs_by_date(params.date)
          #      if data:
          #           logging.info(f"Data is {data}")
          #           s.update({'data':data})
          #      else:
          #          s.update({})
          #      response.meta_data.CopyFrom(s)
          # except Exception as exc:
          #      logging.exception(exc)
          #      response.response = ERROR_FROM_TOOL
          # return response
     
     def ValidateFolder(self, params:Command.ValidateFolder) -> ExecuteCommandReply:
          logging.info("Running validate folder in the server")
          s  = Struct()
          response = ExecuteCommandReply()
          response.return_reply = True
          response.response = SUCCESS
          try:
               data = Data.validate_folder(params.folder_path)
               if data:
                    s.update({'result':True})
               else:
                   s.update({'result':False})
               response.meta_data.CopyFrom(s)
          except Exception as exc:
               logging.exception(exc)
               response.response = ERROR_FROM_TOOL
          return response
             
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port')
    args = parser.parse_args()
    if not args.port:
         raise RuntimeWarning("Port must be provided...")
    serve(ToolBoxServer(), str(args.port))
