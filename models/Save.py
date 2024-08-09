import hashlib
import json
import os


class Save:
    def __init__(self):
        self.receipts = {}
        self.receiptsIDCache = []  # Ids des reçus mis à jour/créés. Permet de savoir quels reçus on doit supprimer de la sauvegarde.
        self.members = {}
        self.config = {}
        if not os.path.isfile(".save"):
            open(".save", "x")

    def cacheThisReceiptID(self, receiptID):
        self.receiptsIDCache.append(receiptID)

    def addMemberReceipts(self, member):
        for receipt in member.receipts:
            receiptData = receipt.toDict()
            receiptDataStr = json.dumps(receiptData, sort_keys=True, default=str)
            self.receipts[receipt.id] = {
                "hash": hashlib.md5(receiptDataStr.encode("utf-8")).hexdigest(),
                "refPayment": receipt.refPayment,
                "sent": False
            }

    def load(self):
        if os.stat(".save").st_size > 0:
            with open(".save", 'r') as saveFile:
                saveContent = saveFile.read()
                saveJSON = json.loads(saveContent)  # TODO: Manage errors
                self.receipts = saveJSON["receipts"]
                self.members = saveJSON["members"]
                self.config = saveJSON["config"]

    def isIDReceiptExists(self, idReceipt):
        return idReceipt in self.receipts

    def getReceiptByID(self, idReceipt):
        if self.isIDReceiptExists(idReceipt):
            return self.receipts[idReceipt]
        return None

    def getHashReceipt(self, idReceipt):
        if self.isIDReceiptExists(idReceipt):
            return self.receipts[idReceipt]["hash"]
        return None

    def save(self):
        receiptsToSave = {id: self.receipts[id] for id in self.receiptsIDCache if id in self.receipts}

        content = {
            "receipts": receiptsToSave,
            "members": self.members,
            "config": self.config
        }
        with open(".save", "w") as outfile:
            json.dump(content, outfile)
