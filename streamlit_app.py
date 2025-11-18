# streamlit_app.py (FINAL STABLE VERSION)

import os
os.environ["STREAMLIT_SERVER_RUN_ON_SAVE"] = "false"   # Fix auto-reload crash

import streamlit as st
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import time

from AI_Agent_Model import predict_stock


# ---------------- DATABASE ----------------
DB_PATH = Path.cwd() / "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, email, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    r = c.fetchone()
    conn.close()
    return r


def reset_password(username, new_pass):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE username=?", (new_pass, username))
    conn.commit()
    conn.close()


# ---------------- SIGNAL ----------------
def get_trading_signal(latest, nextp):
    pct = ((nextp - latest) / (latest + 1e-9)) * 100

    if pct > 0.6:
        return "STRONG BUY", f"+{pct:.2f}%", "📈"
    if pct > 0.1:
        return "BUY", f"+{pct:.2f}%", "📗"
    if pct < -0.6:
        return "STRONG SELL", f"{pct:.2f}%", "📉"
    if pct < -0.1:
        return "SELL", f"{pct:.2f}%", "📕"
    return "HOLD", f"{pct:.2f}%", "⚪"


# ---------------- CSS (Your Same Design) ----------------
st.set_page_config(page_title="AIvest - AI Stock Predictor", layout="wide")

CSS = """
<style>
@keyframes fadeIn {from {opacity:0; transform:translateY(10px);} to {opacity:1;} }

.stApp {
    background: linear-gradient(180deg,#f0f4f9 0%,#ffffff 100%);
    font-family: 'Inter', sans-serif;
}
.stButton>button {
    border-radius:12px; padding:10px 20px;
    font-weight:700; font-size:16px; color:white;
    background:linear-gradient(90deg,#3b82f6,#1d4ed8);
    border:none; box-shadow:0 4px 10px rgba(66,133,244,0.3);
}
.prediction-card {
    border-radius:15px; padding:20px;
    box-shadow:0 8px 20px rgba(0,0,0,0.1);
}
.buy-signal {background:#d1fae5; border-left:5px solid #10b981;}
.sell-signal {background:#fee2e2; border-left:5px solid #ef4444;}
.hold-signal {background:#fef3c7; border-left:5px solid #f59e0b;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------- SESSION ----------------
init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "username" not in st.session_state:
    st.session_state.username = ""


# ---------------- LOGIN PAGE ----------------
def login_page():
    st.title("🔐 AIvest - Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Login"):
            if login_user(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("Invalid credentials")

    with c2:
        if st.button("Forgot Password?"):
            st.session_state.page = "forgot"
            st.rerun()
    with c3:
        if st.button("Create Account"):
            st.session_state.page = "signup"
            st.rerun()


# ---------------- SIGNUP ----------------
def signup_page():
    st.title("📝 Create Account")
    u = st.text_input("Username")
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")

    if st.button("Signup"):
        if u and e and p:
            if add_user(u, e, p):
                st.success("Account created")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("Username already exists")


# ---------------- FORGOT ----------------
def forgot_page():
    st.title("🔑 Reset Password")
    u = st.text_input("Username")
    np = st.text_input("New Password", type="password")

    if st.button("Update Password"):
        reset_password(u, np)
        st.success("Password updated")
        st.session_state.page = "login"
        st.rerun()


# ---------------- BLOCK UNAUTH USERS ----------------
if not st.session_state.logged_in:
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    else:
        forgot_page()
    st.stop()


# ---------------- MAIN APP ----------------
st.sidebar.markdown(f"**User: {st.session_state.username}**")
nav = st.sidebar.radio("Menu", ["Home (Predictor)", "Profile", "Logout"])

if nav == "Logout":
    st.session_state.logged_in = False
    st.session_state.page = "login"
    st.rerun()

if nav == "Profile":
    st.title("👤 Profile")
    st.write(f"Username: **{st.session_state.username}**")
    st.stop()


# ---------------- PREDICTOR ----------------
st.title("💹 AIvest — Financial Agent")
st.write("Predict next-day stock prices using AI.")

symbol = st.text_input("Stock Symbol", placeholder="INFY.NS, TCS.NS")

if st.button("Run Prediction"):
    if not symbol.strip():
        st.warning("Enter a stock symbol")
    else:
        with st.spinner("Processing…"):
            res = predict_stock(symbol.upper())

        if not res:
            st.error("Unable to fetch stock data")
        else:
            score, latest, nxt, (actual, preds, dates) = res

            signal, reason, icon = get_trading_signal(latest, nxt)
            sig_class = signal.lower().replace(" ", "-")

            st.subheader("Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Latest Price", f"₹{latest:.2f}")
            c2.metric("Predicted Price", f"₹{nxt:.2f}", delta=f"{nxt-latest:.2f}")
            c3.metric("Accuracy", f"{score*100:.2f}%")

            st.markdown(
                f"""
                <div class='prediction-card {sig_class}-signal'>
                    <h3>{icon} {signal}</h3>
                    <p>{reason}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.subheader("Actual vs Predicted")

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(dates, actual, label="Actual", color='#0077b6')
            ax.plot(dates, preds, label="Predicted", color='#ff006e', linestyle="--")
            ax.grid(True)
            plt.xticks(rotation=45)
            ax.legend()
            st.pyplot(fig)
