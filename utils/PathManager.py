import logging
from glob import glob
from pathlib import Path


class PathManager:
    def __init__(self):
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
            "PDFTemplate": self._assetsPath / "modeleRecuTichodrome.pdf",
            "memberListsPattern": glob(str(self.dirPaths["listesAdherents"] / "*.xlsx")),
            "paymentFilesPatterns": {
                "helloAsso": glob(str(self.dirPaths["paiementsHelloAsso"] / "*.xlsx")),
                "paypal": glob(str(self.dirPaths["paiementsPaypal"] / "*.xlsx")),
                "virEspChq": glob(str(self.dirPaths["paiementsVirEspChq"] / "*.xlsx")),
                "cb": glob(str(self.dirPaths["paiementsCB"] / "*.csv"))
            }
        }

        self.createDirectories()

    def createDirectories(self):
        for key, path in self.dirPaths.items():
            if not Path.is_dir(path):
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logging.info(f"Dossier créé : {path}")
                except OSError as error:
                    logging.error(f"Impossible de créer le dossier {path} : {error}")

    def getPaths(self):
        return self.dirPaths | self.dirFiles  # merge
