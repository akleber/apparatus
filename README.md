# Welcome to apparatus!

# Installation

ln -s /home/andreas/ags/apparatus.service /etc/systemd/system/apparatus.service


# Brainstorming

* docx export of activies https://python-docx.readthedocs.io/en/latest/

## Pages

/
* About
* Create Event

/eventAdd
/eventEdit/<eventID>
/eventAttendees/<eventID>
* xlsx export
/eventBanner/<eventID>/banner.jpg

/eventView/<tinylink>
/register/<eventID>

/activityAdd
/activityEdit/<activityID>
/activityAbout/<activityID>

/verifyMail/<mailVerificationToken>
* Thank you

/dsgvoData/<dsgvoToken>

/t/<tinylink> -> redirect
/qr/<tinylink>


# References

Fallback banner: http://dragdropsite.github.io/waterpipe.js/


# Tests

* http://127.0.0.1:5000/qr/abc123
* http://127.0.0.1:5000/eventBanner/1/banner.jpg
* http://127.0.0.1:5000/eventBanner/2/banner.jpg
* http://127.0.0.1:5000/t/abc

