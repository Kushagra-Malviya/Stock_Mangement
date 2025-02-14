import decimal
import re
import streamlit as st
import sqlite3
from PIL import Image

# Database connection
def connect_to_database():
    try:
        connection = sqlite3.connect("stockup.db", check_same_thread=False)
        return connection
    except Exception as e:
        st.error(f"Failed to connect to the database: {str(e)}")
        st.stop()

connection = connect_to_database()
cursor = connection.cursor()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# Database helper functions
def get_wallet_balance(user_id):
    cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def update_wallet_balance(user_id, new_balance):
    cursor.execute("UPDATE wallets SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    connection.commit()

def check_shares(user_id):
    cursor.execute("""
        SELECT c.company_name, s.shares_owned 
        FROM shares s JOIN companies c ON s.company_id = c.company_id 
        WHERE user_id = ?""", (user_id,))
    results = cursor.fetchall()
    storage = {"Tata Motors": "TATA", "Infosys": "INFO", "Reliance Industries": "RELIANCE", 
               "ICICI Bank": "ICICI", "HDFC Ltd": "HDFC"}
    return {storage[company]: shares for company, shares in results} if results else {}

def get_stock_price(company_id):
    cursor.execute("SELECT stock_price FROM companies WHERE company_id = ?", (company_id,))
    result = cursor.fetchone()
    return result[0] if result else 0.0

def get_user_shares(user_id, company_id):
    cursor.execute("SELECT shares_owned FROM shares WHERE user_id = ? AND company_id = ?", 
                   (user_id, company_id))
    result = cursor.fetchone()
    return result[0] if result else 0

def update_user_shares(user_id, company_id, new_share_count):
    cursor.execute("UPDATE shares SET shares_owned = ? WHERE user_id = ? AND company_id = ?", 
                   (new_share_count, user_id, company_id))
    connection.commit()

def add_shares_to_portfolio(user_id, company_id, shares):
    cursor.execute("INSERT INTO shares (user_id, company_id, shares_owned) VALUES (?, ?, ?)", 
                   (user_id, company_id, shares))
    connection.commit()

def remove_shares_from_portfolio(user_id, company_id, shares):
    current_shares = get_user_shares(user_id, company_id)
    if current_shares >= shares:
        new_share_count = current_shares - shares
        update_user_shares(user_id, company_id, new_share_count)
    else:
        st.error("You do not have enough shares to make the sale.")

# Streamlit pages
def login_page():
    st.title("StockUp - Login")
    
    with st.form("Login Form"):
        phone = st.text_input("Phone Number")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            cursor.execute("SELECT user_id FROM users WHERE phone_number = ? AND password = ?", 
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
                               VALUES (?, ?, ?, ?, ?)""", 
                               (name, pan, aadhar, phone, password))
                user_id = cursor.lastrowid
                cursor.execute("INSERT INTO wallets (user_id, balance) VALUES (?, ?)", 
                               (user_id, balance))
                connection.commit()
                st.success("Registration Successful! Please login.")
                st.session_state.page = "login"
                st.rerun()
            except sqlite3.Error as err:
                st.error(f"Registration failed: {err}")

def user_dashboard():
    st.title("StockUp - User Dashboard")
    
    user_id = st.session_state.user_id
    balance = get_wallet_balance(user_id)
    
    st.sidebar.title("Navigation")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()
    
    st.write(f"Welcome, User ID: {user_id}")
    st.write(f"Your current balance: ₹{balance}")
    
    if st.button("Add Money to Wallet"):
        amount = st.number_input("Enter amount to add", min_value=0.0)
        if st.button("Add"):
            new_balance = balance + decimal.Decimal(amount)
            update_wallet_balance(user_id, new_balance)
            st.success(f"Added ₹{amount} to your wallet. New balance: ₹{new_balance}")
            st.rerun()
    
    st.subheader("Your Portfolio")
    shares_data = check_shares(user_id)
    if shares_data:
        for company, shares in shares_data.items():
            st.write(f"{company}: {shares} shares")
    else:
        st.write("You currently own no shares.")
    
    st.subheader("Buy/Sell Shares")
    companies = {"TATA": "Tata Motors", "INFO": "Infosys", "RELIANCE": "Reliance Industries", 
                 "ICICI": "ICICI Bank", "HDFC": "HDFC Ltd"}
    selected_company = st.selectbox("Select Company", list(companies.keys()), format_func=lambda x: companies[x])
    
    if st.button("View Company Details"):
        company_id = {"TATA": 1, "INFO": 2, "RELIANCE": 3, "ICICI": 4, "HDFC": 5}[selected_company]
        stock_price = get_stock_price(company_id)
        st.write(f"Current stock price for {companies[selected_company]}: ₹{stock_price}")
        
        action = st.radio("Choose Action", ["Buy", "Sell"])
        if action == "Buy":
            shares_to_buy = st.number_input("Enter number of shares to buy", min_value=1)
            if st.button("Buy Shares"):
                total_cost = shares_to_buy * stock_price
                if balance >= total_cost:
                    new_balance = balance - decimal.Decimal(total_cost)
                    update_wallet_balance(user_id, new_balance)
                    current_shares = get_user_shares(user_id, company_id)
                    if current_shares > 0:
                        new_shares = current_shares + shares_to_buy
                        update_user_shares(user_id, company_id, new_shares)
                    else:
                        add_shares_to_portfolio(user_id, company_id, shares_to_buy)
                    st.success(f"Successfully bought {shares_to_buy} shares of {companies[selected_company]}.")
                    st.rerun()
                else:
                    st.error("Insufficient balance to make the purchase.")
        else:
            shares_to_sell = st.number_input("Enter number of shares to sell", min_value=1)
            if st.button("Sell Shares"):
                current_shares = get_user_shares(user_id, company_id)
                if current_shares >= shares_to_sell:
                    total_sale = shares_to_sell * stock_price
                    new_balance = balance + decimal.Decimal(total_sale)
                    update_wallet_balance(user_id, new_balance)
                    remove_shares_from_portfolio(user_id, company_id, shares_to_sell)
                    st.success(f"Successfully sold {shares_to_sell} shares of {companies[selected_company]}.")
                    st.rerun()
                else:
                    st.error("You do not have enough shares to make the sale.")

def admin_login_page():
    st.title("StockUp - Admin Login")
    
    with st.form("Admin Login Form"):
        admin_id = st.text_input("Admin ID")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            cursor.execute("SELECT * FROM admin_login WHERE username = ? AND password = ?", 
                           (admin_id, password))
            result = cursor.fetchone()
            if result:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Invalid Admin Credentials")
    
    if st.button("Back to User Login"):
        st.session_state.page = "login"
        st.rerun()

def admin_dashboard():
    st.title("StockUp - Admin Dashboard")
    
    st.sidebar.title("Navigation")
    if st.sidebar.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()
    
    st.subheader("Add New Company Stock")
    with st.form("Add Stock Form"):
        company_name = st.text_input("Company Name")
        stock_price = st.number_input("Stock Price", min_value=0.0)
        if st.form_submit_button("Add Stock"):
            try:
                cursor.execute("INSERT INTO companies (company_name, stock_price) VALUES (?, ?)", 
                               (company_name, stock_price))
                connection.commit()
                st.success("New company stock added successfully!")
            except sqlite3.Error as err:
                st.error(f"Failed to add new company stock: {err}")
    
    st.subheader("Delete Company Stock")
    cursor.execute("SELECT company_id, company_name FROM companies")
    companies = cursor.fetchall()
    if companies:
        company_to_delete = st.selectbox("Select Company to Delete", companies, format_func=lambda x: x[1])
        if st.button("Delete Company"):
            try:
                cursor.execute("DELETE FROM companies WHERE company_id = ?", (company_to_delete[0],))
                connection.commit()
                st.success("Company stock deleted successfully!")
            except sqlite3.Error as err:
                st.error(f"Failed to delete company stock: {err}")
    else:
        st.write("No companies available to delete.")
    
    st.subheader("View Login Logs")
    if st.button("View Login Logs"):
        cursor.execute("SELECT * FROM user_login_log")
        login_logs = cursor.fetchall()
        if login_logs:
            st.write("Login Logs:")
            for log in login_logs:
                st.write(f"User ID: {log[1]}, Login Time: {log[2]}")
        else:
            st.write("No login logs available.")
    
    st.subheader("View Stock Logs")
    if st.button("View Stock Logs"):
        cursor.execute("SELECT * FROM stock_log")
        stock_logs = cursor.fetchall()
        if stock_logs:
            st.write("Stock Logs:")
            for log in stock_logs:
                st.write(f"Log ID: {log[0]}, Company ID: {log[1]}, Stock Price: {log[2]}, Log Time: {log[3]}")
        else:
            st.write("No stock logs available.")

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
