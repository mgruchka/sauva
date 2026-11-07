# PostgreSQL local — concluir tarefa 02

## 1. Descobrir instalação existente
No PowerShell:
```powershell
Get-Service *postgres* -ErrorAction SilentlyContinue
Get-ChildItem 'C:\Program Files\PostgreSQL' -Filter psql.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
```
psql fora do PATH não prova ausência do servidor. Se houver instalação, usar SQL Shell (psql) pelo menu Iniciar ou caminho completo encontrado.
Se não houver servidor, instalar uma versão estável suportada pelo instalador indicado em https://www.postgresql.org/download/windows/ (18 serve para o protótipo). Instalar servidor e ferramentas de linha de comando; Stack Builder não é necessário para este projeto. Anotar porta e senha de administrador localmente.

## 2. Criar usuário e bancos separados
Abrir SQL Shell (psql) e conectar ao banco postgres como administrador local. Não enviar a senha ao chat ou ao relatório.
Antes de criar, listar roles com \du e bancos com \l. Se sauva_app, sauva ou sauva_test já existirem, conferir dono e configuração: não apagar/recriar nem trocar senha silenciosamente.

Para uma instalação nova, executar um comando por vez:
```sql
CREATE ROLE sauva_app LOGIN;
```
No psql, definir senha de modo interativo:
```text
\password sauva_app
```
Depois:
```sql
CREATE DATABASE sauva OWNER sauva_app;
CREATE DATABASE sauva_test OWNER sauva_app;
```
Usar sauva_app na aplicação, não o usuário administrador. Os testes criam/removem apenas seu schema temporário em sauva_test.

## 3. Configuração local
Preservar .env existente. Somente se não existir, copiar .env.example para .env. Editar localmente:
```dotenv
DATABASE_URL=postgresql+psycopg://sauva_app:SENHA_CODIFICADA@127.0.0.1:5432/sauva
TEST_DATABASE_URL=postgresql+psycopg://sauva_app:SENHA_CODIFICADA@127.0.0.1:5432/sauva_test
APP_ORIGIN=http://127.0.0.1:8000
SESSION_COOKIE_SECURE=false
DEMO_OWNER_PASSWORD=SENHA_DEMO_1
DEMO_RECIPIENT_PASSWORD=SENHA_DEMO_2
```
Substituir placeholders e porta pelos valores locais reais. A senha do banco na URL precisa de percent-encoding se contiver caracteres reservados como @, :, /, # e %. Senhas DEMO_* são das contas da aplicação, diferentes da senha do PostgreSQL.
Não commitar .env nem imprimir as URLs. Variáveis já definidas no processo prevalecem sobre .env; se houver configuração antiga, corrigir localmente em vez de publicar seus valores.

## 4. Atualizar código e validar
Sincronizar dev/foundation preservando alterações locais. Na raiz do projeto:
```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\python.exe scripts/run_tests.py
```
Migração e seed carregam .env; o launcher fornece configuração ao pytest sem modificar os testes originais.
Resultado esperado: seis testes aprovados. Esse é um alvo, não uma verificação já realizada.
Se ocorrer erro, registrar mensagem sem credenciais. Não registrar testes como aprovados quando houver erro de setup.
Depois de verificar, atualizar docs/STATUS.md e docs/reviews/02-auth.md, revisar staged diff e publicar commit/push para dev/foundation. Informar ao Marcos o SHA; não iniciar 03.

## Referências oficiais
- https://www.postgresql.org/download/windows/
- https://www.postgresql.org/docs/current/sql-createdatabase.html
- https://www.postgresql.org/docs/current/app-psql.html
