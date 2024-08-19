import logging


class LogManager:
    _instance = None
    _initialized = False

    LOGTYPE_INFO = "info"
    LOGTYPE_WARNING = "warning"
    LOGTYPE_ERROR = "error"

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.logs = {}
            self.logStatus = [self.LOGTYPE_INFO, self.LOGTYPE_WARNING, self.LOGTYPE_ERROR]  # PAR ORDRE D'IMPORTANCE ! (- --> +)
            self.logFunctions = {
                self.LOGTYPE_INFO: logging.info,
                self.LOGTYPE_WARNING: logging.warning,
                self.LOGTYPE_ERROR: logging.error
            }
            self.debugConsole = True
            self._initialized = True

    def addLog(self, name, logType, msg):
        logType = logType.lower()
        if name not in self.logs:
            self.logs[name] = {status: [] for status in self.logStatus}
        if logType not in self.logStatus:
            logType = self.LOGTYPE_INFO
        self.logs[name][logType].append(msg)
        if self.debugConsole:
            self._printLogInConsole(name, logType, msg)

    def getLogs(self, name, logType=None):
        if logType is not None:
            if logType in self.logs.get(name, {}):
                return self.logs[name][logType]
            else:
                return None
        else:
            return self.logs[name]

    def _printLogInConsole(self, name, logType, msg):
        logConsole = f"{name}: {msg}"

        # Appel de la fonction de logging correspondante, si elle existe
        logFunction = self.logFunctions.get(logType)
        if logFunction:
            logFunction(logConsole)

    def getLogTypeMsgsAsString(self, name, logType):
        msgs = self.getLogs(name, logType)
        return "\n\n".join(msgs)

    def getHigherStatusOf(self, name):
        logs = self.getLogs(name)
        for status in reversed(self.logStatus):
            if logs[status]:
                return status
