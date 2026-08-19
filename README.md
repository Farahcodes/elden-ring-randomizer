# Elden Ring Randomizer

Small Streamlit app to generate randomized Elden Ring builds from CSV data files.


## Quick start
1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt --user
```

2. Run the Streamlit UI:

```bash
streamlit run generateur_build.py
```

3. Run tests:

```bash
python3 -m pytest -q
```

## Data files
Place the following CSV files next to `generateur_build.py`:

- `Main Hand.csv`
- `Second Hand.csv`
- `Magic.csv`
- `Armor.csv` (supports `Armor Sets` and `Armor Pieces` rows; `Bonus` column is used for magic synergy)
- `Spirit.csv`
- `Tools.csv` (optional)

The generator filters rows using the `leveled` column where applicable. See the CSV examples in the repo for exact headers.

