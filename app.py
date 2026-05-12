import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 1. Настройка страницы (обязательно первой командой)
st.set_page_config(page_title="Auxetic Lattice Generator", layout="wide")

# 2. CSS для минимизации отступов сверху и компактности интерфейса
st.markdown("""
    <style>
           .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                padding-left: 3rem;
                padding-right: 3rem;
            }
           h1 {
               margin-top: -35px;
               padding-top: 0;
               font-size: 2.2rem !important;
           }
           .stMetric {
               background-color: #262730;
               padding: 10px;
               border-radius: 5px;
               border: 1px solid #464b5d;
           }
    </style>
    """, unsafe_allow_html=True)

# --- Функции расчета ---
def get_base_unit(L, S, h, alpha_deg, scale):
    Ls, Ss, hs = L * scale, S * scale, h * scale
    alpha = np.radians(alpha_deg)
    dx = Ss * np.sin(alpha)
    dy = Ss * np.cos(alpha)
    # Площадь материала одной "бабочки" (2 горизонтальных + 4 наклонных луча)
    cell_material_area = (2 * Ls + 4 * Ss) * hs
    return Ls, Ss, hs, alpha, dx, dy, cell_material_area

# --- Боковая панель (Ввод данных) ---
st.sidebar.header("Параметры ячейки (мм)")
L_in = st.sidebar.slider("L (Основание)", 0.5, 10.0, 3.0, 0.1)
S_in = st.sidebar.slider("S (Наклонная балка)", 0.5, 10.0, 1.5, 0.1)
h_in = st.sidebar.slider("h (Толщина)", 0.1, 2.0, 0.4, 0.05)
alpha_in = st.sidebar.slider("Alpha (Угол, град)", 10, 80, 60, 5)
scale_in = st.sidebar.slider("Scale (Масштаб)", 0.1, 5.0, 1.0, 0.1)

st.sidebar.header("Размеры модели (мм)")
B_target = st.sidebar.number_input("Общая ширина (B_target)", 10, 500, 70)
A_target = st.sidebar.number_input("Общая высота (A_target)", 10, 500, 40)

# --- Вычисления ---
Ls, Ss, hs, alpha, dx, dy, s_cell = get_base_unit(L_in, S_in, h_in, alpha_in, scale_in)

# Расчет количества ячеек для заполнения области
nx = int(B_target // (Ls + dx))
if nx % 2 != 0: nx += 1  # Для симметрии

ny = int(A_target // (2 * dy))
ny = (ny // 2) * 2 + 1  # Нечетное количество строк

A_fact = ny * dy
B_fact = nx * (Ls + dx)
total_material_area = s_cell * (nx / 2) * ny # С учетом стыковки ячеек
density = (total_material_area / (A_fact * B_fact)) * 100 if A_fact * B_fact > 0 else 0

# --- Основной интерфейс ---
st.title("Генератор ауксетической решетки")

# Разделяем экран: 3.5 части для графика и 1 часть для параметров
col_left, col_right = st.columns([3.5, 1])

with col_left:
    # Создаем график. figsize теперь меньше по вертикали (6 вместо 8)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Отрисовка решетки
    for r in range(ny):
        for c in range(nx):
            # Рассчитываем смещение
            x_off = c * (Ls + dx)
            y_off = r * dy
            
            # Логика "Butterfly" (отражение каждого второго столбца)
            is_mirrored = (c % 2 != 0)
            direction = -1 if is_mirrored else 1
            
            # Горизонтальный луч
            ax.plot([x_off, x_off + Ls], [y_off, y_off], color='royalblue', lw=hs*2.5)
            
            # Наклонные лучи
            # Вверх
            ax.plot([x_off, x_off - direction * dx], [y_off, y_off + dy/2], color='royalblue', lw=hs*2.5)
            ax.plot([x_off + Ls, x_off + Ls + direction * dx], [y_off, y_off + dy/2], color='royalblue', lw=hs*2.5)
            # Вниз
            ax.plot([x_off, x_off - direction * dx], [y_off, y_off - dy/2], color='royalblue', lw=hs*2.5)
            ax.plot([x_off + Ls, x_off + Ls + direction * dx], [y_off, y_off - dy/2], color='royalblue', lw=hs*2.5)

    ax.set_aspect('equal')
    ax.set_xlim(-10, B_fact + 10)
    ax.set_ylim(-5, A_fact + 5)
    ax.grid(True, linestyle=':', alpha=0.5)
    
    # Вывод графика во всю ширину левой колонки
    st.pyplot(fig, use_container_width=True)

with col_right:
    st.subheader("Результаты")
    
    st.metric("Высота A_fact", f"{A_fact:.2f} мм")
    st.metric("Длина B_fact", f"{B_fact:.2f} мм")
    
    st.divider()
    
    st.metric("Площадь материала", f"{total_material_area:.1f} мм²")
    st.metric("Плотность", f"{density:.2f} %")
    
    st.info("Используйте панель слева для настройки геометрии. График и метрики обновятся автоматически.")
