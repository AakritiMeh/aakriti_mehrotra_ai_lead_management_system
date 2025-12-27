
import streamlit as st
import json
import requests
import os
from datetime import datetime
import pandas as pd


try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except FileNotFoundError:
 
    st.error("API Key missing! Please set it in secrets.toml or Streamlit Cloud Secrets.")
    st.stop()
ADMIN_PASSWORD = "admin123"

LEADS_DB_FILE = "leads_db.json"
USERS_DB_FILE = "users_db.json"



def load_json(filename):
    if not os.path.exists(filename): return []
    try:
        with open(filename, "r") as f: return json.load(f)
    except: return []

def save_json(filename, data):
    with open(filename, "w") as f: json.dump(data, f, indent=4)


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



def classify_lead_with_ai(name, message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    if not GROQ_API_KEY or "YOUR_API_KEY" in GROQ_API_KEY:
        return fallback_logic(message)

    prompt = f"""
    You are an AI Sales Engineer for a Material/Decor brand in India.
    
    PRICE LIST (Estimates in INR):
    1. Laminate Flooring: ₹80 - ₹150 / sqft
    2. Hardwood Flooring: ₹350 - ₹600 / sqft
    3. Tiles/Ceramics: ₹60 - ₹120 / sqft
    4. Lighting: ₹2000 - ₹5000 / unit
    5. Installation: Add approx 20% to material cost.

    Task: Analyze this lead.
    Name: {name}
    Message: {message}

    INSTRUCTIONS:
    1. Identify ALL requirements.
    2. Calculate cost for EACH item.
    3. SUM them up for Total Estimated Quote.
    4. Draft a PROFESSIONAL EMAIL response.

    Return JSON (No Markdown):
    {{
        "intent": "HOT" (urgent), "WARM", or "COLD",
        "category": "General", 
        "score": number 0-100,
        "reasoning": "Breakdown",
        "estimated_quote": "e.g., ₹1.2 Lakhs",
        "email_subject": "Quotation for your [Category] Requirement",
        "email_body": "Dear {name}, based on your requirements, here is the estimate..."
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
        "reasoning": "AI Unavailable", "estimated_quote": "Contact us",
        "email_subject": "Inquiry Received", "email_body": "We will contact you shortly."
    })

st.set_page_config(page_title="Material AI Portal", page_icon="🏗️", layout="wide")

if 'page' not in st.session_state: st.session_state.page = 'home'
if 'user' not in st.session_state: st.session_state.user = None

def nav_to(page): st.session_state.page = page
def logout(): st.session_state.user = None; st.session_state.page = 'home'

if st.session_state.page == 'home':
    st.title("🏗️ Material Solutions AI")
    st.markdown("#### Intelligent Quotes & Lead Management")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("👤 Customer Login", use_container_width=True): nav_to('login')
    with c2:
        if st.button("🆕 Create Account", use_container_width=True): nav_to('register')
    with c3:
        if st.button("🔐 Admin Access", use_container_width=True): nav_to('admin_login')


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

elif st.session_state.page == 'user_dashboard':
    if not st.session_state.user: nav_to('home'); st.rerun()
    
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.user['name']}**")
        st.button("Logout", on_click=logout)
    
    st.title("👤 Customer Portal")
    tab1, tab2 = st.tabs(["📝 New Inquiry", "💬 My Quotes & Chat"])

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

   
    with tab2:
        all_leads = load_json(LEADS_DB_FILE)
        my_leads = [l for l in all_leads if l['email'] == st.session_state.user['email']]
        
        if not my_leads: st.info("No active inquiries.")
        
        for lead in reversed(my_leads):
           
            s_color = "red" if lead['status']=="LOST" else "green" if lead['status']=="WON" else "blue"
            
            with st.expander(f"{lead['timestamp']} | Quote: {lead.get('estimated_quote')} | Status: {lead['status']}"):
                
                st.markdown(f"### 🏷️ Quote: :{s_color}[{lead['estimated_quote']}]")
                st.caption(f"Reasoning: {lead.get('reasoning')}")
                
                if lead['status'] in ["NEW", "CONTACTED"]:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Accept", key=f"acc_{lead['id']}", use_container_width=True):
                            idx = next(i for i, l in enumerate(all_leads) if l['id'] == lead['id'])
                            all_leads[idx]['status'] = "WON"
                            save_json(LEADS_DB_FILE, all_leads)
                            st.rerun()
                    with c2:
                        if st.button("❌ Decline", key=f"dec_{lead['id']}", use_container_width=True):
                            idx = next(i for i, l in enumerate(all_leads) if l['id'] == lead['id'])
                            all_leads[idx]['status'] = "LOST"
                            save_json(LEADS_DB_FILE, all_leads)
                            st.rerun()
                elif lead['status'] == "WON": st.success("🎉 Deal Accepted!")
                elif lead['status'] == "LOST": st.error("❌ Deal Declined.")

                st.divider()
                
            
                st.subheader("💬 Message Admin")
                
                chat_container = st.container(height=300)
                with chat_container:
                    for msg in lead.get('chat_history', []):
                    
                        if msg['role'] == 'assistant':
                            with st.chat_message("assistant", avatar="👨‍💼"):
                                st.write(f"**Admin ({msg['time']}):** {msg['content']}")
                        else:
                            with st.chat_message("user", avatar="👤"):
                                st.write(f"**You ({msg['time']}):** {msg['content']}")

           
                with st.form(key=f"user_chat_{lead['id']}", clear_on_submit=True):
                    user_msg = st.text_input("Type your message (e.g., 'Is the price negotiable?')")
                    if st.form_submit_button("Send Message"):
                        if user_msg:
                            idx = next(i for i, l in enumerate(all_leads) if l['id'] == lead['id'])
                            
                            new_chat = {
                                "role": "user", 
                                "time": datetime.now().strftime("%H:%M"), 
                                "content": user_msg
                            }
                            
                            if 'chat_history' not in all_leads[idx]: all_leads[idx]['chat_history'] = []
                            all_leads[idx]['chat_history'].append(new_chat)
                            
                            save_json(LEADS_DB_FILE, all_leads)
                            st.rerun()

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
            with st.expander(f"{lead['name']} | {lead['estimated_quote']} | {lead['status']}"):
                col_info, col_chat = st.columns([1, 1.5])
                
                with col_info:
                    st.write(f"**Req:** {lead['message']}")
                    st.info(f"AI Logic: {lead.get('reasoning')}")
                    st.write(f"**Phone:** {lead.get('phone')}")
                
                with col_chat:
                    st.subheader("💬 Conversation")
                    
                    chat_box = st.container(height=250)
                    with chat_box:
                        for msg in lead.get('chat_history', []):
                            if msg['role'] == 'assistant':
                                with st.chat_message("assistant", avatar="👨‍💼"):
                                    st.write(f"**Admin:** {msg['content']}")
                            else:
                                with st.chat_message("user", avatar="👤"):
                                    st.write(f"**User:** {msg['content']}")

                    st.write("**Reply & Update Price**")
                    with st.form(key=f"adm_reply_{lead['id']}", clear_on_submit=True):
                        new_quote = st.text_input("Quote Price:", value=lead.get('estimated_quote'))
                        admin_msg = st.text_area("Message:", height=80)
                        
                        if st.form_submit_button("Send & Update"):
                            idx = next(i for i, l in enumerate(leads) if l['id'] == lead['id'])
                            
                      
                            leads[idx]['estimated_quote'] = new_quote
                            leads[idx]['status'] = "CONTACTED"
                            
                            if admin_msg:
                                new_chat = {
                                    "role": "assistant",
                                    "time": datetime.now().strftime("%H:%M"),
                                    "content": admin_msg
                                }
                                if 'chat_history' not in leads[idx]: leads[idx]['chat_history'] = []
                                leads[idx]['chat_history'].append(new_chat)
                            
                            save_json(LEADS_DB_FILE, leads)
                            st.success("Sent!"); st.rerun()
    else:
        st.info("No leads.")