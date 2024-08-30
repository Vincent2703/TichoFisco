from tkinter import Frame, BOTH, YES, Text, Button, filedialog, END, Label
from tkinter.constants import BOTTOM
from tkinter.ttk import Notebook, Style

from utils.Thunderbird import Thunderbird
from utils.styles import centerAlign


class SettingsView(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.fields = {}
        self.createWidgets()
        self.displayWidgets()

    def createWidgets(self):
        def createField(frame, labelTxt, name, fieldType, value=False):
            self.fields[name] = {}
            nbRow = len(self.fields)
            self.fields[name]["label"] = Label(frame, text=labelTxt)
            self.fields[name]["label"].grid(row=nbRow, column=0, sticky="w")

            if fieldType in ("directory", "file"):
                self.fields[name]["text"] = Text(frame, height=1, width=50)
                self.fields[name]["button"] = Button(frame, text="Choisir", command=lambda: cbPathBtn(name, askFor=fieldType))
                self.fields[name]["button"].grid(row=nbRow, column=2, padx=5)
            elif fieldType == "text":
                self.fields[name]["text"] = Text(frame, height=1, width=50)
            else:  # textarea
                self.fields[name]["text"] = Text(frame, height=5, width=50)

            if "text" in self.fields[name]:
                self.fields[name]["text"].grid(row=nbRow, column=1, padx=5, pady=10)
                if value:
                    self.fields[name]["text"].insert(END, value)

        def cbPathBtn(source, askFor="directory"):
            self.controller.openPathDialog(source, askFor)

        _style = Style()
        _style.configure("vertical.TNotebook", tabposition="wn")

        self.settingsNtbk = Notebook(self, style="vertical.TNotebook")

        self.thunderbirdFrm = Frame(self.settingsNtbk)
        self.receipts = Frame(self.settingsNtbk)
        self.settingsNtbk.add(self.thunderbirdFrm, text="Thunderbird")
        self.settingsNtbk.add(self.receipts, text="Reçus fiscaux")

        settings = self.controller.settings
        # TODO : Créer dans Save les champs (type, val par defaut etc) : plus qu'à parcourir
        # Thunderbird :
        TBSettings = settings["thunderbird"]
        createField(self.thunderbirdFrm, labelTxt="Dossier de Thunderbird", name="thunderbirdPath", fieldType="directory", value=TBSettings["path"])
        createField(self.thunderbirdFrm, labelTxt="Dossier du profil Thunderbird", name="thunderbirdProfilePath", fieldType="directory", value=TBSettings["profilePath"])
        createField(self.thunderbirdFrm, labelTxt="Adresse mail", name="thunderbirdFromEmail", fieldType="text", value=TBSettings["fromEmail"])
        createField(self.thunderbirdFrm, labelTxt="Sujet du mail", name="thunderbirdEmailSubject", fieldType="text", value=TBSettings["emailSubject"])
        createField(self.thunderbirdFrm, labelTxt="Corps du mail", name="thunderbirdEmailBody", fieldType="textarea", value=TBSettings["emailBody"])

        self.saveBtn = Button(self.settingsNtbk, text="Enregistrer", command=self.controller.saveSettings)

    def displayWidgets(self):
        self.settingsNtbk.pack(fill=BOTH, expand=YES)
        self.saveBtn.pack(side=BOTTOM, pady=20)
