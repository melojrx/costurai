from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal

from .models import (
    UserProfile, LoginHistory, TentativaLogin, 
    BloqueioIP, ConviteUsuario
)
from apps.core.models import Empresa, UsuarioEmpresa


def get_client_ip(request):
    """Obtém o IP real do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def registrar_tentativa_login(request, username, sucesso=True, motivo_falha=None):
    """Registra tentativa de login no histórico"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    try:
        usuario = User.objects.get(username=username)
        
        # Registrar no histórico
        LoginHistory.objects.create(
            usuario=usuario,
            ip_address=ip_address,
            user_agent=user_agent,
            sucesso=sucesso,
            motivo_falha=motivo_falha
        )
        
        if not sucesso:
            # Registrar tentativa falhada
            TentativaLogin.objects.create(
                usuario=usuario,
                ip_address=ip_address,
                username_tentativa=username,
                password_tentativa="[hidden]"
            )
            
            # Verificar se deve bloquear IP
            verificar_bloqueio_ip(ip_address)
            
    except User.DoesNotExist:
        # Usuário não existe, registrar tentativa suspeita
        TentativaLogin.objects.create(
            ip_address=ip_address,
            username_tentativa=username,
            password_tentativa="[hidden]"
        )
        verificar_bloqueio_ip(ip_address)


def verificar_bloqueio_ip(ip_address):
    """Verifica se deve bloquear IP por tentativas falhadas"""
    from datetime import timedelta
    
    # Contar tentativas nas últimas 10 minutos
    limite_tempo = timezone.now() - timedelta(minutes=10)
    tentativas = TentativaLogin.objects.filter(
        ip_address=ip_address,
        data_tentativa__gte=limite_tempo
    ).count()
    
    # Se mais de 5 tentativas, bloquear por 30 minutos
    if tentativas >= 5:
        bloqueio_ate = timezone.now() + timedelta(minutes=30)
        
        BloqueioIP.objects.update_or_create(
            ip_address=ip_address,
            defaults={
                'bloqueado_ate': bloqueio_ate,
                'tentativas_falhadas': tentativas,
                'motivo': f"{tentativas} tentativas de login falhadas"
            }
        )


def verificar_ip_bloqueado(request):
    """Verifica se IP está bloqueado"""
    ip_address = get_client_ip(request)
    
    try:
        bloqueio = BloqueioIP.objects.get(ip_address=ip_address)
        return bloqueio.esta_bloqueado
    except BloqueioIP.DoesNotExist:
        return False


def login_view(request):
    """View customizada de login"""
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        lembrar = request.POST.get('lembrar') == 'on'
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Registrar login no histórico
                    LoginHistory.objects.create(
                        usuario=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        sucesso=True
                    )
                    
                    # Configurar sessão
                    if not lembrar:
                        request.session.set_expiry(0)
                    
                    # Criar perfil se não existir
                    UserProfile.objects.get_or_create(usuario=user)
                    
                    messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
                    
                    # Redirecionar
                    next_url = request.GET.get('next', reverse('dashboard'))
                    return redirect(next_url)
                else:
                    messages.error(request, 'Sua conta está inativa.')
            else:
                messages.error(request, 'Nome de usuário ou senha incorretos.')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """View de logout customizada"""
    
    # Atualizar histórico de login com logout
    try:
        ultimo_login = LoginHistory.objects.filter(
            usuario=request.user,
            sucesso=True,
            data_logout__isnull=True
        ).latest('data_login')
        
        ultimo_login.data_logout = timezone.now()
        ultimo_login.save()
    except LoginHistory.DoesNotExist:
        pass
    
    messages.success(request, 'Logout realizado com sucesso!')
    logout(request)
    
    return redirect('accounts:login')


# Views para cadastro em etapas
def registro_escolha_view(request):
    """View para escolher método de cadastro"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'auth/cadastro_escolha.html')


def registro_etapa1_view(request):
    """Etapa 1: Dados pessoais do usuário"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Salvar dados na sessão
        request.session['cadastro_etapa1'] = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'telefone': request.POST.get('telefone'),
            'cargo': request.POST.get('cargo'),
            'password': request.POST.get('password'),
            'aceito_termos': request.POST.get('aceito_termos') == 'on'
        }
        
        # Validações básicas
        dados = request.session['cadastro_etapa1']
        
        if not all([dados['first_name'], dados['last_name'], dados['email'], dados['password']]):
            messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
            return render(request, 'auth/cadastro_etapa1.html')
        
        if request.POST.get('password') != request.POST.get('password_confirm'):
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'auth/cadastro_etapa1.html')
        
        if len(dados['password']) < 8:
            messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
            return render(request, 'auth/cadastro_etapa1.html')
        
        if User.objects.filter(email=dados['email']).exists():
            messages.error(request, 'E-mail já está cadastrado.')
            return render(request, 'auth/cadastro_etapa1.html')
        
        if not dados['aceito_termos']:
            messages.error(request, 'Você deve aceitar os termos de uso.')
            return render(request, 'auth/cadastro_etapa1.html')
        
        return redirect('accounts:registro_etapa2')
    
    return render(request, 'auth/cadastro_etapa1.html')


def registro_etapa2_view(request):
    """Etapa 2: Dados da empresa"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if 'cadastro_etapa1' not in request.session:
        messages.error(request, 'Sessão expirou. Comece novamente.')
        return redirect('accounts:registro_etapa1')
    
    if request.method == 'POST':
        # Salvar dados na sessão
        request.session['cadastro_etapa2'] = {
            'nome_empresa': request.POST.get('nome_empresa'),
            'razao_social': request.POST.get('razao_social'),
            'cnpj': request.POST.get('cnpj'),
            'endereco': request.POST.get('endereco'),
            'cidade': request.POST.get('cidade'),
            'estado': request.POST.get('estado'),
            'cep': request.POST.get('cep'),
            'telefone_empresa': request.POST.get('telefone_empresa'),
            'email_empresa': request.POST.get('email_empresa'),
            'capacidade_produtiva': request.POST.get('capacidade_produtiva', 300)
        }
        
        # Validações básicas
        dados = request.session['cadastro_etapa2']
        
        if not all([dados['nome_empresa'], dados['cnpj'], dados['endereco'], dados['cidade'], dados['estado']]):
            messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
            return render(request, 'auth/cadastro_etapa2.html')
        
        return redirect('accounts:registro_etapa3')
    
    return render(request, 'auth/cadastro_etapa2.html')


def registro_etapa3_view(request):
    """Etapa 3: Confirmação e escolha do plano"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if 'cadastro_etapa1' not in request.session or 'cadastro_etapa2' not in request.session:
        messages.error(request, 'Sessão expirou. Comece novamente.')
        return redirect('accounts:registro_etapa1')
    
    # Buscar planos disponíveis
    from apps.core.models import PlanoAssinatura, Empresa, UsuarioEmpresa, AssinaturaEmpresa
    planos = PlanoAssinatura.objects.all().order_by('preco_mensal')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Dados das etapas anteriores
                dados_usuario = request.session['cadastro_etapa1']
                dados_empresa = request.session['cadastro_etapa2']
                plano_id = request.POST.get('plano_id')
                
                # Criar usuário
                user = User.objects.create_user(
                    username=dados_usuario['email'],  # Usar email como username
                    email=dados_usuario['email'],
                    password=dados_usuario['password'],
                    first_name=dados_usuario['first_name'],
                    last_name=dados_usuario['last_name']
                )
                
                # Criar perfil
                UserProfile.objects.create(
                    usuario=user,
                    cargo=dados_usuario['cargo'],
                    telefone=dados_usuario['telefone'],
                    aceito_termos=dados_usuario['aceito_termos'],
                    data_aceite_termos=timezone.now() if dados_usuario['aceito_termos'] else None
                )
                
                # Criar empresa
                empresa = Empresa.objects.create(
                    nome=dados_empresa['nome_empresa'],
                    razao_social=dados_empresa['razao_social'] or dados_empresa['nome_empresa'],
                    cnpj=dados_empresa['cnpj'],
                    endereco=dados_empresa['endereco'],
                    cidade=dados_empresa['cidade'],
                    estado=dados_empresa['estado'],
                    cep=dados_empresa['cep'],
                    telefone=dados_empresa['telefone_empresa'],
                    email=dados_empresa['email_empresa'],
                    capacidade_produtiva=int(dados_empresa['capacidade_produtiva'])
                )
                
                # Vincular usuário como ADMIN da empresa
                UsuarioEmpresa.objects.create(
                    usuario=user,
                    empresa=empresa,
                    role='ADMIN'
                )
                
                # Criar assinatura
                if plano_id:
                    plano = PlanoAssinatura.objects.get(id=plano_id)
                    status = 'TRIAL' if plano.tipo == 'GRATUITO' else 'ATIVA'
                    trial_fim = timezone.now() + timedelta(days=30) if plano.tipo == 'GRATUITO' else None
                    
                    AssinaturaEmpresa.objects.create(
                        empresa=empresa,
                        plano=plano,
                        status=status,
                        trial_fim=trial_fim
                    )
                
                # Login automático
                login(request, user)
                
                # Selecionar empresa criada
                request.session['empresa_atual'] = empresa.id
                
                # Limpar dados da sessão
                del request.session['cadastro_etapa1']
                del request.session['cadastro_etapa2']
                
                messages.success(request, f'Conta criada com sucesso! Bem-vindo ao ConfecçãoManager Pro!')
                
                return redirect('dashboard')
                
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
    
    context = {
        'planos': planos,
        'dados_usuario': request.session.get('cadastro_etapa1'),
        'dados_empresa': request.session.get('cadastro_etapa2'),
    }
    
    return render(request, 'auth/cadastro_etapa3.html', context)


# View de compatibilidade
def registro_view(request):
    """Redirect para nova estrutura de cadastro"""
    return redirect('accounts:registro_escolha')


@login_required
def perfil_view(request):
    """View para visualizar e editar perfil do usuário"""
    
    profile, created = UserProfile.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        try:
            # Atualizar dados do usuário
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            
            # Atualizar perfil
            profile.cpf = request.POST.get('cpf', '')
            profile.telefone = request.POST.get('telefone', '')
            profile.celular = request.POST.get('celular', '')
            profile.endereco = request.POST.get('endereco', '')
            profile.cargo = request.POST.get('cargo', profile.cargo)
            profile.receber_email_notificacoes = request.POST.get('receber_email_notificacoes') == 'on'
            profile.receber_sms_notificacoes = request.POST.get('receber_sms_notificacoes') == 'on'
            
            # Upload de avatar
            if request.FILES.get('avatar'):
                profile.avatar = request.FILES['avatar']
            
            profile.save()
            
            messages.success(request, 'Perfil atualizado com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar perfil: {str(e)}')
    
    # Histórico de logins recentes
    logins_recentes = LoginHistory.objects.filter(
        usuario=request.user,
        sucesso=True
    ).order_by('-data_login')[:10]
    
    context = {
        'profile': profile,
        'logins_recentes': logins_recentes,
    }
    
    return render(request, 'accounts/perfil.html', context)


@login_required 
def alterar_senha_view(request):
    """View para alterar senha"""
    
    if request.method == 'POST':
        senha_atual = request.POST.get('senha_atual')
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        
        # Validações
        if not request.user.check_password(senha_atual):
            messages.error(request, 'Senha atual incorreta.')
            return render(request, 'accounts/alterar_senha.html')
        
        if nova_senha != confirmar_senha:
            messages.error(request, 'As novas senhas não coincidem.')
            return render(request, 'accounts/alterar_senha.html')
        
        if len(nova_senha) < 8:
            messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
            return render(request, 'accounts/alterar_senha.html')
        
        # Alterar senha
        request.user.set_password(nova_senha)
        request.user.save()
        
        # Re-autenticar usuário
        user = authenticate(username=request.user.username, password=nova_senha)
        if user:
            login(request, user)
        
        messages.success(request, 'Senha alterada com sucesso!')
        return redirect('accounts:perfil')
    
    return render(request, 'accounts/alterar_senha.html')


def aceitar_convite_view(request, token):
    """View para aceitar convite de empresa"""
    
    try:
        convite = get_object_or_404(ConviteUsuario, token=token, status='PENDENTE')
        
        if convite.esta_expirado:
            convite.status = 'EXPIRADO'
            convite.save()
            messages.error(request, 'Este convite expirou.')
            return redirect('accounts:login')
        
        if request.method == 'POST':
            if request.user.is_authenticated:
                # Usuário já logado, apenas vincular à empresa
                with transaction.atomic():
                    UsuarioEmpresa.objects.get_or_create(
                        usuario=request.user,
                        empresa=convite.empresa,
                        defaults={
                            'role': convite.role_empresa,
                            'ativo': True
                        }
                    )
                    
                    convite.status = 'ACEITO'
                    convite.aceito_em = timezone.now()
                    convite.usuario_aceito = request.user
                    convite.save()
                    
                    messages.success(
                        request, 
                        f'Você foi vinculado à empresa {convite.empresa.nome} com sucesso!'
                    )
                    
                    # Definir empresa na sessão
                    request.session['empresa_atual'] = convite.empresa.id
                    
                    return redirect('dashboard')
            else:
                # Redirecionar para registro/login
                request.session['convite_token'] = token
                messages.info(
                    request, 
                    f'Você foi convidado para a empresa {convite.empresa.nome}. '
                    'Faça login ou crie uma conta para aceitar o convite.'
                )
                return redirect('accounts:login')
        
        context = {
            'convite': convite
        }
        
        return render(request, 'accounts/aceitar_convite.html', context)
        
    except ConviteUsuario.DoesNotExist:
        messages.error(request, 'Convite não encontrado ou inválido.')
        return redirect('accounts:login')


@login_required
def gestao_conta_view(request):
    """View principal para gestão de conta com abas"""
    from apps.core.models import Empresa, UsuarioEmpresa, AssinaturaEmpresa, PlanoAssinatura
    
    # Dados do usuário
    profile, created = UserProfile.objects.get_or_create(usuario=request.user)
    
    # Empresas do usuário
    empresas_usuario = UsuarioEmpresa.objects.filter(
        usuario=request.user, 
        ativo=True
    ).select_related('empresa', 'empresa__assinatura', 'empresa__assinatura__plano')
    
    # Empresa atual
    empresa_atual_id = request.session.get('empresa_atual')
    empresa_atual = None
    assinatura_atual = None
    
    if empresa_atual_id:
        try:
            empresa_atual = Empresa.objects.get(id=empresa_atual_id)
            assinatura_atual = AssinaturaEmpresa.objects.select_related('plano').get(empresa=empresa_atual)
        except (Empresa.DoesNotExist, AssinaturaEmpresa.DoesNotExist):
            pass
    
    # Planos disponíveis
    planos_disponiveis = PlanoAssinatura.objects.filter(ativo=True, visivel_site=True).order_by('ordem_exibicao')
    
    # Histórico de logins
    logins_recentes = LoginHistory.objects.filter(
        usuario=request.user,
        sucesso=True
    ).order_by('-data_login')[:5]
    
    context = {
        'profile': profile,
        'empresas_usuario': empresas_usuario,
        'empresa_atual': empresa_atual,
        'assinatura_atual': assinatura_atual,
        'planos_disponiveis': planos_disponiveis,
        'logins_recentes': logins_recentes,
    }
    
    return render(request, 'accounts/gestao_conta.html', context)


@login_required
def atualizar_perfil_ajax(request):
    """Atualizar perfil via AJAX"""
    if request.method == 'POST':
        try:
            profile, created = UserProfile.objects.get_or_create(usuario=request.user)
            
            # Atualizar dados do usuário
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            
            # Atualizar perfil
            profile.cpf = request.POST.get('cpf', '')
            profile.telefone = request.POST.get('telefone', '')
            profile.celular = request.POST.get('celular', '')
            profile.endereco = request.POST.get('endereco', '')
            profile.cargo = request.POST.get('cargo', profile.cargo)
            profile.receber_email_notificacoes = request.POST.get('receber_email_notificacoes') == 'true'
            profile.receber_sms_notificacoes = request.POST.get('receber_sms_notificacoes') == 'true'
            
            # Upload de avatar
            if request.FILES.get('avatar'):
                profile.avatar = request.FILES['avatar']
            
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Perfil atualizado com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao atualizar perfil: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})


@login_required
def atualizar_empresa_ajax(request):
    """Atualizar dados da empresa via AJAX"""
    if request.method == 'POST':
        try:
            from apps.core.models import Empresa, UsuarioEmpresa
            
            empresa_id = request.POST.get('empresa_id')
            
            # Verificar se usuário tem permissão para editar a empresa
            usuario_empresa = UsuarioEmpresa.objects.filter(
                usuario=request.user,
                empresa_id=empresa_id,
                role__in=['ADMIN', 'GERENTE']
            ).first()
            
            if not usuario_empresa:
                return JsonResponse({
                    'success': False,
                    'message': 'Você não tem permissão para editar esta empresa'
                })
            
            empresa = usuario_empresa.empresa
            
            # Atualizar dados da empresa
            empresa.nome = request.POST.get('nome', empresa.nome)
            empresa.razao_social = request.POST.get('razao_social', empresa.razao_social)
            empresa.cnpj = request.POST.get('cnpj', empresa.cnpj)
            empresa.endereco = request.POST.get('endereco', empresa.endereco)
            empresa.cidade = request.POST.get('cidade', empresa.cidade)
            empresa.estado = request.POST.get('estado', empresa.estado)
            empresa.cep = request.POST.get('cep', empresa.cep)
            empresa.telefone = request.POST.get('telefone', empresa.telefone)
            empresa.email = request.POST.get('email', empresa.email)
            empresa.capacidade_produtiva = int(request.POST.get('capacidade_produtiva', empresa.capacidade_produtiva))
            
            # Upload de logo
            if request.FILES.get('logo'):
                empresa.logo = request.FILES['logo']
            
            empresa.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Dados da empresa atualizados com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao atualizar empresa: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})


@login_required
def upgrade_plano_view(request):
    """View para upgrade de plano"""
    if request.method == 'POST':
        try:
            from apps.core.models import (
                Empresa, AssinaturaEmpresa, PlanoAssinatura, 
                TransacaoPagamento, HistoricoAssinatura, CupomDesconto
            )
            
            empresa_id = request.POST.get('empresa_id')
            plano_id = request.POST.get('plano_id')
            cupom_codigo = request.POST.get('cupom_codigo', '').strip()
            
            # Verificar permissões
            empresa = get_object_or_404(Empresa, id=empresa_id)
            usuario_empresa = UsuarioEmpresa.objects.filter(
                usuario=request.user,
                empresa=empresa,
                role__in=['ADMIN']
            ).first()
            
            if not usuario_empresa:
                return JsonResponse({
                    'success': False,
                    'message': 'Você não tem permissão para alterar o plano desta empresa'
                })
            
            # Buscar plano e assinatura
            plano_novo = get_object_or_404(PlanoAssinatura, id=plano_id, ativo=True)
            assinatura = get_object_or_404(AssinaturaEmpresa, empresa=empresa)
            
            # Verificar se não é o mesmo plano
            if assinatura.plano.id == plano_novo.id:
                return JsonResponse({
                    'success': False,
                    'message': 'Este já é o seu plano atual'
                })
            
            # Permitir qualquer mudança de plano (upgrade ou downgrade)
            tipo_mudanca = 'UPGRADE' if plano_novo.preco_mensal > assinatura.plano.preco_mensal else 'DOWNGRADE'
            
            # Verificar cupom se fornecido
            cupom = None
            valor_desconto = Decimal('0.00')
            
            if cupom_codigo:
                try:
                    cupom = CupomDesconto.objects.get(codigo=cupom_codigo, ativo=True)
                    if not cupom.esta_valido:
                        return JsonResponse({
                            'success': False,
                            'message': 'Cupom inválido ou expirado'
                        })
                    
                    # Verificar se cupom se aplica ao plano
                    if cupom.planos_aplicaveis.exists() and plano_novo not in cupom.planos_aplicaveis.all():
                        return JsonResponse({
                            'success': False,
                            'message': 'Cupom não se aplica a este plano'
                        })
                    
                    valor_desconto = cupom.calcular_desconto(plano_novo.preco_mensal)
                    
                except CupomDesconto.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Cupom não encontrado'
                    })
            
            # Calcular valores
            valor_original = plano_novo.preco_mensal
            valor_final = valor_original - valor_desconto
            
            with transaction.atomic():
                # Atualizar assinatura
                plano_anterior = assinatura.plano
                assinatura.plano = plano_novo
                assinatura.save()
                
                # Criar transação
                transacao = TransacaoPagamento.objects.create(
                    empresa=empresa,
                    assinatura=assinatura,
                    plano=plano_novo,
                    cupom=cupom,
                    tipo_transacao=tipo_mudanca,
                    gateway='STRIPE',  # Padrão
                    valor_original=valor_original,
                    valor_desconto=valor_desconto,
                    valor_final=valor_final,
                    status='APROVADA',  # Simular aprovação
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Criar histórico
                HistoricoAssinatura.objects.create(
                    assinatura=assinatura,
                    plano_anterior=plano_anterior,
                    plano_novo=plano_novo,
                    acao=tipo_mudanca,
                    valor_anterior=plano_anterior.preco_mensal,
                    valor_novo=plano_novo.preco_mensal,
                    usuario=request.user,
                    data_vigencia=timezone.now()
                )
                
                # Atualizar uso do cupom
                if cupom:
                    cupom.vezes_usado += 1
                    cupom.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Plano atualizado para {plano_novo.nome} com sucesso!',
                'transacao_id': transacao.id_transacao,
                'valor_final': float(valor_final)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar upgrade: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})


@login_required
def validar_cupom_ajax(request):
    """Validar cupom de desconto via AJAX"""
    if request.method == 'POST':
        try:
            from apps.core.models import CupomDesconto, PlanoAssinatura
            
            cupom_codigo = request.POST.get('cupom_codigo', '').strip()
            plano_id = request.POST.get('plano_id')
            
            if not cupom_codigo:
                return JsonResponse({
                    'success': False,
                    'message': 'Código do cupom é obrigatório'
                })
            
            try:
                cupom = CupomDesconto.objects.get(codigo=cupom_codigo, ativo=True)
                
                if not cupom.esta_valido:
                    return JsonResponse({
                        'success': False,
                        'message': 'Cupom inválido ou expirado'
                    })
                
                # Verificar se se aplica ao plano
                if plano_id:
                    plano = PlanoAssinatura.objects.get(id=plano_id)
                    if cupom.planos_aplicaveis.exists() and plano not in cupom.planos_aplicaveis.all():
                        return JsonResponse({
                            'success': False,
                            'message': 'Cupom não se aplica a este plano'
                        })
                    
                    # Calcular desconto
                    valor_desconto = cupom.calcular_desconto(plano.preco_mensal)
                    valor_final = plano.preco_mensal - valor_desconto
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Cupom válido! Desconto de R$ {valor_desconto:.2f}',
                        'valor_desconto': float(valor_desconto),
                        'valor_final': float(valor_final),
                        'tipo_desconto': cupom.tipo_desconto,
                        'percentual': float(cupom.valor_desconto) if cupom.tipo_desconto == 'PERCENTUAL' else None
                    })
                
                return JsonResponse({
                    'success': True,
                    'message': 'Cupom válido!',
                    'tipo_desconto': cupom.tipo_desconto,
                    'valor_desconto': float(cupom.valor_desconto)
                })
                
            except CupomDesconto.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Cupom não encontrado'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao validar cupom: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})


@login_required
def estender_trial_view(request):
    """Estender período de trial"""
    if request.method == 'POST':
        try:
            from apps.core.models import Empresa, AssinaturaEmpresa, UsuarioEmpresa
            
            empresa_id = request.POST.get('empresa_id')
            dias_extensao = int(request.POST.get('dias_extensao', 0))
            
            # Verificar permissões
            empresa = get_object_or_404(Empresa, id=empresa_id)
            usuario_empresa = UsuarioEmpresa.objects.filter(
                usuario=request.user,
                empresa=empresa,
                role='ADMIN'
            ).first()
            
            if not usuario_empresa:
                return JsonResponse({
                    'success': False,
                    'message': 'Você não tem permissão para estender o trial desta empresa'
                })
            
            # Buscar assinatura
            assinatura = get_object_or_404(AssinaturaEmpresa, empresa=empresa)
            
            # Verificar se está em trial
            if assinatura.status != 'TRIAL':
                return JsonResponse({
                    'success': False,
                    'message': 'A empresa não está em período de trial'
                })
            
            # Estender trial
            if assinatura.trial_fim:
                assinatura.trial_fim += timedelta(days=dias_extensao)
            else:
                assinatura.trial_fim = timezone.now() + timedelta(days=dias_extensao)
            
            assinatura.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Trial estendido por {dias_extensao} dias!',
                'nova_data_fim': assinatura.trial_fim.strftime('%d/%m/%Y')
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao estender trial: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})


@login_required
def alterar_senha_ajax(request):
    """Alterar senha via AJAX"""
    if request.method == 'POST':
        try:
            senha_atual = request.POST.get('senha_atual')
            nova_senha = request.POST.get('nova_senha')
            confirmar_senha = request.POST.get('confirmar_senha')
            
            # Validações
            if not request.user.check_password(senha_atual):
                return JsonResponse({
                    'success': False,
                    'message': 'Senha atual incorreta'
                })
            
            if nova_senha != confirmar_senha:
                return JsonResponse({
                    'success': False,
                    'message': 'As novas senhas não coincidem'
                })
            
            if len(nova_senha) < 8:
                return JsonResponse({
                    'success': False,
                    'message': 'A nova senha deve ter pelo menos 8 caracteres'
                })
            
            # Alterar senha
            request.user.set_password(nova_senha)
            request.user.save()
            
            # Re-autenticar usuário
            user = authenticate(username=request.user.username, password=nova_senha)
            if user:
                login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': 'Senha alterada com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao alterar senha: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})


@login_required
def historico_assinatura_view(request):
    """View para histórico de assinatura"""
    from apps.core.models import Empresa, UsuarioEmpresa, HistoricoAssinatura, TransacaoPagamento
    
    empresa_id = request.GET.get('empresa_id')
    if not empresa_id:
        return JsonResponse({'success': False, 'message': 'ID da empresa é obrigatório'})
    
    # Verificar permissões
    usuario_empresa = UsuarioEmpresa.objects.filter(
        usuario=request.user,
        empresa_id=empresa_id,
        ativo=True
    ).first()
    
    if not usuario_empresa:
        return JsonResponse({'success': False, 'message': 'Sem permissão para visualizar'})
    
    # Buscar histórico
    historico = HistoricoAssinatura.objects.filter(
        assinatura__empresa_id=empresa_id
    ).select_related('plano_anterior', 'plano_novo', 'usuario').order_by('-data_mudanca')[:20]
    
    # Buscar transações
    transacoes = TransacaoPagamento.objects.filter(
        empresa_id=empresa_id
    ).select_related('plano', 'cupom').order_by('-data_criacao')[:10]
    
    historico_data = []
    for item in historico:
        historico_data.append({
            'acao': item.get_acao_display(),
            'plano_anterior': item.plano_anterior.nome if item.plano_anterior else None,
            'plano_novo': item.plano_novo.nome,
            'valor_anterior': float(item.valor_anterior) if item.valor_anterior else None,
            'valor_novo': float(item.valor_novo),
            'data_mudanca': item.data_mudanca.strftime('%d/%m/%Y %H:%M'),
            'usuario': item.usuario.get_full_name() if item.usuario else 'Sistema',
            'motivo': item.motivo
        })
    
    transacoes_data = []
    for item in transacoes:
        transacoes_data.append({
            'id_transacao': item.id_transacao,
            'tipo': item.get_tipo_transacao_display(),
            'plano': item.plano.nome,
            'valor_original': float(item.valor_original),
            'valor_desconto': float(item.valor_desconto),
            'valor_final': float(item.valor_final),
            'status': item.get_status_display(),
            'gateway': item.get_gateway_display(),
            'data_criacao': item.data_criacao.strftime('%d/%m/%Y %H:%M'),
            'cupom': item.cupom.codigo if item.cupom else None
        })
    
    return JsonResponse({
        'success': True,
        'historico': historico_data,
        'transacoes': transacoes_data
    })


@login_required
def aplicar_cupom_trial_view(request):
    """Aplicar cupom de extensão de trial"""
    if request.method == 'POST':
        try:
            from apps.core.models import Empresa, AssinaturaEmpresa, CupomDesconto, UsuarioEmpresa
            
            empresa_id = request.POST.get('empresa_id')
            cupom_codigo = request.POST.get('cupom_codigo', '').strip()
            
            if not cupom_codigo:
                return JsonResponse({
                    'success': False,
                    'message': 'Código do cupom é obrigatório'
                })
            
            # Verificar permissões
            empresa = get_object_or_404(Empresa, id=empresa_id)
            usuario_empresa = UsuarioEmpresa.objects.filter(
                usuario=request.user,
                empresa=empresa,
                role__in=['ADMIN']
            ).first()
            
            if not usuario_empresa:
                return JsonResponse({
                    'success': False,
                    'message': 'Você não tem permissão para aplicar cupons nesta empresa'
                })
            
            # Buscar assinatura
            assinatura = get_object_or_404(AssinaturaEmpresa, empresa=empresa)
            
            # Verificar se está no plano gratuito
            if assinatura.plano.tipo != 'GRATUITO':
                return JsonResponse({
                    'success': False,
                    'message': 'Cupons de extensão só podem ser aplicados no plano gratuito'
                })
            
            # Verificar cupom
            try:
                cupom = CupomDesconto.objects.get(codigo=cupom_codigo, ativo=True)
                
                if not cupom.esta_valido:
                    return JsonResponse({
                        'success': False,
                        'message': 'Cupom inválido ou expirado'
                    })
                
                # Verificar se cupom se aplica ao plano gratuito
                if cupom.planos_aplicaveis.exists() and assinatura.plano not in cupom.planos_aplicaveis.all():
                    return JsonResponse({
                        'success': False,
                        'message': 'Este cupom não se aplica ao plano gratuito'
                    })
                
                # Aplicar extensão de trial
                dias_extensao = 30  # Padrão para cupons de trial
                
                if assinatura.trial_fim:
                    # Se já tem data de fim, estender a partir dela
                    nova_data = assinatura.trial_fim + timedelta(days=dias_extensao)
                else:
                    # Se não tem data de fim, definir a partir de hoje
                    nova_data = timezone.now() + timedelta(days=dias_extensao)
                
                assinatura.trial_fim = nova_data
                assinatura.trial_ativo = True
                assinatura.status = 'TRIAL'
                assinatura.save()
                
                # Atualizar uso do cupom
                cupom.vezes_usado += 1
                cupom.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Trial estendido com sucesso! Nova data de expiração: {nova_data.strftime("%d/%m/%Y")}',
                    'nova_data_fim': nova_data.strftime('%d/%m/%Y'),
                    'dias_adicionados': dias_extensao
                })
                
            except CupomDesconto.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Cupom não encontrado'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao aplicar cupom: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})
