from tkinter import END, Frame
from tkinter.ttk import Notebook, Combobox, Treeview

from utils.misc import sortTreeviewCol


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

        def membersCbxCb(event):
            selectedValue = self.membersCbx.get()
            self.controller.memberSelected(selectedValue)  # Informer le contrôleur de la sélection

        def yearsCbxCb(event):
            selectedValue = self.yearsCbx.get()
            self.controller.yearSelected(selectedValue)

        self.receiptsNtbk = Notebook(self)
        self.regularsFr = Frame(self.receiptsNtbk)
        self.irregularsFr = Frame(self.receiptsNtbk)
        self.receiptsNtbk.add(self.irregularsFr, text='Dons ponctuels')
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
                treeview.heading(col["id"], text=col["name"], command=lambda _col=col: sortTreeviewCol(treeview, _col, False))

    def displayWidgets(self):
        self.receiptsNtbk.pack()
        self.membersCbx.pack()
        self.yearsCbx.pack()
        self.receiptsRegTrv.pack()
        self.receiptsIrregTrv.pack()