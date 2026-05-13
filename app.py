import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from stl import mesh
import io
import os
import tripy 

# 1. Настройка страницы
st.set_page_config(
    page_title="IPMech Auxetic Tool", 
    layout="wide"
)

# 2. CSS: Верстка согласно вашим требованиям
st.markdown("""
    <style>
           .block-container { padding-top: 1rem; padding-bottom: 0rem; }
           header { visibility: hidden; }
           
           /* Заголовки секций */
           .section-header {
               margin-top: 5px !important;
               margin-bottom: 10px !important;
               font-size: 1.0rem !important;
               font-weight: bold;
               color: #5c88be; 
               border-bottom: 1px solid #464b5d;
               padding-bottom: 3px;
           }

           /* Горизонтальное расположение подписи и поля */
           .label-col {
               font-size: 0.85rem;
               color: #9ea4b0;
               padding-top: 8px;
           }
           
           /* КАРТОЧКИ ХАРАКТЕРИСТИК (сетка) */
           .metric-box {
               background-color: #1e2129;
               border: 1px solid #3d4455;
               padding: 6px;
               border-radius: 4px;
               margin-bottom: 5px;
               text-align: center;
               min-height: 65px;
               display: flex;
               flex-direction: column;
               justify-content: center;
           }
           /* Шрифт названия ячеек характеристик 0.7 */
           .m-label { color: #9ea4b0; font-size: 0.7rem; text-transform: uppercase; line-height: 1.1; margin-bottom: 4px; }
           .m-value { color: #ffffff; font-size: 0.9rem; font-weight: bold; font-family: 'Consolas', monospace; }
           .m-unit { font-size: 0.6rem; color: #5c88be; }

           /* Стили для подписи в правой колонке */
           .column-footer {
               text-align: center; color: #808495; padding-top: 20px;
               font-size: 0.75rem; border-top: 1px solid #464b5d; margin-top: 20px;
           }
           
           /* Уплотнение кнопок в левой колонке */
           .stButton > button {
               margin-bottom: -10px;
           }
    </style>
    """, unsafe_allow_html=True)

# --- ГЕОМЕТРИЧЕСКИЙ БЛОК ---
def get_base_unit(L, S, h, alpha_deg, scale):
    Ls, Ss, hs = L * scale, S * scale, h * scale
    alpha = np.radians(alpha_deg)
    x1, y1 = 0, hs/2.0
    x2, y2 = Ls, hs/2.0
    x3 = Ls - Ss * np.cos(alpha)
    y3 = hs/2.0 + Ss * np.sin(alpha)
    x4 = x3 + hs * np.sin(alpha)
    y4 = y3 + hs * np.cos(alpha)
    x5 = Ls + (hs * (2 + np.cos(alpha))) / (2 * np.sin(alpha))
    y5 = 0
    top = np.array([[x1, y1], [x2, y2], [x3, y3], [x4, y4], [x5, y5]])
    bottom = np.array([[x4, -y4], [x3, -y3], [x2, -y2], [x1, -y1]])
    points = np.vstack([top, bottom])
    x, y = points[:, 0], points[:, 1]
    unit_area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    return points, unit_area, (Ls, Ss, hs)

def generate_stl(all_units, depth):
    faces = []
    for pts in all_units:
        num_pts = len(pts)
        p_bot = np.hstack([pts, np.zeros((num_pts, 1))])
        p_top = np.hstack([pts, np.full((num_pts, 1), depth)])
        for k in range(num_pts):
            next_k = (k + 1) % num_pts
            faces.append([p_bot[k], p_bot[next_k], p_top[next_k]])
            faces.append([p_bot[k], p_top[next_k], p_top[k]])
        polygon_vertices = [tuple(p) for p in pts]
        try:
            triangles = tripy.earclip(polygon_vertices)
            for tri in triangles:
                v1, v2, v3 = np.array(tri[0]), np.array(tri[1]), np.array(tri[2])
                faces.append([np.append(v1, 0), np.append(v3, 0), np.append(v2, 0)])
                faces.append([np.append(v1, depth), np.append(v2, depth), np.append(v3, depth)])
        except: continue
    model = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces): model.vectors[i] = f
    return model

# --- РАСПРЕДЕЛЕНИЕ КОЛОНОК ---
col_params, col_plot, col_metrics = st.columns([1.0, 3.2, 1.2])

# --- РАСЧЕТЫ (вынесены вверх для использования в кнопках) ---
# Инициализация переменных по умолчанию для предотвращения ошибок
if 'L' not in st.session_state: st.session_state.L = 3.0
if 'S' not in st.session_state: st.session_state.S = 1.5
if 'h' not in st.session_state: st.session_state.h = 0.4
if 'alpha' not in st.session_state: st.session_state.alpha = 60.0
if 'scale' not in st.session_state: st.session_state.scale = 1.0

# --- ЛЕВАЯ КОЛОНКА (ПАРАМЕТРЫ И КНОПКИ) ---
with col_params:
    st.markdown('<div class="section-header">⚙️ Cell Parameters</div>', unsafe_allow_html=True)
    
    def compact_input(label, min_v, max_v, def_v, step, key):
        c1, c2 = st.columns([1.1, 1.0])
        c1.markdown(f'<div class="label-col">{label}</div>', unsafe_allow_html=True)
        return c2.number_input(label, min_v, max_v, def_v, step, key=key, label_visibility="collapsed")

    L_v = compact_input("L (Base rib length, mm)", 0.5, 50.0, 3.0, 0.1, "L")
    S_v = compact_input("S (Inclined rib length, mm)", 0.5, 50.0, 1.5, 0.1, "S")
    h_v = compact_input("h (Wall thickness, mm)", 0.01, 10.0, 0.4, 0.05, "h")
    a_v = compact_input("a (Internal angle, °)", 10.0, 170.0, 60.0, 1.0, "alpha")
    sc_v = compact_input("Scaling factor", 0.01, 20.0, 1.0, 0.1, "scale")

    st.markdown('<div class="section-header">📦 Model Parameters</div>', unsafe_allow_html=True)
    target_A = compact_input("A (Minimum height, mm)", 5.0, 5000.0, 40.0, 1.0, "tA")
    target_B = compact_input("B (Minimum width, mm)", 5.0, 5000.0, 70.0, 1.0, "tB")
    z_depth = compact_input("Z (Depth, mm)", 0.1, 2000.0, 70.0, 1.0, "zD")
    ro_real_v = compact_input("Ro_real (Material density, g/cm^3)", 0.01, 20.0, 1.15, 0.01, "ro")

    # Выполнение расчетов для STL
    points, s_e, scaled = get_base_unit(L_v, S_v, h_v, a_v, sc_v)
    Ls, Ss, hs = scaled
    alpha_r = np.radians(a_v)
    cx = (Ls - Ss * np.cos(alpha_r)) + (hs/2.0) * np.sin(alpha_r)
    cy = (hs/2.0 + Ss * np.sin(alpha_r)) + (hs/2.0) * np.cos(alpha_r)
    w_step, v_step = 2 * cx, 2 * cy
    nx = max(2, ((int(np.ceil(target_B / w_step)) + 1) // 2) * 2)
    ny = max(1, (int(np.ceil(target_A / v_step)) // 2) * 2 + 1)

    all_units_coords = []
    for i in range(nx):
        for j in range(ny):
            u = points.copy()
            if (i + j) % 2 == 0: u[:, 0] = 2 * cx - u[:, 0]
            u[:, 0] += i * w_step; u[:, 1] += j * v_step
            all_units_coords.append(u)

    # Кнопки друг под другом внизу первой колонки
    st.write("") 
    if st.button("🛠️ Generate STL", use_container_width=True):
        with st.spinner("Calc..."):
            stl_mesh = generate_stl(all_units_coords, z_depth)
            buf = io.BytesIO()
            stl_mesh.save("model.stl", fh=buf)
            st.session_state['stl_ready'] = buf.getvalue()
    
    if 'stl_ready' in st.session_state:
        st.download_button("📥 Download STL", st.session_state['stl_ready'], "auxetic.stl", "application/sla", use_container_width=True)

# --- ЦЕНТРАЛЬНАЯ КОЛОНКА ---
with col_plot:
    st.markdown('<div class="section-header">📈 Model</div>', unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(10, 6.0))
    for u in all_units_coords:
        ax.fill(u[:, 0], u[:, 1], facecolor='#5c88be', edgecolor='#333333', linewidth=0.7)
    ax.set_aspect('equal'); ax.grid(True, linestyle=':', alpha=0.3)
    st.pyplot(fig, use_container_width=True)

# --- ПРАВАЯ КОЛОНКА (ХАРАКТЕРИСТИКИ И ПОДПИСЬ) ---
with col_metrics:
    st.markdown('<div class="section-header">🖼️ Cell schematic</div>', unsafe_allow_html=True)
    if os.path.exists("scheme.png"): 
        st.image("scheme.png", use_container_width=True)
    
    st.markdown('<div class="section-header">📊 Calculated Properties</div>', unsafe_allow_html=True)
    def metric_card(label, value, unit=""):
        return f'<div class="metric-box"><div class="m-label">{label}</div><div class="m-value">{value}<span class="m-unit">{unit}</span></div></div>'

    # Расчет выходных параметров
    f_h, f_w = ny * v_step, nx * w_step
    s_eff = f_h * f_w
    n_e = len(all_units_coords)
    s_real = s_e * n_e
    sample_mass = (s_real * z_depth) * ro_real_v * 0.001
    ro_eff_percent = (s_real / s_eff) * 100

    r1_c1, r1_c2, r1_c3 = st.columns(3)
    r1_c1.markdown(metric_card("А_real (Model height), ", f"{f_h:.1f}", "  mm"), unsafe_allow_html=True)
    r1_c2.markdown(metric_card("B_real (Model width), ", f"{f_w:.1f}", "  mm"), unsafe_allow_html=True)
    r1_c3.markdown(metric_card("S_eff = A_real*B_real", f"{s_eff:.0f}", "  mm^2"), unsafe_allow_html=True)

    r2_c1, r2_c2, r2_c3 = st.columns(3)
    r2_c1.markdown(metric_card("S_c (Cell area)", f"{s_e:.1f}", "  mm^2"), unsafe_allow_html=True)
    r2_c2.markdown(metric_card("N_c (Number of cells)", f"{n_e}"), unsafe_allow_html=True)
    r2_c3.markdown(metric_card("S_real = S_c*N_c", f"{s_real:.0f}", "  mm^2"), unsafe_allow_html=True)

    r3_c1, r3_c2, r3_c3 = st.columns(3)
    r3_c1.markdown(metric_card("Ro_real", f"{ro_real_v:.2f}", "  g/cm^3"), unsafe_allow_html=True)
    r3_c2.markdown(metric_card("Model mass", f"{sample_mass:.1f}", "  g"), unsafe_allow_html=True)
    r3_c3.markdown(metric_card("Ro_eff = S_real/S_eff", f"{ro_eff_percent:.1f}", "  %"), unsafe_allow_html=True)

    # Авторская подпись внизу правой колонки
    st.markdown('<div class="column-footer">© 2026 Demin A.I. — Laboratory of Mechanics of Novel Materials and Technologies IPMech RAS</div>', unsafe_allow_html=True)
