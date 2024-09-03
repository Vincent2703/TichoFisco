import tkinter as tk
import tkinter.ttk as ttk

from utils.PathManager import PathManager
from utils.misc import centerTkinterWindow


class MessageBoxDetails(tk.Toplevel):  # Basé sur https://stackoverflow.com/a/50650817

    def __init__(self, title, message, detail='', iconType="info"):
        super().__init__()
        self.iconsPaths = PathManager().getPaths()["assets"]["icons"]

        self.details_expanded = False
        self.title(title)
        self.defaultSize = "550x75"
        self.extendedSize = "550x160"
        self.geometry(self.defaultSize)
        self.minsize(350, 75)
        self.resizable(False, False)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        centerTkinterWindow(self)

        button_frame = tk.Frame(self)
        button_frame.grid(row=0, column=0, sticky="nsew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        text_frame = tk.Frame(self)
        text_frame.grid(row=1, column=0, padx=(7, 7), pady=(7, 7), sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        if iconType == "info":
            icon = tk.PhotoImage(master=text_frame, file=self.iconsPaths["info"])  # Assuming you have an 'info_icon.png' file
        elif iconType == "warning":
            icon = tk.PhotoImage(master=text_frame, file=self.iconsPaths["warning"])  # Assuming you have a 'warning_icon.png' file
        elif iconType == "error":
            icon = tk.PhotoImage(master=text_frame, file=self.iconsPaths["error"])  # Assuming you have an 'error_icon.png' file
        else:
            icon = None

        if icon:
            ttk.Label(button_frame, image=icon).grid(row=0, column=0, padx=(7, 2), pady=(7, 7), sticky='w')
        ttk.Label(button_frame, text=message).grid(row=0, column=1, columnspan=3, pady=(7, 7), padx=(7, 7), sticky='w')
        ttk.Button(button_frame, text="OK", command=self.destroy).grid(row=1, column=1, sticky='e')
        ttk.Button(button_frame, text="Détails",
                   command=self._toggle_details).grid(row=1, column=2, padx=(7, 7), sticky='e')

        self.textbox = tk.Text(text_frame, height=6)
        self.textbox.insert("1.0", detail)
        self.textbox.config(state="disabled")
        self.scrollb = tk.Scrollbar(text_frame, command=self.textbox.yview)
        self.textbox.config(yscrollcommand=self.scrollb.set)

        # Keep a reference to prevent garbage collection
        self.icon = icon

        self.grab_set()  # To make the window modal
        self.transient()  # Associate it with the parent window

    def _toggle_details(self):
        if self.details_expanded:
            self.textbox.grid_forget()
            self.scrollb.grid_forget()
            self.resizable(False, False)
            self.geometry(self.defaultSize)
            self.details_expanded = False
        else:
            self.textbox.grid(row=0, column=0, sticky="nsew")
            self.scrollb.grid(row=0, column=1, sticky="nsew")
            self.resizable(True, True)
            self.geometry(self.extendedSize)
            self.details_expanded = True
