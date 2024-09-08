from datetime import datetime
from hashlib import md5

from orjson import orjson

from models.Save import Save


class Receipt:
    def __init__(self, member, amount, source, date, refPayment, regular=False):
        self.member = member
        self.refPayment = str(refPayment)

        self.regular = regular

        num = 1
        baseID = datetime.strptime(date, "%d/%m/%Y").strftime("%y%m%d") + member.firstName[0].upper() + member.lastName[0].upper()
        if self.regular:
            baseID += 'R'  # 'R' pour "régulier"
        memberEmail = member.email

        while baseID+str(num) in Save().idReceipts:
            if Save().getRefPaymentReceipt(memberEmail, baseID+str(num)) != self.refPayment:
                num += 1
            else:
                break
        self.id = baseID+str(num)

        self.amount = float(amount)
        self.canBeExported = self.amount >= Save().settings["receipts"]["minimalAmount"]

        if self.canBeExported:
            Save().idReceipts.append(self.id)

        self.date = date
        if source == "helloAsso":
            self.source = "Hello Asso"
        elif source == "paypal":
            self.source = "Paypal"
        elif source == "cb":
            self.source = "Carte Bancaire"
        else:
            self.source = source

    def getDataDict(self, editionDate=True):
        member = self.member
        dict = {
            "idReceipt": "ID reçu : " + self.id,
            "name": f"{member.lastName} {member.firstName}",
            "address": member.address,
            "postalCode": member.postalCode,
            "city": member.city,
            "amount": "**" + "{:.2f}".format(self.amount).replace('.', ',') + "**",
            "paymentDate": self.date,
            "paymentYear": str(datetime.strptime(self.date, "%d/%m/%Y").year),
            "paymentSource": self.source,
        }
        if editionDate:
            dict["editionDate"] = datetime.now().strftime("%d/%m/%Y")
        return dict

    def getHash(self):
        dict = self.getDataDict(editionDate=False)
        json = orjson.dumps(dict)
        hash = md5(json).hexdigest()
        return hash
