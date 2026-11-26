<p align="center">
  <img src="commentarium_logo.svg" width="96" alt="CommentariuM logo">
</p>

<h1 align="center">CommentariuM</h1>

<p align="center">
  An A4 mathematical notebook for engineering calculations: live math, units, a symbolic solver,
  tables, plots and drawings on graph paper, exported to vector PDF.
</p>

---

CommentariuM is a desktop worksheet in the spirit of SMath Studio and Mathcad, written in Python and GTK 3.
You type math in a 2D editor anywhere on the page. The whole sheet recalculates from top to bottom as you edit.
Text, tables, plots, pictures and drawings sit next to the calculations, so one page holds the full calculation note.

<p align="center">
  <img src="docs/feature-tour.png" width="640" alt="One-page feature tour worksheet">
  <br><em>The feature tour worksheet (<code>CommentariuM feature tour.cmm.json</code>) exported to PDF</em>
</p>

## Features

### Math
- 2D equation editor with fractions (`/`), powers (`^`), subscripts (`_`), roots (`\`), Σ, ∫, vectors and dot-derivatives (ẋ).
- One `=` either defines (`a = 5`) or evaluates (`a =`). You can define functions: `f(x) = x² + a`.
- Greek letters by name (`alpha` → α), a chosen number of decimal places per result, and boxed equations.
- Notes on equations, shown on hover, like Excel cell comments.

### Units
- Type an apostrophe and a unit after a number: `5'kW`, `2.5'mm`, `20'°C`, `3'm/'s`.
- Units are drawn in their own colour, and unknown units are drawn in red.
- Covers the basic SI units with prefixes: m, g, s, min, h, day, K, °C, A, mol, cd, N, J, Wh, cal, W, Pa, bar, atm, Hz, C, V, Ω, F, H, T, Wb, L, rad and deg.
- Each result is shown in the best-matching derived unit (W, J, Pa, W/(m·K) …). You can also ask for a specific unit: `E = P·t = 'kWh`.
- Unit mismatches are reported on the sheet (`m + s`, `sin(5'm)` …).

### Equations and the solver
- Write equations with `==` (`q == h·(T_s − T_a)`).
- Right-click → **Solve for** rearranges an equation symbolically (SymPy) and falls back to a numeric solution.
- Right-click → **Substitute** replaces a variable using another equation.

### Tables, plots and figures
- Tables whose columns can be used in calculations: `T1(2,3)`, `mean(y_m)`.
- You can paste data from a spreadsheet straight into a table.
- 2D plots of functions and data.
- Pictures from the clipboard or from files.
- Drawings built from shapes, including electrical symbols. Drawings can be resized and cropped, and outlines and fills are set separately.
- Figures, tables and headings are numbered automatically, and a table of contents is built from the headings.

### Engineering tools
| Tool | What it does |
|---|---|
| Curve Fit | Fits model coefficients to data vectors. It inserts the coefficients, the fitted function and a plot. |
| Unit Converter | Converts between SI and English units. |
| Fluid Properties | Gives ρ, c<sub>p</sub>, ν, α, k, μ and Pr for air (100–3000 K) and water (273–600 K). These are also available as sheet functions such as `cp_water(300'K)`. |
| Thermal Spreading | Computes the Lee–Song–Au spreading resistance of a heat source on a plate. |
| Thermal Contact | Computes contact conductance with the Cooper–Mikic–Yovanovich model plus the air gap. |
| Plot Digitizer | Picks data points off a picture of a graph and inserts them as a table and a plot. |

The theory behind the thermal and fluid tools is in [`docs/`](docs).

### Worksheet
- A4 pages on graph paper, in dark and light themes.
- Undo and redo (100 steps), zoom, and full screen (F11).
- Worksheets are saved as JSON (`*.cmm.json`).
- Export to a vector PDF with live links (Ctrl+E).

## Requirements

- Python 3.10+
- GTK 3 with PyGObject and pycairo
- SymPy (solver), NumPy and SciPy (curve fitting and plots)

On Debian or Ubuntu:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-cairo
pip install sympy numpy scipy
```

On Fedora:

```bash
sudo dnf install python3-gobject python3-cairo gtk3
pip install sympy numpy scipy
```

## Running

```bash
python3 CommentariuM.py                                  # new worksheet
python3 CommentariuM.py "CommentariuM feature tour.cmm.json"   # open a worksheet
```

## Quick start

1. Click on the page to place the red cursor, then start typing math: `P = 2.5'kW`.
2. On a new line, type `t = 90'min`. Then type `E = P·t = 'kWh` and the result appears as **3.75 kWh**.
3. Right-click an equation such as `q == h·(T_s − T_a)` and choose **Solve for → T_s**.
4. Use **Insert** for text, tables, plots, pictures and drawings, and **Tools** for the engineering calculators.
5. Press **Ctrl+E** to export the sheet as a PDF.

The **About** dialog lists every feature and keyboard shortcut.

## Keyboard shortcuts

| Keys | Action |
|---|---|
| Ctrl+Z / Ctrl+Y | Undo / redo |
| Ctrl+ + / Ctrl+ − | Zoom |
| Ctrl+E | Export to PDF |
| Ctrl+V | Paste a picture or table data |
| Ctrl+B / Ctrl+U | Bold / underline in text boxes |
| Arrow keys | Move selected objects (Shift: larger steps) |
| F11 | Full screen |

## Example worksheets

- `CommentariuM feature tour.cmm.json`: a one-page tour of the main features.
- `finned heat exchanger model.json`
- `curve fitting to data.json`
