import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 1. Настройка страницы
st.set_page_config(page_title="Auxetic Lattice Generator", layout="wide")

# 2. CSS для компактности
st.markdown("""
    <style>
           .block-container { padding-top: 1rem; padding-bottom: 0rem; }
           h1 { margin-top: -35px; font-size: 2.2rem !important; }
           .stMetric { background-color: #262730; padding: 10px; border-radius: 5px; border: 1px solid #464b5d; }
    </style>
    """, unsafe_allow_html=True)

# --- Математическое ядро ---
def get_geometry(L, S, h, alpha_deg, scale):
    Ls, Ss, hs = L * scale, S * scale, h * scale
    alpha = np.radians(alpha_deg)
    
    # Смещение по X и Y для наклонных ребер
    dx = Ss * np.sin(alpha)
    dy = Ss * np.cos(alpha)
    
    # Площадь одной структурной единицы (1 горизонт + 4 наклонных ребра)
    unit_area = (Ls + 4 * Ss) * hs
    return Ls, Ss, hs, dx, dy, unit_area

# --- Sidebar ---
st.sidebar.header("Параметры ячейки (мм)")
L = st.sidebar.slider("L (Основание)", 0.5, 10.0, 3.0, 0.1)
S = st.sidebar.slider("S (Наклонная балка)", 0.5, 10.0, 1.5, 0.1)
h = st.sidebar.slider("h (Толщина)", 0.1, 2.0, 0.4, 0.05)
alpha_deg = st.sidebar.slider("Alpha (Угол, град)", 10, 80, 60, 5)
scale = st.sidebar.slider("Scale (Масштаб)", 0.1, 5.0, 1.0, 0.1)

st.sidebar.header("Размеры модели (мм)")
B_target = st.sidebar.number_input("Общая ширина", 10, 500, 70)
A_target = st.sidebar.number_input("Общая высота", 10, 500, 40)

# --- Расчеты параметров модели ---
Ls, Ss, hs, dx, dy, s_unit = get_geometry(L, S, h, alpha_deg, scale)

# Количество ячеек (nx - четное для симметрии, ny - нечетное)
nx = int(B_target // (Ls + dx))
if nx % 2 != 0: nx += 1
ny = int(A_target // (2 * dy))
ny = (ny // 2) * 2 + 1

A_fact = ny * dy
B_fact = nx * (Ls + dx)
# Суммарная площадь с учетом того, что балки общие при стыковке
total_material_area = s_unit * (nx / 2) * ny
density = (total_material_area / (A_fact * B_fact)) * 100 if A_fact * B_fact > 0 else 0

# --- Интерфейс ---
st.title("Генератор ауксетической решетки")

col_left, col_right = st.columns([3.5, 1])

with col_left:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Отрисовка ауксетической структуры
    for r in range(ny):
        for c in range(nx):
            x_off = c * (Ls + dx)
            y_off = r * dy
            
            # Зеркальное отражение каждого второго столбца ("Butterfly")
            side = -1 if (c % 2 != 0) else 1
            
            # 1. Центральный горизонтальный луч
            ax.plot([x_off, x_off + Ls], [y_off, y_off], color='royalblue', lw=hs*2.5)
            
            # 2. Наклонные ребра (формируют "входящие" углы)
            # Верхние
            ax.plot([x_off, x_off - side * dx], [y_off, y_off + dy/2], color='royalblue', lw=hs*2.5)
            ax.plot([x_off + Ls, x_off + Ls + side * dx], [y_off, y_off + dy/2], color='royalblue', lw=hs*2.5)
            # Нижние
            ax.plot([x_off, x_off - side * dx], [y_off, y_off - dy/2], color='royalblue', lw=hs*2.5)
            ax.plot([x_off + Ls, x_off + Ls + side * dx], [y_off, y_off - dy/2], color='royalblue', lw=hs*2.5)

    ax.set_aspect('equal')
    ax.set_xlim(-5, B_fact + 5)
    ax.set_ylim(-dy, A_fact + dy)
    ax.grid(True, linestyle=':', alpha=0.4)
    st.pyplot(fig, use_container_width=True)

with col_right:
    st.subheader("Результаты")
    st.metric("Высота A_fact", f"{A_fact:.2f} мм")
    st.metric("Длина B_fact", f"{B_fact:.2f} мм")
    st.divider()
    st.metric("Площадь", f"{total_material_area:.1f} мм²")
    st.metric("Плотность", f"{density:.2f} %")
    st.info("Математика отрисовки учитывает зеркальное отражение узлов для формирования NPR (Negative Poisson's Ratio) эффекта.")
