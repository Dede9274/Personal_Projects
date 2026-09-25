-- Run this with the sqlite3 CLI against a backup of a legacy SQLite database.
-- The legacy users.id and appointment.id columns are expected to be primary keys.
-- SQLite requires the appointment table to be rebuilt to add its foreign key.

PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username
    ON users (username);

ALTER TABLE appointment RENAME TO appointment_legacy;

CREATE TABLE appointment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    phoneNr TEXT NOT NULL,
    IdNr TEXT NOT NULL,
    description TEXT NOT NULL,
    date DATE NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);

INSERT INTO appointment (
    id, user_id, firstname, lastname, phoneNr, IdNr, description, date, time
)
SELECT
    id, NULL, firstname, lastname, phoneNr, IdNr, description, date, time
FROM appointment_legacy;

DROP TABLE appointment_legacy;

CREATE INDEX idx_appointment_user_date
    ON appointment (user_id, date, time);

COMMIT;
PRAGMA foreign_keys = ON;

-- Legacy appointments have no trustworthy owner and remain invisible in
-- My Appointments until an administrator verifies and assigns each user_id:
--
-- UPDATE appointment SET user_id = <verified_user_id> WHERE id = <appointment_id>;
--
-- SQLite cannot add a NOT NULL constraint in place. Leaving user_id nullable is
-- safe here because the application always supplies it for new appointments.
