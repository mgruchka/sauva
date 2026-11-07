# SAÚVAbeta

<img width="190" height="144" alt="sauva-logo" src="https://github.com/user-attachments/assets/230738ba-a616-45ad-8907-6a445592a525" />

O SAÚVA organiza documentos de saúde e converte textos em registros FHIR. Para experimentar, você pode abrir um prontuário, uma receita, um manuscrito e um exame de imagem usando os quatro exemplos do repositório. A demonstração funciona com PostgreSQL local e dispensa chave de API. Para converter **novos documentos de texto** com Gemini, configure a chave no passo 5.

Esse repositório contém o protótipo desenvolvido para o III Hackathon Saúde HCFMUSP de 2026, e é, portanto, uma versão Beta que serve como prova de conceito inicial para o SAÚVA. Convidamos você, também, a rodá-lo e nos dar a sua opinião!

## 1. Instale os pré-requisitos

Instale Git, Python **3.13** e PostgreSQL (a equipe usou PostgreSQL 18). No Windows, inclua o servidor e o SQL Shell (psql) na instalação do PostgreSQL. Guarde a senha de administrador e a porta escolhida, normalmente 5432. [Git](https://git-scm.com/downloads) · [Python](https://www.python.org/downloads/) · [PostgreSQL](https://www.postgresql.org/download/)

## 2. Clone o projeto

O repositório é público. Qualquer colega pode baixar a branch padrão `main` por HTTPS, inclusive sem conta no GitHub. Abra o PowerShell no Windows ou um terminal no macOS/Linux e execute:

```sh
git clone https://github.com/mgruchka/sauva.git
cd sauva
```

Execute os próximos comandos a partir dessa pasta, onde está o arquivo `requirements.txt`.

## 3. Prepare o Python e o arquivo de configuração

**Windows (PowerShell)**

```powershell
py -3.13 -m venv .venv
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

**macOS ou Linux**

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

## 4. Crie o banco local

Com o servidor PostgreSQL iniciado, conecte-se ao banco `postgres` usando uma conta administradora. No Windows, abra **SQL Shell (psql)** pelo menu Iniciar. Aceite os valores locais de servidor, banco e porta e entre como `postgres` com a senha da instalação. No macOS/Linux, abra `psql -d postgres` com a conta administradora da instalação (em instalações Linux com autenticação pelo usuário do sistema, use `sudo -u postgres psql`).

No prompt do **psql**, execute uma linha por vez. O comando `\password` pede que você escolha a senha de **sauva_app**, o usuário que o aplicativo usará para acessar o banco.

```text
CREATE ROLE sauva_app LOGIN;
\password sauva_app
CREATE DATABASE sauva OWNER sauva_app;
\q
```

Se estiver retomando uma instalação existente, use `\du` e `\l` no psql para conferir o usuário e o banco antes de criar qualquer um deles.

## 5. Defina as senhas e, se necessário, a chave Gemini

Abra o arquivo **`.env` na raiz do projeto** em seu editor (no Windows, `notepad .env`). Substitua os três marcadores abaixo pelos valores locais. O arquivo contém segredos e deve ficar apenas no seu computador.

```dotenv
DATABASE_URL=postgresql+psycopg://sauva_app:SENHA_DO_BANCO@127.0.0.1:5432/sauva
APP_ORIGIN=http://127.0.0.1:8000
SESSION_COOKIE_SECURE=false

DEMO_OWNER_PASSWORD="ESCOLHA_A_SENHA_DA_CONTA_1"
DEMO_RECIPIENT_PASSWORD="ESCOLHA_A_SENHA_DA_CONTA_2"

GEMINI_API_KEY=
GEMINI_MODEL=
ENABLE_REAL_GOOGLE=false
FHIR_PROMPT_APPROVED=false
```

| Variável | O que preencher |
| --- | --- |
| `DATABASE_URL` | Use a senha definida com `\password sauva_app` no lugar de `SENHA_DO_BANCO`. Ajuste a porta se necessário. Na parte da senha da URL, codifique caracteres reservados (por exemplo, `@` vira `%40` e `#` vira `%23`). |
| `DEMO_OWNER_PASSWORD` | Escolha a senha para entrar na interface como **demo1@sauva.example**. Esta conta receberá os exemplos. |
| `DEMO_RECIPIENT_PASSWORD` | Escolha outra senha para **demo2@sauva.example**. Use esta conta para receber um documento compartilhado. |

**Para converter novos PDFs ou JPEGs de texto:** cole em `GEMINI_API_KEY` a chave que Marcos enviará separadamente. Em `GEMINI_MODEL`, informe o **ID do modelo Gemini** disponível para essa chave. Nome, ID e número do projeto Google são campos diferentes. Para a demonstração com dados fictícios, defina `ENABLE_REAL_GOOGLE=true` e `FHIR_PROMPT_APPROVED=true`. Salve o arquivo e reinicie o servidor se ele já estiver rodando. Esse fluxo envia texto ou arquivo ao Gemini e pode fazer até duas chamadas por documento. Use dados sintéticos.

## 6. Crie as tabelas, as contas e os exemplos

No mesmo terminal do passo 3, execute na ordem abaixo. No **PowerShell**:

```powershell
& $py -m alembic upgrade head
& $py -m app.seed
& $py scripts/import_demo_documents.py
```

No **macOS/Linux**, com o ambiente virtual ativo:

```sh
python -m alembic upgrade head
python -m app.seed
python scripts/import_demo_documents.py
```

O seed cria as duas contas com as senhas do `.env` no primeiro uso. Executá-lo outra vez preserva as senhas das contas existentes. A importação reutiliza resultados salvos, preserva exemplos já importados e não consome cota Gemini.

## 7. Inicie e experimente

**Windows (PowerShell)**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

**macOS/Linux**

```sh
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

1. Mantenha o terminal aberto e acesse **[http://127.0.0.1:8000](http://127.0.0.1:8000)** no mesmo computador. Use exatamente o endereço configurado em `APP_ORIGIN`.
2. Entre como `demo1@sauva.example` com a senha escolhida no passo 5. Abra um dos quatro exemplos e experimente **Abrir original**, **Ver / salvar PDF** e **Baixar FHIR JSON**.
3. Para testar o compartilhamento, escolha `demo2@sauva.example` como destinatário. Abra o link em uma janela privada **no mesmo computador**, entre como demo2 e use a senha de compartilhamento exibida pela aplicação. O link pode ser resgatado uma vez em até 24 horas e dá acesso ao documento por dez minutos.
4. Para enviar uma receita ou um manuscrito, escolha **Texto**. Para preservar um exame médico como anexo FHIR, escolha **Exame de imagem**. A aplicação aceita PDF/JPEG de até 10 MB e PDFs de até dez páginas. O fluxo de imagem preserva o original sem emitir diagnóstico.

Para encerrar, pressione **Ctrl+C**. Nos próximos usos, inicie o PostgreSQL e repita apenas o comando do passo 7 na pasta do projeto.

## Testes opcionais

Para executar a suíte, crie um banco separado com `CREATE DATABASE sauva_test OWNER sauva_app;` no psql como administrador. Defina `TEST_DATABASE_URL` no `.env` usando o mesmo formato de `DATABASE_URL`, com `/sauva_test` ao final. No Windows, execute:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/run_tests.py
```

No macOS/Linux, substitua `.\.venv\Scripts\python.exe` por `.venv/bin/python`. O runner usa o banco de teste e simula as chamadas ao Google.
