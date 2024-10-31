from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.lista_receitas, name='lista_receitas'),
    path('receita/<int:receita_id>/', views.detalhe_receita, name='detalhe_receita'),
    path('criar/', views.criar_receita, name='criar_receita'),
    path('editar/<int:receita_id>/', views.editar_receita, name='editar_receita'),
    path('excluir/<int:receita_id>/', views.excluir_receita, name='excluir_receita'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('toggle-favorito/<int:receita_id>/', views.toggle_favorito, name='toggle_favorito'),
    path('favoritos/', views.lista_favoritos, name='lista_favoritos'),
    path('colecoes/', views.listar_colecoes, name='listar_colecoes'),
    path('colecoes/nova/', views.criar_colecao, name='criar_colecao'),
    path('colecoes/<int:colecao_id>/', views.detalhe_colecao, name='detalhe_colecao'),
    path('receitas/<int:receita_id>/adicionar-colecao/', views.adicionar_receita_colecao, name='adicionar_receita_colecao'),
    path('colecoes/<int:colecao_id>/remover-receita/<int:receita_id>/', views.remover_receita_colecao, name='remover_receita_colecao'),
    path('verificar-codigo/', views.verificar_codigo, name='verificar_codigo'),
    path('solicitar-recuperacao-senha/', views.password_reset, name='password_reset'),  # URL para solicitar recuperação
    path('redefinir-senha/<str:email>/', views.redefinir_senha, name='redefinir_senha'),  # URL para redefinir senha
    path('selecionar-receitas/', views.selecionar_receitas, name='selecionar_receitas'),
    path('lista-compras/', views.lista_compras, name='lista_compras'),  # URL para a lista de compras
    path('password_reset/', views.password_reset, name='password_reset'),
    path('password_reset_confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
]
