import os
from os.path import isfile

import orjson as orjson

from utils.LogManager import LogManager
from utils.PathManager import PathManager
from utils.misc import saveHiddenFile


class Save:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Save, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.saveFilePath = PathManager().getPaths()["save"]

            self.idReceipts = []  # Ce tableau contiendra l'ensemble des identifiants des reçus générés. Permet de générer une chaîne unique

            self.members = {}  # Ce dict est rempli au lancement du prog grâce au fichier .save
            self.exportedMembers = {}  # Ce dict est rempli lors de la mise à jour des infos. C'est lui qui sera exporté à la fin
            self.settings = {}
            if os.path.isfile(self.saveFilePath):
                self.load()
            else:
                defaultSettings = {
                    "rates": [
                        {"name": "Sans emploi", "value": 10},
                        {"name": "Individuel", "value": 18, "default": True},
                        {"name": "Familial", "value": 25},
                        {"name": "Association", "value": 30},
                    ]
                }
                self.settings = defaultSettings

            self.defaultRate = self._getDefaultRate()

            self._initialized = True

    def _getDefaultRate(self):
        return next((rate for rate in self.settings.get("rates", []) if rate.get("default")), None)

    def getRateByName(self, name):
        normalizedName = name.casefold().replace(' ', '')
        return next((rate for rate in self.settings.get("rates", [])
                     if rate["name"].casefold().replace(' ', '') == normalizedName), None)

    def load(self):
        if isfile(self.saveFilePath) and os.stat(self.saveFilePath).st_size > 0:
            with open(self.saveFilePath, 'r') as saveFile:
                saveContent = saveFile.read()
                saveJSON = orjson.loads(saveContent)  # TODO: Manage errors
                self.members = saveJSON["members"]
                self.settings = saveJSON["settings"]

    def addMemberReceipt(self, memberEmail, receipts):
        for receipt in receipts:
            hash = receipt.getHash()
            if not self._isMemberExported(memberEmail):
                self.exportedMembers[memberEmail] = {"receipts": {}}

            self.exportedMembers[memberEmail]["receipts"][receipt.id] = {
                "hash": hash,
                "regular": receipt.regular,
                "amount": receipt.amount,
                "refPayment": receipt.refPayment,  # TODO Pourrait être un tableau si reg
                "canBeExported": receipt.canBeExported,
                #"emailStatus": None
            }

    def _isMemberExported(self, memberEmail):
        return memberEmail in self.exportedMembers

    def isMemberReceiptExported(self, memberEmail, idReceipt):
        return self._isMemberExported(memberEmail) and idReceipt in self.exportedMembers[memberEmail]["receipts"]

    def getRefPaymentReceipt(self, memberEmail, idReceipt):
        return self.exportedMembers.get(memberEmail, {}).get("receipts", {}).get(idReceipt, {}).get("refPayment")

    def updateMembersReceiptsEmailStatus(self, receipts):
        if len(self.exportedMembers) == 0:
            self.exportedMembers = self.members

        for receipt in receipts:
            email = receipt["emailMember"]
            idReceipt = receipt["idReceipt"]
            emailStatus = receipt["emailStatus"]
            if self.isMemberReceiptExported(email, idReceipt):
                self.exportedMembers[email]["receipts"][idReceipt]["emailStatus"] = emailStatus
        self.save()

    def getSavedReceiptHash(self, memberEmail, idReceipt):
        return self.members.get(memberEmail, {}).get("receipts", {}).get(idReceipt, {}).get("hash")

    def save(self):
        try:
            # On enregistre le fichier .save
            jsonContent = orjson.dumps({
                "members": self.exportedMembers,
                "settings": self.settings
            })
            saveHiddenFile(self.saveFilePath, jsonContent, binary=True)
            self.members = self.exportedMembers
        except Exception as e:
            LogManager().addLog("OS", f"Erreur lors de la sauvegarde : {e}")
