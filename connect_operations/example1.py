import psycopg  # A biblioteca moderna para PostgreSQL
from psycopg.rows import dict_row # Opcional: para retornar resultados como dicionários

# 1. DETALHES DA CONEXÃO
# Estes dados vêm diretamente do seu docker-compose.yml
DB_PARAMS = {
    "dbname": "faculdatabase",
    "user": "admin",
    "password": "admin123",
    "host": "localhost",  # 'localhost' funciona pois você mapeou a porta 5432 para o seu host
    "port": "5432"
}

# 2. FUNÇÃO DE LEITURA (SIMPLES)
def listar_cursos(conn):
    """
    Executa uma consulta SELECT simples para buscar todos os cursos.
    Demonstra o uso de cursor.execute() e cursor.fetchall().
    """
    print("\n--- 1. Listando Todos os Cursos ---")
    try:
        # Usar "with" garante que o cursor será fechado automaticamente
        with conn.cursor() as cur:
            # Executa a query
            cur.execute("SELECT cod_mec, nome, modalidade FROM curso ORDER BY nome;")
            
            # Busca todos os resultados da consulta
            cursos = cur.fetchall()
            
            if not cursos:
                print("Nenhum curso encontrado.")
                return

            for curso in cursos:
                # curso é uma tupla, ex: (1004, 'Análise e Desenvolvimento de Sistemas', 'Híbrido')
                print(f"  -> [{curso[0]}] {curso[1]} (Modalidade: {curso[2]})")
                
    except psycopg.Error as e:
        print(f"Erro ao buscar cursos: {e}")


# 3. FUNÇÃO DE LEITURA (COM PARÂMETRO E JOIN)
def buscar_aluno(conn, matricula):
    """
    Busca um aluno específico e seu curso.
    Demonstra:
    - Uso de JOIN para cruzar tabelas (aluno, pessoa, curso).
    - Prevenção de SQL Injection usando placeholders (%s).
    - Uso de cursor.fetchone() para um único resultado.
    """
    print(f"\n--- 2. Buscando Aluno (Matrícula: {matricula}) ---")
    try:
        with conn.cursor() as cur:
            # Esta query usa JOINs para pegar dados de 3 tabelas
            query = """
            SELECT p.nome, p.email, c.nome AS nome_curso, a.data_inicio
            FROM aluno a
            JOIN pessoa p ON a.cpf = p.cpf
            JOIN curso c ON a.cod_mec = c.cod_mec
            WHERE a.matricula = %s; 
            """
            
            # IMPORTANTE: Sempre passe parâmetros como um segundo argumento
            # (uma tupla) para evitar SQL Injection.
            # NUNCA use f-strings ou '+' para montar queries com dados do usuário.
            cur.execute(query, (matricula,))
            
            # Busca apenas o primeiro resultado
            aluno = cur.fetchone()
            
            if aluno:
                # aluno é uma tupla, ex: ('Rafael Martins', 'rafael.martins51@exemplo.com', 'Engenharia de Software', datetime.date(2019, 4, 9))
                print(f"  Nome:  {aluno[0]}")
                print(f"  Email: {aluno[1]}")
                print(f"  Curso: {aluno[2]}")
                print(f"  Início: {aluno[3].strftime('%d/%m/%Y')}")
            else:
                print(f"  Aluno com matrícula {matricula} não encontrado.")

    except psycopg.Error as e:
        print(f"Erro ao buscar aluno: {e}")


# 4. FUNÇÃO DE LEITURA (COMPLEXA - MÚLTIPLOS JOINS)
def ver_horario_aluno(conn, matricula_aluno, semestre):
    """
    Monta o horário de um aluno para um semestre específico.
    Demonstra uma consulta complexa, pertinente ao seu esquema.
    """
    print(f"\n--- 3. Horário do Aluno ({matricula_aluno}) no Semestre ({semestre}) ---")
    try:
        # Usamos dict_row para que os resultados venham como dicionários Python
        # (ex: {'disciplina': 'Banco de Dados', 'professor': ...})
        # Isso é opcional, mas muito mais legível.
        with conn.cursor(row_factory=dict_row) as cur:
            query = """
            SELECT 
                d.nome AS disciplina,
                p.nome AS professor,
                os.codigo_sala,
                os.dia_semana,
                os.horario_ini,
                os.horario_fim
            FROM horario_aluno ha
            JOIN oferta_semestre os ON ha.id_oferta_semestre = os.id
            JOIN afinidade_professor ap ON os.id_afinidade_professor = ap.id
            JOIN disciplina d ON ap.cod_disciplina = d.cod_disciplina
            JOIN professor prof ON ap.matricula_professor = prof.matricula
            JOIN pessoa p ON prof.cpf = p.cpf
            WHERE ha.matricula_aluno = %s AND os.semestre = %s
            ORDER BY os.dia_semana, os.horario_ini;
            """
            cur.execute(query, (matricula_aluno, semestre))
            horario = cur.fetchall()
            
            if not horario:
                print(f"  Nenhum horário encontrado para o aluno {matricula_aluno} no semestre {semestre}.")
                return

            for item in horario:
                print(f"  - Disciplina: {item['disciplina']}")
                print(f"    Professor:  {item['professor']}")
                print(f"    Local:      Sala {item['codigo_sala']} ({item['dia_semana']} das {item['horario_ini']} às {item['horario_fim']})\n")

    except psycopg.Error as e:
        print(f"Erro ao buscar horário: {e}")


# 5. FUNÇÃO DE ESCRITA (INSERT)
def adicionar_afinidade_professor(conn, matricula_prof, cod_disciplina):
    """
    Adiciona uma nova afinidade de disciplina para um professor.
    Demonstra:
    - Operação de ESCRITA (INSERT).
    - Uso de conn.commit() para salvar as mudanças.
    - Uso de conn.rollback() para desfazer em caso de erro.
    - Uso de 'RETURNING id' para pegar o ID gerado.
    """
    print(f"\n--- 4. Adicionando Afinidade ({matricula_prof} -> {cod_disciplina}) ---")
    
    # Operações de escrita devem ser feitas dentro de um bloco try/except
    # para podermos reverter (rollback) se algo der errado.
    try:
        with conn.cursor() as cur:
            query = """
            INSERT INTO afinidade_professor (matricula_professor, cod_disciplina, data_inclusao)
            VALUES (%s, %s, CURRENT_DATE)
            RETURNING id; -- Pede ao Postgres para retornar o ID da linha recém-criada
            """
            cur.execute(query, (matricula_prof, cod_disciplina))
            
            # Pega o ID retornado
            novo_id = cur.fetchone()[0]
            
            # --- PONTO CRÍTICO ---
            # Se a query foi um sucesso, precisamos "commitar" a transação.
            # Sem isso, a mudança NÃO será salva no banco.
            conn.commit()
            print(f"  SUCESSO: Afinidade adicionada. Novo ID: {novo_id}.")
            
    except psycopg.Error as e:
        # --- PONTO CRÍTICO ---
        # Se ocorreu um erro (ex: a afinidade já existe, violando a 'UNIQUE KEY'),
        # o 'commit' não acontece e devemos reverter a transação.
        conn.rollback()
        print(f"  FALHA: Erro ao adicionar afinidade (transação revertida).")
        print(f"  Detalhe: {e}")


# 6. FUNÇÃO PRINCIPAL (MAIN)
def main():
    """
    Função principal que orquestra a conexão e chama as funções de exemplo.
    """
    try:
        # A forma mais segura de conectar é com um bloco 'with'.
        # Se a conexão falhar, ele levanta uma exceção.
        # Se for bem-sucedida, o 'conn' será fechado automaticamente no final.
        print(f"Tentando conectar ao banco '{DB_PARAMS['dbname']}' em '{DB_PARAMS['host']}'...")
        with psycopg.connect(**DB_PARAMS) as conn:
            
            print("--- CONEXÃO BEM-SUCEDIDA! ---")
            
            # --- CHAMANDO AS FUNÇÕES DE EXEMPLO ---
            
            # Exemplo 1: Leitura simples
            listar_cursos(conn)
            
            # Exemplo 2: Leitura com parâmetro (Aluno A0001 existe no init.sql)
            buscar_aluno(conn, 'A0001')
            
            # Exemplo 3: Leitura complexa (Aluno A0001 tem horário em 2025.1)
            ver_horario_aluno(conn, 'A0001', '2025.1')
            
            # Exemplo 4: Escrita (P0001 e D001 não têm afinidade no init.sql)
            adicionar_afinidade_professor(conn, 'P0001', 'D001') # Programação I
            
            # Exemplo 5: Escrita que vai falhar (P0001 e D007 JÁ existem no init.sql)
            # Isso vai acionar o 'rollback' e demonstrar o tratamento de erro.
            adicionar_afinidade_professor(conn, 'P0001', 'D007') # Arquitetura de Software
            
            print("\n--- FIM DAS OPERAÇÕES ---")

    except psycopg.OperationalError as e:
        # Erro comum se o banco não estiver rodando ou as credenciais estiverem erradas
        print(f"\n--- ERRO DE CONEXÃO ---")
        print(f"Não foi possível conectar ao banco de dados.")
        print(f"Verifique se o container Docker 'postgres_db' está em execução.")
        print(f"Detalhe: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


# Ponto de entrada padrão do script Python
if __name__ == "__main__":
    main()