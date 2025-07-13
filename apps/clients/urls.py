from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Client URLs
    path('', views.ClientListView.as_view(), name='list'),
    path('create/', views.ClientCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='delete'),
    
    # Client Notes URLs
    path('notes/', views.ClientNoteListView.as_view(), name='note_list_all'),
    path('<int:client_pk>/notes/', views.ClientNoteListView.as_view(), name='note_list'),
    path('<int:client_pk>/notes/create/', views.ClientNoteCreateView.as_view(), name='note_create'),
    path('notes/<int:pk>/', views.ClientNoteDetailView.as_view(), name='note_detail'),
    path('notes/<int:pk>/edit/', views.ClientNoteUpdateView.as_view(), name='note_update'),
    path('notes/<int:pk>/delete/', views.ClientNoteDeleteView.as_view(), name='note_delete'),
    
    # AJAX URLs for notes
    path('notes/<int:pk>/toggle-resolved/', views.toggle_note_resolved, name='note_toggle_resolved'),
]