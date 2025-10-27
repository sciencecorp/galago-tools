import os

class Data():
    def __init__(self)-> None:
        return
    
    # @staticmethod
    # def get_media_exchange_logs_by_date(date:str) -> list[dict]:
    #     conf = Config()
    #     conf.load_app_config()
    #     data_dir = conf.app_config.data_folder
    #     if not data_dir:
    #         raise RuntimeError("Data directory can't be null")
    #     file= os.path.join(data_dir,"media_addition",f"media_addition_{date}.txt")
    #     result = []
    #     if os.path.exists(file):
    #         with open(file, mode='r') as f:
    #             next(f)
    #             lines = f.readlines()
    #             for line in lines:
    #                 print(f"Line is {line}")
    #                 row : dict = {}
    #                 line_splitted = line.split(",")
    #                 row = {
    #                     "source_barcode":line_splitted[0],
    #                     "destination_name":line_splitted[1],
    #                     "destination_barcode":line_splitted[2],
    #                     "source_wells":line_splitted[3],
    #                     "percent_exchange":line_splitted[4],
    #                     "new_tips":line_splitted[5],
    #                     "created_on":line_splitted[6]
    #                 }
    #                 result.append(row)
                
    #             return list(reversed(result))
    #     else:
    #         return list({})
    #For now we are assuming there is only 1 liconic per workcell, we should id them in case there are more.
    # @staticmethod
    # def get_liconic_sensor_data(liconic_id:str, date:str) -> dict[str, t.Any]:
    #     conf = Config()
    #     conf.load_app_config()
    #     if not conf.app_config.data_folder:
    #         return {'times':[],'co2_values':[]}
    #     liconic_folder = join(conf.app_config.data_folder,"sensors","liconic",date)
    #     response = {}
    #     time_array : list[str]= []
    #     co2_array : list[str] = []
    #     if os.path.exists(liconic_folder) is False:
    #         return {'times':[],'co2_values':[]}
    #     else:
    #         liconic_file = join(liconic_folder,f"{liconic_id}_co2.txt")
    #         with open(liconic_file, mode='r') as file:
    #             next(file)
    #             lines = file.readlines()
    #             for line in lines:
    #                 line_array = line.split(',')
    #                 time = line_array[0]
    #                 co2 = line_array[1].replace("\n","")
    #                 time_array.append(time)
    #                 co2_array.append(co2)
    #             response["times"]=time_array
    #             response["co2_values"]=co2_array
    #         return response
        
    # @staticmethod
    # def get_ot2_images_by_date(date:str) -> list[str]:
    #     conf = Config()
    #     conf.load_app_config()
    #     if not conf.app_config.data_folder:
    #         return []
    #     ot2_images_folder = join(conf.app_config.data_folder,"images","ot2",date)
    #     images = []
    #     if os.path.exists(ot2_images_folder):
    #         images = [x for x in os.listdir(ot2_images_folder) if x.endswith(".jpg") and "predicted" not in x]
    #         # Sort by creation time
    #         images.sort()
    #         #images.sort(key=lambda x: os.path.getctime(os.path.join(ot2_images_folder, x)))

    #     return images
    
    # @staticmethod
    # def get_ot2_image_bites_by_file_name(date:str, file_name:str) -> dict:
    #     conf = Config()
    #     conf.load_app_config()
    #     if not conf.app_config.data_folder:
    #         return {"created_on":"null","img_bytes":"null"}
    #     ot2_image = join(conf.app_config.data_folder,"images","ot2",date,file_name)
    #     if os.path.exists(ot2_image):
    #         try:
    #             time_pattern = r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"
    #             match = re.search(time_pattern, file_name)
    #             if match:
    #                 datetime_string = match.group()
    #                 dt = datetime.strptime(datetime_string, "%Y-%m-%d_%H-%M-%S")
    #                 formatted_datetime = dt.strftime("%m-%d-%Y %H:%M:%S")
    #             else:
    #                 modified_time = os.path.getmtime(ot2_image)
    #                 formatted_datetime = datetime.fromtimestamp(modified_time).strftime('%m-%d-%Y %H:%M:%S')
    #             with open(ot2_image, 'rb') as image_file:
    #                 image_bytes = image_file.read()
    #                 econcoded_string = base64.b64encode(image_bytes).decode('utf-8')
    #             return  {"created_on":formatted_datetime,"img_bytes":f"data:image/jpeg;base64,{econcoded_string}"}
                
    #         except (OSError, IOError) as e:
    #             print(f"Error reading image file {ot2_image}: {e}")
    #             return {"created_on":"null","img_bytes":"null"}
    #         except Exception as e:
    #             print(f"Unexpected error: {e}")
    #             return {"created_on":"null","img_bytes":"null"}
    #     else:
    #         return  {"created_on":"null","img_bytes":"null"}

    # @staticmethod
    # def get_ot2_processed_image_bites_by_file_name(date:str, file_name:str) -> dict:
    #     conf = Config()
    #     conf.load_app_config()
    #     if not conf.app_config.data_folder:
    #         return {"created_on":"null","img_bytes":"null"}
    #     ot2_image = join(conf.app_config.data_folder,"images","ot2",date,file_name)
    #     if not os.path.exists(ot2_image):
    #         return  {"created_on":"null","img_bytes":"null"}
    #     try:
    #         modified_time = os.path.getmtime(ot2_image)
    #         formatted_time = datetime.fromtimestamp(modified_time).strftime('%m-%d-%Y %H:%M:%S')
    #         with open(ot2_image, 'rb') as image_file:
    #             image_bytes = image_file.read()
    #             econcoded_string = base64.b64encode(image_bytes).decode('utf-8')
    #         return  {"created_on":formatted_time,"img_bytes":f"data:image/jpeg;base64,{econcoded_string}"}
    #     except (OSError, IOError) as e:
    #         logging.warning(f"Error reading image file {ot2_image}: {e}")
    #         return  {"created_on":"null","img_bytes":"null"}
    #     except Exception as e:
    #         logging.warning(f"Unexpected error: {e}")
    #         return  {"created_on":"null","img_bytes":"null"}
    
    @staticmethod
    def validate_folder(folder_path:str) -> bool:
        if os.path.exists(folder_path):
            return True
        else:
            return False
        
