from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from projeto_receitas import settings
from .models import Receita, Avaliacao, ListaCompras, Colecao, Profile
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

# Create your views here.

def lista_receitas(request):
    receitas = Receita.objects.annotate(media_avaliacoes=Avg('avaliacao__nota'))
    query = request.GET.get('q')
    tempo_preparo = request.GET.get('tempo_preparo')
    dificuldade = request.GET.get('dificuldade')
    ordenar_por = request.GET.get('ordenar_por')

    if query:
        receitas = receitas.filter(
            Q(titulo__icontains=query) |
            Q(descricao__icontains=query) |
            Q(ingredientes__icontains=query)
        )

    if tempo_preparo:
        receitas = receitas.filter(tempo_preparo__lte=int(tempo_preparo))

    if dificuldade:
        receitas = receitas.filter(dificuldade=dificuldade)

    if ordenar_por:
        if ordenar_por == 'data_asc':
            receitas = receitas.order_by('data_criacao')
        elif ordenar_por == 'data_desc':
            receitas = receitas.order_by('-data_criacao')
        elif ordenar_por == 'tempo_asc':
            receitas = receitas.order_by('tempo_preparo')
        elif ordenar_por == 'tempo_desc':
            receitas = receitas.order_by('-tempo_preparo')
        elif ordenar_por == 'avaliacao_desc':
            receitas = receitas.order_by('-media_avaliacoes')
        elif ordenar_por == 'avaliacao_asc':
            receitas = receitas.order_by('media_avaliacoes')

    context = {
        'receitas': receitas,
        'query': query,
        'tempo_preparo': tempo_preparo,
        'dificuldade': dificuldade,
        'ordenar_por': ordenar_por,
        'dificuldades': Receita.DIFICULDADE_CHOICES,
    }
    return render(request, 'lista_receitas.html', context)

@login_required
def detalhe_receita(request, receita_id):
    receita = get_object_or_404(Receita, id=receita_id)
    avaliacoes = receita.avaliacao_set.all().order_by('-data_criacao')
    media_avaliacoes = receita.media_avaliacoes()

    if request.method == 'POST':
        if 'adicionar_lista' in request.POST:
            # Adicionar a receita à lista de compras
            lista_compras, created = ListaCompras.objects.get_or_create(usuario=request.user)
            lista_compras.receitas.add(receita)
            messages.success(request, 'Receita adicionada à sua lista de compras.')
            return redirect('detalhe_receita', receita_id=receita.id)

        elif 'nota' in request.POST:
            # Lógica para avaliação
            nota = request.POST.get('nota')
            comentario = request.POST.get('comentario')

            if nota:
                avaliacao, created = Avaliacao.objects.update_or_create(
                    receita=receita,
                    usuario=request.user,
                    defaults={'nota': nota, 'comentario': comentario}
                )
                if created:
                    messages.success(request, "Avaliação adicionada com sucesso!")
                else:
                    messages.success(request, "Avaliação atualizada com sucesso!")
                return redirect('detalhe_receita', receita_id=receita.id)

    context = {
        'receita': receita,
        'avaliacoes': avaliacoes,
        'media_avaliacoes': media_avaliacoes,
    }
    return render(request, 'detalhe_receita.html', context)

@login_required
def criar_receita(request):
    if request.method == 'POST':
        try:
            if not validar_ingredientes(request.POST['ingredientes']):
                messages.error(request, "Formato de ingredientes inválido. Use 'ingrediente: quantidade'.")
                return render(request, 'criar_receita.html', context)

            receita = Receita(
                titulo=request.POST['titulo'],
                descricao=request.POST['descricao'],
                ingredientes=request.POST['ingredientes'],  # Certifique-se de que os ingredientes estão no formato correto
                modo_preparo=request.POST['modo_preparo'],
                tempo_preparo=int(request.POST['tempo_preparo']),
                categoria=request.POST['categoria'],
                dificuldade=request.POST['dificuldade'],
                autor=request.user
            )
            if 'imagem' in request.FILES:
                receita.imagem = request.FILES['imagem']
            receita.save()
            messages.success(request, "Receita criada com sucesso!")
            return redirect('detalhe_receita', receita_id=receita.id)
        except Exception as e:
            messages.error(request, f"Erro ao criar receita: {str(e)}")
    
    context = {
        'categorias': Receita.CATEGORIA_CHOICES,
        'dificuldades': Receita.DIFICULDADE_CHOICES
    }
    return render(request, 'criar_receita.html', context)

@login_required
def editar_receita(request, receita_id):
    receita = get_object_or_404(Receita, id=receita_id, autor=request.user)
    if request.method == 'POST':
        receita.titulo = request.POST['titulo']
        receita.descricao = request.POST['descricao']
        receita.ingredientes = request.POST['ingredientes']
        receita.modo_preparo = request.POST['modo_preparo']
        receita.tempo_preparo = int(request.POST['tempo_preparo'])
        receita.categoria = request.POST['categoria']
        receita.dificuldade = request.POST['dificuldade']
        if 'imagem' in request.FILES:
            receita.imagem = request.FILES['imagem']
        receita.save()
        return redirect('detalhe_receita', receita_id=receita.id)
    return render(request, 'editar_receita.html', {'receita': receita, 'categorias': Receita.CATEGORIA_CHOICES, 'dificuldades': Receita.DIFICULDADE_CHOICES})

@login_required
def excluir_receita(request, receita_id):
    receita = get_object_or_404(Receita, id=receita_id, autor=request.user)
    if request.method == 'POST':
        receita.delete()
        return redirect('lista_receitas')
    return render(request, 'excluir_receita.html', {'receita': receita})

@login_required
@require_POST
def toggle_favorito(request, receita_id):
    receita = get_object_or_404(Receita, id=receita_id)
    if receita.favoritos.filter(id=request.user.id).exists():
        receita.favoritos.remove(request.user)
        is_favorito = False
    else:
        receita.favoritos.add(request.user)
        is_favorito = True
    return JsonResponse({'is_favorito': is_favorito})

@login_required
def lista_favoritos(request):
    receitas_favoritas = request.user.receitas_favoritas.all()
    return render(request, 'lista_favoritos.html', {'receitas': receitas_favoritas})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Você está logado como {username}.")
                return redirect('lista_receitas')
            else:
                messages.error(request,"Usuário ou senha inválidos.")
        else:
            messages.error(request,"Usuário ou senha inválidos.")
    else:
        form = AuthenticationForm()
    
    # Adicionar classes Bootstrap aos campos do formulário
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control bg-dark text-light'
    
    return render(request, 'login.html', {"form": form})

def logout_view(request):
    logout(request)
    messages.info(request, "Você saiu com sucesso.") 
    return redirect('lista_receitas')

def registro_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Nome de usuário já existe.')
            return redirect('registro')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'E-mail já está em uso.')
            return redirect('registro')

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            # Criar o perfil para o novo usuário sem especificar o email
            Profile.objects.create(user=user)
            messages.success(request, 'Conta criada com sucesso! Você pode fazer login agora.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
            return redirect('registro')

    return render(request, 'registro.html')

@login_required
def gerar_lista_compras(request):
    if request.method == 'POST':
        receitas_ids = request.POST.getlist('receitas')
        receitas = Receita.objects.filter(id__in=receitas_ids)
        lista_compras = ListaCompras.objects.create(usuario=request.user)
        lista_compras.receitas.set(receitas)
        
        ingredientes = {}
        for receita in receitas:
            for linha in receita.ingredientes.split('\n'):
                ingrediente = linha.strip()
                if ingrediente:
                    ingredientes[ingrediente] = ingredientes.get(ingrediente, 0) + 1
        
        return render(request, 'lista_compras.html', {'ingredientes': ingredientes})
    
    receitas = Receita.objects.all()
    return render(request, 'selecionar_receitas.html', {'receitas': receitas})

@login_required
def criar_colecao(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        Colecao.objects.create(nome=nome, usuario=request.user)
        return redirect('listar_colecoes')
    return render(request, 'nova_colecao.html')

@login_required
def listar_colecoes(request):
    colecoes = Colecao.objects.filter(usuario=request.user)
    return render(request, 'colecoes.html', {'colecoes': colecoes})

@login_required
def detalhe_colecao(request, colecao_id):
    colecao = get_object_or_404(Colecao, id=colecao_id, usuario=request.user)
    return render(request, 'detalhe_colecao.html', {'colecao': colecao})

@login_required
def adicionar_receita_colecao(request, receita_id):
    if request.method == 'POST':
        colecao_id = request.POST.get('colecao')
        colecao = get_object_or_404(Colecao, id=colecao_id, usuario=request.user)
        receita = get_object_or_404(Receita, id=receita_id)
        colecao.receitas.add(receita)
        return redirect('detalhe_receita', receita_id=receita_id)
    
    colecoes = Colecao.objects.filter(usuario=request.user)
    return render(request, 'adicionar_na_colecao.html', {'colecoes': colecoes, 'receita_id': receita_id})

@login_required
def remover_receita_colecao(request, colecao_id, receita_id):
    colecao = get_object_or_404(Colecao, id=colecao_id, usuario=request.user)
    receita = get_object_or_404(Receita, id=receita_id)
    colecao.receitas.remove(receita)
    return redirect('detalhe_colecao', colecao_id=colecao_id)

def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)

            # Enviar e-mail com o código de verificação
            try:
                subject = 'Redefinição de senha'
                email_template_name = 'password_reset_email.html'
                context = {
                    'email': user.email,
                    'domain': request.get_host(),
                    'site_name': 'Seu Site',
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'user': user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'https' if request.is_secure() else 'http',
                }
                email_body = render_to_string(email_template_name, context)
                send_mail(
                    subject,
                    email_body,
                    settings.EMAIL_HOST_USER,  # Remetente
                    [user.email],
                    fail_silently=False,
                )

                messages.success(request, 'Um e-mail de redefinição de senha foi enviado se o endereço estiver registrado.')
                return redirect('password_reset')  # Redireciona para a página de solicitação
            except Exception as e:
                messages.error(request, f'Erro ao enviar e-mail: {str(e)}')
        except User.DoesNotExist:
            messages.error(request, 'E-mail não encontrado.')

    return render(request, 'solicitar_recuperacao_senha.html')

def verificar_codigo(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        codigo = request.POST.get('codigo')
        try:
            user = User.objects.get(email=email)
            profile = user.profile  # Acessa o perfil do usuário
            if profile.codigo_verificacao == codigo:
                return redirect('redefinir_senha', email=email)
            else:
                messages.error(request, 'Código de verificação incorreto.')
        except User.DoesNotExist:
            messages.error(request, 'E-mail não encontrado.')
    
    return render(request, 'verificar_codigo.html')

def redefinir_senha(request, email):
    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha')
        try:
            user = User.objects.get(email=email)
            user.set_password(nova_senha)
            user.profile.codigo_verificacao = ''  # Limpa o código após a redefinição
            user.profile.save()
            user.save()
            messages.success(request, 'Senha redefinida com sucesso.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'E-mail não encontrado.')
    
    return render(request, 'redefinir_senha.html')

@login_required
def selecionar_receitas(request):
    receitas = Receita.objects.all()  # Obter todas as receitas
    if request.method == 'POST':
        receitas_selecionadas = request.POST.getlist('receitas')  # Obter as receitas selecionadas
        lista_compras = ListaCompras.objects.create(usuario=request.user)  # Criar uma nova lista de compras
        for receita_id in receitas_selecionadas:
            receita = Receita.objects.get(id=receita_id)
            lista_compras.receitas.add(receita)  # Adicionar a receita à lista de compras
        lista_compras.save()
        return redirect('lista_compras')  # Redirecionar para a página da lista de compras

    return render(request, 'selecionar_receitas.html', {'receitas': receitas})

def lista_compras(request):
    lista_compras = ListaCompras.objects.filter(usuario=request.user).last()  # Obter a última lista de compras
    ingredientes = {}
    if lista_compras:
        ingredientes = lista_compras.obter_ingredientes()  # Obter os ingredientes da lista de compras

    return render(request, 'lista_compras.html', {'ingredientes': ingredientes})

def validar_ingredientes(ingredientes):
    for linha in ingredientes.splitlines():
        linha = linha.strip()
        if linha:  # Ignora linhas vazias
            try:
                nome, quantidade = linha.split(':')
                # Verifica se a quantidade é um número
                int(quantidade.strip())
            except ValueError:
                return False  # Retorna False se o formato for inválido
    return True

