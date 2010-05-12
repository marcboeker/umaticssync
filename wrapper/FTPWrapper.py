from ftplib import FTP

class FTPWrapper:
	ftp = None
	file = None
	local_file = None
	
	def __init__(self, host, user, password, path):
		self.ftp = FTP(host, user, password)
		self.ftp.connect()
		self.ftp.cwd(path)
		
	def store_file(self, key, local_file):
		try:
			self.ftp.storebinay(key, open(local_file, 'r'))
		except:
			return False
		
		return True
	
	def del_file(self, key):
		try: 
			self.ftp.delete(key) 
		except:
			return False
		
		return True
	
	def save_file(self, data):
		if not self.file:
			self.file = open(self.local_file, 'w')
			
		self.file.write(data)
	
	def get_file(self, key, local_file):
		self.local_file = local_file
		try: 
			self.ftp.retrbinary('', self.save_file)
		except:
			return False