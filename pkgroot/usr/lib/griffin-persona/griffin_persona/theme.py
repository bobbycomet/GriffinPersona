"""
Griffin Persona — Steam-dark visual theme.

Palette is modeled on Steam's classic dark client chrome:
  - deep navy backgrounds (#171a21 / #1b2838)
  - slate panel blue (#2a475e)
  - Steam link blue accent (#66c0f4 / #1999ff)
  - Steam "owned/positive" green (#a4d007 / #5c7e10)
  - warm amber for warnings, soft red for failures
"""

COLORS = {
    "bg_darkest": "#0e1116",
    "bg_dark": "#171a21",
    "bg_base": "#1b2838",
    "bg_panel": "#202f3e",
    "bg_panel_raised": "#2a475e",
    "bg_input": "#16202a",
    "border": "#0a0e13",
    "border_light": "#3c5366",
    "text_primary": "#c7d5e0",
    "text_secondary": "#8f98a0",
    "text_dim": "#67707a",
    "accent": "#66c0f4",
    "accent_strong": "#1999ff",
    "accent_pressed": "#0e6fb8",
    "good": "#a4d007",
    "good_strong": "#5c7e10",
    "warn": "#e3a01a",
    "bad": "#e0524d",
}

STYLESHEET = f"""
QWidget {{
    background-color: {COLORS['bg_base']};
    color: {COLORS['text_primary']};
    font-family: "Motiva Sans", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

/* ---------- Sidebar navigation ---------- */
QListWidget#Sidebar {{
    background-color: {COLORS['bg_darkest']};
    border: none;
    border-right: 1px solid {COLORS['border']};
    outline: 0;
    padding: 6px 0px;
}}
QListWidget#Sidebar::item {{
    padding: 10px 18px;
    margin: 1px 6px;
    border-radius: 3px;
    color: {COLORS['text_secondary']};
}}
QListWidget#Sidebar::item:selected {{
    background-color: {COLORS['bg_panel_raised']};
    color: white;
    border-left: 3px solid {COLORS['accent']};
}}
QListWidget#Sidebar::item:hover:!selected {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_primary']};
}}

/* ---------- Headers / labels ---------- */
QLabel#PageTitle {{
    font-size: 20px;
    font-weight: 600;
    color: white;
}}
QLabel#PageSubtitle {{
    color: {COLORS['text_secondary']};
    font-size: 13px;
}}
QLabel#SectionHeader {{
    font-size: 14px;
    font-weight: 600;
    color: {COLORS['accent']};
    padding-top: 4px;
}}
QLabel#Muted {{
    color: {COLORS['text_secondary']};
}}
QLabel#Badge {{
    background-color: {COLORS['good_strong']};
    color: white;
    border-radius: 3px;
    padding: 1px 6px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel#BadgeOptional {{
    background-color: {COLORS['bg_panel_raised']};
    color: {COLORS['text_secondary']};
    border-radius: 3px;
    padding: 1px 6px;
    font-size: 11px;
}}

/* ---------- Cards / group boxes ---------- */
QFrame#Card {{
    background-color: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}
QGroupBox {{
    background-color: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 600;
    color: {COLORS['accent']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}}

/* ---------- Buttons ---------- */
QPushButton {{
    background-color: {COLORS['bg_panel_raised']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 7px 16px;
}}
QPushButton:hover {{
    background-color: #355169;
    color: white;
}}
QPushButton:pressed {{
    background-color: {COLORS['accent_pressed']};
}}
QPushButton:disabled {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_dim']};
    border-color: {COLORS['border']};
}}
QPushButton#Primary {{
    background-color: {COLORS['accent_strong']};
    border: 1px solid {COLORS['accent_strong']};
    color: white;
    font-weight: 600;
}}
QPushButton#Primary:hover {{
    background-color: {COLORS['accent']};
}}
QPushButton#Danger {{
    background-color: #5c2120;
    border: 1px solid {COLORS['bad']};
    color: #ffd3d1;
}}
QPushButton#Danger:hover {{
    background-color: {COLORS['bad']};
    color: white;
}}
QPushButton#Link {{
    background: transparent;
    border: none;
    color: {COLORS['accent']};
    text-decoration: underline;
    padding: 2px;
}}

/* ---------- Inputs ---------- */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 4px;
    padding: 5px 8px;
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent_strong']};
}}
QComboBox::drop-down {{ border: none; }}

/* ---------- Checkboxes ---------- */
QCheckBox {{
    spacing: 8px;
    color: {COLORS['text_primary']};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS['border_light']};
    border-radius: 3px;
    background-color: {COLORS['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_strong']};
    border-color: {COLORS['accent_strong']};
}}
QCheckBox::indicator:disabled {{
    background-color: {COLORS['bg_panel']};
    border-color: {COLORS['border']};
}}

/* ---------- Lists / tables ---------- */
QListWidget, QTreeWidget, QTableWidget {{
    background-color: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    gridline-color: {COLORS['border']};
}}
QHeaderView::section {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    padding: 5px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
}}
QTreeWidget::item, QTableWidget::item {{
    padding: 4px;
}}
QTreeWidget::item:selected, QTableWidget::item:selected {{
    background-color: {COLORS['bg_panel_raised']};
}}

/* ---------- Progress bar ---------- */
QProgressBar {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    text-align: center;
    color: {COLORS['text_primary']};
    height: 16px;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent_strong']};
    border-radius: 3px;
}}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 11px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['bg_panel_raised']};
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['border_light']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

/* ---------- Tabs ---------- */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background: {COLORS['bg_panel']};
}}
QTabBar::tab {{
    background: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    padding: 7px 14px;
    border: 1px solid {COLORS['border']};
    border-bottom: none;
}}
QTabBar::tab:selected {{
    background: {COLORS['bg_panel']};
    color: white;
}}

/* ---------- Status pills (diagnostics) ---------- */
QLabel#StatusOk {{ color: {COLORS['good']}; font-weight: 600; }}
QLabel#StatusWarn {{ color: {COLORS['warn']}; font-weight: 600; }}
QLabel#StatusBad {{ color: {COLORS['bad']}; font-weight: 600; }}

QToolTip {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_light']};
    padding: 4px;
}}

QStatusBar {{
    background: {COLORS['bg_darkest']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
}}

QSplitter::handle {{
    background-color: {COLORS['border']};
}}
"""
