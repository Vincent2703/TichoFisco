import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from models.Member import Member
from models.Save import Save
from utils.FileManager import initMembersFile, getDataFromPaymentsFile, exportMembersFile, exportMemberReceipts
from utils.PathManager import PathManager
from utils.misc import openDir


class Update:
    def __init__(self):
        self.paths = PathManager().getPaths()

    def openDataDir(self):
        dirPath = self.paths["actuel"]
        if not openDir(dirPath):
            logging.error(f"Impossible d'ouvrir le dossier : '{dirPath}'")

    def processPayments(self):
        def getNbMemberInList(email, name, surname, list):  # Permet de retrouver un adhérent parmi une liste d'instances
            for nbMember, member in enumerate(list):
                if member.isThisMember(email, name, surname):
                    return nbMember
            return False

        membersByYear = defaultdict(list)  # Contiendra la liste des membres pour chaque année
        years = []  # Liste des années

        """
        Dans un premier temps, on récupère les données des fichiers de paiements
        puis à partir de ces données, on enregistre les adhérents ainsi que leurs paiements
        """
        defaultRate = Save().defaultRate["value"]
        for source, filePaths in self.paths["paymentFilesPatterns"].items():  # Pour chaque fichier de paiement récupéré
            for filePath in filePaths:
                for payment in getDataFromPaymentsFile(filePath, source):  # On obtient ses données
                    year = payment.year
                    if year not in years:  # Si est pas encore tombé sur l'année, on doit soit créer le fichier liste des adhérents correspondant, ou alors le réinit
                        years.append(year)
                        membersByYear[year] = []
                        membersNotesRate = {}
                        membersList = self.paths["listesAdherents"] / f"{year}.xlsx"
                        if Path(membersList).is_file():  # Si le fichier existe déjà
                            workbook = load_workbook(membersList)
                            sheet = workbook.active
                            for row in sheet.iter_rows(min_row=2, max_row=len(sheet['A'])-4):  # On regarde s'il y a des remarques à récupérer pour les remettre dans le fichier final si l'adh y est toujours présent
                                memberEmail = row[0].value
                                notes = row[20].value
                                rate = row[19].value
                                if notes is not None or rate != defaultRate:
                                    membersNotesRate[memberEmail] = {"notes": '', "rate": defaultRate}
                                if notes is not None:
                                    membersNotesRate[memberEmail]["notes"] = str(notes)
                                if rate != defaultRate:
                                    membersNotesRate[memberEmail]["rate"] = float(rate)

                        initMembersFile(year)  # Réinit/Création de la liste des adhérents

                    newMember = Member(payment.email, payment.name, payment.surname, payment.address,
                                       payment.postalCode, payment.city, payment.phone)  # TODO : set by keys
                    if payment.email in membersNotesRate:  # Si on a récup des remarques ou un tarif pour cet adh
                        if membersNotesRate[payment.email]["notes"] is not None:
                            newMember.notes = membersNotesRate[payment.email]["notes"]  # On enregistre les remarques pour l'instance
                        if membersNotesRate[payment.email]["rate"] != defaultRate :
                            memberRate = membersNotesRate[payment.email]["rate"]
                            if str(memberRate).replace('.', '').isnumeric():  # Si c'est une valeur numérique
                                newMember.rate = float(memberRate)  # On enregistre le tarif directement
                            else:  # Sinon on cherche si ça correspond à un nom de tarif enregistré
                                rate = Save().getRateByName(str(memberRate))
                                if rate is not None:
                                    newMember.rate = rate["value"]
                                else:
                                    logging.warning(f"Le tarif renseigné pour {newMember.name} {newMember.surname} est incorrect : '{memberRate}'.\nLe tarif par défaut sera utilisé à la place.")
                                    newMember.rate = Save().defaultRate["value"]

                    nbMember = getNbMemberInList(newMember.email, newMember.name, newMember.surname, membersByYear[year])
                    if type(nbMember) is int:  # Si on a déjà l'adh pour l'année en question
                        member = membersByYear[year][nbMember]
                        member.updateContactData(payment.address, payment.postalCode, payment.city,
                                                 payment.phone)  # On met à jour ses coords de contact si besoin
                        member.addPayment(payment)  # Puis on ajoute son paiement à sa liste de paiements
                    else:
                        membersByYear[year].append(newMember)  # Sinon on ajoute le nouveau adh pour l'année en question
                        newMember.addPayment(payment)  # On ajoute le paiement à sa liste de paiements

        years.sort()  # On trie la liste par ordre chrn

        """
        Dans un second temps, on va regarder si pour chaque adhérent, celui-ci est enregistré dans l'une des années précédentes.
        Son statut ainsi que les valeurs des différents montants pourront être mis à jour.
        """

        for year in years:
            for member in membersByYear[year]:
                prevYear = int(year) - 1
                if len(membersByYear[prevYear]) > 0:
                    nbMember = getNbMemberInList(member.email, member.name, member.surname,
                                                 membersByYear[prevYear])
                    if type(nbMember) is int:
                        paidMembershipNextYear = membersByYear[prevYear][nbMember].amounts["paidMembershipNextYear"]
                        if paidMembershipNextYear > 0:
                            member.amounts["paidMembershipLastYear"] = paidMembershipNextYear
                            member.lastMembership = int(year) - 1

                total = member.amounts["totalYear"]
                restToPay = member.rate - member.amounts["paidMembershipLastYear"]
                membershipThisYear = min(restToPay, total)

                membershipNextYear = 0
                if datetime.strptime(member.receipts[-1].date, "%d/%m/%Y").month >= 9 and total >= member.rate:
                    membershipNextYear = min(restToPay, total - membershipThisYear)
                    member.status = "RAA"

                totalDonation = total - membershipThisYear - membershipNextYear

                member.amounts["paidMembershipYear"] = membershipThisYear
                member.amounts["paidMembershipNextYear"] = membershipNextYear
                member.amounts["donationsYear"] = totalDonation

                if member.status == "NA" or member.status == "DON-ADH":
                    for yearPrec in years:
                        nbMember = getNbMemberInList(member.email, member.name, member.surname, membersByYear[yearPrec])
                        if type(nbMember) is int:
                            if yearPrec < year:
                                member.lastMembership = yearPrec
                                member.status = "RA"

        """Enfin, on exporte les listes des adhérents (Xslx) et les reçus (PDF) """
        for year in years:
            exportMembersFile(self.paths["listesAdherents"] / f"{year}.xlsx", membersByYear[year])
            exportMemberReceipts(membersByYear[year])

        """ Puis on sauvegarde """
        Save().save()

        logging.info("Succès du traitement des fichiers de paiements.")
        return "SUCCESS"
