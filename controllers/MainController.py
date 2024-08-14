from tkinter import ttk

from controllers.tabs.Receipts import Receipts
from controllers.tabs.Update import Update
from views.ReceiptsView import ReceiptsView
from views.UpdateView import UpdateView


class MainController:
    def __init__(self, root):
        self.root = root
        self.root.title("TichoFisco")
        self.notebook = ttk.Notebook(self.root)

        self.updateTab = UpdateView(self.notebook, Update)
        self.receiptsTab = ReceiptsView(self.notebook, Receipts)
        self.optionsTab = UpdateView(self.notebook, Update)

        self.notebook.add(self.updateTab, text="Mise à jour")
        self.notebook.add(self.receiptsTab, text="Reçus fiscaux")
        self.notebook.add(self.optionsTab, text="Options")

        self.notebook.pack(expand=True, fill="both")
