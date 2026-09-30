import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from marketcl import storage
from marketcl.cli import cli


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"MCL_HOME": self.tmp.name})
        self.env.start()
        self.runner = CliRunner()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def invoke(self, args, inp=None):
        return self.runner.invoke(cli, args, input=inp)

    def new_game(self, name="test", capital=""):
        res = self.invoke(["new", name], inp=f"{capital}\n")
        self.assertEqual(res.exit_code, 0, res.output)

    def test_new_default_capital_and_files(self):
        self.new_game()
        game = storage.get_current_game()
        self.assertEqual(game["cash"], 10000.0)
        self.assertTrue((Path(self.tmp.name) / "games" / "test.json").exists())
        self.assertTrue((Path(self.tmp.name) / "config.json").exists())

    def test_new_custom_capital(self):
        self.new_game("big", "25000")
        self.assertEqual(storage.get_current_game()["initial_capital"], 25000.0)

    def test_switch_games(self):
        self.new_game("one")
        self.new_game("two")
        self.assertEqual(storage.get_current_slug(), "two")
        res = self.invoke(["game", "one"])
        self.assertEqual(res.exit_code, 0, res.output)
        self.assertEqual(storage.get_current_slug(), "one")
        res = self.invoke(["game"], inp="2\n")
        self.assertEqual(storage.get_current_slug(), "two")

    @mock.patch("marketcl.cli.get_price", return_value=100.0)
    def test_buy_uses_market_price_and_never_prompts_for_price(self, _):
        self.new_game()
        res = self.invoke(["buy", "aapl"], inp="5\ny\n")
        self.assertEqual(res.exit_code, 0, res.output)
        self.assertNotIn("Price per share", res.output)
        game = storage.get_current_game()
        self.assertEqual(game["cash"], 9500.0)
        self.assertEqual(game["holdings"]["AAPL"], {"shares": 5, "avg_cost": 100.0})
        self.assertEqual(game["transactions"][0]["price"], 100.0)

    @mock.patch("marketcl.cli.get_price", return_value=100.0)
    def test_buy_rejects_too_many_and_can_cancel(self, _):
        self.new_game()
        res = self.invoke(["buy", "AAPL"], inp="1000\n5\nn\n")
        self.assertEqual(res.exit_code, 0, res.output)
        self.assertEqual(storage.get_current_game()["cash"], 10000.0)

    @mock.patch("marketcl.cli.get_price")
    def test_sell_and_average_cost(self, gp):
        self.new_game()
        gp.return_value = 100.0
        self.invoke(["buy", "AAPL"], inp="10\ny\n")
        gp.return_value = 200.0
        self.invoke(["buy", "AAPL"], inp="10\ny\n")
        pos = storage.get_current_game()["holdings"]["AAPL"]
        self.assertEqual(pos, {"shares": 20, "avg_cost": 150.0})
        gp.return_value = 210.0
        res = self.invoke(["sell", "AAPL"], inp="20\ny\n")
        self.assertEqual(res.exit_code, 0, res.output)
        game = storage.get_current_game()
        self.assertNotIn("AAPL", game["holdings"])
        self.assertEqual(game["cash"], 10000 - 1000 - 2000 + 4200)
        self.assertEqual(game["transactions"][-1]["realized_pl"], 1200.0)

    def test_sell_unheld_fails(self):
        self.new_game()
        res = self.invoke(["sell", "AAPL"])
        self.assertNotEqual(res.exit_code, 0)

    @mock.patch("marketcl.cli.get_prices", return_value={"AAPL": 120.0})
    @mock.patch("marketcl.cli.get_price", return_value=100.0)
    def test_list_and_alias(self, *_):
        self.new_game()
        self.invoke(["buy", "AAPL"], inp="10\ny\n")
        for cmd in ("list", "l"):
            res = self.invoke([cmd])
            self.assertEqual(res.exit_code, 0, res.output)

    @mock.patch("marketcl.cli.get_price", return_value=100.0)
    def test_buy_and_sell_aliases(self, _):
        self.new_game()
        res = self.invoke(["b", "aapl"], inp="4\ny\n")
        self.assertEqual(res.exit_code, 0, res.output)
        self.assertEqual(storage.get_current_game()["holdings"]["AAPL"]["shares"], 4)
        res = self.invoke(["s", "aapl"], inp="4\ny\n")
        self.assertEqual(res.exit_code, 0, res.output)
        self.assertEqual(storage.get_current_game()["holdings"], {})

    @mock.patch("marketcl.cli.get_price", return_value=100.0)
    def test_buy_prompts_for_symbol(self, _):
        self.new_game()
        # blank entry is re-prompted, then a symbol, quantity, confirm
        res = self.invoke(["b"], inp="\nmsft\n2\ny\n")
        self.assertEqual(res.exit_code, 0, res.output)
        self.assertIn("Symbol", res.output)
        self.assertEqual(storage.get_current_game()["holdings"]["MSFT"]["shares"], 2)

    @mock.patch("marketcl.cli.get_price", return_value=100.0)
    def test_sell_prompts_for_symbol(self, _):
        self.new_game()
        self.invoke(["b", "MSFT"], inp="3\ny\n")
        res = self.invoke(["s"], inp="msft\n3\ny\n")
        self.assertEqual(res.exit_code, 0, res.output)
        self.assertEqual(storage.get_current_game()["holdings"], {})

    @mock.patch("marketcl.cli.get_prices", return_value={})
    def test_output_ends_with_blank_line(self, _):
        self.new_game()
        for args in (["list"], ["--help"], ["game", "nope"], ["sell", "AAPL"]):
            res = self.invoke(args)
            self.assertTrue(res.output.endswith("\n\n"), (args, repr(res.output[-30:])))

    def test_no_game_error(self):
        res = self.invoke(["list"])
        self.assertNotEqual(res.exit_code, 0)
        self.assertIn("No active game", res.output)


if __name__ == "__main__":
    unittest.main()
