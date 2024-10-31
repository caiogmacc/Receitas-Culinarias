from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Receita(models.Model):
    DIFICULDADE_FACIL = 'F'
    DIFICULDADE_MEDIO = 'M'
    DIFICULDADE_DIFICIL = 'D'
    DIFICULDADE_CHOICES = [
        (DIFICULDADE_FACIL, 'Fácil'),
        (DIFICULDADE_MEDIO, 'Médio'),
        (DIFICULDADE_DIFICIL, 'Difícil'),
    ]

    CATEGORIA_ENTRADA = 'E'
    CATEGORIA_PRATO_PRINCIPAL = 'P'
    CATEGORIA_SOBREMESA = 'S'
    CATEGORIA_BEBIDA = 'B'
    CATEGORIA_CHOICES = [
        (CATEGORIA_ENTRADA, 'Entrada'),
        (CATEGORIA_PRATO_PRINCIPAL, 'Prato Principal'),
        (CATEGORIA_SOBREMESA, 'Sobremesa'),
        (CATEGORIA_BEBIDA, 'Bebida'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    ingredientes = models.TextField()
    modo_preparo = models.TextField()
    tempo_preparo = models.IntegerField(help_text="Tempo em minutos")
    categoria = models.CharField(max_length=1, choices=CATEGORIA_CHOICES)
    dificuldade = models.CharField(max_length=1, choices=DIFICULDADE_CHOICES)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    favoritos = models.ManyToManyField(User, related_name='receitas_favoritas', blank=True)
    imagem = models.ImageField(upload_to='receitas/', null=True, blank=True)

    def __str__(self):
        return self.titulo

    def media_avaliacoes(self):
        avaliacoes = self.avaliacao_set.all()
        if avaliacoes:
            return sum([a.nota for a in avaliacoes]) / len(avaliacoes)
        return 0

class Avaliacao(models.Model):
    receita = models.ForeignKey(Receita, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nota = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('receita', 'usuario')

    def __str__(self):
        return f"{self.usuario.username} - {self.receita.titulo} - {self.nota}"

class ListaCompras(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    receitas = models.ManyToManyField(Receita)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lista de Compras de {self.usuario.username}"

    def obter_ingredientes(self):
        """Retorna um dicionário de ingredientes e suas quantidades."""
        ingredientes = {}
        for receita in self.receitas.all():
            for linha in receita.ingredientes.splitlines():  # Supondo que os ingredientes estão separados por linhas
                linha = linha.strip()  # Remove espaços em branco
                if not linha:  # Ignora linhas vazias
                    continue
                try:
                    nome, quantidade = linha.split(':')  # Supondo que o formato é "ingrediente: quantidade"
                    if nome in ingredientes:
                        ingredientes[nome] += int(quantidade)  # Soma as quantidades se o ingrediente já existir
                    else:
                        ingredientes[nome] = int(quantidade)
                except ValueError:
                    print(f"Formato inválido para a linha: {linha}")  # Loga a linha com formato inválido
        return ingredientes

class Colecao(models.Model):
    nome = models.CharField(max_length=100)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    receitas = models.ManyToManyField('Receita')

    def __str__(self):
        return self.nome

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    codigo_verificacao = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return self.user.username
