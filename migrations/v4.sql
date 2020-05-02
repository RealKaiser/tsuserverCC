PRAGMA foreign_keys = OFF;

CREATE TABLE ip_warns(
	ipid INTEGER NOT NULL,
	warn_id INTEGER NOT NULL,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE,
	FOREIGN KEY (warn_id) REFERENCES warns(warn_id)
		ON DELETE CASCADE
	UNIQUE (ipid) ON CONFLICT IGNORE
);

CREATE TABLE warns(
	warn_id INTEGER PRIMARY KEY,	
	warn_date DATETIME DEFAULT CURRENT_TIMESTAMP,
	warned_by INTEGER,
	reason TEXT,
	FOREIGN KEY (warned_by) REFERENCES ipids(ipid)
		ON DELETE SET NULL
);

PRAGMA foreign_key_check;
PRAGMA foreign_keys = ON;

VACUUM;

PRAGMA user_version = 4;