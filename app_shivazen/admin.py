# app_shivazen/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

# Registros simples (para visualização padrão)
admin.site.register(Funcionalidade)
admin.site.register(Perfil)
admin.site.register(PerfilFuncionalidade)
admin.site.register(Profissional)
admin.site.register(Cliente)
admin.site.register(Prontuario)
admin.site.register(ProntuarioPergunta)
admin.site.register(Procedimento)
admin.site.register(ProfissionalProcedimento)
admin.site.register(Preco)
admin.site.register(DisponibilidadeProfissional)
admin.site.register(BloqueioAgenda)
admin.site.register(Atendimento)
admin.site.register(ProntuarioResposta)
admin.site.register(Notificacao)
admin.site.register(TermoConsentimento)
admin.site.register(LogAuditoria)

# --- CONFIGURAÇÃO CORRIGIDA PARA O ADMIN DE USUÁRIO ---
# Substitua a classe UsuarioAdmin antiga por esta:

@admin.register(Usuario) # Usa o decorator para registrar
class UsuarioAdmin(BaseUserAdmin):
    """
    Define a visualização admin para o modelo de Usuário customizado.
    """
    
    # Adiciona nossos campos customizados ('perfil', 'profissional') 
    # ao formulário de edição no admin.
    # (Copie os fieldsets padrão do BaseUserAdmin e adicione o seu)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Campos Customizados', {'fields': ('perfil', 'profissional')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Campos Customizados', {'fields': ('perfil', 'profissional')}),
    )
    
    # --- CORREÇÃO DOS ERROS ---
    # Substitui 'nome' por 'first_name' (ou 'get_full_name')
    # Substitui 'ativo' por 'is_active' (padrão do Django)
    list_display = ('email', 'first_name', 'perfil', 'is_active', 'is_staff')
    
    # Substitui 'ativo' por 'is_active'
    list_filter = ('perfil', 'is_active', 'is_staff')
    
    # Substitui 'nome' por 'first_name', 'last_name'
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)

# Remova a linha antiga, pois o @admin.register(Usuario) já faz o registro:
# admin.site.register(Usuario, UsuarioAdmin)