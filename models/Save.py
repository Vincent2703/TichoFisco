import hashlib
import json
import os

import orjson as orjson

from utils.misc import saveHiddenFile


class Save:
    def __init__(self):
        self.receipts = {}
        self.receiptsCache = {}  # Ids des reçus mis à jour/créés. Permet de savoir quels reçus on doit supprimer de la sauvegarde.
        self.members = {}
        self.config = {}
        if not os.path.isfile(".save"):
            open(".save", "x")

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
        self.members[memberEmail] = {"notes": memberNotes}

    def load(self):
        if os.stat(".save").st_size > 0:
            with open(".save", 'r') as saveFile:
                saveContent = saveFile.read()
                saveJSON = orjson.loads(saveContent)  # TODO: Manage errors
                self.receipts = saveJSON["receipts"]
                self.members = saveJSON["members"]
                self.config = saveJSON["config"]

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
            "config": self.config
        })
        saveHiddenFile(".save", JSONContent, binary=True)
