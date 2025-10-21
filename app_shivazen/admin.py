# app_shivazen/admin.py
from django.contrib import admin
from .models import *

# Personalização da listagem de Clientes
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'email', 'telefone', 'data_cadastro', 'ativo')
    search_fields = ('nome_completo', 'cpf', 'email')
    list_filter = ('ativo', 'data_cadastro')
    list_per_page = 20

# Personalização da listagem de Atendimentos
@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):
    list_display = ('id_atendimento', 'cliente', 'profissional', 'procedimento', 'data_hora_inicio', 'status_atendimento')
    search_fields = ('cliente__nome_completo', 'profissional__nome')
    list_filter = ('status_atendimento', 'data_hora_inicio', 'profissional', 'procedimento')
    list_per_page = 20
    autocomplete_fields = ['cliente', 'profissional', 'procedimento']

# Personalização da listagem de Profissionais
@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'especialidade', 'ativo')
    search_fields = ('nome', 'especialidade') # <-- CAMPO ADICIONADO PARA CORREÇÃO
    list_filter = ('ativo',)

# Personalização da listagem de Procedimentos
@admin.register(Procedimento)
class ProcedimentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'duracao_minutos', 'ativo')
    search_fields = ('nome',) # <-- CAMPO ADICIONADO PARA CORREÇÃO
    list_filter = ('ativo',)

# Personalização da listagem de Usuários do sistema
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'perfil', 'ativo')
    search_fields = ('nome', 'email') # <-- CAMPO ADICIONADO PARA CORREÇÃO
    list_filter = ('perfil', 'ativo')
    autocomplete_fields = ['perfil', 'profissional']

# Personalização para o Perfil (necessário para o autocomplete do UsuarioAdmin)
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',) # <-- CAMPO ADICIONADO PARA CORREÇÃO

# Registro dos outros modelos (sem personalização avançada por enquanto)
admin.site.register(Funcionalidade)
admin.site.register(DisponibilidadeProfissional)
admin.site.register(BloqueioAgenda)
admin.site.register(Preco)
admin.site.register(Prontuario)
admin.site.register(ProntuarioPergunta)
admin.site.register(ProntuarioResposta)
admin.site.register(Notificacao)
admin.site.register(TermoConsentimento)
admin.site.register(LogAuditoria)
admin.site.register(PerfilFuncionalidade)
admin.site.register(ProfissionalProcedimento)