import streamlit as st
import requests
import json
from google import genai

st.set_page_config(
    page_title="Arena de Predicciones NFL",
    page_icon="🏈",
    layout="wide"
)

st.title("🏈 Arena de Predicciones NFL - Semana Actual")
st.markdown("Dashboard interactivo conectado en tiempo real a la API de ESPN con enfoque en Google Gemini.")
st.info("ℹ️ **Regla de Marcadores:** Los pronósticos se muestran estrictamente en formato **(Puntos Visitante - Puntos Local)**.")

# Configurar cliente de Google GenAI de forma segura
try:
    google_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.warning("⚠️ Falta la clave de API de Gemini en los Secrets de Streamlit.")

# --- PANEL LATERAL DE DIAGNÓSTICO DE APIS ---
with st.sidebar:
    st.header("⚙️ Estado de Conexiones")
    if st.button("🔍 Probar Conexión con IAs"):
        st.info("ℹ️ OpenAI: Usando respaldo local.")
        st.info("ℹ️ Anthropic: Usando respaldo local.")

        # Prueba Google Gemini con el modelo actualizado solicitado (gemini-3.6-flash)
        try:
            google_client.models.generate_content(
                model='gemini-3.6-flash',
                contents='ping'
            )
            st.success("✅ Google Gemini: Conectado")
        except Exception as e:
            st.error(f"❌ Gemini Error: {e}")

@st.cache_data(ttl=3600)
def obtener_cartelera_espn():
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            semana = data.get('week', {}).get('number', 'Desconocida')
            temporada = data.get('season', {}).get('year', 'Actual')
            tipo_temporada = data.get('season', {}).get('type', 2)
            
            fase_map = {1: "Pretemporada", 2: "Temporada Regular", 3: "Postemporada"}
            fase_texto = fase_map.get(tipo_temporada, "Temporada")

            partidos = []
            for event in data.get('events', []):
                competitions = event['competitions'][0]
                competitors = competitions['competitors']
                
                local = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                visitante = next((c for c in competitors if c.get('homeAway') == 'away'), {})
                
                nombre_local = local.get('team', {}).get('displayName', 'Local')
                score_local = local.get('score', '0')
                
                nombre_visitante = visitante.get('team', {}).get('displayName', 'Visitante')
                score_visitante = visitante.get('score', '0')
                
                estado = event['status']['type']['description']
                fecha = event.get('date', '')

                partidos.append({
                    "id": event.get('id'),
                    "nombre_local": nombre_local,
                    "score_local": score_local,
                    "nombre_visitante": nombre_visitante,
                    "score_visitante": score_visitante,
                    "estado": estado,
                    "fecha": fecha
                })
                
            return temporada, fase_texto, semana, partidos
    except Exception as e:
        st.error(f"Error al conectar con la API de ESPN: {e}")
    return None, None, None, []

# Funciones de respaldo para OpenAI y Claude
def consultar_openai_respaldo(visitante, local):
    return {
        "ganador": local,
        "puntos_visitante": 20,
        "puntos_local": 24,
        "analisis": f"Análisis táctico (Respaldo): Ventaja para {local} en casa."
    }

def consultar_claude_respaldo(visitante, local):
    return {
        "ganador": visitante,
        "puntos_visitante": 27,
        "puntos_local": 24,
        "analisis": f"Análisis táctico (Respaldo): El juego aéreo de {visitante} dominará."
    }

def consultar_gemini(visitante, local):
    prompt = f"""Analiza el partido NFL: {visitante} (Visitante) vs {local} (Local).
    Devuelve estrictamente un objeto JSON válido con estas llaves exactas:
    - "ganador": "Nombre del equipo ganador"
    - "puntos_visitante": número entero
    - "puntos_local": número entero
    - "analisis": "Explicación de 1 línea"
    Responde únicamente con el JSON."""
    try:
        response = google_client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto_limpio)
    except Exception as e:
        return {"ganador": "Error", "puntos_visitante": 0, "puntos_local": 0, "analisis": str(e)}

if st.button("🔄 Refrescar Datos"):
    st.cache_data.clear()

temporada, fase, semana, cartelera = obtener_cartelera_espn()

if cartelera:
    st.success(f"📅 **Temporada:** {temporada} ({fase}) | **Semana:** {semana}")
    st.markdown("---")
    
    for idx, p in enumerate(cartelera, 1):
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 3])
            
            with col1:
                st.markdown(f"### ✈️ {p['nombre_visitante']}")
                st.write(f"Marcador real: **{p['score_visitante']}**")
                
            with col2:
                st.markdown(f"<div style='text-align: center; font-weight: bold; color: gray;'>VS</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center;'>Estado: <em>{p['estado']}</em></div>", unsafe_allow_html=True)
                
            with col3:
                st.markdown(f"### 🏠 {p['nombre_local']}")
                st.write(f"Marcador real: **{p['score_local']}**")
            
            with st.expander("🤖 Ver Arena de Predicciones Real (IA vs IA)"):
                if st.button(f"⚡ Ejecutar Predicciones", key=f"btn_{p['id']}"):
                    with st.spinner("Gemini está analizando los encuentros..."):
                        res_gpt = consultar_openai_respaldo(p['nombre_visitante'], p['nombre_local'])
                        res_claude = consultar_claude_respaldo(p['nombre_visitante'], p['nombre_local'])
                        res_gemini = consultar_gemini(p['nombre_visitante'], p['nombre_local'])
                    
                    ic1, ic2, ic3 = st.columns(3)
                    
                    with ic1:
                        st.markdown("**🟢 OpenAI (Respaldo)**")
                        st.write(f"Ganador: **{res_gpt.get('ganador')}**")
                        st.write(f"Pronóstico: `{res_gpt.get('puntos_visitante')} - {res_gpt.get('puntos_local')}`")
                        st.caption(res_gpt.get('analisis'))
                        
                    with ic2:
                        st.markdown("**🟠 Anthropic (Respaldo)**")
                        st.write(f"Ganador: **{res_claude.get('ganador')}**")
                        st.write(f"Pronóstico: `{res_claude.get('puntos_visitante')} - {res_claude.get('puntos_local')}`")
                        st.caption(res_claude.get('analisis'))
                        
                    with ic3:
                        st.markdown("**🔵 Google (Gemini 3.6 Flash)**")
                        st.write(f"Ganador: **{res_gemini.get('ganador')}**")
                        st.write(f"Pronóstico: `{res_gemini.get('puntos_visitante')} - {res_gemini.get('puntos_local')}`")
                        st.caption(res_gemini.get('analisis'))
                else:
                    st.info("Haz clic en el botón para consultar el análisis en vivo.")
                
            st.markdown("---")
else:
    st.warning("No se encontraron partidos disponibles en este momento.")
