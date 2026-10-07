

The required Python packages are listed in `pyproject.toml`.



## Setup

From the project directory, create and activate a virtual environment:

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

### Linux 

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Run

``` bash
python game.py
```

Choose one of the four starting layouts with `--layout` (layout 1 is the default):

```bash
python game.py --layout 2
```

## Controls


- `W`, `A`, `S`, `D`: Move the player
- Mouse: Drag nearby table-setting items
- `E`: Place the carried item when it is in a valid location
- `C`: Open the robot assistant menu
- `Esc`: Close the robot assistant menu
- Close the game window: Exit

## Project Files

- `game.py`: Main game program
- `pyproject.toml`: Python version and dependency configuration
- `assests/`: Game images
- `Default/`: UI images
- `individual sprites/`: Additional sprite assets
- `Kenney Future Narrow.ttf`: Game font
