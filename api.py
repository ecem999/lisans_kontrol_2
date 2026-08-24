import os
import sys
import uuid
import shutil
import asyncio

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from validators import ValidatorFactory
from utils.ocr_service import OCRService
from utils.visual_matcher import VisualMatcher
from config import COUNTRIES_CONFIG
from utils.logger import get_logger
from utils.excel_logger import append_logs
import zipfile
import tempfile
from fastapi.responses import FileResponse
from typing import List

logger = get_logger(__name__)

app = FastAPI(
    title="Antigravity Avrupa Rehber Doğrulama API",
    description="İspanya, Fransa ve İtalya için turist rehberi lisans doğrulama motoru",
    version="1.0.0"
)

# Initialize VisualMatcher globally
# Not: Yüklediğimiz modül klasör yapısıyla uyuşuyor, referans dosyaları varsayılan dizinde.
matcher = VisualMatcher()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Antigravity Avrupa Rehber Doğrulama API'si başarıyla çalışıyor!", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}



UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class GuideDataRequest(BaseModel):
    country: str
    region: Optional[str] = None
    license_no: Optional[str] = None
    name: Optional[str] = None
    document_type: Optional[str] = "official" # official, WFTGA, vb.
    qr_url: Optional[str] = None

@app.post("/api/verify/manual")
async def verify_manual(request: GuideDataRequest):
    """Kullanıcının form üzerinden girdiği verilerle doğrulama yapar."""
    country_code = request.country.lower()
    
    try:
        validator = ValidatorFactory.get_validator(country_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if country_code == "spain" and not request.region:
        raise HTTPException(status_code=400, detail={"error": "MISSING_REGION", "message": "İspanya için bölge (region) alanı zorunludur."})

    guide_data = request.dict()

    try:
        result = await validator.verify_guide(guide_data)
        result["country"] = validator.country_code
        return result
    except Exception as e:
        logger.error(f"Doğrulama sırasında hata: {e}")
        raise HTTPException(status_code=500, detail=f"Sunucu hatası: {str(e)}")


async def process_image_core(file_path: str, original_filename: str, country: str, region: Optional[str]) -> dict:
    try:
        from PIL import Image, ImageEnhance
        with Image.open(file_path) as im:
            # Okunabilirliği bozmamak için limiti 2000 pikselde tuttuk
            im.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
            
            # OCR kalitesini artırmak için Keskinlik ve Kontrastı abartalım
            sharp_enhancer = ImageEnhance.Sharpness(im)
            im = sharp_enhancer.enhance(2.0) # 2 kat keskinleştir
            
            contrast_enhancer = ImageEnhance.Contrast(im)
            im = contrast_enhancer.enhance(1.5) # %50 daha fazla kontrast
            
            # RGB olarak kaydet (şeffaflık kanallarını at)
            im = im.convert("RGB")
            im.save(file_path, "JPEG", quality=95)
            logger.info("Resim başarıyla küçültüldü ve OCR için keskinleştirildi.")
    except Exception as img_e:
        logger.warning(f"Resim küçültme işlemi başarısız: {img_e}")
        
    try:
        ocr = OCRService()
        ocr_result = ocr.parse_image(file_path, country=country)
        
        if ocr_result["status"] != "SUCCESS":
            logger.warning(f"OCR Başarısız: {ocr_result}")
            return {
                "filename": original_filename,
                "status": "ERROR",
                "label": "OCR_FAILED",
                "message": ocr_result.get("message", "Görsel işlenemedi."),
                "extracted_data": {"country": country, "region": region}
            }
            
        ocr_extracted_data = ocr_result["guide_data"]
        
        detected_region = None
        match_score = None
        detected_region_name = None
        
        if country.lower() == "spain" and (not region or region == "auto"):
            logger.info("İspanya için otomatik bölge tespiti (Visual Matcher) başlatılıyor...")
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            
            match_result = matcher.match_image(image_bytes)
            
            if match_result["match_found"]:
                res_region = match_result["region"]
                score = match_result["score"]
                name = None
                for key, val in COUNTRIES_CONFIG["spain"]["regions"].items():
                    if f"{res_region}.jpg" in val.get("reference_image", ""):
                        name = val.get("name")
                        res_region = key 
                        break
                if not name:
                    name = res_region.capitalize()
                    
                logger.info(f"Visual Match Başarılı! Bölge: {name} (Score: {score}%, Good Matches: {match_result['matches_count']})")
                region = res_region
                detected_region = res_region
                match_score = score
                detected_region_name = name
            else:
                score = match_result["score"]
                matches_count = match_result.get("matches_count", 0)
                logger.warning(f"Visual Match başarısız veya eşik değerin altında kaldı. (Score: {score}%, Matches: {matches_count})")
                return {
                    "filename": original_filename,
                    "status": "ERROR",
                    "label": "MISSING_REGION",
                    "message": match_result["message"],
                    "extracted_data": {"country": country, "region": region}
                }
        
        guide_data = {
            "country": country,
            "region": region,
            "license_no": ocr_extracted_data.get("license_no"),
            "name": ocr_extracted_data.get("name"),
            "document_type": ocr_extracted_data.get("document_type", "official"),
            "qr_url": ocr_extracted_data.get("qr_url")
        }
        
        try:
            validator = ValidatorFactory.get_validator(country.lower())
            result = await validator.verify_guide(guide_data)
            result["country"] = validator.country_code
            result["filename"] = original_filename
            
            if detected_region:
                result["detected_region"] = detected_region
                result["detected_region_name"] = detected_region_name
                result["match_score"] = match_score
                
            result["ocr_license_found"] = guide_data.get("license_no")
            result["extracted_data"] = guide_data
            return result
        except ValueError as e:
            return {
                "filename": original_filename,
                "status": "ERROR",
                "label": "VALIDATION_ERROR",
                "message": str(e),
                "extracted_data": guide_data
            }
    except Exception as e:
        logger.error(f"OCR/Doğrulama hatası: {e}")
        return {
            "filename": original_filename,
            "status": "ERROR",
            "label": "SERVER_ERROR",
            "message": f"Görsel işleme hatası: {str(e)}",
            "extracted_data": {"country": country, "region": region}
        }


@app.post("/api/verify/image")
async def verify_image(
    country: str = Form(...),
    region: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """Yüklenen görseli OCR'dan geçirir ve elde edilen verilerle doğrulama yapar."""
    file_ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    result = await process_image_core(file_path, file.filename, country, region)
    
    if result.get("status") == "ERROR":
        status_code = 400
        if result.get("label") == "SERVER_ERROR":
            status_code = 500
        raise HTTPException(status_code=status_code, detail={"error": result.get("label"), "message": result.get("message")})
        
    return result


@app.post("/api/verify/batch")
async def verify_batch(
    country: str = Form(...),
    region: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    """
    Çoklu resim veya tek bir ZIP dosyası yükleyerek toplu doğrulama yapar.
    Sonuçları data/veritabani_log.xlsx dosyasına ekler ve bu dosyayı döndürür.
    """
    results = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Eğer tek bir dosya yüklendiyse ve bu bir ZIP dosyasıysa
        if len(files) == 1 and files[0].filename.lower().endswith(".zip"):
            zip_path = os.path.join(temp_dir, files[0].filename)
            with open(zip_path, "wb") as buffer:
                shutil.copyfileobj(files[0].file, buffer)
                
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile:
                raise HTTPException(status_code=400, detail="Geçersiz ZIP dosyası.")
                
            # ZIP içindeki resimleri bul (Mac OS __MACOSX gibi gizli klasörleri atla)
            for root, _, extracted_files in os.walk(temp_dir):
                if "__MACOSX" in root:
                    continue
                for filename in extracted_files:
                    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                        file_path = os.path.join(root, filename)
                        res = await process_image_core(file_path, filename, country, region)
                        results.append(res)
        else:
            # Doğrudan birden fazla (veya tek) resim yüklendiyse
            for file in files:
                if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    results.append({
                        "filename": file.filename,
                        "status": "ERROR",
                        "label": "INVALID_FILE_TYPE",
                        "message": "Desteklenmeyen dosya formatı.",
                        "extracted_data": {"country": country, "region": region}
                    })
                    continue
                    
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                    
                res = await process_image_core(file_path, file.filename, country, region)
                results.append(res)
                
    if not results:
        raise HTTPException(status_code=400, detail="İşlenecek geçerli resim bulunamadı.")
        
    # Excel dosyasına ekle
    append_logs(results)
    
    # Oluşturulan Excel dosyasını döndür
    log_file_path = "data/veritabani_log.xlsx"
    if not os.path.exists(log_file_path):
        raise HTTPException(status_code=500, detail="Log dosyası oluşturulamadı.")
        
    return FileResponse(
        path=log_file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="veritabani_log.xlsx"
    )
