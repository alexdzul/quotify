from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.ServiceListView.as_view(), name='list'),
    path('create/', views.ServiceCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ServiceDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ServiceUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='delete'),
    
    # Gallery
    path('<int:pk>/gallery/', views.ServiceGalleryView.as_view(), name='gallery'),
    path('<int:service_pk>/gallery/add/', views.ServiceImageCreateView.as_view(), name='add_image'),
    path('<int:pk>/gallery/delete/<int:image_pk>/', views.delete_service_image, name='delete_image'),
    path('<int:pk>/gallery/move/<int:image_pk>/', views.move_service_image, name='move_image'),
    
    # Categories
    path('categories/', views.ServiceCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.ServiceCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.ServiceCategoryUpdateView.as_view(), name='category_update'),
] 