# Bangladesh Social Data Atlas

An interactive Bangladesh district atlas exploring two indicators from BBS/UNICEF MICS 2019:

1. Participation in organized learning
2. Percentage of women aged 20–24 who were first married before age 18

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Data

`data/bangladesh_social_indicators_2019.csv` contains the 64 district-level direct and small-area estimates reproduced from the BBS/UNICEF report.

You must add the district boundary GeoJSON yourself at:

`data/bangladesh_districts.geojson`

Recommended source: Bangladesh administrative boundaries at ADM2/district level, such as the repository documented in the project instructions.

## Important methodological note

The education variable is **participation in organized learning**, not literacy or school completion. The project treats the two variables as an exploratory geographic comparison. It does not claim that education causes or prevents child marriage.

## Suggested next improvements

- Add a Bangladesh division filter.
- Add a toggle between direct and SAE estimates.
- Add district search.
- Add a second map for child marriage before age 15.
- Add female literacy from the 2022 Population and Housing Census as a separate indicator.
- Add a methodology page explaining MICS and small-area estimation.
