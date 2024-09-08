import ctypes
import os.path
import platform
import subprocess
import time
from datetime import datetime
from os.path import isfile
from pathlib import Path

from utils.LogManager import LogManager


def saveHiddenFile(filename, content, binary=False):
    """
    Sauvegarde un fichier en mode caché. Si le fichier existe déjà, il est supprimé et recréé.
    Sous Windows, le fichier est directement marqué comme caché ; sous Linux, le fait que le nom du fichier soit préfixé par un point suffit.

    Paramètres :
        filename : Chemin du fichier à sauvegarder.
        content : Contenu à écrire dans le fichier.
        binary : Indique si le contenu doit être écrit en mode binaire (False par défaut).
    """
    if isfile(filename):
        os.remove(filename)  # Supprimer l'ancien fichier

    mode = "w+"  # Mode écriture
    if binary:
        mode += 'b'  # Ajouter l'option binaire si nécessaire

    # Écriture du contenu dans le fichier
    with open(filename, mode) as file:
        file.write(content)

    if platform.system() == "Windows":
        # Marquer le fichier comme caché sous Windows
        FILE_ATTRIBUTE_HIDDEN = 0x02
        try:
            ctypes.windll.kernel32.SetFileAttributesW(ctypes.create_unicode_buffer(str(filename)),
                                                      FILE_ATTRIBUTE_HIDDEN)
        except Exception as e:
            LogManager().addLog("OS", LogManager.LOGTYPE_ERROR,
                                f"Erreur lors de la définition de l'attribut caché : {e}")
    else:
        # Sous Linux, préfixer le nom du fichier avec un point pour le cacher
        if not filename.startswith('.'):
            os.rename(filename, '.' + filename)


def openDir(path):
    """
    Ouvre un répertoire dans l'explorateur de fichiers de l'OS.

    Paramètre :
        path: Chemin du répertoire à ouvrir.

    Retourne :
        True si l'ouverture est réussie, False sinon.
    """
    path = os.path.normpath(path)  # Normaliser le chemin

    if os.path.isdir(path):
        OS = platform.system()
        if OS == "Windows":
            subprocess.run([os.path.join(os.getenv("WINDIR"), "explorer.exe"), path])
            return True
        elif OS == "Linux":
            subprocess.Popen(["xdg-open", path])
            return True
    LogManager().addLog("OS", LogManager.LOGTYPE_ERROR, f"Impossible d'ouvrir le dossier : '{path}'")
    return False


def openFile(path):
    """
    Ouvre un fichier avec l'application par défaut de l'OS.

    Paramètres :
        path : Chemin du fichier à ouvrir.

    Retourne :
        True si l'ouverture est réussie, False sinon.
    """
    path = os.path.normpath(path)  # Normaliser le chemin

    if os.path.isfile(path):
        OS = platform.system()
        if OS == "Windows":
            os.startfile(path)  # Ouvrir le fichier sous Windows
            return True
        elif OS == "Linux":
            subprocess.call(["xdg-open", path])  # Ouvrir le fichier sous Linux
            return True
    LogManager().addLog("OS", LogManager.LOGTYPE_ERROR, f"Impossible d'ouvrir le fichier : '{path}'")
    return False


def convertFrenchDate(frenchDateStr):
    """
    Convertit une date au format français (avec les mois en français) en datetime.

    Paramètre :
        frenchDateStr : Chaîne de caractères contenant la date en français.

    Retourne :
        Un objet datetime correspondant à la date.
    """
    frenchToEnglishMonths = {
        "Janvier": "January", "Février": "February", "Mars": "March",
        "Avril": "April", "Mai": "May", "Juin": "June",
        "Juillet": "July", "Août": "August", "Septembre": "September",
        "Octobre": "October", "Novembre": "November", "Décembre": "December"
    }

    # Remplacer le mois français par le mois anglais
    englishDateStr = frenchDateStr
    for frenchMonth, englishMonth in frenchToEnglishMonths.items():
        if frenchMonth in frenchDateStr:
            englishDateStr = frenchDateStr.replace(frenchMonth, englishMonth)
            break

    # Gestion d'erreurs lors de la conversion
    try:
        return datetime.strptime(englishDateStr, "%B %d, %Y @ %I:%M %p")
    except ValueError as e:
        LogManager().addLog("OS", LogManager.LOGTYPE_ERROR, f"Erreur lors de la conversion de la date : {e}")
        raise


def centerTkinterWindow(win):
    """
    Centre une fenêtre Tkinter sur l'écran.

    Paramètre :
        win : Fenêtre Tkinter à centrer.
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()


def sortTreeviewCol(trv, col, reverse=False):
    """
    Trie les colonnes d'un Treeview en fonction de leur contenu.

    Paramètres :
        trv : Widget Treeview à trier.
        col : Colonne à trier.
        reverse : Indique si le tri doit être inversé (False par défaut).
    """
    if not col["sort"]:
        return

    colID = col["id"]
    sortType = None
    if "sortType" in col:
        sortType = col["sortType"]

    # Liste des tuples (valeur, clé) pour chaque enfant du Treeview
    l = [(trv.set(k, colID), k) for k in trv.get_children('')]

    # Conversion des valeurs selon le type de tri
    for i, (val, k) in enumerate(l):
        if sortType == "datetime":
            try:
                l[i] = (datetime.strptime(val, "%d/%m/%Y"), k)
            except ValueError:
                l[i] = (datetime.min, k)  # Gérer les dates invalides
        elif sortType == "float":
            try:
                l[i] = (float(val), k)
            except ValueError:
                l[i] = (float('-inf'), k)  # Gérer les flottants invalides
        else:
            l[i] = (val, k)

    # Trier la liste basée sur les valeurs converties
    l.sort(reverse=reverse)

    # Réorganiser les items dans le Treeview selon l'ordre trié
    for index, (val, k) in enumerate(l):
        trv.move(k, '', index)

    # Configurer le header pour trier dans l'autre sens lors du prochain clic
    trv.heading(colID, command=lambda: sortTreeviewCol(trv, col, not reverse))


def getEpoch():
    """
    Retourne le temps UNIX actuel (en secondes depuis 1970).

    Retourne :
        int : Le temps UNIX actuel.
    """
    return int(time.time())


def epochToFrDate(epoch):
    """
    Convertit un timestamp UNIX en une date formatée en français.

    Paramètre :
        epoch : Timestamp UNIX à convertir.

    Retourne :
        str : Date formatée en "dd/mm/YYYY HH:MM".
    """
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(epoch))


def isFileInUse(filepath):
    """
    Vérifie si un fichier est en cours d'utilisation.

    Paramètre :
        filepath : Chemin du fichier à vérifier.

    Retourne :
        bool : True si le fichier est en cours d'utilisation, False sinon.
    """
    path = Path(filepath)

    if not path.exists():
        return False

    try:
        path.rename(path)  # Si le fichier peut être renommé, il n'est pas utilisé
    except PermissionError:
        return True  # Erreur de permission signifie que le fichier est en cours d'utilisation
    else:
        return False
