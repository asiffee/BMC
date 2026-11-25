# Bandhan Marriage Consultant

A full-stack matchmaking website built with **React (Vite)**, **Node.js/Express**, and **MySQL**.

## Roles & Access

| Role | Can do |
|---|---|
| **Admin** | Full rights: publish/delete Home page posts, view/edit/delete every profile (including phone & address) |
| **Matchmaker** | Registers themselves, adds bride/groom profiles. Sees full details of their **own** entries, but for entries added by **other** matchmakers, phone number and address are hidden |
| **General Visitor** | Sees only the Home page (Admin's posts) and the Contact page — no login, no profile data |

## Pages
- **Home** — public, shows posts published by the Admin
- **Matchmaker Panel** (`/matchmaker`, login required) — form to add a profile (name, father's name, phone, address, caste, education, age, siblings, parents alive, household members, photo) + list of all profiles with restricted fields
- **Admin Panel** (`/admin`, login required) — publish/delete posts, full access to every profile
- **Contact** — Asif Javed, 5 Chowk, Chakwal (phone number placeholder — add it in `frontend/src/pages/Contact.jsx`)

## Setup

### 1. Database
```bash
mysql -u root -p < backend/schema.sql
```

### 2. Backend
```bash
cd backend
cp .env.example .env      # then edit .env with your MySQL password + a JWT secret
npm install
node scripts/generate-admin.js admin YourStrongPassword "Asif Javed"   # creates your Admin login
npm run dev                # starts on http://localhost:5000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev                # starts on http://localhost:3000
```

Open **http://localhost:3000** in your browser.
- Log in as Admin with the username/password you created in step 2.
- Or go to "Matchmaker Login → Register here" to create a matchmaker account.

## Notes
- Uploaded photos are stored in `backend/uploads/` and served at `/uploads/...`.
- All access rules (who can see phone/address) are enforced **on the backend**, not just hidden in the UI, so the data can't be exposed by inspecting network requests.
- To change the Contact page phone number later, edit `frontend/src/pages/Contact.jsx`.
