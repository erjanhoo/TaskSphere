from random import randint


def generate_otp():
    otp = randint(100000,999999)
    return otp

def check_otp(sent_otp, entered_otp):
    if sent_otp == entered_otp:
        return True
    else:
        return False