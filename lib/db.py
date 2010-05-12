import sqlite3
from os.path import isfile
from sys import exit
from md5 import md5

class DB:
	"""Manages the complete interaction with the database."""
	
	path = None
	conn = None
	
	def __init__(self, path):
		self.path = path

		if not isfile(path):
			self.connect()
			self.create_struct()

		self.connect()		
			
	def connect(self):
		"""Connects to the database."""
		try:
			self.conn = sqlite3.connect(self.path)
		except:
			exit('DB not found at %s' % self.path)
			
	def create_struct(self):
		"""Inits database."""
		
		structure = """
			CREATE TABLE files (
				hash Varchar PRIMARY KEY NOT NULL,
				job VarChar NOT NULL,
				path VarChar NOT NULL,
				revision Integer NOT NULL DEFAULT '0',
				mtime Integer NOT NULL,
				size Integer NOT NULL DEFAULT '0',
				date Integer NOT NULL DEFAULT current_timestamp,
				encrypted Integer NOT NULL DEFAULT '0',
				compressed Integer NOT NULL DEFAULT '0'
			);
		"""
		
		c = self.conn.cursor()
		c.execute(structure)
		self.conn.commit()
		c.close()
		
	def get_file(self, job, path):
		"""Gets file by job and path or hash."""
		
		# get file by path
		c = self.conn.cursor()
		c.execute("""
			SELECT * FROM files WHERE job = ? AND path = ? LIMIT 1
		""", (job, path))
			
		result = c.fetchone()
		
		if not result:
			c.close()
			return None
		
		c.close()
		
		return {
			'hash': result[0],
			'job': result[1],
			'path': result[2],
			'revision': result[3],
			'mtime': result[4],
			'size': result[5],
			'date': result[6],
			'encrypted': result[7],
			'compressed': result[8],
		}
		
	def get_files(self, job):
		""""Gets all files in a job."""
		
		# get files by job
		c = self.conn.cursor()
		c.execute("""SELECT * FROM files WHERE job = ?""", (job,))
		result = c.fetchall()
		
		if not result:
			c.close()
			return None
		
		c.close()
		
		files = []
		for file in result:
			files.append({
				'hash': file[0],
				'job': file[1],
				'path': file[2],
				'revision': file[3],
				'mtime': file[4],
				'size': file[5],
				'date': file[6],
				'encrypted': file[7],
				'compressed': file[8],
			})
			
		return files
	
	def add_file(self, job, path, mtime, size, encrypted=0, compressed=0):
		"""Adds a file to the database. If the file exists, 
		increment revision."""
		
		hash = md5(job + path).hexdigest()
		revision = 0
		
		c = self.conn.cursor()
		
		# try insert
		try:
			c.execute("""
			  	INSERT INTO files VALUES(
			  		?, ?, ?, ?, ?, ?, current_timestamp, ?, ?
			  	)""", 
			  	(hash, job, path, revision, mtime, size, encrypted, compressed)
			)
			self.conn.commit()
		# otherwise update
		except:
			c.execute("""
			  	UPDATE files SET revision = revision + 1, 
			  	mtime = ?, size = ?, date = current_timestamp
			  	WHERE hash = ? 
			""", (mtime, size, hash))
			self.conn.commit()
			
			# get file info
			c.execute("""SELECT revision FROM files WHERE hash = ?""", (hash,))
			revision = c.fetchone()[0]
			
		c.close()
		
		return {'hash': hash, 'revision': revision}
