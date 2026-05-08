from django.shortcuts import render
import requests
from datetime import datetime
import json


def parse_lichess_time(value):
    """
    Handles both ISO strings and UNIX timestamps (seconds or milliseconds).
    """
    if not value:
        return None

    # UNIX timestamp (int or float)
    if isinstance(value, (int, float)):
        # convert ms → s if needed
        if value > 1e12:
            value = value / 1000
        return datetime.fromtimestamp(value)

    # ISO string
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    return None


def home(request):
    context = {
        "username": "",
        "raw_user": None,
        "user_found": False,
        "error": None,

        "rapid": {"rating": None, "games": None, "rd": None, "prog": None},
        "blitz": {"rating": None, "games": None, "rd": None, "prog": None},
        "bullet": {"rating": None, "games": None, "rd": None, "prog": None},

        "play_time": None,
        "created_date": None,
        "last_seen": None,
        "flair_url": None,

        "recent_games": None,
    }

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        context["username"] = username

        # reset
        context["rapid"] = {}
        context["blitz"] = {}
        context["bullet"] = {}
        context["user_found"] = False
        context["raw_user"] = None
        context["play_time"] = None
        context["created_date"] = None
        context["last_seen"] = None
        context["flair_url"] = None
        context["recent_games"] = None

        try:
            url = f"https://lichess.org/api/user/{username}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                raise Exception("User not found")

            user = response.json()
            perfs = user.get("perfs", {})

            # ratings data
            context["blitz"] = perfs.get("blitz", {})
            context["rapid"] = perfs.get("rapid", {})
            context["bullet"] = perfs.get("bullet", {})

            context["user_found"] = True
            context["raw_user"] = user

            # -----------------------
            # Play time formatting
            # -----------------------
            play_time_seconds = user.get("playTime", {}).get("total")
            if play_time_seconds is not None:
                days = play_time_seconds // 86400
                hours = (play_time_seconds % 86400) // 3600
                minutes = (play_time_seconds % 3600) // 60
                seconds = play_time_seconds % 60
                context["play_time"] = f"{days}d {hours}h {minutes}m {seconds}s"

            # -----------------------
            # Flair
            # -----------------------
            flair_name = user.get("flair")
            if flair_name:
                context["flair_url"] = (
                    "https://lichess1.org/assets/______4/flair/img/"
                    + flair_name
                    + ".webp"
                )

            # -----------------------
            # Created / last seen
            # -----------------------
            created_at = user.get("createdAt")
            seen_at = user.get("seenAt")

            created_dt = parse_lichess_time(created_at)
            seen_dt = parse_lichess_time(seen_at)

            if created_dt:
                context["created_date"] = created_dt.strftime(
                    "%B %d, %Y - %I:%M %p %Z"
                )

            if seen_dt:
                context["last_seen"] = seen_dt.strftime(
                    "%B %d, %Y - %I:%M %p %Z"
                )

            ###############
            # -----------------------
            # Recent games
            # -----------------------

            games_url = (
                f"https://lichess.org/api/games/user/{username}"
                "?max=5&pgnInJson=true"
            )

            headers = {
                "Accept": "application/x-ndjson"
            }

            games_response = requests.get(
                games_url,
                headers=headers,
                timeout=10
            )

            games = []

            if games_response.status_code == 200:

                lines = games_response.text.strip().split("\n")

                for line in lines:

                    if not line.strip():
                        continue

                    game = json.loads(line)

                    players = game.get("players", {})

                    white = players.get("white", {}).get("user", {}).get("name", "Anonymous")
                    black = players.get("black", {}).get("user", {}).get("name", "Anonymous")

                    winner = game.get("winner", "draw")

                    status = game.get("status", "unknown")

                    speed = game.get("speed", "unknown")

                    game_id = game.get("id")

                    games.append({
                        "id": game_id,
                        "white": white,
                        "black": black,
                        "winner": winner,
                        "status": status,
                        "speed": speed.capitalize(),
                    })

                    context["recent_games"] = games

        ### SHOW ERROR
        except Exception as e:
            context["error"] = str(e)

    return render(request, "dashboard/home.html", context)
    # Returns info to the HTML home page