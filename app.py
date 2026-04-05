from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "dev_secret_key" 

# mock data for testing
users = {
    "oleksii": {"email": "oleksii@test.com", "password": "123", "role": "user", "balance": 1000},
    "olivia": {"email": "olivia@test.com", "password": "admin", "role": "admin", "balance": 5000}
}

@app.context_processor
def inject_user():

    username = request.view_args.get("username") if request.view_args else None
    user = users.get(username) if username in users else None
    if user:
        return dict(current_user=username, balance=user["balance"], role=user["role"])
    return dict(current_user=None, balance=None, role=None)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    user = users.get(username)
    if user and user["password"] == password:
        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard", username=username))
        return redirect(url_for("dashboard", username=username))
    flash("Invalid credentials", "danger")
    return redirect(url_for("index"))

# User Routes
@app.route("/dashboard/<username>")
def dashboard(username):
    return render_template("dashboard.html", page_title="Dashboard")

@app.route("/portfolio/<username>")
def portfolio(username):
    view = request.args.get("view", "summary")
    return render_template("portfolio.html", page_category="portfolio", view=view)

@app.route("/transactions/<username>")
def transactions(username):
    return render_template("transactions.html", page_title="Transactions")

# Admin Routes
@app.route("/admin_dashboard/<username>")
def admin_dashboard(username):
    return render_template("admin_dashboard.html", title="Admin Dashboard")

@app.route("/manage_users/<username>")
def manage_users(username):
    return render_template("manage_users.html", title="Manage Users")

@app.route("/manage_coins/<username>")
def manage_coins(username):
    return render_template("manage_coins.html", title="Manage Coins")

@app.route("/logs/<username>")
def logs(username):
    return render_template("logs.html", title="System Logs")

if __name__ == "__main__":
    app.run(debug=True)