## Bot de Telegram – AliExpress Afiliado (Privado)

Este bot recebe um link de produto da AliExpress em chat privado e retorna um post formatado com título, preço antigo/atual, desconto, cupom, frete, avaliação, imagem e um link final de afiliado com o seu TRACKING_ID. Ele NÃO posta automaticamente no canal; você copia e cola manualmente.

### Funcionalidades
- Recebe qualquer link de produto da AliExpress
- Extrai `product_id` do link e consulta a API oficial (APP_KEY/APP_SECRET)
- Se o link já for afiliado, só formata; caso contrário, gera link afiliado com `TRACKING_ID`
- Comandos: `/start`, `/meuid`, `/ajuda`
- Restrição de acesso por `ALLOWED_USER_ID` (opcional)

### Stack
- Python 3.10+
- aiogram 3 + FastAPI (webhook)
- Uvicorn (servidor HTTP)

---

## Arquivos no GitHub (o que subir)
- `main.py`: Aplicação principal (bot + FastAPI + webhook)
- `aliexpress_client.py`: Cliente da API da AliExpress (assinatura e chamadas)
- `utils.py`: Utilidades (parse de link, formatação, etc.)
- `requirements.txt`: Dependências
- `.env.example`: Exemplo de variáveis de ambiente (veja observação abaixo)
- `README.md`: Este tutorial

Observação: se o provedor bloquear dotfiles, suba `env.example` e, no GitHub, renomeie para `.env.example` antes de conectar ao Render.

---

## Variáveis de ambiente (.env)
Crie um arquivo `.env` para desenvolvimento local ou configure no Render como Environment Variables:

```
BOT_TOKEN=8378547653:XXXXXX   # token do BotFather
ALLOWED_USER_ID=123456789     # opcional: seu user ID para acesso privado
WEBHOOK_URL=https://seu-servico.onrender.com/webhook
TIMEZONE=America/Sao_Paulo

APP_KEY=521022
APP_SECRET=Ve15nlPdIv5U7WRwAsWFHCqY2LRnsBes
TRACKING_ID=BOT_TELEGRAM

PORT=10000
```

Nunca commite segredos reais. Use `.env.example` com placeholders no GitHub.

---

## Como rodar localmente (modo webhook com servidor HTTP)
1) Python 3.10+ instalado
2) `pip install -r requirements.txt`
3) Configurar `.env`
4) `python main.py`

O servidor sobe em `http://localhost:10000`. Para receber updates do Telegram localmente, use um túnel (ngrok/Cloudflared) e configure `WEBHOOK_URL` para a URL pública do túnel.

---

## Deploy grátis no Render (passo a passo)

### 1) Criar conta
- Acesse `https://render.com` e crie sua conta gratuita

### 2) Subir o código no GitHub
- Crie um repositório no GitHub e envie estes arquivos:
  - `main.py`, `aliexpress_client.py`, `utils.py`, `requirements.txt`, `.env.example`, `README.md`

### 3) Conectar Render ao GitHub
- No painel do Render, clique em New +
- Escolha "Web Service"
- Conecte sua conta GitHub e selecione o repositório do bot

### 4) Configurar o serviço
- Name: `telegram-aliexpress-bot`
- Region: mais próxima do Brasil (se disponível)
- Branch: `main`
- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python main.py`
- Instance Type: Free

### 5) Environment Variables
Adicione as chaves abaixo em "Environment" (não use valores reais no repositório):
- `BOT_TOKEN` – token do BotFather
- `ALLOWED_USER_ID` – seu user id (rode /meuid local ou no bot para descobrir)
- `WEBHOOK_URL` – a URL pública do serviço no Render + `/webhook`, por exemplo: `https://telegram-aliexpress-bot.onrender.com/webhook`
- `TIMEZONE` – `America/Sao_Paulo`
- `APP_KEY`, `APP_SECRET` – chaves da AliExpress
- `TRACKING_ID` – por exemplo `BOT_TELEGRAM`
- `PORT` – `10000`

Importante: após criar o serviço, copie a URL pública e atualize `WEBHOOK_URL` para `https://SEU_DOMINIO.onrender.com/webhook`. O app configura o webhook automaticamente no startup.

### 6) Deploy automático
- Ative "Auto-Deploy" no Render (Deploy hooks automáticos em cada push na branch selecionada)

### 7) Rodando 24h grátis
- Na modalidade Free, o Render pode hibernar sem tráfego. Como o bot usa webhook, ele acorda ao receber requests do Telegram. Não é necessário job de keep-alive.

---

## Como usar
- No Telegram, abra seu bot e envie um link de produto da AliExpress
- Se o link for válido, você receberá uma mensagem pronta no formato:

```
{NOME DO PRODUTO} | {Frete Grátis / Cupom / Oferta Relâmpago}

💵 De: R$ {preco_antigo} ➜ **R$ {preco_atual}**
🎯 Desconto: {porcentagem}% {Cupom: {cupom}}
🚚 Frete: {informação de frete}
⭐ Avaliação: {nota} ({vendas} vendas)

🔗 Link com Desconto (Afiliado):
{link_afiliado}

📷 Imagem:
{url_imagem}
```

- Se o link já tiver parâmetros de afiliado, o bot preserva
- Se não tiver, o bot gera automaticamente o link de afiliado com seu `TRACKING_ID`
- Se o link for inválido: "Não consegui encontrar esse produto. Verifique o link e tente novamente."

---

## Observações sobre a API da AliExpress
- O cliente (`aliexpress_client.py`) assina as requisições com MD5 conforme padrão comum (`APP_SECRET + sorted(k+v) + APP_SECRET`).
- Os envelopes de resposta podem variar por conta de versões/contas; o código faz parsing defensivo.
- Métodos usados:
  - `aliexpress.affiliate.productdetail.get`
  - `aliexpress.affiliate.link.generate`

Se sua conta usar endpoints/envelopes diferentes, ajuste as chaves no parsing mantendo a estrutura.

---

## Segurança
- Não exponha APP_KEY, APP_SECRET e BOT_TOKEN no repositório
- Use `.env` somente local e Environment Variables no Render

---

## Licença
MIT
