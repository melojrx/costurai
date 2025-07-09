from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Count, Sum, Q

from apps.core.models import (
    Empresa, PlanoAssinatura, AssinaturaEmpresa, 
    UsuarioEmpresa
)
from apps.accounts.models import UserProfile
from apps.core.middleware import get_user_empresas, require_empresa, get_current_empresa
from .models import ConfiguracaoEmpresa, EmpresaStatus
from apps.cadastros.models import Cliente
from apps.producao.models import OrdemProducao
from apps.financeiro.models import ContaReceber


@login_required
def selecionar_empresa(request):
    """
    View para usuário selecionar qual empresa quer acessar.
    Essencial para o sistema multitenant.
    """
    # Buscar empresas que o usuário tem acesso
    empresas_usuario = get_user_empresas(request.user)
    
    if request.method == 'POST':
        empresa_id = request.POST.get('empresa_id')
        
        if empresa_id:
            try:
                empresa = empresas_usuario.get(id=empresa_id)
                # Salvar empresa selecionada na sessão
                request.session['empresa_atual'] = empresa.id
                messages.success(request, f'Empresa {empresa.nome} selecionada com sucesso!')
                return redirect('dashboard')
            except Empresa.DoesNotExist:
                messages.error(request, 'Empresa não encontrada ou você não tem acesso.')
    
    # Se usuário não tem empresas, redirecionar para criar
    if not empresas_usuario.exists():
        messages.info(request, 'Você precisa criar ou ser vinculado a uma empresa primeiro.')
        return redirect('empresas:criar')
    
    # Verificar plano atual do usuário
    plano_atual = None
    try:
        # Buscar a primeira empresa do usuário para verificar o plano
        primeira_empresa = empresas_usuario.first()
        if primeira_empresa:
            assinatura = AssinaturaEmpresa.objects.filter(
                empresa=primeira_empresa,
                status__in=['ATIVA', 'TRIAL']
            ).first()
            
            if assinatura:
                plano_atual = assinatura.plano
            else:
                # Se não tem assinatura, assumir plano gratuito
                plano_atual = PlanoAssinatura.objects.filter(tipo='GRATUITO').first()
    except Exception:
        # Em caso de erro, assumir plano gratuito
        plano_atual = PlanoAssinatura.objects.filter(tipo='GRATUITO').first()
    
    # Se não encontrou plano, criar um padrão
    if not plano_atual:
        plano_atual = PlanoAssinatura.objects.create(
            nome='Gratuito',
            tipo='GRATUITO',
            preco_mensal=0,
            max_empresas=1,
            max_produtos=50,
            max_usuarios=2
        )
    
    context = {
        'empresas': empresas_usuario,
        'total_empresas': empresas_usuario.count(),
        'plano_atual': plano_atual,
    }
    
    return render(request, 'empresas/selecionar.html', context)


@login_required
def criar_empresa(request):
    """
    View para criar nova empresa.
    Automaticamente vincula o usuário criador como ADMIN.
    """
    # Verificar limite de empresas do plano atual
    empresas_usuario = get_user_empresas(request.user)
    total_empresas = empresas_usuario.count()
    
    # Verificar plano atual
    plano_atual = None
    if total_empresas > 0:
        primeira_empresa = empresas_usuario.first()
        assinatura = AssinaturaEmpresa.objects.filter(
            empresa=primeira_empresa,
            status__in=['ATIVA', 'TRIAL']
        ).first()
        
        if assinatura:
            plano_atual = assinatura.plano
    
    # Se não tem plano ou é gratuito, verificar limite
    if not plano_atual or plano_atual.tipo == 'GRATUITO':
        if total_empresas >= 1:
            messages.error(
                request, 
                'Você atingiu o limite de empresas do plano gratuito (1 empresa). '
                'Assine o plano Profissional para criar empresas ilimitadas!'
            )
            return redirect('empresas:selecionar')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Criar empresa
                empresa = Empresa.objects.create(
                    nome=request.POST.get('nome'),
                    razao_social=request.POST.get('razao_social'),
                    cnpj=request.POST.get('cnpj'),
                    endereco=request.POST.get('endereco'),
                    cidade=request.POST.get('cidade'),
                    estado=request.POST.get('estado'),
                    cep=request.POST.get('cep'),
                    telefone=request.POST.get('telefone'),
                    email=request.POST.get('email'),
                    capacidade_produtiva=int(request.POST.get('capacidade_produtiva', 300))
                )
                
                # Vincular usuário como ADMIN da empresa
                UsuarioEmpresa.objects.create(
                    usuario=request.user,
                    empresa=empresa,
                    role='ADMIN'
                )
                
                # Criar assinatura trial
                plano_basico = PlanoAssinatura.objects.filter(tipo='BASICO').first()
                if plano_basico:
                    AssinaturaEmpresa.objects.create(
                        empresa=empresa,
                        plano=plano_basico,
                        status='TRIAL',
                        trial_fim=timezone.now() + timedelta(days=30)
                    )
                
                # Criar configurações padrão
                ConfiguracaoEmpresa.objects.create(empresa=empresa)
                EmpresaStatus.objects.create(empresa=empresa)
                
                # Selecionar empresa criada
                request.session['empresa_atual'] = empresa.id
                
                messages.success(request, f'Empresa {empresa.nome} criada com sucesso!')
                return redirect('dashboard')
                
        except Exception as e:
            messages.error(request, f'Erro ao criar empresa: {str(e)}')
    
    return render(request, 'empresas/criar.html')


@login_required
@require_empresa
def dashboard_empresa(request):
    """
    Dashboard principal da empresa com estatísticas e informações gerais.
    """
    empresa = get_current_empresa()
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    # Buscar ou criar status da empresa
    status_empresa, created = EmpresaStatus.objects.get_or_create(
        empresa=empresa,
        defaults={
            'total_ops_mes': 0,
            'faturamento_mes': 0,
            'ops_atrasadas': 0,
            'capacidade_utilizada': 0
        }
    )
    
    # === DADOS REAIS DO SISTEMA ===
    
    # 1. Total de clientes
    total_clientes = Cliente.objects.filter(empresa=empresa, ativo=True).count()
    
    # 2. OPs em produção
    ops_producao = OrdemProducao.objects.filter(
        empresa=empresa,
        status='EM_PRODUCAO'
    ).count()
    
    # 3. Entregas hoje
    entregas_hoje = OrdemProducao.objects.filter(
        empresa=empresa,
        data_previsao=hoje,
        status__in=['EM_PRODUCAO', 'CONCLUIDA']
    ).count()
    
    # 4. Entregas atrasadas
    entregas_atrasadas = OrdemProducao.objects.filter(
        empresa=empresa,
        data_previsao__lt=hoje,
        status__in=['CADASTRADA', 'EM_PRODUCAO']
    ).count()
    
    # 5. Faturamento do mês
    faturamento_mes = ContaReceber.objects.filter(
        empresa=empresa,
        data_vencimento__gte=inicio_mes,
        status='PAGO'
    ).aggregate(total=Sum('valor_total'))['total'] or 0
    
    # 6. Faturamento mês anterior para comparação
    inicio_mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)
    fim_mes_anterior = inicio_mes - timedelta(days=1)
    
    faturamento_mes_anterior = ContaReceber.objects.filter(
        empresa=empresa,
        data_vencimento__gte=inicio_mes_anterior,
        data_vencimento__lte=fim_mes_anterior,
        status='PAGO'
    ).aggregate(total=Sum('valor_total'))['total'] or 0
    
    # Calcular percentual de crescimento
    crescimento_faturamento = 0
    if faturamento_mes_anterior > 0:
        crescimento_faturamento = ((faturamento_mes - faturamento_mes_anterior) / faturamento_mes_anterior) * 100
    elif faturamento_mes > 0:
        crescimento_faturamento = 100
    
    # 7. Crescimento de clientes este mês
    clientes_mes_passado = Cliente.objects.filter(
        empresa=empresa,
        ativo=True,
        created_at__lt=inicio_mes
    ).count()
    
    crescimento_clientes = 0
    if clientes_mes_passado > 0:
        crescimento_clientes = ((total_clientes - clientes_mes_passado) / clientes_mes_passado) * 100
    elif total_clientes > 0:
        crescimento_clientes = 100
    
    # 8. Crescimento de OPs esta semana
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    ops_semana_atual = OrdemProducao.objects.filter(
        empresa=empresa,
        data_entrada__gte=inicio_semana,
        status='EM_PRODUCAO'
    ).count()
    
    inicio_semana_anterior = inicio_semana - timedelta(days=7)
    ops_semana_anterior = OrdemProducao.objects.filter(
        empresa=empresa,
        data_entrada__gte=inicio_semana_anterior,
        data_entrada__lt=inicio_semana,
        status='EM_PRODUCAO'
    ).count()
    
    crescimento_ops = 0
    if ops_semana_anterior > 0:
        crescimento_ops = ((ops_semana_atual - ops_semana_anterior) / ops_semana_anterior) * 100
    elif ops_semana_atual > 0:
        crescimento_ops = 100
    
    # === ATIVIDADES RECENTES ===
    atividades_recentes = []
    
    # Clientes recentes
    clientes_recentes = Cliente.objects.filter(
        empresa=empresa,
        ativo=True
    ).order_by('-created_at')[:2]
    
    for cliente in clientes_recentes:
        tempo_decorrido = timezone.now() - cliente.created_at
        if tempo_decorrido.days == 0:
            if tempo_decorrido.seconds < 3600:
                tempo_str = f"Há {tempo_decorrido.seconds // 60} min"
            else:
                tempo_str = f"Há {tempo_decorrido.seconds // 3600} horas"
        else:
            tempo_str = f"Há {tempo_decorrido.days} dias"
        
        atividades_recentes.append({
            'icone': 'user-plus',
            'cor': 'primary',
            'titulo': 'Novo cliente cadastrado',
            'descricao': f'{cliente.nome} adicionado ao sistema',
            'tempo': tempo_str
        })
    
    # OPs finalizadas recentemente
    ops_finalizadas = OrdemProducao.objects.filter(
        empresa=empresa,
        status='CONCLUIDA'
    ).order_by('-updated_at')[:2]
    
    for op in ops_finalizadas:
        tempo_decorrido = timezone.now() - op.updated_at
        if tempo_decorrido.days == 0:
            if tempo_decorrido.seconds < 3600:
                tempo_str = f"Há {tempo_decorrido.seconds // 60} min"
            else:
                tempo_str = f"Há {tempo_decorrido.seconds // 3600} horas"
        else:
            tempo_str = f"Há {tempo_decorrido.days} dias"
        
        atividades_recentes.append({
            'icone': 'check-circle',
            'cor': 'success',
            'titulo': 'OP Finalizada',
            'descricao': f'OP #{op.numero_op} - {op.quantidade_total} peças produzidas',
            'tempo': tempo_str
        })
    
    # Ordenar por tempo
    atividades_recentes.sort(key=lambda x: x['tempo'])
    
    # === PRÓXIMAS ENTREGAS ===
    proximas_entregas = OrdemProducao.objects.filter(
        empresa=empresa,
        data_previsao__gte=hoje,
        status__in=['CADASTRADA', 'EM_PRODUCAO']
    ).order_by('data_previsao')[:5]
    
    # Dados para gráficos - OPs por status
    ops_por_status = {}
    for status in ['CADASTRADA', 'EM_PRODUCAO', 'CONCLUIDA', 'ENTREGUE']:
        ops_por_status[status] = OrdemProducao.objects.filter(
            empresa=empresa,
            status=status
        ).count()
    
    # Faturamento últimos 6 meses
    faturamento_meses = []
    for i in range(6):
        mes_ref = (hoje.replace(day=1) - timedelta(days=i*30))
        inicio_mes_ref = mes_ref.replace(day=1)
        
        if i == 0:
            fim_mes_ref = hoje
        else:
            # Último dia do mês
            proximo_mes = inicio_mes_ref.replace(day=28) + timedelta(days=4)
            fim_mes_ref = proximo_mes - timedelta(days=proximo_mes.day)
        
        faturamento_mes_ref = ContaReceber.objects.filter(
            empresa=empresa,
            data_vencimento__gte=inicio_mes_ref,
            data_vencimento__lte=fim_mes_ref,
            status='PAGO'
        ).aggregate(total=Sum('valor_total'))['total'] or 0
        
        faturamento_meses.append({
            'mes': inicio_mes_ref.strftime('%b/%Y'),
            'valor': float(faturamento_mes_ref)
        })
    
    faturamento_meses.reverse()
    
    # Assinatura atual e informações do plano
    assinatura = AssinaturaEmpresa.objects.filter(empresa=empresa).first()
    
    # Corrigir assinaturas TRIAL sem trial_fim definido
    if assinatura and assinatura.status == 'TRIAL' and not assinatura.trial_fim:
        assinatura.trial_fim = timezone.now() + timedelta(days=30)
        assinatura.save()
        print(f"Corrigida assinatura trial para empresa {empresa.nome}")
    
    plano_info = {
        'nome': 'Gratuito',
        'tipo': 'GRATUITO',
        'status': 'ATIVA',
        'dias_restantes': 0,
        'data_vencimento': None,
        'preco_mensal': 0,
        'is_trial': False,
        'is_gratuito': True,
        'cor_status': 'success',
        'icone_status': 'check-circle',
        'mensagem_status': 'Plano ativo',
        'urgencia': 'normal',  # normal, atencao, urgente, critico
        'mostrar_contador': False,
        'proximo_vencimento': None,
        'dias_para_vencimento': 0
    }
    
    if assinatura:
        plano_info.update({
            'nome': assinatura.plano.nome,
            'tipo': assinatura.plano.tipo,
            'status': assinatura.status,
            'preco_mensal': assinatura.plano.preco_mensal,
            'is_gratuito': assinatura.plano.tipo == 'GRATUITO'
        })
        
        # Calcular informações baseadas no status
        hoje = timezone.now().date()
        
        if assinatura.status == 'TRIAL':
            plano_info['is_trial'] = True
            plano_info['mostrar_contador'] = True
            
            if assinatura.trial_fim:
                dias_restantes = (assinatura.trial_fim.date() - hoje).days
                plano_info['dias_restantes'] = max(0, dias_restantes)
                plano_info['data_vencimento'] = assinatura.trial_fim.date()
                
                # Definir urgência baseada nos dias restantes
                if dias_restantes <= 0:
                    plano_info.update({
                        'urgencia': 'critico',
                        'cor_status': 'danger',
                        'icone_status': 'exclamation-triangle',
                        'mensagem_status': 'Trial expirado'
                    })
                elif dias_restantes <= 3:
                    plano_info.update({
                        'urgencia': 'urgente',
                        'cor_status': 'danger',
                        'icone_status': 'exclamation-triangle',
                        'mensagem_status': f'Trial expira em {dias_restantes} dia{"s" if dias_restantes != 1 else ""}'
                    })
                elif dias_restantes <= 7:
                    plano_info.update({
                        'urgencia': 'atencao',
                        'cor_status': 'warning',
                        'icone_status': 'exclamation-circle',
                        'mensagem_status': f'Trial expira em {dias_restantes} dias'
                    })
                else:
                    plano_info.update({
                        'urgencia': 'normal',
                        'cor_status': 'primary',
                        'icone_status': 'clock',
                        'mensagem_status': f'Trial ativo - {dias_restantes} dias restantes'
                    })
        
        elif assinatura.status == 'ATIVA':
            plano_info['mostrar_contador'] = True
            
            # Calcular próximo vencimento (assumindo vencimento mensal)
            if assinatura.data_inicio:
                # Calcular próximo vencimento baseado na data de início
                data_inicio = assinatura.data_inicio.date() if hasattr(assinatura.data_inicio, 'date') else assinatura.data_inicio
                
                # Encontrar o próximo vencimento
                hoje = timezone.now().date()
                ano_atual = hoje.year
                mes_atual = hoje.month
                dia_vencimento = data_inicio.day
                
                # Tentar o mês atual primeiro
                try:
                    proximo_vencimento = date(ano_atual, mes_atual, dia_vencimento)
                    if proximo_vencimento <= hoje:
                        # Se já passou, calcular próximo mês
                        if mes_atual == 12:
                            proximo_vencimento = date(ano_atual + 1, 1, dia_vencimento)
                        else:
                            proximo_vencimento = date(ano_atual, mes_atual + 1, dia_vencimento)
                except ValueError:
                    # Se o dia não existe no mês (ex: 31 de fevereiro), usar último dia do mês
                    import calendar
                    if mes_atual == 12:
                        ultimo_dia = calendar.monthrange(ano_atual + 1, 1)[1]
                        proximo_vencimento = date(ano_atual + 1, 1, min(dia_vencimento, ultimo_dia))
                    else:
                        ultimo_dia = calendar.monthrange(ano_atual, mes_atual + 1)[1]
                        proximo_vencimento = date(ano_atual, mes_atual + 1, min(dia_vencimento, ultimo_dia))
                
                plano_info['proximo_vencimento'] = proximo_vencimento
                dias_para_vencimento = (proximo_vencimento - hoje).days
                plano_info['dias_para_vencimento'] = dias_para_vencimento
                
                # Definir urgência baseada nos dias para vencimento
                if dias_para_vencimento <= 0:
                    plano_info.update({
                        'urgencia': 'critico',
                        'cor_status': 'danger',
                        'icone_status': 'exclamation-triangle',
                        'mensagem_status': 'Pagamento em atraso'
                    })
                elif dias_para_vencimento <= 3:
                    plano_info.update({
                        'urgencia': 'urgente',
                        'cor_status': 'danger',
                        'icone_status': 'exclamation-triangle',
                        'mensagem_status': f'Vence em {dias_para_vencimento} dia{"s" if dias_para_vencimento != 1 else ""}'
                    })
                elif dias_para_vencimento <= 7:
                    plano_info.update({
                        'urgencia': 'atencao',
                        'cor_status': 'warning',
                        'icone_status': 'exclamation-circle',
                        'mensagem_status': f'Vence em {dias_para_vencimento} dias'
                    })
                else:
                    plano_info.update({
                        'urgencia': 'normal',
                        'cor_status': 'success',
                        'icone_status': 'check-circle',
                        'mensagem_status': f'Próximo vencimento em {dias_para_vencimento} dias'
                    })
        
        elif assinatura.status == 'SUSPENSA':
            plano_info.update({
                'urgencia': 'critico',
                'cor_status': 'danger',
                'icone_status': 'ban',
                'mensagem_status': 'Plano suspenso',
                'mostrar_contador': False
            })
        
        elif assinatura.status == 'CANCELADA':
            plano_info.update({
                'urgencia': 'critico',
                'cor_status': 'secondary',
                'icone_status': 'times-circle',
                'mensagem_status': 'Plano cancelado',
                'mostrar_contador': False
            })
    
    context = {
        'empresa': empresa,
        'status_empresa': status_empresa,
        'ops_por_status': ops_por_status,
        'faturamento_meses': faturamento_meses,
        'assinatura': assinatura,
        'plano_info': plano_info,
        'total_usuarios': UsuarioEmpresa.objects.filter(
            empresa=empresa, 
            ativo=True
        ).count(),
        # Dados reais para os cards
        'total_clientes': total_clientes,
        'ops_producao': ops_producao,
        'entregas_hoje': entregas_hoje,
        'entregas_atrasadas': entregas_atrasadas,
        'faturamento_mes': faturamento_mes,
        'crescimento_faturamento': crescimento_faturamento,
        'crescimento_clientes': crescimento_clientes,
        'crescimento_ops': crescimento_ops,
        'atividades_recentes': atividades_recentes,
        'proximas_entregas': proximas_entregas,
        # Datas para template
        'today': hoje,
        'tomorrow': hoje + timedelta(days=1),
    }
    
    return render(request, 'empresas/dashboard.html', context)


@login_required
@require_empresa
def configuracoes_empresa(request):
    """
    View para configurar parâmetros da empresa.
    """
    empresa = get_current_empresa()
    
    # Verificar se usuário é admin
    usuario_empresa = UsuarioEmpresa.objects.filter(
        usuario=request.user,
        empresa=empresa,
        role='ADMIN'
    ).first()
    
    if not usuario_empresa:
        messages.error(request, 'Apenas administradores podem alterar configurações.')
        return redirect('dashboard')
    
    # Buscar ou criar configuração
    config, created = ConfiguracaoEmpresa.objects.get_or_create(
        empresa=empresa
    )
    
    if request.method == 'POST':
        try:
            # Atualizar empresa
            empresa.nome = request.POST.get('nome')
            empresa.razao_social = request.POST.get('razao_social')
            empresa.cnpj = request.POST.get('cnpj')
            empresa.endereco = request.POST.get('endereco')
            empresa.cidade = request.POST.get('cidade')
            empresa.estado = request.POST.get('estado')
            empresa.cep = request.POST.get('cep')
            empresa.telefone = request.POST.get('telefone')
            empresa.email = request.POST.get('email')
            empresa.capacidade_produtiva = int(request.POST.get('capacidade_produtiva'))
            empresa.save()
            
            # Atualizar configurações
            config.dias_uteis_mes = int(request.POST.get('dias_uteis_mes'))
            config.horas_trabalho_dia = int(request.POST.get('horas_trabalho_dia'))
            config.forma_pagamento_padrao = request.POST.get('forma_pagamento_padrao')
            config.notificar_prazo_op = request.POST.get('notificar_prazo_op') == 'on'
            config.dias_antecedencia_prazo = int(request.POST.get('dias_antecedencia_prazo'))
            config.save()
            
            messages.success(request, 'Configurações salvas com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao salvar configurações: {str(e)}')
    
    context = {
        'empresa': empresa,
        'config': config
    }
    
    return render(request, 'empresas/configuracoes.html', context)


@login_required
@require_empresa  
def usuarios_empresa(request):
    """
    View para gerenciar usuários da empresa.
    """
    empresa = get_current_empresa()
    
    # Verificar se usuário é admin
    usuario_empresa = UsuarioEmpresa.objects.filter(
        usuario=request.user,
        empresa=empresa,
        role='ADMIN'
    ).first()
    
    if not usuario_empresa:
        messages.error(request, 'Apenas administradores podem gerenciar usuários.')
        return redirect('dashboard')
    
    usuarios = UsuarioEmpresa.objects.filter(
        empresa=empresa
    ).select_related('usuario').order_by('data_vinculo')
    
    context = {
        'empresa': empresa,
        'usuarios': usuarios
    }
    
    return render(request, 'empresas/usuarios.html', context)


@login_required
def ajax_trocar_empresa(request):
    """Ajax para trocar empresa rapidamente"""
    if request.method == 'POST':
        empresa_id = request.POST.get('empresa_id')
        
        # Verificar se usuário tem acesso
        empresas_usuario = get_user_empresas(request.user)
        
        try:
            empresa = empresas_usuario.get(id=empresa_id)
            request.session['empresa_atual'] = empresa.id
            
            return JsonResponse({
                'success': True,
                'empresa_nome': empresa.nome,
                'redirect_url': reverse('dashboard')
            })
        except Empresa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Empresa não encontrada'
            })
    
    return JsonResponse({'success': False})
