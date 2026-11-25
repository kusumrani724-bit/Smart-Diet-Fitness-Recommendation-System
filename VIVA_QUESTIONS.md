# Viva Questions and Answers

**Project:** Smart Diet & Fitness Recommendation System (MCA AI & ML)

Answers are written in simple words so you can say them naturally in a viva.

---

## Part A: Basic concepts

**1. What is Artificial Intelligence (AI)?**
AI is making computers do tasks that normally need human intelligence, such as learning, understanding,
decision making and recommending. In this project, AI recommends a diet plan and calories for each person.

**2. What is Machine Learning (ML)?**
ML is a part of AI where the computer learns patterns from data instead of being given fixed rules.
Here, the model learns from 4000 example people how goal, BMI and body size affect the plan and calories.

**3. What is Deep Learning?**
Deep Learning is a part of ML that uses neural networks with many layers. It needs a lot of data and
computing power. This project uses Random Forest instead, because it is simpler, explainable and works
well on small tabular data.

**4. What is a recommendation system?**
It is a system that suggests items (foods, exercises, movies) to a user based on their data or
preferences. This project is a *content-based* recommender: it matches meal and exercise
properties (calories, diet type, goal, difficulty) with the user's profile.

**5. What is Healthcare Informatics?**
It is the use of information technology and data to support health and wellness. This project
belongs to this area because it processes health data (BMI, calories) to give wellness guidance.

---

## Part B: Health formulas

**6. What is BMI?**
Body Mass Index = weight (kg) divided by height (m) squared. Example: 65 kg and 175 cm gives
65 / (1.75 x 1.75) = 21.2. Categories: below 18.5 underweight, 18.5 to 24.9 normal, 25 to 29.9
overweight, 30 and above obese.

**7. Why do we convert height from cm to metres?**
The BMI formula needs height in metres. We divide centimetres by 100.

**8. What is BMR?**
Basal Metabolic Rate is the number of calories the body burns at complete rest to keep us alive
(breathing, heartbeat, etc.).

**9. Which formula is used for BMR and why?**
The Mifflin-St Jeor equation. It is considered more accurate for modern populations than the older
Harris-Benedict equation. Male: 10w + 6.25h - 5a + 5. Female: 10w + 6.25h - 5a - 161.

**10. What is TDEE?**
Total Daily Energy Expenditure is the calories a person burns in a full day including activity.
TDEE = BMR x activity factor (1.2 for sedentary up to 1.9 for extremely active).

**11. How is the daily calorie target decided?**
We start from TDEE and adjust by goal: weight loss minus 500, weight gain plus 400, muscle gain
plus 300, maintain 0. We never go below 1500 kcal (male) or 1200 kcal (female) for safety.

**12. How is the protein target calculated?**
Body weight multiplied by grams per kg that depend on the goal: 1.6 for weight loss, 1.4 for gain,
1.8 for muscle gain, 1.0 for maintenance, 1.2 for general fitness.

---

## Part C: Machine learning

**13. What is training data?**
The example data used to teach the model. In this project it is `data/training_data.csv` with 4000
rows. 80% is used for training and 20% for testing.

**14. What are features?**
The input columns the model uses to predict. For the classifier: age, gender, height, weight, BMI,
activity level, fitness goal, diet preference and workout level.

**15. What is the target variable?**
The value we want to predict. For the classifier it is the plan category (for example Weight Loss
Diet). For the regressor it is the daily calorie requirement.

**16. What is classification?**
Predicting a category or label. Our classifier predicts one of five plan categories.

**17. What is regression?**
Predicting a number. Our regressor predicts daily calories in kcal.

**18. Why did you choose Random Forest?**
It is accurate, works on mixed numeric data, needs little tuning, is hard to overfit compared with a
single tree, and gives feature importance so we can explain the result. It is also beginner-friendly.

**19. What is a Decision Tree and how is a Random Forest different?**
A decision tree makes decisions by asking yes/no questions on features. A Random Forest builds many
trees on random parts of the data and combines their votes (classification) or averages
(regression). This gives more stable results than one tree.

**20. What is overfitting?**
When a model memorises the training data, including noise, and performs badly on new data. We check
for it by testing on separate test data that the model has never seen.

**21. What is underfitting?**
When a model is too simple to learn the pattern, so it performs badly on both training and test
data.

**22. What is accuracy?**
Correct predictions divided by total predictions. If 790 of 800 test rows are predicted correctly,
accuracy is 98.75%.

**23. What is precision?**
Of all the items the model predicted as a class, how many were really that class.
Precision = TP / (TP + FP).

**24. What is recall?**
Of all the items that really belong to a class, how many the model found. Recall = TP / (TP + FN).

**25. What is F1-score?**
The harmonic mean of precision and recall: 2 x (P x R) / (P + R). It is useful when we want one
number that balances both.

**26. What are MAE and R-squared (used for the regressor)?**
MAE (Mean Absolute Error) is the average size of the error, for example 83 kcal. R-squared tells how
much of the variation the model explains; closer to 1 is better.

**27. Why is the accuracy so high? Is it real?**
The dataset is synthetic and its labels follow clear dietitian rules, so the model learns them
almost perfectly. In a real-world system with noisy data the accuracy would be lower. We say this
openly in the documentation.

**28. Why did you generate the dataset instead of downloading one?**
Real medical datasets are private and may not match our labels. A generated dataset lets us control
the rules and keeps the project fully offline. A future version should use real reviewed data.

**29. Where exactly is ML used in your project?**
In `utils/recommendations.py`, the function `build_health_summary()` calls `predict_recommendation()`
from `model/prediction.py`. The classifier predicts the plan category and the regressor predicts the
calories. The category then drives the meal and exercise plans.

**30. Why do you compare the ML prediction with the formula?**
For safety. If the prediction differs from the formula by more than 10%, or the model is missing,
the formula value is used. Healthcare-related software should never depend on an unchecked
prediction alone.

**31. How is the trained model saved and loaded?**
With `joblib.dump()` into `trained_model.pkl` and `joblib.load()` when needed. If the file is
missing or unreadable, the app retrains automatically.

**32. Why do you convert text to numbers (encoding)?**
ML algorithms work with numbers. We map values such as "Male" to 0 and "Female" to 1, and activity
levels to 0 to 4.

---

## Part D: Recommendation logic

**33. How does the meal recommendation work?**
Filter meals by diet type and allergies, split the calorie target across five meals, then score every
meal and portion size by how close it is to the calorie and protein share and whether it matches the
goal. The lowest score is chosen.

**34. How does the exercise recommendation work?**
Keep exercises that are within the user's workout level and tagged for the goal, choose exercise
types in a goal-specific order, and set the number of exercises and duration based on activity level.

**35. How do you handle allergies and diet preference?**
Each meal in `meals.csv` has a diet type and allergen tags. Vegan users only see vegan meals, and
meals containing the user's allergens are removed. This is simple keyword matching, so users must still
check ingredients.

**36. What happens if no meal is found?**
The app shows "No suitable meal found" with a warning and a button to edit the profile. It never crashes.

**37. What happens if a user chooses an unsafe goal?**
The classifier was trained to protect users. For example, an underweight user choosing weight loss
gets a Maintenance Diet, and the dashboard explains why.

---

## Part E: Web, database and security

**38. What is Flask and why did you use it?**
Flask is a lightweight Python web framework. It is easy to learn, needs little code and is ideal for
connecting a Python ML model to a web page.

**39. What is Jinja?**
Jinja2 is the template engine used by Flask. It lets HTML pages contain Python-like code such as
`{{ summary.bmi }}`, `{% for meal in meals %}` and `{% extends "base.html" %}`.

**40. What is Bootstrap?**
A CSS framework with ready-made responsive components (navbar, cards, tables, forms, badges,
progress bars). We store it inside the project so the site works offline.

**41. Why SQLite?**
It is a file-based database built into Python, needs no server or installation (no MySQL or XAMPP),
and is perfect for small and medium projects and demonstrations.

**42. How is the database connected?**
`utils/database.py` uses Python's `sqlite3` module. `get_connection()` opens `database.db`, and
`init_db()` creates the tables with `CREATE TABLE IF NOT EXISTS` when the app starts.

**43. How does authentication work?**
On registration the password is hashed and saved. On login we find the user by email and verify the
password with `check_password_hash`. If correct, the user id is stored in the Flask session
(a signed cookie). Protected pages use a `login_required` decorator.

**44. Why is password hashing required?**
If the database leaks, plain passwords would be exposed. A hash is a one-way, salted scrambled value
that cannot be reversed easily, so attackers cannot read the real passwords.

**45. What is CSRF and how did you protect against it?**
Cross-Site Request Forgery is when another website tricks a logged-in user's browser into sending a
request. We add a secret random token to every form and reject POST requests without the correct token.

**46. How do you validate user input?**
`utils/validators.py` checks every field on the server (age, height and weight ranges, email format,
allowed dropdown values). The browser also validates with HTML attributes and JavaScript for a better
experience. Server-side validation is the one that really protects the app.

---

## Part F: Evaluation questions

**47. What are the limitations of the project?**
Synthetic training data, small meal and exercise datasets, BMI ignores muscle mass, no medical
conditions are considered, simple allergy matching, only male and female options for BMR, and it is
designed for local use rather than large-scale deployment.

**48. How could the project be improved?**
Use real datasets, more foods and exercises, wearable integration, a mobile app, a voice assistant,
charts, dietitian-reviewed plans and more advanced models.

**49. Is this system a medical tool?**
No. It is for general wellness and education only. It does not diagnose diseases or replace a doctor
or dietitian, and the app displays this disclaimer on every page.

**50. Explain the complete flow of the project in one minute.**
The user registers and logs in, then enters age, gender, height, weight, activity, goal, diet and
workout level. The server validates the data and calculates BMI, BMR and TDEE. The ML classifier
predicts the plan category and the regressor predicts calories; a safety check compares it with the
formula. Using the final calorie and protein targets, the system picks meals from `meals.csv` and
exercises from `exercises.csv`. The results are saved in SQLite and shown on the dashboard with
tables, badges and progress bars.

---

## Part G: Data source, API and health conditions

**51. Where does your food data come from?**
Ingredient nutrition values are checked against USDA FoodData Central, the official US government food composition database, through its API. Each meal is a recipe (ingredients with grams) and its nutrition is the sum of its ingredients. Five ingredients with no USDA equivalent (paneer, soya chunks, poha, idli, makhana) are labelled as estimates.

**52. What is an API?**
An Application Programming Interface lets one program ask another program for data. Our app sends a search request (for example "lentils") to the USDA server and receives nutrition data in JSON format.

**53. What is an API key and why is it needed?**
A key is a secret code that identifies who is using the API, so the provider can allow access and limit usage (USDA allows 1,000 requests per hour per key).

**54. How do you keep the API key safe?**
It is stored in a `.env` file on the user's computer, not in the code. `.gitignore` excludes it from uploads, and the key is sent in a request header, not in the URL, so it does not appear in logs.

**55. Why do you save USDA results instead of calling the API every time?**
To work offline, to stay under the rate limit, and to make the app fast and demo-safe. `fetch_nutrition.py` runs once, updates the CSV files, and caches results in `usda_cache.json`.

**56. What if USDA returns the wrong food?**
The fetch script compares the USDA calories with our pre-filled value. If they differ by more than 35% (for example raw rice instead of cooked rice) it keeps the old value and marks the row REVIEW in `usda_matches.csv` so a person can check it.

**57. Why are meals built from ingredients?**
USDA has generic foods, not our home-cooked dishes. Summing ingredients lets official ingredient data support dish-level numbers, and also gives fibre, sugar and sodium that the health rules need.

**58. Why do you ask about diseases before the meal plan?**
Diet needs differ with health. For example a diabetic person needs lower sugar and carbohydrates, and a person with high blood pressure needs less salt. The plan is built only after this information is known.

**59. How does the diet change for diabetes?**
Total sugars are limited to 40 g a day, carbohydrates to 50% of calories, and fibre should be at least 30 g. The meal scorer penalises meals that break these limits, and the plan page shows a check table.

**60. How does the diet change for high blood pressure?**
Sodium is limited to 2000 mg a day (WHO advice) and meals are calculated with low-salt cooking (half the added salt). HIIT exercise is removed.

**61. What is the difference between "past" and "current" conditions?**
Current conditions use strict limits. Past conditions use gentler limits (upper limits 25% higher, minimums 15% lower) and a note to keep the doctor informed.

**62. Why are the disease rules not machine learning?**
There is no real, reliable medical dataset available, and health advice must be explainable. Simple rules based on general guidelines are transparent and safer than a model trained on invented data. ML is used for the plan type and calories.

**63. Which conditions does the app refuse to plan for, and why?**
Kidney disease, insulin use, pregnancy or breastfeeding, eating disorder, and cancer treatment, liver disease or recent surgery. These need individual medical supervision, so the app shows a "please consult a doctor" message and no calorie or meal numbers.

**64. How is the sensitive health information protected?**
It is stored only in the local SQLite file on the computer running the app, is shown only to the logged-in user, requires a consent tick, and is never sent to the internet. For a real deployment it would also need encryption and access logging.

**65. What happens to old users when you add new database columns?**
`migrate_db()` checks the table with `PRAGMA table_info` and adds the missing columns with `ALTER TABLE`, so old data is kept and the process can run again safely.

**66. How did you make the home page animated?**
CSS keyframe animations (floating items, gradient blobs, scrolling marquee), animated SVG illustrations, and a small JavaScript IntersectionObserver that reveals sections and counts up numbers when they scroll into view. Animations are turned off for users who prefer reduced motion.
