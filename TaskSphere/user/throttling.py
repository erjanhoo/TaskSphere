from rest_framework.throttling import AnonRateThrottle


class OTPVerificationThrottle(AnonRateThrottle):
    """
    Throttle for OTP verification endpoints to prevent brute-force attacks.
    Allows 5 attempts per minute per IP address.
    """
    rate = '5/min'


class OTPResendThrottle(AnonRateThrottle):
    """
    Throttle for OTP resend endpoints to prevent spam.
    Allows 3 resend requests per hour per IP address.
    """
    rate = '1/min'

class ForgotPasswordThrottle(AnonRateThrottle):
    """
    Throttle for OTP sending to user email in case if 
    he forgot the password. Allows 5 requests per hour per IP address.
    """
    rate = '5/hour'