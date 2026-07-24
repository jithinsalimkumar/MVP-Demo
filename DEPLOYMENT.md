# Production Deployment & MongoDB Atlas Setup Guide

This guide details the step-by-step instructions for configuring MongoDB Atlas and deploying the LeadPulse platform without connection errors.

---

## 1. MongoDB Atlas Setup

### Step 1: Create a Free Cluster
1. Log in to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a free **M0 Shared Cluster** (choose AWS or GCP region nearest to your deployment host).

### Step 2: Create a Database User
1. Go to **Security → Database Access**.
2. Click **+ Add New Database User**.
3. Choose **Password** authentication.
4. Set Username (e.g. `leadpulse_admin`) and a strong Password.
   - *Note*: Avoid unencoded special characters like `@`, `#`, `:`, `/` in passwords, or use URL encoding.
5. Set User Privileges to **Read and write to any database** (`readWriteAnyDatabase`).
6. Click **Add User**.

### Step 3: Network Access (IP Whitelist)
1. Go to **Security → Network Access**.
2. Click **+ Add IP Address**.
3. Select **Allow Access from Anywhere** (`0.0.0.0/0`).
   - *Why*: Hosting providers (Render, Railway, Heroku) rotate IP addresses dynamically. `0.0.0.0/0` enables seamless connections.
4. Click **Confirm**.

### Step 4: Retrieve Connection String
1. Go to **Database → Clusters**.
2. Click **Connect** → **Drivers** → **Python**.
3. Copy the string format:
   ```text
   mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
   ```
4. Replace `<username>` and `<password>` with your database user credentials.

---

## 2. Production Environment Variables

### Backend Environment Variables (Render / Railway / AWS)

Configure these key-value pairs in your hosting control panel:

```env
MONGODB_URI=mongodb+srv://leadpulse_admin:YourPass123@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
DB_NAME=lead_outreach_db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourSecurePassword123
PORT=8050
```

### Frontend Environment Variables (Vercel / Netlify)

```env
NEXT_PUBLIC_API_URL=https://your-deployed-backend-url.com/api
```

---

## 3. Local Verification

To test your production MongoDB Atlas cluster locally before deploying:

1. Edit `backend/.env`:
   ```env
   MONGODB_URI=mongodb+srv://leadpulse_admin:YourPass123@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
   DB_NAME=lead_outreach_db
   ```
2. Run backend:
   ```bash
   python main.py
   ```
3. Look for the startup log:
   `[DB OK] Connected successfully to MongoDB Atlas / Custom URI (lead_outreach_db)`
