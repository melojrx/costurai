#!/usr/bin/env python
"""
Script para configuração inicial do ConfecçãoManager Pro SaaS
Cria planos de assinatura e configurações necessárias
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confeccao_saas.settings')
django.setup()

from apps.core.models import PlanoAssinatura


def criar_planos_assinatura():
    """Cria os planos de assinatura padrão"""
    
    planos = [
        {
            'nome': 'Gratuito',
            'tipo': 'GRATUITO',
            'descricao': 'Perfeito para começar - 30 dias de teste com funcionalidades básicas',
            'preco_mensal': Decimal('0.00'),
            'max_empresas': 1,
            'max_ops_mes': 50,
            'max_usuarios': 2,
            'tem_api': False,
            'tem_relatorios_avancados': False,
            'tem_suporte_prioritario': False,
        },
        {
            'nome': 'Básico',
            'tipo': 'BASICO',
            'descricao': 'Ideal para pequenas confecções com até 100 ordens de produção por mês',
            'preco_mensal': Decimal('49.00'),
            'max_empresas': 1,
            'max_ops_mes': 100,
            'max_usuarios': 5,
            'tem_api': False,
            'tem_relatorios_avancados': True,
            'tem_suporte_prioritario': True,
        },
        {
            'nome': 'Profissional',
            'tipo': 'PROFISSIONAL',
            'descricao': 'Para confecções em crescimento que precisam de mais recursos e integrações',
            'preco_mensal': Decimal('99.00'),
            'max_empresas': 3,
            'max_ops_mes': 500,
            'max_usuarios': 15,
            'tem_api': True,
            'tem_relatorios_avancados': True,
            'tem_suporte_prioritario': True,
        },
        {
            'nome': 'Enterprise',
            'tipo': 'ENTERPRISE',
            'descricao': 'Solução completa para grandes confecções com recursos ilimitados',
            'preco_mensal': Decimal('199.00'),
            'max_empresas': 999,  # Praticamente ilimitado
            'max_ops_mes': 9999,  # Praticamente ilimitado
            'max_usuarios': 999,  # Praticamente ilimitado
            'tem_api': True,
            'tem_relatorios_avancados': True,
            'tem_suporte_prioritario': True,
        },
    ]
    
    print("🔄 Criando planos de assinatura...")
    
    for plano_data in planos:
        plano, created = PlanoAssinatura.objects.get_or_create(
            nome=plano_data['nome'],
            defaults=plano_data
        )
        
        if created:
            print(f"✅ Plano '{plano.nome}' criado com sucesso!")
        else:
            print(f"ℹ️  Plano '{plano.nome}' já existe")
            # Atualizar dados do plano existente
            for key, value in plano_data.items():
                setattr(plano, key, value)
            plano.save()
            print(f"🔄 Plano '{plano.nome}' atualizado")
    
    print(f"\n🎉 {len(planos)} planos configurados com sucesso!")


def main():
    """Função principal do script"""
    print("=" * 60)
    print("🚀 CONFIGURAÇÃO INICIAL - COSTURAI.COM.BR SAAS")
    print("=" * 60)
    print()
    
    try:
        # Aplicar migrações primeiro
        print("📦 Aplicando migrações...")
        os.system('python manage.py migrate')
        print()
        
        # Criar planos de assinatura
        criar_planos_assinatura()
        print()
        
        # Resumo final
        total_planos = PlanoAssinatura.objects.count()
        print("=" * 60)
        print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📊 Total de planos disponíveis: {total_planos}")
        print()
        print("🌐 Para acessar o sistema:")
        print("   python manage.py runserver 8001")
        print("   http://127.0.0.1:8001/")
        print()
        print("🛠️  Para acessar o admin:")
        print("   http://127.0.0.1:8001/admin/")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro durante a configuração: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main() 