# unitribe_server/users/throttles.py
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, ScopedRateThrottle

class LoginThrottle(ScopedRateThrottle):
    scope = 'login'

class RegisterThrottle(ScopedRateThrottle):
    scope = 'register'

class PasswordResetThrottle(ScopedRateThrottle):
    scope = 'password_reset'

class EmailVerificationThrottle(ScopedRateThrottle):
    scope = 'verify_email'