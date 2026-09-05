# arthemis

A two-dimensional simulator of an Artemis-style free-return flyby: the
spacecraft leaves Earth, loops behind the Moon and comes back without an
insertion burn. What it is really about is the line of sight, since the
interesting part of a flyby is the stretch where the Moon sits between the
spacecraft and the only antenna that can hear it.

![Artemis 2 snapshot](snapshot.png)

Earth on the left, the Moon on the right, the dashed line the trajectory, the
orange dot the spacecraft and the cyan line the Earth-to-spacecraft path. When
that cyan line intersects the lunar disc the link is occulted, and
`check_los()` decides it with point-to-line geometry rather than by eye.

## Running it

```bash
pip install -r requirements.txt

python -m arthemis.main                        # animated, in a window
python -m arthemis.main --headless             # no GUI
python -m arthemis.render_snapshot             # one frame to snapshot.png
python -m arthemis.export_animation --out animation.mp4 --frames 240 --fps 24
```

The mission is parameterised rather than hard-coded, so the geometry can be
moved and the occultation re-checked:

```
--moon-x, --moon-y     where the Moon is (km)
--mission-days         how long the transit lasts
--flyby-altitude       how far past the lunar centre the ship passes
--frames               animation length
```

`export_animation` prefers system `ffmpeg` and falls back to a Pillow GIF.

## Real data, not just the model

- `arow_gcs_fetch.py` pulls the latest AROW telemetry from the public
  `p-2-cen1` Google Cloud Storage bucket and parses it.
- `live_simulator.py` queries JPL Horizons for real state vectors
  (`EPHEM_TYPE=VECTORS`, `CENTER=500`) and puts them behind a Streamlit page,
  so the modelled path can be held against an actual ephemeris.

## Tests

`tests/test_main.py` covers the part worth testing, which is the occultation
predicate: a spacecraft at the origin, one directly behind the Moon, and one
off-axis that should stay visible.

```bash
pytest
```

## Known gap

`main.py` calls `matplotlib.cm.get_cmap`, removed in matplotlib 3.9, so the
animation needs `matplotlib<3.9` until that call is replaced with
`matplotlib.colormaps[...]`.
