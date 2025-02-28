from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from .models import RevenueSource, MonthlyRevenue, PowerEntity, MonthlyAllowance, MONTH_CHOICES, ExpenseCategory, MonthlyExpense, Cronograma
import pandas as pd
from decimal import Decimal
from django.db.models import Sum
from datetime import datetime
import json
from django.core.files.storage import FileSystemStorage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.db import models
from django.views.decorators.http import require_http_methods

class DashboardView(TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get('year', datetime.now().year))
        period = self.request.GET.get('period', 'monthly')
        
        allowances = MonthlyAllowance.objects.filter(year=year)
        powers = PowerEntity.objects.all()
        
        data = {
            'labels': [],
            'datasets': []
        }
        
        table_data = []
        totals_by_power = [0] * len(powers)  # Totais por poder (coluna)
        
        if period == 'monthly':
            for month in range(1, 13):
                month_allowances = allowances.filter(month=month)
                month_name = dict(MONTH_CHOICES)[month]
                data['labels'].append(month_name)
                
                values = []
                period_total = 0  # Total do período (linha)
                for i, power in enumerate(powers):
                    power_allowance = month_allowances.filter(power=power).first()
                    value = float(power_allowance.calculated_value) if power_allowance else 0
                    values.append(value)
                    totals_by_power[i] += value
                    period_total += value
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(value)
                
                table_data.append((month_name, values, period_total))
        
        elif period == 'bimonthly':
            for i in range(0, 12, 2):
                months = range(i + 1, i + 3)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[1]]}"
                data['labels'].append(label)
                
                values = []
                period_total = 0  # Total do período (linha)
                for i, power in enumerate(powers):
                    power_allowances = allowances.filter(month__in=months, power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                    values.append(total)
                    totals_by_power[i] += total
                    period_total += total
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(total)
                
                table_data.append((label, values, period_total))
        
        elif period == 'quarterly':
            for i in range(0, 12, 3):
                months = range(i + 1, i + 4)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                data['labels'].append(label)
                
                values = []
                period_total = 0  # Total do período (linha)
                for i, power in enumerate(powers):
                    power_allowances = allowances.filter(month__in=months, power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                    values.append(total)
                    totals_by_power[i] += total
                    period_total += total
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(total)
                
                table_data.append((label, values, period_total))
        
        elif period == 'semiannual':
            for i in range(0, 12, 6):
                months = range(i + 1, i + 7)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                data['labels'].append(label)
                
                values = []
                period_total = 0  # Total do período (linha)
                for i, power in enumerate(powers):
                    power_allowances = allowances.filter(month__in=months, power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                    values.append(total)
                    totals_by_power[i] += total
                    period_total += total
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(total)
                
                table_data.append((label, values, period_total))
        
        elif period == 'annual':
            label = str(year)
            data['labels'].append(label)
            
            values = []
            period_total = 0  # Total do período (linha)
            for i, power in enumerate(powers):
                power_allowances = allowances.filter(power=power)
                total = sum(float(a.calculated_value) for a in power_allowances)
                values.append(total)
                totals_by_power[i] = total
                period_total += total
                data['datasets'].append({
                    'label': power.name,
                    'data': [total]
                })
            
            table_data.append((label, values, period_total))
        
        # Calcula o total geral (soma de todos os valores)
        total_geral = sum(totals_by_power)
        
        context['chart_data'] = json.dumps(data)
        context['powers'] = powers
        context['selected_year'] = year
        context['selected_period'] = period
        context['table_data'] = table_data
        context['totals_by_power'] = totals_by_power
        context['total_geral'] = total_geral
        return context

def upload_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        fs = FileSystemStorage()
        filename = fs.save(excel_file.name, excel_file)
        
        try:
            df = pd.read_excel(fs.path(filename))
            
            if 'ANO' not in df.columns:
                return JsonResponse({
                    'status': 'error',
                    'message': 'A coluna ANO é obrigatória na planilha.'
                })
            
            for _, row in df.iterrows():
                source, _ = RevenueSource.objects.get_or_create(
                    code=str(row['COD FONTE']),
                    name=row['FONTE DE RECURSOS']
                )
                
                year = int(row['ANO'])
                for month_num, month_name in MONTH_CHOICES:
                    month_value = row.get(month_name.upper(), 0)
                    MonthlyRevenue.objects.update_or_create(
                        source=source,
                        year=year,
                        month=month_num,
                        defaults={'value': Decimal(str(month_value))}
                    )
            
            calculate_allowances(year)
            fs.delete(filename)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erro ao processar o arquivo: {str(e)}'
            })
    return JsonResponse({'status': 'error', 'message': 'Nenhum arquivo enviado'})

def calculate_allowances(year=None):
    sources = ['15000', '15010']
    if year is None:
        year = datetime.now().year
    powers = PowerEntity.objects.all()
    
    for month in range(1, 13):
        base_value = MonthlyRevenue.objects.filter(
            source__code__in=sources,
            year=year,
            month=month
        ).aggregate(total=Sum('value'))['total'] or 0
        
        for power in powers:
            MonthlyAllowance.objects.update_or_create(
                power=power,
                year=year,
                month=month,
                defaults={
                    'base_value': base_value,
                    'calculated_value': base_value * (power.percentage / 100)
                }
            )

def generate_report(request, type='revenue'):
    year = int(request.GET.get('year', datetime.now().year))
    period = request.GET.get('period', 'monthly')
    format_type = request.GET.get('format', 'pdf')
    
    if type == 'revenue':
        allowances = MonthlyAllowance.objects.filter(year=year)
        title = 'Previsão dos Duodécimos'
    else:
        allowances = MonthlyExpense.objects.filter(year=year)
        title = 'Cronograma de Desembolso'
    
    powers = PowerEntity.objects.all()
    
    if format_type == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{type}_{year}_{period}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        
        data = [['Período'] + [power.name for power in powers]]
        
        if period == 'monthly':
            for month_num, month_name in MONTH_CHOICES:
                row = [month_name]
                for power in powers:
                    if type == 'revenue':
                        allowance = allowances.filter(month=month_num, power=power).first()
                        value = float(allowance.calculated_value) if allowance else 0
                    else:
                        power_expenses = allowances.filter(month=month_num, power=power)
                        value = sum(float(e.value) for e in power_expenses)
                    row.append(f'R$ {value:,.2f}')
                data.append(row)
        
        elif period == 'bimonthly':
            for i in range(0, 12, 2):
                months = range(i + 1, i + 3)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[1]]}"
                row = [label]
                for power in powers:
                    if type == 'revenue':
                        power_allowances = allowances.filter(month__in=months, power=power)
                        total = sum(float(a.calculated_value) for a in power_allowances)
                    else:
                        power_expenses = allowances.filter(month__in=months, power=power)
                        total = sum(float(e.value) for e in power_expenses)
                    row.append(f'R$ {total:,.2f}')
                data.append(row)
        
        elif period == 'quarterly':
            for i in range(0, 12, 3):
                months = range(i + 1, i + 4)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                row = [label]
                for power in powers:
                    if type == 'revenue':
                        power_allowances = allowances.filter(month__in=months, power=power)
                        total = sum(float(a.calculated_value) for a in power_allowances)
                    else:
                        power_expenses = allowances.filter(month__in=months, power=power)
                        total = sum(float(e.value) for e in power_expenses)
                    row.append(f'R$ {total:,.2f}')
                data.append(row)
        
        elif period == 'semiannual':
            for i in range(0, 12, 6):
                months = range(i + 1, i + 7)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                row = [label]
                for power in powers:
                    if type == 'revenue':
                        power_allowances = allowances.filter(month__in=months, power=power)
                        total = sum(float(a.calculated_value) for a in power_allowances)
                    else:
                        power_expenses = allowances.filter(month__in=months, power=power)
                        total = sum(float(e.value) for e in power_expenses)
                    row.append(f'R$ {total:,.2f}')
                data.append(row)
        
        elif period == 'annual':
            row = [str(year)]
            for power in powers:
                if type == 'revenue':
                    power_allowances = allowances.filter(power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                else:
                    power_expenses = allowances.filter(power=power)
                    total = sum(float(e.value) for e in power_expenses)
                row.append(f'R$ {total:,.2f}')
            data.append(row)
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        return response
    
    elif format_type == 'excel':
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{type}_{year}_{period}.xlsx"'
        
        df = pd.DataFrame(columns=['Período'] + [power.name for power in powers])
        
        if period == 'monthly':
            for month_num, month_name in MONTH_CHOICES:
                row = {'Período': month_name}
                for power in powers:
                    if type == 'revenue':
                        allowance = allowances.filter(month=month_num, power=power).first()
                        row[power.name] = float(allowance.calculated_value) if allowance else 0
                    else:
                        power_expenses = allowances.filter(month=month_num, power=power)
                        row[power.name] = sum(float(e.value) for e in power_expenses)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        elif period == 'bimonthly':
            for i in range(0, 12, 2):
                months = range(i + 1, i + 3)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[1]]}"
                row = {'Período': label}
                for power in powers:
                    if type == 'revenue':
                        power_allowances = allowances.filter(month__in=months, power=power)
                        row[power.name] = sum(float(a.calculated_value) for a in power_allowances)
                    else:
                        power_expenses = allowances.filter(month__in=months, power=power)
                        row[power.name] = sum(float(e.value) for e in power_expenses)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        elif period == 'quarterly':
            for i in range(0, 12, 3):
                months = range(i + 1, i + 4)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                row = {'Período': label}
                for power in powers:
                    if type == 'revenue':
                        power_allowances = allowances.filter(month__in=months, power=power)
                        row[power.name] = sum(float(a.calculated_value) for a in power_allowances)
                    else:
                        power_expenses = allowances.filter(month__in=months, power=power)
                        row[power.name] = sum(float(e.value) for e in power_expenses)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        elif period == 'semiannual':
            for i in range(0, 12, 6):
                months = range(i + 1, i + 7)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                row = {'Período': label}
                for power in powers:
                    if type == 'revenue':
                        power_allowances = allowances.filter(month__in=months, power=power)
                        row[power.name] = sum(float(a.calculated_value) for a in power_allowances)
                    else:
                        power_expenses = allowances.filter(month__in=months, power=power)
                        row[power.name] = sum(float(e.value) for e in power_expenses)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        elif period == 'annual':
            row = {'Período': str(year)}
            for power in powers:
                if type == 'revenue':
                    power_allowances = allowances.filter(power=power)
                    row[power.name] = sum(float(a.calculated_value) for a in power_allowances)
                else:
                    power_expenses = allowances.filter(power=power)
                    row[power.name] = sum(float(e.value) for e in power_expenses)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        df.to_excel(response, index=False)
        return response
    
    return JsonResponse({'status': 'error', 'message': 'Invalid format type'})

def upload_expenses(request):
    if request.method == 'POST' and request.FILES.get('expense_file'):
        expense_file = request.FILES['expense_file']
        fs = FileSystemStorage()
        filename = fs.save(expense_file.name, expense_file)
        
        try:
            df = pd.read_excel(fs.path(filename))
            
            if 'ANO' not in df.columns:
                return JsonResponse({
                    'status': 'error',
                    'message': 'A coluna ANO é obrigatória na planilha.'
                })
            
            for _, row in df.iterrows():
                category, _ = ExpenseCategory.objects.get_or_create(
                    code=str(row['COD DESPESA']),
                    name=row['CATEGORIA']
                )
                
                power = PowerEntity.objects.get(name=row['PODER'])
                year = int(row['ANO'])
                
                for month_num, month_name in MONTH_CHOICES:
                    month_value = row.get(month_name.upper(), 0)
                    MonthlyExpense.objects.update_or_create(
                        category=category,
                        power=power,
                        year=year,
                        month=month_num,
                        defaults={'value': Decimal(str(month_value))}
                    )
            
            fs.delete(filename)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erro ao processar o arquivo: {str(e)}'
            })
    return JsonResponse({'status': 'error', 'message': 'Nenhum arquivo enviado'})

class ExpenseDashboardView(TemplateView):
    template_name = 'core/expense_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(self.request.GET.get('year', datetime.now().year))
        period = self.request.GET.get('period', 'monthly')
        
        expenses = MonthlyExpense.objects.filter(year=year)
        powers = PowerEntity.objects.all()
        categories = ExpenseCategory.objects.all()
        
        data = {
            'labels': [],
            'datasets': []
        }
        
        table_data = []
        totals_by_power = [0] * len(powers)
        
        if period == 'monthly':
            for month in range(1, 13):
                month_expenses = expenses.filter(month=month)
                month_name = dict(MONTH_CHOICES)[month]
                data['labels'].append(month_name)
                
                values = []
                period_total = 0
                for i, power in enumerate(powers):
                    power_expenses = month_expenses.filter(power=power)
                    value = sum(float(e.value) for e in power_expenses)
                    values.append(value)
                    totals_by_power[i] += value
                    period_total += value
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(value)
                
                table_data.append((month_name, values, period_total))
        
        elif period == 'bimonthly':
            for i in range(0, 12, 2):
                months = range(i + 1, i + 3)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[1]]}"
                data['labels'].append(label)
                
                values = []
                period_total = 0
                for i, power in enumerate(powers):
                    power_expenses = expenses.filter(month__in=months, power=power)
                    total = sum(float(e.value) for e in power_expenses)
                    values.append(total)
                    totals_by_power[i] += total
                    period_total += total
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(total)
                
                table_data.append((label, values, period_total))
        
        elif period == 'quarterly':
            for i in range(0, 12, 3):
                months = range(i + 1, i + 4)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                data['labels'].append(label)
                
                values = []
                period_total = 0
                for i, power in enumerate(powers):
                    power_expenses = expenses.filter(month__in=months, power=power)
                    total = sum(float(e.value) for e in power_expenses)
                    values.append(total)
                    totals_by_power[i] += total
                    period_total += total
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(total)
                
                table_data.append((label, values, period_total))
        
        elif period == 'semiannual':
            for i in range(0, 12, 6):
                months = range(i + 1, i + 7)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                data['labels'].append(label)
                
                values = []
                period_total = 0
                for i, power in enumerate(powers):
                    power_expenses = expenses.filter(month__in=months, power=power)
                    total = sum(float(e.value) for e in power_expenses)
                    values.append(total)
                    totals_by_power[i] += total
                    period_total += total
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(total)
                
                table_data.append((label, values, period_total))
        
        elif period == 'annual':
            label = str(year)
            data['labels'].append(label)
            
            values = []
            period_total = 0
            for i, power in enumerate(powers):
                power_expenses = expenses.filter(power=power)
                total = sum(float(e.value) for e in power_expenses)
                values.append(total)
                totals_by_power[i] = total
                period_total += total
                data['datasets'].append({
                    'label': power.name,
                    'data': [total]
                })
            
            table_data.append((label, values, period_total))
        
        # Calcula o total geral
        total_geral = sum(totals_by_power)
        
        context['chart_data'] = json.dumps(data)
        context['powers'] = powers
        context['selected_year'] = year
        context['selected_period'] = period
        context['table_data'] = table_data
        context['totals_by_power'] = totals_by_power
        context['total_geral'] = total_geral
        return context

def update_cronograma_from_excel(file_path):
    try:
        # Lê o arquivo Excel do caminho especificado
        df = pd.read_excel(file_path)
        
        # Verifica se todas as colunas necessárias existem
        required_columns = ['UG', 'Nome Unidade', 'Ano', 'FONTE DE RECURSO', 'VALOR DESPESA']
        month_columns = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 
                        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        
        # Verifica colunas obrigatórias
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Colunas obrigatórias ausentes na planilha: {', '.join(missing_columns)}"
        
        # Normaliza os nomes das colunas dos meses (remove acentos)
        df.columns = [col.lower().replace('marco', 'março') for col in df.columns]
        
        # Remove linhas onde UG é nulo
        df = df.dropna(subset=['ug'])
        
        # Converte UG para inteiro, tratando possíveis erros
        try:
            df['ug'] = df['ug'].fillna(0).astype(int)
        except Exception as e:
            return False, "Erro ao converter UG para número inteiro. Verifique se todos os valores são numéricos."
        
        # Garante que todas as colunas de meses existam
        for month in month_columns:
            if month not in df.columns:
                df[month] = 0
        
        # Converte valores numéricos, substituindo NaN por 0
        numeric_columns = ['valor_despesa'] + month_columns + ['total']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calcula o total se não existir
        if 'total' not in df.columns:
            df['total'] = df[month_columns].sum(axis=1)
        
        # Garante que a coluna Ano existe e tem valores válidos
        if 'ano' not in df.columns or df['ano'].isnull().any():
            df['ano'] = 2025  # Valor padrão se não existir
        else:
            df['ano'] = df['ano'].fillna(2025).astype(int)
        
        # Limpa os dados existentes
        Cronograma.objects.all().delete()
        
        # Itera sobre as linhas do DataFrame e cria registros
        for _, row in df.iterrows():
            try:
                Cronograma.objects.create(
                    ug=int(row['ug']),
                    nome_unidade=str(row['nome unidade']).strip(),
                    ano=int(row['ano']),
                    fonte_recurso=str(row.get('fonte de recurso', '')).strip(),
                    valor_despesa=float(row.get('valor_despesa', 0)),
                    janeiro=float(row['janeiro']),
                    fevereiro=float(row['fevereiro']),
                    marco=float(row['março']),
                    abril=float(row['abril']),
                    maio=float(row['maio']),
                    junho=float(row['junho']),
                    julho=float(row['julho']),
                    agosto=float(row['agosto']),
                    setembro=float(row['setembro']),
                    outubro=float(row['outubro']),
                    novembro=float(row['novembro']),
                    dezembro=float(row['dezembro']),
                    total=float(row['total'])
                )
            except Exception as e:
                print(f"Erro ao processar linha {_}: {str(e)}")
                continue
        
        return True, "Cronograma atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar cronograma: {str(e)}"

@require_http_methods(["POST"])
def upload_cronograma(request):
    try:
        if 'excel_file' not in request.FILES:
            return JsonResponse({'error': 'Nenhum arquivo foi enviado.'}, status=400)
        
        excel_file = request.FILES['excel_file']
        fs = FileSystemStorage()
        filename = fs.save('cronograma.xlsx', excel_file)
        file_path = fs.path(filename)
        
        # Atualiza o banco de dados com os dados do arquivo
        success, message = update_cronograma_from_excel(file_path)
        
        # Remove o arquivo temporário
        fs.delete(filename)
        
        if success:
            return JsonResponse({'message': message})
        else:
            return JsonResponse({'error': message}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class CronogramaView(TemplateView):
    template_name = 'core/cronograma.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtém os parâmetros da URL
            selected_year = int(self.request.GET.get('year', None))
            period = self.request.GET.get('period', 'monthly')
            
            # Obtém os anos disponíveis do banco de dados
            available_years = sorted(Cronograma.objects.values_list('ano', flat=True).distinct())
            
            # Se não foi selecionado um ano, usa o primeiro disponível
            if selected_year is None or selected_year not in available_years:
                selected_year = available_years[0] if available_years else datetime.now().year
            
            # Filtra os dados pelo ano selecionado
            queryset = Cronograma.objects.filter(ano=selected_year)
            
            # Lista de meses
            all_months = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            month_columns = [m.lower() for m in all_months]
            
            # Agrupa os dados por UG e soma os valores
            data = []
            for ug in queryset.values('ug', 'nome_unidade').distinct():
                ug_data = queryset.filter(ug=ug['ug']).aggregate(
                    janeiro=models.Sum('janeiro'),
                    fevereiro=models.Sum('fevereiro'),
                    marco=models.Sum('marco'),
                    abril=models.Sum('abril'),
                    maio=models.Sum('maio'),
                    junho=models.Sum('junho'),
                    julho=models.Sum('julho'),
                    agosto=models.Sum('agosto'),
                    setembro=models.Sum('setembro'),
                    outubro=models.Sum('outubro'),
                    novembro=models.Sum('novembro'),
                    dezembro=models.Sum('dezembro'),
                    total=models.Sum('total')
                )
                
                # Prepara os valores baseado no período selecionado
                if period == 'monthly':
                    months = all_months
                    values = [
                        ug_data['janeiro'], ug_data['fevereiro'], ug_data['marco'],
                        ug_data['abril'], ug_data['maio'], ug_data['junho'],
                        ug_data['julho'], ug_data['agosto'], ug_data['setembro'],
                        ug_data['outubro'], ug_data['novembro'], ug_data['dezembro']
                    ]
                elif period == 'bimonthly':
                    months = ['Jan-Fev', 'Mar-Abr', 'Mai-Jun', 'Jul-Ago', 'Set-Out', 'Nov-Dez']
                    values = [
                        ug_data['janeiro'] + ug_data['fevereiro'],
                        ug_data['marco'] + ug_data['abril'],
                        ug_data['maio'] + ug_data['junho'],
                        ug_data['julho'] + ug_data['agosto'],
                        ug_data['setembro'] + ug_data['outubro'],
                        ug_data['novembro'] + ug_data['dezembro']
                    ]
                elif period == 'quarterly':
                    months = ['Jan-Mar', 'Abr-Jun', 'Jul-Set', 'Out-Dez']
                    values = [
                        ug_data['janeiro'] + ug_data['fevereiro'] + ug_data['marco'],
                        ug_data['abril'] + ug_data['maio'] + ug_data['junho'],
                        ug_data['julho'] + ug_data['agosto'] + ug_data['setembro'],
                        ug_data['outubro'] + ug_data['novembro'] + ug_data['dezembro']
                    ]
                else:  # annual
                    months = ['Total Anual']
                    values = [ug_data['total']]
                
                # Formata os valores em Reais
                formatted_values = [
                    f'R$ {float(value):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
                    for value in values
                ]
                
                data.append({
                    'ug': f"{ug['ug']:04d}",  # Formata UG com zeros à esquerda
                    'nome': ug['nome_unidade'],
                    'ano': selected_year,
                    'valores': formatted_values,
                    'total': f'R$ {float(ug_data["total"]):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
                })
            
            # Ordena os dados por UG
            data.sort(key=lambda x: int(x['ug']))
            
            context.update({
                'data': data,
                'months': months,
                'year': selected_year,
                'selected_period': period,
                'available_periods': [
                    ('monthly', 'Mensal'),
                    ('bimonthly', 'Bimestral'),
                    ('quarterly', 'Quadrimestral'),
                    ('annual', 'Anual')
                ],
                'available_years': available_years
            })
            
        except Exception as e:
            context['error'] = str(e)
        
        return context
