-- Create users table
CREATE TABLE users (
  user_id INTEGER PRIMARY KEY,  -- Auto-incrementing
  full_name TEXT NOT NULL,
  pan_number TEXT NOT NULL UNIQUE,
  aadhar_number TEXT NOT NULL UNIQUE,
  phone_number TEXT NOT NULL,
  password TEXT NOT NULL
);

-- Create wallets table
CREATE TABLE wallets (
  wallet_id INTEGER PRIMARY KEY,  -- Auto-incrementing
  user_id INTEGER NOT NULL,
  balance REAL NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create companies table
CREATE TABLE companies (
  company_id INTEGER PRIMARY KEY,  -- Auto-incrementing
  company_name TEXT NOT NULL,
  sector TEXT NOT NULL,
  stock_price REAL NOT NULL
);

-- Create shares table
CREATE TABLE shares (
  share_id INTEGER PRIMARY KEY,  -- Auto-incrementing
  user_id INTEGER NOT NULL,
  company_id INTEGER NOT NULL,
  shares_owned INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- Insert data for 5 users
INSERT INTO users (full_name, pan_number, aadhar_number, phone_number, password) VALUES
('Amit Kumar', 'ABCDEF12', '123456789012', '9876543210', 'password1'),
('Sneha Gupta', 'FGHIJ5678', '345678901234', '8765432109', 'password2'),
('Rajesh Verma', 'LMNOP1234', '5678901234', '7654321098', 'password3'),
('Priya Sharma', 'UVWXYZ5678', '7890123456', '6543210987', 'password4'),
('Ravi Singh', 'PQRSTU1234', '8900234567', '5432109876', 'password5');

-- Insert balance data for 5 users
INSERT INTO wallets (user_id, balance) VALUES
(1, 10000.00), 
(2, 9500.00),  
(3, 11000.00), 
(4, 8500.00),  
(5, 10250.00); 

-- Add companies
INSERT INTO companies (company_name, sector, stock_price) VALUES
  ('Tata Motors', 'Automobile', 100.00),
  ('Infosys', 'Information Technology', 50.00),
  ('Reliance Industries', 'Conglomerate', 75.00),
  ('ICICI Bank', 'Banking', 45.00),
  ('HDFC Ltd', 'Finance', 60.00);

-- Insert shares for User 1 (Amit Kumar)
INSERT INTO shares (user_id, company_id, shares_owned) VALUES 
(1, 1, 50),
(1, 2, 75),
(1, 4, 30);

-- Insert shares for User 2 (Sneha Gupta)
INSERT INTO shares (user_id, company_id, shares_owned) VALUES 
(2, 2, 60),
(2, 3, 90),
(2, 5, 40);

-- Insert shares for User 3 (Rajesh Verma)
INSERT INTO shares (user_id, company_id, shares_owned) VALUES 
(3, 1, 75),
(3, 4, 20),
(3, 5, 50);

-- Insert shares for User 4 (Priya Sharma)
INSERT INTO shares (user_id, company_id, shares_owned) VALUES 
(4, 3, 100),
(4, 5, 70);

-- Insert shares for User 5 (Ravi Singh)
INSERT INTO shares (user_id, company_id, shares_owned) VALUES 
(5, 1, 40),
(5, 2, 85),
(5, 3, 60);
