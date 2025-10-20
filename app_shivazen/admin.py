# app_shivazen/admin.py
from django.contrib import admin
from .models import *

# Registra os modelos mais importantes para gerenciamento na interface de admin
admin.site.register(Perfil)
admin.site.register(Funcionalidade)
admin.site.register(Profissional)
admin.site.register(Procedimento)
admin.site.register(Cliente)
admin.site.register(Atendimento)
admin.site.register(DisponibilidadeProfissional)
admin.site.register(Usuario)
admin.site.register(ProntuarioPergunta)