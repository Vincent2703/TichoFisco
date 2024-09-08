import os
import pathlib
import platform
from glob import glob
from os.path import isfile, isdir

import orjson

from utils.LogManager import LogManager
from utils.PathManager import PathManager
from utils.misc import saveHiddenFile, getEpoch


class Save:  # todo : A renommer en Cache
    _instance = None  # Instance unique (singleton)
    _initialized = False  # Indique si l'objet a été initialisé

    def __new__(cls, *args, **kwargs):
        # Crée une nouvelle instance si elle n'existe pas encore
        if cls._instance is None:
            cls._instance = super(Save, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Initialisation de l'instance, si elle n'a pas encore été faite
        if not self._initialized:
            self.saveFilePath = PathManager().getPaths()["save"]  # Chemin du fichier de sauvegarde

            # Tableau contenant les identifiants des reçus
            self.idReceipts = []

            # Dictionnaires pour stocker les informations des membres
            self.members = {}
            self.exportedMembers = {}  # Dictionnaire des membres à exporter
            self.settings = {}  # Paramètres de l'application
            self.lastUpdate = None  # Dernière mise à jour

            # Si le fichier de sauvegarde existe, le charger, sinon créer des paramètres par défaut
            if os.path.isfile(self.saveFilePath):
                self.load()
            else:
                self.settings = self._getDefaultSettings()
                self.save()

            self.defaultRate = self._getDefaultRate()  # Taux par défaut

            self._initialized = True

    def _getDefaultSettings(self):
        """
        Génère les paramètres par défaut pour l'application.

        Retourne :
        dict : Paramètres par défaut, incluant le chemin Thunderbird, les reçus, etc.
        """
        def getThunderbirdProfilePath():
            # Récupère le chemin du profil Thunderbird sous Windows
            if platform.system() == "Windows":
                dirProfiles = glob(os.path.join(os.getenv("APPDATA"), "Thunderbird", "Profiles", '*'))
                for dirProfile in dirProfiles:
                    if isdir(os.path.join(dirProfile, "Mail/Local Folders")):
                        return os.path.normpath(dirProfile)
            return ''

        thunderbirdProfilePath = getThunderbirdProfilePath()

        # Définition des paramètres par défaut
        defaultSettings = {
            "thunderbird": {
                "path": '',
                "profilePath": thunderbirdProfilePath,
                "contactsList": "Adhérents",
                "fromEmail": '',
                "emailSubject": "Reçu fiscal pour votre don au Tichodrome",
                "emailBody": "Bonjour,<br/>Veuillez trouver en pièce jointe le reçu fiscal de votre don au Tichodrome."
            },
            "receipts": {
                "minimalAmount": 15,  # Montant minimal pour générer un reçu
                "pdfTemplatePath": (pathlib.Path(__file__).parents[1].resolve() / "assets" / "modeleRecuTichodrome.pdf").as_posix()
            },
            "rates": [  # Liste des taux d'adhésion
                {"name": "Sans emploi", "value": 10},
                {"name": "Individuel", "value": 18, "default": True},  # Par défaut
                {"name": "Familial", "value": 25},
                {"name": "Association", "value": 30},
            ]
        }

        return defaultSettings

    def _getDefaultRate(self):
        """
        Retourne le taux par défaut défini dans les paramètres.

        Retourne :
        dict : Le taux par défaut (ex: Individuel)
        """
        return next((rate for rate in self.settings.get("rates", []) if rate.get("default")), None)

    def getRateByName(self, name):
        """
        Recherche un taux d'adhésion par son nom.

        Paramètres :
        name (str) : Le nom du taux à rechercher.

        Retourne :
        dict : Le taux correspondant, sinon None.
        """
        normalizedName = name.casefold().replace(' ', '')
        return next((rate for rate in self.settings.get("rates", [])
                     if rate["name"].casefold().replace(' ', '') == normalizedName), None)

    def load(self):
        """
        Charge les données du fichier de sauvegarde.
        """
        if isfile(self.saveFilePath) and os.stat(self.saveFilePath).st_size > 0:
            with open(self.saveFilePath, 'r', encoding="utf-8") as saveFile:
                saveContent = saveFile.read()
                saveJSON = orjson.loads(saveContent)  # TODO: Gérer les erreurs
                self.lastUpdate = saveJSON["lastUpdate"]  # Date de la dernière mise à jour
                self.members = saveJSON["members"]  # Membres chargés depuis le fichier
                self.settings = saveJSON["settings"]  # Paramètres chargés depuis le fichier

    def addMemberReceipt(self, memberEmail, receipts):
        """
        Ajoute un reçu à l'email d'un membre.

        Paramètres :
        memberEmail (str) : L'email du membre.
        receipts (list) : Liste des reçus à ajouter.
        """
        for receipt in receipts:
            hash = receipt.getHash()
            if not self._isMemberExported(memberEmail):
                self.exportedMembers[memberEmail] = {"receipts": {}}

            self.exportedMembers[memberEmail]["receipts"][receipt.id] = {
                "hash": hash,
                "regular": receipt.regular,
                "amount": receipt.amount,
                "refPayment": receipt.refPayment,  # TODO Pourrait être un tableau si régulier
                "canBeExported": receipt.canBeExported,
            }

    def _isMemberExported(self, memberEmail):
        """
        Vérifie si un membre est déjà exporté.

        Paramètres :
        memberEmail (str) : L'email du membre à vérifier.

        Retourne :
        bool : True si le membre est exporté, sinon False.
        """
        return memberEmail in self.exportedMembers

    def isMemberReceiptExported(self, memberEmail, idReceipt):
        """
        Vérifie si un reçu d'un membre a déjà été exporté.

        Paramètres :
        memberEmail (str) : L'email du membre.
        idReceipt (str) : L'identifiant du reçu.

        Retourne :
        bool : True si le reçu est exporté, sinon False.
        """
        return self._isMemberExported(memberEmail) and idReceipt in self.exportedMembers[memberEmail]["receipts"]

    def getRefPaymentReceipt(self, memberEmail, idReceipt):
        """
        Récupère la référence de paiement d'un reçu pour un membre.

        Paramètres :
        memberEmail (str) : L'email du membre.
        idReceipt (str) : L'identifiant du reçu.

        Retourne :
        str : La référence de paiement si elle existe, sinon None.
        """
        return self.exportedMembers.get(memberEmail, {}).get("receipts", {}).get(idReceipt, {}).get("refPayment")

    def updateMembersReceiptsEmailStatus(self, receipts):
        """
        Met à jour le statut d'envoi des emails pour les reçus des membres.

        Paramètre :
        receipts (list) : Liste des reçus avec le statut des emails.
        """
        if len(self.exportedMembers) == 0:
            self.exportedMembers = self.members

        for receipt in receipts:
            email = receipt["emailMember"]
            idReceipt = receipt["idReceipt"]
            emailStatus = receipt["emailStatus"]
            if self.isMemberReceiptExported(email, idReceipt):
                self.exportedMembers[email]["receipts"][idReceipt]["emailStatus"] = emailStatus
        self.save()

    def getSavedReceiptHash(self, memberEmail, idReceipt):
        """
        Récupère le hash d'un reçu sauvegardé pour un membre.

        Paramètres :
        memberEmail (str) : L'email du membre.
        idReceipt (str) : L'identifiant du reçu.

        Retourne :
        str : Le hash du reçu si existant, sinon None.
        """
        return self.members.get(memberEmail, {}).get("receipts", {}).get(idReceipt, {}).get("hash")

    def isSettingsFilled(self):
        """
        Vérifie si les paramètres obligatoires sont remplis.

        Retourne :
        bool : True si tous les paramètres obligatoires sont remplis, sinon False.
        """
        result = True
        mandatoryFields = {
            "path": {"frName": "Dossier de Thunderbird", "value": self.settings["thunderbird"]["path"]},
            "profilePath": {"frName": "Dossier du profil Thunderbird", "value": self.settings["thunderbird"]["profilePath"]},
            "email": {"frName": "Adresse mail d'envoi", "value": self.settings["thunderbird"]["fromEmail"]}
        }
        for keyName, field in mandatoryFields.items():
            if len(field["value"]) == 0:
                result = False
                LogManager().addLog("Settings", LogManager.LOGTYPE_WARNING, f"Un paramètre obligatoire ({field['frName']}) est vide.")
        return result

    def saveSettings(self, newSettings, originalSettings=None):
        """
        Sauvegarde les nouveaux paramètres.

        Paramètres :
        newSettings (dict) : Nouveaux paramètres à sauvegarder.
        originalSettings (dict, optionnel) : Paramètres actuels pour garder les valeurs non modifiées.

        Retourne :
        bool : True si la sauvegarde est réussie, sinon False.
        """
        if originalSettings is None:
            originalSettings = self.settings
        for key, value in newSettings.items():
            if isinstance(value, dict) and key in originalSettings:
                self.saveSettings(value, originalSettings[key])
            else:
                originalSettings[key] = value

        return self.save() and self.isSettingsFilled()

    def save(self, refreshDate=False):
        """
        Sauvegarde l'état actuel des membres et des paramètres dans un fichier.

        Paramètre :
        refreshDate (bool) : Indique si la date de sauvegarde doit être rafraîchie.

        Retourne :
        bool : True si la sauvegarde est réussie, sinon False.
        """
        try:
            epoch = refreshDate and getEpoch() or self.lastUpdate
            # Sauvegarde du fichier .save avec les membres et les paramètres
            jsonContent = orjson.dumps({
                "members": self.exportedMembers,
                "settings": self.settings,
                "lastUpdate": epoch
            })

            saveHiddenFile(self.saveFilePath, jsonContent, binary=True)
            self.members = self.exportedMembers
            self.lastUpdate = epoch
            return True
        except Exception as e:
            LogManager().addLog("OS", logType=LogManager.LOGTYPE_ERROR, msg=f"Erreur lors de la sauvegarde : {e}")
            return False

    def resetSettings(self):
        """
        Réinitialise les paramètres aux valeurs par défaut.

        Retourne :
        Aucun
        """
        self.settings = self._getDefaultSettings()

    def resetMembers(self):
        """
        Réinitialise les membres exportés.

        Retourne :
        Aucun
        """
        self.exportedMembers = {}

    def fullReset(self):
        """
        Réinitialise entièrement les paramètres et les membres, puis sauvegarde.

        Retourne :
        bool : True si la réinitialisation est réussie, sinon False.
        """
        try:
            self.resetSettings()
            self.resetMembers()
            self.save()
            return True
        except Exception as e:
            LogManager().addLog("OS", logType=LogManager.LOGTYPE_ERROR, msg=f"Erreur lors de la réinitialisation du cache : {e}")
            return False
