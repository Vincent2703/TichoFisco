import os.path
import re
from os.path import isabs
from tkinter import filedialog, END

from models.Save import Save
from utils import misc


class Settings:
    def __init__(self, view=None):
        self.view = view
        self.settings = Save().settings

    def setView(self, view):
        self.view = view

    def openPathDialog(self, source, askFor="directory"):
        widget = self.view.fields[source]["text"]

        if askFor == "directory":
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfile()

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

        if Save().saveSettings(newSettings):  # todo : afficher message
            pass
        else:
            pass
