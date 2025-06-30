# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterEtudiantView, LoginView ,RegisterPresenceView, GetStudentPresenceView,StudentSettingsView,LogoutView,GetUserIdView



urlpatterns = [
    path('register/', RegisterEtudiantView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('presence/', RegisterPresenceView.as_view(), name='register_presence'),
    path('presence/list/', GetStudentPresenceView.as_view(), name='get_presence_list'),
    path('settings/<int:student_id>/', StudentSettingsView.as_view(), name='student_settings'),
    path('get-user-id/', GetUserIdView.as_view(), name='get_user_id'),
]