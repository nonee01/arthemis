import sys
import pathlib

# Make the 'arthemis' package importable by putting its parent dir on sys.path.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
