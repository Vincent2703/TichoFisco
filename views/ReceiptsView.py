import tkinter as tk
from tkinter.ttk import Combobox


class ReceiptsView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller()
        self.createWidgets()
        self.displayWidgets()

    def createWidgets(self):
        # Dictionnaire associant des clés à des valeurs
        membersCbxDict = self.controller.getKVMembersCbx()

        # Créer une Combobox avec les valeurs du dictionnaire
        self.membersCbx = Combobox(self, values=list(membersCbxDict.values()))

        # Définir la valeur par défaut de la Combobox
        self.membersCbx.set("Tous les adhérents")

        # Fonction appelée lorsque l'utilisateur sélectionne une valeur
        def on_select(event):
            selected_value = self.membersCbx.get()
            # Récupérer la clé correspondant à la valeur sélectionnée
            selected_key = next((k for k, v in membersCbxDict.items() if v == selected_value), None)
            print(f"Clé sélectionnée: {selected_key}, Valeur: {selected_value}")

        # Associer la fonction `on_select` à l'événement de sélection de la Combobox
        self.membersCbx.bind("<<ComboboxSelected>>", on_select)

    def displayWidgets(self):
        self.membersCbx.pack()