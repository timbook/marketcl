import os
import re
import sys
import json
from startup import make_game

def list_games(mcl_path, return_names=False):
    game_names = [re.sub("(game-|\.json)", "", file)
                  for file in os.listdir(mcl_path)
                  if file.startswith("game-")]

    print()
    print("ONGOING GAMES:")
    print("==============")
    print('\n'.join(game_names))
    print()

    if return_names:
        return game_names

def switch_game(mcl_path):
    config_file = os.path.join(mcl_path, "config.json")

    with open(config_file, 'r') as f:
        config = json.load(f)

    games = list_games(mcl_path, return_names=True)
    name = input("Which game would you like to switch to? ").lower()
    if name in games:
        config["current"] = name
        with open(config_file, 'w') as f:
            json.dump(config, f)
    else:
        print(f"Game file does not exist for {name}! Did you make a typo?")
        sys.exit(1)

def rm_game(mcl_path):
    games = list_games(mcl_path, return_names=True)
    name = input("Which game would you like to delete? ").lower()
    if name in games:
        ans = input(f"Are you sure you want to delete {name}'s game? (Y/n) ")
        if ans == "Y":
            file_rm = os.path.join(mcl_path, f"game-{name}.json")
            print(f"Deleting {file_rm}...\n")
            os.remove(file_rm)
        else:
            print("Close call! Exiting...\n")
            sys.exit(0)

def parse_game_arg(opt, mcl_path):
    game_dispatch = {
        "new":    make_game,
        "ls":     list_games,
        "switch": switch_game,
        "rm":    rm_game
    }

    game_dispatch[opt](mcl_path)
