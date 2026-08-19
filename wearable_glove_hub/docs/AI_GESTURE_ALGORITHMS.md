# TinyML Gesture Classification & Tremor Anomaly AI
**Project:** Neuro Sign  
**Developer:** Rudra Attri Pandey  
**Module:** On-Device Real-Time Biomedical Machine Learning Engine

---

## 1. Mathematical Feature Vector

The glove collects a 5-dimensional normalized vector $\mathbf{x} \in \mathbb{R}^5$ at each sample interval:

$$\mathbf{x} = \begin{bmatrix} f_1 \\ f_2 \\ f_3 \\ p \\ r \end{bmatrix} = \begin{bmatrix} \text{Normalized Thumb Bend } [0, 1] \\ \text{Normalized Index Bend } [0, 1] \\ \text{Normalized Middle Bend } [0, 1] \\ \text{Normalized Hand Pitch } [-1, 1] \\ \text{Normalized Hand Roll } [-1, 1] \end{bmatrix}$$

Where:
- $f_i = \text{clamp}\left(\frac{\text{ADC}_i - \text{ADC}_{min,i}}{\text{ADC}_{max,i} - \text{ADC}_{min,i}}, 0, 1\right)$
- $p = \text{clamp}\left(\frac{\theta_{pitch}}{90^\circ}, -1, 1\right)$
- $r = \text{clamp}\left(\frac{\phi_{roll}}{90^\circ}, -1, 1\right)$

---

## 2. Weighted Euclidean Distance Metric

For each candidate gesture class $k \in \{0, 1, \dots, 7\}$ with prototypical centroid $\mathbf{c}_k = [c_{k,1}, c_{k,2}, c_{k,3}, c_{k,4}, c_{k,5}]^T$, the weighted metric distance $D_k(\mathbf{x})$ is computed as:

$$D_k(\mathbf{x}) = \sqrt{ w_f \sum_{i=1}^{3} (f_i - c_{k,i})^2 + w_\theta \left( (p - c_{k,4})^2 + (r - c_{k,5})^2 \right) }$$

Where weights are tuned for maximum discrimination:
- $w_f = 1.2$ (Flex sensor feature weight)
- $w_\theta = 1.5$ (Spatial orientation tilt weight)

The predicted gesture class $\hat{y}$ is selected via minimum distance:

$$\hat{y} = \arg\min_{k} D_k(\mathbf{x})$$

The classification confidence score $C \in [0, 1]$ is formulated as:

$$C = \max\left(0, 1.0 - \frac{D_{\hat{y}}(\mathbf{x})}{2.0}\right)$$

---

## 3. Gesture Centroid Matrix (3-Mode Hierarchy)

| Mode | Gesture ID | Intention / Label | Centroid $\mathbf{c}_k = [f_1, f_2, f_3, p, r]$ | Trigger Threshold | Primary Action Executed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline** | **0** | **Neutral / Rest** | $[0.15, 0.15, 0.15, 0.00, 0.00]$ | Flat / Open Hand | None (Continuous Monitoring) |
| **Mode 1: Flat Bed** | **1** | **Need Water** | $[0.80, 0.15, 0.15, 0.00, 0.00]$ | Bend Finger 1 $\ge 350\text{ms}$ | **Voice Prompt: "I Need Water"** |
| | **2** | **Need Food** | $[0.15, 0.80, 0.15, 0.00, 0.00]$ | Bend Finger 2 $\ge 350\text{ms}$ | **Voice Prompt: "I Need Food"** |
| | **3** | **Need Medicine** | $[0.15, 0.15, 0.80, 0.00, 0.00]$ | Bend Finger 3 $\ge 350\text{ms}$ | **Voice Prompt: "I Need Medicine"** |
| | **4** | **EMERGENCY CALL** | $[0.85, 0.85, 0.85, 0.00, 0.00]$ | All 3 Bent $\ge 350\text{ms}$ | **Fires Alarm Siren + Relay 4** |
| **Mode 2: Tilt Left 90°** | **11** | **Toggle Light 1** | $[0.80, 0.15, 0.15, 0.00, -0.85]$ | Left + Bend Finger 1 | **Toggles Relay 1 (Light 1 ON/OFF)** |
| | **12** | **Toggle Room Fan** | $[0.15, 0.80, 0.15, 0.00, -0.85]$ | Left + Bend Finger 2 | **Toggles Relay 2 (Fan ON/OFF)** |
| | **13** | **Toggle Bed Position** | $[0.15, 0.15, 0.80, 0.00, -0.85]$ | Left + Bend Finger 3 | **Toggles Relay 3 (Bed Adjust ON/OFF)** |
| **Mode 3: Tilt Right 90°** | **21** | **Call Nurse** | $[0.80, 0.15, 0.15, 0.00, +0.85]$ | Right + Bend Finger 1 | **Nurse Ward Call Alert Chime** |
| | **22** | **Pain Alert** | $[0.15, 0.80, 0.15, 0.00, +0.85]$ | Right + Bend Finger 2 | **Patient Pain Warning Alert** |
| | **23** | **All Relays OFF** | $[0.15, 0.15, 0.80, 0.00, +0.85]$ | Right + Bend Finger 3 | **Switches OFF Relays 1, 2, 3 (Sleep)** |

---

## 4. Tremor & Spasm Anomaly Detection Algorithm

For stroke, ALS, and paralysis patients, involuntary muscle spasms and tremors can be critical indicators of distress.

### High-Frequency Jerk Formulation:
Let $\mathbf{a}(t) = [a_x(t), a_y(t), a_z(t)]^T$ be the ADXL345 acceleration vector at sample time $t$. The dynamic jerk magnitude $J(t)$ is defined as:

$$J(t) = \|\mathbf{a}(t) - \mathbf{a}(t - \Delta t)\| = \sqrt{(a_x(t) - a_x(t-\Delta t))^2 + (a_y(t) - a_y(t-\Delta t))^2 + (a_z(t) - a_z(t-\Delta t))^2}$$

The smoothed tremor metric $T(t)$ is calculated via exponential moving average:

$$T(t) = \alpha \cdot (J(t) \times 100) + (1 - \alpha) \cdot T(t - \Delta t), \quad \alpha = 0.3$$

### Spasm Alert Condition:
If $T(t) > 70\%$ for a duration $\Delta t_{\text{sustained}} \ge 800\text{ms}$, the classifier overrides normal gesture states and immediately flags **GESTURE_SPASM_ANOMALY (ID 99)**, triggering the medical warning tone and emergency relay.
