from datetime import datetime

from models.Receipt import Receipt


class Member:
    def __init__(self, email, name, surname, address, postalCode, city, phone):
        self.email = email
        self.name = name.upper()
        self.surname = surname[0].upper() + surname[1:].lower()

        self.receipts = []
        self.status = "NA"
        self.lastMembership = None
        self.sendingMail = True
        self.address, self.postalCode, self.city = address, postalCode, city
        self.phone = str(phone)
        self.amounts = {  # private ?
            "paidMembershipLastYear": 0,
            "paidMembershipYear": 0,
            "paidMemberShipNextYear": 0,
            "donationsYear": 0,
            "totalYear": 0
        }
        self.rate = 18
        self.lastPayment = None
        self.lastTypePayment = None  # or use self.receipts[0]
        self.notes = None

    def updateContactData(self, address, postalCode, city, phone):
        if self.address.casefold() != address.casefold():
            self.address = address
        if self.postalCode.casefold() != postalCode.casefold():
            self.postalCode = postalCode
        if self.city.casefold() != city.casefold():
            self.city = city
        if self.phone.casefold() != phone.casefold():
            self.phone = phone

    def addPayment(self, amount, source, date, donationAfterMembership):
        self.amounts["totalYear"] += amount
        self.lastTypePayment = source
        self.lastPayment = datetime.strptime(date, "%d/%m/%Y")
        if donationAfterMembership:
            self.status = "DON-ADH"
        receipt = Receipt(self, amount, source, date)
        self.receipts.append(receipt)

    def calcAmounts(self):
        restToPay = self.rate - self.amounts["paidMembershipLastYear"]
        self.amounts["paidMembershipYear"] = min(self.amounts["totalYear"], restToPay)

        if self.lastPayment.month >= 9:  # Après septembre, RAA
            self.amounts["paidMembershipNextYear"] = min(self.amounts["totalYear"] - self.amounts["paidMembershipYear"],
                                                         self.rate)
            self.status = "RAA"

        self.amounts["donationsYear"] = self.amounts["totalYear"] - self.amounts["paidMembershipYear"] - self.amounts[
            "paidMembershipNextYear"]

    def addReceipt(self, blabla):
        self.receipts.append(Receipt(self))

    def isThisMember(self, email, name, surname):
        return (email.casefold() == self.email.casefold()) or (
                    name.casefold() == self.name.casefold() and surname.casefold() == self.surname.casefold())

    def hasValidAddress(self):
        return self.address is not None and self.postalCode is not None and self.city is not None

    def toArray(self):
        return [self.email, self.name, self.surname, ";".join([receipt.id for receipt in self.receipts]), self.status,
                self.lastMembership, self.sendingMail, self.address, self.postalCode, self.city, self.phone, 0, 0, 0, 0,
                0, self.lastPayment.strftime("%d/%m/%Y"), self.lastTypePayment, self.notes]