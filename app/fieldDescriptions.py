from flask_babel import _, gettext


def get_field_description(field_name: str) -> str:
    if field_name == "userID":
        return _("Internal ID of a user")
    elif field_name == "firstName":
        return _("First name")
    else:
        return field_name
