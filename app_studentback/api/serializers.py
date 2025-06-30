from rest_framework import serializers
from .models import Prof, Etudiant
import re
from django.contrib.auth import authenticate

class EtudiantRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Etudiant
        fields = ['id', 'last_name', 'first_name', 'email', 'filiere', 'niveau', 'photo', 'password']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.photo:
            representation['photo'] = instance.photo.url
        return representation

    def validate_email(self, value):
        if not re.match(r'^[a-zA-Z0-9_.+-]+@ump\.ac\.ma$', value):
            raise serializers.ValidationError("L'email doit être un email académique UMP (ex: ********@ump.ac.ma)")
        if Etudiant.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un compte avec cet email existe déjà.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        etudiant = Etudiant.objects.create_user(
            username=validated_data['email'],  # Utilisez email comme username
            password=password,
            **validated_data
        )
        return etudiant

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("L'utilisateur est désactivé.")
                return user
            else:
                raise serializers.ValidationError("Identifiants incorrects.")
        else:
            raise serializers.ValidationError("E-mail et mot de passe sont requis.")