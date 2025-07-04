from django.utils.deprecation import MiddlewareMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from .models import Empresa, UsuarioEmpresa
import threading

# Thread local para armazenar a empresa atual
_thread_locals = threading.local()


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware para detectar e configurar a empresa atual (tenant).
    Responsável por:
    1. Identificar qual empresa o usuário está acessando
    2. Validar se o usuário tem acesso à empresa
    3. Configurar contexto global da empresa
    4. Redirecionar para seleção de empresa se necessário
    """
    
    def process_request(self, request):
        # Limpar contexto anterior
        set_current_empresa(None)
        set_current_user(None)
        
        # URLs que não precisam de empresa (login, registro, etc)
        bypass_urls = [
            '/admin/',
            '/accounts/',
            '/api/public/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        # Verificar se a URL atual precisa de empresa
        if any(request.path.startswith(url) for url in bypass_urls):
            return None
        
        # Se usuário não estiver logado, permitir acesso às páginas públicas
        if isinstance(request.user, AnonymousUser):
            return None
        
        # Tentar obter empresa da sessão
        empresa_id = request.session.get('empresa_atual')
        
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=empresa_id, ativa=True)
                
                # Verificar se usuário tem acesso à empresa
                if self._usuario_tem_acesso_empresa(request.user, empresa):
                    set_current_empresa(empresa)
                    set_current_user(request.user)
                    request.empresa_atual = empresa
                    return None
                else:
                    # Usuário não tem acesso, limpar sessão
                    del request.session['empresa_atual']
                    
            except Empresa.DoesNotExist:
                # Empresa não existe, limpar sessão
                if 'empresa_atual' in request.session:
                    del request.session['empresa_atual']
        
        # Se chegou aqui, precisa selecionar empresa
        # Verificar se usuário tem empresas disponíveis
        empresas_usuario = self._get_empresas_usuario(request.user)
        
        if not empresas_usuario:
            # Usuário não tem empresas, redirecionar para criar empresa
            if request.path != reverse('empresas:criar'):
                return redirect('empresas:criar')
        else:
            # Usuário tem empresas, redirecionar para seleção
            if request.path != reverse('empresas:selecionar'):
                return redirect('empresas:selecionar')
        
        return None
    
    def _usuario_tem_acesso_empresa(self, user, empresa):
        """Verifica se usuário tem acesso à empresa"""
        return UsuarioEmpresa.objects.filter(
            usuario=user,
            empresa=empresa,
            ativo=True
        ).exists()
    
    def _get_empresas_usuario(self, user):
        """Retorna empresas que o usuário tem acesso"""
        return Empresa.objects.filter(
            usuarioempresa__usuario=user,
            usuarioempresa__ativo=True,
            ativa=True
        ).distinct()


class TenantQueryMiddleware(MiddlewareMixin):
    """
    Middleware para automaticamente filtrar queries por empresa.
    Este middleware é aplicado após o TenantMiddleware.
    """
    
    def process_request(self, request):
        # Configurar filtros automáticos baseados na empresa atual
        empresa_atual = get_current_empresa()
        if empresa_atual:
            # TODO: Implementar filtro automático nas queries
            # Será usado pelos managers customizados
            pass
        
        return None


# Funções utilitárias para acessar dados do thread local

def set_current_empresa(empresa):
    """Define a empresa atual no contexto thread-local"""
    _thread_locals.empresa = empresa


def get_current_empresa():
    """Retorna a empresa atual do contexto thread-local"""
    return getattr(_thread_locals, 'empresa', None)


def set_current_user(user):
    """Define o usuário atual no contexto thread-local"""
    _thread_locals.user = user


def get_current_user():
    """Retorna o usuário atual do contexto thread-local"""
    return getattr(_thread_locals, 'user', None)


def require_empresa(view_func):
    """
    Decorator para views que exigem empresa selecionada.
    Uso: @require_empresa
    """
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'empresa_atual') or not request.empresa_atual:
            return redirect('empresas:selecionar')
        return view_func(request, *args, **kwargs)
    
    wrapper.__name__ = view_func.__name__
    wrapper.__doc__ = view_func.__doc__
    return wrapper


def get_user_empresas(user):
    """Retorna todas as empresas que o usuário tem acesso"""
    return Empresa.objects.filter(
        usuarioempresa__usuario=user,
        usuarioempresa__ativo=True,
        ativa=True
    ).distinct()


def get_user_role_in_empresa(user, empresa):
    """Retorna o role do usuário na empresa específica"""
    try:
        usuario_empresa = UsuarioEmpresa.objects.get(
            usuario=user,
            empresa=empresa,
            ativo=True
        )
        return usuario_empresa.role
    except UsuarioEmpresa.DoesNotExist:
        return None 