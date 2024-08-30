import csv
from datetime import datetime
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
from utils.LogManager import LogManager
from utils.PathManager import PathManager
from utils.Thunderbird import Thunderbird


def getDataFromPaymentsFile(path, source):
    payments = []

    def addToPayments(payment):
        if newPayment.isValid:
            payments.append(payment)
        else:
            LogManager().addLog("update", LogManager.LOGTYPE_WARNING,
                                f"Impossible de traiter le paiement '{payment.source.upper()}' venant de '{payment.name} {payment.surname}'. Référence du paiement : '{payment.refPayment}'.\nRaison -> {payment.notValidCause}")

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
            if all(row[key] is not None for key in requiredCols) and row[
                "Carte de crédit/débit - État "].casefold() == "completed":
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
            LogManager().addLog("update", LogManager.LOGTYPE_INFO, f"Fichier {membersList} créé.")
            return sheet
        except OSError as error:
            LogManager().addLog("error", LogManager.LOGTYPE_ERROR,
                                f"Impossible de créer le fichier {membersList} : {error}.")
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
            LogManager().addLog("error", LogManager.LOGTYPE_ERROR,
                                f"Impossible de créer le fichier {membersList} : {error}.")
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

        members = sorted(members, key=attrgetter(
            "lastPayment"))  # Trie des membres selon la date du dernier paiement, par ordre chronologique
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
        LogManager().addLog("update", LogManager.LOGTYPE_INFO, f"Succès de l'exportation du fichier {filePath}")
    except(Exception,) as error:
        LogManager().addLog("update", LogManager.LOGTYPE_ERROR,
                            f"Une erreur est survenue lors de l'exportation du fichier {filePath}.\n{error}")


def exportMemberReceipts(members):
    for member in members:
        if member.hasValidAddress():
            try:  # Exportation des PDFs
                receipts = member.receipts
                if member.regularPaymentsReceipt is not None:
                    receipts.append(member.regularPaymentsReceipt)
                exportedReceipts = _exportReceipts(receipts)

                try:  # Sauvegarde des reçus exportés avec succès
                    Save().addMemberReceipt(member.email, exportedReceipts)

                except(Exception,) as error:
                    LogManager().addLog("update", LogManager.LOGTYPE_ERROR,
                                        f"Une erreur est survenue lors de l'enregistrement de '{member.name} {member.surname}' dans le fichier de sauvegarde : {error}")

            except(Exception,) as error:
                LogManager().addLog("update", LogManager.LOGTYPE_ERROR,
                                    f"Une inconnue est survenue lors de l'exportation des reçus de '{member.name} {member.surname} : {error}'")

        else:
            LogManager().addLog("update", LogManager.LOGTYPE_WARNING,
                                f"{member.surname} {member.name}  n'a pas de coordonnées de contact valides. L'édition de ses reçus est impossible.")


def _exportReceipts(receipts):  # TODO : Vérifier si erreur avant de faire exportedReceipts.append(receipt)
    paths = PathManager().getPaths()

    reader = PdfReader(paths["assets"]["PDFTemplate"])
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
            receiptDate = datetime.strptime(receipt.date, "%d/%m/%Y")
            year, month = str(receiptDate.year), str(receiptDate.month)
            directory = path.join(paths["recusFiscaux"], year, month)

            isDirOK = True
            if not path.isdir(directory):
                try:
                    Path(directory).mkdir(parents=True, exist_ok=True)
                    LogManager().addLog("update", LogManager.LOGTYPE_INFO, f"Dossier créé : {directory}")
                except OSError as error:
                    LogManager().addLog("update", LogManager.LOGTYPE_ERROR,
                                        f"Impossible de créer le dossier {directory} : {error}")
                    isDirOK = False

            if isDirOK:
                filepath = path.join(directory, f"{receipt.id}.pdf")
                # Vérifier si le reçu existe déjà et qu'il est identique. Doit également vérifier s'il existe bien dans le répertoire.
                receiptData = receipt.getDataDict()
                newHash = receipt.getHash()
                savedHash = None
                if path.isfile(filepath):
                    savedHash = Save().getSavedReceiptHash(receipt.member.email, receipt.id)
                if savedHash != newHash:
                    writer.update_page_form_field_values(
                        writer.pages[0],
                        receiptData,
                        auto_regenerate=False
                    )

                    with open(filepath, "wb") as output_stream:
                        writer.write(output_stream)
                        LogManager().addLog("update", LogManager.LOGTYPE_INFO, f"Création du reçu '{receipt.id}'.")

                exportedReceipts.append(receipt)
    return exportedReceipts


def importMembers():  # S'il y a plusieurs fois le même membre dans plusieurs listes, on fusionne ses ID de reçus
    paths = PathManager().getPaths()
    memberListsPattern = paths["memberListsPattern"]

    members = {}

    for listPath in memberListsPattern:
        workbook = load_workbook(filename=listPath)
        sheet = workbook.active
        requiredCols = [0, 1, 2, 3]  # Indices des colonnes à vérifier pour les valeurs non nulles
        year = int(str(sheet.cell(row=1, column=14).value).replace("Adh. ", ''))
        for row in sheet.iter_rows(min_row=2):
            if all(row[idx].value is not None for idx in requiredCols):
                email = row[0].value
                IDReceipts = row[3].value.split(';')
                if email not in members:
                    member = {
                        "name": row[1].value,
                        "surname": row[2].value,
                        "IDReceipts": IDReceipts,
                        "years": [year]
                    }
                    members[email] = member
                else:
                    members[email]["IDReceipts"] = list(set(members[email]["IDReceipts"] + IDReceipts))  # todo append ?
                    members[email]["years"].append(year)

        workbook.close()

    return members


def importReceipts():  # Obtient les données venant de Save + Thunderbird (pour les status des mails)
    thunderbirdEmails = Thunderbird().getStatusEmails()
    allMembersInSave = Save().members
    receipts = {}
    for email, member in allMembersInSave.items():
        receipts[email] = {}
        if "receipts" in member:
            for id, receipt in member["receipts"].items():
                datetimeReceipt = datetime.strptime(id[:6], "%y%m%d")
                dateStrReceipt = datetimeReceipt.strftime("%d/%m/%Y")
                receipt["date"] = dateStrReceipt
                receipts[email][id] = receipt
                if id in thunderbirdEmails:
                    statusID = thunderbirdEmails[id]
                else:
                    statusID = 0

                if statusID == 0:
                    statusTxt = "Non préparé"
                elif statusID == 1:
                    statusTxt = "Préparé"
                elif statusID == 2:
                    statusTxt = "Envoyé"
                elif statusID == 3:
                    statusTxt = "Supprimé"
                else:
                    statusTxt = '?'

                receipts[email][id]["emailStatus"] = statusTxt

    return receipts
