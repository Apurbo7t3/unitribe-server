# users/apps.py
from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    
    def ready(self):
        # Import and apply swagger decorators after apps are loaded
        try:
            from .swagger_setup import apply_swagger_decorators
            apply_swagger_decorators()
        except ImportError:
            pass  # Swagger not available or not needed