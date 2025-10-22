# app_shivazen/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime, timedelta # Adicionado para a função de horários

class Funcionalidade(models.Model):
    id_funcionalidade = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'funcionalidade'

class Perfil(models.Model):
    id_perfil = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True, null=True)
    funcionalidades = models.ManyToManyField(Funcionalidade, through='PerfilFuncionalidade')

    class Meta:
        db_table = 'perfil'

class PerfilFuncionalidade(models.Model):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, db_column='id_perfil')
    funcionalidade = models.ForeignKey(Funcionalidade, on_delete=models.CASCADE, db_column='id_funcionalidade')

    class Meta:
        db_table = 'perfil_funcionalidade'
        unique_together = (('perfil', 'funcionalidade'),)

class Profissional(models.Model):
    id_profissional = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'profissional'

    def get_horarios_disponiveis(self, data_selecionada):
        """
        Retorna uma lista de strings de horários disponíveis (ex: "09:00")
        para uma data específica.
        """
        # (1) Converte a data para o dia da semana (1=Dom, 2=Seg, ...)
        dia_semana = data_selecionada.isoweekday() % 7 + 1 
        try:
            # (2) Busca a disponibilidade padrão do profissional para esse dia
            disponibilidade = DisponibilidadeProfissional.objects.get(
                profissional=self, 
                dia_semana=dia_semana
            )
        except DisponibilidadeProfissional.DoesNotExist:
            return [] # Profissional não trabalha neste dia

        # (3) Busca agendamentos e bloqueios existentes
        agendamentos = Atendimento.objects.filter(
            profissional=self, 
            data_hora_inicio__date=data_selecionada, 
            status_atendimento__in=['AGENDADO', 'CONFIRMADO']
        )
        bloqueios = BloqueioAgenda.objects.filter(
            profissional=self, 
            data_hora_inicio__date__lte=data_selecionada, 
            data_hora_fim__date__gte=data_selecionada
        )

        horarios_disponiveis = []
        intervalo = timedelta(minutes=30) # Define o intervalo (ex: 30 min)
        
        # (4) Define a hora de início e fim do expediente
        hora_atual = datetime.combine(data_selecionada, disponibilidade.hora_inicio)
        hora_fim_expediente = datetime.combine(data_selecionada, disponibilidade.hora_fim)

        # (5) Itera sobre os horários do dia
        while hora_atual < hora_fim_expediente:
            horario_ocupado = False
            
            # (6) Verifica se o horário conflita com um agendamento
            for ag in agendamentos:
                if hora_atual >= ag.data_hora_inicio and hora_atual < ag.data_hora_fim:
                    horario_ocupado = True
                    break
            
            # (7) Verifica se o horário conflita com um bloqueio
            if not horario_ocupado:
                for bl in bloqueios:
                    # Verifica se a hora_atual está dentro do período de bloqueio
                    if bl.data_hora_inicio <= hora_atual < bl.data_hora_fim:
                        horario_ocupado = True
                        break
            
            # (8) Se não estiver ocupado, adiciona à lista
            if not horario_ocupado:
                horarios_disponiveis.append(hora_atual.strftime('%H:%M'))
            
            hora_atual += intervalo

        return horarios_disponiveis

# --- MODELO DE USUÁRIO ATUALIZADO ---
# Substitua o modelo 'Usuario' antigo por este
class Usuario(AbstractUser):
    # AbstractUser já possui:
    # id (PK), username, first_name, last_name, email, password (hash),
    # is_staff, is_active, date_joined, etc.
    
    # Vamos garantir que o email seja único e usado para login
    email = models.EmailField(unique=True)

    # Nossos campos customizados
    perfil = models.ForeignKey(Perfil, on_delete=models.RESTRICT, null=True, blank=True)
    profissional = models.OneToOneField(Profissional, on_delete=models.SET_NULL, blank=True, null=True)
    chave_secreta_2fa = models.TextField(blank=True, null=True) # Para RNF-03

    # Define que o campo 'email' será o 'username' para fins de login
    USERNAME_FIELD = 'email'
    
    # Campos obrigatórios ao criar um usuário (além de email e senha)
    # 'username' ainda é usado internamente pelo Django
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'usuario' # Mantém o nome da tabela original

# --- RESTANTE DOS SEUS MODELOS (sem alteração) ---

class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nome_completo = models.CharField(max_length=150)
    data_nascimento = models.DateField(blank=True, null=True)
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    profissao = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cliente'

class Prontuario(models.Model):
    id_prontuario = models.AutoField(primary_key=True)
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)

    class Meta:
        db_table = 'prontuario'

class ProntuarioPergunta(models.Model):
    id_pergunta = models.AutoField(primary_key=True)
    texto = models.TextField()
    tipo_resposta = models.CharField(max_length=50)
    ativa = models.BooleanField(default=True)

    class Meta:
        db_table = 'prontuario_pergunta'

class Procedimento(models.Model):
    id_procedimento = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    duracao_minutos = models.IntegerField()
    ativo = models.BooleanField(default=True)
    profissionais = models.ManyToManyField(Profissional, through='ProfissionalProcedimento')

    class Meta:
        db_table = 'procedimento'

class ProfissionalProcedimento(models.Model):
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, db_column='id_profissional')
    procedimento = models.ForeignKey(Procedimento, on_delete=models.CASCADE, db_column='id_procedimento')

    class Meta:
        db_table = 'profissional_procedimento'
        unique_together = (('profissional', 'procedimento'),)

class Preco(models.Model):
    id_preco = models.AutoField(primary_key=True)
    procedimento = models.ForeignKey(Procedimento, on_delete=models.CASCADE)
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'preco'

class DisponibilidadeProfissional(models.Model):
    id_disponibilidade = models.AutoField(primary_key=True)
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE)
    dia_semana = models.IntegerField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    class Meta:
        db_table = 'disponibilidade_profissional'

class BloqueioAgenda(models.Model):
    id_bloqueio = models.AutoField(primary_key=True)
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, blank=True, null=True)
    data_hora_inicio = models.DateTimeField()
    data_hora_fim = models.DateTimeField()
    motivo = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'bloqueio_agenda'

class Atendimento(models.Model):
    id_atendimento = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT)
    profissional = models.ForeignKey(Profissional, on_delete=models.RESTRICT)
    procedimento = models.ForeignKey(Procedimento, on_delete=models.RESTRICT)
    data_hora_inicio = models.DateTimeField()
    data_hora_fim = models.DateTimeField()
    valor_cobrado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status_atendimento = models.CharField(max_length=20, default='AGENDADO')
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'atendimento'

class ProntuarioResposta(models.Model):
    id_resposta = models.AutoField(primary_key=True)
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE)
    pergunta = models.ForeignKey(ProntuarioPergunta, on_delete=models.RESTRICT)
    resposta_texto = models.TextField(blank=True, null=True)
    resposta_boolean = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = 'prontuario_resposta'

class Notificacao(models.Model):
    id_notificacao = models.AutoField(primary_key=True)
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE)
    canal = models.CharField(max_length=20)
    status_envio = models.CharField(max_length=20)
    data_hora_envio = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'notificacao'

class TermoConsentimento(models.Model):
    id_termo = models.AutoField(primary_key=True)
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE)
    usuario_assinatura = models.ForeignKey(Usuario, on_delete=models.SET_NULL, blank=True, null=True)
    ip_assinatura = models.CharField(max_length=45, blank=True, null=True)
    data_hora_assinatura = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'termo_consentimento'

class LogAuditoria(models.Model):
    id_log = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, blank=True, null=True)
    acao = models.CharField(max_length=255)
    tabela_afetada = models.CharField(max_length=100, blank=True, null=True)
    id_registro_afetado = models.IntegerField(blank=True, null=True)
    detalhes = models.JSONField(blank=True, null=True)
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'log_auditoria'