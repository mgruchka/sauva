# SAÚVA

Protótipo brasileiro para registros de saúde. Apenas a fundação está implementada;
não há autenticação, banco, uploads ou integrações Google.

## Ambiente local (PowerShell)

Use Python 3.13. Crie o ambiente virtual com o caminho explícito do interpretador
instalado (ajuste o caminho se necessário):

```powershell
& 'C:\Users\Marcos\AppData\Local\Programs\Python\Python313\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Não é necessário ativar o ambiente nem configurar `.env`, banco ou credenciais.
`.env.example` reserva configurações para etapas futuras.

## Executar e verificar

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/docs para a documentação interativa e
http://127.0.0.1:8000/health para `{"status":"ok"}`. O endpoint é público e
indica apenas que o processo está vivo; não verifica prontidão de banco ou Google.
Encerre o servidor com Ctrl+C.

Execute o teste fornecido pelo orquestrador:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_health.py -q
```
