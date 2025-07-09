from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F, Avg
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import date, datetime, timedelta
import json

# REST Framework imports
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.filters import SearchFilter, OrderingFilter

# Local imports
from .models import (
    OrdemProducao, 
    GradeProducao, 
    Departamento,
    ConsumoMateriaPrima, 
    StatusOP
)

# Serializers (serão refatorados ou removidos)
# from .serializers import (
#     OrdemProducaoListSerializer, OrdemProducaoDetailSerializer,
#     OrdemProducaoCreateUpdateSerializer, DepartamentoSerializer,
#     CapacidadeProducaoSerializer, ProcessoProducaoSerializer,
#     BulkUpdateStatusSerializer, BulkUpdateProgressSerializer,
#     DashboardStatsSerializer
# )

from apps.core.mixins import TenantMixin
from apps.core.middleware import get_current_empresa
from apps.cadastros import services as cadastros_services
from django.http import HttpResponseRedirect


# As views abaixo foram temporariamente desativadas durante a refatoração
# do app de produção. Elas serão reescritas ou reativadas conforme
# a nova estrutura simplificada do app.

@login_required
def dashboard_producao(request):
    """Dashboard principal do módulo de produção (simplificado)"""
    empresa = get_current_empresa()
    
    # Estatísticas básicas
    stats = {
        'ops_ativas': OrdemProducao.objects.filter(empresa=empresa, status__in=['CADASTRADA', 'EM_PRODUCAO']).count(),
        'ops_em_producao': OrdemProducao.objects.filter(empresa=empresa, status='EM_PRODUCAO').count(),
        'ops_concluidas': OrdemProducao.objects.filter(empresa=empresa, status='CONCLUIDA').count(),
        'ops_atrasadas': OrdemProducao.objects.filter(
            empresa=empresa, 
            data_previsao__lt=timezone.now().date(), 
            status__in=['CADASTRADA', 'EM_PRODUCAO']
        ).count(),
    }
    
    context = {
        'stats': stats,
        'empresa': empresa,
    }
    
    return render(request, 'producao/dashboard_producao.html', context)


class OrdemProducaoListView(LoginRequiredMixin, TenantMixin, ListView):
    model = OrdemProducao
    template_name = 'producao/ops_listar.html'
    context_object_name = 'ops'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # Adicionar filtros aqui se necessário
        return queryset.select_related('cliente', 'produto').order_by('-data_entrada')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = StatusOP.choices
        # Adicionar outras estatísticas aqui se necessário
        return context

class OrdemProducaoDetailView(LoginRequiredMixin, TenantMixin, DetailView):
    model = OrdemProducao
    template_name = 'producao/op_detalhes.html'
    context_object_name = 'op'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        op = self.get_object()
        context['grade'] = op.itens_grade.all().order_by('tamanho')
        context['materias'] = op.materias_primas.select_related('materia_prima').all()
        return context


class OrdemProducaoCreateView(LoginRequiredMixin, TenantMixin, CreateView):
    model = OrdemProducao
    template_name = 'producao/op_form.html'
    fields = ['op_externa', 'data_previsao', 'cliente', 'produto', 'preco_unitario', 'prioridade', 'observacoes']

    def get_success_url(self):
        return reverse('producao:op_detalhes', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.empresa = self.request.empresa_atual
        
        # Chama o método original, que salva o objeto e retorna a resposta de redirect
        response = super().form_valid(form)
        
        # self.object agora está disponível e salvo no banco
        if self.object.produto:
            cadastros_services.copiar_ficha_tecnica_para_op(
                produto=self.object.produto,
                ordem_producao=self.object
            )
        
        # A lógica de salvar a grade precisará ser refeita com formsets
        return response

class OrdemProducaoUpdateView(LoginRequiredMixin, TenantMixin, UpdateView):
    model = OrdemProducao
    template_name = 'producao/op_form.html'
    fields = ['op_externa', 'data_previsao', 'cliente', 'produto', 'preco_unitario', 'prioridade', 'observacoes', 'status']
    
    def get_success_url(self):
        return reverse('producao:op_detalhes', kwargs={'pk': self.object.pk})
