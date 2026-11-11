import os
import json
import re
import time
import math
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://hanifsalman11.github.io/car-lift-index").rstrip("/")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4").strip()
CUSTOM_LIFT = os.environ.get("CUSTOM_LIFT", "").strip()
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "3"))

DOCS_DIR = "docs"
DATA_DIR = "data"
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_lifts.json")
MONETIZATION_FILE = os.path.join(DATA_DIR, "monetization.json")

_CACHED_MODELS = None

# Format: (Lift Model / Garage Scenario, Capacity Lbs, Min Ceiling Inches, Min Concrete Inches, Anchor Torque Ft-Lbs, Lift Style, Power Spec)
SEED_LIFTS = [
    ("BendPak XPR-10AS (10,000 Lb) Clearfloor 2-Post Lift", 10000, 145, 4.25, 90, "2-Post Clearfloor", "240V 30A (2.5 HP Motor)"),
    ("BendPak GP-7LCS (7,000 Lb) Low-Ceiling 2-Post Lift", 7000, 108, 4.00, 85, "2-Post Low-Ceiling", "240V 25A (2.0 HP Motor)"),
    ("BendPak HD-9 & HD-9XW (9,000 Lb) 4-Post Storage Lift", 9000, 130, 4.00, 75, "4-Post Double-Stack", "120V / 240V Power Unit"),
    ("MaxJax M7K (7,000 Lb) Portable Low-Ceiling 2-Post Lift", 7000, 106, 4.25, 90, "Portable 2-Post", "120V 20A Mobile Cart"),
    ("Atlas BP8000 & PV-10P (8,000 / 10,000 Lb) Baseplate 2-Post", 9000, 112, 4.00, 90, "2-Post Baseplate", "240V 30A (3.0 HP Motor)"),
    ("Atlas 9KOH (9,000 Lb) Overhead Clearfloor 2-Post Lift", 9000, 144, 4.00, 90, "2-Post Clearfloor", "240V 30A (3.0 HP Motor)"),
    ("Atlas Garage Pro 8000EXT & 9000 (4-Post Storage Lift)", 8000, 132, 4.00, 70, "4-Post Caster Portable", "120V 20A / 240V 20A"),
    ("Triumph NSS-8 (8,000 Lb) 4-Post Service & Storage Lift", 8000, 128, 4.00, 70, "4-Post Double-Stack", "120V 20A / 240V"),
    ("Triumph NT-9 (9,000 Lb) Low-Ceiling Baseplate 2-Post Lift", 9000, 110, 4.00, 90, "2-Post Baseplate", "240V 30A (3.0 HP Motor)"),
    ("Triumph NTO-10A (10,000 Lb) Asymmetric Overhead 2-Post", 10000, 144, 4.25, 95, "2-Post Clearfloor", "240V 30A (3.0 HP Motor)"),
    ("Tuxedo FP8K-DX & FP9K-DX (8,000 / 9,000 Lb) 4-Post Lift", 8000, 130, 4.00, 75, "4-Post Double-Stack", "120V / 240V Power Unit"),
    ("Tuxedo TP9KACX & TP9KF (9,000 Lb) 2-Post Garage Lift", 9000, 112, 4.00, 90, "2-Post Baseplate/Clear", "240V 30A (3.0 HP Motor)"),
    ("Challenger CL10V3 (10,000 Lb) Versymmetric 2-Post Lift", 10000, 144, 4.25, 110, "2-Post Clearfloor", "240V 30A Commercial"),
    ("Rotary SPOA10 (10,000 Lb) Asymmetric 2-Post Shop Lift", 10000, 142, 4.25, 110, "2-Post Clearfloor", "240V 30A Commercial"),
    ("Rotary SPO12 & BendPak XPR-12FDL (12,000 Lb) Truck Lift", 12000, 166, 6.00, 110, "Heavy-Duty 2-Post", "240V 30A (6\" Concrete!)"),
    ("Katool KT-4H950 (9,500 Lb) 4-Post Storage & Service Lift", 9500, 132, 4.00, 75, "4-Post Double-Stack", "120V / 240V Power Unit"),
    ("Katool KT-H100 & M110 (10,000 / 11,000 Lb) 2-Post Lift", 10000, 112, 4.25, 90, "2-Post Baseplate/Clear", "240V 30A (3.0 HP Motor)"),
    ("QuickJack 5000TL & 7000TL (7,000 Lb) Portable Car Lift", 7000, 96, 3.50, 0, "Portable Frame Lift", "120V 15A Power Unit"),
    ("6,000 Lb Portable Mid-Rise Scissor Car Lift (9-Ft Garage)", 6000, 104, 4.00, 65, "Mid-Rise Scissor Lift", "120V 20A / 240V"),
    ("9-Foot (108-Inch) Garage Ceiling Low-Clearance Car Lift", 8000, 108, 4.00, 85, "Baseplate / 4-Post", "Low-Ceiling Setup"),
    ("10-Foot (120-Inch) Garage Ceiling 2-Post & 4-Post Lift", 9000, 120, 4.00, 90, "Baseplate / 4-Post", "240V 30A Setup"),
    ("11-Foot (132-Inch) Garage Ceiling 4-Post Double-Stacking", 8000, 132, 4.00, 75, "4-Post Double-Stack", "Sports Car + Sedan Stack"),
    ("12-Foot (144-Inch) Garage Ceiling Overhead Clearfloor Lift", 10000, 144, 4.25, 95, "2-Post Clearfloor", "Full Standing Height"),
    ("14-Foot (168-Inch) Pole Barn Ceiling Crew-Cab Truck Lift", 12000, 168, 6.00, 110, "Heavy Truck 2-Post", "6-Inch 3,500 PSI Slab"),
    ("Stacking Two Sports Cars (Corvette / Porsche) on 4-Post Lift", 8000, 116, 4.00, 70, "4-Post Double-Stack", "50\" + 50\" + 12\" Clearance"),
    ("Stacking SUV Under Sedan on 4-Post Garage Storage Lift", 9000, 134, 4.00, 75, "4-Post Double-Stack", "68\" + 54\" + 12\" Clearance"),
    ("240V 3-HP Car Lift Hydraulic Power Unit Breaker & Wire", 10000, 144, 4.25, 90, "240V 30A / 10-2 AWG", "AW-32 / Dexron ATF Fluid"),
    ("3/4\" × 5.5\" Wedge Anchor Bolt Embedment & Concrete PSI", 10000, 144, 4.25, 95, "ACI 318 Concrete Cone", "6\" Edge Distance Rule"),
    ("4-Inch (3,000 PSI) vs 6-Inch (3,500 PSI) Concrete Slab Lift", 10000, 144, 4.25, 95, "Slab Retrofit Footing", "4'×4'×12\" Rebar Pads"),
    ("Asymmetric vs Symmetric 2-Post Lift Arm Center-of-Gravity", 10000, 144, 4.25, 95, "30° Rotated Columns", "Door-Opening Clearance")
]


def load_json(filepath, default):
    """Self-healing JSON loader: otomatis pulih jika file korup atau kosong."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, type(default)) else default
        except Exception as e:
            print(f"[SELF-HEAL] Recovering {filepath} due to read notice: {e}")
    return default


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def safe_float(val, default=9000.0):
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(val))
        return float(cleaned) if cleaned else float(default)
    except Exception:
        return float(default)


def build_amazon_url(search_keywords, mon_cfg):
    domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")
    encoded_q = urllib.parse.quote_plus(search_keywords)
    return f"https://{domain}/s?k={encoded_q}&tag={tag}"


def get_active_gemini_model(api_key):
    """
    LAPIS 1: Mesin Pemindai Versi Model Free Tier Otomatis berbasis Regex tanpa angka versi manual.
    Otomatis mendeteksi model Gemini Flash STABIL generasi tertinggi lintas tahun.
    """
    global _CACHED_MODELS
    if _CACHED_MODELS is not None:
        return _CACHED_MODELS

    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(list_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            scored_models = []

            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])

                if "generateContent" not in methods or "flash" not in name.lower():
                    continue

                if any(bad in name.lower() for bad in [
                    "preview", "exp", "thinking", "image", "tts", "audio", "vision", "8b"
                ]):
                    continue

                ver_match = re.search(r"gemini-(\d+(?:\.\d+)?)-flash", name.lower())
                if ver_match:
                    ver_num = float(ver_match.group(1))
                    if name.lower() == f"gemini-{ver_match.group(1)}-flash":
                        tier_score = 2
                    elif name.lower() == f"gemini-{ver_match.group(1)}-flash-lite":
                        tier_score = 1
                    else:
                        tier_score = 0
                    scored_models.append((ver_num, tier_score, name))
                elif name.lower() == "gemini-flash-latest":
                    scored_models.append((0.1, 0, name))

            if scored_models:
                scored_models.sort(key=lambda x: (x[0], x[1]), reverse=True)
                _CACHED_MODELS = [item[2] for item in scored_models[:2]]
                print(f"[GEMINI] Future-proof active models locked: {_CACHED_MODELS}")
                return _CACHED_MODELS
    except Exception as e:
        print(f"[WARN] Dynamic model discovery notice: {e}")

    _CACHED_MODELS = ["gemini-flash-latest"]
    return _CACHED_MODELS


def discover_google_lift_queries(published_slugs):
    """
    LAPIS 4: 3-Tier Infinite Keyword Supply:
    Tier A: Seed List -> Tier B: Google Suggest US -> Tier C: Combinatorial Lift × Ceiling × Slab Permutator.
    """
    discovered = []
    seeds = [
        "what ceiling height for car lift ",
        "concrete thickness for 2 post lift ",
        "4 post car lift calculator ",
        "bendpak 2 post lift "
    ]
    for seed in seeds:
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q={urllib.parse.quote(seed)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for suggestion in data[1]:
                    cleaned = suggestion.lower()
                    for pref in seeds:
                        if "what " in pref or "calculator" in pref:
                            cleaned = cleaned.replace(pref, "")
                    cleaned = re.sub(
                        r"\b(calculator|size|sizing|chart|manual|review|reddit|for)\b",
                        "",
                        cleaned
                    ).strip()
                    if 5 <= len(cleaned) <= 42:
                        discovered.append((cleaned.title(), 9000, 132, 4.25, 90, "2-Post / 4-Post Lift", "240V 30A (10/2 AWG)"))
        except Exception as e:
            print(f"[WARN] Google Suggest notice: {e}")

    # Tier C Fallback: Combinatorial Permutator (Anti-Habis Lintas Tahun)
    lift_tiers = [
        (7000, 4.00, 85, "7,000-Lb Low-Ceiling 2-Post Lift"),
        (8000, 4.00, 75, "8,000-Lb 4-Post Double-Stack Lift"),
        (9000, 4.00, 90, "9,000-Lb Baseplate 2-Post Lift"),
        (9500, 4.00, 75, "9,500-Lb Extended 4-Post Lift"),
        (10000, 4.25, 95, "10,000-Lb Overhead Clearfloor 2-Post Lift"),
        (12000, 6.00, 110, "12,000-Lb Heavy Truck 2-Post Lift")
    ]
    ceiling_configs = [
        (108, "9-Ft (108\") Garage Ceiling"),
        (114, "9.5-Ft (114\") Garage Ceiling"),
        (120, "10-Ft (120\") Garage Ceiling"),
        (132, "11-Ft (132\") Garage Ceiling"),
        (144, "12-Ft (144\") Shop Ceiling"),
        (168, "14-Ft (168\") Pole Barn Ceiling")
    ]
    for cap_lbs, slab_in, trq_ftlb, l_desc in lift_tiers:
        for ceil_in, c_desc in ceiling_configs:
            if cap_lbs == 12000 and ceil_in < 144:
                continue
            combo_title = f"{l_desc} in {c_desc}"
            test_slug = slugify(f"{combo_title}-slab-clearance-calculator")
            if test_slug not in published_slugs:
                l_style = "4-Post Double-Stack" if "4-Post" in l_desc else "2-Post Service Lift"
                discovered.append((combo_title, cap_lbs, ceil_in, slab_in, trq_ftlb, l_style, "240V 30A (10/2 AWG)"))
                if len(discovered) >= 25:
                    return discovered
    return discovered


def build_deterministic_lift_data(lift_tuple):
    """
    LAPIS 3: Mesin Fisika ANSI/ALI ALCTV, ACI 318 Concrete Pullout & Double-Stack Clearance (100% Bebas Gagal).
    """
    model_name, cap_lbs, min_ceil_in, min_slab_in, anchor_torque_ftlb, lift_style, power_spec = lift_tuple

    tons = round(cap_lbs / 2000.0, 1)
    min_ceil_ft = round(min_ceil_in / 12.0, 1)

    # 1. Perhitungan Tinggi Plafon Minimum untuk Double-Stacking / Standing Service:
    # Rumus 4-Post Double-Stack: Car_Top_Height + Car_Bottom_Height + 5" Runway Thickness + 4" Safety Lock Clearance + 3" Roof Buffer = Total + 12"
    # Dalam plafon min_ceil_in, total tinggi gabungan 2 mobil maksimal (Max Combined Car Height) = min_ceil_in - 12 inci:
    max_combined_cars_in = max(84, min_ceil_in - 12)
    # Tinggi berdiri mekanik di bawah mobil setinggi 60" (Standing Headroom under 60" car):
    max_under_car_headroom_in = max(42, min_ceil_in - 60 - 8)

    # 2. Spesifikasi Lantai Beton ACI 318 & Wedge Anchor Bolts:
    concrete_psi = 3500 if cap_lbs >= 11000 else 3000
    anchor_count = 10 if "2-post" in lift_style.lower() or "2-post" in model_name.lower() else 8
    anchor_spec = "3/4\" × 5-1/2\" Wedge Anchors" if min_slab_in >= 4.0 else "5/8\" × 4-3/4\" Wedge Anchors"

    # 3. Spesifikasi Kelistrikan 240V Hydraulic Power Unit & Kapasitas Oli Hidrolik AW-32:
    breaker_amps = 20 if "120v" in power_spec.lower() and "240v" not in power_spec.lower() else 30
    wire_awg = "12/2 AWG Copper (120V)" if breaker_amps == 20 else "10/2 AWG Copper + NEMA L6-30 Plug (240V)"
    oil_quarts = 14 if cap_lbs <= 8000 else 16

    return {
        "lift_name": model_name,
        "lift_style": lift_style,
        "seo_title": f"{model_name} Ceiling Height, Concrete Slab & Breaker Calculator (2026)",
        "meta_description": f"Calculate exact garage ceiling clearance ({min_ceil_in}\" / {min_ceil_ft} ft), ACI 318 concrete slab thickness ({min_slab_in}\" @ {concrete_psi:,} PSI), {anchor_torque_ftlb} ft-lb anchor torque, and 240V {breaker_amps}A breaker for {model_name}.",
        "specs": {
            "rated_capacity_lbs": cap_lbs,
            "rated_tons": tons,
            "min_ceiling_inches": min_ceil_in,
            "min_ceiling_feet": min_ceil_ft,
            "max_combined_stack_cars_in": max_combined_cars_in,
            "standing_headroom_under_car_in": max_under_car_headroom_in,
            "min_concrete_slab_inches": min_slab_in,
            "min_concrete_psi": concrete_psi,
            "anchor_bolt_spec": anchor_spec,
            "anchor_bolt_count": anchor_count,
            "anchor_torque_ftlbs": anchor_torque_ftlb,
            "breaker_amps": breaker_amps,
            "wire_gauge_spec": wire_awg,
            "hydraulic_fluid_quarts": oil_quarts,
            "lift_style": lift_style
        },
        "ali_verdict": f"Rated at {cap_lbs:,} lbs ({tons:g} Tons, {lift_style}), {model_name} requires a minimum garage ceiling height of {min_ceil_in} inches ({min_ceil_ft} ft)—allowing up to {max_combined_cars_in} inches of combined vehicle height when double-stacking two cars (including 12 inches for the 5\" steel runway, 4\" safety lock rise-off, and 3\" roof buffer) or {max_under_car_headroom_in} inches of standing headroom under a 60\" sedan. Per ANSI/ALI ALCTV and ACI 318 concrete pullout rules, anchor the baseplates into at least a {min_slab_in:g}-inch thick, {concrete_psi:,} PSI reinforced concrete slab using {anchor_count}× {anchor_spec} torqued to {anchor_torque_ftlb} ft-lbs. Wire the hydraulic power unit on a dedicated {breaker_amps}A circuit ({wire_awg}) and fill the reservoir with {oil_quarts} quarts of AW-32 hydraulic fluid.",
        "hardware_bundle": [
            {
                "badge": f"{cap_lbs:,} Lb {lift_style}",
                "title": f"{cap_lbs:,} Lb ({tons:g}-Ton) {lift_style} Automotive Shop & Garage Hoist w/ Power Unit",
                "price_range": "$1,599 - $4,299",
                "amazon_query": f"{cap_lbs} lb {lift_style} Automotive Car Lift Garage Hoist",
                "lft_note": f"Dual hydraulic cylinders and automatic mechanical safety locks support {cap_lbs:,} lbs inside {min_ceil_ft}-ft ceilings."
            },
            {
                "badge": "240V 3-HP Hydraulic Pump",
                "title": f"220V/240V Single-Phase 3.0 HP Hydraulic Car Lift Power Unit (2,950 PSI / {oil_quarts}-Quart Tank)",
                "price_range": "$179 - $349",
                "amazon_query": "220V 240V 3HP Car Lift Hydraulic Power Unit Motor Pump 2950 PSI",
                "lft_note": "Universal SAE mounting flange bolts directly onto 2-post and 4-post lift columns for 40-second full-rise speed."
            },
            {
                "badge": f"{anchor_spec.split()[0]} Wedge Anchors",
                "title": f"Seismic {anchor_spec} Concrete Anchor Bolts (12-Pack) + 3/4\" SDS-Plus Masonry Bit & Torque Wrench",
                "price_range": "$64 - $229",
                "amazon_query": "3/4 x 5-1/2 Wedge Anchor Bolts Car Lift Concrete SDS Plus Bit",
                "lft_note": f"Provides >14,000 lbs of tension pullout strength per column when torqued to {anchor_torque_ftlb} ft-lbs in {min_slab_in:g}\" concrete."
            },
            {
                "badge": "2-Ton Under-Hoist Stands",
                "title": "Pair of 2-Ton High-Reach Under-Hoist Tripod Support Jack Stands (55\"–82\") + 8-Gal Rolling Oil Drain",
                "price_range": "$139 - $299",
                "amazon_query": "2 Ton Underhoist Support Stand Pair High Lift Rolling Oil Drain Tank",
                "lft_note": "Mandatory by ANSI/ALI safety standards at the front and rear bumpers whenever removing heavy drivetrains on a 2-post lift."
            }
        ],
        "garage_checklist": [
            f"Use the 12-Inch Double-Stack Buffer Formula before buying a 4-post lift: add Bottom Car Height + Top Car Height + 12 Inches (5\" steel runway + 4\" rise to clear the mechanical safety locks + 3\" overhead safety margin). In a {min_ceil_in}\" ({min_ceil_ft}') ceiling, your two cars combined cannot exceed {max_combined_cars_in} inches!",
            f"Verify Concrete Slab Depth ({min_slab_in:g}\"+ at {concrete_psi:,} PSI) and Joint Distance: drill a 1/4\" test hole first, and keep all {anchor_spec} at least 6 inches away from any concrete expansion joint, control crack, or slab edge.",
            "Install a High-Lift Garage Door Track Kit and a Wall-Mount Jackshaft Opener (LiftMaster 8500W/98022) so your overhead garage door hugs the ceiling and never hits the roof of the top car.",
            f"Re-torque all {anchor_count} wedge anchor bolts to {anchor_torque_ftlb} ft-lbs with a calibrated torque wrench before the first lift and after every 30 days of service—never use an impact gun on concrete wedge anchors!"
        ],
        "faqs": [
            {
                "q": f"How tall does my garage ceiling need to be for {model_name}?",
                "a": f"{model_name} requires at least {min_ceil_in} inches ({min_ceil_ft} feet) of clear ceiling height. For double-stacking two vehicles on a 4-post lift, add the height of Vehicle 1 + Vehicle 2 + 12 inches (for runways and lock disengagement clearance)—meaning a {min_ceil_in}\" ceiling fits two cars whose combined height is up to {max_combined_cars_in} inches."
            },
            {
                "q": f"How thick does concrete need to be for a {cap_lbs:,} lb car lift?",
                "a": f"Per ACI 318 and lift manufacturer engineering specs, a {cap_lbs:,}-lb lift requires a minimum of {min_slab_in:g} inches of {concrete_psi:,} PSI concrete (cured for at least 28 days) with {anchor_spec} torqued to {anchor_torque_ftlb} ft-lbs. If your garage slab is thin (<4\") or cracked, cut and pour two 4'×4'×12\" reinforced 3,500 PSI concrete footing pads."
            },
            {
                "q": f"What size 240V breaker, wire, and hydraulic oil do I need for {model_name}?",
                "a": f"A standard 2.5 HP to 3.0 HP 240V single-phase car lift hydraulic power unit draws ~18–22 Amps under full load (with high startup inrush), requiring a dedicated {breaker_amps}-Amp 2-pole circuit breaker wired with {wire_awg}, and {oil_quarts} quarts (3.5–4.0 gallons) of AW-32 or AW-46 anti-wear hydraulic oil."
            }
        ]
    }


def generate_lift_data(lift_tuple):
    """
    LAPIS 2: Memanggil model Gemini stabil dengan proteksi Cooldown HTTP 429 & Fallback Otomatis.
    """
    if not GEMINI_API_KEY:
        return build_deterministic_lift_data(lift_tuple)

    model_name, cap_lbs, min_ceil_in, min_slab_in, anchor_torque_ftlb, lift_style, power_spec = lift_tuple
    det_fallback = build_deterministic_lift_data(lift_tuple)
    sp = det_fallback["specs"]

    prompt = f"""
You are an ALI (Automotive Lift Institute) Certified Lift Inspector & Structural Garage Concrete Engineer (ANSI/ALI ALCTV & ACI 318 Specialist). Create an accurate 2026 automotive car lift ceiling height clearance, concrete slab thickness, anchor bolt torque, and 240V hydraulic power unit sizing guide for: "{model_name}".
Baseline specs: Capacity={cap_lbs} lbs ({sp['rated_tons']} Tons, {lift_style}), Min Ceiling={min_ceil_in}" ({sp['min_ceiling_feet']} ft, Max Combined 2-Car Stack={sp['max_combined_stack_cars_in']}"), Concrete Slab={min_slab_in}" @ {sp['min_concrete_psi']} PSI ({sp['anchor_bolt_count']}x {sp['anchor_bolt_spec']} @ {anchor_torque_ftlb} ft-lbs), Electrical={sp['breaker_amps']}A Breaker ({sp['wire_gauge_spec']}), Fluid={sp['hydraulic_fluid_quarts']} Quarts AW-32.
Return ONLY a valid JSON object matching this exact schema:
{{
  "lift_name": "{model_name}",
  "lift_style": "{lift_style}",
  "seo_title": "{model_name} Ceiling Height, Concrete Slab & Breaker Calculator (2026)",
  "meta_description": "Calculate exact garage ceiling clearance, ACI 318 concrete slab thickness, wedge anchor torque, and 240V hydraulic motor breaker size for {model_name}.",
  "specs": {{
    "rated_capacity_lbs": {cap_lbs},
    "rated_tons": {sp['rated_tons']},
    "min_ceiling_inches": {min_ceil_in},
    "min_ceiling_feet": {sp['min_ceiling_feet']},
    "max_combined_stack_cars_in": {sp['max_combined_stack_cars_in']},
    "standing_headroom_under_car_in": {sp['standing_headroom_under_car_in']},
    "min_concrete_slab_inches": {min_slab_in},
    "min_concrete_psi": {sp['min_concrete_psi']},
    "anchor_bolt_spec": "{sp['anchor_bolt_spec']}",
    "anchor_bolt_count": {sp['anchor_bolt_count']},
    "anchor_torque_ftlbs": {anchor_torque_ftlb},
    "breaker_amps": {sp['breaker_amps']},
    "wire_gauge_spec": "{sp['wire_gauge_spec']}",
    "hydraulic_fluid_quarts": {sp['hydraulic_fluid_quarts']},
    "lift_style": "{lift_style}"
  }},
  "ali_verdict": "3-sentence technical summary stating minimum ceiling height in inches/feet, double-stack vehicle clearance formula, required concrete slab thickness/PSI and anchor torque, and 240V breaker/fluid specs.",
  "hardware_bundle": [
    {{
      "badge": "{cap_lbs:,} Lb {lift_style}",
      "title": "{cap_lbs:,} Lb ({sp['rated_tons']:g}-Ton) {lift_style} Automotive Garage Lift w/ Power Unit",
      "price_range": "$1,599 - $4,299",
      "amazon_query": "{cap_lbs} lb {lift_style} Automotive Car Lift Garage",
      "lft_note": "1-sentence mechanical safety lock and ceiling fit note"
    }},
    {{
      "badge": "240V 3-HP Hydraulic Pump",
      "title": "220V/240V 3.0 HP Car Lift Hydraulic Power Unit Motor Pump (2,950 PSI)",
      "price_range": "$179 - $349",
      "amazon_query": "220V 240V 3HP Car Lift Hydraulic Power Unit Motor Pump",
      "lft_note": "1-sentence lift rise speed and AW-32 fluid reservoir note"
    }},
    {{
      "badge": "3/4\" × 5.5\" Wedge Anchors",
      "title": "Seismic {sp['anchor_bolt_spec']} Concrete Anchor Bolts (12-Pack) + SDS-Plus Bit & Torque Wrench",
      "price_range": "$64 - $229",
      "amazon_query": "3/4 x 5-1/2 Wedge Anchor Bolts Car Lift Concrete SDS Plus",
      "lft_note": "1-sentence ACI 318 concrete pullout and {anchor_torque_ftlb} ft-lb torque note"
    }},
    {{
      "badge": "2-Ton Under-Hoist Stands",
      "title": "Pair of 2-Ton High-Reach Under-Hoist Tripod Jack Stands + 8-Gal Rolling Oil Drain",
      "price_range": "$139 - $299",
      "amazon_query": "2 Ton Underhoist Support Stand Pair Rolling Oil Drain Tank",
      "lft_note": "1-sentence center-of-gravity stability and ANSI/ALI safety note"
    }}
  ],
  "garage_checklist": [
    "Step 1 regarding the +12-inch 4-post double-stack ceiling clearance formula",
    "Step 2 regarding {min_slab_in}-inch {sp['min_concrete_psi']} PSI concrete depth and 6-inch crack setback",
    "Step 3 regarding high-lift garage door tracks and wall-mount jackshaft openers",
    "Step 4 regarding torquing wedge anchors to {anchor_torque_ftlb} ft-lbs without an impact gun"
  ],
  "faqs": [
    {{"q": "What ceiling height do I need for {model_name}?", "a": "Exact inches and feet for standing service vs double-stacking two cars."}},
    {{"q": "What concrete thickness and anchor bolt torque are required for {model_name}?", "a": "Exact slab depth, PSI, anchor dimensions, edge distance, and ft-lbs torque."}},
    {{"q": "What size 240V breaker and hydraulic oil does {model_name} use?", "a": "Exact breaker amps, copper wire AWG, and quarts of AW-32 oil."}}
  ]
}}
"""

    for model_id in get_active_gemini_model(GEMINI_API_KEY):
        for attempt in range(2):
            try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json"
                    }
                }
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=40) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                    parsed = json.loads(raw_text)
                    if "specs" in parsed and "hardware_bundle" in parsed:
                        time.sleep(6)
                        return parsed
            except urllib.error.HTTPError as he:
                if he.code == 429:
                    print(f"[RATE-LIMIT] HTTP 429 on {model_id} (attempt {attempt + 1}). Cooling down 20s...")
                    time.sleep(20)
                else:
                    print(f"[WARN] HTTP {he.code} on {model_id} for '{model_name}': {he}")
                    break
            except Exception as e:
                print(f"[WARN] Gemini ({model_id}) notice for '{model_name}': {e}")
                break

    return det_fallback


def build_lift_html_page(data, slug, mon_cfg):
    lift_name = data.get("lift_name", "Automotive Garage Car Lift")
    sp = data.get("specs", {})
    cap_lbs = int(safe_float(sp.get("rated_capacity_lbs", 9000), 9000))
    tons = round(safe_float(sp.get("rated_tons", 4.5), 4.5), 1)
    ceil_in = int(safe_float(sp.get("min_ceiling_inches", 132), 132))
    ceil_ft = round(safe_float(sp.get("min_ceiling_feet", 11.0), 11.0), 1)
    slab_in = round(safe_float(sp.get("min_concrete_slab_inches", 4.25), 4.25), 2)
    psi = int(safe_float(sp.get("min_concrete_psi", 3000), 3000))
    trq_ftlb = int(safe_float(sp.get("anchor_torque_ftlbs", 90), 90))
    brk_a = int(safe_float(sp.get("breaker_amps", 30), 30))
    oil_qts = int(safe_float(sp.get("hydraulic_fluid_quarts", 16), 16))
    l_style = sp.get("lift_style", "2-Post / 4-Post Lift")

    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "2+Post+4+Post+Automotive+Car+Lift+220V+Power+Unit"), mon_cfg)

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": f"{lift_name} Ceiling Height & Concrete Slab Calculator",
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Web Browser",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}
                    } for f in data.get("faqs", [])
                ]
            }
        ]
    }

    bundle_html = ""
    for item in data.get("hardware_bundle", []):
        amz_url = build_amazon_url(item.get("amazon_query", item.get("title", "Automotive Car Lift")), mon_cfg)
        bundle_html += f"""
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col justify-between hover:border-red-500/60 transition">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs font-bold uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/20 px-2.5 py-0.5 rounded">{item.get('badge', 'Shop Lift Gear')}</span>
              <span class="text-sm font-bold text-emerald-400">{item.get('price_range', '$69+')}</span>
            </div>
            <h3 class="text-base font-bold text-white mt-2">{item.get('title', '')}</h3>
            <p class="text-xs text-zinc-400 mt-2 leading-relaxed">🚗 {item.get('lft_note', '')}</p>
          </div>
          <a href="{amz_url}" target="_blank" rel="nofollow sponsored" class="mt-5 block text-center bg-red-500 hover:bg-red-400 text-zinc-950 font-extrabold py-2.5 px-4 rounded-lg text-sm transition shadow-lg">
            Check Price on Amazon →
          </a>
        </div>"""

    # Build Car Lift Type vs Ceiling Height, Concrete Slab, Anchor Torque & Electrical Reference Matrix Table
    lift_tiers = [
        ("6,000–7,000 Lb Portable / MaxJax", "96\" – 108\" (8'–9')", "4.0\" – 4.25\" (3,000 PSI)", "85 – 90 ft-lbs (5/8\"–3/4\")", "120V 20A (12/2 AWG)"),
        ("8,000 Lb 4-Post Storage Lift", "116\" – 132\" (9.7'–11')", "4.0\" Concrete (Freestanding)", "70 ft-lbs (Optional 3/4\")", "120V 20A / 240V 20A"),
        ("9,000 Lb Low-Ceiling Baseplate 2-Post", "108\" – 112\" (9'–9.3')", "4.0\" – 4.25\" (3,000 PSI)", "90 ft-lbs (10× 3/4\"×5.5\")", "240V 30A (10/2 AWG)"),
        ("10,000 Lb Clearfloor Overhead 2-Post", "142\" – 145\" (11.8'–12')", "4.25\" – 4.5\" (3,000 PSI)", "95 – 110 ft-lbs (3/4\"×5.5\")", "240V 30A (10/2 AWG)"),
        ("12,000 Lb Heavy Crew-Cab Truck 2-Post", "164\" – 168\" (13.7'–14')", "6.0\" Concrete (3,500 PSI!)", "110 ft-lbs (12× 3/4\"×6.5\")", "240V 30A (10/2 AWG)")
    ]
    matrix_rows_html = ""
    for l_lbl, c_lbl, s_lbl, a_lbl, e_lbl in lift_tiers:
        matrix_rows_html += f"""
        <tr class="border-b border-zinc-800 hover:bg-zinc-800/40">
          <td class="py-3 px-4 font-bold text-white">{l_lbl}</td>
          <td class="py-3 px-4 font-bold text-red-400">{c_lbl}</td>
          <td class="py-3 px-4 text-emerald-400 font-semibold">{s_lbl}</td>
          <td class="py-3 px-4 text-zinc-300">{a_lbl}</td>
          <td class="py-3 px-4 text-xs text-zinc-300">{e_lbl}</td>
        </tr>"""

    checklist_html = ""
    for idx, step_text in enumerate(data.get("garage_checklist", []), start=1):
        checklist_html += f"""
        <label class="flex items-start gap-3.5 bg-zinc-900 border border-zinc-800 rounded-xl p-4 cursor-pointer hover:border-zinc-700 transition">
          <input type="checkbox" class="mt-1 w-5 h-5 accent-red-500 rounded cursor-pointer lft-check">
          <span class="text-sm text-zinc-200 leading-relaxed"><strong>ALI Safety Step {idx}:</strong> {step_text}</span>
        </label>"""

    faqs_html = "".join([
        f"<div class='bg-zinc-900 border border-zinc-800 rounded-xl p-5'><h3 class='font-bold text-white text-base mb-2'>{f.get('q', '')}</h3><p class='text-sm text-zinc-300 leading-relaxed'>{f.get('a', '')}</p></div>"
        for f in data.get("faqs", [])
    ])

    canonical_url = f"{SITE_BASE_URL}/{slug}.html"
    amz_domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    amz_tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{data.get('seo_title', lift_name)}</title>
  <meta name="description" content="{data.get('meta_description', '')}">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{data.get('seo_title', lift_name)}">
  <meta property="og:description" content="{data.get('meta_description', '')}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="application/ld+json">{json.dumps(schema_graph)}</script>
</head>
<body class="bg-zinc-950 text-zinc-100 antialiased min-h-screen flex flex-col">
  <header class="border-b border-zinc-800 bg-zinc-900/80 backdrop-blur sticky top-0 z-30">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <a href="index.html" class="text-lg font-black tracking-tight text-white flex items-center gap-2">
        <span class="bg-red-500 text-zinc-950 px-2 py-0.5 rounded font-black">CARLIFT</span>SlabIndex
      </a>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-red-500 hover:bg-red-400 text-zinc-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Car Lifts & Power Units →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-10 flex-1 w-full">
    <div class="mb-8">
      <div class="flex flex-wrap items-center gap-2.5 mb-3">
        <span class="text-xs font-extrabold uppercase tracking-widest bg-red-500 text-zinc-950 px-3 py-1 rounded-full">{cap_lbs:,} Lb ({tons:g}-Ton) {l_style}</span>
        <span class="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">Min Ceiling: {ceil_in}" ({ceil_ft} ft) | Slab: {slab_in:g}" ({psi:,} PSI)</span>
        <span class="text-xs font-semibold bg-zinc-800 text-zinc-300 px-3 py-1 rounded-full">Anchor: {trq_ftlb} ft-lbs | 240V {brk_a}A ({oil_qts} Qt AW-32)</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white leading-tight">{data.get('seo_title', lift_name)}</h1>
      <div class="mt-4 bg-zinc-900 border-l-4 border-red-500 p-4 rounded-r-xl text-sm text-zinc-200 leading-relaxed">
        <strong>ANSI/ALI ALCTV & ACI 318 Concrete Verdict:</strong> {data.get('ali_verdict', '')}
      </div>
    </div>

    <!-- INTERACTIVE CAR LIFT CEILING HEIGHT, DOUBLE-STACK & CONCRETE SLAB CALCULATOR -->
    <section class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 sm:p-8 mb-12 shadow-2xl">
      <h2 class="text-xl font-extrabold text-white mb-2">Interactive {lift_name} Ceiling Clearance & Slab Calculator</h2>
      <p class="text-xs text-zinc-400 mb-6">Adjust your top vehicle height, bottom vehicle height (or standing mechanic height), and lift capacity tier to compute required garage ceiling height, concrete slab depth, and 240V power unit circuit specs.</p>

      <div class="grid md:grid-cols-2 gap-8 items-center">
        <div class="space-y-5">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <div class="flex justify-between text-xs font-medium mb-1">
                <label for="car1Slider" class="text-zinc-300">Top Vehicle Height (In)</label>
                <span class="text-red-400 font-bold"><span id="car1Val">54</span>"</span>
              </div>
              <input id="car1Slider" type="range" min="44" max="82" step="1" value="54" class="w-full accent-red-500 cursor-pointer">
            </div>
            <div>
              <div class="flex justify-between text-xs font-medium mb-1">
                <label for="car2Slider" class="text-zinc-300">Bottom Car / Mechanic (In)</label>
                <span class="text-red-400 font-bold"><span id="car2Val">58</span>"</span>
              </div>
              <input id="car2Slider" type="range" min="44" max="82" step="1" value="58" class="w-full accent-red-500 cursor-pointer">
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="capSelect" class="block text-xs font-medium text-zinc-400 mb-1">Lift Capacity & Style</label>
              <select id="capSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-red-500">
                <option value="7000|4.00|85" {"selected" if cap_lbs <= 7500 else ""}>7,000 Lb Portable / Low-Ceiling</option>
                <option value="8000|4.00|75" {"selected" if 7500 < cap_lbs <= 8500 else ""}>8,000 Lb 4-Post Double-Stack</option>
                <option value="9000|4.00|90" {"selected" if 8500 < cap_lbs <= 9500 else ""}>9,000 Lb Baseplate 2-Post</option>
                <option value="10000|4.25|95" {"selected" if 9500 < cap_lbs <= 10500 else ""}>10,000 Lb Clearfloor 2-Post</option>
                <option value="12000|6.00|110" {"selected" if cap_lbs > 10500 else ""}>12,000 Lb Heavy Truck 2-Post</option>
              </select>
            </div>
            <div>
              <label for="modeSelect" class="block text-xs font-medium text-zinc-400 mb-1">Runway & Lock Buffer</label>
              <select id="modeSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-red-500">
                <option value="12" selected>4-Post Double-Stack (+12" Buffer)</option>
                <option value="8">2-Post Frame-Engaging (+8" Buffer)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="bg-zinc-950 border border-red-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-red-400 font-bold">Min Ceiling Height</span>
            <div class="text-2xl sm:text-3xl font-black text-white mt-1"><span id="ceilInOut">124</span>" <span class="text-xs font-normal text-zinc-400">(<span id="ceilFtOut">10.3</span>')</span></div>
            <p id="stackNoteOut" class="text-xs text-red-400 font-semibold mt-1">Includes +12" Lock/Runway</p>
          </div>

          <div class="bg-zinc-950 border border-emerald-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-emerald-400 font-bold">Concrete Slab & Torque</span>
            <div id="slabOut" class="text-xl sm:text-2xl font-black text-emerald-400 mt-1">{slab_in:g}" (3,000 PSI)</div>
            <p id="anchorElecOut" class="text-xs text-zinc-300 font-semibold mt-1">Torque: {trq_ftlb} ft-lb | 240V 30A</p>
          </div>
        </div>
      </div>

      <div class="mt-6 bg-red-950/40 border border-red-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div id="lftAdviceBanner" class="text-sm text-red-100 font-medium"></div>
        <a id="dynamicLftBtn" href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="shrink-0 bg-red-500 hover:bg-red-400 text-zinc-950 font-extrabold px-4 py-2.5 rounded-lg text-xs uppercase tracking-wider transition">
          Shop Matched Car Lift & Power Unit on Amazon →
        </a>
      </div>
    </section>

    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Complete {lift_name} Lift, Power Unit & Anchor Bundle</h2>
        <span class="text-xs text-zinc-400">ANSI/ALI ALCTV & ACI 318 Rated</span>
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{bundle_html}</div>
    </section>

    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-4">Automotive Car Lift Ceiling Height, Concrete Slab Thickness & Anchor Torque Chart</h2>
      <div class="overflow-x-auto bg-zinc-900 border border-zinc-800 rounded-xl">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="border-b border-zinc-800 bg-zinc-950/60 text-zinc-400 uppercase text-xs">
              <th class="py-3.5 px-4">Car Lift Type & Rating</th>
              <th class="py-3.5 px-4 text-red-400">Min Ceiling Height</th>
              <th class="py-3.5 px-4 text-emerald-400">Min Concrete Slab</th>
              <th class="py-3.5 px-4">Wedge Anchor Torque</th>
              <th class="py-3.5 px-4">Power Unit Circuit</th>
            </tr>
          </thead>
          <tbody>{matrix_rows_html}</tbody>
        </table>
      </div>
    </section>

    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">ALI Certified Concrete Slab, Wedge Anchor & High-Lift Door Checklist</h2>
        <span id="lftBadge" class="text-xs font-bold bg-zinc-800 text-red-400 px-3 py-1 rounded-full">0 / 4 Completed</span>
      </div>
      <div class="space-y-3">{checklist_html}</div>
    </section>

    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-5">Frequently Asked Questions ({lift_name})</h2>
      <div class="space-y-4">{faqs_html}</div>
    </section>
  </main>

  <footer class="border-t border-zinc-800 py-8 text-center text-xs text-zinc-500 px-4">
    <p>© {datetime.now(timezone.utc).year} CarLiftSlabIndex. Independent Automotive Lift Ceiling Clearance & ACI 318 Concrete Database. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const amzDomain = "{amz_domain}";
    const amzTag = "{amz_tag}";

    const car1Slider = document.getElementById('car1Slider');
    const car2Slider = document.getElementById('car2Slider');
    const capSelect = document.getElementById('capSelect');
    const modeSelect = document.getElementById('modeSelect');
    const car1Val = document.getElementById('car1Val');
    const car2Val = document.getElementById('car2Val');
    const ceilInOut = document.getElementById('ceilInOut');
    const ceilFtOut = document.getElementById('ceilFtOut');
    const stackNoteOut = document.getElementById('stackNoteOut');
    const slabOut = document.getElementById('slabOut');
    const anchorElecOut = document.getElementById('anchorElecOut');
    const lftAdviceBanner = document.getElementById('lftAdviceBanner');
    const dynamicLftBtn = document.getElementById('dynamicLftBtn');

    function recalculateLift() {{
      const car1In = parseInt(car1Slider.value, 10);
      const car2In = parseInt(car2Slider.value, 10);
      const capParts = capSelect.value.split('|');
      const capLbs = parseInt(capParts[0], 10);
      const slabIn = parseFloat(capParts[1]);
      const trqFtLb = parseInt(capParts[2], 10);
      const bufferIn = parseInt(modeSelect.value, 10);

      car1Val.textContent = car1In;
      car2Val.textContent = car2In;

      const minCeilIn = car1In + car2In + bufferIn;
      const minCeilFt = (minCeilIn / 12.0).toFixed(1);
      const psiReq = capLbs >= 11000 ? "3,500 PSI" : "3,000 PSI";
      const brkSpec = capLbs <= 8000 ? "120V/240V 20A" : "240V 30A (10/2 AWG)";

      ceilInOut.textContent = minCeilIn;
      ceilFtOut.textContent = minCeilFt;
      stackNoteOut.textContent = `Includes +${{bufferIn}}" Lock/Runway Margin`;
      slabOut.textContent = `${{slabIn}}" (${{psiReq}})`;
      anchorElecOut.textContent = `Torque: ${{trqFtLb}} ft-lb | ${{brkSpec.split(' ')[0]}}`;

      lftAdviceBanner.innerHTML = `🚗 <strong>ALI Garage Spec:</strong> Stacking/lifting a ${{car1In}}" vehicle over ${{car2In}}" requires <strong>${{minCeilIn}}" (${{minCeilFt}} ft) of clear ceiling height</strong>, a <strong>${{capLbs.toLocaleString()}}-lb Car Lift</strong> anchored into <strong>${{slabIn}}"+ (${{psiReq}}) concrete at ${{trqFtLb}} ft-lbs</strong>, and a <strong>${{brkSpec}} hydraulic power circuit</strong>.`;
      dynamicLftBtn.href = `https://${{amzDomain}}/s?k=${{capLbs}}+lb+Automotive+Car+Lift+2+Post+4+Post+220V+Power+Unit&tag=${{amzTag}}`;
    }}

    car1Slider.addEventListener('input', recalculateLift);
    car2Slider.addEventListener('input', recalculateLift);
    capSelect.addEventListener('change', recalculateLift);
    modeSelect.addEventListener('change', recalculateLift);
    recalculateLift();

    const checks = document.querySelectorAll('.lft-check');
    const badge = document.getElementById('lftBadge');
    checks.forEach(ch => {{
      ch.addEventListener('change', () => {{
        const done = Array.from(checks).filter(c => c.checked).length;
        badge.textContent = `${{done}} / ${{checks.length}} Completed`;
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)


def rebuild_portal_sitemap_and_rss(published, mon_cfg):
    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "2+Post+4+Post+Automotive+Car+Lift+220V+Power+Unit"), mon_cfg)

    cards_html = ""
    for item in reversed(published):
        cards_html += f"""
        <a href="{item['slug']}.html" class="block bg-zinc-900 border border-zinc-800 hover:border-red-500/60 rounded-xl p-5 transition group">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-black uppercase bg-red-500 text-zinc-950 px-2.5 py-0.5 rounded">{item.get('cap_lbs', 9000):,} Lb ({item.get('ceil_ft', 11.0)}' Ceil)</span>
            <span class="text-xs text-zinc-400">{item.get('slab_in', 4.25):g}" Slab | {item.get('trq', 90)} ft-lb</span>
          </div>
          <h2 class="text-base font-bold text-white group-hover:text-red-400 transition">{item['lift_name']}</h2>
          <p class="text-xs text-zinc-400 mt-2 line-clamp-2">{item['description']}</p>
          <span class="inline-block mt-4 text-xs font-extrabold text-red-400">Calculate Ceiling, Slab & Anchor Torque →</span>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CarLiftSlabIndex — 2-Post & 4-Post Car Lift Ceiling Height, Concrete Slab & Breaker Calculator (2026)</title>
  <meta name="description" content="Calculate exact 2-post and 4-post automotive car lift garage ceiling height clearance, ACI 318 concrete slab thickness, 3/4-inch wedge anchor torque, and 240V hydraulic power unit breaker size for BendPak, MaxJax, Atlas, Triumph, and Katool lifts.">
  <link rel="canonical" href="{SITE_BASE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="CarLiftSlabIndex RSS Feed" href="{SITE_BASE_URL}/rss.xml">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen flex flex-col">
  <header class="border-b border-zinc-800 bg-zinc-900/80 sticky top-0 z-30 backdrop-blur">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <div class="text-lg font-black text-white flex items-center gap-2">
        <span class="bg-red-500 text-zinc-950 px-2 py-0.5 rounded font-black">CARLIFT</span>SlabIndex
      </div>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-red-500 hover:bg-red-400 text-zinc-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Car Lifts & Power Units →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-12 flex-1 w-full">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <h1 class="text-3xl sm:text-5xl font-black text-white tracking-tight">2-Post & 4-Post Car Lift Ceiling Height, Concrete Slab & Breaker Database</h1>
      <p class="text-zinc-400 mt-3 text-base sm:text-lg">Select your automotive lift model or garage ceiling height below to calculate 4-post double-stacking clearance, ACI 318 concrete slab thickness, wedge anchor bolt torque, and 240V hydraulic pump wiring.</p>
      <div class="mt-6">
        <input id="filterInput" type="text" placeholder="Search lift model or ceiling height (e.g. BendPak XPR-10AS, MaxJax M7K, Atlas 9KOH, Triumph NSS-8, 10-Ft Ceiling, 4-Post...)" class="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-red-500">
      </div>
    </div>

    <div id="lftGrid" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{cards_html}</div>
  </main>

  <footer class="border-t border-zinc-800 py-8 text-center text-xs text-zinc-500">
    <p>© {datetime.now(timezone.utc).year} CarLiftSlabIndex. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const filterInput = document.getElementById('filterInput');
    const cards = Array.from(document.getElementById('lftGrid').children);
    filterInput.addEventListener('input', (e) => {{
      const q = e.target.value.toLowerCase();
      cards.forEach(c => {{
        c.style.display = c.textContent.toLowerCase().includes(q) ? 'block' : 'none';
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls_xml = f"""  <url>
    <loc>{SITE_BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n"""

    for item in published:
        urls_xml += f"""  <url>
    <loc>{SITE_BASE_URL}/{item['slug']}.html</loc>
    <lastmod>{item.get('date', today)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>\n"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>""")

    rss_items = ""
    for item in list(reversed(published))[:30]:
        rss_items += f"""    <item>
      <title>{item['title']}</title>
      <link>{SITE_BASE_URL}/{item['slug']}.html</link>
      <guid>{SITE_BASE_URL}/{item['slug']}.html</guid>
      <description>{item['description']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CarLiftSlabIndex Automotive Car Lift Ceiling & Concrete Slab Database</title>
    <link>{SITE_BASE_URL}/</link>
    <description>Interactive 2-Post & 4-Post Car Lift Ceiling Clearance, Concrete Slab & Anchor Torque Calculators</description>
    <atom:link href="{SITE_BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
{rss_items}  </channel>
</rss>"""

    with open(os.path.join(DOCS_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def notify_search_engines(new_urls):
    """Multi-Endpoint Search Engine Pinger (IndexNow Global + Bing + Google WebSub)."""
    if not SITE_BASE_URL or not new_urls:
        return
    parsed_host = urllib.parse.urlparse(SITE_BASE_URL).netloc
    payload = {
        "host": parsed_host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls
    }
    for idx_endpoint in ["https://api.indexnow.org/indexnow", "https://www.bing.com/indexnow"]:
        try:
            req = urllib.request.Request(
                idx_endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                print(f"[INDEXNOW] Pushed {len(new_urls)} URLs to {idx_endpoint} (HTTP {resp.status})")
                break
        except Exception as e:
            print(f"[WARN] IndexNow ({idx_endpoint}) notice: {e}")

    try:
        hub_data = urllib.parse.urlencode({
            "hub.mode": "publish",
            "hub.url": f"{SITE_BASE_URL}/rss.xml"
        }).encode("utf-8")
        req_hub = urllib.request.Request(
            "https://pubsubhubbub.appspot.com/",
            data=hub_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req_hub, timeout=15) as resp_hub:
            print(f"[WEBSUB] Google PubSubHubbub ping status: {resp_hub.status}")
    except Exception as e:
        print(f"[WARN] WebSub ping notice: {e}")


def main():
    published = load_json(PUBLISHED_FILE, [])
    mon_cfg = load_json(MONETIZATION_FILE, {})
    published_slugs = {item["slug"] for item in published if "slug" in item}

    candidates = []
    if CUSTOM_LIFT:
        candidates.append((CUSTOM_LIFT.strip(), 10000, 144, 4.25, 95, "2-Post Clearfloor", "240V 30A (10/2 AWG)"))
    candidates.extend(SEED_LIFTS)
    candidates.extend(discover_google_lift_queries(published_slugs))

    new_urls = []
    count = 0

    for lift_tuple in candidates:
        if count >= PAGES_PER_RUN:
            break
        l_name = lift_tuple[0]
        slug = slugify(f"{l_name}-slab-clearance-calculator")
        if slug in published_slugs:
            continue

        print(f"[ENGINE] Generating car lift ceiling & concrete slab calculator for: {l_name}...")
        try:
            data = generate_lift_data(lift_tuple)
            build_lift_html_page(data, slug, mon_cfg)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            sp = data.get("specs", {})

            published.append({
                "lift_name": data.get("lift_name", l_name),
                "slug": slug,
                "title": data.get("seo_title", f"{l_name} Car Lift Calculator"),
                "description": data.get("meta_description", ""),
                "cap_lbs": int(safe_float(sp.get("rated_capacity_lbs", lift_tuple[1]), lift_tuple[1])),
                "ceil_ft": round(safe_float(sp.get("min_ceiling_feet", round(lift_tuple[2] / 12.0, 1)), 11.0), 1),
                "slab_in": round(safe_float(sp.get("min_concrete_slab_inches", lift_tuple[3]), lift_tuple[3]), 2),
                "trq": int(safe_float(sp.get("anchor_torque_ftlbs", lift_tuple[4]), lift_tuple[4])),
                "date": today
            })
            published_slugs.add(slug)
            if SITE_BASE_URL:
                new_urls.append(f"{SITE_BASE_URL}/{slug}.html")
            count += 1
            if count < PAGES_PER_RUN:
                time.sleep(15)
        except Exception as e:
            print(f"[ERROR] Failed building {l_name}: {e}")

    save_json(PUBLISHED_FILE, published)
    rebuild_portal_sitemap_and_rss(published, mon_cfg)
    if new_urls and SITE_BASE_URL:
        new_urls.append(f"{SITE_BASE_URL}/")
        notify_search_engines(new_urls)
    print(f"[DONE] Published {count} new automotive car lift ceiling & concrete slab calculator pages.")


if __name__ == "__main__":
    main()
