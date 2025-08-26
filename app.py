# 1 - imports
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
import os
import re
import hashlib
from typing import Dict, List, Tuple
import numpy as np

# 2 - Configuración de la página
st.set_page_config(
    page_title="Gestión de Consultorios Odontológicos v2.0",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3 - CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .alert-success {
        background-color: #dcfce7;
        border: 1px solid #16a34a;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .alert-warning {
        background-color: #fef3c7;
        border: 1px solid #d97706;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .alert-error {
        background-color: #fee2e2;
        border: 1px solid #dc2626;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 4 - UserManager
class UserManager:
    """Maneja autenticación y usuarios del sistema"""
    
    def __init__(self):
        self.users_file = "usuarios.json"
        self.data_folder = "data"
        self.init_system()
    
    def init_system(self):
        """Inicializa el sistema creando archivos necesarios"""
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
        if not os.path.exists(self.users_file):
            usuarios_default = {
                "admin": {
                    "password_hash": self.hash_password("admin123"),
                    "nombre": "Dr. Administrador",
                    "email": "admin@dental.com",
                    "plan": "premium",
                    "fecha_registro": datetime.now().isoformat()
                },
                "demo1": {
                    "password_hash": self.hash_password("demo123"),
                    "nombre": "Dr. Demo Uno",
                    "email": "demo1@dental.com",
                    "plan": "trial",
                    "fecha_registro": datetime.now().isoformat()
                },
                "demo2": {
                    "password_hash": self.hash_password("demo123"),
                    "nombre": "Dra. Demo Dos",
                    "email": "demo2@dental.com",
                    "plan": "trial",
                    "fecha_registro": datetime.now().isoformat()
                }
            }
            
            self.save_users(usuarios_default)
            
            for user_id in usuarios_default.keys():
                self.create_user_folder(user_id)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self):
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_users(self, users_data):
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    
    def validate_user(self, username, password):
        users = self.load_users()
        
        if username not in users:
            return False, "Usuario no encontrado"
        
        password_hash = self.hash_password(password)
        
        if users[username]["password_hash"] != password_hash:
            return False, "Contraseña incorrecta"
        
        return True, "Login exitoso"
    
    def get_user_info(self, username):
        users = self.load_users()
        return users.get(username, {})
    
    def create_user_folder(self, user_id):
        user_folder = os.path.join(self.data_folder, user_id)
        
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
            
            initial_data = {
                'consultas': [],
                'config': {
                    'costo_por_hora': 21.68,
                    'tipo_cambio': 1335,
                    'margen_ganancia': 0.40,
                    'region': 'Interior NOA/NEA'
                }
            }
            
            data_file = os.path.join(user_folder, 'dental_data.json')
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2, default=str)

# 5 - DataManager
class DataManager:
    """Manejo de datos del consultorio - Versión Multi-Usuario"""
    
    def __init__(self, user_id=None):
        if user_id:
            self.data_file = os.path.join("data", user_id, "dental_data.json")
        else:
            self.data_file = "dental_data.json"
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.consultas = pd.DataFrame(data.get('consultas', []))
                    self.config = data.get('config', self.get_default_config())
            except Exception as e:
                st.error(f"Error cargando datos: {e}")
                self.init_default_data()
        else:
            self.init_default_data()
    
    def init_default_data(self):
        self.consultas = pd.DataFrame(columns=[
            'fecha', 'paciente', 'tratamiento', 'monto_ars', 'monto_usd', 'medio_pago'
        ])
        self.config = self.get_default_config()
    
    def get_default_config(self):
        return {
            'costo_por_hora': 21.68,
            'tipo_cambio': 1335,
            'margen_ganancia': 0.40,
            'region': 'Interior NOA/NEA'
        }
    
    def save_data(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            data = {
                'consultas': self.consultas.to_dict('records'),
                'config': self.config
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            st.error(f"Error guardando datos: {e}")
            return False
    
    def add_consulta(self, paciente, tratamiento, monto_ars, medio_pago):
        monto_usd = monto_ars / self.config['tipo_cambio']
        nueva_consulta = {
            'fecha': datetime.now().isoformat(),
            'paciente': paciente,
            'tratamiento': tratamiento,
            'monto_ars': monto_ars,
            'monto_usd': round(monto_usd, 2),
            'medio_pago': medio_pago
        }
        
        if self.consultas.empty:
            self.consultas = pd.DataFrame([nueva_consulta])
        else:
            self.consultas = pd.concat([self.consultas, pd.DataFrame([nueva_consulta])], ignore_index=True)
        
        self.save_data()
        return nueva_consulta
    
    def get_resumen(self):
        if self.consultas.empty:
            return {
                'total_consultas': 0,
                'ingreso_total': 0,
                'promedio_consulta': 0,
                'tratamiento_popular': 'N/A',
                'ingresos_mes': 0
            }
        
        if not self.consultas.empty:
            self.consultas['fecha'] = pd.to_datetime(self.consultas['fecha'])
        
        total_consultas = len(self.consultas)
        ingreso_total = self.consultas['monto_usd'].sum()
        promedio_consulta = ingreso_total / total_consultas if total_consultas > 0 else 0
        
        tratamiento_popular = 'N/A'
        if not self.consultas.empty:
            tratamientos = self.consultas['tratamiento'].value_counts()
            if not tratamientos.empty:
                tratamiento_popular = tratamientos.index[0]
        
        fecha_actual = datetime.now()
        mes_actual = self.consultas[
            (self.consultas['fecha'].dt.month == fecha_actual.month) &
            (self.consultas['fecha'].dt.year == fecha_actual.year)
        ]
        ingresos_mes = mes_actual['monto_usd'].sum() if not mes_actual.empty else 0
        
        return {
            'total_consultas': total_consultas,
            'ingreso_total': round(ingreso_total, 2),
            'promedio_consulta': round(promedio_consulta, 2),
            'tratamiento_popular': tratamiento_popular,
            'ingresos_mes': round(ingresos_mes, 2)
        }

# 6 - Funciones auxiliares
def calculate_price_optimized(time_hours: float, materials_usd: float, cost_per_hour: float, margin: float = 0.40):
    """Calcular precio optimizado"""
    if time_hours <= 0 or materials_usd < 0:
        raise ValueError("Horas debe ser > 0 y materiales >= 0")
    
    labor_cost = time_hours * cost_per_hour
    total_cost = labor_cost + materials_usd
    final_price = total_cost * (1 + margin)
    
    return {
        'time_hours': time_hours,
        'cost_per_hour': cost_per_hour,
        'mano_obra': round(labor_cost, 2),
        'materiales': materials_usd,
        'costo_total': round(total_cost, 2),
        'precio_final': round(final_price),
        'margen': margin * 100
    }

def extraer_monto_numerico(monto_str):
    """Extrae valor numérico de string de monto - Mejorada"""
    try:
        if pd.isna(monto_str):
            return 0
        
        monto_clean = str(monto_str).strip()
        
        # Remover símbolos comunes de moneda y separadores
        monto_clean = re.sub(r'[$€£¥₹₽₩¢]', '', monto_clean)  # Símbolos de moneda
        monto_clean = re.sub(r'[^\d.,\-]', '', monto_clean)    # Solo números, comas, puntos y minus
        
        if not monto_clean:
            return 0
        
        # Manejar números negativos
        es_negativo = monto_clean.startswith('-')
        monto_clean = monto_clean.lstrip('-')
        
        # Determinar si el último punto/coma son decimales
        if ',' in monto_clean and '.' in monto_clean:
            # Ambos presentes - el último es decimal
            if monto_clean.rfind(',') > monto_clean.rfind('.'):
                # Coma es decimal: 1.234.567,89
                monto_clean = monto_clean.replace('.', '').replace(',', '.')
            else:
                # Punto es decimal: 1,234,567.89
                monto_clean = monto_clean.replace(',', '')
        elif ',' in monto_clean:
            # Solo comas - podría ser decimal o separador de miles
            if monto_clean.count(',') == 1 and len(monto_clean.split(',')[1]) <= 2:
                # Probablemente decimal: 1234,56
                monto_clean = monto_clean.replace(',', '.')
            else:
                # Separador de miles: 1,234,567
                monto_clean = monto_clean.replace(',', '')
        
        resultado = float(monto_clean)
        return -resultado if es_negativo else resultado
        
    except Exception as e:
        st.warning(f"No se pudo procesar monto '{monto_str}': {e}")
        return 0

def normalizar_fecha_flexible(fecha_valor):
    """Normaliza fechas de múltiples formatos"""
    try:
        if pd.isna(fecha_valor):
            return datetime.now().isoformat()
        
        fecha_str = str(fecha_valor).strip()
        
        # Lista amplia de formatos de fecha
        formatos_fecha = [
            # Formatos dd/mm/yyyy
            '%d/%m/%Y', '%d/%m/%y',
            '%d-%m-%Y', '%d-%m-%y',
            '%d.%m.%Y', '%d.%m.%y',
            
            # Formatos mm/dd/yyyy
            '%m/%d/%Y', '%m/%d/%y',
            '%m-%d-%Y', '%m-%d-%y',
            
            # Formatos yyyy-mm-dd (ISO)
            '%Y-%m-%d', '%Y/%m/%d',
            '%Y.%m.%d', '%Y_%m_%d',
            
            # Con hora
            '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M',
            '%d-%m-%Y %H:%M:%S', '%d-%m-%Y %H:%M',
            '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
            
            # Formatos con texto
            '%d de %B de %Y', '%d %B %Y',
            '%B %d, %Y', '%d %b %Y',
        ]
        
        # Intentar cada formato
        for formato in formatos_fecha:
            try:
                fecha_parsed = datetime.strptime(fecha_str, formato)
                return fecha_parsed.isoformat()
            except ValueError:
                continue
        
        # Si no funciona ningún formato, usar pandas
        try:
            fecha_pandas = pd.to_datetime(fecha_str, dayfirst=True, errors='coerce')
            if not pd.isna(fecha_pandas):
                return fecha_pandas.isoformat()
        except:
            pass
        
        # Último recurso: fecha actual
        st.warning(f"No se pudo procesar fecha '{fecha_valor}', usando fecha actual")
        return datetime.now().isoformat()
        
    except Exception as e:
        st.warning(f"Error procesando fecha '{fecha_valor}': {e}")
        return datetime.now().isoformat()

def show_migration_tool_flexible(data_manager):
    """Herramienta de migración flexible para cualquier CSV"""
    st.subheader("📥 Migración Flexible de Datos")
    
    st.markdown("""
    **🚀 Migración Universal de CSV**
    
    Esta herramienta puede trabajar con cualquier archivo CSV:
    - ✅ Mapea automáticamente las columnas de tu archivo
    - 🔄 Convierte formatos de fecha y moneda
    - 🎭 Mantiene los datos tal como están
    - 📊 Vista previa antes de migrar
    """)
    
    # 1. SELECCIÓN DE ARCHIVO
    uploaded_file = st.file_uploader(
        "📁 Sube tu archivo CSV", 
        type=['csv'],
        help="Sube cualquier archivo CSV con datos de consultas"
    )
    
    if uploaded_file is not None:
        try:
            # Detectar encoding
            encoding_options = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            df = None
            encoding_usado = None
            
            for encoding in encoding_options:
                try:
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    encoding_usado = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                st.error("❌ No se pudo leer el archivo. Verifica el formato.")
                return
            
            st.success(f"✅ Archivo cargado correctamente (encoding: {encoding_usado})")
            
            # 2. VISTA PREVIA DEL ARCHIVO
            with st.expander("👀 Vista Previa del Archivo", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Total Registros", len(df))
                with col2:
                    st.metric("📋 Columnas", len(df.columns))
                with col3:
                    st.metric("💾 Tamaño", f"{uploaded_file.size / 1024:.1f} KB")
                
                st.markdown("**Primeras 5 filas:**")
                st.dataframe(df.head(), use_container_width=True)
                
                st.markdown("**Columnas disponibles:**")
                st.write(", ".join(df.columns.tolist()))
            
            # 3. MAPEO DE COLUMNAS
            st.subheader("🗺️ Mapeo de Columnas")
            st.markdown("Indica qué columna de tu CSV corresponde a cada campo:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📋 Campos Obligatorios:**")
                
                col_paciente = st.selectbox(
                    "👤 Columna de Pacientes *",
                    options=['-- Seleccionar --'] + df.columns.tolist(),
                    help="Columna que contiene los nombres de los pacientes"
                )
                
                col_tratamiento = st.selectbox(
                    "🦷 Columna de Tratamientos *",
                    options=['-- Seleccionar --'] + df.columns.tolist(),
                    help="Columna que describe el tratamiento realizado"
                )
                
                col_monto = st.selectbox(
                    "💰 Columna de Montos *",
                    options=['-- Seleccionar --'] + df.columns.tolist(),
                    help="Columna con el precio/monto del tratamiento"
                )
            
            with col2:
                st.markdown("**📅 Campos Opcionales:**")
                
                col_fecha = st.selectbox(
                    "📅 Columna de Fechas",
                    options=['-- Usar fecha actual --'] + df.columns.tolist(),
                    help="Columna con la fecha de la consulta"
                )
                
                col_medio_pago = st.selectbox(
                    "💳 Columna de Medio de Pago",
                    options=['-- Usar "No especificado" --'] + df.columns.tolist(),
                    help="Columna que indica cómo se pagó"
                )
                
                # Configuración de moneda
                st.markdown("**💱 Configuración de Moneda:**")
                
                tipo_moneda = st.radio(
                    "¿En qué moneda están los montos?",
                    options=["ARS (Pesos Argentinos)", "USD (Dólares)", "Detectar automáticamente"],
                    help="Indica la moneda de los montos en tu CSV"
                )
            
            # 4. VISTA PREVIA DEL MAPEO
            if (col_paciente != '-- Seleccionar --' and 
                col_tratamiento != '-- Seleccionar --' and 
                col_monto != '-- Seleccionar --'):
                
                st.subheader("👁️ Vista Previa del Mapeo")
                
                # Crear muestra de cómo se verán los datos
                muestra = df.head(5).copy()
                
                preview_data = []
                for _, row in muestra.iterrows():
                    # Procesar fecha
                    if col_fecha == '-- Usar fecha actual --':
                        fecha_procesada = datetime.now().strftime('%d/%m/%Y')
                    else:
                        fecha_raw = row[col_fecha]
                        fecha_iso = normalizar_fecha_flexible(fecha_raw)
                        fecha_procesada = datetime.fromisoformat(fecha_iso).strftime('%d/%m/%Y')
                    
                    # Procesar monto
                    monto_raw = row[col_monto]
                    monto_procesado = extraer_monto_numerico(monto_raw)
                    
                    # Procesar medio de pago
                    if col_medio_pago == '-- Usar "No especificado" --':
                        medio_pago = "No especificado"
                    else:
                        medio_pago = str(row[col_medio_pago]) if pd.notna(row[col_medio_pago]) else "No especificado"
                    
                    preview_data.append({
                        'Fecha': fecha_procesada,
                        'Paciente': str(row[col_paciente]),
                        'Tratamiento': str(row[col_tratamiento]),
                        'Monto Original': str(monto_raw),
                        'Monto Procesado': f"${monto_procesado:,.2f}",
                        'Medio de Pago': medio_pago
                    })
                
                preview_df = pd.DataFrame(preview_data)
                st.dataframe(preview_df, use_container_width=True)
                
                # 5. ESTADÍSTICAS PRE-MIGRACIÓN
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    pacientes_unicos = df[col_paciente].nunique()
                    st.metric("👥 Pacientes Únicos", pacientes_unicos)
                
                with col2:
                    tratamientos_unicos = df[col_tratamiento].nunique()
                    st.metric("🦷 Tipos de Tratamiento", tratamientos_unicos)
                
                with col3:
                    # Calcular total estimado
                    montos_procesados = df[col_monto].apply(extraer_monto_numerico)
                    total_estimado = montos_procesados.sum()
                    
                    if tipo_moneda == "ARS (Pesos Argentinos)":
                        total_usd = total_estimado / data_manager.config['tipo_cambio']
                        st.metric("💰 Total Estimado", f"${total_usd:,.0f} USD")
                    elif tipo_moneda == "USD (Dólares)":
                        st.metric("💰 Total Estimado", f"${total_estimado:,.0f} USD")
                    else:  # Auto-detectar
                        avg_monto = montos_procesados.mean()
                        if avg_monto > 1000:
                            # Probablemente ARS
                            total_usd = total_estimado / data_manager.config['tipo_cambio']
                            st.metric("💰 Total Est. (ARS→USD)", f"${total_usd:,.0f} USD")
                        else:
                            # Probablemente USD
                            st.metric("💰 Total Est. (USD)", f"${total_estimado:,.0f} USD")
                
                with col4:
                    registros_validos = len(df.dropna(subset=[col_paciente, col_tratamiento, col_monto]))
                    st.metric("✅ Registros Válidos", registros_validos)
                
                # 6. BOTÓN DE MIGRACIÓN
                st.markdown("---")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("### 🚀 ¿Todo se ve correcto?")
                    st.markdown("Revisa la vista previa y las estadísticas antes de proceder.")
                
                with col2:
                    if st.button("🚀 Ejecutar Migración", type="primary", use_container_width=True):
                        # EJECUTAR MIGRACIÓN
                        with st.spinner("⏳ Migrando datos..."):
                            resultado = ejecutar_migracion_flexible(
                                df=df,
                                col_paciente=col_paciente,
                                col_tratamiento=col_tratamiento,
                                col_monto=col_monto,
                                col_fecha=col_fecha if col_fecha != '-- Usar fecha actual --' else None,
                                col_medio_pago=col_medio_pago if col_medio_pago != '-- Usar "No especificado" --' else None,
                                tipo_moneda=tipo_moneda,
                                data_manager=data_manager
                            )
                        
                        # MOSTRAR RESULTADOS
                        if resultado['success']:
                            st.success("✅ ¡Migración completada exitosamente!")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📥 Registros Migrados", resultado['migrados'])
                            with col2:
                                st.metric("❌ Errores", resultado['errores'])
                            with col3:
                                st.metric("💰 Total Migrado", f"${resultado['total_usd']:.2f} USD")
                            
                            if resultado['errores'] > 0:
                                st.warning(f"⚠️ {resultado['errores']} registros tuvieron problemas y no se migraron")
                            
                            st.info("🔄 Recarga la página para ver los datos migrados en el Dashboard")
                            
                            if st.button("🔄 Recargar Aplicación"):
                                st.rerun()
                        
                        else:
                            st.error(f"❌ Error en la migración: {resultado['error']}")
            
            else:
                st.info("👆 Por favor selecciona al menos las columnas obligatorias para continuar")
        
        except Exception as e:
            st.error(f"❌ Error procesando el archivo: {e}")
    
    else:
        # INFORMACIÓN DE AYUDA CUANDO NO HAY ARCHIVO
        st.info("📁 Sube un archivo CSV para comenzar")
        
        with st.expander("💡 Formatos de CSV Compatibles"):
            st.markdown("""
            **Esta herramienta puede trabajar con CSVs que contengan:**
            
            📋 **Columnas típicas:**
            - Nombres de pacientes (cualquier nombre de columna)
            - Tratamientos o servicios realizados
            - Montos/precios (en cualquier formato)
            - Fechas (múltiples formatos soportados)
            - Medios de pago (opcional)
            
            💰 **Formatos de montos soportados:**
            - `1234.56`, `1,234.56`, `1.234,56`
            - `$1,234.56`, `USD 1234`, `€ 1.234,56`
            - Montos negativos: `-1234.56`
            
            📅 **Formatos de fecha soportados:**
            - `dd/mm/yyyy`, `mm/dd/yyyy`, `yyyy-mm-dd`
            - `dd-mm-yyyy`, `dd.mm.yyyy`
            - Con hora: `dd/mm/yyyy hh:mm:ss`
            
            🌍 **Encodings soportados:**
            - UTF-8, Latin-1, CP1252, ISO-8859-1
            """)

def ejecutar_migracion_flexible(df, col_paciente, col_tratamiento, col_monto, 
                               col_fecha=None, col_medio_pago=None, 
                               tipo_moneda="Detectar automáticamente", data_manager=None):
    """Ejecuta la migración flexible con mapeo de columnas"""
    
    try:
        consultas_migradas = []
        errores = 0
        total_usd = 0
        
        for index, row in df.iterrows():
            try:
                # Procesar fecha
                if col_fecha:
                    fecha = normalizar_fecha_flexible(row[col_fecha])
                else:
                    fecha = datetime.now().isoformat()
                
                # Procesar paciente
                paciente = str(row[col_paciente]).strip() if pd.notna(row[col_paciente]) else f'Paciente_{index+1}'
                
                # Procesar tratamiento
                tratamiento = str(row[col_tratamiento]).strip() if pd.notna(row[col_tratamiento]) else 'Consulta'
                
                # Procesar monto
                monto_numerico = extraer_monto_numerico(row[col_monto])
                
                if monto_numerico <= 0:
                    errores += 1
                    continue
                
                # Determinar ARS y USD según configuración
                if tipo_moneda == "ARS (Pesos Argentinos)":
                    monto_ars = monto_numerico
                    monto_usd = monto_numerico / data_manager.config['tipo_cambio']
                elif tipo_moneda == "USD (Dólares)":
                    monto_usd = monto_numerico
                    monto_ars = monto_numerico * data_manager.config['tipo_cambio']
                else:  # Auto-detectar
                    if monto_numerico > 1000:  # Probablemente ARS
                        monto_ars = monto_numerico
                        monto_usd = monto_numerico / data_manager.config['tipo_cambio']
                    else:  # Probablemente USD
                        monto_usd = monto_numerico
                        monto_ars = monto_numerico * data_manager.config['tipo_cambio']
                
                # Procesar medio de pago
                if col_medio_pago:
                    medio_pago = str(row[col_medio_pago]).strip() if pd.notna(row[col_medio_pago]) else 'No especificado'
                else:
                    medio_pago = 'No especificado'
                
                # Crear consulta
                consulta = {
                    'fecha': fecha,
                    'paciente': paciente,
                    'tratamiento': tratamiento,
                    'monto_ars': round(monto_ars, 2),
                    'monto_usd': round(monto_usd, 2),
                    'medio_pago': medio_pago
                }
                
                consultas_migradas.append(consulta)
                total_usd += monto_usd
                
            except Exception as e:
                errores += 1
                st.warning(f"Error en fila {index+1}: {e}")
                continue
        
        # Agregar a data_manager
        if consultas_migradas:
            for consulta in consultas_migradas:
                nueva_fila = {
                    'fecha': consulta['fecha'],
                    'paciente': consulta['paciente'], 
                    'tratamiento': consulta['tratamiento'],
                    'monto_ars': consulta['monto_ars'],
                    'monto_usd': consulta['monto_usd'],
                    'medio_pago': consulta['medio_pago']
                }
                
                if data_manager.consultas.empty:
                    data_manager.consultas = pd.DataFrame([nueva_fila])
                else:
                    data_manager.consultas = pd.concat([data_manager.consultas, pd.DataFrame([nueva_fila])], ignore_index=True)
            
            data_manager.save_data()
        
        return {
            'success': True,
            'migrados': len(consultas_migradas),
            'errores': errores,
            'total_usd': round(total_usd, 2)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'migrados': 0,
            'errores': 0,
            'total_usd': 0
        }

# Función wrapper para mantener compatibilidad
def show_migration_tool(data_manager):
    """Wrapper para la función de migración flexible"""
    show_migration_tool_flexible(data_manager)

def show_dashboard(data_manager, user_info):
    """Mostrar dashboard principal"""
    st.subheader(f"📊 Dashboard - {user_info.get('nombre', 'Usuario')}")
    
    resumen = data_manager.get_resumen()
    
    # Información de plan
    plan = user_info.get('plan', 'trial')
    if plan == 'trial':
        st.info("🎯 Plan de prueba activo. Sus datos son privados y están separados de otros usuarios.")
    elif plan == 'premium':
        st.success("⭐ Plan Premium activo. Acceso completo a todas las funcionalidades.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Ingresos Totales",
            f"${resumen['ingreso_total']} USD",
            delta=f"${resumen['ingresos_mes']} este mes"
        )
    
    with col2:
        st.metric("👥 Total Consultas", resumen['total_consultas'])
    
    with col3:
        st.metric("📊 Promedio/Consulta", f"${resumen['promedio_consulta']} USD")
    
    with col4:
        st.metric("🔥 Más Popular", resumen['tratamiento_popular'])
    
    if not data_manager.consultas.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Ingresos por Mes")
            
            df_monthly = data_manager.consultas.copy()
            df_monthly['fecha'] = pd.to_datetime(df_monthly['fecha'])
            df_monthly['mes'] = df_monthly['fecha'].dt.to_period('M')
            monthly_income = df_monthly.groupby('mes')['monto_usd'].sum().reset_index()
            monthly_income['mes'] = monthly_income['mes'].astype(str)
            
            fig_monthly = px.bar(
                monthly_income, 
                x='mes', 
                y='monto_usd',
                title="Ingresos Mensuales (USD)",
                color='monto_usd',
                color_continuous_scale='Blues'
            )
            fig_monthly.update_layout(showlegend=False)
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        with col2:
            st.subheader("🥧 Tratamientos Realizados")
            
            tratamientos = data_manager.consultas['tratamiento'].value_counts()
            
            fig_pie = px.pie(
                values=tratamientos.values,
                names=tratamientos.index,
                title="Distribución de Tratamientos"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.subheader("📋 Últimas Consultas")
        
        recent_consultas = data_manager.consultas.tail(10).copy()
        if not recent_consultas.empty:
            recent_consultas['fecha'] = pd.to_datetime(recent_consultas['fecha']).dt.strftime('%d/%m/%Y %H:%M')
            recent_consultas = recent_consultas[['fecha', 'paciente', 'tratamiento', 'monto_usd', 'medio_pago']]
            recent_consultas.columns = ['Fecha', 'Paciente', 'Tratamiento', 'Monto (USD)', 'Medio de Pago']
            st.dataframe(recent_consultas, use_container_width=True)
    
    else:
        st.info("📝 No hay consultas registradas aún. ¡Comience agregando su primera consulta!")

def show_nueva_consulta(data_manager):
    """Formulario para nueva consulta"""
    st.subheader("➕ Registrar Nueva Consulta")
    
    with st.form("nueva_consulta"):
        col1, col2 = st.columns(2)
        
        with col1:
            paciente = st.text_input("👤 Nombre del Paciente *", placeholder="Ej: Juan Pérez")
            tratamiento = st.selectbox(
                "🦷 Tipo de Tratamiento *",
                ["Consulta", "Consulta de Urgencia", "Limpieza", "Operatoria Simple", 
                 "Operatoria Compleja", "Endodoncia Unirradicular", "Endodoncia Multirradicular",
                 "Placa Estabilizadora", "Provisorio", "Corona Metálica", "Corona de Porcelana",
                 "Extracción Simple", "Extracción Compleja", "Otro"]
            )
        
        with col2:
            monto_ars = st.number_input("💰 Monto en ARS *", min_value=0.0, step=1000.0, value=30000.0)
            medio_pago = st.selectbox(
                "💳 Medio de Pago *",
                ["Efectivo", "Transferencia", "Débito", "Crédito", "Mercado Pago", "Otros"]
            )
        
        monto_usd = monto_ars / data_manager.config['tipo_cambio']
        st.info(f"💱 Equivalente en USD: ${monto_usd:.2f} (TC: ${data_manager.config['tipo_cambio']})")
        
        submitted = st.form_submit_button("✅ Registrar Consulta", type="primary")
        
        if submitted:
            if paciente and tratamiento and monto_ars > 0:
                try:
                    nueva_consulta = data_manager.add_consulta(paciente, tratamiento, monto_ars, medio_pago)
                    st.success(f"✅ Consulta registrada: {paciente} - {tratamiento} - ${monto_ars:,.0f} ARS")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al registrar consulta: {e}")
            else:
                st.error("❌ Por favor complete todos los campos obligatorios (*)")

def show_calculadora_precios(data_manager):
    """Calculadora de precios optimizada"""
    st.subheader("💰 Calculadora de Precios")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("calculadora"):
            st.write("📊 Parámetros del Tratamiento")
            
            time_hours = st.number_input(
                "⏱️ Tiempo estimado (horas) *", 
                min_value=0.1, 
                max_value=10.0, 
                value=1.0, 
                step=0.25
            )
            
            materials_usd = st.number_input(
                "🧪 Costo de materiales (USD) *", 
                min_value=0.0, 
                value=5.0, 
                step=1.0
            )
            
            tratamiento_calc = st.text_input(
                "🦷 Nombre del tratamiento (opcional)", 
                placeholder="Ej: Operatoria simple"
            )
            
            calcular = st.form_submit_button("🧮 Calcular Precio", type="primary")
            
            if calcular:
                try:
                    resultado = calculate_price_optimized(
                        time_hours, 
                        materials_usd, 
                        data_manager.config['costo_por_hora'],
                        data_manager.config['margen_ganancia']
                    )
                    
                    st.session_state.ultimo_calculo = resultado
                    
                except Exception as e:
                    st.error(f"❌ Error en cálculo: {e}")
    
    with col2:
        st.write("⚙️ Configuración Actual")
        st.metric("💼 Costo por Hora", f"${data_manager.config['costo_por_hora']} USD")
        st.metric("📊 Margen", f"{data_manager.config['margen_ganancia']*100:.0f}%")
        st.metric("💱 Tipo de Cambio", f"${data_manager.config['tipo_cambio']} ARS")
    
    if hasattr(st.session_state, 'ultimo_calculo'):
        resultado = st.session_state.ultimo_calculo
        
        st.markdown("---")
        st.subheader("📋 Resultado del Cálculo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👷 Mano de Obra", f"${resultado['mano_obra']} USD")
        
        with col2:
            st.metric("🧪 Materiales", f"${resultado['materiales']} USD")
        
        with col3:
            st.metric("💰 Costo Total", f"${resultado['costo_total']} USD")
        
        with col4:
            st.metric("🎯 Precio Final", f"${resultado['precio_final']} USD")
        
        precio_ars = resultado['precio_final'] * data_manager.config['tipo_cambio']
        st.info(f"💱 Precio en ARS: ${precio_ars:,.0f}")

def show_configuracion(data_manager):
    """Configuración del sistema"""
    st.subheader("⚙️ Configuración del Sistema")
    
    with st.form("configuracion"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("💼 Configuración Profesional")
            
            nuevo_costo = st.number_input(
                "💰 Costo por Hora (USD)",
                min_value=1.0,
                value=data_manager.config['costo_por_hora'],
                step=0.50
            )
            
            nuevo_margen = st.slider(
                "📊 Margen de Ganancia (%)",
                min_value=10,
                max_value=100,
                value=int(data_manager.config['margen_ganancia'] * 100),
                step=5
            ) / 100
        
        with col2:
            st.write("🌍 Configuración Regional")
            
            nueva_region = st.selectbox(
                "📍 Su Región",
                ["CABA", "GBA Norte", "GBA Sur", "La Plata", "Córdoba Capital", 
                 "Rosario", "Mendoza", "Tucumán", "Interior Pampeano", 
                 "Interior NOA/NEA", "Patagonia Norte", "Patagonia Sur"],
                index=["CABA", "GBA Norte", "GBA Sur", "La Plata", "Córdoba Capital", 
                       "Rosario", "Mendoza", "Tucumán", "Interior Pampeano", 
                       "Interior NOA/NEA", "Patagonia Norte", "Patagonia Sur"].index(data_manager.config['region'])
            )
            
            nuevo_cambio = st.number_input(
                "💱 Tipo de Cambio ARS/USD",
                min_value=1.0,
                value=float(data_manager.config['tipo_cambio']),
                step=10.0
            )
        
        guardar = st.form_submit_button("💾 Guardar Configuración", type="primary")
        
        if guardar:
            data_manager.config.update({
                'costo_por_hora': nuevo_costo,
                'margen_ganancia': nuevo_margen,
                'region': nueva_region,
                'tipo_cambio': nuevo_cambio
            })
            
            if data_manager.save_data():
                st.success("✅ Configuración guardada exitosamente")
                st.rerun()
            else:
                st.error("❌ Error al guardar configuración")

def show_reportes(data_manager):
    """Mostrar reportes detallados"""
    st.subheader("📈 Reportes Detallados")
    
    if data_manager.consultas.empty:
        st.info("📝 No hay datos suficientes para generar reportes. Agregue algunas consultas primero.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("📅 Fecha Inicio", value=date.today().replace(day=1))
    
    with col2:
        fecha_fin = st.date_input("📅 Fecha Fin", value=date.today())
    
    df_filtrado = data_manager.consultas.copy()
    df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'])
    df_filtrado = df_filtrado[
        (df_filtrado['fecha'].dt.date >= fecha_inicio) & 
        (df_filtrado['fecha'].dt.date <= fecha_fin)
    ]
    
    if df_filtrado.empty:
        st.warning("⚠️ No hay datos en el rango de fechas seleccionado")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Consultas", len(df_filtrado))
    
    with col2:
        ingresos_periodo = df_filtrado['monto_usd'].sum()
        st.metric("💰 Ingresos", f"${ingresos_periodo:.2f} USD")
    
    with col3:
        promedio_periodo = df_filtrado['monto_usd'].mean()
        st.metric("📊 Promedio", f"${promedio_periodo:.2f} USD")
    
    with col4:
        dias_periodo = (fecha_fin - fecha_inicio).days + 1
        consultas_por_dia = len(df_filtrado) / dias_periodo
        st.metric("📅 Consultas/Día", f"{consultas_por_dia:.1f}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Evolución Diaria")
        
        df_diario = df_filtrado.groupby(df_filtrado['fecha'].dt.date).agg({
            'monto_usd': 'sum',
            'paciente': 'count'
        }).reset_index()
        df_diario.columns = ['fecha', 'ingresos', 'consultas']
        
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Scatter(
            x=df_diario['fecha'],
            y=df_diario['ingresos'],
            mode='lines+markers',
            name='Ingresos USD',
            line=dict(color='#3b82f6')
        ))
        
        fig_daily.update_layout(
            title="Ingresos Diarios",
            xaxis_title="Fecha",
            yaxis_title="Ingresos (USD)"
        )
        st.plotly_chart(fig_daily, use_container_width=True)
    
    with col2:
        st.subheader("💳 Medios de Pago")
        
        medios_pago = df_filtrado.groupby('medio_pago')['monto_usd'].sum()
        
        fig_payment = px.pie(
            values=medios_pago.values,
            names=medios_pago.index,
            title="Distribución por Medio de Pago"
        )
        st.plotly_chart(fig_payment, use_container_width=True)
    
    st.subheader("📋 Detalle de Consultas")
    
    df_display = df_filtrado.copy()
    df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y %H:%M')
    df_display = df_display[['fecha', 'paciente', 'tratamiento', 'monto_ars', 'monto_usd', 'medio_pago']]
    df_display.columns = ['Fecha', 'Paciente', 'Tratamiento', 'Monto ARS', 'Monto USD', 'Medio Pago']
    
    df_display['Monto ARS'] = df_display['Monto ARS'].apply(lambda x: f"${x:,.0f}")
    df_display['Monto USD'] = df_display['Monto USD'].apply(lambda x: f"${x:.2f}")
    
    st.dataframe(df_display, use_container_width=True)
    
    if st.button("📥 Exportar Reporte a CSV"):
        csv = df_display.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="💾 Descargar CSV",
            data=csv,
            file_name=f"reporte_dental_{fecha_inicio}_{fecha_fin}.csv",
            mime="text/csv"
        )

def show_login():
    """Pantalla de login segura"""
    st.title("🦷 Sistema de Gestión de Consultorios Odontológicos - Login")
    
    # Solo mostrar información básica, NO las credenciales
    with st.expander("ℹ️ Información del Sistema"):
        st.markdown("""
        **Sistema de Gestión Dental v2.0**
        
        ✨ **Características:**
        - Dashboard con métricas en tiempo real
        - Gestión de consultas y pacientes
        - Calculadora de precios profesional
        - Reportes detallados y exportación
        - Sistema multi-usuario con datos separados
        
        🔐 **Acceso:**
        - Cada usuario tiene sus propios datos privados
        - Sistema de autenticación seguro
        - Datos completamente separados entre usuarios
        
        📞 **Soporte:**
        - Para obtener credenciales de acceso, contacte al administrador
        - Demo disponible para evaluación
        """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.write("🔋 Ingresar al Sistema")
            
            username = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña")
            
            # Checkbox para mostrar hint de demo (opcional)
            show_demo_hint = st.checkbox("🎯 Mostrar usuarios de demo")
            
            if show_demo_hint:
                st.info("""
                **Usuarios de prueba disponibles:**
                
                👨‍⚕️ **Administrador**: `admin` / `admin123`
                👩‍⚕️ **Demo 1**: `demo1` / `demo123`  
                🦷 **Demo 2**: `demo2` / `demo123`
                
                ⚠️ Solo para evaluación del sistema
                """)
            
            login_button = st.form_submit_button("🚀 Ingresar", use_container_width=True)
            
            if login_button:
                if username and password:
                    user_manager = UserManager()
                    is_valid, message = user_manager.validate_user(username, password)
                    
                    if is_valid:
                        st.session_state.authenticated = True
                        st.session_state.user_id = username
                        st.session_state.user_info = user_manager.get_user_info(username)
                        
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                        # Hint sutil para usuarios que tienen problemas
                        if "Usuario no encontrado" in message:
                            st.info("💡 Tip: Verifique el nombre de usuario. Para demo, active el checkbox superior.")
                else:
                    st.warning("⚠️ Por favor complete todos los campos")
    
    # Footer con información de contacto (sin credenciales)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
        📧 ¿Necesita acceso? Contacte al administrador del sistema<br>
        🔒 Sistema seguro - Datos protegidos y privados
        </div>
        """, unsafe_allow_html=True)

def main():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        show_login()
        return
    
    user_id = st.session_state.user_id
    user_info = st.session_state.user_info
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown('<h1 class="main-header">🦷 Sistema de Gestión de Consultorios Odontológicos v2.0</h1>', unsafe_allow_html=True)
    
    with col2:
        st.write(f"👤 {user_info.get('nombre', user_id)}")
    
    with col3:
        if st.button("🚪 Cerrar Sesión"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager(user_id=user_id)
    
    data_manager = st.session_state.data_manager
    
    with st.sidebar:
        # SIDEBAR SIN IMAGEN ROTA
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%); border-radius: 0.5rem; margin-bottom: 1rem; color: white;'>
        <h3>🦷 Dental v2.0</h3>
        <p style='margin: 0; font-size: 0.9em;'>Sistema de Gestión</p>
        </div>
        """, unsafe_allow_html=True)
        
        # MENÚ SIMPLIFICADO (SIN BENCHMARKS)
        menu = st.selectbox(
            "📋 Menú Principal",
            ["🏠 Dashboard", "➕ Nueva Consulta", "💰 Calculadora de Precios", 
             "⚙️ Configuración", "📈 Reportes", "📥 Migrar Datos"]
        )
        
        st.markdown("---")
        
        resumen = data_manager.get_resumen()
        st.metric("💰 Ingresos Totales", f"${resumen['ingreso_total']} USD")
        st.metric("👥 Consultas", resumen['total_consultas'])
        st.metric("📊 Promedio", f"${resumen['promedio_consulta']} USD")
    
    # NAVEGACIÓN SIMPLIFICADA (SIN BENCHMARKS)
    if menu == "🏠 Dashboard":
        show_dashboard(data_manager, user_info)
    elif menu == "➕ Nueva Consulta":
        show_nueva_consulta(data_manager)
    elif menu == "💰 Calculadora de Precios":
        show_calculadora_precios(data_manager)
    elif menu == "⚙️ Configuración":
        show_configuracion(data_manager)
    elif menu == "📈 Reportes":
        show_reportes(data_manager)
    elif menu == "📥 Migrar Datos":
        show_migration_tool(data_manager)

if __name__ == "__main__":
    main()