"""main.py'deki validation handler'i jsonable_encoder ile sarmala."""
import io
import re

path = "app/main.py"
with io.open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1) jsonable_encoder import ekle (yoksa)
if "from fastapi.encoders import jsonable_encoder" not in content:
    content = content.replace(
        "from fastapi.exceptions import RequestValidationError",
        "from fastapi.encoders import jsonable_encoder\nfrom fastapi.exceptions import RequestValidationError",
    )
    print("[OK] jsonable_encoder import eklendi")
else:
    print("[i] import zaten var")

# 2) validation_exception_handler fonksiyonunu komple degistir
# Regex ile: @app.exception_handler(RequestValidationError)'dan sonraki fonksiyonu bul
pattern = re.compile(
    r"(@app\.exception_handler\(RequestValidationError\)\s*\n"
    r"async def validation_exception_handler\(request: Request, exc: RequestValidationError\):\s*\n"
    r"(?:.|\n)*?"
    r"return JSONResponse\(\s*\n"
    r"\s*status_code=status\.HTTP_422_UNPROCESSABLE_ENTITY,\s*\n"
    r"(?:.|\n)*?"
    r"\n\s*\)\s*\n)",
    re.MULTILINE,
)

new_handler = '''@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "error": "validation_error",
            "message": "Gönderilen veriler geçersiz.",
            "details": exc.errors(),
            "request_id": request_id,
        }),
    )
'''

if pattern.search(content):
    content = pattern.sub(new_handler, content, count=1)
    print("[OK] handler regex ile degistirildi")
else:
    print("[!] Regex eslesmedi, alternatif deneme...")
    # Basit ve garantili: eski mesaji jsonable_encoder ile sar
    if "content=jsonable_encoder" not in content:
        # "content={" -> "content=jsonable_encoder({"
        content = content.replace(
            "content={\n            \"error\": \"validation_error\"",
            "content=jsonable_encoder({\n            \"error\": \"validation_error\"",
        )
        # Bu bloktaki kapanis "}," -> "}),"
        # Sadece validation handler icin
        old_tail = '            "request_id": getattr(request.state, "request_id", None),\n        },\n    )'
        new_tail = '            "request_id": getattr(request.state, "request_id", None),\n        }),\n    )'
        content = content.replace(old_tail, new_tail, 1)
        print("[OK] alternatif duzeltme uygulandi")

with io.open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

# Kontrol
print()
print("--- jsonable_encoder kullanimi ---")
for i, line in enumerate(content.split("\n"), 1):
    if "jsonable_encoder" in line:
        print(f"{i}: {line}")