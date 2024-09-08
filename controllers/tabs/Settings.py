import os.path
from os.path import isabs
from pathlib import Path
from tkinter import filedialog, END, messagebox

from models.Save import Save
from utils.LogManager import LogManager
from utils.customTkinter.MessageBoxDetails import MessageBoxDetails


class Settings:
    def __init__(self, view=None):
        """
        Initialise la classe Settings en récupérant la vue passée en paramètre et
        en chargeant les paramètres sauvegardés via la classe Save.

        Paramètre :
            view : Référence vers la vue associée à la classe Settings (optionnel).
        """
        self.view = view
        self.settings = Save().settings

    def setView(self, view):
        """
        Définit la vue associée à la classe Settings.

        Paramètre :
            view : La nouvelle vue à associer.
        """
        self.view = view

    def openPathDialog(self, widget, askFor="directory"):
        """
        Ouvre une boîte de dialogue pour sélectionner un répertoire ou un fichier et
        met à jour la valeur du widget en conséquence.

        Paramètres :
            widget : Le widget qui contiendra le chemin sélectionné.
            askFor : Type de sélection à effectuer ("directory" pour un répertoire, "file" pour un fichier).
        """
        widgetValue = Path(widget.get("1.0", END))

        if askFor == "directory":
            # Ouvre une boîte de dialogue pour sélectionner un répertoire
            path = filedialog.askdirectory(initialdir=widgetValue.as_posix().strip())
        else:
            # Ouvre une boîte de dialogue pour sélectionner un fichier
            dir = widgetValue.parent.as_posix().strip()
            file = widgetValue.name.strip()
            path = filedialog.askopenfile(initialdir=dir, initialfile=file).name

        if path:
            # Met à jour le widget avec le chemin sélectionné
            widget.delete(1.0, END)
            widget.insert(END, os.path.normpath(path))

    def saveSettings(self):
        """
        Sauvegarde les paramètres Thunderbird et reçus en extrayant les données
        des champs de la vue. Si la sauvegarde réussit, un message de confirmation
        s'affiche, sinon un message d'erreur avec les détails du problème.
        """
        newSettings = {"thunderbird": {}, "receipts": {}}

        for name, field in self.view.fields.items():
            if "text" in field:
                value = field["text"].get("1.0", END)
                if len(value.strip()) > 0:
                    if "thunderbird" in name:
                        # Transformation des noms de champ pour Thunderbird
                        key = name.replace("thunderbird", '')
                        key = key[0].lower() + key[1:]
                        if isabs(value):
                            value = os.path.normpath(value.strip())
                        newSettings["thunderbird"][key] = value

        # Sauvegarde des nouveaux paramètres
        if Save().saveSettings(newSettings):
            messagebox.showinfo("Enregistrement des options",
                                "L'enregistrement des options a été effectué avec succès.")
        else:
            # Affiche un message d'erreur en cas de problème lors de l'enregistrement
            detailsMsg = LogManager().getLogTypeMsgsAsString("OS")
            MessageBoxDetails("Enregistrement des options",
                              "Un problème est survenu lors de l'enregistrement des options.", detailsMsg)

    def reset(self, type):
        """
        Réinitialise les paramètres en fonction du type de réinitialisation demandé.
        (À implémenter selon le type de réinitialisation).

        Paramètre :
            type : Le type de réinitialisation (ex: "full" pour une réinitialisation complète).
        """
        if type == "full":
            pass
