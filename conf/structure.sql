CREATE TABLE files (
	hash Varchar PRIMARY KEY NOT NULL,
	job VarChar NOT NULL,
	path VarChar NOT NULL,
	revision Integer NOT NULL DEFAULT '0',
	mtime Integer NOT NULL,
	size Integer NOT NULL DEFAULT '0'
);