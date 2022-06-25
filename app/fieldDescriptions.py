def get_field_description(field_name: str) -> str:
    if field_name == "userID":
        return "Interne ID eines benutzers"
    elif field_name == "firstName":
        return "Vorname"
    else:
        return field_name
