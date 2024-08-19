import os
from datetime import datetime
from glob import glob
from tkinter import END

from models.Save import Save
from utils.FileManager import importMembers
from utils.PathManager import PathManager

ALL_MEMBERS = "Tous les adhérents"
ALL_YEARS = "Toutes"

class Receipts:
    def __init__(self, view=None):
        self.selectedMember = None
        self.view = view

        self.paths = PathManager().getPaths()
        self.members = self._getMembersList()
        self.receipts = self._getReceiptsList()

    def setView(self, view):
        self.view = view

    def updateViewData(self, reloadFiles=True):
        if self.view:
            if reloadFiles:
                self.members = self._getMembersList()
                self.receipts = self._getReceiptsList()

            self._setMembersCbxValues(self._getKVMembersCbx())
            self._setYearsCbxValues(self._getYears())
            self._setReceiptsTrvsValues(self._getAllReceipts())

    def _setMembersCbxValues(self, members):
        membersList = list(members.values())
        membersList.insert(0, "Tous les adhérents")
        self.view.membersCbx["values"] = membersList
        self.view.membersCbx.set("Tous les adhérents")  # TODO : set by index

    def _setReceiptsTrvsValues(self, receipts):
        # Suppression des données existantes dans les Treeviews
        for treeview in [self.view.receiptsRegTrv, self.view.receiptsIrregTrv]:
            for row in treeview.get_children():
                treeview.delete(row)

        # Insertion des nouveaux reçus dans les Treeviews
        for email, regReceipts in receipts["regulars"].items():
            for id, receipt in regReceipts.items():
                self.view.receiptsRegTrv.insert('', END, text=email,
                                           values=(receipt["date"], id, receipt["amount"], receipt["sent"]))

        for email, irregReceipts in receipts["irregulars"].items():
            for id, receipt in irregReceipts.items():
                self.view.receiptsIrregTrv.insert('', END, text=email,
                                             values=(receipt["date"], id, receipt["amount"], receipt["sent"]))

    def _setYearsCbxValues(self, years):
        years.insert(0, "Toutes")
        self.view.yearsCbx["values"] = years
        self.view.yearsCbx.set("Toutes")  # TODO : set by index

    def _getMembersList(self):
        return importMembers()

    def _getKVMembersCbx(self):
        dictMembers = {}
        members = dict(sorted(self.members.items(), key=lambda item: item[1]["name"]))
        for email, member in members.items():
            dictMembers[email] = f"{member['name']} {member['surname']}"

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

    def _getReceiptsList(self):
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

        return receipts

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

    def queryUpdate(self, member=ALL_MEMBERS, year=ALL_YEARS):
        # Si tous les membres sont sélectionnés
        if member == ALL_MEMBERS:
            receipts = self._getAllReceipts()
            self._setYearsCbxValues(self._getYears())
        else:
            # Trouver l'email du membre sélectionné
            memberEmail = next((k for k, v in self._getKVMembersCbx().items() if v == member), None)
            receipts = self._getReceiptsByEmail(memberEmail)
            self._setYearsCbxValues(self.members[memberEmail]["years"])

        # Filtrage des reçus par année si une année spécifique est sélectionnée
        if year != ALL_YEARS:
            receipts = self._filterReceiptsByYear(receipts, year)

        self._setReceiptsTrvsValues(receipts)
        self.view.membersCbx.set(member)
        self.view.yearsCbx.set(year)

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
