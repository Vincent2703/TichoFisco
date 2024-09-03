from tkinter import Frame, Text, Button, END, Label, messagebox
from tkinter.constants import WORD
from tkinter.ttk import Notebook, Style

from models.Save import Save
from utils import FileManager
from utils.LogManager import LogManager
from utils.MessageBoxDetails import MessageBoxDetails
from utils.styles import widthCols

# Constantes pour les types de champs
FIELD_TYPE_DIRECTORY = "directory"
FIELD_TYPE_FILE = "file"
FIELD_TYPE_TEXT = "text"
FIELD_TYPE_INT = "int"
FIELD_TYPE_TEXTAREA = "textarea"

class SettingsView(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.fields = {}
        self.actionButtons = {}
        self.createWidgets()
        self.displayWidgets()

    def createWidgets(self):
        def createField(frame, label, name, fieldType, value=None):
            self.fields[name] = {}
            nbRow = len(self.fields)
            self.fields[name]["label"] = Label(frame, text=label)
            self.fields[name]["label"].grid(row=nbRow, column=0, sticky="w")

            if fieldType in (FIELD_TYPE_DIRECTORY, FIELD_TYPE_FILE):
                self.fields[name]["text"] = Text(frame, height=1, width=50, wrap=WORD)
                self.fields[name]["button"] = Button(frame, text="Choisir", command=lambda: self.cbPathBtn(name, askFor=fieldType))
                self.fields[name]["button"].grid(row=nbRow, column=2, padx=5)
            elif fieldType == FIELD_TYPE_TEXT:
                self.fields[name]["text"] = Text(frame, height=1, width=50, wrap=WORD)
            elif fieldType == FIELD_TYPE_INT:
                self.fields[name]["text"] = Text(frame, height=1, width=5)
            elif fieldType == FIELD_TYPE_TEXTAREA:
                self.fields[name]["text"] = Text(frame, height=5, width=50, wrap=WORD)

            if "text" in self.fields[name]:
                self.fields[name]["text"].grid(row=nbRow, column=1, padx=5, pady=10)
                if value:
                    self.fields[name]["text"].insert(END, value)

        def createActionButton(frame, text, action):
            nb = len(self.actionButtons)
            id = f"actionBtn{nb + 1}"
            # Création du bouton
            self.actionButtons[id] = Button(frame, text=text, command=action)
            # Centrage du bouton avec columnspan et sticky
            self.actionButtons[id].grid(row=nb+1, column=0, padx=5, pady=5, columnspan=2)

        _style = Style()
        _style.configure("vertical.TNotebook", tabposition="wn")

        self.settingsNtbk = Notebook(self, style="vertical.TNotebook")

        self.thunderbirdFrm = Frame(self.settingsNtbk)
        self.receiptsFrm = Frame(self.settingsNtbk)
        self.dataFrm = Frame(self.settingsNtbk)

        self.settingsNtbk.add(self.thunderbirdFrm,  text=" Thunderbird ")
        self.settingsNtbk.add(self.receiptsFrm,     text="Reçus fiscaux")
        self.settingsNtbk.add(self.dataFrm,         text="    Données    ")

        settings = self.controller.settings
        # Thunderbird :
        TBSettings = settings["thunderbird"]
        createField(self.thunderbirdFrm, label="Dossier de Thunderbird", name="thunderbirdPath", fieldType=FIELD_TYPE_DIRECTORY, value=TBSettings["path"])
        createField(self.thunderbirdFrm, label="Dossier du profil Thunderbird", name="thunderbirdProfilePath", fieldType=FIELD_TYPE_DIRECTORY, value=TBSettings["profilePath"])
        createField(self.thunderbirdFrm, label="Adresse mail", name="thunderbirdFromEmail", fieldType=FIELD_TYPE_TEXT, value=TBSettings["fromEmail"])
        createField(self.thunderbirdFrm, label="Sujet du mail", name="thunderbirdEmailSubject", fieldType=FIELD_TYPE_TEXT, value=TBSettings["emailSubject"])
        createField(self.thunderbirdFrm, label="Corps du mail", name="thunderbirdEmailBody", fieldType=FIELD_TYPE_TEXTAREA, value=TBSettings["emailBody"])

        # Receipts
        RSettings = settings["receipts"]
        createField(self.receiptsFrm, label="Montant minimum édition", name="receiptsMinimalAmount", fieldType=FIELD_TYPE_INT, value=RSettings["minimalAmount"])
        createField(self.receiptsFrm, label="Modèle du reçu", name="receiptsPdfTemplatePath", fieldType=FIELD_TYPE_FILE, value=RSettings["pdfTemplatePath"])

        # Data
        createActionButton(self.dataFrm, text="Supprimer tous les reçus", action=lambda: self.cbActionBtn("deleteAllReceipts"))
        createActionButton(self.dataFrm, text="Supprimer toutes les listes d'adhérents", action=lambda: self.cbActionBtn("deleteAllMemberLists"))
        createActionButton(self.dataFrm, text="Supprimer le fichier de cache", action=lambda: self.cbActionBtn("deleteCache"))

        self.saveBtn = Button(self, text="Enregistrer", command=self.controller.saveSettings)

        # Ajouter un événement pour gérer le changement d'onglet (pour cacher le bouton d'enregistrement sur le dernier onglet)
        self.settingsNtbk.bind("<<NotebookTabChanged>>", self.onTabChanged)

    def onTabChanged(self, event):
        selectedTab = event.widget.index(event.widget.select())

        # Si l'onglet sélectionné est "Données" (index 2), masquer le bouton "Enregistrer"
        if selectedTab == 2:
            self.saveBtn.grid_remove()
        else:
            self.saveBtn.grid(row=1, column=0, pady=20, sticky="s")

    def cbPathBtn(self, name, askFor="directory"):
        widget = self.fields[name]["text"]
        self.controller.openPathDialog(widget, askFor)

    def cbActionBtn(self, actionName):
        res = True
        if actionName == "deleteAllReceipts":
            res = FileManager.deleteAllReceipts()
        elif actionName == "deleteAllMemberLists":
            res = FileManager.deleteAllMemberLists()
        elif actionName == "deleteCache":
            res = Save().fullReset()

        if res:
            messagebox.showinfo("Action effectuée", "L'action a été effectuée avec succès.")
        else:
            detailsMsg = LogManager().getLogTypeMsgsAsString("OS")
            MessageBoxDetails("Une erreur est survenue", f"Un problème est survenu lors de l'exécution de l'action. ({actionName})", detailsMsg)

    def displayWidgets(self):
        self.settingsNtbk.grid(row=0, column=0, sticky="nsew")

        if self.settingsNtbk.index("current") != 2:  # Si ce n'est pas l'onglet "Données"
            self.saveBtn.grid(row=1, column=0, pady=20, sticky="s")  # On affiche le bouton pour enregistrer

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Centrer les boutons d'action
        self.dataFrm.grid_columnconfigure(0, weight=1)
        self.dataFrm.grid_columnconfigure(1, weight=1)