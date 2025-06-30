from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Etudiant, Seance, Presence
from .serializers import EtudiantRegisterSerializer, LoginSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
import json
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class RegisterEtudiantView(APIView):
    def post(self, request):
        serializer = EtudiantRegisterSerializer(data=request.data)
        if serializer.is_valid():
            etudiant = serializer.save()
            return Response(
                {"message": "Inscription réussie"}, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"error": "Données invalides", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'student_id': user.id,
                'email': user.email,
                'nom': user.last_name
            }, status=status.HTTP_200_OK)
        else:
            error_message = list(serializer.errors.values())[0][0] if serializer.errors else "Erreur de connexion"
            return Response(
                {"error": error_message},
                status=status.HTTP_400_BAD_REQUEST,
                content_type='application/json'
            )

class RegisterPresenceView(APIView):
    def post(self, request):
        try:
            # Récupérer les données JSON
            data = request.data
            etudiant_id = data.get('etudiant_id')
            seance_id = data.get('seance_id')

            if not etudiant_id or not seance_id:
                return Response({"error": "Données manquantes"}, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier si l'étudiant et la séance existent
            try:
                etudiant = Etudiant.objects.get(id=etudiant_id)
                seance = Seance.objects.get(id=seance_id)
            except Etudiant.DoesNotExist:
                return Response({"error": "Étudiant non trouvé"}, status=status.HTTP_404_NOT_FOUND)
            except Seance.DoesNotExist:
                return Response({"error": "Séance non trouvée"}, status=status.HTTP_404_NOT_FOUND)

            # Vérifier si la séance est en cours
            now = timezone.now()
            if now < seance.date_debut or now > seance.date_fin:
                return Response({"error": "La séance n'est pas en cours actuellement"}, status=status.HTTP_400_BAD_REQUEST)

            # Enregistrer la présence
            presence, created = Presence.objects.get_or_create(
                etudiant=etudiant,
                seance=seance,
                defaults={'status': 'présent(e)'}
            )
            if created:
                return Response({
                    "message": "Présence enregistrée",
                    "etudiant": etudiant.last_name,
                    "seance": seance.id,
                    "scanned_at": presence.scanned_at
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "message": "Présence déjà enregistrée","presence_id": presence.id}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetStudentPresenceView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            etudiant_id = data.get('etudiant_id')

            if not etudiant_id:
                return Response(
                    {"error": "ID étudiant manquant"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Vérifier si l'étudiant existe
            try:
                etudiant = Etudiant.objects.get(id=etudiant_id)
            except Etudiant.DoesNotExist:
                return Response(
                    {"error": "Étudiant non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Récupérer toutes les présences avec les relations nécessaires
            presences = Presence.objects.filter(etudiant=etudiant).select_related(
                'seance__matiere',
                'seance__prof',
                'seance__salle'
            )

            result = []
            for presence in presences:
                result.append({
                    'id': presence.id,
                    'matiere': presence.seance.matiere.nom,
                    'date': presence.seance.date_debut,
                    'status': presence.status,
                    'scanned_at': presence.scanned_at,
                    'prof_nom': f"{presence.seance.prof.last_name} {presence.seance.prof.first_name or ''}",
                    'salle_nom': presence.seance.salle.nom,
                    'salle_type': presence.seance.salle.get_type_salle_display(),
                    'date_fin': presence.seance.date_fin
                })

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StudentSettingsView(APIView):
    def get(self, request, student_id):
        try:
            etudiant = Etudiant.objects.get(id=student_id)
            return Response({
                'id': etudiant.id,
                'last_name': etudiant.last_name,
                'first_name': etudiant.first_name,
                'email': etudiant.email,
                'filiere': etudiant.filiere,
                'niveau': etudiant.niveau,
                'photo': etudiant.photo.url if etudiant.photo else None
            }, status=status.HTTP_200_OK)
        except Etudiant.DoesNotExist:
            return Response({'error': 'Étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, student_id):
        try:
            etudiant = Etudiant.objects.get(id=student_id)

            # Mise à jour des champs
            etudiant.last_name = request.data.get('last_name', etudiant.last_name)
            etudiant.first_name = request.data.get('first_name', etudiant.first_name)
            etudiant.filiere = request.data.get('filiere', etudiant.filiere)
            etudiant.niveau = request.data.get('niveau', etudiant.niveau)

            # Gestion de l'email
            new_email = request.data.get('email')
            if new_email and new_email != etudiant.email:
                if not re.match(r'^[a-zA-Z0-9_.+-]+@ump\.ac\.ma$', new_email):
                    return Response(
                        {"error": "Email UMP requis (ex: nom@ump.ac.ma)"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                etudiant.email = new_email
                etudiant.email = new_email

            # Gestion du mot de passe
            new_password = request.data.get('password')
            if new_password:
                etudiant.set_password(new_password)

            # Gestion de la photo
            if 'photo' in request.FILES:
                etudiant.photo = request.FILES['photo']

            etudiant.save()
            response_data={
                'id': etudiant.id,
                'last_name': etudiant.last_name,
                'first_name': etudiant.first_name,
                'email': etudiant.email,
                'filiere': etudiant.filiere,
                'niveau': etudiant.niveau,
                'photo': etudiant.photo.url if etudiant.photo else None
            }

            return Response(
                {"message": "Profil mis à jour", "etudiant": EtudiantRegisterSerializer(etudiant).data},
                status=status.HTTP_200_OK
            )

        except Etudiant.DoesNotExist:
            return Response(
                {"error": "Étudiant non trouvé"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur serveur: {str(e)}"},  # Capture toute autre erreur
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Récupérer le token de l'utilisateur connecté
            token = Token.objects.get(user=request.user)
            token.delete()  # Supprime le token
            return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"error": "Token introuvable"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#récupérer uniquement l'ID de l'étudiant connecté
class GetUserIdView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            etudiant = Etudiant.objects.get(user=request.user)
            return Response({'id': etudiant.id}, status=status.HTTP_200_OK)
        except Etudiant.DoesNotExist:
            return Response({'error': 'Étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)