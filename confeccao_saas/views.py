from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from apps.core.models import PlanoAssinatura
from django.db import connection
from django.core.cache import cache
import redis


def home_view(request):
    """
    View da página inicial/landing page
    """
    # Se usuário já está logado, redirecionar para dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Buscar planos para exibir na página
    planos = PlanoAssinatura.objects.all().order_by('preco_mensal')
    
    context = {
        'planos': planos,
        'total_planos': planos.count(),
    }
    
    return render(request, 'home/index.html', context)


def home_temporaria(request):
    """View temporária para testar o sistema - manter compatibilidade"""
    return redirect('home')


def dashboard_redirect(request):
    """Redireciona para dashboard da empresa ou seleção de empresa"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    # Se tem empresa na sessão, vai para dashboard
    if request.session.get('empresa_atual'):
        return redirect('empresas:dashboard')
    else:
        return redirect('empresas:selecionar')


def health_check(request):
    """
    Endpoint de health check para monitoramento
    Verifica status do banco de dados e Redis
    """
    health_status = {
        'status': 'healthy',
        'database': 'unknown',
        'cache': 'unknown',
        'errors': []
    }
    
    # Verificar banco de dados
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['database'] = 'healthy'
    except Exception as e:
        health_status['database'] = 'unhealthy'
        health_status['errors'].append(f'Database error: {str(e)}')
        health_status['status'] = 'unhealthy'
    
    # Verificar cache/Redis
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['cache'] = 'healthy'
        else:
            health_status['cache'] = 'unhealthy'
            health_status['errors'].append('Cache write/read failed')
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['cache'] = 'unhealthy'
        health_status['errors'].append(f'Cache error: {str(e)}')
        health_status['status'] = 'unhealthy'
    
    # Retornar resposta apropriada
    if health_status['status'] == 'healthy':
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse(health_status)
        else:
            return HttpResponse("healthy\n", content_type="text/plain")
    else:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse(health_status, status=503)
        else:
            return HttpResponse("unhealthy\n", content_type="text/plain", status=503) 