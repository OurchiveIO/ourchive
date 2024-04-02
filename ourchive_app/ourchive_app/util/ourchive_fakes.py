from faker import Faker


class OurchiveFakes():

	def __init__(self):
		self.faker_util = Faker()
		self.faker_util.random.seed(6875309)

	def generate_users(self):
		pass

	def generate_works(self, obj_count=1, persist_db=False):
		pass

	def generate_bookmarks(self, obj_count=1, persist_db=False):
		pass

	def generate_tags(self, obj_count=1, persist_db=False):
		pass

	def generate_attributes(self, obj_count=1, persist_db=False):
		pass

	def generate_collections(self, obj_count=1, persist_db=False):
		pass
