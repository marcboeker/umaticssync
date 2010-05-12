import os
import os.path
import getopt
import sys
import ConfigParser
import datetime
import logging
from time import sleep
from dateutil.parser import * 
from lib.db import DB
from lib.backup import Backup

class UmaticsSync:
	"""UmaticsSync is an universal backup utility with different storage
	engines and the ability to work with multiple backup revisions. Each
	job is processed in a defined interval.
	
	# Normal backup for a specific job
	$ ./umaticssync.py -j documents
	
	# Restore job with name documents and revision number 32
	$ ./umaticssync.py -j documents -r 32
	
	# Run as daemon and execute every job in it's interval
	$ ./umaticssync.py"""
	
	conf_dir = os.path.expanduser('~/.umaticssync/')
	opts = None
	job_list = None
	sync_list = None
	sync_file = None
	backup_list_fp = None
	backup_size = 0
	db = None
	
	def __init__(self):
		self.opts = self._parse_arg_list()
		
		# toggle debug mode
		if self.opts.has_key('d'):
			logging.basicConfig(level=logging.DEBUG)
		
		# overwrite default config path
		if self.opts.has_key('c'):
			self.conf_dir = self.opts['c']
			logging.info('Using %s as config path' % self.conf_dir)
		
		# check if config path exists
		if not os.path.isdir(self.conf_dir):
			os.mkdir(self.conf_dir)
			logging.error(
				'No configuration available, created %s' % self.conf_dir
			)
			sys.exit()
		
		# backup jobs
		backup_list = os.path.join(self.conf_dir, 'backup_list')
		self.job_list = ConfigParser.ConfigParser()
		self.job_list.read(backup_list)
		self.db = DB(os.path.join(self.conf_dir, 'files.db'))

		# restore
		if self.opts.has_key('r') and self.opts.has_key('j'):
			logging.info(
				'Starting restore mode on job %s with rev %s' 
				% (self.opts['j'], self.opts['r'])
			)
			self.restore(self.opts['j'], self.opts['r'])
		# backup (job-based)
		elif self.opts.has_key('j'):
			logging.info('Starting backup mode on job %s' % self.opts['j'])
			self._get_backup_list(self.opts['j'])
		# backup daemon
		else:
			logging.info('Starting backup daemon')
			
			try:
				while True:		
					self._get_backup_list()
					self._save_sync_list()
					sleep(60)
			except KeyboardInterrupt:
				self._save_sync_list()
				logging.info('Exiting')
				sys.exit()
		
		# save sync file
		if self.sync_list:
			self._save_sync_list()
			
	def _save_sync_list(self):
		"""Saves the current sync list to the file system."""
		fp = open(self.sync_file, 'w')
		self.sync_list.write(fp)
		fp.close()
		
	def _parse_arg_list(self):
		"""Transform list of argument tuples to dict."""
		arg_list = {}
		for arg in getopt.getopt(sys.argv[1:], 'c:r:j:d')[0]:
			arg_list[arg[0][1:]] = arg[1]
	
		return arg_list 
				
	def _get_backup_list(self, job=None):
		"""Get a list of backup jobs and execute the specific job every 
		given interval."""
		# sync list
		self.sync_file = os.path.join(self.conf_dir, 'sync')
		self.sync_list = ConfigParser.ConfigParser()
		self.sync_list.read(self.sync_file)
		
		# fallback to one single job
		if job:
			jobs = [job, ]
		else:
			jobs = self.job_list.sections()
		
		for job in jobs:
			interval = self.job_list.getint(job, 'interval')
			job_dict = self._get_job_dict(job)
			job_dict['name'] = job
						
			try:
				ls = parse(self.sync_list.get(job, 'last_sync'))
				
				# job is in interval range and is not currently running
				if (datetime.datetime.now() - ls) > \
					datetime.timedelta(0, interval, 0) \
					and lbs != 1:
					logging.info('[%s] Starting backup process' % job)
					backup = Backup(job_dict, self.db)
					backup.backup()
					self._set_sync_option(
						job, 'last_sync', datetime.datetime.now()
					)
			except:
				logging.info('[%s] Starting backup process' % job)
				if not self.sync_list.has_section(job):
					self.sync_list.add_section(job)
				backup = Backup(job_dict, self.db)
				backup.backup()
				self._set_sync_option(job, 'last_sync', datetime.datetime.now())

	def _set_sync_option(self, job, option, value):
		"""Set valiable in a section called job with given value."""
		
		if not self.sync_list.has_section(job):
			self.sync_list.add_section(job)
		
		self.sync_list.set(job, option, value)
			
	def _get_job_dict(self, job):
		"""Transform tuple construct into dict."""
		
		jobs = {}		
		for job in self.job_list.items(job):
			jobs[job[0]] = job[1]
			
		return jobs
		
	def restore(self, job, revision):
		"""Restore backup based on job and revision."""
		
		job_dict = self._get_job_dict(job)
		job_dict['name'] = job
		
		# start restore process
		backup = Backup(job_dict, self.db)
		backup.restore(revision)
		
if __name__ == '__main__':
	UmaticsSync()