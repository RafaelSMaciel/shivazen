# shivazen/settings.py
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configuração de Segurança (Variáveis de Ambiente) ---
# Em produção (Railway), crie variáveis de ambiente para estes valores.
# O valor depois da vírgula é um 'default' para desenvolvimento local.

# ATENÇÃO: Troque o valor padrão da SECRET_KEY por um novo se desejar
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY', 
    'django-insecure-3zv0f3g^s$gtfqet^@+*ws5+kg_6x@ez_42x5vg7a$=2g*ru@j' # Mantenha a sua chave local aqui
)

# Em produção, defina a variável de ambiente DEBUG=False
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Em produção, defina ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
# O 'default' '*' é SÓ para desenvolvimento.
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')


# Application definition

INSTALLED_APPS = [
    'jazzmin', 
    'app_shivazen',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shivazen.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'shivazen.wsgi.application'


# --- Banco de Dados com Variáveis de Ambiente ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'shivazen_prod'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'admin'), 
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'options': '-c search_path=shivazen_prod,shivazen_app'
        }
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# --- Configurações de Arquivos Estáticos (WhiteNoise) ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'app_shivazen/static')]

# Pasta para onde o 'collectstatic' vai copiar os arquivos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 

# Adicionado: Armazenamento otimizado do WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Adicionado: Apontando para o novo Modelo de Usuário ---
AUTH_USER_MODEL = 'app_shivazen.Usuario'

# --- Configurações do JAZZMIN (Mantidas) ---
JAZZMIN_SETTINGS = {
    "site_title": "Shiva Zen Admin",
    "site_header": "Shiva Zen",
    "site_brand": "Shiva Zen Admin",
    "login_logo": "assents/LogoCompletaSemFundo.png",
    "site_logo": "assents/LogoSemFundo.png",
    "welcome_sign": "Bem-vindo à Administração da Shiva Zen",
    "copyright": "Shiva Zen Ltda",

    # Links no topo
    "topmenu_links": [
        {"name": "Voltar ao Site",  "url": "shivazen:inicio", "new_window": True},
        {"model": "app_shivazen.Usuario", "name": "Usuários do Sistema"},
    ],

    "navigation": [
        {"name": "PRINCIPAL", "icon": "fas fa-tachometer-alt"},
        {"name": "Agenda", "icon": "fas fa-calendar-alt", "models": [
            {"model": "app_shivazen.atendimento", "label": "Ver Agendamentos", "icon": "fas fa-calendar-check"},
            {"model": "app_shivazen.disponibilidadeprofissional", "label": "Disponibilidades", "icon": "fas fa-clock"},
            {"model": "app_shivazen.bloqueioagenda", "label": "Bloqueios de Agenda", "icon": "fas fa-calendar-times"},
        ]},
        {"name": "Cadastros", "icon": "fas fa-edit", "models": [
            {"model": "app_shivazen.cliente", "label": "Clientes", "icon": "fas fa-address-book"},
            {"model": "app_shivazen.profissional", "label": "Profissionais", "icon": "fas fa-user-md"},
            {"model": "app_shivazen.procedimento", "label": "Procedimentos", "icon": "fas fa-spa"},
            {"model": "app_shivazen.preco", "label": "Tabela de Preços"},
        ]},
        {"name": "Configurações", "icon": "fas fa-cogs", "models": [
            {"name": "Perguntas do Prontuário", "model": "app_shivazen.prontuariopergunta", "icon": "fas fa-question-circle"},
            {"label": "Administração do Site", "icon": "fas fa-tools", "models": [
                {"name": "Usuários (Sistema)", "model": "app_shivazen.usuario", "icon": "fas fa-user-shield"},
                {"name": "Perfis de Acesso", "model": "app_shivazen.perfil", "icon": "fas fa-id-card"},
                {"name": "Funcionalidades", "model": "app_shivazen.funcionalidade", "icon": "fas fa-key"},
                {"name": "Logs de Auditoria", "model": "app_shivazen.logauditoria", "icon": "fas fa-history"},
                # Removidos 'auth.user' e 'auth.group' pois agora gerenciamos por 'app_shivazen.usuario'
            ]},
        ]},
    ],
   
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        # Adicione ícones para seu app se desejar
        "app_shivazen.Usuario": "fas fa-user-shield",
        "app_shivazen.Perfil": "fas fa-id-card",
        # ...
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_theme": "darkly",
    "brand_colour": "#8b5c00",
    "accent": "#b48c4c",
    "navbar": "navbar-white navbar-light",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "actions_sticky_top": True,
    "theme_switcher": True
}