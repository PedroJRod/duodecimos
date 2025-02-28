from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Common choices
MONTH_CHOICES = [
    (1, 'Janeiro'),
    (2, 'Fevereiro'),
    (3, 'Março'),
    (4, 'Abril'),
    (5, 'Maio'),
    (6, 'Junho'),
    (7, 'Julho'),
    (8, 'Agosto'),
    (9, 'Setembro'),
    (10, 'Outubro'),
    (11, 'Novembro'),
    (12, 'Dezembro'),
]

# Create your models here.

class RevenueSource(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class MonthlyRevenue(models.Model):
    source = models.ForeignKey(RevenueSource, on_delete=models.CASCADE)
    year = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    month = models.IntegerField(choices=MONTH_CHOICES)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        unique_together = ('source', 'year', 'month')
    
    def __str__(self):
        return f"{self.source.code} - {self.get_month_display()}/{self.year}: R$ {self.value:,.2f}"

class PowerEntity(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2,
                                   validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

class MonthlyAllowance(models.Model):
    power = models.ForeignKey(PowerEntity, on_delete=models.CASCADE)
    year = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    month = models.IntegerField(choices=MONTH_CHOICES)
    base_value = models.DecimalField(max_digits=15, decimal_places=2)
    calculated_value = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('power', 'year', 'month')
    
    def __str__(self):
        month_name = dict(MONTH_CHOICES)[self.month]
        return f"{self.power.name} - {month_name}/{self.year}: R$ {self.calculated_value:,.2f}"

    def calculate(self):
        self.calculated_value = self.base_value * (self.power.percentage / 100)
        return self.calculated_value

class ExpenseCategory(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = 'Categoria de Despesa'
        verbose_name_plural = 'Categorias de Despesas'
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class MonthlyExpense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    power = models.ForeignKey(PowerEntity, on_delete=models.CASCADE)
    year = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    month = models.IntegerField(choices=MONTH_CHOICES)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        unique_together = ('category', 'power', 'year', 'month')
        verbose_name = 'Despesa Mensal'
        verbose_name_plural = 'Despesas Mensais'
    
    def __str__(self):
        month_name = dict(MONTH_CHOICES)[self.month]
        return f"{self.power.name} - {self.category.name} - {month_name}/{self.year}: R$ {self.value:,.2f}"

class Cronograma(models.Model):
    ug = models.IntegerField()
    nome_unidade = models.CharField(max_length=200)
    ano = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    fonte_recurso = models.CharField(max_length=100)
    valor_despesa = models.DecimalField(max_digits=15, decimal_places=2)
    janeiro = models.DecimalField(max_digits=15, decimal_places=2)
    fevereiro = models.DecimalField(max_digits=15, decimal_places=2)
    marco = models.DecimalField(max_digits=15, decimal_places=2)
    abril = models.DecimalField(max_digits=15, decimal_places=2)
    maio = models.DecimalField(max_digits=15, decimal_places=2)
    junho = models.DecimalField(max_digits=15, decimal_places=2)
    julho = models.DecimalField(max_digits=15, decimal_places=2)
    agosto = models.DecimalField(max_digits=15, decimal_places=2)
    setembro = models.DecimalField(max_digits=15, decimal_places=2)
    outubro = models.DecimalField(max_digits=15, decimal_places=2)
    novembro = models.DecimalField(max_digits=15, decimal_places=2)
    dezembro = models.DecimalField(max_digits=15, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = ('ug', 'ano', 'fonte_recurso')
        verbose_name = 'Cronograma de Desembolso'
        verbose_name_plural = 'Cronogramas de Desembolso'

    def __str__(self):
        return f"UG {self.ug} - {self.nome_unidade} ({self.ano})"
