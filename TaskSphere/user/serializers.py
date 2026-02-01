from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

"""
USER AUTHENTICATION
"""
class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Too short password')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()

        return user
        

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserOTPVerificationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    otp_code = serializers.CharField(max_length=6)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordOTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for password reset page that combines OTP verification + new password.
    User must provide correct OTP AND new password in the same request.
    """
    user_id = serializers.IntegerField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)
    
    def validate(self, data):
        """
        Check that new_password and confirm_password match.
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        return data
    
    def validate_new_password(self, value):
        """
        Validate password strength.
        """
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters long')
        
        # Optional: Add more password strength checks
        if value.isdigit():
            raise serializers.ValidationError('Password cannot be entirely numeric')
        
        if value.isalpha():
            raise serializers.ValidationError('Password cannot be entirely alphabetic')
        
        return value



"""
USER SETTINGS
"""

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters long')
        return value
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        return data


class ChangeUsernameSerializer(serializers.Serializer):
    new_username = serializers.CharField(required=True, max_length=100)
    
    def validate_new_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already taken')
        if len(value) < 3:
            raise serializers.ValidationError('Username must be at least 3 characters long')
        return value


class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate_new_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value


class UserPreferencesSerializer(serializers.Serializer):
    theme = serializers.ChoiceField(choices=['light', 'dark', 'system'], required=False)
    language = serializers.ChoiceField(choices=['en', 'ru'], required=False)


"""
USER INTERFACE
"""

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'registered_at', 'current_streak')
    