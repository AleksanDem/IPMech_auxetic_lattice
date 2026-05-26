import streamlit as st
import numpy as np
import plotly.graph_objects as go
from stl import mesh
import io
from pathlib import Path
import tripy
from shapely.geometry import Polygon
from shapely.ops import unary_union

# 1. Настройка страницы
st.set_page_config(
    page_title="IPMech Auxetic Tool",
    layout="wide"
)

# --- СИСТЕМА ЛОКАЛИЗАЦИИ (RU / EN) ---
TRANSLATIONS = {
    "cell_params":    {"ru": "⚙️ Параметры ячейки",  "en": "⚙️ Cell Parameters"},
    "model_params":   {"ru": "📦 Параметры модели",   "en": "📦 Model Parameters"},
    "frame_section":  {"ru": "🔳 Рамка",               "en": "🔳 Frame"},
    "enable_frame":   {"ru": "Добавить рамку",          "en": "Add frame"},
    "frame_th":       {"ru": "Толщина рамки, мм",      "en": "Frame thickness, mm"},
    "frame_th_help":  {"ru": "Толщина внешней сплошной рамки по периметру (мм)",
                       "en": "Outer solid frame thickness (mm)"},
    "L_label":        {"ru": "L, мм (Основание)",      "en": "L, mm (Base)"},
    "S_label":        {"ru": "S, мм (Наклон)",         "en": "S, mm (Strut)"},
    "h_label":        {"ru": "h, мм (Толщина)",        "en": "h, mm (Thickness)"},
    "alpha_label":    {"ru": "a (°)",                    "en": "a (°)"},
    "L_help":         {"ru": "Длина горизонтального ребра элементарной ячейки (мм)",
                       "en": "Horizontal rib length of unit cell (mm)"},
    "S_help":         {"ru": "Длина наклонного ребра элементарной ячейки (мм)",
                       "en": "Inclined strut length of unit cell (mm)"},
    "h_help":         {"ru": "Толщина стенок структуры (мм)",  "en": "Wall thickness (mm)"},
    "alpha_help":     {"ru": "Внутренний угол наклона ребер (для ауксетиков < 90°)",
                       "en": "Re-entrant angle (auxetic if < 90°)"},
    "keep_prop_label": {"ru": "Сохранять пропорции",    "en": "Keep proportions"},
    "keep_prop_help":  {"ru": "Связать параметры L, S и h для пропорционального изменения", 
                       "en": "Link L, S, and h for proportional scaling"},
    "ro_label":       {"ru": "Плотность Ro, г/см³",    "en": "Density Ro, g/cm³"},
    "width_label":    {"ru": "Ширина B, мм",            "en": "Width B, mm"},
    "height_label":   {"ru": "Высота A, мм",            "en": "Height A, mm"},
    "depth_label":    {"ru": "Глубина Z, мм",           "en": "Depth Z, mm"},
    "width_help":     {"ru": "Минимальная ширина решетки (мм)",
                       "en": "Target minimum lattice width (mm)"},
    "height_help":    {"ru": "Минимальная высота решетки (мм)",
                       "en": "Target minimum lattice height (mm)"},
    "depth_help":     {"ru": "Глубина (толщина) экструзии по оси Z (мм)",
                       "en": "Extrusion depth along Z axis (mm)"},
    "ro_help":        {"ru": "Физическая плотность материала (г/см³)",
                       "en": "Material density (g/cm³)"},
    "btn_generate":   {"ru": "🛠️ Подготовить STL",    "en": "🛠️ Generate STL"},
    "btn_download":   {"ru": "📥 Скачать STL",         "en": "📥 Download STL"},
    "generating":     {"ru": "Генерация файлов...",    "en": "Generating files..."},
    "structure":      {"ru": "📈 Структура",            "en": "📈 Structure"},
    "tab_2d":         {"ru": "2D Чертёж",              "en": "2D Drawing"},
    "tab_3d":         {"ru": "3D Просмотр",              "en": "3D Preview"},
    "3d_stale":       {"ru": "⚠️ Параметры были изменены. Нажмите '🛠️ Подготовить STL' для обновления 3D модели.",
                       "en": "⚠️ Parameters changed. Click '🛠️ Generate STL' to update the 3D model."},
    "3d_empty":       {"ru": "Сгенерируйте STL (кнопка слева), чтобы увидеть 3D превью.",
                       "en": "Generate STL (button on the left) to see 3D preview."},
    "scheme":         {"ru": "🖼️ Схема ячейки",        "en": "🖼️ Cell Diagram"},
    "metrics":        {"ru": "📊 Характеристики",      "en": "📊 Metrics"},
    "m_height":       {"ru": "Высота А",               "en": "Height A"},
    "m_width":        {"ru": "Ширина B",                "en": "Width B"},
    "m_seff":         {"ru": "S габарита",              "en": "S bound"},
    "m_se":           {"ru": "S ячейки",                "en": "S cell"},
    "m_ne":           {"ru": "Ячеек N",                  "en": "Cells N"},
    "m_sreal":        {"ru": "S структуры",             "en": "S struct"},
    "m_volume":       {"ru": "Объём",                    "en": "Volume"},
    "m_mass":         {"ru": "Масса",                    "en": "Mass"},
    "m_ro_total":     {"ru": "Заполнение",              "en": "Fill ratio"},
    "m_depth":        {"ru": "Глубина Z",               "en": "Depth Z"},
    "m_ro_mat":       {"ru": "Плотность Ro",            "en": "Density Ro"},
    "m_poisson":      {"ru": "Коэфф. Пуассона",         "en": "Poisson's ratio"},
    "rot_label":      {"ru": "Поворот, °",             "en": "Rotation, °"},
    "rot_help":       {"ru": "Угол поворота решётки вокруг левого нижнего угла (0,0) (°, против часовой стрелки)"},
    "rot_section":    {"ru": "🔄 Поворот",              "en": "🔄 Rotation"},
    "mm":             {"ru": " мм",  "en": " mm"},
    "mm2":            {"ru": " мм²", "en": " mm²"},
    "mm3":            {"ru": " мм³", "en": " mm³"},
    "g":              {"ru": " г",   "en": " g"},
    "gcm3":           {"ru": " г/см³", "en": " g/cm³"},
}

# Инициализация языка в session_state
if 'lang_toggle' in st.session_state:
    st.session_state['lang'] = 'en' if st.session_state['lang_toggle'] else 'ru'
elif 'lang' not in st.session_state:
    st.session_state['lang'] = 'ru'

# --- ИНИЦИАЛИЗАЦИЯ И СВЯЗЫВАНИЕ ДИНАМИЧЕСКИХ ПАРАМЕТРОВ ---
if 'L' not in st.session_state:
    st.session_state['L'] = 3.0
if 'S' not in st.session_state:
    st.session_state['S'] = 1.5
if 'h' not in st.session_state:
    st.session_state['h'] = 0.5

# Буферные переменные для отслеживания шага изменений пропорций
if 'prev_L' not in st.session_state:
    st.session_state['prev_L'] = st.session_state['L']
    st.session_state['prev_S'] = st.session_state['S']
    st.session_state['prev_h'] = st.session_state['h']

if 'frame_th' not in st.session_state:
    st.session_state['frame_th'] = st.session_state['h']

# --- ФУНКЦИИ ОБРАТНОГО ВЫЗОВА ДЛЯ КАСКАДНОГО МАСШТАБИРОВАНИЯ ---
def on_L_changed():
    if st.session_state.get('keep_prop', False) and st.session_state['prev_L'] > 0:
        factor = st.session_state['L'] / st.session_state['prev_L']
        st.session_state['S'] = float(np.clip(round(st.session_state['prev_S'] * factor, 3), 0.5, 50.0))
        st.session_state['h'] = float(np.clip(round(st.session_state['prev_h'] * factor, 3), 0.01, 10.0))
    st.session_state['prev_L'] = st.session_state['L']
    st.session_state['prev_S'] = st.session_state['S']
    st.session_state['prev_h'] = st.session_state['h']

def on_S_changed():
    if st.session_state.get('keep_prop', False) and st.session_state['prev_S'] > 0:
        factor = st.session_state['S'] / st.session_state['prev_S']
        st.session_state['L'] = float(np.clip(round(st.session_state['prev_L'] * factor, 3), 0.5, 50.0))
        st.session_state['h'] = float(np.clip(round(st.session_state['prev_h'] * factor, 3), 0.01, 10.0))
    st.session_state['prev_L'] = st.session_state['L']
    st.session_state['prev_S'] = st.session_state['S']
    st.session_state['prev_h'] = st.session_state['h']

def on_h_changed():
    if st.session_state.get('keep_prop', False) and st.session_state['prev_h'] > 0:
        factor = st.session_state['h'] / st.session_state['prev_h']
        st.session_state['L'] = float(np.clip(round(st.session_state['prev_L'] * factor, 3), 0.5, 50.0))
        st.session_state['S'] = float(np.clip(round(st.session_state['prev_S'] * factor, 3), 0.5, 50.0))
    st.session_state['prev_L'] = st.session_state['L']
    st.session_state['prev_S'] = st.session_state['S']
    st.session_state['prev_h'] = st.session_state['h']

# Оставшаяся часть логики t(key) и CSS-стилей
def t(key):
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(st.session_state['lang'], entry.get('ru', key))

st.markdown("""
    <style>
           .block-container {
               padding-top: 0.5rem !important;
               padding-bottom: 0.5rem !important;
               padding-left: 1.5rem !important;
               padding-right: 1.5rem !important;
           }
           header { visibility: hidden; }
           div[data-testid="stVerticalBlock"] { gap: 0.35rem !important; }
           div[data-testid="stHorizontalBlock"] { gap: 0.4rem !important; }
           div[data-testid="stElementContainer"] { margin-bottom: 0px !important; }
           .stTabs [data-baseweb="tab-list"] { gap: 8px !important; }
           .stTabs [data-baseweb="tab"] {
               padding-top: 4px !important;
               padding-bottom: 4px !important;
               font-size: 0.85rem !important;
           }
              div[data-testid="stNumberInputContainer"],
              [data-testid="stNumberInput"] > div {
                  height: 28px !important;
                  min-height: 28px !important;
                  max-height: 28px !important;
                  display: flex !important;
                  align-items: center !important;
              }
              div[data-baseweb="base-input"], 
              div[data-baseweb="input"],
              div[data-testid="stNumberInputContainer"] div[data-baseweb="input"] {
                  height: 28px !important;
                  min-height: 28px !important;
                  max-height: 28px !important;
                  align-items: center !important;
              }
              div[data-testid="stNumberInputContainer"] input,
              .stNumberInput input {
                  margin: 0 !important;
                  height: 28px !important;
                  min-height: 28px !important;
                  max-height: 28px !important;
                  padding-top: 0px !important;
                  padding-bottom: 0px !important;
                  font-size: 0.85rem !important;
                  align-self: center !important;
              }
              div[data-testid="stNumberInputContainer"] button,
              .stNumberInput button,
              [data-testid="stNumberInput"] button {
                  margin: 0 !important;
                  border: none !important;
                  height: 28px !important;
                  min-height: 28px !important;
                  max-height: 28px !important;
                  width: 28px !important;
                  padding: 0px !important;
                  align-self: center !important;
                  display: flex !important;
                  align-items: center !important;
                  justify-content: center !important;
              }
             .section-header {
                 margin-top: 8px !important;
                 margin-bottom: 0px !important;
                 font-size: 0.9rem !important;
                 font-weight: bold;
                 color: #5c88be;
                 border-bottom: 1px solid #464b5d;
                 padding-bottom: 5px;
             }
           .label-col { font-size: 0.85rem; color: #9ea4b0; padding-top: 4px; }
           .metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 10px; }
           .metric-box {
               background-color: #1e2129;
               border: 1px solid #3d4455;
               padding: 4px 2px;
               border-radius: 4px;
               text-align: center;
               min-height: 52px;
               display: flex;
               flex-direction: column;
               justify-content: center;
           }
           .m-label { color: #9ea4b0; font-size: 0.62rem; text-transform: uppercase; line-height: 1.1; margin-bottom: 2px; }
           .m-value { color: #ffffff; font-size: 0.85rem; font-weight: bold; font-family: 'Consolas', monospace; }
           .m-unit { font-size: 0.6rem; color: #5c88be; margin-left: 1px; }
            div[data-testid="stCheckbox"], div[data-testid="stToggle"] {
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                margin-top: 0px !important;
                height: 28px !important;
            }
            .lang-label-ru { font-size: 0.85rem; font-weight: bold; height: 28px; display: flex; align-items: center; justify-content: flex-end; }
            .lang-label-en { font-size: 0.85rem; font-weight: bold; height: 28px; display: flex; align-items: center; justify-content: flex-start; }
           .column-footer { text-align: center; color: #808495; padding-top: 10px; font-size: 0.75rem; border-top: 1px solid #464b5d; margin-top: 10px; }
           .stButton > button { margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ГЕОМЕТРИЧЕСКИЙ БЛОК ---

def validate_cell_geometry(L, S, h, alpha_deg, scale):
    if L <= 0.0 or S <= 0.0 or h <= 0.0 or scale <= 0.0:
        return False, "Параметры L, S, h должны быть строго больше нуля"
    if alpha_deg <= 0.0 or alpha_deg >= 180.0:
        return False, "Угол Alpha должен быть в пределах от 0° до 180°"
    alpha = np.radians(alpha_deg)
    if np.sin(alpha) < 1e-4:
        return False, "Угол Alpha слишком близок к критическому значению (0° или 180°)"
    Ls, Ss, hs = L * scale, S * scale, h * scale
    if Ss * np.cos(alpha) >= Ls:
        return False, "Самопересечение ребер: длина наклонного ребра S по горизонтали превосходит основание L"
    try:
        points, _ = get_base_unit(L, S, h, alpha_deg, scale)
        poly = Polygon(points)
        if not poly.is_valid:
            return False, "Геометрическая коллизия: Самопересечение стенок элементарной ячейки"
        return True, ""
    except Exception as e:
        return False, f"Ошибка расчета геометрии: {str(e)}"

@st.cache_data
def get_base_unit(L, S, h, alpha_deg, scale):
    Ls, Ss, hs = L * scale, S * scale, h * scale
    alpha = np.radians(alpha_deg)
    x1, y1 = 0, hs / 2.0
    x2, y2 = Ls, hs / 2.0
    x3 = Ls - Ss * np.cos(alpha)
    y3 = hs / 2.0 + Ss * np.sin(alpha)
    x4 = x3 + hs * np.sin(alpha)
    y4 = y3 + hs * np.cos(alpha)
    x5 = Ls + (hs * (2 + np.cos(alpha))) / (2 * np.sin(alpha))
    y5 = 0
    top = np.array([[x1, y1], [x2, y2], [x3, y3], [x4, y4], [x5, y5]])
    bottom = np.array([[x4, -y4], [x3, -y3], [x2, -y2], [x1, -y1]])
    points = np.vstack([top, bottom])
    return points, (Ls, Ss, hs)

def _extract_polygon_coords(geom, min_area=1e-4):
    results = []
    if geom is None or geom.is_empty:
        return results
    if geom.geom_type == 'Polygon':
        if geom.area >= min_area:
            coords = np.array(geom.exterior.coords)[:-1]
            if len(coords) >= 3:
                results.append(coords)
    elif geom.geom_type in ('MultiPolygon', 'GeometryCollection'):
        for part in geom.geoms:
            results.extend(_extract_polygon_coords(part, min_area))
    return results

@st.cache_data
def compute_geometry(L, S, h, alpha, scale, target_B, target_A, add_frame, frame_th, rotation=0.0):
    points, scaled = get_base_unit(L, S, h, alpha, scale)
    Ls, Ss, hs = scaled
    alpha_r = np.radians(alpha)
    cx_step = (Ls - Ss * np.cos(alpha_r)) + (hs / 2.0) * np.sin(alpha_r)
    cy_step = (hs / 2.0 + Ss * np.sin(alpha_r)) + (hs / 2.0) * np.cos(alpha_r)
    w_step, v_step = 2 * cx_step, 2 * cy_step

    bounding_rect = Polygon([(0, 0), (target_B, 0), (target_B, target_A), (0, target_A)])
    offset_x = offset_y = 0.0

    r_circ = np.sqrt(target_B ** 2 + target_A ** 2)
    nx = max(4, int(np.ceil((target_B + r_circ) / w_step)) + 2)
    ny = max(4, int(np.ceil((target_A + r_circ) / v_step)) + 2)
    start_x = -int(np.ceil(r_circ / w_step))
    start_y = -int(np.ceil(r_circ / v_step))

    theta = np.radians(rotation)
    cos_t, sin_t = np.cos(theta), np.sin(theta)

    def rotate_around_origin(u):
        rx = u[:, 0] * cos_t - u[:, 1] * sin_t
        ry = u[:, 0] * sin_t + u[:, 1] * cos_t
        return np.column_stack([rx, ry])

    polygons_lattice = []
    n_e_original = 0

    for i in range(start_x, nx):
        for j in range(start_y, ny):
            u = points.copy()
            if (i + j) % 2 == 0:
                u[:, 0] = 2 * cx_step - u[:, 0]
            u[:, 0] += i * w_step + offset_x
            u[:, 1] += j * v_step + offset_y

            if abs(rotation) > 1e-6:
                u = rotate_around_origin(u)

            cell_poly = Polygon(u)
            if not cell_poly.is_valid or cell_poly.is_empty:
                cell_poly = cell_poly.buffer(0)
                if cell_poly.is_empty:
                    continue

            if not bounding_rect.intersects(cell_poly):
                continue

            n_e_original += 1
            clipped = bounding_rect.intersection(cell_poly)
            if not clipped.is_valid:
                clipped = clipped.buffer(0)
                
            if not clipped.is_empty:
                if clipped.geom_type == 'Polygon':
                    polygons_lattice.append(clipped)
                elif clipped.geom_type in ('MultiPolygon', 'GeometryCollection'):
                    for part in clipped.geoms:
                        if part.geom_type == 'Polygon':
                            polygons_lattice.append(part)

    if not polygons_lattice:
        return ([], 0.0, target_B, target_A, target_B * target_A, 0.0, target_B, target_A, target_B * target_A, 0)

    f_w_lattice = target_B
    f_h_lattice = target_A
    s_eff_lattice = f_w_lattice * f_h_lattice
    n_e = n_e_original

    try:
        union_poly_lattice = unary_union(polygons_lattice)
        s_real_lattice = union_poly_lattice.area
    except Exception:
        s_real_lattice = sum(p.area for p in polygons_lattice)

    polygons_total = list(polygons_lattice)
    f_w_total, f_h_total = f_w_lattice, f_h_lattice
    s_eff_total, s_real_total = s_eff_lattice, s_real_lattice

    if add_frame:
        offset = frame_th / 2.0
        out_min_y, in_min_y = -offset, offset
        out_max_y, in_max_y = target_A + offset, target_A - offset
        out_min_x, in_min_x = -offset, offset
        out_max_x, in_max_x = target_B + offset, target_B - offset

        rect_B_arr = np.array([[out_min_x, out_min_y], [out_max_x, out_min_y], [out_max_x, in_min_y],  [out_min_x, in_min_y]])
        rect_T_arr = np.array([[out_min_x, in_max_y],  [out_max_x, in_max_y],  [out_max_x, out_max_y], [out_min_x, out_max_y]])
        rect_L_arr = np.array([[out_min_x, in_min_y],  [in_min_x,  in_min_y],  [in_min_x,  in_max_y],  [out_min_x, in_max_y]])
        rect_R_arr = np.array([[in_max_x,  in_min_y],  [out_max_x, in_min_y],  [out_max_x, in_max_y],  [in_max_x,  in_max_y]])

        frame_polys = [Polygon(rect_B_arr), Polygon(rect_T_arr), Polygon(rect_L_arr), Polygon(rect_R_arr)]
        polygons_total.extend(frame_polys)
        
        s_real_total = s_real_lattice + sum(p.area for p in frame_polys)
        f_w_total = out_max_x - out_min_x
        f_h_total = out_max_y - out_min_y
        s_eff_total = f_w_total * f_h_total

    all_units_out = []
    for p in polygons_total:
        all_units_out.extend(_extract_polygon_coords(p))

    return (all_units_out, s_real_lattice, f_w_lattice, f_h_lattice, s_eff_lattice, s_real_total, f_w_total, f_h_total, s_eff_total, n_e)

@st.cache_data
def generate_stl(all_units, depth):
    if not all_units:
        raise ValueError("Нет геометрии для генерации STL")
    all_face_blocks = []
    for pts in all_units:
        num_pts = len(pts)
        if num_pts < 3: continue
        p_bot = np.hstack([pts, np.zeros((num_pts, 1))])
        p_top = np.hstack([pts, np.full((num_pts, 1), depth)])
        k_indices = np.arange(num_pts)
        next_k_indices = (k_indices + 1) % num_pts
        t1 = np.stack([p_bot[k_indices], p_bot[next_k_indices], p_top[next_k_indices]], axis=1)
        t2 = np.stack([p_bot[k_indices], p_top[next_k_indices], p_top[k_indices]], axis=1)
        unit_faces = [t1, t2]
        polygon_vertices = [tuple(p) for p in pts]
        try:
            triangles = tripy.earclip(polygon_vertices)
            if triangles:
                tri_arr = np.array(triangles)
                b_tri = np.zeros((len(triangles), 3, 3))
                b_tri[:, :, :2] = tri_arr[:, [0, 2, 1], :]
                t_tri = np.zeros((len(triangles), 3, 3))
                t_tri[:, :, :2] = tri_arr[:, [0, 1, 2], :]
                t_tri[:, :, 2] = depth
                unit_faces.append(b_tri)
                unit_faces.append(t_tri)
        except Exception:
            pass
        all_face_blocks.append(np.concatenate(unit_faces, axis=0))

    if not all_face_blocks:
        raise ValueError("STL: не удалось построить ни одного полигона")
    faces_array = np.concatenate(all_face_blocks, axis=0)
    model = mesh.Mesh(np.zeros(faces_array.shape[0], dtype=mesh.Mesh.dtype))
    model.vectors = faces_array
    model.update_normals()
    return model

def create_3d_plot(stl_mesh):
    vertices = stl_mesh.vectors.reshape(-1, 3)
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
    i, j, k = np.arange(0, len(x), 3), np.arange(1, len(x), 3), np.arange(2, len(x), 3)
    fig = go.Figure(data=[go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color='#5c88be', flatshading=True,
                                   lighting=dict(ambient=0.4, diffuse=0.8, roughness=0.5, specular=0.5, fresnel=0.2))])
    fig.update_layout(scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), aspectmode='data'),
                      margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=420)
    return fig

# --- РАСПРЕДЕЛЕНИЕ КОЛОНОК ---
col_params, col_plot, col_metrics = st.columns([1.0, 3.0, 1.2])

# --- ЛЕВАЯ КОЛОНКА (ПАРАМЕТРЫ И КНОПКИ) ---
with col_params:
    st.markdown(f'<div class="section-header">{t("cell_params")}</div><div style="height: 12px;"></div>', unsafe_allow_html=True)

    def compact_input(label, min_v, max_v, step, key, help_text="", on_change=None):
        c1, c2 = st.columns([1.1, 1.0])
        tooltip_attr = f'title="{help_text}"' if help_text else ""
        icon = " ⓘ" if help_text else ""
        c1.markdown(f'<div class="label-col" {tooltip_attr}>{label}{icon}</div>', unsafe_allow_html=True)
        return c2.number_input(label, min_v, max_v, step=step, key=key, on_change=on_change, label_visibility="collapsed")

    # Передача кастомных on_change коллбэков для полей геометрии ячейки
    L_v  = compact_input(t("L_label"),     0.5,   50.0,  0.1,  "L",     t("L_help"),     on_change=on_L_changed)
    S_v  = compact_input(t("S_label"),     0.5,   50.0,  0.1,  "S",     t("S_help"),     on_change=on_S_changed)
    h_v  = compact_input(t("h_label"),    0.01,   10.0,  0.05, "h",     t("h_help"),     on_change=on_h_changed)
    
    c1_a, c2_a = st.columns([1.1, 1.0])
    c1_a.markdown(f'<div class="label-col" title="{t("alpha_help")}">{t("alpha_label")} ⓘ</div>', unsafe_allow_html=True)
    a_v = c2_a.number_input(t("alpha_label"), 10.0, 170.0, 60.0, 1.0, key="alpha", label_visibility="collapsed")

    # Добавление чек-бокса взамен поля "Масштаб"
    keep_prop = st.checkbox(t("keep_prop_label"), value=False, key="keep_prop", help=t("keep_prop_help"))

    st.markdown(f'<div class="section-header">{t("model_params")}</div><div style="height: 12px;"></div>', unsafe_allow_html=True)
    
    c1_w, c2_w = st.columns([1.1, 1.0])
    c1_w.markdown(f'<div class="label-col" title="{t("width_help")}">{t("width_label")} ⓘ</div>', unsafe_allow_html=True)
    target_B = c2_w.number_input(t("width_label"), 5.0, 5000.0, 50.0, 1.0, key="tB", label_visibility="collapsed")

    c1_h, c2_h = st.columns([1.1, 1.0])
    c1_h.markdown(f'<div class="label-col" title="{t("height_help")}">{t("height_label")} ⓘ</div>', unsafe_allow_html=True)
    target_A = c2_h.number_input(t("height_label"), 5.0, 5000.0, 70.0, 1.0, key="tA", label_visibility="collapsed")

    c1_d, c2_d = st.columns([1.1, 1.0])
    c1_d.markdown(f'<div class="label-col" title="{t("depth_help")}">{t("depth_label")} ⓘ</div>', unsafe_allow_html=True)
    z_depth = c2_d.number_input(t("depth_label"), 0.1, 2000.0, 70.0, 1.0, key="zD", label_visibility="collapsed")

    c1_ro, c2_ro = st.columns([1.1, 1.0])
    c1_ro.markdown(f'<div class="label-col" title="{t("ro_help")}">{t("ro_label")} ⓘ</div>', unsafe_allow_html=True)
    ro_real_v = c2_ro.number_input(t("ro_label"), 0.01, 20.0, 1.15, 0.01, key="ro", label_visibility="collapsed")

    c1_rt, c2_rt = st.columns([1.1, 1.0])
    c1_rt.markdown(f'<div class="label-col" title="{t("rot_help")}">{t("rot_section")} ⓘ</div>', unsafe_allow_html=True)
    rot_v = c2_rt.number_input(t("rot_label"), -180.0, 180.0, 0.0, 1.0, key="rot", label_visibility="collapsed")

    add_frame = st.checkbox(t("enable_frame"), value=True)
    frame_th = 0.0
    if add_frame:
        frame_th = compact_input(t("frame_th"), 0.01, 50.0, 0.05, "frame_th", t("frame_th_help"))

    # Валидация. Глобальный масштаб теперь жестко равен 1.0
    is_geom_valid, geom_error = validate_cell_geometry(L_v, S_v, h_v, a_v, 1.0)
    if is_geom_valid:
        if target_B <= 0.0 or target_A <= 0.0 or z_depth <= 0.0 or ro_real_v <= 0.0:
            is_geom_valid = False
            geom_error = "Параметры ширины, высоты, глубины и плотности должны быть больше нуля"
        elif add_frame and frame_th <= 0.0:
            is_geom_valid = False
            geom_error = "Толщина рамки должна быть больше нуля"

    if not is_geom_valid:
        st.error(geom_error)

    # Генерация сетки
    if is_geom_valid:
        all_units_coords, s_real_lattice, f_w_lattice, f_h_lattice, s_eff_lattice, s_real_total, f_w_total, f_h_total, s_eff_total, n_e = compute_geometry(
            L_v, S_v, h_v, a_v, 1.0, target_B, target_A, add_frame, frame_th, rot_v
        )
    else:
        all_units_coords, s_real_lattice = [], 0.0
        f_w_lattice = f_h_lattice = s_eff_lattice = s_real_total = f_w_total = f_h_total = s_eff_total = 0.0
        n_e = 0

    active_w     = f_w_total     if add_frame else f_w_lattice
    active_h     = f_h_total     if add_frame else f_h_lattice
    active_s_eff = s_eff_total   if add_frame else s_eff_lattice
    active_s_real = s_real_total if add_frame else s_real_lattice

    _param_hash = hash((L_v, S_v, h_v, a_v, float(keep_prop), target_B, target_A, z_depth, add_frame, frame_th, rot_v))

    st.write("")
    if st.button(t("btn_generate"), use_container_width=True, disabled=(not is_geom_valid or not all_units_coords)):
        with st.spinner(t("generating")):
            try:
                stl_mesh = generate_stl(all_units_coords, z_depth)
                stl_buf = io.BytesIO()
                stl_mesh.save("auxetic.stl", fh=stl_buf)
                st.session_state['stl_ready'] = stl_buf.getvalue()
                st.session_state['fig_3d'] = create_3d_plot(stl_mesh)
                st.session_state['stl_param_hash'] = _param_hash
            except Exception as e:
                st.error(f"Ошибка генерации STL: {e}")

    if 'stl_ready' in st.session_state:
        st.download_button(t("btn_download"), st.session_state['stl_ready'], "auxetic.stl", "application/sla", use_container_width=True)

# --- ЦЕНТРАЛЬНАЯ КОЛОНКА ---
with col_plot:
    st.markdown(f'<div class="section-header">{t("structure")}</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs([t("tab_2d"), t("tab_3d")])

    with tab1:
        fig = go.Figure()
        bx, by = [0, target_B, target_B, 0, 0], [0, 0, target_A, target_A, 0]
        fig.add_trace(go.Scatter(x=bx, y=by, mode='lines', line=dict(color='#ff6b6b', width=1.5, dash='dash'), name='boundary', hoverinfo='skip'))

        for u in all_units_coords:
            fig.add_trace(go.Scatter(x=u[:, 0].tolist() + [u[0, 0]], y=u[:, 1].tolist() + [u[0, 1]], fill="toself", mode="lines",
                                     line=dict(color='#111111', width=0.8), fillcolor='#5c88be', hoverinfo='skip'))

        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
                           xaxis=dict(showgrid=True, gridcolor='#3d4455', zeroline=False, scaleanchor="y", scaleratio=1),
                           yaxis=dict(showgrid=True, gridcolor='#3d4455', zeroline=False), height=420)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with tab2:
        if 'fig_3d' in st.session_state:
            if st.session_state.get('stl_param_hash') != _param_hash:
                st.warning(t("3d_stale"))
            st.plotly_chart(st.session_state['fig_3d'], use_container_width=True)
        else:
            st.info(t("3d_empty"))

# --- ПРАВАЯ КОЛОНКА (ХАРАКТЕРИСТИКИ) ---
with col_metrics:
    hdr_cols = st.columns([1.5, 2.0])
    with hdr_cols[0]:
        st.markdown(f'<div class="section-header" style="border-bottom:none; margin:0; padding:0; line-height:2.2;">{t("metrics")}</div>', unsafe_allow_html=True)
    with hdr_cols[1]:
        lang_cols = st.columns([1.2, 1.0, 1.2])
        is_en = (st.session_state.get('lang', 'ru') == 'en')
        ru_color = "#ffffff" if not is_en else "#6f7380"
        en_color = "#ffffff" if is_en else "#6f7380"
        with lang_cols[0]: st.markdown(f'<div class="lang-label-ru" style="color: {ru_color};">рус</div>', unsafe_allow_html=True)
        with lang_cols[1]: st.toggle("", value=is_en, key="lang_toggle", label_visibility="collapsed")
        with lang_cols[2]: st.markdown(f'<div class="lang-label-en" style="color: {en_color};">EN</div>', unsafe_allow_html=True)
    st.markdown('<div style="border-bottom: 1px solid #464b5d; margin-top: 2px; margin-bottom: 12px;"></div>', unsafe_allow_html=True)

    def metric_card(label, value, unit="", tooltip="", style=""):
        tooltip_attr = f' title="{tooltip}"' if tooltip else ''
        style_attr = f' style="{style}"' if style else ''
        return (f'<div class="metric-box"{tooltip_attr}{style_attr}>'
                f'<div class="m-label">{label}</div>'
                f'<div class="m-value">{value}<span class="m-unit">{unit}</span></div>'
                f'</div>')

    s_e_cell = s_real_lattice / n_e if n_e > 0 else 0
    volume_total = s_real_total * z_depth
    sample_mass = volume_total * ro_real_v * 0.001
    ro_eff_total_percent = (s_real_total / s_eff_total * 100) if s_eff_total > 0 else 0

    _alpha_r = np.radians(a_v)
    _sin_a, _cos_a = np.sin(_alpha_r), np.cos(_alpha_r)
    _ratio = S_v / L_v
    nu_star = (-(_cos_a * (1 - _ratio * _cos_a)) / ((_sin_a ** 2) * _ratio) if abs(_sin_a) > 1e-6 and abs(_ratio) > 1e-6 else 0.0)

    metrics_list = [
        metric_card(t("m_height"), f"{active_h:.1f}", t("mm")),
        metric_card(t("m_width"),  f"{active_w:.1f}", t("mm")),
        metric_card(t("m_seff"),   f"{active_s_eff:.0f}", t("mm2")),
        metric_card(t("m_se"),     f"{s_e_cell:.2f}", t("mm2")),
        metric_card(t("m_ne"),     f"{n_e}", ""),
        metric_card(t("m_sreal"),  f"{s_real_total:.1f}", t("mm2")),
        metric_card(t("m_volume"), f"{volume_total:.0f}", t("mm3")),
        metric_card(t("m_mass"),   f"{sample_mass:.2f}", t("g")),
        metric_card(t("m_ro_total"), f"{ro_eff_total_percent:.1f}", "%"),
        metric_card(t("m_depth"),   f"{z_depth:.0f}", t("mm")),
        metric_card(t("m_ro_mat"),  f"{ro_real_v:.2f}", t("gcm3")),
        metric_card(t("m_poisson"), f"{nu_star:.3f}", "")
    ]
    st.markdown('<div class="metrics-grid">' + "".join(metrics_list) + '</div>', unsafe_allow_html=True)

    _scheme_path = Path(__file__).parent / "scheme.png"
    if _scheme_path.exists():
        st.markdown(f'<div class="section-header">{t("scheme")}</div><div style="height: 8px;"></div>', unsafe_allow_html=True)
        st.image(str(_scheme_path), use_container_width=True)

    st.markdown('<div class="column-footer">© 2026 Demin A.I. — Laboratory of Mechanics of Novel Materials and Technologies IPMech RAS</div>', unsafe_allow_html=True)
