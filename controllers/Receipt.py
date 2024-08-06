from datetime import datetime

from pypdf import PdfReader, PdfWriter, generic


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
        writer.update_page_form_field_values(
            writer.pages[0],
            receipt.toDict(),
            auto_regenerate=False
        )

        with open("donnees/recusFiscaux/" + currentYear + '/' + currentMonth + '/' + receipt.id + ".pdf", "wb") as output_stream:
            writer.write(output_stream)
