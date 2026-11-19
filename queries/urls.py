from django.urls import path

from . import views

urlpatterns = [
    path('queries/', views.QueryListCreateView.as_view(), name='query-list'),
    path('queries/<int:pk>/', views.QueryDetailView.as_view(), name='query-detail'),
    path('queries/<int:pk>/status/', views.QueryStatusUpdateView.as_view(), name='query-status'),
    path('queries/<int:pk>/analyze/', views.QueryAnalyzeView.as_view(), name='query-analyze'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]
