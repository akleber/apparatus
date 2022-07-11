def get_field_description(field_name: str) -> str:
    if field_name == "userID":
        return "Interne ID eines Benutzers"
    elif field_name == "firstName":
        return "Vorname"
    elif field_name == "familyName":
        return "Nachname"
    elif field_name == "mail":
        return "E-Mail Adresse"
    elif field_name == "mailVerificationToken":
        return "Token zum verifizieren der E-Mail Adresse"
    elif field_name == "gdprToken":
        return "Token zum Erzeugen dieser Übersicht"
    elif field_name == "klasse":
        return "Klasse"
    elif field_name == "ganztag":
        return "Ganztag"
    elif field_name == "telefonnummer":
        return "Telefonnummer"
    elif field_name == "foevMitgliedsname":
        return "Name des Fördervereinmitglieds"
    elif field_name == "beideAGs":
        return "Wunsch an beiden AGs teilzunehmen"
    elif field_name == "title1":
        return "AG 1"
    elif field_name == "title2":
        return "AG 2"
    else:
        return field_name
