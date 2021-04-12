from django.test import TestCase
from django.test.utils import override_settings
from playlist.models import Song, PlaylistEntry, OldPlaylistEntry, Artist, Album
from playlist.views import add

class SongTestCase(TestCase):

	def _testSong(self, title):
		Song.objects.create(title=title, album=Album(title), artist=Artist(title))

	def setUp(self):
		self.a = _testSong("A")
		self.b = _testSong("B")
		self.c = _testSong("C")

	@override_settings(NEXT_PASSWORD='test')
	@override_settings(REPLAY_INTERVAL=0)
	def test_play_count(self):
		add(self.a.id)
		add(self.c.id)
		next('test')
		next('test')
		add(self.c.id)
		next('test')
		add(self.c.id)
		next('test')
		add(self.c.id)
		self.assertEqual(self.a.getPlaycount(), 1)
		self.assertEqual(self.a.getPlaycount(), 0)
		self.assertEqual(self.a.getPlaycount(), 3)
