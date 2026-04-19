#!/usr/bin/env python3
"""
download-knowledge-expansion.py — Massive knowledge base expansion for Jarvis.
Downloads Wikipedia content across science, history, philosophy, mythology,
psychology, economics, geography, art, languages, technology, nature, food,
military, sports, and crime.

Usage:
  python download-knowledge-expansion.py              # all categories
  python download-knowledge-expansion.py science      # one category
  python download-knowledge-expansion.py --force      # re-download existing
  python download-knowledge-expansion.py science --force
"""

import json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

BASE_DIR   = Path(__file__).parent.parent.resolve()
NOTES_DIR  = BASE_DIR / "notes" / "generated"
FORCE      = "--force" in sys.argv
BATCH      = next((int(sys.argv[i+1]) for i, a in enumerate(sys.argv) if a == "--batch" and i+1 < len(sys.argv)), 0)
CATEGORIES = [a for a in sys.argv[1:] if not a.startswith("-") and not a.isdigit()] or ["all"]

_downloaded = 0  # global counter for batch mode

# ── Wikipedia fetch ────────────────────────────────────────────────────────────
def fetch_wiki(title):
    params = urllib.parse.urlencode({
        "action": "query", "prop": "extracts", "explaintext": True,
        "exsectionformat": "plain", "titles": title,
        "format": "json", "exlimit": 1,
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "JarvisOfflineAssistant/1.0 (offline AI; personal use)"
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            if not pages: return None
            page = next(iter(pages.values()))
            if page.get("pageid", -1) == -1: return None
            text = page.get("extract", "").strip()
            return text if len(text) > 200 else None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 * (2 ** attempt)
                print(f"    rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    warn: {title}: {e}")
                return None
        except Exception as e:
            print(f"    warn: {title}: {e}")
            return None
    return None

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def save(subdir, filename, title, content):
    out_dir = NOTES_DIR / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    if path.exists() and not FORCE:
        print(f"  skip (exists): {path.name}")
        return False
    text = f"# {title}\n\n{content}\n"
    path.write_text(text, encoding="utf-8")
    print(f"  saved: {subdir}/{path.name}  ({len(content):,} chars)")
    return True

def download_topic(subdir, wiki_title, filename=None):
    global _downloaded
    if BATCH and _downloaded >= BATCH:
        return
    fn = filename or (slugify(wiki_title) + ".md")
    out_path = NOTES_DIR / subdir / fn
    if out_path.exists() and not FORCE:
        return  # skip silently in batch mode
    content = fetch_wiki(wiki_title)
    if content:
        if save(subdir, fn, wiki_title, content):
            _downloaded += 1
    else:
        print(f"  miss: {wiki_title}")
    if BATCH and _downloaded >= BATCH:
        return
    time.sleep(2.0)

# ── Topic map ──────────────────────────────────────────────────────────────────
TOPICS = {

# ════════════════════════════════════════════════════════════════════════════════
"science": {
    "astronomy": [
        "Astronomy", "Solar System", "Sun", "Moon", "Planet",
        "Milky Way", "Galaxy", "Star", "Black hole", "Neutron star",
        "Supernova", "Nebula", "Big Bang", "Dark matter", "Dark energy",
        "Exoplanet", "Hubble Space Telescope", "James Webb Space Telescope",
        "Space exploration", "Cosmology", "Light-year", "Constellation",
        "Asteroid", "Comet", "Meteor", "International Space Station",
    ],
    "biology": [
        "Biology", "Evolution", "Natural selection", "Genetics",
        "DNA", "Cell (biology)", "Photosynthesis", "Ecosystem",
        "Food chain", "Taxonomy (biology)", "Animal", "Mammal",
        "Reptile", "Amphibian", "Insect", "Bird", "Fish",
        "Fungi", "Bacteria", "Virus", "Immune system",
        "Human body", "Anatomy", "Physiology", "Ecology",
        "Biodiversity", "Endangered species", "Extinction",
    ],
    "geology": [
        "Geology", "Plate tectonics", "Earthquake", "Volcano",
        "Rock (geology)", "Mineral", "Fossil", "Geological time scale",
        "Continental drift", "Mountain", "Cave", "Glacier",
        "Erosion", "Sediment", "Soil science", "Geomorphology",
    ],
    "meteorology": [
        "Meteorology", "Weather", "Climate", "Atmosphere of Earth",
        "Hurricane", "Tornado", "Thunderstorm", "Blizzard",
        "Drought", "Flood", "Lightning", "Wind", "Precipitation",
        "Humidity", "Cloud", "Climate change", "Weather forecasting",
    ],
    "oceanography": [
        "Oceanography", "Ocean", "Pacific Ocean", "Atlantic Ocean",
        "Indian Ocean", "Arctic Ocean", "Deep sea", "Coral reef",
        "Ocean current", "Tide", "Wave", "Marine biology",
        "Whale", "Shark", "Dolphin", "Jellyfish", "Bioluminescence",
    ],
    "mathematics": [
        "Mathematics", "Algebra", "Geometry", "Calculus",
        "Statistics", "Number theory", "Prime number", "Pi",
        "Fibonacci number", "Pythagorean theorem", "Probability",
        "Logic", "Set theory", "Linear algebra", "Differential equation",
        "Famous mathematicians", "History of mathematics",
    ],
    "physics": [
        "Physics", "Quantum mechanics", "Theory of relativity",
        "Thermodynamics", "Electromagnetism", "Newton's laws of motion",
        "Gravity", "Atomic theory", "Nuclear physics", "Particle physics",
        "Standard Model", "String theory", "Higgs boson",
        "Speed of light", "Energy", "Force", "Wave",
    ],
    "chemistry": [
        "Chemistry", "Periodic table", "Chemical element",
        "Chemical reaction", "Acid–base reaction", "Organic chemistry",
        "Biochemistry", "Polymer", "Chemical bond", "Atom",
        "Molecule", "Electron", "Isotope", "Radioactivity",
    ],
    "neuroscience": [
        "Neuroscience", "Brain", "Neuron", "Neurotransmitter",
        "Consciousness", "Memory", "Sleep", "Neuroplasticity",
        "Dopamine", "Serotonin", "Prefrontal cortex", "Limbic system",
        "Pain", "Addiction neuroscience", "Dreaming",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"history": {
    "ancient-egypt": [
        "Ancient Egypt", "Pharaoh", "Egyptian pyramid", "Mummy",
        "Egyptian hieroglyphs", "Cleopatra", "Ramesses II",
        "Tutankhamun", "Ancient Egyptian religion", "Sphinx",
        "Valley of the Kings", "Egyptian mythology", "Nile River",
        "Ancient Egyptian technology", "Rosetta Stone",
    ],
    "ancient-rome": [
        "Ancient Rome", "Roman Republic", "Roman Empire",
        "Julius Caesar", "Augustus", "Roman Senate",
        "Gladiator", "Roman army", "Roman law", "Colosseum",
        "Roman mythology", "Marcus Aurelius", "Nero",
        "Fall of the Western Roman Empire", "Roman road",
        "Pompeii", "Roman engineering",
    ],
    "ancient-greece": [
        "Ancient Greece", "Athens", "Sparta", "Democracy",
        "Olympic Games (ancient)", "Alexander the Great",
        "Peloponnesian War", "Persian Wars", "Socrates",
        "Plato", "Aristotle", "Greek mythology", "Homer",
        "Parthenon", "Ancient Greek philosophy", "Hellenistic period",
    ],
    "mesopotamia": [
        "Mesopotamia", "Sumer", "Babylon", "Assyria",
        "Code of Hammurabi", "Cuneiform", "Akkadian Empire",
        "Gilgamesh", "Hanging Gardens of Babylon",
        "Ziggurat", "Ancient Mesopotamian religion",
        "Ur (Mesopotamia)", "Fertile Crescent",
    ],
    "maya-aztec-inca": [
        "Maya civilization", "Aztec Empire", "Inca Empire",
        "Tenochtitlan", "Machu Picchu", "Maya calendar",
        "Quetzalcoatl", "Human sacrifice in Mesoamerica",
        "Spanish conquest of the Aztec Empire",
        "Spanish conquest of the Inca Empire",
        "Mesoamerican pyramids", "Mayan writing system",
    ],
    "vikings": [
        "Vikings", "Norse culture", "Viking Age",
        "Leif Eriksson", "Ragnar Lothbrok",
        "Viking longship", "Norse mythology",
        "Vinland", "Battle of Hastings", "Normans",
        "Scandinavia", "Viking raids", "Runic alphabet",
    ],
    "mongol-empire": [
        "Mongol Empire", "Genghis Khan", "Kublai Khan",
        "Mongol invasions", "Pax Mongolica",
        "Silk Road", "Battle of Mohi", "Golden Horde",
        "Timur", "Mongol military tactics",
    ],
    "byzantine-ottoman": [
        "Byzantine Empire", "Constantinople",
        "Justinian I", "Theodora (6th century)",
        "Ottoman Empire", "Suleiman the Magnificent",
        "Fall of Constantinople", "Ottoman–Habsburg wars",
        "Hagia Sophia", "Eastern Orthodox Church",
    ],
    "asian-history": [
        "History of China", "Silk Road", "Great Wall of China",
        "Tang dynasty", "Ming dynasty", "Qing dynasty",
        "History of Japan", "Samurai", "Feudal Japan",
        "Meiji Restoration", "Opium Wars", "Boxer Rebellion",
        "Chinese Civil War", "History of India", "Mughal Empire",
        "British Raj", "Korean War", "Vietnam War",
    ],
    "american-history": [
        "History of the United States", "American Revolution",
        "Declaration of Independence", "Founding Fathers",
        "American Civil War", "Reconstruction era",
        "Wild West", "Manifest Destiny", "Great Depression",
        "New Deal", "World War II United States home front",
        "Civil rights movement", "Cold War", "Space Race",
        "September 11 attacks", "History of Alaska",
    ],
    "african-history": [
        "History of Africa", "Mali Empire", "Kingdom of Kush",
        "Great Zimbabwe", "Scramble for Africa",
        "Atlantic slave trade", "Nelson Mandela",
        "Apartheid", "Decolonisation of Africa",
        "Carthage", "Ancient Egypt",
    ],
    "cold-war": [
        "Cold War", "Cuban Missile Crisis", "Berlin Wall",
        "Space Race", "Korean War", "Vietnam War",
        "McCarthyism", "NATO", "Warsaw Pact",
        "Détente", "Nuclear arms race",
        "Dissolution of the Soviet Union", "Iron Curtain",
    ],
    "industrial-revolution": [
        "Industrial Revolution", "Steam engine",
        "James Watt", "Cotton gin", "Railway",
        "Child labour in the Industrial Revolution",
        "Urbanization", "Capitalism", "Karl Marx",
        "Labor movement", "Luddite", "Victorian era",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"philosophy": {
    "ancient-philosophy": [
        "Socrates", "Plato", "Aristotle",
        "Pre-Socratic philosophy", "Sophist",
        "Epicureanism", "Cynicism (philosophy)",
        "Skepticism", "Platonic idealism", "Aristotelian logic",
    ],
    "stoicism": [
        "Stoicism", "Marcus Aurelius", "Epictetus",
        "Seneca the Younger", "Zeno of Citium",
        "Meditations (Marcus Aurelius)", "Virtue ethics",
        "Logos (philosophy)", "Apatheia",
    ],
    "modern-philosophy": [
        "René Descartes", "John Locke", "Immanuel Kant",
        "David Hume", "Friedrich Nietzsche",
        "Georg Wilhelm Friedrich Hegel",
        "Arthur Schopenhauer", "Baruch Spinoza",
        "John Stuart Mill", "Utilitarianism",
    ],
    "existentialism": [
        "Existentialism", "Jean-Paul Sartre",
        "Albert Camus", "Søren Kierkegaard",
        "Simone de Beauvoir", "Martin Heidegger",
        "Absurdism", "Nihilism", "Phenomenology",
        "Bad faith (existentialism)", "Authenticity (philosophy)",
    ],
    "eastern-philosophy": [
        "Eastern philosophy", "Confucianism", "Taoism",
        "Buddhism", "Zen", "Hindu philosophy",
        "Jainism", "Legalism (Chinese philosophy)",
        "Mohism", "I Ching",
    ],
    "ethics-political": [
        "Ethics", "Moral philosophy", "Deontological ethics",
        "Consequentialism", "Social contract",
        "Thomas Hobbes", "Jean-Jacques Rousseau",
        "Political philosophy", "Anarchism",
        "Communism", "Libertarianism", "Democracy",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"mythology": {
    "norse-mythology": [
        "Norse mythology", "Odin", "Thor", "Loki",
        "Freya", "Ragnarök", "Yggdrasil", "Nine Worlds",
        "Asgard", "Valhalla", "Valkyrie", "Fenrir",
        "Jörmungandr", "Dwarves in Norse mythology",
        "Eddas", "Prose Edda",
    ],
    "greek-mythology": [
        "Greek mythology", "Zeus", "Hera", "Poseidon",
        "Athena", "Apollo", "Artemis", "Ares",
        "Hermes", "Hephaestus", "Aphrodite", "Hades",
        "Trojan War", "Odysseus", "Heracles",
        "Perseus", "Medusa", "Achilles", "Prometheus",
        "Olympians", "Titans (mythology)",
    ],
    "egyptian-mythology": [
        "Egyptian mythology", "Ra (Egyptian deity)",
        "Osiris", "Isis", "Horus", "Set (deity)",
        "Anubis", "Thoth", "Afterlife in ancient Egyptian belief",
        "Book of the Dead", "Duat", "Ma'at",
    ],
    "celtic-norse-roman": [
        "Celtic mythology", "Druid",
        "Arthurian legend", "King Arthur",
        "Roman mythology", "Jupiter (mythology)",
        "Mars (mythology)", "Venus (mythology)",
        "Aeneid", "Romulus and Remus",
        "Slavic mythology", "Aztec mythology",
        "Inca mythology",
    ],
    "world-mythology": [
        "Hindu mythology", "Ramayana", "Mahabharata",
        "Vishnu", "Shiva", "Brahma", "Ganesha",
        "Sumerian religion", "Enuma Elish",
        "Native American mythology",
        "Aboriginal Australian mythology",
        "Japanese mythology", "Amaterasu",
        "Chinese mythology", "Creation myth",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"psychology": {
    "cognitive-psychology": [
        "Cognitive psychology", "Memory", "Attention",
        "Perception", "Language", "Problem solving",
        "Decision-making", "Cognitive bias",
        "Working memory", "Cognitive load",
        "Mental model", "Heuristics in judgment and decision-making",
    ],
    "social-psychology": [
        "Social psychology", "Conformity", "Obedience to authority",
        "Milgram experiment", "Stanford prison experiment",
        "Bystander effect", "Social influence",
        "Groupthink", "Persuasion", "Stereotypes",
        "In-group favoritism", "Cognitive dissonance",
    ],
    "personality-developmental": [
        "Personality psychology", "Big Five personality traits",
        "Myers–Briggs Type Indicator", "Carl Jung",
        "Archetypes", "Sigmund Freud", "Psychoanalysis",
        "Developmental psychology", "Jean Piaget",
        "Erik Erikson", "Attachment theory",
        "Maslow's hierarchy of needs",
    ],
    "behavioral-abnormal": [
        "Behavioral psychology", "Classical conditioning",
        "Operant conditioning", "Ivan Pavlov",
        "B. F. Skinner", "Reinforcement",
        "Abnormal psychology", "Diagnostic and Statistical Manual of Mental Disorders",
        "Depression (mood)", "Anxiety disorder",
        "Post-traumatic stress disorder", "Schizophrenia",
        "Bipolar disorder", "Borderline personality disorder",
    ],
    "positive-forensic": [
        "Positive psychology", "Flow (psychology)",
        "Happiness", "Gratitude", "Resilience",
        "Emotional intelligence", "Mindfulness",
        "Forensic psychology", "Criminal psychology",
        "Offender profiling", "Psychopathy",
        "Narcissistic personality disorder",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"economics": {
    "macroeconomics": [
        "Macroeconomics", "Gross domestic product",
        "Inflation", "Monetary policy", "Fiscal policy",
        "Recession", "Central bank", "Federal Reserve",
        "Interest rate", "Unemployment",
        "International trade", "Balance of trade",
        "Keynesian economics", "Monetarism",
    ],
    "personal-finance-crypto": [
        "Personal finance", "Budgeting", "Saving",
        "Investment", "Compound interest",
        "Stock market", "Bond (finance)", "Mutual fund",
        "Index fund", "Real estate investing",
        "Cryptocurrency", "Bitcoin", "Blockchain",
        "Ethereum", "Decentralized finance",
    ],
    "economic-history-systems": [
        "Economic history", "Great Depression",
        "2008 financial crisis", "Capitalism",
        "Socialism", "Communism", "Mixed economy",
        "Adam Smith", "Karl Marx", "John Maynard Keynes",
        "Globalization", "World Trade Organization",
        "Behavioral economics", "Daniel Kahneman",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"geography": {
    "world-geography": [
        "Geography", "Continent", "Country",
        "Capital city", "United Nations member states",
        "Europe", "Asia", "Africa", "North America",
        "South America", "Australia (continent)", "Antarctica",
        "Amazon basin", "Sahara", "Himalaya",
        "Amazon River", "Nile", "Mississippi River",
        "Yangtze River", "Andes", "Alps", "Rocky Mountains",
    ],
    "biomes-climate": [
        "Biome", "Tropical rainforest", "Temperate forest",
        "Boreal forest", "Grassland", "Desert",
        "Tundra", "Wetland", "Coral reef",
        "Climate zone", "Köppen climate classification",
        "Arctic", "Antarctic", "Permafrost",
        "Monsoon", "El Niño–Southern Oscillation",
    ],
    "us-geography": [
        "United States", "Alaska", "Hawaii",
        "Great Plains", "Appalachian Mountains",
        "Great Lakes", "Mississippi River",
        "Grand Canyon", "Yellowstone National Park",
        "Death Valley", "Everglades",
        "American Southwest", "Pacific Northwest",
        "New England",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"art-culture": {
    "art-history": [
        "Art history", "Renaissance", "Baroque",
        "Impressionism", "Surrealism", "Abstract art",
        "Modern art", "Contemporary art", "Street art",
        "Leonardo da Vinci", "Michelangelo",
        "Rembrandt", "Claude Monet", "Vincent van Gogh",
        "Pablo Picasso", "Salvador Dalí", "Frida Kahlo",
        "Andy Warhol",
    ],
    "architecture": [
        "Architecture", "Ancient Greek architecture",
        "Roman architecture", "Gothic architecture",
        "Renaissance architecture", "Baroque architecture",
        "Art Deco", "Modernist architecture",
        "Frank Lloyd Wright", "Le Corbusier",
        "Skyscraper", "Bridge", "Seven Wonders of the Ancient World",
    ],
    "music-theory-history": [
        "Music theory", "Scale (music)", "Chord (music)",
        "Rhythm", "Harmony", "Melody",
        "Johann Sebastian Bach", "Wolfgang Amadeus Mozart",
        "Ludwig van Beethoven", "Frédéric Chopin",
        "History of music", "Blues", "Jazz history",
        "Rock music history", "Hip hop history",
    ],
    "film-photography": [
        "History of film", "Silent film", "Golden Age of Hollywood",
        "New Hollywood", "Film genre", "Academy Awards",
        "Stanley Kubrick", "Alfred Hitchcock",
        "Steven Spielberg", "Martin Scorsese",
        "Photography", "History of photography",
        "Ansel Adams", "Documentary photography",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"languages": {
    "linguistics": [
        "Linguistics", "Language", "Phonology",
        "Syntax", "Semantics", "Pragmatics",
        "Language acquisition", "Noam Chomsky",
        "Writing system", "Alphabet", "Logogram",
        "Language family", "Proto-Indo-European language",
        "Constructed language", "Sign language",
    ],
    "world-languages": [
        "List of languages by number of native speakers",
        "Mandarin Chinese", "Spanish language",
        "English language", "Arabic language",
        "Hindi", "Portuguese language",
        "Russian language", "Japanese language",
        "French language", "Latin", "Sanskrit",
        "Etymology", "Slang", "Dialect",
        "Endangered language",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"technology": {
    "computing-internet": [
        "History of computing", "Computer",
        "ENIAC", "History of the Internet",
        "World Wide Web", "Tim Berners-Lee",
        "Dot-com bubble", "Smartphone",
        "Social media", "Cloud computing",
        "Open-source software", "Linux kernel",
        "Apple Inc.", "Microsoft", "Google",
        "Amazon (company)", "Meta Platforms",
    ],
    "ai-cybersecurity": [
        "Artificial intelligence", "Machine learning",
        "Neural network", "Deep learning",
        "Large language model", "ChatGPT",
        "History of artificial intelligence",
        "Alan Turing", "Cybersecurity",
        "Hacker", "Malware", "Ransomware",
        "Encryption", "Cryptography",
        "Notable computer security incidents",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"nature": {
    "environment": [
        "Climate change", "Greenhouse gas",
        "Deforestation", "Biodiversity loss",
        "Ocean pollution", "Plastic pollution",
        "Renewable energy", "Solar power",
        "Wind power", "Conservation biology",
        "Endangered species", "Rewilding (conservation)",
        "National park", "Yellowstone National Park",
        "Amazon rainforest",
    ],
    "natural-disasters": [
        "Natural disaster", "Earthquake",
        "Tsunami", "Volcanic eruption",
        "Hurricane", "Tornado", "Wildfire",
        "Flood", "Drought", "Avalanche",
        "Blizzard", "Landslide",
        "1906 San Francisco earthquake",
        "2004 Indian Ocean earthquake and tsunami",
        "Hurricane Katrina",
    ],
    "animals": [
        "Wolf", "Brown bear", "Mountain lion",
        "Moose", "Caribou", "Bald eagle",
        "Great white shark", "Orca",
        "African elephant", "Lion",
        "Gorilla", "Chimpanzee",
        "Venomous snake", "Crocodile",
        "Migration (ecology)",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"food": {
    "world-cuisines": [
        "Italian cuisine", "French cuisine",
        "Japanese cuisine", "Chinese cuisine",
        "Mexican cuisine", "Indian cuisine",
        "Thai cuisine", "Mediterranean cuisine",
        "Middle Eastern cuisine", "Ethiopian cuisine",
        "Korean cuisine", "Greek cuisine",
        "American cuisine", "Barbecue",
    ],
    "nutrition-fermentation": [
        "Nutrition", "Macronutrient",
        "Protein", "Carbohydrate", "Fat",
        "Vitamin", "Mineral (nutrient)",
        "Metabolism", "Calorie",
        "Fermentation in food processing",
        "Bread", "Beer", "Wine",
        "Cheese", "Kimchi", "Kombucha",
        "History of chocolate", "History of coffee",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"military": {
    "military-history": [
        "Military history", "Battle of Thermopylae",
        "Battle of Marathon", "Siege of Troy",
        "Battle of Hastings", "Crusades",
        "Hundred Years' War", "Battle of Agincourt",
        "Siege of Vienna", "Napoleonic Wars",
        "Battle of Waterloo", "American Civil War battles",
        "World War I", "Battle of the Somme",
        "World War II", "D-Day", "Battle of Stalingrad",
        "Battle of Midway", "Gulf War", "War in Afghanistan",
    ],
    "military-strategy-weapons": [
        "Military strategy", "The Art of War",
        "Sun Tzu", "Carl von Clausewitz",
        "Blitzkrieg", "Guerrilla warfare",
        "Naval warfare", "Air warfare",
        "Nuclear weapon", "History of nuclear weapons",
        "Sword", "Bow and arrow",
        "Firearm", "Tank", "Aircraft carrier",
        "Famous generals", "Napoleon Bonaparte",
        "Erwin Rommel", "George S. Patton",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"sports": {
    "team-sports-history": [
        "History of American football", "Super Bowl",
        "History of baseball", "World Series",
        "History of basketball", "NBA Finals",
        "Association football history", "FIFA World Cup",
        "Ice hockey", "Stanley Cup",
        "Rugby", "Cricket",
        "Famous athletes",
    ],
    "combat-extreme": [
        "Boxing", "Muhammad Ali", "Mike Tyson",
        "Mixed martial arts", "Ultimate Fighting Championship",
        "Wrestling", "Judo", "Brazilian jiu-jitsu",
        "Extreme sport", "Skateboarding",
        "Snowboarding", "Surfing", "Rock climbing",
        "Base jumping", "Motocross",
    ],
    "olympics": [
        "Olympic Games", "Ancient Olympic Games",
        "Summer Olympic Games", "Winter Olympic Games",
        "Usain Bolt", "Michael Phelps",
        "Jesse Owens", "Nadia Comăneci",
        "Olympic records",
    ],
},

# ════════════════════════════════════════════════════════════════════════════════
"crime": {
    "famous-crimes": [
        "Jack the Ripper", "Al Capone",
        "Pablo Escobar", "Ted Bundy",
        "Charles Manson", "John Wayne Gacy",
        "Jeffrey Dahmer", "Zodiac Killer",
        "D. B. Cooper", "Unabomber",
        "Columbine High School massacre",
        "O. J. Simpson murder case",
        "Enron scandal", "Bernie Madoff",
    ],
    "criminal-justice": [
        "Criminal psychology", "Offender profiling",
        "Forensic science", "Fingerprint",
        "DNA profiling", "Lie detection",
        "Prison", "Capital punishment",
        "Criminal law", "Jury trial",
        "Rehabilitation (penology)",
        "Recidivism", "Organized crime",
        "Drug cartel", "Human trafficking",
    ],
},

}  # end TOPICS

# ── Runner ─────────────────────────────────────────────────────────────────────
def run_category(cat_name, cat_data):
    print(f"\n{'='*60}")
    print(f"  CATEGORY: {cat_name.upper()}")
    print(f"{'='*60}")
    for subcat, articles in cat_data.items():
        print(f"\n  [{subcat}]")
        for article in articles:
            download_topic(f"{cat_name}/{subcat}", article)

def main():
    if "all" in CATEGORIES:
        cats = list(TOPICS.keys())
    else:
        cats = [c for c in CATEGORIES if c in TOPICS]
        if not cats:
            print(f"Unknown categories: {CATEGORIES}")
            print(f"Available: {list(TOPICS.keys())}")
            return

    total_cats = len(cats)
    print(f"\nJarvis Knowledge Expansion")
    print(f"Categories: {', '.join(cats)}")
    print(f"Force re-download: {FORCE}")

    for i, cat in enumerate(cats, 1):
        print(f"\n({i}/{total_cats})", end="")
        run_category(cat, TOPICS[cat])

    print("\n\nDone. Run 'Jarvis rebuild-index' to index new content.\n")

if __name__ == "__main__":
    main()
