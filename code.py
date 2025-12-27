import streamlit as st
import json
import requests
import os
from datetime import datetime
import pandas as pd

# --- CONFIGURATION ---
# Access key from Secrets (Best Practice) or fall back to hardcoded for local test
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    GROQ_API_KEY = "gsk_YOUR_API_KEY_HERE" 

ADMIN_PASSWORD = "admin123"

LEADS_DB_FILE = "leads_db.json"
USERS_DB_FILE = "users_db.json"

# --- BACKEND: DATA MANAGEMENT ---

def load_json(filename):
    if not os.path.exists(filename): return []
    try:
        with open(filename, "r") as f: return json.load(f)
    except: return []

def save_json(filename, data):
    with open(filename, "w") as f: json.dump(data, f, indent=4)

# --- BACKEND: AUTHENTICATION ---

def register_user(name, email, password):
    users = load_json(USERS_DB_FILE)
    if any(u['email'] == email for u in users):
        return False, "Email already registered."
    
    new_user = {"name": name, "email": email, "password": password}
    users.append(new_user)
    save_json(USERS_DB_FILE, users)
    return True, "Registration successful! Please login."

def authenticate_user(email, password):
    users = load_json(USERS_DB_FILE)
    user = next((u for u in users if u['email'] == email and u['password'] == password), None)
    return user

# --- BACKEND: AI LOGIC ---

def classify_lead_with_ai(name, message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    # Check for valid key
    if not GROQ_API_KEY or "YOUR_API_KEY" in GROQ_API_KEY:
        return fallback_logic(message)

    prompt = f"""
    You are an AI Sales Engineer.
    
    PRICE LIST (Estimates in INR):
    1. Laminate Flooring: ₹80 - ₹150 / sqft
    2. Hardwood Flooring: ₹350 - ₹600 / sqft
    3. Tiles/Ceramics: ₹60 - ₹120 / sqft
    4. Lighting: ₹2000 - ₹5000 / unit
    5. Installation: Add 20% to material cost.

    Task: Analyze this lead: "{message}" from {name}.

    INSTRUCTIONS:
    1. Calculate cost for EACH item found.
    2. Return JSON ONLY.
    3. "reasoning" MUST be a short calculation summary (e.g. "1000sqft * 100 = 1L"). 
    4. "estimated_quote" MUST be the final formatted string (e.g. "₹1.2 Lakhs").

    Return JSON:
    {{
        "intent": "HOT" or "COLD",
        "category": "General", 
        "score": number 0-100,
        "reasoning": "Show the math here (max 10 words)",
        "estimated_quote": "₹X.X Lakhs",
        "email_subject": "Quote for requirements",
        "email_body": "Full breakdown email..."
    }}
    """
    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
        )
        if response.status_code != 200: return fallback_logic(message)
        content = response.json()['choices'][0]['message']['content']
        return content.replace("```json", "").replace("```", "").strip()
    except: return fallback_logic(message)

def fallback_logic(message):
    return json.dumps({
        "intent": "WARM", "category": "GENERAL", "score": 50,
        "reasoning": "Estimate pending site visit", "estimated_quote": "Pending",
        "email_subject": "Inquiry Received", "email_body": "We will contact you shortly."
    })

# --- FRONTEND SETUP ---
st.set_page_config(page_title="Material AI Portal", page_icon="🏗️", layout="wide")

if 'page' not in st.session_state: st.session_state.page = 'home'
if 'user' not in st.session_state: st.session_state.user = None

def nav_to(page): st.session_state.page = page
def logout(): st.session_state.user = None; st.session_state.page = 'home'

# ==========================================
# 1. HOME
# ==========================================
if st.session_state.page == 'home':
    st.title("🏗️ Material Solutions AI")
    st.write("Intelligent Quotes & Lead Management")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("👤 Customer Login", use_container_width=True): nav_to('login')
    with c2:
        if st.button("🆕 Create Account", use_container_width=True): nav_to('register')
    with c3:
        if st.button("🔐 Admin Access", use_container_width=True): nav_to('admin_login')

# ==========================================
# 2. AUTH
# ==========================================
elif st.session_state.page == 'login':
    st.button("← Back", on_click=lambda: nav_to('home'))
    st.title("Login")
    with st.form("login"):
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            user = authenticate_user(email, pwd)
            if user:
                st.session_state.user = user
                nav_to('user_dashboard')
                st.rerun()
            else:
                st.error("Invalid credentials")

elif st.session_state.page == 'register':
    st.button("← Back", on_click=lambda: nav_to('home'))
    st.title("Register")
    with st.form("reg"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Register"):
            success, msg = register_user(name, email, pwd)
            if success: st.success(msg)
            else: st.error(msg)

# ==========================================
# 3. USER DASHBOARD
# ==========================================
elif st.session_state.page == 'user_dashboard':
    if not st.session_state.user: nav_to('home'); st.rerun()
    
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.user['name']}**")
        st.button("Logout", on_click=logout)
    
    st.title("👤 Customer Portal")
    tab1, tab2 = st.tabs(["📝 New Inquiry", "💬 My Quotes & Chat"])

    # NEW INQUIRY
    with tab1:
        with st.form("new_lead"):
            message = st.text_area("Requirements", height=100)
            phone = st.text_input("Phone Number")
            if st.form_submit_button("Get Quote"):
                with st.spinner("AI Analysis..."):
                    ai_res = json.loads(classify_lead_with_ai(st.session_state.user['name'], message))
                    new_lead = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "name": st.session_state.user['name'],
                        "email": st.session_state.user['email'],
                        "phone": phone,
                        "message": message,
                        "status": "NEW",
                        "chat_history": [
                            {"role": "assistant", "time": datetime.now().strftime("%H:%M"), "content": ai_res.get('email_body')}
                        ],
                        **ai_res
                    }
                    leads = load_json(LEADS_DB_FILE)
                    leads.append(new_lead)
                    save_json(LEADS_DB_FILE, leads)
                    st.success("Inquiry Sent! Check 'My Quotes' tab."); st.rerun()

    # MY QUOTES & CHAT
    with tab2:
        all_leads = load_json(LEADS_DB_FILE)
        my_leads = [l for l in all_leads if l['email'] == st.session_state.user['email']]
        
        if not my_leads: st.info("No active inquiries.")
        
        for lead in reversed(my_leads):
            with st.expander(f"{lead['timestamp']} | {lead['category']}", expanded=True):
                
                # --- UPDATED UI: USE METRICS FOR BETTER VISIBILITY ---
                c_price, c_status, c_act = st.columns([1.5, 1, 1.5])
                
                with c_price:
                    st.metric("Estimated Quote", lead.get('estimated_quote'), help=lead.get('reasoning'))
                
                with c_status:
                    st.metric("Status", lead.get('status'))

                with c_act:
                    if lead['status'] in ["NEW", "CONTACTED"]:
                        c_a, c_b = st.columns(2)
                        if c_a.button("✅ Accept", key=f"acc_{lead['id']}"):
                            idx = next(i for i, l in enumerate(all_leads) if l['id'] == lead['id'])
                            all_leads[idx]['status'] = "WON"
                            save_json(LEADS_DB_FILE, all_leads)
                            st.rerun()
                        if c_b.button("❌ Decline", key=f"dec_{lead['id']}"):
                            idx = next(i for i, l in enumerate(all_leads) if l['id'] == lead['id'])
                            all_leads[idx]['status'] = "LOST"
                            save_json(LEADS_DB_FILE, all_leads)
                            st.rerun()
                    elif lead['status'] == "WON": st.success("🎉 Accepted")
                    elif lead['status'] == "LOST": st.error("❌ Declined")

                st.divider()
                st.subheader("💬 Message Admin")
                
                # Chat History
                chat_box = st.container(height=300)
                with chat_box:
                    for msg in lead.get('chat_history', []):
                        role = "assistant" if msg['role'] == 'assistant' else "user"
                        av = "👨‍💼" if role == "assistant" else "👤"
                        with st.chat_message(role, avatar=av):
                            st.write(msg['content'])

                # Chat Input
                with st.form(key=f"user_chat_{lead['id']}", clear_on_submit=True):
                    user_msg = st.text_input("Type your message...")
                    if st.form_submit_button("Send"):
                        if user_msg:
                            idx = next(i for i, l in enumerate(all_leads) if l['id'] == lead['id'])
                            new_chat = {"role": "user", "time": datetime.now().strftime("%H:%M"), "content": user_msg}
                            if 'chat_history' not in all_leads[idx]: all_leads[idx]['chat_history'] = []
                            all_leads[idx]['chat_history'].append(new_chat)
                            save_json(LEADS_DB_FILE, all_leads)
                            st.rerun()

# ==========================================
# 4. ADMIN DASHBOARD
# ==========================================
elif st.session_state.page == 'admin_login':
    st.button("← Home", on_click=lambda: nav_to('home'))
    st.title("🔐 Admin Login")
    if st.button("Login (Demo)"): st.session_state.page = 'admin_dashboard'; st.rerun()

elif st.session_state.page == 'admin_dashboard':
    with st.sidebar:
        st.button("Logout", on_click=lambda: nav_to('home'))
        if st.button("🗑️ Reset All Data"):
            if os.path.exists(LEADS_DB_FILE): os.remove(LEADS_DB_FILE)
            if os.path.exists(USERS_DB_FILE): os.remove(USERS_DB_FILE)
            st.rerun()

    st.title("📊 Admin Console")
    leads = load_json(LEADS_DB_FILE)
    
    if leads:
        df = pd.DataFrame(leads)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total", len(df))
        c2.metric("Pending", len(df[df['status'] == "NEW"]) if 'status' in df else 0)
        c3.metric("Won", len(df[df['status'] == "WON"]) if 'status' in df else 0)
        
        status_filter = st.radio("View:", ["ALL", "NEW", "CONTACTED", "WON", "LOST"], horizontal=True)
        filtered_leads = leads if status_filter == "ALL" else [l for l in leads if l.get('status') == status_filter]

        for lead in reversed(filtered_leads):
            with st.expander(f"{lead['name']} | {lead.get('estimated_quote')} | {lead['status']}"):
                col_info, col_chat = st.columns([1, 1.5])
                
                with col_info:
                    st.info(f"Req: {lead['message']}")
                    st.caption(f"AI: {lead.get('reasoning')}")
                    
                with col_chat:
                    st.subheader("💬 Chat & Update")
                    
                    # Chat History
                    chat_box = st.container(height=250)
                    with chat_box:
                        for msg in lead.get('chat_history', []):
                            role = "assistant" if msg['role'] == 'assistant' else "user"
                            av = "👨‍💼" if role == "assistant" else "👤"
                            with st.chat_message(role, avatar=av):
                                st.write(msg['content'])

                    # Reply & Update
                    with st.form(key=f"adm_reply_{lead['id']}", clear_on_submit=True):
                        # UPDATED UI: Explicit Override Field
                        col_q, col_msg = st.columns([1, 2])
                        new_quote = col_q.text_input("Override Price:", value=lead.get('estimated_quote'))
                        admin_msg = col_msg.text_input("Message:")
                        
                        if st.form_submit_button("Send & Update"):
                            idx = next(i for i, l in enumerate(leads) if l['id'] == lead['id'])
                            leads[idx]['estimated_quote'] = new_quote
                            leads[idx]['status'] = "CONTACTED"
                            
                            if admin_msg:
                                new_chat = {"role": "assistant", "time": datetime.now().strftime("%H:%M"), "content": admin_msg}
                                if 'chat_history' not in leads[idx]: leads[idx]['chat_history'] = []
                                leads[idx]['chat_history'].append(new_chat)
                            
                            save_json(LEADS_DB_FILE, leads)
                            st.success("Updated!"); st.rerun()
    else:
        st.info("No leads.")