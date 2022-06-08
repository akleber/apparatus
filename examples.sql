BEGIN TRANSACTION;
DROP TABLE IF EXISTS "attendee";
CREATE TABLE IF NOT EXISTS "attendee" (
	"attendeeID"	INTEGER NOT NULL,
	"userID"	INTEGER NOT NULL,
	"klasse"	TEXT,
	"ganztag"	INTEGER,
	"telefonummer"	TEXT,
	"foevMitgliedsname"	TEXT,
	"beideAGs"	INTEGER,
	"primaryActivityChoice"	INTEGER,
	"secondaryActivityChoice"	INTEGER,
	PRIMARY KEY("attendeeID" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "user";
CREATE TABLE IF NOT EXISTS "user" (
	"userID"	INTEGER NOT NULL,
	"firstName"	TEXT,
	"familyName"	TEXT,
	"mail"	TEXT,
	"mailVerificationToken"	TEXT,
	"dsgvoToken"	TEXT,
	PRIMARY KEY("userID" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "event";
CREATE TABLE IF NOT EXISTS "event" (
	"eventID"	INTEGER NOT NULL,
	"tinyurl"	TEXT NOT NULL,
	"active"	INTEGER NOT NULL,
	"title"	TEXT NOT NULL,
	"description"	TEXT,
	"creator"	INTEGER NOT NULL,
	"creationDate"	TEXT NOT NULL,
	"lastChangedDate"	TEXT NOT NULL,
	"registrationDeadline"	TEXT,
	"adminToken"	TEXT NOT NULL,
	"bannerImage"	BLOB,
	PRIMARY KEY("eventID" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "activity";
CREATE TABLE IF NOT EXISTS "activity" (
	"activityID"	INTEGER NOT NULL,
	"eventID"	INTEGER NOT NULL,
	"active"	INTEGER NOT NULL,
	"title"	TEXT NOT NULL,
	"description"	TEXT,
	"seats"	INTEGER,
	"creationDate"	TEXT NOT NULL,
	"lastChangedDate"	TEXT NOT NULL,
	PRIMARY KEY("activityID" AUTOINCREMENT)
);
INSERT INTO "attendee" VALUES (1,2,'3c',1,'+491778026865','Birgit Kleber',1,1,'');
INSERT INTO "user" VALUES (1,'Andreas','Kleber','andreas@drosselweg7a.de','3876a788-0f34-4f54-90ed-43695e626c42','0e818cff-1f45-4af2-8e10-31c36cdfdfa0');
INSERT INTO "user" VALUES (2,'Jakob','Kleber','jakob.kleber@icloud.com','785042b3-0fab-486e-9e0b-9be1e25e3358','b4d09810-8f6e-495a-bd88-06ab5c62d1b1');
INSERT INTO "event" VALUES (1,'abc',1,'AG Angebot Förderverein CUS Schuljahr 2021/22','Schöne Beschreibung',1,'2022-06-06 16:51:53','2022-06-07 09:43:22','2022-08-10 12:00:00','785042b3-0fab-486e-9e0b-9be1e25e3358','');
INSERT INTO "activity" VALUES (1,1,1,'Schach AG','Die wunderbare Schach AG',8,'2022-06-06 16:51:53','2022-06-06 16:55:53');
DROP VIEW IF EXISTS "dsgvoView";
CREATE VIEW dsgvoView AS
SELECT user.firstName , user.familyName , user.mail, user.mailVerificationToken , user.dsgvoToken, 
attendee.klasse, attendee.ganztag, attendee.telefonummer, attendee.foevMitgliedsname , attendee.beideAGs,
a1.title AS title1, a2.title as title2
FROM user 
JOIN attendee ON user.userID = attendee.userID 
LEFT OUTER JOIN activity a1 ON attendee.primaryActivityChoice = a1.activityID
LEFT OUTER JOIN activity a2 ON attendee.secondaryActivityChoice = a2.activityID;
DROP VIEW IF EXISTS "eventAttendees";
CREATE VIEW "eventAttendees" AS SELECT e.title, a.title, u.firstName, u.familyName
FROM event as e
JOIN activity a ON a.eventID = e.eventID
LEFT OUTER JOIN attendee ae ON a.activityID = ae.primaryActivityChoice OR a.activityID = ae.secondaryActivityChoice
LEFT OUTER JOIN user u ON ae.userID = u.userID;
COMMIT;
