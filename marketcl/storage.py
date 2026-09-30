"""JSON persistence for games. Everything lives in ~/.mcl (override with $MCL_HOME)."""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

Game = Dict[str, Any]


def home() -> Path:
    path = Path(os.environ.get("MCL_HOME", Path.home() / ".mcl"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def games_dir() -> Path:
    path = home() / "games"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _config_path() -> Path:
    return home() / "config.json"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug


def _write_json(path: Path, data: Any) -> None:
    """Atomic write so a crash never leaves a half-written file."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _read_json(path: Path, default: Any) -> Any:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


# ---------------------------------------------------------------- games

def game_exists(name: str) -> bool:
    return (games_dir() / f"{slugify(name)}.json").exists()


def create_game(name: str, initial_capital: float) -> Game:
    slug = slugify(name)
    if not slug:
        raise ValueError("Game name must contain letters or numbers.")
    if game_exists(name):
        raise ValueError(f"A game named '{name}' already exists.")
    game: Game = {
        "name": name.strip(),
        "slug": slug,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "initial_capital": round(float(initial_capital), 2),
        "cash": round(float(initial_capital), 2),
        "holdings": {},       # SYMBOL -> {"shares": int, "avg_cost": float}
        "transactions": [],   # chronological log of buys and sells
    }
    save_game(game)
    return game


def save_game(game: Game) -> None:
    _write_json(games_dir() / f"{game['slug']}.json", game)


def load_game(slug: str) -> Optional[Game]:
    return _read_json(games_dir() / f"{slug}.json", None)


def list_games() -> List[Game]:
    games = []
    for path in sorted(games_dir().glob("*.json")):
        game = _read_json(path, None)
        if game:
            games.append(game)
    games.sort(key=lambda g: g.get("created", ""))
    return games


# --------------------------------------------------------- current game

def get_current_slug() -> Optional[str]:
    return _read_json(_config_path(), {}).get("current_game")


def set_current_slug(slug: str) -> None:
    config = _read_json(_config_path(), {})
    config["current_game"] = slug
    _write_json(_config_path(), config)


def get_current_game() -> Optional[Game]:
    slug = get_current_slug()
    return load_game(slug) if slug else None
