const express = require('express');
const pool = require('../config/db');
const { requireAuth, requireRole } = require('../middleware/auth');
const upload = require('../middleware/upload');

const router = express.Router();

// Every route here requires login as Admin or Matchmaker.
// General site visitors never reach these routes (no public GET is exposed).
router.use(requireAuth, requireRole('admin', 'matchmaker'));

// Hides phone & address unless the viewer is the Admin or the profile's own creator.
function filterProfile(profile, viewer) {
  const isOwner = viewer.role === 'matchmaker' && profile.matchmaker_id === viewer.id;
  const isAdmin = viewer.role === 'admin';
  if (isAdmin || isOwner) return profile;

  const { phone, address, ...safe } = profile;
  return { ...safe, phone: null, address: null, restricted: true };
}

// List all profiles, filtered per viewer's role/ownership.
router.get('/', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM profiles ORDER BY created_at DESC');
    res.json(rows.map((p) => filterProfile(p, req.user)));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Could not load profiles.' });
  }
});

// Single profile, filtered per viewer's role/ownership.
router.get('/:id', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM profiles WHERE id = ?', [req.params.id]);
    if (!rows.length) return res.status(404).json({ error: 'Profile not found.' });
    res.json(filterProfile(rows[0], req.user));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Could not load profile.' });
  }
});

// Create a profile. Matchmakers create under their own account; Admin may also add one.
router.post('/', upload.single('photo'), async (req, res) => {
  try {
    const {
      gender, full_name, father_name, phone, address, caste, education, age,
      sisters_count, brothers_count, father_alive, mother_alive, household_members,
    } = req.body;

    if (!gender || !full_name) {
      return res.status(400).json({ error: 'gender and full_name are required.' });
    }
    const photo_url = req.file ? `/uploads/${req.file.filename}` : null;

    const [result] = await pool.query(
      `INSERT INTO profiles
        (matchmaker_id, gender, full_name, father_name, phone, address, caste, education, age,
         sisters_count, brothers_count, father_alive, mother_alive, household_members, photo_url)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [req.user.id, gender, full_name, father_name || null, phone || null, address || null,
        caste || null, education || null, age || null, sisters_count || 0, brothers_count || 0,
        father_alive || 'yes', mother_alive || 'yes', household_members || null, photo_url]
    );
    res.status(201).json({ id: result.insertId });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Could not save profile.' });
  }
});

// Edit a profile — only its own matchmaker, or the Admin.
router.put('/:id', upload.single('photo'), async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM profiles WHERE id = ?', [req.params.id]);
    if (!rows.length) return res.status(404).json({ error: 'Profile not found.' });
    const profile = rows[0];

    const isOwner = req.user.role === 'matchmaker' && profile.matchmaker_id === req.user.id;
    if (req.user.role !== 'admin' && !isOwner) {
      return res.status(403).json({ error: 'You can only edit your own entries.' });
    }

    const fields = [
      'gender', 'full_name', 'father_name', 'phone', 'address', 'caste', 'education', 'age',
      'sisters_count', 'brothers_count', 'father_alive', 'mother_alive', 'household_members',
    ];
    const updates = {};
    fields.forEach((f) => { if (req.body[f] !== undefined) updates[f] = req.body[f]; });
    if (req.file) updates.photo_url = `/uploads/${req.file.filename}`;

    if (Object.keys(updates).length === 0) return res.json({ success: true, unchanged: true });

    const setClause = Object.keys(updates).map((k) => `${k} = ?`).join(', ');
    await pool.query(`UPDATE profiles SET ${setClause} WHERE id = ?`, [...Object.values(updates), req.params.id]);
    res.json({ success: true });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Could not update profile.' });
  }
});

// Delete a profile — only its own matchmaker, or the Admin.
router.delete('/:id', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT matchmaker_id FROM profiles WHERE id = ?', [req.params.id]);
    if (!rows.length) return res.status(404).json({ error: 'Profile not found.' });

    const isOwner = req.user.role === 'matchmaker' && rows[0].matchmaker_id === req.user.id;
    if (req.user.role !== 'admin' && !isOwner) {
      return res.status(403).json({ error: 'You can only delete your own entries.' });
    }

    await pool.query('DELETE FROM profiles WHERE id = ?', [req.params.id]);
    res.json({ success: true });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Could not delete profile.' });
  }
});

module.exports = router;
