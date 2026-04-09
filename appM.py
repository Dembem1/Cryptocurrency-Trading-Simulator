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

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    coinName = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(10), nullable=False) # buy or sell
    amount = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

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
        flash("User not found!", "danger")
        return redirect(url_for("index"))
 
    if not check_password_hash(user.password, password):
        flash("Invalid password", "danger")
        return redirect(url_for("index"))
    
    if user.is_banned:
        flash("You are banned", "danger")
        return redirect(url_for("index"))

    flash("Login successful!", "success")

    if user.role == "admin":
        return redirect(url_for("admin_dashboard", username=username))
    else:
        return redirect(url_for("dashboard", username=username))
    
# ------------ REGISTRATION --------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existingUser = User.query.filter((User.username==username) | (User.email==email)).first()

        if not username or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for("register"))

        if existingUser:
            flash("Username or email already taken!", "warning")
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
        flash("User not found", "danger")
        return redirect(url_for("index"))

    if user.is_banned:
        flash("You are banned", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        coin_name = request.form.get("coin_name", "").lower().strip()
        amount = request.form.get("amount")
        action = request.form.get("action") # buy or sell

        if not coin_name or not amount:
            flash("Missing coin or amount!", "warning")
            return redirect(url_for("dashboard", username=username))

        try:
            amount = float(amount)
        except:
            flash("Invalid amount!", "danger")
            return redirect(url_for("dashboard", username=username))

        if amount <= 0:
            flash("Amount must be greater than 0!", "warning")
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
            flash("Price API error!", "danger")
            print("API ERROR:", e)
            return redirect(url_for("dashboard", username=username))

        if not isinstance(price_data, dict) or coin_name not in price_data:
            flash("Coin not found on CoinGecko!", "warning")
            return redirect(url_for("dashboard", username=username))

        price = price_data[coin_name]["usd"]
        total_cost = price * amount
        
        if user.balance < total_cost:
            flash("Not enough balance!", "warning")
            return redirect(url_for("dashboard", username=username))

        # buy logic
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

        db.session.add(Transaction(
            userId=user.id,
            coinName=coin_name,
            type="buy",
            amount=amount,
            price=price,
            total=total_cost
        ))  

        db.session.commit()
        flash(f"Bought {amount} {coin_name} successfully!", "success")
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

@app.route("/portfolio/<username>", methods=["GET", "POST"])
def portfolio(username):
    view = request.args.get("view", "summary") # EXAMPLES OF SUMMARY AND VIEW OF SOMETHING

    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found", "danger")
        return redirect(url_for("index"))

    if user.is_banned:
        flash("You are banned", "danger")
        return redirect(url_for("index"))

    wallets = Wallet.query.filter_by(userId=user.id).all()
    transactions = Transaction.query.filter_by(userId=user.id).order_by(Transaction.timestamp.desc()).all()

    if request.method == "POST":
        coin_name = request.form.get("coin_name", "").lower().strip()
        amount = request.form.get("amount")

        if not coin_name or not amount:
            flash("Missing coin or amount!", "warning")
            return redirect(url_for("portfolio", username=username))

        try:
            amount = float(amount)
        except:
            flash("Invalid amount!", "danger")
            return redirect(url_for("portfolio", username=username))

        if amount <= 0:
            flash("Amount must be greater than 0!")
            return redirect(url_for("portfolio", username=username))

        wallet_item = Wallet.query.filter_by(
            userId=user.id,
            coinName=coin_name
        ).first()

        if not wallet_item:
            flash("You don't own this coin!", "warning")
            return redirect(url_for("portfolio", username=username))

        if wallet_item.balance < amount:
            flash("Not enough coins to sell!", "warning")
            return redirect(url_for("portfolio", username=username))

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
            return redirect(url_for("portfolio", username=username))

        if not isinstance(price_data, dict) or coin_name not in price_data:
            flash("Coin not found on CoinGecko!", "warning")
            return redirect(url_for("portfolio", username=username))

        price = price_data[coin_name]["usd"]
        total_cost = price * amount

        # sell logic
        user.balance += total_cost
        wallet_item.balance -= amount

        if wallet_item.balance == 0:
            db.session.delete(wallet_item)

        db.session.add(Transaction(
            userId=user.id,
            coinName=coin_name,
            type="sell",
            amount=amount,
            price=price,
            total=total_cost
        ))

        db.session.commit()

        flash(f"Sell {amount} {coin_name} successfully!", "success")
        return redirect(url_for("portfolio", username=username))
    
    # summary calculations
    total_invested = sum(t.total for t in transactions if t.type == "buy")
    total_sold = sum(t.total for t in transactions if t.type == "sell")
    total_trades = len(transactions)
    current_value = 0
    for wallet in wallets:
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": wallet.coinName, "vs_currencies": "usd"},
                timeout=5
            )
            price_data = response.json()
            if isinstance(price_data, dict) and wallet.coinName in price_data:
                current_price = price_data[wallet.coinName]["usd"]
                current_value += wallet.balance * current_price
        except Exception as e:
            print(f"Error fetching price for {wallet.coinName}: {e}")

    profit = current_value + total_sold - total_invested
    roi = (profit / total_invested * 100) if total_invested > 0 else 0    

    return render_template(
        "portfolio.html", 
        username=user.username, 
        balance=user.balance, 
        role=user.role,
        wallets=wallets, 
        page_category="portfolio", 
        view=view,
        total_invested=round(total_invested, 2),
        total_sold=round(total_sold, 2),
        total_trades=total_trades,
        current_value=round(current_value, 2),
        profit=round(profit, 2),
        roi=round(roi, 2),
        transactions=transactions,
        page_title="Portfolio"
        )

# ------------- TRANSACTION ----------------

@app.route("/transactions/<username>")
def transactions(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found", "danger")
        return redirect(url_for("index"))

    if user.is_banned:
        flash("You are banned", "danger")
        return redirect(url_for("index"))

    filter_type = request.args.get("type") # buy, sell or all
    
    query = Transaction.query.filter_by(userId=user.id)
    
    if filter_type == "buy":
        query = query.filter_by(type="buy")
    elif filter_type == "sell":
        query = query.filter_by(type="sell")
    
    transactions = query.order_by(Transaction.timestamp.desc()).all()

    return render_template(
        "transactions.html", 
        username=user.username, 
        balance=user.balance, 
        role=user.role,
        transactions=transactions,
        current_filter=filter_type,
        page_title="Transactions"
        )

# ---------- ADMIN ROUTES ----------------

# ------- ADMIN DASHBOARD --------------

@app.route("/admin_dashboard/<username>")
def admin_dashboard(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash("User not found", "danger")
        return redirect(url_for("index"))

    if user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("index"))

    totalUsers = User.query.count()
    
    totalTransactions = Transaction.query.count()
    
    totalVolume = db.session.query(db.func.sum(Transaction.total)).scalar() or 0

    most_traded_coins = db.session.query(
        Transaction.coinName,
        db.func.count(Transaction.id).label("trade_count")
    ).group_by(Transaction.coinName).order_by(db.desc("trade_count")).limit(5).all()

    most_traded_coin = most_traded_coins[0].coinName if most_traded_coins else "No data"

    return render_template(
        "admin_dashboard.html",
        username=user.username,
        balance=user.balance,
        role=user.role,
        totalTransactions = totalTransactions,
        totalVolume = round(totalVolume, 2),
        most_traded_coin = most_traded_coin,
        totalUsers = totalUsers,
        title="Admin Dashboard"
    )

# ---------- MANAGING USERS ---------

@app.route( "/manage_users/<username>", methods=["GET", "POST"])
def manage_users(username):
    user = User.query.filter_by(username=username).first()
    users = User.query.all()

    if not user:
        flash("User not found", "danger")
        return redirect(url_for("index"))

    if user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("index"))

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

    if not user:
        flash("User not found", "danger")
        return redirect(url_for("index"))

    if user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("index"))

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
        flash("User not found", "danger")
        return redirect(url_for("index"))

    if user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("index"))

    return render_template(
        "logs.html",
        username=user.username,
        balance=user.balance,
        role=user.role,
        title="System Logs"
    )

# ------------- RUN APP -------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)