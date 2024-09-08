from tkinter import DoubleVar, StringVar, Label, messagebox
from tkinter.ttk import Button, Frame

from models.Save import Save
from utils.LogManager import LogManager
from utils.customTkinter.MessageBoxDetails import MessageBoxDetails
from utils.customTkinter.ProgressBarManager import ProgressBarManager
from utils.misc import epochToFrDate


class UpdateView(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.progVal = DoubleVar()
        self.progTxt = StringVar()

        self.controller = controller
        self.createWidgets()
        self.displayWidgets()

    def createWidgets(self):
        def cbUpdateBtn():
            infoStatus, warningStatus, errorStatus = LogManager.LOGTYPE_INFO, LogManager.LOGTYPE_WARNING, LogManager.LOGTYPE_ERROR
            resProcess = self.controller.processPayments()
            if resProcess == "membersListOpen":
                messagebox.showwarning("Liste(s) ouverte(s)", "Veuillez fermer les fichiers contenant une liste d'adhérents avant de procéder à une mise à jour.")
            elif resProcess == infoStatus:
                detailsMsg = LogManager().getLogTypeMsgsAsString("update", infoStatus)
                MessageBoxDetails("Succès de la mise à jour", "La mise à jour a été réalisée avec succès.", detailsMsg)
            elif resProcess == warningStatus:
                detailsMsg = LogManager().getLogTypeMsgsAsString("update", warningStatus)
                MessageBoxDetails("Attention", "Tous les paiements n'ont pas pu être traités.\nUne ou plusieurs erreurs sont survenues lors de leur traitement.", detailsMsg, iconType="warning")
            else:
                warningMsg = LogManager().getLogTypeMsgsAsString("update", warningStatus)
                errorMsg = LogManager().getLogTypeMsgsAsString("update", errorStatus)
                detailsMsg = warningMsg + "\n\n" + errorMsg
                MessageBoxDetails("Erreur critique !", "Une ou plusieurs erreurs critiques sont survenues lors du traitement des paiements.", detailsMsg, iconType="error")

            if resProcess in (infoStatus, warningStatus):
                self.lastUpdateLblValue.set(f"Dernière mise à jour : {epochToFrDate(Save().lastUpdate)}")

        def cbOpenDirBtn():
            if not self.controller.openDataDir():
                detailsMsg = LogManager().getLogTypeMsgsAsString("OS", LogManager.LOGTYPE_ERROR)
                MessageBoxDetails("Erreur !", "Impossible d'ouvrir le dossier.", detailsMsg)

        self.updateBtn = Button(self, text="Mettre à jour", command=cbUpdateBtn)
        self.openDirBtn = Button(self, text="Ouvrir le dossier", command=cbOpenDirBtn)

        self.lastUpdateLblValue = StringVar(value=f"Dernière mise à jour : {epochToFrDate(Save().lastUpdate)}")
        self.lastUpdateLbl = Label(self, textvariable=self.lastUpdateLblValue)

        self.progressBar = ProgressBarManager(self)

    def displayWidgets(self):
        self.updateBtn.pack(ipadx=5, ipady=10, pady=15)
        self.openDirBtn.pack(ipadx=5, ipady=5)

        self.lastUpdateLbl.pack(pady=20)

        self.progressBar.pack()

