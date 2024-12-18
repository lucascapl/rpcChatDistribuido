
# Chat Distribuído com XML-RPC

Este é um sistema de chat distribuído utilizando o protocolo XML-RPC. O sistema é composto por três agentes principais: **Binder**, **Servidor** e **Cliente**. Cada um desempenha um papel fundamental para possibilitar a comunicação entre os usuários.

## Estrutura do Sistema

- **Binder (`binder.py`)**:
  - Atua como um registrador central de serviços.
  - Permite registrar e buscar serviços por nome, endereço IP e porta.
  - Sempre opera na porta fixa `5000`.

- **Servidor (`server.py`)**:
  - Gerencia usuários, salas de chat e mensagens.
  - Possui funcionalidades como:
    - Registro de usuários.
    - Criação e exclusão de salas de chat.
    - Envio e recebimento de mensagens.
  - Registra-se automaticamente no **Binder** como o serviço `ChatService`.

- **Cliente (`cliente.py`)**:
  - Permite que usuários interajam com o sistema de chat.
  - Funcionalidades incluem:
    - Registro de usuário.
    - Criação, entrada e saída de salas.
    - Envio e recebimento de mensagens.

## Pré-requisitos

1. **Python** (versão 3.6 ou superior).
2. As bibliotecas padrão do Python (`xmlrpc`, `threading`, `json`, etc.).
3. Permissões para executar scripts Python e criar arquivos no sistema.

## Estrutura de Diretórios

A estrutura do projeto deve ser organizada da seguinte maneira:

```
/rpcChatDistribuido
  ├── binder/
  │   └── binder.py
  ├── server/
  │   └── server.py
  ├── cliente/
  │   └── cliente.py
  ├── start.bat
  └── README.md
```

## Como Executar

### 1. Configurar o Ambiente

Certifique-se de que o Python está configurado no PATH do sistema operacional.

### 2. Iniciar o Sistema

Execute o arquivo `start.bat` para iniciar todos os componentes do sistema automaticamente.

O script:
- Inicia o **Binder**.
- Aguarda 2 segundos e inicia o **Servidor**.
- Aguarda mais 2 segundos e abre duas instâncias do **Cliente**.

### 3. Interagir com o Sistema

1. No terminal de cada cliente:
   - Registre-se com um nome de usuário **único**.
   - Crie ou entre em uma sala de chat.
   - Envie mensagens para outros usuários conectados.

2. No terminal do servidor, acompanhe as ações registradas no log (`chat_server.log`).

### Limpeza Automática

O sistema remove automaticamente salas de chat que estejam inativas por mais de 5 minutos.

## Logs

O servidor armazena logs no arquivo `chat_server.log`, registrando eventos como:
- Início do servidor.
- Registro de usuários.
- Criação e exclusão de salas.
- Mensagens enviadas.

## Extras

- Logging no arquivo chat_server.log
- Limpeza do console em alguns momentos para cooperar com a UX via console :)

## Licença

Este projeto foi desenvolvido como parte de um trabalho acadêmico para a disciplina de Sistemas Distribuídos na UERJ.
