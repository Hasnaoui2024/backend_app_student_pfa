from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('Le nom d’utilisateur doit être renseigné.')
        if not email:
            raise ValueError('L’email doit être renseigné.')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


# Modèle Professeur
class Prof(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='professeurs',
        blank=True,
        verbose_name='groupes',
        help_text='Les groupes auxquels appartient le professeur.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='professeurs',
        blank=True,
        verbose_name='permissions',
        help_text='Permissions spécifiques pour le professeur.',
    )

    objects = CustomUserManager()

    def __str__(self):
        return self.last_name


# Modèle Étudiant
class Etudiant(AbstractUser):
    email = models.EmailField(unique=True, validators=[
        RegexValidator(
            regex=r'^[a-zA-Z0-9_.+-]+@ump\.ac\.ma$',
            message="L'email doit être un email académique UMP (ex: nom.prenom@ump.ac.ma)"
        )
    ])
    niveau = models.CharField(max_length=50)
    filiere = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='etudiants/', null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'niveau', 'filiere']

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='etudiants',
        blank=True,
        verbose_name='groupes',
        help_text="Les groupes auxquels appartient l'étudiant.",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='etudiants',
        blank=True,
        verbose_name='permissions',
        help_text="Permissions spécifiques pour l'étudiant.",
    )

    objects = CustomUserManager()

    def __str__(self):
        return self.last_name


# Modèle Matière
class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    prof = models.ForeignKey(Prof, on_delete=models.CASCADE, related_name='matieres')

    def __str__(self):
        return self.nom


# Modèle Salle
class Salle(models.Model):
    TYPE_SALLE_CHOICES = [
        ('TP', 'Travaux Pratiques'),
        ('TD', 'Travaux Dirigés'),
        ('Cours', 'Cours'),
    ]
    id_salle = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100) 
    type_salle = models.CharField(max_length=10, choices=TYPE_SALLE_CHOICES)
    prof = models.ForeignKey(Prof, on_delete=models.CASCADE)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id_salle} - {self.type_salle}"


# Modèle Séance
class Seance(models.Model):
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    salle = models.ForeignKey(Salle, on_delete=models.CASCADE)
    prof = models.ForeignKey(Prof, on_delete=models.CASCADE)

    def __str__(self):
        return f"Séance {self.id} - {self.matiere.nom} ({self.date_debut})"


# Modèle Presence
class Presence(models.Model):
    STATUS_PRESENCE = [
        ('présent(e)', 'Présent(e)'),
    ]
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    seance = models.ForeignKey(Seance, on_delete=models.CASCADE)
    scanned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_PRESENCE, default='absent(e)')

    def __str__(self):
        return f"{self.etudiant.nom} - {self.seance} : {self.status}"