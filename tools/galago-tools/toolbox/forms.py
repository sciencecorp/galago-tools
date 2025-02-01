from tkinter import messagebox , StringVar, Tk
import time 
from tkinter import Label
from typing import Optional

class Forms():
    
    def __init__(self) -> None:
        self.total_time = 0

    def show_message(self, title:str, message:str, message_type:str) -> None:
        if message_type == "warning":
            messagebox.showwarning(title, message)
        elif message_type == "error":
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)

    # def show_image(self, title:Optional[str], photo_path: str, width:Optional[int], height:Optional[int]) -> None:
    #     # Create the main window
    #     if not os.path.exists(photo_path):
    #         raise FileNotFoundError() 
        
    #     image_window = tk.Tk()
    #     if not title:
    #         title =  "Image Viewer"
    #     image_window.title(title)
    #     image_window.geometry(f"{width}x{height}")
    #     image_window.configure(background='lightblue')

    #     # Load the image
    #     img  = Image.open(photo_path)
    #     if width and height:
    #         img = img.resize((width, height))
    #     img_tk = ImageTk.PhotoImage(img)

    #     # Create a label to display the image
    #     img_label = Label(image_window, image=img_tk)
    #     img_label.pack(side="top", fill="both", expand=True)

    #     # Run the application
    #     image_window.mainloop()

    def timer(self, time_seconds:int, message:Optional[str]="", show_timer:Optional[bool]=False) -> None:
        if not show_timer:
            time.sleep(time_seconds)
        else:
            self.clock_window = Tk()
            self.clock_window.geometry("300x200")
            self.clock_window.title("Timer")
            self.clock_window.configure(background='white')
            self.total_time = time_seconds
        
            self.time_var = StringVar()
            self.time_var.set("00:00:00")

            self.custom_message_var = StringVar()
            padding = 60
            if message:
                self.custom_message_var.set(message)
                self.custom_message_label = Label(self.clock_window, textvariable=self.custom_message_var, font=('Helvetica', 18), bg='white')
                self.custom_message_label.pack(side='top', pady=20)
                padding = 10
            self.time_label = Label(self.clock_window, textvariable=self.time_var, font=('Helvetica', 48), bg='white')
            self.time_label.pack(side='top', pady=padding)

            self.start_timer()
            self.run()

    def start_timer(self) -> None:
        start_time = time.time()

        def countdown() -> None:
            seconds_spent_waiting = int(time.time() - start_time)
            remaining_time = self.total_time - seconds_spent_waiting

            if remaining_time <= 0:
                self.time_var.set(f"{00:02d}:{00:02d}:{00:02d}")
                self.clock_window.destroy()
                return
            
            self.update_time(remaining_time)
            self.clock_window.after(1000, countdown)

        countdown()

    def run(self) -> None:
        self.clock_window.mainloop()

    def update_time(self, remaining_time:int) -> None:
        hours = remaining_time // 3600
        minutes = (remaining_time % 3600) // 60
        seconds = remaining_time % 60
        self.time_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        return None


# if __name__ == "__main__":
#     f = Forms()
#     f.show_message("Warning", "Hey this is a message", "warning")