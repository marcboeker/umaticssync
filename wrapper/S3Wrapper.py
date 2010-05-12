from lib.s3 import AWSAuthConnection, S3Object

class S3Wrapper:
	"""Handles S3 storage operations."""
	
	s3 = None
	bucket = None
	
	def __init__(self, access_key, secret_key, bucket):
		self.bucket = bucket
		self.s3 = AWSAuthConnection(
			access_key, secret_key
		)
		
	def store_file(self, key, local_file):
		"""Stores file on S3 with private acl."""
		
		try:
			data = open(local_file, 'r').read()
			self.s3.put(
				self.bucket,
				key,
				S3Object(data), {
					'Content-Type': 'application/x-bzip2',
					'x-amz-acl': 'private',
					'Content-Length': len(data)
				}
			)
		except:
			return False
	
	def del_file(self, key):
		"""Deletes file on S3."""
		
		try: 
			self.s3.delete(self.bucket, key) 
		except:
			return False
		
	def get_file(self, key, local_file):
		"""Download file from S3."""
		
		try:
			fh = open(local_file, 'wb')
			fh.write(self.s3.get(self.bucket, key).object.data)
			fh.close()
		except:
			return False
