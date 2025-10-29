import re
from typing import Optional, Tuple

import aiohttp


ALIEXPRESS_HOSTS = (
	"aliexpress.com",
	"pt.aliexpress.com",
	"www.aliexpress.com",
	"m.aliexpress.com",
	"g.aliexpress.com",
	"s.click.aliexpress.com",
)


def extract_product_id(url: str) -> Optional[str]:
	if not url:
		return None

	# Try common patterns
	patterns = [
		# .../item/1234567890.html
		r"/item/(\d+)\.html",
		# .../i/1234567890.html
		r"/i/(\d+)\.html",
		# productId=1234567890
		r"[?&](?:productId|product_id)=(\d+)",
		# .../product/1234567890.html (alguns domínios)
		r"/product/(\d+)\.html",
		# .../item/1234567890 (sem .html)
		r"/item/(\d+)(?:[/?#]|$)",
	]
	for pattern in patterns:
		m = re.search(pattern, url)
		if m:
			return m.group(1)
	return None


def has_affiliate_params(url: str) -> bool:
	if not url:
		return False
	aff_params = (
		"aff_fcid",
		"aff_fsk",
		"aff_platform",
		"aff_trace_key",
		"aff_short_key",
		"dp_cps_id",
	)
	return any((f"{p}=" in url) for p in aff_params)


def format_currency_brl(value: float) -> str:
	return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calc_discount_percent(old_price: Optional[float], new_price: Optional[float]) -> Optional[int]:
	if not old_price or not new_price or old_price <= 0:
		return None
	pct = round((1 - (new_price / old_price)) * 100)
	return max(0, pct)


async def resolve_final_url(original_url: str, timeout_sec: int = 15) -> Optional[str]:
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
	}
	try:
		async with aiohttp.ClientSession(headers=headers) as session:
			# Try HEAD first to follow redirects quickly
			try:
				async with session.head(original_url, allow_redirects=True, timeout=timeout_sec) as resp:
					return str(resp.url)
			except Exception:
				pass
			# Fallback to GET
			async with session.get(original_url, allow_redirects=True, timeout=timeout_sec) as resp:
				return str(resp.url)
	except Exception:
		return None


def extract_first_url(text: str) -> Optional[str]:
	if not text:
		return None
	m = re.search(r"(https?://\S+)", text)
	if not m:
		return None
	url = m.group(1)
	# Remove pontuações comuns no fim
	return url.rstrip(").,>\n\r\t ")
