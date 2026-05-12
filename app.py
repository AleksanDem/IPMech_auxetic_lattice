import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 1. Настройка страницы (ДОЛЖНА быть первой командой)
st.set_page_config(page_title="Auxetic Lattice Generator", layout="wide")

# 2. Стиль интерфейса: поднимаем заголовок и настраиваем вид метрик
st.markdown("""
    <style>
           .block-container {
                padding-top: 1.5rem;
                padding-bottom: 0rem;
                padding-left: 3rem;
                padding-right: 3rem;
            }
           h1 {
               margin-top: -45px;
               padding-top: 0;
               font-size: 2.2rem !important;
           }
           [data-testid="stMetric"] {
               background-color: #262730;
               padding: 15px;
               border-radius: 10px;
               border: 1px solid #464b5d;
           }
    </style>
    """, unsafe_allow_html=True)

# --- Математическое ядро (восстановленная версия) ---
def calculate_geometry(L, S, h, alpha_deg, scale):
    Ls, Ss, hs = L * scale, S * scale, h * scale
    alpha = np.radians(alpha_deg)
    
    # Расчет смещений (alpha - угол наклона к горизонту)
    dx = Ss * np.cos(alpha)
    dy_half = Ss * np.sin(alpha)
    dy = 2 * dy_half
    
    # Площадь одной балки и 4-х ребер
    unit_material_area = (Ls + 4 * Ss) * hs
    return Ls, Ss, hs, dx, dy, dy_half, unit_material_area

# --- Боковая панель (Ввод данных) ---
st.sidebar.header("Параметры ячейки (мм)")
L_val = st.sidebar.slider("L (Основание)", 0.5, 10.0, 3.0, 0.1)
S_val = st.sidebar.slider("S (Наклонная балка)", 0.5, 10.0, 1.5, 0.1)
h_val = st.sidebar.slider("h (Толщина)", 0.1, 2.0, 0.4, 0.05)
alpha_in = st.sidebar.slider("Alpha (Угол, град)", 10, 80, 60, 5)
scale_val = st.sidebar.slider("Scale (Масштаб)", 0.1, 5.0, 1.0, 0.1)

st.sidebar.header("Размеры модели (мм)")
B_target = st.sidebar.number_input("Общая ширина", 10, 500, 70)
A_target = st.sidebar.number_input("Общая высота", 10, 500, 40)

# --- Расчеты параметров ---
Ls, Ss, hs, dx, dy, dy_half, s_unit = calculate_geometry(L_val, S_val, h_val, alpha_in, scale_val)

# Оптимальная компоновка: четное число столбцов, нечетное число строк
nx = int(B_target // (Ls + dx))
if nx % 2 != 0: nx += 1
ny = int(A_target // dy)
ny = (ny // 2) * 2 + 1

B_fact = nx * (Ls + dx) + dx
A_fact = ny * dy
total_area = s_unit * (nx / 2) * ny
density = (total_area / (B_fact * A_fact)) * 100 if B_fact * A_fact > 0 else 0

# --- Основной экран ---
st.title("Генератор ауксетической решетки")

# Разделение на колонки: график слева, метрики справа
col_plot, col_metrics = st.columns([3.5, 1])

with col_plot:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Отрисовка с учетом (0,0) как начала первой балки и зеркалирования "Butterfly"
    for r in range(ny):
        for c in range(nx):
            x0 = c * (Ls + dx)
            y0 = r * dy
            
            # Логика зеркалирования столбцов для формирования узлов
            side = 1 if (c % 2 == 0) else -1
            
            # Центральный горизонтальный луч (начало в x0, y0)
            ax.plot([x0, x0 + Ls], [y0, y0], color='royalblue', lw=hs*2.5, solid_capstyle='round')
            
            # Наклонные ребра (сходящиеся/расходящиеся)
            # Верхняя пара
            ax.plot([x0, x0 - side * dx], [y0, y0 + dy_half], color='royalblue', lw=hs*2.5, solid_capstyle='round')
            ax.plot([x0 + Ls, x0 + Ls + side * dx], [y0, y0 + dy_half], color='royalblue', lw=hs*2.5, solid_capstyle='round')
            # Нижняя пара
            ax.plot([x0, x0 - side * dx], [y0, y0 - dy_half], color='royalblue', lw=hs*2.5, solid_capstyle='round')
            ax.plot([x0 + Ls, x0 + Ls + side * dx], [y0, y0 - dy_half], color='royalblue', lw=hs*2.5, solid_capstyle='round')

    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.4)
    ax.set_xlabel("X, мм")
    ax.set_ylabel("Y, мм")
    
    st.pyplot(fig, use_container_width=True)

with col_metrics:
    st.subheader("Результаты")
    st.metric("Высота A_fact", f"{A_fact:.2f} мм")
    st.metric("Длина B_fact", f"{B_fact:.2f} мм")
    st.divider()
    st.metric("Площадь материала", f"{total_area:.1f} мм²")
    st.metric("Плотность", f"{density:.2f} %")
    
    st.info("Модель готова к экспорту координат для SolidWorks через API.")
