import os
import django
import pandas as pd
from decimal import Decimal

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'duodecimos.settings')
django.setup()

from core.models import Cronograma

def update_database():
    try:
        # Ler o arquivo
        print('Lendo arquivo...')
        df = pd.read_excel('cronograma.xlsx')
        
        # Normalizar nomes das colunas
        df.columns = [col.lower() for col in df.columns]
        
        # Limpar dados existentes
        print('Limpando banco de dados...')
        Cronograma.objects.all().delete()
        
        # Inserir novos dados
        print('Inserindo novos dados...')
        for _, row in df.iterrows():
            Cronograma.objects.create(
                ug=int(row['ug']),
                nome_unidade=str(row['nome unidade']),
                ano=int(row['ano']),
                fonte_recurso=str(row['fonte de recurso']),
                valor_despesa=float(row['valor despesa']),
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
        
        total_registros = Cronograma.objects.count()
        print(f'Atualização concluída com sucesso! Total de registros criados: {total_registros}')
        return True
    except Exception as e:
        print(f'Erro durante a atualização: {str(e)}')
        return False

if __name__ == '__main__':
    update_database() 