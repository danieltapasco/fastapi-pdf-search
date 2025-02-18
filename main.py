from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import fitz  # PyMuPDF
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

PDF_PATH = "public/facturas.pdf"  # Ruta del PDF

# Habilitar CORS solo para el frontend en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.recaudamas.com.co"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definir el esquema de entrada con Pydantic
class InvoiceRequest(BaseModel):
    invoiceNumber: str

# 🔥 Cargar PDF en memoria al iniciar el servidor
print("📄 Cargando PDF en memoria...")
doc = fitz.open(PDF_PATH)

# 🔥 Construir un índice de facturas en el PDF (diccionario {factura: página})
invoice_index = {}
for i, page in enumerate(doc):
    text = page.get_text("text")
    matches = re.findall(r"\b\d{5,10}\b", text)  # Suponiendo que los números de factura tienen entre 5 y 10 dígitos
    for invoice in matches:
        invoice_index[invoice] = i

print(f"✅ Indexadas {len(invoice_index)} facturas en memoria.")

@app.post("/buscar-factura/")
async def buscar_factura(request: InvoiceRequest):
    try:
        invoice_number = request.invoiceNumber.strip()

        if invoice_number not in invoice_index:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        page_index = invoice_index[invoice_number]

        # Extraer solo la página requerida
        new_pdf = fitz.open()
        new_pdf.insert_pdf(doc, from_page=page_index, to_page=page_index)
        pdf_bytes = new_pdf.write()

        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename=factura-{invoice_number}.pdf'})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))