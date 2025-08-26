import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
import os
import re
from typing import Dict, List, Tuple
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="🦷 Gestión Dental v2.0",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
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

class BenchmarksManager:
    """Manejo de benchmarks oficiales"""
    
    @staticmethod
    def get_benchmarks_config():
        return {
            'version': '2025.2',
            'fecha_actualizacion': '2025-08-12',
            'proxima_revision': '2026-02-01',
            'fuentes': 'Colegios Odontológicos Oficiales + Market Research',
            'dolar_referencia': 1335,
            'precios_base_ars': {
                'consulta': 32916,
                'consulta_urgencia': 38149,
                'limpieza': 42343,
                'operatoria_simple': 52350,
                'operatoria_compleja': 73521,
                'endodoncia_unirradicular': 105673,
                'endodoncia_multirradicular': 154496,
                'placa_estabilizadora': 150000,
                'provisorio': 60000,
                'corona_metalica': 270654,
                'corona_porcelana': 338321,
                'extraccion_simple': 71606,
                'extraccion_compleja': 159609
            },
            'ajustes_regionales': {
                'CABA': 1.4,
                'GBA Norte': 1.3,
                'GBA Sur': 1.2,
                'La Plata': 1.2,
                'Córdoba Capital': 1.15,
                'Rosario': 1.15,
                'Mendoza': 1.1,
                'Tucumán': 1.05,
                'Interior Pampeano': 1.0,
                'Interior NOA/NEA': 0.95,
                'Patagonia Norte': 1.2,
                'Patagonia Sur': 1.3
            },
            'metricas': {
                'consultas_mensual_promedio': 45,
                'horas_semanales_promedio': 35,
                'margen_minimo_sector': 25,
                'margen_optimo_sector': 40,
                'inflacion_anual_estimada': 80
            }
        }

class DataManager:
    """Manejo de datos del consultorio"""
    
    def __init__(self):
        self.data_file = "dental_data.json"
        self.load_data()
    
    def load_data(self):
        """Cargar datos desde archivo JSON"""
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
        """Inicializar datos por defecto"""
        self.consultas = pd.DataFrame(columns=[
            'fecha', 'paciente', 'tratamiento', 'monto_ars', 'monto_usd', 'medio_pago'
        ])
        self.config = self.get_default_config()
    
    def get_default_config(self):
        """Configuración por defecto"""
        return {
            'costo_por_hora': 21.68,
            'tipo_cambio': 1335,
            'horas_anuales': 520,
            'margen_ganancia': 0.40,
            'region': 'Interior NOA/NEA',
            'factor_regional': 0.95
        }
    
    def save_data(self):
        """Guardar datos en archivo JSON"""
        try:
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
    
    def add_consulta(self, paciente: str, tratamiento: str, monto_ars: float, medio_pago: str):
        """Agregar nueva consulta"""
        monto_usd = monto_ars / self.config['tipo_cambio']
        nueva_consulta = {
            'fecha': datetime.now().isoformat(),
            'paciente': paciente,
            'tratamiento': tratamiento,
            'monto_ars': monto_ars,
            'monto_usd': round(monto_usd, 2),
            'medio_pago': medio_pago
        }
        
        # Convertir a DataFrame si está vacío
        if self.consultas.empty:
            self.consultas = pd.DataFrame([nueva_consulta])
        else:
            self.consultas = pd.concat([self.consultas, pd.DataFrame([nueva_consulta])], ignore_index=True)
        
        self.save_data()
        return nueva_consulta
    
    def get_resumen(self):
        """Obtener resumen de datos"""
        if self.consultas.empty:
            return {
                'total_consultas': 0,
                'ingreso_total': 0,
                'promedio_consulta': 0,
                'tratamiento_popular': 'N/A',
                'ingresos_mes': 0
            }
        
        # Convertir fechas si es necesario
        if not self.consultas.empty:
            self.consultas['fecha'] = pd.to_datetime(self.consultas['fecha'])
        
        total_consultas = len(self.consultas)
        ingreso_total = self.consultas['monto_usd'].sum()
        promedio_consulta = ingreso_total / total_consultas if total_consultas > 0 else 0
        
        # Tratamiento más popular
        tratamiento_popular = 'N/A'
        if not self.consultas.empty:
            tratamientos = self.consultas['tratamiento'].value_counts()
            if not tratamientos.empty:
                tratamiento_popular = tratamientos.index[0]
        
        # Ingresos del mes actual
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

def main():
    # Inicializar managers
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    
    data_manager = st.session_state.data_manager
    benchmarks = BenchmarksManager.get_benchmarks_config()
    
    # Header principal
    st.markdown('<h1 class="main-header">🦷 Sistema de Gestión Dental v2.0</h1>', unsafe_allow_html=True)
    
    # Sidebar para navegación
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/3b82f6/ffffff?text=Dental+v2.0", width=200)
        
        menu = st.selectbox(
            "📋 Menú Principal",
            ["🏠 Dashboard", "➕ Nueva Consulta", "💰 Calculadora de Precios", 
             "📊 Benchmarks", "⚙️ Configuración", "📈 Reportes", "🎯 Planificación", "📥 Migrar Datos"]
        )
        
        st.markdown("---")
        
        # Información rápida
        resumen = data_manager.get_resumen()
        st.metric("💰 Ingresos Totales", f"${resumen['ingreso_total']} USD")
        st.metric("👥 Consultas", resumen['total_consultas'])
        st.metric("📊 Promedio", f"${resumen['promedio_consulta']} USD")
    
    # Contenido principal según menú seleccionado
    if menu == "🏠 Dashboard":
        show_dashboard(data_manager, benchmarks)
    elif menu == "➕ Nueva Consulta":
        show_nueva_consulta(data_manager)
    elif menu == "💰 Calculadora de Precios":
        show_calculadora_precios(data_manager)
    elif menu == "📊 Benchmarks":
        show_benchmarks(data_manager, benchmarks)
    elif menu == "⚙️ Configuración":
        show_configuracion(data_manager, benchmarks)
    elif menu == "📈 Reportes":
        show_reportes(data_manager)
    elif menu == "📥 Migrar Datos":
        show_migration_tool(data_manager)

def extraer_monto_numerico(monto_str):
    """Extrae valor numérico de string de monto"""
    try:
        if pd.isna(monto_str):
            return 0
        
        # Convertir a string y limpiar
        monto_clean = str(monto_str).strip()
        
        # Remover símbolos ($, espacios, comas para miles)
        monto_clean = re.sub(r'[$\s]', '', monto_clean)
        
        # Reemplazar comas por puntos para decimales
        monto_clean = monto_clean.replace(',', '.')
        
        # Si quedó vacío
        if not monto_clean:
            return 0
        
        return float(monto_clean)
        
    except Exception as e:
        st.error(f"Error extrayendo monto de '{monto_str}': {e}")
        return 0

def normalizar_fecha_csv(fecha_valor):
    """Normaliza fechas del CSV"""
    try:
        if pd.isna(fecha_valor):
            return datetime.now().isoformat()
        
        fecha_str = str(fecha_valor).strip()
        
        # Formatos comunes argentinos
        formatos = [
            '%d/%m/%Y',
            '%d-%m-%Y', 
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d-%m-%Y %H:%M:%S'
        ]
        
        for formato in formatos:
            try:
                fecha_parsed = datetime.strptime(fecha_str, formato)
                return fecha_parsed.isoformat()
            except:
                continue
        
        # Usar pandas como fallback
        try:
            fecha_pandas = pd.to_datetime(fecha_str, dayfirst=True)
            return fecha_pandas.isoformat()
        except:
            return datetime.now().isoformat()
        
    except:
        return datetime.now().isoformat()

def show_migration_tool(data_manager):
    """Herramienta de migración integrada en Streamlit"""
    st.subheader("📥 Migrar Datos Históricos")
    
    st.markdown("""
    Esta herramienta te permite migrar datos desde tu CSV de Google Sheets al sistema.
    
    **Pasos:**
    1. Asegúrate que `ingresos.csv` esté en la carpeta del proyecto
    2. Revisa la vista previa de datos
    3. Ejecuta la migración
    """)
    
    # Verificar si existe el CSV
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not csv_files:
        st.warning("No se encontraron archivos CSV en el proyecto.")
        st.markdown("**Para migrar datos:**")
        st.markdown("1. Exporta tu Google Sheets como CSV")
        st.markdown("2. Sube el archivo al repositorio GitHub")
        st.markdown("3. Reinicia la app en Streamlit Cloud")
        return
    
    st.success(f"Archivos CSV encontrados: {', '.join(csv_files)}")
    
    # Seleccionar archivo a migrar
    archivo_seleccionado = st.selectbox("Selecciona archivo CSV:", csv_files)
    
    if archivo_seleccionado:
        try:
            # Vista previa del CSV
            st.subheader("👀 Vista Previa de Datos")
            
            df_preview = pd.read_csv(archivo_seleccionado, nrows=10)
            st.dataframe(df_preview, use_container_width=True)
            
            # Información del archivo
            df_full = pd.read_csv(archivo_seleccionado)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Registros", len(df_full))
            with col2:
                st.metric("Columnas", len(df_full.columns))
            with col3:
                # Estimar total en USD
                if 'Monto Total' in df_full.columns:
                    montos_ejemplo = df_full['Monto Total'].dropna().head(5)
                    total_estimado = 0
                    for monto in montos_ejemplo:
                        monto_num = extraer_monto_numerico(monto)
                        if monto_num > 1000:  # ARS
                            total_estimado += monto_num / 1335
                        else:  # USD
                            total_estimado += monto_num
                    
                    promedio_estimado = total_estimado / min(len(montos_ejemplo), 5)
                    total_proyecto = promedio_estimado * len(df_full)
                    st.metric("Ingreso Est. Total", f"${total_proyecto:,.0f} USD")
            
            # Análisis de columnas
            st.subheader("📋 Análisis de Columnas")
            
            for col in df_full.columns:
                with st.expander(f"Columna: {col}"):
                    valores_unicos = df_full[col].nunique()
                    valores_nulos = df_full[col].isna().sum()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Valores únicos:** {valores_unicos}")
                        st.write(f"**Valores nulos:** {valores_nulos}")
                    
                    with col2:
                        # Mostrar ejemplos
                        ejemplos = df_full[col].dropna().head(3).tolist()
                        st.write(f"**Ejemplos:** {ejemplos}")
            
            # Botón de migración
            st.markdown("---")
            
            if st.button("🚀 Ejecutar Migración", type="primary", use_container_width=True):
                with st.spinner("Migrando datos..."):
                    resultado = ejecutar_migracion_csv(archivo_seleccionado, data_manager)
                
                if resultado['success']:
                    st.success("✅ Migración completada exitosamente!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Registros Migrados", resultado['migrados'])
                    with col2:
                        st.metric("Errores", resultado['errores'])
                    with col3:
                        st.metric("Total USD", f"${resultado['total_usd']:.2f}")
                    
                    st.info("🔄 Recarga la página para ver los datos en el Dashboard")
                    
                    if st.button("🔄 Recargar App"):
                        st.rerun()
                else:
                    st.error(f"❌ Error en migración: {resultado['error']}")
            
        except Exception as e:
            st.error(f"Error leyendo archivo CSV: {e}")

def ejecutar_migracion_csv(archivo_csv, data_manager):
    """Ejecuta la migración del CSV dentro de Streamlit"""
    try:
        df = pd.read_csv(archivo_csv)
        
        consultas_migradas = []
        errores = 0
        total_usd = 0
        
        for index, row in df.iterrows():
            try:
                # Extraer y limpiar datos
                fecha = normalizar_fecha_csv(row['Fecha'])
                paciente = str(row['Paciente']).strip() if pd.notna(row['Paciente']) else f'Paciente_{index}'
                tratamiento = str(row['Tratamiento']).strip() if pd.notna(row['Tratamiento']) else 'Consulta'
                monto_str = str(row['Monto Total']).strip() if pd.notna(row['Monto Total']) else '0'
                medio_pago = str(row['Medio de Pago']).strip() if pd.notna(row['Medio de Pago']) else 'Efectivo'
                
                # Extraer monto numérico
                monto_numerico = extraer_monto_numerico(monto_str)
                
                if monto_numerico <= 0:
                    errores += 1
                    continue
                
                # Lógica argentina: >$1000 = ARS
                if monto_numerico > 1000:
                    monto_ars = monto_numerico
                    monto_usd = monto_numerico / data_manager.config['tipo_cambio']
                else:
                    monto_usd = monto_numerico
                    monto_ars = monto_numerico * data_manager.config['tipo_cambio']
                
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
                continue
        
        # Agregar consultas al data manager
        if consultas_migradas:
            # Limpiar datos existentes si es necesario
            confirmacion = True  # En producción podrías pedir confirmación
            
            if confirmacion:
                # Agregar consultas una por una o en batch
                for consulta in consultas_migradas:
                    nueva_fila = {
                        'fecha': consulta['fecha'],
                        'paciente': consulta['paciente'], 
                        'tratamiento': consulta['tratamiento'],
                        'monto_ars': consulta['monto_ars'],
                        'monto_usd': consulta['monto_usd'],
                        'medio_pago': consulta['medio_pago']
                    }
                    
                    # Agregar al DataFrame
                    if data_manager.consultas.empty:
                        data_manager.consultas = pd.DataFrame([nueva_fila])
                    else:
                        data_manager.consultas = pd.concat([data_manager.consultas, pd.DataFrame([nueva_fila])], ignore_index=True)
                
                # Guardar datos
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

def show_dashboard(data_manager, benchmarks):
    """Mostrar dashboard principal"""
    st.subheader("📊 Dashboard Principal")
    
    resumen = data_manager.get_resumen()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Ingresos Totales",
            f"${resumen['ingreso_total']} USD",
            delta=f"${resumen['ingresos_mes']} este mes"
        )
    
    with col2:
        st.metric(
            "👥 Total Consultas",
            resumen['total_consultas']
        )
    
    with col3:
        st.metric(
            "📊 Promedio/Consulta",
            f"${resumen['promedio_consulta']} USD"
        )
    
    with col4:
        st.metric(
            "🔥 Más Popular",
            resumen['tratamiento_popular']
        )
    
    # Gráficos si hay datos
    if not data_manager.consultas.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Ingresos por Mes")
            
            # Preparar datos para gráfico mensual
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
            
            # Gráfico de torta de tratamientos
            tratamientos = data_manager.consultas['tratamiento'].value_counts()
            
            fig_pie = px.pie(
                values=tratamientos.values,
                names=tratamientos.index,
                title="Distribución de Tratamientos"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Tabla de consultas recientes
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
        
        # Mostrar conversión a USD
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
    
    # Mostrar último cálculo
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
        
        # Conversión a ARS
        precio_ars = resultado['precio_final'] * data_manager.config['tipo_cambio']
        st.info(f"💱 Precio en ARS: ${precio_ars:,.0f}")

def show_benchmarks(data_manager, benchmarks):
    """Mostrar benchmarks oficiales"""
    st.subheader("📊 Benchmarks Oficiales")
    
    # Información de benchmarks
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Versión", benchmarks['version'])
        st.metric("💱 Dólar Referencia", f"${benchmarks['dolar_referencia']} ARS")
    
    with col2:
        st.metric("📅 Actualizado", benchmarks['fecha_actualizacion'])
        st.metric("🌍 Su Región", data_manager.config['region'])
    
    with col3:
        st.metric("📊 Factor Regional", f"{data_manager.config['factor_regional']:.2f}")
        ajuste_porcentual = (data_manager.config['factor_regional'] - 1) * 100
        st.metric("📈 Ajuste", f"{ajuste_porcentual:+.0f}%")
    
    # Tabla de precios
    st.subheader("💰 Precios de Referencia Ajustados")
    
    precios_data = []
    for tratamiento, precio_base in benchmarks['precios_base_ars'].items():
        precio_regional = precio_base * data_manager.config['factor_regional']
        precio_usd = precio_regional / benchmarks['dolar_referencia']
        
        precios_data.append({
            'Tratamiento': tratamiento.replace('_', ' ').title(),
            'Precio Base (ARS)': f"${precio_base:,.0f}",
            'Precio Regional (ARS)': f"${precio_regional:,.0f}",
            'Precio (USD)': f"${precio_usd:.2f}"
        })
    
    df_precios = pd.DataFrame(precios_data)
    st.dataframe(df_precios, use_container_width=True)
    
    # Análisis personalizado
    if not data_manager.consultas.empty:
        st.subheader("📈 Análisis de Su Práctica")
        
        resumen = data_manager.get_resumen()
        precio_consulta_benchmark = (benchmarks['precios_base_ars']['consulta'] * 
                                   data_manager.config['factor_regional'] / 
                                   benchmarks['dolar_referencia'])
        
        diferencia = ((resumen['promedio_consulta'] / precio_consulta_benchmark - 1) * 100)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📊 Su Promedio", f"${resumen['promedio_consulta']} USD")
            st.metric("🎯 Benchmark", f"${precio_consulta_benchmark:.2f} USD")
        
        with col2:
            if diferencia < -15:
                st.error(f"🚨 Sus precios están {abs(diferencia):.1f}% por debajo del sector")
            elif diferencia < -5:
                st.warning(f"⚠️ Oportunidad de ajuste: {abs(diferencia):.1f}%")
            elif diferencia > 30:
                st.info(f"📈 Precios por encima del promedio: +{diferencia:.1f}%")
            else:
                st.success(f"✅ Precios competitivos: {diferencia:+.1f}%")

def show_configuracion(data_manager, benchmarks):
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
            
            nuevas_horas = st.number_input(
                "⏰ Horas Anuales de Trabajo",
                min_value=100,
                value=data_manager.config['horas_anuales'],
                step=10
            )
        
        with col2:
            st.write("🌍 Configuración Regional")
            
            nueva_region = st.selectbox(
                "📍 Su Región",
                list(benchmarks['ajustes_regionales'].keys()),
                index=list(benchmarks['ajustes_regionales'].keys()).index(data_manager.config['region'])
            )
            
            nuevo_cambio = st.number_input(
                "💱 Tipo de Cambio ARS/USD",
                min_value=1.0,
                value=float(data_manager.config['tipo_cambio']),
                step=10.0
            )
            
            # Mostrar factor regional automático
            factor_auto = benchmarks['ajustes_regionales'][nueva_region]
            st.info(f"📊 Factor regional automático: {factor_auto} ({(factor_auto-1)*100:+.0f}%)")
        
        guardar = st.form_submit_button("💾 Guardar Configuración", type="primary")
        
        if guardar:
            # Actualizar configuración
            data_manager.config.update({
                'costo_por_hora': nuevo_costo,
                'margen_ganancia': nuevo_margen,
                'horas_anuales': nuevas_horas,
                'region': nueva_region,
                'factor_regional': benchmarks['ajustes_regionales'][nueva_region],
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
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("📅 Fecha Inicio", value=date.today().replace(day=1))
    
    with col2:
        fecha_fin = st.date_input("📅 Fecha Fin", value=date.today())
    
    # Filtrar datos
    df_filtrado = data_manager.consultas.copy()
    df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'])
    df_filtrado = df_filtrado[
        (df_filtrado['fecha'].dt.date >= fecha_inicio) & 
        (df_filtrado['fecha'].dt.date <= fecha_fin)
    ]
    
    if df_filtrado.empty:
        st.warning("⚠️ No hay datos en el rango de fechas seleccionado")
        return
    
    # Métricas del período
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
    
    # Gráficos de análisis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Evolución Diaria")
        
        # Agrupar por día
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
        
        # Análisis de medios de pago
        medios_pago = df_filtrado.groupby('medio_pago')['monto_usd'].sum()
        
        fig_payment = px.pie(
            values=medios_pago.values,
            names=medios_pago.index,
            title="Distribución por Medio de Pago"
        )
        st.plotly_chart(fig_payment, use_container_width=True)
    
    # Tabla detallada
    st.subheader("📋 Detalle de Consultas")
    
    # Preparar tabla para mostrar
    df_display = df_filtrado.copy()
    df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y %H:%M')
    df_display = df_display[['fecha', 'paciente', 'tratamiento', 'monto_ars', 'monto_usd', 'medio_pago']]
    df_display.columns = ['Fecha', 'Paciente', 'Tratamiento', 'Monto ARS', 'Monto USD', 'Medio Pago']
    
    # Formatear números
    df_display['Monto ARS'] = df_display['Monto ARS'].apply(lambda x: f"${x:,.0f}")
    df_display['Monto USD'] = df_display['Monto USD'].apply(lambda x: f"${x:.2f}")
    
    st.dataframe(df_display, use_container_width=True)
    
    # Exportar datos
    if st.button("📥 Exportar Reporte a CSV"):
        csv = df_display.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="💾 Descargar CSV",
            data=csv,
            file_name=f"reporte_dental_{fecha_inicio}_{fecha_fin}.csv",
            mime="text/csv"
        )

def show_planificacion(data_manager, benchmarks):
    """Planificación de objetivos"""
    st.subheader("🎯 Planificación de Objetivos 2026")
    
    with st.form("planificacion"):
        st.write("💭 Configure su objetivo anual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            objetivo_anual = st.number_input(
                "🎯 Objetivo de Ingresos Anuales (USD)",
                min_value=1000,
                value=30000,
                step=1000
            )
            
            st.info("""
            💡 **Ideas para inspirarse:**
            • Equipamiento nuevo: $15,000-20,000
            • Renovar consultorio: $25,000-35,000  
            • Consultorio propio: $30,000-50,000
            • Especialización: $35,000-45,000
            """)
        
        with col2:
            horas_semanales = st.number_input(
                "⏰ Horas Semanales Deseadas",
                min_value=10,
                max_value=60,
                value=35,
                step=5
            )
            
            semanas_anuales = st.number_input(
                "📅 Semanas de Trabajo/Año",
                min_value=40,
                max_value=52,
                value=48,
                step=1
            )
        
        calcular_plan = st.form_submit_button("🚀 Generar Plan Estratégico", type="primary")
        
        if calcular_plan:
            # Calcular métricas necesarias
            resumen = data_manager.get_resumen()
            
            # Proyecciones actuales
            if resumen['total_consultas'] > 0:
                ingreso_actual_anual = resumen['ingreso_total']
                ingreso_mensual_promedio = resumen['ingresos_mes']
            else:
                ingreso_mensual_promedio = 1000  # Estimación inicial
                ingreso_actual_anual = 12000
            
            # Cálculos del plan
            objetivo_mensual = objetivo_anual / 12
            horas_anuales_objetivo = horas_semanales * semanas_anuales
            ingreso_por_hora_objetivo = objetivo_anual / horas_anuales_objetivo
            
            incremento_necesario = ((objetivo_mensual / max(ingreso_mensual_promedio, 100)) - 1) * 100
            
            # Escenarios
            precio_actual = resumen['promedio_consulta'] if resumen['total_consultas'] > 0 else 50
            consultas_actuales_mes = max(resumen['total_consultas'] / 3, 10)
            
            st.markdown("---")
            st.subheader("📊 Análisis de Su Plan")
            
            # Métricas objetivo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🎯 Objetivo Anual", f"${objetivo_anual:,.0f} USD")
            
            with col2:
                st.metric("📅 Objetivo Mensual", f"${objetivo_mensual:,.0f} USD")
            
            with col3:
                st.metric("⏰ Ingreso/Hora Objetivo", f"${ingreso_por_hora_objetivo:.2f} USD")
            
            with col4:
                if incremento_necesario > 0:
                    st.metric("📈 Crecimiento Necesario", f"+{incremento_necesario:.1f}%")
                else:
                    st.metric("✅ Ya Superado", f"{incremento_necesario:.1f}%")
            
            # Escenarios para alcanzar objetivo
            st.subheader("🚀 Escenarios para Alcanzar el Objetivo")
            
            # Escenario 1: Solo precios
            if incremento_necesario <= 60 and incremento_necesario > 0:
                nuevo_precio = precio_actual * (1 + incremento_necesario / 100)
                viabilidad_precio = "Alta" if incremento_necesario <= 25 else "Media" if incremento_necesario <= 40 else "Baja"
                
                st.write("**1. 💰 Solo Aumento de Precios**")
                st.write(f"• Aumentar precios {incremento_necesario:.1f}%")
                st.write(f"• Precio promedio: ${precio_actual:.2f} → ${nuevo_precio:.2f} USD")
                st.write(f"• Viabilidad: {viabilidad_precio}")
                st.write("")
            
            # Escenario 2: Solo volumen
            if incremento_necesario > 0:
                consultas_necesarias = consultas_actuales_mes * (1 + incremento_necesario / 100)
                viabilidad_volumen = "Alta" if incremento_necesario <= 30 else "Media" if incremento_necesario <= 60 else "Baja"
                
                st.write("**2. 👥 Solo Aumento de Volumen**")
                st.write(f"• Aumentar consultas {incremento_necesario:.1f}%")
                st.write(f"• Consultas/mes: {consultas_actuales_mes:.0f} → {consultas_necesarias:.0f}")
                st.write(f"• Viabilidad: {viabilidad_volumen}")
                st.write("")
            
            # Escenario 3: Combinado (recomendado)
            if incremento_necesario > 0:
                aumento_combinado = incremento_necesario / 2
                nuevo_precio_comb = precio_actual * (1 + aumento_combinado / 100)
                consultas_comb = consultas_actuales_mes * (1 + aumento_combinado / 100)
                
                st.write("**3. ⭐ Estrategia Combinada (Recomendada)**")
                st.write(f"• +{aumento_combinado:.1f}% precios + {aumento_combinado:.1f}% consultas")
                st.write(f"• Precio: ${precio_actual:.2f} → ${nuevo_precio_comb:.2f} USD")
                st.write(f"• Consultas: {consultas_actuales_mes:.0f} → {consultas_comb:.0f}/mes")
                st.write("• Viabilidad: Alta")
                st.write("")
            
            # Plan de acción
            st.subheader("📋 Plan de Acción Trimestral")
            
            if incremento_necesario > 0:
                aumento_trimestral = incremento_necesario / 4
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Q1 (Ene-Mar 2026)**")
                    st.write(f"• Implementar +{aumento_trimestral:.1f}% precio gradual")
                    st.write("• Mejorar marketing digital")
                    st.write("• Optimizar agenda de citas")
                    st.write("")
                    
                    st.write("**Q3 (Jul-Sep 2026)**")
                    st.write("• Evaluar nuevos servicios")
                    st.write("• Implementar sistema de referidos")
                    st.write("• Análisis de competencia")
                
                with col2:
                    st.write("**Q2 (Abr-Jun 2026)**")
                    st.write("• Consolidar nuevos precios")
                    st.write("• Diversificar tratamientos")
                    st.write("• Capacitación profesional")
                    st.write("")
                    
                    st.write("**Q4 (Oct-Dic 2026)**")
                    st.write("• Revisar cumplimiento objetivo")
                    st.write("• Planificar crecimiento 2027")
                    st.write("• Optimizar procesos")
            else:
                st.success("🎉 ¡Felicitaciones! Ya está superando su objetivo actual.")
                st.write("💡 Considere objetivos más ambiciosos o trabajar menos horas manteniendo ingresos.")

if __name__ == "__main__":
    main()