import os
from tkinter import END

from models.Save import Save
from utils.FileManager import importMembers, importReceipts
from utils.PathManager import PathManager
from utils.Thunderbird import Thunderbird
from utils.misc import openFile

ALL_MEMBERS = "Tous les adhérents"
ALL_YEARS = "Toutes"


class Receipts:
    def __init__(self, view=None):
        self.selectedMember = None
        self.view = view
        if self.view:
            self.progressBar = view.progressBar
            self.lastQuery = None

        self.paths = PathManager().getPaths()
        self.members = self._getMembersList()
        self.receipts = self._getReceiptsList()

    def setView(self, view):
        self.view = view
        if self.view:
            self.progressBar = view.progressBar
            self.lastQuery = None

    def updateViewData(self, reloadFiles=True, reloadQuery=True):
        if self.view:
            if reloadFiles:
                self.members = self._getMembersList()
                self.receipts = self._getReceiptsList()

            self._setMembersCbxValues(self._getKVMembersCbx())
            self.queryUpdate(reloadQuery=reloadQuery)
            self._hideBtns()

    def _setMembersCbxValues(self, members):
        membersList = list(members.values())
        membersList.insert(0, ALL_MEMBERS)
        self.view.membersCbx["values"] = membersList
        self.view.membersCbx.set(ALL_MEMBERS)

    def _setReceiptsTrvsValues(self, receipts):
        # Suppression des données existantes dans les Treeviews
        for treeview in [self.view.receiptsRegTrv, self.view.receiptsIrregTrv]:
            for row in treeview.get_children():
                treeview.delete(row)

        # Insertion des nouveaux reçus dans les Treeviews
        for email, regReceipts in receipts["regulars"].items():
            for id, receipt in regReceipts.items():
                self.view.receiptsRegTrv.insert('', END, text=email,
                                                values=(receipt["date"], id, receipt["amount"], receipt["emailStatus"]))

        for email, irregReceipts in receipts["irregulars"].items():
            for id, receipt in irregReceipts.items():
                self.view.receiptsIrregTrv.insert('', END, text=email,
                                                  values=(receipt["date"], id, receipt["amount"], receipt["emailStatus"]))

        nbReceipts = self._getNbReceipts(receipts)
        self._setNbReceiptsNtbkTab("regulars", nbReceipts["regulars"])
        self._setNbReceiptsNtbkTab("irregulars", nbReceipts["irregulars"])

    def _setYearsCbxValues(self, years):
        if len(years) == 0 or years[0] != ALL_YEARS:
            years.insert(0, ALL_YEARS)
        self.view.yearsCbx["values"] = years
        self.view.yearsCbx.set(ALL_YEARS)

    def _getMembersList(self):
        return importMembers()

    def _getReceiptsList(self):
        return importReceipts()

    def _getKVMembersCbx(self):
        dictMembers = {}
        members = dict(sorted(self.members.items(), key=lambda item: item[1]["lastName"]))
        for email, member in members.items():
            dictMembers[email] = f"{member["lastName"]} {member["firstName"]}"

        return dictMembers

    def _getAllReceipts(self):
        receiptsByRegStatus = {
            "regulars": {},
            "irregulars": {}
        }
        for email, receipts in self.receipts.items():
            for id, receipt in receipts.items():
                regKey = "regulars" if receipt["regular"] else "irregulars"
                receiptsByRegStatus[regKey].setdefault(email, {})[id] = receipt

        return receiptsByRegStatus

    def _getReceiptsByEmail(self, email):
        receiptsByRegStatus = {
            "regulars": {email: {}},
            "irregulars": {email: {}}
        }
        if email in self.receipts:
            for id, receipt in self.receipts[email].items():
                regKey = "regulars" if receipt["regular"] else "irregulars"
                receiptsByRegStatus[regKey][email][id] = receipt

        return receiptsByRegStatus

    def _getYears(self):
        return os.listdir(str(self.paths["recusFiscaux"]))

    def queryUpdate(self, member=ALL_MEMBERS, year=ALL_YEARS, reloadQuery=False):
        if reloadQuery and self.lastQuery:
            member = self.lastQuery["member"]
            year = self.lastQuery["year"]
        self.lastQuery = {"member":member, "year":year}

        # Si tous les membres sont sélectionnés
        if member == ALL_MEMBERS:
            receipts = self._getAllReceipts()
            self._setYearsCbxValues(self._getYears())
        else:
            # Trouver l'email du membre sélectionné
            memberEmail = next((k for k, v in self._getKVMembersCbx().items() if v == member), None)
            receipts = self._getReceiptsByEmail(memberEmail)
            self._setYearsCbxValues(self.members[memberEmail]["years"])

        # Filtrage des reçus par an si une année spécifique est sélectionnée
        if year != ALL_YEARS:
            receipts = self._filterReceiptsByYear(receipts, year)

        self._setReceiptsTrvsValues(receipts)
        self.view.membersCbx.set(member)
        self.view.yearsCbx.set(year)

    def _getNbReceipts(self, receipts):
        nbReceipts = {"regulars": 0, "irregulars": 0}
        for regStatus, members in receipts.items():
            for email, memberReceipts in members.items():
                nbReceipts[regStatus] += len(memberReceipts)
        return nbReceipts

    def _setNbReceiptsNtbkTab(self, regStatus, nb):
        if regStatus == "irregulars":
            self.view.receiptsNtbk.tab(0, text=f"Dons ponctuels ({nb})")
        elif regStatus == "regulars":
            self.view.receiptsNtbk.tab(1, text=f"Dons réguliers ({nb})")

    def _filterReceiptsByYear(self, receipts, year):
        filteredReceipts = {"regulars": {}, "irregulars": {}}
        for regStatus, membersReceipts in receipts.items():
            for email, memberReceipts in membersReceipts.items():
                for id, receipt in memberReceipts.items():
                    if receipt["date"].endswith(year):
                        if email not in filteredReceipts[regStatus]:
                            filteredReceipts[regStatus][email] = {}
                        filteredReceipts[regStatus][email][id] = receipt
        return filteredReceipts

    def _getSelectedRows(self):
        view = self.view
        # Identifier la frame active
        activeFrame = view.receiptsNtbk.nametowidget(view.receiptsNtbk.select())

        # En fonction de la frame active, récupérer le Treeview correspondant
        if activeFrame == view.regularsFr:
            activeTreeview = view.receiptsRegTrv
        else:
            activeTreeview = view.receiptsIrregTrv

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

    def _getPathFromID(self, ID):  # TODO A déplacer
        # Pour bien faire, il faudrait avoir le chemin du reçu dans une colonne cachée
        # Mais là on va juste le récupérer via son ID
        year = f"20{ID[:2]}"
        month = str(int(ID[2:4]))
        path = PathManager().getPaths()["recusFiscaux"] / year / month / f"{ID}.pdf"
        return path

    def openReceiptCb(self):
        selection = self._getSelectedRows()
        if selection:
            for row in selection:
                # On récupère son identifiant
                receiptID = row[2]
                path = self._getPathFromID(receiptID)
                openFile(path)

    def prepareEmail(self):
        selection = self._getSelectedRows()
        nbSteps = len(selection)
        thunderbirdRunning = Thunderbird().isRunning()
        preparedEmails = []
        if thunderbirdRunning:
            nbSteps += 1
        if selection:
            self.progressBar.setNbSteps(nbSteps)
            for row in selection:
                toEmail = row[0]
                idReceipt = row[2]
                filePath = self._getPathFromID(idReceipt)
                Thunderbird().addMail(to=toEmail, filePath=filePath)
                self.progressBar.incrementProgress(labelTxt="Nombre de mails préparés", showStep=True)
                preparedEmails.append({"emailMember": toEmail, "idReceipt": idReceipt, "emailStatus": 1})
        if thunderbirdRunning:
            self.progressBar.incrementProgress(labelTxt="Redémarrage de Thunderbird en cours")
            Thunderbird().reloadThunderbird()

        if len(preparedEmails) > 0:
            Save().updateMembersReceiptsEmailStatus(preparedEmails)

    def _hideBtns(self):
        self.view.openReceiptBtn.pack_forget()
        self.view.prepareEmailBtn.pack_forget()

    def showBtns(self):
        self.view.openReceiptBtn.pack()
        self.view.prepareEmailBtn.pack()

