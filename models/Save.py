import hashlib
import json
import os
from os.path import isfile

import orjson as orjson

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

            # self.receipts = {}
            # self.receiptsCache = {}  # Ids des reçus mis à jour/créés. Permet de savoir quels reçus on doit supprimer de la sauvegarde.
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
        for rate in self.settings["rates"]:
            if "default" in rate and rate["default"] is True:
                return rate
        return None

    def getRateByName(self, name):
        for rate in self.settings["rates"]:
            if rate["name"].casefold().replace(' ', '') == name.casefold().replace(' ', ''):
                return rate
        return None

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
                "sent": False
            }

    def _isMemberExported(self, memberEmail):
        return memberEmail in self.exportedMembers

    def isMemberReceiptExported(self, memberEmail, idReceipt):
        return self._isMemberExported(memberEmail) and idReceipt in self.members[memberEmail]["receipts"]

    def getRefPaymentReceipt(self, memberEmail, idReceipt):
        if self.isMemberReceiptExported(memberEmail, idReceipt):
            return self.exportedMembers[memberEmail]["receipts"][idReceipt]["refPayment"]

    def getSavedReceiptHash(self, memberEmail, idReceipt):
        if memberEmail in self.members:
            if idReceipt in self.members[memberEmail]["receipts"]:
                return self.members[memberEmail]["receipts"][idReceipt]["hash"]
        return None

    def save(self):
        JSONContent = orjson.dumps({
            "members": self.exportedMembers,
            "settings": self.settings
        })
        saveHiddenFile(self.saveFilePath, JSONContent, binary=True)

        self.members = self.exportedMembers
