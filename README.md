# Smart Diet & Fitness Recommendation System

> AI-powered personalized diet and fitness recommendations based on your health profile.

An MCA (Artificial Intelligence & Machine Learning) college project built with **Python, Flask, SQLite, scikit-learn and Bootstrap 5**.

> **Medical disclaimer:** All recommendations are for general wellness and educational purposes only.
> The system does not diagnose diseases or provide medical treatment and is not a substitute for
> advice from a doctor or qualified dietitian.

---

## Objective

Build an intelligent web application that collects a user's health and fitness details, calculates
BMI, BMR and daily calories, uses **machine learning** to choose a suitable plan and calorie target,
and then recommends a personalized **meal plan** and **exercise plan**. Everything is saved in a
local SQLite database and shown on a clean dashboard.

## Technologies Used

```text
Python        Flask         SQLite        USDA FoodData Central API
HTML5         CSS3          Bootstrap 5 (stored locally, works offline)
JavaScript    Pandas        NumPy
Scikit-learn  Joblib
```

## Features

- Register, login and logout (passwords stored as secure hashes, sessions, CSRF protection)
- Health profile form with full validation and a **live BMI preview**
- BMI value and category (Underweight / Normal / Overweight / Obese) with a visual BMI scale
- BMR (Mifflin-St Jeor), TDEE and a safe daily calorie target (never below 1500 kcal male / 1200 kcal female)
- Protein target based on goal and body weight
- **Machine learning**: Random Forest classifier (plan category) + Random Forest regressor (daily calories)
- Safety rule: if the user's goal is unsafe for their BMI (for example weight loss when underweight), the AI suggests a safer plan and explains why
- Meal plan with 5 meals (breakfast, mid-morning snack, lunch, evening snack, dinner) from a 78-item food dataset
  - Filters by Vegetarian / Non-Vegetarian / Vegan and by allergies
  - Scales portions (0.5 to 2 servings) to match the calorie target
  - "Generate another plan" button for variety
- Exercise plan from a 37-item dataset, based on goal, workout level and activity level (sets, reps, duration)
- Dashboard with stat cards, tables, badges, progress bars and weight-progress tracking
- Everything saved in SQLite: users, profiles, recommendation history, weight log
- **Health-conditions step** before any meal plan: asks about current and past diseases (diabetes, blood pressure, cholesterol, heart disease, thyroid, PCOS, gluten and lactose intolerance). The plan changes automatically (sugar, carbs, salt, fat, fibre limits, removed foods, gentler exercise)
- Higher-risk conditions (kidney disease, insulin use, pregnancy, eating disorder, cancer treatment, liver disease) get **no plan**, only a clear "see a doctor" message
- **Food data from USDA FoodData Central** (official US government database): meals are built from ingredients verified through the USDA API, with a live **Food lookup** page
- Animated, modern home page with custom SVG illustrations, scroll animations and count-up numbers
- Works offline after `pip install` (internet is needed only for the optional USDA steps)

## Installation (VS Code on Windows)

1. Install **Python 3.9 or newer** from python.org (tick *Add Python to PATH*).
2. Open the project folder in VS Code (`File > Open Folder`).
3. Open the terminal in VS Code (`Terminal > New Terminal`) and run these one by one:

```bash
python -m venv venv
```

```bash
venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

> If PowerShell blocks activation ("running scripts is disabled"), run this once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and activate again.
> Or switch the VS Code terminal to **Command Prompt**.

## Running the Project

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

- The SQLite database `database.db` is created automatically on first run.
- If `model/trained_model.pkl` is missing (or was made by a different scikit-learn version), the app trains a new model automatically in a few seconds.
- To retrain manually (optional):

```bash
python model/generate_training_data.py
python model/train_model.py
```

### Quick demo

1. Click **Register**, create an account, then **Login**.
2. Fill the profile form, for example: Age 22, Male, 168 cm, 55 kg, Moderately Active, Weight Gain, Vegetarian, Beginner.
3. Press **Generate my plan** to see the dashboard (BMI 19.5, BMR 1,495, TDEE 2,317, about 2,620 kcal target).
4. Open **Meal plan** and press **Generate another plan** to see different foods.

## USDA API Key (food data)

The meal nutrition comes from ingredient values that are verified against the official
**USDA FoodData Central** database. The project already contains pre-filled values, so it runs
without a key, but the pages will say "not yet verified" until you run the fetch step.

1. Get a free key: https://fdc.nal.usda.gov/api-key-signup (it is emailed to you).
2. In the project folder, copy `.env.example` to a new file named `.env`
   (in VS Code: right-click `.env.example`, Copy, Paste, rename to `.env`).
3. Open `.env` and replace the text so it looks like this (use your own key):

```text
USDA_API_KEY=abcd1234yourkeyhere
```

4. With the virtual environment active, run once:

```bash
python data/fetch_nutrition.py
```

This checks about 48 ingredients with USDA, updates `data/ingredients.csv`, rebuilds `data/meals.csv`
and writes a review report `data/usda_matches.csv`. Open that report and check the `usda_food`
column to confirm USDA matched the right food. A safety check ignores any match whose calories are
more than 35% different from the pre-filled value (status `REVIEW`) so a wrong match never corrupts the data.

5. Restart `python app.py`. The About page now shows how many ingredients are verified, and the
   **More > Food lookup (USDA)** page searches USDA live.

Notes: never share `.env` or put your key in the code (`.gitignore` already excludes it). The free key allows
1,000 requests per hour; the fetch step uses about 50 and caches results in `data/usda_cache.json`.
Paneer, soya chunks, poha, idli and makhana have no USDA equivalent and stay as labelled estimates.

## How the Food Data Works

```text
data/ingredients.csv   nutrition per 100 g of each ingredient (verified with USDA)
data/meal_recipes.csv  each meal = ingredients + grams
utils/nutrition.py     meal nutrition = sum of ingredient nutrition  ->  data/meals.csv
```

Meals therefore carry calories, protein, carbs, fat, **fibre, sugar and sodium**, a `source`
label and the share of ingredients that are verified. Recipe grams are typical home portions
(my estimates), so real dishes vary.

## Health Conditions (current and past)

After the profile form the app shows the **Health history** page. For each condition the user picks
*No*, *In the past* or *Currently*. Rules live in `utils/conditions.py` (rule-based on purpose, so every
decision can be explained in a viva). The ML models still choose the plan type and calories.

| Condition | What changes |
|-----------|--------------|
| Diabetes / prediabetes | total sugars at most 40 g, carbohydrates at most 50% of calories, fibre at least 30 g per day |
| High blood pressure | sodium at most 2000 mg (WHO advice) with low-salt cooking (half the added salt), no HIIT |
| High cholesterol | fat at most 30% of calories, fibre at least 25 g |
| Heart disease | fat, sodium and fibre limits, Beginner exercises only, no HIIT, doctor clearance note |
| PCOS / PCOD | carbohydrate, sugar and fibre limits |
| Thyroid | guidance notes only |
| Gluten / lactose intolerance | meals with gluten / milk are removed |
| Kidney disease, insulin use, pregnancy or breastfeeding, eating disorder, cancer treatment / liver disease / recent surgery | **no plan**: message to see a doctor |

"In the past" uses gentler limits (maximums x 1.25, minimums x 0.85). The meal plan page lists each limit
with a green / yellow / red check. These are general guidelines, not medical advice.

**Where answers are stored:** only in `database.db` on your own computer (`profiles` table). Nothing is sent to the internet
(except searches you make on the Food lookup page).

## Project Structure

```text
Smart-Diet-Fitness-Recommendation-System/
|-- app.py                      Flask app: routes, login, forms
|-- requirements.txt            Python packages to install
|-- README.md                   This file
|-- test_app.py                 Automatic tests (python test_app.py)
|-- .env.example                Template for your USDA key (copy to .env)
|-- PROJECT_DOCUMENTATION.md    Full project report text
|-- VIVA_QUESTIONS.md           66 viva questions with answers
|-- database.db                 SQLite database (created automatically)
|
|-- model/
|   |-- generate_training_data.py   Creates data/training_data.csv (4000 rows)
|   |-- train_model.py              Trains and saves the two ML models
|   |-- prediction.py               Loads the models and predicts for one user
|   |-- trained_model.pkl           Saved models (joblib)
|   `-- metrics.json                Accuracy / precision / recall / F1 / MAE / R2
|
|-- data/
|   |-- ingredients.csv         53 ingredients per 100 g (USDA-verified after fetch step)
|   |-- meal_recipes.csv        78 meals as ingredient lists
|   |-- meals.csv               78 meals built from the recipes (calories, macros, fibre, sugar, sodium)
|   |-- fetch_nutrition.py      Verifies ingredients with the USDA API
|   |-- exercises.csv           37 exercises: type, difficulty, muscle, duration, sets, reps, goals
|   `-- training_data.csv       ML training dataset
|
|-- utils/
|   |-- constants.py            Shared lists, limits and file paths
|   |-- calculations.py         BMI, BMR, TDEE, calorie and protein formulas
|   |-- recommendations.py      ML + meal plan + exercise plan logic
|   |-- conditions.py           Health-condition rules
|   |-- nutrition.py            Builds meals from ingredients, USDA update logic
|   |-- usda_api.py             USDA FoodData Central client
|   |-- config.py               Reads the key from .env
|   |-- validators.py           Input checking
|   `-- database.py             All SQLite code
|
|-- templates/                  Jinja2 HTML pages (base, index, login, register, dashboard,
|                               profile, health_conditions, meal_plan, exercises, food_lookup, about, ...)
`-- static/
    |-- css/style.css           Custom design
    |-- images/                 Animated SVG illustrations (plate, runner, shield, bowl, pulse)
    |-- js/script.js            Validation, live BMI preview, scroll animations, count-up
    `-- vendor/                 Bootstrap 5 + Bootstrap Icons (local copy, no internet needed)
```

## Machine Learning

| Item | Details |
|------|---------|
| **Dataset** | `data/training_data.csv`: 4000 synthetic people. Labels follow standard dietitian rules (BMI category, Mifflin-St Jeor, goal adjustments). |
| **Model 1** | `RandomForestClassifier` predicts the **plan category** |
| **Features (Model 1)** | age, gender, height, weight, BMI, activity level, fitness goal, diet preference, workout level |
| **Target (Model 1)** | Weight Loss Diet, Weight Gain Diet, Maintenance Diet, Muscle Gain Diet, General Fitness Plan |
| **Model 2** | `RandomForestRegressor` predicts the **daily calories** |
| **Features (Model 2)** | age, gender, height, weight, activity level, plan category |
| **Target (Model 2)** | calorie requirement (kcal) |
| **Training** | 80% training / 20% testing split (`train_test_split`, `random_state=42`) |
| **Prediction** | `model/prediction.py` encodes the user's profile as numbers and calls `predict()` |
| **Safety check** | If the predicted calories differ from the formula by more than 10%, the formula value is used |

**Where ML is used:** `utils/recommendations.py -> build_health_summary()` calls
`model/prediction.py -> predict_recommendation()`. The predicted plan category decides which goal
drives the meal and exercise plans.

**Honest note:** the data is synthetic and the labels come from rules, so the classifier scores
about 100%. A real-world system would need real, clinically reviewed data. The scores are shown on the About page.

## BMI Calculation

```text
BMI = weight (kg) / [height (m)]^2

Example: 65 kg, 175 cm  ->  65 / (1.75 x 1.75) = 21.2  (Normal)
```

| BMI | Category |
|-----|----------|
| below 18.5 | Underweight |
| 18.5 - 24.9 | Normal |
| 25 - 29.9 | Overweight |
| 30 and above | Obese |

## BMR and TDEE

**BMR (Mifflin-St Jeor)** is the calories the body burns at complete rest:

```text
Male   : BMR = (10 x weight) + (6.25 x height) - (5 x age) + 5
Female : BMR = (10 x weight) + (6.25 x height) - (5 x age) - 161
```

**TDEE** = BMR x activity factor

| Activity | Factor |
|----------|--------|
| Sedentary | 1.2 |
| Lightly Active | 1.375 |
| Moderately Active | 1.55 |
| Very Active | 1.725 |
| Extremely Active | 1.9 |

**Daily calorie target** = TDEE adjusted by goal: Weight Loss -500, Weight Gain +400,
Muscle Gain +300, Maintain / General Fitness 0. A safety floor of 1500 kcal (male) / 1200 kcal (female) is always applied.

Worked example (22 years, male, 168 cm, 55 kg, Moderately Active, Weight Gain):
BMR = 550 + 1050 - 110 + 5 = **1495**; TDEE = 1495 x 1.55 = **2317**; formula target = 2317 + 400 = 2717.
The AI predicts about 2620, which is within 10% of the formula, so the AI value is used.

## Testing Instructions

**Automatic tests:** run `python test_app.py`. It checks every page, login, validation, the database, the ML safety rules, allergy filtering and the missing-model fallback (about 115 checks). The last line should say `ALL TESTS PASSED`.

**Manual tests:**

1. Register and log in, then try invalid inputs (age -5, height 5, empty fields). A red message should appear and the app must not crash.
2. Register with an existing email. You should see "already exists".
3. Try a wrong password. You should see "Invalid email or password".
4. Test the safety logic: Female, 165 cm, 45 kg, Weight Loss. The AI recommends a *Maintenance Diet* and explains why.
5. Test allergies: enter `peanuts, milk`. Those foods disappear from the meal plan.
6. Delete `model/trained_model.pkl` and restart. The model is retrained automatically.
7. Health history: choose *Diabetes - Currently* and compare the meal plan sugar and carbs with a plan without conditions. Choose *Kidney disease - Currently* and check that no plan is shown.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python` not recognised | Reinstall Python and tick *Add Python to PATH* |
| `No module named flask` | Activate the venv (`venv\Scripts\activate`) and run `pip install -r requirements.txt` |
| Port 5000 already in use | Close the other app, or change `port=5000` at the bottom of `app.py` |
| Model warning on start | The app retrains automatically, or run `python model/train_model.py` |
| Want a fresh start | Stop the app and delete `database.db` |
| Food lookup says key not set | Check that `.env` (not `.env.example`) exists in the project folder and restart the app |
| `python data/fetch_nutrition.py` says key rejected | Copy the key again from the email, without spaces |
| Existing `database.db` from the old version | It is upgraded automatically; users are asked the health history question once |

## Future Scope

- Mobile application (Android / iOS)
- Voice assistant for hands-free meal and workout guidance
- Wearable integration (smart watch steps, heart rate, sleep)
- More advanced ML models trained on real, clinically reviewed datasets (XGBoost, neural networks)
- Real-time health tracking and weekly progress charts
- Larger food database with regional cuisines and barcode scanning
- Dietitian-reviewed condition rules and more conditions
- Indian Food Composition Tables (IFCT) as an additional verified data source
- Multi-language support
