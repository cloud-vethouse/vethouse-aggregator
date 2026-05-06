import asyncio
import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="MS4 - Historial Clínico Agregador")

# URLs de los otros microservicios
URL_MS1_MASCOTAS = "http://localhost:8000/api/v1/mascotas"
URL_MS2_CITAS = "http://localhost:8001/api/v1/citas"
URL_MS3_CLINICA = "http://localhost:8002/api/v1/consultas"

@app.get("/health")
def health_check():
    return {"servicio": "vethouse-aggregator (ms4)", "status": "ok"}

@app.get("/api/v1/historial-completo/{id_mascota}")
async def obtener_historial_completo(id_mascota: int):
    async with httpx.AsyncClient() as client:
        try:
            req_mascota = client.get(f"{URL_MS1_MASCOTAS}/{id_mascota}")
            req_citas = client.get(f"{URL_MS2_CITAS}/mascota/{id_mascota}")
            req_consultas = client.get(f"{URL_MS3_CLINICA}/mascota/{id_mascota}")

            res_mascota, res_citas, res_consultas = await asyncio.gather(
                req_mascota, req_citas, req_consultas, return_exceptions=True
            )

            def safe_extract(res):
                if isinstance(res, Exception) or res.status_code != 200:
                    return [] if not isinstance(res, Exception) and "mascota" not in str(res.url) else {}
                try:
                    return res.json()
                except:
                    return []

            consultas_raw = res_consultas.json() if not isinstance(res_consultas, Exception) else []
            expediente = consultas_raw if isinstance(consultas_raw, list) else consultas_raw.get("data", [])

            return {
                "id_mascota": id_mascota,
                "perfil_paciente": safe_extract(res_mascota),
                "agenda_citas": safe_extract(res_citas),
                "expediente_clinico": expediente
            }
        except Exception as e:
            print(f"ERROR CRÍTICO EN AGREGADOR: {str(e)}")
            return {"id_mascota": id_mascota, "error": str(e), "agenda_citas": [], "expediente_clinico": []}