import ctypes
import os.path
import platform
import re
import subprocess
import time
from datetime import datetime
from os.path import isfile
from pathlib import Path

from utils.LogManager import LogManager


def saveHiddenFile(filename, content, binary=False):
    # Écrire le contenu dans le fichier
    if isfile(filename):
        os.remove(filename)  # r+ ?

    mode = "w+"

    if binary:
        mode += 'b'
    with open(filename, mode) as file:
        file.write(content)

    if platform.system() == "Windows":
        # Définir l'attribut de fichier caché sous Windows
        FILE_ATTRIBUTE_HIDDEN = 0x02
        try:
            ctypes.windll.kernel32.SetFileAttributesW(ctypes.create_unicode_buffer(str(filename)),
                                                      FILE_ATTRIBUTE_HIDDEN)
        except Exception as e:
            LogManager().addLog("OS", LogManager.LOGTYPE_ERROR,
                                f"Erreur lors de la définition de l'attribut caché : {e}")
    else:
        # Renommer le fichier pour qu'il commence par un point sous Linux
        if not filename.startswith('.'):
            os.rename(filename, '.' + filename)


def openDir(path):
    path = os.path.normpath(path)

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
    path = os.path.normpath(path)

    if os.path.isfile(path):
        #todo : try except
        OS = platform.system()
        if OS == "Windows":
            os.startfile(path)
            return True
        elif OS == "Linux":
            subprocess.call(["xdg-open", path])
            return True
    LogManager().addLog("OS", LogManager.LOGTYPE_ERROR, f"Impossible d'ouvrir le fichier : '{path}'")
    return False


def convertFrenchDate(frenchDateStr):  # TODO : check error
    # Dictionnaire pour mapper les mois français aux mois anglais
    frenchToEnglishMonths = {
        "Janvier": "January", "Février": "February", "Mars": "March",
        "Avril": "April", "Mai": "May", "Juin": "June",
        "Juillet": "July", "Août": "August", "Septembre": "September",
        "Octobre": "October", "Novembre": "November", "Décembre": "December"
    }

    # Remplacer le mois français par le mois anglais
    for frenchMonth, englishMonth in frenchToEnglishMonths.items():
        if frenchMonth in frenchDateStr:
            englishDateStr = frenchDateStr.replace(frenchMonth, englishMonth)
            break

    # Convertir la chaîne modifiée en objet datetime
    return datetime.strptime(englishDateStr, "%B %d, %Y @ %I:%M %p")


def centerTkinterWindow(win):  # From https://stackoverflow.com/a/10018670
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


def sortTreeviewCol(trv, col, reverse=False):  # Fonction basée sur https://stackoverflow.com/a/61495299
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
                # Convertir la valeur en datetime pour le tri
                l[i] = (datetime.strptime(val, "%d/%m/%Y"), k)
            except ValueError:
                # Gérer les dates invalides en les mettant au min
                l[i] = (datetime.min, k)
        elif sortType == "float":
            try:
                # Convertir la valeur en float pour le tri
                l[i] = (float(val), k)
            except ValueError:
                # Gérer les flottants invalides en les mettant au min
                l[i] = (float('-inf'), k)
        else:
            # Pour les autres types, on garde la valeur telle quelle
            l[i] = (val, k)

    # Trier la liste basée sur les valeurs converties
    l.sort(reverse=reverse)

    # Réorganiser les items dans le Treeview selon l'ordre trié
    for index, (val, k) in enumerate(l):
        trv.move(k, '', index)

    # Configurer le header pour permettre de trier dans l'autre sens lors du prochain clic
    trv.heading(colID, command=lambda: sortTreeviewCol(trv, col, not reverse))

def getEpoch():
    return int(time.time())

def epochToFrDate(epoch):
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(epoch))

def isFileInUse(filepath):  # Basé sur https://stackoverflow.com/a/66598940
    path = Path(filepath)

    if not path.exists():
        return False

    try:
        path.rename(path)
    except PermissionError:
        return True
    else:
        return False