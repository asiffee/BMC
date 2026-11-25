-- Bandhan Marriage Consultant - MySQL schema
CREATE DATABASE IF NOT EXISTS bandhan_db;
USE bandhan_db;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(150) NOT NULL,
  phone VARCHAR(30),
  username VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin', 'matchmaker') NOT NULL DEFAULT 'matchmaker',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts shown publicly on the Home page (created only by Admin)
CREATE TABLE IF NOT EXISTS posts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  content TEXT,
  image_url VARCHAR(500),
  created_by INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Bride/Groom profiles, entered only by Matchmakers
CREATE TABLE IF NOT EXISTS profiles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  matchmaker_id INT NOT NULL,
  gender ENUM('male', 'female') NOT NULL,
  full_name VARCHAR(150) NOT NULL,
  father_name VARCHAR(150),
  phone VARCHAR(30),
  address VARCHAR(300),
  caste VARCHAR(100),
  education VARCHAR(150),
  age INT,
  sisters_count INT DEFAULT 0,
  brothers_count INT DEFAULT 0,
  father_alive ENUM('yes', 'no') DEFAULT 'yes',
  mother_alive ENUM('yes', 'no') DEFAULT 'yes',
  household_members INT,
  photo_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (matchmaker_id) REFERENCES users(id) ON DELETE CASCADE
);

-- After running this schema, create your Admin login by running (in the backend folder):
--   node scripts/generate-admin.js admin YourStrongPassword "Asif Javed"
