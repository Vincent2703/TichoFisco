from glob import glob
from pathlib import Path

from utils.LogManager import LogManager


class PathManager:  # Pour les chemins internes au logiciel uniquement (Thunderbird dans Save.settings)
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PathManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._currentPath = Path.cwd()
            self._assetsPath = self._currentPath / "assets"
            self._dataPath = self._currentPath / "donnees"

            self.dirPaths = {
                "actuel": self._dataPath,
                "listesAdherents": self._dataPath / "listesAdherents",
                "paiementsHelloAsso": self._dataPath / "paiements/helloAsso",
                "paiementsPaypal": self._dataPath / "paiements/paypal",
                "paiementsVirEspChq": self._dataPath / "paiements/virEspChq",
                "paiementsCB": self._dataPath / "paiements/CB",
                "recusFiscaux": self._dataPath / "recusFiscaux"
            }

            self.dirFiles = {
                "save": self._currentPath / ".save",
                "memberListsPattern": glob(str(self.dirPaths["listesAdherents"] / "*.xlsx")),
                "paymentFilesPatterns": {
                    "helloAsso": glob(str(self.dirPaths["paiementsHelloAsso"] / "*.xlsx")),
                    "paypal": glob(str(self.dirPaths["paiementsPaypal"] / "*.xlsx")),
                    "virEspChq": glob(str(self.dirPaths["paiementsVirEspChq"] / "*.xlsx")),
                    "cb": glob(str(self.dirPaths["paiementsCB"] / "*.csv"))
                },
                "assets": {
                    "PDFTemplate": self._assetsPath / "modeleRecuTichodrome.pdf",
                    "icons": {
                        "info": self._assetsPath / "icons/info.png",
                        "warning": self._assetsPath / "icons/warning.png",
                        "error": self._assetsPath / "icons/error.png"
                    }
                }
            }

            self.createDirectories()
            self._initialized = True

    def createDirectories(self):
        for key, path in self.dirPaths.items():
            if not Path.is_dir(path):
                try:
                    path.mkdir(parents=True, exist_ok=True)

                    LogManager().addLog("OS", LogManager.LOGTYPE_INFO, f"Dossier créé : {path}")
                except OSError as error:
                    LogManager().addLog("OS", LogManager.LOGTYPE_ERROR, f"Impossible de créer le dossier {path} : {error}")

    def getPaths(self):
        return self.dirPaths | self.dirFiles  # merge
