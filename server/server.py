import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from datetime import datetime, timedelta
import threading, json, logging

# Configuração do logging
try:
    logging.basicConfig(
        filename="chat_server.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info("Iniciando o servidor de chat...")
except Exception as e:
    print(f"Erro ao configurar o logging: {e}")

class ServidorChat:
    def __init__(self):
        try:
            # Estruturas de dados para gerenciar usuários, salas e inatividade
            self.usuarios = {}  # {nomeUsuario: nomeSala}
            self.salas = {}  # {nomeSala: {"usuarios": [], "mensagens": []}}
            self.salasInativas = {}  # {nomeSala: timestampUltimaAtividade}
            self.arquivoUsuarios = "usuarios.json"  # Nome do arquivo JSON
            self.trava = threading.Lock()  # Inicializa a trava
            self.limpar_arquivo_usuarios()  # Esvazia o arquivo ao iniciar
            logging.info("ServidorChat: Inicializando estruturas de dados...")
        except Exception as e:
            logging.critical(f"Erro ao inicializar servidor: {str(e)}")

    def limpar_arquivo_usuarios(self):
        # Esvazia o arquivo JSON ao iniciar o servidor
        with open(self.arquivoUsuarios, "w") as arquivo:
            json.dump([], arquivo)

    def carregar_usuarios(self):
        # Carrega a lista de usuários do arquivo JSON
        try:
            with open(self.arquivoUsuarios, "r") as arquivo:
                return json.load(arquivo)
        except FileNotFoundError:
            return []

    def salvar_usuario(self, nomeUsuario):
        # Adiciona um novo usuário ao arquivo JSON
        usuarios = self.carregar_usuarios()
        usuarios.append(nomeUsuario)
        with open(self.arquivoUsuarios, "w") as arquivo:
            json.dump(usuarios, arquivo)

    # --- Gerenciamento de Usuários ---
    def registrar_usuario(self, nomeUsuario):
        # Registra um novo usuário, verificando se já existe
        if nomeUsuario in self.carregar_usuarios():
            logging.warning(f"Tentativa de registro de nome duplicado: {nomeUsuario}")
            return False, "Nome de usuário já está em uso."
        self.salvar_usuario(nomeUsuario)
        self.usuarios[nomeUsuario] = None
        logging.info(f"Usuário registrado: {nomeUsuario}")
        return True, "Usuário registrado com sucesso."

    # --- Gerenciamento de Salas ---
    def criar_sala(self, nomeSala):
        # Cria uma nova sala
        with self.trava:
            if nomeSala in self.salas:
                logging.warning(f"Tentativa de criação de sala duplicada: {nomeSala}")
                return False, "O nome da sala já existe."
            self.salas[nomeSala] = {"usuarios": [], "mensagens": []}
            logging.info(f"Sala criada: {nomeSala}")
            return True, f"Sala '{nomeSala}' criada com sucesso."

    def entrar_na_sala(self, nomeUsuario, nomeSala):
        # Faz um usuário entrar em uma sala
        with self.trava:
            if nomeUsuario not in self.usuarios:
                return False, "Usuário não registrado."
            if nomeSala not in self.salas:
                return False, "Sala não encontrada."

            # Remove o usuário de outra sala, se necessário
            if self.usuarios[nomeUsuario]:
                self.sair_da_sala(nomeUsuario)

            # Adiciona o usuário à sala
            self.salas[nomeSala]["usuarios"].append(nomeUsuario)
            self.usuarios[nomeUsuario] = nomeSala
            self.salasInativas.pop(nomeSala, None)  # Remove da lista de inatividade
            self.salas[nomeSala]["mensagens"].append({
                "tipo": "broadcast",
                "origem": "SERVER",
                "conteudo": f"{nomeUsuario} entrou na sala.",
                "timestamp": datetime.now()
            })
            logging.info(f"Usuário '{nomeUsuario}' entrou na sala '{nomeSala}'.")

            # Retorna os dados da sala
            usuariosNaSala = self.salas[nomeSala]["usuarios"]
            mensagens = self.salas[nomeSala]["mensagens"][-50:]  # Últimas 50 mensagens
            return True, {"usuarios": usuariosNaSala, "mensagens": mensagens}

    def sair_da_sala(self, nomeUsuario):
        # Faz um usuário sair da sala atual
        with self.trava:
            if nomeUsuario not in self.usuarios or not self.usuarios[nomeUsuario]:
                return False, "Usuário não está em nenhuma sala."

            nomeSala = self.usuarios[nomeUsuario]
            self.salas[nomeSala]["usuarios"].remove(nomeUsuario)
            self.usuarios[nomeUsuario] = None

            # Adiciona uma mensagem de saída
            self.salas[nomeSala]["mensagens"].append({
                "tipo": "broadcast",
                "origem": "SERVER",
                "conteudo": f"{nomeUsuario} saiu da sala.",
                "timestamp": datetime.now()
            })
            logging.info(f"Usuário '{nomeUsuario}' saiu da sala '{nomeSala}'.")

            # Marca a sala para remoção se estiver vazia
            if not self.salas[nomeSala]["usuarios"]:
                self.salasInativas[nomeSala] = datetime.now()

            return True, f"Usuário '{nomeUsuario}' saiu da sala '{nomeSala}'."

    # --- Mensagens ---
    def enviar_mensagem(self, nomeUsuario, nomeSala, mensagem, destinatario=None):
        # Envia uma mensagem para a sala ou um destinatário específico
        with self.trava:
            if nomeUsuario not in self.usuarios or self.usuarios[nomeUsuario] != nomeSala:
                return False, "Usuário não está na sala especificada."

            mensagemDados = {
                "tipo": "unicast" if destinatario else "broadcast",
                "origem": nomeUsuario,
                "conteudo": mensagem,
                "timestamp": datetime.now()
            }

            if destinatario:
                if destinatario not in self.salas[nomeSala]["usuarios"]:
                    return False, "Destinatário não está na mesma sala."
                mensagemDados["destino"] = destinatario
            else:
                mensagemDados["destino"] = "todos"

            self.salas[nomeSala]["mensagens"].append(mensagemDados)
            logging.info(f"Mensagem enviada por '{nomeUsuario}' na sala '{nomeSala}'.")

            return True, "Mensagem enviada com sucesso."

    def receber_mensagens(self, nomeUsuario, nomeSala):
        # Retorna mensagens da sala para o usuário
        with self.trava:
            if nomeUsuario not in self.usuarios or self.usuarios[nomeUsuario] != nomeSala:
                return False, "Usuário não está na sala especificada."

            mensagens = [
                msg for msg in self.salas[nomeSala]["mensagens"]
                if msg["tipo"] == "broadcast" or msg.get("destino") == nomeUsuario
            ]
            return True, mensagens

    # --- Listagem de Salas e Usuários ---
    def listar_salas(self):
        # Retorna a lista de salas disponíveis
        with self.trava:
            return True, list(self.salas.keys())

    def listar_usuarios(self, nomeSala):
        # Retorna a lista de usuários de uma sala específica
        with self.trava:
            if nomeSala not in self.salas:
                return False, "Sala não encontrada."
            return True, self.salas[nomeSala]["usuarios"]

    # --- Remoção de Salas Inativas ---
    def limpar_salas_inativas(self):
        # Remove salas sem usuários após 5 minutos de inatividade
        while True:
            with self.trava:
                agora = datetime.now()
                for sala, ultimaAtividade in list(self.salasInativas.items()):
                    if agora - ultimaAtividade > timedelta(minutes=1):
                        del self.salas[sala]
                        del self.salasInativas[sala]
                        logging.info(f"Sala '{sala}' removida por inatividade.")
            threading.Event().wait(60)  # Espera 60 segundos antes da próxima verificação


if __name__ == "__main__":
    # Conecta ao Binder
    binder = xmlrpc.client.ServerProxy("http://localhost:5000/")
    nomeProcedimento = "ChatService"
    endereco, porta = "localhost", 8001

    # Registra no Binder
    sucesso, mensagem = binder.registrar_procedimento(nomeProcedimento, endereco, porta)
    logging.info(mensagem)
    print(mensagem)

    if sucesso:
        # Inicia o servidor RPC
        servidor = SimpleXMLRPCServer((endereco, porta), requestHandler=SimpleXMLRPCRequestHandler, allow_none=True)
        servidor.register_instance(ServidorChat())

        # Inicia a thread de limpeza de salas inativas
        threadLimpeza = threading.Thread(target=servidor.instance.limpar_salas_inativas, daemon=True)
        threadLimpeza.start()

        logging.info(f"Servidor de chat rodando em {endereco}:{porta}...")
        print(f"Servidor de chat rodando em {endereco}:{porta}...")
        servidor.serve_forever()
