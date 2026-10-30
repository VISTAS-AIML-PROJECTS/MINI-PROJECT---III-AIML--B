import os
import math
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

from database.database import (
    get_connection,
    init_db,
    seed_demo_data
)
from ml.ai_engine import (
    create_goal_schedule,
    recalculate_savings_plan,
    log_monthly_saving,
    apply_deadline_extension,
    generate_ai_guidance,
    calculate_discipline_score
)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# Secret key for secure session management
app.secret_key = os.environ.get("SECRET_KEY", "goalsave-fintech-ai-super-secret-key-2026")

# Initialize database tables on application start
with app.app_context():
    init_db()


# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------
def get_current_user():
    if "user_id" not in session:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_goals(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM goals
        WHERE user_id = ?
        ORDER BY is_active DESC, id DESC
    """, (user_id,))
    goals = cursor.fetchall()
    conn.close()
    return goals


def get_active_goal(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    # Check if active goal exists
    cursor.execute("""
        SELECT * FROM goals
        WHERE user_id = ? AND is_active = 1
        LIMIT 1
    """, (user_id,))
    goal = cursor.fetchone()
    if not goal:
        # Fallback to latest goal
        cursor.execute("""
            SELECT * FROM goals
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 1
        """, (user_id,))
        goal = cursor.fetchone()
        if goal:
            cursor.execute("UPDATE goals SET is_active = 1 WHERE id = ?", (goal["id"],))
            conn.commit()
    conn.close()
    return goal


def get_monthly_logs_for_goal(goal_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM monthly_savings
        WHERE goal_id = ?
        ORDER BY month_index ASC
    """, (goal_id,))
    logs = cursor.fetchall()
    conn.close()
    return logs


# --------------------------------------------------------------------------
# Authentication Routes
# --------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("user_id", "").strip()
        password = request.form.get("password", "")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM users
            WHERE user_id = ? OR email = ?
        """, (identifier, identifier))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["user_id"]
            session["fullname"] = user["fullname"]
            flash(f"Welcome back, {user['fullname']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid User ID/Email or password. Please try again.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        user_id = request.form.get("user_id", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not fullname or not user_id or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (fullname, user_id, email, password)
                VALUES (?, ?, ?, ?)
            """, (fullname, user_id, email, hashed_password))
            conn.commit()

            # Seed an initial starter goal for new users
            new_goal_target = 60000.0
            new_duration = 6
            new_monthly = 10000.0
            cursor.execute("""
                INSERT INTO goals (
                    user_id, goal_name, target_amount, current_savings,
                    duration_months, monthly_target, start_date, status,
                    revised_monthly_target, is_adjusted, is_active, created_at
                )
                VALUES (?, 'Emergency Fund', ?, 0, ?, ?, DATE('now'), 'active', ?, 0, 1, DATE('now'))
            """, (user_id, new_goal_target, new_duration, new_monthly, new_monthly))
            starter_goal_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Create schedule
            create_goal_schedule(starter_goal_id, user_id, new_goal_target, new_duration, datetime.now().strftime("%Y-%m-%d"))

            flash("Account successfully created! Please log in.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            conn.close()
            flash("Username or email already registered. Please choose another or log in.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/demo_login", methods=["GET", "POST"])
def demo_login():
    """
    1-Click Demo Login: Seeds the ₹60,000 / 6-month goal with ₹5,000 saved in Month 1,
    logging in immediately to demonstrate the AI adjustment in action.
    """
    seed_demo_data("demo_user")
    session["user_id"] = "demo_user"
    session["fullname"] = "Demo User"
    flash("Logged in as Demo User. Experience the AI Savings Adjustment scenario in real-time!", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


# --------------------------------------------------------------------------
# Dashboard Route
# --------------------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    all_goals = get_user_goals(user_id)
    active_goal = get_active_goal(user_id)

    # Calculate total savings across all goals
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(current_savings), 0) as total_savings
        FROM goals WHERE user_id = ?
    """, (user_id,))
    total_user_savings = cursor.fetchone()["total_savings"]

    monthly_logs = []
    active_notif = None
    ai_data = None
    completion_pct = 0.0
    remaining_amount = 0.0
    remaining_months = 0
    next_pending_month = None

    if active_goal:
        goal_id = active_goal["id"]
        monthly_logs = get_monthly_logs_for_goal(goal_id)

        target_amount = float(active_goal["target_amount"])
        saved_so_far = float(active_goal["current_savings"])
        remaining_amount = max(0.0, target_amount - saved_so_far)
        completion_pct = round((saved_so_far / target_amount) * 100, 1) if target_amount > 0 else 0.0

        pending_months = [m for m in monthly_logs if m["actual_amount"] is None]
        remaining_months = len(pending_months)
        if pending_months:
            next_pending_month = pending_months[0]

        # Get latest active AI adjustment notification
        cursor.execute("""
            SELECT * FROM ai_notifications
            WHERE goal_id = ? AND type = 'adjustment'
            ORDER BY id DESC LIMIT 1
        """, (goal_id,))
        active_notif = cursor.fetchone()

        # AI Guidance metrics
        ai_data = generate_ai_guidance(user_id, goal_id)

    conn.close()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        all_user_goals=all_goals,
        active_goal=active_goal,
        total_user_savings=total_user_savings,
        monthly_logs=monthly_logs,
        next_pending_month=next_pending_month,
        active_notif=active_notif,
        ai_data=ai_data,
        completion_pct=completion_pct,
        remaining_amount=remaining_amount,
        remaining_months=remaining_months
    )


# --------------------------------------------------------------------------
# Goals Management Routes
# --------------------------------------------------------------------------
@app.route("/goals")
def goals_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    all_goals = get_user_goals(user_id)
    active_goal = get_active_goal(user_id)
    today_date = date.today().strftime("%Y-%m-%d")

    return render_template(
        "goals.html",
        active_page="goals",
        all_user_goals=all_goals,
        active_goal=active_goal,
        today_date=today_date
    )


@app.route("/goals/add", methods=["POST"])
def add_goal_action():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    goal_name = request.form.get("goal_name", "").strip()
    target_amount = request.form.get("target_amount", type=float)
    current_savings = request.form.get("current_savings", type=float) or 0.0
    duration_months = request.form.get("duration_months", type=int)
    start_date_val = request.form.get("start_date", "").strip() or date.today().strftime("%Y-%m-%d")

    if not goal_name or not target_amount or not duration_months:
        flash("Please provide goal name, target amount, and duration.", "danger")
        return redirect(url_for("goals_page"))

    if target_amount <= 0 or duration_months <= 0:
        flash("Target amount and duration must be greater than zero.", "danger")
        return redirect(url_for("goals_page"))

    net_needed = max(0.0, target_amount - current_savings)
    monthly_target = round(net_needed / duration_months, 2)

    conn = get_connection()
    cursor = conn.cursor()

    # Deactivate previous goals
    cursor.execute("UPDATE goals SET is_active = 0 WHERE user_id = ?", (user_id,))

    cursor.execute("""
        INSERT INTO goals (
            user_id, goal_name, target_amount, current_savings,
            duration_months, monthly_target, start_date, status,
            revised_monthly_target, is_adjusted, is_active, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, 0, 1, DATE('now'))
    """, (
        user_id, goal_name, target_amount, current_savings,
        duration_months, monthly_target, start_date_val, monthly_target
    ))
    goal_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Build monthly savings schedule
    create_goal_schedule(goal_id, user_id, net_needed, duration_months, start_date_val)

    flash(f"Goal '{goal_name}' created successfully with monthly target of ₹{monthly_target:,.2f}!", "success")
    return redirect(url_for("dashboard"))


@app.route("/goals/switch", methods=["POST"])
def switch_active_goal():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    goal_id = request.form.get("goal_id", type=int)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE goals SET is_active = 0 WHERE user_id = ?", (user_id,))
    cursor.execute("UPDATE goals SET is_active = 1 WHERE id = ? AND user_id = ?", (goal_id, user_id))
    conn.commit()
    conn.close()

    flash("Active savings goal switched.", "info")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/goals/delete/<int:goal_id>", methods=["POST"])
def delete_goal_action(goal_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM monthly_savings WHERE goal_id = ? AND user_id = ?", (goal_id, user_id))
    cursor.execute("DELETE FROM ai_notifications WHERE goal_id = ? AND user_id = ?", (goal_id, user_id))
    cursor.execute("DELETE FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
    conn.commit()
    conn.close()

    flash("Goal and its monthly schedule have been removed.", "info")
    return redirect(url_for("goals_page"))


# --------------------------------------------------------------------------
# Monthly Savings Tracker & Log Routes
# --------------------------------------------------------------------------
@app.route("/tracker")
def tracker_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    all_goals = get_user_goals(user_id)
    active_goal = get_active_goal(user_id)

    monthly_logs = []
    active_notif = None
    remaining_amount = 0.0

    if active_goal:
        goal_id = active_goal["id"]
        monthly_logs = get_monthly_logs_for_goal(goal_id)
        remaining_amount = max(0.0, float(active_goal["target_amount"]) - float(active_goal["current_savings"]))

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ai_notifications
            WHERE goal_id = ? AND type = 'adjustment'
            ORDER BY id DESC LIMIT 1
        """, (goal_id,))
        active_notif = cursor.fetchone()
        conn.close()

    return render_template(
        "savings_tracker.html",
        active_page="tracker",
        all_user_goals=all_goals,
        active_goal=active_goal,
        monthly_logs=monthly_logs,
        active_notif=active_notif,
        remaining_amount=remaining_amount
    )


@app.route("/tracker/log", methods=["POST"])
def log_monthly_action():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    goal_id = request.form.get("goal_id", type=int)
    month_index = request.form.get("month_index", type=int)
    actual_amount = request.form.get("actual_amount", type=float)
    notes = request.form.get("notes", "").strip()

    if goal_id is None or month_index is None or actual_amount is None:
        flash("Invalid monthly savings data.", "danger")
        return redirect(request.referrer or url_for("tracker_page"))

    success, result = log_monthly_saving(goal_id, user_id, month_index, actual_amount, notes)

    if success:
        if result.get("is_adjusted"):
            flash(
                f"Saved ₹{actual_amount:,.2f} for Month {month_index}. "
                f"AI Savings Adjustment: Remaining monthly targets recalculated to ₹{result['revised_monthly']:,.2f}.",
                "warning"
            )
        else:
            flash(f"Great job! Recorded savings of ₹{actual_amount:,.2f} for Month {month_index}.", "success")
    else:
        flash(f"Error logging savings: {result}", "danger")

    return redirect(request.referrer or url_for("tracker_page"))


@app.route("/tracker/extend/<int:goal_id>", methods=["POST"])
def apply_extension_action(goal_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    extra_months = request.form.get("extra_months", type=int) or 1

    success, result = apply_deadline_extension(goal_id, user_id, extra_months)

    if success:
        flash(
            f"AI Deadline Extension applied! Goal extended by {extra_months} month(s). "
            f"Your new comfortable monthly target is ₹{result['revised_monthly']:,.2f}/month.",
            "success"
        )
    else:
        flash(f"Could not apply deadline extension: {result}", "danger")

    return redirect(request.referrer or url_for("dashboard"))


# --------------------------------------------------------------------------
# Analytics & Chart Data API Routes
# --------------------------------------------------------------------------
@app.route("/analytics")
def analytics_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    all_goals = get_user_goals(user_id)
    active_goal = get_active_goal(user_id)

    completion_pct = 0.0
    remaining_amount = 0.0
    remaining_months = 0
    expense_categories = []
    expense_amounts = []
    total_expenses = 0.0

    if active_goal:
        target = float(active_goal["target_amount"])
        saved = float(active_goal["current_savings"])
        remaining_amount = max(0.0, target - saved)
        completion_pct = round((saved / target) * 100, 1) if target > 0 else 0.0

        logs = get_monthly_logs_for_goal(active_goal["id"])
        remaining_months = len([m for m in logs if m["actual_amount"] is None])

        # Expense breakdown
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, SUM(amount) as cat_total
            FROM transactions
            WHERE user_id = ? AND transaction_type = 'expense'
            GROUP BY category
            ORDER BY cat_total DESC
        """, (user_id,))
        exp_rows = cursor.fetchall()
        for r in exp_rows:
            expense_categories.append(r["category"])
            expense_amounts.append(float(r["cat_total"]))
            total_expenses += float(r["cat_total"])
        conn.close()

    return render_template(
        "analytics.html",
        active_page="analytics",
        all_user_goals=all_goals,
        active_goal=active_goal,
        completion_pct=completion_pct,
        remaining_amount=remaining_amount,
        remaining_months=remaining_months,
        expense_categories=expense_categories,
        expense_amounts=expense_amounts,
        total_expenses=total_expenses
    )


@app.route("/api/chart_data/<int:goal_id>")
def chart_data_api(goal_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
    goal = cursor.fetchone()
    if not goal:
        conn.close()
        return jsonify({"error": "Goal not found"}), 404

    target_amount = float(goal["target_amount"])
    original_monthly = float(goal["monthly_target"])

    cursor.execute("""
        SELECT * FROM monthly_savings
        WHERE goal_id = ?
        ORDER BY month_index ASC
    """, (goal_id,))
    months = cursor.fetchall()
    conn.close()

    labels = []
    planned_data = []
    actual_data = []
    original_plan = []
    revised_plan = []

    planned_cumulative = []
    actual_cumulative = []
    projected_cumulative = []

    cum_planned = 0.0
    cum_actual = 0.0
    last_actual_index = -1

    for idx, m in enumerate(months):
        labels.append(f"M{m['month_index']}")
        planned_val = float(m["planned_amount"])
        planned_data.append(planned_val)
        original_plan.append(original_monthly)
        revised_plan.append(float(m["revised_target"]))

        cum_planned += planned_val
        planned_cumulative.append(cum_planned)

        if m["actual_amount"] is not None:
            act_val = float(m["actual_amount"])
            actual_data.append(act_val)
            cum_actual += act_val
            actual_cumulative.append(cum_actual)
            projected_cumulative.append(cum_actual)
            last_actual_index = idx
        else:
            actual_data.append(None)
            actual_cumulative.append(None)

    # Build projected trajectory extending from last actual
    if last_actual_index >= 0:
        cum_proj = actual_cumulative[last_actual_index]
        for idx in range(last_actual_index + 1, len(months)):
            cum_proj += revised_plan[idx]
            projected_cumulative.append(min(target_amount, cum_proj))
    else:
        projected_cumulative = planned_cumulative[:]

    total_saved = float(goal["current_savings"])
    remaining_amount = max(0.0, target_amount - total_saved)

    return jsonify({
        "goal_id": goal_id,
        "labels": labels,
        "planned_data": planned_data,
        "actual_data": actual_data,
        "original_plan": original_plan,
        "revised_plan": revised_plan,
        "planned_cumulative": planned_cumulative,
        "actual_cumulative": actual_cumulative,
        "projected_cumulative": projected_cumulative,
        "total_saved": total_saved,
        "remaining_amount": remaining_amount,
        "target_amount": target_amount
    })


# --------------------------------------------------------------------------
# AI Financial Guidance & Simulator Route
# --------------------------------------------------------------------------
@app.route("/ai_guidance")
def ai_guidance_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    all_goals = get_user_goals(user_id)
    active_goal = get_active_goal(user_id)

    ai_data = None
    remaining_amount = 0.0
    remaining_months = 0

    if active_goal:
        ai_data = generate_ai_guidance(user_id, active_goal["id"])
        target = float(active_goal["target_amount"])
        saved = float(active_goal["current_savings"])
        remaining_amount = max(0.0, target - saved)
        logs = get_monthly_logs_for_goal(active_goal["id"])
        remaining_months = len([m for m in logs if m["actual_amount"] is None])

    return render_template(
        "ai_guidance.html",
        active_page="ai_guidance",
        all_user_goals=all_goals,
        active_goal=active_goal,
        ai_data=ai_data,
        remaining_amount=remaining_amount,
        remaining_months=remaining_months
    )


# --------------------------------------------------------------------------
# Expense Tracker Routes
# --------------------------------------------------------------------------
@app.route("/expenses")
def expenses_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    all_goals = get_user_goals(user_id)
    active_goal = get_active_goal(user_id)
    today_date = date.today().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (user_id,))
    transactions = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total_inc
        FROM transactions
        WHERE user_id = ? AND transaction_type = 'income'
    """, (user_id,))
    total_income = cursor.fetchone()["total_inc"]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total_exp
        FROM transactions
        WHERE user_id = ? AND transaction_type = 'expense'
    """, (user_id,))
    total_expenses = cursor.fetchone()["total_exp"]
    conn.close()

    net_savings = total_income - total_expenses

    return render_template(
        "expenses.html",
        active_page="expenses",
        all_user_goals=all_goals,
        active_goal=active_goal,
        transactions=transactions,
        total_income=total_income,
        total_expenses=total_expenses,
        net_savings=net_savings,
        today_date=today_date
    )


@app.route("/expenses/add", methods=["POST"])
def add_transaction_action():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    tx_type = request.form.get("transaction_type", "expense").strip()
    category = request.form.get("category", "Other").strip()
    amount = request.form.get("amount", type=float)
    description = request.form.get("description", "").strip()
    date_val = request.form.get("date", "").strip() or date.today().strftime("%Y-%m-%d")

    if amount is None or amount <= 0:
        flash("Please enter a valid positive amount.", "danger")
        return redirect(url_for("expenses_page"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, transaction_type, category, amount, description, date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, tx_type, category, amount, description, date_val))
    conn.commit()
    conn.close()

    flash(f"{tx_type.capitalize()} of ₹{amount:,.2f} recorded.", "success")
    return redirect(url_for("expenses_page"))


@app.route("/expenses/delete/<int:tx_id>", methods=["POST"])
def delete_transaction_action(tx_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
    conn.commit()
    conn.close()

    flash("Transaction deleted.", "info")
    return redirect(url_for("expenses_page"))


# --------------------------------------------------------------------------
# Profile & Settings Routes
# --------------------------------------------------------------------------
@app.route("/profile")
def profile_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = get_current_user()
    all_goals = get_user_goals(session["user_id"])
    active_goal = get_active_goal(session["user_id"])

    return render_template(
        "profile.html",
        active_page="profile",
        user=user,
        all_user_goals=all_goals,
        active_goal=active_goal
    )


@app.route("/profile/change_password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("login"))

    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")

    user = get_current_user()
    if not check_password_hash(user["password"], old_password):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("profile_page"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "danger")
        return redirect(url_for("profile_page"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET password = ? WHERE user_id = ?
    """, (generate_password_hash(new_password), session["user_id"]))
    conn.commit()
    conn.close()

    flash("Password updated successfully!", "success")
    return redirect(url_for("profile_page"))


@app.route("/profile/reload_demo", methods=["POST"])
def reload_demo_scenario():
    if "user_id" not in session:
        return redirect(url_for("login"))

    seed_demo_data(session["user_id"])
    flash("Demo scenario reloaded successfully with ₹60,000 goal and Month 1 shortfall!", "success")
    return redirect(url_for("dashboard"))


# --------------------------------------------------------------------------
# Main Execution
# --------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
