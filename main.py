import logging
from tkinter import Tk

from controllers.MainController import MainController


# Configurer Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    root = Tk()
    root.geometry("800x450")
    controller = MainController(root)
    root.mainloop()
