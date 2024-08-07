import hashlib
import json
import logging
import os.path
from datetime import datetime
from pypdf import PdfReader, PdfWriter, generic

from utils.loadSave import save


def receiptsToPDFs(receipts):
    now = datetime.now()
    currentYear = str(now.year)
    currentMonth = str(now.month)

    reader = PdfReader("assets/templateReceiptTicho2.pdf")
    writer = PdfWriter(clone_from=reader)
    writerItems = writer.get_fields().items()

    for k, v in writerItems:  # readonly
        o = v.indirect_reference.get_object()
        if o["/FT"] != "/Sig":
            o[generic.NameObject("/Ff")] = generic.NumberObject(o.get("/Ff", 0) | 1)

    for receipt in receipts:
        receiptData = receipt.toDict()
        directory = os.path.join("donnees", "recusFiscaux", currentYear, currentMonth)
        filepath = os.path.join(directory, f"{receipt.id}.pdf")

        # Vérifier si le reçu existe déjà et qu'il est identique. Doit également vérifier s'il existe bien dans le répertoire.
        receiptData = receipt.toDict()
        receiptDataStr = json.dumps(receiptData, sort_keys=True, default=str)
        newHash = hashlib.md5(receiptDataStr.encode("utf-8")).hexdigest()
        savedHash = None
        if os.path.isfile(filepath): #TODO : vérifier pertinence
            savedHash = save.getHashReceipt(receipt.id)

        if savedHash != newHash:
            writer.update_page_form_field_values(
                writer.pages[0],
                receiptData,
                auto_regenerate=False
            )

            with open(filepath, "wb") as output_stream:
                writer.write(output_stream)
                logging.info(f"Création du reçu '{receipt.id}'.")
