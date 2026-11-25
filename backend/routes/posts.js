const express = require('express');
const pool = require('../config/db');
const { requireAuth, requireRole } = require('../middleware/auth');
const upload = require('../middleware/upload');

const router = express.Router();

// Public: anyone visiting the Home page sees posts uploaded by the Admin.
router.get('/', async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT id, title, content, image_url, created_at FROM posts ORDER BY created_at DESC'
    );
    res.json(rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Could not load posts.' });
  }
});

// Admin only: create a post for the Home page.
router.post('/', requireAuth, requireRole('admin'), upload.single('image'), async (req, res) => {
  try {
    const { title, content } = req.body;
    if (!title) return res.status(400).json({ error: 'Title is required.' });
    const image_url = req.file ? `/uploads/${req.file.filename}` : null;

    const [result] = await pool.query(
      'INSERT INTO posts (title, content, image_url, created_by) VALUES (?, ?, ?, ?)',
      [title, content || null, image_url, req.user.id]
    );
    res.status(201).json({ id: result.insertId, title, content, image_url });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Could not create post.' });
  }
});

// Admin only: delete a post.
router.delete('/:id', requireAuth, requireRole('admin'), async (req, res) => {
  try {
    await pool.query('DELETE FROM posts WHERE id = ?', [req.params.id]);
    res.json({ success: true });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Could not delete post.' });
  }
});

module.exports = router;
