# users/swagger_setup.py
def apply_swagger_decorators():
    """Apply Swagger decorators to views after Django is fully loaded"""
    try:
        from . import swagger_docs
        from .views import (
            RegisterView, LoginView, LogoutView,
            VerifyEmailView, PasswordResetRequestView
        )
        
        # Apply decorators
        RegisterView.post = swagger_docs.get_register_swagger()(RegisterView.post)
        LoginView.post = swagger_docs.get_login_swagger()(LoginView.post)
        LogoutView.post = swagger_docs.get_logout_swagger()(LogoutView.post)
        VerifyEmailView.post = swagger_docs.get_verify_email_swagger()(VerifyEmailView.post)
        PasswordResetRequestView.post = swagger_docs.get_password_reset_swagger()(PasswordResetRequestView.post)
        
        print("✅ Swagger decorators applied successfully")
    except ImportError as e:
        print(f"⚠️ Could not apply Swagger decorators: {e}")
    except Exception as e:
        print(f"⚠️ Error applying Swagger decorators: {e}")