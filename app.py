import decimal
import re
from tkinter import messagebox

import mysql.connector
from PIL import Image
from customtkinter import *

app = CTk()
app.geometry("500x400")
set_appearance_mode("dark")
set_default_color_theme("blue")
app.title("DBMS")
frame = CTkFrame(master=app)
img_label = CTkLabel(master=app)
wallet_frame = CTkFrame(master=app)
port = CTkFrame(master=app)
stock_frame = CTkFrame(master=app)

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
        print("Database credentials file not found.")
        sys.exit()
    except Exception as e:
        print(f"Failed to connect to the database: {str(e)}")
        sys.exit()


connection = connect_to_database()
cursor = connection.cursor()


def get_wallet_balance(user_id):
    cursor.execute(f"SELECT balance FROM wallets WHERE user_id = {user_id}")
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None


def update_wallet_balance(user_id, new_balance):
    sql = "UPDATE wallets SET balance = %s WHERE user_id = %s"
    val = (new_balance, user_id)

    # Clear any pending results
    cursor.fetchall()

    cursor.execute(sql, val)
    connection.commit()
    frame_count = 0
    frames_to_destroy = []

    for widget in app.winfo_children():
        if "frame" in widget.winfo_name():
            frames_to_destroy.append(widget)
            frame_count += 1
    for frame in frames_to_destroy:
        frame.destroy()
    logged_in(user_id)


def add_money_to_wallet(user_id, amount):
    current_balance = get_wallet_balance(user_id)
    if current_balance is not None:
        # Convert the amount to decimal
        try:
            amount_decimal = decimal.Decimal(amount)
        except decimal.InvalidOperation as e:
            messagebox.showerror("Error", "Please add a valid Number")
            amount_decimal = 0
        new_balance = current_balance + amount_decimal
        update_wallet_balance(user_id, new_balance)
    else:
        print("User wallet not found. Please check the user ID.")


def add(userid):
    new_bal = CTkInputDialog(text="Enter Amount To Add", title="Balance").get_input()
    if new_bal == None:
        return
    add_money_to_wallet(userid, new_bal)


def check_shares(user_id):
    sql = "SELECT c.company_name, s.shares_owned FROM shares s JOIN companies c ON s.company_id = c.company_id WHERE user_id = %s"
    val = (user_id,)
    cursor.execute(sql, val)
    results = cursor.fetchall()
    storage = {"Tata Motors": "TATA", "Infosys": "INFO", "Reliance Industries": "RELIANCE", "ICICI Bank": "ICICI",
               "HDFC Ltd": "HDFC"}

    if results:
        data = {}
        for company, shares in results:
            data[storage[company]] = shares
        return data
    else:
        return {}


def update_user_shares(user_id, company_id, new_share_count):
    sql = "UPDATE shares SET shares_owned = %s WHERE user_id = %s AND company_id = %s"
    val = (new_share_count, user_id, company_id)
    cursor.execute(sql, val)
    connection.commit()


def get_stock_price(company_id):
    sql = "SELECT stock_price FROM companies WHERE company_id = %s"
    val = (company_id,)
    cursor.execute(sql, val)
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        return 0.0


def add_shares_to_portfolio(user_id, company_id, shares):
    sql = "INSERT INTO shares (user_id, company_id, shares_owned) VALUES (%s, %s, %s)"
    val = (user_id, company_id, shares)
    cursor.execute(sql, val)
    connection.commit()


def get_user_shares(user_id, company_id):
    sql = "SELECT shares_owned FROM shares WHERE user_id = %s AND company_id = %s"
    val = (user_id, company_id)
    cursor.execute(sql, val)
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return 0


def buy_shares(user_id, company):
    global wallet_frame
    global port
    global stock_frame
    ids = {"TATA": "1", "INFO": "2", "RELIANCE": "3", "ICICI": "4", "HDFC": "5"}
    company_id = ids[company]
    shares_to_buy = CTkInputDialog(text="Enter Number of Shares To Buy", title=company).get_input()
    if shares_to_buy:
        shares_to_buy = int(shares_to_buy)
    else:
        return

    stock_price = get_stock_price(company_id)
    purchase_amount = shares_to_buy * float(stock_price)
    wallet_balance = float(get_wallet_balance(user_id))

    current_shares = get_user_shares(user_id, company_id)

    if wallet_balance >= purchase_amount:
        new_balance = wallet_balance - purchase_amount
        update_wallet_balance(user_id, new_balance)

        if current_shares > 0:
            # The user already owns shares in this company; update the share count.
            new_shares = current_shares + shares_to_buy
            update_user_shares(user_id, company_id, new_shares)
        else:
            # The user does not own shares in this company; insert a new entry.
            add_shares_to_portfolio(user_id, company_id, shares_to_buy)

        messagebox.showinfo("Done", f"{company} Shares Bought Successfully")
        frame_count = 0
        frames_to_destroy = []

        for widget in app.winfo_children():
            if "frame" in widget.winfo_name():
                frames_to_destroy.append(widget)
                frame_count += 1
        # Then, destroy each of the identified frames
        for frame in frames_to_destroy:
            frame.destroy()

        logged_in(user_id)

    else:
        messagebox.showerror("Error", "Insufficient balance to make the purchase.")


def remove_shares_from_portfolio(user_id, company_id, shares):
    current_shares = get_user_shares(user_id, company_id)

    if current_shares >= shares:
        new_share_count = current_shares - shares
        update_user_shares(user_id, company_id, new_share_count)
    else:
        print("You do not have enough shares to make the sale.")


def sell_shares(user_id, company):
    global stock_frame
    global port
    global wallet_frame
    ids = {"TATA": "1", "INFO": "2", "RELIANCE": "3", "ICICI": "4", "HDFC": "5"}
    company_id = ids[company]
    shares_to_sell = CTkInputDialog(text="Enter Number of Shares To Sell", title=company).get_input()

    if shares_to_sell:
        shares_to_sell = int(shares_to_sell)
    else:
        return

    user_shares = int(get_user_shares(user_id, company_id))
    if user_shares >= shares_to_sell:
        stock_price = float(get_stock_price(company_id))
        sale_amount = shares_to_sell * stock_price
        wallet_balance = float(get_wallet_balance(user_id))
        new_balance = wallet_balance + sale_amount  # Update wallet balance with the sale amount
        update_wallet_balance(user_id, new_balance)  # Update the wallet balance in the database
        remove_shares_from_portfolio(user_id, company_id, shares_to_sell)
        messagebox.showinfo("Done", f"You have sold {shares_to_sell} shares of {company}.")
        frame_count = 0
        frames_to_destroy = []

        for widget in app.winfo_children():
            if "frame" in widget.winfo_name():
                frames_to_destroy.append(widget)
                frame_count += 1
        for frame in frames_to_destroy:
            frame.destroy()
        logged_in(user_id)
    else:
        messagebox.showerror("Error", "You do not have enough shares to make the sale.")


def out():
    global wallet_frame
    global port
    global stock_frame
    global top
    try:
        top.destroy()
    except:
        pass

    wallet_frame.destroy()
    port.destroy()
    stock_frame.destroy()

    page1()


def view(user_id, company):
    global top
    try:
        top.destroy()
    except:
        pass
    top = CTkToplevel(app)
    top.geometry("300x300")
    top.title(company)
    comp = CTkImage(Image.open(f"./images/{company}.png"), size=(200, 220))
    comp_l = CTkLabel(master=top, text="", image=comp)
    comp_l.pack()
    ids = {"TATA": "1", "INFO": "2", "RELIANCE": "3", "ICICI": "4", "HDFC": "5"}

    price = get_stock_price(ids[company])
    price_label = CTkLabel(master=top, text=f"₹ {price}", font=("Roboto", 16))
    price_label.pack()
    buy_button = CTkButton(master=top, text="Buy", width=120, height=40, hover_color="green", font=("Roboto", 24),
                           command=lambda: buy_shares(user_id, company))
    buy_button.place(x=20, y=250)

    sell_button = CTkButton(master=top, text="Sell", width=120, height=40, hover_color="red", font=("Roboto", 24),
                            command=lambda: sell_shares(user_id, company))
    sell_button.place(x=160, y=250)


def logged_in(userid):
    global frame
    global img_label
    global wallet_frame
    global port
    global stock_frame
    frame.destroy()
    img_label.destroy()
    balance = get_wallet_balance(userid)
    wallet_frame = CTkFrame(master=app, width=220, height=50)
    wallet_frame.grid(row=0, column=0, padx=10, pady=10)

    bal = CTkLabel(master=wallet_frame, text="Balance: ₹", font=("Roboto", 15))
    bal.place(x=20, y=10)
    if balance >= 1000000:
        display = str(round(balance / 1000000, 2)) + " M"
    elif balance >= 1000:
        display = str(round(balance / 1000, 2)) + " K"
    else:
        display = str(balance)
    amt = CTkLabel(master=wallet_frame, text=display, font=("Roboto", 15))
    amt.place(x=90, y=10)
    btn = CTkButton(master=wallet_frame, text="Add +", width=60, height=20, command=lambda: add(userid))
    btn.place(x=150, y=13)

    port = CTkFrame(master=app, width=220, height=320)
    port.grid(row=1, column=0, padx=10, pady=(0, 10))
    txt = CTkLabel(master=port, text="Portfolio", font=("Roboto", 24))
    txt.place(x=60, y=5)
    shares_data = check_shares(userid)
    for i, share in enumerate(shares_data):
        suitcase = CTkImage(dark_image=Image.open("./images/bagw.png"), light_image=Image.open("./images/bagb.png"),
                            size=(20, 15))
        bag = CTkLabel(master=port, text="", image=suitcase)
        bag.place(x=8, y=58 + 40 * i)
        stock_label = CTkLabel(master=port, text=f"{share} : {shares_data[share]} shares", font=("Roboto", 16))

        stock_label.place(x=30, y=60 + 40 * i)

    stock_frame = CTkFrame(master=app, width=250, height=380)
    stock_frame.grid(row=0, column=1, rowspan=2)

    # Add a heading for the stock frame
    stock_heading = CTkLabel(master=stock_frame, text="Watchlist", font=("Roboto", 24))
    stock_heading.place(x=80, y=5)

    # Create a list of stocks with their names and identifiers
    portfolio_stocks = [
        {"name": "TATA Motors", "identifier": "TATA"},
        {"name": "InfoSys", "identifier": "INFO"},
        {"name": "Reliance", "identifier": "RELIANCE"},
        {"name": "ICICI Bank", "identifier": "ICICI"},
        {"name": "HDFC Bank", "identifier": "HDFC"}
    ]

    for i, stock_data in enumerate(portfolio_stocks):
        stock_name = stock_data["name"]
        stock_label = CTkLabel(master=stock_frame, text=stock_name, font=("Roboto", 16))
        stock_label.place(x=80, y=60 + 60 * i)

        eye = CTkImage(Image.open("./images/eye.png"), size=(17, 10))
        viw_btn = CTkButton(master=stock_frame, text="View", width=80, height=20, hover_color="purple", image=eye,
                            command=lambda stock=stock_data["identifier"]: view(userid, stock))
        viw_btn.place(x=90, y=95 + 60 * i)
    lg = CTkImage(Image.open("./images/logout.png"), size=(20, 22))
    logout = CTkButton(master=port, text="Logout", command=out, image=lg)
    logout.place(x=40, y=280)


def check(user, aadhar, pan, phone, pass1, pass2, balance):
    if user != "" and aadhar != "" and pan != "" and phone != "" and pass1 != "" and balance != "":
        # Validate Aadhar number (12 digits)
        if not re.match(r'^\d{12}$', aadhar):
            messagebox.showerror("Error", "Invalid Aadhar number")
            return

        # Validate PAN number (10 characters, uppercase, alphanumeric)
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
            messagebox.showerror("Error", "Invalid PAN number")
            return

        # Validate Indian phone number (10 digits starting with 7, 8, or 9)
        if not re.match(r'^[789]\d{9}$', phone):
            messagebox.showerror("Error", "Invalid phone number")
            return

        if pass1 == pass2:
            AddUser(user, pan, aadhar, phone, pass1, balance)
            messagebox.showinfo("Done", "Registered Successfully")
            page1()
        else:
            messagebox.showerror("Error", "Passwords do not match")
    else:
        messagebox.showerror("Error", "Fill in all details")


def AddUser(full_name, pan_number, aadhar_number, phone_number, password, initial_balance):
    user_sql = "INSERT INTO users (full_name, pan_number, aadhar_number, phone_number, password) VALUES (%s, %s, %s, %s, %s)"
    user_val = (full_name, pan_number, aadhar_number, phone_number, password)

    cursor.execute(user_sql, user_val)
    connection.commit()

    cursor.execute("SELECT LAST_INSERT_ID() AS user_id")
    user_id = cursor.fetchone()[0]

    wallet_sql = "INSERT INTO wallets (user_id, balance) VALUES (%s, %s)"
    wallet_val = (user_id, initial_balance)

    cursor.execute(wallet_sql, wallet_val)
    connection.commit()

    print("User registered successfully!")


def login_check(phone_number, password):
    global frame
    global img_label
    sql = "SELECT user_id FROM users WHERE phone_number = %s AND password = %s"
    val = (phone_number, password)
    cursor.execute(sql, val)
    result = cursor.fetchone()
    if result:
        frame.destroy()
        img_label.destroy()
        logged_in(result[0])
    else:
        messagebox.showerror("Error", "Invalid Credentials")


def backfnc():
    global frame
    global img_label
    frame.destroy()
    img_label.destroy()
    page1()


def login():
    global frame
    global img_label
    frame.destroy()
    frame = CTkFrame(master=app, width=200, height=400)
    frame.grid(row=0, column=1)

    name = CTkLabel(master=frame, text="StockUp", font=("Roboto", 24))
    name.place(x=65, y=20)
    img_logo = CTkImage(Image.open("./images/logo.png"), size=(50, 50))
    logo = CTkLabel(master=frame, image=img_logo, text="")
    logo.place(x=15, y=10)
    # Phone Number Entry
    phone_entry = CTkEntry(master=frame, placeholder_text="Phone Number")
    phone_entry.place(x=30, y=150)

    password_entry = CTkEntry(master=frame, placeholder_text="Password", show="*")
    password_entry.place(x=30, y=190)

    login_button = CTkButton(master=frame, text="Login",
                             command=lambda: login_check(phone_entry.get(), password_entry.get()))
    login_button.place(x=30, y=230)

    back = CTkButton(master=frame, text="Back",
                     command=backfnc, hover_color="orange")
    back.place(x=30, y=270)


def signup():
    global frame
    frame.destroy()
    frame = CTkFrame(master=app, width=200, height=400)
    frame.grid(row=0, column=1)

    name = CTkLabel(master=frame, text="StockUp", font=("Roboto", 24))
    name.place(x=65, y=20)
    img_logo = CTkImage(Image.open("./images/logo.png"), size=(50, 50))
    logo = CTkLabel(master=frame, image=img_logo, text="")
    logo.place(x=15, y=10)

    # UserName
    username = CTkEntry(master=frame, placeholder_text="Full Name")
    username.place(x=30, y=60)

    # Aadhar Number Entry
    aadhar_entry = CTkEntry(master=frame, placeholder_text="Aadhar Number")
    aadhar_entry.place(x=30, y=100)

    # PAN Card Entry
    pan_entry = CTkEntry(master=frame, placeholder_text="PAN Card")
    pan_entry.place(x=30, y=140)

    # Phone Number Entry
    phone_entry = CTkEntry(master=frame, placeholder_text="Phone Number")
    phone_entry.place(x=30, y=180)

    # Password Entry
    password_entry = CTkEntry(master=frame, placeholder_text="Password", show="*")
    password_entry.place(x=30, y=220)

    # Password Confirmation Entry
    password_confirm_entry = CTkEntry(master=frame, placeholder_text="Confirm Password", show="*")
    password_confirm_entry.place(x=30, y=260)

    # Balance
    balance = CTkEntry(master=frame, placeholder_text="Balance")
    balance.place(x=30, y=300)

    sign_btn = CTkButton(master=frame, text="Sign-Up",
                         command=lambda: check(username.get(), aadhar_entry.get(), pan_entry.get(), phone_entry.get(),
                                               password_confirm_entry.get(), password_entry.get(), balance.get()))
    sign_btn.place(x=30, y=335)
    bck = CTkButton(master=frame, text="Back",
                    command=backfnc, hover_color="orange")
    bck.place(x=30, y=370)

def admin_login():
    global frame
    frame.destroy()
    frame = CTkFrame(master=app, width=200, height=400)
    frame.grid(row=0, column=1)

    img_logo = CTkImage(Image.open("./images/logo.png"), size=(50, 50))
    logo = CTkLabel(master=frame, image=img_logo, text="")
    logo.place(x=15, y=10)

    name = CTkLabel(master=frame, text="StockUp", font=("Roboto", 24))
    name.place(x=65, y=20)

    admin_id_entry = CTkEntry(master=frame, placeholder_text="Admin ID")
    admin_id_entry.place(x=30, y=100)

    admin_password_entry = CTkEntry(master=frame, placeholder_text="Password", show="*")
    admin_password_entry.place(x=30, y=140)

    admin_login_button = CTkButton(master=frame, text="Admin Login",
                                   command=lambda: admin_login_check(admin_id_entry.get(), admin_password_entry.get()))
    admin_login_button.place(x=30, y=180)

    back_button = CTkButton(master=frame, text="Back",
                            command=back_to_login, hover_color="orange")
    back_button.place(x=30, y=220)

def admin_login_check(username, password):
    try:
        sql = "SELECT * FROM admin_login WHERE username = %s AND password = %s"
        val = (username, password)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        if result:
            messagebox.showinfo("Success", "Admin login successful!")
            admin_page()
        else:
            messagebox.showerror("Error", "Invalid admin credentials")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to login as admin: {str(e)}")


def back_to_login():
    global frame
    frame.destroy()
    page1()


def admin_page():
    global frame
    global img_label
    frame.destroy()
    img = CTkImage(Image.open("./images/login.jpg"), size=(300, 400))
    img_label = CTkLabel(master=app, image=img, text="")
    img_label.grid(row=0, column=0)

    frame = CTkFrame(master=app, width=200, height=400)
    frame.grid(row=0, column=1)

    img_logo = CTkImage(Image.open("./images/logo.png"), size=(50, 50))
    logo = CTkLabel(master=frame, image=img_logo, text="")
    logo.place(x=15, y=10)

    name = CTkLabel(master=frame, text="StockUp", font=("Roboto", 24))
    name.place(x=65, y=20)
    # Add new company stock button
    add_stock_button = CTkButton(master=frame, text="Add New Stock",
                                 command=add_new_company_stock)
    add_stock_button.place(x=30, y=140)

    # Delete company stock button
    delete_stock_button = CTkButton(master=frame, text="Delete Company Stock",
                                    command=delete_company_stock)
    delete_stock_button.place(x=30, y=180)

    # View login logs button
    login_logs_button = CTkButton(master=frame, text="View Login Logs",
                                  command=view_login_logs)
    login_logs_button.place(x=30, y=220)

    # View stock logs button
    stock_logs_button = CTkButton(master=frame, text="View Stock Logs",
                                  command=view_stock_logs)
    stock_logs_button.place(x=30, y=260)



def add_new_company_stock(company_name, stock_price):
    try:
        sql = "INSERT INTO companies (company_name, stock_price) VALUES (%s, %s)"
        val = (company_name, stock_price)
        cursor.execute(sql, val)
        connection.commit()
        messagebox.showinfo("Success", "New company stock added successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add new company stock: {str(e)}")

def delete_company_stock(company_id):
    try:
        sql = "DELETE FROM companies WHERE company_id = %s"
        val = (company_id,)
        cursor.execute(sql, val)
        connection.commit()
        messagebox.showinfo("Success", "Company stock deleted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete company stock: {str(e)}")

def view_login_logs():
    try:
        cursor.execute("SELECT * FROM user_login_log")
        login_logs = cursor.fetchall()
        if login_logs:
            log_text = "\n".join([f"User ID: {log[1]}, Login Time: {log[2]}" for log in login_logs])
            messagebox.showinfo("Login Logs", log_text)
        else:
            messagebox.showinfo("Login Logs", "No login logs available.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch login logs: {str(e)}")

def view_stock_logs():
    try:
        cursor.execute("SELECT * FROM stock_log")
        stock_logs = cursor.fetchall()
        if stock_logs:
            log_text = "\n".join([f"Log ID: {log[0]}, Company ID: {log[1]}, Stock Price: {log[2]}, Log Time: {log[3]}" for log in stock_logs])
            messagebox.showinfo("Stock Logs", log_text)
        else:
            messagebox.showinfo("Stock Logs", "No stock logs available.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch stock logs: {str(e)}")


def close():
    """
    It Closes the Application

    :return: None
    """
    app.destroy()


def change_theme():
    """
    Changes the Theme from light to dark and visa-vera

    :return: None
    """
    set_appearance_mode("light") if app._get_appearance_mode() == "dark" else set_appearance_mode("dark")


def page1():
    """
    Create the initial page of the application.

    This function sets up the initial page of the application, which includes a background image, the application logo,
    and buttons to either log in, sign up, or log in as an admin.

    Returns:
        None
    """
    global frame
    global img_label
    frame.destroy()
    img_label.destroy()
    wallet_frame.destroy()
    port.destroy()
    stock_frame.destroy()
    img = CTkImage(Image.open("./images/login.jpg"), size=(300, 400))
    img_label = CTkLabel(master=app, image=img, text="")
    img_label.grid(row=0, column=0)

    frame = CTkFrame(master=app, width=200, height=400)
    frame.grid(row=0, column=1)

    img_logo = CTkImage(Image.open("./images/logo.png"), size=(50, 50))
    logo = CTkLabel(master=frame, image=img_logo, text="")
    logo.place(x=15, y=10)

    name = CTkLabel(master=frame, text="StockUp", font=("Roboto", 24))
    name.place(x=65, y=20)

    login_button = CTkButton(master=frame, text="Login",
                             command=login)
    login_button.place(x=30, y=140)

    signup_button = CTkButton(master=frame, text="Sign-Up",
                              command=signup)
    signup_button.place(x=30, y=180)

    admin_login_button = CTkButton(master=frame, text="Admin Login",
                                   command=admin_login)
    admin_login_button.place(x=30, y=220)

    close_btn = CTkButton(master=frame, text="Close App", command=close, fg_color="green", hover_color="red")
    close_btn.place(x=30, y=260)

    t = CTkImage(dark_image=Image.open("./images/dark.png"), light_image=Image.open("./images/light.png"),
                 size=(66, 34))
    theme = CTkButton(master=frame, text="", image=t, fg_color="transparent", hover=False, width=66, height=34,
                      command=change_theme)
    theme.place(x=60, y=300)


page1()
# view()
app.mainloop()
print("""
App Closed...
""")
""" Code Ends """
