// Creates (or updates) the Admin account in the database.
// Usage:  node scripts/generate-admin.js <username> <password> <full_name>
// Example: node scripts/generate-admin.js admin Admin@123 "Asif Javed"
require('dotenv').config();
const bcrypt = require('bcryptjs');
const pool = require('../config/db');

async function run() {
  const [username, password, fullName] = process.argv.slice(2);
  if (!username || !password) {
    console.log('Usage: node scripts/generate-admin.js <username> <password> ["Full Name"]');
    process.exit(1);
  }
  const hash = await bcrypt.hash(password, 10);
  const name = fullName || 'Admin';

  const [existing] = await pool.query('SELECT id FROM users WHERE username = ?', [username]);
  if (existing.length) {
    await pool.query('UPDATE users SET password_hash = ?, role = "admin", full_name = ? WHERE username = ?', [hash, name, username]);
    console.log(`Updated existing user "${username}" to Admin with the new password.`);
  } else {
    await pool.query(
      'INSERT INTO users (full_name, username, password_hash, role) VALUES (?, ?, ?, "admin")',
      [name, username, hash]
    );
    console.log(`Admin account "${username}" created successfully.`);
  }
  process.exit(0);
}

run().catch((err) => {
  console.error('Failed to create admin:', err.message);
  process.exit(1);
});
