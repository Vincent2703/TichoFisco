import csv
from collections import defaultdict
from glob import glob

from openpyxl.utils import get_column_letter
from openpyxl import load_workbook, Workbook
from pathlib import Path
import logging
from datetime import datetime

from controllers.Receipt import receiptsToPDFs
from models.Member import Member
from utils import styles, utils
from utils.loadSave import save


## Fonctions


def getNbMemberInList(email, name, surname, list):
    for nbMember, member in enumerate(list):
        if type(member) != str and member.isThisMember(email, name, surname):
            return nbMember
    return False


def createOrResetMembersList(year):
    membersList = paths["listesAdherents"] / f"{year}.xlsx"
    if not Path(membersList).is_file():
        try:
            workbook = Workbook()
            sheet = workbook.active

            fields = ["Adresse mail", "Nom", "Prenom", "IDs reçus", "Statut",
                      "Date dernière adhésion", "Envoi mails", "Adresse", "Code postal", "Ville", "Téléphone",
                      "Montant adhésion payé année n-1", "Montant adhésion année n", "Montant adhésion année n+1",
                      "Montant dons année n", "Total année n", "Dernier paiement", "Dern. moy. paiement", "Remarques"]

            # Ajouter les en-têtes de colonnes
            sheet.append(fields)

            # repositionner le curseur
            sheet.cell(row=2, column=1)

            for nbCol, width in enumerate(styles.widthCols):
                col = sheet.column_dimensions[get_column_letter(nbCol + 1)]
                col.width = width

            # Appliquer le style de l'en-tête à la première ligne
            for cell in sheet[1]:
                cell.font = styles.fontHeader
                cell.border = styles.borderHeader
                cell.alignment = styles.Alignment(horizontal="center", vertical="center")

            # Sauvegarder le fichier
            workbook.save(membersList)
            workbook.close()
            logging.info(f"Fichier {membersList} créé")
            return sheet
        except OSError as error:
            logging.error(f"Impossible de créer le fichier {membersList} : {error}")
            return False
    else:  ## Sinon remettre tout à zero TODO: garder les remarques ? Mettre avec le fichier cache pour les reçus
        try:
            workbook = load_workbook(membersList)
            sheet = workbook.active

            sheet.delete_rows(2, sheet.max_row)
            workbook.save(membersList)
            workbook.close()
            return sheet
        except OSError as error:
            logging.error(f"Impossible d'ouvrir le fichier {membersList} : {error}")
            return False


def getDataFromPaymentsFile(path, source):
    if source != "cb":
        workbook = load_workbook(filename=path)
        sheet = workbook.active
    else:
        csvContent = []
        with open(path, mode='r') as csvFile:
            csvReader = csv.DictReader(csvFile, delimiter=',')
            for row in csvReader:
                csvContent.append(row)

    payments = []
    if source == "helloAsso":
        requiredCols = [1, 2, 5, 6, 7]  # Indices des colonnes à vérifier pour les valeurs non nulles
        for row in sheet.iter_rows(min_row=2):
            if all(row[idx].value is not None for idx in requiredCols):
                payments.append({
                    "mail": row[7].value,
                    "nom": row[5].value,
                    "prenom": row[6].value,
                    "date": row[2].value.strftime("%d/%m/%Y"),
                    "type": "reguliers" if row[8].value == "Crowdfunding" else "ponctuels",
                    "adresse": row[9].value,
                    "cp": str(row[10].value),
                    "ville": row[11].value,
                    "telephone": '',
                    "montant": float(row[1].value),
                    "source": source,
                    "refPaiement": row[0].value
                })
    elif source == "paypal":
        requiredCols = [0, 2, 8, 9, 4]
        for row in sheet.iter_rows(min_row=4):
            if all(row[idx].value is not None for idx in requiredCols) and row[4].value == "Terminé" and float(row[8].value) > 0:
                prenomNom = row[2].value.rsplit(' ', 1)
                payments.append({
                    "mail": row[9].value,
                    "nom": prenomNom[0],
                    "prenom": prenomNom[1],
                    "date": row[0].value.strftime("%d/%m/%Y"),
                    "type": "reguliers" if row[3].value == "Paiement d'abonnement" else "ponctuels",
                    "adresse": row[11].value,
                    "cp": str(row[13].value),
                    "ville": row[12].value,
                    "telephone": '',
                    "montant": float(row[8].value),
                    "source": source,
                    "refPaiement": row[10].value
                })
    elif source == "virEspChq":
        requiredCols = [0, 2, 3, 4, 8]
        for row in sheet.iter_rows(min_row=2):
            if all(row[idx].value is not None for idx in requiredCols):
                source = ''
                mode = row[9].value.casefold()
                if mode == 'v':
                    source = "Virement"
                elif mode == 'c':
                    source = "Chèque"
                elif mode == 'e':
                    source = "Espèce"
                payments.append({
                    "mail": row[2].value,
                    "nom": row[3].value,
                    "prenom": row[4].value,
                    "date": row[0].value.strftime("%d/%m/%Y"),
                    "type": "reguliers" if row[10].value == "O" else "ponctuels",
                    "adresse": row[5].value,
                    "cp": str(row[6].value),
                    "ville": row[7].value,
                    "telephone": '',
                    "montant": float(row[8].value),
                    "source": source,
                    "refPaiement": row[1].value
                })
    elif source == "cb":
        requiredCols = ["Heure de soumission", "Nom", "Prénom", "E-mail", "Carte de crédit/débit - Montant",
                        "Carte de crédit/débit - État "]
        for row in csvContent:
            if all(row[key] is not None for key in requiredCols) and row[
                "Carte de crédit/débit - État "].casefold() == "completed":
                payments.append({
                    "mail": row["E-mail"],
                    "nom": row["Nom"],
                    "prenom": row["Prénom"],
                    "date": utils.convertFrenchDate(row["Heure de soumission"]).strftime("%d/%m/%Y"),
                    "type": "ponctuels",
                    "adresse": row["Address - Rue"] + ' ' + row["Address - Appartement, suite, etc."],
                    "cp": str(row["Address - Code postal"]),
                    "ville": row["Address - Ville"],
                    "telephone": str(row["Téléphone"]),
                    "montant": float(row["Carte de crédit/débit - Montant"]),
                    "source": source,
                    "refPaiement": str(row["Carte de crédit/débit - ID de la transaction"])
                })

    return payments


# Configurer Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

## Créer les dossiers si besoin ##
currentPath = Path.cwd()
dataPath = currentPath / "donnees"

currentDatetime = datetime.now()

paths = {  # TODO : use Path()
    "actuel": dataPath,
    "listesAdherents": dataPath / "listesAdherents",
    "paiementsHelloAsso": dataPath / "paiements/helloAsso",
    "paiementsPaypal": dataPath / "paiements/paypal",
    "paiementsVirEspChq": dataPath / "paiements/virEspChq",
    "paiementsCB": dataPath / "paiements/CB",
    "recusFiscaux": dataPath / "recusFiscaux"
}

for key, path in paths.items():
    try:
        path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Dossier créé ou déjà existant : {path}")
    except OSError as error:
        logging.error(f"Impossible de créer le dossier {path} : {error}")

paymentsFiles = {
    "helloAsso": glob(str(paths["paiementsHelloAsso"] / "*.xlsx")),
    "paypal": glob(str(paths["paiementsPaypal"] / "*.xlsx")),
    "virEspChq": glob(str(paths["paiementsVirEspChq"] / "*.xlsx")),
    "cb": glob(str(paths["paiementsCB"] / "*.csv"))
}

membersByYear = defaultdict(list)
years = []
for source, filePaths in paymentsFiles.items():
    for filePath in filePaths:
        for payment in getDataFromPaymentsFile(filePath, source):
            year = str(datetime.strptime(payment["date"], "%d/%m/%Y").year)
            if year not in years:  # Si c'est la première fois à l'execution qu'on tombe sur cette année
                years.append(year)  # On ajoute cette année à la liste des années
                membersByYear[year] = []  # On créait une nouvelle liste d'adhérents pour cette année
                sheet = createOrResetMembersList(year)  # On créait ou on réinitialise le fichier liste des adhérents correspondant

                # On doit par conséquent créer le nouvel adhérent pour cette année
                newMember = Member(payment["mail"], payment["nom"], payment["prenom"], payment["adresse"],
                                   payment["cp"], payment["ville"], payment["telephone"])
                newMember.addPayment(payment["montant"], payment["source"], payment["date"], payment["refPaiement"],
                                     False)
                membersByYear[year].append(newMember)
            else:  # S'il y a déjà une liste d'adhérents pour cette année
                nbMember = getNbMemberInList(payment["mail"], payment["nom"], payment["prenom"], membersByYear[year])
                if nbMember:  # S'il y a déjà cet adhérent dans la liste
                    # On le met à jour (si besoin)
                    member = membersByYear[year][nbMember]
                    member.updateContactData(payment["adresse"], payment["cp"], payment["ville"], payment["telephone"])
                    member.addPayment(payment["montant"], payment["source"], payment["date"], payment["refPaiement"],
                                      True)
                else:
                    # Sinon on le créait
                    newMember = Member(payment["mail"], payment["nom"], payment["prenom"], payment["adresse"],
                                       payment["cp"], payment["ville"], payment["telephone"])
                    newMember.addPayment(payment["montant"], payment["source"], payment["date"], payment["refPaiement"],
                                         False)
                    membersByYear[year].append(newMember)

#years.sort(reverse=True)
years.sort()

# nbReceipts = 0


"""for year in years:
    for member in membersByYear[year]:
        prevYearStr = str(int(year)-1)
        if membersByYear[prevYearStr] != []:
            nbMember = getNbMemberInList(member.email, member.name, member.surname, membersByYear) #to fix: Pourquoi membersByYear contient l'année à la fin ?
            if type(nbMember) is int:
                paidMembershipNextYear = membersByYear[prevYearStr][nbMember].amounts["paidMembershipNextYear"]
                print(paidMembershipNextYear) #Pas afficher
                if paidMembershipNextYear > 0:
                    member.amounts["paidMembershipLastYear"] = paidMembershipNextYear

        total = member.amounts["totalYear"]
        restToPay = member.rate-member.amounts["paidMembershipLastYear"]
        membershipThisYear = min(restToPay, total)

        membershipNextYear = 0
        if datetime.strptime(member.receipts[-1].date, "%d/%m/%Y").month >= 9 and total >= member.rate*2:  # Après septembre
            membershipNextYear = min(restToPay, total-membershipThisYear)

        totalDonation = total - membershipThisYear - membershipNextYear

        member.amounts["paidMembershipYear"] = membershipThisYear
        member.amounts["paidMembershipNextYear"] = membershipNextYear
        member.amounts["donationsYear"] = totalDonation"""


for year in years:
    membersByYear[year] = sorted(membersByYear[year], key=lambda member: member.lastPayment or datetime.min)
    workbookPath = paths["listesAdherents"] / f"{year}.xlsx"
    workbook = load_workbook(filename=workbookPath)
    sheet = workbook.active

    for member in membersByYear[year]:
        # Vérification que tous les adhérents ont des coordonnées de contact valides
        if member.hasValidAddress():
            # Création des reçus
            receiptsToPDFs(member.receipts)
            save.addMemberReceipts(member)
            """if receiptsToPDFs(member.receipts):
                nbReceipts+=1
            else:
                logging.error("Une erreur est survenue lors de l'édition des")"""
        else:
            logging.warning(
                member.surname + ' ' + member.name + " n'a pas de coordonnées de contact valides. L'édition de ses reçus est impossible.")





        """for y in years:  # On parcourt chaque année précédente
            if y < year:
                nbMember = getNbMemberInList(member.email, member.name, member.surname, membersByYear[y])
                if nbMember is not False:  # Est-ce que c'est un ancien adhérent ?
                    if int(y) == int(year) - 1:  # Est-ce que c'est currAnnée-1 ?
                        print( membersByYear[y][nbMember].amounts["paidMembershipNextYear"])
                        if membersByYear[y][nbMember].amounts["paidMembershipNextYear"] > 0:  # Est-ce que l'adh a déjà réglé une partie de l'adhésion ?
                            member.amounts["paidMembershipLastYear"] = membersByYear[y][nbMember].amounts["paidMembershipNextYear"]

                    if member.status == "NA":  # Si l'adh a déjà donné cette année
                        member.status = "RA"
                        member.lastMembership = y

                    break"""
        # Calculer les montants
        #member.calcAmounts()

        sheet.append(member.toArray())

    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.border = styles.borderBody

    workbook.save(workbookPath)
    workbook.close()

save.save()
