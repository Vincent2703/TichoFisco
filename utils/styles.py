from openpyxl.styles import Border, Side, Font, Alignment

widthCols = [25, 15, 15, 10, 5, 8, 8, 8, 25, 8, 25, 10, 8, 8, 8, 8, 8, 10, 10, 20]
fontHeader = Font(b=True, size=8)
sideHeader = Side(border_style="thin", color="000000")
borderHeader = Border(
    left=sideHeader, right=sideHeader, top=sideHeader, bottom=sideHeader
)

sideBody = Side(border_style="thin", color="808080")
borderBody = Border(
    left=sideBody, right=sideBody, top=sideBody, bottom=sideBody
)