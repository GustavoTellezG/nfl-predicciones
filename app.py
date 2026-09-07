import streamlit as st
import requests
import json
import anthropic
import google.generativeai as genai

st.set_page_config(
    page_title="Arena de Predicciones NFL",
    page_icon="🏈",
    layout="wide"
)

st.title("🏈 Arena de Predicciones NFL - Semana Actual")
st.markdown("Dashboard interactivo conectado en tiempo real a la API de ESPN con enfrentamiento multi-modelo.")
st.info("ℹ️ **Regla de Marcadores:** Los pronósticos se muestran estrictamente en formato **(Puntos Visitante - Puntos Local)**.")

# Configurar clientes de IA de forma segura
try:
    claude_client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.warning("⚠️ Faltan algunas claves de API en los Secrets de Streamlit.")

# --- PANEL LATERAL DE DIAGNÓSTICO DE APIS ---
with st.sidebar:
    st.header("⚙️ Estado de Conexiones")
    if st.button("🔍 Probar Conexión con IAs"):
        # OpenAI (Simulado por falta de fondos)
        st.info("ℹ️ OpenAI: Usando respaldo local por cuota.")

        # Prueba Anthropic
        try:
            claude_client.messages.create(
                model="claude-3-haiku-20240307", 
                max_tokens=5, 
                messages=[{"role": "user", "content": "ping"}]
            )
            st.success("✅ Anthropic: Conectado")
        except Exception as e:
            st.error(f"❌ Anthropic Error: {e}")

        # Prueba Google Gemini
        try:
            model_test_g = genai.GenerativeModel('gemini-pro')
            model_test_g.generate_content("ping")
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

# Función de respaldo para OpenAI
def consultar_openai_respaldo(visitante, local):
    return {
        "ganador": local,
        "puntos_visitante": 20,
        "puntos_local": 24,
        "analisis": f"Análisis táctico (Modo Respaldo): Ventaja para {local} en casa."
    }

def consultar_claude(visitante, local):
    prompt = f"""Analiza el partido NFL: {visitante} (Visitante) vs {local} (Local).
    Devuelve estrictamente un JSON válido con estas llaves exactas:
    - "ganador": "Nombre del equipo ganador"
    - "puntos_visitante": número entero
    - "puntos_local": número entero
    - "analisis": "Explicación de 1 línea"
    Solo el JSON puro."""
    try:
        message = claude_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = message.content[0].text.strip().replace("```json", "").replace("```", "")
        return json.loads(texto)
    except Exception as e:
        return {"ganador": "Error", "puntos_visitante": 0, "puntos_local": 0, "analisis": str(e)}

def consultar_gemini(visitante, local):
    prompt = f"""Analiza el partido NFL: {visitante} (Visitante) vs {local} (Local).
    Devuelve estrictamente un objeto JSON válido con estas llaves exactas:
    - "ganador": "Nombre del equipo ganador"
    - "puntos_visitante": número entero
    - "puntos_local": número entero
    - "analisis": "Explicación de 1 línea"
    Responde únicamente con el JSON."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
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
                    with st.spinner("Las IAs están analizando los encuentros..."):
                        res_gpt = consultar_openai_respaldo(p['nombre_visitante'], p['nombre_local'])
                        res_claude = consultar_claude(p['nombre_visitante'], p['nombre_local'])
                        res_gemini = consultar_gemini(p['nombre_visitante'], p['nombre_local'])
                    
                    ic1, ic2, ic3 = st.columns(3)
                    
                    with ic1:
                        st.markdown("**🟢 OpenAI (Respaldo)**")
                        st.write(f"Ganador: **{res_gpt.get('ganador')}**")
                        st.write(f"Pronóstico: `{res_gpt.get('puntos_visitante')} - {res_gpt.get('puntos_local')}`")
                        st.caption(res_gpt.get('analisis'))
                        
                    with ic2:
                        st.markdown("**🟠 Anthropic (Claude 3 Haiku)**")
                        st.write(f"Ganador: **{res_claude.get('ganador')}**")
                        st.write(f"Pronóstico: `{res_claude.get('puntos_visitante')} - {res_claude.get('puntos_local')}`")
                        st.caption(res_claude.get('analisis'))
                        
                    with ic3:
                        st.markdown("**🔵 Google (Gemini Pro)**")
                        st.write(f"Ganador: **{res_gemini.get('ganador')}**")
                        st.write(f"Pronóstico: `{res_gemini.get('puntos_visitante')} - {res_gemini.get('puntos_local')}`")
                        st.caption(res_gemini.get('analisis'))
                else:
                    st.info("Haz clic en el botón para consultar el análisis en vivo.")
                
            st.markdown("---")
else:
    st.warning("No se encontraron partidos disponibles en este momento.")
