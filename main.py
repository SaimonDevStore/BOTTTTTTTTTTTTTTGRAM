import asyncio
import os
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from aliexpress_client import AliExpressClient
from utils import extract_product_id, has_affiliate_params, format_currency_brl, calc_discount_percent


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
TIMEZONE = os.getenv("TIMEZONE", "America/Sao_Paulo")

APP_KEY = os.getenv("APP_KEY", "").strip()
APP_SECRET = os.getenv("APP_SECRET", "").strip()
TRACKING_ID = os.getenv("TRACKING_ID", "BOT_TELEGRAM").strip()

if not BOT_TOKEN:
	raise RuntimeError("BOT_TOKEN must be set in environment variables")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

alx_client = AliExpressClient(app_key=APP_KEY, app_secret=APP_SECRET, tracking_id=TRACKING_ID)


class TelegramUpdate(BaseModel):
	update_id: int


# ---- Access Control Helpers ----

def _is_authorized(user_id: Optional[int]) -> bool:
	if not ALLOWED_USER_ID:
		return True
	try:
		return int(ALLOWED_USER_ID) == int(user_id or 0)
	except ValueError:
		return False


# ---- Commands ----

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
	if not _is_authorized(message.from_user.id):
		await message.answer("Acesso negado. Configure ALLOWED_USER_ID para usar o bot.")
		return
	text = (
		"Envie um link de produto da AliExpress e eu retorno uma mensagem formatada com preço, desconto e link de afiliado.\n\n"
		"Comandos disponíveis:\n"
		"/start – Mostrar instruções.\n"
		"/meuid – Mostrar seu ID.\n"
		"/ajuda – Como usar o bot."
	)
	await message.answer(text)


@dp.message(Command("meuid"))
async def cmd_meuid(message: Message) -> None:
	await message.answer(f"Seu ID: {message.from_user.id}")


@dp.message(Command("ajuda"))
async def cmd_ajuda(message: Message) -> None:
	text = (
		"Como usar:\n"
		"1) Envie qualquer link de produto da AliExpress.\n"
		"2) Eu busco as informações oficiais e gero o texto pronto.\n\n"
		"Observações:\n"
		"- Se o link já for afiliado, eu só formato.\n"
		"- Se não for, eu gero com seu TRACKING_ID.\n"
		"- Se o link for inválido, aviso para verificar."
	)
	await message.answer(text)


# ---- Message Handler ----

@dp.message(F.text)
async def handle_link(message: Message) -> None:
	if not _is_authorized(message.from_user.id):
		await message.answer("Acesso negado. Configure ALLOWED_USER_ID para usar o bot.")
		return

	text = (message.text or "").strip()
	if not text.lower().startswith("http"):
		return

	product_id = extract_product_id(text)
	if not product_id:
		await message.answer("Não consegui encontrar esse produto. Verifique o link e tente novamente.")
		return

	try:
		product = await alx_client.get_product_detail(product_id)
		if not product:
			await message.answer("Não consegui encontrar esse produto. Verifique o link e tente novamente.")
			return

		# Extract product info defensively
		title = product.get("product_title") or product.get("title") or "Produto AliExpress"
		image_url = product.get("product_main_image_url") or product.get("image_url") or ""
		prices = product.get("prices") or {}
		current_price = None
		old_price = None
		if isinstance(prices, dict):
			current_price = prices.get("sale_price", {}).get("value") or prices.get("sale_price_formatted")
			old_price = prices.get("original_price", {}).get("value") or prices.get("original_price_formatted")

		# Fallback alternative keys
		if current_price is None:
			current_price = product.get("target_sale_price") or product.get("sale_price")
		if old_price is None:
			old_price = product.get("target_original_price") or product.get("original_price")

		# Normalize numeric prices if given as strings
		def _to_float(v: Optional[str]):
			if v is None:
				return None
			try:
				return float(str(v).replace("R$", "").replace("$", "").replace(" ", "").replace(",", "."))
			except Exception:
				return None

		current_price_num = _to_float(current_price)
		old_price_num = _to_float(old_price)

		pct = calc_discount_percent(old_price_num, current_price_num)

		coupon_info = product.get("coupon_info") or product.get("coupon") or ""
		shipping = product.get("logistics_info", {}).get("freight_committed") if isinstance(product.get("logistics_info"), dict) else None
		if not shipping:
			shipping = "Frete Grátis" if str(product.get("freight_free", "")).lower() in ("true", "1") else "Consulte o frete"
			rule = product.get("freight_rul", "") or product.get("freight_rule", "")
			if rule:
				shipping = f"{shipping} ({rule})"

		# Affiliate link
		affiliate_link = text if has_affiliate_params(text) else None
		if not affiliate_link:
			generated = await alx_client.generate_affiliate_link(text)
			affiliate_link = generated or text

		price_old_text = format_currency_brl(old_price_num) if old_price_num else "-"
		price_new_text = format_currency_brl(current_price_num) if current_price_num else "-"
		pct_text = f"{pct}%" if pct is not None else "-"
		coupon_text = f"Cupom: {coupon_info}" if coupon_info else ""

		# Some products include ratings and sales
		rating = product.get("evaluate_rate") or product.get("averate_score") or product.get("avg_evaluation_rating")
		sales = product.get("sales") or product.get("orders") or product.get("trade_count")
		rating_text = f"{rating}" if rating else "-"
		sales_text = f"{sales}" if sales else "-"

		header_tags = []
		if "frete" in shipping.lower():
			header_tags.append("Frete Grátis")
		if coupon_info:
			header_tags.append("Cupom")
		if pct and pct >= 40:
			header_tags.append("Oferta Relâmpago")
		header = " / ".join(header_tags) if header_tags else "Oferta"

		msg = (
			f"{title} | {header}\n\n"
			f"💵 De: {price_old_text} ➜ **{price_new_text}**\n"
			f"🎯 Desconto: {pct_text}% {coupon_text}\n"
			f"🚚 Frete: {shipping}\n"
			f"⭐ Avaliação: {rating_text} ({sales_text} vendas)\n\n"
			f"🔗 Link com Desconto (Afiliado):\n{affiliate_link}\n"
		)

		await message.answer(msg)
		if image_url:
			# send as separate message to avoid markdown issues
			await message.answer(f"📷 Imagem:\n{image_url}")

	except Exception as e:
		await message.answer("Não consegui encontrar esse produto. Verifique o link e tente novamente.")


# ---- FastAPI Webhook App ----

app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
	if WEBHOOK_URL:
		await bot.set_webhook(f"{WEBHOOK_URL}/{bot.token}")


@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request) -> Response:
	if token != bot.token:
		return JSONResponse(status_code=401, content={"ok": False})
	update = await request.json()
	await dp.feed_webhook_update(bot, update)
	return JSONResponse(status_code=200, content={"ok": True})


# Fallback para casos em que WEBHOOK_URL foi configurado sem "/webhook"
@app.post("/{token}")
async def telegram_webhook_fallback(token: str, request: Request) -> Response:
	if token != bot.token:
		return JSONResponse(status_code=401, content={"ok": False})
	update = await request.json()
	await dp.feed_webhook_update(bot, update)
	return JSONResponse(status_code=200, content={"ok": True})


@app.get("/")
async def healthcheck() -> dict:
	return {"ok": True}


def main() -> None:
	# Local development fallback: polling
	import uvicorn
	port = int(os.getenv("PORT", "10000"))
	uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
	main()
