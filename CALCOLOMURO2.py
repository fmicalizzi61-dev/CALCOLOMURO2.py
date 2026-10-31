import json
import math
import ssl
import urllib.request
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Muro C.A. NTC 2018 - Genio Civile",
    page_icon="🧱",
    layout="wide",
)

st.title(
    "🧱 Progetto Esecutivo Muro in C.A. (Tab. 08 & 09 Complete - NTC 2018)"
)
st.write(
    "Calcolo ufficiale geotecnico e strutturale (Approccio 2 - M2+R2) con"
    " pre-dimensionamento armature ed elaborato grafico."
)

# --- SEZIONE INPUT UTENTE (Sidebar per Desktop / Sottomenu per iPhone) ---
st.sidebar.header("⚙️ Dati di Progetto & Localizzazione")

with st.sidebar.expander("📍 Localizzazione & Sisma", expanded=True):
  lat_val = st.number_input(
      "Latitudine (deg)", value=38.1157, format="%.4f", step=0.0001
  )
  lon_val = st.number_input(
      "Longitudine (deg)", value=15.5534, format="%.4f", step=0.0001
  )
  St = st.number_input(
      "Coeff. topografico St", value=1.20, step=0.05, format="%.2f"
  )
  beta_deg = st.number_input(
      "Inclinazione terrapieno β (°)", value=0.0, step=0.5
  )

with st.sidebar.expander("📐 Geometria Muro", expanded=False):
  H = st.number_input("Altezza totale H (m)", value=5.00, step=0.10)
  B = st.number_input("Larghezza fondazione B (m)", value=3.60, step=0.10)
  t_piede = st.number_input("Mensola di piede (m)", value=1.10, step=0.10)
  s_testa = st.number_input("Spessore testa paramento (m)", value=0.40, step=0.05)
  s_base = st.number_input("Spessore base paramento (m)", value=0.60, step=0.05)
  s_fond = st.number_input("Spessore suola/fondazione (m)", value=0.60, step=0.05)

with st.sidebar.expander("🧱 Materiali", expanded=False):
  Rck = st.number_input("Resistenza cubica Rck (N/mm²)", value=30.0, step=5.0)
  fyk = st.number_input("Tensione snervamento fyk (N/mm²)", value=450.0, step=10.0)
  gamma_cls = st.number_input("Peso spec. cls (kN/m³)", value=25.0, step=0.5)

with st.sidebar.expander("🌱 Terreno & Sovraccarico", expanded=False):
  gamma_t = st.number_input("Peso terreno γ (kN/m³)", value=18.0, step=0.5)
  phi_deg = st.number_input("Attrito interno φ' (°)", value=30.0, step=0.5)
  delta_deg = st.number_input("Attrito terra-muro δ (°)", value=20.0, step=0.5)
  c = st.number_input("Coesione c' (kPa)", value=0.0, step=0.5)
  q = st.number_input("Sovraccarico q (kN/m²)", value=10.0, step=1.0)
  q_amm = st.number_input(
      "Tensione ammissibile q_amm (kPa)", value=300.0, step=10.0
  )


# --- FUNZIONI DI SUPPORTO ---
def ottieni_localita_online(lat, lon):
  url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
  req = urllib.request.Request(
      url, headers={"User-Agent": "MuroCalculatorNTC/1.0"}
  )
  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE
  try:
    with urllib.request.urlopen(req, context=ctx, timeout=3) as response:
      data = json.loads(response.read().decode())
      if "display_name" in data:
        return data["display_name"]
  except Exception:
    pass
  return f"Lat: {lat:.4f}, Lon: {lon:.4f}"


def seleziona_armatura(As_richiesto):
  diametri_test = [12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
  interassi_test = [10, 12.5, 15, 20, 25]
  migliore_phi, migliore_passo, min_diff = 16, 20, 999999.0
  for phi in diametri_test:
    area_singola = math.pi * ((phi / 10.0) ** 2) / 4.0
    for passo in interassi_test:
      As_off = area_singola * (100.0 / passo)
      if As_off >= As_richiesto and (As_off - As_richiesto) < min_diff:
        min_diff = As_off - As_richiesto
        migliore_phi, migliore_passo = phi, int(passo)
  As_eff = (math.pi * ((migliore_phi / 10.0) ** 2) / 4.0) * (
      100.0 / migliore_passo
  )
  return migliore_phi, migliore_passo, As_eff


def disegna_sezione_matplotlib(
    H,
    B,
    t_piede,
    s_testa,
    s_base,
    s_fond,
    p_par,
    pas_par,
    p_comp,
    pas_comp,
    p_tac,
    pas_tac,
    p_pie,
    pas_pie,
    p_rip,
    pas_rip,
):
  t_tacco = B - t_piede - s_base
  H_terreno = H - s_fond

  fig, ax = plt.subplots(figsize=(6, 9))

  # Geometria Fondazione
  poly_fond = [
      (0, 0),
      (B, 0),
      (B, s_fond),
      (0, s_fond),
  ]
  # Geometria Paramento
  poly_par = [
      (t_piede, s_fond),
      (t_piede + s_base, s_fond),
      (t_piede + s_base, H),
      (t_piede + s_base - s_testa, H),
  ]

  ax.add_patch(
      plt.Polygon(
          poly_fond,
          closed=True,
          facecolor="#e9ecef",
          edgecolor="black",
          lw=1.5,
          label="Fondazione",
      )
  )
  ax.add_patch(
      plt.Polygon(
          poly_par,
          closed=True,
          facecolor="#dee2e6",
          edgecolor="black",
          lw=1.5,
          label="Paramento",
      )
  )

  # Terrapieno
  ax.fill_between(
      [t_piede + s_base, B + 1],
      [s_fond, s_fond],
      [H, H],
      color="#f8f9fa",
      hatch="//",
      edgecolor="#adb5bd",
      alpha=0.5,
  )

  # Armature (Linee rosse e blu)
  cp = 0.05
  # Paramento Teso (Monte)
  ax.plot(
      [t_piede + s_base - cp, t_piede + s_base - cp],
      [s_fond + cp, H - cp],
      color="red",
      lw=2.5,
      label=f"Paramento Teso (Φ{p_par}/{pas_par}cm)",
  )
  # Paramento Compresso (Valle)
  ax.plot(
      [t_piede + cp, t_piede + s_base - s_testa + cp],
      [s_fond + cp, H - cp],
      color="blue",
      lw=1.8,
      label=f"Paramento Compresso (Φ{p_comp}/{pas_comp}cm)",
  )
  # Mensola Tacco
  ax.plot(
      [t_piede + s_base, B - cp],
      [s_fond - cp, s_fond - cp],
      color="red",
      lw=2.5,
      label=f"Tacco (Φ{p_tac}/{pas_tac}cm)",
  )
  # Mensola Piede
  ax.plot(
      [cp, t_piede],
      [cp, cp],
      color="red",
      lw=2.5,
      label=f"Piede (Φ{p_pie}/{pas_pie}cm)",
  )

  ax.set_aspect("equal")
  ax.set_xlim(-0.5, B + 1.2)
  ax.set_ylim(-0.5, H + 0.5)
  ax.set_title("Sezione Esecutiva e Disposizione Armature", fontsize=10, fontweight="bold")
  ax.grid(True, linestyle=":", alpha=0.6)
  ax.legend(loc="upper left", fontsize=7)

  return fig


# --- ESECUZIONE DEL CALCOLO ---
sit_str = ottieni_localita_online(lat_val, lon_val)

# Parametri sismici base (NTC 2018)
ag_slo, ag_sld, ag_slv, ag_slc = 0.055, 0.078, 0.235, 0.315
f0_slo, f0_sld, f0_slv, f0_slc = 2.414, 2.371, 2.440, 2.467
tc_slo, tc_sld, tc_slv, tc_slc = 0.274, 0.291, 0.351, 0.376
ss_slo, ss_sld, ss_slv, ss_slc = 1.200, 1.200, 1.170, 1.080

ag_max = ss_slv * St * ag_slv

gamma_phi = 1.2
phi_k = math.radians(phi_deg)
phi_d = math.atan(math.tan(phi_k) / gamma_phi)
delta_k = math.radians(delta_deg)
delta_d = math.atan(math.tan(delta_k) / gamma_phi)

gamma_G2 = 1.3
gamma_G_terreno = 1.0
gamma_Q = 1.3
beta = math.radians(beta_deg)
fyd = fyk / 1.15
gamma_F = 1.3

t_tacco = B - t_piede - s_base
H_terreno = H - s_fond

beta_s = 0.28
kh = beta_s * ag_max
kv = 0.5 * kh
theta = math.atan(kh / (1.0 - kv))

num_arg = math.sin(phi_d + delta_d) * math.sin(phi_d - beta - theta)
den_arg = math.cos(delta_d + beta) * math.cos(theta)
sq_term = math.sqrt(max(0.0, num_arg / den_arg))
Kae = (math.cos(phi_d - theta) ** 2) / (
    (math.cos(theta) ** 2)
    * math.cos(delta_d)
    * (1.0 + sq_term * math.sin(phi_d + delta_d + beta)) ** 2
)

E_terreno = 0.5 * gamma_t * (H**2) * Kae * (1.0 - kv) * gamma_G_terreno
E_q = q * H * Kae * gamma_Q
E_tot = E_terreno + E_q
braccio_E = ((0.5 * gamma_t * (H**2) * (H / 3.0)) + (q * H * (H / 2.0))) / E_tot
M_rib = E_tot * braccio_E

area_par = ((s_testa + s_base) / 2.0) * H_terreno
W_par = area_par * gamma_cls
bar_par = t_piede + s_base - (s_base - s_testa) / 3.0
W_fond = B * s_fond * gamma_cls
bar_fond = B / 2.0
W_terr = t_tacco * H_terreno * gamma_t
bar_terr = t_piede + s_base + (t_tacco / 2.0)
W_q_tacco = t_tacco * q

M_stab = (
    (W_par * gamma_G2 * bar_par)
    + (W_fond * gamma_G2 * bar_fond)
    + ((W_terr * gamma_G2 + W_q_tacco * gamma_Q) * bar_terr)
)

R_rib = M_stab / M_rib if M_rib > 0 else 999.0

N_ed = (
    W_par * gamma_G2 + W_fond * gamma_G2 + W_terr * gamma_G2 + W_q_tacco * gamma_Q
) *