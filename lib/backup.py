from os.path import walk, join, isfile, isdir, getmtime 
from os.path import normpath, getsize, basename, dirname
from os import remove, rename, system
from sys import exit
from crypt import Crypt
from archive import Archive
from urlparse import urlsplit
from db import DB
import tempfile
import logging

class Backup:
	"""Handles complete backup flow. Check if file exists orhas been modified.
	Compresses, encrypts and uploads the file to th destination."""

	db = None
	job = None
	compress = None
	encrypt = None
	
	def __init__(self, job, db):
		self.job = job
		self.db = db
		
		self.archive = Archive()
		self.crypt = Crypt()
	
	def backup(self):
		"""Start backup process."""
		
		if not isdir(self.job['path']):
			self._list_files(
				None, dirname(self.job['path']), [basename(self.job['path']), ]
			)
		else:
			walk(self.job['path'], self._list_files, None)
		
	def _list_files(self, dir, basepath, files):
		"""Callback for walker. Iterates over filelist, builds absolute path
		and checks wheather to skip or upload the file."""
		
		for file in files:
			# absolute path
			path = join(basepath, file)
			
			# only work on files
			if isfile(path)	or (
				not isdir(path) and self.job.has_key('pre_command')):
				
				item = self.db.get_file(self.job['name'], path)
				
				# file is not in db
				if not item:
					self._backup_file(path)
				else:
					# file exists in db, but has a different mtime
					if isfile(path):
						mtime = getmtime(path)
						
						if int(item['mtime']) != int(mtime):
							self._backup_file(path)
					else:
						self._backup_file(path)
						
	def _execute_command(self, command):
		"""Execute pre- or postcommand."""
		if self.job.has_key(command):
			try:
				logging.info('[%s] Executing %s' 
					% (self.job['name'], self.job[command]))
				system(self.job[command])
			except:
				logging.warn('[%s] Command failed %s' 
					% (self.job['name'], self.job[command]))

	def _backup_file(self, path):
		"""Back ups specific file to desired storage device."""
		
		print('[%s] Starting backup for %s' % (self.job['name'], path))
		
		# precommand
		self._execute_command('pre_command')
		
		# get size, mtime
		file_info = self._file_info(path)
		
		# get storeage wrapper
		storage = self._get_account(self.job['destination'])
		dest = join(tempfile.gettempdir(), 'umaticssync')
		
		# is compression deired? bzip2 file
		if self.job.has_key('compress') and self.job['compress'] == 'true':
			logging.info('[%s] Compressing %s' % (self.job['name'], path))
			self.archive.compress(path, dest)
			old_dest = dest
			compressed = 1
		
		# is encryption desired? encrypt with user id
		if self.job.has_key('encrypt') and self.job['encrypt']:
			logging.info('[%s] Encrypting %s' % (self.job['name'], path))
			self.crypt.encrypt(self.job['encrypt'], dest)
			dest = dest + '.gpg'
			remove(old_dest)
			encrypted = 1
		
		# add file/increase revision
		info = self.db.add_file(
			self.job['name'], path, file_info['mtime'], file_info['size'], 
			encrypted, compressed)
		
		# build key and upload, cleanup
		key = normpath('%s/%s.r%%s' % (self.job['name'], path))
		logging.info('[%s] Uploading %s.r%s' 
			% (self.job['name'], path, info['revision']))
		storage.store_file(key % info['revision'], dest)
		remove(dest)
		
		# cleanup old revisions
		revision = int(info['revision']) - int(self.job['revisions'])
		if revision >= 0:
			print "del", key % revision
			storage.del_file(key % revision)
			
		# postcommand
		self._execute_command('post_command')
		
	def _file_info(self, path):
		"""Returns size and mtime."""
		return {'size': getsize(path), 'mtime': getmtime(path)}
		
	def _get_account(self, uri):
		"""Return storage engine object based on the provided URI string."""
		uri = urlsplit(uri)
		
		# s3 backend
		if uri[0] == 's3':
			a_key, s_key = uri[2][2:].split('@')[0].split(':')
			bucket = uri[2][2:].split('@')[1]
			
			from wrapper.S3Wrapper import S3Wrapper
			return S3Wrapper(a_key, s_key, bucket)
		# ftp server
		elif uri[0] == 'ftp':
			user, passwd = uri[2][2:].split('@')[0].split(':')
			host = uri[2][2:].split('@')[1]
			path = uri[2]
			
			from wrapper.FTPWrapper import FTPWrapper
			return FTPWrapper(host, user, passwd, path)
		# @todo: implement
		elif uri[0] == 'scp':
			pass
		# local storage backend
		elif uri[0] == 'file':
			path = uri[1]
			
			from wrapper.FileWrapper import FileWrapper
			return FileWrapper(path)

	def restore(self, revision):
		files = self.db.get_files(self.job['name'])
		
		if len(files) == 0:
			#logging.info('[%s] No files found for backup job')
			return False
		
		# get storage instance
		storage = self._get_account(self.job['destination'])
		
		# iterate thur files
		for file in files:
			try:
				# is given revision in allowed range?
				rev_diff = int(file['revision']) - int(self.job['revisions'])
				if int(revision) in range(rev_diff, file['revision'] + 1):
					rev = revision
				else:
					# fallback to latest file revision
					rev = file['revision']
			except:
				rev = file['revision']
			
			logging.info('[%s] Restoring %s.r%s' 
				% (self.job['name'], file['path'], rev))
			
			# get file
			key = normpath('%s/%s.r%s' % (self.job['name'], file['path'], rev))
			dest = join(tempfile.gettempdir(), 'umaticssync')
			
			logging.info('[%s] Downloading %s' 
				% (self.job['name'], file['path']))
			storage.get_file(key, dest)
			
			if file['encrypted'] == 1:
				logging.info('[%s] Decrypting %s' 
					% (self.job['name'], file['path']))
				self.crypt.decrypt(self.job['encrypt'], dest, dest)
			
			if file['compressed'] == 1:
				logging.info('[%S] Extracting %s' 
					% (self.job['name'], file['path']))
				self.archive.extract(dest)
			else:
				rename(dest, file['path'])
