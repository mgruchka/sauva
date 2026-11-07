# SAÚVA

Protótipo brasileiro para registros de saúde. A autenticação demo exige PostgreSQL;
uploads e integrações Google ainda não estão implementados.

## Ambiente local (PowerShell)

Use Python 3.13. Crie o ambiente virtual com o caminho explícito do interpretador
instalado (ajuste o caminho se necessário):

```powershell
& 'C:\Users\Marcos\AppData\Local\Programs\Python\Python313\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Não é necessário ativar o ambiente. Copie `.env.example` para `.env` e configure
um banco PostgreSQL de desenvolvimento (`sauva`) e outro separado para testes
(`sauva_test`). Crie ambos localmente com seu usuário PostgreSQL e preencha
`DATABASE_URL` e `TEST_DATABASE_URL` no formato `postgresql+psycopg://...`.
Use senhas fortes para as duas contas demo em `DEMO_OWNER_PASSWORD` e
`DEMO_RECIPIENT_PASSWORD`; o seed não altera senhas existentes. Configure
`APP_ORIGIN` exatamente como a origem usada no navegador. Em HTTPS, defina
`SESSION_COOKIE_SECURE=true`.

Execute as migrações e crie as contas somente após configurar o banco:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
```

As contas são `demo1@sauva.example` e `demo2@sauva.example`. Envie email e
senha em JSON para `POST /auth/login`, com header `Origin` igual a `APP_ORIGIN`.
`GET /auth/me` consulta a sessão; `POST /auth/logout` a revoga e também exige
esse header. O cookie é HttpOnly e expira em oito horas.

## Executar e verificar

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/docs para a documentação interativa e
http://127.0.0.1:8000/health para `{"status":"ok"}`. O endpoint é público e
indica apenas que o processo está vivo; não verifica prontidão de banco ou Google.
Encerre o servidor com Ctrl+C.

Para testar, defina `TEST_DATABASE_URL` no ambiente do processo. O teste usa
somente o banco terminado em `_test`, em schema temporário:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_health.py -q
```
