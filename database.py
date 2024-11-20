import os
import psycopg2
from psycopg2 import sql, errors
from psycopg2.extras import RealDictCursor
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.info("Database connection established.")
            self.criar_tabelas()
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
            self.conn = None  # Ensure conn exists even if connection fails

    def criar_tabelas(self):
        if not self.conn:
            logger.info("No database connection. Tables not created.")
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
            logger.info("Tables created or verified.")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating tables: {e}")
        finally:
            cursor.close()

    def listar_colmeias(self):
        if not self.conn:
            logger.info("No database connection. Cannot list colmeias.")
            return []
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, codigo, localizacao, data_instalacao, status FROM colmeias ORDER BY codigo")
                colmeias = cur.fetchall()
            return colmeias
        except Exception as e:
            logger.error(f"Erro ao listar colmeias: {e}")
            return []

    def get_colmeia_by_id(self, colmeia_id):
        if not self.conn:
            logger.info("No database connection. Cannot get colmeia.")
            return None
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, codigo, localizacao, data_instalacao, status FROM colmeias WHERE id = %s", (colmeia_id,))
                colmeia = cur.fetchone()
            return colmeia
        except Exception as e:
            logger.error(f"Erro ao obter colmeia por ID: {e}")
            return None

    def get_inspecoes_by_colmeia_id(self, colmeia_id):
        if not self.conn:
            logger.info("No database connection. Cannot get inspeções.")
            return []
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, data_inspecao, temperatura, umidade, presenca_pragas, estado_geral, observacoes
                    FROM inspecoes
                    WHERE colmeia_id = %s
                    ORDER BY data_inspecao DESC
                """, (colmeia_id,))
                inspecoes = cur.fetchall()
            return inspecoes
        except Exception as e:
            logger.error(f"Erro ao obter inspeções: {e}")
            return []

    def get_producoes_by_colmeia_id(self, colmeia_id):
        if not self.conn:
            logger.info("No database connection. Cannot get produções.")
            return []
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, data_coleta, quantidade_mel, qualidade
                    FROM producao
                    WHERE colmeia_id = %s
                    ORDER BY data_coleta DESC
                """, (colmeia_id,))
                producoes = cur.fetchall()
            return producoes
        except Exception as e:
            logger.error(f"Erro ao obter produções: {e}")
            return []

    def registrar_colmeia(self, codigo, localizacao):
        if not self.conn:
            logger.info("No database connection. Cannot register colmeia.")
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO colmeias (codigo, data_instalacao, localizacao, status)
                    VALUES (%s, %s, %s, %s)
                """, (codigo, datetime.now().date(), localizacao, 'ativa'))
            self.conn.commit()
            logger.info(f"Colmeia {codigo} registrada com sucesso.")
            return True
        except errors.UniqueViolation as e:
            self.conn.rollback()
            logger.error(f"Erro: O código '{codigo}' já está em uso.")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Unexpected error ao registrar colmeia: {e}")
            return False

    def registrar_inspecao(self, colmeia_id, temperatura, umidade, presenca_pragas, estado_geral, observacoes):
        if not self.conn:
            logger.info("No database connection. Cannot register inspeção.")
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO inspecoes (colmeia_id, data_inspecao, temperatura, umidade, presenca_pragas, estado_geral, observacoes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    colmeia_id,
                    datetime.now().date(),
                    temperatura,
                    umidade,
                    presenca_pragas,
                    estado_geral,
                    observacoes
                ))
            self.conn.commit()
            logger.info(f"Inspeção registrada para colmeia ID {colmeia_id}.")
            return True
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Erro ao registrar inspeção: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Unexpected error ao registrar inspeção: {e}")
            return False

    def registrar_producao(self, colmeia_id, quantidade_mel, qualidade):
        if not self.conn:
            logger.info("No database connection. Cannot register produção.")
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO producao (colmeia_id, data_coleta, quantidade_mel, qualidade)
                    VALUES (%s, %s, %s, %s)
                """, (
                    colmeia_id,
                    datetime.now().date(),
                    quantidade_mel,
                    qualidade
                ))
            self.conn.commit()
            logger.info(f"Produção registrada para colmeia ID {colmeia_id}.")
            return True
        except errors.ForeignKeyViolation as e:
            self.conn.rollback()
            logger.error(f"Erro: A colmeia ID '{colmeia_id}' não existe.")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Unexpected error ao registrar produção: {e}")
            return False

    def deletar_colmeia(self, colmeia_id):
        if not self.conn:
            logger.info("No database connection. Cannot delete colmeia.")
            return False
        
        try:
            with self.conn.cursor() as cur:
                # Delete the Colmeia; related inspecoes and producao will be deleted due to ON DELETE CASCADE
                cur.execute("DELETE FROM colmeias WHERE id = %s", (colmeia_id,))
            self.conn.commit()
            logger.info(f"Colmeia ID {colmeia_id} e seus dados foram deletados com sucesso.")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Erro ao deletar colmeia: {e}")
            return False

    def gerar_relatorio_producao(self):
        if not self.conn:
            logger.info("No database connection. Cannot generate relatório.")
            return

        try:
            query = '''
            SELECT c.codigo, p.data_coleta, p.quantidade_mel
            FROM producao p
            JOIN colmeias c ON p.colmeia_id = c.id
            ORDER BY p.data_coleta
            '''
            df = pd.read_sql_query(query, self.conn)
            
            # Check if DataFrame is empty
            if df.empty:
                logger.info("Nenhuma produção registrada para gerar o relatório.")
                return
            
            # Ensure the directory exists
            os.makedirs('static/relatorios/', exist_ok=True)
            
            # Gerar gráfico de produção
            plt.figure(figsize=(10, 6))
            for codigo in df['codigo'].unique():
                df_colmeia = df[df['codigo'] == codigo]
                plt.plot(df_colmeia['data_coleta'], df_colmeia['quantidade_mel'], marker='o', label=codigo)
            
            plt.title('Produção de Mel por Colmeia')
            plt.xlabel('Data')
            plt.ylabel('Quantidade de Mel (kg)')
            plt.legend(title='Colmeias')
            plt.grid(True)
            plt.tight_layout()
            
            # Save the plot
            plt.savefig('static/relatorios/relatorio_producao.png')
            plt.close()
            logger.info("Relatório de produção gerado e salvo em 'static/relatorios/relatorio_producao.png'.")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Erro ao gerar relatório de produção: {e}")

    def verificar_alertas(self):
        if not self.conn:
            logger.info("No database connection. Cannot verificar alertas.")
            return []
        
        try:
            data_limite = (datetime.now() - timedelta(days=15)).date()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT c.codigo, MAX(i.data_inspecao) AS ultima_inspecao
                    FROM colmeias c
                    LEFT JOIN inspecoes i ON c.id = i.colmeia_id
                    GROUP BY c.id
                    HAVING MAX(i.data_inspecao) < %s OR MAX(i.data_inspecao) IS NULL
                """, (data_limite,))
                results = cur.fetchall()
            logger.info(f"Alertas verificados: {results}")
            return results
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Erro ao verificar alertas: {e}")
            return []

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logger.info("Database connection closed.")