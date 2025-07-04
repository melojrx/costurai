"""
URL configuration for ConfecçãoManager Pro SaaS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home_view, home_temporaria, dashboard_redirect, health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Home/Landing
    path('', home_view, name='home'),
    path('home/', home_temporaria, name='home_temporaria'),
    
    # Dashboard redirect
    path('dashboard/', dashboard_redirect, name='dashboard'),
    
    # Apps
    path('auth/', include('apps.accounts.urls', namespace='accounts')),
    path('empresas/', include('apps.empresas.urls', namespace='empresas')),
    path('cadastros/', include('apps.cadastros.urls', namespace='cadastros')),
    path('producao/', include('apps.producao.urls', namespace='producao')),
    path('financeiro/', include('apps.financeiro.urls', namespace='financeiro')),
    path('relatorios/', include('apps.relatorios.urls', namespace='relatorios')),
    path('api/', include('apps.api.urls', namespace='api')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
