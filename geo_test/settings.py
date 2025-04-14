"""
Django settings for geo_test project.

Generated by 'django-admin startproject' using Django 4.2.20.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-xxdsg2epffv4xvj=of7@a!3qjy(nn!_r^+r_4=4m0q$4!8*u%@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'base'
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        # or 'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

CORS_ALLOWED_ORIGINS = [
    # "http://localhost:3000",  
    # "http://localhost:5173",
    'https://figerprint-auther-backend.onrender.com',
    'https://fingerprint-auther-frontend.onrender.com'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'geo_test.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'geo_test.wsgi.application'

# settings.py
GEOPY_USER_AGENT = "base"  # Required for Nominatim


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.contrib.gis.db.backends.postgis',
#         'NAME': 'biometrics_tech',
#         'USER': 'webauthn_user',
#         'PASSWORD': 'FxArNKGA4xTplFZdL67IEh1jCxEwjbkp',
#         'HOST': 'dpg-cvtuqcadbo4c739bfa7g-a',
#         'PORT': '5432',
#     }
# }


import os
import dj_database_url

# Replace DATABASES with:
DATABASES = {
    'default': dj_database_url.config(
        default="postgresql://webauthn_user:iWqDIMj9uwyLvhRoPG4NKnLIUAFIXIfF@dpg-cvun01c9c44c738b6410-a.oregon-postgres.render.com/biometrics",
        conn_max_age=600,
    )
}




# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_EMAIL_UNIQUE = True


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # e.g., smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'geniusokwemba53@gmail.com'
EMAIL_HOST_PASSWORD = 'bevbzislkpdciakm '
DEFAULT_FROM_EMAIL = 'geniusokwemba53@gmail.com'

# Session settings
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True

# Authentication
LOGIN_URL = 'send-otp/'
LOGIN_REDIRECT_URL = 'otp-success/'  # Where to redirect after login
LOGOUT_REDIRECT_URL = 'login'     # Where to redirect after logout



JAZZMIN_SETTINGS = {
    # ====================== Core Branding ======================
    "site_title": "HR Nexus Admin",
    "site_header": "HR Nexus",
    "site_brand": "HR Nexus",
    "site_logo": "images/hr.png",  # Path to your HR logo
    "login_logo": "images/hr.png",  # Optional login screen logo
    "welcome_sign": "Welcome to HR Management System",
    "copyright": "Acme HR Solutions",
    
    # ====================== UI & Layout ======================
    "theme": "slate",  # Best for HR systems (dark sidebar + light content)
    "dark_mode_theme": None,  # Disable auto dark mode
    "show_ui_builder": False,  # Allow admins to tweak UI
    
    # ====================== HR-Specific Customizations ======================
    "icons": {
        "auth": "fas fa-users-cog",  # People management
        "auth.user": "fas fa-user",  # Employees
        "auth.Group": "fas fa-users",  # Teams
        "base.Employee": "fas fa-id-badge",  # Custom icon
        "base.Department": "fas fa-building",
        "base.Attendance": "fas fa-fingerprint",
        "base.Payroll": "fas fa-money-bill-wave",
    },
    
    "related_modal_active": True,  # HR systems benefit from modal popups
    "custom_css": "css/hr_custom.css",  # For additional HR-specific styling
    
    # ====================== Navigation ======================
    "order_with_respect_to": [
        "base",
        "auth",
        "base.Employee",
        "base.Department",
        "base.Attendance",
        "base.Payroll",
    ],
    
    # ====================== HR Dashboard ======================
    "show_sidebar": True,
    "navigation_expanded": True,  # Expanded nav by default for quick access
    "changeform_format": "horizontal_tabs",  # Better for employee records
}

JAZZMIN_UI_TWEAKS = {
    # ===== Professional Color Scheme =====
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-indigo",  # Trustworthy blue
    "accent": "accent-primary",  # HR systems look best with blue accents
    
    # ===== HR-Appropriate Styling =====
    "navbar": "navbar-dark",  # Dark navbar for professionalism
    "no_navbar_border": False,
    "sidebar": "sidebar-dark-indigo",  # Dark sidebar reduces eye strain
    "sidebar_nav_small_text": False,  # Better readability
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,  # Clear hierarchy for HR modules
    
    # ===== Data-Dense UI (HR needs tables!) =====
    "theme": "slate",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",  # For employee actions
        "warning": "btn-warning",  # For alerts
        "danger": "btn-danger",  # For termination flows
        "success": "btn-success"  # For hiring processes
    }
}

