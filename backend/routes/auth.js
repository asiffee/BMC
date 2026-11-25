const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const pool = require('../config/db');

const router = express.Router();

// Public: a new Matchmaker registers themselves.
// (Admin accounts are NOT created here — use backend/scripts/generate-admin.js)
router.post('/register', async (req, res) => {
  try {
    const { full_name, phone, username, password } = req.body;
    if (!full_name || !username || !password) {
      return res.status(400).json({ error: 'full_name, username and password are required.' });
    }

    const [existing] = await pool.query('SELECT id FROM users WHERE username = ?', [username]);
    if (existing.length) return res.status(409).json({ error: 'This username is already taken.' });

    const hash = await bcrypt.hash(password, 10);
    const [result] = await pool.query(
      'INSERT INTO users (full_name, phone, username, password_hash, role) VALUES (?, ?, ?, ?, "matchmaker")',
      [full_name, phone || null, username, hash]
    );

    const token = jwt.sign(
      { id: result.insertId, role: 'matchmaker', full_name },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );
    res.status(201).json({ token, user: { id: result.insertId, full_name, role: 'matchmaker' } });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Registration failed.' });
  }
});

// Public: login for both Admin and Matchmaker accounts.
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    const [rows] = await pool.query('SELECT * FROM users WHERE username = ?', [username]);
    if (!rows.length) return res.status(401).json({ error: 'Invalid username or password.' });

    const user = rows[0];
    const match = await bcrypt.compare(password, user.password_hash);
    if (!match) return res.status(401).json({ error: 'Invalid username or password.' });

    const token = jwt.sign(
      { id: user.id, role: user.role, full_name: user.full_name },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );
    res.json({ token, user: { id: user.id, full_name: user.full_name, role: user.role } });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Login failed.' });
  }
});

module.exports = router;
