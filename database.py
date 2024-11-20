import os
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SistemaMonitoramentoColmeias:
    def __init__(self, dbname, user, password, host, port):
        try:
            # Inicializa o banco de dados PostgreSQL
            self.conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
            print("Database connection established.")
            self.criar_tabelas()
        except Exception as e:
            print(f"Error connecting to the database: {e}")
    
    def criar_tabelas(self):
        cursor = self.conn.cursor()
        
        # Tabela de Colmeias
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS colmeias (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE,
            data_instalacao DATE,
            localizacao TEXT,
            status TEXT
        )''')
        
        # Tabela de Inspeções
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspecoes (
            id SERIAL PRIMARY KEY,
            colmeia_id INTEGER,
            data_inspecao DATE,
            temperatura FLOAT,
            umidade FLOAT,
            presenca_pragas BOOLEAN,
            estado_geral TEXT,
            observacoes TEXT,
            FOREIGN KEY (colmeia_id) REFERENCES colmeias (id)
        )''')
        
        # Tabela de Produção
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS producao (
            id SERIAL PRIMARY KEY,
            colmeia_id INTEGER,
            data_coleta DATE,
            quantidade_mel FLOAT,
            qualidade TEXT,
            FOREIGN KEY (colmeia_id) REFERENCES colmeias (id)
        )''')
        
        self.conn.commit()
        print("Tables created or verified.")
    
    def registrar_colmeia(self, codigo, localizacao):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO colmeias (codigo, data_instalacao, localizacao, status)
            VALUES (%s, %s, %s, %s)
            ''', (codigo, datetime.now().date(), localizacao, 'ativa'))
            self.conn.commit()
            print(f"Colmeia {codigo} registrada com sucesso.")
            return True
        except psycopg2.IntegrityError:
            self.conn.rollback()
            print(f"Erro ao registrar colmeia {codigo}.")
            return False
    
    def registrar_inspecao(self, colmeia_id, temperatura, umidade, presenca_pragas, estado_geral, observacoes):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO inspecoes (colmeia_id, data_inspecao, temperatura, umidade, 
                             presenca_pragas, estado_geral, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (colmeia_id, datetime.now().date(), temperatura, umidade, 
              presenca_pragas, estado_geral, observacoes))
        self.conn.commit()
        print(f"Inspeção registrada para colmeia {colmeia_id}.")
    
    def registrar_producao(self, colmeia_id, quantidade_mel, qualidade):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO producao (colmeia_id, data_coleta, quantidade_mel, qualidade)
        VALUES (%s, %s, %s, %s)
        ''', (colmeia_id, datetime.now().date(), quantidade_mel, qualidade))
        self.conn.commit()
        print(f"Produção registrada para colmeia {colmeia_id}.")
    
    def gerar_relatorio_producao(self):
        query = '''
        SELECT c.codigo, p.data_coleta, p.quantidade_mel
        FROM producao p
        JOIN colmeias c ON p.colmeia_id = c.id
        ORDER BY p.data_coleta
        '''
        df = pd.read_sql_query(query, self.conn)
        
        # Gerar gráfico de produção
        plt.figure(figsize=(10, 6))
        for codigo in df['codigo'].unique():
            dados_colmeia = df[df['codigo'] == codigo]
            plt.plot(dados_colmeia['data_coleta'], 
                    dados_colmeia['quantidade_mel'], 
                    label=f'Colmeia {codigo}')
        
        plt.title('Produção de Mel por Colmeia')
        plt.xlabel('Data')
        plt.ylabel('Quantidade de Mel (kg)')
        plt.legend()
        plt.grid(True)
        plt.savefig('relatorio_producao.png')
        plt.close()
        print("Relatório de produção gerado.")
    
    def verificar_alertas(self):
        # Verifica colmeias que não são inspecionadas há mais de 15 dias
        cursor = self.conn.cursor()
        data_limite = (datetime.now() - timedelta(days=15)).date()
        
        query = '''
        SELECT c.codigo, MAX(i.data_inspecao) as ultima_inspecao
        FROM colmeias c
        LEFT JOIN inspecoes i ON c.id = i.colmeia_id
        GROUP BY c.id
        HAVING MAX(i.data_inspecao) < %s OR MAX(i.data_inspecao) IS NULL
        '''
        
        cursor.execute(query, (data_limite,))
        results = cursor.fetchall()
        print(f"Alertas verificados: {results}")
        return results

    def __del__(self):
        self.conn.close()
        print("Database connection closed.")

# Example usage
if __name__ == "__main__":
    sistema = SistemaMonitoramentoColmeias(
        dbname='apisjr',
        user='postgres',
        password='1963',
        host='localhost',
        port='5432'
    )
    sistema.verificar_alertas()