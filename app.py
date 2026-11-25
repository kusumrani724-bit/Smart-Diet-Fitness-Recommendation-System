"""
app.py
------
Main Flask application: routes (web pages), login handling and form processing.
The heavy work is done in other files:
    utils/calculations.py    -> BMI, BMR, TDEE formulas
    utils/recommendations.py -> ML + meal plan + exercise plan
    utils/database.py        -> SQLite
    utils/validators.py      -> checking user input
    utils/conditions.py      -> health-condition rules (diabetes, blood pressure, ...)
    utils/nutrition.py       -> meal nutrition built from USDA-verified ingredients
    utils/usda_api.py        -> USDA FoodData Central API client

Run with:  python app.py     then open  http://127.0.0.1:5000
"""

import json
import os
import secrets
import sqlite3
from functools import wraps

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from model import prediction
from utils import calculations as calc
from utils import conditions
from utils import database as db
from utils import nutrition
from utils import recommendations as rec
from utils import usda_api
from utils import validators
from utils.config import get_usda_key
from utils.constants import (ACTIVITY_LEVELS, CATEGORY_TO_GOAL, DIET_PREFERENCES,
                             FITNESS_GOALS, GENDERS, METRICS_PATH, WORKOUT_LEVELS)

app = Flask(__name__)
# The secret key signs the login cookie. Set SECRET_KEY as an environment variable for real use.
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-for-college-demo")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Options for the drop-downs, available in every template
FORM_OPTIONS = {
    "genders": GENDERS,
    "activity_levels": ACTIVITY_LEVELS,
    "fitness_goals": FITNESS_GOALS,
    "diet_preferences": DIET_PREFERENCES,
    "workout_levels": WORKOUT_LEVELS,
}


# =====================================================================
# Security helpers: CSRF token + login_required
# =====================================================================
def get_csrf_token():
    """A random token stored in the session and placed in every form."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = get_csrf_token


@app.before_request
def check_csrf_token():
    """Reject POST requests that do not carry the correct token."""
    if request.method == "POST":
        sent_token = request.form.get("csrf_token", "")
        real_token = session.get("csrf_token", "")
        if not sent_token or not real_token or not secrets.compare_digest(sent_token, real_token):
            abort(400)


def login_required(view):
    """Decorator: pages that need a logged-in user."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


@app.context_processor
def inject_globals():
    """Variables available in every template."""
    return {"logged_in": "user_id" in session,
            "user_name": session.get("user_name", ""),
            "options": FORM_OPTIONS}


# =====================================================================
# Helper functions used by several routes
# =====================================================================
def create_and_store_recommendation(user_id, profile):
    """Run formulas + ML for this profile and save the result in the database."""
    summary = rec.build_health_summary(profile)
    db.save_recommendation(user_id, summary)
    if not summary["ml_available"]:
        flash("AI model not available, so formula-based results were used. "
              "Run: python model/train_model.py", "warning")
    return summary


def prepare_summary(recommendation, profile):
    """Add display values (colours, gauge position, effective goal) to the stored result."""
    summary = dict(recommendation)
    summary["effective_goal"] = CATEGORY_TO_GOAL.get(summary["ml_category"], profile["fitness_goal"])
    summary["goal_adjusted"] = summary["effective_goal"] != profile["fitness_goal"]
    summary["bmi_color"] = calc.bmi_badge_color(summary["bmi_category"])
    summary["bmi_marker"] = calc.bmi_marker_position(summary["bmi"])
    summary["healthy_low"], summary["healthy_high"] = calc.healthy_weight_range(profile["height"])
    return summary


def build_progress(user_id, profile, summary):
    """Numbers for the weight-progress section of the dashboard."""
    logs = db.get_weight_logs(user_id)
    start_weight = logs[0]["weight"] if logs else profile["weight"]
    target = calc.calculate_target_weight(profile["height"], start_weight, summary["effective_goal"])
    return {
        "start": start_weight,
        "current": profile["weight"],
        "target": target,
        "percent": calc.calculate_progress_percent(start_weight, profile["weight"], target),
        "change": round(profile["weight"] - start_weight, 1),
        "logs": list(reversed(logs[-6:])),
    }


def get_condition_rules(profile):
    """Health-condition answers of this user, converted into plan rules."""
    answers = conditions.conditions_from_text(profile.get("conditions", ""))
    return conditions.analyze_conditions(answers)


def load_user_data(user_id):
    """Profile + latest saved recommendation, or (None, None) if the profile is not filled yet."""
    profile = db.get_profile(user_id)
    recommendation = db.get_latest_recommendation(user_id)
    if not profile or not recommendation:
        return None, None
    return profile, prepare_summary(recommendation, profile)


# =====================================================================
# Public pages
# =====================================================================
@app.route("/")
def index():
    # A live example (the one from the project brief), calculated with the real code.
    example_profile = {"age": 22, "gender": "Male", "height": 168, "weight": 55,
                       "activity_level": "Moderately Active", "fitness_goal": "Weight Gain",
                       "diet_preference": "Vegetarian", "workout_level": "Beginner"}
    try:
        example = rec.build_health_summary(example_profile)
        example["bmi_color"] = calc.bmi_badge_color(example["bmi_category"])
        example["bmi_marker"] = calc.bmi_marker_position(example["bmi"])
    except Exception:
        example = None            # the home page must never crash because of the example
    stats = {"meals": 78, "exercises": 37, "training_rows": 4000,
             "conditions": len(conditions.DIET_CONDITIONS)}
    try:
        stats["meals"] = len(rec.load_meals())
        stats["exercises"] = len(rec.load_exercises())
        stats["training_rows"] = about_metrics().get("rows", 4000)
    except Exception:
        pass                      # numbers are decoration only
    try:
        data_stats = nutrition.verification_stats()
    except Exception:
        data_stats = None
    return render_template("index.html", example=example, example_profile=example_profile,
                           stats=stats, data_stats=data_stats)


def about_metrics():
    """ML scores saved by train_model.py ({} if the file is missing)."""
    try:
        with open(METRICS_PATH, encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return {}


@app.route("/about")
def about():
    try:
        data_stats = nutrition.verification_stats()
    except Exception:
        data_stats = None
    return render_template("about.html", metrics=about_metrics() or None, data_stats=data_stats,
                           has_usda_key=bool(get_usda_key()))


# =====================================================================
# Authentication
# =====================================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    form = {}
    if request.method == "POST":
        form, errors = validators.validate_registration(request.form)
        if not errors:
            try:
                db.create_user(form["name"], form["email"], generate_password_hash(form["password"]))
                flash("Account created successfully. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                errors.append("An account with this email already exists. Try logging in.")
        for error in errors:
            flash(error, "danger")
        form.pop("password", None)
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.get_user_by_email(email) if email else None

        if user and check_password_hash(user["password"], password):
            session.clear()                       # start a fresh session after login
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html", email=email)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# =====================================================================
# User pages
# =====================================================================
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    saved_profile = db.get_profile(user_id)
    form = dict(saved_profile) if saved_profile else {}

    if request.method == "POST":
        data, errors = validators.validate_profile(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
            form = request.form.to_dict()          # keep what the user typed
        else:
            previous_weight = saved_profile["weight"] if saved_profile else None
            db.save_profile(user_id, data)
            if previous_weight is None or previous_weight != data["weight"]:
                db.add_weight_log(user_id, data["weight"])
            create_and_store_recommendation(user_id, data)
            if not saved_profile or not saved_profile.get("conditions_answered"):
                flash("Profile saved. One more step: tell us about your health history.", "success")
                return redirect(url_for("health_conditions"))
            flash("Profile saved. Your personalised plan is ready!", "success")
            return redirect(url_for("dashboard"))

    summary = None
    if saved_profile and request.method == "GET":
        recommendation = db.get_latest_recommendation(user_id)
        summary = prepare_summary(recommendation, saved_profile) if recommendation else None
    return render_template("profile.html", form=form, summary=summary,
                           has_profile=saved_profile is not None,
                           history_count=db.count_recommendations(user_id))


@app.route("/health-conditions", methods=["GET", "POST"])
@login_required
def health_conditions():
    """Step 2: ask about current and past diseases BEFORE any meal plan is made."""
    user_id = session["user_id"]
    saved_profile = db.get_profile(user_id)
    if not saved_profile:
        flash("Please complete your health profile first.", "info")
        return redirect(url_for("profile"))

    answers = conditions.conditions_from_text(saved_profile.get("conditions", ""))
    notes = saved_profile.get("condition_notes", "")

    if request.method == "POST":
        if request.form.get("action") == "none":
            answers, notes = {}, ""
        else:
            answers = conditions.parse_conditions_form(request.form)
            notes = request.form.get("condition_notes", "").strip()[:300]
            if answers and not request.form.get("consent"):
                flash("Please tick the confirmation box so we can use your health information.", "danger")
                return render_template("health_conditions.html", diet_conditions=conditions.DIET_CONDITIONS,
                                       high_risk=conditions.HIGH_RISK_CONDITIONS, answers=answers,
                                       notes=notes, answered=bool(saved_profile["conditions_answered"]))
        db.save_conditions(user_id, conditions.conditions_to_text(answers), notes)
        flash("Health history saved. Your plan now follows it." if answers
              else "Saved. No health conditions will be applied to your plan.", "success")
        return redirect(url_for("dashboard"))

    return render_template("health_conditions.html", diet_conditions=conditions.DIET_CONDITIONS,
                           high_risk=conditions.HIGH_RISK_CONDITIONS, answers=answers, notes=notes,
                           answered=bool(saved_profile["conditions_answered"]))


def load_ready_user_data(user_id):
    """
    Profile + result + condition rules, or a redirect response if a step is missing:
    step 1 = profile, step 2 = health history, then plans are allowed.
    """
    user_profile, summary = load_user_data(user_id)
    if not user_profile:
        flash("Please complete your health profile first.", "info")
        return None, None, None, redirect(url_for("profile"))
    if not user_profile.get("conditions_answered"):
        flash("Before we build your plan, please tell us about your health history.", "info")
        return None, None, None, redirect(url_for("health_conditions"))
    return user_profile, summary, get_condition_rules(user_profile), None


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    user_profile, summary, rules, redirect_response = load_ready_user_data(user_id)
    if redirect_response:
        return redirect_response

    if rules["blocked"]:                      # higher-risk condition: no plan, see a doctor
        return render_template("dashboard.html", profile=user_profile, summary=summary, rules=rules,
                               meal_plan=None, exercise_plan=None, progress=None)

    meal_plan = rec.generate_meal_plan(summary["calorie_target"], summary["protein_target"],
                                       summary["effective_goal"], user_profile["diet_preference"],
                                       user_profile["allergies"], rules=rules)
    exercise_plan = rec.generate_exercise_plan(summary["effective_goal"],
                                               user_profile["workout_level"],
                                               user_profile["activity_level"], rules)
    return render_template("dashboard.html", profile=user_profile, summary=summary, rules=rules,
                           meal_plan=meal_plan, exercise_plan=exercise_plan,
                           progress=build_progress(user_id, user_profile, summary))


@app.route("/meal-plan")
@login_required
def meal_plan():
    user_profile, summary, rules, redirect_response = load_ready_user_data(session["user_id"])
    if redirect_response:
        return redirect_response
    if rules["blocked"]:
        return render_template("consult_doctor.html", rules=rules, page_title="Meal plan")

    variation = max(0, min(request.args.get("variation", 0, type=int), 9999))
    plan = rec.generate_meal_plan(summary["calorie_target"], summary["protein_target"],
                                  summary["effective_goal"], user_profile["diet_preference"],
                                  user_profile["allergies"], variation, rules)
    return render_template("meal_plan.html", profile=user_profile, summary=summary, plan=plan,
                           rules=rules, variation=variation, next_variation=variation + 1)


@app.route("/exercises")
@login_required
def exercises():
    user_profile, summary, rules, redirect_response = load_ready_user_data(session["user_id"])
    if redirect_response:
        return redirect_response
    if rules["blocked"]:
        return render_template("consult_doctor.html", rules=rules, page_title="Exercise plan")

    plan = rec.generate_exercise_plan(summary["effective_goal"], user_profile["workout_level"],
                                      user_profile["activity_level"], rules)
    return render_template("exercises.html", profile=user_profile, summary=summary, plan=plan, rules=rules)


@app.route("/food-lookup")
@login_required
def food_lookup():
    """Live search in the official USDA FoodData Central database (needs the API key)."""
    query = request.args.get("q", "").strip()[:60]
    results, error = [], None
    if query:
        try:
            results = usda_api.search_foods(query, page_size=8)
        except usda_api.UsdaError as problem:
            error = str(problem)
    return render_template("food_lookup.html", query=query, results=results, error=error,
                           has_key=bool(get_usda_key()))


@app.route("/log-weight", methods=["POST"])
@login_required
def log_weight():
    """Save a new weight, then recalculate everything with the new value."""
    user_id = session["user_id"]
    user_profile = db.get_profile(user_id)
    if not user_profile:
        return redirect(url_for("profile"))

    weight, error = validators.validate_weight(request.form.get("weight"))
    if error:
        flash(error, "danger")
    else:
        db.update_profile_weight(user_id, weight)
        db.add_weight_log(user_id, weight)
        user_profile["weight"] = weight
        create_and_store_recommendation(user_id, user_profile)
        flash(f"Weight updated to {weight} kg. Your plan was recalculated.", "success")
    return redirect(url_for("dashboard"))


# =====================================================================
# Error pages (the app should never show a raw crash page)
# =====================================================================
def show_error(title, message, code):
    return render_template("error.html", title=title, message=message), code


@app.errorhandler(400)
def bad_request(_error):
    return show_error("Form expired", "Your form could not be verified. "
                      "Go back, refresh the page and try again.", 400)


@app.errorhandler(404)
def not_found(_error):
    return show_error("Page not found", "The page you are looking for does not exist.", 404)


@app.errorhandler(sqlite3.Error)
def database_error(_error):
    return show_error("Database problem", "Something went wrong while reading or saving "
                      "your data. Please try again.", 500)


@app.errorhandler(FileNotFoundError)
def dataset_missing(error):
    return show_error("Dataset missing", str(error), 500)


@app.errorhandler(500)
def server_error(_error):
    return show_error("Something went wrong", "An unexpected error occurred. "
                      "Please try again.", 500)


# =====================================================================
# Start-up
# =====================================================================
def prepare_application():
    """Create the database tables and make sure the ML model exists."""
    db.init_db()
    db.migrate_db()
    if not prediction.ensure_model_exists():
        print("WARNING: ML model unavailable. The app will use formulas only.")


prepare_application()

if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(host="127.0.0.1", port=5000, debug=True)
