from .middleware import get_current_empresa, get_current_user, get_user_role_in_empresa
from datetime import datetime, date
from django.utils import timezone


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


def plano_info(request):
    """
    Context processor que adiciona informações do plano da empresa
    em todos os templates.
    """
    context = {}
    
    # Empresa atual
    empresa_atual = get_current_empresa()
    if not empresa_atual:
        return context
    
    # Informações básicas do plano
    plano_info_data = {
        'nome': 'Plano Básico',
        'preco_mensal': 0.00,
        'is_trial': True,
        'mostrar_contador': True,
        'dias_restantes': 30,
        'dias_para_vencimento': 30,
        'data_vencimento': date.today(),
        'proximo_vencimento': date.today(),
        'urgencia': 'normal',
        'cor_status': 'success',
        'icone_status': 'check-circle',
        'mensagem_status': 'Plano ativo',
    }
    
    # Verificar se há assinatura na empresa
    try:
        from apps.empresas.models import AssinaturaEmpresa
        assinatura = AssinaturaEmpresa.objects.filter(empresa=empresa_atual).first()
        
        if assinatura:
            plano_info_data.update({
                'nome': assinatura.plano.nome if hasattr(assinatura, 'plano') else 'Plano Básico',
                'preco_mensal': float(assinatura.plano.preco_mensal) if hasattr(assinatura, 'plano') else 0.00,
            })
            
            # Calcular status baseado na assinatura
            if assinatura.trial_ativo:
                if assinatura.trial_fim:
                    dias_restantes = (assinatura.trial_fim.date() - date.today()).days
                    plano_info_data.update({
                        'is_trial': True,
                        'dias_restantes': max(0, dias_restantes),
                        'data_vencimento': assinatura.trial_fim.date(),
                    })
                    
                    # Definir urgência baseada nos dias restantes
                    if dias_restantes <= 3:
                        plano_info_data.update({
                            'urgencia': 'critico',
                            'cor_status': 'danger',
                            'icone_status': 'exclamation-triangle',
                            'mensagem_status': f'Trial expira em {dias_restantes} dias!',
                        })
                    elif dias_restantes <= 7:
                        plano_info_data.update({
                            'urgencia': 'urgente',
                            'cor_status': 'warning',
                            'icone_status': 'exclamation-circle',
                            'mensagem_status': f'Trial expira em {dias_restantes} dias',
                        })
                    elif dias_restantes <= 15:
                        plano_info_data.update({
                            'urgencia': 'atencao',
                            'cor_status': 'info',
                            'icone_status': 'info-circle',
                            'mensagem_status': f'Trial expira em {dias_restantes} dias',
                        })
    except ImportError:
        # Se o modelo não existir ainda, usar valores padrão
        pass
    except Exception:
        # Em caso de qualquer erro, usar valores padrão
        pass
    
    context['plano_info'] = plano_info_data
    return context 