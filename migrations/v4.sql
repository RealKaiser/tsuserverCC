PRAGMA foreign_keys = OFF;

CREATE TABLE warns(
	warn_id INTEGER PRIMARY KEY,
	ipid INTEGER,
	hdid TEXT,
	warn_date DATETIME DEFAULT CURRENT_TIMESTAMP,
	warned_by INTEGER,
	warn_type TEXT,
	reason TEXT,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE,
	FOREIGN KEY (warned_by) REFERENCES ipids(ipid)
		ON DELETE SET NULL
);

PRAGMA foreign_key_check;
PRAGMA foreign_keys = ON;

VACUUM;

PRAGMA user_version = 4;