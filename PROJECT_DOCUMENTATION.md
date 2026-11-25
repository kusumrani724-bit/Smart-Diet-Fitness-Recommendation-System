# Project Documentation

## Smart Diet & Fitness Recommendation System

**Course:** MCA (Artificial Intelligence & Machine Learning)
**Technology:** Python, Flask, SQLite, scikit-learn, Bootstrap 5

> **Medical disclaimer:** The recommendations produced by this system are for general wellness and
> educational purposes only. The system does not diagnose diseases or provide medical treatment and
> is not a substitute for professional medical advice.

---

## 1. Abstract

Many people want to improve their diet and fitness but do not know how many calories they need,
what to eat, or which exercises suit them. This project presents the **Smart Diet & Fitness
Recommendation System**, a web application that collects a user's health details (age, gender,
height, weight, activity level, goal, diet type and workout level), calculates BMI, BMR and TDEE,
and uses **machine learning** (Random Forest classification and regression) to predict a suitable
plan category and daily calorie requirement. Using these results, the system builds a personalized
five-meal diet plan from a food dataset and a personalized exercise plan from an exercise dataset.
The application is built with Flask and SQLite, stores user data and recommendation history, and
presents results on a responsive Bootstrap dashboard. Before a meal plan is created, the system asks about current and past health conditions (for example diabetes or high blood pressure) and adjusts the plan with explainable rules; higher-risk conditions are referred to a doctor. Food nutrition values are built from ingredients verified against the USDA FoodData Central database. The application runs on a normal laptop and needs the internet only for the optional USDA steps.

## 2. Introduction

Healthcare informatics applies information technology to health and wellness. Lifestyle-related
problems such as obesity, underweight and poor nutrition are increasing. Personalized guidance usually
needs a dietitian or trainer, which not everyone can afford. Artificial Intelligence and Machine
Learning can automate part of this guidance by learning patterns from data and producing instant,
personalized suggestions. This project combines standard health formulas with machine learning and a
recommendation engine in a simple, beginner-friendly web application.

## 3. Problem Statement

Generic diet charts and workout plans ignore individual differences such as body size, age, gender,
activity level, food preference and fitness goal. Users also often choose unsafe goals (for example
weight loss while already underweight). There is a need for an easy-to-use system that gives
**personalized, safe and instant** diet and exercise suggestions, with clear explanations, for
general wellness.

## 4. Existing System

- Printed or online generic diet charts that are the same for everyone.
- Separate BMI or calorie calculators that give numbers but no meal or exercise plan.
- Commercial fitness apps that are paid, need internet and API access, and are not suitable for study.
- Manual consultation with dietitians, which is costly and not always available.

**Drawbacks:** no personalization, no machine learning, no safety checks, no combined view of BMI,
calories, meals and exercises, and limited data storage.

## 5. Proposed System

A web application that:

1. Registers and authenticates users securely.
2. Collects a detailed health profile with input validation.
3. Calculates BMI, BMR and TDEE using standard formulas.
4. Uses a **Random Forest classifier** to predict the best plan category and a **Random Forest
   regressor** to predict daily calories.
5. Checks the ML output against the formula for safety.
6. Recommends meals (filtered by diet and allergies) and exercises (filtered by goal and level).
7. Stores everything in SQLite and displays it on a dashboard with progress tracking.

## 6. Objectives

1. Collect user health and fitness information.
2. Calculate BMI and classify it.
3. Calculate BMR and TDEE (daily calories).
4. Use machine learning to predict a plan category and calorie requirement.
5. Generate a personalized meal plan close to the calorie target.
6. Generate a personalized exercise plan.
7. Display all results on a professional dashboard.
8. Store users, profiles and recommendations in a database.
9. Keep the project simple, offline and suitable for a college demonstration.

## 7. Prerequisite Skills

| Area | Skills needed |
|------|---------------|
| Programming | Python basics: functions, dictionaries, lists, file handling |
| Web | HTML, CSS, Bootstrap, basic JavaScript, Flask routes and Jinja templates |
| Database | SQL basics (CREATE, INSERT, SELECT, UPDATE), SQLite |
| Data / ML | pandas, NumPy, train-test split, Random Forest, accuracy and other metrics |
| Domain | BMI, BMR, TDEE, macronutrients (protein, carbohydrates, fat) |

## 8. Technologies Used

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript | Pages, responsive layout, form validation, live BMI preview |
| Backend | Python 3, Flask | Routing, sessions, business logic |
| Database | SQLite (`sqlite3` module) | Users, profiles, recommendations, weight log |
| ML | scikit-learn, pandas, NumPy, joblib | Training, prediction, data handling, saving the model |
| Security | Werkzeug password hashing, Flask sessions, CSRF token | Safe authentication |
| External data | USDA FoodData Central API (urllib, API key in `.env`) | Authorized nutrition data for ingredients |
| Animation | CSS keyframes, SVG animation, IntersectionObserver | Animated home page and scroll effects |

## 9. System Requirements

**Hardware:** any laptop or PC with 4 GB RAM, 500 MB free disk space.
**Software:** Windows 10/11 (also works on Linux/macOS), Python 3.9 or newer, VS Code, a web browser.
**Internet:** needed to run `pip install` and, optionally, to run `python data/fetch_nutrition.py` and the Food lookup page (free USDA API key).
The application itself runs offline (Bootstrap files and data are stored inside the project).

## 10. System Architecture

```text
+--------------------------- Browser ---------------------------+
|  HTML + Bootstrap + CSS + JavaScript (templates / static)     |
+------------------------------+--------------------------------+
                               | HTTP requests (forms, pages)
+------------------------------v--------------------------------+
|                    Flask application (app.py)                 |
|  routes - sessions - login_required - CSRF - error handlers   |
+--------+----------------+-------------------+-----------------+
         |                |                   |
+--------v------+  +------v---------+  +------v-----------------+
| utils/        |  | utils/         |  | utils/recommendations  |
| validators.py |  | database.py    |  |  + model/prediction.py |
| (input check) |  | (SQLite)       |  |  (ML + meals + exercise)|
+---------------+  +------+---------+  +------+-----------------+
                          |                   |
                 +--------v-------+   +-------v----------------+
                 | database.db    |   | data/*.csv + model.pkl |
                 +----------------+   +------------------------+
```

The design follows a layered approach: presentation (templates), application (Flask routes),
business logic (utils and model) and data (SQLite and CSV files).

## 11. Data Flow

```text
User -> Register / Login -> Enter health profile
     -> Validation (validators.py)
     -> Save profile (SQLite)
     -> BMI -> BMR -> TDEE                       (calculations.py)
     -> ML classifier: plan category             (prediction.py)
     -> ML regressor: daily calories             (prediction.py)
     -> Safety check against formula             (recommendations.py)
     -> Protein target
     -> Meal plan from meals.csv                 (recommendations.py)
     -> Exercise plan from exercises.csv         (recommendations.py)
     -> Save recommendation (SQLite)
     -> Dashboard
```

## 12. Database Design

SQLite database file `database.db`, created automatically by `init_db()`.

**users**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| name | TEXT | |
| email | TEXT | Unique |
| password | TEXT | Hashed (never plain text) |
| created_at | TEXT | Default current timestamp |

**profiles** (one per user)

| Column | Type |
|--------|------|
| id | INTEGER, primary key |
| user_id | INTEGER, unique, foreign key to users.id |
| age, height, weight | INTEGER / REAL |
| gender, activity_level, fitness_goal | TEXT |
| diet_preference, workout_level, allergies | TEXT |

**recommendations** (history: a new row each time results are calculated)

| Column | Type |
|--------|------|
| id, user_id | INTEGER |
| bmi, bmi_category, bmr, tdee | REAL / TEXT / INTEGER |
| calorie_target, protein_target | INTEGER |
| ml_category, ml_confidence, ml_calories | TEXT / REAL / INTEGER |
| created_at | TEXT |

**weight_logs** (for the progress section)

| Column | Type |
|--------|------|
| id, user_id | INTEGER |
| weight | REAL |
| logged_at | TEXT |

**profiles** also stores the health history: `conditions` (JSON such as {"diabetes": "current", "high_bp": "past"}), `condition_notes` (free text, not used in calculations) and `conditions_answered` (0 or 1). Older databases are upgraded automatically by `migrate_db()`.

Relationships: one user has one profile, many recommendations and many weight logs.
The meal and exercise datasets are kept in CSV files and loaded with pandas.

## 13. ML Methodology

**Problem 1: classification.** Predict which plan category suits a person.
**Problem 2: regression.** Predict the daily calories for that plan.

1. **Dataset creation.** `generate_training_data.py` creates 4000 synthetic people with realistic
   heights, BMI values, ages, genders, activity levels, goals, diets and workout levels. Each row is
   labelled with dietitian-style rules: for example an underweight person asking for weight loss is
   labelled *Maintenance Diet*, and an obese person asking for weight gain is labelled *Weight Loss
   Diet*. Calories are computed with the standard formulas plus a little random variation.
2. **Encoding.** Text values (gender, activity, goal, etc.) are converted to numbers.
3. **Split.** 80% training data, 20% test data.
4. **Algorithm.** Random Forest (an ensemble of decision trees) is used for both tasks because it is
   accurate, handles mixed features, needs little tuning and can show feature importance.
5. **Evaluation.** Classifier: accuracy, precision, recall, F1-score. Regressor: MAE and R-squared.
   Results are saved in `model/metrics.json` and shown on the About page.
6. **Deployment.** Both models are saved with joblib in `trained_model.pkl` and loaded by `prediction.py`.
7. **Safety layer.** If the predicted calories differ from the formula by more than 10%, or the
   model is unavailable, the formula value is used.

Typical results (4000 rows): classifier accuracy about 100% (labels follow clear rules),
calorie model MAE about 83 kcal and R-squared about 0.96.

**Feature importance** (classifier): the fitness goal and BMI are the most important features,
which matches real dietitian reasoning.

## 14. BMI Calculation

```text
BMI = weight (kg) / [height (m)]^2        height (m) = height (cm) / 100
```

Example: 65 kg, 175 cm gives 65 / (1.75 x 1.75) = 21.2 (Normal).
Categories: below 18.5 Underweight, 18.5 to 24.9 Normal, 25 to 29.9 Overweight, 30 and above Obese.
BMI is a screening measure and does not directly measure body fat or health.

## 15. BMR Calculation

Mifflin-St Jeor equation (weight in kg, height in cm, age in years):

```text
Male   : BMR = 10 x weight + 6.25 x height - 5 x age + 5
Female : BMR = 10 x weight + 6.25 x height - 5 x age - 161
```

Example: male, 22 years, 168 cm, 55 kg. BMR = 550 + 1050 - 110 + 5 = **1495 kcal/day**.

## 16. TDEE Calculation

```text
TDEE = BMR x Activity Factor
```

| Activity level | Factor |
|----------------|--------|
| Sedentary | 1.2 |
| Lightly Active | 1.375 |
| Moderately Active | 1.55 |
| Very Active | 1.725 |
| Extremely Active | 1.9 |

Example: 1495 x 1.55 = **2317 kcal/day**.

**Goal adjustment:** Weight Loss -500, Weight Gain +400, Muscle Gain +300, Maintain and General
Fitness 0. Minimum calories are 1500 (male) and 1200 (female). Protein target per kg of body weight:
Loss 1.6 g, Gain 1.4 g, Muscle Gain 1.8 g, Maintain 1.0 g, General Fitness 1.2 g.

## 17. Recommendation Methodology

**Meal recommendation (content-based filtering with scoring)**

1. Filter `meals.csv` by diet type (Vegan sees vegan meals, Vegetarian sees vegan and vegetarian,
   Non-Vegetarian sees all).
2. Remove meals containing the user's allergens (keyword matching, for example "nuts" removes nut and peanut items).
3. Split the calorie target across five meals: breakfast 25%, mid-morning snack 10%, lunch 30%,
   evening snack 10%, dinner 25%.
4. For each meal slot, score every candidate and portion size (0.5, 0.75, 1, 1.25, 1.5, 2 servings).
   The score combines calorie error (most important), goal match, protein gap and a small portion penalty.
5. Choose the lowest score. The "Generate another plan" button picks randomly among the top four different meals.
6. Show total calories and protein against the targets.

**Exercise recommendation**

1. Keep exercises at or below the user's workout level (Beginner, Intermediate, Advanced) and tagged for the goal.
2. Prefer the highest allowed difficulty. For weight loss, prefer higher calorie burn.
3. Pick types in a goal-specific order (for example Weight Loss: Cardio, HIIT, Strength, Core, Flexibility).
4. The number of exercises and the duration depend on the activity level (4 exercises for Sedentary up to 7 for Extremely Active).

**Health-condition rules (added step before the meal plan).** After the profile form, the user answers *No / In the past / Currently* for each condition. `utils/conditions.py` converts the answers into daily limits (for example diabetes: sugars at most 40 g and carbohydrates at most 50% of calories; blood pressure: sodium at most 2000 mg following WHO advice, with low-salt cooking), removed allergens (celiac removes gluten, lactose intolerance removes milk) and exercise safety rules (heart disease: Beginner level, no HIIT). The meal scorer adds a penalty to meals that break a limit, so compliant meals win. Past conditions use gentler limits (maximums x 1.25, minimums x 0.85). A table of checks (within limit / slightly off / over limit) is shown to the user. Higher-risk conditions (kidney disease, insulin use, pregnancy or breastfeeding, eating disorder, cancer treatment, liver disease, recent surgery) produce no plan and a message to consult a doctor. The rules are deliberately rule-based (not machine-learned) because no real medical dataset was available and every decision must be explainable.

**Food data pipeline.** `ingredients.csv` holds nutrition per 100 g for 53 ingredients; `fetch_nutrition.py` searches the USDA FoodData Central API (Foundation and SR Legacy generic foods), compares each match with the pre-filled value and accepts it only if calories differ by less than 35% (otherwise status REVIEW, to avoid wrong matches such as raw instead of cooked). `meal_recipes.csv` lists each meal as ingredients with grams, and `nutrition.py` sums them into `meals.csv` (calories, protein, carbs, fat, fibre, sugar, sodium, source). Ingredients with no USDA equivalent (paneer, soya chunks, poha, idli, makhana) are labelled estimates. API results are cached in `usda_cache.json` and the key is read from `.env` and sent in the `X-Api-Key` header.

## 18. Modules

| Module | File(s) | Responsibility |
|--------|---------|----------------|
| Web application | `app.py` | Routes, sessions, CSRF, error pages |
| Authentication | `app.py`, `utils/validators.py` | Register, login, logout, password hashing |
| Validation | `utils/validators.py` | Checks age, height, weight, email, choices |
| Health calculations | `utils/calculations.py` | BMI, BMR, TDEE, calories, protein, target weight |
| ML training | `model/generate_training_data.py`, `model/train_model.py` | Dataset creation, training, evaluation |
| ML prediction | `model/prediction.py` | Load models, predict category and calories |
| Recommendation engine | `utils/recommendations.py` | Health summary, meal plan, exercise plan |
| Database | `utils/database.py` | Tables, queries, migration |
| Health conditions | `utils/conditions.py` | Rules for diseases (current and past) |
| Food data | `utils/nutrition.py`, `utils/usda_api.py`, `data/fetch_nutrition.py` | Ingredient verification and meal building |
| User interface | `templates/`, `static/` | Pages, styling, JavaScript |

## 19. Results

For the sample user (22 years, male, 168 cm, 55 kg, Moderately Active, Weight Gain, Vegetarian,
Beginner) the system produces:

| Output | Value |
|--------|-------|
| BMI | 19.5 (Normal) |
| BMR | 1495 kcal |
| TDEE | 2317 kcal |
| AI plan category | Weight Gain Diet |
| Daily calorie target | about 2620 kcal |
| Protein target | 77 g |
| Meal plan | Five vegetarian meals totalling about 2665 kcal and 99 g protein |
| Exercise plan | Six beginner exercises, about 75 minutes, 4 days a week |

Safety behaviour was tested: an underweight user choosing weight loss receives a Maintenance Diet,
an obese user choosing weight gain receives a Weight Loss Diet, calories never fall below the safe
minimum, invalid input shows messages instead of crashing, and the application falls back to
formulas if the ML model is missing.

## 20. Advantages

- Personalized and instant recommendations.
- Genuine machine learning with explainable models and visible metrics.
- Built-in safety rules and a calorie floor.
- Free, offline, no API keys, no database server.
- Clean modular code that is easy to explain.
- Secure password storage and form protection.
- Stores history and tracks weight progress.

## 21. Limitations

- The training dataset is synthetic; real-world accuracy has not been clinically validated.
- The food dataset has only 78 meals and the exercise dataset 37 exercises.
- Meal values are sums of ingredient values with estimated recipe grams, so real dishes differ; five ingredients have no USDA equivalent and remain estimates. USDA data is US-based and does not include Indian dishes.
- Health-condition rules are simplified general guidelines, not clinical protocols, and were not reviewed by a dietitian.
- Gender options are limited to Male and Female because the BMR formula uses these two.
- BMI does not consider muscle mass, so athletes may be misclassified.
- Allergy filtering uses simple keyword matching and is not a safe replacement for reading ingredient labels.
- No medical conditions (diabetes, thyroid, pregnancy) are considered.
- Formulas are designed for adults; users aged 15 to 17 should consult a doctor.
- For very small, inactive people, the safe calorie minimum can be close to maintenance calories.
- Single-user local server only, not designed for large-scale deployment.

## 22. Future Scope

- Mobile application and push reminders.
- Voice assistant for meals and workouts.
- Wearable device integration (steps, heart rate, sleep).
- More advanced ML models (gradient boosting, neural networks) trained on real, reviewed data.
- Real-time health tracking with charts and weekly reports.
- Bigger regional food database, barcode scanning and recipe suggestions.
- Medical-condition-aware plans validated by dietitians.
- Multi-language interface and cloud deployment.

## 23. Conclusion

The Smart Diet & Fitness Recommendation System shows how formulas, machine learning and a simple
recommendation engine can work together to deliver personalized wellness guidance. The project
covers the complete cycle of data creation, model training, prediction, recommendation, database
storage and web presentation in a beginner-friendly structure. With real datasets and expert review
it can be extended into a practical wellness tool. It is for general wellness and education only and
does not replace professional medical advice.

## 24. References

1. Mifflin, M. D., St Jeor, S. T., et al. (1990). "A new predictive equation for resting energy
   expenditure in healthy individuals." *American Journal of Clinical Nutrition*, 51(2), 241-247.
2. World Health Organization. *Body mass index (BMI) classification.* who.int
3. Breiman, L. (2001). "Random Forests." *Machine Learning*, 45, 5-32.
4. Pedregosa, F. et al. (2011). "Scikit-learn: Machine Learning in Python." *Journal of Machine Learning Research*, 12, 2825-2830.
5. Flask documentation. https://flask.palletsprojects.com
6. SQLite documentation. https://www.sqlite.org/docs.html
7. Bootstrap 5 documentation. https://getbootstrap.com/docs/5.3
8. pandas documentation. https://pandas.pydata.org/docs
9. U.S. Department of Agriculture, Agricultural Research Service. *FoodData Central.* https://fdc.nal.usda.gov (API guide: https://fdc.nal.usda.gov/api-guide.html)
10. World Health Organization. *Guideline: Sodium intake for adults and children* (2012): less than 2 g sodium per day.
11. American Diabetes Association. *Standards of Care in Diabetes* (nutrition therapy chapter).
12. Indian Council of Medical Research - National Institute of Nutrition. *Dietary Guidelines for Indians.*
