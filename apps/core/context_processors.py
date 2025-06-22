from .models import SystemSettings

def system_settings(request):
    """
    Context processor para hacer las configuraciones del sistema
    disponibles en todos los templates
    """
    try:
        settings = SystemSettings.get_settings()
        return {
            'system_settings': settings,
            'system_name': settings.system_name,
            'primary_color': settings.primary_color,
            'currency_symbol': settings.currency_symbol,
            'currency_code': settings.currency_code,
            'quotation_prefix': settings.quotation_number_prefix,
        }
    except Exception:
        # Fallback values if settings don't exist
        return {
            'system_settings': None,
            'system_name': 'Quotify',
            'primary_color': 'primary',
            'currency_symbol': '$',
            'currency_code': 'MXN',
            'quotation_prefix': 'S',
        } 