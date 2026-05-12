import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Настройка страницы
st.set_page_config(page_title="Auxetic Lattice Generator", layout="wide")

def get_base_unit(L, S, h, alpha_deg, scale):
    """Расчет геометрии узла и площади"""
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
    
    # Площадь через формулу Гаусса
    x, y = points[:, 0], points[:, 1]
    unit_area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    
    return points, unit_area, (Ls, Ss, hs)

# --- ИНТЕРФЕЙС (Боковая панель) ---
st.sidebar.header("Параметры ячейки (мм)")
L = st.sidebar.slider("L (Основание)", 0.5, 10.0, 3.0, 0.1)
S = st.sidebar.slider("S (Наклонная балка)", 0.5, 10.0, 1.5, 0.1)
h = st.sidebar.slider("h (Толщина)", 0.1, 2.0, 0.4, 0.05)
alpha = st.sidebar.slider("Alpha (Угол, град)", 20, 85, 60, 1)
scale = st.sidebar.slider("Scale (Масштаб)", 0.1, 5.0, 1.0, 0.05)

st.sidebar.header("Размеры модели (мм)")
total_w = st.sidebar.number_input("Общая ширина (B_target)", 10, 500, 70)
total_h = st.sidebar.number_input("Общая высота (A_target)", 10, 500, 70)

# --- РАСЧЕТЫ ---
points, unit_area, scaled_params = get_base_unit(L, S, h, alpha, scale)
Ls, Ss, hs = scaled_params

# Параметры стыковки
alpha_rad = np.radians(alpha)
x3_s = Ls - Ss * np.cos(alpha_rad)
y3_s = hs/2.0 + Ss * np.sin(alpha_rad)
cx, cy = x3_s + (hs/2.0) * np.sin(alpha_rad), y3_s + (hs/2.0) * np.cos(alpha_rad)

w_step, v_step = 2 * cx, 2 * cy

# Количество (nx - четное, ny - нечетное)
nx = ((int(np.ceil(total_w / w_step)) + 1) // 2) * 2
ny = (int(np.ceil(total_h / v_step)) // 2) * 2 + 1

B_fact, A_fact = nx * w_step, ny * v_step
S_fact = (nx * ny) * unit_area
density = S_fact / (B_fact * A_fact)

# --- ОСНОВНОЙ ЭКРАН ---
st.title("Генератор ауксетической решетки")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Высота A_fact", f"{A_fact:.2f} мм")
col2.metric("Длина B_fact", f"{B_fact:.2f} мм")
col3.metric("Площадь материала", f"{S_fact:.1f} мм²")
col4.metric("Плотность", f"{density*100:.2f} %")

# Отрисовка
fig, ax = plt.subplots(figsize=(7, 6))
for i in range(nx):
    for j in range(ny):
        curr_unit = points.copy()
        if (i + j) % 2 == 0: # Ориентация первого элемента <-
            curr_unit[:, 0] = 2 * cx - curr_unit[:, 0]
        curr_unit[:, 0] += i * w_step
        curr_unit[:, 1] += j * v_step
        ax.fill(curr_unit[:, 0], curr_unit[:, 1], facecolor='gray', edgecolor='blue', alpha=0.8, lw=0.5)

ax.set_aspect('equal')
ax.grid(True, linestyle=':', alpha=0.5)
st.pyplot(fig, use_container_width=True)

st.info(f"Параметры с учетом масштаба: L={Ls:.2f}, S={Ss:.2f}, h={hs:.2f}. Сетка: {nx} столбцов x {ny} строк.")
