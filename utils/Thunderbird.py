import base64
import math
import os.path
import platform
import re
import sqlite3
import subprocess
import time
import uuid
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path

import pytz as pytz

from utils.LogManager import LogManager


class Thunderbird:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Thunderbird, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.system = platform.system()

            self.pathSoftware = Path("G:/Program Files/Thunderbird/")
            self.pathExeSoftware = self.pathSoftware / "thunderbird.exe"
            self.profilePath = Path("C:/Users/Vincent/AppData/Roaming/Thunderbird/Profiles/yds0o9pz.default-esr")
            self.userJSPath = self.profilePath / "user.js"
            self.LocalFoldersPath = self.profilePath / "Mail/Local Folders"

            self.fromEmail = "vincent.bourdon41@gmail.com"
            self.emailDomain = self.fromEmail.split('@', 1)[1]
            self.serviceName = self.emailDomain.split('.', 1)[0].capitalize()

            unsentFolderName = "Unsent Messages"
            self.unsentFolderPath = self.LocalFoldersPath / unsentFolderName

            self.tags = {
                "toSend": {"name": "recuaenvoyer", "text": "Reçu à envoyer", "color": "#e9fc17"},
                #"sent": {"name": "recuenvoye", "text": "Reçu envoyé", "color": "#fca017"},
                #"inTrash": {}
            }

            self._createLocalFolder()
            self._addCustomLabels()

            self.contactListName = "Adhérents"
            self.DBConnection = self._getConnectionToHistoryDB(self.profilePath / "history.sqlite")
            self.cursor = self.DBConnection.cursor()

            self.contactListUID = self._createContactList(self.contactListName)  # Crée la liste de contacts si besoin et récupère l'UID
            self.contacts = self._getContactsFromList(self.contactListUID)

            self.DBConnection.close()

    def _getConnectionToHistoryDB(self, path):
        try:
            return sqlite3.connect(path)
        except Exception as e:
            LogManager().addLog("Thunderbird", LogManager.LOGTYPE_ERROR, f"Impossible de se connection à la BDD history de Thunderbird : {e}")

    def _createContactList(self, name):
        contactList = self.cursor.execute(f"SELECT uid, name FROM lists WHERE name='{name}' LIMIT 1;")
        getContactListUID = next(contactList, [False])[0]
        if not getContactListUID:
            uid = uuid.uuid4()
            self.cursor.execute(f"INSERT INTO lists (uid, name, description) VALUES('{uid}', '{name}', 'Liste des adhérents du Tichodrome')")  # todo try
            self.DBConnection.commit()
            LogManager().addLog("Thunderbird", LogManager.LOGTYPE_INFO, "Création de la liste de contacts")
            if self.isRunning():
                self._terminate()
            return uid
        return getContactListUID

    def _getContactsFromList(self, contactListUID):
        # Crée un dictionnaire pour stocker les contacts
        contacts = {}

        # Créé un dictionnaire pour stocker toutes les propriétés des contacts
        contactsProperties = {}

        # Combiner les requêtes SQL pour récupérer les propriétés directement
        query = f"""
            SELECT p.card, p.name, p.value 
            FROM list_cards lc
            JOIN properties p ON lc.card = p.card
            WHERE lc.list = '{contactListUID}';
        """

        # Parcourir les résultats et structurer les données dans le dictionnaire "contactsProperties"
        for card, name, value in self.cursor.execute(query):
            if card not in contactsProperties:
                contactsProperties[card] = {}
            contactsProperties[card][name] = value

        # Réorganiser le dictionnaire en utilisant l'email comme clé principale
        for contact in contactsProperties.values():
            contacts[contact["PrimaryEmail"]] = {"firstName": contact.get("FirstName"),
                                                 "lastName": contact.get("LastName")}

        return contacts

    def _addContactToList(self, email, firstName, lastName):
        if email not in self.contacts:
            uid = uuid.uuid4()
            contactProperties = {
                "PopularityIndex": '0',
                "LastModifiedDate": math.floor(time.time()),
                "_vCard": f"BEGIN:VCARD\r\nVERSION:4.0\r\nN:{lastName};{firstName};;;\r\nFN:{firstName} {lastName}\r\nEMAIL;PREF=1:{email}\r\nUID:{uid}\r\nEND:VCARD\r\n",
                "DisplayName": f"{firstName} {lastName}",
                "FirstName": firstName,
                "LastName": lastName,
                "PrimaryEmail": email
            }

            values = ",\n\t\t".join(
                [f"('{uid}', '{key}', '{value}')" for key, value in contactProperties.items()]
            )
            queryProperties = f"INSERT INTO properties (card, name, value)\n\tVALUES\n\t\t{values};"

            self.cursor.execute(queryProperties)

            queryListCards = f"INSERT INTO list_cards(list, card) VALUES('{self.contactListUID}', '{uid}')"
            self.cursor.execute(queryListCards)

            self.DBConnection.commit()
            self.contacts[email] = {"firstName": firstName, "lastName": lastName}
            LogManager().addLog("Thunderbird", LogManager.LOGTYPE_INFO, f"{email} ajouté avec succès à la liste de contacts")

    def addContactsToList(self, contacts):
        self.DBConnection = self._getConnectionToHistoryDB(self.profilePath / "history.sqlite")
        self.cursor = self.DBConnection.cursor()
        for email, contactNames in contacts.items():
            self._addContactToList(email, contactNames["firstName"], contactNames["lastName"])
        self.DBConnection.close()

    def _createLocalFolder(self):
        if os.path.isdir(self.LocalFoldersPath):
            if not os.path.isfile(self.unsentFolderPath):
                open(self.unsentFolderPath, 'x')
            if not os.path.isfile(self.unsentFolderPath.with_suffix(".msf")):
                open(self.unsentFolderPath.with_suffix(".msf"), 'x')

    def _addCustomLabels(self):
        with open(self.userJSPath, "a+", encoding="utf-8") as file:
            for key, tag in self.tags.items():
                foundColor, foundTag = False, False
                colorLine = f"""user_pref("mailnews.tags.{tag["name"]}.color", "{tag["color"]}");"""
                tagLine = f"""user_pref("mailnews.tags.{tag["name"]}.tag", "{tag["text"]}");"""
                for line in file:
                    if line == colorLine:
                        foundColor = True
                    if line == tagLine:
                        foundTag = True

                if not foundColor or not foundTag:
                    file.seek(0)
                    file.truncate()
                    file.write(colorLine + tagLine)
            file.close()

    def addMail(self, subject='', to=None, message='', filePath=None):
        timezone = pytz.timezone("Europe/Paris")
        date = format_datetime(datetime.now(timezone))
        messageID = f"<{uuid.uuid4()}@{self.emailDomain}>"

        fileName = (Path(filePath)).name
        with open(filePath, "rb") as pdfFile:
            fileB64 = base64.b64encode(pdfFile.read()).decode("ascii")

        boundary = f"{uuid.uuid4().hex}"

        mimeContent = f"""From 
X-Mozilla-Status: 0800
X-Mozilla-Status2: 00010000
X-Mozilla-Keys: {self.tags["toSend"]["name"]}                                                                  
Content-Type: multipart/mixed; boundary="------------{boundary}"
Message-ID: <{messageID}@{self.emailDomain}>
Date: {date}
MIME-Version: 1.0
User-Agent: Mozilla Thunderbird
Content-Language: fr
To: {to}
From: {self.fromEmail}
Subject: {subject}
X-Mozilla-Draft-Info: internal/draft; vcard=0; receipt=0; DSN=0; uuencode=0;
 attachmentreminder=0; deliveryformat=0
X-Identity-Key: id1

This is a multi-part message in MIME format.
--------------{boundary}
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: 7bit

<!DOCTYPE html>
<html>
  <head>

    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
  </head>
  <body>
    {message}
  </body>
</html>
--------------{boundary}
Content-Type: application/pdf; name="{fileName}"
Content-Disposition: attachment; filename="{fileName}"
Content-Transfer-Encoding: base64

{fileB64}

--------------{boundary}--
"""

        with open(self.unsentFolderPath, "ab") as f:
            f.write(bytes(mimeContent, encoding="utf8"))

    def isRunning(self):
        try:
            if self.system == "Windows":
                output = subprocess.check_output("tasklist", shell=True, text=True)
                return "thunderbird.exe" in output
            elif self.system == "Linux":
                output = subprocess.check_output("pgrep thunderbird", shell=True, text=True)
                return bool(output.strip())
        except subprocess.CalledProcessError:
            LogManager().addLog("OS", LogManager.LOGTYPE_ERROR,
                                "Impossible de déterminer si Thunderbird est en cours d'exécution")
            return False

    def _terminate(self):
        subprocessCmd = ''
        if self.system == "Windows":
            subprocessCmd = "taskkill /f /im thunderbird.exe"
        elif self.system == "Linux":
            subprocessCmd = "pkill thunderbird"

        try:
            subprocess.run(subprocessCmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            LogManager().addLog("OS", LogManager.LOGTYPE_ERROR, "Impossible d'arrêter Thunderbird")
            pass

    def _start(self):
        subprocessCmd = ''
        if self.system == "Windows":
            subprocessCmd = self.pathExeSoftware
        elif self.system == "Linux":
            subprocessCmd = ["thunderbird"]

        try:
            subprocess.Popen(subprocessCmd)
        except OSError as e:
            LogManager().addLog("OS", LogManager.LOGTYPE_ERROR, f"Impossible de démarrer Thunderbird : {e}")

    def reloadThunderbird(self):
        if self.isRunning():
            self._terminate()
            time.sleep(1.5)  # Pour s'assurer que Thunderbird est bien fermé
            self._start()
        return True

    def getStatusEmails(self):  # Status : -1 inconnu (0 pas trouvé) 1 préparé 2 envoyé 3 supprimé
        regexReceiptID = 'filename="(.+)\.pdf"'
        regexMozStatus1 = 'X-Mozilla-Status: ([0-9]+)'
        regexMozStatus2 = 'X-Mozilla-Status2: ([0-9]+)'
        if os.path.isfile(self.unsentFolderPath):
            with open(self.unsentFolderPath, 'r') as file:
                receiptsInThunderbird = {}

                fileContent = file.read()
                emailsContent = fileContent.split("--\nFrom")

                for emailContent in emailsContent:
                    search = re.search(regexReceiptID, emailContent, re.IGNORECASE)
                    if search:
                        receiptID = search.group(1)
                        mozStatus1, mozStatus2 = None, None

                        search = re.search(regexMozStatus1, emailContent, re.IGNORECASE)
                        if search:
                            mozStatus1 = search.group(1)

                        search = re.search(regexMozStatus2, emailContent, re.IGNORECASE)
                        if search:
                            mozStatus2 = search.group(1)

                        status = -1
                        if (mozStatus1 == "0800" and mozStatus2 == "00010000") or (mozStatus1 == "0801" and mozStatus2 == "10000000"):
                            status = 1
                        elif mozStatus1 == "0808" and mozStatus2 == "10010000":
                            status = 2
                        elif mozStatus1 == "0809" and mozStatus2 == "10000000":
                            status = 3

                        receiptsInThunderbird[receiptID] = status

        return receiptsInThunderbird
