from random import randint
from .models import Badges, UserBadge

def generate_otp():
    otp = randint(100000,999999)
    return otp

def check_otp(sent_otp, entered_otp):
    if sent_otp == entered_otp:
        return True
    else:
        return False
    

def assign_badge_based_on_karma(user):
    user_karma_amount = user.karma

    get_badge = Badges.objects.filter(
        karma_min__lte=user_karma_amount,
        karma_max__gte=user_karma_amount
    ).first()

    if UserBadge.objects.filter(user=user, badge=get_badge).exists():
        return
    
    if get_badge is None:
        return

    UserBadge.objects.create(
        user=user,
        badge=get_badge
    )

def award_karma_to_user(user, amount, reason=''):
    if amount <= 0:
        return

    user.karma += amount
    user.save()

    assign_badge_based_on_karma(user=user) 

