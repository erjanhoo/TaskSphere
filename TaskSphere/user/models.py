from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models


class MyUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)  # Normalize email to avoid duplicates
        user = self.model(username=username, email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_admin = True
        user.is_superuser = True  # Required for superuser privileges
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, email):
        return self.get(**{self.model.USERNAME_FIELD: email})


class MyUser(AbstractBaseUser):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    registered_at = models.DateTimeField(auto_now_add=True)
    current_streak = models.PositiveSmallIntegerField(default=0)
    highest_streak = models.PositiveSmallIntegerField(default=0)
    karma = models.SmallIntegerField(default=0)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    forgot_password_otp = models.CharField(max_length=6, blank=True, null=True)
    forgot_password_otp_created_at = models.DateTimeField(blank=True, null=True)
    
    # Profile Picture
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_2fa_enabled = models.BooleanField(default=False)

    objects = MyUserManager() 

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class TemporaryUser(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)
    registered_at = models.DateTimeField(auto_now_add=True)
    otp_code = models.CharField(max_length=6)
    otp_created_at = models.DateTimeField(blank=True, null=True)




class Badges(models.Model):

    LEVELS = [
        ('beginner', 'Beginner'),
        ('novice', 'Novice'),
        ('intermediate', 'Intermediate'),
        ('professional', 'Professional'),
        ('expert', 'Expert'),
        ('master', 'Master'),
        ('grand_master', 'Grand Master'),
        ('enlightened', 'Enlightened')
    ]

    name = models.CharField(choices=LEVELS, max_length=123)
    icon = models.ImageField(upload_to='badges_icons/', blank=True, null=True)

    karma_min = models.PositiveIntegerField(default=0)
    karma_max = models.PositiveIntegerField(default=0)


class UserBadge(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True, blank=True)
    badge = models.ForeignKey(Badges, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f'{self.user.username} - {self.badge.name}'


class KarmaTransaction(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='karma_transactions')
    amount = models.IntegerField()  # Can be positive or negative
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.amount} karma - {self.reason}'
