"""
Aegis-Twin · AI-Driven Digital Twin Dashboard
==============================================
Enterprise Fleet Manager Edition.

Run with: streamlit run app.py
"""

import os

import pandas as pd
import plotly.graph_objects as go
import time
import datetime
import random
import torch
import threading

from scapy.all import sniff
from engine import calculate_trust_score, calculate_jsd
from model import LSTMAutoencoder
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
import streamlit as st
from dotenv import load_dotenv
import folium
from streamlit_folium import st_folium

from auth import create_user, has_users, init_db
from auth_page import render_login_page
from dashboard import render_device_dashboard
from model import LSTMAutoencoder
from registry import IOT_REGISTRY, SESSION_DEFAULTS
from ui import NEON_GREEN, NEON_RED, inject_css

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Aegis-Twin SOC Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- THEME & CSS (SOC Style Glassmorphism) ---
NEON_CYAN = "#00fff2"
NEON_PINK = "#ff007f"
NEON_BLUE = "#00cfff"
# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_dotenv()
init_db()

if not has_users():
    admin_email    = os.environ.get("AEGIS_ADMIN_EMAIL")
    admin_password = os.environ.get("AEGIS_ADMIN_PASSWORD")
    if admin_email and admin_password:
        try:
            create_user(admin_email, admin_password)
        except Exception:
            pass

    st.markdown(f"""
    <style>
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        background: radial-gradient(circle at center, #0B1120 0%, #000000 100%);
        background-color: #0b1120;
        background-image: 
            linear-gradient(rgba(0, 255, 242, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 242, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        color: #e0e6ed;
    }}

    .glass-card {{
        background: rgba(17, 25, 40, 0.75);
        backdrop-filter: blur(12px);         
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); 
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }}

    .fleet-card {{
        background: rgba(17, 25, 40, 0.7);
        backdrop-filter: blur(12px);         
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        text-align: center;
        transition: all 0.3s ease;
    }}
    .fleet-card:hover {{
        border: 1px solid {NEON_CYAN};
        box-shadow: 0 0 15px rgba(0, 255, 242, 0.3);
        transform: translateY(-5px);
    }}

    .section-header {{
        font-family: 'Source Code Pro', monospace;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 20px;
        color: {NEON_CYAN};
        text-transform: uppercase;
        letter-spacing: 2px;
        border-left: 4px solid {NEON_CYAN};
        padding-left: 10px;
    }}

    [data-testid="stSidebar"] {{
        background-color: rgba(11, 17, 32, 0.9);
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}

    h1, h2, h3 {{
        color: white !important;
        font-family: 'Source Code Pro', monospace !important;
    }}

    .marquee-container {{
        background: rgba(0, 0, 0, 0.5);
        border-top: 1px solid {NEON_CYAN};
        border-bottom: 1px solid {NEON_CYAN};
        padding: 5px 0;
        margin-bottom: 20px;
    }}

    @keyframes blinker {{
        50% {{ opacity: 0; }}
    }}
    .status-online {{ color: {NEON_CYAN}; font-weight: bold; }}
    .status-critical {{ color: {NEON_PINK}; font-weight: bold; animation: blinker 1s linear infinite; }}
</style>
""", unsafe_allow_html=True)

# --- CONFIG & REGISTRY ---
PHONE_MAC = "B8:A8:25:B1:EA:6C"
PHONE_BASELINE = [0.35, 0.45, 0.30, 0.70] # Normalized baseline features

IOT_REGISTRY = {
    f"DEV-{i:03d}": {
        "name": f"Sensor Node {i}",
        "type": random.choice(["PLC", "Actuator", "Gateway", "Camera"]),
        "sector": random.choice(["Alpha", "Beta", "Gamma"]),
        "baseline": [random.uniform(0.2, 0.5) for _ in range(4)],
        "icon": random.choice(["⚡", "🚰", "🦾", "❄️", "🔬"])
    } for i in range(1, 11)
}

# --- SESSION STATE INITIALIZATION ---
if 'page' not in st.session_state:
    st.session_state.page = "fleet"
if 'active_device' not in st.session_state:
    st.session_state.active_device = None
if 'device_health' not in st.session_state:
    st.session_state.device_health = {k: "Healthy" for k in IOT_REGISTRY.keys()}
    st.session_state.device_health["PHONE"] = "Healthy"
if 'packet_history' not in st.session_state:
    st.session_state.packet_history = []
if 'threat_log' not in st.session_state:
    st.session_state.threat_log = []
if 'phone_activity_sparkline' not in st.session_state:
    st.session_state.phone_activity_sparkline = [0.1] * 30
if 'live_metrics' not in st.session_state:
    st.session_state.live_metrics = {"jsd": 0.02, "mse": 0.01, "trust": 100.0}
if 'pulse_mse_history' not in st.session_state:
    st.session_state.pulse_mse_history = [0.01] * 50
if 'pulse_jsd_history' not in st.session_state:
    st.session_state.pulse_jsd_history = [0.02] * 50
if 'sensitivity' not in st.session_state:
    st.session_state.sensitivity = 0.15
if 'simulate_attack' not in st.session_state:
    st.session_state.simulate_attack = False

# --- MODEL LOADING ---
inject_css()

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
for k, v in SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------
if not st.session_state.authenticated:
    render_login_page()

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
@st.cache_resource
def load_aegis_model():
    model = LSTMAutoencoder()
    model.eval()
    return model

model_engine = load_aegis_model()

# ---------------------------------------------------------------------------
# PAGE 1 — Fleet overview
# ---------------------------------------------------------------------------
def render_fleet_page():
    st.markdown("<h1 style='text-align:center;color:white;'>🌐 Enterprise Fleet Manager</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#aaa;'>Click a hotspot on the map to open its Digital Twin dashboard. <span style='color:#00ff88'>● Green = Healthy</span> | <span style='color:#ff2d55'>● Red = Compromised</span></p>", unsafe_allow_html=True)
    st.divider()

    # Map initialization centered on JSS Academy, RR Nagar
    center_lat, center_lon = 12.9026, 77.5001
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles="cartodb dark_matter", zoom_control=True)

    for dev_id, info in IOT_REGISTRY.items():
        health = st.session_state.device_health.get(dev_id, "Healthy")
        color = NEON_GREEN if health == "Healthy" else NEON_RED
        is_compromised = health != "Healthy"
        
        # CSS for pulsing effect
        pulse_class = "map-pulsing-marker" if is_compromised else "map-static-marker"
        
        tooltip_html = f"""
        <div style="font-family:'Inter',sans-serif; background:rgba(17,25,40,0.95); color:white; padding:12px; border:1px solid {color}; border-radius:8px; box-shadow:0 0 10px {color}66; min-width:180px;">
            <div style="font-size:1.5rem; margin-bottom:5px;">{info['icon']}</div>
            <strong style="font-size:1.1rem; display:block; margin-bottom:2px;">{info['name']}</strong>
            <code style="color:#00cfff; font-size:0.85em;">{dev_id}</code>
            <div style="margin-top:8px; font-size:0.9em; color:#aaa;">
                Type: {info['type']}<br>
                Sector: {info['sector']}<br>
                Status: <span style="color:{color}; font-weight:bold;">{health.upper()}</span>
            </div>
            <div style="margin-top:10px; font-size:0.8em; color:{color}; border-top:1px solid rgba(255,255,255,0.1); padding-top:5px;">
                ▶ Click to open dashboard
            </div>
        </div>
        """

        # Custom Icon with HTML/CSS for glowing/pulsing effect
        icon_html = f"""
        <div class="{pulse_class}" style="
            background-color: {color};
            width: 18px;
            height: 18px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 0 15px {color};
            cursor: pointer;
        "></div>
        """
        
        folium.Marker(
            location=[info['lat'], info['lon']],
            popup=folium.Popup(tooltip_html, max_width=300),
            tooltip=info['name'],
            icon=folium.DivIcon(
                icon_size=(20, 20),
                icon_anchor=(10, 10),
                html=icon_html,
            ),
            custom_id=dev_id # pass ID to identify click
        ).add_to(m)

    # Custom CSS for the map markers
    st.markdown("""
    <style>
    @keyframes map-pulse {
        0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 45, 85, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 15px rgba(255, 45, 85, 0); }
        100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 45, 85, 0); }
    }
    .map-pulsing-marker {
        animation: map-pulse 1.5s infinite;
    }
    .map-static-marker:hover {
        transform: scale(1.2);
        transition: transform 0.2s ease;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display map
    output = st_folium(m, width="100%", height=500, key="fleet_map")

    # Handle click navigation
    if output and output.get("last_object_clicked"):
        # We need to find which device was clicked based on coordinates if custom_id doesn't propagate easily
        click_lat = output["last_object_clicked"]["lat"]
        click_lon = output["last_object_clicked"]["lng"]
        
        clicked_dev_id = None
        for dev_id, info in IOT_REGISTRY.items():
            if abs(info['lat'] - click_lat) < 0.0001 and abs(info['lon'] - click_lon) < 0.0001:
                clicked_dev_id = dev_id
                break
        
        if clicked_dev_id:
            st.session_state.active_device  = clicked_dev_id
            st.session_state.page           = "dashboard"
            st.session_state.packet_history = pd.DataFrame(columns=["Time","Pkt Size","IAT","Entropy","Symmetry","Status"])
            st.session_state.threat_log     = []
            st.rerun()

    st.divider()

    if st.session_state.remediation_log:
        st.markdown("### 🛠️ Remediation History")
        st.dataframe(pd.DataFrame(st.session_state.remediation_log), width="stretch", hide_index=True)

    if st.session_state.audit_logs:
        st.markdown("### 🧾 Audit Trail")
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
if st.session_state.page == "fleet":
    render_fleet_page()
elif st.session_state.page == "dashboard":
    render_device_dashboard(autoencoder)
