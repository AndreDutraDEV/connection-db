# exercicio.py
#
# OBJETIVO:
# Este arquivo é um exercício para praticar a conexão com o banco de dados
# PostgreSQL usando a biblioteca 'psycopg'.
#
# INSTRUÇÕES:
# 1. Certifique-se de que seu container Docker do Postgres está rodando.
# 2. Complete todas as seções marcadas com:
#    ... # SEU CÓDIGO AQUI
# 3. Rode o script e veja se todas as operações funcionam sem erros.
#
# Boa sorte!

import psycopg
from psycopg import errors # Útil para tratar erros específicos

# 1. DETALHES DA CONEXÃO (Pré-preenchido)
# Estes dados vêm do seu docker-compose.yml
DB_PARAMS = {
    "dbname": "faculdatabase",
    "user": "admin",
    "password": "admin123",
    "host": "localhost",
    "port": "5432"
}

# --------------------------------------------------------------------------
# EXERCÍCIO 1: LER DADOS (SELECT)
# --------------------------------------------------------------------------
def exercicio_1_ler_salas(conn):
    """
    Objetivo: Ler e imprimir todas as salas da tabela 'salas'.
    """
    print("\n--- Exercício 1: LER DADOS (SELECT) ---")
    
    # Esta é a query que você deve executar.
    query = "SELECT codigo, tipo, capacidade FROM salas ORDER BY codigo;"
    
    try:
        # 'with conn.cursor()' gerencia o cursor automaticamente
        with conn.cursor() as cur:
            
            # 1. Execute a query
            ... # SEU CÓDIGO AQUI
            
            # 2. Busque TODOS os resultados da execução
            resultados = ... # SEU CÓDIGO AQUI
            
            print("Salas encontradas no banco:")
            
            # 3. Faça um loop 'for' nos 'resultados' e imprima cada sala
            # Dica: cada 'linha' em 'resultados' será uma tupla, ex: ('S01', 'Sala de Aula', 80)
            for linha in resultados:
                ... # SEU CÓDIGO AQUI (imprima a linha ou formate-a)
                
    except psycopg.Error as e:
        print(f"Erro ao tentar ler dados: {e}")

# --------------------------------------------------------------------------
# EXERCÍCIO 2: INSERIR DADOS (INSERT)
# --------------------------------------------------------------------------
def exercicio_2_inserir_disciplina(conn):
    """
    Objetivo: Inserir uma nova disciplina na tabela 'disciplina'.
    """
    print("\n--- Exercício 2: INSERIR DADOS (INSERT) ---")
    
    # Esta é a query. Note o '%s' (placeholder) para segurança.
    query = """
    INSERT INTO disciplina (cod_disciplina, nome, carga_horaria, ementa) 
    VALUES (%s, %s, %s, %s)
    RETURNING cod_disciplina; 
    """
    # Estes são os dados que vamos inserir
    dados_nova_disciplina = ('D999', 'Python Básico', 60, 'Ementa de Python Básico.')
    
    try:
        with conn.cursor() as cur:
            
            # 1. Execute a query, passando os 'dados_nova_disciplina' como segundo argumento
            #    Isso previne SQL Injection.
            ... # SEU CÓDIGO AQUI
            
            # 2. Busque o resultado (o 'cod_disciplina' que foi retornado)
            #    Use .fetchone() pois esperamos apenas 1 resultado.
            resultado = ... # SEU CÓDIGO AQUI
            
            # 3. Faça o COMMIT da transação para salvar a mudança no banco
            ... # SEU CÓDIGO AQUI
            
            print(f"SUCESSO: Disciplina '{resultado[0]}' inserida.")

    except errors.UniqueViolation as e:
        # Erro específico se a disciplina 'D999' já existir
        print("AVISO: A disciplina 'D999' já existe. Fazendo rollback...")
        # 4. Faça o ROLLBACK da transação para cancelar
        ... # SEU CÓDIGO AQUI
        
    except psycopg.Error as e:
        print(f"Erro ao tentar inserir dados: {e}")
        # 5. Faça o ROLLBACK em caso de qualquer outro erro
        ... # SEU CÓDIGO AQUI

# --------------------------------------------------------------------------
# EXERCÍCIO 3: ATUALIZAR DADOS (UPDATE)
# --------------------------------------------------------------------------
def exercicio_3_atualizar_disciplina(conn):
    """
    Objetivo: Atualizar a carga horária da disciplina 'D999' que acabamos de criar.
    """
    print("\n--- Exercício 3: ATUALIZAR DADOS (UPDATE) ---")
    
    query = "UPDATE disciplina SET carga_horaria = %s WHERE cod_disciplina = %s;"
    
    # Dados para o update: (nova carga horária, código da disciplina)
    dados_update = (80, 'D999') 
    
    try:
        with conn.cursor() as cur:
            
            # 1. Execute a query, passando os 'dados_update'
            ... # SEU CÓDIGO AQUI
            
            # 2. Faça o COMMIT da transação
            ... # SEU CÓDIGO AQUI
            
            # 'cur.rowcount' nos diz quantas linhas foram afetadas
            if cur.rowcount > 0:
                print(f"SUCESSO: Carga horária da disciplina '{dados_update[1]}' atualizada para {dados_update[0]}.")
            else:
                print(f"AVISO: Disciplina '{dados_update[1]}' não encontrada. Nenhuma alteração feita.")

    except psycopg.Error as e:
        print(f"Erro ao tentar atualizar dados: {e}")
        # 3. Faça o ROLLBACK em caso de erro
        ... # SEU CÓDIGO AQUI

# --------------------------------------------------------------------------
# EXERCÍCIO 4: DELETAR DADOS (DELETE)
# --------------------------------------------------------------------------
def exercicio_4_deletar_disciplina(conn):
    """
    Objetivo: Deletar a disciplina 'D999' que criamos e atualizamos.
    """
    print("\n--- Exercício 4: DELETAR DADOS (DELETE) ---")
    
    query = "DELETE FROM disciplina WHERE cod_disciplina = %s;"
    
    # Dados para o delete: (código da disciplina)
    # Note a vírgula: (valor,) para criar uma tupla de 1 elemento
    dados_delete = ('D999',) 
    
    try:
        with conn.cursor() as cur:
            
            # 1. Execute a query, passando os 'dados_delete'
            ... # SEU CÓDIGO AQUI
            
            # 2. Faça o COMMIT
            ... # SEU CÓDIGO AQUI
            
            if cur.rowcount > 0:
                print(f"SUCESSO: Disciplina '{dados_delete[0]}' deletada.")
            else:
                print(f"AVISO: Disciplina '{dados_delete[0]}' não encontrada para deletar.")

    except psycopg.Error as e:
        print(f"Erro ao tentar deletar dados: {e}")
        # 3. Faça o ROLLBACK
        ... # SEU CÓDIGO AQUI

# --------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL (MAIN)
# --------------------------------------------------------------------------
def main():
    """
    Função principal que orquestra a conexão e chama os exercícios.
    """
    print("--- INICIANDO EXERCÍCIO DE BANCO DE DADOS ---")
    
    try:
        # A forma moderna de conectar é com 'with', que gerencia
        # a abertura e fechamento da conexão automaticamente.
        with psycopg.connect(**DB_PARAMS) as conn:
            print("Conexão com o banco 'faculdatabase' estabelecida com sucesso!")
            
            # --- Executando os exercícios ---
            
            # 1. LER
            exercicio_1_ler_salas(conn)
            
            # 2. CRIAR
            exercicio_2_inserir_disciplina(conn)
            
            # 3. ATUALIZAR
            exercicio_3_atualizar_disciplina(conn)
            
            # 4. DELETAR
            exercicio_4_deletar_disciplina(conn)
            
            print("\n--- FIM DOS EXERCÍCIOS ---")

    except psycopg.OperationalError as e:
        # Erro comum se o banco não estiver rodando ou as credenciais erradas
        print("\n--- ERRO DE CONEXÃO ---")
        print(f"Não foi possível conectar ao banco de dados.")
        print(f"Verifique se o container Docker 'postgres_db' está em execução.")
        print(f"Detalhe: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# Ponto de entrada padrão do script
if __name__ == "__main__":
    main()