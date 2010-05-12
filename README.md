# UmaticsSync - Backup as customizable as you want

UmaticsSync helps you to backup whatever and whenever you want. It provides
pluggable storage backends. Currently it supports:

* S3
* FTP
* Filesystem

It also makes use of GnuPG for encrypting the backups before storing them. We
use it in production only with the S3 storage backend. Others are untested.

# Installation

You need the following dependencies:

* Python > 2.4
* Python sqlite3
* Python boto
* SQLite 3 executables
* GnuPG executables

First install the binary dependencies (here for Gentoo):

    USE="sqlite" emerge python sqlite3 setuptools gnupg

Next get the Python dependencies:

    easy_install sqlite3 boto

Obtain the source code:

    git clone git@github.com:marcboeker/umaticssync.git

Edit the backup jobs in <code>conf/backup_list</code> (examples below) and
copy them to ~/.umaticssync (create the directory first).

	mkdir ~/.umaticssync && cp conf/backup_list ~/.umaticssync
	
Now you can start the backup script and deamonize it:

	python umaticssync.py >/dev/null 2>&1
	
	or
	
	screen -dmS backup python umaticssync.py
	
# Configuration

This is a sample backup job, that shows the various options:

	[name-of-the-job]
	interval = 21600
	post_command = rm /tmp/dump.tar.bz2 && rm -Rfv /tmp/dump
	destination = s3://access_key:secret_key@bucket.example.com
	path = /tmp/dump.tar.bz2
	pre_command = mongodump -d db -o /tmp/dump && tar -cjvpf /tmp/dump.tar.bz2 /srv/dump
	revisions = 10
	encrypt = you@yourprivatekey.com
	compress = true

The value in the brackets is the name of the job. This name is later used as
a directory name on the target storage device. Make sure this name has no
fancy chars in it.

	interval = <seconds>

Time between backups

	post_command = <cmd>

Shell command that is run after the backup (e.g. cleanup)
	
	destination = (s3|ftp|file)://<username>:<password>@<host> 

Please refer to the storage wrappers to find the details on the usage

	path = <path-to-backup> 

Should be a file or directory

	pre_command = <cmd> 

Will be run before the backup starts (e.g. compress files)
	
	revisions = <number> 

How many revisions would you like to keep

	encrypt = true|false 

Use gnupg to encrypt backup
	
	compress = true|false 
	
Let umaticssync compress the files for you

# Usage

	# Normal backup for a specific job
	$ ./umaticssync.py -j <job>
	
	# Restore job with name documents and revision number 32
	$ ./umaticssync.py -j <job> -r 32
	
	# Run in foreground and execute every job in the given interval
	$ ./umaticssync.py

# Disclaimer

UmaticsSync and its creator are not responsible for any damages, or missing
files. Use this at your own risk.
