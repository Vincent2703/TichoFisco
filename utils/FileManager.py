import csv
import logging
import os
from datetime import datetime
from hashlib import md5
from json import dumps
from operator import attrgetter
from os import path
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from pypdf import PdfReader, PdfWriter
from pypdf import generic

from models.Payment import Payment
from models.Save import Save
from utils import styles, misc
from utils.PathManager import PathManager


def getDataFromPaymentsFile(path, source):
    payments = []

    def addToPayments(payment):
        if newPayment.isValid:
            payments.append(payment)
        else:
            logging.warning(
                f"Impossible d'ajouter le paiement '{payment.source.upper()}' venant de '{payment.name} {payment.surname}'. Ref: '{payment.refPayment}'.\n{payment.notValidCause}")

    if source != "cb":
        workbook = load_workbook(filename=path)
        sheet = workbook.active
    else:
        csvContent = []
        with open(path, mode='r') as csvFile:
            csvReader = csv.DictReader(csvFile, delimiter=',')
            for row in csvReader:
                csvContent.append(row)

    if source == "helloAsso":
        requiredCols = [1, 2, 5, 6, 7]  # Indices des colonnes à vérifier pour les valeurs non nulles
        for row in sheet.iter_rows(min_row=2):
            if all(row[idx].value is not None for idx in requiredCols):
                newPayment = Payment(
                    email=row[7].value,
                    name=row[5].value,
                    surname=row[6].value,
                    date=row[2].value.strftime("%d/%m/%Y"),
                    regular=row[8].value == "Crowdfunding",
                    address=row[9].value,
                    postalCode=str(row[10].value),
                    city=row[11].value,
                    phone='',
                    amount=float(row[1].value),
                    source=source,
                    refPayment=row[0].value
                )
                addToPayments(newPayment)

    elif source == "paypal":
        requiredCols = [0, 2, 8, 9, 4]
        for row in sheet.iter_rows(min_row=4):
            if all(row[idx].value is not None for idx in requiredCols) and row[4].value == "Terminé" and float(
                    row[8].value) > 0:
                names = row[2].value.rsplit(' ', 1)
                newPayment = Payment(
                    email=row[9].value,
                    name=names[0],
                    surname=names[1],
                    date=row[0].value.strftime("%d/%m/%Y"),
                    regular=row[3].value == "Paiement d'abonnement",
                    address=row[11].value,
                    postalCode=str(row[13].value or ''),
                    city=row[12].value,
                    phone='',
                    amount=float(row[8].value),
                    source=source,
                    refPayment=row[10].value
                )
                addToPayments(newPayment)

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

                newPayment = Payment(
                    email=row[2].value,
                    name=row[3].value,
                    surname=row[4].value,
                    date=row[0].value.strftime("%d/%m/%Y"),
                    regular=row[10].value == "O",
                    address=row[5].value,
                    postalCode=str(row[6].value),
                    city=row[7].value,
                    phone='',
                    amount=float(row[8].value),
                    source=source,
                    refPayment=row[1].value
                )
                addToPayments(newPayment)

    elif source == "cb":
        requiredCols = ["Heure de soumission", "Nom", "Prénom", "E-mail", "Carte de crédit/débit - Montant",
                        "Carte de crédit/débit - État "]
        for row in csvContent:
            if all(row[key] is not None for key in requiredCols) and row["Carte de crédit/débit - État "].casefold() == "completed":
                newPayment = Payment(
                    email=row["E-mail"],
                    name=row["Nom"],
                    surname=row["Prénom"],
                    date=misc.convertFrenchDate(row["Heure de soumission"]).strftime("%d/%m/%Y"),
                    regular=False,
                    address=row["Address - Rue"] + ' ' + row["Address - Appartement, suite, etc."],
                    postalCode=str(row["Address - Code postal"]),
                    city=row["Address - Ville"],
                    phone=str(row["Téléphone"]),
                    amount=float(row["Carte de crédit/débit - Montant"]),
                    source=source,
                    refPayment=str(row["Carte de crédit/débit - ID de la transaction"])
                )
                addToPayments(newPayment)

    return payments


def initMembersFile(year):  # Création du fichier ou réinitialisation
    membersList = PathManager().getPaths()["listesAdherents"] / f"{year}.xlsx"
    if not Path(membersList).is_file():
        try:
            year = str(year)
            precYear = str(int(year) - 1)
            nextYear = str(int(year) + 1)

            workbook = Workbook()
            sheet = workbook.active

            fields = ["Adresse mail", "Nom", "Prénom", "IDs reçus", "Statut",
                      "Dern. adh.", "Régulier", "Envoi mails", "Adresse", "Code postal", "Ville", "Téléphone",
                      "Adh. " + precYear, "Adh. " + year, "Adh. " + nextYear,
                      "Dons " + year, "Total " + year, "Dern. paiement", "Dern. moy. paiement", "Tarif", "Remarques"]

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
                cell.alignment = styles.centerAlign

            # Sauvegarder le fichier
            workbook.save(membersList)
            workbook.close()
            logging.info(f"Fichier {membersList} créé")
            return sheet
        except OSError as error:
            logging.error(f"Impossible de créer le fichier {membersList} : {error}")
            return False
    else:  # Sinon remettre tout à zero
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


def exportMembersFile(filePath, members):
    def calcTotalsPayments(members):
        totals = {
            "withReceipt": 0,
            "withoutReceipt": 0,
            "nbReceipts": 0
        }
        for member in members:
            for receipt in member.receipts:
                if receipt.canBeExported:
                    totals["withReceipt"] += receipt.amount
                    totals["nbReceipts"] += 1
                else:
                    totals["withoutReceipt"] += receipt.amount
        return totals

    try:
        workbook = load_workbook(filename=filePath)
        sheet = workbook.active

        members = sorted(members, key=attrgetter("lastPayment"))  # Trie des membres selon la date du dernier paiement, par ordre chronologique
        for member in members:  # On ajoute chaque membre au fichier Excel
            sheet.append(member.toArray())

        # Calculer et afficher les totaux pour les paiements
        totals = calcTotalsPayments(members)
        startTotalsRow = len(sheet['A']) + 2
        sheet.cell(startTotalsRow, 1).value = "Nombre de reçus"
        sheet.cell(startTotalsRow, 2).value = totals["nbReceipts"]
        sheet.cell(startTotalsRow + 1, 1).value = "Total avec reçus"
        sheet.cell(startTotalsRow + 1, 2).value = totals["withReceipt"]
        sheet.cell(startTotalsRow + 2, 1).value = "Total sans reçus"
        sheet.cell(startTotalsRow + 2, 2).value = totals["withoutReceipt"]

        for row in sheet.iter_rows(min_row=2):  # Et pour le body du tableau, on applique le style correspondant
            for cell in row:
                cell.border = styles.borderBody

        workbook.save(filePath)  # Puis on sauvegarde
        workbook.close()
        logging.info(f"Succès de l'exportation du fichier {filePath}")
    except(Exception,) as error:
        logging.error(f"Une erreur est survenue lors de l'exportation du fichier {filePath}.\n{error}")


def exportMemberReceipts(members):
    for member in members:
        if member.hasValidAddress():
            try:  # Exportation des PDFs
                exportedReceipts = _exportReceipts(member.receipts)
            except(Exception,) as error:
                logging.error(f"Une erreur est survenue lors de l'exportation des reçus de '{member.name} {member.surname}'")

            try:  # Sauvegarde des reçus et des éventuelles remarques et tarifs
                Save().addReceipts(exportedReceipts)
                if member.notes is not None:
                    Save().addMemberNotes(member.email, member.notes)
                if member.rate != Save().defaultRate["value"]:  # Si ce n'est pas le tarif par défaut, on l'enregistre
                    Save().addMembersRate(member.email, member.rate)
            except(Exception,) as error:
                logging.error(f"Une erreur est survenue lors de l'enregistrement de '{member.name} {member.surname}' dans le fichier de sauvegarde.")
        else:
            logging.warning(
                member.surname + ' ' + member.name + " n'a pas de coordonnées de contact valides. L'édition de ses reçus est impossible.")



def _exportReceipts(receipts):
    paths = PathManager().getPaths()

    reader = PdfReader(paths["PDFTemplate"])
    writer = PdfWriter(clone_from=reader)
    # writer.set_need_appearances_writer(True)

    writerItems = writer.get_fields().items()

    for k, v in writerItems:  # readonly
        o = v.indirect_reference.get_object()
        if o["/FT"] != "/Sig":
            o[generic.NameObject("/Ff")] = generic.NumberObject(o.get("/Ff", 0) | 1)

    exportedReceipts = []
    for receipt in receipts:
        if receipt.canBeExported:
            exportedReceipts.append(receipt)
            receiptDate = datetime.strptime(receipt.date, "%d/%m/%Y")
            year, month = str(receiptDate.year), str(receiptDate.month)
            directory = path.join(paths["recusFiscaux"], year, month)
            if not path.isdir(directory):
                try:
                    Path(directory).mkdir(parents=True, exist_ok=True)
                    logging.info(f"Dossier créé : {directory}")
                except OSError as error:
                    logging.error(f"Impossible de créer le dossier {directory} : {error}")
            filepath = path.join(directory, f"{receipt.id}.pdf")

            # Vérifier si le reçu existe déjà et qu'il est identique. Doit également vérifier s'il existe bien dans le répertoire.
            receiptData = receipt.toDict()
            receiptDataStr = dumps(receiptData, sort_keys=True, default=str)  # JSON
            newHash = md5(receiptDataStr.encode("utf-8")).hexdigest()
            savedHash = None
            if path.isfile(filepath):
                savedHash = Save().getHashReceipt(receipt.id)

            if savedHash != newHash:
                writer.update_page_form_field_values(
                    writer.pages[0],
                    receiptData,
                    auto_regenerate=False
                )

                with open(filepath, "wb") as output_stream:
                    writer.write(output_stream)
                    logging.info(f"Création du reçu '{receipt.id}'.")

    return exportedReceipts


def importMembers():  # S'il y a plusieurs fois le même membre dans plusieurs listes, on fusionne ses ID de reçus
    paths = PathManager().getPaths()
    memberListsPattern = paths["memberListsPattern"]

    members = {}

    for listPath in memberListsPattern:
        workbook = load_workbook(filename=listPath)
        sheet = workbook.active
        requiredCols = [0, 1, 2]  # Indices des colonnes à vérifier pour les valeurs non nulles
        for row in sheet.iter_rows(min_row=2):
            if all(row[idx].value is not None for idx in requiredCols):
                email = row[0].value
                IDReceipts = row[3].value.split(';')
                if email not in members:
                    member = {
                        "name": row[1].value,
                        "surname": row[2].value,
                        "IDReceipts": IDReceipts
                    }
                    members[email] = member
                else:
                    members[email]["IDReceipts"] = list(set(members[email]["IDReceipts"] + IDReceipts))

        workbook.close()

    return members
