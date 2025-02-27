from django.contrib import admin
from .models import RevenueSource, MonthlyRevenue, PowerEntity, MonthlyAllowance

@admin.register(RevenueSource)
class RevenueSourceAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(MonthlyRevenue)
class MonthlyRevenueAdmin(admin.ModelAdmin):
    list_display = ('source', 'year', 'month', 'value')
    list_filter = ('source', 'year', 'month')
    search_fields = ('source__code', 'source__name')

@admin.register(PowerEntity)
class PowerEntityAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage')
    search_fields = ('name',)

@admin.register(MonthlyAllowance)
class MonthlyAllowanceAdmin(admin.ModelAdmin):
    list_display = ('power', 'year', 'month', 'base_value', 'calculated_value')
    list_filter = ('power', 'year', 'month')
    search_fields = ('power__name',)
