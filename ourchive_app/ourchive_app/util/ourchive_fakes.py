from faker import Faker
import api.models as models


class OurchiveFakes():

	def __init__(self):
		self.fake = Faker()
		self.fake.random.seed(6875309)

	def generate_users(self, obj_count=1, persist_db=False):
		users = []
		for x in range(0, obj_count):
			user = models.User(username=self.fake.email(), password=self.fake.password(length=15))
			if persist_db:
				user.save()
			users.append(user)
		return users

	def generate_works(self, user_id, obj_count=1, persist_db=False, chapter_count=0):
		works = []
		for x in range(0, obj_count):
			work = models.Work(title=self.fake.sentence(),
				summary=self.fake.paragraph(),
				notes=self.fake.paragraph(),
				is_complete=self.fake.pybool(),
				cover_url=self.fake.url(),
				cover_alt_text=self.fake.sentence(),
				preferred_download_url=self.fake.url(),
				anon_comments_permitted=self.fake.pybool(),
				comments_permitted=self.fake.pybool(),
				word_count=self.fake.pyint(max_value=300000),
				audio_length=self.fake.pyint(),
				fingerguns=self.fake.pyint(),
				draft=self.fake.pybool(),
				comment_count=self.fake.pyint(),
				preferred_download=models.Work.DOWNLOAD_CHOICES[self.fake.pyint(max_value=len(models.Work.DOWNLOAD_CHOICES)-1)],
				epub_url=self.fake.url(),
				m4b_url=self.fake.url(),
				zip_url=self.fake.url(),
				external_id=self.fake.pyint() if x%2 == 0 else None,
				user_id=user_id)
			if persist_db:
				work.save()
			if chapter_count > 0:
				chapters = []
				for y in range(1, chapter_count+1):
					chapter = models.Chapter(user_id=user_id,
						work=work,
						title=self.fake.words(nb=8),
						number=y,
						text=self.fake.paragraph(),
						notes=self.fake.paragraph(),
						end_notes=self.fake.paragraph(),
						word_count=self.fake.pyint(max_value=20000),
						audio_url=self.fake.url(),
						audio_description=self.fake.sentence(),
						audio_length=self.fake.pyint(),
						video_url=self.fake.url(),
						video_description=self.fake.sentence(),
						video_length=self.fake.pyint(),
						image_url=self.fake.url(),
						image_alt_text=self.fake.sentence(),
						image_format=self.fake.mime_type(),
						image_size=str(self.fake.pyint()),
						summary=self.fake.paragraph(),
						draft=self.fake.pybool(),
						comment_count=self.fake.pyint())
					if persist_db:
						chapter.save()
					chapters.append(chapter)
			works.append(work)
		return (works, chapters)

	def generate_bookmarks(self, obj_count=1, persist_db=False):
		pass

	def generate_tags(self, obj_count=1, persist_db=False):
		pass

	def generate_attributes(self, obj_count=1, persist_db=False):
		pass

	def generate_collections(self, obj_count=1, persist_db=False):
		pass
