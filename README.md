# IPMech_RAS_auxetic_lattice

### Parametric Generator of 2D/3D Re-entrant Auxetic Structures

This project provides an interactive tool and a Python-based mathematical framework for designing, analyzing, and exporting **auxetic metamaterials** (specifically re-entrant honeycomb structures). Developed at the **Ishlinsky Institute for Problems in Mechanics of the Russian Academy of Sciences (IPMech RAS)**.

---

## 🔬 Scientific Context
Auxetic materials are characterized by a **negative Poisson's ratio** ($\nu^* < 0$). Unlike conventional materials, they expand laterally when stretched and contract when compressed. This repository focuses on the "re-entrant honeycomb" geometry, widely used in aerospace, medical implants, smart sensors, and impact-absorption systems.

The tool includes an analytical estimation of the effective Poisson's ratio for the re-entrant structure based on the classical **Gibson & Ashby model**:
$$\nu^* = -\frac{\cos\alpha \cdot (1 - \frac{S}{L}\cos\alpha)}{\frac{S}{L} \cdot \sin^2\alpha}$$

---

## 🚀 Key Features

* **Interactive Web UI**: Built with Streamlit, featuring a real-time bilingual switch (**Russian / English**).
* **High-Performance STL Generation**: Optimized with vectorized NumPy mesh generation for instant STL preparation of large lattices (reduces computation time by up to 50x).
* **Topological Validation**: Real-time geometric integrity checks using `shapely` to prevent self-intersections or degenerate cells.
* **Intelligent Tessellation**: Automatic cell generation with an even number of columns and an odd number of rows to guarantee structural symmetry.
* **Precise Boundary Overlap (Frame)**: Smart frame centerline alignment passing through the mid-line of the boundary struts to eliminate gaps at sharp corners.
* **Stale View Detector**: Interactive 3D visualization that warns the user if parameters have been updated and a new STL needs to be generated.
* **Comprehensive Metrics**: Logical layout of dimensions, cell/lattice areas, volume, mass, and effective density.

---

## ⚙️ Geometric & Model Parameters

### Cell Parameters (Параметры ячейки)
* **L**: Horizontal base rib length (мм / mm)
* **S**: Inclined strut rib length (мм / mm)
* **h**: Wall thickness (мм / mm)
* **Alpha ($\alpha$)**: Re-entrant angle (градусы / degrees)
* **Scale**: Global scaling factor applied to all dimensions

### Model Parameters (Параметры модели)
* **Width B**: Minimum target model width (мм / mm)
* **Height A**: Minimum target model height (мм / mm)
* **Depth Z**: Extrusion depth (мм / mm)
* **Ro_real**: True density of the material (г/см³ / g/cm³)

### Frame (Рамка)
* **Add frame**: Adds a solid rectangular frame around the structure
* **Frame thickness**: Thickness of the solid frame (defaults to cell wall thickness $h$)

---

## 📊 Output Metrics Layout

The dashboard organizes engineering metrics into four rows:
1. **Dimensions**: Height (A), Width (B), and Effective Bounding Area ($S_{eff} = A \times B$).
2. **Areas**: Individual cell area ($S_e$), total cell count ($N_e$), and total exact area of the solid structure ($S_{real} = S_e \times N_e$).
3. **Physical Properties**: Volume ($V = S_{real} \times Z$), Mass ($m = \rho_{real} \times V$), and Relative Density ($Ro_{eff} = S_{real} / S_{eff}$).
4. **Additional Parameters**: Depth ($Z$), Material density ($\rho_{real}$), and Analytical Poisson's Ratio ($\nu^*$) by Gibson & Ashby.

---

## 💻 Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AleksanDem/IPMeech_auxetic_lattice.git
   cd IPMeech_auxetic_lattice
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

---

## 📦 Requirements
* `streamlit`
* `numpy`
* `plotly`
* `numpy-stl`
* `shapely`
* `tripy`
* `ezdxf`

---

## 👨‍💻 Developer
**A.I. Demin**  
Ishlinsky Institute for Problems in Mechanics of the Russian Academy of Sciences (IPMech RAS)  
*Leading Engineer*

## 📜 License
This project is developed for research and engineering automation purposes. All rights reserved.
