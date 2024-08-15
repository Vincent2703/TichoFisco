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

            self.receipts = {}
            self.receiptsCache = {}  # Ids des reçus mis à jour/créés. Permet de savoir quels reçus on doit supprimer de la sauvegarde.
            self.members = {}
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
                """JSONContent = orjson.dumps({
                    "receipts": {},
                    "members": {},
                    "settings": self.settings
                })
                saveHiddenFile(self.saveFilePath, JSONContent, True)"""
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
                self.receipts = saveJSON["receipts"]
                self.members = saveJSON["members"]
                self.settings = saveJSON["settings"]

    def cacheThisReceipt(self, receipt):
        self.receiptsCache[receipt.id] = receipt.refPayment

    def addReceipts(self, receipts):
        for receipt in receipts:
            receiptData = receipt.toDict()
            receiptDataStr = json.dumps(receiptData, sort_keys=True, default=str)
            self.receipts[receipt.id] = {
                "hash": hashlib.md5(receiptDataStr.encode("utf-8")).hexdigest(),
                "refPayment": receipt.refPayment,
                "canBeExported": receipt.canBeExported,
                "sent": False
            }

    def addMemberNotes(self, memberEmail, memberNotes):
        if memberEmail not in self.members:
            self._addMember(memberEmail)
        self.members[memberEmail]["notes"] = memberNotes

    def addMembersRate(self, memberEmail, memberRate):
        if memberEmail not in self.members:
            self._addMember(memberEmail)
        self.members[memberEmail]["rate"] = memberRate

    def _addMember(self, memberEmail):
        self.members[memberEmail] = {"notes": '', "rate": self.defaultRate}

    def isIDReceiptExistsInCache(self, idReceipt):
        return idReceipt in self.receiptsCache

    def getCachedReceiptRefPaymentByID(self, idReceipt):
        if self.isIDReceiptExistsInCache(idReceipt):
            return self.receiptsCache[idReceipt]
        return None

    def getHashReceipt(self, idReceipt):
        if idReceipt in self.receipts:
            return self.receipts[idReceipt]["hash"]
        return None

    def save(self):
        receiptsToSave = {id: self.receipts[id] for id in self.receiptsCache if id in self.receipts}

        JSONContent = orjson.dumps({
            "receipts": receiptsToSave,
            "members": self.members,
            "settings": self.settings
        })
        saveHiddenFile(self.saveFilePath, JSONContent, binary=True)
