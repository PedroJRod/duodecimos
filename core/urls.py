from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('upload-excel/', views.upload_excel, name='upload_excel'),
    path('generate-report/', views.generate_report, name='generate_report'),
] 