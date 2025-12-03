"""
Django settings for crm_clinic_system project.
"""

from pathlib import Path
import os
import sys
from dotenv import load_dotenv # Thư viện đọc file .env

# Load biến môi trường từ file .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Thêm thư mục 'apps' vào đường dẫn hệ thống
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# --- 1. CẤU HÌNH BẢO MẬT (Lấy từ .env) ---
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-fallback-key-changeme')

# Mặc định là False cho an toàn, chỉ True nếu trong .env để là True
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

allowed_hosts_env = os.getenv('DJANGO_ALLOWED_HOSTS')
if allowed_hosts_env:
    ALLOWED_HOSTS = allowed_hosts_env.split(',')
else:
    ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize', # Hỗ trợ format tiền
    
    # CÁC APPS CỦA CHÚNG TA
    'apps.authentication', 
    'apps.customers',
    'apps.telesales',
    'apps.bookings',
    'apps.sales',
    'apps.marketing', 
    'apps.hr',
    'apps.chat',
    'apps.resources',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- 2. CẤU HÌNH DATABASE (Thông minh) ---
# Tự động chọn MySQL nếu có cấu hình trong .env, ngược lại dùng SQLite
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

if DB_NAME and DB_USER and DB_PASSWORD and DB_HOST:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': '3306',
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    # Fallback về SQLite (giữ nguyên dữ liệu cũ của bạn)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- 3. CẤU HÌNH EMAIL (SMTP) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

USE_L10N = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','
NUMBER_GROUPING = 3

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# Cấu hình đường dẫn Static Root cho môi trường Production (PythonAnywhere)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'authentication.User'
LOGIN_URL = '/auth/login/' 
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- 4. JAZZMIN SETTINGS (Giao diện Admin) ---
JAZZMIN_SETTINGS = {
    "site_title": "V-Medical Admin",
    "site_header": "V-Medical System",
    "site_brand": "V-Medical",
    "site_logo": "images/logo.png",
    "welcome_sign": "Chào mừng đến V-Medical Clinic",
    "copyright": "V-Medical Clinic Technology",
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Trang chủ", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Vào màn hình Telesale", "url": "/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "authentication.User": "fas fa-user-shield",
        "customers.Customer": "fas fa-address-book",
        "telesales.CallLog": "fas fa-headset",
        "bookings.Appointment": "fas fa-calendar-check",
        "sales.Order": "fas fa-file-invoice-dollar",
        "sales.Service": "fas fa-list-alt",
        "marketing.DailyCampaignStat": "fas fa-chart-line",
        "hr.EmployeeContract": "fas fa-file-contract",
        "hr.Attendance": "fas fa-clock",
        "hr.SalarySlip": "fas fa-money-check-alt",
        "chat.Message": "fas fa-comments",
    },
    "order_with_respect_to": ["telesales", "customers", "bookings", "sales", "marketing", "hr", "chat", "authentication", "auth"],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-dark navbar-primary",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "theme": "flatly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary", "secondary": "btn-secondary", "info": "btn-info",
        "warning": "btn-warning", "danger": "btn-danger", "success": "btn-success"
    }
}