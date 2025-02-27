from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from .models import RevenueSource, MonthlyRevenue, PowerEntity, MonthlyAllowance, MONTH_CHOICES
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
        
        if period == 'monthly':
            for month in range(1, 13):
                month_allowances = allowances.filter(month=month)
                data['labels'].append(dict(MONTH_CHOICES)[month])
                
                for power in powers:
                    power_allowance = month_allowances.filter(power=power).first()
                    if power_allowance:
                        if not any(d['label'] == power.name for d in data['datasets']):
                            data['datasets'].append({
                                'label': power.name,
                                'data': []
                            })
                        for dataset in data['datasets']:
                            if dataset['label'] == power.name:
                                dataset['data'].append(float(power_allowance.calculated_value))
                    else:
                        # Adicionar 0 se não houver valor
                        for dataset in data['datasets']:
                            if dataset['label'] == power.name:
                                dataset['data'].append(0)
        
        elif period == 'bimonthly':
            for i in range(0, 12, 2):
                months = range(i + 1, i + 3)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[1]]}"
                data['labels'].append(label)
                
                for power in powers:
                    power_allowances = allowances.filter(month__in=months, power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(total)
        
        elif period == 'quarterly':
            for i in range(0, 12, 3):
                months = range(i + 1, i + 4)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                data['labels'].append(label)
                
                for power in powers:
                    power_allowances = allowances.filter(month__in=months, power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(total)
        
        elif period == 'semiannual':
            for i in range(0, 12, 6):
                months = range(i + 1, i + 7)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                data['labels'].append(label)
                
                for power in powers:
                    power_allowances = allowances.filter(month__in=months, power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                    
                    if not any(d['label'] == power.name for d in data['datasets']):
                        data['datasets'].append({
                            'label': power.name,
                            'data': []
                        })
                    for dataset in data['datasets']:
                        if dataset['label'] == power.name:
                            dataset['data'].append(total)
        
        elif period == 'annual':
            data['labels'].append(str(year))
            for power in powers:
                power_allowances = allowances.filter(power=power)
                total = sum(float(a.calculated_value) for a in power_allowances)
                
                data['datasets'].append({
                    'label': power.name,
                    'data': [total]
                })
        
        context['chart_data'] = json.dumps(data)
        context['powers'] = powers
        context['selected_year'] = year
        context['selected_period'] = period
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

def generate_report(request):
    year = int(request.GET.get('year', datetime.now().year))
    period = request.GET.get('period', 'monthly')
    format_type = request.GET.get('format', 'pdf')
    
    allowances = MonthlyAllowance.objects.filter(year=year)
    powers = PowerEntity.objects.all()
    
    if format_type == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="duodecimos_{year}_{period}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        
        data = [['Período'] + [power.name for power in powers]]
        
        if period == 'monthly':
            for month_num, month_name in MONTH_CHOICES:
                row = [month_name]
                for power in powers:
                    allowance = allowances.filter(month=month_num, power=power).first()
                    row.append(f'R$ {allowance.calculated_value:,.2f}' if allowance else 'R$ 0,00')
                data.append(row)
        
        elif period == 'bimonthly':
            for i in range(0, 12, 2):
                months = range(i + 1, i + 3)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[1]]}"
                row = [label]
                for power in powers:
                    power_allowances = allowances.filter(month__in=months, power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                    row.append(f'R$ {total:,.2f}')
                data.append(row)
        
        elif period == 'quarterly':
            for i in range(0, 12, 3):
                months = range(i + 1, i + 4)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                row = [label]
                for power in powers:
                    power_allowances = allowances.filter(month__in=months, power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                    row.append(f'R$ {total:,.2f}')
                data.append(row)
        
        elif period == 'semiannual':
            for i in range(0, 12, 6):
                months = range(i + 1, i + 7)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                row = [label]
                for power in powers:
                    power_allowances = allowances.filter(month__in=months, power=power)
                    total = sum(float(a.calculated_value) for a in power_allowances)
                    row.append(f'R$ {total:,.2f}')
                data.append(row)
        
        elif period == 'annual':
            row = [str(year)]
            for power in powers:
                power_allowances = allowances.filter(power=power)
                total = sum(float(a.calculated_value) for a in power_allowances)
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
        response['Content-Disposition'] = f'attachment; filename="duodecimos_{year}_{period}.xlsx"'
        
        df = pd.DataFrame(columns=['Período'] + [power.name for power in powers])
        
        if period == 'monthly':
            for month_num, month_name in MONTH_CHOICES:
                row = {'Período': month_name}
                for power in powers:
                    allowance = allowances.filter(month=month_num, power=power).first()
                    row[power.name] = float(allowance.calculated_value) if allowance else 0
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        elif period == 'bimonthly':
            for i in range(0, 12, 2):
                months = range(i + 1, i + 3)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[1]]}"
                row = {'Período': label}
                for power in powers:
                    power_allowances = allowances.filter(month__in=months, power=power)
                    row[power.name] = sum(float(a.calculated_value) for a in power_allowances)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        elif period == 'quarterly':
            for i in range(0, 12, 3):
                months = range(i + 1, i + 4)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                row = {'Período': label}
                for power in powers:
                    power_allowances = allowances.filter(month__in=months, power=power)
                    row[power.name] = sum(float(a.calculated_value) for a in power_allowances)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        elif period == 'semiannual':
            for i in range(0, 12, 6):
                months = range(i + 1, i + 7)
                label = f"{dict(MONTH_CHOICES)[months[0]]}-{dict(MONTH_CHOICES)[months[-1]]}"
                row = {'Período': label}
                for power in powers:
                    power_allowances = allowances.filter(month__in=months, power=power)
                    row[power.name] = sum(float(a.calculated_value) for a in power_allowances)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        elif period == 'annual':
            row = {'Período': str(year)}
            for power in powers:
                power_allowances = allowances.filter(power=power)
                row[power.name] = sum(float(a.calculated_value) for a in power_allowances)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        
        df.to_excel(response, index=False)
        return response
    
    return JsonResponse({'status': 'error', 'message': 'Invalid format type'})
