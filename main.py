from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import fitz  # PyMuPDF

app = FastAPI()

PDF_PATH = "public/facturas.pdf"  # Ruta del PDF con facturas

# Permitir solo el dominio de tu frontend en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.recaudamas.com.co"],  # 🔥 Cambia esto por tu dominio
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los headers en las peticiones
)

# Definir el esquema de entrada con Pydantic
class InvoiceRequest(BaseModel):
    invoiceNumber: str

@app.post("/buscar-factura/")
async def buscar_factura(request: InvoiceRequest):
    try:
        doc = fitz.open(PDF_PATH)  # Abrir el PDF

        print("Total de páginas en el PDF:", len(doc))
        page_index = -1

        for i, page in enumerate(doc):
            text = page.get_text("text")
            if request.invoiceNumber in text:
                page_index = i
                break

        if page_index == -1:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        # Crear un nuevo PDF con la página encontrada
        new_pdf = fitz.open()
        new_pdf.insert_pdf(doc, from_page=page_index, to_page=page_index)
        pdf_bytes = new_pdf.write()

        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename=factura-{request.invoiceNumber}.pdf'})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))