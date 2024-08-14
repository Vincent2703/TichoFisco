from utils.FileManager import importMembers
from utils.PathManager import PathManager


class Receipts:
    def __init__(self):
        self.paths = PathManager().getPaths()

        self.members = {}
        self._refreshMembersList()

    def _refreshMembersList(self):
        self.members = importMembers()

    def getKVMembersCbx(self):
        dictMembers = {}
        members = dict(sorted(self.members.items(), key=lambda item: item[1]["name"]))
        for email, member in members.items():
            dictMembers[email] = f"{member['name']} {member['surname']}"

        return dictMembers
