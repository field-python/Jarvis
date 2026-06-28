# Jarvis

A fully offline, locally-run AI assistant inspired by Iron Man's J.A.R.V.I.S. Runs on your own hardware with no internet required, no API keys, no subscriptions. Built on [Ollama](https://ollama.com) + Qwen3 with a custom personality.

> *"Good evening, sir."*

---

## What it does

- Ask questions, get answers — fast, offline, no tracking
- Voice mode with wake word ("Hey Jarvis"), local speech-to-text and text-to-speech
- Web UI accessible from your phone or any device on your network
- Offline knowledge base: survival docs, sacred texts, declassified files, classic literature, harm reduction, reloading data, and more
- Casino games, trivia, word games — all playable in the terminal
- Morning briefings, weather, news, timers, reminders, notes
- Coding assistant and interactive lessons
- Stock watchlist with ASCII charts

---

## Requirements

- Linux (primary) or macOS
- [Ollama](https://ollama.com) installed
- Python 3.10+
- ~8GB free RAM (for the 8B model)

---

## Install

```bash
# 1. Pull the base model
ollama pull qwen3:latest
ollama pull qwen2.5-coder:7b      # optional, for Jarvis code / learn

# 2. Clone the repo
git clone https://github.com/field-python/Jarvis.git
cd Jarvis

# 3. Run setup (creates venv, installs packages, builds Jarvis model, adds launcher)
bash setup.sh
```

After setup, `Jarvis` is available as a command from anywhere.

---

## Commands

### Ask & Chat
| Command | What it does |
|---|---|
| `Jarvis "question"` | Ask anything |
| `Jarvis brief "question"` | Short answer |
| `Jarvis detailed "question"` | Long-form answer |
| `Jarvis cite "question"` | Answer with knowledge base citations |
| `Jarvis chat` | Conversation mode with memory |
| `Jarvis menu` | Arrow-key interactive menu of all commands |

### Voice
| Command | What it does |
|---|---|
| `Jarvis voice` | Wake word mode — say "Hey Jarvis" |
| `Jarvis convo` | Continuous conversation, no wake word |
| `Jarvis set-voice` | Choose from 6 voices |

### Info & Tools
| Command | What it does |
|---|---|
| `Jarvis weather [city]` | Current conditions + 3-day forecast |
| `Jarvis news [category]` | Headlines summarized aloud |
| `Jarvis daily` | Morning briefing: weather + news |
| `Jarvis timer 10m` | Countdown with spoken alerts |
| `Jarvis stocks [TICKER]` | Watchlist + ASCII chart |
| `Jarvis note "text"` | Save a quick note |
| `Jarvis web "question"` | DuckDuckGo search, summarized |

### Knowledge Base
| Command | What it does |
|---|---|
| `Jarvis holybooks` | Browse sacred texts (Bible, Quran, Torah, Gita, etc.) |
| `Jarvis classics` | Classic literature library (60+ books) |
| `Jarvis erowid [substance]` | Harm reduction reference |
| `Jarvis search "keyword"` | Keyword search local knowledge base |
| `Jarvis find "topic"` | Semantic search via ChromaDB |

### Coding
| Command | What it does |
|---|---|
| `Jarvis code "task"` | Generate code (qwen2.5-coder), self-correcting |
| `Jarvis learn "topic"` | Interactive step-by-step coding lesson |

### Games
| Command | What it does |
|---|---|
| `Jarvis blackjack` | Blackjack with split, double down, chip system |
| `Jarvis poker` | Texas Hold'em heads-up vs Jarvis AI |
| `Jarvis slots` | Animated slot machine |
| `Jarvis roulette` | Full roulette with all bet types |
| `Jarvis yahtzee` | Full Yahtzee |
| `Jarvis connectfour` | Connect Four vs AI (minimax) |
| `Jarvis scores` | High score leaderboard |

---

## Web UI (Jarvis Mobile)

```bash
Jarvis web
```

Runs a Flask server on port 5000. Access from any device on your network. PIN protected, dark theme, mobile-first. Mic button uses local Whisper for speech-to-text — no Google, no cloud.

To auto-start at boot:
```bash
systemctl --user enable jarvis-web.service
```

---

## Voice Setup

Voice mode requires a few extra packages. Run the installer:

```bash
bash scripts/install-voice.sh
```

Installs: faster-whisper (STT), Piper (TTS), openWakeWord (wake word detection).

---

## Knowledge Base

The `index/source-packages/` folder contains curated reference files covering: survival, wilderness medicine, Alaska hunting/fishing/trapping, off-grid power, ham radio, carpentry, firearms, food storage, coding, chemistry, and more.

The `erowid/` folder contains harm reduction reference files for 17 substances in a browsable offline format.

Sacred texts, classic literature, and declassified government documents can be downloaded with the included download scripts in `scripts/`.

---

## Models

Jarvis runs on a custom Qwen3 8B Modelfile (`Jarvis.Modelfile`) with a tuned personality: calm, dry British wit, direct answers, no moralizing. The coding assistant uses qwen2.5-coder:7b.

---

## Project Structure

```
jarvis/
├── scripts/          # All feature scripts
├── erowid/           # Harm reduction reference files
├── docs/             # Offline survival documentation
├── index/            # Knowledge base source packages
├── profiles/         # Situational response profiles
├── templates/        # Web UI HTML templates
├── static/           # Web UI assets
├── voice/            # Voice model files (downloaded locally)
├── notes/            # Personal notes + knowledge base (gitignored)
├── config/           # Local config + SSL certs (gitignored)
├── memory/           # Jarvis user memory (gitignored)
├── Jarvis.Modelfile  # Custom Ollama model definition
├── jarvis.py         # Main Python launcher
└── setup.sh          # One-command installer
```

---

## License

MIT — free to use, modify, and share.
