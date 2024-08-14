from datetime import datetime

from utils.loadSave import save


class Receipt:
    def __init__(self, member, amount, source, date, refPayment):
        self.member = member
        self.refPayment = str(refPayment)

        num = 1
        baseID = datetime.strptime(date, "%d/%m/%Y").strftime("%y%m%d") + member.surname[0].upper() + member.name[0].upper()
        while save.isIDReceiptExistsInCache(baseID+str(num)):
            if save.getCachedReceiptRefPaymentByID(baseID+str(num)) != self.refPayment:
                num += 1
            else:
                break
        self.id = baseID+str(num)

        self.amount = float(amount)
        self.canBeExported = self.amount >= 15
        self.date = date
        if source == "helloAsso":
            self.source = "Hello Asso"
        elif source == "paypal":
            self.source = "Paypal"
        elif source == "cb":
            self.source = "Carte Bancaire"
        else:
            self.source = source

    def toDict(self):  # private ?
        member = self.member
        return {
            "idReceipt": "ID reçu : " + self.id,
            "name": member.name + ' ' + member.surname,
            "address": member.address,
            "postalCode": member.postalCode,
            "city": member.city,
            "amount": "**" + "{:.2f}".format(self.amount).replace('.', ',') + "**",
            "paymentDate": self.date,
            "paymentYear": str(datetime.strptime(self.date, "%d/%m/%Y").year),
            "paymentSource": self.source,
            "editionDate": datetime.now().strftime("%d/%m/%Y")
        }
