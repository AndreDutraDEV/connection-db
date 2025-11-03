import psycopg
from psycopg.rows import dict_row  # Para resultados como dicionários
from psycopg.pool import ConnectionPool
from psycopg import errors # Para capturar erros específicos do Postgres

# 1. DETALHES DA CONEXÃO (igual ao anterior)
DB_PARAMS = {
    "dbname": "faculdatabase",
    "user": "admin",
    "password": "admin123",
    "host": "localhost",
    "port": "5432"
}

# 2. CRIAÇÃO DO POOL DE CONEXÕES (A FORMA PROFISSIONAL)
# Este pool será criado uma vez quando a aplicação iniciar.
# min_size = 2 -> Manter pelo menos 2 conexões abertas o tempo todo.
# max_size = 10 -> Permitir no máximo 10 conexões simultâneas.
# **DB_PARAMS -> Passa todos os detalhes do nosso dicionário para o pool.
try:
    # O pool é a "caixa" que gerencia as conexões
    pool = ConnectionPool(
        conninfo=psycopg.conninfo.make_conninfo(**DB_PARAMS),
        min_size=2,
        max_size=10
    )
    print("--- Pool de Conexões criado com sucesso ---")
except psycopg.OperationalError as e:
    print(f"--- FALHA AO CRIAR POOL --- \nVerifique o Docker e as credenciais.\n{e}")
    exit()


# 3. FUNÇÃO DE ESCRITA (ATUALIZADA)
def adicionar_afinidade_com_tratamento(matricula_prof, cod_disciplina):
    """
    Demonstra a forma idiomática (padrão) de transação e tratamento de erro.
    - Usa 'with pool.connection()' para pegar uma conexão do pool.
    - Usa 'with conn.transaction()' para garantir commit/rollback automático.
    - Captura um erro específico: UniqueViolation.
    """
    print(f"\n--- 4. Adicionando Afinidade ({matricula_prof} -> {cod_disciplina}) ---")
    
    try:
        # Pega uma conexão do pool (ela será devolvida automaticamente no final)
        with pool.connection() as conn:
            
            # --- O BLOCO DE TRANSAÇÃO PROFISSIONAL ---
            # Se o bloco 'with' terminar sem erros, o conn.commit() é chamado.
            # Se ocorrer QUALQUER exceção, o conn.rollback() é chamado.
            # Você não precisa mais gerenciar isso manualmente.
            with conn.transaction():
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO afinidade_professor (matricula_professor, cod_disciplina, data_inclusao)
                    VALUES (%s, %s, CURRENT_DATE)
                    RETURNING id;
                    """
                    cur.execute(query, (matricula_prof, cod_disciplina))
                    novo_id = cur.fetchone()[0]
                    print(f"  SUCESSO: Afinidade adicionada. Novo ID: {novo_id}.")

    # --- TRATAMENTO DE ERRO ESPECÍFICO ---
    # O código '23505' é o padrão do Postgres para "unique_violation".
    # A biblioteca 'psycopg' nos dá uma exceção Python para isso.
    except errors.UniqueViolation as e:
        # Isso não é um "erro" do nosso código, é uma regra de negócio.
        # Por exemplo: "O usuário tentou cadastrar um CPF que já existe".
        print(f"  AVISO: Essa afinidade já existe no banco de dados.")
        
    except psycopg.Error as e:
        # Pega qualquer outro erro de banco (ex: tabela não existe)
        print(f"  FALHA: Erro inesperado ao adicionar afinidade: {e}")


# 4. FUNÇÃO UPDATE (TÉCNICA USUAL)
def atualizar_titulacao_professor(matricula_prof, nova_titulacao):
    """
    Demonstra uma operação de UPDATE.
    - Usa o bloco de transação.
    - Usa 'cur.rowcount' para verificar se alguma linha foi de fato alterada.
    """
    print(f"\n--- 5. Atualizando Titulação (Professor: {matricula_prof}) ---")
    
    # Titulações válidas do seu ENUM: 
    # 'Graduado', 'Especialista', 'Mestre', 'Doutor', 'Pós-Doutor'
    if nova_titulacao not in ('Graduado', 'Especialista', 'Mestre', 'Doutor', 'Pós-Doutor'):
        print(f"  FALHA: Titulação '{nova_titulacao}' é inválida.")
        return

    try:
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    query = "UPDATE professor SET titulacao = %s WHERE matricula = %s;"
                    cur.execute(query, (nova_titulacao, matricula_prof))
                    
                    # 'cur.rowcount' retorna o número de linhas afetadas pela
                    # última operação (UPDATE, DELETE, INSERT).
                    if cur.rowcount > 0:
                        print(f"  SUCESSO: Titulação do professor {matricula_prof} atualizada para {nova_titulacao}.")
                    else:
                        print(f"  AVISO: Professor {matricula_prof} não encontrado. Nenhuma alteração feita.")

    except psycopg.Error as e:
        print(f"  FALHA: Erro ao atualizar professor: {e}")


# 5. FUNÇÃO DE INSERT EM LOTE (TÉCNICA USUAL)
def cadastrar_novos_alunos_em_lote(novos_alunos_data):
    """
    Demonstra como inserir MÚLTIPLAS linhas de uma vez.
    Isso é MUITO mais rápido do que fazer um 'for loop' e chamar 'cur.execute()'
    para cada aluno.
    """
    print(f"\n--- 6. Cadastrando {len(novos_alunos_data)} Alunos em Lote ---")
    
    try:
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    # A query é para UMA linha, mas usamos 'executemany'
                    query = """
                    INSERT INTO pessoa (cpf, nome, email, data_nascimento) 
                    VALUES (%s, %s, %s, %s);
                    """
                    # 'executemany' executa a query para cada item na lista de tuplas
                    cur.executemany(query, [al['pessoa'] for al in novos_alunos_data])
                    
                    # Agora inserimos na tabela 'aluno'
                    query_aluno = """
                    INSERT INTO aluno (matricula, cod_mec, data_inicio, cpf)
                    VALUES (%s, %s, %s, %s);
                    """
                    cur.executemany(query_aluno, [al['aluno'] for al in novos_alunos_data])
                    
                    print(f"  SUCESSO: {cur.rowcount} novos registros de alunos inseridos.")

    except errors.UniqueViolation as e:
        print(f"  FALHA: Um dos CPFs ou Matrículas já existe. Nenhuma alteração foi feita (rollback).")
    except psycopg.Error as e:
        print(f"  FALHA: Erro ao inserir alunos em lote: {e}")


# 6. FUNÇÃO DE DELETE
def deletar_afinidade(afinidade_id):
    """
    Demonstra uma operação de DELETE.
    - Usa o bloco de transação.
    - Usa 'cur.rowcount' para verificar se a linha foi deletada.
    """
    print(f"\n--- 7. Deletando Afinidade (ID: {afinidade_id}) ---")
    try:
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    # NOTA: Cuidado com DELETE sem 'WHERE'. 
                    # Aqui, estamos deletando pelo ID ('id' da tabela 'afinidade_professor')
                    query = "DELETE FROM afinidade_professor WHERE id = %s;"
                    cur.execute(query, (afinidade_id,))
                    
                    if cur.rowcount > 0:
                        print(f"  SUCESSO: Afinidade ID {afinidade_id} deletada.")
                    else:
                        print(f"  AVISO: Nenhuma afinidade com ID {afinidade_id} foi encontrada.")

    except psycopg.Error as e:
        print(f"  FALHA: Erro ao deletar afinidade: {e}")


# 7. FUNÇÃO PRINCIPAL (MAIN)
def main():
    """
    Função principal que orquestra as chamadas.
    O bloco 'with pool:' garante que o pool será fechado corretamente
    ao final da execução do programa.
    """
    with pool:
        # Exemplo 4: Adicionar uma nova (P0001 e D001)
        # (ID 697, com base no seu dump, será o próximo)
        adicionar_afinidade_com_tratamento('P0001', 'D001') # Programação I
        
        # Exemplo 4.1: Tentar adicionar a mesma de novo (vai falhar)
        adicionar_afinidade_com_tratamento('P0001', 'D001') # Vai dar UniqueViolation
        
        # Exemplo 4.2: Tentar adicionar uma que JÁ EXISTE no init.sql
        adicionar_afinidade_com_tratamento('P0001', 'D007') # Vai dar UniqueViolation
        
        # Exemplo 5: Atualizar titulação do P0001 (de 'Graduado' para 'Mestre')
        atualizar_titulacao_professor('P0001', 'Mestre')
        
        # Exemplo 5.1: Tentar atualizar um professor que não existe
        atualizar_titulacao_professor('P9999', 'Doutor')
        
        # Exemplo 6: Inserir 2 novos alunos em lote
        novos_alunos = [
            {
                "pessoa": ('11122233344', 'Aluno Lote 1', 'lote1@exemplo.com', '2005-01-01'),
                "aluno": ('A0201', 1001, '2025-01-01', '11122233344')
            },
            {
                "pessoa": ('55566677788', 'Aluno Lote 2', 'lote2@exemplo.com', '2006-02-02'),
                "aluno": ('A0202', 1002, '2025-01-01', '55566677788')
            }
        ]
        cadastrar_novos_alunos_em_lote(novos_alunos)

        # Exemplo 7: Deletar a afinidade que criamos no primeiro passo
        # (Seu dump para em 696, então o primeiro INSERT deve ter criado o 697)
        deletar_afinidade(697) # ID 697
        
        print("\n--- FIM DAS OPERAÇÕES (POOL SERÁ FECHADO) ---")


# Ponto de entrada padrão
if __name__ == "__main__":
    main()