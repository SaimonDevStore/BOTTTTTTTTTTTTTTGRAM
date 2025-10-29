import hashlib
import json
import time
from typing import Any, Dict, Optional

import aiohttp


class AliExpressClient:
	API_BASE_URL = "https://api-sg.aliexpress.com/sync"

	def __init__(self, app_key: str, app_secret: str, tracking_id: str) -> None:
		self.app_key = app_key
		self.app_secret = app_secret
		self.tracking_id = tracking_id

	@staticmethod
	def _md5_hex(data: str) -> str:
		return hashlib.md5(data.encode("utf-8")).hexdigest().upper()

	def _sign(self, params: Dict[str, Any]) -> str:
		# Signature: MD5 of APP_SECRET + concatenated(sorted(k+v)) + APP_SECRET
		sorted_items = sorted((k, str(v)) for k, v in params.items() if v is not None)
		concatenated = "".join([k + v for k, v in sorted_items])
		return self._md5_hex(f"{self.app_secret}{concatenated}{self.app_secret}")

	async def _request(self, method: str, biz_params: Dict[str, Any]) -> Dict[str, Any]:
		public_params: Dict[str, Any] = {
			"app_key": self.app_key,
			"method": method,
			"sign_method": "md5",
			"timestamp": int(time.time() * 1000),
			"format": "json",
		}
		payload: Dict[str, Any] = {**public_params, **biz_params}
		payload["sign"] = self._sign(payload)

		async with aiohttp.ClientSession() as session:
			async with session.post(self.API_BASE_URL, data=payload, timeout=20) as resp:
				resp.raise_for_status()
				data = await resp.json(content_type=None)
				return data

	async def get_product_detail(self, product_id: str, locale: str = "pt_BR", currency: str = "BRL") -> Optional[Dict[str, Any]]:
		# Method name based on official affiliate product detail API
		method = "aliexpress.affiliate.productdetail.get"
		biz_params = {
			"product_ids": product_id,
			"target_currency": currency,
			"target_language": locale,
		}
		data = await self._request(method, biz_params)

		# The exact response envelope may vary; we normalize defensively
		result = (
			data.get("aliexpress_affiliate_productdetail_get_response")
			or data.get("data")
		)
		if not result:
			return None

		products = (
			result.get("resp_result", {}).get("result", {}).get("products")
			or result.get("result", {}).get("products")
		)
		if not products:
			return None
		return products[0]

	async def generate_affiliate_link(self, original_url: str) -> Optional[str]:
		method = "aliexpress.affiliate.link.generate"
		biz_params = {
			"promotion_link_type": "AE_GLOBAL",
			"tracking_id": self.tracking_id,
			"source_values": json.dumps([original_url]),
		}
		data = await self._request(method, biz_params)
		result = (
			data.get("aliexpress_affiliate_link_generate_response")
			or data.get("data")
		)
		if not result:
			return None
		links = (
			result.get("resp_result", {}).get("result", {}).get("promotion_links")
			or result.get("result", {}).get("promotion_links")
		)
		if not links:
			return None
		link_obj = links[0]
		return link_obj.get("promotion_link") or link_obj.get("discount_link") or link_obj.get("target_url")
