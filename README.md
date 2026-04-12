# Cryptocurrency-Trading-Simulator

## Project Overview

This is a web-based Cryptocurrency Trading Simulator uni project. The system allows users to simulate cryptocurrency trading using virtual funds in a controlled and risk-free environment (not using real money).

Each user receives an initial balance of $1000 and can perform buy and sell operations based on real-time market prices retrieved from the CoinGecko API. The platform records transactions and provides portfolio analytics, including profit/loss and return on investment (ROI).
The application is strictly educational and does not process real financial transactions.


## Technology Stack

Frontend:
- HTML
- CSS
- Bootstrap
- JavaScript
- Chart.js

Backend:
- Python
- Flask
- RESTful API architecture

Database:
- SQLite (via Flask-SQLAlchemy)

Security:
- Werkzeug (Password Hashing)

External Integration:
- CoinGecko Public API


## Project Structure
- app.py # Main Flask application
- config.py # Configuration settings
- static/ # CSS, JavaScript, assets
- templates/ # HTML templates


## Core Features

- User registration and login
- Role-based access (User / Admin)
- Real-time cryptocurrency prices
- Buy and sell simulation
- Portfolio analytics with charts
- Transaction history
- Admin management panel


## Setup Instructions

1. Clone the repository
   "git clone https://github.com/Dembem1/Cryptocurrency-Trading-Simulator.git"
2. Create a virtual environment
3. Install dependencies:
   "pip install flask flask-sqlalchemy flask-migrate requests"
4. Enviroment Configuration
   Database: Uses SQLite by default (test.db)
   API: Uses the CoinGecko Public Api (No API key key required for basic usage)
5. Run the application:
   "python app.py"
