import os
import shutil

class FileWrapper:
	path = None
	
	def __init__(self, path):
		self.path = path
		
	def store_file(self, key, local_file):
		try:
			shutil.copy(local_file, self.path + key)
		except:
			return False
		
		return True
	
	def del_file(self, key):
		try: 
			os.remove(self.path + key) 
		except:
			return False
		
		return True
	
	def get_file(self, key, local_file):
		try: 
			shutil.copy(self.path + key, local_file) 
		except:
			return False