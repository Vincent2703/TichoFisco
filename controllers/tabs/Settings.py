import os.path
from os.path import isabs
from pathlib import Path
from tkinter import filedialog, END, messagebox

from models.Save import Save
from utils.LogManager import LogManager
from utils.MessageBoxDetails import MessageBoxDetails


class Settings:
    def __init__(self, view=None):
        self.view = view
        self.settings = Save().settings

    def setView(self, view):
        self.view = view

    def openPathDialog(self, widget, askFor="directory"):
        widgetValue = Path(widget.get("1.0", END))

        if askFor == "directory":
            path = filedialog.askdirectory(initialdir=widgetValue.as_posix().strip())
        else:
            dir = widgetValue.parent.as_posix().strip()
            file = widgetValue.name.strip()
            path = filedialog.askopenfile(initialdir=dir, initialfile=file).name

        if path:
            widget.delete(1.0, END)
            widget.insert(END, os.path.normpath(path))

    def saveSettings(self):  # todo : quelque chose de + flexible (def champs dans Save() par ex)
        newSettings = {"thunderbird":{}, "receipts":{}}

        for name, field in self.view.fields.items():
            if "text" in field:
                value = field["text"].get("1.0",END)
                if len(value.strip()) > 0:
                    if "thunderbird" in name:
                        key = name.replace("thunderbird", '')
                        key = key[0].lower() + key[1:]
                        if isabs(value):
                            value = os.path.normpath(value.strip())
                        newSettings["thunderbird"][key] = value

        if Save().saveSettings(newSettings):
            messagebox.showinfo("Enregistrement des options", "L'enregistrement des options a été effectué avec succès.")
        else:
            detailsMsg = LogManager().getLogTypeMsgsAsString("OS")
            MessageBoxDetails("Enregistrement des options", "Un problème est survenu lors de l'enregistrement des options.", detailsMsg)

    def reset(self, type):
        if type == "full":
            pass