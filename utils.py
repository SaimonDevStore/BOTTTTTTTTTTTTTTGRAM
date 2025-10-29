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


async def resolve_final_url(original_url: str, timeout_sec: int = 12) -> Optional[str]:
	try:
		async with aiohttp.ClientSession() as session:
			async with session.get(original_url, allow_redirects=True, timeout=timeout_sec) as resp:
				return str(resp.url)
	except Exception:
		return None
