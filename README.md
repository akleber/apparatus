# Welcome to apparatus!

# Installation

ln -s /home/andreas/ags/apparatus.service /etc/systemd/system/apparatus.service

# ToDos

* eventAdmin add admin token
* Form validation
* Max two activity selection, no preferences
* eMail -> mandatory
* AGBs info text, link?


# Ideas

* Anmeldezeitraum



# Brainstorming


## Pages

/
* About
* Create Event

/eventAdd
/eventAdmin/<eventID>/edit
/eventAdmin/<eventID>/attendees/xlsx
* xlsx export

/eventAdmin/<eventID>/activity/docx
* docx export https://python-docx.readthedocs.io/en/latest/
/eventAdmin/<eventID>/activity/add
/eventAdmin/<eventID>/activity/edit/<activityID>
/eventAdmin/<eventID>/qr

/event/<eventID>/view
/event/<eventID>/register
/event/<eventID>/banner.jpg
/activityAbout/<activityID>

/verifyMail/<mailVerificationToken>
* Thank you

/gdprData/<gdprToken>

/t/<tinylink>
* redirect to eventID
* rate limit


# References

Fallback banner: http://dragdropsite.github.io/waterpipe.js/


# Tests

http://127.0.0.1:5000/qr/1
http://127.0.0.1:5000/event/1/banner.jpg
http://127.0.0.1:5000/event/2/banner.jpg
http://127.0.0.1:5000/t/abc
http://127.0.0.1:5000/event/1/view
http://127.0.0.1:5000/gdpr/b4d09810-8f6e-495a-bd88-06ab5c62d1b1


# Babel

pybabel extract -F babel.cfg -k _l -o messages.pot .
pybabel init -i messages.pot -d app/translations -l de
pybabel update -i messages.pot -d app/translations
pybabel compile -d app/translations