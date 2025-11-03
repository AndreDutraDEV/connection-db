# app_orm.py

import psycopg
from sqlalchemy import create_engine, select, update, delete, String, Date, Integer, Enum, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from typing import List, Optional

# 1. DETALHES DA CONEXÃO
DB_URL = "postgresql+psycopg://admin:admin123@localhost:5432/faculdatabase"

# 2. SETUP DO ORM
# O Engine gerencia a conexão (similar ao Pool)
engine = create_engine(DB_URL, echo=False) # Mude echo=True para ver o SQL gerado

# A Sessão é o objeto que usamos para interagir com o banco
# (similar à 'conn' individual)
SessionLocal = sessionmaker(bind=engine)

# Classe Base para nossos "Models" (tabelas)
class Base(DeclarativeBase):
    pass

# 3. DEFINIÇÃO DOS MODELS (MAPEAMENTO TABELA -> CLASSE)
# Vamos mapear Pessoa, Curso e Aluno

class Pessoa(Base):
    __tablename__ = "pessoa" # Nome exato da tabela no SQL
    
    # Mapeia colunas para atributos da classe
    cpf: Mapped[str] = mapped_column(String(11), primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    data_nascimento: Mapped[Optional[Date]] = mapped_column(Date)
    
    # Relacionamento: Um 'Aluno' está ligado a esta 'Pessoa'
    # 'back_populates' faz o link bidirecional
    aluno: Mapped["Aluno"] = relationship(back_populates="pessoa")

class Curso(Base):
    __tablename__ = "curso"
    
    cod_mec: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    modalidade: Mapped[str] = mapped_column(Enum('Presencial', 'EAD', 'Híbrido', 'Semipresencial', name='modalidade_enum'))
    
    # Relacionamento: Um 'Curso' tem uma lista de 'Alunos'
    alunos: Mapped[List["Aluno"]] = relationship(back_populates="curso")

class Aluno(Base):
    __tablename__ = "aluno"
    
    matricula: Mapped[str] = mapped_column(String(20), primary_key=True)
    data_inicio: Mapped[Optional[Date]] = mapped_column(Date)
    
    # Chaves Estrangeiras (FK)
    cod_mec: Mapped[int] = mapped_column(ForeignKey("curso.cod_mec"))
    cpf: Mapped[str] = mapped_column(ForeignKey("pessoa.cpf"), unique=True)
    
    # Relacionamentos (a "mágica" do ORM)
    # Define os links com as classes Pessoa e Curso
    curso: Mapped["Curso"] = relationship(back_populates="alunos")
    pessoa: Mapped["Pessoa"] = relationship(back_populates="aluno")

    def __repr__(self):
        # Uma representação bonita para imprimir o objeto
        return f"<Aluno(matricula='{self.matricula}', nome='{self.pessoa.nome}')>"

# 4. FUNÇÕES DE EXEMPLO (OPERAÇÕES CRUD)

def criar_novo_aluno(session):
    """ Exemplo de INSERT """
    print("\n--- 1. Criando Novo Aluno (INSERT) ---")
    
    # 1. Cria os objetos Python
    # (CPFs e Matrículas devem ser únicos, use dados novos)
    nova_pessoa = Pessoa(
        cpf="99988877766",
        nome="Joana D'Arc",
        email="joana.orm@exemplo.com",
        data_nascimento="1412-01-06"
    )
    
    novo_aluno = Aluno(
        matricula="A0999",
        data_inicio="2025-01-01",
        cod_mec=1001, # Ciência da Computação
        pessoa=nova_pessoa # O ORM entende essa relação!
    )
    
    # 2. Adiciona à sessão (prepara para o 'commit')
    try:
        session.add(novo_aluno)
        
        # 3. "Commita" a transação (salva no banco)
        session.commit()
        print(f"  SUCESSO: Aluno '{nova_pessoa.nome}' criado.")
        
    except Exception as e:
        # Se o CPF/Matrícula já existir, o banco dará erro
        session.rollback()
        print(f"  FALHA: Erro ao criar aluno (talvez já exista). {e}")

def buscar_aluno_com_join(session, matricula):
    """ Exemplo de SELECT com JOIN automático """
    print(f"\n--- 2. Buscando Aluno '{matricula}' (SELECT + JOIN) ---")
    
    # Cria a query: SELECT * FROM aluno WHERE matricula = ...
    stmt = select(Aluno).where(Aluno.matricula == matricula)
    
    # Executa e pega o primeiro resultado (ou None)
    aluno = session.scalars(stmt).first()
    
    if aluno:
        print(f"  Encontrado: {aluno.matricula}")
        
        # --- A MÁGICA DO ORM ---
        # Não fizemos JOIN, mas o ORM busca os dados relacionados
        # quando acessamos os atributos. (Isso é chamado de "lazy loading")
        print(f"  Nome....: {aluno.pessoa.nome}") # Faz um SELECT em 'pessoa'
        print(f"  Email...: {aluno.pessoa.email}")
        print(f"  Curso...: {aluno.curso.nome}")   # Faz um SELECT em 'curso'
        print(f"  Modalide: {aluno.curso.modalidade}")
    else:
        print(f"  Aluno '{matricula}' não encontrado.")

def atualizar_email_aluno(session, matricula, novo_email):
    """ Exemplo de UPDATE """
    print(f"\n--- 3. Atualizando Email do Aluno '{matricula}' (UPDATE) ---")
    
    try:
        # 1. Busca o aluno (e sua pessoa)
        #    'join(Pessoa)' faz o JOIN explicitamente (Eager Loading)
        stmt = select(Aluno).join(Pessoa).where(Aluno.matricula == matricula)
        aluno = session.scalars(stmt).first()
        
        if not aluno:
            print(f"  AVISO: Aluno '{matricula}' não encontrado.")
            return

        # 2. Modifica o atributo do objeto Python
        print(f"  Email antigo: {aluno.pessoa.email}")
        aluno.pessoa.email = novo_email
        
        # 3. Commita a transação (o ORM detecta a mudança e gera o UPDATE)
        session.commit()
        print(f"  Email novo..: {aluno.pessoa.email}")
        print("  SUCESSO: Email atualizado.")
        
    except Exception as e:
        session.rollback()
        print(f"  FALHA: Erro ao atualizar (talvez o email já exista). {e}")

def deletar_aluno(session, matricula):
    """ Exemplo de DELETE """
    print(f"\n--- 4. Deletando Aluno '{matricula}' (DELETE) ---")
    
    try:
        # 1. Busca o aluno que queremos deletar
        aluno = session.get(Aluno, matricula) # .get() busca pela Primary Key
        
        if not aluno:
            print(f"  AVISO: Aluno '{matricula}' não encontrado.")
            return

        # 2. Deleta o objeto da sessão
        # (O ORM cuidará das FKs, se configurado, mas
        #  a 'pessoa' associada NÃO será deletada aqui)
        session.delete(aluno)
        
        # 3. Commita
        session.commit()
        print(f"  SUCESSO: Aluno '{matricula}' deletado.")
        
        # (Opcional: deletar a pessoa também)
        # stmt_pessoa = delete(Pessoa).where(Pessoa.cpf == aluno.cpf)
        # session.execute(stmt_pessoa)
        # session.commit()
        # print(f"  SUCESSO: Pessoa CPF '{aluno.cpf}' deletada.")
        
    except Exception as e:
        session.rollback()
        print(f"  FALHA: Erro ao deletar aluno. {e}")


def main():
    # 'with' garante que a sessão será fechada no final
    with SessionLocal() as session:
        
        # Vamos rodar os exemplos
        
        # 1. INSERT (Descomente para rodar)
        # criar_novo_aluno(session) 
        
        # 2. SELECT
        buscar_aluno_com_join(session, 'A0001') # Aluno do seu init.sql
        
        # 3. UPDATE
        # atualizar_email_aluno(session, 'A0001', 'rafael.martins.novo@exemplo.com')
        
        # 4. DELETE (Descomente o aluno criado para poder deletar)
        # deletar_aluno(session, 'A0999')

    print("\n--- FIM DAS OPERAÇÕES (SESSÃO FECHADA) ---")
    
if __name__ == "__main__":
    # Esta linha é opcional, mas útil se você rodar este script
    # pela primeira vez, para que o ORM "conheça" os ENUMs
    # customizados (modalidade_enum, etc.) do seu banco.
    Base.metadata.create_all(engine) 
    
    main()