from tkinter import Frame, Button, messagebox
from tkinter.ttk import Notebook, Combobox, Treeview

from utils.ProgressBarManager import ProgressBarManager
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

        def cbPrepareEmail():
            self.controller.prepareEmail()
            messagebox.showinfo("Succès de l'opération", "Les mails ont été préparés avec succès dans Thunderbird.")
            self.controller.updateViewData()

        def cbRefresh():
            self.controller.updateViewData()

        def cbTreeview(event):
            self.controller.showBtns()

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
            {"id": "status", "name": "Statut", "width": 100, "sort": True},
        ]
        self.receiptsIrregTrv = Treeview(self.irregularsFr, columns=[col["id"] for col in columns[1:]])
        self.receiptsIrregTrv.bind("<ButtonRelease-1>", cbTreeview)
        self.receiptsRegTrv = Treeview(self.regularsFr, columns=[col["id"] for col in columns[1:]])
        self.receiptsRegTrv.bind("<ButtonRelease-1>", cbTreeview)

        for col in columns:
            for treeview in [self.receiptsRegTrv, self.receiptsIrregTrv]:
                treeview.column(col["id"], width=col["width"])
                treeview.heading(col["id"], text=col["name"], command=lambda col=col, trv=treeview: sortTreeviewCol(trv, col, False))

        self.openReceiptBtn = Button(self, text="Ouvrir le reçu", command=self.controller.openReceiptCb)

        self.prepareEmailBtn = Button(self, text="Préparer le mail", command=cbPrepareEmail)

        self.progressBar = ProgressBarManager(self)

        self.refreshBtn = Button(self, text="Actualiser", command=cbRefresh)

    def displayWidgets(self):
        self.receiptsNtbk.pack()
        self.membersCbx.pack()
        self.yearsCbx.pack()
        self.receiptsRegTrv.pack()
        self.receiptsIrregTrv.pack()
        #self.openReceiptBtn.pack()
        #self.prepareEmailBtn.pack()

        self.progressBar.pack()

        self.refreshBtn.pack()

