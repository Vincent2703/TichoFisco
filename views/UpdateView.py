import tkinter as tk
from tkinter import messagebox


class UpdateView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller()
        self.createWidgets()
        self.displayWidgets()

    def createWidgets(self):
        def cbUpdateBtn():
            resProcess = self.controller.processPayments()
            if resProcess == "SUCCESS":
                messagebox.showinfo("Mise à jour réussie", "Traitement et exportation des fichiers complétés avec succès.")
            elif resProcess == "WARNING":
                messagebox.Message(icon=messagebox.WARNING, messagebox="Une ou plusieurs erreurs sont survenues lors du traitement des paiements.")
            else:
                messagebox.showerror("Erreur critique !", "Une erreur critique est survenue lors de la mise à jour !")

        self.updateBtn = tk.Button(self, text="Mettre à jour", command=cbUpdateBtn)
        self.openDirBtn = tk.Button(self, text="Ouvrir le dossier", command=self.controller.openDataDir)

    def displayWidgets(self):
        self.updateBtn.pack()
        self.openDirBtn.pack()
