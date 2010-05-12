from os import system
import tarfile

class Archive:
	"""Handles file compression and extraction."""
	
	def compress(self, src, target):
		"""Compress file."""
		try:
			tbz2 = tarfile.TarFile.open(target, 'w:bz2')
			tbz2.add(src)
			tbz2.close()
		except:
			return False
	
	def extract(self, src):
		"""Extract file to root."""
		try:
			tbz2 = tarfile.TarFile.open(src, 'r:bz2')
			tbz2.extractall('/')
			tbz2.close()
		except:
			return False