from flask import Flask, render_template, request, redirect, url_for, flash, g
app = Flask(__name__)
app.secret_key = "dev_secret_key" # for flash messages

# temporary mock users (no database yet)
users = {
    "oleksii": {
        "email": "oleksii@test.com",
        "password": "1234",
        "role": "user",
        "balance": 1000
    },

    "olivia": {
        "email": "olivia@test.com",
        "password": "admin",
        "role": "admin",
        "balance": 1000
    }
}

# get current user's username, balance, role (made for navigation, to see balance and username on the pages)
@app.context_processor
def inject_user():
    username = request.view_args.get("username") if request.view_args else None

    if username and username in users:
        user = users.get(username)

        return dict(
            current_user=username,
            balance=user["balance"],
            role=user["role"]
        )

    return dict(current_user=None, balance=None, role=None)

# public route

@app.route("/")
def index():
    return render_template("index.html")


# authentication routes
# log in
@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("Please fill all fields.", "warning")
        return redirect(url_for("index"))

    user = users.get(username)

    if user and user["password"] == password:

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard", username=username))

        return redirect(url_for("dashboard", username=username))
    
    flash("Invalid username or password.", "danger")
    return redirect(url_for("index"))

# register
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for("register"))

        if username in users:
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        users[username] = {
            "email": email,
            "password": password,
            "role": "user",
            "balance": 1000
        }

        print(users)  # debug, to see new user in the terminal

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("index"))

    return render_template("register.html")


# user routes

@app.route("/dashboard/<username>")
def dashboard(username):
    user = users.get(username)
    return render_template("dashboard.html", username=username, balance=user["balance"], page_title="Dashboard")


@app.route("/portfolio/<username>")
def portfolio(username):
    view = request.args.get("view", "summary")  # default = summary
    user = users.get(username)
    return render_template("portfolio.html", username=username, balance=user["balance"], page_category="portfolio", view=view)


@app.route("/transactions/<username>")
def transactions(username):
    user = users.get(username)
    return render_template("transactions.html", username=username, balance=user["balance"], page_title="Transactions")


# admin routes

@app.route("/admin_dashboard/<username>")
def admin_dashboard(username):
    user = users.get(username)
    return render_template("admin_dashboard.html", username=username, balance=user.get("balance", 0), title="Admin Dashboard")

@app.route("/manage_users/<username>")
def manage_users(username):
    user = users.get(username)
    return render_template("manage_users.html", username=username, balance=user["balance"], title="Manage Users")


@app.route("/manage_coins/<username>")
def manage_coins(username):
    user = users.get(username)
    return render_template("manage_coins.html", username=username, balance=user["balance"], title="Manage Coins")


@app.route("/logs/<username>")
def logs(username):
    user = users.get(username)
    return render_template("logs.html", username=username, balance=user["balance"], title="System Logs")


# run app.py

if __name__ == "__main__":
    app.run(debug=True)