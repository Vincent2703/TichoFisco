import os
import csv
from glob import glob
from openpyxl import load_workbook, Workbook
from pathlib import Path
import logging
from datetime import datetime


def findMember(email, name, surname, filePath):
    workbook = load_workbook(filename=filePath)
    sheet = workbook.active
    for row_number, row in enumerate(sheet.iter_rows(min_row=2), start=2):
        if row[1].value != None and row[2].value != None and row[3].value != None and row[1].value == email and row[2].value == name and row[3].value == surname:
            return row_number, row
    return False, False


def importHelloAsso(filePath):
    if Path(filePath).is_file():
        workbook = load_workbook(filename=filePath)
        sheet = workbook.active
        secondRow = [cell.value for cell in sheet[2]]
        return secondRow
    else:
        logging.error(f"Impossible d'importer le fichier HelloAsso {filePath}")

#Configurer Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


## Créer les dossiers si besoin ##
currentPath = Path.cwd()
dataPath = currentPath/"donnees"

currentDatetime = datetime.now()

paths = {
    "actuel": dataPath,
    "listesAdherents": dataPath/"listesAdherents",
    "paiementsHelloAsso": dataPath/"paiements/helloAsso",
    "paiementsPaypal": dataPath/"paiements/paypal",
    "paiementsVirEspChq": dataPath/"paiements/virEspChq",
    "paiementsCB": dataPath/"paiements/CB",
    "recusFiscaux": dataPath/"recusFiscaux"/str(currentDatetime.year)/str(currentDatetime.month)
}

for key, path in paths.items():
    try:
        path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Dossier créé ou déjà existant : {path}")
    except OSError as error:
        logging.error(f"Impossible de créer le dossier {path} : {error}")


## Créer une nouvelle liste adhérents si besoin ##
currentMembersListPath = paths["listesAdherents"]/f"{currentDatetime.year}.xlsx"
if not Path(currentMembersListPath).is_file():
    try:
        workbook = Workbook()
        sheet = workbook.active

        fields = ["Date enregistrement", "Adresse mail", "Nom", "Prenom", "Identifiant du reçu", "Statut", "Date dernière adhésion", "Envoi mails", "Adresse", "Code postale", "Ville", "Téléphone", "Montant adhésion", "Montant don", "Total", "Date dernier paiement", "Moyen paiement", "Remarques"]
        
        # Ajouter les en-têtes de colonnes
        sheet.append(fields)
        
        # Sauvegarder le fichier
        workbook.save(currentMembersListPath)
        logging.info(f"Fichier {currentMembersListPath} créé")
    except OSError as error:
        logging.error(f"Impossible de créer le fichier {currentMembersListPath} : {error}")
else: ## Sinon remettre tout à zero
    try:
        workbook = load_workbook(currentMembersListPath)
        sheet = workbook.active
        for row in sheet.iter_rows(min_row=2):
                for cell in row:
                    cell.value = None
        workbook.save(currentMembersListPath)
    except OSError as error:
            logging.error(f"Impossible d'ouvrir le fichier {currentMembersListPath} : {error}")



## Parcourir les fichiers HelloAsso
"""for path in glob(str(paths["paiementsHelloAsso"]/"*.xlsx")):
    importHelloAsso(path)"""

#member = {"mail": "testEmail", "nom": "testNom", "prenom": "testPrenom"}
#manageMemberRecord(member, glob(str(paths["listesAdherents"]/"*.csv")))

helloAsso = importHelloAsso(paths["paiementsHelloAsso"]/"export-paiements HELLO ASSO 31_12_2023-24_01_2024 Vir du 31012024.xlsx")

#D'abord on regarde dans la liste de l'année en cours
nbRow, rowMemberCurrList = findMember(helloAsso[7], helloAsso[5], helloAsso[6], currentMembersListPath) #return juste le nbRow

if rowMemberCurrList:
    workbook = load_workbook(filename=currentMembersListPath)
    sheet = workbook.active
     
    if helloAsso[9] != rowMemberCurrList[9]: #Nouvelle adresse
        sheet.cell(nbRow, 9).value = helloAsso[9]
    if helloAsso[10] != rowMemberCurrList[10]: #Nouveau CP 
        sheet.cell(nbRow, 10).value = helloAsso[10]
    if helloAsso[11] != rowMemberCurrList[11]: #Nouvelle ville
        sheet.cell(nbRow, 11).value = helloAsso[11]

    total = sheet[nbRow][14].value or 0
    sheet.cell(nbRow, 14).value = int(total) + int(helloAsso[1])

    workbook.save(currentMembersListPath)

    logging.info("Mise à jour de la ligne dans la liste des adhérents pour %s", helloAsso[7])
else:
    otherLists = [file for file in glob(str(paths["listesAdherents"]/"*.csv")) if os.path.basename(file) != f"{currentDatetime.year}.csv"]
    otherLists.sort(reverse=True)

    rowMemberOlderList = None
    for path in otherLists:
        rowMemberOlderList = findMember(helloAsso[7], helloAsso[5], helloAsso[6], path)
        if rowMemberOlderList:
            break
    
    if rowMemberOlderList:
        logging.info("Création d'une nouvelle ligne dans la liste des adhérents selon les données d'une ancienne adhésion")
    else:
        fields = [currentDatetime.strftime("%d/%m/%Y"), 
                          helloAsso[7], helloAsso[5], 
                          helloAsso[6], '?', "NA", '?', "Oui", 
                          helloAsso[9], helloAsso[10], 
                          helloAsso[11], '?', min(int(helloAsso[1]), 18), 
                          max(0, int(helloAsso[1])-18), helloAsso[1], 
                          helloAsso[4].strftime("%d/%m/%Y"), "Hello Asso", '/']
        
        sheet.append(fields)
        workbook.save(currentMembersListPath)

        logging.info("Création d'une nouvelle ligne dans la liste des adhérents")
