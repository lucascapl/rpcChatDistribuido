from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

class Binder:
    def __init__(self):
        # armazena os procedimentos no formato {nome_do_procedimento: {"endereco": endereco, "porta": porta}}
        self.procedures = {}

    def registrar_procedimento(self, nomeProcedimento, endereco, porta):
        # registra um procedimento remoto com um nome, endereço IP e porta
        if nomeProcedimento in self.procedures:
            return False, f"Procedimento '{nomeProcedimento}' já está registrado."
        self.procedures[nomeProcedimento] = {"endereco": endereco, "porta": porta}
        return True, f"Procedimento '{nomeProcedimento}' registrado com sucesso no endereço {endereco}:{porta}."

    def buscar_procedimento(self, nomeProcedimento):
        # Retorna o endereço e a porta de um procedimento remoto pelo nome
        if nomeProcedimento not in self.procedures:
            return False, f"Procedimento '{nomeProcedimento}' não encontrado."
        return True, self.procedures[nomeProcedimento]

if __name__ == "__main__":
    # O Binder será executado na porta fixa 5000
    portaBinder = 5000
    servidor = SimpleXMLRPCServer(("localhost", portaBinder), requestHandler=SimpleXMLRPCRequestHandler)
    servidor.register_instance(Binder())
    print(f"Binder está rodando na porta {portaBinder}...")
    servidor.serve_forever()
