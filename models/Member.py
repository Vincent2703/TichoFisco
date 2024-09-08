from datetime import datetime

from models.Receipt import Receipt
from models.Save import Save


class Member:
    def __init__(self, email, lastName, firstName, address, postalCode, city, phone):
        self.email = email
        self.lastName = lastName
        self.firstName = firstName

        self.receipts = []  # Seulement pour les paiements ponctuels
        self.regularPaymentsReceipt = None
        self.status = None
        self.lastMembership = None
        self.regular = None
        self.sendingMail = True
        self.address, self.postalCode, self.city = address, postalCode, city
        self.phone = str(phone)
        self.amounts = {  # private ?
            "paidMembershipLastYear": 0,
            "paidMembershipYear": 0,
            "paidMembershipNextYear": 0,
            "donationsYear": 0,
            "totalYear": 0
        }
        self.rate = Save().defaultRate["value"]
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

    def addPayment(self, payment):
        paymentAmount = float(payment.amount)

        self.amounts["totalYear"] += paymentAmount
        self.lastTypePayment = payment.source
        self.lastPayment = datetime.strptime(payment.date, "%d/%m/%Y")

        regularPayment = payment.regular
        if self.regular is None:
            self.regular = bool(regularPayment)
        elif regularPayment != self.regular:
            self.regular = "P&R"

        if self.status is None:
            self.status = "NA"
        elif self.status == "NA":
            self.status = "DON-ADH"

        if regularPayment:
            if self.regularPaymentsReceipt is None:
                self.regularPaymentsReceipt = Receipt(self, paymentAmount, payment.source, payment.date,
                                                      payment.refPayment, True)
            else:
                minimalAmountForReceipt = Save().settings["receipts"]["minimalAmount"]

                totalAmount = self.regularPaymentsReceipt.amount + paymentAmount
                self.regularPaymentsReceipt.amount = totalAmount
                self.regularPaymentsReceipt.canBeExported = totalAmount >= minimalAmountForReceipt
                self.regularPaymentsReceipt.source = payment.source
                self.regularPaymentsReceipt.date = payment.date
                print(payment.refPayment, payment.date)
                self.regularPaymentsReceipt.refPayment = payment.refPayment  # Utile ?
        else:
            receipt = Receipt(self, paymentAmount, payment.source, payment.date, payment.refPayment, False)
            if receipt.canBeExported:
                self.receipts.append(receipt)

    def isThisMember(self, email, lastName, firstName):
        return (email.casefold() == self.email.casefold()) or (lastName.casefold() == self.lastName.casefold() and firstName.casefold() == self.firstName.casefold())

    def hasValidAddress(self):
        return self.address is not None and self.postalCode is not None and self.city is not None

    def toArray(self):
        receipts = self.receipts
        if self.regularPaymentsReceipt is not None and self.regularPaymentsReceipt.amount >= 15:
            receipts.append(self.regularPaymentsReceipt)
        receiptsId = ";".join([receipt.id for receipt in receipts])

        return [self.email, self.lastName, self.firstName, receiptsId, self.status,
                self.lastMembership, self.regular, self.sendingMail, self.address, self.postalCode, self.city,
                self.phone,
                self.amounts["paidMembershipLastYear"], self.amounts["paidMembershipYear"],
                self.amounts["paidMembershipNextYear"], self.amounts["donationsYear"], self.amounts["totalYear"],
                self.lastPayment.strftime("%d/%m/%Y"), self.lastTypePayment, self.rate, self.notes]
