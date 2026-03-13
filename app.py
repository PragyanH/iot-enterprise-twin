"""
Aegis-Twin · AI-Driven Digital Twin Dashboard
==============================================
Enterprise Fleet Manager Edition.
Includes a multi-device IoT Registry, Fleet Overview, and deep-dive
anomaly dashboard powered by PyTorch and the LSTM Autoencoder engines.

Run with: streamlit run app.py
"""

import streamlit as st
import numpy as np
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

# --- PAGE CONFIG ---
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

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;600;700&display=swap');

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
@st.cache_resource
def load_aegis_model():
    model = LSTMAutoencoder()
    model.eval()
    return model

model_engine = load_aegis_model()

# --- SCAPY BACKGROUND SNIFFER ---
def start_sniffer():
    last_pkt_time = time.time()
    
    def handle_packet(pkt):
        nonlocal last_pkt_time
        try:
            # Check MAC
            if hasattr(pkt, 'src') and (pkt.src.lower() == PHONE_MAC.lower() or pkt.dst.lower() == PHONE_MAC.lower()):
                size = len(pkt)
                now = time.time()
                iat = now - last_pkt_time
                last_pkt_time = now
                
                # Normalization
                norm_size = min(size / 1500.0, 1.0)
                norm_iat = min(iat / 2.0, 1.0)
                
                # Logic for Download Spike
                if size > 1000 or st.session_state.simulate_attack:
                    entropy = 0.82 + random.uniform(-0.02, 0.02)
                    symmetry = 0.15 + random.uniform(-0.05, 0.05)
                else:
                    entropy = 0.35 + random.uniform(-0.05, 0.05)
                    symmetry = 0.75 + random.uniform(-0.05, 0.05)
                
                features = [norm_size, norm_iat, entropy, symmetry]
                
                # Generate MSE/JSD via Model & Engine
                with torch.no_grad():
                    # Seq length 10 required by model
                    test_seq = torch.tensor([features]*10, dtype=torch.float32).unsqueeze(0)
                    mse_tensor = model_engine.reconstruction_error(test_seq)
                    mse = float(mse_tensor[0])
                
                jsd = calculate_jsd(features, PHONE_BASELINE)
                trust = calculate_trust_score(mse, jsd)
                
                # Update Session State Safely
                st.session_state.live_metrics = {"jsd": jsd, "mse": mse, "trust": trust}
                st.session_state.pulse_mse_history.append(mse)
                st.session_state.pulse_mse_history.pop(0)
                st.session_state.pulse_jsd_history.append(jsd)
                st.session_state.pulse_jsd_history.pop(0)
                st.session_state.phone_activity_sparkline.append(norm_size)
                st.session_state.phone_activity_sparkline.pop(0)
                
                if trust < 50:
                    st.session_state.threat_log.insert(0, {
                        "time": datetime.datetime.now().strftime("%H:%M:%S"),
                        "device": "Aegis-Phone",
                        "msg": f"Anomalous Traffic detected (JSD: {jsd:.2f})",
                        "type": "CRITICAL"
                    })
        except Exception:
            pass

    try:
        sniff(prn=handle_packet, store=0)
    except:
        # Simulation loop if Scapy fails (no Npcap/Admin)
        while True:
            time.sleep(0.5)
            # Dummy packet processing
            size = 1200 if st.session_state.simulate_attack else random.randint(64, 500)
            now = time.time()
            iat = now - last_pkt_time
            last_pkt_time = now
            norm_size = min(size / 1500.0, 1.0)
            norm_iat = min(iat / 2.0, 1.0)
            
            if st.session_state.simulate_attack:
                entropy, symmetry = 0.82, 0.15
            else:
                entropy, symmetry = 0.35, 0.75
            
            feat = [norm_size, norm_iat, entropy, symmetry]
            jsd = calculate_jsd(feat, PHONE_BASELINE)
            mse = 0.42 if st.session_state.simulate_attack else 0.02
            trust = calculate_trust_score(mse, jsd)
            
            st.session_state.live_metrics = {"jsd": jsd, "mse": mse, "trust": trust}
            st.session_state.pulse_mse_history.append(mse)
            st.session_state.pulse_mse_history.pop(0)
            st.session_state.pulse_jsd_history.append(jsd)
            st.session_state.pulse_jsd_history.pop(0)
            st.session_state.phone_activity_sparkline.append(norm_size)
            st.session_state.phone_activity_sparkline.pop(0)

if 'sniffer_thread' not in st.session_state:
    ctx = get_script_run_ctx()
    t = threading.Thread(target=start_sniffer, daemon=True)
    add_script_run_ctx(t, ctx)
    t.start()
    st.session_state.sniffer_thread = True

# --- NAVIGATION ---
def navigate(to, device=None):
    st.session_state.page = to
    st.session_state.active_device = device
    # Clear logs when entering new device
    if to == "dashboard":
        st.session_state.threat_log = []

# --- PAGE: FLEET OVERVIEW ---
def render_fleet():
    st.markdown("<h1 style='text-align: center; letter-spacing: 5px; color: white;'>🌐 AEGIS FLEET REGISTRY</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #aaa; margin-bottom: 40px;'>Real-time monitoring of registered enterprise assets.</p>", unsafe_allow_html=True)

    cols = st.columns(4)
    for idx, (dev_id, info) in enumerate(IOT_REGISTRY.items()):
        with cols[idx % 4]:
            health = st.session_state.device_health[dev_id]
            st.markdown(f"""
            <div class="fleet-card">
                <div style="font-size: 3rem; margin-bottom: 10px;">{info['icon']}</div>
                <h3>{info['name']}</h3>
                <p style="color: {NEON_CYAN}; font-weight: bold;">{dev_id}</p>
                <div class="{'status-online' if health == 'Healthy' else 'status-critical'}">
                    {'● ONLINE' if health == 'Healthy' else '● CRITICAL'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"OPEN TWIN", key=f"btn_{dev_id}", use_container_width=True):
                navigate("dashboard", dev_id)
                st.rerun()

    st.markdown("---")
    st.markdown(f"<h2 style='text-align: center; color: {NEON_CYAN};'>🛡️ LIVE HARDWARE GATEWAY</h2>", unsafe_allow_html=True)
    
    c_left, c_right = st.columns([1, 2])
    with c_left:
        # Mini Fragment for the Phone Card Sparkline
        @st.fragment(run_every=0.1)
        def phone_card_fragment():
            st.markdown(f"""
            <div class="fleet-card" style="border: 2px solid {NEON_CYAN}; background: rgba(0, 255, 242, 0.05);">
                <div style="font-size: 3.5rem;">📱</div>
                <h3 style="color: white;">Aegis-Linked Phone</h3>
                <p style="color: {NEON_CYAN};">MAC: {PHONE_MAC}</p>
                <div class="status-online">● HARDWARE SYNC ACTIVE</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Sparkline
            fig = go.Figure(go.Scatter(y=st.session_state.phone_activity_sparkline, fill='tozeroy', line=dict(color=NEON_CYAN, width=2)))
            fig.update_layout(height=60, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown("<p style='text-align:center; font-size: 0.7rem; color: #5fcfcf;'>NETWORK ACTIVITY SYNC</p>", unsafe_allow_html=True)
            
            if st.button("ENTER HARDWARE TWIN", use_container_width=True):
                navigate("dashboard", "PHONE")
                st.rerun()
        
        phone_card_fragment()

    with c_right:
        st.markdown("<div style='height: 300px; display: flex; align-items: center; justify-content: center; color: #444; border: 1px dashed #444; border-radius: 12px;'>SYSTEM TELEMETRY FEED ACTIVE</div>", unsafe_allow_html=True)

# --- PAGE: DASHBOARD ---
def render_dashboard():
    dev_id = st.session_state.active_device
    is_phone = (dev_id == "PHONE")
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"<h2 style='color:{NEON_CYAN}'>🛡️ SOC COMMAND</h2>", unsafe_allow_html=True)
        if st.button("← FLEET REGISTRY", use_container_width=True):
            navigate("fleet")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🛠️ TUNING")
        st.session_state.sensitivity = st.slider("Anomaly Sensitivity", 0.05, 0.50, st.session_state.sensitivity)
        
        if is_phone:
            st.markdown("---")
            st.markdown("### 🔥 ATTACK SIM")
            st.session_state.simulate_attack = st.toggle("Trigger 3GB Download Attack", value=st.session_state.simulate_attack)
        
        st.markdown("---")
        st.markdown("### ☣️ REMEDIATION")
        if st.button("QUARANTINE DEVICE", use_container_width=True):
            st.warning(f"Device {dev_id} placed in isolated subnet.")
            if not is_phone: st.session_state.device_health[dev_id] = "Compromised"
        if st.button("EXECUTE REMEDIATION", use_container_width=True):
            st.success("Remediation script executed. Wiping memory...")
            if not is_phone: st.session_state.device_health[dev_id] = "Healthy"

    # Marquee (outside fragment for top bar persistence)
    @st.fragment(run_every=0.1)
    def dashboard_fragment():
        m = st.session_state.live_metrics
        trust = m['trust']
        status_color = NEON_CYAN if trust >= 50 else NEON_PINK
        
        # 1. Neural Pulse Marquee
        st.markdown(f"""
        <div class="marquee-container">
            <marquee scrollamount="10" style="color: {status_color}; font-family: 'Source Code Pro', monospace; font-size: 1.2rem;">
                // [AEGIS-ACTIVE] // MAC: {PHONE_MAC if is_phone else dev_id} // JSD: {m['jsd']:.4f} // MSE: {m['mse']:.4f} // ANOMALY PROBABILITY: {max(0, 100-trust):.1f}% // STATUS: {'INTEGRITY VERIFIED' if trust >= 50 else 'SECURITY COMPROMISED'} //
            </marquee>
        </div>
        """, unsafe_allow_html=True)

        # 2. Large Trust Score Gauge
        c_main = st.columns([1, 2, 1])
        with c_main[1]:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = trust,
                domain = {'x': [0, 1], 'y': [0, 1]},
                number = {'font': {'color': 'white', 'size': 100}, 'suffix': "%"},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': status_color},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': status_color,
                    'steps': [
                        {'range': [0, 50], 'color': 'rgba(255, 0, 127, 0.2)'}
                    ],
                }
            ))
            fig_gauge.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=0,b=0,l=0,r=0))
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
            st.markdown("<h3 style='text-align:center; margin-top: -50px;'>SYSTEM TRUST SCORE</h3>", unsafe_allow_html=True)

        # 3. Visuals Side-by-Side
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">3D Cluster Drift Plot</div>', unsafe_allow_html=True)
            # 3D Plot logic
            feat = [random.random() for _ in range(3)] if not is_phone else st.session_state.phone_activity_sparkline[-3:]
            fig3d = go.Figure(data=[go.Scatter3d(
                x=[PHONE_BASELINE[0] if is_phone else 0.5], 
                y=[PHONE_BASELINE[1] if is_phone else 0.5], 
                z=[PHONE_BASELINE[2] if is_phone else 0.5],
                mode='markers', name='Baseline', marker=dict(size=10, color=NEON_BLUE)
            )])
            fig3d.add_trace(go.Scatter3d(
                x=[feat[0]], y=[feat[1]], z=[feat[2]],
                mode='markers', name='Live', marker=dict(size=15, color=status_color)
            ))
            fig3d.update_layout(scene=dict(xaxis=dict(range=[0,1]), yaxis=dict(range=[0,1]), zaxis=dict(range=[0,1])),
                              height=400, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig3d, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Neural Health Monitor</div>', unsafe_allow_html=True)
            fig_health = go.Figure()
            fig_health.add_trace(go.Scatter(y=st.session_state.pulse_mse_history, name="MSE (Anomaly)", line=dict(color=NEON_PINK, width=3)))
            fig_health.add_trace(go.Scatter(y=st.session_state.pulse_jsd_history, name="JSD (Friction)", line=dict(color=NEON_CYAN, width=3)))
            # Add sensitivity threshold line
            fig_health.add_shape(type="line", x0=0, y0=st.session_state.sensitivity, x1=50, y1=st.session_state.sensitivity, line=dict(color="orange", width=2, dash="dash"))
            fig_health.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=0,b=0), font=dict(color="white"))
            st.plotly_chart(fig_health, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        # 4. Math Section
        st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Mathematical Security Verification</div>', unsafe_allow_html=True)
        st.latex(rf"f_{{jsd}}(P \| Q) = \frac{{1}}{{2}} \sum P \ln \frac{{P}}{{M}} + \frac{{1}}{{2}} \sum Q \ln \frac{{Q}}{{M}} \approx {m['jsd']:.4f}")
        st.latex(rf"\mathcal{{L}}_{{MSE}} = \frac{{1}}{{N}} \sum_{{i=1}}^{{N}} |x_i - \hat{{x}}_i|^2 \approx {m['mse']:.4f}")
        st.latex(rf"T = 100 - (f_{{jsd}} \cdot 100 + \mathcal{{L}}_{{MSE}} \cdot 200) \implies {trust:.2f}\%")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 5. Live Threat Log
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Live Anomaly Log</div>', unsafe_allow_html=True)
        if st.session_state.threat_log:
            for entry in st.session_state.threat_log[:5]:
                st.markdown(f"<p style='color: {NEON_PINK if entry['type']=='CRITICAL' else 'white'}'>[{entry['time']}] <b>{entry['device']}</b>: {entry['msg']}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #444'>NO ANOMALIES DETECTED IN CURRENT WINDOW</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    dashboard_fragment()

# --- MAIN ROUTER ---
if st.session_state.page == "fleet":
    render_fleet()
else:
    render_dashboard()