from tkinter import Frame, Button, messagebox
from tkinter.ttk import Notebook, Combobox, Treeview
from utils.customTkinter.ProgressBarManager import ProgressBarManager
from utils.misc import sortTreeviewCol


class ReceiptsView(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.frames = {}  # Dictionnaire pour stocker les frames
        self.widgets = {}  # Dictionnaire pour stocker tous les widgets
        self.createWidgets()
        self.displayWidgets()


    def createWidgets(self):
        """
        Méthode pour créer les widgets dans l'onglet
        """
        # Fonction pour ajouter un widget au dictionnaire des widgets plus facilement
        def addWidget(widget, widgetName):
            self.widgets[widgetName] = widget

        # Callback pour les Comboboxes de sélection
        def cbxCb(event):
            self.controller.queryUpdate(
                member=self.widgets["membersCbx"].get(),
                year=self.widgets["yearsCbx"].get()
            )

        # Callback pour préparer les emails
        def cbPrepareEmail():
            self.controller.prepareEmail()
            messagebox.showinfo("Succès de l'opération", "Les mails ont été préparés avec succès dans Thunderbird.")
            self.controller.updateViewData()

        # Callback pour rafraîchir les données
        def cbRefresh():
            self.controller.updateViewData()

        # Callback pour la sélection dans le Treeview
        def cbTreeview(event):
            self.controller.showBtns()

        # Création des widgets

        # Notebook pour afficher les onglets des dons réguliers et ponctuels
        receiptsNtbk = Notebook(self)
        addWidget(receiptsNtbk, "receiptsNtbk")

        # Frames pour les dons réguliers et ponctuels
        self.frames["irregularsFr"] = Frame(receiptsNtbk)
        self.frames["regularsFr"] = Frame(receiptsNtbk)

        receiptsNtbk.add(self.frames["irregularsFr"], text="Dons ponctuels")
        receiptsNtbk.add(self.frames["regularsFr"], text="Dons réguliers")

        # Comboboxes pour les membres et les années
        membersCbx = Combobox(self)
        membersCbx.bind("<<ComboboxSelected>>", cbxCb)
        addWidget(membersCbx, "membersCbx")

        yearsCbx = Combobox(self)
        yearsCbx.bind("<<ComboboxSelected>>", cbxCb)
        addWidget(yearsCbx, "yearsCbx")

        # Configuration des colonnes du Treeview
        columns = [
            {"id": "#0", "name": "Adhérent", "width": 150, "sort": False},
            {"id": "date", "name": "Date", "width": 100, "sort": True, "sortType": "datetime"},
            {"id": "receiptID", "name": "ID reçu", "width": 100, "sort": True},
            {"id": "amount", "name": "Montant", "width": 100, "sort": True, "sortType": "float"},
            {"id": "status", "name": "Statut", "width": 100, "sort": True},
        ]

        # Treeview pour les reçus irréguliers et réguliers
        receiptsIrregTrv = Treeview(self.frames["irregularsFr"], columns=[col["id"] for col in columns[1:]])
        receiptsIrregTrv.bind("<ButtonRelease-1>", cbTreeview)
        addWidget(receiptsIrregTrv, "receiptsIrregTrv")

        receiptsRegTrv = Treeview(self.frames["regularsFr"], columns=[col["id"] for col in columns[1:]])
        receiptsRegTrv.bind("<ButtonRelease-1>", cbTreeview)
        addWidget(receiptsRegTrv, "receiptsRegTrv")

        # Configuration des colonnes des Treeview avec tri si applicable
        for col in columns:
            for treeview in [self.widgets["receiptsIrregTrv"], self.widgets["receiptsRegTrv"]]:
                treeview.column(col["id"], width=col["width"])
                treeview.heading(col["id"], text=col["name"],
                                 command=lambda col=col, trv=treeview: sortTreeviewCol(trv, col, False))

        # Bouton pour ouvrir un reçu
        openReceiptBtn = Button(self, text="Ouvrir le reçu", command=self.controller.openReceiptCb)
        addWidget(openReceiptBtn, "openReceiptBtn")

        # Bouton pour préparer les emails
        prepareEmailBtn = Button(self, text="Préparer le mail", command=cbPrepareEmail)
        addWidget(prepareEmailBtn, "prepareEmailBtn")

        # Barre de progression
        progressBar = ProgressBarManager(self)
        addWidget(progressBar, "progressBar")

        # Bouton pour actualiser la vue
        refreshBtn = Button(self, text="Actualiser", command=cbRefresh)
        addWidget(refreshBtn, "refreshBtn")


    def displayWidgets(self):
        """
        Méthode pour afficher les widgets dans l'onglet
        """

        # On affiche tous les widgets
        for widget in self.widgets.values():
            widget.pack()

