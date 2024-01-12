from django.test import TestCase
from rest_framework.test import APIClient
from etl.ao3.work_import import EtlWorkImport
from etl.export.chive_export import ChiveExport
import json
import api.models as models
from django.core.management import call_command

class Ao3ImportTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		fixtures = [
			'tagtype', 'tags', 'worktype', 'work', 'bookmark', 'bookmarkcollection', 'chapter', 'ourchivesettings', 'objectmapping'
		]
		cls.test_user = models.User.objects.create(username="test_user", email="test_user@test.com")
		cls.test_admin_user = models.User.objects.create(username="test_admin_user", email="test_admin@test.com")
		for db_name in cls._databases_names(include_mirrors=False):
			call_command("loaddata", *fixtures, verbosity=0, database=db_name)

	def test_process_work_data(self):
		import_cls = EtlWorkImport(1, True, True, False)
		work_id = import_cls.process_work_data(json.loads(self.test_work_data))
		created_work = models.Work.objects.get(pk=work_id)
		self.assertEqual(created_work.summary, "<p>An incident leads Prunella to acquire a somewhat inconvenient student.</p>")
		self.assertEqual(len(created_work.tags.all()), 3)
		self.assertEqual(len(created_work.attributes.all()), 2)
		self.assertFalse(created_work.comments_permitted)
		self.assertTrue(created_work.anon_comments_permitted)
		self.assertTrue(created_work.draft)
		self.assertEquals(created_work.word_count, 1119)

	def test_process_chapter_data(self):
		import_cls = EtlWorkImport(1, True, True, False)
		work_id = import_cls.process_work_data(json.loads(self.test_work_data))
		chapter_ids = import_cls.process_chapter_data(json.loads(self.test_chapter_data), work_id)
		self.assertEquals(len(chapter_ids), 1)
		created_chapter = models.Chapter.objects.get(pk=chapter_ids[0])
		self.assertEqual(created_chapter.title, "Chapter One")

	def test_create_work_export(self):
		works = models.Work.objects.all()
		exporter = ChiveExport()
		exporter.write_csv(works)
		for work in works:
			exporter.write_csv(work.chapters.all())

	def test_create_bookmark_export(self):
		bookmarks = models.Bookmark.objects.all()
		exporter = ChiveExport()
		exporter.write_csv(bookmarks)

	def test_create_collection_export(self):
		collections = models.BookmarkCollection.objects.all()
		exporter = ChiveExport()
		exporter.write_csv(collections)

	test_work_data =  r"""{
                "id": 8878807,
                "title": "Like Mother, Like Daughter",
                "author": "impertinence",
                "summary": "<p>An incident leads Prunella to acquire a somewhat inconvenient student.</p>",
                "rating": [
                    "General Audiences"
                ],
                "warnings": [],
                "category": [
                    "F/M"
                ],
                "fandoms": [
                    "Sorcerer to the Crown - Zen Cho"
                ],
                "relationship": [
                    "Prunella Gentleman/Zacharias Wythe"
                ],
                "characters": null,
                "additional_tags": null,
                "language": "English",
                "collections": "Yuletide 2016",
                "stats": {
                    "published": "2016-12-17",
                    "completed": "2016-12-17",
                    "words": 1119
                }
            }"""

	test_chapter_data = r"""{
			"id": 8878807,
			"content": [
				{
				"title": "Chapter One",
				"content": "<p>Prunella expected the disrespect she received from various magicians, of course. Too, she expected various incidents of stubborn English wives, and Zachariah's own brand of reticence, which was good for infuriating said English wives - but also, unfortunately, good for infuriating Prunella herself. But then, she'd expected that too, for she was an irritable sort who rarely maintained a good temper over the longterm.</p><p>So very little came as a surprise, those first few months of being Sorcerer Royal. But what Prunella was currently staring at - well, this surprise was unpleasant enough to make up for the lack.</p><p>Not what. <em>Who.</em> The little girl in question crossed her arms and glared at Prunella. \"I <em>said</em>, where's my mum?\"</p><p>\"Ah.\" The answer was that the girl's mother, the wife of one of the magicians that Prunella now lead, had been dispatched halfway around the world using some rather complicated magic, an answer Prunella suspected the little girl would not accept. \"To a...shop?\"</p><p>\"We have <em>servants</em> for that.\"</p><p>\"Do you have servants to teach you to be less impudent? Do you know who I am?\"</p><p>\"Some big lady what's in charge of all this.\" Prunella had rarely seen as expansive and disdainful a hand gesture as followed this statement.</p><p>\"You're a bit too high-class for that grammar,\" she told the child. \"And your mother will be back soon.\" Hopefully. \"Good day.\"</p><p>She turned and walked - two steps, four, and yes, behind her was the patter of small, very expensive shoes. She stopped, sighed, and turned around.</p><p>The child looked at her with big blue eyes and a thumb in her mouth. Right, then. It was to be bribery.</p><p>\"Take your hand out of your mouth, and I shall test you for magic,\" Prunella said.</p><p>The child clapped her spittle-covered thumb against her palm and grinned broadly.</p><p>-</p><p>When she arrived back at the house with the little girl - Emily - in tow, Zacharias was working on his latest project, a magical study of the physical properties of ammonites. It was likely to be utterly politically useless, which of course meant that he loved it. </p><p>\"Hello, dear,\" she said. \"I've acquired a parasite.\" She gestured broadly to Emily.</p><p>\"That's an ugly rock,\" Emily said.</p><p>\"It's not a rock,\" Zacharias said. \"It's a fossil.\"</p><p>\"Still ugly.\"</p><p>\"Emily!\"</p><p>Emily looked up at Prunella. Prunella looked down at her. She gave her best Mind Your Elders look; Emily returned the gesture with a mutinous glare.</p><p>At the table, Zacharias chuckled.</p><p>Right, then. \"You test her,\" Prunella said. \"I've very important work to do.\"</p><p>\"Of course. Happy to. Come here, then.\" Zacharias gestured to Emily. \"Let's see what you're capable of.\"</p><p>That was one problem dealt with, then, and very neatly. I wash my hands of her, Prunella thought with force, and went to see a Lord about a dragon.</p><p>-</p><p>\"She's staggeringly powerful,\" Zacharias said over meat and potatoes.</p><p>Emily had been handed off to a nurse to spend her night in something resembling her normal pampered luxury, so she didn't see Prunella drop her fork and swear a blue streak.</p><p>\"I suppose it's hardly surprising,\" she said. \"Her mother, after all, has magic, and her father's one of our magicians.\"</p><p>\"We can send her to school.\"</p><p>\"We'll have to. I certainly don't want her around.\"</p><p>Zacharias' only response to this pronouncement was an amused look.</p><p>Prunella prickled. \"What?\"</p><p>\"She reminds me of you, a bit.\"</p><p>\"Me! A spoiled, selfish little peer of the realm reminds you of <em>me</em>?\"</p><p>\"Only a bit,\" Zacharias said. But he kept smiling.</p><p>He was altogether too sentimental sometimes. Prunella huffed and said, \"Well. We'll tell her tomorrow.\"</p><p>\"Of course,\" Zacharias said, and returned to his roast.</p><p>-</p><p>\"No.\"</p><p>Prunella raised her eyebrows at Emily. \"You know, two years ago, little girls couldn't learn magic at all. You're lucky.\"</p><p>\"No.\"</p><p>\"Do you plan to say anything else? A more graceful declination, perhaps?\"</p><p>\"I want my mum,\" Emily said, \"and I want <em>you</em> to teach me.\"</p><p>\"Well, I want sixteen chocolates and a great big wolf to carry me everywhere. We don't always get what we want.\"</p><p>Emily only stuck her chin out, accompanying it with a mutinous glare.</p><p>Right, then. Time for diplomacy. \"Why don't you want to go, exactly? Perhaps we can compromise.\"</p><p>\"You've got a dragon,\" Emily said. \"The school hasn't got dragons.\"</p><p>\"I have several familiars - it's not the same thing - and anyway - <em>argh.</em>\" Somehow, she'd grown far more used to dealing with obstreperous old men than little girls. \"I don't think you'd like to have me as a teacher. We're not exactly getting along, are we?\"</p><p>Emily's lip began to tremble. Her eyes filled with tears.</p><p>Oh, no.</p><p>She opened her mouth and wailed. Prunella winced, and for a moment felt really very guilty - but only for a moment, because for heaven's sake! \"Emily -\"</p><p>\"Aaaauuuughghghgh!\" Emily shouted - and a brilliantly blue orb appeared above her head.</p><p>Prunella shut her mouth and watched. The screaming continued, and the orb grew in color and in brilliance until it surrounded Emily entirely. Then, just as Prunella was about to intervene, Emily shut her mouth.</p><p>The orb contracted around her, and they - orb and girl - disappeared.</p><p>Prunella barely had any time to panic before Emily reappeared, several feet to the right, so close to a wall that when the orb disappeared, the girl fell against the wood paneling. </p><p>\"Emily,\" Prunella said. \"How many times did you watch your parents practice the travel ritual?\"</p><p>Emily's expression cleared into a devil's own smugness. \"I'll tell you if you teach me more.\"</p><p>\"Deal.\"</p><p>-</p><p>As it turned out, Emily had witnessed quite a bit - enough to retrace the ritual and send them on the path that led to discovering her mother, stranded on a rock in northernmost Scotland and quite irritated with the entire premise. When Prunella attempted to delicately suggest that they ought to find their daughter a competent magical tutor, Lady Rockingham snapped, \"You do whatever you like,\" and Emily yelled, \"Don't be mean to my teacher!\", and Prunella's familiars divided themselves between glaring at Lady Rockingham and preening at Emily - who of course, they all liked, since she was as small and entitled as they.</p><p>It was, Zacharias remarked that night, an arrangement that suited Prunella very well. </p><p>\"That's ridiculous,\" Prunella sniffed. \"What do I care for some child's development?\"</p><p>\"Quite a bit, I think.\"</p><p>Zacharias wore that smile, half-shy and half-knowing, that Prunella both loved and hated. She couldn't help but kiss him then.</p><p>\"I'm not having any children of my own,\" she said.</p><p>\"I know.\"</p><p>\"And I'm not going to take on a string of impudent girls as apprentices, either.\"</p><p>\"Mmmm.\"</p><p>He didn't believe her. Pah! They could have that argument another day.</p>"
				}
			]
		}"""
