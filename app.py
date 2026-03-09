from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

# temporary mock users (no database yet)
users = {
    "oleksii": {"password": "1234", "role": "user"},
    "olivia": {"password": "admin", "role": "admin"}
}

# public route

@app.route("/")
def index():
    return render_template("index.html")


# authentication routes

@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return redirect(url_for("index"))

    user = users.get(username)

    if user and user["password"] == password:

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard", username=username))

        return redirect(url_for("dashboard", username=username))

    else: return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return redirect(url_for("register"))

        if username in users:
            return redirect(url_for("register"))

        users[username] = {
            "username": username,
            "password": password,
            "role": "user"
        }

        return redirect(url_for("index"))

    return render_template("register.html")


# user routes

@app.route("/dashboard/<username>")
def dashboard(username):
    return render_template("dashboard.html", username=username)


@app.route("/portfolio/<username>")
def portfolio(username):
    return render_template("portfolio.html", username=username)


@app.route("/transactions/<username>")
def transactions(username):
    return render_template("transactions.html", username=username)


# admin routes

@app.route("/admin_dashboard/<username>")
def admin_dashboard(username):
    return render_template("admin_dashboard.html", username=username)


@app.route("/manage_users/<username>")
def manage_users(username):
    return render_template("manage_users.html", username=username)


@app.route("/manage_coins/<username>")
def manage_coins(username):
    return render_template("manage_coins.html", username=username)


@app.route("/logs/<username>")
def logs(username):
    return render_template("logs.html", username=username)


# run app.py

if __name__ == "__main__":
    app.run(debug=True)