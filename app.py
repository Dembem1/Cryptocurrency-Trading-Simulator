from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key = "dev_secret_key" # for flash messages

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    #add hashing
    role = db.Column(db.String, default='user', nullable=False)
    balance = db.Column(db.Float, default=1000)
    wallets = db.relationship('Wallet', backref='user', lazy=True)

class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    coinName = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# temporary mock users (no database yet)
# users = {
#     "oleksii": {
#         "email": "oleksii@test.com",
#         "password": "1234",
#         "role": "user",
#         "balance": 1000
#     },

#     "olivia": {
#         "email": "olivia@test.com",
#         "password": "admin",
#         "role": "admin",
#         "balance": 1000
#     }
# }

# get current user's username, balance, role (made for navigation, to see balance and username on the pages)
# @app.context_processor
# def inject_user():
#     username = request.view_args.get("username") if request.view_args else None

#     if username and username in users:
#         user = users.get(username)

#         return dict(
#             current_user=username,
#             balance=user["balance"],
#             role=user["role"]
#         )

#     return dict(current_user=None, balance=None, role=None)

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
    
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found!")
 
    if user.password == password:
        if user.role == "admin":
            return redirect(url_for("admin_dashboard", username=username))
        
        flash("Login details correct! Redirecting...")
        return redirect(url_for("dashboard", username=username))
    else:
        flash("Invalid username or password.", "danger")
        return redirect(url_for("index")) 
    # user = users.get(username)

    # if user and user["password"] == password:

    #     if user["role"] == "admin":
    #         return redirect(url_for("admin_dashboard", username=username))

    #     return redirect(url_for("dashboard", username=username))
    
    # flash("Invalid username or password.", "danger")
    # return redirect(url_for("index"))

# register
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        existingUser = User.query.filter_by(username=username).first()
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for("register"))

        if existingUser:
            flash("Username already taken!")
            return redirect(url_for("register"))

        if username and email and password:
            try:
                new_user = User(username=username, email=email, password=password)
                db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("index"))
    
        # if username in users:
        #     flash("Username already exists.", "danger")
        #     return redirect(url_for("register"))

        # users[username] = {
        #     "email": email,
        #     "password": password,
        #     "role": "user",
        #     "balance": 1000
        # }

        # print(users)  # debug, to see new user in the terminal

        # flash("Registration successful. Please login.", "success")
        # return redirect(url_for("index"))

    return render_template("register.html")


# user routes

@app.route("/dashboard/<username>")
def dashboard(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found!")

    return render_template("dashboard.html", username=user.username, balance=user.balance, role=user.role, page_title="Dashboard")


@app.route("/portfolio/<username>")
def portfolio(username):
    view = request.args.get("view", "summary")  # default = summary

    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found!")

    return render_template("portfolio.html", username=user.username, balance=user.balance, role=user.role, view=view, page_category="portfolio")


@app.route("/transactions/<username>")
def transactions(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found!")

    return render_template("transactions.html", username=user.username, balance=user.balance, role=user.role, page_title="Transactions")


# admin routes

@app.route("/admin_dashboard/<username>")
def admin_dashboard(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        return "User not found!"

    totalUsers = User.query.count()

    return render_template(
        "admin_dashboard.html",
        username=user.username,
        balance=user.balance,
        totalUsers = totalUsers,
        title="Admin Dashboard"
    )


@app.route( "/manage_users/<username>", methods=["GET", "POST"])
def manage_users(username):
    user = User.query.filter_by(username=username).first()
    users = User.query.all()

    if not user:
        return "User not found!"

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_to_ban = User.query.get(user_id)
        user_to_unban = User.query.get(user_id)

        if user_to_ban:
            user_to_ban.role = 'banned'
            db.session.commit()
        elif user_to_unban:
            user_to_unban.role = 'user'
            db.session.commit()

    return render_template(
        "manage_users.html",
        username=user.username,
        balance=user.balance,
        users=users,
        title="Manage Users"
    )


@app.route("/manage_coins/<username>")
def manage_coins(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        return "User not found!"

    return render_template(
        "manage_coins.html",
        username=user.username,
        balance=user.balance,
        title="Manage Coins"
    )


@app.route("/logs/<username>")
def logs(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        return "User not found!"

    return render_template(
        "logs.html",
        username=user.username,
        balance=user.balance,
        title="System Logs"
    )

# run app.py

if __name__ == "__main__":
    app.run(debug=True)