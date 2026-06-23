# Jeewa Guru — Swiss Ephemeris Live Tester

Live birth chart calculator that calls **pyswisseph** (Swiss Ephemeris) directly.
Validates planetary positions, Rahu Kalaya, Nakshatra, Dasha, and Navamsha.

---

## Requirements

- Python 3.8 or higher
- Internet connection (first run only, to install packages)

---

## Setup & Run

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Run the server

```bash
python app.py
```

### Step 3 — Open browser

```
http://localhost:5050
```

---

## What it calculates

| Feature | Method |
|---|---|
| Planet positions | pyswisseph swe.calc_ut() with FLG_SIDEREAL |
| Ayanamsa | Lahiri (SIDM_LAHIRI) — Indian govt standard 1955 |
| Lagna (Ascendant) | swe.houses() with Whole Sign system |
| Nakshatra + Pada | Moon sidereal ÷ 13.333° |
| Vimshottari Dasha | Moon Nakshatra lord + elapsed fraction |
| Navamsha D9 | Position within sign ÷ 3.333° |
| Tithi, Yoga, Karana | Moon-Sun angle calculations |
| Sunrise / Sunset | swe.rise_trans() with GPS coordinates |
| Rahu Kalaya | Traditional Panchanga Method (day ÷ 8 segments) |

---

## How to validate results

1. **DrikPanchang** → Kundali → enter same birth details → select Lahiri ayanamsa
   - Planet positions should match within ±1°
   - Nakshatra and Pada should be identical

2. **rahu-kalaya.lk** → enter same date + location
   - Rahu Kala times should match within ±5 minutes

3. **JHora software** (free, Windows) → cross-check Dasha periods

---

## Note on ephemeris data files

This tester uses the **Moshier analytical mode** (built into pyswisseph, no files needed)
which gives ~1 arcsecond precision — sufficient for testing and validation.

For **production Jeewa Guru**, download the compressed Swiss Ephemeris data files
(~97 MB) from Astrodienst and configure `swe.set_ephe_path("/path/to/ephe/")`.
This gives 0.001 arcsecond (sub-arcsecond) precision.

Download files: https://www.astro.com/swisseph/swephinfo_e.htm

---

## License note

Swiss Ephemeris: dual-licensed AGPL / Commercial (CHF 750).
For Jeewa Guru as a commercial app, purchase the Professional License
before deployment: https://www.astro.com/swisseph/swephinfo_e.htm
