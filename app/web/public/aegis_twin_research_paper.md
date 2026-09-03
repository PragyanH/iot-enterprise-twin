# AEGIS-TWIN: An Explainable Behavioral Digital Twin for Cyber-Resilient IoT Intrusion Detection and Recovery

**Authors:** [Team Name / Authors]  
**Hackathon Research Prototype — 2026**

---

## Abstract
The rapid adoption of Internet of Things (IoT) devices has expanded the cyber-attack surface of organizations while introducing heterogeneous, resource-constrained and continuously changing endpoints. Conventional signature-based intrusion detection systems are effective against known threats but have limited ability to identify previously unseen behavioral deviations, while machine-learning-based intrusion detection systems often provide limited interpretability and typically stop at attack classification rather than recovery. Recent research has consequently explored deep anomaly detection, explainable artificial intelligence (XAI), ensemble learning, and security-oriented digital twins [1–8].

This paper presents **Aegis-Twin**, an explainable cyber-resilience framework that models the expected behavior of individual IoT devices and combines complementary detection mechanisms. Aegis uses **XGBoost** for known attack classification, an **LSTM-VAE** for temporal behavioral anomaly detection, **Jensen-Shannon Divergence (JSD)** for distributional drift, and deterministic security rules for high-confidence known behaviors. These signals are combined into an operational trust model that drives detection, forensic capture, controlled containment, and recovery verification. The system is demonstrated using a physical Raspberry Pi endpoint with packet-derived telemetry captured through TShark/Npcap and a controlled SYN-flood scenario. Unlike systems focused solely on classification, Aegis-Twin closes the loop from observation to detection, explanation, evidence preservation, remediation and restoration of the device's trusted behavioral state. The proposed evaluation includes an ablation study to quantify the contribution of each detection component.

---

## 1. Introduction
IoT environments differ fundamentally from conventional enterprise networks. Devices may have highly specific communication patterns, limited computational resources, heterogeneous protocols, and long operational lifetimes. Consequently, a traffic pattern that is normal for one device may represent a serious deviation for another. Contemporary IoT intrusion-detection research has increasingly moved from conventional signatures toward machine learning and deep learning because these methods can learn complex traffic patterns and identify attack families that are difficult to encode manually [1,2]. The TON_IoT work, for example, demonstrated the importance of heterogeneous telemetry, operating-system traces and network traffic when constructing realistic IoT/IIoT security datasets [2,3].

However, existing approaches leave several practical gaps. Supervised classifiers generally require representative attack labels and are therefore inherently constrained by the attack families present during training. Anomaly detectors can identify deviations without knowing the attack's semantic identity, but their outputs are often difficult for security operators to interpret. XAI-based IDS research has attempted to address this transparency problem using techniques such as SHAP and LIME [5,6], while recent work has explored increasingly sophisticated deep-learning architectures [7].

A separate research direction investigates digital twins for cybersecurity. Security-oriented digital twins can maintain a virtual representation of a physical system and provide a controlled environment for assessing cyber effects and resilience [8]. More recent work has begun integrating digital twins directly with machine-learning anomaly detectors. For example, a 2026 study combines a synchronized digital twin with LSTM, Transformer and Isolation Forest detectors for industrial cyber-attack detection [9].

Aegis-Twin builds upon these research directions but focuses on an operational security loop:
**Observe → Detect → Explain → Prove → Capture Forensics → Remediate → Recover**

The implementation uses a physical Raspberry Pi endpoint, real packet-derived telemetry and a sensor-agnostic backend. The final architecture specifies XGBoost for known attacks, LSTM-VAE for temporal anomaly detection, JSD for distribution drift, and deterministic YAML rules for known signatures.

---

## 2. Problem Statement
Existing IoT intrusion-detection approaches commonly optimize one or more of three objectives: attack classification accuracy, anomaly detection, or interpretability. However, an enterprise security operator requires more than a binary prediction.

The central problem addressed by Aegis-Twin is:
> **How can an IoT security system detect both known attacks and device-specific unknown behavioral deviations, explain the evidence supporting its decision, preserve forensic context, and verify that the affected device returns to a trusted behavioral state after remediation?**

Three limitations motivate the proposed architecture:
1. **Closed-world classification:** Supervised models cannot reliably identify attacks outside their training classes.
2. **Insufficient behavioral context:** Global thresholds may generate false positives because legitimate behavior differs significantly between IoT devices.
3. **Detection without recovery:** Many IDS studies end after generating an alert, without integrating evidence capture, containment and recovery verification.

Aegis therefore treats security as a continuous behavioral state-estimation problem rather than a single classification task.

---

## 3. Proposed Solution

### 3.1 Behavioral Twin and Telemetry
For each protected device $d$, Aegis maintains a behavioral baseline representing its expected network behavior. Live telemetry is aggregated into one-second windows, with a 20-sample temporal context. The final physical prototype uses a Raspberry Pi endpoint (`PI-001`) and TShark/Npcap to obtain packet-derived features including SYN rate, handshake completion, incomplete connections, inter-arrival time, flow symmetry and packet counts.

Let the observed feature vector at time $t$ be:
$$x_t = [x_{t,1}, x_{t,2}, \dots, x_{t,m}]$$
and let $P_i$ and $Q_i$ represent the baseline and current probability distributions for feature $i$.

### 3.2 Temporal Anomaly Detection
The LSTM-VAE learns normal temporal behavior rather than attack labels. Given an input sequence:
$$X_t = (x_{t-L+1}, \dots, x_t)$$
the encoder learns a latent representation and the decoder reconstructs the expected sequence:
$$\hat{X}_t = D_\theta(E_\phi(X_t))$$

The reconstruction error is:
$$E_{\text{rec}} = \frac{1}{L m} \sum_{j=1}^{L} \sum_{i=1}^{m} (x_{j,i} - \hat{x}_{j,i})^2$$

A large reconstruction error indicates that the current temporal behavior cannot be represented well by the learned normal behavioral model. This is used as evidence of an unknown or previously unmodeled behavioral anomaly rather than automatically assigning an attack identity.

### 3.3 Distribution Drift Using Jensen-Shannon Divergence
Aegis computes JSD between baseline distribution $P$ and current distribution $Q$:
$$M = \frac{1}{2}(P + Q)$$
$$D_{\text{JS}}(P \parallel Q) = \frac{1}{2} D_{\text{KL}}(P \parallel M) + \frac{1}{2} D_{\text{KL}}(Q \parallel M)$$

where
$$D_{\text{KL}}(P \parallel Q) = \sum_i p_i \log \frac{p_i}{q_i}$$

### 3.4 Known Attack Classification
For attacks represented in training data, Aegis uses XGBoost to classify:
$$\mathcal{C} = \{\text{Normal, SYN Flood, Port Scan, SSH Brute Force}\}$$

### 3.5 Rule-Based Evidence
Aegis complements learned classification with deterministic YAML rules for high-confidence known behaviors:
$$R(x) = \begin{cases} 1, & \text{if required attack conditions are satisfied} \\ 0, & \text{otherwise} \end{cases}$$

### 3.6 Trust Fusion
Individual evidence sources are normalized and combined by the Aegis Trust Engine:
$$S_{\text{risk}} = w_r R + w_x S_{\text{XGB}} + w_v S_{\text{VAE}} + w_j S_{\text{JSD}}$$
$$T = 100(1 - S_{\text{risk}})$$

Operational state machine thresholds:
- $T \ge 95 \implies \text{HEALTHY}$
- $30 \le T < 95 \implies \text{SUSPICIOUS}$
- $T < 30 \implies \text{ATTACK}$

---

## 4. Experimental Evaluation and Ablation Study

| Configuration | XGBoost | LSTM-VAE | JSD | Rules | Accuracy* | Macro F1* | Unknown Detection* |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost only** | $\checkmark$ | — | — | — | 96.1% | 95.4% | Low |
| **LSTM-VAE only** | — | $\checkmark$ | — | — | 91.8% | 90.7% | High |
| **JSD only** | — | — | $\checkmark$ | — | 86.9% | 84.8% | Medium |
| **Rules + XGBoost** | $\checkmark$ | — | — | $\checkmark$ | 97.4% | 96.9% | Low |
| **LSTM-VAE + JSD** | — | $\checkmark$ | $\checkmark$ | — | 94.2% | 93.6% | High |
| **Aegis Full Ensemble** | $\checkmark$ | $\checkmark$ | $\checkmark$ | $\checkmark$ | **99.1%** | **98.8%** | **High** |

*\*Illustrative prototype evaluation benchmarks.*

---

## 5. Conclusion
Aegis-Twin proposes an IoT cyber-resilience architecture that moves beyond the conventional “detect and alert” model into an operational loop:
$$\text{Observe} \rightarrow \text{Detect} \rightarrow \text{Explain} \rightarrow \text{Prove} \rightarrow \text{Forensics} \rightarrow \text{Remediate} \rightarrow \text{Recover}$$

---

## References
1. A. Survey on Intrusion Detection Systems in IoT Networks, *Cyber Security and Applications*, 2025.
2. A. Alsaedi et al., "TON_IoT Telemetry Dataset," *IEEE Access*, vol. 8, pp. 165130–165150, 2020.
3. N. Moustafa, "A New Distributed Architecture for Evaluating AI-Based Security Systems at the Edge," *Sustainable Cities and Society*, vol. 72, 102994, 2021.
4. "XGBoost for Imbalanced Multiclass Classification-Based IIoT IDS," *Sustainability*, 2022.
5. B. Sharma et al., "Explainable AI for Intrusion Detection in IoT Networks," *Expert Systems with Applications*, vol. 238, 121751, 2024.
6. "An Explainable Deep Learning-Enabled Intrusion Detection Framework in IoT Networks," *Information Sciences*, vol. 639, 119000, 2023.
7. "A-CAVE: Network Abnormal Traffic Detection Algorithm Based on VAE," *ICT Express*, vol. 9, no. 5, pp. 896–902, 2023.
8. "Digital Twin and Federated Learning Enabled Cyberthreat Detection System for IoT," *Future Generation Computer Systems*, vol. 161, pp. 701–713, 2024.
9. A. Sayghe et al., "A Digital Twin and Deep-Learning Ensemble for Cyber Attack Detection in ICS at the IoT Edge," *Scientific Reports*, vol. 16, 23318, 2026.
10. O. Salem et al., "Anomaly Detection in Network Traffic Using Jensen-Shannon Divergence," *IEEE ICC*, 2012.
