BEGIN TRANSACTION;
DROP TABLE IF EXISTS "election";
CREATE TABLE IF NOT EXISTS "election" (
	"electionID"	TEXT NOT NULL,
	"description"	TEXT,
	"creatorName"	TEXT,
	"creatorMail"	TEXT,
	"creatorMailVerificationToken"	TEXT,
	"deadline"	TEXT,
	"mode"	INTEGER,
	PRIMARY KEY("electionID")
);
DROP TABLE IF EXISTS "election_options";
CREATE TABLE IF NOT EXISTS "election_options" (
	"optionID"	TEXT NOT NULL,
	"electionID"	TEXT NOT NULL,
	"name"	TEXT,
	"rank"	INTEGER,
	PRIMARY KEY("optionID")
);
DROP TABLE IF EXISTS "election_vote";
CREATE TABLE IF NOT EXISTS "election_vote" (
	"voteID"	INTEGER NOT NULL,
	"optionID"	TEXT,
	"name"	TEXT,
	PRIMARY KEY("voteID")
);
INSERT INTO "election" ("electionID","description","creatorName","creatorMail","creatorMailVerificationToken","deadline","mode") VALUES ('5a546805-49a4-44f7-b5ad-17ce60aa4b96','Klassenfest der Gryffindors 3. Stufe','Andreas','andreas@drosselweg7a.de','364ef4d6-608c-4c74-8520-3dda64522d29','123',0);
INSERT INTO "election_options" ("optionID","electionID","name","rank") VALUES ('ef869ddb-64ee-4624-81b9-a29468f691da','5a546805-49a4-44f7-b5ad-17ce60aa4b96','Di. 15.4.2022',1);
INSERT INTO "election_options" ("optionID","electionID","name","rank") VALUES ('5402b3f8-6f74-4678-9b58-8d7e748528d2','5a546805-49a4-44f7-b5ad-17ce60aa4b96','Mi. 16.4.2022',2);
INSERT INTO "election_options" ("optionID","electionID","name","rank") VALUES ('c6370bf1-d135-4619-abce-bf61f1b5d45e','5a546805-49a4-44f7-b5ad-17ce60aa4b96','Do. 17.4.2022',3);
INSERT INTO "election_vote" ("voteID","optionID","name") VALUES (1,'ef869ddb-64ee-4624-81b9-a29468f691da','Harry');
INSERT INTO "election_vote" ("voteID","optionID","name") VALUES (2,'5402b3f8-6f74-4678-9b58-8d7e748528d2','Harry');
INSERT INTO "election_vote" ("voteID","optionID","name") VALUES (3,'ef869ddb-64ee-4624-81b9-a29468f691da','Ron');
COMMIT;
