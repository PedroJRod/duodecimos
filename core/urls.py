from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('upload-excel/', views.upload_excel, name='upload_excel'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('expenses/', views.ExpenseDashboardView.as_view(), name='expense_dashboard'),
    path('upload-expenses/', views.upload_expenses, name='upload_expenses'),
    path('generate-expense-report/', views.generate_report, {'type': 'expense'}, name='generate_expense_report'),
    path('cronograma/', views.CronogramaView.as_view(), name='cronograma'),
    path('upload-cronograma/', views.upload_cronograma, name='upload_cronograma'),
] 