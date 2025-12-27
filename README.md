---

# Material Solutions AI - Intelligent Lead Management System

**A "Speed-to-Lead" AI CRM that captures, qualifies, and quotes customer inquiries instantly.**

This application is a full-stack AI solution built with **Streamlit** and **Groq (Llama 3)**. It solves the problem of lost leads in the material/home decor industry by providing instant, AI-generated price estimates and a unified communication portal between customers and sales teams.

---

## 🌟 Key Features

### 👤 Customer Portal

- **Instant AI Quotation:** Users get a real-time price estimate based on their requirements (e.g., "1000 sqft laminate").
- **Smart Parsing:** The AI extracts quantities and calculates costs for multiple items (For e.g. - Flooring + Lighting + Installation).
- **Two-Way Chat:** Customers can negotiate or ask follow-up questions directly within the inquiry thread.
- **Actionable Status:** Users can **Accept** or **Decline** deals with a single click.

### 🔐 Admin Dashboard (CRM)

- **Centralized Command Center:** View all leads categorized by status (New, Contacted, Won, Lost).
- **AI Insights:** View "Hot/Cold" intent classification and AI reasoning for every lead.
- **Quote Editor:** Admins can override the AI price and send a negotiated offer.
- **Integrated Messaging:** Reply to customers directly from the dashboard without switching to email.

---

## 🛠️ Tech Stack

- **Frontend & Backend:** [Streamlit](https://streamlit.io/) (Python)
- **AI Engine:** [Groq API](https://groq.com/) running **Llama-3.1-8b-Instant**
- **Data Persistence:** JSON-based local storage (No SQL DB required for demo)
- **Data Handling:** Pandas

---

## 🚀 Installation & Local Setup

Follow these steps to run the app on your machine.

### 1. Clone the Repository

```bash
git clone https://github.com/AakritiMeh/aakriti_mehrotra_ai_lead_management_system.git
cd ai-lead-manager

```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

```

### 3. Configure API Keys (Securely)

Create a secrets file to store your API key.

1. Create a folder named `.streamlit` in the root directory.
2. Inside it, create a file named `secrets.toml`.
3. Add your Groq API key:

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "gsk_YOUR_ACTUAL_API_KEY_HERE"

```

_(Get a free key at [console.groq.com](https://console.groq.com/keys))_

### 4. Run the App

```bash
streamlit run app.py

```

---

## 📖 Usage Guide

### 🧑‍💻 For Customers

1. Click **"Create Account"** to register (Simulated).
2. Login and go to **"New Inquiry"**.
3. Type a requirement like: _"I need 1200 sqft of ceramic tiles and 5 hanging lights."_
4. View the AI-generated quote in the **"My Quotes"** tab.
5. Use the chat box to ask the admin for a discount.

### 👮‍♂️ For Admins

1. Go to **"Admin Access"** from the Home page.
2. **Default Password:** `admin123`
3. Navigate to the Dashboard to see incoming leads.
4. Expand a lead to see AI analysis.
5. Type a message and a **New Price** in the form to update the customer's quote.

---

## 📂 Project Structure

```text
ai-lead-manager/
├── app.py                # Main application code
├── requirements.txt      # Python dependencies
├── .gitignore            # Ignores secrets and DB files
├── leads_db.json         # Stores lead data (Generated automatically)
├── users_db.json         # Stores user credentials (Generated automatically)
└── .streamlit/
    └── secrets.toml      # Local API keys (DO NOT UPLOAD TO GITHUB)

```
