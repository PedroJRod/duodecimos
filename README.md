# Sistema de Cálculo de Duodécimos

Este sistema foi desenvolvido para calcular automaticamente os repasses mensais (duodécimos) dos poderes com base nas receitas previstas de uma planilha de 'Receita Mensal'.

## Funcionalidades

- Importação de planilha de receitas
- Cálculo automático dos duodécimos mensais
- Visualização em gráficos
- Geração de relatórios em PDF e Excel
- Filtros por período (mensal, bimestral, trimestral, semestral e anual)

## Requisitos

- Python 3.8 ou superior
- Django 5.0 ou superior
- Outras dependências listadas em requirements.txt

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd duodecimo
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute as migrações do banco de dados:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Crie um superusuário:
```bash
python manage.py createsuperuser
```

6. Inicie o servidor de desenvolvimento:
```bash
python manage.py runserver
```

## Configuração Inicial

1. Acesse o painel administrativo em `http://localhost:8000/admin/`
2. Faça login com as credenciais do superusuário
3. Adicione os Poderes com seus respectivos percentuais:
   - Assembleia Legislativa (4,77%)
   - TCE (2,54%)
   - TJ (11,29%)
   - MP (4,98%)
   - DPE (1,47%)

## Uso

1. Acesse a aplicação em `http://localhost:8000`
2. Faça upload da planilha de receitas no formato especificado
3. Visualize os gráficos e relatórios gerados
4. Exporte os relatórios em PDF ou Excel conforme necessário

## Formato da Planilha

A planilha deve seguir o seguinte formato:

| ANO | COD FONTE | FONTE DE RECURSOS | JANEIRO | FEVEREIRO | ... | DEZEMBRO |
|-----|-----------|------------------|----------|-----------|-----|----------|
| 2024 | 15000 | Recursos não Vinculados de Impostos | valor | valor | ... | valor |
| 2024 | 15010 | Outros Recursos não Vinculados | valor | valor | ... | valor |

### Colunas Obrigatórias:
- **ANO**: Ano de referência dos valores
- **COD FONTE**: Código da fonte de recurso (15000 ou 15010)
- **FONTE DE RECURSOS**: Nome descritivo da fonte
- **JANEIRO** até **DEZEMBRO**: Valores mensais em formato numérico

**Observações:**
1. Os nomes das colunas devem estar exatamente como especificado (incluindo maiúsculas)
2. Os valores mensais devem ser numéricos (podem incluir decimais)
3. O sistema aceita arquivos nos formatos .xlsx e .xls

## Suporte

Para reportar problemas ou sugerir melhorias, por favor, abra uma issue no repositório. 