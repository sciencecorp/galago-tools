import os 



# def kill_processes(self, process_name: str) -> None:
#         # check if any processes are running (length of returned list is > 0)
#         if len([proc_str for proc_str in os.popen('tasklist').readlines() if proc_str.startswith(process_name)]) > 0:

#             # # ask user with pop whether or not to kill processes
#             # style_flag = 0x00001124 # 1 -> sys modal,no; 1 -> default to NO button; 2 -> add ? icon, 4 -> yes/no button style
#             # return_val = ctypes.windll.user32.MessageBoxW(0, f"Kill running {process_name} processes?", f"Kill {self.__class__} Processes", style_flag)
            
#             # # if "OK" then kill 'em
#             # if return_val == 1:
#             #     logging.info("ABCToolDriver Killing Previously Active %s processes", process_name)
#             #     while len([proc_str for proc_str in os.popen('tasklist').readlines() if proc_str.startswith(process_name)]) > 0:

#             #         # kill process(es)
#             #         os.system(f"taskkill /f /im {process_name}")

for proc_str in os.popen('tasklist').readlines():
    print(proc_str)