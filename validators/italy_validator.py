from validators.base_validator import BaseValidator
from config import STATUS_MAP
from utils.scraper import AsyncScraper

class ItalyValidator(BaseValidator):
    def __init__(self):
        super().__init__("italy")

    async def verify_guide(self, guide_data: dict) -> dict:
        # 1. WFTGA Kontrolü
        wftga_check = self.check_wftga_policy(guide_data.get("document_type", ""))
        if wftga_check["status"] == "INVALID":
            return wftga_check

        # 2. QR Kod Kontrolü Hızlı Geçişi (İtalya'ya Özel)
        qr_url = guide_data.get("qr_url", "")
        if qr_url:
            return await self._verify_via_qr(qr_url)

        # 3. Lisans Formatı Kontrolü
        license_no = guide_data.get("license_no", "")
        if not self.validate_license_format(license_no):
            return {
                "status": "INVALID",
                "label": STATUS_MAP["INVALID"]["label"],
                "message": f"Geçersiz İtalya lisans formatı. Beklenen: {self.config['license_format']}"
            }

        # 4. Ulusal Veritabanı Sorgusu
        return await self._check_national_db(guide_data)

    async def _verify_via_qr(self, qr_url: str) -> dict:
        import requests
        import asyncio
        
        # Sadece resmi domain'leri kabul et
        official_domains = ["ministeroturismo.gov.it", "turismo.gov.it"]
        is_official = any(domain in qr_url for domain in official_domains)
        
        if not is_official:
            return {
                "status": "UNKNOWN",
                "label": "Geçersiz Domain",
                "url": qr_url,
                "message": "QR kod resmi bakanlık domainine ait değil."
            }
            
        try:
            # IO işlemini bloklamamak için asyncio.to_thread ile çalıştırıyoruz
            response = await asyncio.to_thread(requests.get, qr_url, timeout=10)
            if response.status_code == 200:
                return {
                    "status": "VALID",
                    "label": "Sistemden Döndü (QR)",
                    "url": qr_url,
                    "message": "QR kod resmi sistemde başarıyla doğrulandı."
                }
            else:
                return {
                    "status": "INVALID",
                    "label": "Bulunamadı (QR)",
                    "url": qr_url,
                    "message": f"QR kod sayfasına ulaşılamadı (HTTP {response.status_code})."
                }
        except Exception as e:
            return {
                "status": "UNKNOWN",
                "label": "Bağlantı Hatası",
                "url": qr_url,
                "message": f"QR kod doğrulanırken hata oluştu: {str(e)}"
            }

    async def _check_national_db(self, guide_data: dict) -> dict:
        from utils.excel_validator import check_guide_in_excel
        
        excel_result = await check_guide_in_excel("italy", guide_data.get("name", ""))
        
        if excel_result["status"] == "VALID":
            return {
                "status": "VALID",
                "label": "Sistemden Döndü",
                "message": excel_result["message"],
                "url": excel_result.get("url")
            }
            
        return {
            "status": "UNKNOWN",
            "label": "Eksik Veri",
            "message": excel_result["message"]
        }
