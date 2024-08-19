from tkinter import IntVar, DoubleVar, StringVar, Label, X, RIGHT, LEFT
from tkinter.ttk import Progressbar, Button, Frame

from utils.LogManager import LogManager
from utils.MessageBoxDetails import MessageBoxDetails


class UpdateView(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.progVal = DoubleVar()
        self.progTxt = StringVar()

        self.controller = controller
        self.createWidgets()
        self.displayWidgets()

    def createWidgets(self):
        def cbUpdateBtn():  # A mettre dans le modèle ?
            infoStatus, warningStatus, errorStatus = LogManager.LOGTYPE_INFO, LogManager.LOGTYPE_WARNING, LogManager.LOGTYPE_ERROR
            resProcess = self.controller.processPayments()
            if resProcess == infoStatus:
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

        def cbOpenDirBtn():
            if not self.controller.openDataDir():
                detailsMsg = LogManager().getLogTypeMsgsAsString("OS", LogManager.LOGTYPE_ERROR)
                MessageBoxDetails("Erreur !", "Impossible d'ouvrir le dossier.", detailsMsg)

        self.updateBtn = Button(self, text="Mettre à jour", command=cbUpdateBtn)
        self.openDirBtn = Button(self, text="Ouvrir le dossier", command=cbOpenDirBtn)

        self.updatePrgb = Progressbar(self, variable=self.progVal)
        self.updateLbl = Label(self, textvariable=self.progTxt)

    def displayWidgets(self):
        self.updateBtn.pack()
        self.openDirBtn.pack()

        self.updatePrgb.pack(padx=20, pady=10, side=LEFT, fill=X, expand=True)
        self.updateLbl.pack(padx=20, pady=10, side=RIGHT)

