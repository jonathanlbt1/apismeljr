import os
import psycopg2
from psycopg2 import sql
from psycopg2 import errors
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SistemaMonitoramentoColmeias:
    def __init__(self):
        try:
            # Initialize PostgreSQL database using environment variables
            self.conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
            self.conn.autocommit = False  # Enable manual transaction management
            print("Database connection established.")
            self.criar_tabelas()
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            self.conn = None  # Ensure conn exists even if connection fails

    def criar_tabelas(self):
        if not self.conn:
            print("No database connection. Tables not created.")
            return

        cursor = self.conn.cursor()
        
        try:
            # Tabela de Colmeias
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS colmeias (
                id SERIAL PRIMARY KEY,
                codigo TEXT UNIQUE NOT NULL,
                data_instalacao DATE NOT NULL,
                localizacao TEXT NOT NULL,
                status TEXT NOT NULL
            )''')
            
            # Tabela de Inspeções
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS inspecoes (
                id SERIAL PRIMARY KEY,
                colmeia_id INTEGER NOT NULL,
                data_inspecao DATE NOT NULL,
                temperatura FLOAT NOT NULL,
                umidade FLOAT NOT NULL,
                presenca_pragas BOOLEAN NOT NULL,
                estado_geral TEXT NOT NULL,
                observacoes TEXT,
                FOREIGN KEY (colmeia_id) REFERENCES colmeias (id) ON DELETE CASCADE
            )''')
            
            # Tabela de Produção
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS producao (
                id SERIAL PRIMARY KEY,
                colmeia_id INTEGER NOT NULL,
                data_coleta DATE NOT NULL,
                quantidade_mel FLOAT NOT NULL,
                qualidade TEXT NOT NULL,
                FOREIGN KEY (colmeia_id) REFERENCES colmeias (id) ON DELETE CASCADE
            )''')
            
            self.conn.commit()
            print("Tables created or verified.")
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating tables: {e}")
        finally:
            cursor.close()

    def registrar_colmeia(self, codigo, localizacao):
        if not self.conn:
            print("No database connection. Cannot register colmeia.")
            return False

        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO colmeias (codigo, data_instalacao, localizacao, status)
            VALUES (%s, %s, %s, %s)
            ''', (codigo, datetime.now().date(), localizacao, 'ativa'))
            self.conn.commit()
            print(f"Colmeia {codigo} registrada com sucesso.")
            return True
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            if isinstance(e, errors.UniqueViolation):
                print(f"Erro ao registrar colmeia: Código '{codigo}' já existe.")
            else:
                print(f"Erro ao registrar colmeia: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            print(f"Unexpected error ao registrar colmeia: {e}")
            return False
        finally:
            cursor.close()

    def registrar_inspecao(self, colmeia_id, temperatura, umidade, presenca_pragas, estado_geral, observacoes):
        if not self.conn:
            print("No database connection. Cannot register inspeção.")
            return False

        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO inspecoes (colmeia_id, data_inspecao, temperatura, umidade, 
                                 presenca_pragas, estado_geral, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (colmeia_id, datetime.now().date(), temperatura, umidade, 
                  presenca_pragas, estado_geral, observacoes))
            self.conn.commit()
            print(f"Inspeção registrada para colmeia ID {colmeia_id}.")
            return True
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            print(f"Erro ao registrar inspeção: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            print(f"Unexpected error ao registrar inspeção: {e}")
            return False
        finally:
            cursor.close()

    def registrar_producao(self, colmeia_id, quantidade_mel, qualidade):
        if not self.conn:
            print("No database connection. Cannot register produção.")
            return False

        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO producao (colmeia_id, data_coleta, quantidade_mel, qualidade)
            VALUES (%s, %s, %s, %s)
            ''', (colmeia_id, datetime.now().date(), quantidade_mel, qualidade))
            self.conn.commit()
            print(f"Produção registrada para colmeia ID {colmeia_id}.")
            return True
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            if isinstance(e, errors.ForeignKeyViolation):
                print(f"Erro ao registrar produção: Colmeia ID {colmeia_id} não existe.")
            else:
                print(f"Erro ao registrar produção: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            print(f"Unexpected error ao registrar produção: {e}")
            return False
        finally:
            cursor.close()

    def gerar_relatorio_producao(self):
        if not self.conn:
            print("No database connection. Cannot generate relatório.")
            return

        cursor = self.conn.cursor()
        try:
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
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao gerar relatório de produção: {e}")
        finally:
            cursor.close()

    def verificar_alertas(self):
        if not self.conn:
            print("No database connection. Cannot verificar alertas.")
            return []

        cursor = self.conn.cursor()
        try:
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
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao verificar alertas: {e}")
            return []
        finally:
            cursor.close()

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("Database connection closed.")

    def listar_colmeias(self):
        if not self.conn:
            print("No database connection. Cannot list colmeias.")
            return []
        
        cursor = self.conn.cursor()
        colmeias = []
        try:
            cursor.execute("SELECT id, codigo, localizacao FROM colmeias ORDER BY codigo")
            rows = cursor.fetchall()
            colmeias = [{'id': row[0], 'codigo': row[1], 'localizacao': row[2]} for row in rows]
        except Exception as e:
            print(f"Erro ao listar colmeias: {e}")
        finally:
            cursor.close()
        
        return colmeias

# Example usage
if __name__ == "__main__":
    sistema = SistemaMonitoramentoColmeias()
    sistema.verificar_alertas()