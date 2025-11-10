import mysql.connector
from mysql.connector import errorcode
from datetime import datetime

# --- 1. Classe de Conexão com o Banco ---
# Gerencia a conexão, execução de queries e fetching de dados.

class Database:
    """Classe para gerenciar a conexão com o banco de dados MySQL."""
    
    def __init__(self, host, user, password, database):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.connection = None

    def connect(self):
        """Estabelece a conexão com o banco de dados."""
        try:
            self.connection = mysql.connector.connect(**self.config)
            print("Conexão com o MySQL estabelecida com sucesso.")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Erro: Usuário ou senha do banco de dados inválidos.")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print(f"Erro: O banco de dados '{self.config['database']}' não existe.")
            else:
                print(f"Erro ao conectar ao MySQL: {err}")
            return None
        return self.connection

    def disconnect(self):
        """Fecha a conexão com o banco de dados."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexão com o MySQL fechada.")

    def execute_query(self, query, params=None):
        """Executa uma query (INSERT, UPDATE, DELETE) e retorna o ID do último registro inserido."""
        conn = self.connect()
        if not conn:
            return None
            
        cursor = conn.cursor()
        last_id = None
        try:
            cursor.execute(query, params)
            conn.commit()
            last_id = cursor.lastrowid
            print("Query executada com sucesso.")
        except mysql.connector.Error as err:
            print(f"Erro ao executar query: {err}")
            conn.rollback()
        finally:
            cursor.close()
            self.disconnect()
        return last_id

    def fetch_query(self, query, params=None):
        """Executa uma query (SELECT) e retorna os resultados."""
        conn = self.connect()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True) # Retorna resultados como dicionários
        results = None
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
            print("Fetch realizado com sucesso.")
        except mysql.connector.Error as err:
            print(f"Erro ao buscar dados: {err}")
        finally:
            cursor.close()
            self.disconnect()
        return results

# --- 2. Classes de Modelo (Representação dos Dados) ---
# Classes simples para armazenar os dados das entidades.

class Pessoa:
    def __init__(self, cpf, nome, telefone):
        self.cpf = cpf
        self.nome = nome
        self.telefone = telefone

class Aluno(Pessoa):
    def __init__(self, cpf, nome, telefone, numero_matricula):
        super().__init__(cpf, nome, telefone)
        self.numero_matricula = numero_matricula

class Professor(Pessoa):
    def __init__(self, cpf, nome, telefone, siape, departamento):
        super().__init__(cpf, nome, telefone)
        self.siape = siape
        self.departamento = departamento

class Sala:
    def __init__(self, id_sala, numero_sala, status, id_bloco):
        self.id_sala = id_sala
        self.numero_sala = numero_sala
        self.status = status
        self.id_bloco = id_bloco

class SalaDeAula(Sala):
     def __init__(self, id_sala, numero_sala, status, id_bloco, capacidade_alunos):
        super().__init__(id_sala, numero_sala, status, id_bloco)
        self.capacidade_alunos = capacidade_alunos

# (Outras classes de modelo como Bloco, Chave, Funcionario, etc. podem ser criadas da mesma forma)


# --- 3. Classe Principal da Aplicação (Lógica de Negócio) ---

class KeyControlApp:
    """Classe que contém a lógica de negócio para o controle de chaves."""
    
    def __init__(self, db_instance):
        self.db = db_instance

    # --- Métodos de Cadastro ---

    def add_bloco(self, nome_bloco):
        """Adiciona um novo bloco."""
        query = "INSERT INTO Bloco (nome_bloco) VALUES (%s)"
        return self.db.execute_query(query, (nome_bloco,))

    def add_pessoa(self, cpf, nome, telefone):
        """Adiciona uma nova pessoa (base)."""
        query = "INSERT INTO Pessoa (cpf, nome, telefone) VALUES (%s, %s, %s)"
        # execute_query retorna o ID, mas para Pessoa o PK é CPF, então só confirmamos
        self.db.execute_query(query, (cpf, nome, telefone))
        return cpf

    def add_aluno(self, cpf, nome, telefone, numero_matricula):
        """Adiciona um novo aluno (Pessoa + Aluno)."""
        self.add_pessoa(cpf, nome, telefone) # Primeiro insere na superclasse
        query = "INSERT INTO Aluno (cpf, numero_matricula) VALUES (%s, %s)"
        self.db.execute_query(query, (cpf, numero_matricula))
        print(f"Aluno {nome} (Mat. {numero_matricula}) cadastrado.")
        return cpf

    def add_professor(self, cpf, nome, telefone, siape, departamento):
        """Adiciona um novo professor (Pessoa + Professor)."""
        self.add_pessoa(cpf, nome, telefone)
        query = "INSERT INTO Professor (cpf, siape, departamento) VALUES (%s, %s, %s)"
        self.db.execute_query(query, (cpf, siape, departamento))
        print(f"Professor {nome} (SIAPE {siape}) cadastrado.")
        return cpf
        
    def add_sala_aula(self, numero_sala, status, id_bloco, capacidade):
        """Adiciona uma nova Sala de Aula (Sala + Sala_de_Aula)."""
        # 1. Insere na superclasse Sala
        query_sala = "INSERT INTO Sala (numero_sala, status, id_bloco) VALUES (%s, %s, %s)"
        id_sala = self.db.execute_query(query_sala, (numero_sala, status, id_bloco))
        
        if id_sala:
            # 2. Insere na especialização Sala_de_Aula
            query_aula = "INSERT INTO Sala_de_Aula (id_sala, capacidade_alunos) VALUES (%s, %s)"
            self.db.execute_query(query_aula, (id_sala, capacidade))
            print(f"Sala de Aula {numero_sala} (ID: {id_sala}) cadastrada no bloco {id_bloco}.")
            return id_sala
        return None

    def add_chave(self, codigo_visual, id_sala):
        """Adiciona uma nova chave e a associa a uma sala."""
        query = "INSERT INTO Chave (codigo_visual, id_sala) VALUES (%s, %s)"
        return self.db.execute_query(query, (codigo_visual, id_sala))

    def add_atendente(self, nome, turno):
        """Adiciona um novo funcionário Atendente."""
        query_func = "INSERT INTO Funcionario (nome_funcionario) VALUES (%s)"
        id_func = self.db.execute_query(query_func, (nome,))
        
        if id_func:
            query_atend = "INSERT INTO Atendente (id_funcionario, turno) VALUES (%s, %s)"
            self.db.execute_query(query_atend, (id_func, turno))
            print(f"Atendente {nome} (ID: {id_func}) cadastrado no turno {turno}.")
            return id_func
        return None

    # --- Métodos de Empréstimo ---

    def registrar_emprestimo(self, cpf_pessoa, id_chave, id_funcionario_retirada):
        """Registra a retirada de uma chave."""
        query = """
        INSERT INTO Emprestimo 
        (data_hora_retirada, cpf_pessoa, id_chave, id_funcionario_retirada)
        VALUES (%s, %s, %s, %s)
        """
        # Usamos NOW() do Python para registrar a hora exata
        data_hora = datetime.now()
        params = (data_hora, cpf_pessoa, id_chave, id_funcionario_retirada)
        
        id_emprestimo = self.db.execute_query(query, params)
        if id_emprestimo:
            print(f"Empréstimo {id_emprestimo} registrado para CPF {cpf_pessoa} às {data_hora}.")
            
            # Opcional: Atualizar status da sala para 'Indisponível'
            # (Isso exigiria uma query de UPDATE na tabela Sala, buscando pelo id_chave)
            
        return id_emprestimo

    def registrar_devolucao(self, id_emprestimo, id_funcionario_devolucao):
        """Registra a devolução de uma chave."""
        query = """
        UPDATE Emprestimo
        SET data_hora_devolucao = %s, id_funcionario_devolucao = %s
        WHERE id_emprestimo = %s AND data_hora_devolucao IS NULL
        """
        data_hora = datetime.now()
        params = (data_hora, id_funcionario_devolucao, id_emprestimo)
        
        # execute_query não retorna ID em updates, mas podemos verificar se funcionou
        # (Para um sistema real, verificaríamos o 'rowcount' no cursor)
        self.db.execute_query(query, params)
        print(f"Devolução do empréstimo {id_emprestimo} registrada às {data_hora}.")
        
        # Opcional: Atualizar status da sala para 'Disponível'

    # --- Métodos de Consulta ---

    def get_emprestimos_ativos(self):
        """Retorna uma lista de todos os empréstimos que ainda não foram devolvidos."""
        query = """
        SELECT e.*, p.nome AS nome_pessoa, c.codigo_visual, s.numero_sala
        FROM Emprestimo e
        JOIN Pessoa p ON e.cpf_pessoa = p.cpf
        JOIN Chave c ON e.id_chave = c.id_chave
        JOIN Sala s ON c.id_sala = s.id_sala
        WHERE e.data_hora_devolucao IS NULL
        ORDER BY e.data_hora_retirada ASC
        """
        return self.db.fetch_query(query)

    def get_sala_por_numero(self, numero_sala, id_bloco):
        """Encontra uma sala pelo seu número e bloco."""
        query = "SELECT * FROM Sala WHERE numero_sala = %s AND id_bloco = %s"
        return self.db.fetch_query(query, (numero_sala, id_bloco))


# --- 4. Exemplo de Uso ---

if __name__ == "__main__":
    # 
    # **IMPORTANTE**: Altere com suas credenciais do MySQL
    # 
    db_config = {
        'host': 'localhost',
        'user': 'root',         # Usuário padrão do MySQL
        'password': 'root', # **ALTERE AQUI**
        'database': 'controle_chaves_campus'
    }

    # 1. Inicializa o banco de dados e a aplicação
    db = Database(db_config['host'], db_config['user'], db_config['password'], db_config['database'])
    app = KeyControlApp(db)

    print("--- Iniciando Teste da Aplicação de Controle de Chaves ---")

    try:
        # 2. Cadastros Iniciais
        print("\n[+] Cadastrando Bloco, Funcionário, Pessoa e Sala...")
        id_bloco_A = app.add_bloco("Bloco A")
        id_atendente_Joao = app.add_atendente("João da Portaria", "Manhã")
        cpf_aluno_Maria = app.add_aluno("11122233344", "Maria Silva", "55999887766", "20251001")
        id_sala_101 = app.add_sala_aula("101", "Disponível", id_bloco_A, 50)
        
        # 3. Cadastrar uma chave para a sala
        print("\n[+] Cadastrando Chave...")
        id_chave_101 = app.add_chave("CH-A-101", id_sala_101)
        
        if not all([id_bloco_A, id_atendente_Joao, cpf_aluno_Maria, id_sala_101, id_chave_101]):
             raise Exception("Falha em um dos cadastros iniciais. Verifique o banco e as credenciais.")

        print("\n--- Cadastros básicos concluídos ---")
        
        # 4. Simular Empréstimo
        print(f"\n[>] Registrando empréstimo da chave {id_chave_101} para {cpf_aluno_Maria} por {id_atendente_Joao}...")
        id_emp = app.registrar_emprestimo(cpf_aluno_Maria, id_chave_101, id_atendente_Joao)
        
        # 5. Consultar Empréstimos Ativos
        print("\n[*] Consultando empréstimos ativos...")
        ativos = app.get_emprestimos_ativos()
        if ativos:
            print(f"Total de {len(ativos)} empréstimos ativos:")
            for emprestimo in ativos:
                print(f"  - ID: {emprestimo['id_emprestimo']}, Pessoa: {emprestimo['nome_pessoa']}, Sala: {emprestimo['numero_sala']}, Retirada: {emprestimo['data_hora_retirada']}")
        
        # 6. Simular Devolução
        print(f"\n[<] Registrando devolução do empréstimo {id_emp}...")
        app.registrar_devolucao(id_emp, id_atendente_Joao)

        # 7. Verificar se o empréstimo foi finalizado
        print("\n[*] Consultando empréstimos ativos novamente...")
        ativos_final = app.get_emprestimos_ativos()
        if not ativos_final:
            print("  - Nenhum empréstimo ativo. Devolução bem-sucedida.")
        else:
            print(f"  - {len(ativos_final)} empréstimos ainda ativos.")
            
    except Exception as e:
        print(f"\n--- Ocorreu um erro durante a execução ---")
        print(f"Erro: {e}")
        print("Verifique se o servidor MySQL está rodando e se as credenciais em 'db_config' estão corretas.")

    print("\n--- Teste da Aplicação Finalizado ---")