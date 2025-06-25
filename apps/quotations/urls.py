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
    path('<int:pk>/pdf/', views.QuotationPDFView.as_view(), name='pdf'),
    path('<int:pk>/preview/', views.QuotationPreviewView.as_view(), name='preview'),
    
    # AJAX endpoints
    path('<int:pk>/update-status/', views.update_quotation_status, name='update_status'),
    path('get-company-info/<int:company_id>/', views.get_company_info, name='get_company_info'),
    
    # Activity management
    path('<int:quotation_pk>/activities/', views.QuotationActivityListView.as_view(), name='activity_list'),
    path('<int:quotation_pk>/activities/create/', views.QuotationActivityCreateView.as_view(), name='activity_create'),
    path('activities/<int:pk>/edit/', views.QuotationActivityUpdateView.as_view(), name='activity_update'),
    path('activities/<int:pk>/complete/', views.mark_activity_completed, name='activity_complete'),
    
    # Item management
    path('<int:quotation_pk>/items/create/', views.QuotationItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', views.QuotationItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.QuotationItemDeleteView.as_view(), name='item_delete'),
    
    # AJAX endpoints for items
    path('api/service-info/', views.get_service_info, name='service_info'),
    path('<int:quotation_pk>/items/add-quick/', views.add_item_quick, name='item_add_quick'),
] 