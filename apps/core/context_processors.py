from .middleware import get_current_empresa, get_current_user, get_user_role_in_empresa


def empresa_context(request):
    """
    Context processor que adiciona informações da empresa atual
    e do usuário em todos os templates.
    """
    context = {}
    
    # Empresa atual
    empresa_atual = get_current_empresa()
    if empresa_atual:
        context['empresa_atual'] = empresa_atual
    
    # Usuário atual
    user_atual = get_current_user()
    if user_atual and empresa_atual:
        # Role do usuário na empresa atual
        user_role = get_user_role_in_empresa(user_atual, empresa_atual)
        context['user_role'] = user_role
        
        # Permissões baseadas no role
        context['can_admin'] = user_role == 'ADMIN'
        context['can_manage'] = user_role in ['ADMIN', 'GERENTE']
        context['can_operate'] = user_role in ['ADMIN', 'GERENTE', 'OPERADOR']
        context['can_view'] = user_role in ['ADMIN', 'GERENTE', 'OPERADOR', 'VIEWER']
    
    return context 