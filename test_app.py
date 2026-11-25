"""
test_app.py - automatic checks for the whole application.
Run with:  python test_app.py
It uses a temporary database, so your real database.db is not touched.
"""
import os, re, sys, tempfile
tmp = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = os.path.join(tmp, "test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app as appmod
from utils import database as db
app = appmod.app
app.config["TESTING"] = True

def token(client, url="/login"):
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

def post(client, url, data, page=None, follow=True):
    data = dict(data); data["csrf_token"] = token(client, page or url)
    return client.post(url, data=data, follow_redirects=follow)

ok = lambda cond, msg: print(("PASS " if cond else "FAIL ") + msg) or (cond or sys.exit(1))
c = app.test_client()

# public pages
for u in ["/", "/about", "/login", "/register"]:
    ok(c.get(u).status_code == 200, f"GET {u} 200")
ok(c.get("/nope").status_code == 404, "404 page")
for u in ["/dashboard", "/profile", "/meal-plan", "/exercises"]:
    r = c.get(u); ok(r.status_code == 302 and "/login" in r.headers["Location"], f"{u} redirects to login")
ok(c.post("/login", data={"email": "a@b.com", "password": "x"}).status_code == 400, "POST without CSRF rejected")

# register validation
bad = [dict(name="", email="x", password="123", confirm_password="123"),
       dict(name="A", email="bad-email", password="123456", confirm_password="123456"),
       dict(name="A", email="a@b.com", password="123456", confirm_password="999999")]
for b in bad:
    r = post(c, "/register", b); ok(b"alert-danger" in r.data, f"register rejects {b['email']!r}")
good = dict(name="Test User", email="Test@Example.com", password="secret1", confirm_password="secret1")
r = post(c, "/register", good); ok(b"Account created" in r.data, "register ok")
r = post(c, "/register", good); ok(b"already exists" in r.data, "duplicate email handled")
stored = db.get_user_by_email("test@example.com")
ok(stored and stored["password"] != "secret1" and stored["password"].startswith(("scrypt", "pbkdf2")), "password hashed")

# login
r = post(c, "/login", dict(email="test@example.com", password="wrong")); ok(b"Invalid email or password" in r.data, "wrong password message")
r = post(c, "/login", dict(email="test@example.com", password="secret1"))
ok(b"complete your health profile" in r.data, "login -> redirected to profile first time")

# profile validation
prof = dict(age="22", gender="Male", height="168", weight="55", activity_level="Moderately Active",
            fitness_goal="Weight Gain", diet_preference="Vegetarian", workout_level="Beginner", allergies="")
for field, val in [("age","-5"),("age","abc"),("age","200"),("height","5"),("height","999"),("weight","0"),("weight","nan"),("gender","Alien"),("fitness_goal","")]:
    p = dict(prof); p[field] = val
    r = post(c, "/profile", p); ok(b"alert-danger" in r.data, f"profile rejects {field}={val!r}")
r = post(c, "/profile", prof)
ok(r.request.path == "/health-conditions" and b"Before we build your meal plan" in r.data, "profile saved -> health history step first")
ok(c.get("/dashboard").status_code == 302 and "/health-conditions" in c.get("/dashboard").headers["Location"], "dashboard locked until health history answered")
ok(c.get("/meal-plan").status_code == 302, "meal plan locked until health history answered")
r = post(c, "/health-conditions", {"cond_diabetes": "current"}, page="/health-conditions")
ok(b"tick the confirmation box" in r.data, "conditions need consent")
r = post(c, "/health-conditions", {"action": "none"}, page="/health-conditions")
html = r.get_data(as_text=True)
ok("Hello, Test" in html, "no conditions -> dashboard")
for needle in ["19.5", "1,495", "2,620", "Weight Gain Diet", "Personalized meal plan", "Exercise plan", "Weight progress", "bmi-pin"]:
    ok(needle in html, f"dashboard contains {needle}")
ok(db.count_recommendations(1) == 1, "recommendation stored in DB")
ok(len(db.get_weight_logs(1)) == 1, "first weight log stored")

for u in ["/meal-plan", "/meal-plan?variation=1", "/meal-plan?variation=abc", "/meal-plan?variation=-4", "/exercises", "/profile"]:
    ok(c.get(u).status_code == 200, f"GET {u}")
a = c.get("/meal-plan").get_data(as_text=True); b = c.get("/meal-plan?variation=2").get_data(as_text=True)
ok(re.findall(r"fw-semibold\">([^<]+)<", a) != [] , "meal plan rows rendered")

# log weight -> recalculation
r = post(c, "/log-weight", dict(weight="57.5"), page="/dashboard"); ok(b"Weight updated" in r.data and b"57.5" in r.data, "log weight")
ok(db.count_recommendations(1) == 2, "recommendation recalculated and stored")
r = post(c, "/log-weight", dict(weight="-3"), page="/dashboard"); ok(b"alert-danger" in r.data, "log weight validation")

# safety cases through the ML pipeline
from utils import recommendations as rec
cases = {
 "underweight wants loss": dict(age=25,gender="Female",height=165,weight=45,activity_level="Sedentary",fitness_goal="Weight Loss",diet_preference="Vegan",workout_level="Beginner"),
 "obese wants gain": dict(age=40,gender="Male",height=170,weight=105,activity_level="Lightly Active",fitness_goal="Weight Gain",diet_preference="Non-Vegetarian",workout_level="Intermediate"),
 "small female loss (calorie floor)": dict(age=60,gender="Female",height=150,weight=50,activity_level="Sedentary",fitness_goal="Weight Loss",diet_preference="Vegetarian",workout_level="Beginner"),
 "advanced athlete muscle": dict(age=28,gender="Male",height=180,weight=80,activity_level="Extremely Active",fitness_goal="Muscle Gain",diet_preference="Non-Vegetarian",workout_level="Advanced"),
}
for name, p in cases.items():
    s = rec.build_health_summary(p)
    m = rec.generate_meal_plan(s["calorie_target"], s["protein_target"], s["effective_goal"], p["diet_preference"], "")
    e = rec.generate_exercise_plan(s["effective_goal"], p["workout_level"], p["activity_level"])
    print(f"   {name}: BMI {s['bmi']} {s['ml_category']} cal {s['calorie_target']} (ml {s['ml_calories']}, formula {s['formula_calories']}) plan {m['total_calories']} kcal, {len(e['exercises'])} exercises, adjusted={s['goal_adjusted']}")
    floor = 1500 if p["gender"]=="Male" else 1200
    ok(s["calorie_target"] >= floor, f"calorie floor ok: {name}")
    ok(not m["is_empty"] and not e["is_empty"], f"plans not empty: {name}")
    if name.startswith("advanced"):
        ok(all(x["difficulty"] in ("Beginner","Intermediate","Advanced") for x in e["exercises"]) and any(x["difficulty"]=="Advanced" for x in e["exercises"]), "advanced exercises used")
    if name.startswith("underweight"):
        ok(s["ml_category"] == "Maintenance Diet", "underweight + loss -> Maintenance (safety)")
    if name.startswith("obese"):
        ok(s["ml_category"] == "Weight Loss Diet", "obese + gain -> Weight Loss (safety)")

# allergies and diet rules
m = rec.generate_meal_plan(2200, 90, "Maintain Weight", "Vegan", "peanuts, nuts, gluten, soy")
foods = [r["food"] for r in m["meals"]]; print("   vegan/allergy foods:", foods)
ok(not any(w in " ".join(foods).lower() for w in ["peanut","almond","walnut","roti","toast","soy","tofu"]), "allergy filter works")
m = rec.generate_meal_plan(2200, 90, "Maintain Weight", "Vegetarian", "")
ok(not any(x["food"] in ("Boiled Eggs (2)","Chicken Curry with Rice") for x in m["meals"]), "vegetarian excludes non-veg")
m = rec.generate_meal_plan(2200, 90, "Maintain Weight", "Vegan", "milk dairy eggs fish nuts peanut gluten soy wheat")
print("   extreme allergy warnings:", m["warnings"], m["is_empty"])

# empty meal handling: block everything
rec._cache["meals"] = rec.load_meals().iloc[0:0]
m = rec.generate_meal_plan(2000, 80, "Weight Loss", "Vegan", ""); ok(m["is_empty"] and len(m["warnings"]) == 5, "empty meal list handled")
rec._cache.clear()

# missing ML model -> fallback, no crash
from model import prediction
import utils.constants as K
saved = prediction._loaded_models; prediction._loaded_models = None
orig = prediction.MODEL_PATH; prediction.MODEL_PATH = "/nonexistent/model.pkl"
s = rec.build_health_summary(cases["advanced athlete muscle"]); ok(not s["ml_available"] and s["calorie_target"] > 0, "missing model -> formula fallback")
r = post(c, "/profile", prof); ok(r.status_code == 200 and b"AI model not available" in r.data, "missing model message shown in web app")
prediction.MODEL_PATH = orig; prediction._loaded_models = saved


# ======================= NEW FEATURES (health conditions, USDA data) =======================
import json, shutil
from unittest import mock
from utils import conditions as cond, nutrition, usda_api
import pandas as pd

print("\n-- health conditions --")
def rules_for(**kw): return cond.analyze_conditions(kw)
def plan_for(rules, diet="Vegetarian"):
    return rec.generate_meal_plan(2200, 100, "Maintain Weight", diet, "", rules=rules)

base = plan_for(None)
dia = plan_for(rules_for(diabetes="current")); dia_past = plan_for(rules_for(diabetes="past"))
ok(dia["total_sugar"] < base["total_sugar"] and dia["macro_percent"]["carbs"] < base["macro_percent"]["carbs"], "diabetes lowers sugar and carb share")
ok(all(ch["status"] == "ok" for ch in dia["checks"]), "diabetes checks all within limit")
ok(rules_for(diabetes="past")["limits"]["max_sugar"] > rules_for(diabetes="current")["limits"]["max_sugar"], "past history uses gentler limits")
bp = plan_for(rules_for(high_bp="current"))
ok(bp["total_sodium"] < base["total_sodium"] and bp["low_salt"], "blood pressure lowers sodium (low-salt cooking)")
ok(bp["total_sodium"] <= 2000, "blood pressure plan under WHO sodium limit")
gl = plan_for(rules_for(celiac="current"))
meals = rec.load_meals()
gluten_foods = set(meals[meals["allergens"].str.contains("gluten")]["meal_name"])
ok(not any(m["food"] in gluten_foods for m in gl["meals"]), "celiac plan has no gluten meals")
lac = plan_for(rules_for(lactose="current"))
milk_foods = set(meals[meals["allergens"].str.contains("milk")]["meal_name"])
ok(not any(m["food"] in milk_foods for m in lac["meals"]), "lactose plan has no dairy meals")
hd = rec.generate_exercise_plan("General Fitness", "Advanced", "Very Active", rules_for(heart_disease="current"))
ok(all(e["difficulty"] == "Beginner" and e["type"] != "HIIT" for e in hd["exercises"]) and hd["safety_note"], "heart disease -> beginner, no HIIT, safety note")
for key in ["kidney_disease", "uses_insulin", "pregnancy", "eating_disorder", "other_serious"]:
    ok(rules_for(**{key: "current"})["blocked"], f"{key} blocks the plan")
ok(rules_for(eating_disorder="past")["blocked"], "past eating disorder blocks the plan")
ok(not rules_for(kidney_disease="past")["blocked"], "past kidney history does not block")
ok(cond.conditions_from_text("not json") == {} and cond.conditions_from_text('{"x":"current","diabetes":"bogus"}') == {}, "bad stored condition text handled")
form = {"cond_diabetes": "past", "cond_pregnancy": "past", "cond_high_bp": "hack"}
ok(cond.parse_conditions_form(form) == {"diabetes": "past"}, "form parsing ignores invalid answers")

print("\n-- conditions through the website --")
c2 = app.test_client()
post(c2, "/register", dict(name="Sam", email="sam@example.com", password="secret1", confirm_password="secret1"))
post(c2, "/login", dict(email="sam@example.com", password="secret1"))
post(c2, "/profile", prof)
r = post(c2, "/health-conditions", {"cond_diabetes": "current", "cond_high_bp": "past", "consent": "yes", "condition_notes": "metformin"}, page="/health-conditions")
html = r.get_data(as_text=True)
ok("Diabetes or prediabetes" in html and "Health-condition checks" in html and "Within limit" in html, "dashboard shows chips and condition checks")
ok("metformin" in c2.get("/health-conditions").get_data(as_text=True), "notes remembered")
ok(b"Health-condition checks" in c2.get("/meal-plan").data, "meal plan page shows checks")
r = post(c2, "/health-conditions", {"cond_kidney_disease": "current", "consent": "yes"}, page="/health-conditions")
ok(b"speak to a doctor" in r.data and b"Estimated total" not in r.data, "high-risk: dashboard shows no plan")
ok(b"talk to a doctor" in c2.get("/meal-plan").data and b"talk to a doctor" in c2.get("/exercises").data, "high-risk: meal and exercise pages blocked")
post(c2, "/health-conditions", {"action": "none"}, page="/health-conditions")
ok(b"Estimated total" in c2.get("/dashboard").data, "clearing conditions restores the plan")

print("\n-- database migration --")
import sqlite3
old_db = os.path.join(tmp, "old.db")
conn = sqlite3.connect(old_db)
conn.executescript("""CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, created_at TEXT);
 CREATE TABLE profiles (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE, age INTEGER, gender TEXT, height REAL, weight REAL,
 activity_level TEXT, fitness_goal TEXT, diet_preference TEXT, workout_level TEXT, allergies TEXT);
 INSERT INTO users VALUES (1,'Old','old@x.com','h','2026-01-01');
 INSERT INTO profiles VALUES (1,1,30,'Male',170,70,'Sedentary','Weight Loss','Vegetarian','Beginner','');""")
conn.commit(); conn.close()
real_path = db.DB_PATH; db.DB_PATH = old_db
db.init_db(); db.migrate_db(); db.migrate_db()          # twice: must be safe to repeat
p = db.get_profile(1)
ok(p["conditions_answered"] == 0 and p["conditions"] == "" and p["age"] == 30, "old database upgraded, old data kept")
db.DB_PATH = real_path

print("\n-- nutrition pipeline --")
ing = nutrition.load_ingredients()
meals_calc = nutrition.compute_meals().set_index("meal_name")
grams = {"rice_white": 180, "lentils": 150, "oil": 6, "cucumber": 50, "tomato": 50, "salt": 2.5}
expected = sum(ing.loc[k, "calories"] * g / 100 for k, g in grams.items())
ok(abs(meals_calc.loc["Dal Rice with Salad", "calories"] - expected) <= 1, "meal calories = sum of ingredient calories")
saved = pd.read_csv(os.path.join("data", "meals.csv")).set_index("meal_name")
ok(len(saved) == 78 and (saved["calories"] == meals_calc["calories"]).all(), "meals.csv matches the recipes")
ok((saved["salt_sodium"] <= saved["sodium"]).all() and (saved["calories"] > 0).all(), "meal data sane (salt part <= sodium, calories > 0)")

print("\n-- USDA client (mocked, no internet used) --")
sample = {"foodNutrients": [
    {"nutrientId": 2047, "nutrientNumber": "957", "unitName": "KCAL", "value": 116},
    {"nutrientId": 1008, "nutrientNumber": "208", "unitName": "KJ", "value": 485},      # kilojoules must be ignored
    {"nutrientId": 1003, "unitName": "G", "value": 9.0}, {"nutrientId": 1005, "unitName": "G", "value": 20.1},
    {"nutrientId": 1004, "unitName": "G", "value": 0.4}, {"nutrientId": 1079, "unitName": "G", "value": 7.9},
    {"nutrientId": 2000, "unitName": "G", "value": 1.8}, {"nutrientId": 1093, "unitName": "MG", "value": 2}]}
n = usda_api.extract_nutrients(sample)
ok(n["calories"] == 116 and n["protein"] == 9.0 and n["fibre"] == 7.9 and n["sugar"] == 1.8 and n["sodium"] == 2, "nutrients parsed (kcal, not kJ)")
with mock.patch("utils.usda_api.get_usda_key", return_value=""):
    try: usda_api.search_foods("rice"); ok(False, "missing key should raise")
    except usda_api.UsdaError as e: ok("No USDA API key" in str(e), "missing key gives a clear message")

class FakeResponse:
    def __init__(self, data): self.data = data
    def read(self): return json.dumps(self.data).encode()
    def __enter__(self): return self
    def __exit__(self, *a): return False
payload = {"foods": [{"fdcId": 123, "description": "Lentils, mature seeds, cooked, boiled, without salt", "dataType": "SR Legacy", **sample}]}
with mock.patch("utils.usda_api.urllib.request.urlopen", return_value=FakeResponse(payload)) as fake:
    res = usda_api.search_foods("lentils", api_key="TESTKEY")
    sent = fake.call_args[0][0]
    ok(res[0]["fdc_id"] == 123 and res[0]["nutrients"]["calories"] == 116, "search results parsed")
    ok("TESTKEY" not in sent.full_url and sent.get_header("X-api-key") == "TESTKEY", "key sent in header, not in the URL")
import urllib.error
for code, word in [(403, "rejected"), (429, "rate limit"), (500, "HTTP 500")]:
    err = urllib.error.HTTPError("u", code, "x", {}, None)
    with mock.patch("utils.usda_api.urllib.request.urlopen", side_effect=err):
        try: usda_api.search_foods("rice", api_key="K"); ok(False, "should raise")
        except usda_api.UsdaError as e: ok(word in str(e), f"HTTP {code} gives a friendly message")
with mock.patch("utils.usda_api.urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
    try: usda_api.search_foods("rice", api_key="K"); ok(False, "should raise")
    except usda_api.UsdaError as e: ok("internet" in str(e), "no internet gives a friendly message")

# verification logic with a temporary copy of ingredients.csv
backup = os.path.join(tmp, "ingredients_copy.csv"); shutil.copy(nutrition.INGREDIENTS_CSV, backup)
real_csv = nutrition.INGREDIENTS_CSV; nutrition.INGREDIENTS_CSV = backup
def fake_search(query):
    table = {
      "Lentils, mature seeds, cooked, boiled, without salt": ("Lentils, mature seeds, cooked, boiled, without salt", 116),
      "Rice, white, long-grain, regular, enriched, cooked": ("Rice, white, long-grain, regular, enriched, RAW", 365)}   # wrong match: raw instead of cooked
    if query in table:
        name, kcal = table[query]
        return [{"fdc_id": 1, "description": name, "data_type": "SR Legacy",
                 "nutrients": {"calories": kcal, "protein": 9.0, "carbs": 20.0, "fat": 0.4, "fibre": 7.9, "sugar": 1.8, "sodium": 2}}]
    return []
report = nutrition.update_ingredients_from_usda(fake_search, usda_api.best_match, cache={}, log=lambda *_: None)
status = {r["key"]: r["status"] for r in report}
ok(status["lentils"] == "VERIFIED", "good USDA match is accepted")
ok(status["rice_white"].startswith("REVIEW"), "suspicious match (raw vs cooked) is NOT applied")
ok(status["paneer"] == "ESTIMATE" and status["oil"] == "NOT FOUND", "no-USDA items stay estimates; missing results reported")
after = pd.read_csv(backup).set_index("key")
ok(after.loc["lentils", "source"] == "USDA FoodData Central" and after.loc["rice_white", "calories"] == 130, "ingredients file updated safely")
stats = nutrition.verification_stats(); ok(stats["verified"] == 1 and stats["estimates"] == 5, "verification stats counted")
nutrition.INGREDIENTS_CSV = real_csv

print("\n-- food lookup page --")
c3 = app.test_client()
post(c3, "/register", dict(name="Lee", email="lee@example.com", password="secret1", confirm_password="secret1"))
post(c3, "/login", dict(email="lee@example.com", password="secret1"))
with mock.patch("app.get_usda_key", return_value=""), mock.patch("utils.usda_api.get_usda_key", return_value=""):
    r = c3.get("/food-lookup?q=rice"); ok(b"USDA API key not set" in r.data and r.status_code == 200, "lookup without key shows setup help")
with mock.patch("app.get_usda_key", return_value="K"), mock.patch("app.usda_api.search_foods", return_value=[{"fdc_id": 9, "description": "Lentils test", "data_type": "SR Legacy", "nutrients": {"calories": 116, "protein": 9, "carbs": 20, "fat": 0.4, "fibre": 7.9, "sugar": 1.8, "sodium": 2}}]):
    r = c3.get("/food-lookup?q=lentils"); ok(b"Lentils test" in r.data and b"FDC ID 9" in r.data, "lookup shows results")
with mock.patch("app.get_usda_key", return_value="K"), mock.patch("app.usda_api.search_foods", side_effect=usda_api.UsdaError("USDA rate limit reached")):
    r = c3.get("/food-lookup?q=x"); ok(b"rate limit" in r.data and r.status_code == 200, "lookup shows API errors politely")
ok(app.test_client().get("/food-lookup").status_code == 302, "food lookup needs login")
ok(b"Food data you can trace" in c3.get("/").data and b"Where the food data comes from" in c3.get("/about").data, "home and about mention the data source")

# logout
r = c.get("/logout", follow_redirects=True); ok(b"logged out" in r.data, "logout")
ok(c.get("/dashboard").status_code == 302, "dashboard locked after logout")
print("\nALL TESTS PASSED")
