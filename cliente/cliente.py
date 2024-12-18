import xmlrpc.client, threading, time, sys, os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import limpar_console

class ClienteChat:
    def __init__(self, enderecoBinder):
        self.binder = xmlrpc.client.ServerProxy(enderecoBinder, allow_none=True)
        self.servidor = None
        self.nomeUsuario = None
        self.salaAtual = None
        self.trava = threading.Lock()  # Trava para sincronização
        self.ultimoTimestamp = None  # Timestamp da última mensagem exibida
        self.ignorarPrimeiroFetch = False  # Controla se o primeiro fetch deve ser ignorado

    def descobrir_servico(self, nomeProcedimento):
        # Descobre o serviço através do Binder
        sucesso, servico = self.binder.buscar_procedimento(nomeProcedimento)
        if not sucesso:
            print(servico)
            return False
        enderecoServidor = f"http://{servico['endereco']}:{servico['porta']}/"
        self.servidor = xmlrpc.client.ServerProxy(enderecoServidor, allow_none=True)
        return True

    def registrar_usuario(self):
        # Registra o usuário com um nome único
        while True:
            nomeUsuario = input("Digite seu nome de usuário: ").strip()
            sucesso, mensagem = self.servidor.registrar_usuario(nomeUsuario)
            print(mensagem)
            if sucesso:
                self.nomeUsuario = nomeUsuario
                break

    def criar_sala(self):
        limpar_console()
        # Cria uma nova sala com um nome único
        nomeSala = input("Digite o nome da sala: ").strip()
        sucesso, mensagem = self.servidor.criar_sala(nomeSala)
        print(mensagem)

    def entrar_na_sala(self):
        # Entra em uma sala existente
        nomeSala = input("Digite o nome da sala: ").strip()
        sucesso, resposta = self.servidor.entrar_na_sala(self.nomeUsuario, nomeSala)
        if sucesso:
            print(f"Sucesso ao entrar na sala {nomeSala}!")
            self.salaAtual = nomeSala
            self.ignorarPrimeiroFetch = True
            print("\nUsuários conectados:")
            print(", ".join(resposta["usuarios"]))
            print("\nÚltimas 50 mensagens:")
            for msg in resposta["mensagens"]:
                print(self.formatar_mensagem(msg))
            if resposta["mensagens"]:
                self.ultimoTimestamp = resposta["mensagens"][-1]["timestamp"]
        else:
            print(resposta)

    def sair_da_sala(self):
        # Sai da sala atual
        if not self.salaAtual:
            print("Você não está em nenhuma sala.")
            return
        with self.trava:
            try:
                sucesso, mensagem = self.servidor.sair_da_sala(self.nomeUsuario)
                print(mensagem)
                if sucesso:
                    self.salaAtual = None
                    self.ultimoTimestamp = None
            except Exception as e:
                print(f"Erro ao tentar sair da sala: {e}")

    def listar_salas(self):
        # Lista todas as salas disponíveis
        try:
            limpar_console()
            sucesso, salas = self.servidor.listar_salas()
            if sucesso:
                print("Salas disponíveis:")
                for sala in salas:
                    print(f"- {sala}")
            else:
                print(salas)
        except Exception as e:
            print(f"Erro ao listar salas: {e}")

    def listar_usuarios(self):
        # Lista os usuários na sala atual
        if not self.salaAtual:
            print("Você precisa primeiro entrar em uma sala.")
            return
        with self.trava:
            try:
                sucesso, usuarios = self.servidor.listar_usuarios(self.salaAtual)
                if sucesso:
                    print("Usuários nesta sala:")
                    for usuario in usuarios:
                        print(f"- {usuario}")
                else:
                    print(usuarios)
            except Exception as e:
                print(f"Erro ao listar usuários da sala: {e}")

    def enviar_mensagem(self):
        # Envia uma mensagem na sala atual
        if not self.salaAtual:
            print("Você precisa primeiro entrar em uma sala.")
            return
        destinatario = input("Digite o username do destinatário ou tecle [enter] para escrever publicamente na sala: ").strip()
        mensagem = input("Digite sua mensagem: ").strip()
        destinatario = None if destinatario == "" else destinatario

        with self.trava:
            try:
                sucesso, resposta = self.servidor.enviar_mensagem(self.nomeUsuario, self.salaAtual, mensagem, destinatario)
                if sucesso:
                    print("Mensagem enviada.")
                else:
                    print(resposta)
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")

    def buscar_mensagens(self):
        # Busca mensagens periodicamente
        while True:
            with self.trava:
                if not self.salaAtual:
                    time.sleep(2)
                    continue

                if self.ignorarPrimeiroFetch:
                    self.ignorarPrimeiroFetch = False
                    time.sleep(2)
                    continue

                try:
                    sucesso, mensagens = self.servidor.receber_mensagens(self.nomeUsuario, self.salaAtual)
                    if sucesso:
                        novasMensagens = [
                            msg for msg in mensagens
                            if self.ultimoTimestamp is None or msg["timestamp"] > self.ultimoTimestamp
                        ]
                        if novasMensagens:
                            self.ultimoTimestamp = novasMensagens[-1]["timestamp"]
                            for msg in novasMensagens:
                                print(self.formatar_mensagem(msg))
                except Exception as e:
                    print(f"Erro ao atualizar as mensagens: {e}")
            time.sleep(2)

    def formatar_mensagem(self, mensagem):
        # Formata uma mensagem para exibição
        timestamp_rpc = mensagem["timestamp"]
        timestamp = datetime.strptime(str(timestamp_rpc), "%Y%m%dT%H:%M:%S")
        origem = mensagem["origem"]
        conteudo = mensagem["conteudo"]
        destino = mensagem.get("destino", "todos")
        if destino == "todos":
            return f"\n[{timestamp}] {origem}: {conteudo}"
        else:
            return f"\n[{timestamp}] {origem} -> {destino}: {conteudo}"

    def executar(self):
        # Executa o cliente
        print("Procurando serviço de chat...")
        if not self.descobrir_servico("ChatService"):
            return
        self.registrar_usuario()

        threading.Thread(target=self.buscar_mensagens, daemon=True).start()

        while True:
            if self.salaAtual:
                print("\nSala atual:", self.salaAtual)
                print("Comandos:")
                print("1. Enviar mensagem")
                print("2. Sair da sala")
                print("3. Listar usuários")
                print("4. Encerrar")

                opcao = input("Escolha uma opção: ").strip()
                if opcao == "1":
                    self.enviar_mensagem()
                elif opcao == "2":
                    self.sair_da_sala()
                elif opcao == "3":
                    self.listar_usuarios()
                elif opcao == "4":
                    print("Encerrando...")
                    break
                else:
                    print("Opção inválida. Escolha novamente.")
            else:
                print("\n--- Atualmente você não está em nenhuma sala ---")
                print("Comandos:")
                print("1. Criar sala")
                print("2. Entrar em uma sala")
                print("3. Listar salas")
                print("4. Encerrar")

                opcao = input("Escolha uma opção: ").strip()
                if opcao == "1":
                    self.criar_sala()
                elif opcao == "2":
                    self.entrar_na_sala()
                elif opcao == "3":
                    self.listar_salas()
                elif opcao == "4":
                    print("Encerrando...")
                    break
                else:
                    print("Opção inválida. Escolha novamente.")

if __name__ == "__main__":
    # Endereço do Binder (porta fixa)
    enderecoBinder = "http://localhost:5000/"
    cliente = ClienteChat(enderecoBinder)
    cliente.executar()
