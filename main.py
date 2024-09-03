import logging
from tkinter import Tk

from controllers.MainController import MainController

# Configuration de logging pour afficher des messages d'information/warnings/erreurs sous un format spécifique
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    # Création de la fenêtre principale de l'application
    root = Tk()
    root.geometry("800x450")  # Dimensions de la fenêtre
    controller = MainController(root)  # Contrôleur principal
    # Démarre Tkinter
    root.mainloop()
