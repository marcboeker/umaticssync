from os import system

class Crypt:
	"""Handles encryption requests.""" 
	
	pw = None
	
	def encrypt(self, user, src):
		"""Encrypts a file with a specific user id."""
		
		try:
			system('gpg --yes -e -r %s %s' % (user, src))
		except:
			return False
	
	def decrypt(self, user, src, target):
		"""Decrypt file with password save function."""
		
		if not self.pw:
			self.pw = raw_input('Please enter your pw: ')
		
		try:
			system("""echo "%s" | gpg --batch --passphrase-fd 0 --yes -d \
			 	-r %s -o %s %s >/dev/null 2>&1""" 
			 	% (self.pw, user, target, src))
		except:
			return False