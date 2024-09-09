import os
from tkinter import END

from models.Save import Save
from utils.FileManager import importMembers, importReceipts
from utils.PathManager import PathManager
from models.Thunderbird import Thunderbird
from utils.misc import openFile

ALL_MEMBERS = "Tous les adhérents"
ALL_YEARS = "Toutes"


class Receipts:
    def __init__(self, view=None):
        self.selectedMember = None
        self.view = view
        self.frames = self.view.frames if self.view else None
        self.widgets = self.view.widgets if self.view else None
        self.lastQuery = None
        self.paths = PathManager().getPaths()
        self.members = self._getMembersList()
        self.receipts = self._getReceiptsList()

    def setView(self, view):
        """
        Associe une vue à l'instance de Receipts.
        """
        self.view = view
        if self.view:
            self.frames = self.view.frames
            self.widgets = self.view.widgets
            self.lastQuery = None

    def updateViewData(self, reloadFiles=True, reloadQuery=True):
        """
        Met à jour les données de la vue.
        """
        if self.view:
            if reloadFiles:
                self.members = self._getMembersList()
                self.receipts = self._getReceiptsList()

            self._setMembersCbxValues(self._getKVMembersCbx())
            self.queryUpdate(reloadQuery=reloadQuery)
            self._hideBtns()

    def _setMembersCbxValues(self, members):
        """
        Définit les valeurs du combobox des membres.
        """
        membersList = list(members.values())
        membersList.insert(0, ALL_MEMBERS)
        membersCbx = self.widgets["membersCbx"]
        membersCbx["values"] = membersList
        membersCbx.set(ALL_MEMBERS)

    def _setReceiptsTrvsValues(self, receipts):
        """
        Remplit les Treeviews avec les reçus des membres.
        """
        regTrv, irregTrv = self.widgets["receiptsRegTrv"], self.widgets["receiptsIrregTrv"]
        self._clearTreeviews([regTrv, irregTrv])

        # Insertion des reçus réguliers et irréguliers
        for email, irregReceipts in receipts["irregulars"].items():
            for id, receipt in irregReceipts.items():
                irregTrv.insert('', END, text=email, values=(receipt["date"], id, receipt["amount"], receipt["emailStatus"]))

        for email, regReceipts in receipts["regulars"].items():
            for id, receipt in regReceipts.items():
                regTrv.insert('', END, text=email, values=(receipt["date"], id, receipt["amount"], receipt["emailStatus"]))

        nbReceipts = self._getNbReceipts(receipts)
        self._setNbReceiptsNtbkTab("irregulars", nbReceipts["irregulars"])
        self._setNbReceiptsNtbkTab("regulars", nbReceipts["regulars"])

    def _clearTreeviews(self, treeviews):
        """
        Supprime les données des Treeviews.
        """
        for treeview in treeviews:
            for row in treeview.get_children():
                treeview.delete(row)

    def _setYearsCbxValues(self, years):
        """
        Définit les valeurs du combobox des années.
        """
        yearsCbx = self.widgets["yearsCbx"]
        if len(years) == 0 or years[0] != ALL_YEARS:
            years.insert(0, ALL_YEARS)
        yearsCbx["values"] = years
        yearsCbx.set(ALL_YEARS)

    def _getMembersList(self):
        """
        Retourne la liste des membres importés.
        """
        return importMembers()

    def _getReceiptsList(self):
        """
        Retourne la liste des reçus importés.
        """
        return importReceipts()

    def _getKVMembersCbx(self):
        """
        Retourne un dictionnaire des membres avec leur email en clé et leur nom complet en valeur.
        """
        dictMembers = {}
        members = dict(sorted(self.members.items(), key=lambda item: item[1]["lastName"]))
        for email, member in members.items():
            dictMembers[email] = f"{member['lastName']} {member['firstName']}"
        return dictMembers

    def _getAllReceipts(self):
        """
        Retourne tous les reçus, séparés en réguliers et irréguliers.
        """
        receiptsByRegStatus = {"regulars": {}, "irregulars": {}}
        for email, receipts in self.receipts.items():
            for id, receipt in receipts.items():
                regKey = "regulars" if receipt["regular"] else "irregulars"
                receiptsByRegStatus[regKey].setdefault(email, {})[id] = receipt
        return receiptsByRegStatus

    def _getReceiptsByEmail(self, email):
        """
        Retourne les reçus d'un membre par son email.
        """
        receiptsByRegStatus = {"regulars": {email: {}}, "irregulars": {email: {}}}
        if email in self.receipts:
            for id, receipt in self.receipts[email].items():
                regKey = "regulars" if receipt["regular"] else "irregulars"
                receiptsByRegStatus[regKey][email][id] = receipt
        return receiptsByRegStatus

    def _getYears(self):
        """
        Retourne la liste des années disponibles dans les reçus fiscaux.
        """
        return os.listdir(str(self.paths["recusFiscaux"]))

    def queryUpdate(self, member=ALL_MEMBERS, year=ALL_YEARS, reloadQuery=False):
        """
        Met à jour les reçus en fonction du membre et de l'année sélectionnés.
        """
        if reloadQuery and self.lastQuery:
            member, year = self.lastQuery["member"], self.lastQuery["year"]
        self.lastQuery = {"member": member, "year": year}

        if member == ALL_MEMBERS:
            receipts = self._getAllReceipts()
            self._setYearsCbxValues(self._getYears())
        else:
            memberEmail = next((k for k, v in self._getKVMembersCbx().items() if v == member), None)
            receipts = self._getReceiptsByEmail(memberEmail)
            self._setYearsCbxValues(self.members[memberEmail]["years"])

        if year != ALL_YEARS:
            receipts = self._filterReceiptsByYear(receipts, year)

        self._setReceiptsTrvsValues(receipts)

    def _getNbReceipts(self, receipts):
        """
        Retourne le nombre de reçus réguliers et irréguliers.
        """
        nbReceipts = {"regulars": 0, "irregulars": 0}
        for regStatus, members in receipts.items():
            nbReceipts[regStatus] += sum(len(memberReceipts) for memberReceipts in members.values())
        return nbReceipts

    def _setNbReceiptsNtbkTab(self, regStatus, nb):
        """
        Met à jour l'onglet des reçus avec le nombre de reçus.
        """
        receiptsNtbk = self.widgets["receiptsNtbk"]
        tabText = f"Dons réguliers ({nb})" if regStatus == "regulars" else f"Dons ponctuels ({nb})"
        receiptsNtbk.tab(1 if regStatus == "regulars" else 0, text=tabText)

    def _filterReceiptsByYear(self, receipts, year):
        """
        Filtre les reçus par année.
        """
        filteredReceipts = {"regulars": {}, "irregulars": {}}
        for regStatus, membersReceipts in receipts.items():
            for email, memberReceipts in membersReceipts.items():
                filteredReceipts[regStatus][email] = {id: receipt for id, receipt in memberReceipts.items() if receipt["date"].endswith(year)}
        return filteredReceipts

    def _getSelectedRows(self):
        receiptsNtbk = self.widgets["receiptsNtbk"]
        regularsFr = self.frames["regularsFr"]
        regTrv, irregTrv = self.widgets["receiptsRegTrv"], self.widgets["receiptsIrregTrv"]

        # Identifier la frame active
        activeFrame = receiptsNtbk.nametowidget(receiptsNtbk.select())

        # En fonction de la frame active, récupérer le Treeview correspondant
        if activeFrame == regularsFr:
            activeTreeview = regTrv
        else:
            activeTreeview = irregTrv

        # Obtenir la ligne sélectionnée dans le Treeview actif
        selection = activeTreeview.selection()

        if selection:
            allValues = []
            # Récupérer les valeurs des lignes sélectionnées
            for row in selection:
                item = activeTreeview.item(row)
                itemValues = item["values"]
                itemText = item["text"]
                itemValues.insert(0, itemText)
                allValues.append(itemValues)

            return allValues
        return False

    def _getPathFromID(self, ID):
        # Pour bien faire, il faudrait avoir le chemin du reçu dans une colonne cachée
        # Mais là on va juste le récupérer via son ID
        year = f"20{ID[:2]}"
        month = str(int(ID[2:4]))
        path = PathManager().getPaths()["recusFiscaux"] / year / month / f"{ID}.pdf"
        return path

    def openReceiptCb(self):
        """
        Ouvre les reçus sélectionnés dans un visualiseur externe.
        """
        selection = self._getSelectedRows()
        if selection:
            for row in selection:
                receiptID = row[2]
                path = self._getPathFromID(receiptID)
                openFile(path)

    def prepareEmail(self):
        """
        Prépare l'envoi des reçus par email via Thunderbird.
        """
        selection = self._getSelectedRows()
        nbSteps = len(selection)
        progressBar = self.widgets["progressBar"]
        thunderbirdRunning = Thunderbird().isRunning()
        preparedEmails = []

        if thunderbirdRunning:
            nbSteps += 1

        if selection:
            progressBar.setNbSteps(nbSteps)
            for row in selection:
                toEmail, idReceipt = row[0], row[2]
                filePath = self._getPathFromID(idReceipt)
                Thunderbird().addMail(to=toEmail, filePath=filePath)
                progressBar.incrementProgress(labelTxt="Nombre de mails préparés", showStep=True)
                preparedEmails.append({"emailMember": toEmail, "idReceipt": idReceipt, "emailStatus": 1})

            if thunderbirdRunning:
                progressBar.incrementProgress(labelTxt="Redémarrage de Thunderbird en cours")
                Thunderbird().reloadThunderbird()

        if preparedEmails:
            Save().updateMembersReceiptsEmailStatus(preparedEmails)

    def _hideBtns(self):
        """
        Cache les boutons d'ouverture de reçus et de préparation d'email.
        """
        self.widgets["openReceiptBtn"].pack_forget()
        self.widgets["prepareEmailBtn"].pack_forget()

    def showBtns(self):
        """
        Affiche les boutons d'ouverture de reçus et de préparation d'email.
        """
        self.widgets["openReceiptBtn"].pack()
        self.widgets["prepareEmailBtn"].pack()

