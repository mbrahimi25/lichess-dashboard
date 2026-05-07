from django.shortcuts import render
import berserk

client = berserk.Client()

def home(request):
    context = {
        "username": "",

        "rapid": {
            "rating": None,
            "games": None,
            "rd": None,
            "prog": None,
        },

        "blitz": {
            "rating": None,
            "games": None,
            "rd": None,
            "prog": None,
        },

        "bullet": {
            "rating": None,
            "games": None,
            "rd": None,
            "prog": None,
        },

        "user_found": False,
        "play_time": None,
        "created_date": None,
        "last_seen": None,
        "error": None,
        "flair_url": None,
        "raw_user": None,
    }

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        context["username"] = username

        # ALWAYS reset before fetching new user
        context["rapid"] = {}
        context["blitz"] = {}
        context["bullet"] = {}
        context["user_found"] = False
        context["raw_user"] = None
        context["play_time"] = None
        context["created_date"] = None
        context["last_seen"] = None
        context["flair_url"] = None

        try:
            user = client.users.get_public_data(username)
            perfs = user.get("perfs", {})

            context["blitz"] = perfs.get("blitz", {})
            context["rapid"] = perfs.get("rapid", {})
            context["bullet"] = perfs.get("bullet", {})

            context["user_found"] = True

            context["raw_user"] = user

            play_time_seconds = user.get("playTime", {}).get("total")
            if play_time_seconds:
                days = play_time_seconds // 86400
                hours = (play_time_seconds % 86400) // 3600
                minutes = (play_time_seconds % 3600) // 60
                seconds = play_time_seconds % 60
                context["play_time"] = f"{days}d {hours}h {minutes}m {seconds}s"

            # Formats the play time of the user in a readable format to be displayed in the web app

            flair_name = user.get("flair", {})
            if flair_name:
                context["flair_url"] = "https://lichess1.org/assets/______4/flair/img/" + flair_name + ".webp"
            # Sets the flair_url from the user's flair image, if they have one

            created_at = user.get("createdAt")
            seen_at = user.get("seenAt")

            if created_at:
                context["created_date"] = created_at.strftime("%B %d, %Y - %I:%M %p %Z")

            if seen_at:
                context["last_seen"] = seen_at.strftime("%B %d, %Y - %I:%M %p %Z")

            # Formats the dates the user was last seen at, and the date of their account creation, into a string

        except Exception:
            context["error"] = "User not found"

    return render(request, "dashboard/home.html", context)