from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import requests

# ------------------- DATABASE, APP, MIGRATION, FLASH MESSAGES ----------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)

app.secret_key = "dev_secret_key"

# ------------- TABLES SETTINGS ------------------

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String, default='user', nullable=False)
    balance = db.Column(db.Float, default=1000)
    wallets = db.relationship('Wallet', backref='user', lazy=True)
    is_banned = db.Column(db.Boolean, default=False)

class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    coinName = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Coin(db.Model):
    __tablename__ = 'coins'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)



# --------- PUBLIC ROUTE ----------

@app.route("/")
def index():
    return render_template("index.html")

# -------- AUTHENTICATION ROUTES --------

# -------- LOG IN -------------
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
 
    if check_password_hash(user.password, password):
        if user.role == "admin":
            return redirect(url_for("admin_dashboard", username=username))
        elif user.role == "user":
            if user.is_banned == False:
                flash("Login details correct! Redirecting...")
                return redirect(url_for("dashboard", username=username))
            else:
                flash("You were banned, please contact admin for future actions!")
                return redirect(url_for("index"))
    else:
        flash("Invalid username or password.", "danger")
        return redirect(url_for("index"))
    
# ------------ REGISTRATION --------------
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
                new_user = User(
                    username=username, 
                    email=email, 
                    password=generate_password_hash(password)
                    )
                db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("index"))

    return render_template("register.html")

# ------------ USER ROUTES ---------

# ------------ DASHBOARD ------------
@app.route("/dashboard/<username>", methods=["GET", "POST"])
def dashboard(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found!")
        return redirect(url_for("home"))

    if request.method == "POST":
        coin_name = request.form.get("coin_name", "").lower().strip()
        amount = request.form.get("amount")

        if not coin_name or not amount:
            flash("Missing coin or amount!")
            return redirect(url_for("dashboard", username=username))

        try:
            amount = float(amount)
        except:
            flash("Invalid amount!")
            return redirect(url_for("dashboard", username=username))

        if amount <= 0:
            flash("Amount must be greater than 0!")
            return redirect(url_for("dashboard", username=username))

        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_name,
            "vs_currencies": "usd"
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            price_data = response.json()

            print("PRICE API RESPONSE:", price_data)

        except Exception as e:
            flash("Price API error!")
            print("API ERROR:", e)
            return redirect(url_for("dashboard", username=username))

        if not isinstance(price_data, dict) or coin_name not in price_data:
            flash("Coin not found on CoinGecko!")
            return redirect(url_for("dashboard", username=username))

        price = price_data[coin_name]["usd"]
        total_cost = price * amount

        if user.balance < total_cost:
            flash("Not enough balance!")
            return redirect(url_for("dashboard", username=username))

        user.balance -= total_cost

        wallet_item = Wallet.query.filter_by(
            userId=user.id,
            coinName=coin_name
        ).first()

        if wallet_item:
            wallet_item.balance += amount
        else:
            db.session.add(Wallet(
                userId=user.id,
                coinName=coin_name,
                balance=amount
            ))

        db.session.commit()

        flash(f"Bought {amount} {coin_name} successfully!")
        return redirect(url_for("dashboard", username=username))

    all_coins = Coin.query.all()
    coins_ids = [c.name.lower().strip() for c in all_coins if c.name]

    data = []

    if coins_ids:
        ids_string = ",".join(coins_ids)

        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ids_string,
            "include_24hr_change": "true"
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            print("MARKET API RESPONSE TYPE:", type(data))

            if not isinstance(data, list):
                print("Unexpected API response:", data)
                data = []

        except Exception as e:
            print(f"Error fetching market data: {e}")
            data = []

    return render_template(
        "dashboard.html",
        username=user.username,
        balance=user.balance,
        role=user.role,
        prices=data,
        page_title="Dashboard"
    )

# -------- PORTFOLIO --------------

@app.route("/portfolio/<username>")
def portfolio(username):
    view = request.args.get("view", "summary") # EXAMPLES OF SUMMARY AND VIEW OF SOMETHING

    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found!")

    wallets = Wallet.query.filter_by(userId=user.id).all()

    return render_template(
        "portfolio.html", 
        username=user.username, 
        balance=user.balance, 
        role=user.role,
        wallets=wallets, 
        page_category="portfolio", 
        view=view
        )

# ------------- TRANSACTION ----------------

@app.route("/transactions/<username>")
def transactions(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found!")

    return render_template(
        "transactions.html", 
        username=user.username, 
        balance=user.balance, 
        role=user.role, 
        page_title="Transactions"
        )

# ---------- ADMIN ROUTES ----------------

# ------- ADMIN DASHBOARD --------------

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
        role=user.role,
        totalUsers = totalUsers,
        title="Admin Dashboard"
    )

# ---------- MANAGING USERS ---------

@app.route( "/manage_users/<username>", methods=["GET", "POST"])
def manage_users(username):
    user = User.query.filter_by(username=username).first()
    users = User.query.all()

    if not user:
        return "User not found!"

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        admin_action = request.form.get('action')
        user_to_change = User.query.get(user_id)

        if user_to_change:
            if admin_action == "ban":
                user_to_change.is_banned = True
            elif admin_action == "unban":
                user_to_change.is_banned = False

            db.session.commit()

    return render_template(
        "manage_users.html",
        username=user.username,
        balance=user.balance,
        role=user.role,
        users=users,
        title="Manage Users"
    )

# ------- MANAGING COINS (NOT IN USE) -------------

@app.route("/manage_coins/<username>", methods=["GET", "POST"])
def manage_coins(username):
    user = User.query.filter_by(username=username).first()

    if request.method == "POST":
        coin_name = request.form.get("coin_name", "").lower().strip()
        action = request.form.get("action")

        if not coin_name:
            flash("Please enter coin name!")
            return redirect(url_for("manage_coins", username=username))
        
        if action == "add":
            is_exist = Coin.query.filter_by(name=coin_name.lower()).first()

            if is_exist:
                flash("Coin already exist!")
            else:
                new_coin = Coin(name=coin_name)
                db.session.add(new_coin)
                db.session.commit()
                flash("New coin added!")
        elif action == "delete":
            coin = Coin.query.filter_by(name=coin_name.lower()).first()

            if coin:
                db.session.delete(coin)
                db.session.commit()
                flash("Coin deleted")
            else:
                flash("Coin not found!")
        
    all_coins = Coin.query.all()
    coins_ids = [coin.name for coin in all_coins]

    data = {}
    if coins_ids:
        ids_string = ",".join(coins_ids)

        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': ids_string,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_last_update_at': 'true'
        }

    try:
        response = requests.get(url, params=params)
        data = response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        data = {}

    if not user:
        return "User not found!"



    return render_template(
        "manage_coins.html",
        username=user.username,
        balance=user.balance,
        role=user.role,
        prices=data,
        title="Manage Coins"
    )


# --------- LOGS -----------------

@app.route("/logs/<username>")
def logs(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        return "User not found!"

    return render_template(
        "logs.html",
        username=user.username,
        balance=user.balance,
        role=user.role,
        title="System Logs"
    )

# ------------- RUN APP -------------

if __name__ == "__main__":
    app.run(debug=True)