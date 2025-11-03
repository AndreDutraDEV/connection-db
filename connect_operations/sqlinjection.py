# app_vulneravel.py
#
# ######################################################################
# # ATENÇÃO: ESTE É UM EXEMPLO DE CÓDIGO VULNERÁVEL.                  #
# # NÃO USE ESTE CÓDIGO EM NENHUMA CIRCUNSTÂNCIA.                      #
# # ELE SERVE APENAS PARA DEMONSTRAR O SQL INJECTION.                  #
# ######################################################################

import psycopg

DB_PARAMS = {
    "dbname": "faculdatabase",
    "user": "admin",
    "password": "admin123",
    "host": "localhost",
    "port": "5432"
}

def buscar_aluno_vulneravel(conn, matricula_input_usuario):
    """
    Esta função é VULNERÁVEL a SQL Injection.
    Ela usa uma f-string (formatação de string) para inserir
    a entrada do usuário DIRETAMENTE na query.
    """
    print(f"\n--- Buscando Aluno com: '{matricula_input_usuario}' ---")
    
    # O PROBLEMA ESTÁ AQUI:
    # A entrada do usuário é misturada com o comando SQL.
    query = f"SELECT matricula, cpf FROM aluno WHERE matricula = '{matricula_input_usuario}';"
    
    print(f"Query Executada: {query}")
    
    try:
        with conn.cursor() as cur:
            # Nota: O psycopg3 é mais seguro e pode bloquear algumas
            # formas de "stacking" (múltiplos comandos), mas a 
            # vulnerabilidade de exfiltração de dados (UNION) ainda existe.
            cur.execute(query) 
            
            resultados = cur.fetchall()
            
            if not resultados:
                print("Nenhum resultado.")
            
            for linha in resultados:
                print(f"  -> Encontrado: {linha}")
                
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

def main():
    try:
        with psycopg.connect(**DB_PARAMS) as conn:
            print("--- Conexão estabelecida (Modo Vulnerável) ---")
            
            # --- CENÁRIO 1: Uso normal ---
            # O usuário insere um dado esperado.
            entrada_normal = "A0001"
            buscar_aluno_vulneravel(conn, entrada_normal)
            
            # --- CENÁRIO 2: Ataque de Bypass Lógico ---
            # O atacante "quebra" a string SQL e insere sua própria lógica.
            # Ele fecha a string com ' e adiciona uma condição que é
            # sempre verdadeira (OR '1'='1'). O -- no final
            # comenta o resto da query original.
            entrada_maliciosa_1 = "A0001' OR '1'='1"
            buscar_aluno_vulneravel(conn, entrada_maliciosa_1)
            # Resultado: A query se torna "SELECT ... WHERE matricula = 'A0001' OR '1'='1';"
            # Isso retorna TODOS os alunos do banco.
            
            # --- CENÁRIO 3: Ataque de Exfiltração (UNION) ---
            # O atacante "finge" ser uma matrícula, mas usa UNION
            # para "colar" os resultados de outra tabela (ex: professor)
            # na consulta.
            entrada_maliciosa_2 = "XXXXX' UNION SELECT matricula, cpf FROM professor; --"
            buscar_aluno_vulneravel(conn, entrada_maliciosa_2)
            # Resultado: A query se torna:
            # "SELECT ... FROM aluno WHERE matricula = 'XXXXX' 
            #  UNION 
            #  SELECT matricula, cpf FROM professor; --';"
            # Isso retorna os dados (matrícula e CPF) de TODOS os professores.
            
            # --- CENÁRIO 4: Ataque Destrutivo (DROP TABLE) ---
            # (O psycopg moderno bloqueia isso por padrão, mas outros
            # drivers/configurações podem permitir)
            # O atacante tenta rodar um segundo comando.
            entrada_maliciosa_3 = "A0001'; DROP TABLE horario_aluno; --"
            buscar_aluno_vulneravel(conn, entrada_maliciosa_3)
            # Resultado: Se permitido, executaria "SELECT...;" e DEPOIS "DROP TABLE...;"

    except Exception as e:
        print(f"Erro de conexão: {e}")

if __name__ == "__main__":
    main()
    
# A FORMA CORRETA (NÃO VULNERÁVEL):
# query_correta = "SELECT matricula, cpf FROM aluno WHERE matricula = %s;"
# cur.execute(query_correta, (matricula_input_usuario,))