from tkinter import END, Frame, Button
from tkinter.ttk import Notebook, Combobox, Treeview

from utils.PathManager import PathManager
from utils.Thunderbird import Thunderbird
from utils.misc import sortTreeviewCol, openFile


class ReceiptsView(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.createWidgets()
        self.displayWidgets()

    def createWidgets(self):
        def cbxCb(event):
            self.controller.queryUpdate(
                member=self.membersCbx.get(),
                year=self.yearsCbx.get()
            )

        self.receiptsNtbk = Notebook(self)

        self.regularsFr = Frame(self.receiptsNtbk)
        self.irregularsFr = Frame(self.receiptsNtbk)
        self.receiptsNtbk.add(self.irregularsFr, text="Dons ponctuels")
        self.receiptsNtbk.add(self.regularsFr, text="Dons réguliers")

        self.membersCbx = Combobox(self)
        self.membersCbx.bind("<<ComboboxSelected>>", cbxCb)

        self.yearsCbx = Combobox(self)
        self.yearsCbx.bind("<<ComboboxSelected>>", cbxCb)

        columns = [
            {"id": "#0", "name": "Adhérent", "width": 150, "sort": False},
            {"id": "date", "name": "Date", "width": 100, "sort": True, "sortType": "datetime"},
            {"id": "receiptID", "name": "ID reçu", "width": 100, "sort": True},
            {"id": "amount", "name": "Montant", "width": 100, "sort": True, "sortType": "float"},
            {"id": "sent", "name": "Envoyé", "width": 100, "sort": True},
        ]
        self.receiptsIrregTrv = Treeview(self.irregularsFr, columns=[col["id"] for col in columns[1:]])
        self.receiptsRegTrv = Treeview(self.regularsFr, columns=[col["id"] for col in columns[1:]])

        for col in columns:
            for treeview in [self.receiptsRegTrv, self.receiptsIrregTrv]:
                treeview.column(col["id"], width=col["width"])
                treeview.heading(col["id"], text=col["name"], command=lambda col=col, trv=treeview: sortTreeviewCol(trv, col, False))


        self.openReceiptBtn = Button(self, text="Ouvrir le reçu", command=self._openReceiptCb)

        self.prepareEmailBtn = Button(self, text="Préparer le mail", command=self._prepareEmail)

    def displayWidgets(self):
        self.receiptsNtbk.pack()
        self.membersCbx.pack()
        self.yearsCbx.pack()
        self.receiptsRegTrv.pack()
        self.receiptsIrregTrv.pack()
        self.openReceiptBtn.pack()
        self.prepareEmailBtn.pack()

    def _getSelectedRow(self):
        # Identifier la frame active
        activeFrame = self.receiptsNtbk.nametowidget(self.receiptsNtbk.select())

        # En fonction de la frame active, récupérer le Treeview correspondant
        if activeFrame == self.regularsFr:
            activeTreeview = self.receiptsRegTrv
        else:
            activeTreeview = self.receiptsIrregTrv

        # Obtenir la ligne sélectionnée dans le Treeview actif
        selectedItem = activeTreeview.selection()

        if selectedItem:
            # Récupérer les valeurs de la ligne sélectionnée
            itemValues = activeTreeview.item(selectedItem)["values"]
            return itemValues
        return False

    def _getPathFromID(self, ID):  # A déplacer
        # Pour bien faire, il faudrait avoir le chemin du reçu dans une colonne cachée
        # Mais là on va juste le récupérer via son ID
        year = f"20{ID[:2]}"
        month = str(int(ID[2:4]))
        path = PathManager().getPaths()["recusFiscaux"] / year / month / f"{ID}.pdf"
        return path

    def _openReceiptCb(self):
        selectedRow = self._getSelectedRow()
        if selectedRow:
            # On récupère son identifiant
            receiptID = selectedRow[1]
            path = self._getPathFromID(receiptID)
            openFile(path)

    def _prepareEmail(self):
        selectedRow = self._getSelectedRow()
        if selectedRow:
            print(selectedRow) # TODO : Récupérer l'email !
            toEmail = selectedRow[3]
            print(toEmail)
            filePath = self._getPathFromID(selectedRow[1])
            Thunderbird().addMail(subject="test", to=toEmail, message="Ceci est un <b>test</b> !", filePath=filePath)