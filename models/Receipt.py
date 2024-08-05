import datetime

from main import paths


class Receipt:
    def __init__(self, member, amount, date, source):
        self.member = member
        self.id = datetime.now().strftime("%y%m%d")+member.surname[0].upper().to+member.name[0].upper()+'0'
        self.amount = amount
        self.date = date
        if source == "helloAsso":
            self.source = "Hello Asso"
        elif source == "paypal":
            self.source = "Paypal"
        elif source == "cb":
            self.source = "Carte Bancaire"
        else:
            self.source = source

    def toPDF(self):
        template = "../assets/templateReceiptTicho2.pdf"
        destFilePath = paths["recusFiscaux"]/f"{self.id}.pdf"
        dataToFill = {}
