from flask import Flask, render_template, request, redirect, url_for, flash
from database import SistemaMonitoramentoColmeias
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')  # Use env var or default

# Initialize the backend system
sistema = SistemaMonitoramentoColmeias()

@app.route('/')
def index():
    # Define the timezone for São Paulo
    tz = pytz.timezone('America/Sao_Paulo')
    # Get the current date and time in São Paulo
    now = datetime.now(tz)
    # Format the datetime as desired (e.g., DD/MM/YYYY HH:MM)
    current_datetime = now.strftime('%d/%m/%Y %H:%M')
    return render_template('index.html', current_datetime=current_datetime)

@app.route('/registrar_colmeia_page')
def registrar_colmeia_page():
    return render_template('registrar_colmeia.html')

@app.route('/registrar_inspecao_page')
def registrar_inspecao_page():
    colmeias_list = sistema.listar_colmeias()
    return render_template('registrar_inspecao.html', colmeias=colmeias_list)

@app.route('/registrar_producao_page')
def registrar_producao_page():
    colmeias_list = sistema.listar_colmeias()
    return render_template('registrar_producao.html', colmeias=colmeias_list)

@app.route('/registrar_colmeia', methods=['POST'])
def registrar_colmeia():
    codigo = request.form['codigo']
    localizacao = request.form['localizacao']
    try:
        if sistema.registrar_colmeia(codigo, localizacao):
            flash('Colmeia registrada com sucesso!', 'success')
        else:
            flash('Erro ao registrar colmeia. Código já existe.', 'error')
    except Exception as e:
        flash(f'Erro ao registrar colmeia: {e}', 'error')
    return redirect(url_for('registrar_colmeia_page'))

@app.route('/registrar_inspecao', methods=['POST'])
def registrar_inspecao():
    colmeia_id = request.form['colmeia_id']
    temperatura = request.form['temperatura']
    umidade = request.form['umidade']
    presenca_pragas = request.form.get('presenca_pragas') == 'on'
    estado_geral = request.form['estado_geral']
    observacoes = request.form['observacoes']
    try:
        if sistema.registrar_inspecao(colmeia_id, temperatura, umidade, presenca_pragas, estado_geral, observacoes):
            flash('Inspeção registrada com sucesso!', 'success')
        else:
            flash('Erro ao registrar inspeção.', 'error')
    except Exception as e:
        flash(f'Erro ao registrar inspeção: {e}', 'error')
    return redirect(url_for('registrar_inspecao_page'))

@app.route('/registrar_producao', methods=['POST'])
def registrar_producao():
    colmeia_id = request.form['colmeia_id']
    quantidade_mel = request.form['quantidade_mel']
    qualidade = request.form['qualidade']
    try:
        if sistema.registrar_producao(colmeia_id, quantidade_mel, qualidade):
            flash('Produção registrada com sucesso!', 'success')
        else:
            flash('Erro ao registrar produção. Verifique se a Colmeia selecionada está correta.', 'error')
    except Exception as e:
        flash(f'Erro ao registrar produção: {e}', 'error')
    return redirect(url_for('registrar_producao_page'))

@app.route('/verificar_alertas')
def verificar_alertas():
    alertas = sistema.verificar_alertas()
    if not alertas:
        alertas = None  # Ensure alertas is None if no alerts are found
    return render_template('alertas.html', alertas=alertas)

# 🆕 New Route: Relatórios Page
@app.route('/relatorios', methods=['GET', 'POST'])
def relatorios():
    if request.method == 'POST':
        colmeia_id = request.form.get('colmeia_id')
        if not colmeia_id:
            flash('Nenhuma Colmeia selecionada.', 'error')
            return redirect(url_for('relatorios'))
        
        # Fetch Colmeia details
        colmeia = sistema.get_colmeia_by_id(colmeia_id)
        if not colmeia:
            flash('Colmeia não encontrada.', 'error')
            return redirect(url_for('relatorios'))
        
        # Fetch related Inspections and Productions
        inspecoes = sistema.get_inspecoes_by_colmeia_id(colmeia_id)
        producoes = sistema.get_producoes_by_colmeia_id(colmeia_id)
        
        return render_template('relatorios.html', colmeia=colmeia, inspecoes=inspecoes, producoes=producoes)
    
    else:
        # GET request: Render the dropdown with all Colmeias
        colmeias_list = sistema.listar_colmeias()
        return render_template('relatorios.html', colmeias=colmeias_list)

# 🆕 New Route: Delete Colmeia
@app.route('/delete_colmeia/<int:colmeia_id>', methods=['POST'])
def delete_colmeia(colmeia_id):
    try:
        success = sistema.deletar_colmeia(colmeia_id)
        if success:
            flash('Colmeia e seus dados foram deletados com sucesso.', 'success')
        else:
            flash('Erro ao deletar a Colmeia.', 'error')
    except Exception as e:
        flash(f'Erro ao deletar a Colmeia: {e}', 'error')
    return redirect(url_for('relatorios'))

if __name__ == "__main__":
    app.run(debug=True)