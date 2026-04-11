#!/usr/bin/env python3
"""
download-pop-culture.py — Download pop culture, gaming, TV, movies, music, celebrities.
Run: Jarvis download-pop-culture [category|all] [--force]
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "notes", "generated", "pop-culture")

TOPICS = {
    "movies": [
        "History of film",
        "Academy Awards",
        "Action film",
        "Science fiction film",
        "Horror film",
        "Thriller film",
        "Drama film",
        "Comedy film",
        "Animated film",
        "Documentary film",
        "Superhero film",
        "Western film",
        "Film noir",
        "Stanley Kubrick",
        "Steven Spielberg",
        "Martin Scorsese",
        "Francis Ford Coppola",
        "Christopher Nolan",
        "Quentin Tarantino",
        "The Godfather",
        "Citizen Kane",
        "Star Wars",
        "Jurassic Park",
        "The Dark Knight",
        "Pulp Fiction",
        "Schindler's List",
        "Inception",
        "The Shawshank Redemption",
        "Forrest Gump",
        "Titanic (1997 film)",
        "Jaws (film)",
        "E.T. the Extra-Terrestrial",
        "The Silence of the Lambs (film)",
        "Fight Club (film)",
        "No Country for Old Men (film)",
        "Casablanca (film)",
        "Gone with the Wind (film)",
        "2001: A Space Odyssey",
        "Apocalypse Now",
        "The Matrix",
        "Goodfellas",
        "Blade Runner",
        "Alien (film)",
        "The Terminator",
    ],
    "tv": [
        "Television in the United States",
        "Streaming television",
        "Reality television",
        "Breaking Bad",
        "The Sopranos",
        "Game of Thrones",
        "The Wire",
        "Seinfeld",
        "The Simpsons",
        "Friends (TV series)",
        "The Office (American TV series)",
        "Parks and Recreation",
        "Stranger Things",
        "The Walking Dead",
        "Dexter (TV series)",
        "House (TV series)",
        "Lost (TV series)",
        "Twin Peaks",
        "True Detective",
        "Chernobyl (miniseries)",
        "Band of Brothers (miniseries)",
        "Planet Earth (TV series)",
        "American Horror Story",
        "South Park",
        "Family Guy",
        "Rick and Morty",
        "The Mandalorian",
        "Yellowstone (TV series)",
    ],
    "music-artists": [
        "Elvis Presley",
        "The Beatles",
        "Michael Jackson",
        "Bob Dylan",
        "David Bowie",
        "Prince (musician)",
        "Madonna (entertainer)",
        "Bruce Springsteen",
        "Eminem",
        "Jay-Z",
        "Tupac Shakur",
        "Notorious B.I.G.",
        "Johnny Cash",
        "Dolly Parton",
        "Jimi Hendrix",
        "Janis Joplin",
        "Jim Morrison",
        "Kurt Cobain",
        "Freddie Mercury",
        "Mick Jagger",
        "Bob Marley",
        "Frank Sinatra",
        "Miles Davis",
        "John Coltrane",
        "Chuck Berry",
        "Little Richard",
        "Aretha Franklin",
        "Ray Charles",
        "Stevie Wonder",
        "Whitney Houston",
        "Taylor Swift",
        "Beyoncé",
        "Kanye West",
        "Drake (musician)",
        "Nirvana (band)",
        "Radiohead",
        "Pink Floyd",
        "The Rolling Stones",
        "AC/DC",
        "Metallica",
        "Iron Maiden",
    ],
    "music-genres": [
        "Rock music",
        "Heavy metal music",
        "Hip hop music",
        "Country music",
        "Jazz",
        "Blues",
        "Soul music",
        "Punk rock",
        "Grunge",
        "Electronic music",
        "Reggae",
        "Gospel music",
        "Classical music",
        "Folk music",
        "R&B",
        "Alternative rock",
        "Pop music",
        "Disco",
        "Funk",
        "Psychedelic rock",
        "Death metal",
        "Rap music",
        "Trap music",
    ],
    "celebrities": [
        "Marilyn Monroe",
        "Audrey Hepburn",
        "Clark Gable",
        "James Dean",
        "Marlon Brando",
        "Elizabeth Taylor",
        "Jack Nicholson",
        "Robert De Niro",
        "Al Pacino",
        "Meryl Streep",
        "Tom Hanks",
        "Denzel Washington",
        "Brad Pitt",
        "Leonardo DiCaprio",
        "Johnny Depp",
        "Arnold Schwarzenegger",
        "Sylvester Stallone",
        "Clint Eastwood",
        "Morgan Freeman",
        "Robin Williams",
        "Jim Carrey",
        "Eddie Murphy",
        "Will Smith",
        "Dwayne Johnson",
        "Oprah Winfrey",
        "Howard Stern",
        "David Letterman",
        "Jay Leno",
    ],
    "gaming": [
        "Video game",
        "History of video games",
        "Nintendo",
        "PlayStation (console)",
        "Xbox (console)",
        "PC gaming",
        "Atari",
        "Sega",
        "Super Mario",
        "The Legend of Zelda",
        "Pokémon",
        "Minecraft",
        "Grand Theft Auto",
        "Call of Duty",
        "Halo (franchise)",
        "Doom (franchise)",
        "Tetris",
        "Pac-Man",
        "Space Invaders",
        "Pong",
        "World of Warcraft",
        "Counter-Strike",
        "Fortnite",
        "The Elder Scrolls",
        "Final Fantasy",
        "Dark Souls",
        "Resident Evil",
        "Metal Gear",
        "Mortal Kombat",
        "Street Fighter",
        "Sonic the Hedgehog",
        "Donkey Kong",
        "E-sports",
        "Video game industry",
        "Arcade game",
        "Role-playing video game",
        "First-person shooter",
        "Open world",
    ],
    "internet-culture": [
        "Internet meme",
        "YouTube",
        "TikTok",
        "Instagram",
        "Twitter",
        "Reddit",
        "Facebook",
        "Influencer marketing",
        "Podcast",
        "Streaming media",
        "Netflix",
        "Amazon Prime Video",
        "Disney+",
        "Twitch (service)",
        "OnlyFans",
        "Wikipedia",
        "4chan",
        "Viral video",
        "Social media",
        "Cancel culture",
        "Doomscrolling",
    ],
    "sports-stars": [
        "Michael Jordan",
        "LeBron James",
        "Kobe Bryant",
        "Muhammad Ali",
        "Mike Tyson",
        "Babe Ruth",
        "Willie Mays",
        "Mickey Mantle",
        "Hank Aaron",
        "Wayne Gretzky",
        "Tiger Woods",
        "Roger Federer",
        "Serena Williams",
        "Pelé",
        "Lionel Messi",
        "Cristiano Ronaldo",
        "Usain Bolt",
        "Michael Phelps",
        "Simone Biles",
        "Tom Brady",
        "Jerry Rice",
        "Joe Montana",
        "Emmitt Smith",
        "Walter Payton",
        "Shaquille O'Neal",
        "Magic Johnson",
        "Larry Bird",
        "Bill Russell",
        "Kareem Abdul-Jabbar",
    ],
}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def wiki_fetch(title, max_chars=5000):
    params = urllib.parse.urlencode({
        "action":         "query",
        "titles":         title,
        "prop":           "extracts",
        "explaintext":    "1",
        "exsectionformat":"plain",
        "format":         "json",
        "redirects":      "1",
        "exchars":        str(max_chars),
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "JarvisOfflineAssistant/1.0 (offline AI; personal use)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data  = json.loads(r.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
        page = next(iter(pages.values()))
        if page.get("pageid", -1) == -1:
            return None
        text = page.get("extract", "").strip()
        return text if len(text) > 150 else None
    except Exception as e:
        print(f"    warn: {title}: {e}")
        return None


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    force  = "--force" in sys.argv

    if target == "all":
        cats = list(TOPICS.keys())
    elif target in TOPICS:
        cats = [target]
    else:
        print(f"Unknown category: {target}")
        print(f"Available: {', '.join(TOPICS.keys())}, all")
        sys.exit(1)

    grand_total = 0
    for cat in cats:
        out_dir = os.path.join(OUTPUT_DIR, cat)
        os.makedirs(out_dir, exist_ok=True)
        pages = TOPICS[cat]
        print(f"\n[{cat.upper()}]  {len(pages)} topics  →  {out_dir}")

        for title in pages:
            slug     = slugify(title)
            out_path = os.path.join(out_dir, f"{slug}.md")

            if os.path.exists(out_path) and not force:
                print(f"  skip  {title}")
                continue

            print(f"  fetch {title}...", end=" ", flush=True)
            text = wiki_fetch(title)
            if not text:
                print("not found")
                continue

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n*Source: Wikipedia*\n\n{text}\n")
            print(f"ok ({len(text):,} chars)")
            grand_total += 1
            time.sleep(0.3)

    print(f"\nDone — {grand_total} articles downloaded.")
    print("Run 'Jarvis rebuild-index' to make them searchable.")


if __name__ == "__main__":
    main()
