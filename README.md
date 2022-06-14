# Welcome to apparatus!

# Installation

ln -s /home/andreas/ags/apparatus.service /etc/systemd/system/apparatus.service


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
/eventAdmin/<eventID>/activity/<activityID>/edit

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

/qr/<tinylink>


# References

Fallback banner: http://dragdropsite.github.io/waterpipe.js/


# Tests

http://127.0.0.1:5000/qr/1
http://127.0.0.1:5000/event/1/banner.jpg
http://127.0.0.1:5000/event/2/banner.jpg
http://127.0.0.1:5000/t/abc
http://127.0.0.1:5000/event/1/view

