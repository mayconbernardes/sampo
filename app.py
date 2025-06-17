from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import re
import matplotlib
matplotlib.use('Agg')  # Backend não interativo para Matplotlib
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Pasta para salvar arquivos CSV
app.config['ALLOWED_EXTENSIONS'] = {'csv'}  # Apenas arquivos CSV

# Função para verificar extensão do arquivo
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Função para sanitizar dados do CSV
def sanitize_csv_data(df):
    for col in df.columns:
        if df[col].dtype == object:  # Verifica apenas colunas de strings
            df[col] = df[col].apply(lambda x: re.sub(r'^[=+-]', '', str(x)) if pd.notnull(x) else x)
    return df

# Rota principal
@app.route('/', methods=['GET', 'POST'])
def index():
    data = None
    filename = None
    plot_url = None
    
    if request.method == 'POST':
        # Verifica se um arquivo foi enviado
        if 'file' not in request.files:
            return render_template('index.html', error="Nenhum arquivo enviado.", data=None, filename=None)
        
        file = request.files['file']
        
        # Verifica se o arquivo tem nome
        if file.filename == '':
            return render_template('index.html', error="Nenhum arquivo selecionado.", data=None, filename=None)
        
        # Verifica se o arquivo é permitido
        if file and allowed_file(file.filename):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            try:
                # Ler o CSV
                df = pd.read_csv(filepath)
                
                # Sanitizar os dados
                df = sanitize_csv_data(df)
                
                # Converter dados para dicionário
                data = df.to_dict(orient='records')
                
                # Gerar gráfico para colunas numéricas
                fig, ax = plt.subplots(figsize=(8, 5))
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                if numeric_cols.empty:
                    return render_template('index.html', error="Nenhuma coluna numérica encontrada no CSV.", data=data, filename=file.filename)
                
                for column in numeric_cols:
                    ax.plot(df[column], label=column)
                ax.set_title(f"Gráfico dos Dados do CSV: {file.filename}")
                ax.set_xlabel("Índice")
                ax.set_ylabel("Valores")
                ax.legend()
                
                # Salvar gráfico como imagem em memória
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')
                plt.close(fig)  # Fechar figura para liberar memória
                
                return render_template('index.html', data=data, filename=file.filename, plot_url=plot_url)
            
            except Exception as e:
                return render_template('index.html', error=f"Erro ao processar o CSV: {str(e)}", data=None, filename=None)
        
        else:
            return render_template('index.html', error="Tipo de arquivo inválido. Apenas CSV é permitido.", data=None, filename=None)
    
    return render_template('index.html', data=None, filename=None)

if __name__ == '__main__':
    # Criar pasta de uploads se não existir
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True)