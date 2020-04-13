import os
import json

def startup_check(mcl_path):
    config_file = os.path.join(mcl_path, "config.json")

    # Dotfile check
    if not os.path.exists(mcl_path):
        print(f"marketcl directory not found, creating {mcl_path}")
        os.mkdir(mcl_path)

    # Config file check
    if not os.path.exists(config_file):
        print(f"config file not found, creating {config_file}")
        name = input("Starting a game. What is your name? ").lower()
        config = {"current": name}
        with open(config_file, 'w') as f:
            json.dump(config, f)
        make_game(mcl_path, name)

def make_game(mcl_path, name=None):
    if not name:
        name = input("Starting a game. What is your name? ").lower()

    print("STARTING NEW GAME")

    init_cash = input("How much cash would you like to start with (default is $10,000)? ")
    trade_fee = input("Enter a trading fee (default is $5): ")
    cap_gains_tax = input("Enter capital gains tax (default is 15%): ")

    def set_or_default(val, default):
        return default if val == "" else float(val)

    init_cash = set_or_default(init_cash, 10000.0)
    trade_fee = set_or_default(trade_fee, 5.0)
    cap_gains_tax = set_or_default(cap_gains_tax, 0.15)

    game_data = {
        "init_cash": init_cash,
        "cash": init_cash,
        "cap_gains_tax": cap_gains_tax,
        "trade_fee": trade_fee,
        "total_tax": 0,
        "total_fee": 0,
        "portfolio": []
    }

    game_file = os.path.join(mcl_path, f"game-{name}.json")    
    with open(game_file, 'w') as f:
        json.dump(game_data, f)

    print("Started a game for {} with ${:,.2f}!".format(name, init_cash))
