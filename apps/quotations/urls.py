from django.urls import path
from . import views

app_name = 'quotations'

urlpatterns = [
    path('', views.QuotationListView.as_view(), name='list'),
    path('kanban/', views.QuotationKanbanView.as_view(), name='kanban'),
    path('create/', views.QuotationCreateView.as_view(), name='create'),
    path('<int:pk>/', views.QuotationDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.QuotationUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.QuotationDeleteView.as_view(), name='delete'),
    path('<int:pk>/duplicate/', views.QuotationDuplicateView.as_view(), name='duplicate'),
    
    # AJAX endpoints
    path('<int:pk>/update-status/', views.update_quotation_status, name='update_status'),
] 