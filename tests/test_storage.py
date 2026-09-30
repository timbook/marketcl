import os
import tempfile
import unittest
from unittest import mock

from marketcl import storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"MCL_HOME": self.tmp.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_create_and_load(self):
        game = storage.create_game("My Game", 500)
        self.assertEqual(storage.load_game(game["slug"])["cash"], 500.0)

    def test_duplicate_names_rejected(self):
        storage.create_game("My Game", 500)
        with self.assertRaises(ValueError):
            storage.create_game("my game", 500)

    def test_list_games(self):
        storage.create_game("a", 1)
        storage.create_game("b", 1)
        self.assertEqual([g["name"] for g in storage.list_games()], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
