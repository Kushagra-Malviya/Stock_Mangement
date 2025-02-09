import decimal
import re
import streamlit as st
import mysql.connector
from PIL import Image

# Database connection
def connect_to_database():
    try:
        with open("database_credentials.txt", "r") as file:
            lines = file.readlines()

        credentials = {}
        for line in lines:
            key, value = line.strip().split(": ")
            credentials[key] = value

        return mysql.connector.connect(
            host=credentials["Host"],
            user=credentials["User"],
            password=credentials["Password"],
            database=credentials["Database"]
        )

    except FileNotFoundError:
        st.error("Database credentials file not found.")
        st.stop()
    except Exception as e:
        st.error(f"Failed to connect to the database: {str(e)}")
        st.stop()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

connection = connect_to_database()
cursor = connection.cursor()

# Database helper functions (same as original)
def get_wallet_balance(user_id):
    cursor.execute(f"SELECT balance FROM wallets WHERE user_id = {user_id}")
    result = cursor.fetchone()
    return result[0] if result else None

def update_wallet_balance(user_id, new_balance):
    cursor.execute("UPDATE wallets SET balance = %s WHERE user_id = %s", (new_balance, user_id))
    connection.commit()

def check_shares(user_id):
    cursor.execute("""SELECT c.company_name, s.shares_owned 
                   FROM shares s JOIN companies c ON s.company_id = c.company_id 
                   WHERE user_id = %s""", (user_id,))
    results = cursor.fetchall()
    storage = {"Tata Motors": "TATA", "Infosys": "INFO", "Reliance Industries": "RELIANCE", 
               "ICICI Bank": "ICICI", "HDFC Ltd": "HDFC"}
    return {storage[company]: shares for company, shares in results} if results else {}

def get_stock_price(company_id):
    cursor.execute("SELECT stock_price FROM companies WHERE company_id = %s", (company_id,))
    result = cursor.fetchone()
    return result[0] if result else 0.0

def get_user_shares(user_id, company_id):
    cursor.execute("SELECT shares_owned FROM shares WHERE user_id = %s AND company_id = %s", 
                   (user_id, company_id))
    result = cursor.fetchone()
    return result[0] if result else 0

# Streamlit pages
def login_page():
    st.title("StockUp - Login")
    
    with st.form("Login Form"):
        phone = st.text_input("Phone Number")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            cursor.execute("SELECT user_id FROM users WHERE phone_number = %s AND password = %s", 
                           (phone, password))
            result = cursor.fetchone()
            if result:
                st.session_state.logged_in = True
                st.session_state.user_id = result[0]
                st.rerun()
            else:
                st.error("Invalid Credentials")
                
    if st.button("Sign Up"):
        st.session_state.page = "signup"
        st.rerun()
        
    if st.button("Admin Login"):
        st.session_state.page = "admin_login"
        st.rerun()

def signup_page():
    st.title("StockUp - Sign Up")
    
    with st.form("Signup Form"):
        name = st.text_input("Full Name")
        aadhar = st.text_input("Aadhar Number")
        pan = st.text_input("PAN Card")
        phone = st.text_input("Phone Number")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        balance = st.number_input("Initial Balance", min_value=0.0)
        
        if st.form_submit_button("Register"):
            if password != confirm_password:
                st.error("Passwords do not match")
                return
                
            # Validation checks
            if not re.match(r'^\d{12}$', aadhar):
                st.error("Invalid Aadhar number")
                return
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
                st.error("Invalid PAN number")
                return
            if not re.match(r'^[789]\d{9}$', phone):
                st.error("Invalid phone number")
                return
                
            try:
                cursor.execute("""INSERT INTO users (full_name, pan_number, aadhar_number, phone_number, password) 
                               VALUES (%s, %s, %s, %s, %s)""", 
                               (name, pan, aadhar, phone, password))
                user_id = cursor.lastrowid
                cursor.execute("INSERT INTO wallets (user_id, balance) VALUES (%s, %s)", 
                               (user_id, balance))
                connection.commit()
                st.success("Registration Successful! Please login.")
                st.session_state.page = "login"
                st.rerun()
            except mysql.connector.Error as err:
                st.error(f"Registration failed: {err}")

def user_dashboard():
    st.title("StockUp - Trading Dashboard")
    
    # Wallet Section
    balance = get_wallet_balance(st.session_state.user_id)
    col1, col2 = st.columns([1,3])
    with col1:
        st.subheader(f"Wallet Balance: ₹{balance:,.2f}")
        with st.form("Add Money"):
            amount = st.number_input("Amount to Add", min_value=0.0)
            if st.form_submit_button("Add Funds"):
                add_money_to_wallet(st.session_state.user_id, amount)
                st.rerun()
                
    # Portfolio Section
    st.subheader("Your Portfolio")
    shares = check_shares(st.session_state.user_id)
    if shares:
        for stock, qty in shares.items():
            st.write(f"{stock}: {qty} shares")
    else:
        st.write("No holdings yet")
    
    # Stock Market Section
    st.subheader("Available Stocks")
    companies = {
        "TATA": "Tata Motors",
        "INFO": "Infosys",
        "RELIANCE": "Reliance Industries",
        "ICICI": "ICICI Bank",
        "HDFC": "HDFC Bank"
    }
    
    for symbol, name in companies.items():
        with st.expander(f"{name} ({symbol})"):
            price = get_stock_price(list(companies.keys()).index(symbol) + 1)
            st.write(f"Current Price: ₹{price:,.2f}")
            
            col1, col2 = st.columns(2)
            with col1:
                with st.form(f"Buy {symbol}"):
                    buy_qty = st.number_input("Quantity", min_value=1, key=f"buy_{symbol}")
                    if st.form_submit_button("Buy"):
                        buy_shares(st.session_state.user_id, symbol, buy_qty)
                        st.rerun()
            with col2:
                with st.form(f"Sell {symbol}"):
                    sell_qty = st.number_input("Quantity", min_value=1, key=f"sell_{symbol}")
                    if st.form_submit_button("Sell"):
                        sell_shares(st.session_state.user_id, symbol, sell_qty)
                        st.rerun()
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()

def admin_dashboard():
    st.title("Admin Dashboard")
    
    st.subheader("Stock Management")
    with st.form("Add Stock"):
        st.write("Add New Company")
        name = st.text_input("Company Name")
        price = st.number_input("Initial Stock Price", min_value=0.0)
        if st.form_submit_button("Add Company"):
            add_new_company_stock(name, price)
            
    with st.form("Remove Stock"):
        st.write("Remove Company")
        company_id = st.number_input("Company ID", min_value=1, step=1)
        if st.form_submit_button("Remove Company"):
            delete_company_stock(company_id)
    
    st.subheader("System Logs")
    if st.button("View Login Logs"):
        view_login_logs()
        
    if st.button("View Stock Logs"):
        view_stock_logs()
        
    if st.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

# Modified transaction functions
def buy_shares(user_id, symbol, quantity):
    company_id = list({"TATA", "INFO", "RELIANCE", "ICICI", "HDFC"}).index(symbol) + 1
    price = get_stock_price(company_id)
    total_cost = price * quantity
    
    if get_wallet_balance(user_id) >= total_cost:
        current_shares = get_user_shares(user_id, company_id)
        new_balance = get_wallet_balance(user_id) - total_cost
        
        if current_shares > 0:
            cursor.execute("UPDATE shares SET shares_owned = shares_owned + %s WHERE user_id = %s AND company_id = %s",
                           (quantity, user_id, company_id))
        else:
            cursor.execute("INSERT INTO shares (user_id, company_id, shares_owned) VALUES (%s, %s, %s)",
                           (user_id, company_id, quantity))
        
        update_wallet_balance(user_id, new_balance)
        connection.commit()
        st.success(f"Successfully bought {quantity} {symbol} shares!")
    else:
        st.error("Insufficient funds")

def sell_shares(user_id, symbol, quantity):
    company_id = list({"TATA", "INFO", "RELIANCE", "ICICI", "HDFC"}).index(symbol) + 1
    current_shares = get_user_shares(user_id, company_id)
    
    if current_shares >= quantity:
        price = get_stock_price(company_id)
        total_sale = price * quantity
        new_balance = get_wallet_balance(user_id) + total_sale
        
        cursor.execute("UPDATE shares SET shares_owned = shares_owned - %s WHERE user_id = %s AND company_id = %s",
                       (quantity, user_id, company_id))
        update_wallet_balance(user_id, new_balance)
        connection.commit()
        st.success(f"Successfully sold {quantity} {symbol} shares!")
    else:
        st.error("Not enough shares to sell")

# Main app flow
def main():
    if st.session_state.logged_in:
        user_dashboard()
    elif st.session_state.admin_logged_in:
        admin_dashboard()
    else:
        if 'page' not in st.session_state:
            st.session_state.page = "login"
            
        if st.session_state.page == "login":
            login_page()
        elif st.session_state.page == "signup":
            signup_page()
        elif st.session_state.page == "admin_login":
            admin_login_page()

if __name__ == "__main__":
    main()
