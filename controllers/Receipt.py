from hashlib import md5
from json import dumps
import logging
from datetime import datetime
from os import path
from pathlib import Path

from pypdf import PdfReader, PdfWriter, generic

from utils.loadSave import save


def receiptsToPDFs(receipts):
    reader = PdfReader("assets/templateReceiptTicho.pdf")
    writer = PdfWriter(clone_from=reader)
    writer.set_need_appearances_writer(True)

    writerItems = writer.get_fields().items()

    for k, v in writerItems:  # readonly

        o = v.indirect_reference.get_object()
        if o["/FT"] != "/Sig":
            o[generic.NameObject("/Ff")] = generic.NumberObject(o.get("/Ff", 0) | 1)

    for receipt in receipts:
        receiptDate = datetime.strptime(receipt.date, "%d/%m/%Y")
        year, month = str(receiptDate.year), str(receiptDate.month)
        directory = path.join("donnees", "recusFiscaux", year, month)
        if not path.isdir(directory):
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                logging.info(f"Dossier créé ou déjà existant : {directory}")
            except OSError as error:
                logging.error(f"Impossible de créer le dossier {directory} : {error}")
        filepath = path.join(directory, f"{receipt.id}.pdf")

        # Vérifier si le reçu existe déjà et qu'il est identique. Doit également vérifier s'il existe bien dans le répertoire.
        receiptData = receipt.toDict()
        receiptDataStr = dumps(receiptData, sort_keys=True, default=str)  # JSON
        newHash = md5(receiptDataStr.encode("utf-8")).hexdigest()
        savedHash = None
        if path.isfile(filepath):
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
