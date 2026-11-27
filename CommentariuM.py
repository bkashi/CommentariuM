import os
import sys
import math
import unicodedata
import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Gdk, GLib, GObject, Pango, PangoCairo


GREEK_AUTOCOMPLETE = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "Delta": "Δ",
    "epsilon": "ε",
    "zeta": "ζ",
    "eta": "η",
    "theta": "θ",
    "Theta": "Θ",
    "kappa": "κ",
    "lambda": "λ",
    "Lambda": "Λ",
    "mu": "μ",
    "nu": "ν",
    "xi": "ξ",
    "pi": "π",
    "Pi": "Π",
    "rho": "ρ",
    "sigma": "σ",
    "Sigma": "Σ",
    "tau": "τ",
    "phi": "φ",
    "Phi": "Φ",
    "chi": "χ",
    "psi": "ψ",
    "Psi": "Ψ",
    "omega": "ω",
    "Omega": "Ω",
    "inf": "∞",
}


THEMES = {
    "dark": {
        "desk_bg": (0.07, 0.08, 0.09),
        "page_shadow": (0.0, 0.0, 0.0, 0.55),
        "page_border": (0.32, 0.36, 0.42),
        "margin_guide": (0.26, 0.30, 0.36),
        "canvas_bg": (0.12, 0.13, 0.15),
        "grid_minor": (0.18, 0.20, 0.23),
        "grid_major": (0.24, 0.27, 0.32),
        "title_text": (0.98, 0.99, 1.00),
        "heading_text": (0.58, 0.80, 0.98),
        "text": (0.90, 0.92, 0.95),
        "muted_text": (0.52, 0.57, 0.65),
        "operator": (0.45, 0.75, 0.98),
        "result": (0.42, 0.85, 0.55),
        "error": (0.95, 0.40, 0.40),
        "placeholder_fill": (0.22, 0.25, 0.30),
        "placeholder_border": (0.45, 0.50, 0.58),
        "box_editing_bg": (0.16, 0.18, 0.22, 0.92),
        "box_selected_border": (0.34, 0.61, 0.84),
        "box_editing_border": (0.40, 0.72, 0.98),
        "cursor": (0.98, 0.80, 0.25),
        "unit": (0.80, 0.60, 0.98),
    },
    "light": {
        "desk_bg": (0.70, 0.72, 0.75),
        "page_shadow": (0.0, 0.0, 0.0, 0.25),
        "page_border": (0.52, 0.56, 0.62),
        "margin_guide": (0.72, 0.78, 0.86),
        "canvas_bg": (0.90, 0.90, 0.89),
        "grid_minor": (0.82, 0.84, 0.87),
        "grid_major": (0.72, 0.77, 0.83),
        "title_text": (0.05, 0.12, 0.24),
        "heading_text": (0.08, 0.30, 0.62),
        "text": (0.10, 0.12, 0.16),
        "muted_text": (0.48, 0.53, 0.60),
        "operator": (0.05, 0.35, 0.75),
        "result": (0.08, 0.52, 0.22),
        "error": (0.80, 0.15, 0.15),
        "placeholder_fill": (0.84, 0.86, 0.90),
        "placeholder_border": (0.55, 0.62, 0.72),
        "box_editing_bg": (0.94, 0.94, 0.93, 0.92),
        "box_selected_border": (0.15, 0.48, 0.82),
        "box_editing_border": (0.10, 0.42, 0.85),
        "cursor": (0.85, 0.15, 0.15),
        "unit": (0.50, 0.18, 0.64),
    },
}


# PDF export keeps classic white paper, whatever the on-screen light paper tint is.
THEMES["print"] = dict(
    THEMES["light"],
    canvas_bg=(0.99, 0.99, 0.98),
    grid_minor=(0.89, 0.92, 0.95),
    grid_major=(0.78, 0.84, 0.90),
    placeholder_fill=(0.90, 0.92, 0.96),
    box_editing_bg=(1.0, 1.0, 1.0, 0.92),
)


TEXT_STYLES = {
    "title": {
        "label": "Title",
        "font": "Ubuntu, DejaVu Sans, sans-serif Bold 32",
        "color_key": "title_text",
        "underline_bar": True,
        "centered": True,
    },
    "subtitle": {
        "label": "Subtitle",
        "font": "Ubuntu, DejaVu Sans, sans-serif 14",
        "color_key": "heading_text",
        "underline_bar": False,
        "centered": True,
    },
    "heading1": {
        "label": "Heading 1",
        "font": "Ubuntu, DejaVu Sans, sans-serif Bold 18",
        "color_key": "heading_text",
        "underline_bar": False,
    },
    "heading2": {
        "label": "Heading 2",
        "font": "Ubuntu, DejaVu Sans, sans-serif Bold 15",
        "color_key": "heading_text",
        "underline_bar": False,
    },
    "heading3": {
        "label": "Heading 3",
        "font": "Ubuntu, DejaVu Sans, sans-serif Bold Italic 13",
        "color_key": "heading_text",
        "underline_bar": False,
    },
    "normal": {
        "label": "Normal",
        "font": "Ubuntu, DejaVu Sans, sans-serif 12",
        "color_key": "text",
        "underline_bar": False,
    },
}


# Headings are numbered automatically (1, 1.1, 1.1.1) and sit at a fixed
# indentation per level (x position on the page); they can only be dragged up/down.
HEADING_LEVELS = {"heading1": 1, "heading2": 2, "heading3": 3}
# Title and subtitle also have a fixed x: they span the page width and are centered.
HEADING_X = {"title": 40, "subtitle": 40, "heading1": 40, "heading2": 60, "heading3": 80}
# Multi-line text boxes: distance between baselines = 1.5 × the font size
TEXT_LINE_SPACING = 1.5


def line_spacing_factor(pango_ctx, font_desc, lines=TEXT_LINE_SPACING) -> float:
    """Pango spaces lines at factor × the font's own line height (which for most fonts is
    already ~1.2 × the font size); convert 'lines' (in font sizes) into that factor."""
    try:
        metrics = pango_ctx.get_metrics(font_desc, None)
        height = metrics.get_height()
        size = font_desc.get_size()
        if not font_desc.get_size_is_absolute():
            dpi = PangoCairo.context_get_resolution(pango_ctx)
            size = size * ((dpi if dpi and dpi > 0 else 96.0) / 72.0)
        if height > 0 and size > 0:
            return max(0.5, lines * size / height)
    except Exception:
        pass
    return lines


def strip_manual_heading_number(text: str) -> str:
    """'1.2 Geometry' -> 'Geometry' (headings are numbered automatically now)."""
    import re
    rest = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s+", "", text, count=1)
    return rest if rest.strip() else text


# ============================================================================
# 2D Equation AST Model (SMath Studio / Mathcad / MS Equation style)
# ============================================================================


class MathSeq:
    """A horizontal sequence of MathNode items, with layout metrics (width, ascent, descent)."""

    def __init__(self, parent_node=None):
        self.parent_node = parent_node
        self.items = []
        # Layout metrics computed during measure()
        self.width = 0.0
        self.ascent = 0.0
        self.descent = 0.0
        self.scale = 1.0
        # Absolute coordinates inside the MathBox for mouse hit-testing
        self.abs_x = 0.0
        self.abs_y = 0.0
        self.caret_positions = []  # x offsets for index 0..len(items)
        # (item index, width): room left after that item for a result shown in a chosen unit
        # (E = P·t = [15] kWh); set by MathBox on its root only
        self.result_gap = None
        self.result_gap_x = 0.0

    @property
    def height(self):
        return self.ascent + self.descent

    def insert(self, index, node):
        node.parent_seq = self
        self.items.insert(index, node)

    def append(self, node):
        node.parent_seq = self
        self.items.append(node)

    def is_empty(self):
        return len(self.items) == 0


class MathNode:
    """Base class for an element inside a MathSeq."""

    def __init__(self):
        self.parent_seq = None
        self.width = 0.0
        self.ascent = 0.0
        self.descent = 0.0
        self.abs_x = 0.0
        self.abs_y = 0.0

    @property
    def height(self):
        return self.ascent + self.descent

    def slots(self):
        return []


class CharNode(MathNode):
    """A single character or multi-char operator token (e.g. 'x', '2', '+', ':=', 'π')."""

    def __init__(self, text):
        super().__init__()
        self.text = text

    def is_operator(self):
        return self.text in ("+", "-", "·", ":=", "=", "==", "<", ">", "≤", "≥", "≠", ",")


# Dot above a letter (Newton's notation for a time derivative: ẋ, Q̇, θ̇). Stored as the
# letter plus a combining dot, so it stays one character/identifier everywhere.
DOT_ABOVE = "\u0307"


def tok_base(t: str) -> str:
    """Token without combining accents ('ẋ' -> 'x')."""
    return "".join(c for c in unicodedata.normalize("NFD", t) if not unicodedata.combining(c))


def tok_is_letter(t: str) -> bool:
    b = tok_base(t)
    return len(b) == 1 and b.isalpha()


def tok_is_alnum(t: str) -> bool:
    b = tok_base(t)
    return len(b) == 1 and b.isalnum() if b != t else t.isalnum()


def tok_has_dot(t: str) -> bool:
    return DOT_ABOVE in unicodedata.normalize("NFD", t)


def tok_toggle_dot(t: str) -> str:
    if tok_has_dot(t):
        return unicodedata.normalize("NFC", unicodedata.normalize("NFD", t).replace(DOT_ABOVE, ""))
    return unicodedata.normalize("NFC", t + DOT_ABOVE)


def split_letters(s: str) -> list:
    """Split a name into characters, keeping combining accents with their letter."""
    out = []
    for c in unicodedata.normalize("NFD", s):
        if unicodedata.combining(c) and out:
            out[-1] += c
        else:
            out.append(c)
    return [unicodedata.normalize("NFC", c) for c in out]


class FracNode(MathNode):
    """2D vertical stacked fraction: num / den."""

    def __init__(self, num=None, den=None):
        super().__init__()
        self.num = num if num is not None else MathSeq(self)
        self.den = den if den is not None else MathSeq(self)
        self.num.parent_node = self
        self.den.parent_node = self

    def slots(self):
        return [self.num, self.den]


class SupNode(MathNode):
    """Superscript / Exponent box."""

    def __init__(self, exp=None):
        super().__init__()
        self.exp = exp if exp is not None else MathSeq(self)
        self.exp.parent_node = self

    def slots(self):
        return [self.exp]


class SubNode(MathNode):
    """Subscript box."""

    def __init__(self, sub=None):
        super().__init__()
        self.sub = sub if sub is not None else MathSeq(self)
        self.sub.parent_node = self

    def slots(self):
        return [self.sub]


class SqrtNode(MathNode):
    """Square root / N-th root with dynamic radical symbol."""

    def __init__(self, radicand=None, degree=None):
        super().__init__()
        self.radicand = radicand if radicand is not None else MathSeq(self)
        self.radicand.parent_node = self
        self.degree = degree
        if self.degree is not None:
            self.degree.parent_node = self

    def slots(self):
        if self.degree is not None:
            return [self.degree, self.radicand]
        return [self.radicand]


class ParenNode(MathNode):
    """Auto-scaling parentheses around an inner sequence."""

    def __init__(self, inner=None):
        super().__init__()
        self.inner = inner if inner is not None else MathSeq(self)
        self.inner.parent_node = self

    def slots(self):
        return [self.inner]


class SumNode(MathNode):
    """2D Summation operator ∑ with lower limit, upper limit, and body."""

    def __init__(self, lower=None, upper=None, body=None):
        super().__init__()
        self.lower = lower if lower is not None else MathSeq(self)
        self.upper = upper if upper is not None else MathSeq(self)
        self.body = body if body is not None else MathSeq(self)
        self.lower.parent_node = self
        self.upper.parent_node = self
        self.body.parent_node = self

    def slots(self):
        return [self.lower, self.upper, self.body]


class IntNode(MathNode):
    """2D Definite/Indefinite Integral ∫ with lower limit, upper limit, integrand, and d-variable."""

    def __init__(self, lower=None, upper=None, body=None, var=None):
        super().__init__()
        self.lower = lower if lower is not None else MathSeq(self)
        self.upper = upper if upper is not None else MathSeq(self)
        self.body = body if body is not None else MathSeq(self)
        self.var = var if var is not None else MathSeq(self)
        self.lower.parent_node = self
        self.upper.parent_node = self
        self.body.parent_node = self
        self.var.parent_node = self

    def slots(self):
        return [self.lower, self.upper, self.body, self.var]


_MODIFIER_KEYS = {"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Meta_L", "Meta_R",
                  "Super_L", "Super_R", "Caps_Lock", "Shift_Lock", "ISO_Level3_Shift", "ISO_Level5_Shift",
                  "Mode_switch", "ISO_Next_Group", "ISO_Prev_Group", "Num_Lock", "Hyper_L", "Hyper_R"}


class UnitNode(MathNode):
    """A measurement unit ('m, 'kW, '°C …), typed with an apostrophe and drawn upright in
    the unit colour. It is one atom: 5'kW means 5 · kW."""

    def __init__(self, name=""):
        super().__init__()
        self.name = name


# ============================================================================
# Layout & Cairo Renderer for 2D Equations
# ============================================================================


class MathRenderer:
    BASE_FONT_SIZE = 15.0  # pt

    @classmethod
    def _make_layout(cls, pango_ctx, text, scale=1.0, italic=False, bold=False):
        layout = Pango.Layout.new(pango_ctx)
        font_size = max(8.0, cls.BASE_FONT_SIZE * scale)
        style_str = "Italic " if italic else ""
        weight_str = "Bold " if bold else ""
        desc = Pango.FontDescription.from_string(
            f"Times New Roman, Liberation Serif, TeX Gyre Termes, DejaVu Serif, serif {style_str}{weight_str}{font_size:.1f}"
        )
        layout.set_font_description(desc)
        layout.set_text(text, -1)
        ink, logical = layout.get_pixel_extents()
        baseline = layout.get_baseline() / Pango.SCALE
        width = max(logical.width, 1)
        ascent = max(baseline, logical.height * 0.75)
        descent = max(logical.height - ascent, logical.height * 0.25)
        return layout, float(width), float(ascent), float(descent)

    @classmethod
    def _dot_geom(cls, layout, scale, italic):
        """Centre (x, y in layout coordinates) and radius of a time-derivative dot above
        the glyph(s) in `layout`."""
        ink, _logical = layout.get_pixel_extents()
        r = 1.45 * scale
        cx = ink.x + ink.width / 2.0 + (0.10 * ink.height if italic else 0.0)
        cy = ink.y - 2.6 * scale - r
        return cx, cy, r

    @classmethod
    def measure_seq(cls, pango_ctx, seq: MathSeq, scale=1.0):
        seq.scale = scale
        if not seq.items:
            # Empty placeholder box size
            w = 13.0 * scale
            asc = 11.0 * scale
            desc = 4.0 * scale
            seq.width = w
            seq.ascent = asc
            seq.descent = desc
            return

        total_w = 0.0
        max_asc = 10.0 * scale
        max_desc = 3.0 * scale

        for idx, item in enumerate(seq.items):
            prev_item = seq.items[idx - 1] if idx > 0 else None
            cls.measure_node(pango_ctx, item, scale, prev_item)
            total_w += item.width
            max_asc = max(max_asc, item.ascent)
            max_desc = max(max_desc, item.descent)
        gap = getattr(seq, "result_gap", None)
        if gap is not None:
            total_w += gap[1]

        seq.width = total_w
        seq.ascent = max_asc
        seq.descent = max_desc

    UNIT_GAP = 2.5  # space before a unit (5 kW), in points at scale 1

    @classmethod
    def measure_node(cls, pango_ctx, node: MathNode, scale=1.0, prev_item=None):
        if isinstance(node, UnitNode):
            _lay, w, asc, desc = cls._make_layout(pango_ctx, node.name or "'", scale)
            node.width = w + cls.UNIT_GAP * scale
            node.ascent = asc
            node.descent = desc
            return
        if isinstance(node, CharNode):
            display_text = f" {OP_DISPLAY.get(node.text, node.text)} " if node.is_operator() and node.text != "," else (
                ", " if node.text == "," else node.text
            )
            is_var = tok_is_letter(node.text)
            has_dot = tok_has_dot(node.text)
            if has_dot:
                display_text = tok_base(node.text)  # the dot is drawn by hand (fonts place it badly)
            lay, w, asc, desc = cls._make_layout(pango_ctx, display_text, scale, italic=is_var, bold=node.text == "==")
            if has_dot:
                _cx, dot_y, r = cls._dot_geom(lay, scale, is_var)
                asc = max(asc, asc - (dot_y - r) + 1.0 * scale)
            node.width = w
            node.ascent = asc
            node.descent = desc

        elif isinstance(node, FracNode):
            sub_scale = max(0.75, scale * 0.88)
            cls.measure_seq(pango_ctx, node.num, sub_scale)
            cls.measure_seq(pango_ctx, node.den, sub_scale)
            pad = 6.0 * scale
            axis_shift = 5.0 * scale  # Height of fraction bar above baseline
            gap = 3.0 * scale
            node.width = max(node.num.width, node.den.width) + pad * 2
            node.ascent = axis_shift + gap + node.num.height
            node.descent = max(0.0, node.den.height + gap - axis_shift)

        elif isinstance(node, SupNode):
            sub_scale = max(0.62, scale * 0.72)
            cls.measure_seq(pango_ctx, node.exp, sub_scale)
            base_asc = prev_item.ascent if prev_item is not None else 12.0 * scale
            shift_up = max(6.0 * scale, base_asc * 0.55)
            node.width = node.exp.width + 2.0 * scale
            node.ascent = shift_up + node.exp.ascent
            node.descent = max(0.0, node.exp.descent - shift_up)

        elif isinstance(node, SubNode):
            sub_scale = max(0.62, scale * 0.72)
            cls.measure_seq(pango_ctx, node.sub, sub_scale)
            base_desc = prev_item.descent if prev_item is not None else 3.0 * scale
            shift_down = max(5.0 * scale, base_desc + 4.0 * scale)
            node.width = node.sub.width + 2.0 * scale
            node.ascent = max(0.0, node.sub.ascent - shift_down)
            node.descent = shift_down + node.sub.descent

        elif isinstance(node, SqrtNode):
            cls.measure_seq(pango_ctx, node.radicand, scale)
            deg_w = 0.0
            deg_asc = 0.0
            if node.degree is not None:
                cls.measure_seq(pango_ctx, node.degree, max(0.58, scale * 0.65))
                deg_w = max(0.0, node.degree.width - 4.0 * scale)
                deg_asc = node.degree.height + 4.0 * scale
            hook_w = 13.0 * scale
            pad_right = 4.0 * scale
            top_pad = 4.0 * scale
            node.width = deg_w + hook_w + node.radicand.width + pad_right
            node.ascent = max(node.radicand.ascent + top_pad, deg_asc)
            node.descent = node.radicand.descent + 2.0 * scale

        elif isinstance(node, ParenNode):
            cls.measure_seq(pango_ctx, node.inner, scale)
            paren_w = 8.0 * scale
            node.width = paren_w * 2 + node.inner.width
            node.ascent = node.inner.ascent + 2.0 * scale
            node.descent = node.inner.descent + 2.0 * scale

        elif isinstance(node, SumNode):
            lim_scale = max(0.60, scale * 0.68)
            cls.measure_seq(pango_ctx, node.lower, lim_scale)
            cls.measure_seq(pango_ctx, node.upper, lim_scale)
            cls.measure_seq(pango_ctx, node.body, scale)
            sym_w = 22.0 * scale
            sym_half = 12.0 * scale
            axis_shift = 5.0 * scale
            op_w = max(sym_w, node.lower.width, node.upper.width) + 6.0 * scale
            node.width = op_w + node.body.width + 4.0 * scale
            node.ascent = max(
                node.body.ascent,
                axis_shift + sym_half + 2.0 * scale + node.upper.height,
            )
            node.descent = max(
                node.body.descent,
                sym_half - axis_shift + 2.0 * scale + node.lower.height,
            )

        elif isinstance(node, IntNode):
            lim_scale = max(0.60, scale * 0.68)
            cls.measure_seq(pango_ctx, node.lower, lim_scale)
            cls.measure_seq(pango_ctx, node.upper, lim_scale)
            cls.measure_seq(pango_ctx, node.body, scale)
            cls.measure_seq(pango_ctx, node.var, scale)
            _, d_w, d_asc, d_desc = cls._make_layout(pango_ctx, " d", scale, italic=True)
            sym_w = 16.0 * scale
            sym_half = 16.0 * scale
            axis_shift = 5.0 * scale
            lim_w = max(node.lower.width, node.upper.width)
            node.width = sym_w + lim_w + 4.0 * scale + node.body.width + d_w + node.var.width + 2.0 * scale
            node.ascent = max(
                node.body.ascent,
                d_asc,
                node.var.ascent,
                axis_shift + sym_half + node.upper.ascent,
            )
            node.descent = max(
                node.body.descent,
                d_desc,
                node.var.descent,
                sym_half - axis_shift + node.lower.descent,
            )

    @classmethod
    def draw_seq(cls, cr, pango_ctx, seq: MathSeq, x: float, baseline_y: float, theme: dict):
        seq.abs_x = x
        seq.abs_y = baseline_y - seq.ascent
        seq.caret_positions = [x]

        if not seq.items:
            # Draw SMath/Mathcad-style placeholder rectangle
            pw = seq.width - 2.0
            ph = seq.height - 2.0
            px = x + 1.0
            py = baseline_y - seq.ascent + 1.0
            cr.save()
            cr.set_source_rgb(*theme["placeholder_fill"])
            cr.rectangle(px, py, pw, ph)
            cr.fill_preserve()
            cr.set_source_rgb(*theme["placeholder_border"])
            cr.set_line_width(1.0)
            cr.set_dash([2.0, 2.0])
            cr.stroke()
            cr.restore()
            seq.caret_positions.append(x + seq.width)
            return

        cur_x = x
        gap = getattr(seq, "result_gap", None)
        for idx, item in enumerate(seq.items):
            prev_item = seq.items[idx - 1] if idx > 0 else None
            cls.draw_node(cr, pango_ctx, item, cur_x, baseline_y, seq.scale, theme, prev_item)
            cur_x += item.width
            if gap is not None and idx == gap[0]:
                seq.result_gap_x = cur_x
                cur_x += gap[1]
            seq.caret_positions.append(cur_x)

    @classmethod
    def draw_node(
        cls,
        cr,
        pango_ctx,
        node: MathNode,
        x: float,
        baseline_y: float,
        scale: float,
        theme: dict,
        prev_item=None,
    ):
        node.abs_x = x
        node.abs_y = baseline_y - node.ascent

        if isinstance(node, UnitNode):
            layout, _, asc, _ = cls._make_layout(pango_ctx, node.name or "'", scale)
            cr.save()
            if not node.name:
                cr.set_source_rgb(*theme["muted_text"])
            elif unit_is_known(node.name):
                cr.set_source_rgb(*theme.get("unit", theme["text"]))
            else:
                cr.set_source_rgb(*theme["error"])
            cr.move_to(x + cls.UNIT_GAP * scale, baseline_y - asc)
            PangoCairo.show_layout(cr, layout)
            cr.restore()
            return

        if isinstance(node, CharNode):
            display_text = f" {OP_DISPLAY.get(node.text, node.text)} " if node.is_operator() and node.text != "," else (
                ", " if node.text == "," else node.text
            )
            is_var = tok_is_letter(node.text)
            has_dot = tok_has_dot(node.text)
            if has_dot:
                display_text = tok_base(node.text)
            layout, _, asc, _ = cls._make_layout(pango_ctx, display_text, scale, italic=is_var, bold=node.text == "==")
            cr.save()
            if node.is_operator():
                cr.set_source_rgb(*theme["operator"])
            else:
                cr.set_source_rgb(*theme["text"])
            cr.move_to(x, baseline_y - asc)
            PangoCairo.show_layout(cr, layout)
            if has_dot:
                cx, dot_y, r = cls._dot_geom(layout, scale, is_var)
                cr.new_path()
                cr.arc(x + cx, baseline_y - asc + dot_y, r, 0, 2 * math.pi)
                cr.fill()
            cr.restore()

        elif isinstance(node, FracNode):
            axis_shift = 5.0 * scale
            gap = 3.0 * scale
            bar_y = baseline_y - axis_shift

            # Draw numerator centered
            num_x = x + (node.width - node.num.width) / 2.0
            num_baseline = bar_y - gap - node.num.descent
            cls.draw_seq(cr, pango_ctx, node.num, num_x, num_baseline, theme)

            # Draw fraction bar
            cr.save()
            cr.set_source_rgb(*theme["text"])
            cr.set_line_width(max(1.2, 1.4 * scale))
            cr.move_to(x + 2.0 * scale, bar_y)
            cr.line_to(x + node.width - 2.0 * scale, bar_y)
            cr.stroke()
            cr.restore()

            # Draw denominator centered
            den_x = x + (node.width - node.den.width) / 2.0
            den_baseline = bar_y + gap + node.den.ascent
            cls.draw_seq(cr, pango_ctx, node.den, den_x, den_baseline, theme)

        elif isinstance(node, SupNode):
            base_asc = prev_item.ascent if prev_item is not None else 12.0 * scale
            shift_up = max(6.0 * scale, base_asc * 0.55)
            cls.draw_seq(cr, pango_ctx, node.exp, x + 1.0 * scale, baseline_y - shift_up, theme)

        elif isinstance(node, SubNode):
            base_desc = prev_item.descent if prev_item is not None else 3.0 * scale
            shift_down = max(5.0 * scale, base_desc + 4.0 * scale)
            cls.draw_seq(cr, pango_ctx, node.sub, x + 1.0 * scale, baseline_y + shift_down, theme)

        elif isinstance(node, SqrtNode):
            deg_w = 0.0
            if node.degree is not None:
                deg_w = max(0.0, node.degree.width - 4.0 * scale)
                deg_baseline = baseline_y - node.radicand.ascent * 0.55
                cls.draw_seq(cr, pango_ctx, node.degree, x, deg_baseline, theme)

            hook_w = 13.0 * scale
            rad_x = x + deg_w + hook_w
            cls.draw_seq(cr, pango_ctx, node.radicand, rad_x, baseline_y, theme)

            # Draw radical symbol around radicand
            top_y = baseline_y - node.radicand.ascent - 2.5 * scale
            bot_y = baseline_y + node.radicand.descent + 1.0 * scale
            mid_y = top_y + (bot_y - top_y) * 0.60

            cr.save()
            cr.set_source_rgb(*theme["text"])
            cr.set_line_width(max(1.2, 1.4 * scale))
            cr.move_to(x + deg_w + 1.0 * scale, mid_y)
            cr.line_to(x + deg_w + 3.5 * scale, mid_y - 2.0 * scale)
            cr.line_to(x + deg_w + 7.5 * scale, bot_y)
            cr.line_to(rad_x - 1.5 * scale, top_y)
            cr.line_to(rad_x + node.radicand.width + 2.5 * scale, top_y)
            cr.line_to(rad_x + node.radicand.width + 2.5 * scale, top_y + 3.5 * scale)
            cr.stroke()
            cr.restore()

        elif isinstance(node, ParenNode):
            paren_w = 8.0 * scale
            cls.draw_seq(cr, pango_ctx, node.inner, x + paren_w, baseline_y, theme)

            top_y = baseline_y - node.ascent + 2.0 * scale
            bot_y = baseline_y + node.descent - 2.0 * scale
            mid_y = (top_y + bot_y) / 2.0
            curve_dx = 5.0 * scale

            cr.save()
            cr.set_source_rgb(*theme["text"])
            cr.set_line_width(max(1.3, 1.5 * scale))
            # Left paren
            lx = x + paren_w - 1.5 * scale
            cr.move_to(lx, top_y)
            cr.curve_to(lx - curve_dx, top_y + (bot_y - top_y) * 0.25, lx - curve_dx, bot_y - (bot_y - top_y) * 0.25, lx, bot_y)
            cr.stroke()
            # Right paren
            rx = x + node.width - paren_w + 1.5 * scale
            cr.move_to(rx, top_y)
            cr.curve_to(rx + curve_dx, top_y + (bot_y - top_y) * 0.25, rx + curve_dx, bot_y - (bot_y - top_y) * 0.25, rx, bot_y)
            cr.stroke()
            cr.restore()

        elif isinstance(node, SumNode):
            sym_w = 22.0 * scale
            sym_half = 12.0 * scale
            axis_shift = 5.0 * scale
            op_w = max(sym_w, node.lower.width, node.upper.width) + 6.0 * scale
            center_x = x + op_w / 2.0
            axis_y = baseline_y - axis_shift

            # Draw Sigma symbol
            sx0 = center_x - sym_w / 2.0
            sx1 = center_x + sym_w / 2.0
            sy0 = axis_y - sym_half
            sy1 = axis_y + sym_half
            cr.save()
            cr.set_source_rgb(*theme["operator"])
            cr.set_line_width(max(1.5, 1.8 * scale))
            cr.move_to(sx1, sy0 + 3.0 * scale)
            cr.line_to(sx1, sy0)
            cr.line_to(sx0, sy0)
            cr.line_to(center_x + 1.0 * scale, axis_y)
            cr.line_to(sx0, sy1)
            cr.line_to(sx1, sy1)
            cr.line_to(sx1, sy1 - 3.0 * scale)
            cr.stroke()
            cr.restore()

            # Upper and lower limits
            up_x = center_x - node.upper.width / 2.0
            up_base = sy0 - 2.0 * scale - node.upper.descent
            cls.draw_seq(cr, pango_ctx, node.upper, up_x, up_base, theme)

            low_x = center_x - node.lower.width / 2.0
            low_base = sy1 + 2.0 * scale + node.lower.ascent
            cls.draw_seq(cr, pango_ctx, node.lower, low_x, low_base, theme)

            # Body
            cls.draw_seq(cr, pango_ctx, node.body, x + op_w + 2.0 * scale, baseline_y, theme)

        elif isinstance(node, IntNode):
            sym_w = 16.0 * scale
            sym_half = 16.0 * scale
            axis_shift = 5.0 * scale
            axis_y = baseline_y - axis_shift
            lim_w = max(node.lower.width, node.upper.width)

            # Draw Integral curve ∫
            ix = x + sym_w * 0.5
            top_y = axis_y - sym_half
            bot_y = axis_y + sym_half
            cr.save()
            cr.set_source_rgb(*theme["operator"])
            cr.set_line_width(max(1.6, 1.9 * scale))
            cr.move_to(ix + 5.0 * scale, top_y + 3.0 * scale)
            cr.curve_to(ix + 3.0 * scale, top_y - 2.0 * scale, ix, top_y, ix, axis_y)
            cr.curve_to(ix, bot_y, ix - 3.0 * scale, bot_y + 2.0 * scale, ix - 5.0 * scale, bot_y - 3.0 * scale)
            cr.stroke()
            cr.restore()

            # Limits
            cls.draw_seq(cr, pango_ctx, node.upper, x + sym_w, top_y + 4.0 * scale, theme)
            cls.draw_seq(cr, pango_ctx, node.lower, x + sym_w, bot_y - 2.0 * scale, theme)

            # Body
            body_x = x + sym_w + lim_w + 4.0 * scale
            cls.draw_seq(cr, pango_ctx, node.body, body_x, baseline_y, theme)

            # 'd' + variable
            d_x = body_x + node.body.width
            layout, d_w, d_asc, _ = cls._make_layout(pango_ctx, " d", scale, italic=True)
            cr.save()
            cr.set_source_rgb(*theme["operator"])
            cr.move_to(d_x, baseline_y - d_asc)
            PangoCairo.show_layout(cr, layout)
            cr.restore()

            cls.draw_seq(cr, pango_ctx, node.var, d_x + d_w, baseline_y, theme)


# ============================================================================
# Worksheet Evaluation Engine (SMath Studio / Mathcad top-down evaluator)
# ============================================================================


# How operator tokens are shown on the sheet. A single '=' both defines (when something
# follows it: a = 5) and evaluates (when it ends the box: a =). Older worksheets store
# definitions as ':=', which is displayed as '=' too. '==' makes an equation
# (y == 2x + 4), shown as a bold '=' and solved via right-click -> Solve for.
OP_DISPLAY = {":=": "=", "==": "="}

BUILTIN_MATH_FUNCS = {
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sinh", "cosh", "tanh", "sqrt", "ln", "log", "exp", "abs",
    "rows", "cols", "col", "row", "len", "total", "mean", "max", "min",
}


def seq_to_python_expr(seq: MathSeq, env: dict = None, is_lhs: bool = False) -> str:
    """Convert a 2D MathSeq into a valid Python math expression string."""
    parts = []
    items = seq.items
    i = 0
    while i < len(items):
        node = items[i]
        # Insert implicit multiplication when needed (e.g. 2x, 2(x+1), a(x+1), (a)(b), 2 sqrt(x))
        if i > 0:
            prev = items[i - 1]
            prev_is_val = (
                (isinstance(prev, CharNode) and (tok_is_alnum(prev.text) or prev.text in GREEK_AUTOCOMPLETE.values()))
                or isinstance(prev, (ParenNode, FracNode, SqrtNode, SupNode, SubNode, UnitNode))
            )
            curr_is_val = (
                (isinstance(node, CharNode) and (tok_is_letter(node.text) or node.text in GREEK_AUTOCOMPLETE.values()))
                or isinstance(node, (ParenNode, FracNode, SqrtNode, SumNode, IntNode, UnitNode))
            )
            if prev_is_val and curr_is_val:
                if isinstance(node, ParenNode) and isinstance(prev, (CharNode, SubNode)):
                    # Gather preceding identifier word to check if it is a function call vs constant*(...)
                    k = i - 1
                    ident_chars = []
                    if isinstance(items[k], SubNode):
                        ident_chars.append("_" + seq_to_python_expr(items[k].sub, env))
                        k -= 1
                    while k >= 0 and isinstance(items[k], CharNode) and (
                        tok_is_alnum(items[k].text) or items[k].text in GREEK_AUTOCOMPLETE.values()
                    ):
                        ident_chars.append(items[k].text)
                        k -= 1
                    # Names may end in digits (e.g. T1), but cannot start with them (2x -> x)
                    ident = "".join(reversed(ident_chars)).lstrip("0123456789")
                    is_fn_call = (
                        is_lhs
                        or ident in BUILTIN_MATH_FUNCS
                        or (env is not None and callable(env.get(ident)))
                        or (env is not None and ident not in env and len(ident) == 1)
                    )
                    if not is_fn_call:
                        parts.append("*")
                elif isinstance(prev, CharNode) and prev.text.isdigit() and isinstance(node, CharNode) and node.text.isdigit():
                    pass
                elif (isinstance(prev, CharNode) and tok_is_letter(prev.text) and isinstance(node, CharNode)
                      and tok_is_letter(node.text) and "π" not in (prev.text, node.text)):
                    pass
                else:
                    parts.append("*")

        if isinstance(node, UnitNode):
            parts.append(f"_U[{normalize_unit_name(node.name)!r}]")
        elif isinstance(node, CharNode):
            t = node.text
            if t == "·":
                parts.append("*")
            elif t == "π":
                parts.append("pi")
            elif t == "∞":
                parts.append("inf")
            elif t == "≤":
                parts.append("<=")
            elif t == "≥":
                parts.append(">=")
            elif t == "≠":
                parts.append("!=")
            elif tok_has_dot(t):
                # same form Python itself uses for identifiers (NFKC)
                parts.append(unicodedata.normalize("NFKC", t))
            else:
                parts.append(t)
        elif isinstance(node, SubNode):
            # Subscript acts as part of variable identifier: x_1
            sub_txt = seq_to_python_expr(node.sub, env).strip()
            parts.append(f"_{sub_txt}")
        elif isinstance(node, SupNode):
            exp_txt = seq_to_python_expr(node.exp, env)
            parts.append(f"**({exp_txt})")
        elif isinstance(node, FracNode):
            num_txt = seq_to_python_expr(node.num, env)
            den_txt = seq_to_python_expr(node.den, env)
            parts.append(f"(({num_txt})/({den_txt}))")
        elif isinstance(node, SqrtNode):
            rad_txt = seq_to_python_expr(node.radicand, env)
            if node.degree is not None and not node.degree.is_empty():
                deg_txt = seq_to_python_expr(node.degree, env)
                parts.append(f"(({rad_txt})**(1.0/({deg_txt})))")
            else:
                parts.append(f"sqrt({rad_txt})")
        elif isinstance(node, ParenNode):
            inner_txt = seq_to_python_expr(node.inner, env)
            parts.append(f"({inner_txt})")
        elif isinstance(node, SumNode):
            low_txt = seq_to_python_expr(node.lower, env)
            up_txt = seq_to_python_expr(node.upper, env)
            body_txt = seq_to_python_expr(node.body, env)
            if "=" in low_txt:
                var_name, start_expr = low_txt.split("=", 1)
                var_name = var_name.strip()
            else:
                var_name, start_expr = "k", low_txt
            parts.append(f"_smath_sum(lambda {var_name}: ({body_txt}), {start_expr}, {up_txt})")
        elif isinstance(node, IntNode):
            low_txt = seq_to_python_expr(node.lower, env).strip()
            up_txt = seq_to_python_expr(node.upper, env).strip()
            body_txt = seq_to_python_expr(node.body, env)
            var_name = seq_to_python_expr(node.var, env).strip() or "x"
            parts.append(f"_smath_int(lambda {var_name}: ({body_txt}), {low_txt}, {up_txt})")

        i += 1
    return "".join(parts)


def _smath_sum(fn, start, end):
    s = int(round(float(start)))
    e = int(round(float(end)))
    return sum(fn(k) for k in range(s, e + 1))


def _smath_int(fn, a, b, n=200):
    a = a if isinstance(a, Quantity) else float(a)
    b = b if isinstance(b, Quantity) else float(b)
    if a == b:
        return 0.0
    h = (b - a) / n
    total = fn(a) + fn(b)
    for i in range(1, n):
        x = a + i * h
        total += (4.0 if i % 2 == 1 else 2.0) * fn(x)
    return total * h / 3.0


# ============================================================================
# Measurement units (SMath / Mathcad style): 5'kW, 20'°C, 3'm/'s …
# A Quantity is a value in coherent SI units plus the exponents of the seven SI base
# units. Results whose units cancel collapse back to plain numbers, so sheets without
# units behave exactly as before. Plots, curve fits, tables and the solver see the SI
# number (float(q)).
# ============================================================================

from fractions import Fraction

UNIT_BASE = ("m", "kg", "s", "K", "A", "mol", "cd")


class UnitError(Exception):
    """Units that don't fit together (m + s, sin(5 m) …); the message is shown on the sheet."""


def _D(m=0, kg=0, s=0, K=0, A=0, mol=0, cd=0):
    return tuple(Fraction(v) for v in (m, kg, s, K, A, mol, cd))


DIMLESS = _D()
_SUP_DIGITS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _dims_add(a, b, k=1):
    return tuple(x + k * y for x, y in zip(a, b))


def _q_parts(x):
    """(value, dims) of a number / Quantity / °C, or None for anything else."""
    if isinstance(x, Quantity):
        return x.value, x.dims
    if isinstance(x, _Celsius):
        return 1.0, _D(K=1)
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float, Fraction)):
        return float(x), DIMLESS
    return None


def _mk_q(value, dims):
    return value if dims == DIMLESS else Quantity(value, dims)


class Quantity:
    __slots__ = ("value", "dims")

    def __init__(self, value, dims):
        self.value = float(value)
        self.dims = dims

    # -- helpers
    def _same(self, other, op):
        p = _q_parts(other)
        if p is None:
            return None
        v, d = p
        if d != self.dims and not (d == DIMLESS and v == 0):
            raise UnitError(f"units don't match: {unit_dims_str(self.dims)} {op} {unit_dims_str(d) or '1'}")
        return v

    # -- arithmetic
    def __add__(self, o):
        v = self._same(o, "+")
        return NotImplemented if v is None else _mk_q(self.value + v, self.dims)

    __radd__ = __add__

    def __sub__(self, o):
        v = self._same(o, "−")
        return NotImplemented if v is None else _mk_q(self.value - v, self.dims)

    def __rsub__(self, o):
        v = self._same(o, "−")
        return NotImplemented if v is None else _mk_q(v - self.value, self.dims)

    def __mul__(self, o):
        p = _q_parts(o)
        if p is None:
            return NotImplemented
        return _mk_q(self.value * p[0], _dims_add(self.dims, p[1]))

    __rmul__ = __mul__

    def __truediv__(self, o):
        p = _q_parts(o)
        if p is None:
            return NotImplemented
        return _mk_q(self.value / p[0], _dims_add(self.dims, p[1], -1))

    def __rtruediv__(self, o):
        p = _q_parts(o)
        if p is None:
            return NotImplemented
        return _mk_q(p[0] / self.value, _dims_add(p[1], self.dims, -1))

    def __pow__(self, n):
        if isinstance(n, (Quantity, _Celsius)):
            raise UnitError("an exponent can't have units")
        fr = Fraction(float(n)).limit_denominator(1000)
        return _mk_q(self.value ** float(n), tuple(d * fr for d in self.dims))

    def __rpow__(self, _base):
        raise UnitError("an exponent can't have units")

    def __neg__(self):
        return Quantity(-self.value, self.dims)

    def __pos__(self):
        return self

    def __abs__(self):
        return Quantity(abs(self.value), self.dims)

    def __round__(self, n=None):
        return Quantity(round(self.value, n or 0), self.dims)

    # -- comparisons
    def _cmp_val(self, o, op):
        v = self._same(o, op)
        if v is None:
            raise UnitError(f"can't compare {unit_dims_str(self.dims)} with that")
        return v

    def __lt__(self, o):
        return self.value < self._cmp_val(o, "<")

    def __le__(self, o):
        return self.value <= self._cmp_val(o, "≤")

    def __gt__(self, o):
        return self.value > self._cmp_val(o, ">")

    def __ge__(self, o):
        return self.value >= self._cmp_val(o, "≥")

    def __eq__(self, o):
        p = _q_parts(o)
        if p is None:
            return False
        return p[1] == self.dims and p[0] == self.value or (p[0] == 0 == self.value)

    def __ne__(self, o):
        return not self.__eq__(o)

    def __hash__(self):
        return hash((self.value, self.dims))

    # -- conversions (SI number, used by plots, fits, tables, fluid functions)
    def __float__(self):
        return self.value

    def __int__(self):
        return int(self.value)

    def __bool__(self):
        return self.value != 0

    def __repr__(self):
        return f"{self.value!r} {unit_dims_str(self.dims)}"


class _Celsius:
    """'°C. After a number it is an absolute temperature (20'°C = 293.15 K); inside a
    compound unit (W/(m·°C)) it is a temperature difference, i.e. the same as K."""

    _K = None

    def _k(self):
        return Quantity(1.0, _D(K=1))

    def __rmul__(self, o):
        if isinstance(o, (int, float)) and not isinstance(o, bool):
            return Quantity(float(o) + 273.15, _D(K=1))
        return o * self._k()

    def __mul__(self, o):
        return self._k() * o

    def __truediv__(self, o):
        return self._k() / o

    def __rtruediv__(self, o):
        return o / self._k()

    def __pow__(self, n):
        return self._k() ** n

    def __float__(self):
        return 1.0

    def __repr__(self):
        return "°C"


CELSIUS = _Celsius()
CELSIUS_NAME = "°C"

_SI_PREFIX = {"G": 1e9, "M": 1e6, "k": 1e3, "h": 1e2, "c": 1e-2, "m": 1e-3,
              "μ": 1e-6, "n": 1e-9, "p": 1e-12}

UNITS = {}  # name -> (factor to coherent SI, dims)


def _def_unit(name, factor, dims, prefixes=""):
    UNITS[name] = (float(factor), dims)
    for pr in prefixes:
        UNITS[pr + name] = (float(factor) * _SI_PREFIX[pr], dims)


_N_D, _J_D, _W_D = _D(kg=1, m=1, s=-2), _D(kg=1, m=2, s=-2), _D(kg=1, m=2, s=-3)
_def_unit("m", 1, _D(m=1), "kcmμn")
_def_unit("g", 1e-3, _D(kg=1), "kmμ")
_def_unit("t", 1e3, _D(kg=1))
_def_unit("s", 1, _D(s=1), "mμn")
_def_unit("min", 60, _D(s=1))
_def_unit("h", 3600, _D(s=1))
_def_unit("day", 86400, _D(s=1))
_def_unit("K", 1, _D(K=1), "m")
_def_unit("A", 1, _D(A=1), "kmμ")
_def_unit("mol", 1, _D(mol=1), "km")
_def_unit("cd", 1, _D(cd=1))
_def_unit("N", 1, _N_D, "kMm")
_def_unit("J", 1, _J_D, "kMGm")
_def_unit("Wh", 3600, _J_D, "kMG")
_def_unit("cal", 4.184, _J_D, "k")
_def_unit("W", 1, _W_D, "kMGm")
_def_unit("Pa", 1, _D(kg=1, m=-1, s=-2), "hkMG")
_def_unit("bar", 1e5, _D(kg=1, m=-1, s=-2), "m")
_def_unit("atm", 101325, _D(kg=1, m=-1, s=-2))
_def_unit("Hz", 1, _D(s=-1), "kMG")
_def_unit("C", 1, _D(A=1, s=1), "m")
_def_unit("V", 1, _D(kg=1, m=2, s=-3, A=-1), "kMm")
_def_unit("Ω", 1, _D(kg=1, m=2, s=-3, A=-2), "kMm")
_def_unit("F", 1, _D(kg=-1, m=-2, s=4, A=2), "mμnp")
_def_unit("H", 1, _D(kg=1, m=2, s=-2, A=-2), "mμ")
_def_unit("T", 1, _D(kg=1, s=-2, A=-1), "mμ")
_def_unit("Wb", 1, _D(kg=1, m=2, s=-2, A=-1))
_def_unit("L", 1e-3, _D(m=3), "m")
_def_unit("rad", 1, DIMLESS, "m")
_def_unit("deg", math.pi / 180.0, DIMLESS)

# Typed spellings that become the proper symbol when the unit is finished
UNIT_ALIASES = {"ohm": "Ω", "kohm": "kΩ", "Mohm": "MΩ", "mohm": "mΩ", "degC": "°C", "C°": "°C",
                "celsius": "°C", "l": "L", "ml": "mL", "sec": "s", "hr": "h", "hrs": "h"}
# Full names, any capitalisation, with SI prefixes spelled out: 'joule, 'kilowatt, 'Megapascal …
_UNIT_FULL_NAMES = {
    "meter": "m", "metre": "m", "gram": "g", "tonne": "t", "second": "s", "minute": "min", "hour": "h",
    "kelvin": "K", "ampere": "A", "amp": "A", "mole": "mol", "candela": "cd", "newton": "N",
    "joule": "J", "watthour": "Wh", "calorie": "cal", "watt": "W", "pascal": "Pa", "hertz": "Hz",
    "coulomb": "C", "volt": "V", "farad": "F", "henry": "H", "tesla": "T", "weber": "Wb",
    "liter": "L", "litre": "L", "radian": "rad", "degree": "deg", "ohm": "Ω",
}
_PREFIX_NAMES = {"giga": "G", "mega": "M", "kilo": "k", "hecto": "h", "centi": "c", "milli": "m",
                 "micro": "μ", "nano": "n", "pico": "p"}

# Named units tried when showing a result (best match: W/(m·K), J/kg, Pa·s …)
_DISPLAY_DERIVED = [(n, UNITS[n][1]) for n in ("W", "J", "N", "Pa", "C", "V", "Ω", "F", "H", "T", "Wb")]


def normalize_unit_name(name: str) -> str:
    if name in UNITS or name == CELSIUS_NAME:
        return name
    if name in UNIT_ALIASES:
        return UNIT_ALIASES[name]
    low = name.lower()
    if low.endswith("s") and low[:-1] and not low.endswith("ss"):
        low_sing = low[:-1]  # plurals: joules, watts, hours
    else:
        low_sing = low
    for cand in (low, low_sing):
        if cand in _UNIT_FULL_NAMES:
            return _UNIT_FULL_NAMES[cand]
        for pn, ps in _PREFIX_NAMES.items():
            if cand.startswith(pn) and cand[len(pn):] in _UNIT_FULL_NAMES:
                full = ps + _UNIT_FULL_NAMES[cand[len(pn):]]
                if full in UNITS:
                    return full
    if low in ("degc", "degreec", "degreecelsius", "celsius"):
        return CELSIUS_NAME
    if name.startswith("u") and ("μ" + name[1:]) in UNITS:
        return "μ" + name[1:]
    return name


def unit_is_known(name: str) -> bool:
    return name in UNITS or name == CELSIUS_NAME


class _UnitTable(dict):
    def __missing__(self, key):
        raise UnitError("type a unit name" if not key else f"unknown unit '{key}'")


UNIT_VALUES = _UnitTable({n: _mk_q(f, d) for n, (f, d) in UNITS.items()})
UNIT_VALUES[CELSIUS_NAME] = CELSIUS


class _CelsiusSI:
    """°C for the solver / curve fit, which work with plain SI numbers."""

    def __rmul__(self, o):
        return o + 273.15

    __mul__ = __rmul__

    def __rtruediv__(self, o):
        return o

    def __truediv__(self, o):
        return 1 / o

    def __pow__(self, _n):
        return 1


UNIT_SI_NUMBERS = _UnitTable({n: f for n, (f, _d) in UNITS.items()})
UNIT_SI_NUMBERS[CELSIUS_NAME] = _CelsiusSI()


def _sup(e: Fraction) -> str:
    if e == 1:
        return ""
    if e.denominator == 1:
        return str(e.numerator).translate(_SUP_DIGITS)
    return f"^({e})"


def unit_dims_str(dims) -> str:
    """Best-matching unit text for the dimensions: W/(m·K), J/kg, m/s², Pa·s …"""
    if dims == DIMLESS:
        return ""
    best = None
    for sym, ddims in [(None, DIMLESS)] + _DISPLAY_DERIVED:
        res = _dims_add(dims, ddims, -1)
        used = 1 if sym else 0
        cost = (sum(abs(r) for r in res) + used, sum(1 for r in res if r) + used)
        if best is None or cost < best[0]:
            best = (cost, sym, res)
    _cost, sym, res = best
    num = [sym] if sym else []
    den = []
    for name, e in zip(UNIT_BASE, res):
        if e > 0:
            num.append(name + _sup(e))
        elif e < 0:
            den.append(name + _sup(-e))
    n = "·".join(num) if num else "1"
    if not den:
        return n
    d = "·".join(den)
    return f"{n}/({d})" if len(den) > 1 else f"{n}/{d}"


def _dimless_fn(fn, name):
    def _f(*args):
        for a in args:
            if isinstance(a, (Quantity, _Celsius)):
                raise UnitError(f"{name}() needs a number without units")
        return fn(*args)
    return _f


def _unit_sqrt(x):
    return x ** 0.5 if isinstance(x, Quantity) else math.sqrt(x)


def _si_args(fn):
    """Wrap a function that works on SI numbers (fluid properties …)."""
    def _f(*args):
        return fn(*[float(a) if isinstance(a, Quantity) else a for a in args])
    return _f


def _vec_total(v):
    vals = list(v)
    if any(isinstance(x, Quantity) for x in vals):
        return sum(vals[1:], vals[0])
    return sum(float(x) for x in vals)


def format_number(val, decimals=None) -> str:
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, Quantity):
        u = unit_dims_str(val.dims)
        return f"{format_number(val.value, decimals=decimals)} {u}" if u else format_number(val.value, decimals)
    if isinstance(val, (list, tuple)):
        return "[" + ", ".join(format_number(v, decimals=decimals) for v in val) + "]"
    if isinstance(val, (int, float)):
        if math.isnan(val):
            return "NaN"
        if math.isinf(val):
            return "∞" if val > 0 else "-∞"
        if decimals is not None:
            d = max(0, min(15, int(decimals)))
            v_clean = 0.0 if abs(float(val)) < 1e-15 else float(val)
            return f"{v_clean:.{d}f}"
        if abs(val - round(val)) < 1e-10 and abs(val) < 1e14:
            return str(int(round(val)))
        return f"{val:.6g}"
    return str(val)


def _normalize_seq_ast(seq: MathSeq):
    """
    Auto-repair common 2D entry traps:
    1) If ':=' was typed inside a top-level ParenNode (e.g. f(x := x^2 + a)), promote ':=' and its RHS out of ParenNode.
    2) If '+' or '-' or '=' or ':=' was typed inside SupNode.exp after the exponent term (e.g. x^(2+a)),
       promote '+ a' out of SupNode.exp back to the parent sequence baseline (so x^2+a -> x² + a).
    """
    idx = 0
    while idx < len(seq.items):
        node = seq.items[idx]
        if isinstance(node, ParenNode) and seq.parent_node is None:
            # Check if ':=' was typed inside ParenNode
            for sub_i, sub_it in enumerate(node.inner.items):
                if isinstance(sub_it, CharNode) and sub_it.text == ":=":
                    trailing = node.inner.items[sub_i:]
                    del node.inner.items[sub_i:]
                    for offset, tr in enumerate(trailing):
                        seq.insert(idx + 1 + offset, tr)
                    break
        elif isinstance(node, SupNode):
            # Check if '+' / '-' / '=' / ':=' was typed after at least 1 token in SupNode.exp
            exp_items = node.exp.items
            for sub_i in range(1, len(exp_items)):
                sub_it = exp_items[sub_i]
                if isinstance(sub_it, CharNode) and sub_it.text in ("+", "-", "=", ":="):
                    trailing = exp_items[sub_i:]
                    del exp_items[sub_i:]
                    for offset, tr in enumerate(trailing):
                        seq.insert(idx + 1 + offset, tr)
                    break
        elif isinstance(node, SubNode):
            sub_items = node.sub.items
            for sub_i in range(1, len(sub_items)):
                sub_it = sub_items[sub_i]
                if isinstance(sub_it, CharNode) and sub_it.text in ("+", "-", "·", "*", "=", ":="):
                    trailing = sub_items[sub_i:]
                    del sub_items[sub_i:]
                    for offset, tr in enumerate(trailing):
                        seq.insert(idx + 1 + offset, tr)
                    break

        for child_slot in node.slots():
            _normalize_seq_ast(child_slot)
        idx += 1


def _format_symbolic_rhs(rhs_str: str, args: list, env: dict, decimals=None) -> str:
    """Format a function body with known constants from env substituted for display."""
    import re
    units = []

    def _unit_hold(m):
        units.append(m.group(1))
        return f"\x00{len(units) - 1}\x00"

    disp = re.sub(r"_U\['([^']*)'\]", _unit_hold, rhs_str)
    disp = disp.replace("**", "^").replace("*", "·")
    disp = re.sub(r"\^\(([A-Za-z0-9_]+)\)", r"^\1", disp)

    def _repl(match):
        word = match.group(0)
        if word in args or word in BUILTIN_MATH_FUNCS:
            return word
        if word in env and isinstance(env[word], (int, float)):
            return format_number(env[word], decimals=decimals)
        return word

    disp = re.sub(r"\b[A-Za-z_]\w*\b", _repl, disp)
    return re.sub("\x00(\\d+)\x00", lambda m: units[int(m.group(1))], disp)


def _is_unit_tail(items) -> bool:
    """True if `items` is only a unit expression ('kWh, 'W/'m², 'kg/('m·'s) …)."""
    found = []

    def ok(seq_items, in_exp=False):
        for it in seq_items:
            if isinstance(it, UnitNode):
                found.append(it)
            elif isinstance(it, CharNode):
                t = it.text
                if t in ("·", "/"):
                    continue
                if in_exp and (t.isdigit() or t in ("-", ".")):
                    continue
                return False
            elif isinstance(it, SupNode):
                if not ok(it.exp.items, True):
                    return False
            elif isinstance(it, (FracNode, ParenNode)):
                if not all(ok(sl.items, in_exp) for sl in it.slots()):
                    return False
            else:
                return False
        return True

    return bool(items) and ok(items) and bool(found)


def result_unit_split(items):
    """Index of the '=' that is followed only by a result unit (E = P·t = 'kWh), else None."""
    for j in range(len(items) - 2, 0, -1):
        it = items[j]
        if isinstance(it, CharNode) and it.text == "=":
            return j if _is_unit_tail(items[j + 1:]) else None
    return None


def strip_eval_suffix(items):
    """Items without the trailing evaluation: '… =' or '… = unit'."""
    items = list(items)
    j = result_unit_split(items)
    if j is not None:
        return items[:j]
    if items and isinstance(items[-1], CharNode) and items[-1].text == "=":
        return items[:-1]
    return items


def format_in_unit(val, tail_items, env, decimals=None) -> str:
    """The number of `val` expressed in the unit written after '=' (the unit itself is
    drawn by the box). °C on its own converts an absolute temperature."""
    tail_seq = MathSeq()
    tail_seq.items = list(tail_items)
    tail_txt = seq_to_plain_text(tail_seq).strip()
    if (len(tail_items) == 1 and isinstance(tail_items[0], UnitNode)
            and normalize_unit_name(tail_items[0].name) == CELSIUS_NAME):
        t_val, t_dims, offset = 1.0, _D(K=1), 273.15
    else:
        tq = eval(seq_to_python_expr(tail_seq, env).strip(), env)
        tp = _q_parts(tq)
        if tp is None or tp[0] == 0:
            raise UnitError(f"can't show the result in {tail_txt}")
        t_val, t_dims, offset = tp[0], tp[1], 0.0

    def conv(v):
        if isinstance(v, (list, tuple)):
            return [conv(x) for x in v]
        pv = _q_parts(v)
        if pv is None:
            raise UnitError(f"can't show this in {tail_txt}")
        if pv[1] != t_dims:
            raise UnitError(f"units don't match: {unit_dims_str(pv[1]) or 'no unit'} vs {tail_txt}")
        return (pv[0] - offset) / t_val

    return format_number(conv(val), decimals=decimals)


def evaluate_box_ast(
    root: MathSeq,
    env: dict,
    is_editing: bool = False,
    decimals=None,
):
    """
    Inspect top-level tokens of root for ':=' (or '=') assignment and trailing '=' (evaluation).
    Updates env if ':=' (or mid-box '=') is present, and returns a result string if trailing '=' is present.
    """
    if not is_editing:
        _normalize_seq_ast(root)

    items = root.items
    if not items:
        return None, False

    # Check if last token is '=' (requesting evaluation display)
    # A trailing '==' (nothing after it yet) also just evaluates, like '='
    unit_j = result_unit_split(items)
    tail_items = items[unit_j + 1:] if unit_j is not None else None
    if unit_j is not None:
        wants_eval, work_items = True, items[:unit_j]
    else:
        wants_eval = isinstance(items[-1], CharNode) and items[-1].text in ("=", "==")
        work_items = items[:-1] if wants_eval else items

    def _fmt(v):
        if tail_items is not None:
            return format_in_unit(v, tail_items, env, decimals=decimals)
        return format_number(v, decimals=decimals)

    # Find top-level ':=' (or top-level '=' if ':=' is not present)
    assign_idx = None
    for idx, it in enumerate(work_items):
        if isinstance(it, CharNode) and it.text == ":=":
            assign_idx = idx
            break
    if assign_idx is None:
        for idx, it in enumerate(work_items):
            if isinstance(it, CharNode) and it.text == "=" and 0 < idx < len(work_items) - 1:
                assign_idx = idx
                break

    env.setdefault("__builtins__", {})
    sheet_funcs = env.setdefault("_sheet_functions", [])
    sheet_vecs = env.setdefault("_sheet_vectors", [])
    sheet_func_defs = env.setdefault("_sheet_func_defs", {})

    try:
        if assign_idx is not None:
            lhs_seq = MathSeq()
            lhs_seq.items = work_items[:assign_idx]
            rhs_seq = MathSeq()
            rhs_seq.items = work_items[assign_idx + 1 :]
            lhs_str = seq_to_python_expr(lhs_seq, env, is_lhs=True).strip()
            rhs_str = seq_to_python_expr(rhs_seq, env, is_lhs=False).strip()
            if not lhs_str or not rhs_str:
                return ("?" if wants_eval else None), False

            # Support function definitions like f(x) := x^2 + a
            if "(" in lhs_str and lhs_str.endswith(")"):
                fn_name, arg_part = lhs_str[:-1].split("(", 1)
                fn_name = fn_name.strip()
                args = [a.strip() for a in arg_part.split(",") if a.strip()]
                fn_code = f"lambda {', '.join(args)}: ({rhs_str})"
                fn_obj = eval(fn_code, env)
                # Test-evaluate with dummy 1.0 args to verify constants in rhs_str are defined
                test_args = [1.0 for _ in args]
                try:
                    fn_obj(*test_args)
                except (ZeroDivisionError, UnitError):
                    pass
                env[fn_name] = fn_obj
                sheet_func_defs[fn_name] = (args, rhs_str)
                if fn_name not in sheet_funcs:
                    sheet_funcs.append(fn_name)
                if wants_eval:
                    return _format_symbolic_rhs(rhs_str, args, env, decimals=decimals), False
                return None, False
            else:
                val = eval(rhs_str, env)
                env[lhs_str] = val
                if isinstance(val, (list, tuple)) and lhs_str not in sheet_vecs:
                    sheet_vecs.append(lhs_str)
                return (_fmt(val) if wants_eval else None), False
        elif wants_eval:
            expr_seq = MathSeq()
            expr_seq.items = work_items
            expr_str = seq_to_python_expr(expr_seq, env, is_lhs=False).strip()
            if not expr_str:
                return "?", False
            try:
                val = eval(expr_str, env)
                return _fmt(val), False
            except NameError:
                # If user wrote f(x) = where f is a sheet function and x is an undefined symbolic identifier
                if "(" in expr_str and expr_str.endswith(")"):
                    fn_name, arg_part = expr_str[:-1].split("(", 1)
                    fn_name = fn_name.strip()
                    call_args = [a.strip() for a in arg_part.split(",") if a.strip()]
                    if fn_name in sheet_func_defs and all(ca.isidentifier() and ca not in env for ca in call_args):
                        f_args, f_rhs = sheet_func_defs[fn_name]
                        return _format_symbolic_rhs(f_rhs, f_args, env, decimals=decimals), False
                raise
    except UnitError as exc:
        if wants_eval:
            return f"? {exc}", True
    except Exception:
        if wants_eval:
            return "?", True
    return None, False


# ============================================================================
# Equation Solver (y == 2x + 4  ->  right-click  ->  Solve for x  ->  x = (y - 4)/2)
# ============================================================================

EQ_TOKEN = "=="


class SolveError(Exception):
    """Raised with a user-readable message when an equation cannot be solved."""


def equation_sides(root: MathSeq):
    """Return (lhs_seq, rhs_seq) if the box is an equation 'lhs == rhs', else None."""
    items = root.items
    if items and isinstance(items[-1], CharNode) and items[-1].text == "=":
        items = items[:-1]
    idxs = [i for i, it in enumerate(items) if isinstance(it, CharNode) and it.text == EQ_TOKEN]
    if len(idxs) != 1 or idxs[0] == 0 or idxs[0] == len(items) - 1:
        return None
    lhs, rhs = MathSeq(), MathSeq()
    lhs.items = items[: idxs[0]]
    rhs.items = items[idxs[0] + 1 :]
    return lhs, rhs


def is_equation_box(root: MathSeq) -> bool:
    return any(isinstance(it, CharNode) and it.text == EQ_TOKEN for it in root.items)


class _SolveEnv(dict):
    """Env used when translating an equation for SymPy: unknown single letters followed by
    '(' are treated as multiplication (a(x+1) = a·(x+1)), not as function calls."""

    def __contains__(self, key):
        return True


_SOLVE_NUM_RE = None
_SOLVE_IDENT_RE = None


def _py_to_sympy(py_str: str, func_defs: dict, depth: int = 0, e_symbol: bool = False):
    """Evaluate a Python expression string (from seq_to_python_expr) into a SymPy expression.
    Every unknown name becomes a symbol; sheet-defined functions are expanded inline."""
    import re
    import sympy as sp

    global _SOLVE_NUM_RE, _SOLVE_IDENT_RE
    if _SOLVE_NUM_RE is None:
        _SOLVE_NUM_RE = re.compile(r"(?<![\w.])(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?")
        _SOLVE_IDENT_RE = re.compile(r"[^\W\d][\w\u0300-\u036f]*")
    if depth > 20:
        raise SolveError("Function definitions are nested too deeply.")

    def _num(m):
        txt = m.group(0)
        if "." in txt or "e" in txt.lower():
            return f"_N('{txt}')"
        return f"_I({txt})"

    code = _SOLVE_NUM_RE.sub(_num, py_str)
    if e_symbol:
        # A lone 'e' (not raised to a power, as in e^x) is a coefficient, not Euler's number
        code = re.sub(r"(?<![\w.])e(?![\w(])(?!\s*\*\*)", "_e_coef", code)

    def _to_num(txt):
        f = sp.Float(txt)
        return sp.Integer(int(f)) if f == int(f) else f

    def _sum(fn, start, end):
        k = sp.Dummy("k", integer=True)
        return sp.summation(fn(k), (k, start, end))

    def _integral(fn, a, b):
        t = sp.Dummy("t")
        return sp.integrate(fn(t), (t, a, b))

    ns = {
        "_I": sp.Integer, "_N": _to_num,
        "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
        "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
        "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
        "sqrt": sp.sqrt, "exp": sp.exp, "abs": sp.Abs,
        "ln": sp.log, "log": lambda z: sp.log(z, 10),
        "pi": sp.pi, "e": sp.E, "inf": sp.oo,
        "_smath_sum": _sum, "_smath_int": _integral,
        "_e_coef": sp.Symbol("e"),
        "_U": UNIT_SI_NUMBERS,
    }

    def _make_sheet_fn(name, args, body):
        def _fn(*vals):
            if len(vals) != len(args):
                raise SolveError(f"{name}() expects {len(args)} argument(s).")
            inner = _py_to_sympy(body, func_defs, depth + 1)
            return inner.subs({sp.Symbol(a): v for a, v in zip(args, vals)}, simultaneous=True)
        return _fn

    called = {m.group(1) for m in re.finditer(r"([^\W\d][\w\u0300-\u036f]*)\s*\(", code)}
    for name in set(_SOLVE_IDENT_RE.findall(code)):
        if name in ns:
            continue
        if name in func_defs and name in called:
            args, body = func_defs[name]
            ns[name] = _make_sheet_fn(name, args, body)
        else:
            ns[name] = sp.Symbol(name)
    try:
        return sp.sympify(eval(code, {"__builtins__": {}}, ns))
    except SolveError:
        raise
    except Exception:
        raise SolveError("This equation uses something the solver can't handle (tables, comparisons, …).")


def equation_to_sympy(root: MathSeq, env: dict):
    """Return (lhs, rhs) SymPy expressions for an equation box."""
    sides = equation_sides(root)
    if sides is None:
        raise SolveError("Write an equation with '==' first, e.g. y == 2x + 4.")
    senv = _SolveEnv({k: v for k, v in (env or {}).items() if callable(v)})
    func_defs = dict((env or {}).get("_sheet_func_defs", {}))
    out = []
    for seq in sides:
        py = seq_to_python_expr(seq, senv).strip()
        if not py:
            raise SolveError("Both sides of the equation need something on them.")
        out.append(_py_to_sympy(py, func_defs))
    return out[0], out[1]


def equation_unknowns(root: MathSeq, env: dict) -> list:
    """Names of the variables appearing in an equation box (for the Solve-for menu)."""
    try:
        lhs, rhs = equation_to_sympy(root, env)
    except SolveError:
        return []
    names = {s.name for s in (lhs.free_symbols | rhs.free_symbols)}
    return sorted(names, key=lambda n: (n.lower(), n))


def solve_equation(root: MathSeq, var: str, env: dict):
    """Solve the equation box for `var`.
    Returns (solutions, numeric) where solutions is a list of SymPy expressions.
    Symbolic first; if SymPy cannot rearrange it and every other variable has a value on the
    sheet, falls back to a numeric root search (numeric=True)."""
    import sympy as sp

    var = unicodedata.normalize("NFKC", var)
    lhs, rhs = equation_to_sympy(root, env)
    sym = sp.Symbol(var)
    eq = sp.Eq(lhs, rhs)
    if eq is sp.true or eq is sp.false or sym not in (lhs.free_symbols | rhs.free_symbols):
        raise SolveError(f"'{var}' does not appear in the equation.")

    def _try_solve(equation, target):
        try:
            return sp.solve(equation, target, rational=False)
        except Exception:
            return None

    def _tidy(expr):
        # Prefer (y - 4)/2 over y/2 - 2. Combine over a common denominator only when that is no more complicated
        try:
            t = sp.together(expr)
            if sp.fraction(t)[1] != 1 and sp.count_ops(t) <= sp.count_ops(expr):
                return t
        except Exception:
            pass
        return expr

    sols = _try_solve(eq, sym)
    if sols and len(sols) > 1:
        # Engineering quantities are usually positive: if assuming that leaves fewer
        # solutions (A = πr² -> only r = √(A/π)), use those.
        all_syms = lhs.free_symbols | rhs.free_symbols
        pos = {s_: sp.Symbol(s_.name, positive=True) for s_ in all_syms}
        psols = _try_solve(eq.subs(pos), pos[sym])
        if psols and len(psols) < len(sols):
            back = {v: k for k, v in pos.items()}
            sols = [ps.subs(back) for ps in psols]
    if sols:
        # Drop solutions that are certainly complex
        real = [s_ for s_ in sols if s_.is_real is not False]
        return [_tidy(s_) for s_ in (real or sols)], False

    # Numeric fallback: all other variables must have numeric values
    others = (lhs.free_symbols | rhs.free_symbols) - {sym}
    subs = {}
    missing = []
    for s in others:
        v = (env or {}).get(s.name)
        if isinstance(v, Quantity):
            v = float(v)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            subs[s] = v
        else:
            missing.append(s.name)
    if missing:
        raise SolveError(
            f"Can't rearrange this for {var}. To solve it numerically, give a value to: "
            + ", ".join(sorted(missing))
        )
    f = (lhs - rhs).subs(subs)
    guess = (env or {}).get(var)
    if isinstance(guess, Quantity):
        guess = float(guess)
    guesses = [guess] if isinstance(guess, (int, float)) and not isinstance(guess, bool) else []
    guesses += [1.0, 0.1, 10.0, -1.0, 100.0, 0.0, -10.0, 1000.0]
    for g in guesses:
        try:
            root_val = sp.nsolve(f, sym, g)
            if abs(complex(root_val).imag) < 1e-12:
                return [sp.Float(complex(root_val).real)], True
        except Exception:
            continue
    raise SolveError(f"No solution for {var} was found.")


# ---- SymPy expression  ->  editable 2D MathSeq -------------------------------


def _name_to_nodes(name: str) -> list:
    """'x' -> [x];  'T_in' -> [T, Sub(in)]."""
    if "_" in name.strip("_"):
        base, sub = name.split("_", 1)
        sub_seq = MathSeq()
        for ch in split_letters(sub):
            sub_seq.append(CharNode(ch))
        return [CharNode(ch) for ch in split_letters(base)] + [SubNode(sub=sub_seq)]
    return [CharNode(ch) for ch in split_letters(name)]


def _seq_of(nodes: list, parent=None) -> MathSeq:
    seq = MathSeq(parent)
    for n in nodes:
        seq.append(n)
    return seq


def _sympy_to_nodes(expr) -> list:
    import sympy as sp

    def paren(nodes):
        return [ParenNode(inner=_seq_of(nodes))]

    def number(val) -> list:
        if isinstance(val, sp.Integer):
            return [CharNode(c) for c in str(int(val))]
        if isinstance(val, sp.Rational):
            p, q = int(val.p), int(val.q)
            sign = [CharNode("-")] if p < 0 else []
            return sign + [FracNode(num=_seq_of([CharNode(c) for c in str(abs(p))]),
                                    den=_seq_of([CharNode(c) for c in str(q)]))]
        txt = format_number(float(val))
        if "e" in txt:  # 1.2e-05 -> 1.2·10^(-5)
            mant, ex = txt.split("e")
            sup = _seq_of([CharNode(c) for c in str(int(ex))])
            return [CharNode(c) for c in mant] + [CharNode("·"), CharNode("1"), CharNode("0"), SupNode(exp=sup)]
        return [CharNode(c) for c in txt]

    def needs_paren_as_factor(e):
        return isinstance(e, sp.Add) or (e.is_Number and e < 0) or (
            isinstance(e, sp.Mul) and e.could_extract_minus_sign())

    def conv(e) -> list:
        if e is sp.pi:
            return [CharNode("π")]
        if e is sp.E:
            return [CharNode("e")]
        if e in (sp.oo, sp.zoo):
            return [CharNode("∞")]
        if e is sp.S.NegativeInfinity:
            return [CharNode("-"), CharNode("∞")]
        if e is sp.I:
            return [CharNode("i")]
        if e.is_Number:
            if e < 0:
                return [CharNode("-")] + number(-e)
            return number(e)
        if isinstance(e, sp.Symbol):
            return _name_to_nodes(e.name)
        if isinstance(e, sp.Add):
            terms = e.as_ordered_terms()
            # Positive terms first: y - a rather than -a + y
            terms = [t for t in terms if not t.could_extract_minus_sign()] + [
                t for t in terms if t.could_extract_minus_sign()]
            out = conv(terms[0])
            for t in terms[1:]:
                if t.could_extract_minus_sign():
                    out += [CharNode("-")] + conv(-t)
                else:
                    out += [CharNode("+")] + conv(t)
            return out
        if isinstance(e, (sp.Mul, sp.Pow)):
            if isinstance(e, sp.Mul) and e.could_extract_minus_sign():
                inner = conv(-e)
                return [CharNode("-")] + inner
            num, den = sp.fraction(e)
            if den != 1:
                return [FracNode(num=_seq_of(conv(num)), den=_seq_of(conv(den)))]
            if isinstance(e, sp.Pow):
                base, ex = e.args
                if ex == sp.Rational(1, 2):
                    return [SqrtNode(radicand=_seq_of(conv(base)))]
                if isinstance(ex, sp.Rational) and ex.p == 1 and ex.q > 2:
                    return [SqrtNode(radicand=_seq_of(conv(base)),
                                     degree=_seq_of([CharNode(c) for c in str(ex.q)]))]
                bn = conv(base)
                if not (isinstance(base, sp.Symbol) or (base.is_Integer and base >= 0) or base is sp.pi
                        or base is sp.E or isinstance(base, sp.Function)):
                    bn = paren(bn)
                return bn + [SupNode(exp=_seq_of(conv(ex)))]
            # Plain product
            factors = e.as_ordered_factors()
            out = []
            prev = None
            for f in factors:
                fn = conv(f)
                if needs_paren_as_factor(f) and not (prev is None and f.is_Number):
                    fn = paren(fn)
                if prev is not None:
                    implicit = prev.is_Number and not f.is_Number and (
                        isinstance(f, (sp.Symbol, sp.Add)) or f is sp.pi)
                    if not implicit:
                        out.append(CharNode("·"))
                out += fn
                prev = f
            return out
        if isinstance(e, sp.exp):
            return [CharNode("e"), SupNode(exp=_seq_of(conv(e.args[0])))]
        if isinstance(e, sp.log):
            if len(e.args) == 2 and e.args[1] == 10:
                name = "log"
            else:
                name = "ln"
            return [CharNode(c) for c in name] + paren(conv(e.args[0]))
        if isinstance(e, sp.Abs):
            return [CharNode(c) for c in "abs"] + paren(conv(e.args[0]))
        if isinstance(e, sp.Function):
            name = type(e).__name__
            args_nodes = []
            for i, a in enumerate(e.args):
                if i:
                    args_nodes.append(CharNode(","))
                args_nodes += conv(a)
            return [CharNode(c) for c in name] + paren(args_nodes)
        # Fallback: plain text
        txt = str(e).replace("**", "^").replace("*", "·")
        return [CharNode(c) for c in txt]

    return conv(expr)


def sympy_to_math_seq(expr) -> MathSeq:
    return _seq_of(_sympy_to_nodes(expr))


def build_solution_seq(var: str, expr) -> MathSeq:
    """MathSeq for the definition 'var = expr'."""
    return _seq_of(_name_to_nodes(var) + [CharNode("=")] + _sympy_to_nodes(expr))


def build_equation_seq(lhs, rhs) -> MathSeq:
    """MathSeq for the equation 'lhs == rhs'."""
    return _seq_of(_sympy_to_nodes(lhs) + [CharNode(EQ_TOKEN)] + _sympy_to_nodes(rhs))


def seq_to_plain_text(seq: MathSeq) -> str:
    """Short one-line text of a MathSeq, for menu labels."""
    out = []
    for it in seq.items:
        if isinstance(it, UnitNode):
            out.append(" " + it.name)
        elif isinstance(it, CharNode):
            t = OP_DISPLAY.get(it.text, it.text)
            out.append(f" {t} " if it.is_operator() and it.text != "," else t)
        elif isinstance(it, FracNode):
            out.append(f"({seq_to_plain_text(it.num)})/({seq_to_plain_text(it.den)})")
        elif isinstance(it, SupNode):
            out.append(f"^{seq_to_plain_text(it.exp)}" if len(it.exp.items) == 1 else f"^({seq_to_plain_text(it.exp)})")
        elif isinstance(it, SubNode):
            out.append(seq_to_plain_text(it.sub))
        elif isinstance(it, SqrtNode):
            out.append(f"√({seq_to_plain_text(it.radicand)})")
        elif isinstance(it, ParenNode):
            out.append(f"({seq_to_plain_text(it.inner)})")
        elif isinstance(it, SumNode):
            out.append("∑…")
        elif isinstance(it, IntNode):
            out.append("∫…")
    return " ".join("".join(out).split())


def definition_sides(root: MathSeq):
    """If the box is a plain variable definition 'name = expr', return (name, rhs_seq)."""
    items = strip_eval_suffix(root.items)
    if any(isinstance(it, CharNode) and it.text == EQ_TOKEN for it in items):
        return None
    idx = None
    for i, it in enumerate(items):
        if isinstance(it, CharNode) and it.text == ":=":
            idx = i
            break
    if idx is None:
        for i, it in enumerate(items):
            if isinstance(it, CharNode) and it.text == "=" and 0 < i < len(items) - 1:
                idx = i
                break
    if idx is None or idx == 0 or idx == len(items) - 1:
        return None
    lhs, rhs = MathSeq(), MathSeq()
    lhs.items = items[:idx]
    rhs.items = items[idx + 1 :]
    name = seq_to_python_expr(lhs, None, is_lhs=True).strip()
    if not name.isidentifier():
        return None  # function definitions f(x) = … are not substituted
    return name, rhs


def substitution_sources(target_root: MathSeq, other_roots: list, env: dict) -> dict:
    """For each variable of the target equation, the other boxes that can supply it:
    {var: [(label, root, kind)]}, kind is 'equation' or 'definition'."""
    import sympy as sp

    try:
        lhs, rhs = equation_to_sympy(target_root, env)
    except SolveError:
        return {}
    target_vars = {sym.name for sym in (lhs.free_symbols | rhs.free_symbols)}
    out = {}
    for root in other_roots:
        if root is target_root:
            continue
        if is_equation_box(root):
            try:
                l2, r2 = equation_to_sympy(root, env)
            except SolveError:
                continue
            names = {sym.name for sym in (l2.free_symbols | r2.free_symbols)}
            label = seq_to_plain_text(root)
            for v in sorted(names & target_vars):
                out.setdefault(v, []).append((label, root, "equation"))
        else:
            d = definition_sides(root)
            if d and d[0] in target_vars:
                label = seq_to_plain_text(_seq_of(_name_to_nodes(d[0]))) + " = " + seq_to_plain_text(d[1])
                out.setdefault(d[0], []).append((label, root, "definition"))
    return out


def substitute_equation(target_root: MathSeq, var: str, source_root: MathSeq, env: dict):
    """Replace `var` in the target equation using the source box.
    Returns (list of (lhs, rhs), numeric_flag)."""
    import sympy as sp

    var = unicodedata.normalize("NFKC", var)
    lhs, rhs = equation_to_sympy(target_root, env)
    sym = sp.Symbol(var)
    numeric = False
    if is_equation_box(source_root):
        l2, r2 = equation_to_sympy(source_root, env)
        if l2 == sym and sym not in r2.free_symbols:
            exprs = [r2]
        elif r2 == sym and sym not in l2.free_symbols:
            exprs = [l2]
        else:
            exprs, numeric = solve_equation(source_root, var, env)
    else:
        d = definition_sides(source_root)
        if d is None or d[0] != var:
            raise SolveError(f"That box does not define {var}.")
        senv = _SolveEnv({k: v for k, v in (env or {}).items() if callable(v)})
        py = seq_to_python_expr(d[1], senv).strip()
        exprs = [_py_to_sympy(py, dict((env or {}).get("_sheet_func_defs", {})))]
    results = []
    for ex in exprs:
        if sym in ex.free_symbols:
            raise SolveError(f"The source still contains {var}, so it can't replace it.")
        nl, nr = lhs.subs(sym, ex), rhs.subs(sym, ex)
        if sp.simplify(nl - nr) == 0:
            raise SolveError("After substituting, both sides are identical (the equation becomes 0 = 0).")
        results.append((nl, nr))
    return results, numeric


# ============================================================================
# AST JSON Serialization & Deserialization (for File -> Save / Open)
# ============================================================================

import base64
import json


# ---------------------------------------------------------------------------
# Curve fitting (Tools ▸ Curve Fit…)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Unit conversion (Tools ▸ Unit Converter)
# Each unit: (symbol, name, system, factor to the SI unit of the category).
# Temperature uses offsets and is handled by _temp_to_k / _temp_from_k.
# ---------------------------------------------------------------------------
_LB = 0.45359237
_LBF = 4.4482216152605
_FT = 0.3048
_IN = 0.0254
_GAL = 3.785411784e-3
_UKGAL = 4.54609e-3
_BBL = 0.158987294928

UNIT_CATEGORIES = {
    "Temperature": [
        ("°C", "degree Celsius", "SI", None),
        ("K", "kelvin", "SI", None),
        ("°F", "degree Fahrenheit", "English", None),
        ("°R", "degree Rankine", "English", None),
    ],
    "Length": [
        ("m", "meter", "SI", 1.0),
        ("km", "kilometer", "SI", 1e3),
        ("cm", "centimeter", "SI", 1e-2),
        ("mm", "millimeter", "SI", 1e-3),
        ("µm", "micrometer", "SI", 1e-6),
        ("in", "inch", "English", _IN),
        ("ft", "foot", "English", _FT),
        ("yd", "yard", "English", 0.9144),
        ("mi", "mile", "English", 1609.344),
        ("mil", "thousandth of an inch", "English", _IN / 1000),
        ("nmi", "nautical mile", "English", 1852.0),
    ],
    "Area": [
        ("m²", "square meter", "SI", 1.0),
        ("km²", "square kilometer", "SI", 1e6),
        ("cm²", "square centimeter", "SI", 1e-4),
        ("mm²", "square millimeter", "SI", 1e-6),
        ("ha", "hectare", "SI", 1e4),
        ("in²", "square inch", "English", _IN ** 2),
        ("ft²", "square foot", "English", _FT ** 2),
        ("yd²", "square yard", "English", 0.9144 ** 2),
        ("acre", "acre", "English", 4046.8564224),
        ("mi²", "square mile", "English", 1609.344 ** 2),
    ],
    "Volume": [
        ("m³", "cubic meter", "SI", 1.0),
        ("L", "liter", "SI", 1e-3),
        ("mL", "milliliter", "SI", 1e-6),
        ("cm³", "cubic centimeter", "SI", 1e-6),
        ("in³", "cubic inch", "English", _IN ** 3),
        ("ft³", "cubic foot", "English", _FT ** 3),
        ("yd³", "cubic yard", "English", 0.9144 ** 3),
        ("gal (US)", "US gallon", "English", _GAL),
        ("gal (UK)", "imperial gallon", "English", _UKGAL),
        ("fl oz (US)", "US fluid ounce", "English", _GAL / 128),
        ("bbl", "oil barrel (42 US gal)", "English", _BBL),
    ],
    "Mass": [
        ("kg", "kilogram", "SI", 1.0),
        ("g", "gram", "SI", 1e-3),
        ("mg", "milligram", "SI", 1e-6),
        ("t", "tonne (metric ton)", "SI", 1e3),
        ("lb", "pound", "English", _LB),
        ("oz", "ounce", "English", _LB / 16),
        ("gr", "grain", "English", _LB / 7000),
        ("slug", "slug", "English", _LBF / _FT),
        ("ton (US)", "short ton (2000 lb)", "English", 2000 * _LB),
        ("ton (UK)", "long ton (2240 lb)", "English", 2240 * _LB),
    ],
    "Force": [
        ("N", "newton", "SI", 1.0),
        ("kN", "kilonewton", "SI", 1e3),
        ("MN", "meganewton", "SI", 1e6),
        ("dyn", "dyne", "SI", 1e-5),
        ("kgf", "kilogram-force", "SI", 9.80665),
        ("lbf", "pound-force", "English", _LBF),
        ("ozf", "ounce-force", "English", _LBF / 16),
        ("kip", "kilopound-force", "English", 1000 * _LBF),
        ("pdl", "poundal", "English", _LB * _FT),
    ],
    "Time": [
        ("s", "second", "SI", 1.0),
        ("ms", "millisecond", "SI", 1e-3),
        ("µs", "microsecond", "SI", 1e-6),
        ("min", "minute", "SI", 60.0),
        ("h", "hour", "SI", 3600.0),
        ("day", "day", "SI", 86400.0),
        ("week", "week", "SI", 7 * 86400.0),
        ("yr", "year (365.25 days)", "SI", 365.25 * 86400.0),
    ],
    "Speed": [
        ("m/s", "meter per second", "SI", 1.0),
        ("km/h", "kilometer per hour", "SI", 1 / 3.6),
        ("cm/s", "centimeter per second", "SI", 1e-2),
        ("ft/s", "foot per second", "English", _FT),
        ("ft/min", "foot per minute", "English", _FT / 60),
        ("in/s", "inch per second", "English", _IN),
        ("mph", "mile per hour", "English", 1609.344 / 3600),
        ("kn", "knot", "English", 1852 / 3600),
    ],
    "Volumetric Flow Rate": [
        ("m³/s", "cubic meter per second", "SI", 1.0),
        ("m³/h", "cubic meter per hour", "SI", 1 / 3600),
        ("L/s", "liter per second", "SI", 1e-3),
        ("L/min", "liter per minute", "SI", 1e-3 / 60),
        ("ft³/s", "cubic foot per second (cfs)", "English", _FT ** 3),
        ("ft³/min", "cubic foot per minute (cfm)", "English", _FT ** 3 / 60),
        ("gpm (US)", "US gallon per minute", "English", _GAL / 60),
        ("gph (US)", "US gallon per hour", "English", _GAL / 3600),
        ("gpm (UK)", "imperial gallon per minute", "English", _UKGAL / 60),
        ("bbl/day", "oil barrel per day", "English", _BBL / 86400),
    ],
    "Pressure": [
        ("Pa", "pascal", "SI", 1.0),
        ("kPa", "kilopascal", "SI", 1e3),
        ("MPa", "megapascal", "SI", 1e6),
        ("bar", "bar", "SI", 1e5),
        ("mbar", "millibar", "SI", 1e2),
        ("atm", "standard atmosphere", "SI", 101325.0),
        ("mmHg", "millimeter of mercury (torr)", "SI", 133.322387415),
        ("psi", "pound-force per square inch", "English", _LBF / _IN ** 2),
        ("ksi", "kilopound-force per square inch", "English", 1000 * _LBF / _IN ** 2),
        ("psf", "pound-force per square foot", "English", _LBF / _FT ** 2),
        ("inHg", "inch of mercury (32 °F)", "English", 3386.389),
        ("inH₂O", "inch of water (4 °C)", "English", 249.08891),
        ("ftH₂O", "foot of water (4 °C)", "English", 2989.06692),
    ],
}


def _temp_to_k(v, unit):
    return {"°C": lambda t: t + 273.15, "K": lambda t: t,
            "°F": lambda t: (t - 32.0) * 5.0 / 9.0 + 273.15, "°R": lambda t: t * 5.0 / 9.0}[unit](v)


def _temp_from_k(k, unit):
    return {"°C": lambda t: t - 273.15, "K": lambda t: t,
            "°F": lambda t: (t - 273.15) * 9.0 / 5.0 + 32.0, "°R": lambda t: t * 9.0 / 5.0}[unit](k)


def convert_unit(value: float, category: str, from_unit: str, to_unit: str) -> float:
    """Convert value between two units of one category in UNIT_CATEGORIES."""
    if category == "Temperature":
        return _temp_from_k(_temp_to_k(value, from_unit), to_unit)
    fac = {u[0]: u[3] for u in UNIT_CATEGORIES[category]}
    return value * fac[from_unit] / fac[to_unit]


def format_unit_value(v: float) -> str:
    if v == 0:
        return "0"
    a = abs(v)
    if 1e-4 <= a < 1e9:
        s = f"{v:.8g}"
    else:
        mant, ex = f"{v:.6e}".split("e")
        mant = mant.rstrip("0").rstrip(".")
        s = f"{mant}e{int(ex)}"
    return s


# ---------------------------------------------------------------------------
# Fluid thermophysical properties (Tools ▸ Fluid Properties, and sheet functions)
# Tabulated reference data (Incropera & DeWitt, Fundamentals of Heat and Mass
# Transfer, Table A.4 air at "atmospheric pressure" -- its densities correspond to
# exactly 1 bar = 100 kPa (ρ = p/(R·T), R = 287.05 J/kg·K) -- and Table A.6
# saturated liquid water),
# interpolated with monotone cubic (PCHIP) curves. SI units, T in kelvin.
# ---------------------------------------------------------------------------
# Air: T [K], rho [kg/m³], cp [kJ/kg·K], mu·1e7 [N·s/m²], k·1e3 [W/m·K]
_AIR_TABLE = [
    (100, 3.5562, 1.032, 71.1, 9.34), (150, 2.3364, 1.012, 103.4, 13.8),
    (200, 1.7458, 1.007, 132.5, 18.1), (250, 1.3947, 1.006, 159.6, 22.3),
    (300, 1.1614, 1.007, 184.6, 26.3), (350, 0.9950, 1.009, 208.2, 30.0),
    (400, 0.8711, 1.014, 230.1, 33.8), (450, 0.7740, 1.021, 250.7, 37.3),
    (500, 0.6964, 1.030, 270.1, 40.7), (550, 0.6329, 1.040, 288.4, 43.9),
    (600, 0.5804, 1.051, 305.8, 46.9), (650, 0.5356, 1.063, 322.5, 49.7),
    (700, 0.4975, 1.075, 338.8, 52.4), (750, 0.4643, 1.087, 354.6, 54.9),
    (800, 0.4354, 1.099, 369.8, 57.3), (850, 0.4097, 1.110, 384.3, 59.6),
    (900, 0.3868, 1.121, 398.1, 62.0), (950, 0.3666, 1.131, 411.3, 64.3),
    (1000, 0.3482, 1.141, 424.4, 66.7), (1100, 0.3166, 1.159, 449.0, 71.5),
    (1200, 0.2902, 1.175, 473.0, 76.3), (1300, 0.2679, 1.189, 496.0, 82.0),
    (1400, 0.2488, 1.207, 530.0, 91.0), (1500, 0.2322, 1.230, 557.0, 100.0),
    (1600, 0.2177, 1.248, 584.0, 106.0), (1700, 0.2049, 1.267, 611.0, 113.0),
    (1800, 0.1935, 1.286, 637.0, 120.0), (1900, 0.1833, 1.307, 663.0, 128.0),
    (2000, 0.1741, 1.337, 689.0, 137.0), (2100, 0.1658, 1.372, 715.0, 147.0),
    (2200, 0.1582, 1.417, 740.0, 160.0), (2300, 0.1513, 1.478, 766.0, 175.0),
    (2400, 0.1448, 1.558, 792.0, 196.0), (2500, 0.1389, 1.665, 818.0, 222.0),
    (3000, 0.1135, 2.726, 955.0, 486.0),
]
# Saturated liquid water: T [K], v·1e3 [m³/kg], cp [kJ/kg·K], mu·1e6 [N·s/m²], k·1e3 [W/m·K]
_WATER_TABLE = [
    (273.15, 1.000, 4.217, 1750, 569), (275, 1.000, 4.211, 1652, 574),
    (280, 1.000, 4.198, 1422, 582), (285, 1.000, 4.189, 1225, 590),
    (290, 1.001, 4.184, 1080, 598), (295, 1.002, 4.181, 959, 606),
    (300, 1.003, 4.179, 855, 613), (305, 1.005, 4.178, 769, 620),
    (310, 1.007, 4.178, 695, 628), (315, 1.009, 4.179, 631, 634),
    (320, 1.011, 4.180, 577, 640), (325, 1.013, 4.182, 528, 645),
    (330, 1.016, 4.184, 489, 650), (335, 1.018, 4.186, 453, 656),
    (340, 1.021, 4.188, 420, 660), (345, 1.024, 4.191, 389, 664),
    (350, 1.027, 4.195, 365, 668), (355, 1.030, 4.199, 343, 671),
    (360, 1.034, 4.203, 324, 674), (365, 1.038, 4.209, 306, 677),
    (370, 1.041, 4.214, 289, 679), (373.15, 1.044, 4.217, 279, 680),
    (380, 1.049, 4.226, 260, 683), (390, 1.058, 4.239, 237, 686),
    (400, 1.067, 4.256, 217, 688), (410, 1.077, 4.278, 200, 688),
    (420, 1.088, 4.302, 185, 688), (430, 1.099, 4.331, 173, 685),
    (440, 1.110, 4.360, 162, 682), (450, 1.123, 4.400, 152, 678),
    (460, 1.137, 4.440, 143, 673), (470, 1.152, 4.480, 136, 667),
    (480, 1.167, 4.530, 129, 660), (490, 1.184, 4.590, 124, 651),
    (500, 1.203, 4.660, 118, 642), (510, 1.222, 4.740, 113, 631),
    (520, 1.244, 4.840, 108, 621), (530, 1.268, 4.950, 104, 608),
    (540, 1.294, 5.080, 101, 594), (550, 1.323, 5.240, 97, 580),
    (560, 1.355, 5.430, 94, 563), (570, 1.392, 5.680, 91, 548),
    (580, 1.433, 6.000, 88, 528), (590, 1.482, 6.410, 84, 513),
    (600, 1.541, 7.000, 81, 497),
]


class _Pchip:
    """Monotone piecewise-cubic Hermite interpolation (Fritsch–Carlson), scalar input."""

    def __init__(self, xs, ys):
        self.x, self.y = list(xs), list(ys)
        n = len(xs)
        h = [xs[i + 1] - xs[i] for i in range(n - 1)]
        d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
        m = [0.0] * n
        m[0], m[-1] = d[0], d[-1]
        for i in range(1, n - 1):
            if d[i - 1] * d[i] <= 0:
                m[i] = 0.0
            else:
                w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        self.h, self.m = h, m

    def __call__(self, t):
        import bisect
        x, y, h, m = self.x, self.y, self.h, self.m
        i = min(max(bisect.bisect_right(x, t) - 1, 0), len(x) - 2)
        s = (t - x[i]) / h[i]
        h00, h10 = (1 + 2 * s) * (1 - s) ** 2, s * (1 - s) ** 2
        h01, h11 = s * s * (3 - 2 * s), s * s * (s - 1)
        return h00 * y[i] + h10 * h[i] * m[i] + h01 * y[i + 1] + h11 * h[i] * m[i + 1]


def _build_fluid(table, first_is_volume):
    T = [r[0] for r in table]
    rho = [1000.0 / r[1] if first_is_volume else r[1] for r in table]
    mu_scale = 1e-6 if first_is_volume else 1e-7
    return {
        "range": (T[0], T[-1]),
        "rho": _Pchip(T, rho),
        "cp": _Pchip(T, [r[2] * 1000.0 for r in table]),
        "mu": _Pchip(T, [r[3] * mu_scale for r in table]),
        "k": _Pchip(T, [r[4] * 1e-3 for r in table]),
    }


FLUIDS = {
    "air": dict(_build_fluid(_AIR_TABLE, False), label="Dry air", gas=True, p_ref=1e5),
    "water": dict(_build_fluid(_WATER_TABLE, True), label="Water (saturated liquid)", gas=False, p_ref=None),
}

# (key, display name, symbol, SI unit, English unit, factor SI -> English)
FLUID_PROPS = [
    ("rho", "Density", "ρ", "kg/m³", "lb/ft³", 0.062427961),
    ("cp", "Specific heat capacity", "cₚ", "J/(kg·K)", "Btu/(lb·°F)", 1 / 4186.8),
    ("nu", "Kinematic viscosity", "ν", "m²/s", "ft²/s", 1 / 0.09290304),
    ("alpha", "Thermal diffusivity", "α", "m²/s", "ft²/h", 3600 / 0.09290304),
    ("k", "Thermal conductivity", "k", "W/(m·K)", "Btu/(h·ft·°F)", 1 / 1.7307347),
    ("mu", "Dynamic viscosity", "μ", "Pa·s", "lb/(ft·s)", 0.67196897),
    ("Pr", "Prandtl number", "Pr", "–", "–", 1.0),
]

P_ATM = 101325.0


def fluid_property(fluid: str, prop: str, T, p=P_ATM):
    """Property `prop` of `fluid` ('air' / 'water') at temperature T [K] (and pressure p [Pa],
    default 1 atm, used for air only: ρ ∝ p, ν and α ∝ 1/p; the air table is at 1 bar).
    Raises ValueError outside the data range."""
    if hasattr(T, "__len__"):
        import numpy as np
        return np.array([fluid_property(fluid, prop, float(t), p) for t in T])
    f = FLUIDS[fluid]
    T = float(T)
    lo, hi = f["range"]
    if not (lo - 1e-9 <= T <= hi + 1e-9):
        raise ValueError(f"{fluid} properties: T = {T:g} K is outside the data range {lo:g}–{hi:g} K")
    ratio = (float(p) / f["p_ref"]) if f["gas"] else 1.0
    if f["gas"] and ratio <= 0:
        raise ValueError("pressure must be positive")
    rho = f["rho"](T) * ratio
    if prop == "rho":
        return rho
    if prop in ("cp", "k", "mu"):
        return f[prop](T)
    if prop == "nu":
        return f["mu"](T) / rho
    if prop == "alpha":
        return f["k"](T) / (rho * f["cp"](T))
    if prop == "Pr":
        return f["cp"](T) * f["mu"](T) / f["k"](T)
    raise KeyError(prop)


def _fluid_sheet_funcs() -> dict:
    """rho_water(T), cp_air(T, p) … for math boxes; T in K, p in Pa (air only).
    Greek spellings (ρ_water, ν_air, α_air, μ_water) are registered too."""
    greek = {"rho": "ρ", "nu": "ν", "alpha": "α", "mu": "μ"}
    funcs = {}
    for fluid in FLUIDS:
        for key, *_rest in FLUID_PROPS:
            if FLUIDS[fluid]["gas"]:
                fn = (lambda fl, pr: lambda T, p=P_ATM: fluid_property(fl, pr, T, p))(fluid, key)
            else:
                fn = (lambda fl, pr: lambda T: fluid_property(fl, pr, T))(fluid, key)
            funcs[f"{key}_{fluid}"] = fn
            if key in greek:
                funcs[f"{greek[key]}_{fluid}"] = fn
    return funcs


FLUID_SHEET_FUNCS = _fluid_sheet_funcs()

# Units of the fluid properties (SI dims) and how the Fluid Properties tool writes them
FLUID_PROP_DIMS = {
    "rho": _D(kg=1, m=-3), "cp": _D(m=2, s=-2, K=-1), "nu": _D(m=2, s=-1), "alpha": _D(m=2, s=-1),
    "k": _D(kg=1, m=1, s=-3, K=-1), "mu": _D(kg=1, m=-1, s=-1), "Pr": DIMLESS,
}
_FLUID_GREEK_KEYS = {"ρ": "rho", "ν": "nu", "α": "alpha", "μ": "mu"}


def _fluid_unit_fn(fn, dims, name):
    """Sheet fluid function that takes T (and p) with or without units. With units
    (T = 300'K or 27'°C) the result carries its unit too (kg/m³, W/(m·K) …)."""
    arg_dims = (_D(K=1), _D(kg=1, m=-1, s=-2))
    arg_names = ("T", "p")

    def _f(*args):
        had_units = False
        plain = []
        for i, a in enumerate(args):
            if isinstance(a, Quantity):
                want = arg_dims[min(i, 1)]
                if a.dims != want:
                    raise UnitError(f"{name}(): {arg_names[min(i, 1)]} must be in {unit_dims_str(want)}")
                had_units = True
                a = a.value
            plain.append(a)
        v = fn(*plain)
        return _mk_q(v, dims) if had_units else v
    return _f


def fluid_sheet_funcs_with_units() -> dict:
    out = {}
    for name, fn in FLUID_SHEET_FUNCS.items():
        key = name.rsplit("_", 1)[0]
        key = _FLUID_GREEK_KEYS.get(key, key)
        out[name] = _fluid_unit_fn(fn, FLUID_PROP_DIMS.get(key, DIMLESS), name)
    return out


def fluid_unit_nodes(key: str) -> list:
    """Unit nodes written after a fluid property value: ρ = 998 kg/m³ …"""
    U = UnitNode

    def frac(num, den):
        return FracNode(num=_seq_of(num), den=_seq_of(den))

    def sq(n):
        return SupNode(exp=_seq_of([CharNode(str(n))]))

    return {
        "rho": [frac([U("kg")], [U("m"), sq(3)])],
        "cp": [frac([U("J")], [U("kg"), CharNode("·"), U("K")])],
        "nu": [frac([U("m"), sq(2)], [U("s")])],
        "alpha": [frac([U("m"), sq(2)], [U("s")])],
        "k": [frac([U("W")], [U("m"), CharNode("·"), U("K")])],
        "mu": [U("Pa"), CharNode("·"), U("s")],
    }.get(key, [])


# ---------------------------------------------------------------------------
# Thermal spreading resistance (Tools ▸ Thermal Spreading), Lee, Song, Au & Moran,
# "Constriction/Spreading Resistance Model for Electronics Packaging", ASME/JSME
# Thermal Engineering Conf., 1995. Rectangular source and plate are replaced by
# circles of equal area; the plate is cooled on its far side with a uniform h.
# ---------------------------------------------------------------------------
SPREAD_MATERIALS = [
    ("Copper", 398.0), ("Aluminum (pure)", 237.0), ("Aluminum 6061", 167.0),
    ("Aluminum 6063", 201.0), ("Aluminum die cast (A380)", 96.0), ("Brass", 110.0),
    ("Steel (carbon)", 50.0), ("Stainless steel 304", 16.2), ("Silicon", 148.0),
    ("Alumina (Al₂O₃)", 30.0), ("Aluminum nitride (AlN)", 170.0), ("FR-4 (through-plane)", 0.3),
]


def lee_spreading(src_l, src_w, pl_l, pl_w, t, k, h, Q=None):
    """Spreading resistance of a centered rectangular source (src_l × src_w) on a plate
    (pl_l × pl_w × t) with conductivity k, cooled on the far side by h. SI units.
    Returns a dict with the dimensionless groups and resistances in K/W."""
    if min(src_l, src_w, pl_l, pl_w, t, k, h) <= 0:
        raise ValueError("All sizes, k and h must be positive.")
    As, Ap = src_l * src_w, pl_l * pl_w
    if As > Ap:
        raise ValueError("The source is larger than the plate.")
    a, b = math.sqrt(As / math.pi), math.sqrt(Ap / math.pi)
    eps, tau, Bi = a / b, t / b, h * b / k
    lam = math.pi + 1.0 / (math.sqrt(math.pi) * eps)
    th = math.tanh(lam * tau)
    phi = (th + lam / Bi) / (1.0 + (lam / Bi) * th)
    psi_avg = 0.5 * (1.0 - eps) ** 1.5 * phi
    psi_max = (1.0 - eps) * phi / math.sqrt(math.pi)
    base = math.sqrt(math.pi) * k * a
    r = {
        "a": a, "b": b, "eps": eps, "tau": tau, "Bi": Bi, "lam": lam, "phi": phi,
        "psi_avg": psi_avg, "psi_max": psi_max,
        "R_sp": psi_avg / base, "R_spmax": psi_max / base,
        "R_1D": t / (k * Ap), "R_conv": 1.0 / (h * Ap),
    }
    r["R_tot"] = r["R_sp"] + r["R_1D"] + r["R_conv"]
    r["R_totmax"] = r["R_spmax"] + r["R_1D"] + r["R_conv"]
    if Q is not None:
        r["dT"], r["dTmax"] = Q * r["R_tot"], Q * r["R_totmax"]
    return r


# ---------------------------------------------------------------------------
# Thermal contact resistance (Tools ▸ Thermal Contact), ported from
# "thermal contact calculator.html": Cooper–Mikic–Yovanovich plastic contact
# conductance + Yovanovich air-gap conductance, in parallel.
# ---------------------------------------------------------------------------
CONTACT_MATERIALS = {
    # key: (name, k [W/m·K], H [Pa], sigma [m] machined, m machined, rgb)
    "Cu": ("Copper (annealed)", 391.0, 400e6, 1.0e-6, 0.15, (0.757, 0.475, 0.247)),
    "Al": ("Aluminum (6061-T6)", 167.0, 930e6, 1.0e-6, 0.12, (0.725, 0.745, 0.761)),
    "Steel": ("Mild Steel (AISI 1018)", 51.9, 1300e6, 1.0e-6, 0.12, (0.541, 0.580, 0.639)),
    "Alumina": ("Alumina (96%)", 25.0, 12800e6, 0.5e-6, 0.08, (0.894, 0.863, 0.788)),
}
# Finish factors scale a material's baseline (machined) sigma and m.
CONTACT_FINISHES = {
    "cast": ("Cast (as-cast)", 10.0, 1.4),
    "machined": ("Machined (milled)", 1.0, 1.0),
    "polished": ("Polished", 0.15, 0.5),
    "extruded": ("Extruded", 2.0, 1.15),
}
CONTACT_K_AIR = 0.026  # W/m·K at ~300 K


def thermal_contact(k1, H1, s1, m1, k2, H2, s2, m2, area, force, k_gas=CONTACT_K_AIR):
    """Joint conductance of two rough surfaces pressed together in air (SI units).
    h_contact = 1.25·k_s·(m/σ)·(P/H_c)^0.95, h_gap = k_gas/Y with
    Y/σ = 1.184·[−ln(3.132·P/H_c)]^0.547, h_joint = h_contact + h_gap."""
    ks = 2 * k1 * k2 / (k1 + k2)
    sigma = math.hypot(s1, s2)
    m = math.hypot(m1, m2)
    Hc = min(H1, H2)
    P = force / area if area > 0 else 0.0
    ratio = P / Hc if Hc > 0 else 0.0
    h_c = 1.25 * ks * (m / sigma) * ratio ** 0.95 if ratio > 0 and sigma > 0 else 0.0
    arg = 3.132 * ratio
    h_g, Y = 0.0, None
    if 0 < arg < 1 and sigma > 0:
        Y = 1.184 * (-math.log(arg)) ** 0.547 * sigma
        h_g = k_gas / Y if Y > 0 else 0.0
    h_j = h_c + h_g
    R = 1.0 / (h_j * area) if h_j > 0 and area > 0 else math.inf
    return {"ks": ks, "sigma": sigma, "m": m, "Hc": Hc, "P": P, "ratio": ratio, "Y": Y,
            "h_c": h_c, "h_g": h_g, "h_j": h_j, "R": R,
            "R_area": 1.0 / h_j if h_j > 0 else math.inf, "gap_saturated": arg >= 1}


def fit_model_candidates(roots: list, env: dict) -> list:
    """Math boxes that can serve as a fit model, e.g. 'y = a·x² + b·x + c', 'y == …' or
    'f(x) = …'. Returns [(label, root, out_name, sympy_expr, fn_args)]."""
    senv = _SolveEnv({k: v for k, v in (env or {}).items() if callable(v)})
    func_defs = dict((env or {}).get("_sheet_func_defs", {}))
    out = []
    for root in roots:
        items = strip_eval_suffix(root.items)
        idx = None
        for tok in (EQ_TOKEN, ":=", "="):
            for i, it in enumerate(items):
                if isinstance(it, CharNode) and it.text == tok and 0 < i < len(items) - 1:
                    idx = i
                    break
            if idx is not None:
                break
        if idx is None:
            continue
        lhs, rhs = MathSeq(), MathSeq()
        lhs.items = items[:idx]
        rhs.items = items[idx + 1:]
        try:
            lhs_str = seq_to_python_expr(lhs, None, is_lhs=True).strip()
            py = seq_to_python_expr(rhs, senv).strip()
            if not py:
                continue
            expr = _py_to_sympy(py, func_defs, e_symbol=True)
        except Exception:
            continue
        fn_args = []
        out_name = lhs_str
        if "(" in lhs_str and lhs_str.endswith(")"):
            out_name, arg_part = lhs_str[:-1].split("(", 1)
            out_name = out_name.strip()
            fn_args = [a.strip() for a in arg_part.split(",") if a.strip()]
        if not out_name.isidentifier():
            continue
        if len(getattr(expr, "free_symbols", ())) < 2:
            continue
        label = f"{seq_to_plain_text(lhs)} = {seq_to_plain_text(rhs)}"
        out.append((label, root, out_name, expr, fn_args))
    return out


def fit_data_vectors(env: dict) -> list:
    """Names of numeric vectors on the sheet (math-box vectors and table columns)."""
    names = []
    for k in list((env or {}).get("_sheet_vectors", [])) + list((env or {}).keys()):
        if k in names or not isinstance(k, str) or k.startswith("_"):
            continue
        v = env.get(k)
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            try:
                [float(t) for t in v]
            except Exception:
                continue
            names.append(k)
    return names


def run_curve_fit(expr, xvar: str, params: list, guesses: list, fixed: dict, xs, ys):
    """Least-squares fit of `expr` (SymPy) to the data. Returns a dict with the fitted
    values, standard errors, R², RMSE and the fitted model."""
    import numpy as np
    import sympy as sp
    from scipy.optimize import curve_fit

    X = np.asarray([float(v) for v in xs], dtype=float)
    Y = np.asarray([float(v) for v in ys], dtype=float)
    if len(X) != len(Y):
        raise SolveError(f"The x data has {len(X)} values but the y data has {len(Y)}.")
    if len(X) < len(params):
        raise SolveError(f"{len(params)} coefficients need at least {len(params)} data points (have {len(X)}).")
    if not params:
        raise SolveError("Tick at least one coefficient to fit.")
    model = expr.subs({sp.Symbol(k): v for k, v in fixed.items()})
    left = {s.name for s in model.free_symbols} - {xvar} - set(params)
    if left:
        raise SolveError("No value on the sheet for: " + ", ".join(sorted(left)) +
                         ". Tick it to fit it, or define it above.")
    f = sp.lambdify([sp.Symbol(xvar)] + [sp.Symbol(p) for p in params], model, "numpy")

    def g(xx, *pp):
        return np.broadcast_to(np.asarray(f(xx, *pp), dtype=float), np.shape(xx))

    import time as _time

    def sse(pp):
        with np.errstate(all="ignore"):
            r = Y - g(X, *pp)
            v = float(np.sum(r * r))
        return v if math.isfinite(v) else float("inf")

    # Guard against aliasing: with sparse data a fast oscillation can thread through
    # every point. Such a curve swings far more between the points than the data do,
    # so compare the curve's total variation with that of the data themselves.
    order = np.argsort(X)
    data_tv = float(np.sum(np.abs(np.diff(Y[order])))) or 1e-300
    dense = np.linspace(float(np.min(X)), float(np.max(X)), 4000)

    def plausible(pp):
        with np.errstate(all="ignore"):
            yy = g(dense, *pp)
            tv = float(np.sum(np.abs(np.diff(yy))))
        return math.isfinite(tv) and tv <= 3.0 * data_tv + 1e-12

    def local(p0, maxfev):
        try:
            with np.errstate(all="ignore"):
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    pp, cov = curve_fit(g, X, Y, p0=list(p0), maxfev=maxfev)
            return sse(pp), pp, cov
        except Exception:
            return float("inf"), None, None

    p_user = [float(v) for v in guesses]
    first_exc = None
    try:
        with np.errstate(all="ignore"):
            popt, pcov = curve_fit(g, X, Y, p0=p_user, maxfev=20000)
        best = (sse(popt), popt, pcov)
    except Exception as exc:
        first_exc = exc
        best = (float("inf"), None, None)
    user_sse = best[0]

    # Multi-start search: a nonlinear model (sin, exp, powers…) often has many local
    # minima, so a single start value easily ends in the wrong one. Try starts spread
    # over sign and magnitude, plus scales taken from the data, and keep the best.
    rng = np.random.default_rng(12345)
    npar = len(params)
    xspan = float(np.ptp(X)) or 1.0
    yspan = float(np.ptp(Y)) or 1.0
    scales = sorted({1.0, yspan / 2, yspan, 1.0 / xspan, 2 * math.pi / xspan, float(np.mean(np.abs(Y))) or 1.0})
    starts = []
    for k in range(1, 41):  # frequency-like ladder (k half-periods over the x span)
        base = [scales[int(rng.integers(len(scales)))] * rng.choice([-1, 1]) for _ in range(npar)]
        for j in range(npar):
            st = list(base)
            st[j] = k * math.pi / xspan
            starts.append(st)
    for _ in range(300):
        mode = rng.random()
        if mode < 0.4:
            st = [rng.choice([-1, 1]) * 10 ** rng.uniform(-2.5, 2.5) for _ in range(npar)]
        elif mode < 0.7:
            st = [rng.choice([-1, 1]) * scales[int(rng.integers(len(scales)))] * 10 ** rng.uniform(-0.5, 0.5)
                  for _ in range(npar)]
        else:
            st = [(u if u != 0 else 1.0) * math.exp(rng.normal(0, 1.2)) * (1 if rng.random() < 0.85 else -1)
                  for u in p_user]
        starts.append(st)
    t0 = _time.monotonic()
    cand = []
    for st in starts:
        if _time.monotonic() - t0 > 4.0:
            break
        v, pp, cov = local(st, 400 * (npar + 1))
        if pp is not None and plausible(pp):
            cand.append((v, pp))
    cand.sort(key=lambda c: c[0])
    if best[1] is not None and not plausible(best[1]):
        best = (float("inf"), None, None)
    for v, pp in cand[:5]:  # polish the best few
        v2, pp2, cov2 = local(pp, 20000)
        if pp2 is not None and v2 < best[0] * (1 - 1e-9) and plausible(pp2):
            best = (v2, pp2, cov2)
    if best[1] is None:  # nothing passed the aliasing check: fall back to the plain fit
        try:
            with np.errstate(all="ignore"):
                popt, pcov = curve_fit(g, X, Y, p0=p_user, maxfev=20000)
            best = (sse(popt), popt, pcov)
        except Exception as exc:
            first_exc = first_exc or exc
    if best[1] is None:
        raise SolveError(f"The fit did not converge ({first_exc}). Try other starting values.")
    popt, pcov = best[1], best[2]
    improved = math.isfinite(user_sse) is False or best[0] < user_sse * (1 - 1e-6)
    resid = Y - g(X, *popt)
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((Y - np.mean(Y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rmse = float(np.sqrt(ss_res / len(X)))
    try:
        perr = [float(v) for v in np.sqrt(np.diag(pcov))]
    except Exception:
        perr = [float("inf")] * len(params)
    values = {p: float(v) for p, v in zip(params, popt)}
    return {
        "values": values,
        "errors": dict(zip(params, perr)),
        "r2": r2,
        "rmse": rmse,
        "n": len(X),
        "x_range": (float(np.min(X)), float(np.max(X))),
        "y_range": (float(np.min(Y)), float(np.max(Y))),
        "improved": bool(improved),
    }


def _number_nodes(val: float, sig: int = 8) -> list:
    """Nodes for a number with `sig` significant digits; 1.2e-05 -> 1.2·10^(-5)."""
    txt = f"{val:.{sig}g}"
    if "e" in txt:
        mant, ex = txt.split("e")
        sup = _seq_of([CharNode(c) for c in str(int(ex))])
        return [CharNode(c) for c in mant] + [CharNode("·"), CharNode("1"), CharNode("0"), SupNode(exp=sup)]
    return [CharNode(c) for c in txt]


def build_value_seq(name: str, val: float) -> MathSeq:
    return _seq_of(_name_to_nodes(name) + [CharNode("=")] + _number_nodes(val))


def build_function_seq(name: str, args: list, expr) -> MathSeq:
    """MathSeq for the function definition 'name(args) = expr'."""
    arg_nodes = []
    for i, a in enumerate(args):
        if i:
            arg_nodes.append(CharNode(","))
        arg_nodes += _name_to_nodes(a)
    return _seq_of(_name_to_nodes(name) + [ParenNode(inner=_seq_of(arg_nodes)), CharNode("=")] + _sympy_to_nodes(expr))


def serialize_math_seq(seq: MathSeq) -> list:
    items = []
    for it in seq.items:
        if isinstance(it, UnitNode):
            items.append({"t": "unit", "v": it.name})
        elif isinstance(it, CharNode):
            items.append({"t": "char", "v": it.text})
        elif isinstance(it, FracNode):
            items.append({"t": "frac", "num": serialize_math_seq(it.num), "den": serialize_math_seq(it.den)})
        elif isinstance(it, SupNode):
            items.append({"t": "sup", "exp": serialize_math_seq(it.exp)})
        elif isinstance(it, SubNode):
            items.append({"t": "sub", "sub": serialize_math_seq(it.sub)})
        elif isinstance(it, SqrtNode):
            items.append({
                "t": "sqrt",
                "rad": serialize_math_seq(it.radicand),
                "deg": serialize_math_seq(it.degree) if it.degree is not None else None,
            })
        elif isinstance(it, ParenNode):
            items.append({"t": "paren", "in": serialize_math_seq(it.inner)})
        elif isinstance(it, SumNode):
            items.append({
                "t": "sum",
                "low": serialize_math_seq(it.lower),
                "up": serialize_math_seq(it.upper),
                "body": serialize_math_seq(it.body),
            })
        elif isinstance(it, IntNode):
            items.append({
                "t": "int",
                "low": serialize_math_seq(it.lower),
                "up": serialize_math_seq(it.upper),
                "body": serialize_math_seq(it.body),
                "var": serialize_math_seq(it.var),
            })
    return items


def deserialize_math_seq(data: list, parent_node=None) -> MathSeq:
    seq = MathSeq(parent_node)
    for entry in data or []:
        kind = entry.get("t")
        if kind == "char":
            seq.append(CharNode(entry.get("v", "")))
        elif kind == "unit":
            seq.append(UnitNode(entry.get("v", "")))
        elif kind == "frac":
            num = deserialize_math_seq(entry.get("num", []))
            den = deserialize_math_seq(entry.get("den", []))
            seq.append(FracNode(num=num, den=den))
        elif kind == "sup":
            seq.append(SupNode(exp=deserialize_math_seq(entry.get("exp", []))))
        elif kind == "sub":
            seq.append(SubNode(sub=deserialize_math_seq(entry.get("sub", []))))
        elif kind == "sqrt":
            rad = deserialize_math_seq(entry.get("rad", []))
            deg_data = entry.get("deg")
            deg = deserialize_math_seq(deg_data) if deg_data is not None else None
            seq.append(SqrtNode(radicand=rad, degree=deg))
        elif kind == "paren":
            seq.append(ParenNode(inner=deserialize_math_seq(entry.get("in", []))))
        elif kind == "sum":
            node = SumNode(
                lower=deserialize_math_seq(entry.get("low", [])),
                upper=deserialize_math_seq(entry.get("up", [])),
                body=deserialize_math_seq(entry.get("body", [])),
            )
            seq.append(node)
        elif kind == "int":
            node = IntNode(
                lower=deserialize_math_seq(entry.get("low", [])),
                upper=deserialize_math_seq(entry.get("up", [])),
                body=deserialize_math_seq(entry.get("body", [])),
                var=deserialize_math_seq(entry.get("var", [])),
            )
            seq.append(node)
    return seq


# ============================================================================
# Interactive 2D MathBox Widget
# ============================================================================


class MathBox(Gtk.DrawingArea):
    PADDING_X = 8.0
    PADDING_Y = 6.0

    def __init__(self, canvas, x, y):
        super().__init__()
        self.canvas = canvas
        self.x = int(x)
        self.y = int(y)
        self.logical_w = 28
        self.logical_h = 28

        self.root = MathSeq(None)
        self.cursor_seq = self.root
        self.cursor_idx = 0

        self.editing = False
        self.selected = False
        self.dragging = False
        self.drag_start_root_x = 0
        self.drag_start_root_y = 0
        self.drag_start_box_x = 0
        self.drag_start_box_y = 0

        self.eval_result = None
        self.eval_error = False
        self.decimal_places = None  # None = Auto (6 sig figs), or int 0..15 fixed decimals
        self.boxed = False  # Draw permanent solid frame around equation (also exported to PDF)
        self.note = ""  # Excel-style comment: red corner mark, shown when hovering

        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.FOCUS_CHANGE_MASK
        )

        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("key-press-event", self.on_key_press)
        self.connect("focus-out-event", self.on_focus_out)

        self.update_layout()

    def is_empty(self):
        return self.root.is_empty()

    def set_selected(self, selected):
        self.selected = selected
        self.queue_draw()

    def set_decimal_places(self, decimals):
        self.decimal_places = None if decimals is None else max(0, min(15, int(decimals)))
        self.canvas.recalculate_worksheet()
        self.update_layout()
        self.queue_draw()
        if callable(getattr(self.canvas, "on_selection_changed", None)):
            self.canvas.on_selection_changed(self.canvas.selected_box)

    def _open_custom_decimals_dialog(self):
        toplevel = self.get_toplevel()
        parent = toplevel if isinstance(toplevel, Gtk.Window) else None
        dlg = Gtk.Dialog(
            title="Result Decimal Places",
            transient_for=parent,
            flags=0,
        )
        dlg.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK,
            Gtk.ResponseType.OK,
        )
        dlg.set_default_size(300, 120)
        box = dlg.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(14)
        box.set_margin_end(14)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl = Gtk.Label(label="Decimal places (0–15):")
        lbl.set_xalign(0.0)
        adj = Gtk.Adjustment(
            value=float(self.decimal_places if self.decimal_places is not None else 4),
            lower=0.0,
            upper=15.0,
            step_increment=1.0,
            page_increment=2.0,
            page_size=0.0,
        )
        spin = Gtk.SpinButton(adjustment=adj, climb_rate=1.0, digits=0)
        spin.set_numeric(True)
        row.pack_start(lbl, True, True, 0)
        row.pack_start(spin, False, False, 0)
        box.pack_start(row, False, False, 0)
        dlg.show_all()

        if dlg.run() == Gtk.ResponseType.OK:
            val = spin.get_value_as_int()
            dlg.destroy()
            self.canvas.set_decimal_places_for_selected(val, fallback_box=self)
        else:
            dlg.destroy()

    def _show_context_menu(self, event):
        menu = Gtk.Menu()
        cur = self.decimal_places

        if is_equation_box(self.root):
            env = getattr(self.canvas, "last_env", None) or {}
            names = equation_unknowns(self.root, env)
            solve_mi = Gtk.MenuItem(label="Solve for")
            if names:
                sub = Gtk.Menu()
                for nm in names:
                    disp = nm.replace("_", " ") if "_" in nm.strip("_") else nm
                    mi = Gtk.MenuItem(label=disp)
                    mi.connect("activate", lambda _mi, v=nm: self.canvas.solve_equation_box(self, v))
                    sub.append(mi)
                solve_mi.set_submenu(sub)
            else:
                solve_mi.set_sensitive(False)
            menu.append(solve_mi)

            sources = self.canvas.substitution_menu_sources(self)
            subst_mi = Gtk.MenuItem(label="Substitute")
            if sources:
                vmenu = Gtk.Menu()
                for nm in sorted(sources, key=lambda n: (n.lower(), n)):
                    disp = nm.replace("_", " ") if "_" in nm.strip("_") else nm
                    vmi = Gtk.MenuItem(label=disp)
                    smenu = Gtk.Menu()
                    for label, src_root, kind in sources[nm]:
                        text = label if len(label) <= 60 else label[:57] + "…"
                        smi = Gtk.MenuItem(label=f"from {kind}:  {text}")
                        smi.connect(
                            "activate",
                            lambda _mi, v=nm, r=src_root: self.canvas.substitute_into_equation_box(self, v, r),
                        )
                        smenu.append(smi)
                    vmi.set_submenu(smenu)
                    vmenu.append(vmi)
                subst_mi.set_submenu(vmenu)
            else:
                subst_mi.set_sensitive(False)
                subst_mi.set_tooltip_text("No other equation or definition on the sheet shares a variable with this one.")
            menu.append(subst_mi)
            menu.append(Gtk.SeparatorMenuItem())

        box_prefix = "✓ " if self.boxed else "    "
        box_mi = Gtk.MenuItem(label=f"{box_prefix}Box Equation (Border Frame)")
        box_mi.connect(
            "activate",
            lambda _mi: self.canvas.toggle_boxed_for_selected(fallback_box=self),
        )
        menu.append(box_mi)
        menu.append(Gtk.SeparatorMenuItem())

        header_item = Gtk.MenuItem(label="Result Decimal Places")
        header_item.set_sensitive(False)
        menu.append(header_item)
        menu.append(Gtk.SeparatorMenuItem())

        presets = [
            (None, "Auto (Default)"),
            (0, "0 Decimal Places  (12)"),
            (1, "1 Decimal Place   (12.3)"),
            (2, "2 Decimal Places  (12.34)"),
            (3, "3 Decimal Places  (12.345)"),
            (4, "4 Decimal Places  (12.3456)"),
            (5, "5 Decimal Places"),
            (6, "6 Decimal Places"),
            (8, "8 Decimal Places"),
            (10, "10 Decimal Places"),
        ]
        for dec_val, label in presets:
            prefix = "✓ " if cur == dec_val else "    "
            mi = Gtk.MenuItem(label=f"{prefix}{label}")
            mi.connect(
                "activate",
                lambda _mi, d=dec_val: self.canvas.set_decimal_places_for_selected(d, fallback_box=self),
            )
            menu.append(mi)

        menu.append(Gtk.SeparatorMenuItem())
        custom_mi = Gtk.MenuItem(label="    Custom Decimal Places...")
        custom_mi.connect("activate", lambda _mi: self._open_custom_decimals_dialog())
        menu.append(custom_mi)

        menu.append(Gtk.SeparatorMenuItem())
        note_mi = Gtk.MenuItem(label="Edit Note…" if self.note else "Add Note…")
        note_mi.connect("activate", lambda _mi: GLib.idle_add(lambda: self.edit_note() and False))
        menu.append(note_mi)
        if self.note:
            dn_mi = Gtk.MenuItem(label="Delete Note")
            dn_mi.connect("activate", lambda _mi: self.set_note(""))
            menu.append(dn_mi)

        menu.append(Gtk.SeparatorMenuItem())
        del_mi = Gtk.MenuItem(label="Delete Selected")
        del_mi.connect("activate", lambda _mi: self.canvas.remove_selected_boxes(self))
        menu.append(del_mi)

        menu.show_all()
        menu.popup_at_pointer(event)

    def set_note(self, text: str):
        self.note = (text or "").strip()
        self.set_tooltip_text(self.note if self.note else None)
        self.queue_draw()

    def edit_note(self):
        toplevel = self.get_toplevel()
        dlg = Gtk.Dialog(
            title="Note",
            transient_for=toplevel if isinstance(toplevel, Gtk.Window) else None,
            flags=0,
        )
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        dlg.set_default_size(380, 200)
        area = dlg.get_content_area()
        for side in ("start", "end", "top", "bottom"):
            getattr(area, f"set_margin_{side}")(12)
        area.set_spacing(6)
        area.pack_start(Gtk.Label(label="Note for this equation (shown when the mouse is over it):", xalign=0.0),
                        False, False, 0)
        tv = Gtk.TextView()
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.get_buffer().set_text(self.note)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.add(tv)
        area.pack_start(sw, True, True, 0)
        dlg.show_all()
        tv.grab_focus()
        if dlg.run() == Gtk.ResponseType.OK:
            buf = tv.get_buffer()
            self.set_note(buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False))
        dlg.destroy()
        return True

    def start_editing(self):
        self.editing = True
        self.dragging = False
        self.selected = True
        self.canvas.focus_without_scroll(self)
        self.update_layout()
        self.queue_draw()

    def stop_editing(self):
        if not self.editing:
            return
        if getattr(self, "_unit_entry", None) is not None:
            self._commit_unit_entry(recalc=False)
        self.editing = False
        if self.is_empty():
            self.canvas.remove_box(self)
            return
        self.canvas.recalculate_worksheet()
        self.update_layout()
        self.queue_draw()

    def _set_result_gap(self, pango_ctx) -> bool:
        """Leave room after the '=' for the result when a result unit follows it."""
        j = result_unit_split(self.root.items) if self.eval_result is not None else None
        if j is None:
            self.root.result_gap = None
            return False
        _, rw, _, _ = MathRenderer._make_layout(pango_ctx, f" {self.eval_result}", 1.0, bold=True)
        self.root.result_gap = (j, rw + 2.0)
        return True

    def update_layout(self):
        _sched = getattr(getattr(self, "canvas", None), "schedule_page_breaks", None)
        if _sched:
            _sched()
        pango_ctx = self.get_pango_context()
        in_gap = self._set_result_gap(pango_ctx)
        MathRenderer.measure_seq(pango_ctx, self.root, 1.0)
        extra_w = 0.0
        if self.eval_result is not None and not in_gap:
            _, rw, _, _ = MathRenderer._make_layout(pango_ctx, f" {self.eval_result}", 1.0, bold=True)
            extra_w = rw + 6.0
        w = max(28, int(math.ceil(self.root.width + extra_w + self.PADDING_X * 2)))
        h = max(28, int(math.ceil(self.root.height + self.PADDING_Y * 2)))
        self.logical_w = w
        self.logical_h = h
        z = getattr(self.canvas, "zoom", 1.0)
        self.set_size_request(max(16, int(math.ceil(w * z))), max(16, int(math.ceil(h * z))))
        self.queue_draw()

    def draw_content(self, cr, theme=None, for_export=False):
        if theme is None:
            theme = THEMES[self.canvas.theme_name]
        w, h = self.logical_w, self.logical_h

        # Background fill when editing
        if self.editing and not for_export:
            cr.save()
            cr.set_source_rgba(*theme["box_editing_bg"])
            cr.rectangle(0, 0, w, h)
            cr.fill()
            cr.restore()

        # Permanent equation box border (visible on sheet and in PDF export)
        if self.boxed:
            cr.save()
            cr.set_source_rgb(*theme["heading_text"])
            cr.set_line_width(1.6)
            cr.rectangle(1.0, 1.0, w - 2.0, h - 2.0)
            cr.stroke()
            cr.restore()

        # Render 2D equation tree
        pango_ctx = self.get_pango_context()
        in_gap = self._set_result_gap(pango_ctx)
        MathRenderer.measure_seq(pango_ctx, self.root, 1.0)
        baseline_y = self.PADDING_Y + self.root.ascent
        MathRenderer.draw_seq(cr, pango_ctx, self.root, self.PADDING_X, baseline_y, theme)

        # Render evaluation result (if expression ends with '=', or '= unit')
        if self.eval_result is not None:
            res_x = self.root.result_gap_x if in_gap else self.PADDING_X + self.root.width
            layout, _, r_asc, _ = MathRenderer._make_layout(
                pango_ctx, f" {self.eval_result}", 1.0, bold=True
            )
            cr.save()
            cr.set_source_rgb(*(theme["error"] if self.eval_error else theme["result"]))
            cr.move_to(res_x, baseline_y - r_asc)
            PangoCairo.show_layout(cr, layout)
            cr.restore()

        if for_export:
            return

        # Render active 2D cursor & slot highlight
        if self.editing:
            seq = self.cursor_seq
            idx = max(0, min(self.cursor_idx, len(seq.caret_positions) - 1))
            if seq.caret_positions:
                cx = seq.caret_positions[idx]
                cy_top = seq.abs_y
                cy_bot = seq.abs_y + seq.height
                cr.save()
                cr.set_source_rgb(*theme["cursor"])
                cr.set_line_width(1.8)
                cr.move_to(cx, cy_top)
                cr.line_to(cx, cy_bot)
                cr.stroke()
                cr.restore()

        # Selection or Editing frame
        if self.editing:
            cr.save()
            cr.set_source_rgb(*theme["box_editing_border"])
            cr.set_line_width(1.2)
            cr.rectangle(0.6, 0.6, w - 1.2, h - 1.2)
            cr.stroke()
            cr.restore()
        elif self.selected:
            cr.save()
            cr.set_source_rgb(*theme["box_selected_border"])
            cr.set_line_width(1.2)
            cr.set_dash([4.0, 3.0])
            cr.rectangle(0.6, 0.6, w - 1.2, h - 1.2)
            cr.stroke()
            cr.restore()

        # Note marker: small red triangle in the top-right corner (screen only)
        if getattr(self, "note", "") and not for_export:
            t = 7.0
            cr.save()
            cr.set_source_rgb(0.86, 0.12, 0.12)
            cr.move_to(w - t, 0)
            cr.line_to(w, 0)
            cr.line_to(w, t)
            cr.close_path()
            cr.fill()
            cr.restore()

    def on_draw(self, widget, cr):
        z = getattr(self.canvas, "zoom", 1.0)
        cr.save()
        cr.scale(z, z)
        self.draw_content(cr, for_export=False)
        cr.restore()
        return True

    # ------------------------------------------------------------------------
    # Mouse Handling (Single-click select/drag, Double-click or click-inside edit)
    # ------------------------------------------------------------------------

    def _hit_test_seq(self, seq: MathSeq, mx: float, my: float):
        """Find the deepest (MathSeq, index) closest to mouse (mx, my)."""
        for item in seq.items:
            for child_seq in item.slots():
                if (
                    child_seq.abs_x - 3 <= mx <= child_seq.abs_x + child_seq.width + 3
                    and child_seq.abs_y - 3 <= my <= child_seq.abs_y + child_seq.height + 3
                ):
                    return self._hit_test_seq(child_seq, mx, my)

        best_idx = 0
        best_dist = float("inf")
        for idx, cx in enumerate(seq.caret_positions):
            d = abs(mx - cx)
            if d < best_dist:
                best_dist = d
                best_idx = idx
        return seq, best_idx

    def on_button_press(self, widget, event):
        if event.button == 1:
            z = getattr(self.canvas, "zoom", 1.0)
            lx, ly = event.x / z, event.y / z
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.canvas.select_box(self)
                self.start_editing()
                seq, idx = self._hit_test_seq(self.root, lx, ly)
                self.cursor_seq = seq
                self.cursor_idx = idx
                self.queue_draw()
                return True

            if self.editing:
                seq, idx = self._hit_test_seq(self.root, lx, ly)
                self.cursor_seq = seq
                self.cursor_idx = idx
                self.canvas.focus_without_scroll(self)
                self.queue_draw()
                return True
            else:
                self.canvas.handle_box_button_press(self, event)
                self.dragging = True
                self.drag_start_root_x = event.x_root
                self.drag_start_root_y = event.y_root
                self.drag_start_box_x = self.x
                self.drag_start_box_y = self.y
                return True
        elif event.button == 3:
            if self not in self.canvas.selected_boxes:
                self.canvas.select_box(self)
            self._show_context_menu(event)
            return True
        return False

    def on_motion_notify(self, widget, event):
        if self.dragging and not self.editing:
            z = getattr(self.canvas, "zoom", 1.0)
            dx = int((event.x_root - self.drag_start_root_x) / z)
            dy = int((event.y_root - self.drag_start_root_y) / z)
            self.canvas.drag_box_or_group(self, dx, dy)
            return True
        return False

    def on_button_release(self, widget, event):
        if event.button == 1 and self.dragging:
            self.dragging = False
            self.canvas.recalculate_worksheet()
            return True
        return False

    def on_focus_out(self, widget, event):
        # Note: toolbar clicks keep editing active via can_focus=False on toolbar buttons
        self.stop_editing()
        return False

    # ------------------------------------------------------------------------
    # 2D Structural Keyboard Editing & Navigation
    # ------------------------------------------------------------------------

    def _extract_preceding_term(self, seq: MathSeq, idx: int) -> MathSeq:
        """Pop the contiguous term immediately before idx (for '/' fraction creation)."""
        start = idx
        while start > 0:
            prev = seq.items[start - 1]
            if isinstance(prev, CharNode) and prev.is_operator():
                break
            start -= 1
        extracted = MathSeq()
        for it in seq.items[start:idx]:
            extracted.append(it)
        del seq.items[start:idx]
        self.cursor_idx = start
        return extracted

    def _trailing_word(self, seq: MathSeq, idx: int):
        """Return (start_idx, word_str) of contiguous ASCII letters before idx."""
        start = idx
        chars = []
        while start > 0 and isinstance(seq.items[start - 1], CharNode):
            ch = seq.items[start - 1].text
            if len(ch) == 1 and ch.isalpha() and not tok_has_dot(ch):
                chars.append(ch)
                start -= 1
            else:
                break
        chars.reverse()
        return start, "".join(chars)

    def _try_convert_trailing_word(self):
        """Convert trailing 'sqrt', 'sum', 'int', or Greek name into 2D symbol/node."""
        start, word = self._trailing_word(self.cursor_seq, self.cursor_idx)
        if not word:
            return False
        if word == "sqrt":
            del self.cursor_seq.items[start : self.cursor_idx]
            self.cursor_idx = start
            self.insert_sqrt()
            return True
        if word == "root":
            del self.cursor_seq.items[start : self.cursor_idx]
            self.cursor_idx = start
            self.insert_nth_root()
            return True
        if word == "sum":
            del self.cursor_seq.items[start : self.cursor_idx]
            self.cursor_idx = start
            self.insert_sum()
            return True
        if word == "int":
            del self.cursor_seq.items[start : self.cursor_idx]
            self.cursor_idx = start
            self.insert_integral()
            return True
        if word in GREEK_AUTOCOMPLETE:
            del self.cursor_seq.items[start : self.cursor_idx]
            self.cursor_idx = start
            self.insert_char(GREEK_AUTOCOMPLETE[word])
            return True
        return False

    def insert_dot_accent(self):
        """Dot above (time derivative): toggles the dot on the letter left of the cursor;
        with no letter there, the next letter typed gets the dot."""
        prev = self.cursor_seq.items[self.cursor_idx - 1] if self.cursor_idx > 0 else None
        if isinstance(prev, CharNode) and tok_is_letter(prev.text):
            prev.text = tok_toggle_dot(prev.text)
            self._pending_dot = False
            self._after_edit()
        else:
            self._pending_dot = True
        self.canvas.focus_without_scroll(self)

    def insert_char(self, text: str):
        if getattr(self, "_pending_dot", False):
            self._pending_dot = False
            if tok_is_letter(text) and not tok_has_dot(text):
                text = tok_toggle_dot(text)
        node = CharNode(text)
        self.cursor_seq.insert(self.cursor_idx, node)
        self.cursor_idx += 1
        self._after_edit()

    def insert_unit(self, name: str = ""):
        """Insert a unit after the cursor; with no name, start typing one (the ' key)."""
        if getattr(self, "_unit_entry", None) is not None:
            self._commit_unit_entry(recalc=False)
        node = UnitNode(name)
        self.cursor_seq.insert(self.cursor_idx, node)
        self.cursor_idx += 1
        self._unit_entry = None if name else node
        self._after_edit()

    def _unit_entry_active(self):
        ue = getattr(self, "_unit_entry", None)
        if ue is None:
            return None
        if self.cursor_idx > 0 and self.cursor_seq.items[self.cursor_idx - 1] is ue:
            return ue
        self._commit_unit_entry()
        return None

    def _commit_unit_entry(self, recalc=True):
        """Finish the unit being typed: spellings like ohm / degC / um become Ω / °C / μm;
        an empty unit is removed."""
        node = getattr(self, "_unit_entry", None)
        self._unit_entry = None
        if node is None:
            return
        seq = getattr(node, "parent_seq", None)
        if not node.name:
            if seq is not None and node in seq.items:
                i = seq.items.index(node)
                del seq.items[i]
                if self.cursor_seq is seq and self.cursor_idx > i:
                    self.cursor_idx -= 1
        else:
            node.name = normalize_unit_name(node.name)
        if recalc:
            self._after_edit()

    def insert_fraction(self):
        num_seq = self._extract_preceding_term(self.cursor_seq, self.cursor_idx)
        frac = FracNode(num=num_seq)
        self.cursor_seq.insert(self.cursor_idx, frac)
        if num_seq.is_empty():
            self.cursor_seq = frac.num
            self.cursor_idx = 0
        else:
            self.cursor_seq = frac.den
            self.cursor_idx = 0
        self._after_edit()

    def insert_superscript(self):
        sup = SupNode()
        self.cursor_seq.insert(self.cursor_idx, sup)
        self.cursor_seq = sup.exp
        self.cursor_idx = 0
        self._after_edit()

    def insert_subscript(self):
        sub = SubNode()
        self.cursor_seq.insert(self.cursor_idx, sub)
        self.cursor_seq = sub.sub
        self.cursor_idx = 0
        self._after_edit()

    def insert_sqrt(self):
        sq = SqrtNode()
        self.cursor_seq.insert(self.cursor_idx, sq)
        self.cursor_seq = sq.radicand
        self.cursor_idx = 0
        self._after_edit()

    def insert_nth_root(self):
        sq = SqrtNode(degree=MathSeq())
        self.cursor_seq.insert(self.cursor_idx, sq)
        self.cursor_seq = sq.degree
        self.cursor_idx = 0
        self._after_edit()

    def insert_parens(self):
        p = ParenNode()
        self.cursor_seq.insert(self.cursor_idx, p)
        self.cursor_seq = p.inner
        self.cursor_idx = 0
        self._after_edit()

    def insert_vector_brackets(self):
        """Insert [ ] brackets and place the cursor between them for entering a discrete vector."""
        self.cursor_seq.insert(self.cursor_idx, CharNode("["))
        self.cursor_seq.insert(self.cursor_idx + 1, CharNode("]"))
        self.cursor_idx += 1
        self._after_edit()

    def insert_text_tokens(self, text: str):
        """Insert a sequence of characters/tokens directly at the cursor."""
        for ch in text:
            self.cursor_seq.insert(self.cursor_idx, CharNode(ch))
            self.cursor_idx += 1
        self._after_edit()

    def insert_sum(self):
        s = SumNode()
        s.lower.append(CharNode("k"))
        s.lower.append(CharNode("="))
        s.lower.append(CharNode("1"))
        self.cursor_seq.insert(self.cursor_idx, s)
        self.cursor_seq = s.upper
        self.cursor_idx = 0
        self._after_edit()

    def insert_integral(self):
        it = IntNode()
        it.var.append(CharNode("x"))
        self.cursor_seq.insert(self.cursor_idx, it)
        self.cursor_seq = it.lower
        self.cursor_idx = 0
        self._after_edit()

    def move_left(self):
        if self.cursor_idx > 0:
            prev_node = self.cursor_seq.items[self.cursor_idx - 1]
            slots = prev_node.slots()
            if slots:
                self.cursor_seq = slots[-1]
                self.cursor_idx = len(self.cursor_seq.items)
            else:
                self.cursor_idx -= 1
        elif self.cursor_seq.parent_node is not None:
            parent_node = self.cursor_seq.parent_node
            slots = parent_node.slots()
            s_idx = slots.index(self.cursor_seq)
            if s_idx > 0:
                self.cursor_seq = slots[s_idx - 1]
                self.cursor_idx = len(self.cursor_seq.items)
            else:
                parent_seq = parent_node.parent_seq
                self.cursor_idx = parent_seq.items.index(parent_node)
                self.cursor_seq = parent_seq
        self.queue_draw()

    def move_right(self):
        if self.cursor_idx < len(self.cursor_seq.items):
            next_node = self.cursor_seq.items[self.cursor_idx]
            slots = next_node.slots()
            if slots:
                self.cursor_seq = slots[0]
                self.cursor_idx = 0
            else:
                self.cursor_idx += 1
        elif self.cursor_seq.parent_node is not None:
            parent_node = self.cursor_seq.parent_node
            slots = parent_node.slots()
            s_idx = slots.index(self.cursor_seq)
            if s_idx + 1 < len(slots):
                self.cursor_seq = slots[s_idx + 1]
                self.cursor_idx = 0
            else:
                parent_seq = parent_node.parent_seq
                self.cursor_idx = parent_seq.items.index(parent_node) + 1
                self.cursor_seq = parent_seq
        self.queue_draw()

    def step_out_slot(self):
        """Step out of the current 2D construct (Space / Tab), like SMath & MS Equation."""
        if self.cursor_seq.parent_node is not None:
            parent_node = self.cursor_seq.parent_node
            slots = parent_node.slots()
            s_idx = slots.index(self.cursor_seq)
            if s_idx + 1 < len(slots):
                self.cursor_seq = slots[s_idx + 1]
                self.cursor_idx = len(self.cursor_seq.items)
            else:
                parent_seq = parent_node.parent_seq
                self.cursor_idx = parent_seq.items.index(parent_node) + 1
                self.cursor_seq = parent_seq
            self.queue_draw()

    def move_up(self):
        seq = self.cursor_seq
        while seq is not None and seq.parent_node is not None:
            p = seq.parent_node
            if isinstance(p, FracNode) and seq is p.den:
                self.cursor_seq = p.num
                self.cursor_idx = min(self.cursor_idx, len(p.num.items))
                self.queue_draw()
                return
            if isinstance(p, (SumNode, IntNode)) and seq is p.lower:
                self.cursor_seq = p.upper
                self.cursor_idx = min(self.cursor_idx, len(p.upper.items))
                self.queue_draw()
                return
            seq = p.parent_seq

    def move_down(self):
        seq = self.cursor_seq
        while seq is not None and seq.parent_node is not None:
            p = seq.parent_node
            if isinstance(p, FracNode) and seq is p.num:
                self.cursor_seq = p.den
                self.cursor_idx = min(self.cursor_idx, len(p.den.items))
                self.queue_draw()
                return
            if isinstance(p, (SumNode, IntNode)) and seq is p.upper:
                self.cursor_seq = p.lower
                self.cursor_idx = min(self.cursor_idx, len(p.lower.items))
                self.queue_draw()
                return
            seq = p.parent_seq

    def handle_backspace(self):
        if self.cursor_idx > 0:
            prev_node = self.cursor_seq.items[self.cursor_idx - 1]
            slots = prev_node.slots()
            if not slots:
                del self.cursor_seq.items[self.cursor_idx - 1]
                self.cursor_idx -= 1
            else:
                if all(s.is_empty() for s in slots):
                    del self.cursor_seq.items[self.cursor_idx - 1]
                    self.cursor_idx -= 1
                else:
                    self.cursor_seq = slots[-1]
                    self.cursor_idx = len(self.cursor_seq.items)
        elif self.cursor_seq.parent_node is not None:
            parent_node = self.cursor_seq.parent_node
            parent_seq = parent_node.parent_seq
            p_idx = parent_seq.items.index(parent_node)
            if isinstance(parent_node, FracNode) and self.cursor_seq is parent_node.den and parent_node.den.is_empty():
                # Unwrap numerator back into parent_seq
                num_items = parent_node.num.items
                del parent_seq.items[p_idx]
                for offset, it in enumerate(num_items):
                    parent_seq.insert(p_idx + offset, it)
                self.cursor_seq = parent_seq
                self.cursor_idx = p_idx + len(num_items)
            elif all(s.is_empty() for s in parent_node.slots()):
                del parent_seq.items[p_idx]
                self.cursor_seq = parent_seq
                self.cursor_idx = p_idx
            else:
                self.move_left()
                return
        self._after_edit()

    def handle_delete(self):
        """Forward delete: remove what is right of the cursor (mirror of Backspace)."""
        seq = self.cursor_seq
        if self.cursor_idx < len(seq.items):
            nxt = seq.items[self.cursor_idx]
            slots = nxt.slots()
            if not slots or all(sl.is_empty() for sl in slots):
                del seq.items[self.cursor_idx]
            else:
                # Step into the structure (fraction, power, brackets, …) instead of wiping it
                self.cursor_seq = slots[0]
                self.cursor_idx = 0
                self.queue_draw()
                return
        elif seq.parent_node is not None:
            parent_node = seq.parent_node
            parent_seq = parent_node.parent_seq
            p_idx = parent_seq.items.index(parent_node)
            if all(sl.is_empty() for sl in parent_node.slots()):
                del parent_seq.items[p_idx]
                self.cursor_seq = parent_seq
                self.cursor_idx = p_idx
            else:
                self.move_right()
                return
        else:
            return
        self._after_edit()

    def _after_edit(self):
        self.canvas.recalculate_worksheet()
        self.update_layout()

    def _step_out_to_root_if_needed(self):
        """Step out of ParenNode / SupNode / SubNode / SqrtNode / FracNode to root before ':=' or '='."""
        seq = self.cursor_seq
        while seq.parent_node is not None:
            if isinstance(seq.parent_node, (SumNode, IntNode)) and seq is seq.parent_node.lower:
                return
            p_node = seq.parent_node
            p_seq = p_node.parent_seq
            self.cursor_idx = p_seq.items.index(p_node) + 1
            self.cursor_seq = p_seq
            seq = self.cursor_seq

    def on_key_press(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            return False
        keyname = Gdk.keyval_name(event.keyval)

        if not self.editing:
            if keyname in ("Delete", "BackSpace"):
                self.canvas.remove_selected_boxes(self)
                return True
            if keyname in ("Return", "KP_Enter"):
                self.start_editing()
                return True
            return False

        # Typing a unit after an apostrophe: letters (and °) go into the unit name
        ch_u = chr(Gdk.keyval_to_unicode(event.keyval)) if Gdk.keyval_to_unicode(event.keyval) else ""
        if getattr(event, "is_modifier", False) or keyname in _MODIFIER_KEYS:
            return False  # Shift / AltGr / Caps Lock alone must not end a unit being typed
        ue = self._unit_entry_active()
        if ue is not None:
            if ch_u and (ch_u.isalpha() or ch_u == "°"):
                ue.name += ch_u
                self._after_edit()
                return True
            if keyname == "BackSpace":
                if ue.name:
                    ue.name = ue.name[:-1]
                    self._after_edit()
                else:
                    self._commit_unit_entry()  # removes the empty unit
                return True
            self._commit_unit_entry()
            if keyname in ("space", "Tab"):
                return True
        elif keyname == "BackSpace" and self.cursor_idx > 0 and isinstance(
                self.cursor_seq.items[self.cursor_idx - 1], UnitNode):
            # Backspace into a unit edits it again
            prev_u = self.cursor_seq.items[self.cursor_idx - 1]
            prev_u.name = prev_u.name[:-1]
            self._unit_entry = prev_u
            self._after_edit()
            return True
        if ch_u == "'":
            self._try_convert_trailing_word()
            self.insert_unit("")
            return True

        # Navigation keys
        if keyname == "Left":
            self.move_left()
            return True
        if keyname == "Right":
            self.move_right()
            return True
        if keyname == "Up":
            self.move_up()
            return True
        if keyname == "Down":
            self.move_down()
            return True
        if keyname in ("Tab", "ISO_Left_Tab"):
            if not self._try_convert_trailing_word():
                self.step_out_slot()
            return True
        if keyname == "space":
            if not self._try_convert_trailing_word():
                self.step_out_slot()
            return True
        if keyname == "Escape":
            self._try_convert_trailing_word()
            self.stop_editing()
            return True
        if keyname in ("Return", "KP_Enter"):
            self._try_convert_trailing_word()
            self.canvas.exit_box_and_move_down(self)
            return True
        if keyname == "BackSpace":
            self.handle_backspace()
            return True
        if keyname in ("Delete", "KP_Delete"):
            self.handle_delete()
            return True

        # Structural 2D math shortcuts (SMath / Mathcad / MS Equation style)
        ch = chr(Gdk.keyval_to_unicode(event.keyval)) if Gdk.keyval_to_unicode(event.keyval) else ""

        # Auto-step-out of SubNode on any operator or delimiter
        if isinstance(self.cursor_seq.parent_node, SubNode) and len(self.cursor_seq.items) > 0:
            if ch in ("+", "-", "*", "/", "^", "(", ")", ":", "=", ",", ";"):
                self.step_out_slot()

        # Auto-step-out of SupNode when typing '+', '-', ',', ';' after at least 1 token (so x^2+a -> x² + a)
        if isinstance(self.cursor_seq.parent_node, SupNode) and len(self.cursor_seq.items) > 0:
            if ch in ("+", "-", ",", ";"):
                self._try_convert_trailing_word()
                self.step_out_slot()

        if ch == "/":
            self._try_convert_trailing_word()
            self.insert_fraction()
            return True
        if ch == "^":
            self._try_convert_trailing_word()
            self.insert_superscript()
            return True
        if ch == "_":
            self._try_convert_trailing_word()
            self.insert_subscript()
            return True
        if ch == "\\":
            self._try_convert_trailing_word()
            self.insert_sqrt()
            return True
        if ch == "(":
            if not self._try_convert_trailing_word():
                self.insert_parens()
            return True
        if ch == ")":
            self._try_convert_trailing_word()
            seq = self.cursor_seq
            while seq is not None and seq.parent_node is not None:
                if isinstance(seq.parent_node, ParenNode):
                    parent_node = seq.parent_node
                    parent_seq = parent_node.parent_seq
                    self.cursor_idx = parent_seq.items.index(parent_node) + 1
                    self.cursor_seq = parent_seq
                    self.queue_draw()
                    break
                seq = seq.parent_node.parent_seq
            return True
        if ch == ":":
            self._try_convert_trailing_word()
            self._step_out_to_root_if_needed()
            self.insert_char(":=")
            return True
        if ch == "=":
            self._try_convert_trailing_word()
            self._step_out_to_root_if_needed()
            # A single '=' defines (a = 5) or evaluates (a =). A second '=' right after it
            # turns it into an equation '==' (y == 2x + 4) that can be solved for a variable.
            if self.cursor_idx > 0 and isinstance(self.cursor_seq.items[self.cursor_idx - 1], CharNode):
                prev_node = self.cursor_seq.items[self.cursor_idx - 1]
                prev_txt = prev_node.text
                if prev_txt == "=" and self.cursor_seq is self.root:
                    prev_node.text = EQ_TOKEN
                    self._after_edit()
                    return True
                if prev_txt in (":=", "=", EQ_TOKEN):
                    return True
                if prev_txt == "<":
                    self.cursor_seq.items[self.cursor_idx - 1].text = "≤"
                    self._after_edit()
                    return True
                if prev_txt == ">":
                    self.cursor_seq.items[self.cursor_idx - 1].text = "≥"
                    self._after_edit()
                    return True
                if prev_txt == "!":
                    self.cursor_seq.items[self.cursor_idx - 1].text = "≠"
                    self._after_edit()
                    return True
            self.insert_char("=")
            return True
        if ch == "*":
            self._try_convert_trailing_word()
            self.insert_char("·")
            return True
        if ch == '"' and self.is_empty():
            # SMath Studio shortcut: typing '"' in an empty box converts it into a TextBox (defaulting to normal style)
            x, y = self.x, self.y
            canvas = self.canvas
            self.editing = False
            canvas.remove_box(self)
            canvas.create_text_box(x, y, style_name="normal", edit=True)
            return True

        # Printable characters (digits, letters, +, -, ., ,, etc.)
        if ch and ch.isprintable():
            if not ch.isalpha():
                self._try_convert_trailing_word()
            self.insert_char(ch)
            return True

        return False


# ============================================================================
# Styled Text Box Widget (Title, Heading 1, Heading 2, Heading 3, Normal)
# ============================================================================


class TextBox(Gtk.DrawingArea):
    PADDING_X = 8.0
    PADDING_Y = 5.0

    def __init__(self, canvas, x, y, style_name="normal", text="", bold=False, underline=False):
        super().__init__()
        self.canvas = canvas
        self.x = int(x)
        self.y = int(y)
        self.logical_w = 60
        self.logical_h = 28
        self.bold = bool(bold)
        self.underline = bool(underline)
        self.style_name = style_name if style_name in TEXT_STYLES else "normal"
        self.text = text
        self.cursor_pos = len(text)
        self.heading_number = ""  # "1.2" for headings, set by MathCanvas.renumber_headings

        self.editing = False
        self.selected = False
        self.dragging = False
        self.drag_start_root_x = 0
        self.drag_start_root_y = 0
        self.drag_start_box_x = 0
        self.drag_start_box_y = 0

        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.FOCUS_CHANGE_MASK
        )

        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("key-press-event", self.on_key_press)
        self.connect("focus-out-event", self.on_focus_out)

        self.update_layout()

    def is_empty(self):
        return len(self.text.strip()) == 0

    def set_style_name(self, style_name: str):
        if style_name in TEXT_STYLES:
            self.style_name = style_name
            if style_name not in HEADING_LEVELS:
                self.heading_number = ""
            else:
                old = self.text
                self.text = strip_manual_heading_number(self.text)
                self.cursor_pos = max(0, min(len(self.text), self.cursor_pos - (len(old) - len(self.text))))
            self.update_layout()
            if self in self.canvas.boxes:
                self.canvas.move_box(self, self.x, self.y)  # headings snap to their fixed indentation
                self.canvas.renumber_headings()
            self.queue_draw()

    def set_heading_number(self, number: str):
        if number != self.heading_number:
            self.heading_number = number
            self.update_layout()

    def _font_desc(self):
        fd = Pango.FontDescription.from_string(TEXT_STYLES[self.style_name]["font"])
        if getattr(self, "bold", False):
            fd.set_weight(Pango.Weight.BOLD)
        return fd

    def set_format(self, bold=None, underline=None):
        if bold is not None:
            self.bold = bool(bold)
        if underline is not None:
            self.underline = bool(underline)
        self.update_layout()
        self.queue_draw()

    def _number_width(self) -> float:
        """Width reserved for the heading number (plus a gap), 0 for non-headings."""
        if not self.heading_number:
            return 0.0
        layout = Pango.Layout.new(self.get_pango_context())
        layout.set_font_description(self._font_desc())
        layout.set_text(self.heading_number, -1)
        _, logical = layout.get_pixel_extents()
        return float(logical.width) + 12.0

    def _text_x(self) -> float:
        return self.PADDING_X + self._number_width()

    def _show_context_menu(self, event):
        menu = Gtk.Menu()
        header = Gtk.MenuItem(label="Text Style")
        header.set_sensitive(False)
        menu.append(header)
        group = None
        for sid in ("title", "subtitle", "heading1", "heading2", "heading3", "normal"):
            cfg = TEXT_STYLES[sid]
            size = cfg["font"].split()[-1]
            mi = Gtk.RadioMenuItem.new_with_label_from_widget(group, f"{cfg['label']}  ({size} pt)")
            group = mi
            mi.set_active(sid == self.style_name)
            mi.connect(
                "toggled",
                lambda w, st=sid: w.get_active() and self.canvas.set_style_for_text_boxes(st, fallback_box=self),
            )
            menu.append(mi)
        menu.append(Gtk.SeparatorMenuItem())
        for label, attr in (("Bold  (Ctrl+B)", "bold"), ("Underline  (Ctrl+U)", "underline")):
            ci = Gtk.CheckMenuItem(label=label)
            ci.set_active(getattr(self, attr))
            ci.connect("toggled", lambda w, a=attr: self.canvas.toggle_text_format(a, fallback_box=self))
            menu.append(ci)
        menu.append(Gtk.SeparatorMenuItem())
        edit_mi = Gtk.MenuItem(label="Edit Text")
        edit_mi.connect("activate", lambda _mi: self.start_editing())
        menu.append(edit_mi)
        del_mi = Gtk.MenuItem(label="Delete")
        del_mi.connect("activate", lambda _mi: self.canvas.remove_selected_boxes(self))
        menu.append(del_mi)
        menu.show_all()
        menu.popup_at_pointer(event)

    def set_selected(self, selected):
        self.selected = selected
        self.queue_draw()

    def start_editing(self):
        self.editing = True
        self.dragging = False
        self.selected = True
        self.canvas.focus_without_scroll(self)
        self.update_layout()
        self.queue_draw()

    def stop_editing(self):
        if not self.editing:
            return
        self.editing = False
        if self.is_empty():
            self.canvas.remove_box(self)
            return
        self.update_layout()
        self.queue_draw()

    def _create_pango_layout(self, display_text=None):
        pango_ctx = self.get_pango_context()
        layout = Pango.Layout.new(pango_ctx)
        layout.set_font_description(self._font_desc())
        if TEXT_STYLES[self.style_name].get("centered"):
            # Centered styles span the page between the margins
            max_w = int(self.canvas.A4_WIDTH - 2 * self.canvas.PAGE_MARGIN - self.PADDING_X * 2)
            layout.set_alignment(Pango.Alignment.CENTER)
        else:
            max_w = max(120, self.canvas.A4_WIDTH - self.x - self.canvas.PAGE_MARGIN
                        - int(self.PADDING_X * 2) - int(self._number_width()))
        layout.set_width(max_w * Pango.SCALE)
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        layout.set_line_spacing(line_spacing_factor(pango_ctx, self._font_desc()))
        txt = self.text if display_text is None else display_text
        layout.set_text(txt, -1)
        if getattr(self, "underline", False) and txt:
            attrs = Pango.AttrList()
            attrs.insert(Pango.attr_underline_new(Pango.Underline.SINGLE))
            layout.set_attributes(attrs)
        return layout

    def update_layout(self):
        _sched = getattr(getattr(self, "canvas", None), "schedule_page_breaks", None)
        if _sched:
            _sched()
        style_cfg = TEXT_STYLES[self.style_name]
        placeholder = f"[{style_cfg['label']}]"
        shown = self.text if self.text else placeholder
        layout = self._create_pango_layout(shown)
        _, logical = layout.get_pixel_extents()
        extra_h = 6 if style_cfg["underline_bar"] else 0
        w = int(math.ceil(max(logical.width, 40) + self._number_width() + self.PADDING_X * 2 + 4))
        if style_cfg.get("centered"):
            # Title / subtitle span the full page width between the margins
            w = int(self.canvas.A4_WIDTH - 2 * self.canvas.PAGE_MARGIN)
        h = int(math.ceil(max(logical.height, 20) + self.PADDING_Y * 2 + extra_h))
        self.logical_w = w
        self.logical_h = h
        z = getattr(self.canvas, "zoom", 1.0)
        self.set_size_request(max(16, int(math.ceil(w * z))), max(16, int(math.ceil(h * z))))
        self.queue_draw()
        self.canvas.notify_toc_changed()

    def draw_content(self, cr, theme=None, for_export=False):
        if theme is None:
            theme = THEMES[self.canvas.theme_name]
        style_cfg = TEXT_STYLES[self.style_name]
        w, h = self.logical_w, self.logical_h

        if self.editing and not for_export:
            cr.save()
            cr.set_source_rgba(*theme["box_editing_bg"])
            cr.rectangle(0, 0, w, h)
            cr.fill()
            cr.restore()

        if self.text:
            layout = self._create_pango_layout(self.text)
            color = theme[style_cfg["color_key"]]
        else:
            if for_export:
                return
            layout = self._create_pango_layout(f"[{style_cfg['label']}]")
            color = theme["muted_text"]

        tx = self._text_x()
        if self.heading_number:
            num_layout = Pango.Layout.new(self.get_pango_context())
            num_layout.set_font_description(self._font_desc())
            num_layout.set_text(self.heading_number, -1)
            cr.save()
            cr.set_source_rgb(*theme[style_cfg["color_key"]])
            cr.move_to(self.PADDING_X, self.PADDING_Y)
            PangoCairo.show_layout(cr, num_layout)
            cr.restore()

        cr.save()
        cr.set_source_rgb(*color)
        cr.move_to(tx, self.PADDING_Y)
        PangoCairo.show_layout(cr, layout)
        cr.restore()

        # Title accent line: only under the text itself (last line if wrapped)
        if style_cfg["underline_bar"]:
            _, logical = layout.get_pixel_extents()
            it = layout.get_iter()
            while it.next_line():
                pass
            _, line_rect = it.get_line_extents()
            lx = line_rect.x / Pango.SCALE
            lw = line_rect.width / Pango.SCALE
            bar_y = self.PADDING_Y + logical.height + 3.5
            cr.save()
            cr.set_source_rgb(*theme["heading_text"])
            cr.set_line_width(1.8)
            cr.move_to(tx + lx, bar_y)
            cr.line_to(tx + lx + lw, bar_y)
            cr.stroke()
            cr.restore()

        if for_export:
            return

        # Draw caret when editing
        if self.editing:
            edit_layout = self._create_pango_layout(self.text)
            byte_idx = len(self.text[: self.cursor_pos].encode("utf-8"))
            strong_pos, _ = edit_layout.get_cursor_pos(byte_idx)
            cx = self._text_x() + strong_pos.x / Pango.SCALE
            cy = self.PADDING_Y + strong_pos.y / Pango.SCALE
            ch = max(14.0, strong_pos.height / Pango.SCALE)
            cr.save()
            cr.set_source_rgb(*theme["cursor"])
            cr.set_line_width(1.8)
            cr.move_to(cx, cy)
            cr.line_to(cx, cy + ch)
            cr.stroke()
            cr.restore()

        # Selection / Editing border
        if self.editing:
            cr.save()
            cr.set_source_rgb(*theme["box_editing_border"])
            cr.set_line_width(1.2)
            cr.rectangle(0.6, 0.6, w - 1.2, h - 1.2)
            cr.stroke()
            cr.restore()
        elif self.selected:
            cr.save()
            cr.set_source_rgb(*theme["box_selected_border"])
            cr.set_line_width(1.2)
            cr.set_dash([4.0, 3.0])
            cr.rectangle(0.6, 0.6, w - 1.2, h - 1.2)
            cr.stroke()
            cr.restore()

    def on_draw(self, widget, cr):
        z = getattr(self.canvas, "zoom", 1.0)
        cr.save()
        cr.scale(z, z)
        self.draw_content(cr, for_export=False)
        cr.restore()
        return True

    def _set_cursor_from_xy(self, mx: float, my: float):
        layout = self._create_pango_layout(self.text)
        lx = int((mx - self._text_x()) * Pango.SCALE)
        ly = int((my - self.PADDING_Y) * Pango.SCALE)
        inside, byte_index, trailing = layout.xy_to_index(lx, ly)
        char_idx = len(self.text.encode("utf-8")[:byte_index].decode("utf-8", errors="ignore"))
        self.cursor_pos = max(0, min(len(self.text), char_idx + (1 if trailing > 0 else 0)))

    def on_button_press(self, widget, event):
        if event.button == 1:
            z = getattr(self.canvas, "zoom", 1.0)
            lx, ly = event.x / z, event.y / z
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.canvas.select_box(self)
                self.start_editing()
                self._set_cursor_from_xy(lx, ly)
                self.queue_draw()
                return True

            if self.editing:
                self._set_cursor_from_xy(lx, ly)
                self.canvas.focus_without_scroll(self)
                self.queue_draw()
                return True
            else:
                self.canvas.handle_box_button_press(self, event)
                self.dragging = True
                self.drag_start_root_x = event.x_root
                self.drag_start_root_y = event.y_root
                self.drag_start_box_x = self.x
                self.drag_start_box_y = self.y
                return True
        if event.button == 3:
            if self not in self.canvas.selected_boxes:
                self.canvas.select_box(self)
            self._show_context_menu(event)
            return True
        return False

    def on_motion_notify(self, widget, event):
        if self.dragging and not self.editing:
            z = getattr(self.canvas, "zoom", 1.0)
            dx = int((event.x_root - self.drag_start_root_x) / z)
            dy = int((event.y_root - self.drag_start_root_y) / z)
            self.canvas.drag_box_or_group(self, dx, dy)
            return True
        return False

    def on_button_release(self, widget, event):
        if event.button == 1 and self.dragging:
            self.dragging = False
            self.canvas.recalculate_worksheet()
            return True
        return False

    def on_focus_out(self, widget, event):
        self.stop_editing()
        return False

    def on_key_press(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            return False
        keyname = Gdk.keyval_name(event.keyval)
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)

        if not self.editing:
            if keyname in ("Delete", "BackSpace"):
                self.canvas.remove_selected_boxes(self)
                return True
            if keyname in ("Return", "KP_Enter"):
                self.start_editing()
                return True
            return False

        if keyname == "Escape":
            self.stop_editing()
            return True
        if keyname in ("Return", "KP_Enter"):
            if shift:
                self.text = self.text[: self.cursor_pos] + "\n" + self.text[self.cursor_pos :]
                self.cursor_pos += 1
                self.update_layout()
            else:
                self.canvas.exit_box_and_move_down(self)
            return True
        if keyname == "Left":
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
                self.queue_draw()
            return True
        if keyname == "Right":
            if self.cursor_pos < len(self.text):
                self.cursor_pos += 1
                self.queue_draw()
            return True
        if keyname == "Home":
            line_start = self.text.rfind("\n", 0, self.cursor_pos)
            self.cursor_pos = 0 if line_start == -1 else line_start + 1
            self.queue_draw()
            return True
        if keyname == "End":
            line_end = self.text.find("\n", self.cursor_pos)
            self.cursor_pos = len(self.text) if line_end == -1 else line_end
            self.queue_draw()
            return True
        if keyname == "BackSpace":
            if self.cursor_pos > 0:
                self.text = self.text[: self.cursor_pos - 1] + self.text[self.cursor_pos :]
                self.cursor_pos -= 1
                self.update_layout()
            return True
        if keyname == "Delete":
            if self.cursor_pos < len(self.text):
                self.text = self.text[: self.cursor_pos] + self.text[self.cursor_pos + 1 :]
                self.update_layout()
            return True

        ch = chr(Gdk.keyval_to_unicode(event.keyval)) if Gdk.keyval_to_unicode(event.keyval) else ""
        if ch and ch.isprintable():
            self.text = self.text[: self.cursor_pos] + ch + self.text[self.cursor_pos :]
            self.cursor_pos += 1
            self.update_layout()
            return True

        return False


# ============================================================================
# 2D Plot Box (Functions as Lines + Discrete Values as Symbols + Axis/Scale)
# ============================================================================


SERIES_COLORS = [
    (0.30, 0.72, 0.98),  # Blue
    (0.98, 0.55, 0.25),  # Orange
    (0.42, 0.88, 0.52),  # Green
    (0.92, 0.42, 0.78),  # Magenta
    (0.98, 0.85, 0.30),  # Yellow
]


# ============================================================================
# Figure Caption Helpers (shared by PlotBox and ImageBox)
# ============================================================================

CAPTION_BTN_LABEL = "✎ Caption"


def draw_figure_caption_button(fig, cr, theme, bx=6.0, by=6.0):
    """Draw the on-figure caption button (top-left). It is drawn inside the figure,
    so it always moves with it. Stores its hit rectangle in logical coordinates."""
    pango_ctx = fig.get_pango_context()
    label = CAPTION_BTN_LABEL if fig.title.strip() else "＋ Caption"
    lay, lw, la, ld = MathRenderer._make_layout(pango_ctx, label, 0.62, bold=True)
    bw, bh = lw + 12.0, la + ld + 6.0
    cr.save()
    cr.set_source_rgb(*theme["canvas_bg"])
    cr.rectangle(bx, by, bw, bh)
    cr.fill()
    cr.set_source_rgb(*theme["box_editing_border"])
    cr.set_line_width(1.2)
    cr.rectangle(bx, by, bw, bh)
    cr.stroke()
    cr.set_source_rgb(*theme["heading_text"])
    cr.move_to(bx + 6.0, by + 3.0)
    PangoCairo.show_layout(cr, lay)
    cr.restore()
    fig._caption_btn_rect = (bx, by, bw, bh)


def hit_figure_caption_button(fig, lx, ly) -> bool:
    rect = getattr(fig, "_caption_btn_rect", None)
    if not fig.selected or rect is None:
        return False
    bx, by, bw, bh = rect
    return bx <= lx <= bx + bw and by <= ly <= by + bh


def open_figure_caption_dialog(fig):
    """Small dialog to add / edit / remove a figure's caption."""
    toplevel = fig.get_toplevel()
    parent = toplevel if isinstance(toplevel, Gtk.Window) else None
    prefix = getattr(fig, "CAPTION_PREFIX", "Figure")
    where = getattr(fig, "CAPTION_WHERE", "beneath")
    dlg = Gtk.Dialog(title=f"{prefix} {fig.fig_num} Caption", transient_for=parent, flags=0)
    dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_APPLY, Gtk.ResponseType.OK)
    dlg.set_default_response(Gtk.ResponseType.OK)
    dlg.set_default_size(420, -1)

    box = dlg.get_content_area()
    box.set_spacing(6)
    for side in ("start", "end", "top", "bottom"):
        getattr(box, f"set_margin_{side}")(12)
    hint = Gtk.Label(
        label=f"Shown as “{prefix} {fig.fig_num}: …” {where} the {prefix.lower()}. Leave empty to remove."
    )
    hint.set_xalign(0.0)
    hint.set_line_wrap(True)
    entry = Gtk.Entry(text=fig.title)
    entry.set_activates_default(True)
    box.pack_start(hint, False, False, 0)
    box.pack_start(entry, False, False, 0)

    dlg.show_all()
    entry.grab_focus()
    if dlg.run() == Gtk.ResponseType.OK:
        fig.title = entry.get_text().strip()
        fig.update_layout()
        fig.canvas.recalculate_worksheet()
        fig.canvas.notify_toc_changed()
        fig.queue_draw()
    dlg.destroy()


PLOT_SYMBOLS = [
    ("circle", "Circle (●)"),
    ("circle_o", "Open Circle (○)"),
    ("square", "Square (■)"),
    ("square_o", "Open Square (□)"),
    ("diamond", "Diamond (◆)"),
    ("diamond_o", "Open Diamond (◇)"),
    ("triangle", "Triangle (▲)"),
    ("triangle_o", "Open Triangle (△)"),
    ("cross", "Cross (✕)"),
    ("plus", "Plus (+)"),
]


PLOT_SYMBOLS_WITH_NONE = [("none", "None")] + PLOT_SYMBOLS

PLOT_COLORS = [
    ("auto", "Automatic", None),
    ("black", "Black / White", None),  # follows the theme's text colour
    ("blue", "Blue", (0.12, 0.47, 0.85)),
    ("red", "Red", (0.86, 0.18, 0.16)),
    ("green", "Green", (0.16, 0.62, 0.24)),
    ("orange", "Orange", (0.96, 0.52, 0.10)),
    ("purple", "Purple", (0.56, 0.27, 0.74)),
    ("brown", "Brown", (0.58, 0.36, 0.20)),
    ("teal", "Teal", (0.05, 0.60, 0.62)),
    ("magenta", "Magenta", (0.88, 0.25, 0.68)),
    ("gray", "Gray", (0.50, 0.52, 0.55)),
    ("lightblue", "Light Blue", (0.30, 0.72, 0.98)),
]
PLOT_COLOR_RGB = {cid: rgb for cid, _n, rgb in PLOT_COLORS}

PLOT_LINE_TYPES = [
    ("none", "None", None),
    ("solid", "Solid ───", []),
    ("dashed", "Dashed ‒ ‒ ‒", [6.0, 4.0]),
    ("dotted", "Dotted ·······", [0.1, 3.4]),
    ("dashdot", "Dash-dot ‒ · ‒", [7.0, 3.0, 0.1, 3.0]),
    ("longdash", "Long dash ── ──", [12.0, 5.0]),
]
PLOT_LINE_DASH = {lid: d for lid, _n, d in PLOT_LINE_TYPES}


UI_FONT_PT = 13  # font size of the whole interface (menus, panes, dialogs)


def apply_ui_font_size(size_pt=UI_FONT_PT):
    """Set the interface font to `size_pt`, keeping the desktop's font family.
    Worksheet content is unaffected (it uses its own explicit fonts)."""
    settings = Gtk.Settings.get_default()
    if settings is None:
        return
    cur = settings.get_property("gtk-font-name") or "Sans 10"
    desc = Pango.FontDescription.from_string(cur)
    family = desc.get_family() or "Sans"
    settings.set_property("gtk-font-name", f"{family} {size_pt}")


_LARGE_DIALOG_CSS_DONE = False


def use_large_dialog_font(dlg, size_pt=13):
    """Give a dialog (and everything inside it) a larger font."""
    global _LARGE_DIALOG_CSS_DONE
    if not _LARGE_DIALOG_CSS_DONE:
        css = Gtk.CssProvider()
        css.load_from_data(
            f"#large-font-dialog, #large-font-dialog * {{ font-size: {size_pt}pt; }}".encode()
        )
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        _LARGE_DIALOG_CSS_DONE = True
    dlg.set_name("large-font-dialog")


_ENTER_KEYS = ("Return", "KP_Enter", "ISO_Enter")


def install_enter_applies(dlg):
    """Make Enter in a dialog do the same as its Apply / OK / Insert button, wherever
    the focus is (entries, spin buttons, combos, check boxes). Text views, lists, push
    buttons and entries with their own Enter action keep their own behaviour."""
    if (getattr(dlg, "_enter_applies", False) or getattr(dlg, "NO_ENTER_APPLY", False)
            or isinstance(dlg, (Gtk.FileChooserDialog, Gtk.MessageDialog))):
        return
    dlg._enter_applies = True
    resp = None
    for r in (Gtk.ResponseType.OK, Gtk.ResponseType.APPLY, Gtk.ResponseType.ACCEPT, Gtk.ResponseType.YES):
        if dlg.get_widget_for_response(r) is not None:
            resp = r
            break
    if resp is None:
        dw = dlg.get_default_widget()
        if dw is not None and dlg.get_response_for_widget(dw) != Gtk.ResponseType.NONE:
            resp = dlg.get_response_for_widget(dw)
    if resp is None:
        area = dlg.get_action_area()
        for btn in (area.get_children() if area is not None else []):
            if isinstance(btn, Gtk.Button) and (btn.get_label() or "").startswith("Insert"):
                resp = dlg.get_response_for_widget(btn)
                break
    if resp is None:
        return
    dlg.set_default_response(resp)
    activate_id = GObject.signal_lookup("activate", Gtk.Entry)

    def on_key(_w, event):
        if Gdk.keyval_name(event.keyval) not in _ENTER_KEYS:
            return False
        if event.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK | Gdk.ModifierType.SHIFT_MASK):
            return False
        f = dlg.get_focus()
        if isinstance(f, (Gtk.TextView, Gtk.TreeView)):
            return False
        if isinstance(f, Gtk.Button) and not isinstance(f, Gtk.ToggleButton):
            return False  # Enter on a focused push button presses that button
        if isinstance(f, Gtk.Entry) and GObject.signal_has_handler_pending(f, activate_id, 0, False):
            return False
        w = dlg.get_widget_for_response(resp)
        if w is not None and not w.is_sensitive():
            return False
        if isinstance(f, Gtk.SpinButton):
            f.update()
        dlg.response(resp)
        return True

    dlg.connect("key-press-event", on_key)


_orig_dialog_run = Gtk.Dialog.run


def _dialog_run_enter_applies(self, *args):
    try:
        install_enter_applies(self)
    except Exception:
        pass
    return _orig_dialog_run(self, *args)


Gtk.Dialog.run = _dialog_run_enter_applies


def plot_axis_range(vals, log=False, pad_frac=0.06):
    """A tidy axis range enclosing `vals` (whole decades on a log axis)."""
    vals = [v for v in vals if math.isfinite(v) and (v > 0 or not log)]
    if not vals:
        return None
    lo, hi = min(vals), max(vals)
    if log:
        return 10.0 ** math.floor(math.log10(lo) + 1e-9), 10.0 ** math.ceil(math.log10(max(hi, lo * 1.0001)) - 1e-9)
    pad = (hi - lo) * pad_frac or (abs(hi) * 0.1 or 1.0)
    return float(f"{lo - pad:.3g}"), float(f"{hi + pad:.3g}")


class PlotBox(Gtk.DrawingArea):
    """
    2D Plot region on the A4 worksheet where:
    - Lines correspond to functions defined in the sheet (e.g. 'f; g' or 'f(x); g(x)')
    - Symbols correspond to vectors with discrete values defined in the sheet (e.g. 'vx, vy')
    - Configurable X and Y axis limits (x_min, x_max, y_min, y_max) and scale (Linear or Log10)
    """

    def __init__(
        self,
        canvas,
        x,
        y,
        width=460,
        height=275,
        title="Sine wave",
        func_expr="f; g",
        discrete_data="vx, vy",
        symbol_style="circle",
        connect_discrete=False,
        series_symbols=None,
        series_styles=None,
        x_min=-6.0,
        x_max=6.0,
        y_min=-1.5,
        y_max=1.5,
        x_scale="linear",
        y_scale="linear",
        show_grid=True,
        show_legend=True,
        x_title="",
        y_title="",
    ):
        super().__init__()
        self.canvas = canvas
        self.x_title = x_title or ""
        self.y_title = y_title or ""
        self.x = int(x)
        self.y = int(y)
        self.plot_w = int(width)
        self.plot_h = int(height)
        self.logical_w = self.plot_w
        self.logical_h = self.plot_h

        self.fig_num = 1
        self.title = title
        self.func_expr = func_expr
        self.discrete_data = discrete_data
        self.symbol_style = symbol_style
        # Per-series symbol overrides: {series label: symbol id}
        # Per-series style overrides: {series label: {"color", "line", "symbol"}}
        self.series_styles = {k: dict(v) for k, v in (series_styles or {}).items() if isinstance(v, dict)}
        for k, v in (series_symbols or {}).items():  # older files: symbol only
            self.series_styles.setdefault(k, {}).setdefault("symbol", v)
        self.connect_discrete = connect_discrete

        self.x_min = float(x_min)
        self.x_max = float(x_max)
        self.y_min = float(y_min)
        self.y_max = float(y_max)
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.show_grid = show_grid
        self.show_legend = show_legend

        self.editing = False
        self.selected = False
        self.dragging = False
        self.drag_start_root_x = 0
        self.drag_start_root_y = 0
        self.drag_start_box_x = 0
        self.drag_start_box_y = 0
        self.env = {}

        self.set_can_focus(True)
        self.update_layout()
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.SCROLL_MASK
        )

        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("key-press-event", self.on_key_press)
        self.connect("scroll-event", self.on_scroll)

    def _make_caption_layout(self, pango_ctx=None):
        if pango_ctx is None:
            pango_ctx = self.get_pango_context()
        caption_str = self.get_caption_text()
        t_layout, _, _, _ = MathRenderer._make_layout(pango_ctx, caption_str, 0.78, bold=True)
        wrap_w = max(80, int(self.plot_w - 20))
        t_layout.set_width(wrap_w * Pango.SCALE)
        t_layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        t_layout.set_alignment(Pango.Alignment.CENTER)
        _, logical = t_layout.get_pixel_extents()
        return t_layout, wrap_w, max(18, int(math.ceil(logical.height)))

    def update_layout(self):
        _sched = getattr(getattr(self, "canvas", None), "schedule_page_breaks", None)
        if _sched:
            _sched()
        _, _, cap_h = self._make_caption_layout()
        extra_cap_h = max(0, cap_h - 20)
        self.logical_w = self.plot_w
        self.logical_h = self.plot_h + extra_cap_h
        z = getattr(self.canvas, "zoom", 1.0)
        self.set_size_request(
            max(60, int(math.ceil(self.logical_w * z))),
            max(40, int(math.ceil(self.logical_h * z))),
        )
        self.queue_draw()

    def is_empty(self):
        return False

    def set_selected(self, selected):
        self.selected = selected
        self.queue_draw()

    def start_editing(self):
        self.open_config_dialog()

    def stop_editing(self):
        self.editing = False
        self.queue_draw()

    def update_env(self, env: dict, fig_num: int = 1):
        self.env = env
        old_fig = getattr(self, "fig_num", None)
        self.fig_num = int(fig_num)
        if old_fig != self.fig_num:
            self.update_layout()
        else:
            self.queue_draw()

    def get_caption_text(self) -> str:
        raw = self.title.strip()
        if raw.lower().startswith("figure "):
            parts = raw.split(":", 1)
            if len(parts) == 2 and parts[0][7:].strip().isdigit():
                raw = parts[1].strip()
        return f"Figure {self.fig_num}: {raw}" if raw else f"Figure {self.fig_num}"

    def _transform_x(self, val: float):
        if self.x_scale == "log":
            if val <= 0:
                return None
            return math.log10(val)
        return val

    def _transform_y(self, val: float):
        if self.y_scale == "log":
            if val <= 0:
                return None
            return math.log10(val)
        return val

    def _resolve_sheet_functions(self, raw=None):
        resolved = []
        raw = self.func_expr if raw is None else raw
        entries = [e.strip() for e in raw.replace(",", ";").split(";") if e.strip()]
        for entry in entries:
            fn_name = entry.split("(", 1)[0].strip() if "(" in entry else entry
            fn_obj = self.env.get(fn_name)
            if callable(fn_obj):
                resolved.append((f"{fn_name}(x)", fn_obj))
                continue
            rhs = entry.split(":=", 1)[1].strip() if ":=" in entry else (
                entry.split("=", 1)[1].strip() if "=" in entry else entry
            )
            py_rhs = rhs.replace("^", "**").replace("·", "*")
            try:
                inline_fn = eval(f"lambda x: ({py_rhs})", self.env)
                resolved.append((entry, inline_fn))
            except Exception:
                pass
        return resolved

    def series_style(self, label, kind, idx, theme=None, styles=None):
        """Effective (rgb, line id, symbol id) of a series. kind is 'func' or 'vec';
        idx is the series' position across all series (for the automatic colour)."""
        st = (self.series_styles if styles is None else styles).get(label, {})
        cid = st.get("color", "auto")
        if cid == "black":
            rgb = tuple((theme or THEMES[self.canvas.theme_name])["text"])
        else:
            rgb = PLOT_COLOR_RGB.get(cid) or SERIES_COLORS[idx % len(SERIES_COLORS)]
        if kind == "func":
            line = st.get("line", "solid")
            sym = st.get("symbol", "none")
        else:
            line = st.get("line", "dashed" if self.connect_discrete else "none")
            sym = st.get("symbol", self.symbol_style)
        return rgb, line, sym

    @staticmethod
    def _apply_dash(cr, line, width):
        dash = PLOT_LINE_DASH.get(line) or []
        cr.set_line_width(width)
        if line == "dotted" or line == "dashdot":
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            dash = [d * (width if d > 1 else 1) / 1.6 if d > 1 else d for d in dash]
        cr.set_dash(dash)

    def _resolve_sheet_vector_series(self, raw=None):
        series_list = []
        raw = (self.discrete_data if raw is None else raw).strip()
        if not raw:
            return series_list

        chunks = [c.strip() for c in raw.replace("\n", ";").split(";") if c.strip()]
        if len(chunks) == 2 and "," not in chunks[0] and "," not in chunks[1]:
            v0 = self.env.get(chunks[0])
            v1 = self.env.get(chunks[1])
            if isinstance(v0, (list, tuple)) and isinstance(v1, (list, tuple)):
                pts = [(float(px), float(py)) for px, py in zip(v0, v1)]
                return [(f"({chunks[0]}, {chunks[1]})", pts)]

        for chunk in chunks:
            cleaned = chunk.strip().lstrip("(").rstrip(")")
            if "," in cleaned:
                x_name, y_name = [p.strip() for p in cleaned.split(",", 1)]
                xs = self.env.get(x_name)
                ys = self.env.get(y_name)
                if isinstance(xs, (list, tuple)) and isinstance(ys, (list, tuple)):
                    try:
                        pts = [(float(px), float(py)) for px, py in zip(xs, ys)]
                        series_list.append((f"({x_name}, {y_name})", pts))
                    except Exception:
                        pass
            else:
                v_name = cleaned.strip()
                ys = self.env.get(v_name)
                if isinstance(ys, (list, tuple)):
                    try:
                        pts = [(float(i + 1), float(py)) for i, py in enumerate(ys)]
                        series_list.append((v_name, pts))
                    except Exception:
                        pass
        return series_list

    def _draw_symbol(self, cr, sx: float, sy: float, r: float = 4.2, style=None):
        style = style or self.symbol_style
        hollow = style.endswith("_o")
        if hollow:
            style = style[:-2]

        def finish():
            if hollow:
                bg = getattr(self, "_sym_bg", None)
                if bg is not None:  # blank out the line behind an open symbol
                    src = cr.get_source()
                    cr.set_source_rgb(*bg)
                    cr.fill_preserve()
                    cr.set_source(src)
                cr.set_line_width(1.6)
                cr.stroke()
            else:
                cr.fill()

        if style == "circle":
            cr.new_sub_path()
            cr.arc(sx, sy, r, 0, 2 * math.pi)
            finish()
        elif style == "square":
            cr.rectangle(sx - r, sy - r, r * 2, r * 2)
            finish()
        elif style == "diamond":
            cr.move_to(sx, sy - r * 1.25)
            cr.line_to(sx + r * 1.25, sy)
            cr.line_to(sx, sy + r * 1.25)
            cr.line_to(sx - r * 1.25, sy)
            cr.close_path()
            finish()
        elif style == "triangle":
            cr.move_to(sx, sy - r * 1.25)
            cr.line_to(sx + r * 1.2, sy + r)
            cr.line_to(sx - r * 1.2, sy + r)
            cr.close_path()
            finish()
        elif style == "cross":
            cr.set_line_width(2.0)
            cr.move_to(sx - r, sy - r)
            cr.line_to(sx + r, sy + r)
            cr.move_to(sx - r, sy + r)
            cr.line_to(sx + r, sy - r)
            cr.stroke()
        elif style == "plus":
            cr.set_line_width(2.0)
            cr.move_to(sx - r * 1.1, sy)
            cr.line_to(sx + r * 1.1, sy)
            cr.move_to(sx, sy - r * 1.1)
            cr.line_to(sx, sy + r * 1.1)
            cr.stroke()

    def draw_content(self, cr, theme=None, for_export=False):
        if theme is None:
            theme = THEMES[self.canvas.theme_name]
        pango_ctx = self.get_pango_context()
        self._sym_bg = tuple(theme["canvas_bg"])[:3]
        t_layout, wrap_w, cap_h = self._make_caption_layout(pango_ctx)
        extra_cap_h = max(0, cap_h - 20)
        w = self.plot_w
        h = self.plot_h + extra_cap_h

        # Plot frame background
        if not for_export:
            cr.save()
            cr.set_source_rgba(*theme["box_editing_bg"])
            cr.rectangle(0, 0, w, h)
            cr.fill()
            cr.restore()

        x_title = (self.x_title or "").strip()
        y_title = (self.y_title or "").strip()
        AX_TITLE_H = 18.0
        pad_left = 52.0 + (AX_TITLE_H if y_title else 0.0)
        pad_right = 18.0
        pad_top = 24.0
        pad_bot = 54.0 + (AX_TITLE_H if x_title else 0.0)
        pw = max(60.0, w - pad_left - pad_right)
        ph = max(50.0, self.plot_h - pad_top - pad_bot)

        if not for_export:
            # Header buttons, right to left, all in the same plain bracketed style.
            cap_txt = "[✎ Caption]" if self.title.strip() else "[＋ Caption]"
            items = [
                ("cfg", "⚙", 0.95, "Plot settings (axes, scale, series)"),
                ("legend", "[☑ Legend]" if self.show_legend else "[☐ Legend]", 0.62, None),
                ("zoom", "[⤢ Zoom All]", 0.62, None),
                ("caption", cap_txt, 0.62, None),
            ]
            if w < 360:  # narrow plot: icons only
                items = [(k, (t.split(" ")[0] + "]") if t.startswith("[") else t, sc, tip)
                         for k, t, sc, tip in items]
            self._header_rects = {}
            hx = w - 8
            for key, txt, scale, _tip in items:
                lay, lw, la, ld = MathRenderer._make_layout(pango_ctx, txt, scale)
                hx -= lw
                ty = 5 if scale < 0.8 else 1
                cr.save()
                cr.set_source_rgb(*theme["muted_text"])
                cr.move_to(hx, ty)
                PangoCairo.show_layout(cr, lay)
                cr.restore()
                self._header_rects[key] = (hx - 3, 0, lw + 6, 26)
                hx -= 10
            self._legend_toggle_rect = self._header_rects["legend"]
            self._zoom_all_rect = self._header_rects["zoom"]

        cr.save()
        cr.set_source_rgb(*theme["heading_text"])
        caption_x = (w - wrap_w) / 2.0
        caption_y = pad_top + ph + 26.0 + (AX_TITLE_H if x_title else 0.0)
        cr.move_to(caption_x, caption_y)
        PangoCairo.show_layout(cr, t_layout)
        cr.restore()


        tx_min = math.log10(max(1e-12, self.x_min)) if self.x_scale == "log" else self.x_min
        tx_max = math.log10(max(1e-11, self.x_max)) if self.x_scale == "log" else self.x_max
        ty_min = math.log10(max(1e-12, self.y_min)) if self.y_scale == "log" else self.y_min
        ty_max = math.log10(max(1e-11, self.y_max)) if self.y_scale == "log" else self.y_max
        if tx_max <= tx_min:
            tx_max = tx_min + 1.0
        if ty_max <= ty_min:
            ty_max = ty_min + 1.0

        def to_screen_x(tx):
            return pad_left + (tx - tx_min) / (tx_max - tx_min) * pw

        def to_screen_y(ty):
            return pad_top + ph - (ty - ty_min) / (ty_max - ty_min) * ph

        cr.save()
        cr.set_source_rgb(*theme["canvas_bg"])
        cr.rectangle(pad_left, pad_top, pw, ph)
        cr.fill()
        cr.restore()

        num_ticks = 5
        for i in range(num_ticks + 1):
            frac = i / num_ticks
            gx = pad_left + frac * pw
            gy = pad_top + (1.0 - frac) * ph
            tx_val = tx_min + frac * (tx_max - tx_min)
            ty_val = ty_min + frac * (ty_max - ty_min)

            if self.show_grid:
                cr.save()
                cr.set_source_rgb(*theme["grid_major"])
                cr.set_line_width(0.8)
                cr.set_dash([2.0, 2.0])
                cr.move_to(gx, pad_top)
                cr.line_to(gx, pad_top + ph)
                cr.move_to(pad_left, gy)
                cr.line_to(pad_left + pw, gy)
                cr.stroke()
                cr.restore()

            x_disp = (10.0 ** tx_val) if self.x_scale == "log" else tx_val
            y_disp = (10.0 ** ty_val) if self.y_scale == "log" else ty_val
            xlbl, xlw, _, _ = MathRenderer._make_layout(pango_ctx, f"{x_disp:.3g}", 0.58)
            ylbl, ylw, yla, _ = MathRenderer._make_layout(pango_ctx, f"{y_disp:.3g}", 0.58)
            cr.save()
            cr.set_source_rgb(*theme["muted_text"])
            cr.move_to(gx - xlw / 2.0, pad_top + ph + 4)
            PangoCairo.show_layout(cr, xlbl)
            cr.move_to(max(2.0, pad_left - ylw - 5), gy - yla / 2.0)
            PangoCairo.show_layout(cr, ylbl)
            cr.restore()

        # Axis titles
        if x_title or y_title:
            cr.save()
            cr.set_source_rgb(*theme["text"])
            if x_title:
                xt, xtw, _, _ = MathRenderer._make_layout(pango_ctx, x_title, 0.64)
                cr.move_to(pad_left + (pw - xtw) / 2.0, pad_top + ph + 20)
                PangoCairo.show_layout(cr, xt)
            if y_title:
                yt, ytw, yta, ytd = MathRenderer._make_layout(pango_ctx, y_title, 0.64)
                cr.save()
                cr.translate(3.0, pad_top + (ph + ytw) / 2.0)
                cr.rotate(-math.pi / 2.0)
                cr.move_to(0, 0)
                PangoCairo.show_layout(cr, yt)
                cr.restore()
            cr.restore()

        cr.save()
        cr.set_source_rgb(*theme["page_border"])
        cr.set_line_width(1.1)
        if self.x_scale == "linear" and tx_min <= 0 <= tx_max:
            zx = to_screen_x(0.0)
            cr.move_to(zx, pad_top)
            cr.line_to(zx, pad_top + ph)
        if self.y_scale == "linear" and ty_min <= 0 <= ty_max:
            zy = to_screen_y(0.0)
            cr.move_to(pad_left, zy)
            cr.line_to(pad_left + pw, zy)
        cr.stroke()
        cr.restore()

        cr.save()
        cr.rectangle(pad_left, pad_top, pw, ph)
        cr.clip()

        legend_items = []
        sheet_funcs = self._resolve_sheet_functions()
        samples = 220
        for f_idx, (fn_label, fn_callable) in enumerate(sheet_funcs):
            color, f_line, f_sym = self.series_style(fn_label, "func", f_idx, theme)
            legend_items.append((fn_label, color, (f_line, f_sym)))
            marks = []
            cr.save()
            cr.set_source_rgb(*color)
            self._apply_dash(cr, f_line, 2.0)
            pen_down = False
            for s in range(samples + 1):
                tx = tx_min + (s / samples) * (tx_max - tx_min)
                x_val = (10.0 ** tx) if self.x_scale == "log" else tx
                try:
                    y_val = float(fn_callable(x_val))
                    if math.isnan(y_val) or math.isinf(y_val):
                        pen_down = False
                        continue
                    ty = self._transform_y(y_val)
                    if ty is None:
                        pen_down = False
                        continue
                    sx = to_screen_x(tx)
                    sy = to_screen_y(ty)
                    if not (-2000 <= sy <= 4000):
                        pen_down = False
                        continue
                    if f_sym != "none" and s % 20 == 10:
                        marks.append((sx, sy))
                    if not pen_down:
                        cr.move_to(sx, sy)
                        pen_down = True
                    else:
                        cr.line_to(sx, sy)
                except Exception:
                    pen_down = False
            if f_line == "none":
                cr.new_path()
            else:
                cr.stroke()
            cr.set_dash([])
            for sx, sy in marks:
                self._draw_symbol(cr, sx, sy, r=4.2, style=f_sym)
            cr.restore()

        vec_series = self._resolve_sheet_vector_series()
        for v_idx, (vec_label, pts) in enumerate(vec_series):
            sym_color, v_line, sym_style = self.series_style(vec_label, "vec", len(sheet_funcs) + v_idx, theme)
            legend_items.append((vec_label, sym_color, (v_line, sym_style)))
            screen_pts = []
            for px, py in pts:
                tx = self._transform_x(px)
                ty = self._transform_y(py)
                if tx is not None and ty is not None:
                    screen_pts.append((to_screen_x(tx), to_screen_y(ty)))

            if v_line != "none" and len(screen_pts) >= 2:
                cr.save()
                cr.set_source_rgb(*sym_color)
                self._apply_dash(cr, v_line, 1.4)
                cr.move_to(screen_pts[0][0], screen_pts[0][1])
                for sx, sy in screen_pts[1:]:
                    cr.line_to(sx, sy)
                cr.stroke()
                cr.restore()

            if sym_style != "none":
                cr.save()
                cr.set_source_rgb(*sym_color)
                for sx, sy in screen_pts:
                    self._draw_symbol(cr, sx, sy, r=4.2, style=sym_style)
                cr.restore()

        cr.restore()  # End clip

        cr.save()
        cr.set_source_rgb(*theme["page_border"])
        cr.set_line_width(1.2)
        cr.rectangle(pad_left, pad_top, pw, ph)
        cr.stroke()
        cr.restore()

        if self.show_legend and legend_items:
            # Framed legend box sized to its entries
            rows = [(MathRenderer._make_layout(pango_ctx, t, 0.58), col, kind) for t, col, kind in legend_items]
            box_pad = 6.0
            inner_w = max(28 + lw for (_l, lw, _a, _d), _c, _k in rows)
            inner_h = sum(la + ld + 2 for (_l, _w, la, ld), _c, _k in rows) - 2
            bx = pad_left + 8
            by = pad_top + 6
            bw = inner_w + 2 * box_pad
            bh = inner_h + 2 * box_pad
            cr.save()
            cr.set_source_rgb(*theme["canvas_bg"])
            cr.rectangle(bx, by, bw, bh)
            cr.fill_preserve()
            cr.set_source_rgb(*theme["page_border"])
            cr.set_line_width(0.9)
            cr.stroke()
            cr.restore()
            lx = bx + box_pad
            ly = by + box_pad
            for (lbl_lay, lw, la, ld), col, kind in rows:
                cr.save()
                cr.set_source_rgb(*col)
                k_line, k_sym = kind
                my = ly + la * 0.6
                if k_line != "none":
                    cr.save()
                    self._apply_dash(cr, k_line, 1.8)
                    cr.move_to(lx, my)
                    cr.line_to(lx + 24, my)
                    cr.stroke()
                    cr.restore()
                if k_sym != "none":
                    self._draw_symbol(cr, lx + 12, my, r=3.5, style=k_sym)
                cr.set_source_rgb(*theme["text"])
                cr.move_to(lx + 28, ly)
                PangoCairo.show_layout(cr, lbl_lay)
                cr.restore()
                ly += la + ld + 2

        if self.selected and not for_export:
            cr.save()
            cr.set_source_rgb(*theme["box_selected_border"])
            cr.set_line_width(1.4)
            cr.set_dash([4.0, 3.0])
            cr.rectangle(0.7, 0.7, w - 1.4, h - 1.4)
            cr.stroke()
            cr.restore()

    def on_draw(self, widget, cr):
        z = getattr(self.canvas, "zoom", 1.0)
        cr.save()
        cr.scale(z, z)
        self.draw_content(cr, for_export=False)
        cr.restore()
        return True

    def on_button_press(self, widget, event):
        if event.button == 1:
            z = getattr(self.canvas, "zoom", 1.0)
            lx, ly = event.x / z, event.y / z
            was_selected = self.selected
            self.canvas.handle_box_button_press(self, event)
            self.canvas.focus_without_scroll(self)
            hr = getattr(self, "_header_rects", {})

            def _hit(key):
                r = hr.get(key)
                return (event.type == Gdk.EventType.BUTTON_PRESS and r is not None
                        and r[0] <= lx <= r[0] + r[2] and ly <= r[3])

            if _hit("caption"):
                self.dragging = False
                GLib.idle_add(lambda: open_figure_caption_dialog(self) and False)
                return True
            if _hit("cfg"):
                self.dragging = False
                GLib.idle_add(self._open_config_dialog_idle)
                return True
            r = getattr(self, "_legend_toggle_rect", None)
            if event.type == Gdk.EventType.BUTTON_PRESS and r and r[0] <= lx <= r[0] + r[2] and ly <= r[3]:
                self.dragging = False
                self.toggle_legend()
                return True
            r = getattr(self, "_zoom_all_rect", None)
            if event.type == Gdk.EventType.BUTTON_PRESS and r and r[0] <= lx <= r[0] + r[2] and ly <= r[3]:
                self.dragging = False
                self.zoom_to_data()
                return True
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.dragging = False
                GLib.idle_add(self._open_config_dialog_idle)
                return True
            self.dragging = True
            self.drag_start_root_x = event.x_root
            self.drag_start_root_y = event.y_root
            self.drag_start_box_x = self.x
            self.drag_start_box_y = self.y
            return True
        if event.button == 3:
            if self not in self.canvas.selected_boxes:
                self.canvas.select_box(self)
            self._show_context_menu(event)
            return True
        return False

    def data_extents(self, func_expr=None, discrete=None, x_scale=None, y_scale=None):
        """Axis limits (x0, x1, y0, y1) that show all the data of the plot: the x range of
        the vectors (or the current x range when only functions are plotted) and the y
        range of everything visible in it. None when there is nothing to show."""
        import numpy as np
        x_log = (x_scale or self.x_scale) == "log"
        y_log = (y_scale or self.y_scale) == "log"
        series = self._resolve_sheet_vector_series(discrete)
        funcs = self._resolve_sheet_functions(func_expr)
        xs = [p[0] for _l, pts in series for p in pts]
        ys = [p[1] for _l, pts in series for p in pts]
        xr = plot_axis_range(xs, x_log, pad_frac=0.04) if xs else None
        if xr is None:
            if not funcs:
                return None
            xr = (self.x_min, self.x_max)
            if x_log and xr[0] <= 0:
                xr = (0.1, max(xr[1], 10.0))
        if funcs:
            if x_log:
                grid = np.logspace(math.log10(xr[0]), math.log10(xr[1]), 400)
            else:
                grid = np.linspace(xr[0], xr[1], 400)
            fy = []
            for _l, fn in funcs:
                for xv in grid:
                    try:
                        v = float(fn(float(xv)))
                    except Exception:
                        continue
                    if math.isfinite(v) and (v > 0 or not y_log):
                        fy.append(v)
            if len(fy) > 20:  # ignore the spikes of a pole (tan, 1/x …)
                lo, hi = np.percentile(fy, [0.5, 99.5])
                fy = [v for v in fy if lo <= v <= hi]
            ys += fy
        yr = plot_axis_range(ys, y_log)
        if yr is None:
            return None
        return xr[0], xr[1], yr[0], yr[1]

    def zoom_to_data(self):
        ext = self.data_extents()
        if ext is None:
            return False
        self.x_min, self.x_max, self.y_min, self.y_max = ext
        self.queue_draw()
        mark = getattr(self.canvas, "mark_modified", None)
        if callable(mark):
            mark()
        return True

    def toggle_legend(self):
        self.show_legend = not self.show_legend
        self.queue_draw()
        mark = getattr(self.canvas, "mark_modified", None)
        if callable(mark):
            mark()

    def _toggle_grid(self):
        self.show_grid = not self.show_grid
        self.queue_draw()
        mark = getattr(self.canvas, "mark_modified", None)
        if callable(mark):
            mark()

    def _show_context_menu(self, event):
        menu = Gtk.Menu()
        mi = Gtk.MenuItem(label="Plot Settings…")
        mi.connect("activate", lambda _m: GLib.idle_add(self._open_config_dialog_idle))
        menu.append(mi)
        mi = Gtk.MenuItem(label="Zoom All Data  (reset axes)")
        mi.connect("activate", lambda _m: self.zoom_to_data())
        menu.append(mi)
        menu.append(Gtk.SeparatorMenuItem())
        for label, active, cb in (
            ("Show Legend", self.show_legend, self.toggle_legend),
            ("Show Grid", self.show_grid, self._toggle_grid),
        ):
            ci = Gtk.CheckMenuItem(label=label)
            ci.set_active(active)
            ci.connect("toggled", lambda _m, f=cb: f())
            menu.append(ci)
        menu.append(Gtk.SeparatorMenuItem())
        mi = Gtk.MenuItem(label="Delete")
        mi.connect("activate", lambda _m: self.canvas.remove_selected_boxes(self))
        menu.append(mi)
        menu.show_all()
        menu.popup_at_pointer(event)

    def _open_config_dialog_idle(self):
        self.dragging = False
        self.open_config_dialog()
        return False

    def on_motion_notify(self, widget, event):
        if self.dragging:
            if not (event.state & Gdk.ModifierType.BUTTON1_MASK):
                self.dragging = False
                return False
            z = getattr(self.canvas, "zoom", 1.0)
            dx = int((event.x_root - self.drag_start_root_x) / z)
            dy = int((event.y_root - self.drag_start_root_y) / z)
            self.canvas.drag_box_or_group(self, dx, dy)
            return True
        return False

    def on_button_release(self, widget, event):
        if event.button == 1 and self.dragging:
            self.dragging = False
            self.canvas.recalculate_worksheet()
            return True
        return False

    def on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ("Delete", "BackSpace"):
            self.canvas.remove_selected_boxes(self)
            return True
        if keyname in ("Return", "KP_Enter"):
            self.open_config_dialog()
            return True
        return False

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            return self.canvas.on_scroll_zoom(widget, event)
        return False

    def open_config_dialog(self):
        self.dragging = False
        toplevel = self.get_toplevel()
        parent = toplevel if isinstance(toplevel, Gtk.Window) else None
        dlg = Gtk.Dialog(
            title="Plot Options - Sheet Functions (Lines), Sheet Vectors (Symbols), Limits & Scale",
            transient_for=parent,
            flags=0,
        )
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_APPLY, Gtk.ResponseType.OK)
        dlg.set_default_size(820, 600)

        content = dlg.get_content_area()
        grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        grid.set_margin_start(14)
        grid.set_margin_end(14)
        grid.set_margin_top(12)
        grid.set_margin_bottom(12)
        content.add(grid)

        row = 0

        def add_row(label_text, widget_item):
            nonlocal row
            lbl = Gtk.Label(label=label_text)
            lbl.set_xalign(0.0)
            grid.attach(lbl, 0, row, 1, 1)
            widget_item.set_hexpand(True)
            grid.attach(widget_item, 1, row, 3, 1)
            row += 1

        title_entry = Gtk.Entry(text=self.title)
        add_row(f"Figure {self.fig_num} Title:", title_entry)

        avail_funcs = self.env.get("_sheet_functions", [])
        # A name can be defined as a vector and later redefined (e.g. as a function):
        # list only the names that still hold a vector.
        avail_vecs = [vn for vn in self.env.get("_sheet_vectors", [])
                      if isinstance(self.env.get(vn), (list, tuple))]
        avail_funcs = [fn for fn in avail_funcs if callable(self.env.get(fn, len))]

        func_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        func_entry = Gtk.Entry(text=self.func_expr)
        func_entry.set_tooltip_text("Function name(s) defined in the sheet separated by ';', e.g. f; g")
        func_vbox.pack_start(func_entry, False, False, 0)
        fn_hint = Gtk.Label()
        fn_list_str = ", ".join(f"{fn}(x)" for fn in avail_funcs) if avail_funcs else "none defined above plot yet"
        fn_hint.set_markup(f"<small>Sheet functions available: <b>{GLib_markup_escape(fn_list_str)}</b></small>")
        fn_hint.set_xalign(0.0)
        func_vbox.pack_start(fn_hint, False, False, 0)
        add_row("Sheet Functions [Lines]:", func_vbox)

        disc_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        disc_entry = Gtk.Entry(text=self.discrete_data)
        disc_entry.set_tooltip_text("Vector pair(s) defined in the sheet, e.g. vx, vy")
        disc_vbox.pack_start(disc_entry, False, False, 0)
        vec_hint = Gtk.Label()
        vec_list_str = (
            ", ".join(f"{vn} ({len(self.env.get(vn, []))} pts)" for vn in avail_vecs)
            if avail_vecs
            else "none defined above plot yet (define e.g. vx = [1, 2, 3])"
        )
        vec_hint.set_markup(f"<small>Sheet vectors available: <b>{GLib_markup_escape(vec_list_str)}</b></small>")
        vec_hint.set_xalign(0.0)
        disc_vbox.pack_start(vec_hint, False, False, 0)
        add_row("Sheet Vectors [Symbols]:", disc_vbox)

        sym_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sym_combo = Gtk.ComboBoxText()
        for sid, sname in PLOT_SYMBOLS:
            sym_combo.append(sid, sname)
        sym_combo.set_active_id(self.symbol_style)
        sym_combo.set_tooltip_text("Symbol used by any series that has no symbol of its own")
        conn_chk = Gtk.CheckButton(label="Connect discrete points with dashed line")
        conn_chk.set_active(self.connect_discrete)
        sym_box.pack_start(sym_combo, False, False, 0)
        sym_box.pack_start(conn_chk, False, False, 0)
        add_row("Default Symbol:", sym_box)

        # Colour, line type and symbol for every series; rebuilt as the lists are edited
        series_choice = {k: dict(v) for k, v in self.series_styles.items()}
        series_grid = Gtk.Grid(column_spacing=8, row_spacing=4)
        add_row("Series Styles:", series_grid)

        def _combo(options, active, key, field):
            cb = Gtk.ComboBoxText()
            for oid, oname, *_rest in options:
                cb.append(oid, oname)
            cb.set_active_id(active)

            def _changed(c):
                series_choice.setdefault(key, {})[field] = c.get_active_id()

            cb.connect("changed", _changed)
            return cb

        def rebuild_series_rows(*_a):
            for ch in series_grid.get_children():
                series_grid.remove(ch)
            series = [(lab, "func") for lab, _f in self._resolve_sheet_functions(func_entry.get_text())]
            series += [(lab, "vec") for lab, _p in self._resolve_sheet_vector_series(disc_entry.get_text())]
            if not series:
                hint = Gtk.Label()
                hint.set_markup("<small>No series found yet.</small>")
                hint.set_xalign(0.0)
                series_grid.attach(hint, 0, 0, 4, 1)
            for col_i, head in enumerate(("Series", "Color", "Line", "Symbol")):
                if series:
                    hl = Gtk.Label()
                    hl.set_markup(f"<small><b>{head}</b></small>")
                    hl.set_xalign(0.0)
                    series_grid.attach(hl, col_i, 0, 1, 1)
            saved_connect = self.connect_discrete
            self.connect_discrete = conn_chk.get_active()
            for i, (lab, kind) in enumerate(series):
                st = series_choice.get(lab, {})
                _rgb, line, sym = self.series_style(lab, kind, i, styles=series_choice)
                lbl = Gtk.Label(label=lab)
                lbl.set_xalign(0.0)
                lbl.set_width_chars(min(max(len(lab), 10), 30))
                lbl.set_ellipsize(Pango.EllipsizeMode.END)
                lbl.set_max_width_chars(30)
                lbl.set_tooltip_text(lab)
                series_grid.attach(lbl, 0, i + 1, 1, 1)
                series_grid.attach(_combo(PLOT_COLORS, st.get("color", "auto"), lab, "color"), 1, i + 1, 1, 1)
                series_grid.attach(_combo(PLOT_LINE_TYPES, line, lab, "line"), 2, i + 1, 1, 1)
                series_grid.attach(_combo(PLOT_SYMBOLS_WITH_NONE, sym, lab, "symbol"), 3, i + 1, 1, 1)
            self.connect_discrete = saved_connect
            series_grid.show_all()

        rebuild_series_rows()
        disc_entry.connect("changed", rebuild_series_rows)
        func_entry.connect("changed", rebuild_series_rows)

        x_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        xmin_entry = Gtk.Entry(text=str(self.x_min))
        xmin_entry.set_width_chars(12)
        xmax_entry = Gtk.Entry(text=str(self.x_max))
        xmax_entry.set_width_chars(12)
        xscale_combo = Gtk.ComboBoxText()
        xscale_combo.append("linear", "Linear Scale")
        xscale_combo.append("log", "Log10 Scale")
        xscale_combo.set_active_id(self.x_scale)
        x_box.pack_start(Gtk.Label(label="Min:"), False, False, 0)
        x_box.pack_start(xmin_entry, False, False, 0)
        x_box.pack_start(Gtk.Label(label="Max:"), False, False, 0)
        x_box.pack_start(xmax_entry, False, False, 0)
        x_box.pack_start(Gtk.Label(label="Scale:"), False, False, 0)
        x_box.pack_start(xscale_combo, False, False, 0)
        add_row("X-Axis Limits & Scale:", x_box)

        xt_entry = Gtk.Entry(text=self.x_title)
        xt_entry.set_placeholder_text("e.g. Time [s]")
        add_row("X-Axis Title:", xt_entry)

        y_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ymin_entry = Gtk.Entry(text=str(self.y_min))
        ymin_entry.set_width_chars(12)
        ymax_entry = Gtk.Entry(text=str(self.y_max))
        ymax_entry.set_width_chars(12)
        yscale_combo = Gtk.ComboBoxText()
        yscale_combo.append("linear", "Linear Scale")
        yscale_combo.append("log", "Log10 Scale")
        yscale_combo.set_active_id(self.y_scale)
        y_box.pack_start(Gtk.Label(label="Min:"), False, False, 0)
        y_box.pack_start(ymin_entry, False, False, 0)
        y_box.pack_start(Gtk.Label(label="Max:"), False, False, 0)
        y_box.pack_start(ymax_entry, False, False, 0)
        y_box.pack_start(Gtk.Label(label="Scale:"), False, False, 0)
        y_box.pack_start(yscale_combo, False, False, 0)
        add_row("Y-Axis Limits & Scale:", y_box)

        zoom_btn = Gtk.Button(label="⤢ Zoom All Data")
        zoom_btn.set_tooltip_text("Set the axis limits so that all the data and curves are shown")

        def on_zoom_all(_b):
            ext = self.data_extents(func_entry.get_text(), disc_entry.get_text(),
                                    xscale_combo.get_active_id(), yscale_combo.get_active_id())
            if ext is None:
                return
            for ent, v in zip((xmin_entry, xmax_entry, ymin_entry, ymax_entry), ext):
                ent.set_text(f"{v:.6g}")

        zoom_btn.connect("clicked", on_zoom_all)
        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom_box.pack_start(zoom_btn, False, False, 0)
        add_row("", zoom_box)

        yt_entry = Gtk.Entry(text=self.y_title)
        yt_entry.set_placeholder_text("e.g. Temperature [°C]")
        add_row("Y-Axis Title:", yt_entry)

        opt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        w_entry = Gtk.Entry(text=str(self.plot_w))
        w_entry.set_width_chars(6)
        h_entry = Gtk.Entry(text=str(self.plot_h))
        h_entry.set_width_chars(6)
        grid_chk = Gtk.CheckButton(label="Grid")
        grid_chk.set_active(self.show_grid)
        leg_chk = Gtk.CheckButton(label="Legend")
        leg_chk.set_active(self.show_legend)
        opt_box.pack_start(Gtk.Label(label="W×H:"), False, False, 0)
        opt_box.pack_start(w_entry, False, False, 0)
        opt_box.pack_start(h_entry, False, False, 0)
        opt_box.pack_start(grid_chk, False, False, 0)
        opt_box.pack_start(leg_chk, False, False, 0)
        add_row("Size & Display:", opt_box)

        dlg.show_all()
        resp = dlg.run()
        if resp == Gtk.ResponseType.OK:
            self.title = title_entry.get_text().strip()
            self.func_expr = func_entry.get_text().strip()
            self.discrete_data = disc_entry.get_text().strip()
            self.symbol_style = sym_combo.get_active_id() or "circle"
            live = {lab for lab, _p in self._resolve_sheet_vector_series()}
            live |= {lab for lab, _f in self._resolve_sheet_functions()}
            self.series_styles = {k: v for k, v in series_choice.items() if v and (k in live or not live)}
            self.connect_discrete = conn_chk.get_active()
            self.x_scale = xscale_combo.get_active_id() or "linear"
            self.y_scale = yscale_combo.get_active_id() or "linear"
            try:
                self.x_min = float(eval(xmin_entry.get_text(), self.env))
                self.x_max = float(eval(xmax_entry.get_text(), self.env))
                self.y_min = float(eval(ymin_entry.get_text(), self.env))
                self.y_max = float(eval(ymax_entry.get_text(), self.env))
            except Exception:
                pass
            if self.x_scale == "log" and self.x_min <= 0:
                self.x_min = 0.1
                self.x_max = max(self.x_max, 10.0)
            if self.y_scale == "log" and self.y_min <= 0:
                self.y_min = 0.1
                self.y_max = max(self.y_max, 10.0)
            try:
                self.plot_w = max(220, min(self.canvas.A4_WIDTH - 40, int(w_entry.get_text())))
                self.plot_h = max(150, min(600, int(h_entry.get_text())))
            except ValueError:
                pass
            self.show_grid = grid_chk.get_active()
            self.show_legend = leg_chk.get_active()
            self.x_title = xt_entry.get_text().strip()
            self.y_title = yt_entry.get_text().strip()
            self.update_layout()
            self.canvas.move_box(self, self.x, self.y)
            self.canvas.notify_toc_changed()
            self.queue_draw()
        self.dragging = False
        dlg.destroy()


# ============================================================================
# Pasted / Inserted Picture Box (ImageBox) with Interactive Drag-Resize Handles
# ============================================================================

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf


class ImageBox(Gtk.DrawingArea):
    """
    Picture / Image box on the A4 worksheet.
    - Supports pasting directly from clipboard (Ctrl+V) or inserting from file.
    - Interactive drag-resize handles on the bottom-right corner, right edge, and bottom edge.
    - Scroll wheel scales the picture proportionally; double-click configures caption & size.
    """

    CAPTION_HEIGHT = 28
    HANDLE_SIZE = 10

    def __init__(self, canvas, x, y, pixbuf: GdkPixbuf.Pixbuf, title="", width=None, height=None):
        super().__init__()
        self.canvas = canvas
        self.orig_pixbuf = pixbuf
        orig_w = max(1, pixbuf.get_width())
        orig_h = max(1, pixbuf.get_height())
        self.aspect = orig_w / float(orig_h)

        if width is not None and height is not None:
            self.img_w = max(32, int(width))
            self.img_h = max(24, int(height))
        else:
            max_init_w = min(480, self.canvas.A4_WIDTH - 80)
            if orig_w > max_init_w:
                self.img_w = int(max_init_w)
                self.img_h = max(32, int(round(self.img_w / self.aspect)))
            else:
                self.img_w = int(orig_w)
                self.img_h = int(orig_h)

        self.title = title
        self.fig_num = 1
        self.editing = False
        self.selected = False
        self.dragging = False
        self.resizing_mode = None  # None, "corner", "right", "bottom"
        self.drag_start_root_x = 0
        self.drag_start_root_y = 0
        self.drag_start_box_x = 0
        self.drag_start_box_y = 0
        self.resize_start_w = self.img_w
        self.resize_start_h = self.img_h

        self.x = int(x)
        self.y = int(y)
        self.box_w = self.img_w + 8
        self.box_h = self.img_h + 8
        self.logical_w = self.box_w
        self.logical_h = self.box_h
        self._scaled_cache = None
        self.update_layout()

        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.SCROLL_MASK
        )
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("leave-notify-event", self.on_leave_notify)
        self.connect("key-press-event", self.on_key_press)
        self.connect("scroll-event", self.on_scroll)

    def get_caption_text(self) -> str:
        raw = self.title.strip()
        if not raw:
            return ""
        if raw.lower().startswith("figure "):
            parts = raw.split(":", 1)
            if len(parts) == 2 and parts[0][7:].strip().isdigit():
                raw = parts[1].strip()
        return f"Figure {self.fig_num}: {raw}" if raw else f"Figure {self.fig_num}"

    def _make_caption_layout(self, pango_ctx=None):
        caption_str = self.get_caption_text()
        if not caption_str:
            return None, 0, 0
        if pango_ctx is None:
            pango_ctx = self.get_pango_context()
        t_layout, _, _, _ = MathRenderer._make_layout(pango_ctx, caption_str, 0.76, bold=True)
        wrap_w = max(48, int(self.img_w))
        t_layout.set_width(wrap_w * Pango.SCALE)
        t_layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        t_layout.set_alignment(Pango.Alignment.CENTER)
        _, logical = t_layout.get_pixel_extents()
        return t_layout, wrap_w, max(20, int(math.ceil(logical.height)) + 8)

    def update_layout(self):
        _sched = getattr(getattr(self, "canvas", None), "schedule_page_breaks", None)
        if _sched:
            _sched()
        _, _, extra_h = self._make_caption_layout()
        self.box_w = self.img_w + 8
        self.box_h = self.img_h + 8 + extra_h
        self.logical_w = self.box_w
        self.logical_h = self.box_h
        self._scaled_cache = self.orig_pixbuf.scale_simple(
            max(1, self.img_w), max(1, self.img_h), GdkPixbuf.InterpType.BILINEAR
        )
        z = getattr(self.canvas, "zoom", 1.0)
        self.set_size_request(
            max(24, int(math.ceil(self.box_w * z))),
            max(24, int(math.ceil(self.box_h * z))),
        )
        self.queue_draw()

    def _update_size_request(self):
        self.update_layout()

    def is_empty(self):
        return False

    def set_selected(self, selected):
        self.selected = selected
        self.queue_draw()

    def start_editing(self):
        self.open_config_dialog()

    def stop_editing(self):
        self.editing = False
        self.queue_draw()

    def _hit_resize_handle(self, lx: float, ly: float):
        """Detect if logical coordinates (lx, ly) are over corner, right, or bottom resize grips."""
        w = self.box_w
        img_bot = self.img_h + 8
        g = 14.0
        if lx >= w - g and (img_bot - g <= ly <= self.box_h):
            return "corner"
        if lx >= w - g and 0 <= ly <= img_bot:
            return "right"
        if (img_bot - g <= ly <= self.box_h) and 0 <= lx <= w:
            return "bottom"
        return None

    def _set_cursor_by_name(self, name):
        win = self.get_window()
        if win is None:
            return
        if name is None:
            win.set_cursor(None)
            return
        display = win.get_display()
        try:
            cursor = Gdk.Cursor.new_from_name(display, name)
            win.set_cursor(cursor)
        except Exception:
            win.set_cursor(None)

    def draw_content(self, cr, theme=None, for_export=False):
        if theme is None:
            theme = THEMES[self.canvas.theme_name]
        w, h = self.box_w, self.box_h

        if self._scaled_cache is not None:
            cr.save()
            Gdk.cairo_set_source_pixbuf(cr, self._scaled_cache, 4, 4)
            cr.paint()
            cr.restore()

        if self.title.strip():
            pango_ctx = self.get_pango_context()
            t_layout, wrap_w, _ = self._make_caption_layout(pango_ctx)
            if t_layout is not None:
                cr.save()
                cr.set_source_rgb(*theme["heading_text"])
                cr.move_to((w - wrap_w) / 2.0, self.img_h + 8)
                PangoCairo.show_layout(cr, t_layout)
                cr.restore()

        if for_export:
            return

        if self.selected or self.resizing_mode is not None:
            cr.save()
            cr.set_source_rgb(*theme["box_selected_border"])
            cr.set_line_width(1.4)
            cr.set_dash([4.0, 3.0])
            cr.rectangle(0.7, 0.7, w - 1.4, h - 1.4)
            cr.stroke()
            cr.restore()

            # Draw interactive resize handles (bottom-right corner, right midpoint, bottom midpoint)
            hs = 8.0
            img_bot = self.img_h + 4
            handles = [
                (w - hs - 1, img_bot - hs / 2.0),  # bottom-right corner
                (w - hs - 1, max(4.0, (img_bot - hs) / 2.0)),  # right edge
                (max(4.0, (w - hs) / 2.0), img_bot - hs / 2.0),  # bottom edge
            ]
            cr.save()
            for hx, hy in handles:
                cr.set_source_rgb(*theme["canvas_bg"])
                cr.rectangle(hx, hy, hs, hs)
                cr.fill()
                cr.set_source_rgb(*theme["box_editing_border"])
                cr.set_line_width(1.4)
                cr.rectangle(hx, hy, hs, hs)
                cr.stroke()
            cr.restore()

            if self.resizing_mode is None:
                draw_figure_caption_button(self, cr, theme)

            # Live dimension badge while resizing
            if self.resizing_mode is not None:
                pango_ctx = self.get_pango_context()
                dim_lay, dw, da, dd = MathRenderer._make_layout(
                    pango_ctx, f"{self.img_w} × {self.img_h} px", 0.62, bold=True
                )
                cr.save()
                cr.set_source_rgba(0.1, 0.12, 0.16, 0.82)
                cr.rectangle(6, 6, dw + 10, da + dd + 6)
                cr.fill()
                cr.set_source_rgb(0.95, 0.97, 1.0)
                cr.move_to(11, 9)
                PangoCairo.show_layout(cr, dim_lay)
                cr.restore()

    def on_draw(self, widget, cr):
        z = getattr(self.canvas, "zoom", 1.0)
        cr.save()
        cr.scale(z, z)
        self.draw_content(cr, for_export=False)
        cr.restore()
        return True

    def on_button_press(self, widget, event):
        if event.button == 1:
            z = getattr(self.canvas, "zoom", 1.0)
            lx, ly = event.x / z, event.y / z
            was_selected = self.selected
            self.canvas.handle_box_button_press(self, event)
            self.canvas.focus_without_scroll(self)
            if was_selected and hit_figure_caption_button(self, lx, ly):
                self.dragging = False
                self.resizing_mode = None
                GLib.idle_add(lambda: open_figure_caption_dialog(self) and False)
                return True
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.dragging = False
                self.resizing_mode = None
                GLib.idle_add(self._open_config_dialog_idle)
                return True

            handle = self._hit_resize_handle(lx, ly)
            if handle is not None:
                self.resizing_mode = handle
                self.drag_start_root_x = event.x_root
                self.drag_start_root_y = event.y_root
                self.resize_start_w = self.img_w
                self.resize_start_h = self.img_h
                self.queue_draw()
                return True

            self.dragging = True
            self.drag_start_root_x = event.x_root
            self.drag_start_root_y = event.y_root
            self.drag_start_box_x = self.x
            self.drag_start_box_y = self.y
            return True
        if event.button == 3:
            if self not in self.canvas.selected_boxes:
                self.canvas.select_box(self)
            self._show_context_menu(event)
            return True
        return False

    def _show_context_menu(self, event):
        menu = Gtk.Menu()
        for label, cb in (
            ("Picture Options & Size…", lambda: GLib.idle_add(self._open_config_dialog_idle)),
            ("Caption…", lambda: GLib.idle_add(lambda: open_figure_caption_dialog(self) and False)),
            (None, None),
            ("Delete Picture", lambda: self.canvas.remove_selected_boxes(self)),
        ):
            if label is None:
                menu.append(Gtk.SeparatorMenuItem())
                continue
            mi = Gtk.MenuItem(label=label)
            mi.connect("activate", lambda _m, f=cb: f())
            menu.append(mi)
        menu.show_all()
        menu.popup_at_pointer(event)

    def _open_config_dialog_idle(self):
        self.dragging = False
        self.resizing_mode = None
        self.open_config_dialog()
        return False

    def on_motion_notify(self, widget, event):
        z = getattr(self.canvas, "zoom", 1.0)
        lx, ly = event.x / z, event.y / z

        if self.resizing_mode is not None:
            if not (event.state & Gdk.ModifierType.BUTTON1_MASK):
                self.resizing_mode = None
                return False
            dx = (event.x_root - self.drag_start_root_x) / z
            dy = (event.y_root - self.drag_start_root_y) / z
            free_aspect = bool(event.state & Gdk.ModifierType.SHIFT_MASK)
            max_w = max(80, self.canvas.A4_WIDTH - self.x - 16)
            max_h = max(60, self.canvas.total_height - self.y - 36)

            if self.resizing_mode == "corner":
                new_w = max(36, min(max_w, int(round(self.resize_start_w + dx))))
                if free_aspect:
                    new_h = max(24, min(max_h, int(round(self.resize_start_h + dy))))
                else:
                    new_h = max(24, min(max_h, int(round(new_w / self.aspect))))
                    new_w = max(36, min(max_w, int(round(new_h * self.aspect))))
                self.img_w, self.img_h = new_w, new_h
            elif self.resizing_mode == "right":
                new_w = max(36, min(max_w, int(round(self.resize_start_w + dx))))
                self.img_w = new_w
                if not free_aspect:
                    self.img_h = max(24, min(max_h, int(round(new_w / self.aspect))))
            elif self.resizing_mode == "bottom":
                new_h = max(24, min(max_h, int(round(self.resize_start_h + dy))))
                self.img_h = new_h
                if not free_aspect:
                    self.img_w = max(36, min(max_w, int(round(new_h * self.aspect))))

            self.update_layout()
            return True

        if self.dragging:
            if not (event.state & Gdk.ModifierType.BUTTON1_MASK):
                self.dragging = False
                return False
            dx = int((event.x_root - self.drag_start_root_x) / z)
            dy = int((event.y_root - self.drag_start_root_y) / z)
            self.canvas.drag_box_or_group(self, dx, dy)
            return True

        # Update hover cursor over resize handles
        handle = self._hit_resize_handle(lx, ly)
        if handle == "corner":
            self._set_cursor_by_name("nwse-resize")
        elif handle == "right":
            self._set_cursor_by_name("ew-resize")
        elif handle == "bottom":
            self._set_cursor_by_name("ns-resize")
        else:
            self._set_cursor_by_name(None)
        return False

    def on_leave_notify(self, widget, event):
        if self.resizing_mode is None:
            self._set_cursor_by_name(None)
        return False

    def on_button_release(self, widget, event):
        if event.button == 1:
            if self.resizing_mode is not None:
                self.resizing_mode = None
                self.aspect = max(1, self.img_w) / float(max(1, self.img_h))
                self.queue_draw()
                return True
            if self.dragging:
                self.dragging = False
                self.canvas.recalculate_worksheet()
                return True
        return False

    def on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ("Delete", "BackSpace"):
            self.canvas.remove_selected_boxes(self)
            return True
        if keyname in ("Return", "KP_Enter"):
            self.open_config_dialog()
            return True
        return False

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            return self.canvas.on_scroll_zoom(widget, event)
        factor = 1.10 if event.direction == Gdk.ScrollDirection.UP else (
            0.90 if event.direction == Gdk.ScrollDirection.DOWN else 1.0
        )
        if factor != 1.0:
            new_w = max(36, min(self.canvas.A4_WIDTH - 40, int(round(self.img_w * factor))))
            self.img_w = new_w
            self.img_h = max(24, int(round(self.img_w / self.aspect)))
            self.update_layout()
            return True
        return False

    def open_config_dialog(self):
        toplevel = self.get_toplevel()
        parent = toplevel if isinstance(toplevel, Gtk.Window) else None
        dlg = Gtk.Dialog(title="Picture Options & Size", transient_for=parent, flags=0)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_APPLY, Gtk.ResponseType.OK)

        content = dlg.get_content_area()
        grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        grid.set_margin_start(14)
        grid.set_margin_end(14)
        grid.set_margin_top(12)
        grid.set_margin_bottom(12)
        content.add(grid)

        title_entry = Gtk.Entry(text=self.title)
        w_entry = Gtk.Entry(text=str(self.img_w))
        h_entry = Gtk.Entry(text=str(self.img_h))
        lock_chk = Gtk.CheckButton(label="Preserve aspect ratio")
        lock_chk.set_active(True)
        center_chk = Gtk.CheckButton(label="Center horizontally on A4 page")
        center_chk.set_active(abs(self.x - (self.canvas.A4_WIDTH - self.box_w) // 2) <= 10)

        grid.attach(Gtk.Label(label="Caption (optional):"), 0, 0, 1, 1)
        grid.attach(title_entry, 1, 0, 1, 1)
        grid.attach(Gtk.Label(label="Width (px):"), 0, 1, 1, 1)
        grid.attach(w_entry, 1, 1, 1, 1)
        grid.attach(Gtk.Label(label="Height (px):"), 0, 2, 1, 1)
        grid.attach(h_entry, 1, 2, 1, 1)
        grid.attach(lock_chk, 0, 3, 2, 1)
        grid.attach(center_chk, 0, 4, 2, 1)

        dlg.show_all()
        if dlg.run() == Gtk.ResponseType.OK:
            self.title = title_entry.get_text().strip()
            try:
                new_w = max(36, min(self.canvas.A4_WIDTH - 40, int(w_entry.get_text())))
                if lock_chk.get_active():
                    new_h = max(24, int(round(new_w / self.aspect)))
                else:
                    new_h = max(24, min(self.canvas.A4_HEIGHT - 60, int(h_entry.get_text())))
                    self.aspect = new_w / float(new_h)
                self.img_w, self.img_h = new_w, new_h
            except ValueError:
                pass
            self.update_layout()
            if center_chk.get_active():
                self.canvas.move_box(self, max(0, (self.canvas.A4_WIDTH - self.box_w) // 2), self.y)
            self.canvas.recalculate_worksheet()
            self.canvas.notify_toc_changed()
            self.queue_draw()
        dlg.destroy()


# ============================================================================
# Link Box (a clickable web address shown as text; double-click to edit)
# ============================================================================

LINK_FONT = "Ubuntu, DejaVu Sans, sans-serif 12"


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if url and "://" not in url and not url.startswith("mailto:"):
        url = "https://" + url
    return url


def ask_link(parent, url="", text=""):
    """Dialog for a link's web address and display text. Returns (url, text) or None."""
    dlg = Gtk.Dialog(
        title="Link",
        transient_for=parent if isinstance(parent, Gtk.Window) else None,
        flags=0,
    )
    dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
    dlg.set_default_response(Gtk.ResponseType.OK)
    dlg.set_default_size(440, -1)
    area = dlg.get_content_area()
    for side in ("start", "end", "top", "bottom"):
        getattr(area, f"set_margin_{side}")(12)
    grid = Gtk.Grid(column_spacing=10, row_spacing=8)
    url_entry = Gtk.Entry(text=url, hexpand=True)
    url_entry.set_placeholder_text("https://example.com")
    url_entry.set_activates_default(True)
    text_entry = Gtk.Entry(text=text, hexpand=True)
    text_entry.set_placeholder_text("Text shown on the sheet (the address if left empty)")
    text_entry.set_activates_default(True)
    grid.attach(Gtk.Label(label="Web address:", xalign=1.0), 0, 0, 1, 1)
    grid.attach(url_entry, 1, 0, 1, 1)
    grid.attach(Gtk.Label(label="Display text:", xalign=1.0), 0, 1, 1, 1)
    grid.attach(text_entry, 1, 1, 1, 1)
    area.pack_start(grid, False, False, 0)
    dlg.show_all()
    url_entry.grab_focus()
    result = None
    if dlg.run() == Gtk.ResponseType.OK:
        result = (normalize_url(url_entry.get_text()), text_entry.get_text().strip())
    dlg.destroy()
    return result


def open_url(widget, url: str):
    url = normalize_url(url)
    if not url:
        return
    toplevel = widget.get_toplevel() if widget is not None else None
    try:
        Gtk.show_uri_on_window(toplevel if isinstance(toplevel, Gtk.Window) else None, url, Gdk.CURRENT_TIME)
    except Exception:
        try:
            import subprocess
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


class LinkBox(Gtk.DrawingArea):
    """A web link on the sheet: shown as underlined text. Ctrl+click opens it in the web
    browser; double-click edits the address and display text. Exported to PDF as a live link."""

    PAD_X = 3.0
    PAD_Y = 3.0

    def __init__(self, canvas, x, y, url="", text=""):
        super().__init__()
        self.canvas = canvas
        self.x = int(x)
        self.y = int(y)
        self.url = normalize_url(url)
        self.text = text or ""
        self.editing = False
        self.selected = False
        self.dragging = False
        self.drag_start_root_x = self.drag_start_root_y = 0
        self.drag_start_box_x = self.drag_start_box_y = 0
        self.logical_w = 40
        self.logical_h = 24
        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("key-press-event", self.on_key_press)
        self.update_layout()

    def shown_text(self) -> str:
        return self.text or self.url or "[link]"

    def is_empty(self):
        return False

    def set_selected(self, selected):
        self.selected = selected
        self.queue_draw()

    def start_editing(self):
        pass

    def stop_editing(self):
        self.editing = False

    def _layout(self, pango_ctx=None):
        lay = Pango.Layout.new(pango_ctx or self.get_pango_context())
        lay.set_font_description(Pango.FontDescription.from_string(LINK_FONT))
        lay.set_text(self.shown_text(), -1)
        attrs = Pango.AttrList()
        attrs.insert(Pango.attr_underline_new(Pango.Underline.SINGLE))
        lay.set_attributes(attrs)
        return lay

    def update_layout(self):
        _sched = getattr(getattr(self, "canvas", None), "schedule_page_breaks", None)
        if _sched:
            _sched()
        _, logical = self._layout().get_pixel_extents()
        self.logical_w = int(math.ceil(logical.width + 2 * self.PAD_X))
        self.logical_h = int(math.ceil(logical.height + 2 * self.PAD_Y))
        z = getattr(self.canvas, "zoom", 1.0)
        self.set_size_request(max(8, int(math.ceil(self.logical_w * z))), max(8, int(math.ceil(self.logical_h * z))))
        self.set_tooltip_text(f"{self.url}\nCtrl+click to open · double-click to edit" if self.url else
                              "Double-click to set the web address")
        self.queue_draw()

    @staticmethod
    def _link_rgb(theme):
        tr, tg, tb = theme["text"][:3]
        return (0.45, 0.66, 1.0) if (tr + tg + tb) / 3.0 > 0.5 else (0.08, 0.33, 0.80)

    def draw_content(self, cr, theme=None, for_export=False):
        if theme is None:
            theme = THEMES[self.canvas.theme_name]
        lay = self._layout()
        tagged = for_export and self.url and hasattr(cr, "tag_begin")
        if tagged:
            safe = self.url.replace("\\", "\\\\").replace("'", "\\'")
            cr.tag_begin(cairo.TAG_LINK, f"uri='{safe}'")
        cr.save()
        cr.set_source_rgb(*self._link_rgb(theme))
        cr.move_to(self.PAD_X, self.PAD_Y)
        PangoCairo.show_layout(cr, lay)
        cr.restore()
        if tagged:
            cr.tag_end(cairo.TAG_LINK)
        if not for_export and self.selected:
            cr.save()
            cr.set_source_rgb(*theme["box_selected_border"])
            cr.set_line_width(1.2)
            cr.set_dash([4.0, 3.0])
            cr.rectangle(0.6, 0.6, self.logical_w - 1.2, self.logical_h - 1.2)
            cr.stroke()
            cr.restore()

    def on_draw(self, widget, cr):
        z = getattr(self.canvas, "zoom", 1.0)
        cr.save()
        cr.scale(z, z)
        self.draw_content(cr, for_export=False)
        cr.restore()
        return True

    def edit_link(self):
        res = ask_link(self.get_toplevel(), self.url, self.text)
        if res is not None:
            self.url, self.text = res
            if not self.url and not self.text:
                self.canvas.remove_box(self)
                return False
            self.update_layout()
            self.canvas.notify_toc_changed()
        self.canvas.focus_without_scroll(self)
        return False

    def on_button_press(self, widget, event):
        if event.button == 3:
            if self not in self.canvas.selected_boxes:
                self.canvas.select_box(self)
            self._show_context_menu(event)
            return True
        if event.button != 1:
            return False
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.type == Gdk.EventType.BUTTON_PRESS:
            open_url(self, self.url)
            return True
        self.canvas.handle_box_button_press(self, event)
        self.canvas.focus_without_scroll(self)
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.dragging = False
            GLib.idle_add(self.edit_link)
            return True
        self.dragging = True
        self.drag_start_root_x, self.drag_start_root_y = event.x_root, event.y_root
        self.drag_start_box_x, self.drag_start_box_y = self.x, self.y
        return True

    def on_motion_notify(self, widget, event):
        win = self.get_window()
        if win is not None:
            try:
                name = "pointer" if event.state & Gdk.ModifierType.CONTROL_MASK else None
                win.set_cursor(Gdk.Cursor.new_from_name(win.get_display(), name) if name else None)
            except Exception:
                pass
        if self.dragging:
            if not (event.state & Gdk.ModifierType.BUTTON1_MASK):
                self.dragging = False
                return False
            z = getattr(self.canvas, "zoom", 1.0)
            dx = int((event.x_root - self.drag_start_root_x) / z)
            dy = int((event.y_root - self.drag_start_root_y) / z)
            self.canvas.drag_box_or_group(self, dx, dy)
            return True
        return False

    def on_button_release(self, widget, event):
        if event.button == 1 and self.dragging:
            self.dragging = False
            self.canvas.recalculate_worksheet()
            return True
        return False

    def on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ("Delete", "BackSpace"):
            self.canvas.remove_selected_boxes(self)
            return True
        if keyname in ("Return", "KP_Enter"):
            GLib.idle_add(self.edit_link)
            return True
        return False

    def _show_context_menu(self, event):
        menu = Gtk.Menu()
        for label, cb, ok in (
            ("Open Link", lambda: open_url(self, self.url), bool(self.url)),
            ("Edit Link…", lambda: GLib.idle_add(self.edit_link), True),
            ("Copy Address", lambda: Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(self.url, -1), bool(self.url)),
            (None, None, True),
            ("Delete", lambda: self.canvas.remove_selected_boxes(self), True),
        ):
            if label is None:
                menu.append(Gtk.SeparatorMenuItem())
                continue
            mi = Gtk.MenuItem(label=label)
            mi.set_sensitive(ok)
            mi.connect("activate", lambda _mi, f=cb: f())
            menu.append(mi)
        menu.show_all()
        menu.popup_at_pointer(event)

    def to_dict(self) -> dict:
        return {"type": "link", "x": self.x, "y": self.y, "url": self.url, "text": self.text}


# ============================================================================
# Drawing Box (simple illustrations from shapes: lines, arrows, rectangles,
# ellipses and text labels — a movable figure with a caption)
# ============================================================================

DRAW_COLORS = [
    ("auto", None),  # follows the theme text colour (black on paper / PDF)
    ("red", (0.85, 0.15, 0.15)),
    ("blue", (0.12, 0.40, 0.85)),
    ("green", (0.10, 0.58, 0.25)),
    ("orange", (0.95, 0.55, 0.10)),
    ("gray", (0.55, 0.57, 0.60)),
]
DRAW_COLOR_LABELS = {
    "auto": "Automatic (black / white)", "red": "Red", "blue": "Blue",
    "green": "Green", "orange": "Orange", "gray": "Gray",
}
DRAW_TOOLS = [
    ("select", "↖ Select"),
    ("line", "╱ Line"),
    ("arrow", "→ Arrow"),
    ("arrow2", "↔ Double Arrow"),
    ("rect", "▭ Rectangle"),
    ("ellipse", "◯ Ellipse"),
    ("triangle", "△ Triangle"),
    ("arc", "◜ Arc"),
    ("text", "T Text"),
    ("resistor", "⏛ Resistor"),
    ("resistor_box", "▭ Resistor (IEC box)"),
    ("capacitor", "⊣⊢ Capacitor"),
    ("switch", "⌁ Switch"),
    ("ground", "⏚ Ground"),
    ("fan", "✇ Fan"),
]
# Electrical symbols: drawn along the segment (x1, y1) → (x2, y2), so dragging an end
# resizes and rotates them (Shift snaps to 45°). Ground hangs from (x1, y1).
DRAW_ELEC_TYPES = ("resistor", "resistor_box", "capacitor", "switch", "ground", "fan")
DRAW_ELEC_TOOLS = [t for t in DRAW_TOOLS if t[0] in DRAW_ELEC_TYPES]
DRAW_LINE_TOOLS = [t for t in DRAW_TOOLS if t[0] in ("line", "arrow", "arrow2")]
DRAW_SHAPE_TOOLS = [t for t in DRAW_TOOLS if t[0] not in ("select", "line", "arrow", "arrow2") + DRAW_ELEC_TYPES]
DRAW_FILLABLE = ("rect", "ellipse", "triangle")
DRAW_IMAGE_MAX_PX = 1600  # pasted pictures are scaled down to this size (longest side)
_DRAW_SHAPES_CLIP_MARK = "\u2063CommentariuM drawing shapes"  # on the system clipboard after copying shapes
DRAW_TEXT_FONT = "Ubuntu, DejaVu Sans, sans-serif 11"
DRAW_LINE_TYPES = ("line", "arrow", "arrow2")
# Line thicknesses offered for every shape (drawing units)
DRAW_WIDTHS = [("thin", "─ Thin", 1.0), ("medium", "━ Medium", 1.8), ("thick", "▬ Thick", 3.2)]
DRAW_HEADS = [("filled", "▶ Filled Head"), ("open", "> Simple Head")]
# Fill of rectangles, ellipses and triangles, set apart from the outline colour:
#   s["fill"]: False (none) | "outline" (same colour as the outline) | a colour key below
#   s["fill_light"]: True = light, see-through tint; False = solid
# (older files: fill True meant a light tint of the outline colour)
DRAW_FILL_COLORS = [
    ("black", (0.0, 0.0, 0.0)), ("white", (1.0, 1.0, 1.0)),
    ("red", (0.85, 0.15, 0.15)), ("blue", (0.12, 0.40, 0.85)), ("green", (0.10, 0.58, 0.25)),
    ("orange", (0.95, 0.55, 0.10)), ("gray", (0.55, 0.57, 0.60)), ("yellow", (0.98, 0.85, 0.20)),
]
DRAW_FILL_LABELS = {"outline": "Same as Outline", "black": "Black", "white": "White", "red": "Red",
                    "blue": "Blue", "green": "Green", "orange": "Orange", "gray": "Gray", "yellow": "Yellow"}


def draw_fill_key(v):
    """Normalised fill value: False, 'outline' or a colour key."""
    if v is True:
        return "outline"
    return v if v == "outline" or v in dict(DRAW_FILL_COLORS) else False


def draw_fill_light(s) -> bool:
    if "fill_light" in s:
        return bool(s["fill_light"])
    return s.get("fill") is True  # old tint fills


_DRAW_CLIPBOARD = {"shapes": [], "pastes": 0}  # shapes copied inside drawings (shared by all drawings)


def draw_width_key(w: float) -> str:
    """Nearest named thickness for a stored width."""
    return min(DRAW_WIDTHS, key=lambda d: abs(d[2] - float(w)))[0]


class DrawingBox(Gtk.DrawingArea):
    """A figure made of simple shapes. Double-click (or Enter) to draw; the tool strip
    appears under the drawing while editing. Shapes are kept in drawing coordinates."""

    PAD = 4
    BTN_H = 24
    HANDLE = 7.0
    CAPTION_PREFIX = "Figure"
    CAPTION_WHERE = "beneath"

    def __init__(self, canvas, x, y, width=420, height=240, title="", shapes=None, background=True):
        super().__init__()
        self.canvas = canvas
        self.x = int(x)
        self.y = int(y)
        self.draw_w = max(60, int(width))
        self.draw_h = max(40, int(height))
        self.title = title
        self.shapes = [self._normalize_shape(dict(s)) for s in (shapes or [])]
        self.background = bool(background)
        self.fig_num = 1

        self.editing = False
        self.selected = False
        self.dragging = False
        self.resizing = False
        self.drag_start_root_x = 0
        self.drag_start_root_y = 0
        self.drag_start_box_x = 0
        self.drag_start_box_y = 0
        self.resize_start_w = self.draw_w
        self.resize_start_h = self.draw_h
        self.cropping = None  # "l" | "r" | "t" | "b" while dragging a crop handle

        self.tool = "select"
        self.cur_color = "auto"
        self.cur_fill = False
        self.cur_fill_light = False
        self.cur_width = 1.8
        self.cur_head = "filled"
        self.cur_shape = "line"  # shape shown in the Shape combo
        self.sel_shape = None  # index into self.shapes
        self.op = None  # active mouse operation while editing
        self._strip_buttons = []  # (key, rect) in widget logical coords
        self.logical_w = self.draw_w + 2 * self.PAD
        self.logical_h = self.draw_h + 2 * self.PAD

        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("leave-notify-event", lambda *_a: self._set_cursor_by_name(None) or False)
        self.connect("key-press-event", self.on_key_press)
        self.update_layout()

    # ---- shape selection (one primary shape, optionally several) ------------------

    @property
    def sel_shape(self):
        return getattr(self, "_sel_primary", None)

    @sel_shape.setter
    def sel_shape(self, idx):
        self._sel_primary = idx
        self._sel_set = [] if idx is None else [idx]

    def _set_selection(self, indices):
        idx = sorted({i for i in indices if 0 <= i < len(self.shapes)})
        self._sel_set = idx
        self._sel_primary = idx[-1] if idx else None

    def _selected_indices(self):
        return [i for i in getattr(self, "_sel_set", []) if 0 <= i < len(self.shapes)]

    def _multi(self):
        return len(self._selected_indices()) > 1

    @staticmethod
    def _shift_shape(sh, dx, dy, orig=None):
        o = orig or sh
        for k in ("x1", "x2", "x3"):
            if k in sh:
                sh[k] = o[k] + dx
        for k in ("y1", "y2", "y3"):
            if k in sh:
                sh[k] = o[k] + dy

    # ---- basic box protocol --------------------------------------------------

    def is_empty(self):
        return False

    def set_selected(self, selected):
        self.selected = selected
        self.queue_draw()

    def start_editing(self):
        self.editing = True
        self.dragging = False
        self.resizing = False
        self.selected = True
        self.canvas.focus_without_scroll(self)
        self.update_layout()

    def stop_editing(self):
        if not self.editing:
            return
        self.editing = False
        self.sel_shape = None
        self.op = None
        self.tool = "select"
        self.update_layout()

    def get_caption_text(self) -> str:
        raw = self.title.strip()
        if not raw:
            return ""
        if raw.lower().startswith("figure "):
            parts = raw.split(":", 1)
            if len(parts) == 2 and parts[0][7:].strip().isdigit():
                raw = parts[1].strip()
        return f"Figure {self.fig_num}: {raw}" if raw else f"Figure {self.fig_num}"

    def _make_caption_layout(self, pango_ctx=None):
        caption_str = self.get_caption_text()
        if not caption_str:
            return None, 0, 0
        if pango_ctx is None:
            pango_ctx = self.get_pango_context()
        t_layout, _, _, _ = MathRenderer._make_layout(pango_ctx, caption_str, 0.76, bold=True)
        wrap_w = max(48, int(self.draw_w))
        t_layout.set_width(wrap_w * Pango.SCALE)
        t_layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        t_layout.set_alignment(Pango.Alignment.CENTER)
        _, logical = t_layout.get_pixel_extents()
        return t_layout, wrap_w, max(20, int(math.ceil(logical.height)) + 8)

    def _layout_strip(self):
        """Flow the tool-strip buttons under the drawing; returns the strip height."""
        pango_ctx = self.get_pango_context()
        # "dd:" entries are drop-down (combo) buttons that open a list
        items = [
            ("dd:line", "Line  ▾"),
            ("dd:shape", "Shape  ▾"),
            ("dd:color", "      Outline  ▾"),
            ("dd:fill", "      Fill  ▾"),
            ("dd:width", "Thickness  ▾"),
            ("background", "▣ Background" if self.background else "▢ Background"),
        ]
        x0 = self.PAD
        y0 = self.PAD + self.draw_h + 6
        max_x = max(self.draw_w, 260) + self.PAD
        bx, by = x0, y0
        self._strip_buttons = []
        for key, lbl in items:
            if lbl is None:
                bw = float(self.BTN_H - 4)
            else:
                _, lw, _, _ = MathRenderer._make_layout(pango_ctx, lbl, 0.62, bold=True)
                bw = lw + 12.0
            if bx + bw > max_x and bx > x0:
                bx = x0
                by += self.BTN_H + 4
            self._strip_buttons.append((key, lbl, (bx, by, bw, float(self.BTN_H))))
            bx += bw + 4
        return (by + self.BTN_H + 4) - (self.PAD + self.draw_h)

    def update_layout(self):
        _sched = getattr(getattr(self, "canvas", None), "schedule_page_breaks", None)
        if _sched:
            _sched()
        strip_h = self._layout_strip() if self.editing else 0
        _, _, cap_h = self._make_caption_layout()
        self.strip_h = strip_h
        self.logical_w = max(self.draw_w, 260 if self.editing else 0) + 2 * self.PAD
        self.logical_h = self.draw_h + 2 * self.PAD + strip_h + cap_h
        z = getattr(self.canvas, "zoom", 1.0)
        self.set_size_request(
            max(24, int(math.ceil(self.logical_w * z))),
            max(24, int(math.ceil(self.logical_h * z))),
        )
        self.queue_draw()

    # ---- geometry helpers ----------------------------------------------------

    def _color_rgb(self, name, theme):
        for k, rgb in DRAW_COLORS:
            if k == name:
                return rgb if rgb is not None else theme["text"]
        return theme["text"]

    def _text_layout(self, shape, pango_ctx=None):
        if pango_ctx is None:
            pango_ctx = self.get_pango_context()
        lay = Pango.Layout.new(pango_ctx)
        lay.set_font_description(Pango.FontDescription.from_string(DRAW_TEXT_FONT))
        lay.set_text(shape.get("text", ""), -1)
        return lay

    @staticmethod
    def _elec_geometry(s):
        """Primitives of an electrical symbol: [("poly", [(x, y), …]) | ("circle", (cx, cy, r))].
        Built in a frame along p1 → p2 (t along, h across, both as fractions of the length)."""
        x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 1e-6:
            return [("poly", [(x1, y1), (x2, y2)])]
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        vx, vy = -uy, ux  # across; for a left→right symbol, -h is up on the screen

        def P(t, h=0.0):
            return (x1 + (ux * t + vx * h) * L, y1 + (uy * t + vy * h) * L)

        t = s["type"]
        if t == "resistor":
            pts = [P(0.0), P(0.25)]
            for i in range(6):
                pts.append(P(0.25 + 0.5 * (2 * i + 1) / 12.0, -0.09 if i % 2 == 0 else 0.09))
            pts += [P(0.75), P(1.0)]
            return [("poly", pts)]
        if t == "resistor_box":
            return [("poly", [P(0.0), P(0.25)]), ("poly", [P(0.75), P(1.0)]),
                    ("poly", [P(0.25, -0.09), P(0.75, -0.09), P(0.75, 0.09), P(0.25, 0.09), P(0.25, -0.09)])]
        if t == "capacitor":
            return [("poly", [P(0.0), P(0.44)]), ("poly", [P(0.56), P(1.0)]),
                    ("poly", [P(0.44, -0.2), P(0.44, 0.2)]), ("poly", [P(0.56, -0.2), P(0.56, 0.2)])]
        if t == "switch":
            r = 0.025
            a, b = P(0.3 + r), P(0.7 - r)
            return [("poly", [P(0.0), P(0.3)]), ("poly", [P(0.7), P(1.0)]),
                    ("circle", P(0.3) + (r * L,)), ("circle", P(0.7) + (r * L,)),
                    ("poly", [a, P(0.67, -0.19)])]
        if t == "ground":
            return [("poly", [P(0.0), P(0.6)]),
                    ("poly", [P(0.6, -0.32), P(0.6, 0.32)]),
                    ("poly", [P(0.8, -0.2), P(0.8, 0.2)]),
                    ("poly", [P(1.0, -0.08), P(1.0, 0.08)])]
        if t == "fan":  # a circle (diameter p1 → p2) with three filled blades round a hub
            prims = [("circle", P(0.5) + (0.5 * L,)), ("circle", P(0.5) + (0.07 * L,))]
            w = math.radians(80.0)
            for k in range(3):
                a0 = math.radians(-90.0 + 120.0 * k) - w / 2.0
                pts = []
                for j in range(21):
                    u = j / 20.0
                    rho = 0.42 * math.sin(math.pi * u) * (0.45 + 0.55 * u)
                    phi = a0 + w * u
                    pts.append(P(0.5 + rho * math.cos(phi), rho * math.sin(phi)))
                prims.append(("fpoly", pts))
            return prims
        return [("poly", [(x1, y1), (x2, y2)])]

    def _bbox(self, s):
        if s["type"] in DRAW_ELEC_TYPES:
            xs, ys = [], []
            for kind, data in self._elec_geometry(s):
                if kind == "circle":
                    cx, cy, rr = data
                    xs += [cx - rr, cx + rr]
                    ys += [cy - rr, cy + rr]
                else:
                    xs += [p[0] for p in data]
                    ys += [p[1] for p in data]
            return min(xs), min(ys), max(xs), max(ys)
        if s["type"] == "text":
            lay = self._text_layout(s)
            _, logical = lay.get_pixel_extents()
            return s["x1"], s["y1"], s["x1"] + logical.width, s["y1"] + logical.height
        if s["type"] in ("triangle", "arc"):
            pts = self._triangle_pts(s) if s["type"] == "triangle" else self._arc_pts(s, 24)
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return min(xs), min(ys), max(xs), max(ys)
        return min(s["x1"], s["x2"]), min(s["y1"], s["y2"]), max(s["x1"], s["x2"]), max(s["y1"], s["y2"])

    @staticmethod
    def _normalize_shape(s):
        """Bring shapes saved by older versions to the current form."""
        if s.get("type") == "triangle" and "x3" not in s:
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            s["x1"], s["y1"], s["x2"], s["y2"], s["x3"], s["y3"] = (x1 + x2) / 2.0, y1, x2, y2, x1, y2
        if s.get("type") == "arc" and "angle" not in s:
            # old quarter arcs bulged towards the corner (x1, y2)
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            nx, ny = -(y2 - y1), (x2 - x1)
            side = (x1 - (x1 + x2) / 2.0) * nx + (y2 - (y1 + y2) / 2.0) * ny
            s["angle"] = 90.0 if side >= 0 else -90.0
        return s

    @staticmethod
    def _triangle_pts(s):
        return [(s["x1"], s["y1"]), (s["x2"], s["y2"]), (s.get("x3", s["x1"]), s.get("y3", s["y2"]))]

    @staticmethod
    def _triangle_from_drag(s, sx, sy, ex, ey):
        """Isosceles triangle filling the drag box (apex on the start side)."""
        s["x1"], s["y1"] = (sx + ex) / 2.0, sy
        s["x2"], s["y2"] = ex, ey
        s["x3"], s["y3"] = sx, ey

    @staticmethod
    def _arc_geom(s):
        """Circular arc from (x1, y1) to (x2, y2) with included angle s['angle'] (degrees;
        the sign picks the side it bulges to). Returns (cx, cy, R, start_angle, sweep) or None
        for a straight segment."""
        x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
        theta = float(s.get("angle", 90.0))
        c = math.hypot(x2 - x1, y2 - y1)
        if c < 1e-6 or abs(theta) < 0.5:
            return None
        th = math.radians(min(359.0, abs(theta)))
        R = c / (2.0 * math.sin(th / 2.0))
        d = R * math.cos(th / 2.0)  # chord midpoint -> centre (negative past 180°)
        ux, uy = (x2 - x1) / c, (y2 - y1) / c
        nx, ny = -uy, ux
        sg = 1.0 if theta > 0 else -1.0
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        cx, cy = mx - sg * nx * d, my - sg * ny * d
        a1 = math.atan2(y1 - cy, x1 - cx)
        # bulge point (middle of the arc)
        bx, by = mx + sg * nx * (R - d), my + sg * ny * (R - d)
        am = math.atan2(by - cy, bx - cx)
        best = None
        for direction in (1.0, -1.0):
            mid = a1 + direction * th / 2.0
            err = abs(math.atan2(math.sin(mid - am), math.cos(mid - am)))
            if best is None or err < best[0]:
                best = (err, direction)
        return cx, cy, R, a1, best[1] * th

    @classmethod
    def _arc_pts(cls, s, n=48):
        g = cls._arc_geom(s)
        if g is None:
            return [(s["x1"], s["y1"]), (s["x2"], s["y2"])]
        cx, cy, R, a1, sweep = g
        return [(cx + R * math.cos(a1 + sweep * i / n), cy + R * math.sin(a1 + sweep * i / n)) for i in range(n + 1)]

    @classmethod
    def _arc_mid(cls, s):
        g = cls._arc_geom(s)
        if g is None:
            return (s["x1"] + s["x2"]) / 2.0, (s["y1"] + s["y2"]) / 2.0
        cx, cy, R, a1, sweep = g
        return cx + R * math.cos(a1 + sweep / 2.0), cy + R * math.sin(a1 + sweep / 2.0)

    @staticmethod
    def _arc_angle_from_mid(s, hx, hy):
        """Included angle for an arc whose middle is dragged to (hx, hy)."""
        x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
        c = math.hypot(x2 - x1, y2 - y1)
        if c < 1e-6:
            return s.get("angle", 90.0)
        nx, ny = -(y2 - y1) / c, (x2 - x1) / c
        h = (hx - (x1 + x2) / 2.0) * nx + (hy - (y1 + y2) / 2.0) * ny  # signed sagitta
        theta = math.degrees(4.0 * math.atan(2.0 * abs(h) / c))
        theta = max(1.0, min(359.0, theta))
        return theta if h >= 0 else -theta

    @staticmethod
    def _seg_dist(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
        cx, cy = x1 + t * dx, y1 + t * dy
        return math.hypot(px - cx, py - cy)

    def _hit_shape(self, ax, ay):
        for i in range(len(self.shapes) - 1, -1, -1):
            s = self.shapes[i]
            if s["type"] in DRAW_LINE_TYPES:
                if self._seg_dist(ax, ay, s["x1"], s["y1"], s["x2"], s["y2"]) <= 6 + s.get("width", 1.6):
                    return i
            elif s["type"] in DRAW_ELEC_TYPES:
                tol = 6 + s.get("width", 1.6)
                for kind, data in self._elec_geometry(s):
                    if kind == "circle":
                        if math.hypot(ax - data[0], ay - data[1]) <= data[2] + tol:
                            return i
                    elif any(self._seg_dist(ax, ay, *data[j], *data[j + 1]) <= tol for j in range(len(data) - 1)):
                        return i
            elif s["type"] == "arc":
                pts = self._arc_pts(s, 20)
                tol = 6 + s.get("width", 1.6)
                if any(self._seg_dist(ax, ay, *pts[j], *pts[j + 1]) <= tol for j in range(len(pts) - 1)):
                    return i
            else:
                x0, y0, x1, y1 = self._bbox(s)
                if x0 - 4 <= ax <= x1 + 4 and y0 - 4 <= ay <= y1 + 4:
                    return i
        return None

    def _handles(self, s):
        """[(name, x, y)] grips of a shape, in drawing coordinates."""
        if s["type"] in DRAW_LINE_TYPES or s["type"] in DRAW_ELEC_TYPES:
            return [("p1", s["x1"], s["y1"]), ("p2", s["x2"], s["y2"])]
        if s["type"] == "text":
            return []
        if s["type"] == "triangle":
            return [("v%d" % (i + 1), px, py) for i, (px, py) in enumerate(self._triangle_pts(s))]
        if s["type"] == "arc":
            mx, my = self._arc_mid(s)
            return [("p1", s["x1"], s["y1"]), ("p2", s["x2"], s["y2"]), ("mid", mx, my)]
        x0, y0, x1, y1 = self._bbox(s)
        return [("nw", x0, y0), ("ne", x1, y0), ("sw", x0, y1), ("se", x1, y1)]

    def _hit_handle(self, ax, ay):
        if self.sel_shape is None or self.sel_shape >= len(self.shapes) or self._multi():
            return None
        for name, hx, hy in self._handles(self.shapes[self.sel_shape]):
            if abs(ax - hx) <= self.HANDLE and abs(ay - hy) <= self.HANDLE:
                return name
        return None

    def _hit_box_resize(self, lx, ly):
        gx = self.PAD + self.draw_w
        gy = self.PAD + self.draw_h
        return abs(lx - gx) <= 9 and abs(ly - gy) <= 9

    def _crop_handles(self):
        """Crop handles at the middle of each edge: (side, x, y, horizontal_bar)."""
        P, w, h = self.PAD, self.draw_w, self.draw_h
        return [("l", P, P + h / 2.0, False), ("r", P + w, P + h / 2.0, False),
                ("t", P + w / 2.0, P, True), ("b", P + w / 2.0, P + h, True)]

    def _hit_crop_edge(self, lx, ly):
        for side, hx, hy, horiz in self._crop_handles():
            along, across = (abs(lx - hx), abs(ly - hy)) if horiz else (abs(ly - hy), abs(lx - hx))
            if along <= 14 and across <= 7:
                return side
        return None

    @staticmethod
    def _scaled_shape(sh, fx, fy):
        out = dict(sh)
        for k in ("x1", "x2", "x3"):
            if k in out:
                out[k] = sh[k] * fx
        for k in ("y1", "y2", "y3"):
            if k in out:
                out[k] = sh[k] * fy
        return out

    def _clamp(self, ax, ay):
        return max(0.0, min(float(self.draw_w), ax)), max(0.0, min(float(self.draw_h), ay))

    def _set_cursor_by_name(self, name):
        win = self.get_window()
        if win is None:
            return
        try:
            win.set_cursor(Gdk.Cursor.new_from_name(win.get_display(), name) if name else None)
        except Exception:
            win.set_cursor(None)

    # ---- drawing -------------------------------------------------------------

    def _draw_shape(self, cr, s, theme, pango_ctx):
        rgb = self._color_rgb(s.get("color", "auto"), theme)
        lw = float(s.get("width", 1.6))
        t = s["type"]
        cr.new_path()  # never carry a current point over from the previous shape
        cr.save()
        cr.set_line_width(lw)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        if t in ("rect", "ellipse"):
            x0, y0, x1, y1 = self._bbox(s)
            w, h = max(1.0, x1 - x0), max(1.0, y1 - y0)
            if t == "rect":
                cr.rectangle(x0, y0, w, h)
            else:
                cr.save()
                cr.translate(x0 + w / 2.0, y0 + h / 2.0)
                cr.scale(w / 2.0, h / 2.0)
                cr.new_sub_path()
                cr.arc(0, 0, 1.0, 0, 2 * math.pi)
                cr.restore()
            self._apply_fill(cr, s, rgb)
            self._stroke_outline(cr, s, rgb)
        elif t == "triangle":
            for i, (px, py) in enumerate(self._triangle_pts(s)):
                (cr.move_to if i == 0 else cr.line_to)(px, py)
            cr.close_path()
            self._apply_fill(cr, s, rgb)
            self._stroke_outline(cr, s, rgb)
        elif t == "arc":
            for i, (px, py) in enumerate(self._arc_pts(s)):
                (cr.move_to if i == 0 else cr.line_to)(px, py)
            cr.set_source_rgb(*rgb)
            cr.stroke()
        elif t in DRAW_LINE_TYPES:
            x1, y1, x2, y2 = s["x1"], s["y1"], s["x2"], s["y2"]
            cr.set_source_rgb(*rgb)
            if t in ("arrow", "arrow2") and (x1, y1) != (x2, y2):
                filled = s.get("head", "filled") != "open"
                ang = math.atan2(y2 - y1, x2 - x1)
                head = 7.0 + 2.2 * lw
                L = math.hypot(x2 - x1, y2 - y1)
                both = t == "arrow2"
                head = min(head, L / (2.2 if both else 1.1))
                # stop the shaft at the arrow head(s) so the tips stay sharp
                # open (">") heads: the shaft runs all the way to the tip
                cut = head * 0.8 if filled else 0.0
                ex, ey = math.cos(ang), math.sin(ang)
                sx1, sy1 = (x1 + ex * cut, y1 + ey * cut) if both else (x1, y1)
                sx2, sy2 = x2 - ex * cut, y2 - ey * cut
                cr.move_to(sx1, sy1)
                cr.line_to(sx2, sy2)
                cr.stroke()
                tips = [(x2, y2, ang)] + ([(x1, y1, ang + math.pi)] if both else [])
                for tx, ty, a in tips:
                    if filled:
                        cr.move_to(tx, ty)
                        cr.line_to(tx - head * math.cos(a - 0.42), ty - head * math.sin(a - 0.42))
                        cr.line_to(tx - head * math.cos(a + 0.42), ty - head * math.sin(a + 0.42))
                        cr.close_path()
                        cr.fill()
                    else:
                        # open head: two strokes meeting at the tip, like ">"
                        cr.move_to(tx - head * math.cos(a - 0.5), ty - head * math.sin(a - 0.5))
                        cr.line_to(tx, ty)
                        cr.line_to(tx - head * math.cos(a + 0.5), ty - head * math.sin(a + 0.5))
                        cr.stroke()
            else:
                cr.move_to(x1, y1)
                cr.line_to(x2, y2)
                cr.stroke()
        elif t == "text":
            lay = self._text_layout(s, pango_ctx)
            cr.set_source_rgb(*rgb)
            cr.move_to(s["x1"], s["y1"])
            PangoCairo.show_layout(cr, lay)
            cr.new_path()  # show_layout leaves the current point at the text
        elif t in DRAW_ELEC_TYPES:
            cr.set_source_rgb(*rgb)
            for kind, data in self._elec_geometry(s):
                if kind == "circle":
                    cx, cy, rr = data
                    cr.new_sub_path()
                    cr.arc(cx, cy, max(1.5, rr), 0, 2 * math.pi)
                else:
                    for i, (px, py) in enumerate(data):
                        (cr.move_to if i == 0 else cr.line_to)(px, py)
                    if kind == "fpoly":
                        cr.close_path()
                        cr.fill_preserve()
                cr.stroke()
        elif t == "image":
            self._draw_image_shape(cr, s)
        cr.restore()

    def _image_pixbuf(self, s):
        """Decoded picture of an image shape (cached by its data)."""
        data = s.get("png", "")
        cache = self.__dict__.setdefault("_img_cache", {})
        pb = cache.get(data)
        if pb is None and data:
            try:
                loader = GdkPixbuf.PixbufLoader.new_with_type("png")
                loader.write(base64.b64decode(data))
                loader.close()
                pb = loader.get_pixbuf()
            except Exception:
                pb = None
            if pb is not None:
                if len(cache) > 32:
                    cache.clear()
                cache[data] = pb
        return pb

    def _draw_image_shape(self, cr, s):
        x0, y0, x1, y1 = self._bbox(s)
        bw, bh = x1 - x0, y1 - y0
        pb = self._image_pixbuf(s)
        if pb is None or bw < 1 or bh < 1:
            cr.set_source_rgb(0.6, 0.6, 0.6)
            cr.set_line_width(1.0)
            cr.rectangle(x0, y0, max(bw, 1), max(bh, 1))
            cr.stroke()
            return
        rot = int(s.get("rot", 0)) % 360
        iw, ih = pb.get_width(), pb.get_height()
        cr.translate((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        cr.rotate(math.radians(rot))
        sw, sh = (bh, bw) if rot in (90, 270) else (bw, bh)
        cr.scale(sw / iw, sh / ih)
        cr.translate(-iw / 2.0, -ih / 2.0)
        Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
        try:
            cr.get_source().set_filter(cairo.FILTER_GOOD)
        except Exception:
            pass
        cr.rectangle(0, 0, iw, ih)
        cr.fill()

    def _image_aspect(self, s):
        iw, ih = float(s.get("iw", 0) or 0), float(s.get("ih", 0) or 0)
        if iw <= 0 or ih <= 0:
            pb = self._image_pixbuf(s)
            if pb is None:
                return None
            iw, ih = float(pb.get_width()), float(pb.get_height())
        if int(s.get("rot", 0)) % 180 == 90:
            iw, ih = ih, iw
        return iw / ih

    def add_picture(self, pixbuf) -> bool:
        """Put a picture into the drawing, as a shape that can be moved, resized and rotated."""
        if pixbuf is None:
            return False
        w, h = pixbuf.get_width(), pixbuf.get_height()
        if max(w, h) > DRAW_IMAGE_MAX_PX:
            f = DRAW_IMAGE_MAX_PX / float(max(w, h))
            w, h = max(1, int(round(w * f))), max(1, int(round(h * f)))
            pixbuf = pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
        ok, buf = pixbuf.save_to_bufferv("png", [], [])
        if not ok:
            return False
        # fit inside 70 % of the drawing, never enlarged
        f = min(1.0, 0.7 * self.draw_w / w, 0.7 * self.draw_h / h)
        dw, dh = w * f, h * f
        x0, y0 = (self.draw_w - dw) / 2.0, (self.draw_h - dh) / 2.0
        s = {"type": "image", "x1": x0, "y1": y0, "x2": x0 + dw, "y2": y0 + dh,
             "png": base64.b64encode(buf).decode("ascii"), "iw": w, "ih": h, "rot": 0}
        self.shapes.append(s)
        self._set_selection([len(self.shapes) - 1])
        self.tool = "select"
        if not self.editing:
            self.start_editing()
        self.update_layout()
        return True

    def paste_picture(self) -> bool:
        return self.add_picture(self.canvas._try_load_pixbuf_from_clipboard())

    def insert_picture_from_file(self) -> bool:
        return self.add_picture(self.canvas.choose_picture_file())

    @staticmethod
    def _clipboard_holds_our_shapes():
        try:
            txt = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).wait_for_text()
        except Exception:
            return False
        return txt == _DRAW_SHAPES_CLIP_MARK

    def draw_content(self, cr, theme=None, for_export=False):
        if theme is None:
            theme = THEMES[self.canvas.theme_name]
        pango_ctx = self.get_pango_context()
        P = self.PAD
        show_frame = not for_export and (self.selected or self.editing or not self.shapes)

        # Drawing area
        if self.background:
            cr.save()
            cr.set_source_rgb(*self._drawing_bg_rgb(theme))
            cr.rectangle(P, P, self.draw_w, self.draw_h)
            cr.fill()
            cr.restore()
        if self.editing and not for_export:
            cr.save()
            cr.set_source_rgba(*theme["box_editing_bg"])
            cr.rectangle(P, P, self.draw_w, self.draw_h)
            cr.fill()
            cr.restore()
        if show_frame:
            cr.save()
            cr.set_source_rgb(*(theme["box_editing_border"] if self.editing else theme["placeholder_border"]))
            cr.set_line_width(1.0)
            cr.set_dash([3.0, 3.0])
            cr.rectangle(P + 0.5, P + 0.5, self.draw_w - 1, self.draw_h - 1)
            cr.stroke()
            cr.restore()
        if not self.shapes and not for_export:
            hint = "Double-click to draw" if not self.editing else "Pick a line or shape below, then drag here"
            lay, lw, la, ld = MathRenderer._make_layout(pango_ctx, hint, 0.7)
            cr.save()
            cr.set_source_rgb(*theme["muted_text"])
            cr.move_to(P + (self.draw_w - lw) / 2.0, P + (self.draw_h - la - ld) / 2.0)
            PangoCairo.show_layout(cr, lay)
            cr.restore()

        cr.save()
        cr.translate(P, P)
        cr.rectangle(0, 0, self.draw_w, self.draw_h)
        cr.clip()
        for s in self.shapes:
            self._draw_shape(cr, s, theme, pango_ctx)
        # selection grips
        sel_idx = self._selected_indices() if (self.editing and not for_export) else []
        if sel_idx:
            cr.set_source_rgb(*theme["box_selected_border"])
            cr.set_line_width(1.0)
            cr.set_dash([3.0, 2.0])
            for i in sel_idx:
                x0, y0, x1, y1 = self._bbox(self.shapes[i])
                cr.rectangle(x0 - 3, y0 - 3, (x1 - x0) + 6, (y1 - y0) + 6)
                cr.stroke()
            cr.set_dash([])
        band = self.op if (self.editing and not for_export and self.op and self.op.get("kind") == "band") else None
        if band is not None:
            bx0, by0 = min(band["sx"], band["ex"]), min(band["sy"], band["ey"])
            bw, bh = abs(band["ex"] - band["sx"]), abs(band["ey"] - band["sy"])
            sc = theme["box_selected_border"]
            cr.set_source_rgba(sc[0], sc[1], sc[2], 0.12)
            cr.rectangle(bx0, by0, bw, bh)
            cr.fill()
            cr.set_source_rgb(*sc)
            cr.set_line_width(1.0)
            cr.set_dash([4.0, 3.0])
            cr.rectangle(bx0, by0, bw, bh)
            cr.stroke()
            cr.set_dash([])
        if len(sel_idx) == 1:
            s = self.shapes[sel_idx[0]]
            hs = self.HANDLE
            for _name, hx, hy in self._handles(s):
                cr.set_source_rgb(*theme["canvas_bg"])
                cr.rectangle(hx - hs / 2, hy - hs / 2, hs, hs)
                cr.fill()
                cr.set_source_rgb(*theme["box_editing_border"])
                cr.rectangle(hx - hs / 2, hy - hs / 2, hs, hs)
                cr.stroke()
        cr.restore()

        # Tool strip (editing only, never exported)
        y_cap = P + self.draw_h + 4
        if self.editing and not for_export:
            self._layout_strip()
            for key, lbl, (bx, by, bw, bh) in self._strip_buttons:
                active = (
                    key == "tool:" + self.tool
                    or (key == "dd:line" and self.tool in dict(DRAW_LINE_TOOLS))
                    or (key == "dd:shape" and (self.tool in dict(DRAW_SHAPE_TOOLS) or self.tool in DRAW_ELEC_TYPES))
                    or (key == "background" and self.background)
                )
                cr.save()
                cr.set_source_rgb(*(theme["box_selected_border"] if active else theme["canvas_bg"]))
                cr.rectangle(bx, by, bw, bh)
                cr.fill()
                cr.set_source_rgb(*theme["box_editing_border"])
                cr.set_line_width(1.0)
                cr.rectangle(bx + 0.5, by + 0.5, bw - 1, bh - 1)
                cr.stroke()
                lay, lw, la, ld = MathRenderer._make_layout(pango_ctx, lbl, 0.62, bold=True)
                cr.set_source_rgb(*(theme["canvas_bg"] if active else theme["text"]))
                cr.move_to(bx + 6, by + (bh - la - ld) / 2.0)
                PangoCairo.show_layout(cr, lay)
                if key == "dd:color" and self.cur_color == "none":
                    cr.set_source_rgb(*theme["canvas_bg"])
                    cr.rectangle(bx + 6, by + 5, 16, bh - 10)
                    cr.fill()
                    cr.set_source_rgb(0.8, 0.2, 0.2)  # no outline: a diagonal slash
                    cr.set_line_width(1.2)
                    cr.move_to(bx + 7, by + bh - 6)
                    cr.line_to(bx + 21, by + 6)
                    cr.stroke()
                elif key == "dd:color":
                    # swatch of the current colour inside the Colour combo
                    cr.set_source_rgb(*self._color_rgb(self.cur_color, theme))
                    cr.rectangle(bx + 6, by + 5, 16, bh - 10)
                    cr.fill()
                    cr.set_source_rgb(*theme["box_editing_border"])
                    cr.set_line_width(0.8)
                    cr.rectangle(bx + 6, by + 5, 16, bh - 10)
                    cr.stroke()
                if key == "dd:fill":
                    frgb = self._fill_rgb(self.cur_fill, self._color_rgb(self.cur_color, theme))
                    cr.set_source_rgb(*theme["canvas_bg"])
                    cr.rectangle(bx + 6, by + 5, 16, bh - 10)
                    cr.fill()
                    if frgb is not None:
                        cr.set_source_rgba(frgb[0], frgb[1], frgb[2], 0.3 if self.cur_fill_light else 1.0)
                        cr.rectangle(bx + 6, by + 5, 16, bh - 10)
                        cr.fill()
                    else:  # no fill: a diagonal slash
                        cr.set_source_rgb(0.8, 0.2, 0.2)
                        cr.set_line_width(1.2)
                        cr.move_to(bx + 7, by + bh - 6)
                        cr.line_to(bx + 21, by + 6)
                        cr.stroke()
                    cr.set_source_rgb(*theme["box_editing_border"])
                    cr.set_line_width(0.8)
                    cr.rectangle(bx + 6, by + 5, 16, bh - 10)
                    cr.stroke()
                cr.restore()
            y_cap += self.strip_h

        # Caption
        t_layout, wrap_w, _ = self._make_caption_layout(pango_ctx)
        if t_layout is not None:
            cr.save()
            cr.set_source_rgb(*theme["heading_text"])
            cr.move_to(P + (self.draw_w - wrap_w) / 2.0, y_cap)
            PangoCairo.show_layout(cr, t_layout)
            cr.restore()

        if for_export:
            return
        if self.selected and not self.editing:
            cr.save()
            cr.set_source_rgb(*theme["box_selected_border"])
            cr.set_line_width(1.4)
            cr.set_dash([4.0, 3.0])
            cr.rectangle(0.7, 0.7, self.logical_w - 1.4, self.logical_h - 1.4)
            cr.stroke()
            cr.set_dash([])
            hs = 8.0
            gx, gy = P + self.draw_w - hs / 2, P + self.draw_h - hs / 2
            cr.set_source_rgb(*theme["canvas_bg"])
            cr.rectangle(gx, gy, hs, hs)
            cr.fill()
            cr.set_source_rgb(*theme["box_editing_border"])
            cr.rectangle(gx, gy, hs, hs)
            cr.stroke()
            # crop handles: dark bars at the middle of each edge
            for _side, hx, hy, horiz in self._crop_handles():
                bw_, bh_ = (18.0, 5.0) if horiz else (5.0, 18.0)
                cr.set_source_rgb(*theme["text"])
                cr.rectangle(hx - bw_ / 2, hy - bh_ / 2, bw_, bh_)
                cr.fill()
            cr.restore()
            draw_figure_caption_button(self, cr, theme)

    def on_draw(self, widget, cr):
        z = getattr(self.canvas, "zoom", 1.0)
        cr.save()
        cr.scale(z, z)
        self.draw_content(cr, for_export=False)
        cr.restore()
        return True

    # ---- strip actions -------------------------------------------------------

    def _apply_to_selected(self, **props):
        for i in self._selected_indices():
            sh = self.shapes[i]
            upd = dict(props)
            if sh["type"] not in DRAW_FILLABLE:
                upd.pop("fill", None)
                upd.pop("fill_light", None)
            if "head" in upd and sh["type"] not in ("arrow", "arrow2"):
                upd.pop("head")
            sh.update(upd)

    @staticmethod
    def _fill_rgb(fill, outline_rgb):
        f = draw_fill_key(fill)
        if f is False:
            return None
        return outline_rgb if f == "outline" else dict(DRAW_FILL_COLORS)[f]

    @staticmethod
    def _stroke_outline(cr, s, rgb):
        """Stroke a rectangle / ellipse / triangle outline, unless it is set to No Outline."""
        if s.get("color") == "none":
            cr.new_path()
            return
        cr.set_source_rgb(*rgb)
        cr.stroke()

    def _apply_fill(self, cr, s, rgb):
        frgb = self._fill_rgb(s.get("fill"), rgb)
        if frgb is None:
            return
        cr.set_source_rgba(frgb[0], frgb[1], frgb[2], 0.22 if draw_fill_light(s) else 1.0)
        cr.fill_preserve()

    def _drawing_bg_rgb(self, theme):
        """White behind the drawing in the light theme, black in the dark one."""
        tr, tg, tb = theme["text"][:3]
        return (0.0, 0.0, 0.0) if (tr + tg + tb) / 3.0 > 0.5 else (1.0, 1.0, 1.0)

    def _popup_dropdown(self, key, rect):
        """Combo-box style list under a strip button."""
        menu = Gtk.Menu()

        def add(label, action_key, active, markup=False, radio=True):
            # check items drawn as radios: the current choice is marked, and picking any
            # entry (even the marked one) applies it
            mi = Gtk.CheckMenuItem(label=label)
            mi.set_draw_as_radio(radio)
            if markup:
                mi.get_child().set_markup(label)
            mi.set_active(active)
            mi.connect("activate", lambda _w, k=action_key: self._strip_click(k))
            menu.append(mi)

        if key == "dd:line":
            line_tool = self.tool if self.tool in dict(DRAW_LINE_TOOLS) else None
            for k, lbl in DRAW_LINE_TOOLS:
                add(lbl, "tool:" + k, k == line_tool)
            menu.append(Gtk.SeparatorMenuItem())  # arrow heads are a separate choice
            for k, lbl in DRAW_HEADS:
                add(lbl, "head:" + k, k == self.cur_head)
        elif key == "dd:shape":
            shape_tool = self.tool if self.tool in dict(DRAW_SHAPE_TOOLS) else None
            for k, lbl in DRAW_SHAPE_TOOLS:
                add(lbl, "tool:" + k, k == shape_tool)
            menu.append(Gtk.SeparatorMenuItem())
            sel = self.shapes[self.sel_shape] if self.sel_shape is not None and self.sel_shape < len(self.shapes) else None
            hdr = Gtk.MenuItem(label="Electrical")
            hdr.set_sensitive(False)
            menu.append(hdr)
            for k, lbl in DRAW_ELEC_TOOLS:
                add(lbl, "tool:" + k, k == self.tool)
            menu.append(Gtk.SeparatorMenuItem())
            hdr = Gtk.MenuItem(label="Picture")
            hdr.set_sensitive(False)
            menu.append(hdr)
            for lbl, cb in (("🖼 Paste Picture  (Ctrl+V)", self.paste_picture),
                            ("🖼 Picture from File…", self.insert_picture_from_file)):
                mi = Gtk.MenuItem(label=lbl)
                mi.connect("activate", lambda _w, f=cb: GLib.idle_add(lambda: (f(), False)[1]))
                menu.append(mi)
            menu.append(Gtk.SeparatorMenuItem())
            mi = Gtk.MenuItem(label="Rotate Selected Shape 90°  (R)")
            mi.set_sensitive(sel is not None and sel["type"] not in ("text",))
            mi.connect("activate", lambda _w: self._rotate_selected(90))
            menu.append(mi)
        elif key == "dd:color":
            theme = THEMES[self.canvas.theme_name]
            add("No Outline  (rectangle, ellipse, triangle)", "color:none", self.cur_color == "none")
            for k, _rgb in DRAW_COLORS:
                r, g, b = self._color_rgb(k, theme)
                hexc = "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
                add(f'<span foreground="{hexc}" size="large">■</span>  {DRAW_COLOR_LABELS.get(k, k)}',
                    "color:" + k, k == self.cur_color, markup=True)
        elif key == "dd:fill":
            theme = THEMES[self.canvas.theme_name]
            sel = self.shapes[self.sel_shape] if self._has_sel_shape() else None
            if sel is not None and sel["type"] in DRAW_FILLABLE:
                cur_f, cur_l = draw_fill_key(sel.get("fill")), draw_fill_light(sel)
            else:
                cur_f, cur_l = draw_fill_key(self.cur_fill), self.cur_fill_light
            hdr = Gtk.MenuItem(label="Fill  (rectangle, ellipse, triangle)")
            hdr.set_sensitive(False)
            menu.append(hdr)
            add("No Fill", "fill:none", cur_f is False)
            orgb = self._color_rgb(self.cur_color, theme)
            for k in ["outline"] + [c for c, _rgb in DRAW_FILL_COLORS]:
                r, g, b = orgb if k == "outline" else dict(DRAW_FILL_COLORS)[k]
                hexc = "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
                # outline the white swatch so it shows on a white menu
                sw = '<span foreground="#888888" size="large">□</span>' if k == "white" else \
                    f'<span foreground="{hexc}" size="large">■</span>'
                add(f"{sw}  {DRAW_FILL_LABELS[k]}", "fill:" + k, cur_f == k, markup=True)
            menu.append(Gtk.SeparatorMenuItem())
            add("Light  (see-through tint)", "fill_light", cur_l, radio=False)
        elif key == "dd:width":
            cur = draw_width_key(self.cur_width)
            for k, lbl, _w in DRAW_WIDTHS:
                add(lbl, "width:" + k, k == cur)
        menu.show_all()
        z = getattr(self.canvas, "zoom", 1.0)
        bx, by, bw, bh = rect
        r = Gdk.Rectangle()
        r.x, r.y, r.width, r.height = int(bx * z), int(by * z), int(bw * z), int(bh * z)
        menu.popup_at_rect(self.get_window(), r, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)

    def _strip_click(self, key):
        if key.startswith("tool:"):
            self.tool = key[5:]
            if self.tool != "select":
                self.cur_shape = self.tool
                self.sel_shape = None
        elif key.startswith("color:"):
            self.cur_color = key[6:]
            self._apply_to_selected(color=self.cur_color)
        elif key.startswith("fill:"):
            v = key[5:]
            self.cur_fill = False if v == "none" else v
            if v == "none":
                self.cur_fill_light = False
            self._apply_to_selected(fill=self.cur_fill, fill_light=self.cur_fill_light)
        elif key == "fill_light":
            sel = self.shapes[self.sel_shape] if self._has_sel_shape() else None
            base = draw_fill_light(sel) if sel is not None and sel["type"] in DRAW_FILLABLE else self.cur_fill_light
            self.cur_fill_light = not base
            if self.cur_fill is False:
                self.cur_fill = "outline"  # Light with no fill: a light tint of the outline colour
            for i in self._selected_indices():
                sh = self.shapes[i]
                if sh["type"] in DRAW_FILLABLE:
                    if not draw_fill_key(sh.get("fill")):
                        sh["fill"] = "outline"
                    elif sh.get("fill") is True:
                        sh["fill"] = "outline"
                    sh["fill_light"] = self.cur_fill_light
        elif key.startswith("width:"):
            self.cur_width = next(w for k, _l, w in DRAW_WIDTHS if k == key[6:])
            self._apply_to_selected(width=self.cur_width)
        elif key.startswith("head:"):
            self.cur_head = key[5:]
            self._apply_to_selected(head=self.cur_head)
        elif key == "background":
            self.background = not self.background
        elif key == "delete":
            self._delete_selected_shape()
        elif key == "done":
            self.stop_editing()
            return
        self.update_layout()

    # ---- copy / paste of shapes ----------------------------------------------

    def _has_sel_shape(self):
        return self.sel_shape is not None and self.sel_shape < len(self.shapes)

    def copy_shape(self) -> bool:
        sel = self._selected_indices()
        if not sel:
            return False
        import copy as _copy
        _DRAW_CLIPBOARD["shapes"] = [_copy.deepcopy(self.shapes[i]) for i in sel]
        _DRAW_CLIPBOARD["pastes"] = 0
        try:  # so a picture copied elsewhere afterwards wins on Ctrl+V
            Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(_DRAW_SHAPES_CLIP_MARK, -1)
        except Exception:
            pass
        return True

    def cut_shape(self) -> bool:
        if not self.copy_shape():
            return False
        self._delete_selected_shape()
        _DRAW_CLIPBOARD["pastes"] = -1  # paste the cut shape back in place first
        return True

    def paste_shapes(self) -> bool:
        if not _DRAW_CLIPBOARD["shapes"]:
            return False
        import copy as _copy
        _DRAW_CLIPBOARD["pastes"] += 1
        off = 12.0 * max(0, _DRAW_CLIPBOARD["pastes"])
        group = [_copy.deepcopy(src) for src in _DRAW_CLIPBOARD["shapes"]]
        xs = [sh[k] for sh in group for k in ("x1", "x2", "x3") if k in sh]
        ys = [sh[k] for sh in group for k in ("y1", "y2", "y3") if k in sh]
        # shift by the offset, but keep the whole group inside this drawing
        dx = max(-min(xs), min(off, self.draw_w - max(xs)))
        dy = max(-min(ys), min(off, self.draw_h - max(ys)))
        first = len(self.shapes)
        for sh in group:
            self._shift_shape(sh, dx, dy)
            self.shapes.append(sh)
        self._set_selection(range(first, len(self.shapes)))
        self.tool = "select"
        self.update_layout()
        return True

    def duplicate_shape(self) -> bool:
        if not self.copy_shape():
            return False
        return self.paste_shapes()

    def handle_clipboard_key(self, keyname) -> bool:
        k = keyname.lower()
        if k == "c":
            return self.copy_shape() or True
        if k == "x":
            return self.cut_shape() or True
        if k == "v":
            # a picture copied after the last shape copy is pasted as a picture
            if not (_DRAW_CLIPBOARD["shapes"] and self._clipboard_holds_our_shapes()):
                if self.paste_picture():
                    return True
            return self.paste_shapes() or True
        if k == "d":
            return self.duplicate_shape() or True
        if k == "a":
            self.tool = "select"
            self._set_selection(range(len(self.shapes)))
            self.update_layout()
            return True
        return False

    def _rotate_selected(self, deg=90):
        """Rotate the selected shape about its centre (Shift+R / menu: other direction)."""
        sel = self._selected_indices()
        if not sel:
            return
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)
        if len(sel) == 1:
            s = self.shapes[sel[0]]
            if s["type"] == "text":
                return
            keys = [k for k in ("1", "2", "3") if "x" + k in s]
            if s["type"] in ("rect", "ellipse"):
                x0, y0, x1, y1 = self._bbox(s)
                cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            else:
                cx = sum(s["x" + k] for k in keys) / len(keys)
                cy = sum(s["y" + k] for k in keys) / len(keys)
        else:  # a group turns about the centre of its bounding box
            boxes = [self._bbox(self.shapes[i]) for i in sel]
            cx = (min(b[0] for b in boxes) + max(b[2] for b in boxes)) / 2.0
            cy = (min(b[1] for b in boxes) + max(b[3] for b in boxes)) / 2.0
        for i in sel:
            s = self.shapes[i]
            if s["type"] == "text":  # text stays upright; its position turns with the group
                x0, y0, x1, y1 = self._bbox(s)
                mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
                dx, dy = mx - cx, my - cy
                nx, ny = cx + dx * ca - dy * sa, cy + dx * sa + dy * ca
                self._shift_shape(s, nx - mx, ny - my)
                continue
            for k in ("1", "2", "3"):
                if "x" + k in s:
                    dx, dy = s["x" + k] - cx, s["y" + k] - cy
                    s["x" + k], s["y" + k] = cx + dx * ca - dy * sa, cy + dx * sa + dy * ca
            if s["type"] == "image":
                s["rot"] = int(round(s.get("rot", 0) + deg)) % 360
                if len(sel) == 1:  # keep a turned picture inside the drawing
                    x0, y0, x1, y1 = self._bbox(s)
                    dx = max(-x0, min(0.0, self.draw_w - x1)) if x1 - x0 <= self.draw_w else -x0
                    dy = max(-y0, min(0.0, self.draw_h - y1)) if y1 - y0 <= self.draw_h else -y0
                    self._shift_shape(s, dx, dy)
        self.queue_draw()

    def _delete_selected_shape(self):
        for i in sorted(self._selected_indices(), reverse=True):
            del self.shapes[i]
        self.sel_shape = None
        self.queue_draw()

    def _ask_text(self, initial=""):
        toplevel = self.get_toplevel()
        dlg = Gtk.Dialog(
            title="Drawing Text",
            transient_for=toplevel if isinstance(toplevel, Gtk.Window) else None,
            flags=0,
        )
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        dlg.set_default_size(320, -1)
        area = dlg.get_content_area()
        for side in ("start", "end", "top", "bottom"):
            getattr(area, f"set_margin_{side}")(12)
        entry = Gtk.Entry(text=initial)
        entry.set_activates_default(True)
        area.pack_start(entry, False, False, 0)
        dlg.show_all()
        entry.grab_focus()
        txt = entry.get_text() if dlg.run() == Gtk.ResponseType.OK else None
        if txt is not None:
            txt = entry.get_text()
        dlg.destroy()
        return txt

    # ---- mouse ---------------------------------------------------------------

    def on_button_press(self, widget, event):
        z = getattr(self.canvas, "zoom", 1.0)
        lx, ly = event.x / z, event.y / z
        if event.button == 3:
            if self not in self.canvas.selected_boxes:
                self.canvas.select_box(self)
            self._show_context_menu(event)
            return True
        if event.button != 1:
            return False

        if not self.editing:
            was_selected = self.selected
            self.canvas.handle_box_button_press(self, event)
            self.canvas.focus_without_scroll(self)
            if was_selected and hit_figure_caption_button(self, lx, ly):
                self.dragging = False
                GLib.idle_add(lambda: open_figure_caption_dialog(self) and False)
                return True
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.dragging = False
                self.resizing = False
                self.start_editing()
                return True
            if was_selected and self._hit_box_resize(lx, ly):
                # corner: resize (scales the shapes with the drawing)
                self.resizing = True
                self.drag_start_root_x, self.drag_start_root_y = event.x_root, event.y_root
                self.resize_start_w, self.resize_start_h = self.draw_w, self.draw_h
                self._resize_orig_shapes = [dict(sh) for sh in self.shapes]
                return True
            crop_side = self._hit_crop_edge(lx, ly) if was_selected else None
            if crop_side:
                # edge: crop (changes the visible area, shapes keep their size)
                self.cropping = crop_side
                self.drag_start_root_x, self.drag_start_root_y = event.x_root, event.y_root
                self.resize_start_w, self.resize_start_h = self.draw_w, self.draw_h
                self._crop_start_xy = (self.x, self.y)
                self._resize_orig_shapes = [dict(sh) for sh in self.shapes]
                return True
            self.dragging = True
            self.drag_start_root_x, self.drag_start_root_y = event.x_root, event.y_root
            self.drag_start_box_x, self.drag_start_box_y = self.x, self.y
            return True

        # ---- editing mode ----
        self.canvas.focus_without_scroll(self)
        for key, _lbl, (bx, by, bw, bh) in self._strip_buttons:
            if bx <= lx <= bx + bw and by <= ly <= by + bh:
                if event.type == Gdk.EventType.BUTTON_PRESS:
                    if key.startswith("dd:"):
                        self._popup_dropdown(key, (bx, by, bw, bh))
                    else:
                        self._strip_click(key)
                return True
        ax, ay = lx - self.PAD, ly - self.PAD
        if not (0 <= ax <= self.draw_w and 0 <= ay <= self.draw_h):
            return True
        if self.tool == "select":
            handle = self._hit_handle(ax, ay)
            if handle is not None:
                self.op = {"kind": "handle", "name": handle}
                return True
            idx = self._hit_shape(ax, ay)
            additive = bool(event.state & (Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.CONTROL_MASK))
            cur = self._selected_indices()
            if additive:
                if idx is None:  # Shift-drag on empty space: add a rectangle of shapes
                    self.op = {"kind": "band", "sx": ax, "sy": ay, "ex": ax, "ey": ay, "base": cur}
                else:  # Shift/Ctrl-click toggles a shape in the selection
                    self._set_selection([i for i in cur if i != idx] if idx in cur else cur + [idx])
                    self.op = None
                self.update_layout()
                return True
            if idx is not None and idx in cur and len(cur) > 1:
                # drag one of several selected shapes: move them all
                self.op = {"kind": "move", "ax": ax, "ay": ay,
                           "origs": {i: dict(self.shapes[i]) for i in cur}}
                self.queue_draw()
                return True
            if idx is None:  # drag on empty space: rubber-band selection
                self.sel_shape = None
                self.op = {"kind": "band", "sx": ax, "sy": ay, "ex": ax, "ey": ay, "base": []}
                self.update_layout()
                return True
            self.sel_shape = idx
            if idx is not None:
                s = self.shapes[idx]
                self.cur_color = s.get("color", "auto")
                if s["type"] in DRAW_FILLABLE:
                    self.cur_fill = draw_fill_key(s.get("fill", False))
                    self.cur_fill_light = draw_fill_light(s)
                self.cur_width = float(s.get("width", 1.6))
                if s["type"] in ("arrow", "arrow2"):
                    self.cur_head = s.get("head", "filled")
                if event.type == Gdk.EventType._2BUTTON_PRESS and s["type"] == "text":
                    self.op = None
                    GLib.idle_add(self._edit_text_idle, idx)
                    return True
                self.op = {"kind": "move", "ax": ax, "ay": ay, "origs": {idx: dict(s)}}
            else:
                self.op = None
            self.update_layout()
            return True
        if self.tool == "text":
            GLib.idle_add(self._create_text_idle, ax, ay)
            return True
        shape = {
            "type": self.tool, "x1": ax, "y1": ay, "x2": ax, "y2": ay,
            "color": self.cur_color, "fill": self.cur_fill if self.tool in DRAW_FILLABLE else False,
            "fill_light": self.cur_fill_light if self.tool in DRAW_FILLABLE else False,
            "width": self.cur_width,
        }
        if self.tool in ("arrow", "arrow2"):
            shape["head"] = self.cur_head
        if self.tool == "triangle":
            self._triangle_from_drag(shape, ax, ay, ax, ay)
        if self.tool == "arc":
            shape["angle"] = 90.0
        self.shapes.append(shape)
        self.sel_shape = len(self.shapes) - 1
        self.op = {"kind": "create", "sx": ax, "sy": ay}
        self.queue_draw()
        return True

    def _create_text_idle(self, ax, ay):
        txt = self._ask_text("")
        if txt and txt.strip():
            self.shapes.append({
                "type": "text", "x1": ax, "y1": ay, "x2": ax, "y2": ay,
                "color": self.cur_color, "fill": False, "width": self.cur_width, "text": txt,
            })
            self.sel_shape = len(self.shapes) - 1
        self.tool = "select"
        self.update_layout()
        self.canvas.focus_without_scroll(self)
        return False

    def _edit_text_idle(self, idx):
        if idx < len(self.shapes):
            txt = self._ask_text(self.shapes[idx].get("text", ""))
            if txt is not None:
                if txt.strip():
                    self.shapes[idx]["text"] = txt
                else:
                    del self.shapes[idx]
                    self.sel_shape = None
        self.update_layout()
        self.canvas.focus_without_scroll(self)
        return False

    def on_motion_notify(self, widget, event):
        z = getattr(self.canvas, "zoom", 1.0)
        lx, ly = event.x / z, event.y / z
        held = bool(event.state & Gdk.ModifierType.BUTTON1_MASK)
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)

        if self.resizing:
            if not held:
                self.resizing = False
                return False
            dx = (event.x_root - self.drag_start_root_x) / z
            dy = (event.y_root - self.drag_start_root_y) / z
            w0, h0 = float(self.resize_start_w), float(self.resize_start_h)
            max_w = self.canvas.A4_WIDTH - self.x - 2 * self.PAD
            nw = max(60.0, min(max_w, w0 + dx))
            nh = max(40.0, min(1000.0, h0 + dy))
            if not shift:  # keep proportions (Shift: free)
                f = nw / w0 if abs(nw / w0 - 1.0) >= abs(nh / h0 - 1.0) else nh / h0
                f = max(f, 60.0 / w0, 40.0 / h0)
                f = min(f, max_w / w0, 1000.0 / h0)
                nw, nh = w0 * f, h0 * f
            self.draw_w, self.draw_h = int(round(nw)), int(round(nh))
            fx, fy = self.draw_w / w0, self.draw_h / h0
            orig = getattr(self, "_resize_orig_shapes", None) or []
            if len(orig) == len(self.shapes):
                self.shapes = [self._scaled_shape(sh, fx, fy) for sh in orig]
            self.update_layout()
            return True
        if getattr(self, "cropping", None):
            if not held:
                self.cropping = None
                return False
            dx = (event.x_root - self.drag_start_root_x) / z
            dy = (event.y_root - self.drag_start_root_y) / z
            w0, h0 = self.resize_start_w, self.resize_start_h
            x0, y0 = self._crop_start_xy
            side = self.cropping
            sx = sy = 0  # shift of the shapes inside the drawing
            nx, ny = x0, y0
            if side == "r":
                self.draw_w = int(max(60, min(self.canvas.A4_WIDTH - self.x - 2 * self.PAD, w0 + dx)))
            elif side == "b":
                self.draw_h = int(max(40, min(1000, h0 + dy)))
            elif side == "l":
                d = int(round(max(-x0, min(w0 - 60, dx))))
                nx, self.draw_w, sx = x0 + d, w0 - d, -d
            elif side == "t":
                d = int(round(max(-y0, min(h0 - 40, dy))))
                ny, self.draw_h, sy = y0 + d, h0 - d, -d
            orig = getattr(self, "_resize_orig_shapes", None) or []
            if (sx or sy or side in ("l", "t")) and len(orig) == len(self.shapes):
                self.shapes = [dict(sh) for sh in orig]
                for sh in self.shapes:
                    self._shift_shape(sh, sx, sy)
            self.update_layout()
            if (nx, ny) != (self.x, self.y):
                self.canvas.move_box(self, nx, ny)
            return True
        if self.dragging and not self.editing:
            if not held:
                self.dragging = False
                return False
            dx = int((event.x_root - self.drag_start_root_x) / z)
            dy = int((event.y_root - self.drag_start_root_y) / z)
            self.canvas.drag_box_or_group(self, dx, dy)
            return True

        if self.editing and self.op is not None and held and self.op.get("kind") == "band":
            self.op["ex"], self.op["ey"] = self._clamp(lx - self.PAD, ly - self.PAD)
            self.queue_draw()
            return True
        if self.editing and self.op is not None and held and self.op.get("kind") == "move":
            ax, ay = self._clamp(lx - self.PAD, ly - self.PAD)
            dx, dy = ax - self.op["ax"], ay - self.op["ay"]
            for i, o in self.op["origs"].items():
                if i < len(self.shapes):
                    self._shift_shape(self.shapes[i], dx, dy, orig=o)
            self.queue_draw()
            return True
        if self.editing and self.op is not None and held and self.sel_shape is not None \
                and self.sel_shape < len(self.shapes):
            ax, ay = self._clamp(lx - self.PAD, ly - self.PAD)
            s = self.shapes[self.sel_shape]
            kind = self.op["kind"]
            if kind == "create":
                sx0, sy0 = self.op.get("sx", s["x1"]), self.op.get("sy", s["y1"])
                if shift and (s["type"] in DRAW_LINE_TYPES or s["type"] == "arc" or s["type"] in DRAW_ELEC_TYPES):
                    # snap to multiples of 45°
                    dx, dy = ax - sx0, ay - sy0
                    ang = round(math.atan2(dy, dx) / (math.pi / 4)) * (math.pi / 4)
                    L = math.hypot(dx, dy)
                    ax, ay = self._clamp(sx0 + L * math.cos(ang), sy0 + L * math.sin(ang))
                elif shift:
                    side = max(abs(ax - sx0), abs(ay - sy0))
                    ax = sx0 + math.copysign(side, ax - sx0)
                    ay = sy0 + math.copysign(side, ay - sy0)
                if s["type"] == "triangle":
                    self._triangle_from_drag(s, self.op["sx"], self.op["sy"], ax, ay)
                else:
                    s["x2"], s["y2"] = ax, ay
            elif kind == "handle":
                name = self.op["name"]
                if name in ("v1", "v2", "v3"):
                    s["x" + name[1]], s["y" + name[1]] = ax, ay
                elif name == "mid":
                    s["angle"] = self._arc_angle_from_mid(s, ax, ay)
                elif name in ("p1", "p2"):
                    if shift and (s["type"] in DRAW_LINE_TYPES or s["type"] in DRAW_ELEC_TYPES):
                        fx, fy = (s["x2"], s["y2"]) if name == "p1" else (s["x1"], s["y1"])
                        ang = round(math.atan2(ay - fy, ax - fx) / (math.pi / 4)) * (math.pi / 4)
                        Lh = math.hypot(ax - fx, ay - fy)
                        ax, ay = self._clamp(fx + Lh * math.cos(ang), fy + Lh * math.sin(ang))
                    s["x" + name[1]], s["y" + name[1]] = ax, ay
                else:
                    # move whichever stored corner is on that side (keeps a triangle's or
                    # arc's orientation)
                    west = "x1" if s["x1"] <= s["x2"] else "x2"
                    east = "x2" if west == "x1" else "x1"
                    north = "y1" if s["y1"] <= s["y2"] else "y2"
                    south = "y2" if north == "y1" else "y1"
                    ar = self._image_aspect(s) if s["type"] == "image" and not shift else None
                    if ar:  # keep the picture's proportions about the opposite corner
                        fx = s[east] if "w" in name else s[west]
                        fy = s[south] if "n" in name else s[north]
                        bw, bh = max(4.0, abs(ax - fx)), max(4.0, abs(ay - fy))
                        bw = max(bw, bh * ar)
                        bh = bw / ar
                        ax = fx - bw if "w" in name else fx + bw
                        ay = fy - bh if "n" in name else fy + bh
                    s[west if "w" in name else east] = ax
                    s[north if "n" in name else south] = ay
            self.queue_draw()
            return True

        # hover cursors
        crop_hover = self._hit_crop_edge(lx, ly) if (not self.editing and self.selected) else None
        if not self.editing and self.selected and self._hit_box_resize(lx, ly):
            self._set_cursor_by_name("nwse-resize")
        elif crop_hover:
            self._set_cursor_by_name("ew-resize" if crop_hover in ("l", "r") else "ns-resize")
        elif self.editing and self.tool != "select":
            self._set_cursor_by_name("crosshair")
        elif self.editing and self._hit_handle(lx - self.PAD, ly - self.PAD):
            self._set_cursor_by_name("move")
        else:
            self._set_cursor_by_name(None)
        return False

    def on_button_release(self, widget, event):
        if event.button != 1:
            return False
        if self.resizing or getattr(self, "cropping", None):
            self.resizing = False
            self.cropping = None
            self._resize_orig_shapes = None
            self.canvas.recalculate_worksheet()
            return True
        if self.dragging:
            self.dragging = False
            self.canvas.recalculate_worksheet()
            return True
        if self.editing and self.op is not None and self.op.get("kind") == "band":
            b = self.op
            x0, x1 = sorted((b["sx"], b["ex"]))
            y0, y1 = sorted((b["sy"], b["ey"]))
            hits = []
            if (x1 - x0) > 3 or (y1 - y0) > 3:
                for i, sh in enumerate(self.shapes):
                    bx0, by0, bx1, by1 = self._bbox(sh)
                    if x0 <= bx0 and bx1 <= x1 and y0 <= by0 and by1 <= y1:  # fully inside
                        hits.append(i)
            self._set_selection(list(b["base"]) + hits)
            if self.sel_shape is not None:
                sh = self.shapes[self.sel_shape]
                self.cur_color = sh.get("color", "auto")
                self.cur_width = float(sh.get("width", 1.6))
            self.op = None
            self.update_layout()
            return True
        if self.editing and self.op is not None:
            if self.op["kind"] == "create" and self.sel_shape is not None and self.sel_shape < len(self.shapes):
                s = self.shapes[self.sel_shape]
                x0, y0, x1, y1 = self._bbox(s)
                if math.hypot(x1 - x0, y1 - y0) < 4:
                    # a plain click places a default-sized shape
                    if s["type"] == "triangle":
                        sx, sy = self.op["sx"], self.op["sy"]
                        ex, ey = self._clamp(sx + 80, sy + 60)
                        self._triangle_from_drag(s, sx, sy, ex, ey)
                    elif s["type"] == "ground":
                        s["x2"], s["y2"] = self._clamp(s["x1"], s["y1"] + 40)
                    elif s["type"] in DRAW_LINE_TYPES or s["type"] == "arc" or s["type"] in DRAW_ELEC_TYPES:
                        s["x2"], s["y2"] = self._clamp(s["x1"] + 80, s["y1"])
                    else:
                        s["x2"], s["y2"] = self._clamp(s["x1"] + 80, s["y1"] + 50)
                self.tool = "select"  # like PowerPoint: back to the pointer after drawing
                self.update_layout()
            self.op = None
            self.queue_draw()
            return True
        return False

    # ---- keyboard ------------------------------------------------------------

    def on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if not self.editing:
            if keyname in ("Delete", "BackSpace"):
                self.canvas.remove_selected_boxes(self)
                return True
            if keyname in ("Return", "KP_Enter"):
                self.start_editing()
                return True
            return False
        if keyname in ("Delete", "BackSpace"):
            self._delete_selected_shape()
            return True
        if keyname == "Escape":
            if self.tool != "select":
                self.tool = "select"  # drop the chosen tool, back to selecting shapes
                self.queue_draw()
            elif self.sel_shape is not None:
                self.sel_shape = None
                self.queue_draw()
            else:
                self.stop_editing()
            return True
        if keyname in ("r", "R") and self.sel_shape is not None and self.sel_shape < len(self.shapes):
            self._rotate_selected(-90 if keyname == "R" else 90)
            return True
        steps = {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1)}
        if keyname in steps and self._selected_indices():
            k = 10 if event.state & Gdk.ModifierType.SHIFT_MASK else 1
            dx, dy = steps[keyname]
            for i in self._selected_indices():
                self._shift_shape(self.shapes[i], dx * k, dy * k)
            self.queue_draw()
            return True
        return True  # keep other keys inside the drawing while editing

    def _show_context_menu(self, event):
        menu = Gtk.Menu()

        def add(label, cb, sensitive=True):
            mi = Gtk.MenuItem(label=label)
            mi.connect("activate", lambda _mi: cb())
            mi.set_sensitive(sensitive)
            menu.append(mi)

        add("Done Drawing" if self.editing else "Edit Drawing", self.stop_editing if self.editing else self.start_editing)
        add("Caption…", lambda: open_figure_caption_dialog(self))
        bg_mi = Gtk.CheckMenuItem(label="Background (white / black)")
        bg_mi.set_active(self.background)
        bg_mi.connect("toggled", lambda w: (setattr(self, "background", w.get_active()), self.update_layout()))
        menu.append(bg_mi)
        add("Paste Picture into Drawing", self.paste_picture)
        add("Insert Picture from File into Drawing…", self.insert_picture_from_file)
        if self.editing:
            has_sel = self.sel_shape is not None and self.sel_shape < len(self.shapes)
            menu.append(Gtk.SeparatorMenuItem())
            add("Copy Shape  (Ctrl+C)", self.copy_shape, has_sel)
            add("Cut Shape  (Ctrl+X)", self.cut_shape, has_sel)
            add("Paste Shape  (Ctrl+V)", self.paste_shapes, bool(_DRAW_CLIPBOARD["shapes"]))
            add("Duplicate Shape  (Ctrl+D)", self.duplicate_shape, has_sel)
            menu.append(Gtk.SeparatorMenuItem())
            add("Rotate Shape 90°  (R; Shift+R the other way)", lambda: self._rotate_selected(90), has_sel)
            add("Bring Shape to Front", self._shape_to_front, has_sel)
            add("Send Shape to Back", self._shape_to_back, has_sel)
            add("Delete Shape", self._delete_selected_shape, has_sel)
        menu.append(Gtk.SeparatorMenuItem())
        add("Center on Page", lambda: self.canvas.move_box(self, max(0, (self.canvas.A4_WIDTH - self.logical_w) // 2), self.y))
        add("Delete Drawing", lambda: self.canvas.remove_selected_boxes(self))
        menu.show_all()
        menu.popup_at_pointer(event)

    def _shape_to_front(self):
        sel = self._selected_indices()
        if sel:
            moved = [self.shapes[i] for i in sel]
            self.shapes = [sh for i, sh in enumerate(self.shapes) if i not in sel] + moved
            self._set_selection(range(len(self.shapes) - len(moved), len(self.shapes)))
            self.queue_draw()

    def _shape_to_back(self):
        sel = self._selected_indices()
        if sel:
            moved = [self.shapes[i] for i in sel]
            self.shapes = moved + [sh for i, sh in enumerate(self.shapes) if i not in sel]
            self._set_selection(range(len(moved)))
            self.queue_draw()

    def to_dict(self) -> dict:
        def r(v):
            return round(float(v), 1)
        shapes = []
        for s in self.shapes:
            d = {k: (r(v) if k in ("x1", "y1", "x2", "y2", "width") else v) for k, v in s.items()}
            shapes.append(d)
        return {
            "type": "drawing", "x": self.x, "y": self.y,
            "width": self.draw_w, "height": self.draw_h,
            "title": self.title, "shapes": shapes, "background": self.background,
        }


# ============================================================================
# Arrow (a free-standing simple-head arrow on the sheet, outside any drawing)
# ============================================================================


def ask_arrow_style(parent, color="auto", width=1.8, title="Arrow"):
    """Dialog with Color and Thickness combos. Returns (color, width) or None."""
    dlg = Gtk.Dialog(
        title=title,
        transient_for=parent if isinstance(parent, Gtk.Window) else None,
        flags=0,
    )
    dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
    dlg.set_default_response(Gtk.ResponseType.OK)
    area = dlg.get_content_area()
    for side in ("start", "end", "top", "bottom"):
        getattr(area, f"set_margin_{side}")(12)
    grid = Gtk.Grid(column_spacing=10, row_spacing=8)
    color_combo = Gtk.ComboBoxText()
    for k, _rgb in DRAW_COLORS:
        color_combo.append(k, DRAW_COLOR_LABELS.get(k, k))
    color_combo.set_active_id(color if color in dict(DRAW_COLORS) else "auto")
    width_combo = Gtk.ComboBoxText()
    for k, lbl, _w in DRAW_WIDTHS:
        width_combo.append(k, lbl)
    width_combo.set_active_id(draw_width_key(width))
    grid.attach(Gtk.Label(label="Color:", xalign=1.0), 0, 0, 1, 1)
    grid.attach(color_combo, 1, 0, 1, 1)
    grid.attach(Gtk.Label(label="Thickness:", xalign=1.0), 0, 1, 1, 1)
    grid.attach(width_combo, 1, 1, 1, 1)
    area.pack_start(grid, False, False, 0)
    dlg.show_all()
    result = None
    if dlg.run() == Gtk.ResponseType.OK:
        wk = width_combo.get_active_id() or "medium"
        result = (color_combo.get_active_id() or "auto", next(w for k, _l, w in DRAW_WIDTHS if k == wk))
    dlg.destroy()
    return result


class ArrowBox(Gtk.DrawingArea):
    """A simple-head (">") arrow placed directly on the sheet. Drag it to move it, drag an
    end grip (when selected) to change its length/direction (Shift snaps to 45°), and
    double-click to choose its color and thickness."""

    PAD = 10.0
    GRIP = 7.0

    def __init__(self, canvas, x1, y1, x2, y2, color="auto", width=1.8, head=True):
        super().__init__()
        self.canvas = canvas
        self.color = color
        self.width = float(width)
        self.head = bool(head)  # False: a plain floating line
        self.editing = False
        self.selected = False
        self.dragging = False
        self.grip = None  # "p1" / "p2" while dragging an end
        self.drag_start_root_x = self.drag_start_root_y = 0
        self.drag_start_box_x = self.drag_start_box_y = 0
        self._grip_start = None
        self.x = self.y = 0
        self.logical_w = self.logical_h = 20
        self._set_ends(x1, y1, x2, y2, place=False)
        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("key-press-event", self.on_key_press)
        self.set_tooltip_text("Double-click for color and thickness")

    # ends in sheet coordinates <-> local (widget) coordinates
    def ends(self):
        return (self.x + self.lx1, self.y + self.ly1, self.x + self.lx2, self.y + self.ly2)

    def _set_ends(self, x1, y1, x2, y2, place=True):
        P = self.PAD
        ox, oy = min(x1, x2) - P, min(y1, y2) - P
        self.lx1, self.ly1, self.lx2, self.ly2 = x1 - ox, y1 - oy, x2 - ox, y2 - oy
        self.logical_w = int(math.ceil(abs(x2 - x1) + 2 * P))
        self.logical_h = int(math.ceil(abs(y2 - y1) + 2 * P))
        self.x, self.y = int(round(ox)), int(round(oy))
        # keep the ends exact after rounding the origin
        self.lx1, self.lx2 = x1 - self.x, x2 - self.x
        self.ly1, self.ly2 = y1 - self.y, y2 - self.y
        z = getattr(self.canvas, "zoom", 1.0)
        self.set_size_request(max(8, int(math.ceil(self.logical_w * z))), max(8, int(math.ceil(self.logical_h * z))))
        if place and self.get_parent() is not None:
            self.canvas.fixed.move(self, int(round(self.x * z)), int(round(self.y * z)))
        self.queue_draw()

    def update_layout(self):
        _sched = getattr(getattr(self, "canvas", None), "schedule_page_breaks", None)
        if _sched:
            _sched()
        z = getattr(self.canvas, "zoom", 1.0)
        self.set_size_request(max(8, int(math.ceil(self.logical_w * z))), max(8, int(math.ceil(self.logical_h * z))))
        self.queue_draw()

    def is_empty(self):
        return False

    def set_selected(self, selected):
        self.selected = selected
        self.queue_draw()

    def start_editing(self):
        pass

    def stop_editing(self):
        self.editing = False

    def draw_content(self, cr, theme=None, for_export=False):
        if theme is None:
            theme = THEMES[self.canvas.theme_name]
        rgb = dict(DRAW_COLORS).get(self.color) or theme["text"]
        x1, y1, x2, y2 = self.lx1, self.ly1, self.lx2, self.ly2
        lw = self.width
        cr.save()
        cr.set_source_rgb(*rgb)
        cr.set_line_width(lw)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.move_to(x1, y1)
        cr.line_to(x2, y2)
        cr.stroke()
        L = math.hypot(x2 - x1, y2 - y1)
        if L > 0.5 and self.head:
            a = math.atan2(y2 - y1, x2 - x1)
            head = min(7.0 + 2.2 * lw, L / 1.1)
            cr.move_to(x2 - head * math.cos(a - 0.5), y2 - head * math.sin(a - 0.5))
            cr.line_to(x2, y2)
            cr.line_to(x2 - head * math.cos(a + 0.5), y2 - head * math.sin(a + 0.5))
            cr.stroke()
        cr.restore()
        if self.selected and not for_export:
            g = self.GRIP
            cr.save()
            cr.set_line_width(1.0)
            for gx, gy in ((x1, y1), (x2, y2)):
                cr.set_source_rgb(*theme["canvas_bg"])
                cr.rectangle(gx - g / 2, gy - g / 2, g, g)
                cr.fill()
                cr.set_source_rgb(*theme["box_selected_border"])
                cr.rectangle(gx - g / 2, gy - g / 2, g, g)
                cr.stroke()
            cr.restore()

    def on_draw(self, widget, cr):
        z = getattr(self.canvas, "zoom", 1.0)
        cr.save()
        cr.scale(z, z)
        self.draw_content(cr, for_export=False)
        cr.restore()
        return True

    def _near_line(self, lx, ly):
        return DrawingBox._seg_dist(lx, ly, self.lx1, self.ly1, self.lx2, self.ly2) <= 6 + self.width

    def _hit_grip(self, lx, ly):
        if not self.selected:
            return None
        for name, gx, gy in (("p1", self.lx1, self.ly1), ("p2", self.lx2, self.ly2)):
            if abs(lx - gx) <= self.GRIP and abs(ly - gy) <= self.GRIP:
                return name
        return None

    def edit_style(self):
        res = ask_arrow_style(self.get_toplevel(), self.color, self.width,
                              title="Arrow" if self.head else "Line")
        if res is not None:
            self.color, self.width = res
            self.queue_draw()
        self.canvas.focus_without_scroll(self)
        return False

    def on_button_press(self, widget, event):
        z = getattr(self.canvas, "zoom", 1.0)
        lx, ly = event.x / z, event.y / z
        grip = self._hit_grip(lx, ly) if event.button == 1 else None
        if grip is None and not self._near_line(lx, ly):
            return False  # empty corner of the box: let the sheet have the click
        if event.button == 3:
            if self not in self.canvas.selected_boxes:
                self.canvas.select_box(self)
            self._show_context_menu(event)
            return True
        if event.button != 1:
            return False
        self.canvas.focus_without_scroll(self)
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.dragging = False
            self.grip = None
            GLib.idle_add(self.edit_style)
            return True
        self.drag_start_root_x, self.drag_start_root_y = event.x_root, event.y_root
        if grip is not None:
            self.grip = grip
            self._grip_start = self.ends()
            return True
        self.canvas.handle_box_button_press(self, event)
        self.dragging = True
        self.drag_start_box_x, self.drag_start_box_y = self.x, self.y
        return True

    def on_motion_notify(self, widget, event):
        held = bool(event.state & Gdk.ModifierType.BUTTON1_MASK)
        z = getattr(self.canvas, "zoom", 1.0)
        if self.grip is not None:
            if not held:
                self.grip = None
                return False
            x1, y1, x2, y2 = self._grip_start
            dx = (event.x_root - self.drag_start_root_x) / z
            dy = (event.y_root - self.drag_start_root_y) / z
            if self.grip == "p1":
                fx, fy, mx, my = x2, y2, x1 + dx, y1 + dy
            else:
                fx, fy, mx, my = x1, y1, x2 + dx, y2 + dy
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                ang = round(math.atan2(my - fy, mx - fx) / (math.pi / 4)) * (math.pi / 4)
                L = math.hypot(mx - fx, my - fy)
                mx, my = fx + L * math.cos(ang), fy + L * math.sin(ang)
            mx = max(self.PAD, min(self.canvas.A4_WIDTH - self.PAD, mx))
            my = max(self.PAD, min(self.canvas.total_height - self.PAD, my))
            if self.grip == "p1":
                self._set_ends(mx, my, fx, fy)
            else:
                self._set_ends(fx, fy, mx, my)
            return True
        if self.dragging:
            if not held:
                self.dragging = False
                return False
            dx = int((event.x_root - self.drag_start_root_x) / z)
            dy = int((event.y_root - self.drag_start_root_y) / z)
            self.canvas.drag_box_or_group(self, dx, dy)
            return True
        win = self.get_window()
        if win is not None:
            lx, ly = event.x / z, event.y / z
            name = "move" if self._hit_grip(lx, ly) else None
            try:
                win.set_cursor(Gdk.Cursor.new_from_name(win.get_display(), name) if name else None)
            except Exception:
                pass
        return False

    def on_button_release(self, widget, event):
        if event.button != 1:
            return False
        if self.grip is not None:
            self.grip = None
            self.canvas.recalculate_worksheet()
            return True
        if self.dragging:
            self.dragging = False
            self.canvas.recalculate_worksheet()
            return True
        return False

    def on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ("Delete", "BackSpace"):
            self.canvas.remove_selected_boxes(self)
            return True
        if keyname in ("Return", "KP_Enter"):
            GLib.idle_add(self.edit_style)
            return True
        return False

    def _show_context_menu(self, event):
        menu = Gtk.Menu()
        for label, cb in (
            ("Color & Thickness…", lambda: GLib.idle_add(self.edit_style)),
            *((("Reverse Direction", self._reverse), ("Remove Arrow Head (plain line)", self._toggle_head))
              if self.head else (("Add Arrow Head", self._toggle_head),)),
            (None, None),
            ("Delete", lambda: self.canvas.remove_selected_boxes(self)),
        ):
            if label is None:
                menu.append(Gtk.SeparatorMenuItem())
                continue
            mi = Gtk.MenuItem(label=label)
            mi.connect("activate", lambda _mi, f=cb: f())
            menu.append(mi)
        menu.show_all()
        menu.popup_at_pointer(event)

    def _reverse(self):
        x1, y1, x2, y2 = self.ends()
        self._set_ends(x2, y2, x1, y1)

    def _toggle_head(self):
        self.head = not self.head
        self.set_tooltip_text("Double-click for color and thickness")
        self.queue_draw()
        cp = getattr(self.canvas, "undo_checkpoint", None)
        if callable(cp):
            cp()

    def to_dict(self) -> dict:
        x1, y1, x2, y2 = self.ends()
        r = lambda v: round(float(v), 1)
        return {"type": "arrow" if self.head else "line", "x1": r(x1), "y1": r(y1), "x2": r(x2), "y2": r(y2),
                "color": self.color, "width": self.width}


# ============================================================================
# Data Table Box (cell data usable in calculations anywhere on the sheet)
# ============================================================================


_TABLE_CELL_ENV = {
    "__builtins__": {},
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "sqrt": math.sqrt, "ln": math.log, "log": math.log10, "exp": math.exp,
    "abs": abs, "pi": math.pi, "π": math.pi, "e": math.e,
}


_DECIMAL_COMMA_RE = None


def _is_number_text(t: str) -> bool:
    try:
        float(t)
        return True
    except ValueError:
        return False


def parse_tabular_text(text: str, require_numbers: bool = True):
    """Parse pasted tabular text (from a spreadsheet, a plot digitizer, CSV …).
    Columns may be separated by tabs, commas, semicolons or spaces; a decimal comma is
    accepted when the separator is not a comma. A first row that is not numeric is taken as
    the column headers. Returns (headers or None, rows) with all cells as strings, or None
    when the text does not look like a table of numbers."""
    import re
    global _DECIMAL_COMMA_RE
    if _DECIMAL_COMMA_RE is None:
        _DECIMAL_COMMA_RE = re.compile(r"^[-+]?\d*,\d+([eE][-+]?\d+)?$")
    if not text:
        return None
    lines = [ln.strip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    lines = [ln for ln in lines if ln]
    if not lines:
        return None
    if any("\t" in ln for ln in lines):
        rows = [[c.strip() for c in ln.split("\t")] for ln in lines]
        delim = "\t"
    elif all(";" in ln for ln in lines) or (len(lines) > 1 and all(";" in ln for ln in lines[1:])):
        rows = [[c.strip() for c in ln.split(";")] for ln in lines]
        delim = ";"
    elif any("," in ln for ln in lines) and len({ln.count(",") for ln in lines}) == 1:
        rows = [[c.strip() for c in ln.split(",")] for ln in lines]
        delim = ","
    else:
        rows = [ln.split() for ln in lines]
        delim = " "
    if delim != ",":
        rows = [[c.replace(",", ".") if _DECIMAL_COMMA_RE.match(c) else c for c in r] for r in rows]
    headers = None
    if len(rows) > 1 and not all(_is_number_text(c) for c in rows[0] if c) and \
            sum(_is_number_text(c) for c in rows[1] if c) >= max(1, len([c for c in rows[1] if c]) // 2):
        headers, rows = rows[0], rows[1:]
    ncols = max(len(r) for r in rows) if rows else 0
    if headers is not None:
        ncols = max(ncols, len(headers))
        headers = headers + [""] * (ncols - len(headers))
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    cells = [c for r in rows for c in r if c]
    if require_numbers:
        if len(cells) < 2 or sum(_is_number_text(c) for c in cells) < 0.6 * len(cells):
            return None
    return headers, rows


def parse_table_cell(raw: str):
    """Convert a cell's text to a value: '' -> None, numbers -> float,
    constant expressions (e.g. 2*pi, 1e-3, sqrt(2)) -> float, anything else -> str."""
    txt = (raw or "").strip()
    if not txt:
        return None
    try:
        return float(txt)
    except ValueError:
        pass
    expr = txt.replace("^", "**").replace("·", "*").replace("×", "*").replace("−", "-")
    if any(ch.isdigit() for ch in expr) or "pi" in expr or "π" in expr:
        try:
            val = eval(expr, dict(_TABLE_CELL_ENV))
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return float(val)
        except Exception:
            pass
    return txt


class SheetTable:
    """Value bound to a table's name on the sheet.
    T(i, j) -> cell at row i, column j (1-based; j may also be the column header text)
    T(i)    -> row i as a vector
    """

    def __init__(self, name, headers, values):
        self.name = name
        self.headers = list(headers)
        self.values = values  # list of rows, each a list of parsed cell values

    def _col_index(self, j):
        if isinstance(j, str):
            if j in self.headers:
                return self.headers.index(j)
            raise KeyError(f"{self.name} has no column '{j}'")
        jj = int(round(float(j)))
        if not 1 <= jj <= len(self.headers):
            raise IndexError(f"{self.name}: column {jj} out of range 1..{len(self.headers)}")
        return jj - 1

    def _row_index(self, i):
        ii = int(round(float(i)))
        if not 1 <= ii <= len(self.values):
            raise IndexError(f"{self.name}: row {ii} out of range 1..{len(self.values)}")
        return ii - 1

    def __call__(self, i, j=None):
        row = self.values[self._row_index(i)]
        if j is None:
            return [math.nan if v is None else v for v in row]
        v = row[self._col_index(j)]
        if v is None:
            raise ValueError(f"{self.name}({i}, {j}) is empty")
        return v

    def column(self, j):
        c = self._col_index(j)
        col = [r[c] for r in self.values]
        while col and col[-1] is None:
            col.pop()
        return [math.nan if v is None else v for v in col]

    def __len__(self):
        return len(self.values)

    def __repr__(self):
        return f"<table {self.name}: {len(self.values)}×{len(self.headers)}>"


def _tbl_rows(t):
    return len(t)


def _tbl_cols(t):
    return len(t.headers) if isinstance(t, SheetTable) else 1


def _tbl_col(t, j):
    return t.column(j)


def _tbl_row(t, i):
    return t(i)


def _vec_mean(v):
    vals = list(v)
    if not vals:
        return math.nan
    return _vec_total(vals) / len(vals)


# Functions made available to every math box (useful on table columns / vectors)
TABLE_SHEET_FUNCS = {
    "rows": _tbl_rows,
    "cols": _tbl_cols,
    "col": _tbl_col,
    "row": _tbl_row,
    "len": len,
    "total": _vec_total,
    "mean": _vec_mean,
    "max": max,
    "min": min,
}


class TableBox(Gtk.DrawingArea):
    """
    Data table on the A4 worksheet.
    - The table name (e.g. T1) is a sheet variable: T1(i, j) gives the cell in row i, column j (1-based).
    - Every column whose header is a valid name (e.g. Re, Nu, x_1) becomes a vector variable
      holding that column's values, usable in math boxes and plots anywhere on the sheet.
    - Click a cell to edit; Enter / Tab / arrows move between cells; right-click for row/column options.
    - The name is shown only in the Table Options dialog (double-click the bar above the table).
    - An optional caption ("Table N: ...") is drawn above the table and moves with it.
    - Drag the table by the bar / caption above it.
    """

    HANDLE_H = 22  # drag bar above the table; holds the caption button when selected
    CAPTION_PREFIX = "Table"
    CAPTION_WHERE = "above"
    PAD = 4
    MIN_COL_W = 56
    CELL_PAD_X = 6
    SB_W = 9       # scroll bar width when only some rows are shown
    SB_GAP = 3

    def __init__(self, canvas, x, y, name="T1", headers=None, cells=None, rows=4, cols=3, title=""):
        super().__init__()
        self.canvas = canvas
        self.name = name
        self.title = title
        self.fig_num = 1  # table number, assigned by the canvas
        self.grid_top = self.HANDLE_H
        self.caption_h = 0
        if headers is None:
            headers = [f"c{j + 1}" for j in range(cols)]
        self.headers = [str(h) for h in headers]
        ncols = len(self.headers)
        if cells is None:
            cells = [["" for _ in range(ncols)] for _ in range(rows)]
        self.cells = [[str(v) if v is not None else "" for v in (list(r) + [""] * ncols)[:ncols]] for r in cells]

        self.x = int(x)
        self.y = int(y)
        self.editing = False
        self.selected = False
        self.dragging = False
        self.drag_start_root_x = 0
        self.drag_start_root_y = 0
        self.drag_start_box_x = 0
        self.drag_start_box_y = 0
        self.active = None  # (row, col); row -1 is the header row
        self.cursor_pos = 0
        self.col_widths = []
        self.row_h = 24
        self.logical_w = 100
        self.logical_h = 60
        self.visible_rows = 0   # 0 = show all rows; N = show N rows with a scroll bar
        self.row_offset = 0     # first row shown when scrolling
        self._sb_drag = None    # (start y, start offset) while dragging the scroll thumb

        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.FOCUS_CHANGE_MASK
        )
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("key-press-event", self.on_key_press)
        self.connect("scroll-event", self.on_scroll)
        self.update_layout()

    # ---------------------------------------------------------------- data
    @property
    def n_rows(self):
        return len(self.cells)

    @property
    def n_cols(self):
        return len(self.headers)

    # ----------------------------------------------------------- scrolling
    @property
    def shown_rows(self):
        n = self.n_rows
        return n if self.visible_rows <= 0 or n <= self.visible_rows else self.visible_rows

    @property
    def scrolling(self):
        return self.shown_rows < self.n_rows

    def _clamp_offset(self):
        self.row_offset = max(0, min(self.row_offset, self.n_rows - self.shown_rows))

    def scroll_rows(self, delta) -> bool:
        old = self.row_offset
        self.row_offset += int(delta)
        self._clamp_offset()
        if self.row_offset != old:
            self.queue_draw()
            return True
        return False

    def _ensure_row_visible(self, r):
        if r is None or r < 0 or not self.scrolling:
            return
        if r < self.row_offset:
            self.row_offset = r
        elif r >= self.row_offset + self.shown_rows:
            self.row_offset = r - self.shown_rows + 1
        self._clamp_offset()

    def set_visible_rows(self, n):
        self.visible_rows = max(0, int(n))
        self._clamp_offset()
        self.update_layout()

    def _sb_geometry(self):
        """(x, y, w, h, thumb_y, thumb_h) of the scroll bar, or None when not scrolling."""
        if not self.scrolling:
            return None
        x = self.PAD + sum(self.col_widths) + self.SB_GAP
        y = self.grid_top + self.row_h
        h = self.row_h * self.shown_rows
        frac = self.shown_rows / self.n_rows
        th = max(14.0, h * frac)
        span = self.n_rows - self.shown_rows
        ty = y + (h - th) * (self.row_offset / span if span else 0.0)
        return x, y, float(self.SB_W), float(h), ty, th

    def _cell_text(self, r, c):
        return self.headers[c] if r < 0 else self.cells[r][c]

    def _set_cell_text(self, r, c, text):
        if r < 0:
            self.headers[c] = text
        else:
            self.cells[r][c] = text

    @staticmethod
    def header_var_name(header: str):
        h = header.strip().replace(" ", "_")
        return h if h.isidentifier() else None

    def to_sheet_table(self) -> SheetTable:
        values = [[parse_table_cell(t) for t in row] for row in self.cells]
        while values and all(v is None for v in values[-1]):
            values.pop()  # trailing blank rows don't count as data
        return SheetTable(self.name, [h.strip() for h in self.headers], values)

    # -------------------------------------------------------------- layout
    def _layout(self, text, bold=False, header=False, pango_ctx=None):
        if pango_ctx is None:
            pango_ctx = self.get_pango_context()
        layout, _, _, _ = MathRenderer._make_layout(pango_ctx, "", 0.8, bold=bold)
        if header and "_" in text.strip():
            base, sub = text.strip().split("_", 1)
            layout.set_markup(
                f"{GLib.markup_escape_text(base)}<sub>{GLib.markup_escape_text(sub)}</sub>", -1
            )
        else:
            layout.set_text(text, -1)
        return layout

    def _display_text(self, r, c, for_export=False):
        raw = self._cell_text(r, c)
        if r < 0 or (self.editing and self.active == (r, c) and not for_export):
            return raw
        val = parse_table_cell(raw)
        if isinstance(val, float):
            try:
                float(raw.strip())
                return raw.strip()
            except ValueError:
                return format_number(val)
        return raw

    def update_layout(self):
        _sched = getattr(getattr(self, "canvas", None), "schedule_page_breaks", None)
        if _sched:
            _sched()
        pango_ctx = self.get_pango_context()
        probe = self._layout("Xg", pango_ctx=pango_ctx)
        _, logical = probe.get_pixel_extents()
        self.row_h = max(20, logical.height + 8)
        widths = []
        for c in range(self.n_cols):
            w = self.MIN_COL_W
            for r in range(-1, self.n_rows):
                # Fit both the typed text and its computed value (they differ for e.g. 2*pi)
                for txt in {self._cell_text(r, c), self._display_text(r, c, for_export=True)}:
                    lay = self._layout(txt + " ", bold=(r < 0), header=(r < 0), pango_ctx=pango_ctx)
                    _, lg = lay.get_pixel_extents()
                    w = max(w, lg.width + 2 * self.CELL_PAD_X)
            widths.append(int(math.ceil(w)))
        self.col_widths = widths
        grid_w = sum(widths)
        cap_lay = self._make_caption_layout(pango_ctx)
        if cap_lay is not None:
            _, cl = cap_lay.get_pixel_extents()
            self.caption_h = int(math.ceil(cl.height)) + 6
        else:
            self.caption_h = 0
        self.grid_top = self.HANDLE_H + self.caption_h
        self._clamp_offset()
        sb = (self.SB_W + self.SB_GAP) if self.scrolling else 0
        self.logical_w = int(max(grid_w, 90) + 2 * self.PAD + sb)
        self.logical_h = int(self.grid_top + self.row_h * (self.shown_rows + 1) + self.PAD)
        z = getattr(self.canvas, "zoom", 1.0)
        self.set_size_request(
            max(24, int(math.ceil(self.logical_w * z))),
            max(24, int(math.ceil(self.logical_h * z))),
        )
        self.queue_draw()

    def _update_size_request(self):
        self.update_layout()

    def get_caption_text(self) -> str:
        raw = self.title.strip()
        if not raw:
            return ""
        if raw.lower().startswith("table "):
            parts = raw.split(":", 1)
            if len(parts) == 2 and parts[0][6:].strip().isdigit():
                raw = parts[1].strip()
        return f"Table {self.fig_num}: {raw}" if raw else f"Table {self.fig_num}"

    def _make_caption_layout(self, pango_ctx=None):
        caption_str = self.get_caption_text()
        if not caption_str:
            return None
        if pango_ctx is None:
            pango_ctx = self.get_pango_context()
        lay, _, _, _ = MathRenderer._make_layout(pango_ctx, caption_str, 0.76, bold=True)
        lay.set_width(max(90, sum(self.col_widths)) * Pango.SCALE)
        lay.set_wrap(Pango.WrapMode.WORD_CHAR)
        lay.set_alignment(Pango.Alignment.CENTER)
        return lay

    def _cell_rect(self, r, c):
        x0 = self.PAD + sum(self.col_widths[:c])
        vis = r if r < 0 else r - self.row_offset
        y0 = self.grid_top + (vis + 1) * self.row_h
        return x0, y0, self.col_widths[c], self.row_h

    def _hit_cell(self, lx, ly):
        if ly < self.grid_top:
            return None
        r = int((ly - self.grid_top) // self.row_h) - 1
        if r >= self.shown_rows:
            return None
        if r >= 0:
            r += self.row_offset
        x = self.PAD
        for c, w in enumerate(self.col_widths):
            if x <= lx < x + w:
                return (r, c)
            x += w
        return None

    # -------------------------------------------------------------- drawing
    def draw_content(self, cr, theme=None, for_export=False):
        if theme is None:
            theme = THEMES[self.canvas.theme_name]
        pango_ctx = self.get_pango_context()
        w, h = self.logical_w, self.logical_h
        grid_w = sum(self.col_widths)
        gx, gy = self.PAD, self.grid_top
        grid_h = self.row_h * (self.shown_rows + 1)
        row_range = [-1] + list(range(self.row_offset, self.row_offset + self.shown_rows))

        # Caption above the table (moves with it)
        cap_lay = self._make_caption_layout(pango_ctx)
        if cap_lay is not None:
            cr.save()
            cr.set_source_rgb(*theme["heading_text"])
            cr.move_to(gx, self.HANDLE_H)
            PangoCairo.show_layout(cr, cap_lay)
            cr.restore()

        # Background & header band
        cr.save()
        cr.set_source_rgb(*theme["canvas_bg"])
        cr.rectangle(gx, gy, grid_w, grid_h)
        cr.fill()
        cr.set_source_rgb(*theme["placeholder_fill"])
        cr.rectangle(gx, gy, grid_w, self.row_h)
        cr.fill()
        cr.restore()

        # Cell text
        for r in row_range:
            for c in range(self.n_cols):
                x0, y0, cw, ch = self._cell_rect(r, c)
                txt = self._display_text(r, c, for_export=for_export)
                if not txt:
                    continue
                is_active = self.editing and self.active == (r, c) and not for_export
                lay = self._layout(txt, bold=(r < 0), header=(r < 0 and not is_active), pango_ctx=pango_ctx)
                _, lg = lay.get_pixel_extents()
                val = None if r < 0 else parse_table_cell(self._cell_text(r, c))
                if r < 0:
                    tx = x0 + (cw - lg.width) / 2.0
                    color = theme["heading_text"]
                elif isinstance(val, float) and not is_active:
                    tx = x0 + cw - self.CELL_PAD_X - lg.width
                    color = theme["text"]
                else:
                    tx = x0 + self.CELL_PAD_X
                    color = theme["text"]
                if is_active:
                    tx = x0 + self.CELL_PAD_X
                cr.save()
                cr.set_source_rgb(*color)
                cr.move_to(tx, y0 + (ch - lg.height) / 2.0)
                PangoCairo.show_layout(cr, lay)
                cr.restore()

        # Grid lines
        cr.save()
        cr.set_source_rgb(*theme["page_border"])
        cr.set_line_width(1.0)
        for r in range(self.shown_rows + 2):
            yy = gy + r * self.row_h + 0.5
            cr.move_to(gx, yy)
            cr.line_to(gx + grid_w, yy)
        xx = gx
        for c in range(self.n_cols + 1):
            cr.move_to(xx + 0.5, gy)
            cr.line_to(xx + 0.5, gy + grid_h)
            if c < self.n_cols:
                xx += self.col_widths[c]
        cr.stroke()
        # Heavier rule under the header row
        cr.set_line_width(1.8)
        cr.move_to(gx, gy + self.row_h + 0.5)
        cr.line_to(gx + grid_w, gy + self.row_h + 0.5)
        cr.stroke()
        cr.restore()

        # Scroll bar (only some rows shown)
        sbg = self._sb_geometry()
        if sbg is not None:
            sx, sy, sw, sh, ty, th = sbg

            def rounded(x, y, ww, hh, rad):
                rad = min(rad, ww / 2, hh / 2)
                cr.new_sub_path()
                cr.arc(x + ww - rad, y + rad, rad, -math.pi / 2, 0)
                cr.arc(x + ww - rad, y + hh - rad, rad, 0, math.pi / 2)
                cr.arc(x + rad, y + hh - rad, rad, math.pi / 2, math.pi)
                cr.arc(x + rad, y + rad, rad, math.pi, 1.5 * math.pi)
                cr.close_path()

            cr.save()
            tr = theme["page_border"]
            cr.set_source_rgba(tr[0], tr[1], tr[2], 0.35)
            rounded(sx, sy, sw, sh, sw / 2)
            cr.fill()
            cr.set_source_rgb(*theme["muted_text"])
            rounded(sx + 1, ty + 1, sw - 2, th - 2, (sw - 2) / 2)
            cr.fill()
            cr.restore()

        if for_export:
            return

        # Active cell frame + text cursor
        if (self.editing and self.active is not None
                and (self.active[0] < 0 or self.row_offset <= self.active[0] < self.row_offset + self.shown_rows)):
            r, c = self.active
            x0, y0, cw, ch = self._cell_rect(r, c)
            cr.save()
            cr.set_source_rgb(*theme["box_editing_border"])
            cr.set_line_width(2.0)
            cr.rectangle(x0 + 1, y0 + 1, cw - 2, ch - 2)
            cr.stroke()
            prefix = self._cell_text(r, c)[: self.cursor_pos]
            pl = self._layout(prefix, bold=(r < 0), pango_ctx=pango_ctx)
            _, plg = pl.get_pixel_extents()
            cx = x0 + self.CELL_PAD_X + plg.width + 0.5
            cr.set_source_rgb(*theme["cursor"])
            cr.set_line_width(1.5)
            cr.move_to(cx, y0 + 4)
            cr.line_to(cx, y0 + ch - 4)
            cr.stroke()
            cr.restore()

        if self.selected:
            cr.save()
            cr.set_source_rgb(*theme["box_selected_border"])
            cr.set_line_width(1.4)
            cr.set_dash([4.0, 3.0])
            cr.rectangle(0.7, 0.7, w - 1.4, h - 1.4)
            cr.stroke()
            cr.restore()
            draw_figure_caption_button(self, cr, theme, bx=gx, by=1.0)

    def on_draw(self, widget, cr):
        z = getattr(self.canvas, "zoom", 1.0)
        cr.save()
        cr.scale(z, z)
        self.draw_content(cr, for_export=False)
        cr.restore()
        return True

    # ------------------------------------------------------ canvas protocol
    def is_empty(self):
        return False

    def set_selected(self, selected):
        self.selected = selected
        if not selected and self.editing:
            self.stop_editing()
        self.queue_draw()

    def start_editing(self, cell=None):
        if cell is None:
            cell = self.active if self.active is not None else (0 if self.n_rows else -1, 0)
        self.active = cell
        self._ensure_row_visible(cell[0])
        self.cursor_pos = len(self._cell_text(*cell))
        self.editing = True
        self.canvas.focus_without_scroll(self)
        self.update_layout()

    def stop_editing(self):
        if not self.editing:
            return
        self.editing = False
        self.update_layout()
        self.canvas.recalculate_worksheet()

    def _commit_edit(self):
        self.update_layout()
        self.canvas.recalculate_worksheet()

    # --------------------------------------------------------------- mouse
    def on_button_press(self, widget, event):
        z = getattr(self.canvas, "zoom", 1.0)
        lx, ly = event.x / z, event.y / z
        if event.button == 3:
            if self not in self.canvas.selected_boxes:
                self.canvas.select_box(self)
            cell = self._hit_cell(lx, ly)
            self._show_context_menu(event, cell)
            return True
        if event.button != 1:
            return False

        sbg = self._sb_geometry()
        if sbg is not None and event.type == Gdk.EventType.BUTTON_PRESS:
            sx, sy, sw, sh, ty, th = sbg
            if sx - 2 <= lx <= sx + sw + 2 and sy <= ly <= sy + sh:
                if self not in self.canvas.selected_boxes:
                    self.canvas.select_box(self)
                if ty <= ly <= ty + th:
                    self._sb_drag = (ly, self.row_offset)
                else:  # click in the track: page up / down
                    self.scroll_rows(self.shown_rows if ly > ty + th else -self.shown_rows)
                return True

        cell = self._hit_cell(lx, ly)
        was_selected = self.selected
        self.canvas.handle_box_button_press(self, event)
        if event.state & (Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.CONTROL_MASK):
            return True
        if was_selected and hit_figure_caption_button(self, lx, ly):
            self.dragging = False
            GLib.idle_add(lambda: open_figure_caption_dialog(self) and False)
            return True
        if cell is None:
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.dragging = False
                if self.caption_h and self.HANDLE_H <= ly < self.grid_top:
                    GLib.idle_add(lambda: open_figure_caption_dialog(self) and False)
                else:
                    GLib.idle_add(self._open_options_idle)
                return True
            self.canvas.focus_without_scroll(self)
            self.dragging = True
            self.drag_start_root_x = event.x_root
            self.drag_start_root_y = event.y_root
            self.drag_start_box_x = self.x
            self.drag_start_box_y = self.y
            return True

        self.selected = True
        self.start_editing(cell)
        # Place the text cursor near the click position
        x0, _, _, _ = self._cell_rect(*cell)
        txt = self._cell_text(*cell)
        best, best_d = len(txt), None
        for i in range(len(txt) + 1):
            lay = self._layout(txt[:i], bold=(cell[0] < 0))
            _, lg = lay.get_pixel_extents()
            d = abs(x0 + self.CELL_PAD_X + lg.width - lx)
            if best_d is None or d < best_d:
                best, best_d = i, d
        self.cursor_pos = best
        self.queue_draw()
        return True

    def _open_options_idle(self):
        self.open_options_dialog()
        return False

    def _update_hover_cursor(self, event):
        win = self.get_window()
        if win is None:
            return
        z = getattr(self.canvas, "zoom", 1.0)
        lx, ly = event.x / z, event.y / z
        over_bar = ly < self.grid_top and not hit_figure_caption_button(self, lx, ly)
        try:
            win.set_cursor(Gdk.Cursor.new_from_name(win.get_display(), "move") if over_bar else None)
        except Exception:
            win.set_cursor(None)

    def on_motion_notify(self, widget, event):
        if self._sb_drag is not None:
            if not (event.state & Gdk.ModifierType.BUTTON1_MASK):
                self._sb_drag = None
                return False
            sbg = self._sb_geometry()
            if sbg is None:
                self._sb_drag = None
                return False
            z = getattr(self.canvas, "zoom", 1.0)
            _sx, _sy, _sw, sh, _ty, th = sbg
            span = self.n_rows - self.shown_rows
            per_px = span / max(1.0, sh - th)
            y0, off0 = self._sb_drag
            self.row_offset = int(round(off0 + (event.y / z - y0) * per_px))
            self._clamp_offset()
            self.queue_draw()
            return True
        if not self.dragging:
            self._update_hover_cursor(event)
        if self.dragging:
            if not (event.state & Gdk.ModifierType.BUTTON1_MASK):
                self.dragging = False
                return False
            z = getattr(self.canvas, "zoom", 1.0)
            dx = int((event.x_root - self.drag_start_root_x) / z)
            dy = int((event.y_root - self.drag_start_root_y) / z)
            self.canvas.drag_box_or_group(self, dx, dy)
            return True
        return False

    def on_button_release(self, widget, event):
        if event.button == 1 and self._sb_drag is not None:
            self._sb_drag = None
            return True
        if event.button == 1 and self.dragging:
            self.dragging = False
            self.canvas.recalculate_worksheet()
            return True
        return False

    def on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            return self.canvas.on_scroll_zoom(widget, event)
        if not self.scrolling:
            return False
        if event.direction == Gdk.ScrollDirection.UP:
            step = -1
        elif event.direction == Gdk.ScrollDirection.DOWN:
            step = 1
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            ok, _dx, dy = event.get_scroll_deltas()
            acc = getattr(self, "_scroll_acc", 0.0) + (dy if ok else 0.0)
            step = int(acc)
            self._scroll_acc = acc - step
            if step == 0:
                return True
        else:
            return False
        # At the first / last row the wheel scrolls the page again
        return self.scroll_rows(step)

    # ------------------------------------------------------------ keyboard
    def _move_active(self, dr, dc, grow=False):
        r, c = self.active
        r2, c2 = r + dr, c + dc
        if c2 >= self.n_cols:
            c2, r2 = 0, r2 + 1
        elif c2 < 0:
            c2, r2 = self.n_cols - 1, r2 - 1
        if r2 >= self.n_rows:
            if not grow:
                return
            self.cells.append(["" for _ in range(self.n_cols)])
        r2 = max(-1, r2)
        self.active = (r2, c2)
        self.cursor_pos = len(self._cell_text(r2, c2))
        self._ensure_row_visible(r2)
        self._commit_edit()

    def on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)

        if not self.editing:
            if ctrl:
                return False
            if keyname in ("Delete", "BackSpace"):
                self.canvas.remove_selected_boxes(self)
                return True
            if keyname in ("Return", "KP_Enter", "F2"):
                self.start_editing()
                return True
            return False

        if ctrl:
            return False
        r, c = self.active
        text = self._cell_text(r, c)

        if keyname == "Escape":
            self.stop_editing()
            return True
        if keyname in ("Return", "KP_Enter"):
            self._move_active(-1 if shift else 1, 0, grow=not shift)
            return True
        if keyname in ("Tab", "ISO_Left_Tab"):
            self._move_active(0, -1 if (shift or keyname == "ISO_Left_Tab") else 1, grow=True)
            return True
        if keyname == "Up":
            self._move_active(-1, 0)
            return True
        if keyname == "Down":
            self._move_active(1, 0)
            return True
        if keyname == "Left":
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
                self.queue_draw()
            elif c > 0:
                self._move_active(0, -1)
            return True
        if keyname == "Right":
            if self.cursor_pos < len(text):
                self.cursor_pos += 1
                self.queue_draw()
            elif c < self.n_cols - 1:
                self._move_active(0, 1)
                self.cursor_pos = 0
                self.queue_draw()
            return True
        if keyname == "Home":
            self.cursor_pos = 0
            self.queue_draw()
            return True
        if keyname == "End":
            self.cursor_pos = len(text)
            self.queue_draw()
            return True
        if keyname == "BackSpace":
            if self.cursor_pos > 0:
                self._set_cell_text(r, c, text[: self.cursor_pos - 1] + text[self.cursor_pos:])
                self.cursor_pos -= 1
                self._commit_edit()
            return True
        if keyname == "Delete":
            if self.cursor_pos < len(text):
                self._set_cell_text(r, c, text[: self.cursor_pos] + text[self.cursor_pos + 1:])
                self._commit_edit()
            return True

        uni = Gdk.keyval_to_unicode(event.keyval)
        ch = chr(uni) if uni else ""
        if ch and ch.isprintable():
            self._set_cell_text(r, c, text[: self.cursor_pos] + ch + text[self.cursor_pos:])
            self.cursor_pos += 1
            self._commit_edit()
            return True
        return True  # swallow other keys while editing a cell

    # ----------------------------------------------------- row/col editing
    def insert_row(self, at):
        at = max(0, min(self.n_rows, at))
        self.cells.insert(at, ["" for _ in range(self.n_cols)])
        self._commit_edit()

    def delete_row(self, r):
        if self.n_rows > 1 and 0 <= r < self.n_rows:
            del self.cells[r]
            if self.active is not None and self.active[0] >= self.n_rows:
                self.active = (self.n_rows - 1, self.active[1])
            self._commit_edit()

    def _unique_header(self):
        k = self.n_cols + 1
        while f"c{k}" in self.headers:
            k += 1
        return f"c{k}"

    def insert_col(self, at):
        at = max(0, min(self.n_cols, at))
        self.headers.insert(at, self._unique_header())
        for row in self.cells:
            row.insert(at, "")
        self._commit_edit()

    def delete_col(self, c):
        if self.n_cols > 1 and 0 <= c < self.n_cols:
            del self.headers[c]
            for row in self.cells:
                del row[c]
            if self.active is not None and self.active[1] >= self.n_cols:
                self.active = (self.active[0], self.n_cols - 1)
            self._commit_edit()

    def paste_grid(self, headers, rows, at=None):
        """Write pasted data into the table starting at cell `at` (row, col), adding rows and
        columns as needed. Headers are used when pasting at the top of the table."""
        r0, c0 = at if at is not None else (self.active if self.active is not None else (0, 0))
        r0, c0 = max(-1, r0), max(0, c0)
        if headers is not None and r0 > 0:
            headers = None  # pasting into the middle of the data: keep the existing headers
        if r0 < 0:
            r0 = 0  # data always goes below the header row
        ncols = max([len(r) for r in rows] + [len(headers) if headers else 0])
        while self.n_cols < c0 + ncols:
            self.headers.append(self._unique_header())
            for row in self.cells:
                row.append("")
        while self.n_rows < r0 + len(rows):
            self.cells.append(["" for _ in range(self.n_cols)])
        if headers:
            for j, h in enumerate(headers):
                if h.strip():
                    self.headers[c0 + j] = h.strip()
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                self.cells[r0 + i][c0 + j] = v
        self.active = (r0, c0)
        self.cursor_pos = len(self._cell_text(r0, c0))
        self._commit_edit()

    def _paste_clipboard_at(self, cell):
        clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        parsed = parse_tabular_text(clip.wait_for_text() or "", require_numbers=False) if clip else None
        if parsed:
            self.paste_grid(parsed[0], parsed[1], at=cell)

    def _show_context_menu(self, event, cell):
        menu = Gtk.Menu()

        def add(label, cb, sensitive=True):
            mi = Gtk.MenuItem(label=label)
            mi.set_sensitive(sensitive)
            mi.connect("activate", lambda _m: cb())
            menu.append(mi)

        r, c = cell if cell is not None else (self.n_rows - 1, self.n_cols - 1)
        rr = max(0, r)
        add("Insert Row Above", lambda: self.insert_row(rr), r >= 0)
        add("Insert Row Below", lambda: self.insert_row(rr + 1))
        add("Delete Row", lambda: self.delete_row(rr), r >= 0 and self.n_rows > 1)
        menu.append(Gtk.SeparatorMenuItem())
        add("Insert Column Left", lambda: self.insert_col(c))
        add("Insert Column Right", lambda: self.insert_col(c + 1))
        add("Delete Column", lambda: self.delete_col(c), self.n_cols > 1)
        menu.append(Gtk.SeparatorMenuItem())
        if self.visible_rows > 0:
            add("Show All Rows", lambda: self.set_visible_rows(0))
        else:
            add("Show 10 Rows with Scroll Bar", lambda: self.set_visible_rows(10), self.n_rows > 10)
        add("Paste Data Here  (Ctrl+V)", lambda: self._paste_clipboard_at(cell if cell is not None else (0, 0)))
        add("Caption…", lambda: open_figure_caption_dialog(self))
        add("Table Options…", self.open_options_dialog)
        add("Delete Table", lambda: self.canvas.remove_selected_boxes(self))
        menu.show_all()
        menu.attach_to_widget(self, None)
        menu.popup_at_pointer(event)

    # ------------------------------------------------------------ dialogs
    def open_options_dialog(self):
        toplevel = self.get_toplevel()
        parent = toplevel if isinstance(toplevel, Gtk.Window) else None
        dlg = Gtk.Dialog(title="Table Options", transient_for=parent, flags=0)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_APPLY, Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)

        content = dlg.get_content_area()
        grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        for side in ("start", "end", "top", "bottom"):
            getattr(grid, f"set_margin_{side}")(12)
        content.add(grid)

        name_entry = Gtk.Entry(text=self.name)
        name_entry.set_activates_default(True)
        name_entry.set_tooltip_text("Used in math boxes, e.g. name(2, 1). Not shown on the sheet.")
        cap_entry = Gtk.Entry(text=self.title)
        cap_entry.set_activates_default(True)
        cap_entry.set_placeholder_text("optional – shown above the table")
        rows_spin = Gtk.SpinButton.new_with_range(1, 500, 1)
        rows_spin.set_value(self.n_rows)
        cols_spin = Gtk.SpinButton.new_with_range(1, 26, 1)
        cols_spin.set_value(self.n_cols)
        limit_chk = Gtk.CheckButton(label="Show only")
        limit_chk.set_active(self.visible_rows > 0)
        shown_spin = Gtk.SpinButton.new_with_range(1, 500, 1)
        shown_spin.set_value(self.visible_rows if self.visible_rows > 0 else min(10, max(1, self.n_rows)))
        shown_spin.set_sensitive(self.visible_rows > 0)
        limit_chk.connect("toggled", lambda b: shown_spin.set_sensitive(b.get_active()))
        shown_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        shown_box.pack_start(limit_chk, False, False, 0)
        shown_box.pack_start(shown_spin, False, False, 0)
        shown_box.pack_start(Gtk.Label(label="rows, with a scroll bar"), False, False, 0)
        err_lbl = Gtk.Label()
        err_lbl.set_xalign(0.0)
        help_lbl = Gtk.Label()
        help_lbl.set_xalign(0.0)
        help_lbl.set_line_wrap(True)
        help_lbl.set_max_width_chars(52)
        help_lbl.set_markup(
            "<small>Use in any math box:\n"
            "  <tt>name(i, j)</tt> – cell in row i, column j (1-based)\n"
            "  <tt>Header</tt> – a column's values as a vector (e.g. <tt>Re</tt>, <tt>x_1</tt>)\n"
            "  <tt>rows(name)</tt>, <tt>cols(name)</tt>, <tt>col(name, j)</tt>, <tt>row(name, i)</tt>\n"
            "  <tt>total</tt>, <tt>mean</tt>, <tt>min</tt>, <tt>max</tt>, <tt>len</tt> on a column</small>"
        )

        grid.attach(Gtk.Label(label="Table name:", xalign=0.0), 0, 0, 1, 1)
        grid.attach(name_entry, 1, 0, 1, 1)
        grid.attach(Gtk.Label(label=f"Table {self.fig_num} caption:", xalign=0.0), 0, 1, 1, 1)
        grid.attach(cap_entry, 1, 1, 1, 1)
        grid.attach(Gtk.Label(label="Rows:", xalign=0.0), 0, 2, 1, 1)
        grid.attach(rows_spin, 1, 2, 1, 1)
        grid.attach(Gtk.Label(label="Columns:", xalign=0.0), 0, 3, 1, 1)
        grid.attach(cols_spin, 1, 3, 1, 1)
        grid.attach(Gtk.Label(label="Rows shown:", xalign=0.0), 0, 4, 1, 1)
        grid.attach(shown_box, 1, 4, 1, 1)
        grid.attach(err_lbl, 0, 5, 2, 1)
        grid.attach(help_lbl, 0, 6, 2, 1)

        dlg.show_all()
        while True:
            if dlg.run() != Gtk.ResponseType.OK:
                break
            new_name = name_entry.get_text().strip().replace(" ", "_")
            if not new_name.isidentifier():
                err_lbl.set_markup("<span foreground='#d33'>Name must start with a letter and contain no symbols.</span>")
                continue
            self.name = new_name
            self.title = cap_entry.get_text().strip()
            nr, nc = int(rows_spin.get_value()), int(cols_spin.get_value())
            while self.n_cols < nc:
                self.insert_col(self.n_cols)
            while self.n_cols > nc:
                self.delete_col(self.n_cols - 1)
            while self.n_rows < nr:
                self.cells.append(["" for _ in range(self.n_cols)])
            del self.cells[nr:]
            if self.active is not None:
                self.active = (min(self.active[0], self.n_rows - 1), min(self.active[1], self.n_cols - 1))
            self.visible_rows = int(shown_spin.get_value()) if limit_chk.get_active() else 0
            self._commit_edit()
            break
        dlg.destroy()


# ============================================================================
# A4 Graph-Paper Page Canvas (SMath Studio / Mathcad Page View + Zoom + File IO)
# ============================================================================


DIGITIZER_SERIES_COLORS = [
    (0.85, 0.15, 0.15), (0.10, 0.45, 0.85), (0.10, 0.62, 0.25), (0.85, 0.50, 0.05),
    (0.55, 0.20, 0.70), (0.05, 0.60, 0.60), (0.75, 0.20, 0.55), (0.45, 0.35, 0.20),
]


def digitizer_axis_value(p, a, b, va, vb, along, log=False):
    """Data value of image point p for one axis, calibrated by the points a and b (values va,
    vb). The point is projected onto the line a→b along the direction `along` (the other
    axis), so rotated or skewed scans are handled. Returns None if the geometry is degenerate."""
    ux, uy = b[0] - a[0], b[1] - a[1]
    wx, wy = along
    det = ux * wy - uy * wx
    if abs(det) < 1e-9:
        return None
    rx, ry = p[0] - a[0], p[1] - a[1]
    s = (rx * wy - ry * wx) / det  # fraction of the way from a to b
    if log:
        if va <= 0 or vb <= 0:
            return None
        return 10 ** (math.log10(va) + s * (math.log10(vb) - math.log10(va)))
    return va + s * (vb - va)


class PlotDigitizer(Gtk.Dialog):
    NO_ENTER_APPLY = True  # Enter is used while typing calibration values
    """Pick data points off a picture of a graph (Tools ▸ Plot Digitizer).

    1. Load the graph: Open Image…, Paste Image (Ctrl+V), or start from a picture selected on
       the sheet.
    2. Calibrate: click two points on the x axis (X1, X2) and two on the y axis (Y1, Y2) and type
       their values; tick 'log' for logarithmic axes.
    3. Click the data points. Drag a point to move it, right-click to delete it, arrow keys
       nudge the selected point. Several series can be collected.
    4. Insert the data into the sheet as a table (optionally with a plot), or copy it.
    """

    CAL_KEYS = ("X1", "X2", "Y1", "Y2")
    MAG = 4.0       # magnifier factor relative to the current view
    MAG_R = 70      # magnifier half-size in screen pixels

    def __init__(self, canvas, pixbuf=None):
        toplevel = canvas.get_toplevel()
        super().__init__(title="Plot Digitizer",
                         transient_for=toplevel if isinstance(toplevel, Gtk.Window) else None, flags=0)
        self.canvas = canvas
        self.pixbuf = None
        self.view_zoom = 1.0
        self.cal = {k: None for k in self.CAL_KEYS}      # image coordinates
        self.mode = "X1"                                 # X1/X2/Y1/Y2 or 'points'
        self.series = [{"name": "1", "points": []}]
        self.cur = 0
        self.sel = None                                  # selected point index
        self.drag = None
        self.pointer = None                              # pointer in image coordinates
        self._busy = False

        self.RESP_COPY, self.RESP_INSERT = 1, 2
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        self.add_button("Copy Data", self.RESP_COPY)
        self.add_button("Insert into Sheet", self.RESP_INSERT)
        self.set_default_size(1200, 820)

        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        for m in ("start", "end", "top", "bottom"):
            getattr(root, f"set_margin_{m}")(8)
        self.get_content_area().pack_start(root, True, True, 0)

        # ---------------------------------------------------------------- view
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        root.pack_start(left, True, True, 0)
        bar = Gtk.Box(spacing=6)
        left.pack_start(bar, False, False, 0)
        for label, cb, tip in (
            ("Open Image…", self._open_file, "Load a picture of the graph (PNG, JPEG, …)"),
            ("Paste Image", self._paste_image, "Paste a screenshot of the graph from the clipboard (Ctrl+V)"),
        ):
            b = Gtk.Button(label=label)
            b.set_tooltip_text(tip)
            b.connect("clicked", lambda _b, f=cb: f())
            bar.pack_start(b, False, False, 0)
        bar.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 4)
        for label, cb in (("−", lambda: self._set_zoom(self.view_zoom / 1.25)),
                          ("+", lambda: self._set_zoom(self.view_zoom * 1.25)),
                          ("Fit", self._zoom_fit), ("100 %", lambda: self._set_zoom(1.0))):
            b = Gtk.Button(label=label)
            b.connect("clicked", lambda _b, f=cb: f())
            bar.pack_start(b, False, False, 0)
        self.zoom_lbl = Gtk.Label(label="")
        bar.pack_start(self.zoom_lbl, False, False, 6)

        self.area = Gtk.DrawingArea()
        self.area.set_can_focus(True)
        self.area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
                             | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK
                             | Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.KEY_PRESS_MASK)
        self.area.connect("draw", self._on_draw)
        self.area.connect("button-press-event", self._on_press)
        self.area.connect("button-release-event", self._on_release)
        self.area.connect("motion-notify-event", self._on_motion)
        self.area.connect("leave-notify-event", self._on_leave)
        self.area.connect("scroll-event", self._on_scroll)
        self.area.connect("key-press-event", self._on_key)
        self.area.connect("realize", lambda w: w.get_window().set_cursor(
            Gdk.Cursor.new_from_name(w.get_display(), "crosshair")))
        self.sw = Gtk.ScrolledWindow()
        self.sw.add(self.area)
        self.sw.set_hexpand(True)
        self.sw.set_vexpand(True)
        self.sw.get_hadjustment().connect("value-changed", lambda *_a: self.area.queue_draw())
        self.sw.get_vadjustment().connect("value-changed", lambda *_a: self.area.queue_draw())
        left.pack_start(self.sw, True, True, 0)
        self.status = Gtk.Label(label="")
        self.status.set_xalign(0.0)
        self.status.set_line_wrap(True)
        left.pack_start(self.status, False, False, 0)
        self.coord_lbl = Gtk.Label(label="")
        self.coord_lbl.set_xalign(0.0)
        left.pack_start(self.coord_lbl, False, False, 0)

        # ---------------------------------------------------------------- panel
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        panel.set_size_request(340, -1)
        root.pack_start(panel, False, False, 0)

        def head(text):
            l = Gtk.Label()
            l.set_markup(f"<b>{text}</b>")
            l.set_xalign(0.0)
            panel.pack_start(l, False, False, 0)

        head("1  Axis calibration")
        g = Gtk.Grid(column_spacing=6, row_spacing=5)
        panel.pack_start(g, False, False, 0)
        self.cal_btn, self.cal_val, self.cal_state = {}, {}, {}
        tips = {"X1": "a point on the x axis with a known value",
                "X2": "a second point on the x axis, far from X1",
                "Y1": "a point on the y axis with a known value",
                "Y2": "a second point on the y axis, far from Y1"}
        for i, k in enumerate(self.CAL_KEYS):
            b = Gtk.ToggleButton(label=f"Pick {k}")
            b.set_tooltip_text(f"Then click {tips[k]} on the graph")
            b.connect("toggled", self._on_cal_toggled, k)
            e = Gtk.Entry()
            e.set_width_chars(9)
            e.set_placeholder_text("value")
            e.connect("changed", lambda *_a: self._refresh())
            st = Gtk.Label(label="—")
            st.set_xalign(0.0)
            g.attach(b, 0, i, 1, 1)
            g.attach(e, 1, i, 1, 1)
            g.attach(st, 2, i, 1, 1)
            self.cal_btn[k], self.cal_val[k], self.cal_state[k] = b, e, st
        self.log_x = Gtk.CheckButton(label="log x axis")
        self.log_y = Gtk.CheckButton(label="log y axis")
        for c in (self.log_x, self.log_y):
            c.connect("toggled", lambda *_a: self._refresh())
        lg = Gtk.Box(spacing=12)
        lg.pack_start(self.log_x, False, False, 0)
        lg.pack_start(self.log_y, False, False, 0)
        panel.pack_start(lg, False, False, 0)

        head("2  Data points")
        srow = Gtk.Box(spacing=6)
        panel.pack_start(srow, False, False, 0)
        srow.pack_start(Gtk.Label(label="Series:"), False, False, 0)
        self.series_combo = Gtk.ComboBoxText()
        self.series_combo.connect("changed", self._on_series_changed)
        srow.pack_start(self.series_combo, True, True, 0)
        add_s = Gtk.Button(label="+ New")
        add_s.set_tooltip_text("Start another data series (another curve on the same graph)")
        add_s.connect("clicked", lambda _b: self._new_series())
        srow.pack_start(add_s, False, False, 0)
        nrow = Gtk.Box(spacing=6)
        panel.pack_start(nrow, False, False, 0)
        nrow.pack_start(Gtk.Label(label="Name:"), False, False, 0)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_tooltip_text("Used for the table columns: x_name, y_name")
        self.name_entry.connect("changed", self._on_name_changed)
        nrow.pack_start(self.name_entry, True, True, 0)

        self.store = Gtk.ListStore(int, str, str)
        self.view = Gtk.TreeView(model=self.store)
        for i, t in enumerate(("#", "x", "y")):
            cell = Gtk.CellRendererText()
            cell.set_property("xalign", 1.0)
            col = Gtk.TreeViewColumn(t, cell, text=i)
            col.set_expand(i > 0)
            self.view.append_column(col)
        self.view.get_selection().connect("changed", self._on_list_select)
        lsw = Gtk.ScrolledWindow()
        lsw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        lsw.set_vexpand(True)
        lsw.add(self.view)
        panel.pack_start(lsw, True, True, 0)
        prow = Gtk.Box(spacing=6)
        panel.pack_start(prow, False, False, 0)
        for label, cb in (("Delete Point", self._delete_selected), ("Clear Series", self._clear_series),
                          ("Delete Series", self._delete_series)):
            b = Gtk.Button(label=label)
            b.connect("clicked", lambda _b, f=cb: f())
            prow.pack_start(b, True, True, 0)

        head("3  Output")
        orow = Gtk.Box(spacing=6)
        panel.pack_start(orow, False, False, 0)
        orow.pack_start(Gtk.Label(label="Significant digits:"), False, False, 0)
        self.sig = Gtk.SpinButton.new_with_range(2, 10, 1)
        self.sig.set_value(4)
        orow.pack_start(self.sig, False, False, 0)
        self.sort_x = Gtk.CheckButton(label="Sort points by x")
        self.sort_x.set_active(True)
        panel.pack_start(self.sort_x, False, False, 0)
        self.want_plot = Gtk.CheckButton(label="Also insert a plot of the data")
        self.want_plot.set_active(True)
        panel.pack_start(self.want_plot, False, False, 0)

        self.connect("key-press-event", self._on_dialog_key)
        self._fill_series_combo()
        if pixbuf is not None:
            self.set_pixbuf(pixbuf)
        self._refresh()

    # ------------------------------------------------------------------ image
    def set_pixbuf(self, pixbuf):
        self.pixbuf = pixbuf
        GLib.idle_add(lambda: self._zoom_fit() and False)
        self._set_mode("X1" if None in self.cal.values() else "points")

    def _open_file(self):
        dlg = Gtk.FileChooserDialog(title="Open Graph Image", parent=self, action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        flt = Gtk.FileFilter()
        flt.set_name("Image files")
        flt.add_pixbuf_formats()
        dlg.add_filter(flt)
        fname = dlg.get_filename() if dlg.run() == Gtk.ResponseType.OK else None
        dlg.destroy()
        if fname:
            try:
                self.set_pixbuf(GdkPixbuf.Pixbuf.new_from_file(fname))
            except Exception as exc:
                self.status.set_text(f"Could not open the image: {exc}")

    def _paste_image(self):
        pb = self.canvas._try_load_pixbuf_from_clipboard()
        if pb is None:
            self.status.set_text("The clipboard holds no image. Take a screenshot of the graph (or copy it) "
                                 "and press Paste Image again.")
            return
        self.set_pixbuf(pb)

    def _set_zoom(self, z):
        if self.pixbuf is None:
            return
        self.view_zoom = max(0.05, min(16.0, z))
        self.area.set_size_request(int(self.pixbuf.get_width() * self.view_zoom),
                                   int(self.pixbuf.get_height() * self.view_zoom))
        self.zoom_lbl.set_text(f"{self.view_zoom * 100:.0f} %")
        self.area.queue_draw()

    def _zoom_fit(self):
        if self.pixbuf is None:
            return
        aw = max(100, self.sw.get_allocated_width() - 20)
        ah = max(100, self.sw.get_allocated_height() - 20)
        self._set_zoom(min(aw / self.pixbuf.get_width(), ah / self.pixbuf.get_height(), 4.0))

    # ------------------------------------------------------------ calibration
    def _set_mode(self, mode):
        self.mode = mode
        self._busy = True
        for k, b in self.cal_btn.items():
            b.set_active(k == mode)
        self._busy = False
        self._refresh()

    def _on_cal_toggled(self, btn, key):
        if self._busy:
            return
        if btn.get_active():
            self._set_mode(key)
        elif self.mode == key:
            self._set_mode("points")

    def calibrated(self):
        if None in self.cal.values():
            return False
        return all(self._cal_value(k) is not None for k in self.CAL_KEYS)

    def _cal_value(self, k):
        txt = self.cal_val[k].get_text().strip().replace(",", ".").replace("−", "-")
        try:
            v = float(eval(txt.replace("^", "**"), {"__builtins__": {}}, {"pi": math.pi}))
            return v if math.isfinite(v) else None
        except Exception:
            return None

    def to_data(self, p):
        """Image point -> (x, y) in data units, or None before calibration is complete."""
        if not self.calibrated():
            return None
        X1, X2, Y1, Y2 = (self.cal[k] for k in self.CAL_KEYS)
        y_dir = (Y2[0] - Y1[0], Y2[1] - Y1[1])
        x_dir = (X2[0] - X1[0], X2[1] - X1[1])
        x = digitizer_axis_value(p, X1, X2, self._cal_value("X1"), self._cal_value("X2"), y_dir,
                                 self.log_x.get_active())
        y = digitizer_axis_value(p, Y1, Y2, self._cal_value("Y1"), self._cal_value("Y2"), x_dir,
                                 self.log_y.get_active())
        if x is None or y is None:
            return None
        return x, y

    # ---------------------------------------------------------------- series
    def _fill_series_combo(self):
        self._busy = True
        self.series_combo.remove_all()
        for i, s in enumerate(self.series):
            self.series_combo.append(str(i), f"{s['name']}  ({len(s['points'])} pts)")
        self.series_combo.set_active(self.cur)
        self.name_entry.set_text(self.series[self.cur]["name"])
        self._busy = False

    def _on_series_changed(self, combo):
        if self._busy or combo.get_active() < 0:
            return
        self.cur = combo.get_active()
        self.sel = None
        self.name_entry.set_text(self.series[self.cur]["name"])
        self._refresh()

    def _on_name_changed(self, entry):
        if self._busy:
            return
        name = "".join(ch for ch in entry.get_text().strip() if ch.isalnum() or ch == "_")
        self.series[self.cur]["name"] = name or str(self.cur + 1)
        self._busy = True
        it = self.series_combo.get_model().get_iter(Gtk.TreePath(self.cur))
        self.series_combo.get_model().set_value(
            it, 0, f"{self.series[self.cur]['name']}  ({len(self.series[self.cur]['points'])} pts)")
        self._busy = False

    def _new_series(self):
        k = len(self.series) + 1
        names = {s["name"] for s in self.series}
        while str(k) in names:
            k += 1
        self.series.append({"name": str(k), "points": []})
        self.cur = len(self.series) - 1
        self.sel = None
        self._fill_series_combo()
        self._set_mode("points")

    def _delete_series(self):
        if len(self.series) == 1:
            self._clear_series()
            return
        del self.series[self.cur]
        self.cur = max(0, self.cur - 1)
        self.sel = None
        self._fill_series_combo()
        self._refresh()

    def _clear_series(self):
        self.series[self.cur]["points"].clear()
        self.sel = None
        self._refresh()

    def _delete_selected(self):
        pts = self.series[self.cur]["points"]
        if self.sel is not None and 0 <= self.sel < len(pts):
            del pts[self.sel]
            self.sel = min(self.sel, len(pts) - 1) if pts else None
            self._refresh()

    # ------------------------------------------------------------ mouse/keys
    def _img(self, ex, ey):
        return ex / self.view_zoom, ey / self.view_zoom

    def _nearest(self, ip, max_screen_px=8):
        best, bd = None, None
        for i, (px, py) in enumerate(self.series[self.cur]["points"]):
            d = math.hypot((px - ip[0]) * self.view_zoom, (py - ip[1]) * self.view_zoom)
            if d <= max_screen_px and (bd is None or d < bd):
                best, bd = i, d
        return best

    def _on_press(self, widget, event):
        if self.pixbuf is None:
            return True
        widget.grab_focus()
        ip = self._img(event.x, event.y)
        if not (0 <= ip[0] <= self.pixbuf.get_width() and 0 <= ip[1] <= self.pixbuf.get_height()):
            return True
        if event.button == 3:
            i = self._nearest(ip, 12)
            if i is not None:
                self.sel = i
                self._delete_selected()
            return True
        if event.button != 1:
            return True
        if self.mode in self.CAL_KEYS:
            k = self.mode
            self.cal[k] = ip
            nxt = [c for c in self.CAL_KEYS if self.cal[c] is None]
            self._set_mode(nxt[0] if nxt else "points")
            if not self.cal_val[k].get_text().strip():
                self.cal_val[k].grab_focus()
            return True
        i = self._nearest(ip)
        if i is None:
            self.series[self.cur]["points"].append(list(ip))
            i = len(self.series[self.cur]["points"]) - 1
        self.sel = i
        self.drag = i
        self._refresh()
        return True

    def _on_release(self, widget, event):
        self.drag = None
        return True

    def _on_motion(self, widget, event):
        if self.pixbuf is None:
            return True
        ip = self._img(event.x, event.y)
        self.pointer = ip
        if self.drag is not None and event.state & Gdk.ModifierType.BUTTON1_MASK:
            self.series[self.cur]["points"][self.drag] = list(ip)
            self._refresh(keep_list=True)
        d = self.to_data(ip)
        self.coord_lbl.set_text(
            f"pixel ({ip[0]:.1f}, {ip[1]:.1f})" + (f"   →   x = {d[0]:.6g},  y = {d[1]:.6g}" if d else ""))
        self.area.queue_draw()
        return True

    def _on_leave(self, widget, event):
        self.pointer = None
        self.area.queue_draw()
        return False

    def _on_scroll(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            up = event.direction == Gdk.ScrollDirection.UP or (
                event.direction == Gdk.ScrollDirection.SMOOTH and event.delta_y < 0)
            self._set_zoom(self.view_zoom * (1.2 if up else 1 / 1.2))
            return True
        return False

    def _on_key(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        pts = self.series[self.cur]["points"]
        steps = {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1)}
        if keyname in steps and self.sel is not None and self.sel < len(pts):
            k = (5.0 if event.state & Gdk.ModifierType.SHIFT_MASK else 1.0) / self.view_zoom
            dx, dy = steps[keyname]
            pts[self.sel][0] += dx * k
            pts[self.sel][1] += dy * k
            self._refresh(keep_list=True)
            return True
        if keyname in ("Delete", "BackSpace", "KP_Delete"):
            self._delete_selected()
            return True
        if keyname == "Escape" and self.mode in self.CAL_KEYS:
            self._set_mode("points")
            return True
        return False

    def _on_dialog_key(self, widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK and Gdk.keyval_name(event.keyval) in ("v", "V"):
            focus = self.get_focus()
            if not isinstance(focus, Gtk.Entry):
                self._paste_image()
                return True
        return False

    def _on_list_select(self, selection):
        if self._busy:
            return
        model, it = selection.get_selected()
        if it is not None:
            self.sel = model[it][0] - 1
            self.area.queue_draw()

    # --------------------------------------------------------------- drawing
    def _draw_overlay(self, cr, tx, ty, scale_px):
        """Calibration marks and points; tx/ty map image -> screen coordinates."""
        for k in self.CAL_KEYS:
            p = self.cal[k]
            if p is None:
                continue
            col = (0.85, 0.15, 0.15) if k.startswith("X") else (0.10, 0.40, 0.85)
            sx, sy = tx(p[0]), ty(p[1])
            cr.set_source_rgb(*col)
            cr.set_line_width(1.5)
            cr.move_to(sx - 9, sy)
            cr.line_to(sx + 9, sy)
            cr.move_to(sx, sy - 9)
            cr.line_to(sx, sy + 9)
            cr.stroke()
            cr.arc(sx, sy, 5, 0, 2 * math.pi)
            cr.stroke()
            cr.move_to(sx + 7, sy - 7)
            cr.set_font_size(12)
            cr.show_text(k)
        for si, s in enumerate(self.series):
            col = DIGITIZER_SERIES_COLORS[si % len(DIGITIZER_SERIES_COLORS)]
            for i, (px, py) in enumerate(s["points"]):
                sx, sy = tx(px), ty(py)
                cr.set_source_rgb(1, 1, 1)
                cr.arc(sx, sy, 5.2, 0, 2 * math.pi)
                cr.fill()
                cr.set_source_rgb(*col)
                cr.arc(sx, sy, 4, 0, 2 * math.pi)
                cr.fill() if si == self.cur else cr.stroke()
                if si == self.cur and i == self.sel:
                    cr.set_line_width(1.5)
                    cr.arc(sx, sy, 8, 0, 2 * math.pi)
                    cr.stroke()

    def _on_draw(self, widget, cr):
        w, h = widget.get_allocated_width(), widget.get_allocated_height()
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.paint()
        if self.pixbuf is None:
            cr.set_source_rgb(1, 1, 1)
            cr.set_font_size(15)
            cr.move_to(20, 34)
            cr.show_text("Open a picture of a graph, or paste a screenshot (Ctrl+V).")
            return False
        z = self.view_zoom
        cr.save()
        cr.scale(z, z)
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        if z > 2:
            cr.get_source().set_filter(cairo.FILTER_NEAREST)
        cr.paint()
        cr.restore()
        self._draw_overlay(cr, lambda x: x * z, lambda y: y * z, z)

        # magnifier in a corner of the visible part, away from the pointer
        if self.pointer is not None:
            hv, vv = self.sw.get_hadjustment().get_value(), self.sw.get_vadjustment().get_value()
            vw, vh = self.sw.get_allocated_width(), self.sw.get_allocated_height()
            R = self.MAG_R
            ppx, ppy = self.pointer[0] * z, self.pointer[1] * z
            cx = hv + vw - R - 24 if ppx - hv < vw / 2 else hv + R + 10
            cy = vv + R + 10 if ppy - vv > vh / 2 else vv + vh - R - 24
            m = z * self.MAG
            cr.save()
            cr.rectangle(cx - R, cy - R, 2 * R, 2 * R)
            cr.clip()
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.paint()
            cr.save()
            cr.translate(cx - self.pointer[0] * m, cy - self.pointer[1] * m)
            cr.scale(m, m)
            Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
            cr.get_source().set_filter(cairo.FILTER_NEAREST)
            cr.paint()
            cr.restore()
            self._draw_overlay(cr, lambda x: cx + (x - self.pointer[0]) * m,
                               lambda y: cy + (y - self.pointer[1]) * m, m)
            cr.set_source_rgba(0, 0, 0, 0.8)
            cr.set_line_width(1)
            cr.move_to(cx - R, cy + 0.5)
            cr.line_to(cx + R, cy + 0.5)
            cr.move_to(cx + 0.5, cy - R)
            cr.line_to(cx + 0.5, cy + R)
            cr.stroke()
            cr.restore()
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.set_line_width(2)
            cr.rectangle(cx - R, cy - R, 2 * R, 2 * R)
            cr.stroke()
        return False

    # ----------------------------------------------------------- refreshing
    def _refresh(self, keep_list=False):
        for k in self.CAL_KEYS:
            p = self.cal[k]
            self.cal_state[k].set_text("—" if p is None else f"({p[0]:.0f}, {p[1]:.0f}) px")
        pts = self.series[self.cur]["points"]
        self._busy = True
        if keep_list and len(self.store) == len(pts):
            for i, p in enumerate(pts):
                d = self.to_data(p)
                self.store[i][1] = f"{d[0]:.5g}" if d else "—"
                self.store[i][2] = f"{d[1]:.5g}" if d else "—"
        else:
            self.store.clear()
            for i, p in enumerate(pts):
                d = self.to_data(p)
                self.store.append([i + 1, f"{d[0]:.5g}" if d else "—", f"{d[1]:.5g}" if d else "—"])
        if self.sel is not None and self.sel < len(self.store):
            path = Gtk.TreePath(self.sel)
            self.view.get_selection().select_path(path)
            self.view.scroll_to_cell(path, None, False, 0, 0)
        self._busy = False
        it = self.series_combo.get_active_iter()
        if it is not None:
            self.series_combo.get_model().set_value(
                it, 0, f"{self.series[self.cur]['name']}  ({len(pts)} pts)")
        if self.pixbuf is None:
            msg = "Step 1: open a picture of the graph or paste a screenshot (Ctrl+V)."
        elif self.mode in self.CAL_KEYS:
            what = "x axis" if self.mode.startswith("X") else "y axis"
            msg = (f"Step 2: click point {self.mode} — a point on the {what} whose value you know "
                   f"(e.g. a labelled tick mark), then type its value. Ctrl+scroll zooms.")
        elif not self.calibrated():
            missing = [k for k in self.CAL_KEYS if self.cal[k] is None or self._cal_value(k) is None]
            msg = "Step 2: calibration incomplete — " + ", ".join(
                f"{k} {'not picked' if self.cal[k] is None else 'needs a value'}" for k in missing) + "."
        else:
            msg = ("Step 3: click the data points. Drag a point to move it, right-click to delete it, "
                   "arrow keys nudge the selected point; '+ New' starts another series.")
        self.status.set_text(msg)
        self.area.queue_draw()

    # --------------------------------------------------------------- output
    def results(self):
        """[(name, [(x, y), …]), …] for the series that have points (data units)."""
        out = []
        for s in self.series:
            pts = [self.to_data(p) for p in s["points"]]
            pts = [p for p in pts if p is not None]
            if self.sort_x.get_active():
                pts.sort(key=lambda p: p[0])
            if pts:
                out.append((s["name"], pts))
        return out

    def as_text(self):
        sig = int(self.sig.get_value())
        res = self.results()
        heads, cols = [], []
        for name, pts in res:
            heads += [f"x_{name}", f"y_{name}"]
            cols += [[f"{p[0]:.{sig}g}" for p in pts], [f"{p[1]:.{sig}g}" for p in pts]]
        n = max((len(c) for c in cols), default=0)
        lines = ["\t".join(heads)] + ["\t".join(c[i] if i < len(c) else "" for c in cols) for i in range(n)]
        return "\n".join(lines)


class MathCanvas(Gtk.ScrolledWindow):
    # Standard A4 Portrait dimensions at 96 DPI: 210 mm × 297 mm = 794 × 1123 px
    A4_WIDTH = 794
    A4_HEIGHT = 1123
    PAGE_MARGIN = 40  # ~10.5 mm printable margin guide
    MINOR_GRID = 20
    MAJOR_GRID = 100

    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.boxes = []
        self.selected_box = None
        self.selected_boxes = []
        self.rubberband_active = False
        self.rb_start_x = 0.0
        self.rb_start_y = 0.0
        self.rb_curr_x = 0.0
        self.rb_curr_y = 0.0
        self.rb_base_selection = []
        self._group_drag_origins = {}
        # Sheet insertion cursor (crosshair), in logical page coordinates
        self.cursor_x = 60
        self.cursor_y = 60
        self.show_grid = True
        self.theme_name = "light"
        self.active_text_style = "normal"
        self.zoom = 1.0
        self.num_pages = 1
        self.on_toc_updated = None
        self.on_zoom_changed = None
        self.current_file_path = None

        # Outer workspace desk backdrop that centers the A4 page and draws its drop shadow
        self.desk_box = Gtk.EventBox()
        self.desk_box.set_can_focus(False)
        self.desk_box.set_app_paintable(True)
        self.desk_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.SCROLL_MASK)
        self.desk_box.connect("draw", self.on_draw_desk)
        self.desk_box.connect("button-press-event", self.on_desk_button_press)
        self.desk_box.connect("scroll-event", self.on_scroll_zoom)

        # The A4 Sheet itself, centered horizontally with desk margins
        self.event_box = Gtk.EventBox()
        self.event_box.set_halign(Gtk.Align.CENTER)
        self.event_box.set_valign(Gtk.Align.START)
        self.event_box.set_margin_top(28)
        self.event_box.set_margin_bottom(36)
        self.event_box.set_margin_start(28)
        self.event_box.set_margin_end(28)
        self.event_box.set_can_focus(False)
        self.event_box.set_app_paintable(True)
        self.event_box.set_size_request(self.A4_WIDTH, self.A4_HEIGHT)
        self.event_box.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.SCROLL_MASK
        )
        self.event_box.connect("draw", self.on_draw_grid)
        self.event_box.connect_after("draw", self.on_draw_rubberband)
        self.event_box.connect("button-press-event", self.on_canvas_button_press)
        self.event_box.connect("motion-notify-event", self.on_canvas_motion_notify)
        self.event_box.connect("button-release-event", self.on_canvas_button_release)
        self.event_box.connect("key-press-event", self.on_canvas_key_press)
        self.event_box.connect("scroll-event", self.on_scroll_zoom)

        self.fixed = Gtk.Fixed()
        self.fixed.set_can_focus(False)
        self.fixed.set_size_request(self.A4_WIDTH, self.A4_HEIGHT)
        self.event_box.add(self.fixed)

        self.desk_box.add(self.event_box)
        self.add(self.desk_box)

        self._dummy_vadj = Gtk.Adjustment()
        self._dummy_hadj = Gtk.Adjustment()
        self._locked_vy = None
        self._locked_hx = None
        self._disable_focus_autoscroll()
        self.connect("realize", lambda _w: self._disable_focus_autoscroll())
        self.connect("map", lambda _w: self._disable_focus_autoscroll())

    def _disable_focus_autoscroll(self):
        """Disconnect GTK Container focus adjustments so focus changes never scroll the page."""
        viewport = self.get_child()
        for container in (self, viewport, self.desk_box, self.event_box, self.fixed):
            if isinstance(container, Gtk.Container):
                container.set_focus_vadjustment(self._dummy_vadj)
                container.set_focus_hadjustment(self._dummy_hadj)

    def _restore_locked_scroll(self):
        vadj = self.get_vadjustment()
        hadj = self.get_hadjustment()
        if vadj is not None and self._locked_vy is not None and abs(vadj.get_value() - self._locked_vy) > 0.5:
            vadj.set_value(self._locked_vy)
        if hadj is not None and self._locked_hx is not None and abs(hadj.get_value() - self._locked_hx) > 0.5:
            hadj.set_value(self._locked_hx)
        return False

    def focus_without_scroll(self, widget):
        """Grab focus on widget while preserving horizontal and vertical scroll positions."""
        self._disable_focus_autoscroll()
        vadj = self.get_vadjustment()
        hadj = self.get_hadjustment()
        vy = vadj.get_value() if vadj is not None else None
        hx = hadj.get_value() if hadj is not None else None
        self._locked_vy = vy
        self._locked_hx = hx
        if widget is not None and widget.get_can_focus():
            widget.grab_focus()
        self._restore_locked_scroll()
        GLib.idle_add(self._restore_locked_scroll, priority=GLib.PRIORITY_HIGH_IDLE)
        GLib.idle_add(self._restore_locked_scroll, priority=GLib.PRIORITY_DEFAULT_IDLE)

    # ------------------------------------------------------------------------
    # Multi-Page Management & Sheet Zoom (Zoom In, Zoom Out, Reset, Ctrl+Scroll)
    # ------------------------------------------------------------------------

    @property
    def total_height(self) -> int:
        return self.num_pages * self.A4_HEIGHT

    def set_num_pages(self, n: int):
        new_count = max(1, int(n))
        if new_count == self.num_pages:
            return
        self.num_pages = new_count
        zw = int(round(self.A4_WIDTH * self.zoom))
        zh = int(round(self.total_height * self.zoom))
        self.event_box.set_size_request(zw, zh)
        self.fixed.set_size_request(zw, zh)
        vadj = self.get_vadjustment()
        if vadj is not None and vadj.get_upper() < zh + 64:
            vadj.set_upper(zh + 64)
        self.desk_box.queue_draw()
        self.event_box.queue_draw()

    def add_page(self):
        self.set_num_pages(self.num_pages + 1)

    def trim_empty_pages(self) -> int:
        """Remove empty pages at the end of the worksheet; returns how many were removed.
        Leftover empty (unedited) boxes on those pages are discarded too."""
        def keeps(b):
            return not b.is_empty() or getattr(b, "editing", False)
        last = 0
        for b in self.boxes:
            if keeps(b):
                bh = getattr(b, "logical_h", 28)
                last = max(last, (int(b.y) + max(1, int(bh)) - 1) // self.A4_HEIGHT)
        needed = max(1, last + 1)
        removed = self.num_pages - needed
        if removed <= 0:
            return 0
        limit = needed * self.A4_HEIGHT
        for b in [b for b in self.boxes if not keeps(b) and b.y >= limit]:
            self.boxes.remove(b)
            if b in self.selected_boxes:
                self.selected_boxes.remove(b)
            if self.selected_box is b:
                self.selected_box = None
            self.fixed.remove(b)
        self.set_num_pages(needed)
        return removed

    def ensure_page_for_y(self, y_bottom: int):
        needed_pages = max(1, int(math.ceil(max(1, y_bottom) / float(self.A4_HEIGHT))))
        if needed_pages > self.num_pages:
            self.set_num_pages(needed_pages)

    def _ensure_y_visible(self, y: int, h: int = 36):
        """Scroll viewport if needed so logical y..y+h is visible."""
        vadj = self.get_vadjustment()
        if vadj is None:
            return
        page_size = vadj.get_page_size()
        if page_size <= 1:
            return
        cur_val = vadj.get_value()
        top_px = 28 + y * self.zoom
        bot_px = 28 + (y + h + 28) * self.zoom

        target_val = None
        if bot_px > cur_val + page_size:
            target_val = bot_px - page_size
        elif top_px < cur_val:
            target_val = max(0.0, top_px - 24)

        if target_val is not None:
            self._locked_vy = target_val
            vadj.set_value(target_val)
            GLib.idle_add(self._restore_locked_scroll, priority=GLib.PRIORITY_HIGH_IDLE)
            GLib.idle_add(self._restore_locked_scroll, priority=GLib.PRIORITY_DEFAULT_IDLE)

    def set_zoom(self, new_zoom: float):
        clamped = round(max(0.40, min(2.50, float(new_zoom))), 2)
        if abs(clamped - self.zoom) < 1e-4:
            return
        self.zoom = clamped
        zw = int(round(self.A4_WIDTH * self.zoom))
        zh = int(round(self.total_height * self.zoom))
        self.event_box.set_size_request(zw, zh)
        self.fixed.set_size_request(zw, zh)
        for b in self.boxes:
            b.update_layout()
            self.fixed.move(b, int(round(b.x * self.zoom)), int(round(b.y * self.zoom)))
        self.desk_box.queue_draw()
        self.event_box.queue_draw()
        if callable(self.on_zoom_changed):
            self.on_zoom_changed(self.zoom)

    def zoom_in(self):
        self.set_zoom(self.zoom + 0.10)

    def zoom_out(self):
        self.set_zoom(self.zoom - 0.10)

    def reset_zoom(self):
        self.set_zoom(1.0)

    def on_scroll_zoom(self, _widget, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self.zoom_in()
                return True
            if event.direction == Gdk.ScrollDirection.DOWN:
                self.zoom_out()
                return True
        return False

    def notify_toc_changed(self):
        if callable(self.on_toc_updated):
            self.on_toc_updated()

    def get_toc_headings(self):
        heading_styles = ("title", "subtitle", "heading1", "heading2", "heading3")
        headings = [
            b
            for b in self.boxes
            if isinstance(b, TextBox) and b.style_name in heading_styles
        ]
        return sorted(headings, key=lambda b: (b.y // 10, b.x))

    def renumber_headings(self):
        """Number Heading 1/2/3 boxes as 1, 1.1, 1.1.1 in reading order."""
        counters = [0, 0, 0]
        for b in self.get_toc_headings():
            level = HEADING_LEVELS.get(b.style_name)
            if level is None:
                continue
            counters[level - 1] += 1
            for i in range(level, 3):
                counters[i] = 0
            b.set_heading_number(".".join(str(c) for c in counters[:level]))

    def toggle_text_format(self, attr: str, fallback_box=None) -> bool:
        """Toggle bold / underline on the selected text boxes (all on when any is off)."""
        targets = [b for b in self.selected_boxes if isinstance(b, TextBox) and b in self.boxes]
        if fallback_box is not None and fallback_box not in targets:
            targets = [fallback_box]
        if not targets:
            return False
        on = not all(getattr(tb, attr) for tb in targets)
        for tb in targets:
            tb.set_format(**{attr: on})
        cp = getattr(self, "undo_checkpoint", None)
        if callable(cp):
            cp()
        return True

    def set_style_for_text_boxes(self, style_name: str, fallback_box=None):
        targets = [b for b in self.selected_boxes if isinstance(b, TextBox) and b in self.boxes]
        if fallback_box is not None and fallback_box not in targets:
            targets = [fallback_box]
        for tb in targets:
            tb.set_style_name(style_name)
        self.notify_toc_changed()

    def insert_symbol(self, sym: str):
        """Symbols pane: insert into the text box being edited/selected, else into a math box."""
        sel = self.selected_box
        if isinstance(sel, TextBox) and sel in self.boxes:
            if not sel.editing:
                sel.start_editing()
            sel.text = sel.text[: sel.cursor_pos] + sym + sel.text[sel.cursor_pos :]
            sel.cursor_pos += len(sym)
            sel.update_layout()
            self.focus_without_scroll(sel)
            return
        self.get_active_or_new_box().insert_char(sym)

    def insert_unit(self, name: str):
        """Units list: insert a unit into the math box being edited (or a new one)."""
        self.get_active_or_new_box().insert_unit(name)

    def get_toc_figures(self):
        figs = [
            b
            for b in self.boxes
            if isinstance(b, (PlotBox, ImageBox, DrawingBox))
        ]
        return sorted(figs, key=lambda b: (b.y // 20, b.x))

    def scroll_to_box(self, box):
        self.select_box(box)
        vadj = self.get_vadjustment()
        if vadj is not None:
            page_size = vadj.get_page_size()
            target_y = max(0.0, float(box.y * self.zoom + 28 - 40))
            max_y = max(0.0, vadj.get_upper() - page_size)
            clamped_target = min(target_y, max_y)
            self._locked_vy = clamped_target
            vadj.set_value(clamped_target)

    def exit_box_and_move_down(self, box):
        x = box.x
        logical_h = getattr(box, "logical_h", max(int(box.get_allocation().height / self.zoom), 28))
        page_idx = max(0, box.y // self.A4_HEIGHT)
        page_bottom = (page_idx + 1) * self.A4_HEIGHT
        usable_bottom = page_bottom - self.PAGE_MARGIN - 28

        if box.is_empty():
            raw_next_y = box.y + self.MINOR_GRID
            if raw_next_y > usable_bottom:
                if page_idx + 1 >= self.num_pages:
                    self.set_num_pages(page_idx + 2)
                next_y = round(((page_idx + 1) * self.A4_HEIGHT + self.PAGE_MARGIN + 10) / 10) * 10
            else:
                next_y = raw_next_y
            self.move_box(box, x, next_y)
            self.focus_without_scroll(box)
            self._ensure_y_visible(next_y, 36)
            return

        raw_next_y = round((box.y + logical_h + 10) / 10) * 10
        if raw_next_y > usable_bottom:
            if page_idx + 1 >= self.num_pages:
                self.set_num_pages(page_idx + 2)
            next_y = round(((page_idx + 1) * self.A4_HEIGHT + self.PAGE_MARGIN + 10) / 10) * 10
        else:
            next_y = raw_next_y

        box.stop_editing()

        for other in self.boxes:
            if other is not box and abs(other.y - next_y) <= 12 and abs(other.x - x) <= 40:
                self.select_box(other)
                other.start_editing()
                self._ensure_y_visible(other.y, getattr(other, "logical_h", 36))
                return

        new_box = self.create_box(x, next_y, edit=True)
        self._ensure_y_visible(new_box.y, getattr(new_box, "logical_h", 36))

    # ------------------------------------------------------------------------
    # Sheet insertion cursor (text-editor style: click to place, type to insert,
    # Enter pushes everything below down by one line)
    # ------------------------------------------------------------------------

    LINE_H = 20  # one "line" on the sheet = one minor grid step
    CURSOR_STEP = 10

    def set_sheet_cursor(self, x, y, scroll=False):
        self.cursor_x = int(max(0, min(self.A4_WIDTH - 20, round(x / 10) * 10)))
        self.cursor_y = int(max(0, min(self.total_height - 10, round(y / 10) * 10)))
        if scroll:
            self._ensure_y_visible(self.cursor_y, self.LINE_H)
        self.event_box.queue_draw()

    def sheet_cursor_visible(self) -> bool:
        return not self.selected_boxes and not any(b.editing for b in self.boxes)

    def insert_line_at_cursor(self):
        """Move every box at or below the cursor down one line (like Enter in a text editor)."""
        dy = self.LINE_H
        movers = [b for b in self.boxes if b.y >= self.cursor_y]
        if movers:
            lowest = max(b.y + getattr(b, "logical_h", 28) for b in movers)
            self.ensure_page_for_y(lowest + dy + 10)
            for b in sorted(movers, key=lambda bb: -bb.y):
                self.move_box(b, b.x, b.y + dy)
        self.ensure_page_for_y(self.cursor_y + dy + 40)
        self.set_sheet_cursor(self.cursor_x, self.cursor_y + dy, scroll=True)
        if movers:
            self.recalculate_worksheet()

    def remove_line_at(self, top) -> bool:
        """Remove the empty line [top, top+LINE_H) and pull everything below it up."""
        dy = self.LINE_H
        if top < 0:
            return False
        # The line must not contain the top of any box (like deleting an empty text line)
        if any(top <= b.y < top + dy for b in self.boxes):
            return False
        movers = [b for b in self.boxes if b.y >= top + dy]
        for b in sorted(movers, key=lambda bb: bb.y):
            self.move_box(b, b.x, b.y - dy)
        if movers:
            self.recalculate_worksheet()
        return True

    def handle_sheet_cursor_key(self, event) -> bool:
        if event.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK):
            return False
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ("Return", "KP_Enter"):
            self.insert_line_at_cursor()
            return True
        if keyname == "BackSpace":
            if self.remove_line_at(self.cursor_y - self.LINE_H):
                self.set_sheet_cursor(self.cursor_x, self.cursor_y - self.LINE_H, scroll=True)
            return True
        if keyname == "Delete":
            self.remove_line_at(self.cursor_y)
            return True
        moves = {
            "Up": (0, -self.CURSOR_STEP), "Down": (0, self.CURSOR_STEP),
            "Left": (-self.CURSOR_STEP, 0), "Right": (self.CURSOR_STEP, 0),
        }
        if keyname in moves:
            mx, my = moves[keyname]
            if my > 0:
                self.ensure_page_for_y(self.cursor_y + my + 40)
            self.set_sheet_cursor(self.cursor_x + mx, self.cursor_y + my, scroll=True)
            return True
        if keyname == "Home":
            self.set_sheet_cursor(self.PAGE_MARGIN + 20, self.cursor_y)
            return True
        uni = Gdk.keyval_to_unicode(event.keyval)
        ch = chr(uni) if uni else ""
        if ch and ch.isprintable() and ch != " ":
            # Start a new math box at the cursor and type the character into it
            box = self.create_box(self.cursor_x, self.cursor_y, edit=True)
            box.on_key_press(box, event)
            return True
        return False

    def draw_sheet_cursor(self, cr):
        if not self.sheet_cursor_visible():
            return
        t = THEMES[self.theme_name]
        cx, cy = self.cursor_x + 0.5, self.cursor_y + 0.5
        arm = 7.0
        cr.save()
        cr.scale(self.zoom, self.zoom)
        cr.set_source_rgb(*t["error"])
        cr.set_line_width(max(1.2, 1.6 / self.zoom))
        cr.move_to(cx - arm, cy)
        cr.line_to(cx + arm, cy)
        cr.move_to(cx, cy - arm)
        cr.line_to(cx, cy + arm)
        cr.stroke()
        cr.restore()

    def on_draw_desk(self, widget, cr):
        theme = THEMES[self.theme_name]
        alloc = widget.get_allocation()
        cr.set_source_rgb(*theme["desk_bg"])
        cr.rectangle(0, 0, alloc.width, alloc.height)
        cr.fill()

        page_alloc = self.event_box.get_allocation()
        px, py = self.event_box.translate_coordinates(widget, 0, 0) or (28, 28)
        cr.save()
        cr.set_source_rgba(*theme["page_shadow"])
        cr.rectangle(px + 6, py + 6, page_alloc.width, page_alloc.height)
        cr.fill()
        cr.restore()
        return False

    def draw_page_background(self, cr, pango_ctx, theme=None, show_grid=None, for_export=False):
        if theme is None:
            theme = THEMES[self.theme_name]
        if show_grid is None:
            show_grid = self.show_grid
        w, h = self.A4_WIDTH, self.A4_HEIGHT
        page_count = 1 if for_export else self.num_pages
        total_h = page_count * h

        cr.set_source_rgb(*theme["canvas_bg"])
        cr.rectangle(0, 0, w, total_h)
        cr.fill()

        if show_grid:
            cr.set_source_rgb(*theme["grid_minor"])
            cr.set_line_width(1.0)
            for x in range(0, w, self.MINOR_GRID):
                if x % self.MAJOR_GRID != 0:
                    cr.move_to(x + 0.5, 0)
                    cr.line_to(x + 0.5, total_h)
            for y in range(0, total_h, self.MINOR_GRID):
                if y % self.MAJOR_GRID != 0:
                    cr.move_to(0, y + 0.5)
                    cr.line_to(w, y + 0.5)
            cr.stroke()

            cr.set_source_rgb(*theme["grid_major"])
            cr.set_line_width(1.0)
            for x in range(0, w, self.MAJOR_GRID):
                cr.move_to(x + 0.5, 0)
                cr.line_to(x + 0.5, total_h)
            for y in range(0, total_h, self.MAJOR_GRID):
                cr.move_to(0, y + 0.5)
                cr.line_to(w, y + 0.5)
            cr.stroke()

            if not for_export:
                m = self.PAGE_MARGIN
                cr.save()
                cr.set_source_rgb(*theme["margin_guide"])
                cr.set_line_width(1.0)
                cr.set_dash([5.0, 5.0])
                for p in range(page_count):
                    y_off = p * h
                    cr.rectangle(m + 0.5, y_off + m + 0.5, w - 2 * m - 1.0, h - 2 * m - 1.0)
                cr.stroke()
                cr.restore()

        if not for_export:
            for p in range(page_count):
                y_off = p * h
                if p > 0:
                    # Draw distinct page-break divider band between A4 pages
                    cr.save()
                    cr.set_source_rgb(*theme["desk_bg"])
                    cr.rectangle(0, y_off - 4, w, 8)
                    cr.fill()
                    cr.set_source_rgb(*theme["page_border"])
                    cr.set_line_width(1.5)
                    cr.move_to(0, y_off - 4)
                    cr.line_to(w, y_off - 4)
                    cr.move_to(0, y_off + 4)
                    cr.line_to(w, y_off + 4)
                    cr.stroke()
                    cr.restore()

                lbl_txt = f"Page {p + 1} / {page_count}  —  A4 (210 × 297 mm)"
                layout, lw, _, _ = MathRenderer._make_layout(pango_ctx, lbl_txt, 0.65)
                cr.save()
                cr.set_source_rgb(*theme["page_border"])
                cr.move_to(w - lw - 12, y_off + h - 22)
                PangoCairo.show_layout(cr, layout)
                cr.restore()

            cr.save()
            cr.set_source_rgb(*theme["page_border"])
            cr.set_line_width(1.5)
            cr.rectangle(0.75, 0.75, w - 1.5, total_h - 1.5)
            cr.stroke()
            cr.restore()

    def on_draw_grid(self, widget, cr):
        cr.save()
        cr.scale(self.zoom, self.zoom)
        self.draw_page_background(cr, widget.get_pango_context(), for_export=False)
        cr.restore()
        return False

    def _next_spawn_y(self) -> int:
        if not self.boxes:
            return 60
        lowest = max(b.y + getattr(b, "logical_h", 36) for b in self.boxes)
        cand_y = round((lowest + 20) / 10) * 10
        page_idx = cand_y // self.A4_HEIGHT
        page_bottom = (page_idx + 1) * self.A4_HEIGHT
        if cand_y > page_bottom - self.PAGE_MARGIN - 30:
            cand_y = round(((page_idx + 1) * self.A4_HEIGHT + self.PAGE_MARGIN + 10) / 10) * 10
        self.ensure_page_for_y(cand_y + 60)
        return cand_y

    def _insert_point(self):
        """Where Insert commands put a new object: right below the selected box, or at the
        red sheet cursor when nothing is selected. Returns (x, y)."""
        sel = self.selected_box if self.selected_box in self.boxes else None
        if sel is not None:
            if sel.is_empty() and isinstance(sel, MathBox):
                return sel.x, sel.y
            h = getattr(sel, "logical_h", 28) - getattr(sel, "strip_h", 0)
            return sel.x, int(math.ceil((sel.y + h + 10) / 10.0) * 10)
        return self.cursor_x, self.cursor_y

    def _take_insert_point(self):
        """_insert_point(), also discarding an empty selected math box it replaces."""
        x, y = self._insert_point()
        sel = self.selected_box if self.selected_box in self.boxes else None
        if isinstance(sel, MathBox) and sel.is_empty():
            sel.editing = False
            self.remove_box(sel)
        return x, y

    def _make_room(self, box):
        """Push everything below a newly inserted box down so nothing overlaps it, and put
        the sheet cursor under it."""
        h = getattr(box, "logical_h", 28) - getattr(box, "strip_h", 0)
        bottom = box.y + h + 10
        movers = [b for b in self.boxes if b is not box and b.y >= box.y]
        if movers:
            first = min(b.y for b in movers)
            if first < bottom:
                shift = int(math.ceil((bottom - first) / 10.0) * 10)
                lowest = max(b.y + getattr(b, "logical_h", 28) for b in movers)
                self.ensure_page_for_y(lowest + shift + 10)
                for b in sorted(movers, key=lambda bb: -bb.y):
                    self.move_box(b, b.x, b.y + shift)
                self.recalculate_worksheet()
        self.cursor_y = int(math.ceil(bottom / 10.0) * 10)
        self._ensure_y_visible(box.y, h)

    def create_link_box(self, x, y, url="", text="") -> "LinkBox":
        lb = LinkBox(self, max(0, int(round(x / 10) * 10)), max(10, int(round(y / 10) * 10)), url=url, text=text)
        self.ensure_page_for_y(lb.y + lb.logical_h + 20)
        self.boxes.append(lb)
        self.fixed.put(lb, int(round(lb.x * self.zoom)), int(round(lb.y * self.zoom)))
        lb.show_all()
        return lb

    def create_arrow_box(self, x1, y1, x2, y2, color="auto", width=1.8, head=True) -> "ArrowBox":
        ab = ArrowBox(self, float(x1), float(y1), float(x2), float(y2), color=color, width=width, head=head)
        self.ensure_page_for_y(ab.y + ab.logical_h + 20)
        self.boxes.append(ab)
        self.fixed.put(ab, int(round(ab.x * self.zoom)), int(round(ab.y * self.zoom)))
        ab.show_all()
        return ab

    def insert_arrow(self, head=True):
        """Insert ▸ Arrow / Line: a 120-wide arrow (or plain line) pointing right at the cursor."""
        x, y = self._take_insert_point()
        x = max(ArrowBox.PAD, min(self.A4_WIDTH - 140, x))
        yc = y + ArrowBox.PAD
        ab = self.create_arrow_box(x, yc, x + 120, yc, head=head)
        self.select_box(ab)
        self._make_room(ab)
        self.focus_without_scroll(ab)
        return ab

    def insert_link(self):
        """Insert ▸ Link…: ask for the address and text, then place it at the cursor."""
        res = ask_link(self.get_toplevel())
        if res is None or not (res[0] or res[1]):
            return None
        x, y = self._take_insert_point()
        lb = self.create_link_box(x, y, url=res[0], text=res[1])
        self.select_box(lb)
        self._make_room(lb)
        self.focus_without_scroll(lb)
        return lb

    def insert_text_box(self, style_name="normal"):
        x, y = self._take_insert_point()
        tb = self.create_text_box(x if style_name == "normal" else 60, y, style_name=style_name, edit=True)
        self._make_room(tb)
        return tb

    def insert_math_box(self):
        x, y = self._take_insert_point()
        mb = self.create_box(x, y, edit=True)
        self._make_room(mb)
        return mb

    def create_box(self, x, y, edit=True) -> MathBox:
        snap_x = max(10, min(self.A4_WIDTH - 60, round(x / 10) * 10))
        snap_y = max(10, round(y / 10) * 10)
        self.ensure_page_for_y(snap_y + 40)
        box = MathBox(self, snap_x, snap_y)
        self.boxes.append(box)
        self.fixed.put(box, int(round(box.x * self.zoom)), int(round(box.y * self.zoom)))
        box.show_all()
        self.select_box(box)
        if edit:
            box.start_editing()
        return box

    def create_text_box(self, x, y, style_name="normal", text="", edit=True) -> TextBox:
        snap_x = max(10, min(self.A4_WIDTH - 80, round(x / 10) * 10))
        if style_name in HEADING_X:
            snap_x = HEADING_X[style_name]
        snap_y = max(10, round(y / 10) * 10)
        self.ensure_page_for_y(snap_y + 40)
        tbox = TextBox(self, snap_x, snap_y, style_name=style_name, text=text)
        self.boxes.append(tbox)
        self.fixed.put(tbox, int(round(tbox.x * self.zoom)), int(round(tbox.y * self.zoom)))
        tbox.show_all()
        self.select_box(tbox)
        if edit:
            tbox.start_editing()
        self.renumber_headings()
        self.notify_toc_changed()
        return tbox

    def create_plot_box(self, x=0, y=None, **kwargs) -> PlotBox:
        at_cursor = y is None
        if at_cursor:
            y = self._take_insert_point()[1]
        snap_y = max(10, round(y / 10) * 10)
        pbox = PlotBox(self, 0, snap_y, **kwargs)
        self.ensure_page_for_y(snap_y + pbox.plot_h + 20)
        pbox.x = max(0, (self.A4_WIDTH - pbox.plot_w) // 2)
        self.boxes.append(pbox)
        self.fixed.put(pbox, int(round(pbox.x * self.zoom)), int(round(pbox.y * self.zoom)))
        pbox.show_all()
        self.select_box(pbox)
        self.recalculate_worksheet()
        self.notify_toc_changed()
        if at_cursor:
            self._make_room(pbox)
        return pbox

    def create_image_box(self, pixbuf: GdkPixbuf.Pixbuf, x=None, y=None, title="", width=None, height=None) -> ImageBox:
        at_cursor = y is None
        if at_cursor:
            y = self._take_insert_point()[1]
        snap_y = max(10, round(y / 10) * 10)
        ibox = ImageBox(self, 0, snap_y, pixbuf=pixbuf, title=title, width=width, height=height)
        self.ensure_page_for_y(snap_y + ibox.box_h + 20)
        ibox.x = max(0, (self.A4_WIDTH - ibox.box_w) // 2) if x is None else int(x)
        self.boxes.append(ibox)
        self.fixed.put(ibox, int(round(ibox.x * self.zoom)), int(round(ibox.y * self.zoom)))
        ibox.show_all()
        self.select_box(ibox)
        self.recalculate_worksheet()
        self.notify_toc_changed()
        if at_cursor:
            self._make_room(ibox)
        return ibox

    def create_drawing_box(self, x=None, y=None, width=420, height=240, title="", shapes=None, edit=True,
                           background=True):
        at_cursor = y is None
        if at_cursor:
            y = self._take_insert_point()[1]
        snap_y = max(10, round(y / 10) * 10)
        dbox = DrawingBox(self, 0, snap_y, width=width, height=height, title=title, shapes=shapes,
                          background=background)
        self.ensure_page_for_y(snap_y + dbox.logical_h + 20)
        dbox.x = max(0, (self.A4_WIDTH - dbox.logical_w) // 2) if x is None else int(x)
        self.boxes.append(dbox)
        self.fixed.put(dbox, int(round(dbox.x * self.zoom)), int(round(dbox.y * self.zoom)))
        dbox.show_all()
        self.select_box(dbox)
        self.recalculate_worksheet()
        self.notify_toc_changed()
        if edit:
            dbox.start_editing()
        if at_cursor:
            self._make_room(dbox)
        return dbox

    def _next_table_name(self) -> str:
        used = {b.name for b in self.boxes if isinstance(b, TableBox)}
        k = 1
        while f"T{k}" in used:
            k += 1
        return f"T{k}"

    def create_table_box(self, x=60, y=None, name=None, headers=None, cells=None, rows=4, cols=3, edit=True, title="") -> TableBox:
        at_cursor = y is None
        if at_cursor:
            y = self._take_insert_point()[1]
        snap_x = max(10, min(self.A4_WIDTH - 120, round(x / 10) * 10))
        snap_y = max(10, round(y / 10) * 10)
        tbox = TableBox(
            self, snap_x, snap_y, name=name or self._next_table_name(),
            headers=headers, cells=cells, rows=rows, cols=cols, title=title,
        )
        self.ensure_page_for_y(snap_y + tbox.logical_h + 20)
        self.boxes.append(tbox)
        self.fixed.put(tbox, int(round(tbox.x * self.zoom)), int(round(tbox.y * self.zoom)))
        tbox.show_all()
        self.select_box(tbox)
        if edit:
            tbox.start_editing((-1, 0))
        self.recalculate_worksheet()
        if at_cursor:
            self._make_room(tbox)
        return tbox

    def paste_table_text(self) -> bool:
        """Ctrl+V with tabular text on the clipboard (e.g. copied from a plot digitizer or a
        spreadsheet): fill the table being edited / selected from its current cell, or create
        a new table. Returns False when the clipboard has no table or a text/math box is being
        edited (the box then pastes the text itself)."""
        clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        text = clip.wait_for_text() if clip is not None else None
        parsed = parse_tabular_text(text or "")
        if parsed is None:
            return False
        headers, rows = parsed
        editing = [b for b in self.boxes if b.editing]
        target = None
        if editing:
            if len(editing) == 1 and isinstance(editing[0], TableBox):
                target = editing[0]
            else:
                return False
        elif isinstance(self.selected_box, TableBox) and self.selected_box in self.boxes:
            target = self.selected_box
        if target is not None:
            target.paste_grid(headers, rows, at=target.active if target.editing else (-1, 0))
            return True
        if headers is None:
            headers = [f"c{j + 1}" for j in range(len(rows[0]))]
        else:
            headers = [h if h.strip() else f"c{j + 1}" for j, h in enumerate(headers)]
        self.create_table_box(headers=headers, cells=rows, edit=False)
        return True

    def _try_load_pixbuf_from_clipboard(self):
        for sel_atom in (Gdk.SELECTION_CLIPBOARD, Gdk.SELECTION_PRIMARY):
            clip = Gtk.Clipboard.get(sel_atom)
            if clip is None:
                continue
            pixbuf = clip.wait_for_image()
            if pixbuf is not None:
                return pixbuf
            uris = clip.wait_for_uris()
            if uris:
                for uri in uris:
                    if uri.startswith("file://"):
                        from urllib.parse import unquote
                        fpath = unquote(uri[7:]).strip()
                        if os.path.isfile(fpath):
                            try:
                                return GdkPixbuf.Pixbuf.new_from_file(fpath)
                            except Exception:
                                pass
            txt = clip.wait_for_text()
            if txt:
                candidate = txt.strip().splitlines()[0].strip()
                if candidate.startswith("file://"):
                    from urllib.parse import unquote
                    candidate = unquote(candidate[7:]).strip()
                if os.path.isfile(candidate):
                    try:
                        return GdkPixbuf.Pixbuf.new_from_file(candidate)
                    except Exception:
                        pass
        return None

    def paste_from_clipboard(self, open_dialog_if_empty=False) -> bool:
        pixbuf = self._try_load_pixbuf_from_clipboard()
        if pixbuf is not None:
            self.create_image_box(pixbuf)
            return True

        if open_dialog_if_empty:
            return self.insert_picture_from_file()
        return False

    def insert_picture_from_file(self) -> bool:
        """Choose an image file and insert it as a picture on the sheet."""
        pb = self.choose_picture_file()
        if pb is None:
            return False
        self.create_image_box(pb)
        return True

    def choose_picture_file(self):
        """File chooser for a picture; returns its pixbuf or None."""
        toplevel = self.get_toplevel()
        parent = toplevel if isinstance(toplevel, Gtk.Window) else None
        dlg = Gtk.FileChooserDialog(title="Insert Picture from File", parent=parent,
                                    action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Insert", Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        flt = Gtk.FileFilter()
        flt.set_name("Image files (PNG, JPEG, SVG, BMP, GIF, WebP…)")
        flt.add_pixbuf_formats()
        dlg.add_filter(flt)
        flt_all = Gtk.FileFilter()
        flt_all.set_name("All files")
        flt_all.add_pattern("*")
        dlg.add_filter(flt_all)
        last_dir = getattr(self, "_last_picture_dir", None)
        if last_dir and os.path.isdir(last_dir):
            dlg.set_current_folder(last_dir)
        preview = Gtk.Image()
        preview.set_size_request(220, -1)
        dlg.set_preview_widget(preview)

        def on_update(chooser):
            fn = chooser.get_preview_filename()
            ok = False
            if fn and os.path.isfile(fn):
                try:
                    preview.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(fn, 210, 210, True))
                    ok = True
                except Exception:
                    pass
            chooser.set_preview_widget_active(ok)

        dlg.connect("update-preview", on_update)
        fname = dlg.get_filename() if dlg.run() == Gtk.ResponseType.OK else None
        dlg.destroy()
        if not fname or not os.path.isfile(fname):
            return None
        self._last_picture_dir = os.path.dirname(fname)
        try:
            return GdkPixbuf.Pixbuf.new_from_file(fname)
        except Exception as exc:
            self._show_solver_message(f"Could not open the picture:\n{fname}\n\n{exc}", title="Insert Picture")
            return None

    def insert_or_style_text_box(self, style_name: str):
        self.active_text_style = style_name
        selected_texts = [b for b in self.selected_boxes if isinstance(b, TextBox) and b in self.boxes]
        if len(selected_texts) > 1:
            for tb in selected_texts:
                tb.set_style_name(style_name)
            return selected_texts[-1]
        sel = self.selected_box
        if isinstance(sel, TextBox) and sel in self.boxes:
            sel.set_style_name(style_name)
            if not sel.editing:
                sel.start_editing()
            else:
                self.focus_without_scroll(sel)
            return sel
        if isinstance(sel, MathBox) and sel in self.boxes and sel.is_empty():
            x, y = sel.x, sel.y
            sel.editing = False
            self.remove_box(sel)
            return self.create_text_box(x, y, style_name=style_name, edit=True)
        return self.insert_text_box(style_name)

    def set_selected_boxes(self, boxes_list, primary_box=None):
        self._disable_focus_autoscroll()
        vadj = self.get_vadjustment()
        hadj = self.get_hadjustment()
        vy = vadj.get_value() if vadj is not None else None
        hx = hadj.get_value() if hadj is not None else None
        self._locked_vy = vy
        self._locked_hx = hx

        unique_boxes = []
        for b in boxes_list:
            if b in self.boxes and b not in unique_boxes:
                unique_boxes.append(b)

        self.selected_boxes = unique_boxes
        if primary_box in self.selected_boxes:
            self.selected_box = primary_box
        elif self.selected_boxes:
            self.selected_box = self.selected_boxes[-1]
        else:
            self.selected_box = None

        selected_set = set(self.selected_boxes)
        for b in list(self.boxes):
            if b not in selected_set or len(selected_set) > 1:
                if b.editing:
                    b.stop_editing()
            b.set_selected(b in selected_set)

        if not self.selected_boxes:
            toplevel = self.get_toplevel()
            if isinstance(toplevel, Gtk.Window):
                cur_focus = toplevel.get_focus()
                if cur_focus is not None and cur_focus.is_ancestor(self):
                    toplevel.set_focus(None)

        if callable(getattr(self, "on_selection_changed", None)):
            self.on_selection_changed(self.selected_box)
        self.event_box.queue_draw()

        self._restore_locked_scroll()
        GLib.idle_add(self._restore_locked_scroll, priority=GLib.PRIORITY_HIGH_IDLE)
        GLib.idle_add(self._restore_locked_scroll, priority=GLib.PRIORITY_DEFAULT_IDLE)

    def select_box(self, box):
        self.set_selected_boxes([box] if box is not None else [], primary_box=box)

    def select_all_boxes(self):
        self.set_selected_boxes(list(self.boxes))

    def set_decimal_places_for_selected(self, decimals, fallback_box=None):
        math_targets = [b for b in self.selected_boxes if isinstance(b, MathBox) and b in self.boxes]
        if not math_targets and isinstance(self.selected_box, MathBox) and self.selected_box in self.boxes:
            math_targets = [self.selected_box]
        if not math_targets and isinstance(fallback_box, MathBox) and fallback_box in self.boxes:
            math_targets = [fallback_box]
        if not math_targets:
            return
        norm_dec = None if decimals is None else max(0, min(15, int(decimals)))
        for mb in math_targets:
            mb.decimal_places = norm_dec
        self.recalculate_worksheet()
        for mb in math_targets:
            mb.update_layout()
            mb.queue_draw()
        if callable(getattr(self, "on_selection_changed", None)):
            self.on_selection_changed(self.selected_box)

    def toggle_boxed_for_selected(self, fallback_box=None, force_state=None):
        math_targets = [b for b in self.selected_boxes if isinstance(b, MathBox) and b in self.boxes]
        if not math_targets and isinstance(self.selected_box, MathBox) and self.selected_box in self.boxes:
            math_targets = [self.selected_box]
        if not math_targets and isinstance(fallback_box, MathBox) and fallback_box in self.boxes:
            math_targets = [fallback_box]
        if not math_targets:
            return
        new_state = (not all(mb.boxed for mb in math_targets)) if force_state is None else bool(force_state)
        for mb in math_targets:
            mb.boxed = new_state
            mb.queue_draw()
        if callable(getattr(self, "on_selection_changed", None)):
            self.on_selection_changed(self.selected_box)

    def handle_box_button_press(self, box, event):
        shift_or_ctrl = bool(
            event.state & (Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.CONTROL_MASK)
        )
        if shift_or_ctrl:
            if box in self.selected_boxes:
                new_sel = [b for b in self.selected_boxes if b is not box]
                self.set_selected_boxes(new_sel)
            else:
                new_sel = list(self.selected_boxes) + [box]
                self.set_selected_boxes(new_sel, primary_box=box)
        elif box in self.selected_boxes and len(self.selected_boxes) > 1:
            self.selected_box = box
            for b in self.selected_boxes:
                if b.editing:
                    b.stop_editing()
        else:
            self.select_box(box)

        self._group_drag_origins = {b: (b.x, b.y) for b in self.selected_boxes}

    def drag_box_or_group(self, box, dx: int, dy: int):
        if box in self.selected_boxes and len(self.selected_boxes) >= 1 and self._group_drag_origins:
            for b in self.selected_boxes:
                ox, oy = self._group_drag_origins.get(b, (b.x, b.y))
                new_x = round(max(0, ox + dx) / 10) * 10
                new_y = round(max(0, oy + dy) / 10) * 10
                self.move_box(b, new_x, new_y)
        else:
            ox = getattr(box, "drag_start_box_x", box.x)
            oy = getattr(box, "drag_start_box_y", box.y)
            new_x = round(max(0, ox + dx) / 10) * 10
            new_y = round(max(0, oy + dy) / 10) * 10
            self.move_box(box, new_x, new_y)

    def _alignable_selection(self):
        """Selected objects that can move sideways (headings and titles have a fixed
        indentation)."""
        out = []
        for b in self.selected_boxes:
            if b not in self.boxes:
                continue
            if isinstance(b, TextBox) and b.style_name in HEADING_X:
                continue
            out.append(b)
        return out

    def align_selected(self, side: str) -> int:
        """Align the selected objects: side 'left' lines up their left edges with the leftmost
        one, 'right' their right edges with the rightmost one. Returns how many moved."""
        targets = self._alignable_selection()
        if len(targets) < 2:
            return 0
        moved = 0
        if side == "left":
            ref = min(b.x for b in targets)
            new_x = {b: ref for b in targets}
        else:
            ref = max(b.x + getattr(b, "logical_w", 28) for b in targets)
            new_x = {b: ref - getattr(b, "logical_w", 28) for b in targets}
        for b in targets:
            if new_x[b] != b.x:
                self.move_box(b, new_x[b], b.y)
                moved += 1
        if moved:
            self.event_box.queue_draw()
            self.recalculate_worksheet()  # left-to-right order on a line can change evaluation order
        return moved

    NUDGE_STEP = 10       # arrow key: one snap step (the same grid dragging snaps to)
    NUDGE_STEP_BIG = 50   # Shift + arrow

    def nudge_selected(self, dx: int, dy: int) -> bool:
        """Move the selected objects by (dx, dy) sheet pixels (arrow keys). Returns True if
        anything was selected to move."""
        targets = [b for b in self.selected_boxes if b in self.boxes]
        if not targets:
            return False
        # Move the group as a whole: stop at the left / top edge instead of squashing it
        dx = max(dx, -min(b.x for b in targets))
        dy = max(dy, -min(b.y for b in targets))
        if dx == 0 and dy == 0:
            return True
        order = sorted(targets, key=lambda b: b.y, reverse=dy > 0)
        for b in order:
            bh = getattr(b, "logical_h", 28)
            old_y = b.y
            new_y = b.y + dy
            if dy > 0:
                self.ensure_page_for_y(new_y + bh + 40)
            self.move_box(b, b.x + dx, new_y)
            if dy < 0 and b.y >= old_y:
                # Pushed back by the page-break rule: hop to the bottom of the previous page
                page_idx = int(old_y) // self.A4_HEIGHT
                if page_idx > 0:
                    limit = page_idx * self.A4_HEIGHT - self.PAGE_MARGIN
                    self.move_box(b, b.x, int((limit - bh) // 10 * 10))
        self._nudge_scroll_into_view(self.selected_box if self.selected_box in targets else targets[0])
        self.event_box.queue_draw()
        # Re-evaluate once the key is released / repeats have settled (order of boxes matters)
        if getattr(self, "_nudge_recalc_id", None):
            GLib.source_remove(self._nudge_recalc_id)
        self._nudge_recalc_id = GLib.timeout_add(250, self._nudge_recalc)
        return True

    def _nudge_recalc(self):
        self._nudge_recalc_id = None
        self.recalculate_worksheet()
        return False

    def _nudge_scroll_into_view(self, box):
        vadj = self.get_vadjustment()
        if vadj is None or box is None:
            return
        top = box.y * self.zoom
        bottom = (box.y + getattr(box, "logical_h", 28)) * self.zoom
        v, page = vadj.get_value(), vadj.get_page_size()
        target = None
        if top < v + 20:
            target = max(0.0, top - 20)
        elif bottom > v + page - 20:
            target = min(bottom - page + 20, max(0.0, vadj.get_upper() - page))
        if target is not None:
            self._locked_vy = target
            vadj.set_value(target)

    def _page_break_y(self, y: int, h: int):
        """If an object starting at y with height h would cross the bottom margin of its
        page, return the y at the top of the next page; otherwise None."""
        usable_h = self.A4_HEIGHT - 2 * self.PAGE_MARGIN
        if h > usable_h:
            return None  # taller than a page: nothing to gain by moving it
        page_idx = max(0, int(y) // self.A4_HEIGHT)
        limit = (page_idx + 1) * self.A4_HEIGHT - self.PAGE_MARGIN
        if y + h <= limit:
            return None
        return int(math.ceil(((page_idx + 1) * self.A4_HEIGHT + self.PAGE_MARGIN) / 10.0) * 10)

    def schedule_page_breaks(self):
        if getattr(self, "_page_break_pending", False):
            return
        self._page_break_pending = True
        GLib.idle_add(self._run_page_breaks, priority=GLib.PRIORITY_DEFAULT_IDLE)

    def _run_page_breaks(self):
        self._page_break_pending = False
        self.enforce_page_breaks()
        return False

    def enforce_page_breaks(self):
        """Objects that don't fit at the bottom of a page skip to the next page; everything
        below them moves down by the same amount so the layout stays in order."""
        if getattr(self, "_dragging_any", False):
            return
        for _ in range(200):
            moved = False
            for b in sorted(self.boxes, key=lambda bb: (bb.y, bb.x)):
                bh = getattr(b, "logical_h", 28)
                new_y = self._page_break_y(b.y, bh)
                if new_y is None:
                    continue
                shift = new_y - b.y
                old_y = b.y
                movers = [o for o in self.boxes if o.y >= old_y]
                lowest = max(o.y + getattr(o, "logical_h", 28) for o in movers)
                self.ensure_page_for_y(lowest + shift + 10)
                for o in sorted(movers, key=lambda oo: -oo.y):
                    o.y = o.y + shift
                    self.fixed.move(o, int(round(o.x * self.zoom)), int(round(o.y * self.zoom)))
                moved = True
                break
            if not moved:
                break
        self.notify_toc_changed()

    def move_box(self, box, x, y):
        bw = getattr(box, "logical_w", 28)
        bh = getattr(box, "logical_h", 28)
        nb_y = self._page_break_y(y, bh)
        if nb_y is not None:
            self.ensure_page_for_y(nb_y + bh + 10)
            y = nb_y
        if isinstance(box, TextBox) and box.style_name in HEADING_X:
            clamped_x = HEADING_X[box.style_name]
        else:
            clamped_x = max(0, min(self.A4_WIDTH - bw, x))
        clamped_y = max(0, min(self.total_height - bh, y))
        box.x = clamped_x
        box.y = clamped_y
        self.fixed.move(box, int(round(clamped_x * self.zoom)), int(round(clamped_y * self.zoom)))
        if isinstance(box, (TextBox, PlotBox, ImageBox, DrawingBox)):
            self.notify_toc_changed()

    def remove_box(self, box):
        if box in self.boxes:
            self.boxes.remove(box)
            if box in self.selected_boxes:
                self.selected_boxes.remove(box)
            if self.selected_box is box:
                self.selected_box = self.selected_boxes[-1] if self.selected_boxes else None
            self.fixed.remove(box)
            self.recalculate_worksheet()
            if isinstance(box, (TextBox, PlotBox, ImageBox, DrawingBox)):
                self.notify_toc_changed()

    def remove_selected_boxes(self, fallback_box=None):
        targets = list(self.selected_boxes) if self.selected_boxes else ([fallback_box] if fallback_box else [])
        had_toc_item = False
        removed_any = False
        for b in targets:
            if b in self.boxes:
                if isinstance(b, (TextBox, PlotBox, ImageBox, DrawingBox)):
                    had_toc_item = True
                self.boxes.remove(b)
                self.fixed.remove(b)
                removed_any = True
        self.selected_boxes = [b for b in self.selected_boxes if b in self.boxes]
        self.selected_box = self.selected_boxes[-1] if self.selected_boxes else None
        if removed_any:
            self.recalculate_worksheet()
            if had_toc_item:
                self.notify_toc_changed()

    def clear_boxes(self):
        self.selected_box = None
        self.selected_boxes = []
        for b in list(self.boxes):
            self.fixed.remove(b)
        self.boxes.clear()
        self.set_num_pages(1)
        self.notify_toc_changed()
        self.event_box.queue_draw()

    def new_worksheet(self):
        self.clear_boxes()
        self.current_file_path = None
        self.create_text_box(60, 40, style_name="title", text="Untitled Worksheet", edit=True)
        self.reset_undo()

    # ------------------------------------------------------------------------
    # Undo / Redo: whole-worksheet snapshots, taken after each change settles
    # ------------------------------------------------------------------------
    UNDO_LIMIT = 100

    def reset_undo(self):
        """Forget the history (new / opened worksheet); the next checkpoint is the baseline."""
        self._undo_stack = []
        self._undo_idx = -1
        self._undo_images = {}
        self._undo_restored = False

    def _undo_snapshot(self) -> str:
        data = self.to_dict()
        data.pop("zoom", None)
        data.pop("theme", None)
        images = self.__dict__.setdefault("_undo_images", {})
        for item in data["boxes"]:
            if item.get("type") == "image" and item.get("png_b64"):
                key = "img%d" % (hash(item["png_b64"]) & 0xFFFFFFFFFFFF)
                images[key] = item["png_b64"]
                item["png_b64"] = "@" + key
        return json.dumps(data, sort_keys=True, ensure_ascii=False)

    def _undo_busy(self) -> bool:
        """True while a change is still in progress (typing in a box, dragging)."""
        for b in self.boxes:
            if getattr(b, "editing", False) or getattr(b, "dragging", False):
                return True
            if getattr(b, "grip", None) is not None:
                return True
        return False

    def undo_checkpoint(self, *_a):
        """Record the worksheet if it changed since the last recorded state."""
        if getattr(self, "_undo_restoring", False):
            return False
        if not hasattr(self, "_undo_stack"):
            self.reset_undo()
        if self._undo_busy():
            return False
        try:
            snap = self._undo_snapshot()
        except Exception:
            return False
        stack = self._undo_stack
        if self._undo_restored:
            # The restored worksheet may settle slightly (page breaks, trimming): adopt it
            self._undo_restored = False
            if 0 <= self._undo_idx < len(stack):
                stack[self._undo_idx] = snap
                return False
        if self._undo_idx >= 0 and stack[self._undo_idx] == snap:
            return False
        del stack[self._undo_idx + 1:]
        stack.append(snap)
        if len(stack) > self.UNDO_LIMIT:
            del stack[0]
        self._undo_idx = len(stack) - 1
        return False

    def _undo_finish_editing(self):
        for b in list(self.boxes):
            if getattr(b, "editing", False) and hasattr(b, "stop_editing"):
                b.stop_editing()
            for attr in ("dragging",):
                if getattr(b, attr, False):
                    setattr(b, attr, False)

    def can_undo(self) -> bool:
        return getattr(self, "_undo_idx", -1) > 0

    def can_redo(self) -> bool:
        return 0 <= getattr(self, "_undo_idx", -1) < len(getattr(self, "_undo_stack", [])) - 1

    def undo(self):
        self._undo_finish_editing()
        self.undo_checkpoint()
        if not self.can_undo():
            return False
        self._undo_idx -= 1
        self._undo_restore(self._undo_stack[self._undo_idx])
        return True

    def redo(self):
        self._undo_finish_editing()
        self.undo_checkpoint()
        if not self.can_redo():
            return False
        self._undo_idx += 1
        self._undo_restore(self._undo_stack[self._undo_idx])
        return True

    def _undo_restore(self, snap: str):
        data = json.loads(snap)
        images = getattr(self, "_undo_images", {})
        for item in data.get("boxes", []):
            ref = item.get("png_b64", "")
            if item.get("type") == "image" and ref.startswith("@"):
                item["png_b64"] = images.get(ref[1:], "")
        vadj = self.get_vadjustment()
        hadj = self.get_hadjustment()
        vpos, hpos = vadj.get_value(), hadj.get_value()
        cur = (self.cursor_x, self.cursor_y)
        path = getattr(self, "current_file_path", None)
        self._undo_restoring = True
        try:
            self.load_from_dict(data)
        finally:
            self._undo_restoring = False
        self.current_file_path = path
        self.cursor_x, self.cursor_y = cur
        self._undo_restored = True

        def _back():
            vadj.set_value(min(vpos, vadj.get_upper() - vadj.get_page_size()))
            hadj.set_value(min(hpos, hadj.get_upper() - hadj.get_page_size()))
            return False

        GLib.idle_add(_back)
        self.event_box.queue_draw()

    # ------------------------------------------------------------------------
    # Save / Save As / Open (JSON) & Export PDF (Vector Cairo PDFSurface)
    # ------------------------------------------------------------------------

    def to_dict(self) -> dict:
        serialized_boxes = []
        for b in self.boxes:
            if isinstance(b, MathBox):
                if b.is_empty():
                    continue
                serialized_boxes.append({
                    "type": "math",
                    "x": b.x,
                    "y": b.y,
                    "decimals": b.decimal_places,
                    "boxed": b.boxed,
                    "ast": serialize_math_seq(b.root),
                    **({"note": b.note} if b.note else {}),
                })
            elif isinstance(b, TextBox):
                if b.is_empty():
                    continue
                serialized_boxes.append({
                    "type": "text",
                    "x": b.x,
                    "y": b.y,
                    "style": b.style_name,
                    "text": b.text,
                    **({"bold": True} if b.bold else {}),
                    **({"underline": True} if b.underline else {}),
                })
            elif isinstance(b, PlotBox):
                serialized_boxes.append({
                    "type": "plot",
                    "x": b.x,
                    "y": b.y,
                    "width": b.plot_w,
                    "height": b.plot_h,
                    "title": b.title,
                    "func_expr": b.func_expr,
                    "discrete_data": b.discrete_data,
                    "symbol_style": b.symbol_style,
                    "series_styles": b.series_styles,
                    "connect_discrete": b.connect_discrete,
                    "x_min": b.x_min,
                    "x_max": b.x_max,
                    "y_min": b.y_min,
                    "y_max": b.y_max,
                    "x_scale": b.x_scale,
                    "y_scale": b.y_scale,
                    "show_grid": b.show_grid,
                    "show_legend": b.show_legend,
                    "x_title": b.x_title,
                    "y_title": b.y_title,
                })
            elif isinstance(b, TableBox):
                serialized_boxes.append({
                    "type": "table",
                    "x": b.x,
                    "y": b.y,
                    "name": b.name,
                    "title": b.title,
                    "headers": list(b.headers),
                    "cells": [list(r) for r in b.cells],
                    **({"visible_rows": b.visible_rows, "row_offset": b.row_offset} if b.visible_rows else {}),
                })
            elif isinstance(b, (DrawingBox, LinkBox, ArrowBox)):
                serialized_boxes.append(b.to_dict())
            elif isinstance(b, ImageBox):
                cache = getattr(b, "_png_b64_cache", None)
                if cache is not None and cache[0] is b.orig_pixbuf:
                    b64_png = cache[1]
                else:
                    ok, buf = b.orig_pixbuf.save_to_bufferv("png", [], [])
                    b64_png = base64.b64encode(buf).decode("ascii") if ok else ""
                    b._png_b64_cache = (b.orig_pixbuf, b64_png)
                serialized_boxes.append({
                    "type": "image",
                    "x": b.x,
                    "y": b.y,
                    "width": b.img_w,
                    "height": b.img_h,
                    "title": b.title,
                    "png_b64": b64_png,
                })
        return {
            "version": 1,
            "theme": self.theme_name,
            "show_grid": self.show_grid,
            "zoom": self.zoom,
            "num_pages": self.num_pages,
            "boxes": serialized_boxes,
        }

    def load_from_dict(self, data: dict):
        self.clear_boxes()
        # The theme is an app preference (View ▸ Toggle Dark / Light), not part of a worksheet
        if "show_grid" in data:
            self.show_grid = bool(data["show_grid"])
        if "num_pages" in data:
            self.set_num_pages(int(data["num_pages"]))
        if "zoom" in data:
            self.set_zoom(float(data["zoom"]))

        for item in data.get("boxes", []):
            btype = item.get("type")
            x = int(item.get("x", 60))
            y = int(item.get("y", 60))
            if btype == "math":
                mb = self.create_box(x, y, edit=False)
                mb.decimal_places = item.get("decimals", None)
                mb.boxed = bool(item.get("boxed", False))
                if item.get("note"):
                    mb.set_note(str(item["note"]))
                mb.root = deserialize_math_seq(item.get("ast", []))
                mb.cursor_seq = mb.root
                mb.cursor_idx = len(mb.root.items)
                mb.update_layout()
            elif btype == "text":
                style = item.get("style", "normal")
                text = item.get("text", "")
                if style in HEADING_LEVELS:
                    text = strip_manual_heading_number(text)
                tb = self.create_text_box(x, y, style_name=style, text=text, edit=False)
                if item.get("bold") or item.get("underline"):
                    tb.set_format(bold=item.get("bold", False), underline=item.get("underline", False))
            elif btype == "plot":
                self.create_plot_box(
                    x, y,
                    width=item.get("width", 460),
                    height=item.get("height", 275),
                    title=item.get("title", ""),
                    func_expr=item.get("func_expr", "f"),
                    discrete_data=item.get("discrete_data", ""),
                    symbol_style=item.get("symbol_style", "circle"),
                    series_symbols=item.get("series_symbols") or {},
                    series_styles=item.get("series_styles") or {},
                    connect_discrete=item.get("connect_discrete", False),
                    x_min=item.get("x_min", -6.0),
                    x_max=item.get("x_max", 6.0),
                    y_min=item.get("y_min", -1.5),
                    y_max=item.get("y_max", 1.5),
                    x_scale=item.get("x_scale", "linear"),
                    y_scale=item.get("y_scale", "linear"),
                    show_grid=item.get("show_grid", True),
                    show_legend=item.get("show_legend", True),
                    x_title=item.get("x_title", ""),
                    y_title=item.get("y_title", ""),
                )
            elif btype == "table":
                tbl = self.create_table_box(
                    x, y,
                    name=item.get("name") or None,
                    headers=item.get("headers") or None,
                    cells=item.get("cells") or None,
                    title=item.get("title", ""),
                    edit=False,
                )
                if item.get("visible_rows"):
                    tbl.row_offset = int(item.get("row_offset", 0))
                    tbl.set_visible_rows(item["visible_rows"])
            elif btype in ("arrow", "line"):
                self.create_arrow_box(item.get("x1", 60), item.get("y1", 60), item.get("x2", 180), item.get("y2", 60),
                                      color=item.get("color", "auto"), width=item.get("width", 1.8),
                                      head=(btype == "arrow"))
            elif btype == "link":
                self.create_link_box(x, y, url=item.get("url", ""), text=item.get("text", ""))
            elif btype == "drawing":
                self.create_drawing_box(
                    x=x, y=y,
                    width=item.get("width", 420),
                    height=item.get("height", 240),
                    title=item.get("title", ""),
                    shapes=item.get("shapes") or [],
                    edit=False,
                    background=bool(item.get("background", False)),
                )
            elif btype == "image":
                b64_png = item.get("png_b64", "")
                if b64_png:
                    try:
                        raw_bytes = base64.b64decode(b64_png)
                        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
                        loader.write(raw_bytes)
                        loader.close()
                        pb = loader.get_pixbuf()
                        if pb is not None:
                            self.create_image_box(
                                pb,
                                x=x,
                                y=y,
                                title=item.get("title", ""),
                                width=item.get("width"),
                                height=item.get("height"),
                            )
                    except Exception:
                        pass

        self.select_box(None)
        self.recalculate_worksheet()
        self.trim_empty_pages()
        self.notify_toc_changed()
        self.cursor_x, self.cursor_y = 60, self._next_spawn_y()
        self.desk_box.queue_draw()
        self.event_box.queue_draw()

    def save_to_file(self, filepath: str):
        self.recalculate_worksheet()
        self.trim_empty_pages()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        self.current_file_path = filepath

    def load_from_file(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_from_dict(data)
        self.current_file_path = filepath
        self.reset_undo()

    def export_pdf(self, pdf_path: str):
        """Render all A4 pages of the worksheet to a multi-page vector PDF file (210 × 297 mm = 595.28 × 841.89 pt)."""
        self.recalculate_worksheet()
        self.trim_empty_pages()
        pdf_w_pt = 595.27559
        pdf_h_pt = 841.88976
        surface = cairo.PDFSurface(pdf_path, pdf_w_pt, pdf_h_pt)
        cr = cairo.Context(surface)
        sx = pdf_w_pt / float(self.A4_WIDTH)
        sy = pdf_h_pt / float(self.A4_HEIGHT)

        # Use classic print-friendly light theme for PDF export
        export_theme = THEMES["print"]
        sorted_boxes = sorted(self.boxes, key=lambda box: (box.y, box.x))

        for page_idx in range(self.num_pages):
            page_top = page_idx * self.A4_HEIGHT
            page_bot = (page_idx + 1) * self.A4_HEIGHT

            cr.save()
            cr.scale(sx, sy)
            cr.rectangle(0, 0, self.A4_WIDTH, self.A4_HEIGHT)
            cr.clip()

            self.draw_page_background(
                cr,
                self.event_box.get_pango_context(),
                theme=export_theme,
                show_grid=False,
                for_export=True,
            )

            for b in sorted_boxes:
                if b.is_empty():
                    continue
                bh = getattr(b, "logical_h", 28)
                if b.y + bh < page_top or b.y >= page_bot:
                    continue
                cr.save()
                cr.translate(b.x, b.y - page_top)
                b.draw_content(cr, theme=export_theme, for_export=True)
                cr.restore()

            cr.restore()
            cr.show_page()

        surface.finish()

    def recalculate_worksheet(self):
        """Evaluate all MathBoxes and update PlotBoxes in top-to-bottom, left-to-right order."""
        env = {
            "sin": _dimless_fn(math.sin, "sin"),
            "cos": _dimless_fn(math.cos, "cos"),
            "tan": _dimless_fn(math.tan, "tan"),
            "asin": _dimless_fn(math.asin, "asin"),
            "acos": _dimless_fn(math.acos, "acos"),
            "atan": _dimless_fn(math.atan, "atan"),
            "sinh": _dimless_fn(math.sinh, "sinh"),
            "cosh": _dimless_fn(math.cosh, "cosh"),
            "tanh": _dimless_fn(math.tanh, "tanh"),
            "sqrt": _unit_sqrt,
            "ln": _dimless_fn(math.log, "ln"),
            "log": _dimless_fn(math.log10, "log"),
            "exp": _dimless_fn(math.exp, "exp"),
            "abs": abs,
            "_U": UNIT_VALUES,
            "pi": math.pi,
            "e": math.e,
            "inf": math.inf,
            "_smath_sum": _smath_sum,
            "_smath_int": _smath_int,
        }
        env.update(TABLE_SHEET_FUNCS)
        env.update(fluid_sheet_funcs_with_units())
        # Tables are injected before any box is evaluated, so their data can be
        # used anywhere on the sheet (above or below the table itself).
        table_vecs = []
        for tb in sorted((b for b in self.boxes if isinstance(b, TableBox)), key=lambda b: (b.y // 20, b.x)):
            st = tb.to_sheet_table()
            env[tb.name] = st
            for j, hdr in enumerate(st.headers):
                var = TableBox.header_var_name(hdr)
                if var and var not in TABLE_SHEET_FUNCS and var != tb.name:
                    env[var] = st.column(j + 1)
                    if var not in table_vecs:
                        table_vecs.append(var)
        env["_sheet_vectors"] = table_vecs
        ordered = sorted(self.boxes, key=lambda b: (b.y // 20, b.x))
        fig_counter = 0
        table_counter = 0
        for b in ordered:
            if isinstance(b, MathBox):
                res, err = evaluate_box_ast(
                    b.root,
                    env,
                    is_editing=b.editing,
                    decimals=b.decimal_places,
                )
                if b.eval_result != res or b.eval_error != err:
                    b.eval_result = res
                    b.eval_error = err
                    b.update_layout()
            elif isinstance(b, PlotBox):
                fig_counter += 1
                b.update_env(env, fig_num=fig_counter)
            elif isinstance(b, TableBox):
                table_counter += 1
                if b.fig_num != table_counter:
                    b.fig_num = table_counter
                    b.update_layout()
            elif isinstance(b, (ImageBox, DrawingBox)):
                fig_counter += 1
                old_num = getattr(b, "fig_num", None)
                b.fig_num = fig_counter
                if old_num != fig_counter:
                    b.update_layout()
        self.last_env = env
        self.renumber_headings()
        self.notify_toc_changed()

    def solve_equation_box(self, box, var: str):
        """Solve the equation in `box` for `var` and put 'var = …' box(es) right below it."""
        self.recalculate_worksheet()
        env = getattr(self, "last_env", {}) or {}
        try:
            sols, numeric = solve_equation(box.root, var, env)
        except SolveError as exc:
            self._show_solver_message(str(exc))
            return
        except Exception as exc:
            self._show_solver_message(f"The solver failed: {exc}")
            return
        if not sols:
            self._show_solver_message(f"No solution for {var} was found.")
            return

        names = [var] if len(sols) == 1 else [f"{var}_{i + 1}" for i in range(len(sols))]
        self._place_boxes_below(box, [build_solution_seq(nm, sol) for nm, sol in zip(names, sols)], show_value=True)
        if numeric:
            self._show_solver_message(
                f"{var} could not be rearranged symbolically, so it was solved numerically "
                "using the current values on the sheet.",
                info=True,
            )

    def _place_boxes_below(self, box, seqs, show_value=False):
        """Create math boxes holding `seqs` right under `box`, pushing lower boxes down."""
        top = int(round((box.y + box.logical_h + 10) / 10) * 10)
        movers = [b for b in self.boxes if b is not box and b.y >= top]
        new_boxes = []
        y = top
        for seq in seqs:
            nb = self.create_box(box.x, y, edit=False)
            nb.root = seq
            nb.cursor_seq, nb.cursor_idx = nb.root, len(nb.root.items)
            if show_value:
                nb.root.append(CharNode("="))  # removed below if it can't be evaluated yet
            nb.update_layout()
            new_boxes.append(nb)
            y = int(round((nb.y + nb.logical_h + 10) / 10) * 10)

        # Make room: push everything that was below the source box down
        shift = y - top
        if movers and shift > 0:
            lowest = max(b.y + getattr(b, "logical_h", 28) for b in movers)
            self.ensure_page_for_y(lowest + shift + 10)
            for b in sorted(movers, key=lambda bb: -bb.y):
                self.move_box(b, b.x, b.y + shift)
        self.recalculate_worksheet()
        if show_value:
            # Show the value straight away only when everything it needs is known above it
            failed = [nb for nb in new_boxes if nb.eval_error or nb.eval_result in (None, "?")]
            for nb in failed:
                if nb.root.items and isinstance(nb.root.items[-1], CharNode) and nb.root.items[-1].text == "=":
                    nb.root.items.pop()
            if failed:
                self.recalculate_worksheet()
                for nb in failed:
                    nb.update_layout()
        self.select_box(new_boxes[-1])
        return new_boxes

    # ----------------------------------------------------------- Tools ▸ Curve Fit
    def open_plot_digitizer(self):
        """Tools ▸ Plot Digitizer: pick data points off a picture of a graph."""
        sel = self.selected_box if self.selected_box in self.boxes else None
        pb = sel.orig_pixbuf if isinstance(sel, ImageBox) else None
        last = getattr(self, "_digitizer_last", None)
        dlg = PlotDigitizer(self, pb if pb is not None else (last or {}).get("pixbuf"))
        if last and (pb is None or pb is last.get("pixbuf")):
            dlg.cal = dict(last["cal"])
            for k, v in last["vals"].items():
                dlg.cal_val[k].set_text(v)
            dlg.log_x.set_active(last["log_x"])
            dlg.log_y.set_active(last["log_y"])
            dlg.series = [{"name": s["name"], "points": [list(p) for p in s["points"]]} for s in last["series"]]
            dlg.cur = 0
            dlg._fill_series_combo()
            dlg._set_mode("points" if None not in dlg.cal.values() else
                          next(k for k in dlg.CAL_KEYS if dlg.cal[k] is None))
        dlg.show_all()
        res = None
        while True:
            resp = dlg.run()
            if resp == dlg.RESP_COPY:
                if dlg.results():
                    Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(dlg.as_text(), -1)
                    dlg.status.set_text("Data copied to the clipboard (tab-separated, with headers).")
                else:
                    dlg.status.set_text("Nothing to copy yet: calibrate the axes and click some data points.")
                continue
            if resp == dlg.RESP_INSERT:
                res = dlg.results()
                if not res:
                    dlg.status.set_text("Nothing to insert yet: calibrate the axes and click some data points.")
                    continue
            break
        sig = int(dlg.sig.get_value())
        want_plot = dlg.want_plot.get_active()
        log_x, log_y = dlg.log_x.get_active(), dlg.log_y.get_active()
        self._digitizer_last = {
            "pixbuf": dlg.pixbuf, "cal": dict(dlg.cal),
            "vals": {k: dlg.cal_val[k].get_text() for k in dlg.CAL_KEYS},
            "log_x": log_x, "log_y": log_y,
            "series": [{"name": s["name"], "points": [list(p) for p in s["points"]]} for s in dlg.series],
        }
        dlg.destroy()
        if res:
            self._insert_digitized(res, sig, want_plot, log_x, log_y)

    def _insert_digitized(self, res, sig, want_plot, log_x, log_y):
        taken = set(getattr(self, "last_env", {}) or {})
        for b in self.boxes:
            if isinstance(b, TableBox):
                taken.update(h.strip() for h in b.headers)
        headers, cols, pairs = [], [], []
        for name, pts in res:
            nm = name
            if name.isdigit():  # numbered series: take the next free number (x_3, not x_12)
                k = int(name)
                while f"x_{k}" in taken or f"y_{k}" in taken:
                    k += 1
                nm = str(k)
            else:
                k = 2
                while f"x_{nm}" in taken or f"y_{nm}" in taken:
                    nm = f"{name}{k}"
                    k += 1
            taken.update((f"x_{nm}", f"y_{nm}"))
            headers += [f"x_{nm}", f"y_{nm}"]
            cols += [[f"{p[0]:.{sig}g}" for p in pts], [f"{p[1]:.{sig}g}" for p in pts]]
            pairs.append((f"x_{nm}", f"y_{nm}"))
        n = max(len(c) for c in cols)
        cells = [[c[i] if i < len(c) else "" for c in cols] for i in range(n)]
        tbl = self.create_table_box(headers=headers, cells=cells, edit=False, title="Digitized data")
        if not want_plot:
            return

        def rng(vals, log):
            return plot_axis_range(vals, log, pad_frac=0.08) or ((0.1, 10.0) if log else (0.0, 1.0))

        xs = [p[0] for _n, pts in res for p in pts]
        ys = [p[1] for _n, pts in res for p in pts]
        x0, x1 = rng(xs, log_x)
        y0, y1 = rng(ys, log_y)
        self.select_box(tbl)
        self.create_plot_box(
            title="Digitized data", func_expr="",
            discrete_data="; ".join(f"{a}, {b}" for a, b in pairs),
            x_title="x", y_title="y", x_min=x0, x_max=x1, y_min=y0, y_max=y1,
            x_scale="log" if log_x else "linear", y_scale="log" if log_y else "linear",
        )

    def open_unit_converter(self):
        """Tools ▸ Unit Converter: SI ⇄ English units, live conversion with a table of all units."""
        toplevel = self.get_toplevel()
        dlg = Gtk.Dialog(title="Unit Converter",
                         transient_for=toplevel if isinstance(toplevel, Gtk.Window) else None, flags=0)
        RESP_COPY = 1
        dlg.add_button("Copy Result", RESP_COPY)
        dlg.add_button("Close", Gtk.ResponseType.CLOSE)
        dlg.set_default_size(640, 620)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("start", "end", "top", "bottom"):
            getattr(outer, f"set_margin_{m}")(14)
        dlg.get_content_area().pack_start(outer, True, True, 0)

        grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        outer.pack_start(grid, False, False, 0)

        def lbl(text):
            l = Gtk.Label(label=text)
            l.set_xalign(0.0)
            return l

        cat_combo = Gtk.ComboBoxText()
        for c in UNIT_CATEGORIES:
            cat_combo.append(c, c)
        value_entry = Gtk.Entry()
        value_entry.set_text("1")
        value_entry.set_hexpand(True)
        value_entry.set_tooltip_text("A number or a simple expression, e.g. 2.5, 1e5, 3/4, 12*7")
        from_combo = Gtk.ComboBoxText()
        to_combo = Gtk.ComboBoxText()
        from_combo.set_hexpand(True)
        to_combo.set_hexpand(True)
        swap_btn = Gtk.Button(label="⇅ Swap")
        swap_btn.set_tooltip_text("Swap the From and To units")
        result_lbl = Gtk.Label()
        result_lbl.set_xalign(0.0)
        result_lbl.set_selectable(True)

        grid.attach(lbl("Quantity:"), 0, 0, 1, 1)
        grid.attach(cat_combo, 1, 0, 2, 1)
        grid.attach(lbl("Value:"), 0, 1, 1, 1)
        grid.attach(value_entry, 1, 1, 2, 1)
        grid.attach(lbl("From:"), 0, 2, 1, 1)
        grid.attach(from_combo, 1, 2, 1, 1)
        grid.attach(swap_btn, 2, 2, 1, 2)
        grid.attach(lbl("To:"), 0, 3, 1, 1)
        grid.attach(to_combo, 1, 3, 1, 1)
        grid.attach(lbl("Result:"), 0, 4, 1, 1)
        grid.attach(result_lbl, 1, 4, 2, 1)

        outer.pack_start(lbl("All units (click a row to convert to it):"), False, False, 0)
        store = Gtk.ListStore(str, str, str, str)
        view = Gtk.TreeView(model=store)
        for i, (title, xalign) in enumerate((("Value", 1.0), ("Unit", 0.0), ("Name", 0.0), ("System", 0.0))):
            cell = Gtk.CellRendererText()
            cell.set_property("xalign", xalign)
            col = Gtk.TreeViewColumn(title, cell, text=i)
            col.set_resizable(True)
            view.append_column(col)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        sw.add(view)
        outer.pack_start(sw, True, True, 0)

        state = {"busy": False, "result": ""}

        def parse_value():
            txt = value_entry.get_text().strip().replace("^", "**").replace("·", "*").replace("×", "*")
            if not txt:
                return None
            try:
                v = float(eval(txt, {"__builtins__": {}}, {"pi": math.pi, "π": math.pi, "sqrt": math.sqrt}))
            except Exception:
                return None
            return v if math.isfinite(v) else None

        def update(*_a):
            if state["busy"]:
                return
            cat = cat_combo.get_active_id()
            fu, tu = from_combo.get_active_id(), to_combo.get_active_id()
            store.clear()
            v = parse_value()
            if cat is None or fu is None or tu is None or v is None:
                result_lbl.set_markup('<span foreground="#c03030">Enter a number</span>' if v is None else "")
                state["result"] = ""
                return
            r = convert_unit(v, cat, fu, tu)
            state["result"] = format_unit_value(r)
            result_lbl.set_markup(
                f'<span size="x-large"><b>{GLib.markup_escape_text(state["result"])} '
                f'{GLib.markup_escape_text(tu)}</b></span>')
            for sym, name, system, _f in UNIT_CATEGORIES[cat]:
                store.append([format_unit_value(convert_unit(v, cat, fu, sym)), sym, name, system])

        def fill_units(*_a):
            cat = cat_combo.get_active_id()
            state["busy"] = True
            from_combo.remove_all()
            to_combo.remove_all()
            units = UNIT_CATEGORIES[cat]
            for sym, name, system, _f in units:
                text = f"{sym}   —   {name}  ({system})"
                from_combo.append(sym, text)
                to_combo.append(sym, text)
            from_combo.set_active(0)
            eng = [u[0] for u in units if u[2] == "English"]
            if not to_combo.set_active_id(eng[0] if eng else units[-1][0]):
                to_combo.set_active(len(units) - 1)
            state["busy"] = False
            update()

        def swap(*_a):
            fu, tu = from_combo.get_active_id(), to_combo.get_active_id()
            state["busy"] = True
            from_combo.set_active_id(tu)
            to_combo.set_active_id(fu)
            state["busy"] = False
            update()

        def row_clicked(_view, path, _col):
            to_combo.set_active_id(store[path][1])

        cat_combo.connect("changed", fill_units)
        from_combo.connect("changed", update)
        to_combo.connect("changed", update)
        value_entry.connect("changed", update)
        swap_btn.connect("clicked", swap)
        view.connect("row-activated", row_clicked)
        view.set_activate_on_single_click(True)
        cat_combo.set_active_id(getattr(self, "_unit_conv_last_cat", "Temperature"))
        if cat_combo.get_active_id() is None:
            cat_combo.set_active(0)

        dlg.show_all()
        value_entry.grab_focus()
        while True:
            resp = dlg.run()
            if resp == RESP_COPY:
                if state["result"]:
                    Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(state["result"], -1)
                continue
            break
        self._unit_conv_last_cat = cat_combo.get_active_id()
        dlg.destroy()

    def _open_theory_pdf(self, filename, parent=None):
        """Open a theory document from the docs/ folder next to this program in the default PDF viewer."""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", filename)
        if not os.path.exists(path):
            self._show_solver_message(f"The document was not found:\n\n{path}", title="Theory")
            return
        uri = GLib.filename_to_uri(path, None)
        win = parent if isinstance(parent, Gtk.Window) else self.get_toplevel()
        try:
            Gtk.show_uri_on_window(win if isinstance(win, Gtk.Window) else None, uri, Gdk.CURRENT_TIME)
        except Exception:
            try:
                import subprocess
                subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as exc:
                self._show_solver_message(f"Could not open the document: {exc}", title="Theory")

    def open_fluid_properties(self):
        """Tools ▸ Fluid Properties: ρ, cₚ, ν, α, k (and μ, Pr) of dry air or water vs temperature."""
        toplevel = self.get_toplevel()
        dlg = Gtk.Dialog(title="Fluid Properties",
                         transient_for=toplevel if isinstance(toplevel, Gtk.Window) else None, flags=0)
        RESP_INSERT, RESP_THEORY = 1, 2
        dlg.add_button("Close", Gtk.ResponseType.CLOSE)
        dlg.add_button("Insert into Sheet", RESP_INSERT)
        theory_btn = dlg.add_button("📖 Theory (PDF)", RESP_THEORY)
        theory_btn.set_tooltip_text("Open the document describing the theory, equations and data sources")
        dlg.get_action_area().set_child_secondary(theory_btn, True)
        dlg.set_default_size(760, -1)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("start", "end", "top", "bottom"):
            getattr(outer, f"set_margin_{m}")(14)
        dlg.get_content_area().pack_start(outer, True, True, 0)

        def lbl(text, xalign=0.0):
            l = Gtk.Label(label=text)
            l.set_xalign(xalign)
            return l

        grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        outer.pack_start(grid, False, False, 0)
        fluid_combo = Gtk.ComboBoxText()
        for key, f in FLUIDS.items():
            fluid_combo.append(key, f["label"])
        t_entry = Gtk.Entry()
        t_entry.set_text(getattr(self, "_fluid_last_T", "25"))
        t_entry.set_hexpand(True)
        t_unit = Gtk.ComboBoxText()
        for u in ("°C", "K", "°F"):
            t_unit.append(u, u)
        t_unit.set_active_id(getattr(self, "_fluid_last_Tu", "°C"))
        p_entry = Gtk.Entry()
        p_entry.set_text("1")
        p_unit = Gtk.ComboBoxText()
        P_UNITS = {"atm": 101325.0, "bar": 1e5, "kPa": 1e3, "Pa": 1.0, "psi": 6894.757293168}
        for u in P_UNITS:
            p_unit.append(u, u)
        p_unit.set_active_id("atm")
        p_label = lbl("Pressure:")
        range_lbl = lbl("")
        range_lbl.get_style_context().add_class("dim-label")

        grid.attach(lbl("Fluid:"), 0, 0, 1, 1)
        grid.attach(fluid_combo, 1, 0, 2, 1)
        grid.attach(lbl("Temperature:"), 0, 1, 1, 1)
        grid.attach(t_entry, 1, 1, 1, 1)
        grid.attach(t_unit, 2, 1, 1, 1)
        grid.attach(p_label, 0, 2, 1, 1)
        grid.attach(p_entry, 1, 2, 1, 1)
        grid.attach(p_unit, 2, 2, 1, 1)
        grid.attach(range_lbl, 1, 3, 2, 1)

        res = Gtk.Grid(column_spacing=16, row_spacing=6)
        res.set_margin_top(6)
        outer.pack_start(res, False, False, 0)
        for j, h in enumerate(("Property", "", "SI", "", "English", "")):
            l = Gtk.Label()
            l.set_markup(f"<b>{h}</b>")
            l.set_xalign(1.0 if j in (2, 4) else 0.0)
            res.attach(l, j, 0, 1, 1)
        value_lbls = {}
        for i, (key, name, sym, si_u, en_u, _f) in enumerate(FLUID_PROPS, start=1):
            res.attach(lbl(name), 0, i, 1, 1)
            res.attach(lbl(sym), 1, i, 1, 1)
            v_si, v_en = lbl("", 1.0), lbl("", 1.0)
            v_si.set_selectable(True)
            v_en.set_selectable(True)
            res.attach(v_si, 2, i, 1, 1)
            res.attach(lbl(si_u), 3, i, 1, 1)
            res.attach(v_en, 4, i, 1, 1)
            res.attach(lbl(en_u), 5, i, 1, 1)
            value_lbls[key] = (v_si, v_en)
        msg_lbl = lbl("")
        outer.pack_start(msg_lbl, False, False, 0)

        hint = lbl(
            "On the sheet you can also use these as functions of T in kelvin, e.g.\n"
            "ρ_water(T), cp_water(T), ν_water(T), α_water(T), k_water(T), μ_water(T), Pr_water(T)\n"
            "and the same with _air; air takes an optional pressure in Pa: ρ_air(T, p).\n"
            "Data: Incropera & DeWitt, Tables A.4 (air, tabulated at 1 bar) and A.6 (saturated water).")
        hint.set_line_wrap(True)
        hint.get_style_context().add_class("dim-label")
        outer.pack_start(hint, False, False, 4)

        state = {"vals": None}

        def num(entry):
            txt = entry.get_text().strip().replace("^", "**").replace("·", "*").replace("−", "-")
            try:
                v = float(eval(txt, {"__builtins__": {}}, {"pi": math.pi}))
                return v if math.isfinite(v) else None
            except Exception:
                return None

        def temp_K():
            v = num(t_entry)
            if v is None:
                return None
            return {"°C": v + 273.15, "K": v, "°F": (v - 32.0) * 5.0 / 9.0 + 273.15}[t_unit.get_active_id()]

        def update(*_a):
            fluid = fluid_combo.get_active_id()
            if fluid is None:
                return
            f = FLUIDS[fluid]
            gas = f["gas"]
            for w in (p_label, p_entry, p_unit):
                w.set_sensitive(gas)
            lo, hi = f["range"]
            range_lbl.set_text(f"Valid for {lo:g} – {hi:g} K  ({lo - 273.15:.2f} – {hi - 273.15:.2f} °C)"
                               + ("" if gas else ", at saturation pressure"))
            T = temp_K()
            p = P_ATM
            if gas:
                pv = num(p_entry)
                p = pv * P_UNITS[p_unit.get_active_id()] if pv is not None else None
            err = None
            vals = {}
            if T is None:
                err = "Enter a temperature."
            elif gas and (p is None or p <= 0):
                err = "Enter a positive pressure."
            else:
                try:
                    for key, *_r in FLUID_PROPS:
                        vals[key] = fluid_property(fluid, key, T, p)
                except ValueError as exc:
                    err = str(exc)
            state["vals"] = None if err else (fluid, T, vals)
            for key, name, sym, si_u, en_u, fac in FLUID_PROPS:
                v_si, v_en = value_lbls[key]
                if err:
                    v_si.set_text("—")
                    v_en.set_text("—")
                else:
                    v_si.set_text(format_unit_value(float(f"{vals[key]:.4g}")))
                    v_en.set_text(format_unit_value(float(f"{vals[key] * fac:.4g}")))
            msg_lbl.set_markup(f'<span foreground="#c03030">{GLib.markup_escape_text(err)}</span>' if err else "")

        fluid_combo.connect("changed", update)
        for w in (t_entry, p_entry):
            w.connect("changed", update)
        for w in (t_unit, p_unit):
            w.connect("changed", update)
        fluid_combo.set_active_id(getattr(self, "_fluid_last", "water"))
        if fluid_combo.get_active_id() is None:
            fluid_combo.set_active(0)

        dlg.show_all()
        t_entry.grab_focus()
        insert = None
        while True:
            resp = dlg.run()
            if resp == RESP_THEORY:
                self._open_theory_pdf('Fluid Properties - Theory and Data.pdf', dlg)
                continue
            if resp == RESP_INSERT:
                if state["vals"] is None:
                    continue
                insert = state["vals"]
            break
        self._fluid_last = fluid_combo.get_active_id()
        self._fluid_last_T = t_entry.get_text()
        self._fluid_last_Tu = t_unit.get_active_id()
        dlg.destroy()
        if insert is None:
            return
        _fluid, T, vals = insert
        names = {"rho": "ρ", "cp": "c_p", "nu": "ν", "alpha": "α", "k": "k", "mu": "μ", "Pr": "Pr"}
        def with_unit(seq, nodes):
            for nd in nodes:
                seq.append(nd)
            return seq

        seqs = [with_unit(build_value_seq("T", round(T, 6)), [UnitNode("K")])]
        seqs += [with_unit(build_value_seq(names[key], float(f"{vals[key]:.5g}")), fluid_unit_nodes(key))
                 for key, *_r in FLUID_PROPS]
        x, y = self._take_insert_point()
        anchor = self.create_box(x, y, edit=False)
        anchor.root = seqs[0]
        anchor.cursor_seq, anchor.cursor_idx = anchor.root, len(anchor.root.items)
        anchor.update_layout()
        self._place_boxes_below(anchor, seqs[1:], show_value=False)

    def open_thermal_spreading(self):
        """Tools ▸ Thermal Spreading: Lee–Song–Au spreading resistance of a heat source on a plate."""
        toplevel = self.get_toplevel()
        dlg = Gtk.Dialog(title="Thermal Spreading (Lee–Song–Au)",
                         transient_for=toplevel if isinstance(toplevel, Gtk.Window) else None, flags=0)
        RESP_INSERT, RESP_THEORY = 1, 2
        dlg.add_button("Close", Gtk.ResponseType.CLOSE)
        dlg.add_button("Insert into Sheet", RESP_INSERT)
        theory_btn = dlg.add_button("📖 Theory (PDF)", RESP_THEORY)
        theory_btn.set_tooltip_text("Open the document describing the theory, equations and data sources")
        dlg.get_action_area().set_child_secondary(theory_btn, True)
        dlg.set_default_size(720, -1)
        saved = getattr(self, "_spread_last", {})

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for m in ("start", "end", "top", "bottom"):
            getattr(outer, f"set_margin_{m}")(14)
        dlg.get_content_area().pack_start(outer, True, True, 0)

        def lbl(text, xalign=0.0, markup=False):
            l = Gtk.Label()
            (l.set_markup if markup else l.set_text)(text)
            l.set_xalign(xalign)
            return l

        grid = Gtk.Grid(column_spacing=10, row_spacing=7)
        outer.pack_start(grid, False, False, 0)
        LEN_UNITS = {"mm": 1e-3, "cm": 1e-2, "m": 1.0}
        fields = {}
        row = [0]

        def section(text):
            l = lbl(f"<b>{text}</b>", markup=True)
            l.set_margin_top(4)
            grid.attach(l, 0, row[0], 3, 1)
            row[0] += 1

        def add_field(key, label, default, units=None, unit_default=None):
            ent = Gtk.Entry()
            ent.set_text(saved.get(key, (default, None))[0])
            ent.set_hexpand(True)
            grid.attach(lbl(label), 0, row[0], 1, 1)
            grid.attach(ent, 1, row[0], 1, 1)
            if isinstance(units, dict):
                cb = Gtk.ComboBoxText()
                for u in units:
                    cb.append(u, u)
                cb.set_active_id(saved.get(key, (None, unit_default))[1] or unit_default)
                grid.attach(cb, 2, row[0], 1, 1)
                fields[key] = (ent, cb, units)
            else:
                grid.attach(lbl(units or ""), 2, row[0], 1, 1)
                fields[key] = (ent, None, None)
            row[0] += 1
            return ent

        section("Heat source (centered on the plate)")
        add_field("sl", "Length:", "10", LEN_UNITS, "mm")
        add_field("sw", "Width:", "10", LEN_UNITS, "mm")
        section("Plate / heat-sink base")
        add_field("pl", "Length:", "50", LEN_UNITS, "mm")
        add_field("pw", "Width:", "50", LEN_UNITS, "mm")
        add_field("t", "Thickness:", "5", LEN_UNITS, "mm")
        mat = Gtk.ComboBoxText()
        mat.append("custom", "Custom")
        for name, kv in SPREAD_MATERIALS:
            mat.append(name, f"{name}  ({kv:g} W/m·K)")
        grid.attach(lbl("Material:"), 0, row[0], 1, 1)
        grid.attach(mat, 1, row[0], 2, 1)
        row[0] += 1
        k_ent = add_field("k", "Conductivity k:", "167", "W/(m·K)")
        section("Cooling of the far side of the plate")
        h_mode = Gtk.ComboBoxText()
        h_mode.append("h", "Heat transfer coefficient h")
        h_mode.append("R", "Heat-sink resistance R_hs (h = 1 / (R_hs·A_plate))")
        h_mode.set_active_id(saved.get("_hmode", "h"))
        grid.attach(lbl("Specify by:"), 0, row[0], 1, 1)
        grid.attach(h_mode, 1, row[0], 2, 1)
        row[0] += 1
        h_ent = add_field("h", "h:", "1000", "W/(m²·K)")
        h_lbl = grid.get_child_at(0, row[0] - 1)
        h_unit = grid.get_child_at(2, row[0] - 1)
        add_field("Q", "Heat load Q (optional):", "10", "W")

        res = Gtk.Grid(column_spacing=16, row_spacing=4)
        res.set_margin_top(6)
        outer.pack_start(res, False, False, 0)
        OUT = [
            ("eps", "ε = a/b (source / plate radius)", ""),
            ("tau", "τ = t/b", ""),
            ("Bi", "Bi = h·b/k", ""),
            ("phi", "Φ", ""),
            ("R_sp", "Spreading resistance, average R_sp", "K/W"),
            ("R_spmax", "Spreading resistance, maximum R_sp,max", "K/W"),
            ("R_1D", "1-D conduction  t/(k·A_plate)", "K/W"),
            ("R_conv", "Convection / sink  1/(h·A_plate)", "K/W"),
            ("R_tot", "Total, average source temperature", "K/W"),
            ("R_totmax", "Total, maximum source temperature", "K/W"),
            ("dT", "Source rise above coolant, average  Q·R_tot", "K"),
            ("dTmax", "Source rise above coolant, maximum", "K"),
        ]
        out_lbls = {}
        for i, (key, text, unit) in enumerate(OUT):
            bold = key in ("R_sp", "R_tot", "dT")
            res.attach(lbl(text), 0, i, 1, 1)
            v = lbl("", 1.0)
            v.set_selectable(True)
            res.attach(v, 1, i, 1, 1)
            res.attach(lbl(unit), 2, i, 1, 1)
            out_lbls[key] = (v, bold)
        msg_lbl = lbl("")
        outer.pack_start(msg_lbl, False, False, 0)
        note = lbl("Lee, Song, Au & Moran (1995): source and plate are replaced by circles of equal area "
                   "(a = √(A_s/π), b = √(A_p/π)); λ = π + 1/(√π·ε), Φ = (tanh λτ + λ/Bi)/(1 + (λ/Bi)·tanh λτ), "
                   "ψ_avg = ½(1−ε)^1.5·Φ, ψ_max = (1−ε)·Φ/√π, R_sp = ψ/(√π·k·a).")
        note.set_line_wrap(True)
        note.set_max_width_chars(80)
        note.get_style_context().add_class("dim-label")
        outer.pack_start(note, False, False, 2)

        state = {"r": None, "busy": False}

        def num(ent):
            txt = ent.get_text().strip().replace("^", "**").replace("·", "*").replace("−", "-").replace(",", ".")
            if not txt:
                return None
            try:
                v = float(eval(txt, {"__builtins__": {}}, {"pi": math.pi}))
                return v if math.isfinite(v) else None
            except Exception:
                return None

        def si(key):
            ent, cb, units = fields[key]
            v = num(ent)
            if v is None:
                return None
            return v * units[cb.get_active_id()] if cb is not None else v

        def update(*_a):
            if state["busy"]:
                return
            byR = h_mode.get_active_id() == "R"
            h_lbl.set_text("R_hs:" if byR else "h:")
            h_unit.set_text("K/W" if byR else "W/(m²·K)")
            vals = {k: si(k) for k in fields}
            err, r = None, None
            missing = [k for k in ("sl", "sw", "pl", "pw", "t", "k", "h") if vals[k] is None]
            if missing:
                err = "Fill in all sizes, k and " + ("R_hs" if byR else "h") + "."
            else:
                h = vals["h"]
                if byR:
                    h = 1.0 / (vals["h"] * vals["pl"] * vals["pw"]) if vals["h"] > 0 else -1
                try:
                    r = lee_spreading(vals["sl"], vals["sw"], vals["pl"], vals["pw"], vals["t"], vals["k"], h,
                                      vals["Q"])
                except (ValueError, ZeroDivisionError, OverflowError) as exc:
                    err = str(exc) or "Invalid input."
            state["r"] = r
            for key, (v, bold) in out_lbls.items():
                if r is None or key not in r:
                    v.set_text("—")
                    continue
                txt = GLib.markup_escape_text(format_unit_value(float(f"{r[key]:.4g}")))
                v.set_markup(f"<b>{txt}</b>" if bold else txt)
            msg_lbl.set_markup(f'<span foreground="#c03030">{GLib.markup_escape_text(err)}</span>' if err else "")

        def mat_changed(*_a):
            mid = mat.get_active_id()
            kv = dict(SPREAD_MATERIALS).get(mid)
            if kv is not None:
                state["busy"] = True
                k_ent.set_text(f"{kv:g}")
                state["busy"] = False
            update()

        def k_edited(*_a):
            if state["busy"]:
                return
            kv = dict(SPREAD_MATERIALS).get(mat.get_active_id())
            if kv is not None and num(k_ent) != kv:
                state["busy"] = True
                mat.set_active_id("custom")
                state["busy"] = False

        for ent, cb, _u in fields.values():
            ent.connect("changed", update)
            if cb is not None:
                cb.connect("changed", update)
        k_ent.connect("changed", k_edited)
        mat.connect("changed", mat_changed)
        h_mode.connect("changed", update)
        kv0 = num(k_ent)
        mat.set_active_id(next((n for n, kv in SPREAD_MATERIALS if kv == kv0), "custom"))
        update()

        dlg.show_all()
        insert = None
        while True:
            resp = dlg.run()
            if resp == RESP_THEORY:
                self._open_theory_pdf('Thermal Spreading - Theory and Data.pdf', dlg)
                continue
            if resp == RESP_INSERT:
                if state["r"] is None:
                    continue
                insert = state["r"]
            break
        self._spread_last = {k: (e.get_text(), cb.get_active_id() if cb else None) for k, (e, cb, _u) in fields.items()}
        self._spread_last["_hmode"] = h_mode.get_active_id()
        dlg.destroy()
        if insert is None:
            return
        names = ["R_sp", "R_spmax", "R_1D", "R_conv", "R_tot", "R_totmax"] + [n for n in ("dT", "dTmax") if n in insert]
        seqs = [build_value_seq(n, float(f"{insert[n]:.5g}")) for n in names]
        x, y = self._take_insert_point()
        anchor = self.create_box(x, y, edit=False)
        anchor.root = seqs[0]
        anchor.cursor_seq, anchor.cursor_idx = anchor.root, len(anchor.root.items)
        anchor.update_layout()
        self._place_boxes_below(anchor, seqs[1:], show_value=False)

    def open_thermal_contact(self):
        """Tools ▸ Thermal Contact: CMY contact + Yovanovich air-gap joint conductance."""
        toplevel = self.get_toplevel()
        dlg = Gtk.Dialog(title="Thermal Contact Resistance (CMY + air gap)",
                         transient_for=toplevel if isinstance(toplevel, Gtk.Window) else None, flags=0)
        RESP_INSERT, RESP_THEORY = 1, 2
        dlg.add_button("Close", Gtk.ResponseType.CLOSE)
        dlg.add_button("Insert into Sheet", RESP_INSERT)
        theory_btn = dlg.add_button("📖 Theory (PDF)", RESP_THEORY)
        theory_btn.set_tooltip_text("Open the document describing the theory, equations and data sources")
        dlg.get_action_area().set_child_secondary(theory_btn, True)
        dlg.set_default_size(980, -1)
        saved = getattr(self, "_contact_last", {})

        def lbl(text, xalign=0.0, markup=False):
            l = Gtk.Label()
            (l.set_markup if markup else l.set_text)(text)
            l.set_xalign(xalign)
            return l

        cols = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        for m in ("start", "end", "top", "bottom"):
            getattr(cols, f"set_margin_{m}")(14)
        dlg.get_content_area().pack_start(cols, True, True, 0)

        # ---------------- inputs
        grid = Gtk.Grid(column_spacing=10, row_spacing=7)
        cols.pack_start(grid, True, True, 0)
        row = [0]
        state = {"busy": False, "r": None}

        def attach(label, widget, unit=None, width=1):
            if label is not None:
                grid.attach(lbl(label), 0, row[0], 1, 1)
            grid.attach(widget, 1, row[0], width, 1)
            if unit is not None:
                grid.attach(unit if isinstance(unit, Gtk.Widget) else lbl(unit), 2, row[0], 1, 1)
            row[0] += 1

        surfaces = []
        for i, (mat_def, fin_def) in enumerate((("Al", "machined"), ("Alumina", "machined")), start=1):
            hdr = lbl(f"<b>Surface {i}</b>", markup=True)
            hdr.set_margin_top(4 if i == 1 else 10)
            grid.attach(hdr, 0, row[0], 3, 1)
            row[0] += 1
            mat = Gtk.ComboBoxText()
            for key, d in CONTACT_MATERIALS.items():
                mat.append(key, d[0])
            mat.set_active_id(saved.get(f"mat{i}", mat_def))
            fin = Gtk.ComboBoxText()
            for key, d in CONTACT_FINISHES.items():
                fin.append(key, d[0])
            fin.set_active_id(saved.get(f"fin{i}", fin_def))
            sig = Gtk.Entry()
            sig.set_tooltip_text("RMS surface roughness σ, filled in from the material and finish; "
                                 "type a measured value to override")
            slope = Gtk.Entry()
            slope.set_tooltip_text("Mean absolute asperity slope m, filled in from the material and finish; "
                                   "type a measured value to override")
            attach("Material:", mat, width=2)
            attach("Finish:", fin, width=2)
            attach("Roughness σ:", sig, "µm")
            attach("Asperity slope m:", slope, "–")
            surfaces.append({"mat": mat, "fin": fin, "sig": sig, "m": slope})

        hdr = lbl("<b>Joint</b>", markup=True)
        hdr.set_margin_top(10)
        grid.attach(hdr, 0, row[0], 3, 1)
        row[0] += 1
        AREA_UNITS = {"mm²": 1e-6, "cm²": 1e-4, "in²": 6.4516e-4}
        FORCE_UNITS = {"N": 1.0, "lbf": 4.44822, "kgf": 9.80665}
        area_e, force_e = Gtk.Entry(), Gtk.Entry()
        area_e.set_text(saved.get("area", "625"))
        force_e.set_text(saved.get("force", "50"))
        area_u, force_u = Gtk.ComboBoxText(), Gtk.ComboBoxText()
        for u in AREA_UNITS:
            area_u.append(u, u)
        for u in FORCE_UNITS:
            force_u.append(u, u)
        area_u.set_active_id(saved.get("area_u", "mm²"))
        force_u.set_active_id(saved.get("force_u", "N"))
        area_e.set_hexpand(True)
        attach("Apparent contact area:", area_e, area_u)
        attach("Clamping force:", force_e, force_u)

        # cross-section + share bar
        diagram = Gtk.DrawingArea()
        diagram.set_size_request(-1, 120)
        diagram.set_margin_top(10)
        grid.attach(diagram, 0, row[0], 3, 1)
        row[0] += 1

        # ---------------- results
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cols.pack_start(right, True, True, 0)
        res = Gtk.Grid(column_spacing=14, row_spacing=6)
        right.pack_start(res, False, False, 0)
        OUT = [
            ("P", "Contact pressure", "kPa", 1e-3),
            ("ratio", "P / H_c (controlling material)", "", 1.0),
            ("h_c", "Contact conductance h_contact", "W/(m²·K)", 1.0),
            ("h_g", "Gap conductance h_gap (air)", "W/(m²·K)", 1.0),
            ("h_j", "Joint conductance h_joint", "W/(m²·K)", 1.0),
            ("R", "Total thermal resistance", "K/W", 1.0),
            ("R_area", "Area-specific resistance", "mm²·K/W", 1e6),
        ]
        out_lbls = {}
        for i, (key, text, unit, _s) in enumerate(OUT):
            res.attach(lbl(text), 0, i, 1, 1)
            v = lbl("", 1.0)
            v.set_selectable(True)
            res.attach(v, 1, i, 1, 1)
            res.attach(lbl(unit), 2, i, 1, 1)
            out_lbls[key] = v
        share_lbl = lbl("")
        right.pack_start(share_lbl, False, False, 0)
        props_lbl = lbl("")
        props_lbl.set_line_wrap(True)
        props_lbl.get_style_context().add_class("dim-label")
        right.pack_start(props_lbl, False, False, 0)
        flags_lbl = lbl("")
        flags_lbl.set_line_wrap(True)
        flags_lbl.set_max_width_chars(50)
        right.pack_start(flags_lbl, False, False, 0)
        note = lbl("h_contact = 1.25·k_s·(m/σ)·(P/H_c)^0.95 (Cooper–Mikic–Yovanovich, plastic), k_s harmonic mean, "
                   "σ = √(σ₁²+σ₂²), m = √(m₁²+m₂²), H_c = Vickers hardness of the softer material. "
                   "h_gap = k_air/Y, Y/σ = 1.184·[−ln(3.132·P/H_c)]^0.547 (Yovanovich). "
                   "Default σ, m, k, H are representative of machined surfaces; use measured values for design.")
        note.set_line_wrap(True)
        note.set_max_width_chars(50)
        note.get_style_context().add_class("dim-label")
        right.pack_start(note, False, False, 6)

        def num(ent):
            txt = ent.get_text().strip().replace("^", "**").replace("·", "*").replace("−", "-").replace(",", ".")
            try:
                v = float(eval(txt, {"__builtins__": {}}, {"pi": math.pi}))
                return v if math.isfinite(v) else None
            except Exception:
                return None

        def fill_surface(s, *_a):
            md = CONTACT_MATERIALS[s["mat"].get_active_id()]
            fd = CONTACT_FINISHES[s["fin"].get_active_id()]
            state["busy"] = True
            s["sig"].set_text(f"{md[3] * fd[1] * 1e6:.4g}")
            s["m"].set_text(f"{md[4] * fd[2]:.4g}")
            state["busy"] = False
            update()

        def update(*_a):
            if state["busy"]:
                return
            vals = []
            for s in surfaces:
                md = CONTACT_MATERIALS[s["mat"].get_active_id()]
                vals.append((md, num(s["sig"]), num(s["m"])))
            A = num(area_e)
            F = num(force_e)
            err = None
            if any(v[1] is None or v[1] <= 0 or v[2] is None or v[2] <= 0 for v in vals):
                err = "σ and m must be positive numbers."
            elif A is None or A <= 0 or F is None or F < 0:
                err = "Enter a positive area and a non-negative force."
            r = None
            if not err:
                (m1d, s1, sl1), (m2d, s2, sl2) = vals
                r = thermal_contact(m1d[1], m1d[2], s1 * 1e-6, sl1, m2d[1], m2d[2], s2 * 1e-6, sl2,
                                    A * AREA_UNITS[area_u.get_active_id()], F * FORCE_UNITS[force_u.get_active_id()])
            state["r"] = r
            for key, _t, _u, scale in OUT:
                v = out_lbls[key]
                if r is None:
                    v.set_text("—")
                    continue
                x = r[key] * scale
                txt = "∞" if math.isinf(x) else format_unit_value(float(f"{x:.4g}"))
                big = key in ("h_j", "R")
                v.set_markup(f"<b>{GLib.markup_escape_text(txt)}</b>" if big else GLib.markup_escape_text(txt))
            if r is None:
                share_lbl.set_text("")
                props_lbl.set_text("")
                flags_lbl.set_markup(f'<span foreground="#c03030">{GLib.markup_escape_text(err)}</span>')
                state["pct"] = 50.0
                diagram.queue_draw()
                return
            tot = r["h_c"] + r["h_g"]
            pct = r["h_c"] / tot * 100 if tot > 0 else 50.0
            state["pct"] = pct
            share_lbl.set_text(f"Heat path share: contact {pct:.0f} %  ·  air gap {100 - pct:.0f} %")
            soft = vals[0][0][0] if vals[0][0][2] <= vals[1][0][2] else vals[1][0][0]
            props_lbl.set_text(
                f"k_s (harmonic mean) = {r['ks']:.3g} W/(m·K)\n"
                f"combined σ = {r['sigma'] * 1e6:.3g} µm, m = {r['m']:.3g}\n"
                f"H_c = {r['Hc'] / 1e6:.4g} MPa — {soft}\n"
                f"k_air = {CONTACT_K_AIR} W/(m·K)")
            flags = []
            if r["ratio"] > 0.05:
                flags.append("⚠ P/H_c is high for this model's typical validity range (best under ~1e-2). "
                             "h_contact may be optimistic.")
            if r["gap_saturated"]:
                flags.append("⚠ Gap model saturated (contact area ≈ apparent area): gap term set to 0.")
            flags_lbl.set_markup("\n".join(
                f'<span foreground="#d99a4e">{GLib.markup_escape_text(f)}</span>' for f in flags))
            diagram.queue_draw()

        def draw_diagram(widget, cr):
            w, h = widget.get_allocated_width(), widget.get_allocated_height()
            pct = state.get("pct", 50.0)
            c1 = CONTACT_MATERIALS[surfaces[0]["mat"].get_active_id()]
            c2 = CONTACT_MATERIALS[surfaces[1]["mat"].get_active_id()]
            bar_h = 10
            body_h = h - bar_h - 26
            gap = max(4.0, 16.0 - pct / 8.0)
            mid = body_h / 2
            n = 14

            def edge(base, sign):
                pts = []
                for i in range(n + 1):
                    jit = (1.0 if i % 2 == 0 else -0.4) * gap * 0.5 * sign
                    pts.append((i * w / n, base + jit))
                return pts

            top_edge = edge(mid - gap / 2, 1)
            bot_edge = edge(mid + gap / 2, -1)
            for color, edge_pts, y_far in ((c1[5], top_edge, 0), (c2[5], bot_edge, body_h)):
                cr.set_source_rgba(*color, 0.85)
                cr.move_to(0, y_far)
                for x, y in edge_pts:
                    cr.line_to(x, y)
                cr.line_to(w, y_far)
                cr.close_path()
                cr.fill()
            cr.set_source_rgba(0.05, 0.05, 0.06, 0.6)
            cr.select_font_face("monospace")
            cr.set_font_size(11)
            cr.move_to(8, 16)
            cr.show_text(c1[0].split(" ")[0])
            cr.move_to(8, body_h - 8)
            cr.show_text(c2[0].split(" ")[0])
            # share bar
            y0 = body_h + 8
            cw = w * pct / 100.0
            cr.set_source_rgb(0.757, 0.475, 0.247)
            cr.rectangle(0, y0, cw, bar_h)
            cr.fill()
            cr.set_source_rgb(0.725, 0.745, 0.761)
            cr.rectangle(cw, y0, w - cw, bar_h)
            cr.fill()
            ctx = widget.get_style_context()
            fg = ctx.get_color(Gtk.StateFlags.NORMAL)
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.8)
            cr.set_font_size(10)
            cr.move_to(0, y0 + bar_h + 12)
            cr.show_text("contact path")
            ext = cr.text_extents("air-gap path")
            cr.move_to(w - ext.width - 2, y0 + bar_h + 12)
            cr.show_text("air-gap path")
            return False

        diagram.connect("draw", draw_diagram)
        for i, s in enumerate(surfaces, start=1):
            s["mat"].connect("changed", lambda _w, s=s: fill_surface(s))
            s["fin"].connect("changed", lambda _w, s=s: fill_surface(s))
            s["sig"].connect("changed", update)
            s["m"].connect("changed", update)
            state["busy"] = True
            sv = saved.get(f"sm{i}")
            if sv:
                s["sig"].set_text(sv[0])
                s["m"].set_text(sv[1])
            state["busy"] = False
            if not sv:
                fill_surface(s)
        for w_ in (area_e, force_e):
            w_.connect("changed", update)
        for w_ in (area_u, force_u):
            w_.connect("changed", update)
        update()

        dlg.show_all()
        insert = None
        while True:
            resp = dlg.run()
            if resp == RESP_THEORY:
                self._open_theory_pdf('Thermal Contact - Theory and Data.pdf', dlg)
                continue
            if resp == RESP_INSERT:
                if state["r"] is None:
                    continue
                insert = state["r"]
            break
        self._contact_last = {
            "area": area_e.get_text(), "force": force_e.get_text(),
            "area_u": area_u.get_active_id(), "force_u": force_u.get_active_id(),
        }
        for i, s in enumerate(surfaces, start=1):
            self._contact_last[f"mat{i}"] = s["mat"].get_active_id()
            self._contact_last[f"fin{i}"] = s["fin"].get_active_id()
            self._contact_last[f"sm{i}"] = (s["sig"].get_text(), s["m"].get_text())
        dlg.destroy()
        if insert is None:
            return
        items = [("P_c", insert["P"]), ("h_contact", insert["h_c"]), ("h_gap", insert["h_g"]),
                 ("h_joint", insert["h_j"])]
        if math.isfinite(insert["R"]):
            items.append(("R_joint", insert["R"]))
        seqs = [build_value_seq(n, float(f"{v:.5g}")) for n, v in items]
        x, y = self._take_insert_point()
        anchor = self.create_box(x, y, edit=False)
        anchor.root = seqs[0]
        anchor.cursor_seq, anchor.cursor_idx = anchor.root, len(anchor.root.items)
        anchor.update_layout()
        self._place_boxes_below(anchor, seqs[1:], show_value=False)

    def open_curve_fit(self):
        """Fit the coefficients of a model written on the sheet (e.g. y = a·x² + b·x + c)
        to two data vectors, then write the coefficients back to the sheet."""
        import sympy as sp

        self.recalculate_worksheet()
        env = getattr(self, "last_env", {}) or {}
        math_boxes = sorted((b for b in self.boxes if isinstance(b, MathBox)), key=lambda b: (b.y // 20, b.x))
        cands = fit_model_candidates([b.root for b in math_boxes], env)
        box_of = {id(b.root): b for b in math_boxes}
        vecs = fit_data_vectors(env)
        title = "Curve Fit"
        if not cands:
            self._show_solver_message(
                "Write the model on the sheet first, with the coefficients as plain letters, "
                "for example:\n\n    y = a·x² + b·x + c\n\nThen open Tools ▸ Curve Fit again.", info=True, title=title)
            return
        if not vecs:
            self._show_solver_message(
                "Define the data as vectors on the sheet first, for example\n\n"
                "    xdata1 = [0, 1, 2, 3]\n    ydata1 = [1.1, 2.9, 7.2, 13.1]\n\n"
                "or put them in a table.", info=True, title=title)
            return

        toplevel = self.get_toplevel()
        dlg = Gtk.Dialog(title=title, transient_for=toplevel if isinstance(toplevel, Gtk.Window) else None, flags=0)
        RESP_FIT, RESP_INSERT = 1, 2
        dlg.add_button("Close", Gtk.ResponseType.CANCEL)
        dlg.add_button("Fit", RESP_FIT)
        dlg.add_button("Insert into Sheet", RESP_INSERT)
        dlg.set_default_response(RESP_FIT)
        dlg.set_default_size(560, -1)
        grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        for m in ("start", "end", "top", "bottom"):
            getattr(grid, f"set_margin_{m}")(14)
        dlg.get_content_area().add(grid)
        row = [0]

        def add_row(label, widget):
            lbl = Gtk.Label(label=label)
            lbl.set_xalign(0.0)
            lbl.set_valign(Gtk.Align.START)
            grid.attach(lbl, 0, row[0], 1, 1)
            widget.set_hexpand(True)
            grid.attach(widget, 1, row[0], 1, 1)
            row[0] += 1

        model_combo = Gtk.ComboBoxText()
        for i, c in enumerate(cands):
            model_combo.append(str(i), c[0])
        sel = self.selected_box
        pick = next((i for i, c in enumerate(cands) if sel is not None and getattr(sel, "root", None) is c[1]), 0)
        model_combo.set_active(pick)
        add_row("Model:", model_combo)

        xvar_combo = Gtk.ComboBoxText()
        add_row("Independent variable:", xvar_combo)

        par_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        add_row("Coefficients to fit:", par_box)

        def vec_combo(prefer):
            cb = Gtk.ComboBoxText()
            for v in vecs:
                cb.append(v, f"{v}  ({len(env[v])} values)")
            best = next((v for v in vecs if v.lower().startswith(prefer)), vecs[0])
            cb.set_active_id(best)
            return cb

        xdata_combo = vec_combo("x")
        ydata_combo = vec_combo("y")
        add_row("X data:", xdata_combo)
        add_row("Y data:", ydata_combo)

        opt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        fn_chk = Gtk.CheckButton(label="Also define the fitted function")
        fn_chk.set_active(True)
        plot_chk = Gtk.CheckButton(label="Also insert a plot of the data and the fit")
        plot_chk.set_active(True)
        opt_box.pack_start(fn_chk, False, False, 0)
        opt_box.pack_start(plot_chk, False, False, 0)
        add_row("Insert:", opt_box)

        result_lbl = Gtk.Label()
        result_lbl.set_xalign(0.0)
        result_lbl.set_selectable(True)
        result_lbl.set_line_wrap(True)
        result_lbl.set_markup("<small>Press <b>Fit</b> to compute the coefficients.</small>")
        grid.attach(result_lbl, 0, row[0], 2, 1)

        par_widgets = {}  # name -> (check, entry)
        state = {"result": None}

        def current():
            return cands[max(0, model_combo.get_active())]

        def rebuild_params(*_a):
            label, root, out_name, expr, fn_args = current()
            names = sorted((s.name for s in expr.free_symbols), key=lambda n: (n.lower(), n))
            xv = xvar_combo.get_active_id()
            if xv not in names:
                xv = fn_args[0] if fn_args and fn_args[0] in names else ("x" if "x" in names else names[0])
            for ch in par_box.get_children():
                par_box.remove(ch)
            par_widgets.clear()
            for n in names:
                if n == xv:
                    continue
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                chk = Gtk.CheckButton(label=n)
                chk.set_size_request(70, -1)
                ent = Gtk.Entry(text="1")
                ent.set_width_chars(10)
                ent.set_tooltip_text("Starting value for the fit")
                sheet_val = env.get(n)
                fixed_ok = isinstance(sheet_val, (int, float)) and not isinstance(sheet_val, bool)
                if n == "e" and sheet_val == math.e:
                    fixed_ok = False  # built-in Euler's number, not a value set on the sheet
                # Fit everything that has no value yet; letters already defined keep their value
                chk.set_active(not fixed_ok or n in (state.get("fitted") or ()))
                if fixed_ok:
                    ent.set_text(format_number(float(sheet_val)))
                note = Gtk.Label()
                note.set_xalign(0.0)
                note.set_markup(f"<small>start value{'  (sheet value used when unticked)' if fixed_ok else ''}</small>")
                hb.pack_start(chk, False, False, 0)
                hb.pack_start(ent, False, False, 0)
                hb.pack_start(note, False, False, 0)
                par_box.pack_start(hb, False, False, 0)
                par_widgets[n] = (chk, ent)
            par_box.show_all()
            return xv

        def rebuild_xvar(*_a):
            label, root, out_name, expr, fn_args = current()
            names = sorted((s.name for s in expr.free_symbols), key=lambda n: (n.lower(), n))
            xv = fn_args[0] if fn_args and fn_args[0] in names else ("x" if "x" in names else names[0])
            xvar_combo.handler_block(xv_handler)
            xvar_combo.remove_all()
            for n in names:
                xvar_combo.append(n, n)
            xvar_combo.set_active_id(xv)
            xvar_combo.handler_unblock(xv_handler)
            rebuild_params()
            state["result"] = None

        xv_handler = xvar_combo.connect("changed", lambda *_a: (rebuild_params(), state.update(result=None)))
        model_combo.connect("changed", rebuild_xvar)
        rebuild_xvar()

        def do_fit():
            label, root, out_name, expr, fn_args = current()
            xv = xvar_combo.get_active_id()
            params, guesses, fixed = [], [], {}
            for n, (chk, ent) in par_widgets.items():
                if chk.get_active():
                    try:
                        g0 = float(eval(ent.get_text().replace("^", "**"), {"__builtins__": {}}, {"pi": math.pi, "e": math.e}))
                    except Exception:
                        raise SolveError(f"The start value of {n} is not a number.")
                    params.append(n)
                    guesses.append(g0)
                elif isinstance(env.get(n), (int, float)):
                    fixed[n] = float(env[n])
            xs = env.get(xdata_combo.get_active_id())
            ys = env.get(ydata_combo.get_active_id())
            res = run_curve_fit(expr, xv, params, guesses, fixed, xs, ys)
            res.update(model=current(), xvar=xv, fixed=fixed,
                       xdata=xdata_combo.get_active_id(), ydata=ydata_combo.get_active_id())
            state["result"] = res
            state["fitted"] = set(params)
            lines = []
            for n in params:
                v, e = res["values"][n], res["errors"][n]
                err = "" if not math.isfinite(e) else f"   ± {e:.3g}"
                lines.append(f"<tt><b>{GLib_markup_escape(n)}</b> = {v:.8g}{err}</tt>")
                par_widgets[n][1].set_text(f"{v:.8g}")
            r2 = "–" if math.isnan(res["r2"]) else f"{res['r2']:.6f}"
            lines.append(f"<small>R² = {r2}    RMSE = {res['rmse']:.4g}    points = {res['n']}</small>")
            if res.get("improved"):
                lines.append("<small><i>A better minimum was found than the one reached from the start "
                             "values; the start values were updated.</i></small>")
            if not math.isnan(res["r2"]) and res["r2"] < 0.9:
                tip = (" For a wave, add a phase and an offset: a·sin(b·x + c) + d."
                       if expr.has(sp.sin) or expr.has(sp.cos) else "")
                lines.append("<small><span foreground='#c0392b'>This is the best this model can do, and it does "
                             "not follow the data well — the model is probably missing a term." + tip +
                             "</span></small>")
            result_lbl.set_markup("\n".join(lines))

        dlg.show_all()
        while True:
            resp = dlg.run()
            if resp not in (RESP_FIT, RESP_INSERT):
                break
            try:
                if resp == RESP_FIT or state["result"] is None:
                    do_fit()
            except SolveError as exc:
                result_lbl.set_markup(f"<span foreground='#c0392b'>{GLib_markup_escape(str(exc))}</span>")
                continue
            except Exception as exc:
                result_lbl.set_markup(f"<span foreground='#c0392b'>The fit failed: {GLib_markup_escape(str(exc))}</span>")
                continue
            if resp == RESP_INSERT:
                res = state["result"]
                want_fn, want_plot = fn_chk.get_active(), plot_chk.get_active()
                dlg.destroy()
                self._insert_fit_results(res, box_of.get(id(res["model"][1])), want_fn, want_plot)
                return
        dlg.destroy()

    def _insert_fit_results(self, res, model_box, want_fn=True, want_plot=True):
        import sympy as sp

        label, root, out_name, expr, fn_args = res["model"]
        xv = res["xvar"]
        seqs = [build_value_seq(n, v) for n, v in res["values"].items()]
        fit_name = None
        if want_fn or want_plot:
            fit_name = f"{out_name}_fit" if "_" not in out_name else f"{out_name}fit"
            taken = set(getattr(self, "last_env", {}) or {})
            k = 2
            base = fit_name
            while fit_name in taken:
                fit_name = f"{base}{k}"
                k += 1
            seqs.append(build_function_seq(fit_name, [xv], expr))
        if model_box is None or model_box not in self.boxes:
            x, y = self._take_insert_point()
            model_box = self.create_box(x, y, edit=False)  # placeholder anchor
            anchor_tmp = model_box
        else:
            anchor_tmp = None
        new_boxes = self._place_boxes_below(model_box, seqs, show_value=False)
        if anchor_tmp is not None:
            self.remove_box(anchor_tmp)
        if want_plot and fit_name:
            x0, x1 = res["x_range"]
            y0, y1 = res["y_range"]
            dx = (x1 - x0) * 0.08 or 1.0
            dy = (y1 - y0) * 0.12 or 1.0
            self.select_box(new_boxes[-1])
            self.create_plot_box(
                title=f"Curve fit of {res['ydata']} vs {res['xdata']}",
                func_expr=fit_name,
                discrete_data=f"{res['xdata']}, {res['ydata']}",
                x_title=res["xdata"], y_title=res["ydata"],
                x_min=float(f"{x0 - dx:.4g}"), x_max=float(f"{x1 + dx:.4g}"),
                y_min=float(f"{y0 - dy:.4g}"), y_max=float(f"{y1 + dy:.4g}"),
            )
        self.recalculate_worksheet()

    def substitution_menu_sources(self, box) -> dict:
        ordered = sorted((b for b in self.boxes if isinstance(b, MathBox)), key=lambda b: (b.y // 20, b.x))
        return substitution_sources(box.root, [b.root for b in ordered], getattr(self, "last_env", {}) or {})

    def substitute_into_equation_box(self, box, var: str, source_root):
        """Replace `var` in the equation `box` using another equation/definition; the new
        equation is placed right below."""
        self.recalculate_worksheet()
        env = getattr(self, "last_env", {}) or {}
        try:
            results, numeric = substitute_equation(box.root, var, source_root, env)
        except SolveError as exc:
            self._show_solver_message(str(exc), title="Substitute")
            return
        except Exception as exc:
            self._show_solver_message(f"Substitution failed: {exc}", title="Substitute")
            return
        self._place_boxes_below(box, [build_equation_seq(l, r) for l, r in results])
        if numeric:
            self._show_solver_message(
                f"{var} could not be isolated symbolically, so its numeric value was substituted.",
                info=True, title="Substitute",
            )

    def _show_solver_message(self, text: str, info: bool = False, title: str = "Solve for"):
        toplevel = self.get_toplevel()
        dlg = Gtk.MessageDialog(
            transient_for=toplevel if isinstance(toplevel, Gtk.Window) else None,
            flags=0,
            message_type=Gtk.MessageType.INFO if info else Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dlg.format_secondary_text(text)
        dlg.run()
        dlg.destroy()

    def get_active_or_new_box(self) -> MathBox:
        if isinstance(self.selected_box, MathBox) and self.selected_box in self.boxes:
            if not self.selected_box.editing:
                self.selected_box.start_editing()
            return self.selected_box
        return self.insert_math_box()

    def insert_function_call(self, fn_name: str):
        box = self.get_active_or_new_box()
        for ch in fn_name:
            box.insert_char(ch)
        box.insert_parens()

    def on_desk_button_press(self, widget, event):
        if event.button == 1:
            self.select_box(None)
            return True
        return False

    def on_canvas_button_press(self, widget, event):
        if event.button == 1:
            lx = event.x / self.zoom
            ly = event.y / self.zoom
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.rubberband_active = False
                self.event_box.queue_draw()
                self.set_sheet_cursor(lx, ly)
                self.create_box(lx, ly, edit=True)
                return True
            else:
                self.set_sheet_cursor(lx, ly)
                shift_or_ctrl = bool(
                    event.state & (Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.CONTROL_MASK)
                )
                if shift_or_ctrl:
                    self.rb_base_selection = list(self.selected_boxes)
                else:
                    self.rb_base_selection = []
                    self.select_box(None)
                self.rubberband_active = True
                self.rb_start_x = lx
                self.rb_start_y = ly
                self.rb_curr_x = lx
                self.rb_curr_y = ly
                self.event_box.queue_draw()
                return True
        return False

    def on_canvas_motion_notify(self, widget, event):
        if self.rubberband_active:
            self.rb_curr_x = max(0.0, min(float(self.A4_WIDTH), event.x / self.zoom))
            self.rb_curr_y = max(0.0, min(float(self.total_height), event.y / self.zoom))

            rx1 = min(self.rb_start_x, self.rb_curr_x)
            ry1 = min(self.rb_start_y, self.rb_curr_y)
            rx2 = max(self.rb_start_x, self.rb_curr_x)
            ry2 = max(self.rb_start_y, self.rb_curr_y)

            hits = list(self.rb_base_selection)
            if (rx2 - rx1) >= 3.0 or (ry2 - ry1) >= 3.0:
                for b in self.boxes:
                    bx1 = b.x
                    by1 = b.y
                    bx2 = b.x + getattr(b, "logical_w", 28)
                    by2 = b.y + getattr(b, "logical_h", 28)
                    # Check rectangle overlap (SMath Studio style marquee selection)
                    if bx1 <= rx2 and bx2 >= rx1 and by1 <= ry2 and by2 >= ry1:
                        if b not in hits:
                            hits.append(b)

            self.set_selected_boxes(hits)
            self.event_box.queue_draw()
            return True
        return False

    def on_canvas_button_release(self, widget, event):
        if event.button == 1 and self.rubberband_active:
            self.rubberband_active = False
            self.event_box.queue_draw()
            return True
        return False

    def on_draw_rubberband(self, widget, cr):
        self.draw_sheet_cursor(cr)
        if not self.rubberband_active:
            return False
        rx1 = min(self.rb_start_x, self.rb_curr_x)
        ry1 = min(self.rb_start_y, self.rb_curr_y)
        rw = abs(self.rb_curr_x - self.rb_start_x)
        rh = abs(self.rb_curr_y - self.rb_start_y)
        if rw < 2.0 and rh < 2.0:
            return False

        cr.save()
        cr.scale(self.zoom, self.zoom)
        t = THEMES[self.theme_name]
        cr.set_source_rgba(*t["box_selected_border"], 0.16)
        cr.rectangle(rx1, ry1, rw, rh)
        cr.fill_preserve()
        cr.set_source_rgba(*t["box_selected_border"], 0.90)
        cr.set_line_width(1.2 / self.zoom)
        cr.set_dash([5.0 / self.zoom, 3.0 / self.zoom])
        cr.stroke()
        cr.restore()
        return False

    def on_canvas_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname in ("Delete", "BackSpace") and self.selected_boxes:
            if not any(b.editing for b in self.selected_boxes):
                self.remove_selected_boxes()
                return True
        if self.selected_box is not None and not self.selected_box.editing:
            return self.selected_box.on_key_press(self.selected_box, event)
        return False


# ============================================================================
# LHS Table of Contents (TOC) Pane
# ============================================================================


class TOCPane(Gtk.Box):
    """Left-hand side pane listing document headings (Title, H1, H2, H3) and List of Figures."""

    INDENT_BY_STYLE = {
        "title": 4,
        "subtitle": 4,
        "heading1": 12,
        "heading2": 26,
        "heading3": 40,
    }

    BADGE_BY_STYLE = {
        "title": "T",
        "subtitle": "ST",
        "heading1": "H1",
        "heading2": "H2",
        "heading3": "H3",
    }

    def __init__(self, canvas: MathCanvas):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.canvas = canvas
        self._row_to_box = {}
        self._fig_row_to_box = {}
        self._updating = False

        self.set_size_request(185, -1)

        vpaned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        vpaned.set_wide_handle(True)
        vpaned.set_position(380)

        # Upper section: Table of Contents (Headings)
        toc_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_box.set_margin_start(10)
        header_box.set_margin_end(8)
        header_box.set_margin_top(8)
        header_box.set_margin_bottom(6)

        title_lbl = Gtk.Label()
        title_lbl.set_markup("<b>Table of Contents</b>")
        title_lbl.set_xalign(0.0)
        title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        header_box.pack_start(title_lbl, True, True, 0)

        toc_vbox.pack_start(header_box, False, False, 0)
        toc_vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.listbox = Gtk.ListBox()
        self.listbox.set_can_focus(False)
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.set_activate_on_single_click(True)
        self.listbox.connect("row-activated", self._on_row_activated)
        scroller.add(self.listbox)
        toc_vbox.pack_start(scroller, True, True, 0)

        # Lower section: List of Figures
        fig_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        fig_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        fig_header_box.set_margin_start(10)
        fig_header_box.set_margin_end(8)
        fig_header_box.set_margin_top(8)
        fig_header_box.set_margin_bottom(6)

        fig_title_lbl = Gtk.Label()
        fig_title_lbl.set_markup("<b>List of Figures</b>")
        fig_title_lbl.set_xalign(0.0)
        fig_title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        fig_header_box.pack_start(fig_title_lbl, True, True, 0)

        fig_vbox.pack_start(fig_header_box, False, False, 0)
        fig_vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        fig_scroller = Gtk.ScrolledWindow()
        fig_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.fig_listbox = Gtk.ListBox()
        self.fig_listbox.set_can_focus(False)
        self.fig_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.fig_listbox.set_activate_on_single_click(True)
        self.fig_listbox.connect("row-activated", self._on_fig_row_activated)
        fig_scroller.add(self.fig_listbox)
        fig_vbox.pack_start(fig_scroller, True, True, 0)

        vpaned.pack1(toc_vbox, resize=True, shrink=True)
        vpaned.pack2(fig_vbox, resize=True, shrink=True)
        self.pack_start(vpaned, True, True, 0)

    def refresh(self):
        self._updating = True
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        self._row_to_box.clear()

        headings = self.canvas.get_toc_headings()
        if not headings:
            empty_row = Gtk.ListBoxRow()
            empty_row.set_can_focus(False)
            empty_row.set_selectable(False)
            empty_row.set_activatable(False)
            lbl = Gtk.Label(label="No headings yet.\nAdd Title, H1, H2, or H3.")
            lbl.set_xalign(0.0)
            lbl.set_margin_start(10)
            lbl.set_margin_end(8)
            lbl.set_margin_top(10)
            lbl.set_margin_bottom(10)
            lbl.set_line_wrap(True)
            empty_row.add(lbl)
            self.listbox.add(empty_row)
        else:
            for box in headings:
                row = Gtk.ListBoxRow()
                row.set_can_focus(False)
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                indent = self.INDENT_BY_STYLE.get(box.style_name, 8)
                hbox.set_margin_start(indent)
                hbox.set_margin_end(6)
                hbox.set_margin_top(4)
                hbox.set_margin_bottom(4)


                raw_title = (
                    box.text.strip().splitlines()[0]
                    if box.text.strip()
                    else f"({TEXT_STYLES[box.style_name]['label']})"
                )
                if getattr(box, "heading_number", ""):
                    raw_title = f"{box.heading_number}  {raw_title}"
                lbl = Gtk.Label()
                if box.style_name in ("title", "heading1"):
                    lbl.set_markup(f"<b>{GLib_markup_escape(raw_title)}</b>")
                else:
                    lbl.set_text(raw_title)
                lbl.set_xalign(0.0)
                lbl.set_ellipsize(Pango.EllipsizeMode.END)

                hbox.pack_start(lbl, True, True, 0)
                row.add(hbox)
                self.listbox.add(row)
                self._row_to_box[row] = box

                if box is self.canvas.selected_box:
                    self.listbox.select_row(row)

        self.listbox.show_all()

        # Refresh List of Figures
        for child in self.fig_listbox.get_children():
            self.fig_listbox.remove(child)
        self._fig_row_to_box.clear()

        figures = self.canvas.get_toc_figures()
        if not figures:
            empty_fig_row = Gtk.ListBoxRow()
            empty_fig_row.set_can_focus(False)
            empty_fig_row.set_selectable(False)
            empty_fig_row.set_activatable(False)
            flbl = Gtk.Label(label="No figures yet.\nInsert Plot or Image.")
            flbl.set_xalign(0.0)
            flbl.set_margin_start(10)
            flbl.set_margin_end(8)
            flbl.set_margin_top(10)
            flbl.set_margin_bottom(10)
            flbl.set_line_wrap(True)
            empty_fig_row.add(flbl)
            self.fig_listbox.add(empty_fig_row)
        else:
            for idx, fbox in enumerate(figures, start=1):
                row = Gtk.ListBoxRow()
                row.set_can_focus(False)
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                hbox.set_margin_start(8)
                hbox.set_margin_end(6)
                hbox.set_margin_top(4)
                hbox.set_margin_bottom(4)

                fig_num = getattr(fbox, "fig_num", idx)
                badge = Gtk.Label()
                badge.set_markup(f"<small><tt>F{fig_num}</tt></small>")
                badge.set_xalign(0.0)

                raw_cap = fbox.title.strip().splitlines()[0] if fbox.title.strip() else ""
                if raw_cap.lower().startswith("figure "):
                    parts = raw_cap.split(":", 1)
                    if len(parts) == 2 and parts[0][7:].strip().isdigit():
                        raw_cap = parts[1].strip()
                if not raw_cap:
                    raw_cap = (
                        f"Plot ({fbox.func_expr})" if isinstance(fbox, PlotBox)
                        else "Drawing" if isinstance(fbox, DrawingBox) else "Image"
                    )

                lbl = Gtk.Label(label=f"Figure {fig_num}: {raw_cap}")
                lbl.set_xalign(0.0)
                lbl.set_ellipsize(Pango.EllipsizeMode.END)
                lbl.set_tooltip_text(f"Figure {fig_num}: {raw_cap}")

                hbox.pack_start(badge, False, False, 0)
                hbox.pack_start(lbl, True, True, 0)
                row.add(hbox)
                self.fig_listbox.add(row)
                self._fig_row_to_box[row] = fbox

                if fbox is self.canvas.selected_box:
                    self.fig_listbox.select_row(row)

        self.fig_listbox.show_all()
        self._updating = False

    def _on_row_activated(self, _listbox, row):
        if self._updating:
            return
        box = self._row_to_box.get(row)
        if box is not None and box in self.canvas.boxes:
            self.canvas.scroll_to_box(box)

    def _on_fig_row_activated(self, _listbox, row):
        if self._updating:
            return
        fbox = self._fig_row_to_box.get(row)
        if fbox is not None and fbox in self.canvas.boxes:
            self.canvas.scroll_to_box(fbox)


def GLib_markup_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ============================================================================
# RHS Comprehensive Math Symbols & Functions Palette Pane
# ============================================================================


class SymbolsPane(Gtk.Box):
    """Right-hand side pane containing categorized math structures, operators, functions, and symbols."""

    def __init__(self, canvas: MathCanvas):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.canvas = canvas
        self.set_size_request(210, -1)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_box.set_margin_start(10)
        header_box.set_margin_end(8)
        header_box.set_margin_top(8)
        header_box.set_margin_bottom(6)

        title_lbl = Gtk.Label()
        title_lbl.set_markup("<b>Math Symbols</b>")
        title_lbl.set_xalign(0.0)
        title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        header_box.pack_start(title_lbl, True, True, 0)

        self.pack_start(header_box, False, False, 0)
        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        body.set_margin_start(8)
        body.set_margin_end(8)
        body.set_margin_top(8)
        body.set_margin_bottom(12)

        def add_section(title_text, items, cols=4):
            sec_lbl = Gtk.Label()
            sec_lbl.set_markup(f"<small><b>{GLib_markup_escape(title_text)}</b></small>")
            sec_lbl.set_xalign(0.0)
            body.pack_start(sec_lbl, False, False, 0)

            grid = Gtk.Grid(column_spacing=3, row_spacing=3)
            grid.set_column_homogeneous(True)
            for idx, (label, tip, cb) in enumerate(items):
                btn = Gtk.Button(label=label)
                btn.set_can_focus(False)
                btn.set_tooltip_text(tip)
                btn.connect("clicked", lambda _b, fn=cb: fn())
                grid.attach(btn, idx % cols, idx // cols, 1, 1)
            body.pack_start(grid, False, False, 2)

        # 1) 2D Structures, Plot & Picture
        add_section(
            "2D Structures & Image",
            [
                ("a/b", "Fraction (/)", lambda: self.canvas.get_active_or_new_box().insert_fraction()),
                ("xⁿ", "Superscript (^)", lambda: self.canvas.get_active_or_new_box().insert_superscript()),
                ("xₙ", "Subscript (_)", lambda: self.canvas.get_active_or_new_box().insert_subscript()),
                ("√x", "Square Root (\\)", lambda: self.canvas.get_active_or_new_box().insert_sqrt()),
                ("ⁿ√x", "N-th Root", lambda: self.canvas.get_active_or_new_box().insert_nth_root()),
                ("( )", "Parentheses", lambda: self.canvas.get_active_or_new_box().insert_parens()),
                ("[ ]", "Vector [v1, v2, ...]", lambda: self.canvas.get_active_or_new_box().insert_vector_brackets()),
                ("∑", "Summation", lambda: self.canvas.get_active_or_new_box().insert_sum()),
                ("∫", "Definite Integral", lambda: self.canvas.get_active_or_new_box().insert_integral()),
                ("ẋ", "Dot above (time derivative, e.g. ẋ, Q̇): dots the letter left of the cursor, or the next letter typed",
                 lambda: self.canvas.get_active_or_new_box().insert_dot_accent()),
                ("Img", "Paste Picture from Clipboard (Ctrl+V) or File", lambda: self.canvas.paste_from_clipboard(open_dialog_if_empty=True)),
            ],
            cols=4,
        )

        # 1b) Measurement units (also typed with an apostrophe: 5'kW)
        unit_btns = [
            ("m", "metre"), ("mm", "millimetre"), ("kg", "kilogram"), ("g", "gram"),
            ("s", "second"), ("min", "minute"), ("h", "hour"), ("K", "kelvin"),
            ("°C", "degree Celsius (20'°C = 293.15 K)"), ("A", "ampere"), ("mol", "mole"), ("N", "newton"),
            ("kN", "kilonewton"), ("J", "joule"), ("kJ", "kilojoule"), ("kWh", "kilowatt-hour"),
            ("W", "watt"), ("kW", "kilowatt"), ("Pa", "pascal"), ("kPa", "kilopascal"),
            ("MPa", "megapascal"), ("bar", "bar"), ("L", "litre"), ("Hz", "hertz"),
            ("V", "volt"), ("Ω", "ohm"), ("rad", "radian"), ("deg", "degree (angle)"),
        ]
        add_section(
            "Units  (type ' then the unit: 5'kW)",
            [(u, f"{u}: {tip}", lambda n=u: self.canvas.insert_unit(n)) for u, tip in unit_btns],
            cols=4,
        )

        # 2) Operators & Relations
        op_symbols = [
            ("=", "Define (a = 5) or Evaluate (a =)"),
            ("==", "Equation (y == 2x + 4): right-click it → Solve for"),
            ("+", "Plus"),
            ("-", "Minus"),
            ("·", "Multiply (*)"),
            ("±", "Plus-Minus"),
            ("∓", "Minus-Plus"),
            ("×", "Cross Multiply"),
            ("÷", "Divide"),
            ("<", "Less Than"),
            (">", "Greater Than"),
            ("≤", "Less or Equal (<=)"),
            ("≥", "Greater or Equal (>=)"),
            ("≠", "Not Equal (!=)"),
            ("≈", "Approximately Equal"),
            ("≡", "Identical To"),
            ("∝", "Proportional To"),
            ("!", "Factorial"),
            ("%", "Percent / Modulo"),
            ("∞", "Infinity (inf)"),
            ("←", "Arrow Left"),
            ("→", "Arrow Right"),
            ("↑", "Arrow Up"),
            ("↓", "Arrow Down"),
        ]
        add_section(
            "Operators & Relations",
            [
                (sym if sym == EQ_TOKEN else OP_DISPLAY.get(sym, sym), tip, lambda s=sym: self.canvas.insert_symbol(s))
                for sym, tip in op_symbols
            ],
            cols=4,
        )

        # 3) Functions
        fn_names = [
            ("sin", "Sine"),
            ("cos", "Cosine"),
            ("tan", "Tangent"),
            ("asin", "Arc Sine"),
            ("acos", "Arc Cosine"),
            ("atan", "Arc Tangent"),
            ("sinh", "Hyperbolic Sine"),
            ("cosh", "Hyperbolic Cosine"),
            ("tanh", "Hyperbolic Tangent"),
            ("ln", "Natural Logarithm"),
            ("log", "Base-10 Logarithm"),
            ("exp", "Exponential e^x"),
            ("abs", "Absolute Value"),
        ]
        add_section(
            "Functions",
            [(fn, tip, lambda f=fn: self.canvas.insert_function_call(f)) for fn, tip in fn_names],
            cols=3,
        )

        # 4) Greek Lowercase
        greek_lower = [
            ("α", "alpha"), ("β", "beta"), ("γ", "gamma"), ("δ", "delta"),
            ("ε", "epsilon"), ("ζ", "zeta"), ("η", "eta"), ("θ", "theta"),
            ("ι", "iota"), ("κ", "kappa"), ("λ", "lambda"), ("μ", "mu"),
            ("ν", "nu"), ("ξ", "xi"), ("π", "pi"), ("ρ", "rho"),
            ("σ", "sigma"), ("τ", "tau"), ("υ", "upsilon"), ("φ", "phi"),
            ("χ", "chi"), ("ψ", "psi"), ("ω", "omega"),
        ]
        add_section(
            "Greek (Lowercase)",
            [(sym, f"{sym} ({name})", lambda s=sym: self.canvas.insert_symbol(s)) for sym, name in greek_lower],
            cols=5,
        )

        # 5) Greek Uppercase
        greek_upper = [
            ("Γ", "Gamma"), ("Δ", "Delta"), ("Θ", "Theta"), ("Λ", "Lambda"),
            ("Ξ", "Xi"), ("Π", "Pi"), ("Σ", "Sigma"), ("Υ", "Upsilon"),
            ("Φ", "Phi"), ("Ψ", "Psi"), ("Ω", "Ω"),
        ]
        add_section(
            "Greek (Uppercase)",
            [(sym, f"{sym} ({name})", lambda s=sym: self.canvas.insert_symbol(s)) for sym, name in greek_upper],
            cols=5,
        )

        # 6) Calculus, Logic & Set Theory
        misc_symbols = [
            ("∂", "Partial Derivative"),
            ("∇", "Nabla / Gradient"),
            ("°", "Degree"),
            ("∀", "For All"),
            ("∃", "There Exists"),
            ("∈", "Element Of"),
            ("∉", "Not Element Of"),
            ("⊂", "Subset Of"),
            ("⊆", "Subset or Equal"),
            ("∪", "Union"),
            ("∩", "Intersection"),
            ("∅", "Empty Set"),
            ("∧", "Logical AND"),
            ("∨", "Logical OR"),
            ("¬", "Logical NOT"),
            ("⇒", "Implies"),
            ("⇔", "If and Only If"),
            ("→", "Right Arrow"),
            ("←", "Left Arrow"),
            ("↔", "Left-Right Arrow"),
        ]
        add_section(
            "Calculus, Sets & Logic",
            [(sym, tip, lambda s=sym: self.canvas.insert_symbol(s)) for sym, tip in misc_symbols],
            cols=5,
        )

        scroller.add(body)
        self.pack_start(scroller, True, True, 0)


# ============================================================================
# Main Window with File Menu, Clean Top Bar, Zoom Controls, TOC & Symbols Panes
# ============================================================================


# ============================================================================
# CommentariuM App Logo & Window / Toolbar Branding
# ============================================================================


# Embedded CommentariuM logo (SVG, base64-encoded)
COMMENTARIUM_LOGO_SVG_B64 = (
    'PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjgg'
    'MTI4IiB3aWR0aD0iMjU2IiBoZWlnaHQ9IjI1NiI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGll'
    'bnQgaWQ9ImJnR3JhZCIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+CiAgICAg'
    'IDxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiMxYTIyMzQiLz4KICAgICAgPHN0b3Agb2Zm'
    'c2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjMGYxNTIyIi8+CiAgICA8L2xpbmVhckdyYWRpZW50Pgog'
    'ICAgPGxpbmVhckdyYWRpZW50IGlkPSJwYWdlR3JhZCIgeDE9IjAlIiB5MT0iMCUiIHgyPSIwJSIg'
    'eTI9IjEwMCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjZjhmYWZjIi8+'
    'CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iI2UyZThmMCIvPgogICAgPC9s'
    'aW5lYXJHcmFkaWVudD4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZ29sZEdyYWQiIHgxPSIwJSIg'
    'eTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdG9w'
    'LWNvbG9yPSIjZmJiZjI0Ii8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0i'
    'I2Q5NzcwNiIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICA8L2RlZnM+CgogIDwhLS0gT3V0ZXIg'
    'Um91bmRlZCBCYWRnZSAtLT4KICA8cmVjdCB4PSI2IiB5PSI2IiB3aWR0aD0iMTE2IiBoZWlnaHQ9'
    'IjExNiIgcng9IjI0IiBmaWxsPSJ1cmwoI2JnR3JhZCkiIHN0cm9rZT0iIzM4YmRmOCIgc3Ryb2tl'
    'LXdpZHRoPSIzLjUiLz4KCiAgPCEtLSBOb3RlYm9vayBTcGluZSAvIFNoYWRvdyAtLT4KICA8cmVj'
    'dCB4PSIyNCIgeT0iMTgiIHdpZHRoPSI4MCIgaGVpZ2h0PSI5NCIgcng9IjYiIGZpbGw9IiMwOTBk'
    'MTYiIG9wYWNpdHk9IjAuNDUiLz4KCiAgPCEtLSBBNCBHcmFwaCBQYXBlciBTaGVldCB3aXRoIEZv'
    'bGRlZCBUb3AtUmlnaHQgQ29ybmVyIC0tPgogIDxwYXRoIGQ9Ik0gMjQgMTYgTCA4NCAxNiBMIDEw'
    'NCAzNiBMIDEwNCAxMTAgQyAxMDQgMTEyLjIgMTAyLjIgMTE0IDEwMCAxMTQgTCAyOCAxMTQgQyAy'
    'NS44IDExNCAyNCAxMTIuMiAyNCAxMTAgWiIgZmlsbD0idXJsKCNwYWdlR3JhZCkiLz4KICA8cGF0'
    'aCBkPSJNIDg0IDE2IEwgODQgMzYgTCAxMDQgMzYgWiIgZmlsbD0iI2NiZDVlMSIvPgoKICA8IS0t'
    'IFN1YnRsZSBFbmdpbmVlcmluZyBHcmFwaCBHcmlkIG9uIFNoZWV0IC0tPgogIDxnIHN0cm9rZT0i'
    'Izk0YTNiOCIgc3Ryb2tlLXdpZHRoPSIxIiBvcGFjaXR5PSIwLjQ1Ij4KICAgIDxsaW5lIHgxPSI0'
    'MCIgeTE9IjE2IiB4Mj0iNDAiIHkyPSIxMTQiLz4KICAgIDxsaW5lIHgxPSI1NiIgeTE9IjE2IiB4'
    'Mj0iNTYiIHkyPSIxMTQiLz4KICAgIDxsaW5lIHgxPSI3MiIgeTE9IjE2IiB4Mj0iNzIiIHkyPSIx'
    'MTQiLz4KICAgIDxsaW5lIHgxPSI4OCIgeTE9IjM2IiB4Mj0iODgiIHkyPSIxMTQiLz4KICAgIDxs'
    'aW5lIHgxPSIyNCIgeTE9IjM2IiB4Mj0iMTA0IiB5Mj0iMzYiLz4KICAgIDxsaW5lIHgxPSIyNCIg'
    'eTE9IjUyIiB4Mj0iMTA0IiB5Mj0iNTIiLz4KICAgIDxsaW5lIHgxPSIyNCIgeTE9IjY4IiB4Mj0i'
    'MTA0IiB5Mj0iNjgiLz4KICAgIDxsaW5lIHgxPSIyNCIgeTE9Ijg0IiB4Mj0iMTA0IiB5Mj0iODQi'
    'Lz4KICAgIDxsaW5lIHgxPSIyNCIgeTE9IjEwMCIgeDI9IjEwNCIgeTI9IjEwMCIvPgogIDwvZz4K'
    'CiAgPCEtLSBMZWZ0IE5vdGVib29rIE1hcmdpbiBMaW5lIC0tPgogIDxsaW5lIHgxPSIzNCIgeTE9'
    'IjE2IiB4Mj0iMzQiIHkyPSIxMTQiIHN0cm9rZT0iI2VmNDQ0NCIgc3Ryb2tlLXdpZHRoPSIxLjYi'
    'IG9wYWNpdHk9IjAuNjUiLz4KCiAgPCEtLSBNYXRoZW1hdGljYWwgQ3VydmUgb24gU2hlZXQgLS0+'
    'CiAgPHBhdGggZD0iTSAzNiA5MiBRIDU0IDQ2LCA3MiA3MiBUIDk4IDQ4IiBmaWxsPSJub25lIiBz'
    'dHJva2U9IiMwMjg0YzciIHN0cm9rZS13aWR0aD0iMy4yIiBzdHJva2UtbGluZWNhcD0icm91bmQi'
    'Lz4KCiAgPCEtLSBDbGFzc2ljIEludGVncmFsIEVtYmxlbSAn4oirJyAtLT4KICA8dGV4dCB4PSI1'
    'OCIgeT0iODgiIGZvbnQtZmFtaWx5PSJTZXJpZiIgZm9udC1zaXplPSI2MCIgZm9udC13ZWlnaHQ9'
    'ImJvbGQiIGZvbnQtc3R5bGU9Iml0YWxpYyIgZmlsbD0iIzBmMTcyYSIgdGV4dC1hbmNob3I9Im1p'
    'ZGRsZSI+4oirPC90ZXh0PgoKICA8IS0tIEdvbGQgQm9va21hcmsgLyBTZWFsIFJpYmJvbiAtLT4K'
    'ICA8cGF0aCBkPSJNIDQwIDE2IEwgNTIgMTYgTCA1MiAzOCBMIDQ2IDMyIEwgNDAgMzggWiIgZmls'
    'bD0idXJsKCNnb2xkR3JhZCkiLz4KPC9zdmc+Cg=='
)


def render_commentarium_logo_pixbuf(size: int = 32) -> GdkPixbuf.Pixbuf:
    """Render the embedded CommentariuM SVG logo at the given size, with a pure-Cairo vector fallback."""
    try:
        loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
        loader.set_size(size, size)
        loader.write(base64.b64decode(COMMENTARIUM_LOGO_SVG_B64))
        loader.close()
        pb = loader.get_pixbuf()
        if pb is not None:
            return pb
    except Exception:
        pass

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    cr = cairo.Context(surface)
    s = size / 128.0
    cr.scale(s, s)

    # Outer badge
    cr.set_source_rgb(0.10, 0.13, 0.20)
    cr.rectangle(8, 8, 112, 112)
    cr.fill_preserve()
    cr.set_source_rgb(0.22, 0.74, 0.97)
    cr.set_line_width(4.0)
    cr.stroke()

    # Graph paper sheet
    cr.set_source_rgb(0.96, 0.97, 0.99)
    cr.move_to(24, 16)
    cr.line_to(84, 16)
    cr.line_to(104, 36)
    cr.line_to(104, 112)
    cr.line_to(24, 112)
    cr.close_path()
    cr.fill()

    # Folded corner
    cr.set_source_rgb(0.78, 0.83, 0.89)
    cr.move_to(84, 16)
    cr.line_to(84, 36)
    cr.line_to(104, 36)
    cr.close_path()
    cr.fill()

    # Gold ribbon
    cr.set_source_rgb(0.96, 0.68, 0.12)
    cr.move_to(38, 16)
    cr.line_to(50, 16)
    cr.line_to(50, 38)
    cr.line_to(44, 32)
    cr.line_to(38, 38)
    cr.close_path()
    cr.fill()

    # Integral sign
    cr.set_source_rgb(0.06, 0.09, 0.16)
    cr.select_font_face("Serif", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(58)
    cr.move_to(46, 88)
    cr.show_text("∫")

    return Gdk.pixbuf_get_from_surface(surface, 0, 0, size, size)


class MainWindow(Gtk.Window):
    RECENT_FILES_PATH = os.path.expanduser("~/.config/smath_clone/recent_files.json")
    SETTINGS_PATH = os.path.expanduser("~/.config/smath_clone/settings.json")
    MAX_RECENT_FILES = 10

    def __init__(self):
        apply_ui_font_size()
        super().__init__(title="CommentariuM — A4 Mathematical Notebook")
        self.set_resizable(True)
        self.set_default_size(1408, 880)  # 10% wider than the original 1280
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_size_request(360, 300)
        self.connect("destroy", Gtk.main_quit)
        # Always open filling the screen (maximized); F11 toggles true full screen
        self.maximize()
        self._is_fullscreen = False
        self.connect("window-state-event", self._on_window_state)
        self.connect("key-press-event", self._on_window_key_press)
        # Undo history: record the worksheet after each key/mouse release, plus a slow
        # heartbeat that catches changes made from menus and dialogs.
        self._undo_pending = False

        def _schedule_checkpoint(*_a):
            if not self._undo_pending:
                self._undo_pending = True

                def _run():
                    self._undo_pending = False
                    self.canvas.undo_checkpoint()
                    return False

                GLib.timeout_add(120, _run)
            return False

        def _after_event(_w, ev):
            if ev.type in (Gdk.EventType.KEY_RELEASE, Gdk.EventType.BUTTON_RELEASE):
                _schedule_checkpoint()

        self.connect("event-after", _after_event)
        GLib.timeout_add(900, lambda: (_schedule_checkpoint(), True)[1])

        try:
            logo_pb = render_commentarium_logo_pixbuf(128)
            if logo_pb is not None:
                self.set_icon(logo_pb)
        except Exception:
            pass

        self.recent_files = self._load_recent_files()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.canvas = MathCanvas()
        theme_pref = self._load_settings().get("theme", "light")
        self.canvas.theme_name = theme_pref if theme_pref in THEMES else "light"
        self.toc_pane = TOCPane(self.canvas)
        self.symbols_pane = SymbolsPane(self.canvas)
        self.canvas.on_toc_updated = self.toc_pane.refresh
        self.canvas.on_zoom_changed = self._on_zoom_updated
        self.canvas.on_selection_changed = self._on_canvas_selection_changed

        # Inner horizontal split: Center A4 Worksheet Canvas | RHS Math Symbols Pane
        self.rpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.rpaned.set_wide_handle(True)
        self.rpaned.pack1(self.canvas, resize=True, shrink=True)
        self.rpaned.pack2(self.symbols_pane, resize=False, shrink=True)
        self.rpaned.set_position(948)  # give the extra width to the canvas

        # Outer horizontal split: LHS Table of Contents | (Center Canvas + RHS Symbols)
        self.hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.hpaned.set_wide_handle(True)
        # LHS: command panel (menus, save, align) on top of the table of contents
        self.lhs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.lhs_box.pack_start(self._build_toolbar(), False, False, 0)
        self.lhs_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        self.lhs_box.pack_start(self.toc_pane, True, True, 0)
        self.hpaned.pack1(self.lhs_box, resize=False, shrink=True)
        self.hpaned.pack2(self.rpaned, resize=True, shrink=True)
        self.hpaned.set_position(332)  # left pane (menus + contents) ≈ 330 px

        self._build_statusbar()  # status label kept (unpacked) so status updates stay harmless

        vbox.pack_start(self.hpaned, True, True, 0)
        self.add(vbox)

        loaded_initial = False
        cli_file = sys.argv[1] if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]) else None
        target_file = cli_file or (self.recent_files[0] if self.recent_files else None)
        if target_file and os.path.isfile(target_file):
            try:
                self.canvas.load_from_file(target_file)
                self._add_recent_file(target_file)
                self._update_window_title()
                if hasattr(self, "status_label"):
                    self.status_label.set_text(f"Opened last file: {target_file}")
                loaded_initial = True
            except Exception:
                loaded_initial = False

        if not loaded_initial:
            self._populate_starter_examples()
        self.toc_pane.refresh()

    def _load_settings(self) -> dict:
        try:
            with open(self.SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_setting(self, key, value):
        data = self._load_settings()
        data[key] = value
        try:
            os.makedirs(os.path.dirname(self.SETTINGS_PATH), exist_ok=True)
            with open(self.SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_recent_files(self) -> list:
        try:
            if os.path.isfile(self.RECENT_FILES_PATH):
                with open(self.RECENT_FILES_PATH, "r", encoding="utf-8") as f:
                    items = json.load(f)
                if isinstance(items, list):
                    return [str(p) for p in items if isinstance(p, str) and os.path.isfile(p)][
                        : self.MAX_RECENT_FILES
                    ]
        except Exception:
            pass
        return []

    def _save_recent_files(self):
        try:
            os.makedirs(os.path.dirname(self.RECENT_FILES_PATH), exist_ok=True)
            with open(self.RECENT_FILES_PATH, "w", encoding="utf-8") as f:
                json.dump(self.recent_files[: self.MAX_RECENT_FILES], f, indent=2)
        except Exception:
            pass

    def _add_recent_file(self, filepath: str):
        if not filepath:
            return
        abspath = os.path.abspath(filepath)
        self.recent_files = [abspath] + [p for p in self.recent_files if os.path.abspath(p) != abspath]
        self.recent_files = self.recent_files[: self.MAX_RECENT_FILES]
        self._save_recent_files()
        self._rebuild_recent_files_submenu()

    def _clear_recent_files(self):
        self.recent_files = []
        self._save_recent_files()
        self._rebuild_recent_files_submenu()
        if hasattr(self, "status_label"):
            self.status_label.set_text("Cleared recent files list.")

    def _open_recent_file(self, filepath: str):
        if not filepath or not os.path.isfile(filepath):
            self.recent_files = [p for p in self.recent_files if p != filepath]
            self._save_recent_files()
            self._rebuild_recent_files_submenu()
            if hasattr(self, "status_label"):
                self.status_label.set_text(f"Recent file not found: {filepath}")
            return
        try:
            self.canvas.load_from_file(filepath)
            self._add_recent_file(filepath)
            self._update_window_title()
            if hasattr(self, "status_label"):
                self.status_label.set_text(f"Opened: {filepath}")
        except Exception as exc:
            if hasattr(self, "status_label"):
                self.status_label.set_text(f"Failed to open file: {exc}")

    def _rebuild_recent_files_submenu(self):
        if not hasattr(self, "recent_files_menu") or self.recent_files_menu is None:
            return
        for child in list(self.recent_files_menu.get_children()):
            self.recent_files_menu.remove(child)

        existing = [p for p in self.recent_files if os.path.isfile(p)]
        if not existing:
            empty_item = Gtk.MenuItem(label="(No recent files)")
            empty_item.set_sensitive(False)
            self.recent_files_menu.append(empty_item)
        else:
            for idx, fpath in enumerate(existing, start=1):
                base = os.path.basename(fpath)
                parent_dir = os.path.dirname(fpath)
                mi = Gtk.MenuItem(label=f"{idx}. {base}   ({parent_dir})")
                mi.connect("activate", lambda _mi, p=fpath: self._open_recent_file(p))
                self.recent_files_menu.append(mi)
            self.recent_files_menu.append(Gtk.SeparatorMenuItem())
            clear_mi = Gtk.MenuItem(label="Clear Recent Files")
            clear_mi.connect("activate", lambda _mi: self._clear_recent_files())
            self.recent_files_menu.append(clear_mi)

        self.recent_files_menu.show_all()

    def do_key_press_event(self, event):
        if event.keyval == Gdk.KEY_KP_Delete:
            event.keyval = Gdk.KEY_Delete  # the keypad Delete key acts like Delete
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)
        keyname = Gdk.keyval_name(event.keyval)

        if ctrl:
            focus_w = self.get_focus()
            in_entry = isinstance(focus_w, (Gtk.Entry, Gtk.TextView)) and not focus_w.is_ancestor(self.canvas)
            # A drawing being edited: Ctrl+C / X / V / D copy, cut, paste, duplicate its shapes
            draw_box = next((b for b in self.canvas.boxes if isinstance(b, DrawingBox) and b.editing), None)
            if draw_box is not None and not in_entry and keyname.lower() in ("a", "c", "x", "v", "d"):
                draw_box.handle_clipboard_key(keyname)
                return True
            if keyname in ("z", "Z") and not in_entry:
                if shift:
                    self.canvas.redo()
                else:
                    self.canvas.undo()
                return True
            if keyname in ("y", "Y") and not in_entry:
                self.canvas.redo()
                return True
            if keyname in ("a", "A"):
                if not any(b.editing for b in self.canvas.boxes):
                    self.canvas.select_all_boxes()
                    return True
            elif keyname in ("v", "V"):
                if self.canvas.paste_from_clipboard(open_dialog_if_empty=False):
                    return True
                if self.canvas.paste_table_text():
                    return True
            elif keyname in ("b", "B", "u", "U") and not in_entry:
                if self.canvas.toggle_text_format("bold" if keyname in ("b", "B") else "underline"):
                    return True
            elif keyname in ("n", "N"):
                self._on_file_new()
                return True
            elif keyname in ("o", "O"):
                self._on_file_open()
                return True
            elif keyname in ("s", "S"):
                if shift:
                    self._on_file_save_as()
                else:
                    self._on_file_save()
                return True
            elif keyname in ("e", "E", "p", "P"):
                self._on_file_export_pdf()
                return True
            elif keyname in ("plus", "equal", "KP_Add"):
                self.canvas.zoom_in()
                return True
            elif keyname in ("minus", "underscore", "KP_Subtract"):
                self.canvas.zoom_out()
                return True
            elif keyname in ("0", "KP_0"):
                self.canvas.reset_zoom()
                return True

        # Sheet cursor gets keys first (before GTK uses arrows/Enter for focus navigation),
        # unless another control such as the TOC list has the keyboard focus.
        focus = self.get_focus()
        focus_is_input = isinstance(
            focus, (Gtk.Entry, Gtk.TextView, Gtk.TreeView, Gtk.ListBox, Gtk.ListBoxRow, Gtk.ComboBox)
        ) and not focus.is_ancestor(self.canvas)
        # Arrow keys move the selected objects (when none of them is being edited)
        nudges = {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1),
                  "KP_Left": (-1, 0), "KP_Right": (1, 0), "KP_Up": (0, -1), "KP_Down": (0, 1)}
        if (keyname in nudges and not focus_is_input and not ctrl
                and not (event.state & Gdk.ModifierType.MOD1_MASK)
                and self.canvas.selected_boxes
                and not any(b.editing for b in self.canvas.boxes)):
            step = self.canvas.NUDGE_STEP_BIG if shift else self.canvas.NUDGE_STEP
            ux, uy = nudges[keyname]
            if self.canvas.nudge_selected(ux * step, uy * step):
                return True
        if not focus_is_input and self.canvas.sheet_cursor_visible():
            if self.canvas.handle_sheet_cursor_key(event):
                return True

        res = Gtk.Window.do_key_press_event(self, event)
        if not res:
            if keyname in ("Delete", "BackSpace") and self.canvas.selected_boxes:
                if not any(b.editing for b in self.canvas.selected_boxes):
                    self.canvas.remove_selected_boxes()
                    return True
            if self.canvas.selected_box is not None and not self.canvas.selected_box.editing:
                return self.canvas.selected_box.on_key_press(self.canvas.selected_box, event)
        return res

    def _make_menu_button(self, label_text: str, tooltip: str, items: list) -> Gtk.MenuButton:
        menu_btn = Gtk.MenuButton(label=label_text)
        menu_btn.set_relief(Gtk.ReliefStyle.NONE)
        menu_btn.set_can_focus(False)
        menu_btn.set_tooltip_text(tooltip)

        menu = Gtk.Menu()
        for entry in items:
            if entry[0] is None:
                menu.append(Gtk.SeparatorMenuItem())
            else:
                label, cb = entry[0], entry[1]
                mi = Gtk.MenuItem(label=label)
                mi.connect("activate", lambda _mi, fn=cb: fn())
                menu.append(mi)
                if len(entry) >= 3 and entry[2]:
                    setattr(self, entry[2], mi)
        menu.show_all()
        menu_btn.set_popup(menu)
        return menu_btn

    def _build_file_menu_button(self) -> Gtk.MenuButton:
        menu_btn = Gtk.MenuButton(label="File ▾")
        menu_btn.set_relief(Gtk.ReliefStyle.NONE)
        menu_btn.set_can_focus(False)
        menu_btn.set_tooltip_text("File menu: New, Open, Recent Files, Save (Ctrl+S), Save As, Export PDF")

        menu = Gtk.Menu()

        def add_item(label, cb):
            mi = Gtk.MenuItem(label=label)
            mi.connect("activate", lambda _mi: cb())
            menu.append(mi)
            return mi

        add_item("New  (Ctrl+N)", self._on_file_new)
        add_item("Open...  (Ctrl+O)", self._on_file_open)

        recent_parent = Gtk.MenuItem(label="Recent Files")
        self.recent_files_menu = Gtk.Menu()
        recent_parent.set_submenu(self.recent_files_menu)
        menu.append(recent_parent)
        self._rebuild_recent_files_submenu()

        menu.append(Gtk.SeparatorMenuItem())
        add_item("Save  (Ctrl+S)", self._on_file_save)
        add_item("Save As...  (Ctrl+Shift+S)", self._on_file_save_as)
        menu.append(Gtk.SeparatorMenuItem())
        add_item("Export PDF...  (Ctrl+E)", self._on_file_export_pdf)

        menu.show_all()
        menu_btn.set_popup(menu)
        return menu_btn

    def _build_insert_menu_button(self) -> Gtk.MenuButton:
        return self._make_menu_button(
            "Insert ▾",
            "Insert Plot, Picture/Image, Table, Text Box, Math Box, or New A4 Page",
            [
                ("Plot", lambda: self.canvas.create_plot_box()),
                ("Picture from File…", self.canvas.insert_picture_from_file),
                ("Paste Picture  (Ctrl+V)", self._on_paste_picture),
                ("Table", lambda: self.canvas.create_table_box()),
                ("Drawing", lambda: self.canvas.create_drawing_box()),
                ("Arrow", lambda: self.canvas.insert_arrow()),
                ("Line", lambda: self.canvas.insert_arrow(head=False)),
                ("Link…", lambda: self.canvas.insert_link()),
                (None, None),
                ("Text Box", lambda: self.canvas.insert_text_box("normal")),
                ("Title", lambda: self.canvas.insert_text_box("title")),
                ("Subtitle", lambda: self.canvas.insert_text_box("subtitle")),
                ("Heading 1", lambda: self.canvas.insert_text_box("heading1")),
                ("Heading 2", lambda: self.canvas.insert_text_box("heading2")),
                ("Heading 3", lambda: self.canvas.insert_text_box("heading3")),
                ("Math Equation Box", lambda: self.canvas.insert_math_box()),
                (None, None),
                ("New A4 Page", self.canvas.add_page),
            ],
        )

    def _build_edit_menu_button(self) -> Gtk.MenuButton:
        return self._make_menu_button(
            "Edit ▾",
            "Edit menu: select, delete, tidy pages",
            [
                ("Undo  (Ctrl+Z)", self.canvas.undo),
                ("Redo  (Ctrl+Y)", self.canvas.redo),
                (None, None),
                ("Paste Data as Table  (Ctrl+V)", self._on_paste_table),
                ("Select All", self.canvas.select_all_boxes),
                ("Delete Selected", lambda: self.canvas.remove_selected_boxes()),
                (None, None),
                ("Remove Empty Pages at End", self._on_trim_pages),
            ],
        )

    def _build_view_menu_button(self) -> Gtk.MenuButton:
        return self._make_menu_button(
            "View ▾",
            "View menu: Zoom, TOC Pane, Symbols Pane, Grid, Theme",
            [
                ("Zoom In  (Ctrl++)", self.canvas.zoom_in),
                ("Zoom Out  (Ctrl+-)", self.canvas.zoom_out),
                ("Reset Zoom  (Ctrl+0)", self.canvas.reset_zoom, "zoom_reset_menuitem"),
                (None, None),
                ("Table of Contents", self._on_toggle_toc),
                ("Math Symbols Pane", self._on_toggle_symbols),
                (None, None),
                ("Graph-Paper Grid", lambda: self._on_toggle_grid(None)),
                ("Dark / Light Theme", lambda: self._on_toggle_theme(None)),
                (None, None),
                ("Full Screen  (F11)", lambda: self.unfullscreen() if self._is_fullscreen else self.fullscreen()),
            ],
        )

    def _build_toolbar(self) -> Gtk.Box:
        """Command panel (logo, menus, save, align) shown at the top of the left-hand pane,
        so the canvas gets the full window height."""
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        panel.set_margin_start(6)
        panel.set_margin_end(6)
        panel.set_margin_top(6)
        panel.set_margin_bottom(6)

        # Row 1: logo, save, align buttons
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        try:
            tb_logo = render_commentarium_logo_pixbuf(32)
            if tb_logo is not None:
                top_row.pack_start(Gtk.Image.new_from_pixbuf(tb_logo), False, False, 2)
        except Exception:
            pass

        save_btn = Gtk.Button(label="💾")
        save_btn.set_relief(Gtk.ReliefStyle.NONE)
        save_btn.set_can_focus(False)
        save_btn.set_tooltip_text("Save the worksheet (Ctrl+S)")
        save_btn.connect("clicked", lambda _b: self._on_file_save())

        self.align_left_btn = self._make_align_button(
            "left", "Align Left: line up the left edges of the selected objects (select two or more)")
        self.align_right_btn = self._make_align_button(
            "right", "Align Right: line up the right edges of the selected objects (select two or more)")
        top_row.pack_end(self.align_right_btn, False, False, 0)
        top_row.pack_end(self.align_left_btn, False, False, 0)
        top_row.pack_end(save_btn, False, False, 0)
        panel.pack_start(top_row, False, False, 0)

        # Menu buttons in a compact grid
        menus = [
            self._build_file_menu_button(),
            self._build_edit_menu_button(),
            self._build_insert_menu_button(),
            self._build_view_menu_button(),
            self._make_menu_button(
                "Tools ▾",
                "Tools: curve fitting, unit conversion, fluid properties, thermal spreading, thermal contact, plot digitizer",
                [("Curve Fit…", self.canvas.open_curve_fit),
                 ("Unit Converter…", self.canvas.open_unit_converter),
                 ("Fluid Properties…", self.canvas.open_fluid_properties),
                 ("Thermal Spreading…", self.canvas.open_thermal_spreading),
                 ("Thermal Contact…", self.canvas.open_thermal_contact),
                 (None, None),
                 ("Plot Digitizer…", self.canvas.open_plot_digitizer)],
            ),
            self._make_menu_button(
                "About ▾",
                "About CommentariuM and its features",
                [("About CommentariuM…", self._on_about)],
            ),
        ]
        grid = Gtk.Grid(column_spacing=2, row_spacing=2)
        grid.set_column_homogeneous(True)
        for i, mb in enumerate(menus):
            mb.set_hexpand(True)
            grid.attach(mb, i % 3, i // 3, 1, 1)
        panel.pack_start(grid, False, False, 0)

        self._update_align_buttons()
        return panel

    ABOUT_FEATURES = [
        ("Undo", [
            "Undo / Redo (Ctrl+Z, Ctrl+Y or Ctrl+Shift+Z, also in the Edit menu): up to 100 steps; "
            "typing in a box counts as one step",
        ]),
        ("Tools", [
            "Curve Fit: fit the coefficients of a model on the sheet (e.g. y = a·x² + b·x + c) to data vectors; "
            "inserts the coefficients, the fitted function and a plot",
            "Unit Converter: SI ⇄ English for temperature, length, area, volume, mass, force, time, "
            "speed, volumetric flow rate and pressure",
            "Fluid Properties: density, specific heat, kinematic viscosity, thermal diffusivity, thermal "
            "conductivity (also μ, Pr) of dry air (100–3000 K) and water (273–600 K) vs temperature; "
            "also as sheet functions ρ_water(T), cp_air(T), ν_air(T, p) … (T in K)",
            "Thermal Spreading: Lee–Song–Au spreading resistance of a centered heat source on a plate "
            "(sizes in mm / cm / m), with 1-D, convection and total resistances and the source temperature rise",
            "Thermal Contact: joint conductance and resistance of two rough surfaces clamped in air "
            "(Cooper–Mikic–Yovanovich contact + Yovanovich air gap), by material, finish, area and force",
            "Plot Digitizer: pick data points off a picture of a graph (open, paste or a selected picture); "
            "4-point axis calibration, linear or log axes, several series, magnifier; inserts a table and a plot",
            "Paste data: Ctrl+V with numbers copied from a spreadsheet or another digitizer (tabs, commas, "
            "semicolons or spaces) creates a table, or fills the table being edited from its current cell",
        ]),
        ("Worksheet", [
            "A4 pages on graph paper, dark and light themes, zoom (Ctrl + / Ctrl −)",
            "Red sheet cursor: click to place, Enter / Backspace insert or remove a line, start typing to add math",
            "Move selected objects with the arrow keys (10 px steps; Shift + arrow: 50 px)",
            "Align Left / Align Right buttons (left pane): line up the edges of two or more selected objects",
            "Text boxes: Bold (Ctrl+B) and Underline (Ctrl+U) from the right-click menu",
            "Tables: show only N rows with a scroll bar (Table Options or right-click); all rows still count as data",
            "Dialogs: Enter does the same as Apply / OK / Insert",
            "Table of contents (left) and math symbols pane (right)",
            "Save / open worksheets (JSON), recent files, export to vector PDF (Ctrl+E)",
        ]),
        ("Math", [
            "2D equation editor: fractions (/), powers (^), subscripts (_), roots (\\), Σ, ∫, vectors, dot above for time derivatives (ẋ)",
            "One '=' defines (a = 5) or evaluates (a =); functions f(x) = x² + a",
            "Greek letters by name (alpha → α, kappa → κ …), results with chosen decimal places (right-click)",
            "Boxed equations, live recalculation of the whole sheet",
            "Notes on equations (right-click → Add Note): red corner mark, shown when hovering",
        ]),
        ("Units", [
            "Type an apostrophe and the unit after a number: 5'kW, 2.5'mm, 20'°C (also 'degC), 3'm/'s, 'ohm → Ω, 'um → μm",
            "Units are drawn in their own colour (red if unknown) and can also be inserted from the Units list (right pane)",
            "Basic SI units with prefixes: m, g, s, min, h, day, K, °C, A, mol, cd, N, J, Wh, cal, W, Pa, bar, atm, Hz, C, V, Ω, F, H, T, Wb, L, rad, deg",
            "Results are shown in SI with the best-matching unit: W, J, Pa, W/(m·K), J/kg, m/s² …",
            "Mismatched units are reported on the sheet (m + s, sin(5 m) …)",
            "A number followed by °C is an absolute temperature (20'°C = 293.15 K); write temperature differences in K",
            "Show a result in the unit you want: write the unit after the final '=' (E = P·t = 'kWh → 15 kWh; "
            "T = '°C; d = 'mm; q = 'W/'m²); the box reports units that don't match",
            "Fluid functions with units: ρ_water(300'K) or k_air(20'°C) give kg/m³, W/(m·K) …; "
            "the Fluid Properties tool inserts its values with units",
            "Plots, curve fits, tables and the solver work with the SI numbers",
        ]),
        ("Equations & Solver", [
            "Write equations with '==' (y == 2x + 4)",
            "Right-click → Solve for: symbolic rearranging (x = (y − 4)/2), numeric fallback",
            "Right-click → Substitute: replace a variable using another equation or definition",
        ]),
        ("Text", [
            "Title, Heading 1–3 and Normal text styles (right-click a text box)",
            "Headings numbered automatically (1, 1.1, 1.1.1) with fixed indentation",
            "Web links (Insert → Link): Ctrl+click opens, double-click edits, live links in PDF",
            "Free arrows on the sheet (Insert → Arrow): drag the ends, double-click for color and thickness",
            "Free lines on the sheet (Insert → Line): like arrows, without a head (Shift while dragging an end snaps to 45°)",
            "Drawings: electrical symbols in the Shape list (resistor, IEC resistor, capacitor, switch, ground, fan); "
            "drag an end to resize / rotate (Shift: 45° steps), R rotates the selected shape 90°",
            "Drawings: Ctrl+C / Ctrl+X / Ctrl+V / Ctrl+D copy, cut, paste and duplicate shapes (also between drawings)",
            "Drawings: select several shapes by dragging a rectangle, Shift/Ctrl-click, or Ctrl+A; move, nudge, "
            "rotate, recolor, copy or delete them together",
            "Drawings: drag the corner handle to resize (scales the content, keeps proportions; Shift: free), "
            "drag the bars in the middle of the edges to crop",
            "Drawings: Outline and Fill colors are set separately (Outline: also No Outline; Fill: none, same as outline, black, white, "
            "colors; solid or light tint)",
            "Drawings: paste a picture with Ctrl+V while editing (or Shape ▾ → Picture, or from a file); "
            "drag a corner to resize (keeps proportions; Shift: free), R rotates it 90°",
        ]),
        ("Figures & Tables", [
            "2D plots of functions and data, with captions",
            "Pictures from the clipboard or files, resizable, with captions",
            "Drawings made of simple shapes (lines, single- and double-headed arrows with filled or simple heads, rectangles, ellipses, triangles with movable corners, arcs with adjustable angle, text; three line thicknesses; optional white/black background), with captions",
            "Tables whose columns can be used in calculations (T1(2,3), mean(Re) …)",
            "Figures and tables numbered automatically",
        ]),
    ]

    def _on_paste_picture(self):
        if not self.canvas.paste_from_clipboard():
            self.canvas._show_solver_message(
                "The clipboard holds no picture.\n\nCopy an image (or an image file) first, or use "
                "Insert ▸ Picture from File… to choose one.", info=True, title="Paste Picture")

    def _on_paste_table(self):
        if not self.canvas.paste_table_text():
            self.canvas._show_solver_message(
                "The clipboard holds no table of numbers.\n\nCopy data with one row per line and the "
                "columns separated by tabs, commas, semicolons or spaces — for example from a plot "
                "digitizer or a spreadsheet.", info=True, title="Paste Data")

    def _on_trim_pages(self, *_a):
        n = self.canvas.trim_empty_pages()
        self.canvas.desk_box.queue_draw()
        self.canvas.event_box.queue_draw()
        self.status_label.set_text(
            f"Removed {n} empty page{'s' if n != 1 else ''} at the end." if n else "No empty pages at the end."
        )

    def _on_window_state(self, _win, event):
        self._is_fullscreen = bool(event.new_window_state & Gdk.WindowState.FULLSCREEN)
        return False

    def _on_window_key_press(self, _win, event):
        if event.keyval == Gdk.KEY_F11:
            if self._is_fullscreen:
                self.unfullscreen()
            else:
                self.fullscreen()
            return True
        return False

    def _on_about(self):
        dlg = Gtk.Dialog(title="About CommentariuM", transient_for=self, flags=0)
        dlg.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        dlg.set_default_size(560, 600)
        content = dlg.get_content_area()
        content.set_spacing(8)

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        head.set_margin_start(18)
        head.set_margin_top(16)
        try:
            pb = render_commentarium_logo_pixbuf(72)
            if pb is not None:
                head.pack_start(Gtk.Image.new_from_pixbuf(pb), False, False, 0)
        except Exception:
            pass
        title = Gtk.Label(xalign=0.0)
        title.set_markup(
            '<span size="xx-large"><b>CommentariuM</b></span>\n'
            "A4 mathematical notebook for engineering calculations"
        )
        head.pack_start(title, False, False, 0)
        content.pack_start(head, False, False, 0)

        parts = []
        for section, items in self.ABOUT_FEATURES:
            parts.append(f"<b>{GLib_markup_escape(section)}</b>")
            parts += [f"  •  {GLib_markup_escape(it)}" for it in items]
            parts.append("")
        body = Gtk.Label(xalign=0.0, yalign=0.0)
        body.set_markup("\n".join(parts))
        body.set_line_wrap(True)
        body.set_selectable(False)
        body.set_margin_start(18)
        body.set_margin_end(18)
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.add(body)
        content.pack_start(scroller, True, True, 0)
        dlg.show_all()
        dlg.run()
        dlg.destroy()

    def _on_canvas_selection_changed(self, box):
        """Hook called by the canvas when the selection changes: enables the align buttons."""
        self._update_align_buttons()

    def _update_align_buttons(self):
        ok = len(self.canvas._alignable_selection()) >= 2
        for name in ("align_left_btn", "align_right_btn"):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.set_sensitive(ok)

    def _make_align_button(self, side: str, tooltip: str) -> Gtk.Button:
        """Toolbar button with a drawn align-left / align-right icon (a guide line and bars of
        different lengths flush against it), in the theme's text colour."""
        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_can_focus(False)
        btn.set_tooltip_text(tooltip)
        icon = Gtk.DrawingArea()
        icon.set_size_request(22, 22)

        def draw(widget, cr):
            w, h = widget.get_allocated_width(), widget.get_allocated_height()
            col = widget.get_style_context().get_color(widget.get_state_flags())
            cr.set_source_rgba(col.red, col.green, col.blue, col.alpha)
            s = min(w, h)
            ox, oy = (w - s) / 2, (h - s) / 2
            u = s / 22.0
            line_x = ox + (3 if side == "left" else 19) * u
            cr.set_line_width(1.6 * u)
            cr.move_to(line_x, oy + 2 * u)
            cr.line_to(line_x, oy + 20 * u)
            cr.stroke()
            for top, length in ((4, 14), (9.5, 8), (15, 11)):
                bx = line_x + 2 * u if side == "left" else line_x - 2 * u - length * u
                cr.rectangle(bx, oy + top * u, length * u, 3.5 * u)
                cr.fill()
            return False

        icon.connect("draw", draw)
        btn.add(icon)
        btn.connect("clicked", lambda _b: self.canvas.align_selected(side))
        btn.connect("state-flags-changed", lambda *_a: icon.queue_draw())
        return btn

    def _on_zoom_updated(self, zoom_val: float):
        pct = int(round(zoom_val * 100))
        if hasattr(self, "zoom_reset_menuitem") and self.zoom_reset_menuitem is not None:
            self.zoom_reset_menuitem.set_label("Reset Zoom  (Ctrl+0)")
        if hasattr(self, "status_label") and self.status_label is not None:
            self.status_label.set_text(
                f"Zoom: {pct}%  |  File: Ctrl+S Save, Ctrl+E Export PDF  |  Images: Drag corner/edges to resize"
            )

    # ------------------------------------------------------------------------
    # File Menu Actions (New, Open, Save, Save As, Export PDF)
    # ------------------------------------------------------------------------

    def _update_window_title(self):
        if self.canvas.current_file_path:
            fname = os.path.basename(self.canvas.current_file_path)
            self.set_title(f"{fname} — CommentariuM")
        else:
            self.set_title("CommentariuM — A4 Mathematical Notebook")

    def _on_file_new(self):
        self.canvas.new_worksheet()
        self._update_window_title()
        if hasattr(self, "status_label"):
            self.status_label.set_text("Created new CommentariuM worksheet.")

    def _on_file_open(self):
        dlg = Gtk.FileChooserDialog(
            title="Open CommentariuM Worksheet",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        flt = Gtk.FileFilter()
        flt.set_name("CommentariuM Worksheet (*.cmm, *.smath, *.json)")
        flt.add_pattern("*.cmm")
        flt.add_pattern("*.smath")
        flt.add_pattern("*.smath.json")
        flt.add_pattern("*.json")
        dlg.add_filter(flt)
        if dlg.run() == Gtk.ResponseType.OK:
            path = dlg.get_filename()
            dlg.destroy()
            if path and os.path.isfile(path):
                try:
                    self.canvas.load_from_file(path)
                    self._add_recent_file(path)
                    self._update_window_title()
                    if hasattr(self, "status_label"):
                        self.status_label.set_text(f"Opened: {path}")
                except Exception as exc:
                    if hasattr(self, "status_label"):
                        self.status_label.set_text(f"Failed to open file: {exc}")
        else:
            dlg.destroy()

    def _on_file_save(self):
        if self.canvas.current_file_path:
            try:
                self.canvas.save_to_file(self.canvas.current_file_path)
                self._add_recent_file(self.canvas.current_file_path)
                self._update_window_title()
                if hasattr(self, "status_label"):
                    self.status_label.set_text(f"Saved: {self.canvas.current_file_path}")
            except Exception as exc:
                if hasattr(self, "status_label"):
                    self.status_label.set_text(f"Error saving file: {exc}")
        else:
            self._on_file_save_as()

    def _on_file_save_as(self):
        dlg = Gtk.FileChooserDialog(
            title="Save CommentariuM Worksheet As",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dlg.set_do_overwrite_confirmation(True)
        default_name = (
            os.path.basename(self.canvas.current_file_path)
            if self.canvas.current_file_path
            else "notebook.cmm.json"
        )
        dlg.set_current_name(default_name)
        if dlg.run() == Gtk.ResponseType.OK:
            path = dlg.get_filename()
            dlg.destroy()
            if path:
                if not (path.endswith(".json") or path.endswith(".smath") or path.endswith(".cmm")):
                    path += ".cmm.json"
                try:
                    self.canvas.save_to_file(path)
                    self._add_recent_file(path)
                    self._update_window_title()
                    if hasattr(self, "status_label"):
                        self.status_label.set_text(f"Saved: {path}")
                except Exception as exc:
                    if hasattr(self, "status_label"):
                        self.status_label.set_text(f"Error saving file: {exc}")
        else:
            dlg.destroy()

    def _on_file_export_pdf(self):
        dlg = Gtk.FileChooserDialog(
            title="Export A4 Worksheet to PDF",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        dlg.set_do_overwrite_confirmation(True)
        dlg.set_current_name("worksheet.pdf")
        flt = Gtk.FileFilter()
        flt.set_name("PDF Document (*.pdf)")
        flt.add_pattern("*.pdf")
        dlg.add_filter(flt)
        if dlg.run() == Gtk.ResponseType.OK:
            path = dlg.get_filename()
            dlg.destroy()
            if path:
                if not path.lower().endswith(".pdf"):
                    path += ".pdf"
                try:
                    self.canvas.export_pdf(path)
                    if hasattr(self, "status_label"):
                        self.status_label.set_text(f"Exported PDF: {path}")
                except Exception as exc:
                    if hasattr(self, "status_label"):
                        self.status_label.set_text(f"Error exporting PDF: {exc}")
        else:
            dlg.destroy()

    def _build_statusbar(self) -> Gtk.Box:
        sbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sbar.set_margin_start(10)
        sbar.set_margin_end(10)
        sbar.set_margin_top(3)
        sbar.set_margin_bottom(3)

        self.status_label = Gtk.Label(
            label="File: Ctrl+S Save, Ctrl+E Export PDF  |  Zoom: Ctrl+Scroll or −/+  |  Images: Drag corner/edges to resize"
        )
        self.status_label.set_xalign(0.0)
        self.status_label.set_ellipsize(Pango.EllipsizeMode.END)
        sbar.pack_start(self.status_label, True, True, 0)
        return sbar

    def _on_toggle_toc(self):
        if self.toc_pane.get_visible():
            self.toc_pane.hide()
        else:
            self.toc_pane.show_all()
            self.toc_pane.refresh()

    def _on_toggle_symbols(self):
        if self.symbols_pane.get_visible():
            self.symbols_pane.hide()
        else:
            self.symbols_pane.show_all()

    def _on_toggle_grid(self, _btn):
        self.canvas.show_grid = not self.canvas.show_grid
        self.canvas.event_box.queue_draw()

    def _on_toggle_theme(self, _btn):
        self.canvas.theme_name = "light" if self.canvas.theme_name == "dark" else "dark"
        self._save_setting("theme", self.canvas.theme_name)
        self.canvas.desk_box.queue_draw()
        self.canvas.event_box.queue_draw()
        for b in self.canvas.boxes:
            b.queue_draw()

    def _populate_starter_examples(self):
        """Create a sample A4 worksheet showcasing multi-level Headings, 2D live equations, sheet functions/vectors, and a 2D Plot."""
        self.canvas.create_text_box(60, 40, style_name="title", text="Engineering Calculation Sheet", edit=False)
        self.canvas.create_text_box(60, 88, style_name="heading1", text="1. Section Properties", edit=False)
        self.canvas.create_text_box(60, 122, style_name="heading2", text="1.1 Circular Cross-Section", edit=False)
        self.canvas.create_text_box(
            60,
            152,
            style_name="normal",
            text="Press Enter inside any box to exit and move down one line. Use the RHS pane for symbols.",
            edit=False,
        )

        # 1) r := 5
        b1 = self.canvas.create_box(60, 185, edit=False)
        b1.insert_char("r")
        b1.insert_char(":=")
        b1.insert_char("5")

        # 2) A := pi * r^2 =
        b2 = self.canvas.create_box(220, 180, edit=False)
        b2.insert_char("A")
        b2.insert_char(":=")
        b2.insert_char("π")
        b2.insert_char("·")
        b2.insert_char("r")
        b2.insert_superscript()
        b2.insert_char("2")
        b2.step_out_slot()
        b2.insert_char("=")

        self.canvas.create_text_box(60, 232, style_name="heading1", text="2. Combined Stress Factor", edit=False)
        self.canvas.create_text_box(60, 266, style_name="heading3", text="2.1.1 Normalized Ratio", edit=False)

        # 3) y := (sqrt(r^2 + 11) + 4) / (2 * r) =
        b3 = self.canvas.create_box(60, 298, edit=False)
        b3.insert_char("y")
        b3.insert_char(":=")
        b3.insert_fraction()
        b3.cursor_seq = b3.root.items[-1].num
        b3.cursor_idx = 0
        b3.insert_sqrt()
        b3.insert_char("r")
        b3.insert_superscript()
        b3.insert_char("2")
        b3.step_out_slot()
        b3.insert_char("+")
        b3.insert_char("1")
        b3.insert_char("1")
        b3.step_out_slot()
        b3.insert_char("+")
        b3.insert_char("4")
        b3.step_out_slot()
        b3.insert_char("2")
        b3.insert_char("·")
        b3.insert_char("r")
        b3.step_out_slot()
        b3.insert_char("=")

        self.canvas.create_text_box(60, 376, style_name="heading1", text="3. Harmonic Response & Measured Data", edit=False)
        self.canvas.create_text_box(
            60,
            410,
            style_name="normal",
            text="Define functions f(x), g(x) for plot lines and vectors vx, vy for discrete plot symbols:",
            edit=False,
        )

        # 4) Sheet Function 1: f(x) := 0.2 · r · sin(x)
        bf = self.canvas.create_box(60, 442, edit=False)
        bf.insert_char("f")
        bf.insert_parens()
        bf.insert_char("x")
        bf.step_out_slot()
        bf.insert_char(":=")
        bf.insert_text_tokens("0.2")
        bf.insert_char("·")
        bf.insert_char("r")
        bf.insert_char("·")
        bf.insert_text_tokens("sin")
        bf.insert_parens()
        bf.insert_char("x")
        bf.step_out_slot()

        # 5) Sheet Function 2: g(x) := 0.5 · cos(x)
        bg = self.canvas.create_box(380, 442, edit=False)
        bg.insert_char("g")
        bg.insert_parens()
        bg.insert_char("x")
        bg.step_out_slot()
        bg.insert_char(":=")
        bg.insert_text_tokens("0.5")
        bg.insert_char("·")
        bg.insert_text_tokens("cos")
        bg.insert_parens()
        bg.insert_char("x")
        bg.step_out_slot()

        # 6) Sheet Vector vx := [-5, -3, -1.5, 0, 1.5, 3, 5]
        bvx = self.canvas.create_box(60, 484, edit=False)
        bvx.insert_text_tokens("vx")
        bvx.insert_char(":=")
        bvx.insert_text_tokens("[-5, -3, -1.5, 0, 1.5, 3, 5]")

        # 7) Sheet Vector vy := [0.92, -0.18, -0.98, 0, 0.99, 0.16, -0.94]
        bvy = self.canvas.create_box(60, 522, edit=False)
        bvy.insert_text_tokens("vy")
        bvy.insert_char(":=")
        bvy.insert_text_tokens("[0.92, -0.18, -0.98, 0, 0.99, 0.16, -0.94]")

        # 8) PlotBox referencing sheet functions "f; g" (lines) and sheet vectors "vx, vy" (symbols)
        self.canvas.create_plot_box(
            60,
            568,
            width=560,
            height=295,
            title="Sine wave and discrete measurements",
            func_expr="f; g",
            discrete_data="vx, vy",
            symbol_style="circle",
            connect_discrete=False,
            x_min=-6.0,
            x_max=6.0,
            y_min=-1.5,
            y_max=1.5,
            x_scale="linear",
            y_scale="linear",
        )

        self.canvas.select_box(None)
        self.canvas.recalculate_worksheet()


if __name__ == "__main__":
    import time

    try:
        _initial_mtime = os.path.getmtime(os.path.abspath(__file__))
    except OSError:
        _initial_mtime = None

    def _auto_reload_on_change():
        if _initial_mtime is not None:
            try:
                cur_mtime = os.path.getmtime(os.path.abspath(__file__))
                if cur_mtime > _initial_mtime and (time.time() - cur_mtime) >= 1.5:
                    os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)] + sys.argv[1:])
            except OSError:
                pass
        return True

    GLib.timeout_add(800, _auto_reload_on_change)
    window = MainWindow()
    window.show_all()
    Gtk.main()
