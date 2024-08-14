import tkinter as tk


class UpdateView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller()
        self.createWidgets()
        self.displayWidgets()

    def createWidgets(self):
        self.updateBtn = tk.Button(self, text="Mettre à jour", command=self.controller.processPayments)
        self.openDirBtn = tk.Button(self, text="Ouvrir le dossier", command=self.controller.openDataDir)

    def displayWidgets(self):
        self.updateBtn.pack()
        self.openDirBtn.pack()
