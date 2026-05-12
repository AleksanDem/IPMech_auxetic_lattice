import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 1. Настройка страницы
st.set_page_config(page_title="Auxetic Lattice Generator", layout="wide")

# 2. Стиль интерфейса (CSS)
st.markdown("""
    <style>
           .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
            }
           h1 {
               margin-top: -40px;
               font-size: 2.2rem !important;
           }
           [data-testid="stMetric"] {
               background-color: #262730;
               padding: 5px 10px !important;
               border-radius: 10px;
               border: 1px solid #464b5d;
               margin-bottom: -10px !important;
           }
           
    </style>
    """, unsafe_allow_html=True)

# --- МАТЕМАТИЧЕСКОЕ ЯДРО ---
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

# --- ИНТЕРФЕЙС (Боковая панель) ---
st.sidebar.header("Параметры ячейки (мм)")
L_val = st.sidebar.slider("L (Основание)", 0.5, 10.0, 3.0, 0.1)
S_val = st.sidebar.slider("S (Наклонная балка)", 0.5, 10.0, 1.5, 0.1)
h_val = st.sidebar.slider("h (Толщина)", 0.1, 2.0, 0.4, 0.05)
alpha_val = st.sidebar.slider("Alpha (Угол, град)", 20, 85, 60, 1)
scale_val = st.sidebar.slider("Scale (Масштаб)", 0.1, 5.0, 1.0, 0.05)

st.sidebar.header("Размеры модели (мм)")
total_w = st.sidebar.number_input("Общая ширина (B_target)", 10, 500, 70)
total_h = st.sidebar.number_input("Общая высота (A_target)", 10, 500, 40)

# --- РАСЧЕТЫ ---
points, unit_area, scaled_params = get_base_unit(L_val, S_val, h_val, alpha_val, scale_val)
Ls, Ss, hs = scaled_params

alpha_rad = np.radians(alpha_val)
x3_s = Ls - Ss * np.cos(alpha_rad)
y3_s = hs/2.0 + Ss * np.sin(alpha_rad)
cx, cy = x3_s + (hs/2.0) * np.sin(alpha_rad), y3_s + (hs/2.0) * np.cos(alpha_rad)

w_step, v_step = 2 * cx, 2 * cy
nx = ((int(np.ceil(total_w / w_step)) + 1) // 2) * 2
ny = (int(np.ceil(total_h / v_step)) // 2) * 2 + 1

B_fact, A_fact = nx * w_step, ny * v_step
S_fact = (nx * ny) * unit_area
density = S_fact / (B_fact * A_fact) if B_fact * A_fact > 0 else 0

# --- ОСНОВНОЙ ЭКРАН ---
st.title("Генератор ауксетической решетки")

# Создаем две колонки: левая для графика (большая), правая для данных (узкая)
col_plot, col_data = st.columns([3.5, 1])

with col_plot:
    fig, ax = plt.subplots(figsize=(10, 7))
    for i in range(nx):
        for j in range(ny):
            curr_unit = points.copy()
            if (i + j) % 2 == 0:
                curr_unit[:, 0] = 2 * cx - curr_unit[:, 0]
            curr_unit[:, 0] += i * w_step
            curr_unit[:, 1] += j * v_step
            ax.fill(curr_unit[:, 0], curr_unit[:, 1], facecolor='royalblue', edgecolor='#1f2d3d', alpha=0.8, lw=0.5)

    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.3)
    ax.set_facecolor('#f0f2f6')
    st.pyplot(fig, use_container_width=True)

with col_data:
    st.subheader("Результаты")
    st.metric("Высота A_fact", f"{A_fact:.2f} мм")
    st.metric("Длина B_fact", f"{B_fact:.2f} мм")
    
    st.divider()
    
    st.metric("Площадь материала", f"{S_fact:.1f} мм²")
    st.metric("Плотность", f"{density*100:.2f} %")
    
    st.info(f"Сетка: {nx}x{ny}\nL={Ls:.2f}, S={Ss:.2f}, h={hs:.2f}")

st.write("<br><br>", unsafe_allow_html=True) # Добавляем немного отступа
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "© 2026 Demin A.I. — Laboratory of Mechanics of Novel Materials and Technologies IPMech RAS"
    "</p>", 
    unsafe_allow_html=True
)
