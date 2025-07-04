from django.db import models
from django.contrib.auth.models import User
from apps.core.models import Empresa, PlanoAssinatura, AssinaturaEmpresa


class ConfiguracaoEmpresa(models.Model):
    """Configurações específicas da empresa"""
    empresa = models.OneToOneField(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='configuracao'
    )
    
    # Configurações de produção
    dias_uteis_mes = models.IntegerField(default=22, verbose_name="Dias Úteis por Mês")
    horas_trabalho_dia = models.IntegerField(default=8, verbose_name="Horas de Trabalho por Dia")
    
    # Configurações financeiras
    moeda_padrao = models.CharField(max_length=3, default='BRL', verbose_name="Moeda Padrão")
    forma_pagamento_padrao = models.CharField(
        max_length=50, 
        default='À Vista',
        verbose_name="Forma de Pagamento Padrão"
    )
    
    # Configurações de notificação
    notificar_prazo_op = models.BooleanField(default=True, verbose_name="Notificar Prazo de OP")
    dias_antecedencia_prazo = models.IntegerField(default=3, verbose_name="Dias de Antecedência para Prazo")
    
    # Configurações de relatório
    horario_envio_relatorio = models.TimeField(
        null=True, 
        blank=True, 
        verbose_name="Horário de Envio de Relatório Diário"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuração da Empresa"
        verbose_name_plural = "Configurações das Empresas"
    
    def __str__(self):
        return f"Configurações - {self.empresa.nome}"


class EmpresaStatus(models.Model):
    """Status e estatísticas da empresa"""
    empresa = models.OneToOneField(
        Empresa, 
        on_delete=models.CASCADE, 
        related_name='status'
    )
    
    # Estatísticas gerais
    total_ops_mes = models.IntegerField(default=0, verbose_name="Total de OPs no Mês")
    faturamento_mes = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Faturamento do Mês"
    )
    
    # Status operacional
    ops_atrasadas = models.IntegerField(default=0, verbose_name="OPs Atrasadas")
    capacidade_utilizada = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="Capacidade Utilizada (%)"
    )
    
    # Última atualização
    ultima_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Status da Empresa"
        verbose_name_plural = "Status das Empresas"
    
    def __str__(self):
        return f"Status - {self.empresa.nome}"
