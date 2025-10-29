import re
from typing import Optional, Tuple


ALIEXPRESS_HOSTS = (
	"aliexpress.com",
	"pt.aliexpress.com",
	"www.aliexpress.com",
	"m.aliexpress.com",
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
