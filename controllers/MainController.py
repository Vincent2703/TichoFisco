from tkinter import ttk

from controllers.tabs.Receipts import Receipts
from controllers.tabs.Settings import Settings
from controllers.tabs.Update import Update
from models.Save import Save
from utils.LogManager import LogManager
from utils.customTkinter.MessageBoxDetails import MessageBoxDetails
from utils.misc import centerTkinterWindow
from views.ReceiptsView import ReceiptsView
from views.UpdateView import UpdateView
from views.SettingsView import SettingsView


class MainController:
    def __init__(self, root):
        """
        Initialisation du contrôleur principal.
        Crée les onglets, configure la fenêtre principale, et vérifie le remplissage des options obligatoires.

        Paramètres :
            - root : la fenêtre principale Tkinter.
        """
        self.root = root
        self.root.title("TichoFisco")
        centerTkinterWindow(self.root)

        self.notebook = ttk.Notebook(self.root)  # Création d'un Notebook pour contenir les onglets

        # Initialisation des contrôleurs pour chaque onglet
        self.Update = Update()
        self.Receipts = Receipts()
        self.Settings = Settings()

        self._initializeTabs()

        self._checkSettings()  # Vérifie si les paramètres nécessaires sont renseignés


    def _initializeTabs(self):
        """
        Initialisation des onglets.
        Création des onglets, des vues et contrôleurs et association entre eux.
        """
        # Création des vues et association avec les contrôleurs
        self.updateTab = UpdateView(self.notebook, self.Update)
        self.Update.setView(self.updateTab)

        self.receiptsTab = ReceiptsView(self.notebook, self.Receipts)
        self.Receipts.setView(self.receiptsTab)

        self.settingsTab = SettingsView(self.notebook, self.Settings)
        self.Settings.setView(self.settingsTab)

        # Ajout des onglets au Notebook
        self.notebook.add(self.updateTab, text="Mise à jour")
        self.notebook.add(self.receiptsTab, text="Reçus fiscaux")
        self.notebook.add(self.settingsTab, text="Options")

        # Actions à effectuer au clic et au changement d'onglet
        self.notebook.bind("<Button>", self._onTabClicked)
        self.notebook.bind("<<NotebookTabChanged>>", self._onTabChanged)

        # Affiche le Notebook et étend les onglets pour remplir l'espace disponible
        self.notebook.pack(expand=True, fill="both")

    def _onTabClicked(self, event):
        """
        Méthode déclenchée lorsque l'on clique sur un onglet.
        Vérifie les paramètres avant de permettre le changement d'onglet.
        """
        clicked_tab = event.widget.identify(event.x, event.y)

        if clicked_tab == "label" and not Save().isSettingsFilled():
            # Annule le changement d'onglet si les paramètres ne sont pas remplis
            detailsMsg = LogManager().getLogTypeMsgsAsString("Settings")
            self.notebook.select(2)  # Redirige vers l'onglet "Options"
            MessageBoxDetails("Paramètre(s) manquant(s)", "Veuillez renseigner les paramètres manquants.", detailsMsg)
            return "break"  # Empêche l'événement de se propager et de changer d'onglet

    def _onTabChanged(self, event):
        """
        Méthode déclenchée lorsque l'on change d'onglet.
        Met à jour les données de l'onglet "Reçus fiscaux" si nécessaire.

        Paramètres :
            - event : l'événement déclenché lors du changement d'onglet.
        """
        selected_tab = event.widget.select()
        tab_index = event.widget.index(selected_tab)

        if tab_index == 1:  # Si l'onglet sélectionné est "Reçus fiscaux"
            self.Receipts.updateViewData()

    def _checkSettings(self):
        """
        Vérifie si les paramètres nécessaires sont renseignés.
        Si les paramètres ne sont pas renseignés, un message est affiché
        et l'utilisateur est redirigé vers l'onglet des options.
        """
        if not Save().isSettingsFilled():  # Vérifie si les paramètres sont remplis
            detailsMsg = LogManager().getLogTypeMsgsAsString("Settings")
            self.notebook.select(2)  # Sélectionne l'onglet "Options"
            MessageBoxDetails("Paramètre(s) manquant(s)", "Veuillez renseigner les paramètres manquants.", detailsMsg)
