PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
            user_id TEXT PRIMARY KEY,
            reference_signature_path TEXT NOT NULL
        );
INSERT INTO users VALUES('8ca1c578-68af-406f-bb2f-9c4a3fb292f6','signatures_storage\8ca1c578-68af-406f-bb2f-9c4a3fb292f6_reference.png');
INSERT INTO users VALUES('51808110-dcd3-4c13-9595-2f444d7daa47','signatures_storage\51808110-dcd3-4c13-9595-2f444d7daa47_reference.png');
INSERT INTO users VALUES('8a22a5b3-2e46-44a7-8fa5-d33e2127d504','signatures_storage\8a22a5b3-2e46-44a7-8fa5-d33e2127d504_reference.png');
INSERT INTO users VALUES('46181206-c7e2-4a53-a6b4-6362bf3a16c4','signatures_storage\46181206-c7e2-4a53-a6b4-6362bf3a16c4_reference.png');
COMMIT;
