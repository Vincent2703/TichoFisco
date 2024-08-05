from datetime import datetime


def convertFrenchDate(frenchDateStr):
    # Dictionnaire pour mapper les mois français aux mois anglais
    frenchToEnglishMonths = {
        "Janvier": "January", "Février": "February", "Mars": "March",
        "Avril": "April", "Mai": "May", "Juin": "June",
        "Juillet": "July", "Août": "August", "Septembre": "September",
        "Octobre": "October", "Novembre": "November", "Décembre": "December"
    }

    # Remplacer le mois français par le mois anglais
    for frenchMonth, englishMonth in frenchToEnglishMonths.items():
        if frenchMonth in frenchDateStr:
            englishDateStr = frenchDateStr.replace(frenchMonth, englishMonth)
            break

    # Convertir la chaîne modifiée en objet datetime
    return datetime.strptime(englishDateStr, "%B %d, %Y @ %I:%M %p")
