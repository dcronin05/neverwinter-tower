# Neverwinter Tower: Dedicated NWN Server Project

Welcome to **Neverwinter Tower**, a programmatically managed dedicated server project for *Neverwinter Nights: Enhanced Edition*.

---

## Project Structure
* `modules/`: Contains the `.mod` files loaded by the server. Currently loaded: `Neverwinter Chess.mod`.
* `servervault/`: Holds the server-side player character sheets (`.bic` files).
  * `servervault/khaun/`: Stash for player **Khaun** containing:
    * `daniel.bic`: A Level 1 Fighter named **Daniel**.
    * `neil.bic`: A Level 1 Rogue named **Neil**.
* `tools/`: Python utilities for managing raw GFF files.
  * `edit_char_name.py`: A pure Python utility that parses binary GFF files and renames `FirstName`/`LastName` values in LocStrings.
* `settings.tml`: The primary server configuration settings.
* `nwnplayer.ini`: INI options synced by the server.
* `.venv/`: The local virtual environment used for Python automation.

---

## Development Setup

### Python Virtual Environment
We run all project-related Python tasks inside a local virtual environment:
```powershell
# Create venv
python -m venv .venv
# Install dependencies (such as pynwn, once compilation tools are available)
.venv\Scripts\pip install pynwn
```

### Modifying Character Names
To create or rename a server vault character sheet from a pregenerated `.bic` file:
```powershell
.venv\Scripts\python tools\edit_char_name.py <input_path> <output_path> <first_name> [last_name]
```

### Git Branching Workflow
We version this repository using a strict development branch strategy:
1. Initialize the feature branch:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Commit your changes.
3. Merge back to the main branch using a non-fast-forward merge to preserve the branch commits:
   ```bash
   git checkout main
   git merge feat/your-feature --no-ff -m "merge: explanation of features integrated"
   ```
