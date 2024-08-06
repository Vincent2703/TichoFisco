from datetime import datetime


class Receipt:
    def __init__(self, member, amount, source, date):
        self.member = member
        # Vérifier si reçu le même jour
        self.id = datetime.strptime(date, "%d/%m/%Y").strftime("%y%m%d") + member.surname[0].upper() + member.name[0].upper() + '0'
        self.amount = float(amount)
        self.date = date
        if source == "helloAsso":
            self.source = "Hello Asso"
        elif source == "paypal":
            self.source = "Paypal"
        elif source == "cb":
            self.source = "Carte Bancaire"
        else:
            self.source = source

    def toDict(self):
        member = self.member
        return {
            "idReceipt": self.id,
            "name": member.name,
            "surname": member.surname,
            "address": member.address,
            "postalCode": member.postalCode,
            "city": member.city,
            "amount": "**" + "{:.2f}".format(self.amount) + "**",
            "paymentDate": self.date,
            "paymentSource": self.source,
            "editionDate": datetime.now().strftime("%d/%m/%Y")
        }
