"""
Jeewa Guru — Swiss Ephemeris Live Tester
=========================================
Run:  python app.py
Open: http://localhost:5050
"""

from flask import Flask, request, jsonify, render_template_string
import swisseph as swe
import math
from datetime import date, datetime, timedelta

app = Flask(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

RASHIS = [
    ("Mesha",     "மேஷம்",   "මේෂ",    "Aries"),
    ("Vrishabha", "ரிஷபம்",  "වෘෂභ",   "Taurus"),
    ("Mithuna",   "மிதுனம்", "මිථුන",  "Gemini"),
    ("Kataka",    "கடகம்",   "කටක",    "Cancer"),
    ("Simha",     "சிம்மம்", "සිංහ",   "Leo"),
    ("Kanya",     "கன்னி",   "කන්‍යා", "Virgo"),
    ("Tula",      "துலாம்",  "තුලා",   "Libra"),
    ("Vrischika", "விருச்சிகம்","වෘශ්චික","Scorpio"),
    ("Dhanu",     "தனுசு",   "ධනු",    "Sagittarius"),
    ("Makara",    "மகரம்",   "මකර",    "Capricorn"),
    ("Kumbha",    "கும்பம்", "කුම්භ",  "Aquarius"),
    ("Meena",     "மீனம்",   "මීන",    "Pisces"),
]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni",
    "Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha",
    "Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
    "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

NAKSHATRA_LORDS = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"
] * 3

DASHA_ORDER  = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
DASHA_YEARS  = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,"Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}

PLANET_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
}

PLANET_SI = {
    "Sun":"සූර්ය","Moon":"චන්ද්‍ර","Mercury":"බුධ","Venus":"ශුක්‍ර",
    "Mars":"කුජ","Jupiter":"ගුරු","Saturn":"ශනි","Rahu":"රාහු","Ketu":"කේතු"
}

PLANET_TA = {
    "Sun":"சூரியன்","Moon":"சந்திரன்","Mercury":"புதன்","Venus":"சுக்கிரன்",
    "Mars":"செவ்வாய்","Jupiter":"குரு","Saturn":"சனி","Rahu":"ராகு","Ketu":"கேது"
}

AYANAMSA_MAP = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman":  swe.SIDM_RAMAN,
    "kp":     swe.SIDM_KRISHNAMURTI,
}

DAYS_EN = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

RAHU_KALA_SEGMENT = {0:2, 1:7, 2:5, 3:6, 4:4, 5:3, 6:8}  # Mon=0 ... Sun=6 (Python weekday)

TITHI_NAMES = [
    "Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami",
    "Shashthi","Saptami","Ashtami","Navami","Dashami",
    "Ekadashi","Dwadashi","Trayodashi","Chaturdashi","Purnima",
    "Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami",
    "Shashthi","Saptami","Ashtami","Navami","Dashami",
    "Ekadashi","Dwadashi","Trayodashi","Chaturdashi","Amavasya",
]

YOGA_NAMES = [
    "Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma",
    "Dhriti","Shula","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra",
    "Siddhi","Vyatipata","Variyan","Parigha","Shiva","Siddha","Sadhya","Shubha",
    "Shukla","Brahma","Indra","Vaidhriti"
]

KARANA_NAMES = [
    "Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti",
    "Shakuni","Chatushpada","Naga","Kimstughna"
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def jd_to_utc_h(jd):
    return ((jd - 0.5) % 1) * 24

def h_to_hm(h):
    h = h % 24
    return f"{int(h):02d}:{int((h % 1) * 60):02d}"

def deg_to_dms(deg):
    deg = deg % 360
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(((deg - d) * 60 - m) * 60)
    return f"{d}° {m:02d}' {s:02d}\""

def rashi_of(lon):
    return int(lon / 30) % 12

def deg_in_rashi(lon):
    return lon % 30

def nakshatra_of(moon_sid):
    return int(moon_sid / (360 / 27)) % 27

def pada_of(moon_sid):
    return int((moon_sid % (360 / 27)) / (360 / 108)) + 1

def tithi_of(moon_sid, sun_sid):
    diff = (moon_sid - sun_sid) % 360
    return int(diff / 12) + 1

def yoga_of(moon_sid, sun_sid):
    total = (moon_sid + sun_sid) % 360
    return int(total / (360 / 27)) % 27

def karana_of(moon_sid, sun_sid):
    diff = (moon_sid - sun_sid) % 360
    k = int(diff / 6)
    if k == 0:
        return 10  # Kimstughna
    elif k >= 57:
        return [10, 7, 8, 9][(k - 57) % 4]
    else:
        return (k - 1) % 7

def get_vimshottari_dasha(moon_sid, birth_date):
    nak_idx   = nakshatra_of(moon_sid)
    lord      = NAKSHATRA_LORDS[nak_idx]
    progress  = (moon_sid % (360/27)) / (360/27)
    remaining = DASHA_YEARS[lord] * (1 - progress)

    start_idx = DASHA_ORDER.index(lord)
    results   = []
    cursor    = birth_date

    for i in range(9):
        idx  = (start_idx + i) % 9
        p    = DASHA_ORDER[idx]
        yrs  = remaining if i == 0 else DASHA_YEARS[p]
        days = yrs * 365.25
        end  = cursor + timedelta(days=days)
        results.append({
            "planet":     p,
            "planet_si":  PLANET_SI[p],
            "planet_ta":  PLANET_TA[p],
            "years":      round(yrs, 2),
            "start":      cursor.strftime("%d %b %Y"),
            "end":        end.strftime("%d %b %Y"),
            "is_current": cursor <= datetime.now().date() <= end.date() if hasattr(end,"date") else False,
        })
        cursor = end.date() if hasattr(end,"date") else end

    return results

def get_sunrise_sunset(year, month, day, lat, lon, tz):
    jd_midnight = swe.julday(year, month, day, -tz)
    try:
        r_rise = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_RISE, [lon, lat, 0])
        r_set  = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_SET,  [lon, lat, 0])
        sr_utc = jd_to_utc_h(r_rise[1][0])
        ss_utc = jd_to_utc_h(r_set[1][0])
        sr_loc = (sr_utc + tz) % 24
        ss_loc = (ss_utc + tz) % 24
        if ss_loc < sr_loc:
            ss_loc += 24
        return sr_loc, ss_loc
    except Exception as e:
        return None, None

def get_rahu_kala(sr, ss, dow):
    if sr is None:
        return None, None
    day_len = ss - sr
    seg_len = day_len / 8
    slot    = RAHU_KALA_SEGMENT.get(dow, 1)
    rk_start = sr + seg_len * (slot - 1)
    rk_end   = sr + seg_len * slot
    return rk_start, rk_end

# ── Core calculation ─────────────────────────────────────────────────────────

def calculate_chart(year, month, day, hour_local, lat, lon, tz, ayanamsa_key="lahiri"):
    utc_hour = hour_local - tz
    jd = swe.julday(year, month, day, utc_hour)

    ayan_const = AYANAMSA_MAP.get(ayanamsa_key, swe.SIDM_LAHIRI)
    swe.set_sid_mode(ayan_const)
    ayan_val = round(swe.get_ayanamsa_ut(jd), 6)

    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    planets = {}
    for name, pid in PLANET_IDS.items():
        xx, _ = swe.calc_ut(jd, pid, flags)
        lon_sid = xx[0] % 360
        rashi_i = rashi_of(lon_sid)
        deg_in  = deg_in_rashi(lon_sid)
        planets[name] = {
            "lon_sid":    round(lon_sid, 4),
            "lon_trop":   round((lon_sid + ayan_val) % 360, 4),
            "retro":      xx[3] < 0,
            "speed":      round(xx[3], 4),
            "rashi":      rashi_i,
            "rashi_name": RASHIS[rashi_i][0],
            "rashi_si":   RASHIS[rashi_i][2],
            "rashi_ta":   RASHIS[rashi_i][1],
            "rashi_en":   RASHIS[rashi_i][3],
            "deg_in_rashi": round(deg_in, 4),
            "dms":        deg_to_dms(deg_in),
            "planet_si":  PLANET_SI[name],
            "planet_ta":  PLANET_TA[name],
        }

    # Rahu / Ketu
    rahu_xx, _ = swe.calc_ut(jd, swe.MEAN_NODE, flags)
    rahu_sid = rahu_xx[0] % 360
    ketu_sid = (rahu_sid + 180) % 360
    for nm, sid in [("Rahu", rahu_sid), ("Ketu", ketu_sid)]:
        ri = rashi_of(sid)
        planets[nm] = {
            "lon_sid": round(sid, 4),
            "lon_trop": round((sid + ayan_val) % 360, 4),
            "retro": True,
            "speed": round(rahu_xx[3], 4),
            "rashi": ri,
            "rashi_name": RASHIS[ri][0],
            "rashi_si": RASHIS[ri][2],
            "rashi_ta": RASHIS[ri][1],
            "rashi_en": RASHIS[ri][3],
            "deg_in_rashi": round(deg_in_rashi(sid), 4),
            "dms": deg_to_dms(deg_in_rashi(sid)),
            "planet_si": PLANET_SI[nm],
            "planet_ta": PLANET_TA[nm],
        }

    # Lagna
    cusps, ascmc = swe.houses(jd, lat, lon, b'W')
    lagna_sid = ascmc[0] % 360
    lagna_ri  = rashi_of(lagna_sid)

    # Panchang
    moon_sid = planets["Moon"]["lon_sid"]
    sun_sid  = planets["Sun"]["lon_sid"]
    nak_i    = nakshatra_of(moon_sid)
    pada     = pada_of(moon_sid)
    tithi    = tithi_of(moon_sid, sun_sid)
    yoga     = yoga_of(moon_sid, sun_sid)
    karana   = karana_of(moon_sid, sun_sid)
    paksha   = "Shukla (Waxing)" if tithi <= 15 else "Krishna (Waning)"

    # Navamsha (D9)
    navamsha = {}
    for nm, pd in planets.items():
        sid = pd["lon_sid"]
        rashi_num = int(sid / 30)
        deg_in_r  = sid % 30
        nav_div   = int(deg_in_r / (30/9))
        start_map = [0,3,6,9,0,3,6,9,0,3,6,9]
        nav_rashi = (start_map[rashi_num] + nav_div) % 12
        navamsha[nm] = {"rashi": nav_rashi, "rashi_name": RASHIS[nav_rashi][0], "rashi_si": RASHIS[nav_rashi][2]}

    nav_lagna_deg = lagna_sid % 30
    nav_lagna_div = int(nav_lagna_deg / (30/9))
    nav_lagna_rashi = (start_map[lagna_ri] + nav_lagna_div) % 12

    # Dasha
    birth_dt = date(year, month, day)
    dashas   = get_vimshottari_dasha(moon_sid, birth_dt)

    # Sunrise / Rahu Kala
    dow = date(year, month, day).weekday()
    sr, ss = get_sunrise_sunset(year, month, day, lat, lon, tz)
    rk_start, rk_end = get_rahu_kala(sr, ss, dow)

    # House placements (Whole Sign)
    house_placements = {}
    for nm, pd in planets.items():
        house = ((pd["rashi"] - lagna_ri) % 12) + 1
        house_placements[nm] = house

    return {
        "jd":           round(jd, 6),
        "ayanamsa":     round(ayan_val, 4),
        "ayanamsa_key": ayanamsa_key,
        "lagna":        round(lagna_sid, 4),
        "lagna_rashi":  lagna_ri,
        "lagna_name":   RASHIS[lagna_ri][0],
        "lagna_si":     RASHIS[lagna_ri][2],
        "lagna_ta":     RASHIS[lagna_ri][1],
        "lagna_dms":    deg_to_dms(lagna_sid % 30),
        "planets":      planets,
        "navamsha":     navamsha,
        "nav_lagna":    {"rashi": nav_lagna_rashi, "rashi_name": RASHIS[nav_lagna_rashi][0], "rashi_si": RASHIS[nav_lagna_rashi][2]},
        "nakshatra":    NAKSHATRAS[nak_i],
        "nak_index":    nak_i,
        "pada":         pada,
        "nak_lord":     NAKSHATRA_LORDS[nak_i],
        "tithi":        tithi,
        "tithi_name":   TITHI_NAMES[tithi - 1],
        "paksha":       paksha,
        "yoga":         YOGA_NAMES[yoga],
        "karana":       KARANA_NAMES[min(karana, len(KARANA_NAMES)-1)],
        "dashas":       dashas,
        "weekday":      DAYS_EN[dow],
        "weekday_idx":  dow,
        "sunrise":      h_to_hm(sr) if sr else "N/A",
        "sunset":       h_to_hm(ss) if ss else "N/A",
        "rahu_start":   h_to_hm(rk_start) if rk_start else "N/A",
        "rahu_end":     h_to_hm(rk_end) if rk_end else "N/A",
        "house_placements": house_placements,
        "swe_version":  "DE431 (pyswisseph)",
    }

# ── HTML Template ─────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jeewa Guru — Swiss Ephemeris Tester</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--navy:#1C2B4A;--gold:#C9A227;--lg:#f7f6f0;--card:#fff;--border:#e0ddd4;--text:#2c2b27;--muted:#6b6860;--green:#1E5631;--lgreen:#E8F5E9;--red:#C62828;--lred:#FFEBEE;--amber:#7A4300;--lamber:#FFF3E0;--blue:#0D47A1;--lblue:#E3F2FD}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--lg);color:var(--text);min-height:100vh}
header{background:var(--navy);color:#fff;padding:20px 32px;display:flex;align-items:center;gap:16px}
header h1{font-size:22px;font-weight:600;letter-spacing:.5px}
header p{font-size:13px;opacity:.7;margin-top:2px}
.gold{color:var(--gold)}
main{max-width:1100px;margin:0 auto;padding:24px 20px;display:grid;grid-template-columns:340px 1fr;gap:20px;align-items:start}
@media(max-width:760px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:0.5px solid var(--border);border-radius:12px;padding:20px}
.card h2{font-size:14px;font-weight:600;color:var(--navy);margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid var(--border)}
label{display:block;font-size:12px;color:var(--muted);margin-bottom:4px;margin-top:12px}
label:first-of-type{margin-top:0}
input,select{width:100%;padding:8px 10px;border:0.5px solid var(--border);border-radius:8px;font-size:13px;background:#faf9f5;outline:none;transition:border .15s}
input:focus,select:focus{border-color:var(--navy)}
.presets{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.preset-btn{font-size:11px;padding:4px 10px;border:0.5px solid var(--border);border-radius:6px;background:#faf9f5;cursor:pointer;color:var(--text);transition:background .15s}
.preset-btn:hover{background:#eee}
.calc-btn{width:100%;margin-top:16px;padding:11px;background:var(--navy);color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:opacity .15s}
.calc-btn:hover{opacity:.88}
.badge{display:inline-block;padding:2px 9px;border-radius:99px;font-size:11px;font-weight:600}
.b-green{background:var(--lgreen);color:var(--green)}
.b-red{background:var(--lred);color:var(--red)}
.b-amber{background:var(--lamber);color:var(--amber)}
.b-blue{background:var(--lblue);color:var(--blue)}
.b-gray{background:#f0ede4;color:var(--muted)}
.row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:0.5px solid #f0ede4;font-size:13px}
.row:last-child{border:none}
.row .lbl{color:var(--muted);min-width:140px}
.row .val{font-weight:500;text-align:right}
.planet-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:4px}
.p-card{background:#faf9f5;border-radius:8px;padding:10px 12px;border:0.5px solid var(--border)}
.p-name{font-size:11px;color:var(--muted);margin-bottom:2px}
.p-si{font-size:12px;color:var(--navy);font-weight:500}
.p-pos{font-size:13px;font-weight:600;color:var(--text);margin:2px 0}
.p-dms{font-size:11px;color:var(--muted)}
.p-retro{font-size:11px;color:var(--amber);font-weight:500}
.dasha-row{display:flex;justify-content:space-between;align-items:center;padding:7px 10px;border-radius:8px;margin-bottom:4px;font-size:12px}
.dasha-row.current{background:var(--lblue);border-left:3px solid var(--blue)}
.dasha-row:not(.current){background:#faf9f5;border-left:3px solid var(--border)}
.tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.tab{font-size:12px;padding:5px 14px;border:0.5px solid var(--border);border-radius:6px;background:#faf9f5;cursor:pointer;color:var(--muted)}
.tab.active{background:var(--navy);color:#fff;border-color:var(--navy)}
.panel{display:none}.panel.active{display:block}
.rahu-box{background:var(--lamber);border-left:3px solid var(--gold);border-radius:0 8px 8px 0;padding:10px 14px;margin:6px 0;font-size:13px}
.ok-box{background:var(--lgreen);border-left:3px solid #3B6D11;border-radius:0 8px 8px 0;padding:10px 14px;margin:8px 0;font-size:12px;color:var(--green)}
.warn-box{background:var(--lamber);border-left:3px solid #854F0B;border-radius:0 8px 8px 0;padding:10px 14px;margin:8px 0;font-size:12px;color:var(--amber)}
.code{background:#1e1e1e;color:#d4d4d4;border-radius:8px;padding:14px 16px;font-family:'Courier New',monospace;font-size:11.5px;line-height:1.7;overflow-x:auto;margin-top:8px}
.code .cm{color:#6A9955}.code .cs{color:#CE9178}.code .ck{color:#569CD6}.code .cf{color:#DCDCAA}
.spinner{width:18px;height:18px;border:2px solid #ddd;border-top-color:var(--navy);border-radius:50%;animation:spin .6s linear infinite;display:inline-block;vertical-align:middle;margin-right:8px}
@keyframes spin{to{transform:rotate(360deg)}}
#results{display:none}
#loading{display:none;padding:16px;text-align:center;color:var(--muted);font-size:13px}
.nav-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.nav-cell{background:#faf9f5;border-radius:6px;padding:6px 8px;border:0.5px solid var(--border);font-size:11px;text-align:center}
.nav-cell .p{font-weight:600;color:var(--navy)}
.nav-cell .r{color:var(--muted)}
.house-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.h-cell{background:#faf9f5;border-radius:6px;padding:7px 10px;border:0.5px solid var(--border);font-size:12px}
.h-num{font-size:10px;color:var(--muted);margin-bottom:2px}
.h-sign{font-weight:600;color:var(--navy);font-size:11px}
.h-planets{font-size:11px;color:var(--text);margin-top:2px}
.version-tag{font-size:10px;background:#eee;color:var(--muted);padding:2px 7px;border-radius:4px;font-family:monospace}
</style>
</head>
<body>
<header>
  <div>
    <h1>Jeewa Guru <span class="gold">— Swiss Ephemeris Tester</span></h1>
    <p>Live birth chart calculation via pyswisseph (NASA JPL DE431) · Lahiri Ayanamsa · Whole Sign houses</p>
  </div>
</header>

<main>
<!-- LEFT: Input form -->
<div>
  <div class="card">
    <h2>Birth details</h2>
    <label>Date of birth</label>
    <input type="date" id="dob" value="1990-07-15">
    <label>Time of birth (24h format)</label>
    <input type="time" id="tob" value="14:30">
    <label>Latitude</label>
    <input type="number" id="lat" value="6.9271" step="0.0001">
    <label>Longitude</label>
    <input type="number" id="lon" value="79.8612" step="0.0001">
    <label>Timezone offset (hours from UTC)</label>
    <input type="number" id="tz" value="5.5" step="0.5">
    <label>Ayanamsa</label>
    <select id="ayanamsa">
      <option value="lahiri" selected>Lahiri (Chitrapaksha) — recommended</option>
      <option value="raman">Raman</option>
      <option value="kp">Krishnamurti (KP)</option>
    </select>
    <label>Location presets</label>
    <div class="presets">
      <button class="preset-btn" onclick="loc(6.9271,79.8612,5.5)">Colombo</button>
      <button class="preset-btn" onclick="loc(7.2906,80.6337,5.5)">Kandy</button>
      <button class="preset-btn" onclick="loc(6.0535,80.2210,5.5)">Galle</button>
      <button class="preset-btn" onclick="loc(8.3114,80.4037,5.5)">Anuradhapura</button>
      <button class="preset-btn" onclick="loc(9.6615,80.0255,5.5)">Jaffna</button>
      <button class="preset-btn" onclick="loc(6.8498,79.9004,5.5)">Moratuwa</button>
      <button class="preset-btn" onclick="loc(28.6139,77.2090,5.5)">New Delhi</button>
      <button class="preset-btn" onclick="loc(13.0827,80.2707,5.5)">Chennai</button>
      <button class="preset-btn" onclick="loc(12.9716,77.5946,5.5)">Bengaluru</button>
      <button class="preset-btn" onclick="loc(19.0760,72.8777,5.5)">Mumbai</button>
    </div>
    <button class="calc-btn" onclick="calculate()">Calculate birth chart</button>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>How to validate results</h2>
    <div style="font-size:12px;color:var(--muted);line-height:1.6">
      <p style="margin-bottom:8px">Cross-check the generated chart against:</p>
      <p><strong>DrikPanchang:</strong> <a href="https://www.drikpanchang.com/vedic-astrology/kundali/vedic-kundali.html" target="_blank">drikpanchang.com → Kundali</a> — enter the same birth details, select Lahiri ayanamsa. Planet positions should match within ±1°.</p>
      <p style="margin-top:8px"><strong>Rahu Kalaya:</strong> <a href="https://rahu-kalaya.lk" target="_blank">rahu-kalaya.lk</a> — compare Rahu Kala times for the birth date.</p>
      <p style="margin-top:8px"><strong>JHora software:</strong> Free Vedic astrology desktop software. Use for cross-validation of Dasha periods and Navamsha chart.</p>
    </div>
  </div>
</div>

<!-- RIGHT: Results -->
<div>
  <div id="loading"><span class="spinner"></span>Calling Swiss Ephemeris (pyswisseph)...</div>
  <div id="results">

    <div class="card" style="margin-bottom:16px">
      <h2>Summary <span class="version-tag" id="swe-ver"></span></h2>
      <div id="summary-content"></div>
    </div>

    <div class="card" style="margin-bottom:16px">
      <h2>All 9 Grahas — sidereal positions</h2>
      <div class="planet-grid" id="planet-grid"></div>
    </div>

    <div class="card" style="margin-bottom:16px">
      <div class="tabs">
        <button class="tab active" onclick="showTab('panchang')">Panchang</button>
        <button class="tab" onclick="showTab('houses')">Houses</button>
        <button class="tab" onclick="showTab('navamsha')">Navamsha D9</button>
        <button class="tab" onclick="showTab('dasha')">Vimshottari Dasha</button>
        <button class="tab" onclick="showTab('rahu')">Rahu Kalaya</button>
        <button class="tab" onclick="showTab('code')">Python code</button>
      </div>

      <div id="tab-panchang" class="panel active" id="tab-panchang"></div>
      <div id="tab-houses"   class="panel"></div>
      <div id="tab-navamsha" class="panel"></div>
      <div id="tab-dasha"    class="panel"></div>
      <div id="tab-rahu"     class="panel"></div>
      <div id="tab-code"     class="panel"></div>
    </div>

  </div>
</div>
</main>

<script>
function loc(la,lo,tz){
  document.getElementById('lat').value=la;
  document.getElementById('lon').value=lo;
  document.getElementById('tz').value=tz;
}

function showTab(name){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-'+name).classList.add('active');
}

async function calculate(){
  const dob=document.getElementById('dob').value;
  const tob=document.getElementById('tob').value;
  const lat=document.getElementById('lat').value;
  const lon=document.getElementById('lon').value;
  const tz=document.getElementById('tz').value;
  const ayan=document.getElementById('ayanamsa').value;
  if(!dob||!tob){alert('Please enter date and time.');return;}
  document.getElementById('results').style.display='none';
  document.getElementById('loading').style.display='block';
  try{
    const r=await fetch('/calculate',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({dob,tob,lat:parseFloat(lat),lon:parseFloat(lon),tz:parseFloat(tz),ayanamsa:ayan})
    });
    const d=await r.json();
    if(d.error){alert('Error: '+d.error);document.getElementById('loading').style.display='none';return;}
    render(d);
  }catch(e){alert('Server error: '+e);document.getElementById('loading').style.display='none';}
}

function rashi_label(p){return p.rashi_name+' '+p.dms+' ('+p.rashi_si+')';}

function render(d){
  document.getElementById('swe-ver').textContent=d.swe_version;

  // Summary
  const cur=d.dashas.find(x=>x.is_current)||d.dashas[0];
  document.getElementById('summary-content').innerHTML=`
    <div class="row"><span class="lbl">Julian Day</span><span class="val">${d.jd}</span></div>
    <div class="row"><span class="lbl">Ayanamsa (${d.ayanamsa_key})</span><span class="val">${d.ayanamsa}°</span></div>
    <div class="row"><span class="lbl">Lagna (Ascendant)</span><span class="val">${d.lagna_name} — ${d.lagna_si} &nbsp;<span class="badge b-blue">${d.lagna_dms}</span></span></div>
    <div class="row"><span class="lbl">Chandra Rashi</span><span class="val">${d.planets.Moon.rashi_name} — ${d.planets.Moon.rashi_si}</span></div>
    <div class="row"><span class="lbl">Janma Nakshatra</span><span class="val">${d.nakshatra}, Pada ${d.pada} &nbsp;<span class="badge b-gray">Lord: ${d.nak_lord}</span></span></div>
    <div class="row"><span class="lbl">Current Dasha</span><span class="val">${cur.planet} (${cur.planet_si}) &nbsp;<span class="badge b-blue">${cur.start} – ${cur.end}</span></span></div>
    <div class="row"><span class="lbl">Tithi</span><span class="val">${d.tithi_name} (${d.tithi}) — ${d.paksha}</span></div>
    <div class="row"><span class="lbl">Weekday</span><span class="val">${d.weekday}</span></div>
    <div class="row"><span class="lbl">Sunrise / Sunset</span><span class="val">${d.sunrise} &nbsp;/&nbsp; ${d.sunset}</span></div>
    <div class="row"><span class="lbl">Rahu Kalaya</span><span class="val"><span class="badge b-amber">${d.rahu_start} – ${d.rahu_end}</span></span></div>
  `;

  // Planets
  const order=['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Rahu','Ketu'];
  document.getElementById('planet-grid').innerHTML=order.map(nm=>{
    const p=d.planets[nm];
    return`<div class="p-card">
      <div class="p-name">${nm} &nbsp;<span class="p-si">${p.planet_si} / ${p.planet_ta}</span></div>
      <div class="p-pos">${p.rashi_name} ${p.dms}</div>
      <div class="p-dms">${p.lon_sid.toFixed(4)}° sidereal</div>
      <div class="p-dms">${p.lon_trop.toFixed(4)}° tropical</div>
      <div style="margin-top:3px">${p.retro?'<span class="badge b-amber">Vakri (retrograde)</span>':'<span class="badge b-green">Direct</span>'}</div>
    </div>`;
  }).join('');

  // Panchang tab
  document.getElementById('tab-panchang').innerHTML=`
    <div class="row"><span class="lbl">Tithi</span><span class="val">${d.tithi_name} (${d.tithi}) — ${d.paksha}</span></div>
    <div class="row"><span class="lbl">Nakshatra</span><span class="val">${d.nakshatra}, Pada ${d.pada}</span></div>
    <div class="row"><span class="lbl">Yoga</span><span class="val">${d.yoga}</span></div>
    <div class="row"><span class="lbl">Karana</span><span class="val">${d.karana}</span></div>
    <div class="row"><span class="lbl">Vara (weekday)</span><span class="val">${d.weekday}</span></div>
    <div class="row"><span class="lbl">Sunrise</span><span class="val">${d.sunrise} local</span></div>
    <div class="row"><span class="lbl">Sunset</span><span class="val">${d.sunset} local</span></div>
    <div class="row"><span class="lbl">Moon-Sun angle</span><span class="val">${((d.planets.Moon.lon_sid - d.planets.Sun.lon_sid + 360)%360).toFixed(2)}°</span></div>
    <div class="ok-box" style="margin-top:10px">Compare Tithi and Nakshatra against <a href="https://www.drikpanchang.com/panchang/day-panchang.html" target="_blank">DrikPanchang daily Panchang</a> for the birth date. Should match exactly.</div>
  `;

  // Houses tab
  const lagna_ri = d.lagna_rashi;
  let houseHTML='<div class="house-grid">';
  for(let h=1;h<=12;h++){
    const ri=(lagna_ri+h-1)%12;
    const rashis=['Mesha','Vrishabha','Mithuna','Kataka','Simha','Kanya','Tula','Vrischika','Dhanu','Makara','Kumbha','Meena'];
    const rashi_si_list=['මේෂ','වෘෂභ','මිථුන','කටක','සිංහ','කන්‍යා','තුලා','වෘශ්චික','ධනු','මකර','කුම්භ','මීන'];
    const planets_in=Object.entries(d.house_placements).filter(([,hh])=>hh===h).map(([nm])=>nm);
    houseHTML+=`<div class="h-cell">
      <div class="h-num">House ${h}</div>
      <div class="h-sign">${rashis[ri]} (${rashi_si_list[ri]})</div>
      <div class="h-planets">${planets_in.length?planets_in.join(', '):''}</div>
    </div>`;
  }
  houseHTML+='</div>';
  document.getElementById('tab-houses').innerHTML=houseHTML;

  // Navamsha tab
  document.getElementById('tab-navamsha').innerHTML=`
    <p style="font-size:12px;color:var(--muted);margin-bottom:10px">D9 chart — Navamsha positions (each sign divided into 9 parts of 3°20' each)</p>
    <div class="row"><span class="lbl">Navamsha Lagna</span><span class="val">${d.nav_lagna.rashi_name} (${d.nav_lagna.rashi_si})</span></div>
    <div class="nav-grid" style="margin-top:10px">
      ${['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Rahu','Ketu'].map(nm=>`
        <div class="nav-cell">
          <div class="p">${nm}</div>
          <div class="r">${d.navamsha[nm].rashi_name}</div>
          <div style="font-size:10px;color:var(--muted)">${d.navamsha[nm].rashi_si}</div>
        </div>`).join('')}
    </div>
  `;

  // Dasha tab
  document.getElementById('tab-dasha').innerHTML=`
    <p style="font-size:12px;color:var(--muted);margin-bottom:10px">Vimshottari Dasha — 120-year planetary period system based on Moon Nakshatra</p>
    ${d.dashas.map(ds=>`
      <div class="dasha-row ${ds.is_current?'current':''}">
        <div>
          <strong>${ds.planet}</strong> <span style="color:var(--muted);font-size:11px">${ds.planet_si} / ${ds.planet_ta}</span>
          ${ds.is_current?'<span class="badge b-blue" style="margin-left:6px">Current</span>':''}
        </div>
        <div style="text-align:right">
          <div style="font-weight:500">${ds.start} – ${ds.end}</div>
          <div style="color:var(--muted);font-size:11px">${ds.years} years</div>
        </div>
      </div>`).join('')}
    <div class="ok-box">Validate Dasha start/end dates against JHora software (Jagannatha Hora) using the same birth details.</div>
  `;

  // Rahu Kala tab
  document.getElementById('tab-rahu').innerHTML=`
    <p style="font-size:12px;color:var(--muted);margin-bottom:10px">Calculated using Swiss Ephemeris swe.rise_trans() with GPS coordinates — Traditional Panchanga Method</p>
    <div class="row"><span class="lbl">Birth weekday</span><span class="val">${d.weekday}</span></div>
    <div class="row"><span class="lbl">Sunrise (local)</span><span class="val">${d.sunrise}</span></div>
    <div class="row"><span class="lbl">Sunset (local)</span><span class="val">${d.sunset}</span></div>
    <div class="rahu-box">
      <div style="font-size:12px;color:var(--amber);margin-bottom:4px;font-weight:600">Rahu Kalaya</div>
      <div style="font-size:18px;font-weight:700;color:var(--navy)">${d.rahu_start} – ${d.rahu_end}</div>
      <div style="font-size:11px;color:var(--muted);margin-top:4px">Segment: day divided into 8 equal parts. ${d.weekday} = segment ${[,8,2,7,5,6,4,3][[...['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']].indexOf(d.weekday)+1]}.</div>
    </div>
    <div class="ok-box">Cross-check at <a href="https://rahu-kalaya.lk" target="_blank">rahu-kalaya.lk</a>. Enter the same date and location. Times should match within ±5 minutes.</div>
  `;

  // Code tab
  const [yr,mo,da]=document.getElementById('dob').value.split('-');
  const [hr,mn]=document.getElementById('tob').value.split(':');
  document.getElementById('tab-code').innerHTML=`
    <p style="font-size:12px;color:var(--muted);margin-bottom:8px">Exact pyswisseph code that produced these results</p>
    <div class="code"><span class="cm"># pip install pyswisseph</span>
<span class="ck">import</span> swisseph <span class="ck">as</span> swe

<span class="cm"># 1. Set ephemeris path (download .se1 files from Astrodienst)</span>
swe.<span class="cf">set_ephe_path</span>(<span class="cs">"/path/to/ephe/"</span>)

<span class="cm"># 2. Set Lahiri ayanamsa (mandatory for Sri Lankan Jyotish)</span>
swe.<span class="cf">set_sid_mode</span>(swe.SIDM_LAHIRI)

<span class="cm"># 3. Convert birth time to Julian Day (UTC)</span>
utc_hour = ${parseFloat(hr)+parseFloat(mn)/60} - ${document.getElementById('tz').value}  <span class="cm"># local - tz_offset</span>
jd = swe.<span class="cf">julday</span>(${yr}, ${mo}, ${da}, utc_hour)
<span class="cm"># jd = ${d.jd}</span>

<span class="cm"># 4. Calculate planet positions (sidereal)</span>
flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
sun,  _ = swe.<span class="cf">calc_ut</span>(jd, swe.SUN,     flags)  <span class="cm"># ${d.planets.Sun.lon_sid}°</span>
moon, _ = swe.<span class="cf">calc_ut</span>(jd, swe.MOON,    flags)  <span class="cm"># ${d.planets.Moon.lon_sid}°</span>
merc, _ = swe.<span class="cf">calc_ut</span>(jd, swe.MERCURY, flags)  <span class="cm"># ${d.planets.Mercury.lon_sid}°</span>
rahu, _ = swe.<span class="cf">calc_ut</span>(jd, swe.MEAN_NODE, flags) <span class="cm"># ${d.planets.Rahu.lon_sid}° (Rahu)</span>
<span class="cm"># Ketu = Rahu + 180 = ${d.planets.Ketu.lon_sid}°</span>

<span class="cm"># 5. Lagna via Whole Sign houses</span>
cusps, ascmc = swe.<span class="cf">houses</span>(jd, ${document.getElementById('lat').value}, ${document.getElementById('lon').value}, b<span class="cs">'W'</span>)
lagna = ascmc[0]  <span class="cm"># ${d.lagna}° = ${d.lagna_name}</span>

<span class="cm"># 6. Sunrise for Rahu Kala</span>
jd_midnight = swe.<span class="cf">julday</span>(${yr}, ${mo}, ${da}, ${-parseFloat(document.getElementById('tz').value)})
rt = swe.<span class="cf">rise_trans</span>(jd_midnight, swe.SUN, swe.CALC_RISE,
                       [${document.getElementById('lon').value}, ${document.getElementById('lat').value}, 0])
<span class="cm"># Sunrise local = ${d.sunrise}, Rahu Kala = ${d.rahu_start}–${d.rahu_end}</span>
</div>
  `;

  document.getElementById('loading').style.display='none';
  document.getElementById('results').style.display='block';
}
</script>
</body>
</html>
"""

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json()
        dob  = data["dob"]   # "YYYY-MM-DD"
        tob  = data["tob"]   # "HH:MM"
        lat  = float(data["lat"])
        lon  = float(data["lon"])
        tz   = float(data["tz"])
        ayan = data.get("ayanamsa", "lahiri")

        yr, mo, da = map(int, dob.split("-"))
        hr, mn     = map(int, tob.split(":"))
        hour_local = hr + mn / 60

        result = calculate_chart(yr, mo, da, hour_local, lat, lon, tz, ayan)
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()})

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Jeewa Guru — Swiss Ephemeris Live Tester")
    print("="*55)
    print("  Open your browser at:  http://localhost:5050")
    print("  Press Ctrl+C to stop")
    print("="*55 + "\n")
    app.run(host="0.0.0.0", port=5050, debug=False)
