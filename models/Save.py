import hashlib
import json
import os


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

    def addMemberReceipts(self, member):
        for receipt in member.receipts:
            receiptData = receipt.toDict()
            receiptDataStr = json.dumps(receiptData, sort_keys=True, default=str)
            self.receipts[receipt.id] = {
                "hash": hashlib.md5(receiptDataStr.encode("utf-8")).hexdigest(),
                "refPayment": receipt.refPayment,
                "sent": False
            }

    def addMemberNotes(self, memberEmail, memberNotes):
        self.members[memberEmail] = {"notes": memberNotes}

    def load(self):
        if os.stat(".save").st_size > 0:
            with open(".save", 'r') as saveFile:
                saveContent = saveFile.read()
                saveJSON = json.loads(saveContent)  # TODO: Manage errors
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

        content = {
            "receipts": receiptsToSave,
            "members": self.members,
            "config": self.config
        }
        with open(".save", "w") as outfile:
            json.dump(content, outfile)
