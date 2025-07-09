from django import template
from django.template.defaultfilters import floatformat
import locale

register = template.Library()

@register.filter
def currency_brl(value):
    """
    Formata um valor numérico para moeda brasileira (R$ 10.000,00)
    """
    if value is None:
        return 'R$ 0,00'
    
    try:
        # Converte para float se necessário
        if isinstance(value, str):
            value = float(value)
        
        # Formata com 2 casas decimais
        formatted = floatformat(value, 2)
        
        # Converte ponto para vírgula (decimal brasileiro)
        formatted = formatted.replace('.', ',')
        
        # Adiciona separador de milhares
        parts = formatted.split(',')
        integer_part = parts[0]
        decimal_part = parts[1] if len(parts) > 1 else '00'
        
        # Adiciona pontos como separador de milhares
        if len(integer_part) > 3:
            # Inverte a string para facilitar a inserção dos pontos
            reversed_int = integer_part[::-1]
            grouped = []
            for i in range(0, len(reversed_int), 3):
                grouped.append(reversed_int[i:i+3])
            integer_part = '.'.join(grouped)[::-1]
        
        return f'R$ {integer_part},{decimal_part}'
    
    except (ValueError, TypeError):
        return 'R$ 0,00'

@register.filter
def currency_brl_simple(value):
    """
    Formata um valor numérico para moeda brasileira sem casas decimais (R$ 10.000)
    """
    if value is None:
        return 'R$ 0'
    
    try:
        # Converte para float se necessário
        if isinstance(value, str):
            value = float(value)
        
        # Arredonda para inteiro
        value = round(value)
        
        # Converte para string
        formatted = str(value)
        
        # Adiciona separador de milhares
        if len(formatted) > 3:
            # Inverte a string para facilitar a inserção dos pontos
            reversed_int = formatted[::-1]
            grouped = []
            for i in range(0, len(reversed_int), 3):
                grouped.append(reversed_int[i:i+3])
            formatted = '.'.join(grouped)[::-1]
        
        return f'R$ {formatted}'
    
    except (ValueError, TypeError):
        return 'R$ 0'

@register.filter
def currency_brl_precision(value, precision=2):
    """
    Formata um valor numérico para moeda brasileira com precisão customizada
    """
    if value is None:
        return f'R$ 0,{"0" * precision}'
    
    try:
        # Converte para float se necessário
        if isinstance(value, str):
            value = float(value)
        
        # Formata com precisão especificada
        formatted = floatformat(value, precision)
        
        # Converte ponto para vírgula (decimal brasileiro)
        formatted = formatted.replace('.', ',')
        
        # Adiciona separador de milhares
        parts = formatted.split(',')
        integer_part = parts[0]
        decimal_part = parts[1] if len(parts) > 1 else '0' * precision
        
        # Adiciona pontos como separador de milhares
        if len(integer_part) > 3:
            # Inverte a string para facilitar a inserção dos pontos
            reversed_int = integer_part[::-1]
            grouped = []
            for i in range(0, len(reversed_int), 3):
                grouped.append(reversed_int[i:i+3])
            integer_part = '.'.join(grouped)[::-1]
        
        if precision > 0:
            return f'R$ {integer_part},{decimal_part}'
        else:
            return f'R$ {integer_part}'
    
    except (ValueError, TypeError):
        return f'R$ 0,{"0" * precision}' 