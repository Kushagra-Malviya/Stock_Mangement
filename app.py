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
