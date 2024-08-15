import ctypes
import logging
import os.path
import platform
import subprocess
from datetime import datetime
from os.path import isfile


def saveHiddenFile(filename, content, binary=False):
    # Écrire le contenu dans le fichier
    if not isfile(filename):
        mode = "w+"
    else:
        mode = "r+"
    if binary:
        mode += 'b'
    with open(filename, mode) as file:
        file.write(content)

    if platform.system() == "Windows":
        # Définir l'attribut de fichier caché sous Windows
        FILE_ATTRIBUTE_HIDDEN = 0x02
        try:
            ctypes.windll.kernel32.SetFileAttributesW(ctypes.create_unicode_buffer(str(filename)), FILE_ATTRIBUTE_HIDDEN)
        except Exception as e:
            logging.error(f"Erreur lors de la définition de l'attribut caché : {e}")
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
    logging.error(f"Impossible d'ouvrir le dossier : '{path}'")
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
