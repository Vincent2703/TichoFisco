import base64
import os.path
import uuid
from datetime import datetime
from email.header import Header
from email.utils import format_datetime
from pathlib import Path
import quopri


import pytz as pytz


class Thunderbird:
    def __init__(self):
        self.pathSoftware = "G:/Program Files/Thunderbird/"
        self.pathLocalFolders = Path("C:/Users/Vincent/AppData/Roaming/Thunderbird/Profiles/yds0o9pz.default-esr/Mail/Local Folders")

        self.fromEmail = "vincent.bourdon41@gmail.com"
        self.emailDomain = self.fromEmail.split('@', 1)[1]
        self.serviceName = self.emailDomain.split('.', 1)[0].capitalize()

        fccClear = f"imap://{self.fromEmail}@imap.{self.emailDomain}/[{self.serviceName}]/Messages envoyés"
        self.fcc = quopri.encodestring(fccClear.encode("utf-8")) #TODO fix !

        self._createLocalFolder()

    def _createLocalFolder(self):
        if os.path.isdir(self.pathLocalFolders):
            if not os.path.isfile(self.pathLocalFolders / "reçus à envoyer"):
                open(self.pathLocalFolders / "reçus à envoyer", 'x')
            if not os.path.isfile(self.pathLocalFolders / "reçus à envoyer.msf"):
                open(self.pathLocalFolders / "reçus à envoyer.msf", 'x')

    def addMail(self, subject='', to=None, message='', filePath=None):
        timezone = pytz.timezone("Europe/Paris")
        date = format_datetime(datetime.now(timezone))
        messageID = f"<{uuid.uuid4()}@{self.emailDomain}>"

        fileName = (Path(filePath)).name
        pdf_name = os.path.basename(filePath)
        with open(filePath, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read()).decode("ascii")

        boundary = f"{uuid.uuid4().hex}"

        mimeContent = f"""From 
X-Mozilla-Status: 0000
X-Mozilla-Status2: 00000000
X-Mozilla-Keys:                                                                                 
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
Fcc: {self.fcc}

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

{encoded_string}

--------------{boundary}--
"""

        with open(self.pathLocalFolders / "reçus à envoyer", "ab") as f:
            f.write(bytes(mimeContent, encoding="utf8"))



    """def addMail(self, subject='', to=None, message='', filePath=None):
        timezone = pytz.timezone("Europe/Paris")
        date = format_datetime(datetime.now(timezone))
        messageID = f'<{uuid.uuid4()}@{self.emailDomain}>'

        email = EmailMessage()
        email["From"] = self.fromEmail
        email["To"] = to
        email["Subject"] = subject + str(uuid.uuid4())
        email["Date"] = date
        email["Message-ID"] = messageID

        email.set_content(message)
        email.add_alternative(f\
            <!DOCTYPE html>
            <html>
              <body>
                <p>{message}<br>
                </p>
              </body>
            </html>
            , subtype="html")

        if filePath is not None:
            with open(filePath, "rb") as pdf:
                pdf_data = pdf.read()
                pdf_name = os.path.basename(filePath)
                email.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=pdf_name)

        with open(self.pathLocalFolders / "reçus à envoyer", "wb") as f:
            f.write(bytes(email))"""
            #f.write(b'\n\n')  # Séparateur entre les emails


