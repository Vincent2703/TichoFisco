from datetime import datetime

from models.Member import Member
from models.Save import Save
from utils import FileManager
from utils.FileManager import getDataFromPaymentsFile, exportMembersFile, exportMemberReceipts
from utils.LogManager import LogManager
from utils.PathManager import PathManager
from models.Thunderbird import Thunderbird
from utils.misc import openDir, isFileInUse


class Update:
    def __init__(self, view=None):
        """
        Initialise l'instance d'Update avec les chemins de fichiers et la vue associée.
        Si une vue est fournie, initialise également la barre de progression.

        Paramètres :
            - view : la vue associée (optionnelle).
        """
        self.view = view
        if self.view:
            self.progressBar = view.progressBar

        self.paths = PathManager().getPaths()
        self.paymentFiles = self.paths["paymentFilesPatterns"].items()

        self.years = []  # Contiendra la liste des années contenant des informations sur les adhérents

    def setView(self, view):
        """
        Associe une vue à l'instance d'Update et initialise la barre de progression si la vue est fournie.

        Paramètres :
            - view : la vue à associer.
        """
        self.view = view
        if self.view:
            self.progressBar = view.progressBar

    def openDataDir(self):
        """
        Ouvre le répertoire de données actuel et gère les erreurs d'ouverture.

        Retourne :
            - True si le répertoire a été ouvert avec succès, False sinon.
        """
        dirPath = self.paths["actuel"]
        if not openDir(dirPath):
            LogManager().addLog("OS", LogManager.LOGTYPE_ERROR, f"Impossible d'ouvrir le dossier : '{dirPath}'")
            return False
        return True

    def processPayments(self):
        """
        Fonction principale pour faire une mise à jour.
        Récupère les informations des fichiers de paiement.
        Exportation des listes d'adhérents, des reçus fiscaux, du fichier de cache et des contacts sur Thunderbird.

        Retourne :
            - Le plus haut statut des logs "update" générés. Indique s'il y a eu des problèmes (critiques ou non).
        """
        PathManager().update()
        self.paths = PathManager().getPaths()
        self.paymentFiles = self.paths["paymentFilesPatterns"].items()

        membersListOpen = False
        for filepath in self.paths["memberListsPattern"]:
            if isFileInUse(filepath):
                membersListOpen = True

        if membersListOpen:
            return "membersListOpen"
        else:
            # Initialisation de la barre de progression
            if self.view:
                nbSteps = 0
                for files in self.paymentFiles:  # todo : on peut pas faire len(files) ?
                    nbSteps += len(files[1])
                self.progressBar.setNbSteps(nbSteps)

            # Traitement des fichiers de paiement
            payments = self.getPaymentsData()  # By year and member email
            self.progressBar.resetProgress()

            if len(payments) > 0:
                years = list(payments.keys())  # Les clés de payments sont les années des paiements, sans doublon
                self.progressBar.setNbSteps(len(years * 2))  # *2 pour la récupération des données + création/reset des listes d'adhérents

                existingMembersData = {}
                for year in years:
                    # Récupération des éventuels notes et tarifs spéciaux dans les anciennes listes d'adhérents, si existantes
                    existingMembersData[year] = FileManager.getExistingMembersData(year)

                    # Création ou réinitialisation de la liste des adhérents de l'année
                    FileManager.initMembersFile(year)
                    self.progressBar.incrementProgress(labelTxt="Récupération et recréation des listes", showStep=True, hideAfterFinish=False, incrSteps=2)

                self.progressBar.resetProgress()

                membersByYear, emailContacts = self.createMembers(payments, existingMembersData)

                # Mise à jour des membres avec les informations des années précédentes
                self.updateMembersFromPreviousYears(membersByYear)

                self.exportFiles(membersByYear)

                self.saveCacheAndEmailContacts(emailContacts)
            else:
                LogManager().addLog("update", LogManager.LOGTYPE_WARNING, "Aucun paiement n'a été trouvé/validé")

        return LogManager().getHigherStatusOf("update")

    def getPaymentsData(self):
        """
        Récupère les informations de paiement à partir des fichiers.

        Retourne :
            - Les paiements groupés par année et par mail d'dhérent.
                La liste des paiements de chaque adhérent est trié par ordre chronologique.
        """
        payments = {}  # Par année et par mail d'adhérent
        for source, filePaths in self.paymentFiles:
            for filePath in filePaths:
                self.progressBar.incrementProgress(labelTxt="Traitement des fichiers de paiements", showStep=True, hideAfterFinish=False)
                for payment in getDataFromPaymentsFile(filePath, source):
                    year = payment.year
                    email = payment.email
                    payments.setdefault(year, {}).setdefault(email, []).append(payment)  # Ajout l'année et l'email s'il n'y a pas déjà l'entrée

        # Trier les paiements pour chaque membre par date
        for year, members in payments.items():
            for email, paymentList in members.items():
                paymentList.sort(key=lambda p: datetime.strptime(p.date, "%d/%m/%Y"))  # Tri par date

        return payments

    def createMembers(self, payments, existingMembersData):
        """
        Cette fonction crée ou met à jour des instances Member à partir des données de paiement fournies et des données existantes des membres.

        Paramètres :
            payments (dict): Un dictionnaire contenant les paiements des membres groupés par année et par mail d'adhérent.
            existingMembersData (dict): Un dictionnaire similaire contenant les données existantes des membres (remarques, tarifs, etc.).

        Retourne :
            dict: Un dictionnaire trié chronologiquement contenant les membres par année et email.
            dict: Un dictionnaire associant les emails des membres à leurs informations de contact (prénom et nom).
        """
        self.progressBar.setNbSteps(sum(len(member) for member in payments.values()))

        emailContacts = {}
        membersByYear = {}

        # Itération sur les années et les paiements associés
        for year, memberPayments in payments.items():
            membersByYear[year] = {}

            for email, payments in memberPayments.items():
                self.progressBar.incrementProgress(labelTxt="Création des adhérents", showStep=True, hideAfterFinish=False)
                for payment in payments:
                    # Création du membre ou mise à jour des informations du membre existant
                    if email not in membersByYear[year]:
                        membersByYear[year][email] = Member(email, payment.lastName, payment.firstName, payment.address, payment.postalCode, payment.city, payment.phone)
                    else:
                        membersByYear[year][email].updateContactData(payment.address, payment.postalCode, payment.city, payment.phone)
                    membersByYear[year][email].addPayment(payment)

                    if email not in emailContacts:
                        emailContacts[email] = {"firstName": membersByYear[year][email].firstName, "lastName": membersByYear[year][email].lastName}

                    # Récupération des données existantes pour le membre, si disponibles
                    if year in existingMembersData and email in existingMembersData[year]:
                        existingData = existingMembersData[year][email]

                        # Mise à jour des remarques et du tarif
                        if "notes" in existingData:
                            membersByYear[year][email].notes = existingData["notes"]

                        if "rate" in existingData:
                            memberRate = existingData["rate"]
                            try:
                                # Vérification si le tarif est numérique
                                rate_value = float(memberRate)
                            except ValueError:
                                # Si ce n'est pas numérique, on cherche le tarif par nom
                                rate = Save().getRateByName(str(memberRate))
                                if rate:
                                    rate_value = rate["value"]
                                else:
                                    LogManager().addLog(
                                        "update", LogManager.LOGTYPE_WARNING,
                                        f"Le tarif renseigné pour {membersByYear[year][email].lastName} {membersByYear[year][email].firstName} est incorrect : '{memberRate}'.\nLe tarif par défaut sera utilisé à la place."
                                    )
                                    rate_value = Save().defaultRate["value"]

                            membersByYear[year][email].rate = rate_value

        self.progressBar.resetProgress()
        return dict(sorted(membersByYear.items())), emailContacts  # Trie par ordre chronologique

    def updateMembersFromPreviousYears(self, membersByYear):  # todo A renommer ! S'occupe aussi de calculer les montants
        """
        Met à jour les informations des membres en utilisant les données des années précédentes.

        Args:
            membersByYear (dict): Dictionnaire des membres classés par année.
        """
        self.progressBar.setNbSteps(len(membersByYear.items()))
        # Parcours des années et de leurs membres
        for year, members in membersByYear.items():
            self.progressBar.incrementProgress(labelTxt="Mise à jour des adhérents", showStep=True, hideAfterFinish=False)
            prevYear = int(year) - 1

            # Itération sur chaque membre de l'année en cours
            for currentMember in members.values():
                # Vérifie si le membre existe dans l'année précédente
                if prevYear in membersByYear and currentMember.email in membersByYear[prevYear]:
                    prevMember = membersByYear[prevYear][currentMember.email]

                    # Met à jour les montants de l'année précédente si le membre a payé pour l'année suivante
                    paidMembershipLastYear = prevMember.amounts["paidMembershipNextYear"]
                    if paidMembershipLastYear > 0:
                        currentMember.amounts["paidMembershipLastYear"] = min(currentMember.rate, paidMembershipLastYear)

                # Calcul des montants de l'année en cours
                total = currentMember.amounts["totalYear"]
                restToPay = currentMember.rate - currentMember.amounts["paidMembershipLastYear"]
                membershipThisYear = min(restToPay, total)

                # Détermine le montant de la cotisation pour l'année suivante
                membershipNextYear = 0
                # Extraction des dates des reçus (s'ils existent)
                lastReceiptDate = datetime.strptime(currentMember.receipts[-1].date,
                                                    "%d/%m/%Y") if currentMember.receipts else None
                regularPaymentDate = datetime.strptime(currentMember.regularPaymentsReceipt.date,
                                                       "%d/%m/%Y") if currentMember.regularPaymentsReceipt else None
                # Vérification de la validité des reçus
                isValidLastReceipt = lastReceiptDate and lastReceiptDate.month >= 9
                isValidRegularPayment = regularPaymentDate and regularPaymentDate.month >= 9

                if (isValidLastReceipt or isValidRegularPayment) and total >= currentMember.rate:
                    membershipNextYear = min(restToPay, total - membershipThisYear)
                    currentMember.status = "RAA"

                # Calcul des dons totaux
                totalDonation = total - membershipThisYear - membershipNextYear

                # Mise à jour des montants du membre
                currentMember.amounts["paidMembershipYear"] = membershipThisYear
                currentMember.amounts["paidMembershipNextYear"] = membershipNextYear
                currentMember.amounts["donationsYear"] = totalDonation

                # Mise à jour du statut du membre si nécessaire
                if currentMember.status in {"NA", "DON-ADH"}:
                    # Trouve l'année précédente la plus récente où le membre est présent
                    for precYear in sorted(membersByYear.keys()):
                        if currentMember.email in membersByYear[precYear] and precYear < int(year):
                            currentMember.lastMembership = precYear
                            if currentMember.status == "NA":
                                currentMember.status = "RA"
                                break  # On met à jour le statut une seule fois

    def exportFiles(self, membersByYear):
        """
          Exporte les listes d'adhérents pour chaque année et génère les reçus fiscaux.
          La barre de progression est mise à jour à chaque étape.

          Paramètres :
              membersByYear (dict): Un dictionnaire contenant les membres classés par année et email.
          """
        self.progressBar.setNbSteps(1)

        for year, members in membersByYear.items():
            self.progressBar.incrementProgress(labelTxt=f"Exportation de la liste des adhérents pour l'année {year}", showStep=False, hideAfterFinish=False)
            exportMembersFile(self.paths["listesAdherents"] / f"liste des adhérents {year}.xlsx", members)
            #self.progressBar.incrementProgress(labelTxt=f"Exportation des reçus fiscaux pour l'année {year} en cours", showStep=False, hideAfterFinish=False)
            self.progressBar.setNbSteps(len(members))
            exportMemberReceipts(members, self.progressBar) #C'est pas propre mais chut
        self.progressBar.resetProgress()

    def saveCacheAndEmailContacts(self, emailContacts):
        """
            Sauvegarde le cache et exporte les contacts des membres vers Thunderbird.
            La barre de progression est mise à jour.

            Paramètres :
                emailContacts (dict): Un dictionnaire contenant les emails et noms des contacts à exporter.
            """
        self.progressBar.setNbSteps(2)

        # On sauvegarde la liste de contacts Thunderbird
        self.progressBar.incrementProgress(labelTxt="Exportation des contacts", showStep=False, hideAfterFinish=False)
        Thunderbird().addContactsToList(emailContacts)

        self.progressBar.incrementProgress(labelTxt="Sauvegarde", showStep=False, hideAfterFinish=True)
        Save().save(refreshDate=True)
