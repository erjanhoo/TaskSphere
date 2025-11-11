from random import randint
from .models import Badges, UserBadge, KarmaTransaction

def generate_otp():
    otp = randint(100000,999999)
    return otp

def check_otp(sent_otp, entered_otp):
    if sent_otp == entered_otp:
        return True
    else:
        return False
    

def assign_badge_based_on_karma(user):
    """
    Assign all badges that the user has earned based on their total karma.
    Awards all badges from beginner up to their current karma level.
    """
    user_karma_amount = user.karma

    # Get all badges the user should have earned (all badges with max <= user's karma)
    earned_badges = Badges.objects.filter(karma_max__lte=user_karma_amount)
    
    # Also include the current level badge
    current_level_badge = Badges.objects.filter(
        karma_min__lte=user_karma_amount,
        karma_max__gte=user_karma_amount
    ).first()
    
    # Collect all badges to award
    badges_to_award = list(earned_badges)
    if current_level_badge and current_level_badge not in badges_to_award:
        badges_to_award.append(current_level_badge)
    
    # Award each badge if not already awarded
    for badge in badges_to_award:
        if not UserBadge.objects.filter(user=user, badge=badge).exists():
            UserBadge.objects.create(user=user, badge=badge)

def award_karma_to_user(user, amount, reason=''):
    """
    Award karma to user and track the transaction.
    Amount can be positive (award) or negative (penalty).
    """
    if amount == 0:
        return

    user.karma += amount
    
    # Prevent negative karma
    if user.karma < 0:
        user.karma = 0
    
    user.save()
    
    # Track the transaction
    KarmaTransaction.objects.create(
        user=user,
        amount=amount,
        reason=reason
    )

    assign_badge_based_on_karma(user=user)

     

