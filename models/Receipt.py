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
        baseID = datetime.strptime(date, "%d/%m/%Y").strftime("%y%m%d") + member.surname[0].upper() + member.name[0].upper()
        if self.regular:
            baseID += 'R'  # Pour régulier
        memberEmail = member.email
        while Save().isMemberReceiptExported(memberEmail, baseID+str(num)):
            if Save().getRefPaymentReceipt(memberEmail, baseID+str(num)) != self.refPayment:
                num += 1
            else:
                break
        self.id = baseID+str(num)

        self.amount = float(amount)
        self.canBeExported = self.amount >= 15  # TODO : const dans settings
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
            "name": member.name + ' ' + member.surname,
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
