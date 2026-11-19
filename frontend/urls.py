from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_page, name='login-page'),
    path('register/', views.register_page, name='register-page'),
    path('queries/', views.queries_page, name='queries-page'),
    path('queries/new/', views.query_new_page, name='query-new-page'),
    path('queries/<int:pk>/', views.query_detail_page, name='query-detail-page'),
    path('queries/<int:pk>/edit/', views.query_edit_page, name='query-edit-page'),
]
