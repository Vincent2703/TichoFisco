import re

from utils.LogManager import LogManager


class Payment:
    def __init__(self, email, lastName, firstName, date, regular, address, postalCode, city, phone, amount, source, refPayment):
        self.isValid = True
        self.notValidCause = None

        emailRegex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if re.match(emailRegex, email):
            self.email = email
        else:
            self.setNoValid(f"Mail incorrect : '{email}'")

        self.lastName = lastName.upper().replace("'", "`")
        self.firstName = firstName[0].upper().replace("'", "`") + firstName[1:].lower().replace("'", "`")

        dateRegex = r'^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/(\d{4})$'
        if re.match(dateRegex, date):
            self.date = date
            self.year = int(date[6:10])
        else:
            self.setNoValid(f"Date incorrect : '{date}'")

        self.regular = regular is True

        if address != '':
            self.address = str(address)
        else:
            self.setNoValid(f"Adresse incorrect : '{address}'")

        postalCodeRegex = r"^\d{5}$"
        if re.match(postalCodeRegex, postalCode):
            self.postalCode = postalCode
        else:
            self.setNoValid(f"Code postal incorrect : '{postalCode}'")

        if city != '':
            self.city = str(city)
        else:
            self.setNoValid(f"Ville incorrecte : '{city}'")

        if phone != '':
            phone = str(phone).replace(' ', '').replace("'", '')

            # Vérifie si le numéro commence par "33" et a 11 chiffres → Remplace par "0"
            if phone[0] == "+":
                phone = '0'+phone[3:]

            if len(phone) == 10 and phone.startswith("0"):
                self.phone = phone
            elif len(phone) == 9:
                self.phone = "0" + phone
            else:
                self.phone = ""  # Numéro invalide
                LogManager().addLog("update", LogManager.LOGTYPE_WARNING, f"Numéro de téléphone incorrect : '{phone}'")
        else:
            self.phone = ''

        amount = float(amount)
        if float(amount) > 0:
            self.amount = amount
        else:
            self.setNoValid(f"Montant du don incorrect : '{amount}€'")

        self.source = str(source)

        if refPayment is not None:
            self.refPayment = str(refPayment)
        else:
            self.setNoValid(f"Référence du paiement inexistante : '{refPayment}'")

    def setNoValid(self, cause):
        self.isValid = False
        self.notValidCause = cause

