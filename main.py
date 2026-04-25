import asyncio
import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="MS4 - Historial Clínico Agregador")

URL_MS1_MASCOTAS = "http://localhost:8000/api/v1/mascotas"
URL_MS2_CITAS = "http://localhost:8001/veterinarios"
URL_MS3_CLINICA = "http://localhost:8002/api/v1/consultas"

@app.get("/health")
def health_check():
    return {"servicio": "vethouse-aggregator (ms4)", "status": "ok"}

@app.get("/api/v1/historial-completo/{id_mascota}")
async def obtener_historial_completo(id_mascota: int):
    # httpx.AsyncClient permite hacer peticiones HTTP sin bloquear el hilo principal
    async with httpx.AsyncClient() as client:
        try:
            req_mascota = client.get(f"{URL_MS1_MASCOTAS}/{id_mascota}")
            req_citas = client.get(f"{URL_MS2_CITAS}/mascota/{id_mascota}")
            req_consultas = client.get(f"{URL_MS3_CLINICA}/mascota/{id_mascota}")

            res_mascota, res_citas, res_consultas = await asyncio.gather(
                req_mascota, req_citas, req_consultas, return_exceptions=True
            )

            historial = {
                "id_mascota": id_mascota,
                "perfil_paciente": res_mascota.json() if not isinstance(res_mascota, Exception) and res_mascota.status_code == 200 else {"error": "MS1 no disponible"},
                
                "agenda_citas": res_citas.json() if not isinstance(res_citas, Exception) and res_citas.status_code == 200 else [],
                
                "expediente_clinico": res_consultas.json() if not isinstance(res_consultas, Exception) and res_consultas.status_code == 200 else []
            }

            return historial

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fallo crítico en el agregador: {str(e)}")
