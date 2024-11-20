from flask import Flask, render_template, request, redirect, url_for, flash
from database import SistemaMonitoramentoColmeias

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the backend system
sistema = SistemaMonitoramentoColmeias()

@app.route('/')
def index():
    return render_template('index.html')

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
    return redirect(url_for('index'))

@app.route('/registrar_inspecao', methods=['POST'])
def registrar_inspecao():
    colmeia_id = request.form['colmeia_id']
    temperatura = request.form['temperatura']
    umidade = request.form['umidade']
    presenca_pragas = request.form.get('presenca_pragas') == 'on'
    estado_geral = request.form['estado_geral']
    observacoes = request.form['observacoes']
    try:
        sistema.registrar_inspecao(colmeia_id, temperatura, umidade, presenca_pragas, estado_geral, observacoes)
        flash('Inspeção registrada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao registrar inspeção: {e}', 'error')
    return redirect(url_for('index'))

@app.route('/registrar_producao', methods=['POST'])
def registrar_producao():
    colmeia_id = request.form['colmeia_id']
    quantidade_mel = request.form['quantidade_mel']
    qualidade = request.form['qualidade']
    try:
        sistema.registrar_producao(colmeia_id, quantidade_mel, qualidade)
        flash('Produção registrada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao registrar produção: {e}', 'error')
    return redirect(url_for('index'))

@app.route('/verificar_alertas')
def verificar_alertas():
    alertas = sistema.verificar_alertas()
    if not alertas:
        alertas = None  # Ensure alertas is None if no alerts are found
    return render_template('alertas.html', alertas=alertas)

if __name__ == "__main__":
    app.run(debug=True)