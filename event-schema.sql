BEGIN TRANSACTION;
DROP TABLE IF EXISTS "attendee";
CREATE TABLE IF NOT EXISTS "attendee" (
	"attendeeID"	TEXT NOT NULL,
	"userID"	INTEGER NOT NULL,
	"klasse"	TEXT,
	"ganztag"	INTEGER,
	"geschlecht"	INTEGER,
	"telefonnummer"	TEXT,
	"foevMitgliedsname"	TEXT,
	"beideAGs"	INTEGER,
	"primaryActivityChoice"	INTEGER,
	"secondaryActivityChoice"	INTEGER,
	PRIMARY KEY("attendeeID")
);
DROP TABLE IF EXISTS "user";
CREATE TABLE IF NOT EXISTS "user" (
	"userID"	INTEGER NOT NULL,
	"firstName"	TEXT,
	"familyName"	TEXT,
	"mail"	TEXT,
	"mailVerificationToken"	TEXT,
	"gdprToken"	TEXT,
	PRIMARY KEY("userID" AUTOINCREMENT)
);
DROP TABLE IF EXISTS "event";
CREATE TABLE IF NOT EXISTS "event" (
	"eventID"	TEXT NOT NULL,
	"tinylink"	TEXT NOT NULL,
	"active"	INTEGER NOT NULL,
	"title"	TEXT NOT NULL,
	"description"	TEXT,
	"legal"	TEXT,
	"creator"	INTEGER NOT NULL,
	"creationDate"	TEXT NOT NULL,
	"lastChangedDate"	TEXT NOT NULL,
	"registrationDeadline"	TEXT,
	"adminToken"	TEXT NOT NULL,
	"bannerImage"	BLOB,
	PRIMARY KEY("eventID")
);
DROP TABLE IF EXISTS "activity";
CREATE TABLE IF NOT EXISTS "activity" (
	"activityID"	TEXT NOT NULL,
	"eventID"	TEXT NOT NULL,
	"active"	INTEGER NOT NULL,
	"title"	TEXT NOT NULL,
	"description"	TEXT,
	"seats"	INTEGER,
	"creationDate"	TEXT NOT NULL,
	"lastChangedDate"	TEXT NOT NULL,
	PRIMARY KEY("activityID")
);
DROP TABLE IF EXISTS "stats";
CREATE TABLE IF NOT EXISTS "stats" (
	"timestamp"	TEXT,
	"event"	TEXT
);
DROP VIEW IF EXISTS "eventAttendees";
CREATE VIEW "eventAttendees" AS SELECT e.eventID, u.firstName, u.familyName, u.mail, u.mailVerificationToken,at.klasse,group_concat(a.title, "|") as AGs,at.attendeeID
FROM event as e
INNER JOIN activity a ON a.eventID = e.eventID
INNER JOIN attendee at ON a.activityID = at.primaryActivityChoice OR a.activityID = at.secondaryActivityChoice
INNER JOIN user u ON at.userID = u.userID
GROUP BY u.userID;
DROP VIEW IF EXISTS "eventAttendeesXlsx";
CREATE VIEW "eventAttendeesXlsx" AS SELECT e.eventID, u.firstName, u.familyName, u.mail, u.mailVerificationToken,at.klasse,at.geschlecht,at.ganztag,at.telefonnummer,at.foevMitgliedsname,at.beideAGs,a.title as AG
FROM event as e
INNER JOIN activity a ON a.eventID = e.eventID
INNER JOIN attendee at ON a.activityID = at.primaryActivityChoice OR a.activityID = at.secondaryActivityChoice
INNER JOIN user u ON at.userID = u.userID;
DROP VIEW IF EXISTS "gdprView";
CREATE VIEW gdprView AS
SELECT user.firstName , user.familyName , user.mail, user.mailVerificationToken , user.gdprToken, 
attendee.klasse, attendee.geschlecht, attendee.ganztag, attendee.telefonnummer, attendee.foevMitgliedsname , attendee.beideAGs,
a1.title AS title1, a2.title as title2
FROM user 
JOIN attendee ON user.userID = attendee.userID 
LEFT OUTER JOIN activity a1 ON attendee.primaryActivityChoice = a1.activityID
LEFT OUTER JOIN activity a2 ON attendee.secondaryActivityChoice = a2.activityID;
COMMIT;
