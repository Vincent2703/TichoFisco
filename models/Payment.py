import logging
import re


class Payment:
    def __init__(self, email, name, surname, date, regular, address, postalCode, city, phone, amount, source,
                 refPayment):
        self.isValid = True
        self.notValidCause = None

        emailRegex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if re.match(emailRegex, email):
            self.email = email
        else:
            self.setNoValid(f"Mail incorrect : '{email}'")

        self.name = name.upper()
        self.surname = surname[0].upper() + surname[1:].lower()

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

        phone = str(phone)
        if len(phone) == 10 and phone[0] == 0:
            self.phone = phone
        elif len(phone) == 9:
            self.phone = '0' + phone
        else:
            self.phone = ''
            if phone != '':
                logging.warning(f"Numéro de téléphone incorrect : '{phone}'")

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

