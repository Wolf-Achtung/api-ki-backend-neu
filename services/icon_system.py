"""
KI-Sicherheit.jetzt Custom Icon System
Inline-SVG Icons für PDF-Reports - Puppeteer-optimiert
"""

import re

# Brand Color Palette
COLORS = {
    "blue-dark": "#1e3a5f",
    "blue-mid": "#2d5a87",
    "blue-light": "#4a90c2",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#3b82f6",
    "purple": "#8b5cf6",
    "teal": "#14b8a6",
    "gray": "#4b5563",
}

# SVG Icon Definitions (24x24 viewBox)
ICONS = {
    # ═══════════════════════════════════════════
    # STATUS ICONS
    # ═══════════════════════════════════════════

    "success": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>''',
        "default_color": "success",
    },

    "check": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
        </svg>''',
        "default_color": "success",
    },

    "warning": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>''',
        "default_color": "warning",
    },

    "danger": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>''',
        "default_color": "danger",
    },

    "info": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>''',
        "default_color": "info",
    },

    # ═══════════════════════════════════════════
    # CONCEPT ICONS
    # ═══════════════════════════════════════════

    "security": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <polyline points="9 12 11 14 15 10"/>
        </svg>''',
        "default_color": "blue-dark",
    },

    "lock": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>''',
        "default_color": "blue-dark",
    },

    "lightbulb": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 18h6"/>
            <path d="M10 22h4"/>
            <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
        </svg>''',
        "default_color": "warning",
    },

    "target": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <circle cx="12" cy="12" r="6"/>
            <circle cx="12" cy="12" r="2"/>
        </svg>''',
        "default_color": "purple",
    },

    "rocket": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
            <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
            <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
            <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
        </svg>''',
        "default_color": "purple",
    },

    "star": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{color}" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>''',
        "default_color": "warning",
    },

    # ═══════════════════════════════════════════
    # TREND ICONS
    # ═══════════════════════════════════════════

    "trend-up": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
            <polyline points="17 6 23 6 23 12"/>
        </svg>''',
        "default_color": "success",
    },

    "trend-down": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
            <polyline points="17 18 23 18 23 12"/>
        </svg>''',
        "default_color": "danger",
    },

    # ═══════════════════════════════════════════
    # OBJECT ICONS
    # ═══════════════════════════════════════════

    "clock": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
        </svg>''',
        "default_color": "info",
    },

    "document": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
        </svg>''',
        "default_color": "gray",
    },

    "euro": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M14.5 9.5a3.5 3.5 0 0 0-5 0L9 10"/>
            <path d="M14.5 14.5a3.5 3.5 0 0 1-5 0L9 14"/>
            <line x1="7" y1="12" x2="17" y2="12"/>
        </svg>''',
        "default_color": "success",
    },

    "users": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>''',
        "default_color": "blue-mid",
    },

    "settings": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>''',
        "default_color": "gray",
    },

    "chart": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
        </svg>''',
        "default_color": "info",
    },

    "checklist": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
        </svg>''',
        "default_color": "success",
    },

    "arrow-right": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
        </svg>''',
        "default_color": "blue-mid",
    },

    "play": {
        "svg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{color}" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>''',
        "default_color": "success",
    },
}


# ═══════════════════════════════════════════════════════════════
# EMOJI TO ICON MAPPING
# ═══════════════════════════════════════════════════════════════

EMOJI_MAP = {
    # Status
    "✅": "success",
    "✓": "check",
    "☑": "check",
    "⚠️": "warning",
    "⚠": "warning",
    "❌": "danger",
    "✗": "danger",
    "❎": "danger",
    "ℹ️": "info",
    "ℹ": "info",

    # Concepts
    "🔒": "lock",
    "🔐": "lock",
    "🛡️": "security",
    "🛡": "security",
    "💡": "lightbulb",
    "🎯": "target",
    "🚀": "rocket",
    "🛣️": "rocket",  # Road/Implementation → rocket icon
    "🛣": "rocket",   # Variant without selector
    "⭐": "star",
    "✨": "star",
    "⚡": "lightbulb",

    # Trends
    "📈": "trend-up",
    "📉": "trend-down",
    "↑": "trend-up",
    "↓": "trend-down",

    # Objects
    "⏱️": "clock",
    "⏰": "clock",
    "⏳": "clock",
    "🕐": "clock",
    "📄": "document",
    "📋": "document",
    "📝": "document",
    "💶": "euro",
    "💰": "euro",
    "👥": "users",
    "👤": "users",
    "⚙️": "settings",
    "🔧": "settings",
    "📊": "chart",
    "📌": "target",
    "▶️": "play",
    "▶": "play",
    "→": "arrow-right",
    "➡️": "arrow-right",
}


# ═══════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════

def get_icon(name: str, size: int = 20, color: str = None) -> str:
    """
    Get an SVG icon by name.

    Args:
        name: Icon name (e.g., 'success', 'warning', 'security')
        size: Icon size in pixels (default: 20)
        color: Color name from palette or hex code (default: icon's default)

    Returns:
        Inline SVG string with specified size and color

    Example:
        get_icon('success', 16)  # Small green checkmark
        get_icon('warning', 24, 'danger')  # Warning icon in red
    """
    if name not in ICONS:
        name = "info"  # Fallback

    icon_def = ICONS[name]
    svg = icon_def["svg"]

    # Resolve color
    if color is None:
        color = icon_def["default_color"]

    if color in COLORS:
        color_hex = COLORS[color]
    elif color.startswith("#"):
        color_hex = color
    else:
        color_hex = COLORS.get(color, "#4b5563")

    # Apply color and size
    svg = svg.replace("{color}", color_hex)
    svg = svg.replace('viewBox=', f'width="{size}" height="{size}" style="vertical-align: middle; flex-shrink: 0;" viewBox=')

    return svg


def get_icon_inline(name: str, size: int = 16, color: str = None) -> str:
    """
    Get icon formatted for inline text use (with proper spacing).
    """
    icon = get_icon(name, size, color)
    return f'<span style="display: inline-flex; align-items: center; margin-right: 4px;">{icon}</span>'


def replace_emojis_with_icons(text: str, size: int = 18) -> str:
    """
    Replace all emojis in text with corresponding SVG icons.

    Args:
        text: Text containing emojis
        size: Icon size in pixels

    Returns:
        Text with emojis replaced by inline SVG icons
    """
    if not text:
        return text

    # Decode numeric HTML entities in the emoji/symbol code ranges first, so a
    # template that wrote e.g. "&#x1F4CB;" instead of the literal "📋" still gets
    # replaced by an SVG icon (otherwise Chromium has no emoji font -> tofu box).
    # Only symbol/emoji codepoints are decoded; ASCII/latin entities are untouched.
    def _decode_emoji_entity(m):
        raw = m.group(1)
        cp = int(raw[1:], 16) if raw[0] in ("x", "X") else int(raw)
        if cp >= 0x1F000 or 0x2190 <= cp <= 0x2BFF:
            return chr(cp)
        return m.group(0)

    text = re.sub(r'&#(x[0-9A-Fa-f]+|\d+);', _decode_emoji_entity, text)

    for emoji, icon_name in EMOJI_MAP.items():
        if emoji in text:
            icon_html = get_icon_inline(icon_name, size)
            text = text.replace(emoji, icon_html)

    return text


def get_status_badge(text: str, status: str = "info", size: int = 14) -> str:
    """
    Create a status badge with icon.

    Args:
        text: Badge text (e.g., "HOCH", "MITTEL", "NIEDRIG")
        status: Status type ('success', 'warning', 'danger', 'info')
        size: Icon size

    Returns:
        HTML string for styled badge
    """
    bg_colors = {
        "success": "#dcfce7",
        "warning": "#fef3c7",
        "danger": "#fee2e2",
        "info": "#dbeafe",
    }
    text_colors = {
        "success": "#166534",
        "warning": "#92400e",
        "danger": "#b91c1c",
        "info": "#1e40af",
    }

    icon_map = {
        "success": "check",
        "warning": "warning",
        "danger": "danger",
        "info": "info",
    }

    bg = bg_colors.get(status, bg_colors["info"])
    txt = text_colors.get(status, text_colors["info"])
    icon_name = icon_map.get(status, "info")
    icon = get_icon(icon_name, size, status)

    return f'''<span style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; background: {bg}; color: {txt};">{icon}{text}</span>'''


def get_callout(title: str, text: str, status: str = "info", size: int = 22) -> str:
    """
    Create a callout box with icon.

    Args:
        title: Callout title
        text: Callout body text
        status: Status type ('success', 'warning', 'danger', 'info')
        size: Icon size

    Returns:
        HTML string for styled callout
    """
    bg_colors = {
        "success": "#dcfce7",
        "warning": "#fef3c7",
        "danger": "#fee2e2",
        "info": "#dbeafe",
    }
    border_colors = {
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#3b82f6",
    }

    icon_map = {
        "success": "success",
        "warning": "warning",
        "danger": "danger",
        "info": "info",
    }

    bg = bg_colors.get(status, bg_colors["info"])
    border = border_colors.get(status, border_colors["info"])
    icon_name = icon_map.get(status, "info")
    icon = get_icon(icon_name, size, status)

    return f'''<div style="display: flex; gap: 12px; padding: 12px 16px; border-radius: 8px; background: {bg}; border-left: 4px solid {border}; margin: 12px 0;">
        {icon}
        <div>
            <div style="font-weight: 600; margin-bottom: 2px;">{title}</div>
            <div style="font-size: 14px; color: #4b5563;">{text}</div>
        </div>
    </div>'''


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE EXPORTS
# ═══════════════════════════════════════════════════════════════

# Pre-built commonly used icons (for direct use in templates)
ICON_SUCCESS = get_icon("success", 18)
ICON_WARNING = get_icon("warning", 18)
ICON_DANGER = get_icon("danger", 18)
ICON_INFO = get_icon("info", 18)
ICON_CHECK = get_icon("check", 18)
ICON_SECURITY = get_icon("security", 18)
ICON_LIGHTBULB = get_icon("lightbulb", 18)
ICON_ROCKET = get_icon("rocket", 18)
ICON_STAR = get_icon("star", 18)
ICON_CLOCK = get_icon("clock", 18)
ICON_EURO = get_icon("euro", 18)
ICON_TREND_UP = get_icon("trend-up", 18)
ICON_TREND_DOWN = get_icon("trend-down", 18)
