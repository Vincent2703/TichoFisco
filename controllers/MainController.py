from tkinter import ttk

from controllers.tabs.Receipts import Receipts
from controllers.tabs.Settings import Settings
from controllers.tabs.Update import Update
from utils.misc import centerTkinterWindow
from views.ReceiptsView import ReceiptsView
from views.UpdateView import UpdateView
from views.SettingsView import SettingsView


class MainController:
    def __init__(self, root):
        self.root = root
        self.root.title("TichoFisco")
        centerTkinterWindow(self.root)

        self.notebook = ttk.Notebook(self.root)

        self.Update = Update()
        self.Receipts = Receipts()
        self.Settings = Settings()

        self.updateTab = UpdateView(self.notebook, self.Update)
        self.Update.setView(self.updateTab)

        self.receiptsTab = ReceiptsView(self.notebook, self.Receipts)
        self.Receipts.setView(self.receiptsTab)

        self.settingsTab = SettingsView(self.notebook, self.Settings)
        self.Settings.setView(self.settingsTab)

        self.notebook.add(self.updateTab, text="Mise à jour")
        self.notebook.add(self.receiptsTab, text="Reçus fiscaux")
        self.notebook.add(self.settingsTab, text="Options")

        self.notebook.bind("<<NotebookTabChanged>>", self.onTabSelected)

        self.notebook.pack(expand=True, fill="both")

    def onTabSelected(self, event):
        selected_tab = event.widget.select()
        tab_index = event.widget.index(selected_tab)

        if tab_index == 1:
            self.Receipts.updateViewData()
