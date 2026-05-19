import streamlit as st
import numpy as np
import plotly.graph_objects as go
from stl import mesh
import io
import os
import tripy 
from shapely.geometry import Polygon
from shapely.ops import unary_union
import ezdxf

# 1. Настройка страницы
st.set_page_config(
    page_title="IPMech Auxetic Tool", 
    layout="wide"
)

# --- СИСТЕМА ЛОКАЛИЗАЦИИ (RU / EN) ---
TRANSLATIONS = {
    "cell_params": {"ru": "⚙️ Параметры ячейки", "en": "⚙️ Cell Parameters"},
    "model_params": {"ru": "📦 Параметры модели", "en": "📦 Model Parameters"},
    "frame_section": {"ru": "🔳 Рамка", "en": "🔳 Frame"},
    "enable_frame": {"ru": "Добавить frame", "en": "Add frame"},
    "frame_th": {"ru": "Толщина рамки, мм", "en": "Frame thickness, mm"},
    "frame_th_help": {"ru": "Толщина внешней сплошной рамки по периметру (мм)", "en": "Outer solid frame thickness (mm)"},
    "L_label": {"ru": "L, мм (Основание)", "en": "L, mm (Base)"},
    "S_label": {"ru": "S, мм (Наклон)", "en": "S, mm (Strut)"},
    "h_label": {"ru": "h, мм (Толщина)", "en": "h, mm (Thickness)"},
    "alpha_label": {"ru": "a (°)", "en": "a (°)"},
    "L_help": {"ru": "Длина горизонтального ребра элементарной ячейки (мм)", "en": "Horizontal rib length of unit cell (mm)"},
    "S_help": {"ru": "Длина наклонного ребра элементарной ячейки (мм)", "en": "Inclined strut length of unit cell (mm)"},
    "h_help": {"ru": "Толщина стенок структуры (мм)", "en": "Wall thickness (mm)"},
    "alpha_help": {"ru": "Внутренний угол наклона ребер (для ауксетиков < 90°)", "en": "Re-entrant angle (auxetic if < 90°)"},
    "scale_help": {"ru": "Масштабный коэффициент всей геометрии", "en": "Global geometry scale factor"},
    "width_label": {"ru": "Ширина модели (минимальная) В, мм", "en": "Width (minimal) B, mm"},
    "height_label": {"ru": "Высота модели (минимальная) А, мм", "en": "Height (minimal) A, mm"},
    "depth_label": {"ru": "Глубина модели Z, мм", "en": "Depth Z, mm"},
    "width_help": {"ru": "Минимальная ширина решетки (мм)", "en": "Target minimum lattice width (mm)"},
    "height_help": {"ru": "Минимальная высота решетки (мм)", "en": "Target minimum lattice height (mm)"},
    "depth_help": {"ru": "Глубина (толщина) экструзии по оси Z (мм)", "en": "Extrusion depth along Z axis (mm)"},
    "ro_help": {"ru": "Физическая плотность материала (г/см³)", "en": "Material density (g/cm³)"},
    "btn_generate": {"ru": "🛠️ Подготовить STL", "en": "🛠️ Generate STL"},
    "btn_download": {"ru": "📥 Скачать STL", "en": "📥 Download STL"},
    "generating": {"ru": "Генерация файлов...", "en": "Generating files..."},
    "structure": {"ru": "📈 Структура", "en": "📈 Structure"},
    "tab_2d": {"ru": "2D Чертёж", "en": "2D Drawing"},
    "tab_3d": {"ru": "3D Просмотр", "en": "3D Preview"},
    "3d_stale": {"ru": "⚠️ Параметры были изменены. Нажмите '🛠️ Подготовить STL' для обновления 3D модели.", "en": "⚠️ Parameters changed. Click '🛠️ Generate STL' to update the 3D model."},
    "3d_empty": {"ru": "Сгенерируйте STL (кнопка слева), чтобы увидеть 3D превью.", "en": "Generate STL (button on the left) to see 3D preview."},
    "scheme": {"ru": "🖼️ Схема ячейки", "en": "🖼️ Cell Diagram"},
    "metrics": {"ru": "📊 Характеристики", "en": "📊 Metrics"},
    "m_height": {"ru": "Высота модели, мм (A)", "en": "Height, mm (A)"},
    "m_width": {"ru": "Ширина модели, мм (B)", "en": "Width, mm (B)"},
    "m_seff": {"ru": "S_eff=A*B, мм²", "en": "S_eff=A*B, mm²"},
    "m_se": {"ru": "Площадь ячейки, мм² (S_e)", "en": "S_e (cell), mm²"},
    "m_ne": {"ru": "Количество ячеек, N_e", "en": "N_e (cells)"},
    "m_sreal": {"ru": "S_real=S_e*N_e, мм²", "en": "S_real=S_e*N_e, mm²"},
    "m_volume": {"ru": "Объём, мм³ (V=S_real*Z)", "en": "Volume, V=S_real*Z, mm³"},
    "m_mass": {"ru": "Масса, г (m=Ro_real*V)", "en": "Mass, m=Ro_real*V, g"},
    "m_ro_total": {"ru": "Ro_eff=S_real/S_eff, %", "en": "Ro_eff=S_real/S_eff, %"},
    "m_depth": {"ru": "Глубина, мм (Z)", "en": "Depth Z"},
    "m_ro_mat": {"ru": "Плотность, (г/см³) (Ro_real)", "en": "density Ro_real (g/cm³)"},
    "m_poisson": {"ru": "Пуассон по Gibson & Ashby", "en": "Poisson's by Gibson & Ashby"},
    "mm": {"ru": " мм", "en": " mm"},
    "mm2": {"ru": " мм²", "en": " mm²"},
    "mm3": {"ru": " мм³", "en": " mm³"},
    "g": {"ru": " г", "en": " g"},
}

# Инициализация языка в session_state
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'ru'

def t(key):
    """Получить перевод строки по ключу для текущего языка."""
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(st.session_state['lang'], entry.get('ru', key))

# 2. CSS: Верстка
st.markdown("""
    <style>
           .block-container { padding-top: 0.2rem; padding-bottom: 0rem; }
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
           /* Шрифт названия ячеек характеристик */
           .m-label { color: #9ea4b0; font-size: 0.75rem; text-transform: uppercase; line-height: 1.1; margin-bottom: 4px; }
           .m-value { color: #ffffff; font-size: 1.05rem; font-weight: bold; font-family: 'Consolas', monospace; }
           .m-unit { font-size: 0.7rem; color: #5c88be; }

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
# Валидация геометрической корректности ячейки
def validate_cell_geometry(L, S, h, alpha_deg, scale):
    """
    Проверяет элементарную ячейку на самопересечение, вырождение и выходы за рамки здравого смысла.
    Возвращает (is_valid, error_message).
    """
    if alpha_deg <= 0.0 or alpha_deg >= 180.0:
        return False, "Угол Alpha должен быть в пределах от 0° до 180°"
    
    alpha = np.radians(alpha_deg)
    if np.sin(alpha) < 1e-4:
        return False, "Угол Alpha слишком близок к критическому значению (0° или 180°)"
    
    Ls, Ss, hs = L * scale, S * scale, h * scale
    
    # 1. Проверка на то, что наклонное ребро не уходит слишком далеко влево/вправо
    # (Ss * cos(alpha) не должен превосходить Ls)
    if Ss * np.cos(alpha) >= Ls:
        return False, "Самопересечение ребер: длина наклонного ребра S по горизонтали превосходит основание L (Ss*cos(alpha) >= Ls)"
        
    # 2. Проверка расстояния между наклонными ветвями (исключение коллизий при больших толщинах h)
    try:
        points, _ = get_base_unit(L, S, h, alpha_deg, scale)
        poly = Polygon(points)
        if not poly.is_valid:
            from shapely.validation import explain_validity
            reason = explain_validity(poly)
            # Переводим типичные ошибки на понятный русский язык
            reason_ru = reason
            if "Self-intersection" in reason:
                reason_ru = "Пересечение стенок элементарной ячейки (избыточная толщина h или критический угол Alpha)"
            elif "Ring Self-intersection" in reason:
                reason_ru = "Самопересечение внешнего контура ячейки"
            return False, f"Геометрическая коллизия: {reason_ru}"
        return True, ""
    except Exception as e:
        return False, f"Ошибка расчета геометрии: {str(e)}"

@st.cache_data
def get_base_unit(L, S, h, alpha_deg, scale):
    """
    Рассчитывает координаты вершин элементарной ячейки.
    """
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
    return points, (Ls, Ss, hs)

@st.cache_data
def compute_geometry(L, S, h, alpha, scale, target_B, target_A, add_frame, frame_th):
    """
    Генерирует полную сетку структуры с опциональным добавлением внешней рамки.
    Раздельно считает параметры решетки (без рамки) и финальной модели (с рамкой).
    """
    points, scaled = get_base_unit(L, S, h, alpha, scale)
    Ls, Ss, hs = scaled
    alpha_r = np.radians(alpha)
    cx = (Ls - Ss * np.cos(alpha_r)) + (hs/2.0) * np.sin(alpha_r)
    cy = (hs/2.0 + Ss * np.sin(alpha_r)) + (hs/2.0) * np.cos(alpha_r)
    w_step, v_step = 2 * cx, 2 * cy
    nx = max(2, ((int(np.ceil(target_B / w_step)) + 1) // 2) * 2)
    ny = max(1, (int(np.ceil(target_A / v_step)) // 2) * 2 + 1)

    all_units_coords = []
    polygons_lattice = []
    for i in range(nx):
        for j in range(ny):
            u = points.copy()
            if (i + j) % 2 == 0: 
                u[:, 0] = 2 * cx - u[:, 0]
            u[:, 0] += i * w_step
            u[:, 1] += j * v_step
            all_units_coords.append(u)
            polygons_lattice.append(Polygon(u))

    min_x = np.min([np.min(u[:, 0]) for u in all_units_coords])
    max_x = np.max([np.max(u[:, 0]) for u in all_units_coords])
    min_y = np.min([np.min(u[:, 1]) for u in all_units_coords])
    max_y = np.max([np.max(u[:, 1]) for u in all_units_coords])

    f_w_lattice = max_x - min_x
    f_h_lattice = max_y - min_y
    s_eff_lattice = f_w_lattice * f_h_lattice

    # Расчет точной площади только решетки через Shapely
    try:
        union_poly_lattice = unary_union(polygons_lattice)
        s_real_lattice = union_poly_lattice.area
    except Exception as e:
        s_real_lattice = sum(p.area for p in polygons_lattice)

    # Инициализация переменных полной модели
    all_units_out = list(all_units_coords)
    polygons_total = list(polygons_lattice)
    f_w_total = f_w_lattice
    f_h_total = f_h_lattice
    s_eff_total = s_eff_lattice
    s_real_total = s_real_lattice

    if add_frame:
        offset = frame_th / 2.0
        # Сдвиг серединной линии рамки внутрь к серединной линии стенок граничных ячеек.
        # По Y: граничные стенки — наклонные ребра, проекция толщины = hs*cos(alpha).
        # По X: граничные стенки — наклонные ребра, проекция толщины = hs*sin(alpha).
        # Серединная линия стенки отстоит от bbox на половину проекции.
        shift_y = hs * np.cos(alpha_r) / 2.0
        shift_x = hs * np.sin(alpha_r) / 2.0
        
        # Центры рамочных полос смещены внутрь от bbox на shift
        cy_bot = min_y + shift_y   # центр нижней полосы
        cy_top = max_y - shift_y   # центр верхней полосы
        cx_lft = min_x + shift_x   # центр левой полосы
        cx_rgt = max_x - shift_x   # центр правой полосы
        
        in_min_y = cy_bot + offset   # внутренний край нижней полосы
        out_min_y = cy_bot - offset  # наружный край нижней полосы
        in_max_y = cy_top - offset   # внутренний край верхней полосы  
        out_max_y = cy_top + offset  # наружный край верхней полосы
        in_min_x = cx_lft + offset   # внутренний край левой полосы
        out_min_x = cx_lft - offset  # наружный край левой полосы
        in_max_x = cx_rgt - offset   # внутренний край правой полосы
        out_max_x = cx_rgt + offset  # наружный край правой полосы
        
        rect_B = np.array([[out_min_x, out_min_y], [out_max_x, out_min_y], [out_max_x, in_min_y], [out_min_x, in_min_y]])
        rect_T = np.array([[out_min_x, in_max_y], [out_max_x, in_max_y], [out_max_x, out_max_y], [out_min_x, out_max_y]])
        rect_L = np.array([[out_min_x, in_min_y], [in_min_x, in_min_y], [in_min_x, in_max_y], [out_min_x, in_max_y]])
        rect_R = np.array([[in_max_x, in_min_y], [out_max_x, in_min_y], [out_max_x, in_max_y], [in_max_x, in_max_y]])
        
        frame_coords = [rect_B, rect_T, rect_L, rect_R]
        all_units_out.extend(frame_coords)
        for rc in frame_coords:
            polygons_total.append(Polygon(rc))
        
        # Габариты по наружным краям рамки
        f_w_total = out_max_x - out_min_x
        f_h_total = out_max_y - out_min_y
        s_eff_total = f_w_total * f_h_total
        
        try:
            union_poly_total = unary_union(polygons_total)
            s_real_total = union_poly_total.area
        except Exception as e:
            s_real_total = s_real_lattice + sum(Polygon(rc).area for rc in frame_coords)

    n_e = nx * ny

    return (
        all_units_out, 
        s_real_lattice, f_w_lattice, f_h_lattice, s_eff_lattice,
        s_real_total, f_w_total, f_h_total, s_eff_total,
        n_e
    )

@st.cache_data
def generate_stl(all_units, depth):
    """
    Оптимизированная векторизованная генерация STL-сетки.
    Заменяет медленные циклы заполнения и собирает всю модель
    одним numpy-массивом перед инициализацией Mesh.
    """
    all_face_blocks = []
    
    for pts in all_units:
        num_pts = len(pts)
        p_bot = np.hstack([pts, np.zeros((num_pts, 1))])
        p_top = np.hstack([pts, np.full((num_pts, 1), depth)])
        
        # Векторизованное построение боковых граней (2 треугольника на сегмент)
        k_indices = np.arange(num_pts)
        next_k_indices = (k_indices + 1) % num_pts
        
        # Треугольники 1: [bot[k], bot[next], top[next]]
        t1 = np.stack([p_bot[k_indices], p_bot[next_k_indices], p_top[next_k_indices]], axis=1)
        # Треугольники 2: [bot[k], top[next], top[k]]
        t2 = np.stack([p_bot[k_indices], p_top[next_k_indices], p_top[k_indices]], axis=1)
        
        unit_faces = [t1, t2]
        
        # Триангуляция крышек (верхней и нижней) через tripy
        polygon_vertices = [tuple(p) for p in pts]
        try:
            triangles = tripy.earclip(polygon_vertices)
            if triangles:
                tri_arr = np.array(triangles) # shape: (num_triangles, 3, 2)
                
                # Нижняя грань (нормаль вниз, меняем порядок вершин для правильного обхода)
                b_tri = np.zeros((len(triangles), 3, 3))
                b_tri[:, :, :2] = tri_arr[:, [0, 2, 1], :]
                # z-координата = 0
                
                # Верхняя грань (нормаль вверх, стандартный обход)
                t_tri = np.zeros((len(triangles), 3, 3))
                t_tri[:, :, :2] = tri_arr[:, [0, 1, 2], :]
                t_tri[:, :, 2] = depth
                
                unit_faces.append(b_tri)
                unit_faces.append(t_tri)
        except Exception as e:
            pass
            
        all_face_blocks.append(np.concatenate(unit_faces, axis=0))
        
    faces_array = np.concatenate(all_face_blocks, axis=0)
    model = mesh.Mesh(np.zeros(faces_array.shape[0], dtype=mesh.Mesh.dtype))
    model.vectors = faces_array
    
    # Автоматически обновляем векторы нормалей для слайсеров
    model.update_normals()
    return model

# Экспорт структуры в 2D DXF формат для CAD (эскиз)
def generate_dxf_2d(all_units_coords):
    """
    Экспортирует плоский контур решетки в формат 2D DXF как замкнутые полилинии.
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    for pts in all_units_coords:
        points_list = [(p[0], p[1]) for p in pts]
        msp.add_lwpolyline(points_list, close=True)
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode('utf-8')

# Экспорт 3D модели в DXF (поверхностная сетка 3DFACE)
def generate_dxf_3d(stl_mesh):
    """
    Экспортирует 3D модель решетки в DXF в виде 3D-граней (3DFACE).
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    for vector in stl_mesh.vectors:
        v1, v2, v3 = vector[0], vector[1], vector[2]
        # В DXF 3DFACE имеет 4 точки, для треугольника дублируем третью точку
        msp.add_3dface([v1, v2, v3, v3])
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode('utf-8')

def create_3d_plot(stl_mesh):
    vertices = stl_mesh.vectors.reshape(-1, 3)
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
    i = np.arange(0, len(x), 3)
    j = np.arange(1, len(x), 3)
    k = np.arange(2, len(x), 3)
    
    fig = go.Figure(data=[
        go.Mesh3d(
            x=x, y=y, z=z,
            i=i, j=j, k=k,
            color='#5c88be',
            flatshading=True,
            lighting=dict(ambient=0.4, diffuse=0.8, roughness=0.5, specular=0.5, fresnel=0.2),
            lightposition=dict(x=100, y=100, z=100)
        )
    ])
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=600
    )
    return fig

# --- ПЕРЕКЛЮЧАТЕЛЬ ЯЗЫКА ---
_lang_cols = st.columns([5, 1])
with _lang_cols[1]:
    _lang_choice = st.toggle("EN", value=(st.session_state['lang'] == 'en'), key="lang_toggle")
    st.session_state['lang'] = 'en' if _lang_choice else 'ru'

# --- РАСПРЕДЕЛЕНИЕ КОЛОНОК ---
col_params, col_plot, col_metrics = st.columns([1.0, 3.0, 1.2])

# --- ЛЕВАЯ КОЛОНКА (ПАРАМЕТРЫ И КНОПКИ) ---
with col_params:
    st.markdown(f'<div class="section-header">{t("cell_params")}</div>', unsafe_allow_html=True)
    
    def compact_input(label, min_v, max_v, def_v, step, key, help_text=""):
        c1, c2 = st.columns([1.1, 1.0])
        tooltip_attr = f'title="{help_text}"' if help_text else ""
        icon = " ⓘ" if help_text else ""
        c1.markdown(f'<div class="label-col" {tooltip_attr}>{label}{icon}</div>', unsafe_allow_html=True)
        return c2.number_input(label, min_v, max_v, def_v, step, key=key, label_visibility="collapsed")

    L_v = compact_input(t("L_label"), 0.5, 50.0, 3.0, 0.1, "L", t("L_help"))
    S_v = compact_input(t("S_label"), 0.5, 50.0, 1.5, 0.1, "S", t("S_help"))
    h_v = compact_input(t("h_label"), 0.01, 10.0, 0.4, 0.05, "h", t("h_help"))
    a_v = compact_input(t("alpha_label"), 10.0, 170.0, 60.0, 1.0, "alpha", t("alpha_help"))
    sc_v = compact_input("Scale", 0.01, 20.0, 1.0, 0.1, "scale", t("scale_help"))

    st.markdown(f'<div class="section-header">{t("model_params")}</div>', unsafe_allow_html=True)
    target_B = compact_input(t("width_label"), 5.0, 5000.0, 70.0, 1.0, "tB", t("width_help"))
    target_A = compact_input(t("height_label"), 5.0, 5000.0, 40.0, 1.0, "tA", t("height_help"))
    z_depth = compact_input(t("depth_label"), 0.1, 2000.0, 70.0, 1.0, "zD", t("depth_help"))
    ro_real_v = compact_input("Ro_real", 0.01, 20.0, 1.15, 0.01, "ro", t("ro_help"))

    # Секция Рамки
    st.markdown(f'<div class="section-header">{t("frame_section")}</div>', unsafe_allow_html=True)
    add_frame = st.checkbox(t("enable_frame"), value=False)
    frame_th = 0.0
    if add_frame:
        frame_th = compact_input(t("frame_th"), 0.01, 50.0, float(h_v), 0.05, "frame_th", t("frame_th_help"))

    # Валидация геометрических параметров
    is_geom_valid, geom_error = validate_cell_geometry(L_v, S_v, h_v, a_v, sc_v)
    if not is_geom_valid:
        st.error(geom_error)

    # Вычисление геометрии (кэшируется)
    (
        all_units_coords, 
        s_real_lattice, f_w_lattice, f_h_lattice, s_eff_lattice,
        s_real_total, f_w_total, f_h_total, s_eff_total,
        n_e
    ) = compute_geometry(
        L_v, S_v, h_v, a_v, sc_v, target_B, target_A, add_frame, frame_th
    )

    # Выбираем активные размеры и площади в зависимости от включения рамки
    active_w = f_w_total if add_frame else f_w_lattice
    active_h = f_h_total if add_frame else f_h_lattice
    active_s_eff = s_eff_total if add_frame else s_eff_lattice
    active_s_real = s_real_total if add_frame else s_real_lattice

    # Хеш текущих параметров для отслеживания устаревшей 3D-модели
    _param_hash = hash((L_v, S_v, h_v, a_v, sc_v, target_B, target_A, z_depth, add_frame, frame_th))

    st.write("") 
    if st.button(t("btn_generate"), use_container_width=True, disabled=not is_geom_valid):
        with st.spinner(t("generating")):
            stl_mesh = generate_stl(all_units_coords, z_depth)
            stl_buf = io.BytesIO()
            stl_mesh.save("model.stl", fh=stl_buf)
            st.session_state['stl_ready'] = stl_buf.getvalue()
            st.session_state['fig_3d'] = create_3d_plot(stl_mesh)
            st.session_state['stl_param_hash'] = _param_hash
    
    if 'stl_ready' in st.session_state:
        st.download_button(t("btn_download"), st.session_state['stl_ready'], "auxetic.stl", "application/sla", use_container_width=True)

# --- ЦЕНТРАЛЬНАЯ КОЛОНКА ---
with col_plot:
    st.markdown(f'<div class="section-header">{t("structure")}</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs([t("tab_2d"), t("tab_3d")])
    
    with tab1:
        fig = go.Figure()
        x_all, y_all = [], []
        for u in all_units_coords:
            x_all.extend(u[:, 0].tolist() + [u[0, 0]] + [None])
            y_all.extend(u[:, 1].tolist() + [u[0, 1]] + [None])

        fig.add_trace(go.Scatter(
            x=x_all, y=y_all, 
            fill="toself",
            mode="lines",
            line=dict(color='#333333', width=1),
            fillcolor='#5c88be',
            hoverinfo='skip'
        ))

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=True, gridcolor='#3d4455', zeroline=False, scaleanchor="y", scaleratio=1),
            yaxis=dict(showgrid=True, gridcolor='#3d4455', zeroline=False),
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    with tab2:
        if 'fig_3d' in st.session_state:
            if st.session_state.get('stl_param_hash') != _param_hash:
                st.warning(t("3d_stale"))
            st.plotly_chart(st.session_state['fig_3d'], use_container_width=True)
        else:
            st.info(t("3d_empty"))

# --- ПРАВАЯ КОЛОНКА (ХАРАКТЕРИСТИКИ И ПОДПИСЬ) ---
with col_metrics:
    st.markdown(f'<div class="section-header">{t("scheme")}</div>', unsafe_allow_html=True)
    if os.path.exists("scheme.png"): 
        st.image("scheme.png", use_container_width=True)
    
    st.markdown(f'<div class="section-header">{t("metrics")}</div>', unsafe_allow_html=True)
    def metric_card(label, value, unit=""):
        return f'<div class="metric-box"><div class="m-label">{label}</div><div class="m-value">{value}<span class="m-unit">{unit}</span></div></div>'

    # Вычисление производных параметров
    s_e_cell = s_real_lattice / n_e if n_e > 0 else 0       # площадь одной ячейки
    volume_total = s_real_total * z_depth                     # объём материала (мм³)
    sample_mass = volume_total * ro_real_v * 0.001            # масса (г)
    ro_eff_lattice_percent = (s_real_lattice / s_eff_lattice) * 100
    ro_eff_total_percent = (s_real_total / s_eff_total) * 100
    # Оценка коэффициента Пуассона re-entrant структуры (Gibson & Ashby)
    _alpha_r = np.radians(a_v)
    _sin_a = np.sin(_alpha_r)
    _cos_a = np.cos(_alpha_r)
    _ratio = S_v / L_v
    nu_star = -(_cos_a * (1 - _ratio * _cos_a)) / ((_sin_a**2) * _ratio) if abs(_sin_a) > 1e-6 and abs(_ratio) > 1e-6 else 0.0

    # Ряд 1: Линейные размеры и эффективная площадь
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    r1_c1.markdown(metric_card(t("m_height"), f"{active_h:.1f}", t("mm")), unsafe_allow_html=True)
    r1_c2.markdown(metric_card(t("m_width"), f"{active_w:.1f}", t("mm")), unsafe_allow_html=True)
    r1_c3.markdown(metric_card(t("m_seff"), f"{active_s_eff:.0f}", t("mm2")), unsafe_allow_html=True)

    # Ряд 2: Подсчет реальной площади
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    r2_c1.markdown(metric_card(t("m_se"), f"{s_e_cell:.2f}", t("mm2")), unsafe_allow_html=True)
    r2_c2.markdown(metric_card(t("m_ne"), f"{n_e}"), unsafe_allow_html=True)
    r2_c3.markdown(metric_card(t("m_sreal"), f"{s_real_total:.1f}", t("mm2")), unsafe_allow_html=True)

    # Ряд 3: Характеристики модели
    r3_c1, r3_c2, r3_c3 = st.columns(3)
    r3_c1.markdown(metric_card(t("m_volume"), f"{volume_total:.0f}", t("mm3")), unsafe_allow_html=True)
    r3_c2.markdown(metric_card(t("m_mass"), f"{sample_mass:.2f}", t("g")), unsafe_allow_html=True)
    r3_c3.markdown(metric_card(t("m_ro_total"), f"{ro_eff_total_percent:.1f}", "%"), unsafe_allow_html=True)

    # Ряд 4: Дополнительные параметры
    r4_c1, r4_c2, r4_c3 = st.columns(3)
    r4_c1.markdown(metric_card(t("m_depth"), f"{z_depth:.0f}", t("mm")), unsafe_allow_html=True)
    r4_c2.markdown(metric_card(t("m_ro_mat"), f"{ro_real_v:.2f}", " г/см³"), unsafe_allow_html=True)
    r4_c3.markdown(metric_card(t("m_poisson"), f"{nu_star:.3f}"), unsafe_allow_html=True)

    st.markdown('<div class="column-footer">© 2026 Demin A.I. — Laboratory of Mechanics of Novel Materials and Technologies IPMech RAS<br><i>*Optimized by Antigravity v2.0*</i></div>', unsafe_allow_html=True)
