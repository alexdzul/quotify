from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def dynamic_css(primary_color):
    """
    Genera CSS dinámico basado en el color principal seleccionado
    """
    
    # Mapeo de colores Bootstrap a códigos hexadecimales
    color_map = {
        'primary': '#0d6efd',
        'success': '#198754',
        'info': '#0dcaf0',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'dark': '#212529',
        'purple': '#6f42c1',
        'pink': '#d63384',
        'orange': '#fd7e14',
        'teal': '#20c997',
        'indigo': '#6610f2'
    }
    
    # Obtener el color seleccionado o usar primary por defecto
    color_code = color_map.get(primary_color, color_map['primary'])
    
    # Generar variaciones del color
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    def lighten_color(hex_color, factor=0.2):
        rgb = hex_to_rgb(hex_color)
        lightened = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
        return rgb_to_hex(lightened)
    
    def darken_color(hex_color, factor=0.2):
        rgb = hex_to_rgb(hex_color)
        darkened = tuple(max(0, int(c * (1 - factor))) for c in rgb)
        return rgb_to_hex(darkened)
    
    # Generar variaciones
    primary = color_code
    primary_light = lighten_color(color_code, 0.1)
    primary_lighter = lighten_color(color_code, 0.2)
    primary_dark = darken_color(color_code, 0.1)
    primary_darker = darken_color(color_code, 0.2)
    
    # Generar CSS
    css = f"""
    <style>
        :root {{
            --bs-primary: {primary};
            --bs-primary-rgb: {', '.join(map(str, hex_to_rgb(primary)))};
            --primary-color: {primary};
            --primary-light: {primary_light};
            --primary-lighter: {primary_lighter};
            --primary-dark: {primary_dark};
            --primary-darker: {primary_darker};
        }}
        
        /* Navbar */
        .navbar.bg-primary,
        .bg-primary {{
            background-color: {primary} !important;
        }}
        
        /* Buttons */
        .btn-primary {{
            background-color: {primary};
            border-color: {primary};
        }}
        
        .btn-primary:hover {{
            background-color: {primary_dark};
            border-color: {primary_dark};
        }}
        
        .btn-primary:active,
        .btn-primary.active {{
            background-color: {primary_darker};
            border-color: {primary_darker};
        }}
        
        .btn-outline-primary {{
            color: {primary};
            border-color: {primary};
        }}
        
        .btn-outline-primary:hover {{
            background-color: {primary};
            border-color: {primary};
        }}
        
        /* Sidebar Navigation */
        .sidebar .nav-link.active {{
            background-color: {primary} !important;
            color: white !important;
        }}
        
        .sidebar .nav-link:hover {{
            color: {primary} !important;
        }}
        
        /* Links */
        a {{
            color: {primary};
        }}
        
        a:hover {{
            color: {primary_dark};
        }}
        
        /* Form Controls */
        .form-control:focus,
        .form-select:focus {{
            border-color: {primary};
            box-shadow: 0 0 0 0.2rem {primary}40;
        }}
        
        /* Badges */
        .badge.bg-primary {{
            background-color: {primary} !important;
        }}
        
        /* Text Colors */
        .text-primary {{
            color: {primary} !important;
        }}
        
        /* Borders */
        .border-primary {{
            border-color: {primary} !important;
        }}
        
        /* Status badges - keep original colors but add primary variants */
        .status-badge.status-primary {{
            background-color: {primary};
            color: white;
        }}
        
        /* Cards */
        .card.border-primary {{
            border-color: {primary} !important;
        }}
        
        .card-header.bg-primary {{
            background-color: {primary} !important;
        }}
        
        /* Progress bars */
        .progress-bar {{
            background-color: {primary};
        }}
        
        /* Pagination */
        .page-link {{
            color: {primary};
        }}
        
        .page-item.active .page-link {{
            background-color: {primary};
            border-color: {primary};
        }}
        
        /* Tables */
        .table-primary {{
            background-color: {primary_lighter};
        }}
        
        /* Alerts */
        .alert-primary {{
            color: {primary_darker};
            background-color: {primary_lighter};
            border-color: {primary_light};
        }}
        
        /* Dropdown */
        .dropdown-item:hover,
        .dropdown-item:focus {{
            background-color: {primary_lighter};
        }}
        
        /* Custom elements */
        .text-purple {{
            color: {primary} !important;
        }}
    </style>
    """
    
    return mark_safe(css)


@register.filter
def currency_format(value, currency_symbol='$'):
    """
    Formatea un valor con el símbolo de moneda configurado
    """
    try:
        return f"{currency_symbol}{float(value):,.2f}"
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"


@register.simple_tag
def system_title(default_title="Quotify"):
    """
    Devuelve el título del sistema configurado o el por defecto
    """
    from apps.core.models import SystemSettings
    try:
        settings = SystemSettings.get_settings()
        return settings.system_name or default_title
    except:
        return default_title 