#v6.0
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
    page_title="Manny App - Sistema de Gestión de Consultorios de Salud",
    page_icon="🏥",
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
    .cost-analysis-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 4 - UserManager
class UserManager:
    def __init__(self):
        self.users_file = "usuarios.json"
        self.data_folder = "data"
        self.init_system()
    
    def init_system(self):
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
        if not os.path.exists(self.users_file):
            usuarios_default = {
                "admin": {
                    "password_hash": self.hash_password("Homero123"),
                    "nombre": "Dr. Administrador",
                    "email": "admin@manny.com",
                    "especialidad": "odontologia",
                    "plan": "premium",
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
                    'costo_por_hora': 29000,
                    'margen_ganancia': 0.40,
                    'tipo_cambio_usd_ars': 1335.0,
                    'horas_anuales_trabajadas': 1100
                },
                'equipos': [],
                'gastos_fijos': []
            }
            data_file = os.path.join(user_folder, 'dental_data.json')
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2, default=str)

# 5 - DataManager expandido con análisis de costos
class DataManager:
    def __init__(self, user_id=None):
        if user_id:
            self.data_file = os.path.join("data", user_id, "dental_data.json")
        else:
            self.data_file = "dental_data.json"
        self.user_id = user_id
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.consultas = pd.DataFrame(data.get('consultas', []))
                    self.config = data.get('config', self.get_default_config())
                    self.equipos = data.get('equipos', [])
                    self.gastos_fijos = data.get('gastos_fijos', [])
            except Exception as e:
                st.error(f"Error cargando datos: {e}")
                self.init_default_data()
        else:
            self.init_default_data()
    
    def init_default_data(self):
        self.consultas = pd.DataFrame(columns=['fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago'])
        self.config = self.get_default_config()
        self.equipos = []
        self.gastos_fijos = []
    
    def get_default_config(self):
        return {
            'costo_por_hora': 29000,
            'margen_ganancia': 0.40,
            'tipo_cambio_usd_ars': 1335.0,
            'horas_anuales_trabajadas': 1100
        }
    
    def save_data(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            data = {
                'consultas': self.consultas.to_dict('records'),
                'config': self.config,
                'equipos': self.equipos,
                'gastos_fijos': self.gastos_fijos
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            st.error(f"Error guardando datos: {e}")
            return False
    
    def add_consulta(self, paciente, tratamiento, monto_ars, medio_pago):
        nueva_consulta = {
            'fecha': datetime.now().isoformat(),
            'paciente': paciente,
            'tratamiento': tratamiento,
            'monto_ars': monto_ars,
            'medio_pago': medio_pago
        }
        if self.consultas.empty:
            self.consultas = pd.DataFrame([nueva_consulta])
        else:
            self.consultas = pd.concat([self.consultas, pd.DataFrame([nueva_consulta])], ignore_index=True)
        self.save_data()
        return nueva_consulta
    
    def add_equipo(self, nombre, monto_usd, años_vida_util, fecha_compra, observaciones=""):
        nuevo_equipo = {
            'id': len(self.equipos) + 1,
            'nombre': nombre,
            'monto_compra_usd': float(monto_usd),
            'años_vida_util': int(años_vida_util),
            'fecha_compra': fecha_compra.isoformat() if isinstance(fecha_compra, date) else fecha_compra,
            'observaciones': observaciones,
            'activo': True,
            'fecha_creacion': datetime.now().isoformat()
        }
        self.equipos.append(nuevo_equipo)
        self.save_data()
        return nuevo_equipo
    
    def add_gasto_fijo(self, concepto, monto_mensual_ars):
        nuevo_gasto = {
            'id': len(self.gastos_fijos) + 1,
            'concepto': concepto,
            'monto_mensual_ars': float(monto_mensual_ars),
            'activo': True,
            'fecha_creacion': datetime.now().isoformat()
        }
        self.gastos_fijos.append(nuevo_gasto)
        self.save_data()
        return nuevo_gasto
    
    def delete_equipo(self, equipo_id):
        """Eliminar equipo por ID"""
        self.equipos = [e for e in self.equipos if e.get('id') != equipo_id]
        self.save_data()
        return True
    
    def delete_gasto_fijo(self, gasto_id):
        """Eliminar gasto fijo por ID"""
        self.gastos_fijos = [g for g in self.gastos_fijos if g.get('id') != gasto_id]
        self.save_data()
        return True
    
    def delete_consulta(self, index):
        """Eliminar consulta por índice"""
        if 0 <= index < len(self.consultas):
            self.consultas = self.consultas.drop(index).reset_index(drop=True)
            self.save_data()
            return True
        return False
    
    def delete_all_consultas(self):
        """Eliminar todas las consultas"""
        self.consultas = pd.DataFrame(columns=['fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago'])
        self.save_data()
        return True
    
    def calcular_costo_hora_real(self):
        """Cálculo integral del costo por hora basado en equipos y gastos fijos"""
        
        # 1. Costos de equipos (amortización con inflación 4% anual)
        costo_equipos_anual_usd = 0
        for equipo in self.equipos:
            if equipo.get('activo', True):
                # Amortización con inflación
                costo_reposicion = equipo['monto_compra_usd'] * (1.04 ** equipo['años_vida_util'])
                amortizacion_anual = costo_reposicion / equipo['años_vida_util']
                costo_equipos_anual_usd += amortizacion_anual
        
        # Convertir USD a ARS
        tipo_cambio = self.config.get('tipo_cambio_usd_ars', 1335)
        costo_equipos_anual_ars = costo_equipos_anual_usd * tipo_cambio
        
        # 2. Gastos fijos anuales (ARS)
        costo_gastos_anual_ars = sum([
            gasto['monto_mensual_ars'] * 12 
            for gasto in self.gastos_fijos 
            if gasto.get('activo', True)
        ])
        
        # 3. Cálculo final
        costo_total_anual = costo_equipos_anual_ars + costo_gastos_anual_ars
        horas_anuales = self.config.get('horas_anuales_trabajadas', 1100)
        
        costo_hora = costo_total_anual / horas_anuales if horas_anuales > 0 else 0
        
        return {
            'costo_hora_ars': costo_hora,
            'costo_equipos_anual': costo_equipos_anual_ars,
            'costo_gastos_anual': costo_gastos_anual_ars,
            'costo_total_anual': costo_total_anual,
            'horas_anuales': horas_anuales,
            'cantidad_equipos': len([e for e in self.equipos if e.get('activo', True)]),
            'cantidad_gastos': len([g for g in self.gastos_fijos if g.get('activo', True)])
        }
    
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
        ingreso_total = self.consultas['monto_ars'].sum()
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
        ingresos_mes = mes_actual['monto_ars'].sum() if not mes_actual.empty else 0
        
        return {
            'total_consultas': total_consultas,
            'ingreso_total': round(ingreso_total, 0),
            'promedio_consulta': round(promedio_consulta, 0),
            'tratamiento_popular': tratamiento_popular,
            'ingresos_mes': round(ingresos_mes, 0)
        }

# 6 - Funciones de análisis de costos
def show_configuracion_costos(data_manager):
    """Página de configuración de costos"""
    st.title("⚙️ Configuración de Costos")
    
    tab1, tab2, tab3 = st.tabs(["🔧 Equipos", "🏢 Gastos Fijos", "⚙️ Parámetros"])
    
    with tab1:
        st.subheader("🔧 Equipamiento del Consultorio")
        
        # Mostrar equipos actuales con botones de eliminar
        if data_manager.equipos:
            st.markdown("**Equipos registrados:**")
            
            for equipo in data_manager.equipos:
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{equipo['nombre']}**")
                with col2:
                    st.write(f"${equipo['monto_compra_usd']:,.0f} USD")
                with col3:
                    st.write(f"{equipo['años_vida_util']} años")
                with col4:
                    fecha_compra = pd.to_datetime(equipo['fecha_compra']).strftime('%d/%m/%Y')
                    st.write(fecha_compra)
                with col5:
                    if st.button("🗑️", key=f"del_equipo_{equipo['id']}", help="Eliminar equipo"):
                        data_manager.delete_equipo(equipo['id'])
                        st.success("Equipo eliminado")
                        st.rerun()
        else:
            st.info("No hay equipos registrados aún.")
        
        # Formulario para nuevo equipo
        with st.form("nuevo_equipo"):
            st.markdown("**Agregar Nuevo Equipo**")
            
            col1, col2 = st.columns(2)
            with col1:
                nombre_equipo = st.text_input("Nombre del Equipo *", placeholder="Ej: Sillón Dental")
                monto_usd = st.number_input("Precio pagado (USD) *", min_value=0.0, step=100.0, value=1000.0)
            
            with col2:
                años_vida = st.selectbox("Vida Útil (años)", [3, 5, 7, 8, 10], index=1)
                fecha_compra = st.date_input("Fecha de Compra", value=date.today())
            
            observaciones = st.text_area("Observaciones (opcional)")
            
            if st.form_submit_button("💾 Agregar Equipo", type="primary"):
                if nombre_equipo and monto_usd > 0:
                    data_manager.add_equipo(nombre_equipo, monto_usd, años_vida, fecha_compra, observaciones)
                    st.success("✅ Equipo agregado correctamente")
                    st.rerun()
                else:
                    st.error("❌ Complete los campos obligatorios")
    
    with tab2:
        st.subheader("🏢 Gastos Fijos Mensuales")
        
        # Mostrar gastos actuales con botones de eliminar
        if data_manager.gastos_fijos:
            st.markdown("**Gastos fijos registrados:**")
            
            for gasto in data_manager.gastos_fijos:
                col1, col2, col3 = st.columns([4, 3, 1])
                
                with col1:
                    st.write(f"**{gasto['concepto']}**")
                with col2:
                    st.write(f"${gasto['monto_mensual_ars']:,.0f} ARS/mes")
                with col3:
                    if st.button("🗑️", key=f"del_gasto_{gasto['id']}", help="Eliminar gasto"):
                        data_manager.delete_gasto_fijo(gasto['id'])
                        st.success("Gasto eliminado")
                        st.rerun()
            
            st.markdown("---")
            total_mensual = sum([g['monto_mensual_ars'] for g in data_manager.gastos_fijos if g.get('activo', True)])
            st.metric("💰 Total Gastos Fijos", f"${total_mensual:,.0f} ARS/mes")
        else:
            st.info("No hay gastos fijos registrados aún.")
        
        # Formulario para nuevo gasto
        with st.form("nuevo_gasto"):
            st.markdown("**Agregar Nuevo Gasto Fijo**")
            
            col1, col2 = st.columns(2)
            with col1:
                concepto = st.text_input("Concepto *", placeholder="Ej: Alquiler")
            with col2:
                monto_mensual = st.number_input("Monto mensual (ARS) *", min_value=0.0, step=1000.0, value=50000.0)
            
            if st.form_submit_button("💾 Agregar Gasto", type="primary"):
                if concepto and monto_mensual > 0:
                    data_manager.add_gasto_fijo(concepto, monto_mensual)
                    st.success("✅ Gasto agregado correctamente")
                    st.rerun()
                else:
                    st.error("❌ Complete los campos obligatorios")
    
    with tab3:
        st.subheader("⚙️ Parámetros de Trabajo")
        
        with st.form("parametros"):
            col1, col2 = st.columns(2)
            
            with col1:
                nuevas_horas = st.number_input(
                    "Horas anuales trabajadas",
                    min_value=500,
                    max_value=2000,
                    value=data_manager.config.get('horas_anuales_trabajadas', 1100),
                    step=50,
                    help="Horas productivas anuales (descontando vacaciones, días no trabajados, etc.)"
                )
                
                nuevo_margen = st.slider(
                    "Margen de ganancia objetivo (%)",
                    min_value=10,
                    max_value=200,
                    value=int(data_manager.config.get('margen_ganancia', 0.4) * 100),
                    step=5
                ) / 100
            
            with col2:
                nuevo_tc = st.number_input(
                    "Tipo de cambio USD/ARS",
                    min_value=100.0,
                    max_value=5000.0,
                    value=data_manager.config.get('tipo_cambio_usd_ars', 1335.0),
                    step=10.0,
                    help="Para convertir equipos en USD a ARS"
                )
            
            if st.form_submit_button("💾 Actualizar Parámetros", type="primary"):
                data_manager.config.update({
                    'horas_anuales_trabajadas': nuevas_horas,
                    'margen_ganancia': nuevo_margen,
                    'tipo_cambio_usd_ars': nuevo_tc
                })
                data_manager.save_data()
                st.success("✅ Parámetros actualizados exitosamente")
                st.rerun()

def show_analisis_costos(data_manager, user_info):
    """Página de análisis de costos integral"""
    st.title("💰 Análisis de Costos y Rentabilidad")
    
    especialidad = user_info.get('especialidad', 'odontologia')
    especialidad_emoji = {
        'odontologia': '🦷',
        'dermatologia': '🧴',
        'kinesiologia': '🏃‍♂️'
    }.get(especialidad, '🏥')
    
    st.markdown(f"### {especialidad_emoji} {especialidad.title()}")
    
    # Calcular métricas de costos
    costos_analysis = data_manager.calcular_costo_hora_real()
    
    # Verificar si tiene costos configurados
    if costos_analysis['costo_total_anual'] == 0:
        st.warning("⚠️ No tiene equipos ni gastos fijos configurados. Vaya a 'Configuración Costos' para comenzar.")
        st.info("💡 El análisis de costos le permitirá conocer su costo real por hora y optimizar sus precios.")
        return
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Costo Real/Hora", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
    with col2:
        precio_minimo = costos_analysis['costo_hora_ars'] * 1.5  # 50% margen
        st.metric("📊 Precio Mín. (50%)", f"${precio_minimo:,.0f} ARS")
    
    with col3:
        precio_optimo = costos_analysis['costo_hora_ars'] * 2  # 100% margen
        st.metric("🎯 Precio Óptimo (100%)", f"${precio_optimo:,.0f} ARS")
    
    with col4:
        resumen = data_manager.get_resumen()
        if resumen['promedio_consulta'] > 0:
            consultas_breakeven = costos_analysis['costo_total_anual'] / resumen['promedio_consulta']
            st.metric("⚖️ Consultas Break-Even", f"{consultas_breakeven:,.0f} /año")
        else:
            st.metric("⚖️ Consultas Break-Even", "Sin datos")
    
    # Gráfico de composición de costos
    if costos_analysis['costo_total_anual'] > 0:
        st.subheader("📊 Composición de Costos Anuales")
        
        costos_data = pd.DataFrame([
            {"Categoría": "Equipos (Amortización)", "Monto": costos_analysis['costo_equipos_anual']},
            {"Categoría": "Gastos Fijos", "Monto": costos_analysis['costo_gastos_anual']}
        ])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_costos = px.pie(
                costos_data, 
                values='Monto', 
                names='Categoría',
                title=f"Total Anual: ${costos_analysis['costo_total_anual']:,.0f} ARS",
                color_discrete_sequence=['#3b82f6', '#ef4444']
            )
            st.plotly_chart(fig_costos, use_container_width=True)
        
        with col2:
            st.markdown("**📈 Resumen de Configuración**")
            st.metric("🔧 Equipos", costos_analysis['cantidad_equipos'])
            st.metric("🏢 Gastos Fijos", costos_analysis['cantidad_gastos'])
            st.metric("⏰ Horas Anuales", costos_analysis['horas_anuales'])
    
    # Análisis de rentabilidad actual
    if resumen['total_consultas'] > 0:
        st.subheader("📈 Análisis de Rentabilidad Actual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💵 Ingresos vs Costos**")
            ingresos_anuales = resumen['ingreso_total'] * 12  # Proyección anual
            margen_real = ((ingresos_anuales - costos_analysis['costo_total_anual']) / ingresos_anuales * 100) if ingresos_anuales > 0 else 0
            
            if margen_real > 50:
                st.success(f"✅ Margen excelente: {margen_real:.1f}%")
            elif margen_real > 25:
                st.warning(f"⚠️ Margen aceptable: {margen_real:.1f}%")
            else:
                st.error(f"🚨 Margen bajo: {margen_real:.1f}%")
        
        with col2:
            st.markdown("**⏰ Eficiencia Horaria**")
            consultas_mes = resumen['total_consultas'] / max(1, len(data_manager.consultas['fecha'].dt.month.unique()) if not data_manager.consultas.empty else 1)
            eficiencia = (consultas_mes * 12) / costos_analysis['horas_anuales'] if costos_analysis['horas_anuales'] > 0 else 0
            
            st.metric("Consultas por Hora Disponible", f"{eficiencia:.2f}")

# 7 - Funciones de interfaz (actualizadas)
def show_dashboard(data_manager, user_info):
    especialidad = user_info.get('especialidad', 'odontologia')
    especialidad_emoji = {
        'odontologia': '🦷',
        'dermatologia': '🧴', 
        'kinesiologia': '🏃‍♂️'
    }.get(especialidad, '🏥')
    
    st.subheader(f"📊 Dashboard - {user_info.get('nombre', 'Usuario')} {especialidad_emoji}")
    
    # Análisis de costos en el dashboard
    costos_analysis = data_manager.calcular_costo_hora_real()
    
    # Mostrar alerta si tiene costos configurados
    if costos_analysis['costo_total_anual'] > 0:
        st.markdown(f"""
        <div class="cost-analysis-card">
            <h3>💰 Análisis de Costos Automático</h3>
            <p>Su costo real por hora: <strong>${costos_analysis['costo_hora_ars']:,.0f} ARS</strong></p>
            <p>Precio mínimo recomendado (50% margen): <strong>${costos_analysis['costo_hora_ars'] * 1.5:,.0f} ARS</strong></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Configure sus equipos y gastos fijos para obtener análisis de costos automático.")
    
    # Dashboard original
    resumen = data_manager.get_resumen()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Ingresos Totales", f"${resumen['ingreso_total']:,.0f} ARS")
    
    with col2:
        st.metric("👥 Total Consultas", resumen['total_consultas'])
    
    with col3:
        st.metric("📊 Promedio/Consulta", f"${resumen['promedio_consulta']:,.0f} ARS")
    
    with col4:
        st.metric("🔥 Más Popular", resumen['tratamiento_popular'])
    
    if not data_manager.consultas.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Ingresos por Mes")
            df_monthly = data_manager.consultas.copy()
            df_monthly['fecha'] = pd.to_datetime(df_monthly['fecha'])
            df_monthly['mes'] = df_monthly['fecha'].dt.to_period('M')
            monthly_income = df_monthly.groupby('mes')['monto_ars'].sum().reset_index()
            monthly_income['mes'] = monthly_income['mes'].astype(str)
            
            fig_monthly = px.bar(monthly_income, x='mes', y='monto_ars', title="Ingresos Mensuales")
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        with col2:
            st.subheader("🥧 Tratamientos")
            tratamientos = data_manager.consultas['tratamiento'].value_counts()
            fig_pie = px.pie(values=tratamientos.values, names=tratamientos.index)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No hay consultas registradas aún.")

def show_calculadora_inteligente(data_manager):
    """Calculadora inteligente con análisis de costos automático"""
    st.title("🧮 Calculadora Inteligente de Precios")
    
    # Análisis de costos disponibles
    costos_analysis = data_manager.calcular_costo_hora_real()
    tiene_costos_configurados = costos_analysis['costo_total_anual'] > 0
    
    if tiene_costos_configurados:
        st.success(f"✅ Usando su costo real calculado: ${costos_analysis['costo_hora_ars']:,.0f} ARS/hora")
    else:
        st.warning("⚠️ Configure equipos y gastos fijos para cálculos más precisos")
    
    # Formulario principal
    with st.form("calculadora_inteligente"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📋 Parámetros del Tratamiento")
            
            # Selección de tratamiento con opción personalizada
            lista_tratamientos = [
                "Consulta", "Limpieza", "Operatoria Simple", "Operatoria Compleja", 
                "Endodoncia", "Corona", "Extracción Simple", "Extracción Compleja", "Otro"
            ]
            
            tratamiento_base = st.selectbox("Tipo de Tratamiento", lista_tratamientos)
            
            if tratamiento_base == "Otro":
                tratamiento_seleccionado = st.text_input(
                    "Especificar tratamiento:",
                    placeholder="Ej: Blanqueamiento, Implante, etc."
                )
                if not tratamiento_seleccionado:
                    tratamiento_seleccionado = "Personalizado"
            else:
                tratamiento_seleccionado = tratamiento_base
            
            # Tiempos estimados por tratamiento
            tiempos_estandar = {
                "Consulta": 0.5,
                "Limpieza": 1.0,
                "Operatoria Simple": 1.5,
                "Operatoria Compleja": 2.5,
                "Endodoncia": 3.0,
                "Corona": 2.0,
                "Extracción Simple": 0.75,
                "Extracción Compleja": 2.0,
                "Personalizado": 1.0
            }
            
            tiempo_sugerido = tiempos_estandar.get(tratamiento_seleccionado, 1.0)
            
            time_hours = st.number_input(
                "Tiempo estimado (horas)",
                min_value=0.1,
                max_value=8.0,
                value=tiempo_sugerido,
                step=0.25,
                help="Tiempo que demora realizar el tratamiento"
            )
            
            materials_ars = st.number_input(
                "Costo de materiales (ARS)",
                min_value=0.0,
                value=5000.0,
                step=1000.0,
                help="Costo total de insumos para este tratamiento"
            )
        
        with col2:
            st.subheader("⚙️ Configuración de Costos")
            
            # Toggle para usar costo automático o manual
            if tiene_costos_configurados:
                usar_costo_real = st.checkbox(
                    "Usar costo real calculado",
                    value=True,
                    help="Basado en sus equipos y gastos fijos configurados"
                )
                
                if usar_costo_real:
                    costo_hora_usar = costos_analysis['costo_hora_ars']
                    st.metric("Costo/Hora Real", f"${costo_hora_usar:,.0f} ARS")
                else:
                    costo_hora_usar = st.number_input(
                        "Costo por hora manual (ARS)",
                        min_value=5000.0,
                        value=29000.0,
                        step=1000.0
                    )
                    st.warning("Usando costo manual en lugar del calculado")
            else:
                usar_costo_real = False
                costo_hora_usar = st.number_input(
                    "Costo por hora (ARS)",
                    min_value=5000.0,
                    value=29000.0,
                    step=1000.0,
                    help="Configure equipos y gastos para cálculo automático"
                )
        
        calcular = st.form_submit_button("🧮 Calcular Recomendaciones", type="primary")
        
        if calcular:
            # Cálculo base
            costo_mano_obra = time_hours * costo_hora_usar
            costo_total = costo_mano_obra + materials_ars
            
            # Recomendaciones con diferentes márgenes
            margenes = {
                "Supervivencia (25%)": 0.25,
                "Competitivo (50%)": 0.50,
                "Premium (75%)": 0.75,
                "Especialista (100%)": 1.00
            }
            
            st.markdown("---")
            st.subheader("💰 Análisis de Costos")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Mano de Obra", f"${costo_mano_obra:,.0f} ARS")
            with col2:
                st.metric("Materiales", f"${materials_ars:,.0f} ARS")
            with col3:
                st.metric("Costo Total", f"${costo_total:,.0f} ARS")
            
            st.subheader("📊 Recomendaciones de Precios")
            
            recomendaciones = []
            for nombre_margen, porcentaje_margen in margenes.items():
                precio_final = costo_total * (1 + porcentaje_margen)
                ganancia = precio_final - costo_total
                
                recomendaciones.append({
                    "Margen": nombre_margen,
                    "Precio": f"${precio_final:,.0f} ARS",
                    "Ganancia": f"${ganancia:,.0f} ARS",
                    "Valor": precio_final
                })
            
            # Mostrar recomendaciones en columnas
            col1, col2 = st.columns(2)
            
            for i, rec in enumerate(recomendaciones):
                col = col1 if i % 2 == 0 else col2
                
                with col:
                    # Color según el margen
                    if "Supervivencia" in rec["Margen"]:
                        color = "🟡"
                    elif "Competitivo" in rec["Margen"]:
                        color = "🟢"
                    elif "Premium" in rec["Margen"]:
                        color = "🔵"
                    else:  # Especialista
                        color = "🟣"
                    
                    recomendado = "← RECOMENDADO" if "Competitivo" in rec["Margen"] else ""
                    
                    st.markdown(f"""
                    **{color} {rec["Margen"]} {recomendado}**
                    - Precio: {rec["Precio"]}
                    - Ganancia: {rec["Ganancia"]}
                    """)
            
            # Búsqueda en registros históricos
            st.subheader("📋 Histórico de Este Tratamiento")
            
            if not data_manager.consultas.empty:
                # Buscar tratamientos exactos o similares
                tratamientos_exactos = data_manager.consultas[
                    data_manager.consultas['tratamiento'].str.lower() == tratamiento_seleccionado.lower()
                ]
                
                if not tratamientos_exactos.empty:
                    st.markdown("**Registros anteriores encontrados:**")
                    
                    # Mostrar últimos 5 registros
                    ultimos_registros = tratamientos_exactos.tail(5).sort_values('fecha', ascending=False)
                    
                    for _, registro in ultimos_registros.iterrows():
                        fecha_registro = pd.to_datetime(registro['fecha']).strftime('%d/%m/%Y')
                        
                        col1, col2, col3 = st.columns([2, 2, 2])
                        with col1:
                            st.write(f"**{registro['paciente']}**")
                        with col2:
                            st.write(f"${registro['monto_ars']:,.0f} ARS")
                        with col3:
                            st.write(fecha_registro)
                    
                    # Estadísticas del histórico
                    precio_promedio = tratamientos_exactos['monto_ars'].mean()
                    precio_ultimo = tratamientos_exactos.iloc[-1]['monto_ars']
                    
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Precio Promedio Histórico", f"${precio_promedio:,.0f} ARS")
                    with col2:
                        st.metric("Último Precio Cobrado", f"${precio_ultimo:,.0f} ARS")
                    with col3:
                        total_realizados = len(tratamientos_exactos)
                        st.metric("Veces Realizadas", total_realizados)
                    
                    # Comparación con recomendaciones actuales
                    precio_competitivo = costo_total * 1.5
                    
                    if precio_ultimo < costo_total:
                        st.error(f"⚠️ Su último precio (${precio_ultimo:,.0f}) estaba por debajo del costo actual")
                    elif precio_ultimo < precio_competitivo:
                        diferencia = precio_competitivo - precio_ultimo
                        st.warning(f"💡 Puede aumentar ${diferencia:,.0f} respecto al último precio cobrado")
                    else:
                        st.success("✅ Su último precio estaba bien posicionado")
                        
                else:
                    st.info(f"No se encontraron registros anteriores de '{tratamiento_seleccionado}'")
                    st.info("Una vez que registre este tratamiento, aparecerá en el histórico para futuras consultas")
            else:
                st.info("No hay consultas registradas aún para mostrar histórico")

def extraer_monto_numerico(monto_str):
    """Extrae valor numérico de string de monto"""
    try:
        if pd.isna(monto_str):
            return 0
        
        monto_clean = str(monto_str).strip()
        
        # Remover símbolos comunes de moneda
        monto_clean = re.sub(r'[$€£¥₹₽₩¢]', '', monto_clean)
        monto_clean = re.sub(r'[^\d.,\-]', '', monto_clean)
        
        if not monto_clean:
            return 0
        
        # Manejar números negativos
        es_negativo = monto_clean.startswith('-')
        monto_clean = monto_clean.lstrip('-')
        
        # Determinar si el último punto/coma son decimales
        if ',' in monto_clean and '.' in monto_clean:
            if monto_clean.rfind(',') > monto_clean.rfind('.'):
                monto_clean = monto_clean.replace('.', '').replace(',', '.')
            else:
                monto_clean = monto_clean.replace(',', '')
        elif ',' in monto_clean:
            if monto_clean.count(',') == 1 and len(monto_clean.split(',')[1]) <= 2:
                monto_clean = monto_clean.replace(',', '.')
            else:
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
        
        formatos_fecha = [
            '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y', '%d.%m.%Y', '%d.%m.%y',
            '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
            '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y_%m_%d',
            '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d-%m-%Y %H:%M:%S', '%d-%m-%Y %H:%M',
            '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
            '%d de %B de %Y', '%d %B %Y', '%B %d, %Y', '%d %b %Y',
        ]
        
        for formato in formatos_fecha:
            try:
                fecha_parsed = datetime.strptime(fecha_str, formato)
                return fecha_parsed.isoformat()
            except ValueError:
                continue
        
        try:
            fecha_pandas = pd.to_datetime(fecha_str, dayfirst=True, errors='coerce')
            if not pd.isna(fecha_pandas):
                return fecha_pandas.isoformat()
        except:
            pass
        
        st.warning(f"No se pudo procesar fecha '{fecha_valor}', usando fecha actual")
        return datetime.now().isoformat()
        
    except Exception as e:
        st.warning(f"Error procesando fecha '{fecha_valor}': {e}")
        return datetime.now().isoformat()

def show_migration_tool(data_manager):
    """Herramienta de migración flexible para cualquier CSV"""
    st.title("📥 Migración de Datos desde CSV")
    
    st.markdown("""
    **Migración Universal de CSV**
    
    Esta herramienta puede trabajar con cualquier archivo CSV:
    - Mapea automáticamente las columnas de tu archivo
    - Convierte formatos de fecha y moneda
    - Todo en pesos argentinos
    - Vista previa antes de migrar
    """)
    
    uploaded_file = st.file_uploader(
        "Sube tu archivo CSV", 
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
                st.error("No se pudo leer el archivo. Verifica el formato.")
                return
            
            st.success(f"Archivo cargado correctamente (encoding: {encoding_usado})")
            
            # Vista previa del archivo
            with st.expander("Vista Previa del Archivo", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Registros", len(df))
                with col2:
                    st.metric("Columnas", len(df.columns))
                with col3:
                    st.metric("Tamaño", f"{uploaded_file.size / 1024:.1f} KB")
                
                st.markdown("**Primeras 5 filas:**")
                st.dataframe(df.head(), use_container_width=True)
                
                st.markdown("**Columnas disponibles:**")
                st.write(", ".join(df.columns.tolist()))
            
            # Mapeo de columnas
            st.subheader("Mapeo de Columnas")
            st.markdown("Indica qué columna de tu CSV corresponde a cada campo:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Campos Obligatorios:**")
                
                col_paciente = st.selectbox(
                    "Columna de Pacientes *",
                    options=['-- Seleccionar --'] + df.columns.tolist()
                )
                
                col_tratamiento = st.selectbox(
                    "Columna de Tratamientos *",
                    options=['-- Seleccionar --'] + df.columns.tolist()
                )
                
                col_monto = st.selectbox(
                    "Columna de Montos (ARS) *",
                    options=['-- Seleccionar --'] + df.columns.tolist()
                )
            
            with col2:
                st.markdown("**Campos Opcionales:**")
                
                col_fecha = st.selectbox(
                    "Columna de Fechas",
                    options=['-- Usar fecha actual --'] + df.columns.tolist()
                )
                
                col_medio_pago = st.selectbox(
                    "Columna de Medio de Pago",
                    options=['-- Usar "No especificado" --'] + df.columns.tolist()
                )
            
            # Vista previa del mapeo
            if (col_paciente != '-- Seleccionar --' and 
                col_tratamiento != '-- Seleccionar --' and 
                col_monto != '-- Seleccionar --'):
                
                st.subheader("Vista Previa del Mapeo")
                
                muestra = df.head(5).copy()
                preview_data = []
                
                for _, row in muestra.iterrows():
                    if col_fecha == '-- Usar fecha actual --':
                        fecha_procesada = datetime.now().strftime('%d/%m/%Y')
                    else:
                        fecha_raw = row[col_fecha]
                        fecha_iso = normalizar_fecha_flexible(fecha_raw)
                        fecha_procesada = datetime.fromisoformat(fecha_iso).strftime('%d/%m/%Y')
                    
                    monto_raw = row[col_monto]
                    monto_procesado = extraer_monto_numerico(monto_raw)
                    
                    if col_medio_pago == '-- Usar "No especificado" --':
                        medio_pago = "No especificado"
                    else:
                        medio_pago = str(row[col_medio_pago]) if pd.notna(row[col_medio_pago]) else "No especificado"
                    
                    preview_data.append({
                        'Fecha': fecha_procesada,
                        'Paciente': str(row[col_paciente]),
                        'Tratamiento': str(row[col_tratamiento]),
                        'Monto Original': str(monto_raw),
                        'Monto ARS': f"${monto_procesado:,.0f}",
                        'Medio de Pago': medio_pago
                    })
                
                preview_df = pd.DataFrame(preview_data)
                st.dataframe(preview_df, use_container_width=True)
                
                # Estadísticas pre-migración
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    pacientes_unicos = df[col_paciente].nunique()
                    st.metric("Pacientes Únicos", pacientes_unicos)
                
                with col2:
                    tratamientos_unicos = df[col_tratamiento].nunique()
                    st.metric("Tipos de Tratamiento", tratamientos_unicos)
                
                with col3:
                    montos_procesados = df[col_monto].apply(extraer_monto_numerico)
                    total_estimado = montos_procesados.sum()
                    st.metric("Total Estimado", f"${total_estimado:,.0f} ARS")
                
                with col4:
                    registros_validos = len(df.dropna(subset=[col_paciente, col_tratamiento, col_monto]))
                    st.metric("Registros Válidos", registros_validos)
                
                # Botón de migración
                st.markdown("---")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("### ¿Todo se ve correcto?")
                    st.markdown("Revisa la vista previa y las estadísticas antes de proceder.")
                
                with col2:
                    if st.button("Ejecutar Migración", type="primary", use_container_width=True):
                        with st.spinner("Migrando datos..."):
                            resultado = ejecutar_migracion_flexible(
                                df=df,
                                col_paciente=col_paciente,
                                col_tratamiento=col_tratamiento,
                                col_monto=col_monto,
                                col_fecha=col_fecha if col_fecha != '-- Usar fecha actual --' else None,
                                col_medio_pago=col_medio_pago if col_medio_pago != '-- Usar "No especificado" --' else None,
                                data_manager=data_manager
                            )
                        
                        if resultado['success']:
                            st.success("Migración completada exitosamente!")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Registros Migrados", resultado['migrados'])
                            with col2:
                                st.metric("Errores", resultado['errores'])
                            with col3:
                                st.metric("Total Migrado", f"${resultado['total_ars']:,.0f} ARS")
                            
                            if resultado['errores'] > 0:
                                st.warning(f"{resultado['errores']} registros tuvieron problemas y no se migraron")
                            
                            st.info("Recarga la página para ver los datos migrados en el Dashboard")
                            
                            if st.button("Recargar Aplicación"):
                                st.rerun()
                        
                        else:
                            st.error(f"Error en la migración: {resultado['error']}")
            
            else:
                st.info("Por favor selecciona al menos las columnas obligatorias para continuar")
        
        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")
    
    else:
        st.info("Sube un archivo CSV para comenzar")

def ejecutar_migracion_flexible(df, col_paciente, col_tratamiento, col_monto, 
                               col_fecha=None, col_medio_pago=None, data_manager=None):
    """Ejecuta la migración flexible solo con pesos argentinos"""
    
    try:
        consultas_migradas = []
        errores = 0
        total_ars = 0
        
        for index, row in df.iterrows():
            try:
                if col_fecha:
                    fecha = normalizar_fecha_flexible(row[col_fecha])
                else:
                    fecha = datetime.now().isoformat()
                
                paciente = str(row[col_paciente]).strip() if pd.notna(row[col_paciente]) else f'Paciente_{index+1}'
                tratamiento = str(row[col_tratamiento]).strip() if pd.notna(row[col_tratamiento]) else 'Consulta'
                monto_numerico = extraer_monto_numerico(row[col_monto])
                
                if monto_numerico <= 0:
                    errores += 1
                    continue
                
                if col_medio_pago:
                    medio_pago = str(row[col_medio_pago]).strip() if pd.notna(row[col_medio_pago]) else 'No especificado'
                else:
                    medio_pago = 'No especificado'
                
                consulta = {
                    'fecha': fecha,
                    'paciente': paciente,
                    'tratamiento': tratamiento,
                    'monto_ars': round(monto_numerico, 0),
                    'medio_pago': medio_pago
                }
                
                consultas_migradas.append(consulta)
                total_ars += monto_numerico
                
            except Exception as e:
                errores += 1
                st.warning(f"Error en fila {index+1}: {e}")
                continue
        
        if consultas_migradas:
            for consulta in consultas_migradas:
                nueva_fila = {
                    'fecha': consulta['fecha'],
                    'paciente': consulta['paciente'], 
                    'tratamiento': consulta['tratamiento'],
                    'monto_ars': consulta['monto_ars'],
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
            'total_ars': round(total_ars, 0)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'migrados': 0,
            'errores': 0,
            'total_ars': 0
        }

def show_nueva_consulta(data_manager):
    st.subheader("➕ Registrar Nueva Consulta")
    
    with st.form("nueva_consulta"):
        col1, col2 = st.columns(2)
        
        with col1:
            paciente = st.text_input("Nombre del Paciente *", placeholder="Ej: Juan Pérez")
            tratamiento = st.selectbox("Tipo de Tratamiento *", 
                ["Consulta", "Limpieza", "Operatoria Simple", "Endodoncia", "Otro"])
        
        with col2:
            monto_ars = st.number_input("Monto en ARS *", min_value=0.0, step=1000.0, value=30000.0)
            medio_pago = st.selectbox("Medio de Pago *", 
                ["Efectivo", "Transferencia", "Débito", "Crédito", "Otros"])
        
        submitted = st.form_submit_button("✅ Registrar Consulta", type="primary")
        
        if submitted:
            if paciente and tratamiento and monto_ars > 0:
                try:
                    data_manager.add_consulta(paciente, tratamiento, monto_ars, medio_pago)
                    st.success(f"✅ Consulta registrada: {paciente} - ${monto_ars:,.0f} ARS")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Complete todos los campos obligatorios")

def show_login():
    st.title("🏥 Manny App - Sistema de Gestión de Consultorios")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.write("🔐 Ingresar al Sistema")
            
            username = st.text_input("Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            
            show_demo = st.checkbox("Mostrar credenciales de prueba")
            if show_demo:
                st.info("**Usuario:** admin | **Contraseña:** Homero123")
            
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
                else:
                    st.warning("⚠️ Complete todos los campos")

def main():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        show_login()
        return
    
    user_id = st.session_state.user_id
    user_info = st.session_state.user_info
    
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        especialidad = user_info.get('especialidad', 'odontologia')
        especialidad_emoji = {'odontologia': '🦷', 'dermatologia': '🧴', 'kinesiologia': '🏃‍♂️'}.get(especialidad, '🏥')
        st.markdown(f'<h1 class="main-header">Manny App - {especialidad.title()} {especialidad_emoji}</h1>', unsafe_allow_html=True)
    
    with col2:
        st.write(f"👤 {user_info.get('nombre', user_id)}")
    
    with col3:
        if st.button("🚪 Cerrar Sesión"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # DataManager
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager(user_id=user_id)
    
    data_manager = st.session_state.data_manager
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%); border-radius: 0.5rem; margin-bottom: 1rem; color: white;'>
        <h3>🏥 Manny App</h3>
        <p style='margin: 0; font-size: 0.9em;'>{especialidad.title()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        menu = st.selectbox("📋 Menú Principal", 
                           ["🏠 Dashboard", "➕ Nueva Consulta", "📋 Gestionar Consultas", "🧮 Calculadora Inteligente", "💰 Análisis de Costos", "⚙️ Configuración Costos", "📥 Importar Datos"])
        
        st.markdown("---")
        resumen = data_manager.get_resumen()
        st.metric("💰 Ingresos", f"${resumen['ingreso_total']:,.0f} ARS")
        st.metric("📊 Consultas", resumen['total_consultas'])
        
        # Mostrar costo por hora si está configurado
        costos_analysis = data_manager.calcular_costo_hora_real()
        if costos_analysis['costo_total_anual'] > 0:
            st.markdown("---")
            st.metric("🔧 Costo/Hora Real", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
    # Router de páginas
    if menu == "🏠 Dashboard":
        show_dashboard(data_manager, user_info)
    elif menu == "➕ Nueva Consulta":
        show_nueva_consulta(data_manager)
    elif menu == "📋 Gestionar Consultas":
        show_gestionar_consultas(data_manager)
    elif menu == "🧮 Calculadora Inteligente":
        show_calculadora_inteligente(data_manager)
    elif menu == "💰 Análisis de Costos":
        show_analisis_costos(data_manager, user_info)
    elif menu == "⚙️ Configuración Costos":
        show_configuracion_costos(data_manager)
    elif menu == "📥 Migrar Datos":
        show_migration_tool(data_manager)

# =============================================================================
# FUNCIONES DE GESTIÓN DE CONSULTAS - COPIAR EN TU MANNY APP
# =============================================================================

def show_gestionar_consultas(data_manager):
    """Módulo completo de gestión de consultas existentes"""
    st.title("📋 Gestión de Consultas")
    
    if data_manager.consultas.empty:
        st.info("No hay consultas registradas aún. Ve a 'Nueva Consulta' para agregar la primera.")
        return
    
    # Preparar datos para mostrar
    df_consultas = data_manager.consultas.copy()
    df_consultas['fecha'] = pd.to_datetime(df_consultas['fecha'])
    
    # Pestañas para organizar funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Ver Todas", "🔍 Buscar/Filtrar", "✏️ Editar", "🗑️ Eliminar"
    ])
    
    with tab1:
        st.subheader("📋 Todas las Consultas")
        
        # Controles de visualización
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mostrar_desde = st.selectbox(
                "📅 Mostrar desde:",
                ["Más recientes", "Más antiguas", "Este mes", "Último mes", "Este año"]
            )
        
        with col2:
            cantidad_mostrar = st.selectbox(
                "📊 Cantidad a mostrar:",
                [10, 25, 50, 100, "Todas"],
                index=1
            )
        
        with col3:
            ordenar_por = st.selectbox(
                "🔄 Ordenar por:",
                ["Fecha (desc)", "Fecha (asc)", "Monto (desc)", "Monto (asc)", "Paciente", "Tratamiento"]
            )
        
        # Aplicar filtros de visualización
        df_display = aplicar_filtros_visualizacion(df_consultas, mostrar_desde, cantidad_mostrar, ordenar_por)
        
        # Mostrar resumen de la vista actual
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Consultas Mostradas", len(df_display))
        with col2:
            total_vista = df_display['monto_ars'].sum()
            st.metric("💰 Total Vista", f"${total_vista:,.0f} ARS")
        with col3:
            if len(df_display) > 0:
                promedio_vista = df_display['monto_ars'].mean()
                st.metric("📈 Promedio Vista", f"${promedio_vista:,.0f} ARS")
            else:
                st.metric("📈 Promedio Vista", "$0 ARS")
        with col4:
            st.metric("📅 Total Consultas", len(df_consultas))
        
        # Tabla de consultas con formato mejorado
        if not df_display.empty:
            df_mostrar = formatear_tabla_consultas(df_display)
            
            # Agregar índice para selección
            df_mostrar.insert(0, 'ID', range(1, len(df_mostrar) + 1))
            
            st.dataframe(
                df_mostrar, 
                use_container_width=True,
                hide_index=True
            )
            
            # Botón de exportación
            if st.button("📥 Exportar Vista a CSV"):
                csv_data = df_mostrar.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 Descargar CSV",
                    data=csv_data,
                    file_name=f"consultas_vista_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
    
    with tab2:
        st.subheader("🔍 Buscar y Filtrar Consultas")
        
        # Formulario de búsqueda avanzada
        with st.form("busqueda_avanzada"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔍 Criterios de Búsqueda:**")
                
                buscar_paciente = st.text_input(
                    "👤 Buscar por paciente:",
                    placeholder="Nombre del paciente...",
                    help="Busca por nombre completo o parcial"
                )
                
                buscar_tratamiento = st.selectbox(
                    "🦷 Filtrar por tratamiento:",
                    ["Todos"] + sorted(df_consultas['tratamiento'].unique().tolist())
                )
                
                buscar_medio_pago = st.selectbox(
                    "💳 Filtrar por medio de pago:",
                    ["Todos"] + sorted(df_consultas['medio_pago'].unique().tolist())
                )
            
            with col2:
                st.markdown("**📅 Rango de Fechas:**")
                
                fecha_desde = st.date_input(
                    "Desde:",
                    value=df_consultas['fecha'].min().date(),
                    min_value=df_consultas['fecha'].min().date(),
                    max_value=df_consultas['fecha'].max().date()
                )
                
                fecha_hasta = st.date_input(
                    "Hasta:",
                    value=df_consultas['fecha'].max().date(),
                    min_value=df_consultas['fecha'].min().date(),
                    max_value=df_consultas['fecha'].max().date()
                )
                
                st.markdown("**💰 Rango de Montos (ARS):**")
                
                monto_min = df_consultas['monto_ars'].min()
                monto_max = df_consultas['monto_ars'].max()
                
                rango_montos = st.slider(
                    "Selecciona rango:",
                    min_value=float(monto_min),
                    max_value=float(monto_max),
                    value=(float(monto_min), float(monto_max)),
                    step=1000.0,
                    format="$%,.0f"
                )
            
            buscar_btn = st.form_submit_button("🔍 Buscar", type="primary")
            
            if buscar_btn:
                # Aplicar filtros de búsqueda
                df_filtrado = aplicar_filtros_busqueda(
                    df_consultas, 
                    buscar_paciente, 
                    buscar_tratamiento, 
                    buscar_medio_pago,
                    fecha_desde, 
                    fecha_hasta, 
                    rango_montos
                )
                
                st.session_state.df_filtrado = df_filtrado
        
        # Mostrar resultados de búsqueda
        if hasattr(st.session_state, 'df_filtrado') and not st.session_state.df_filtrado.empty:
            st.success(f"✅ Se encontraron {len(st.session_state.df_filtrado)} consultas")
            
            # Resumen de resultados
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Resultados", len(st.session_state.df_filtrado))
            with col2:
                total_filtrado = st.session_state.df_filtrado['monto_ars'].sum()
                st.metric("💰 Total", f"${total_filtrado:,.0f} ARS")
            with col3:
                promedio_filtrado = st.session_state.df_filtrado['monto_ars'].mean()
                st.metric("📈 Promedio", f"${promedio_filtrado:,.0f} ARS")
            
            # Mostrar tabla de resultados
            df_resultados = formatear_tabla_consultas(st.session_state.df_filtrado)
            df_resultados.insert(0, 'ID', range(1, len(df_resultados) + 1))
            
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
            
            # Limpiar resultados
            if st.button("🗑️ Limpiar Búsqueda"):
                if hasattr(st.session_state, 'df_filtrado'):
                    del st.session_state.df_filtrado
                st.rerun()
        
        elif hasattr(st.session_state, 'df_filtrado'):
            st.warning("⚠️ No se encontraron consultas con los criterios especificados")
    
    with tab3:
        st.subheader("✏️ Editar Consultas")
        st.markdown("Selecciona una consulta para editar sus datos:")
        
        # Selección de consulta para editar
        df_para_editar = df_consultas.copy()
        df_para_editar['display'] = df_para_editar.apply(
            lambda row: f"{row['fecha'].strftime('%d/%m/%Y')} - {row['paciente']} - {row['tratamiento']} - ${row['monto_ars']:,.0f}",
            axis=1
        )
        
        consulta_seleccionada = st.selectbox(
            "🔍 Seleccionar consulta:",
            options=range(len(df_para_editar)),
            format_func=lambda x: df_para_editar.iloc[x]['display'],
            key="consulta_editar"
        )
        
        if consulta_seleccionada is not None:
            consulta_datos = df_para_editar.iloc[consulta_seleccionada]
            
            st.markdown("---")
            st.markdown(f"**Editando consulta del {consulta_datos['fecha'].strftime('%d/%m/%Y %H:%M')}:**")
            
            # Formulario de edición
            with st.form("editar_consulta"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nuevo_paciente = st.text_input(
                        "👤 Paciente *",
                        value=consulta_datos['paciente']
                    )
                    
                    tratamientos_disponibles = ["Consulta", "Limpieza", "Operatoria Simple", "Operatoria Compleja", 
                                               "Endodoncia", "Corona", "Extracción Simple", "Extracción Compleja", "Otro"]
                    
                    try:
                        indice_tratamiento = tratamientos_disponibles.index(consulta_datos['tratamiento'])
                    except ValueError:
                        indice_tratamiento = 0
                    
                    nuevo_tratamiento = st.selectbox(
                        "🦷 Tratamiento *",
                        tratamientos_disponibles,
                        index=indice_tratamiento
                    )
                
                with col2:
                    nuevo_monto = st.number_input(
                        "💰 Monto (ARS) *",
                        min_value=0.0,
                        value=float(consulta_datos['monto_ars']),
                        step=1000.0
                    )
                    
                    medios_pago_disponibles = ["Efectivo", "Transferencia", "Débito", "Crédito", "Mercado Pago", "Otros"]
                    
                    try:
                        indice_medio_pago = medios_pago_disponibles.index(consulta_datos['medio_pago'])
                    except ValueError:
                        indice_medio_pago = 0
                    
                    nuevo_medio_pago = st.selectbox(
                        "💳 Medio de Pago *",
                        medios_pago_disponibles,
                        index=indice_medio_pago
                    )
                
                nueva_fecha = st.date_input(
                    "📅 Fecha",
                    value=consulta_datos['fecha'].date()
                )
                
                nueva_hora = st.time_input(
                    "🕒 Hora",
                    value=consulta_datos['fecha'].time()
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    guardar_cambios = st.form_submit_button("💾 Guardar Cambios", type="primary")
                
                with col2:
                    cancelar_edicion = st.form_submit_button("❌ Cancelar")
                
                if guardar_cambios:
                    if nuevo_paciente and nuevo_tratamiento and nuevo_monto > 0:
                        # Crear nueva fecha completa
                        nueva_fecha_completa = datetime.combine(nueva_fecha, nueva_hora)
                        
                        # Actualizar la consulta usando el índice real del DataFrame
                        data_manager.consultas.iloc[consulta_seleccionada, data_manager.consultas.columns.get_loc('fecha')] = nueva_fecha_completa.isoformat()
                        data_manager.consultas.iloc[consulta_seleccionada, data_manager.consultas.columns.get_loc('paciente')] = nuevo_paciente
                        data_manager.consultas.iloc[consulta_seleccionada, data_manager.consultas.columns.get_loc('tratamiento')] = nuevo_tratamiento
                        data_manager.consultas.iloc[consulta_seleccionada, data_manager.consultas.columns.get_loc('monto_ars')] = nuevo_monto
                        data_manager.consultas.iloc[consulta_seleccionada, data_manager.consultas.columns.get_loc('medio_pago')] = nuevo_medio_pago
                        
                        if data_manager.save_data():
                            st.success("✅ Consulta actualizada exitosamente")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar los cambios")
                    else:
                        st.error("❌ Por favor complete todos los campos obligatorios")
                
                if cancelar_edicion:
                    st.info("Edición cancelada")
    
    with tab4:
        st.subheader("🗑️ Eliminar Consultas")
        
        st.warning("⚠️ **Atención:** La eliminación de consultas es permanente y no se puede deshacer.")
        
        # Selección para eliminación individual
        df_para_eliminar = df_consultas.copy()
        df_para_eliminar['display'] = df_para_eliminar.apply(
            lambda row: f"{row['fecha'].strftime('%d/%m/%Y')} - {row['paciente']} - {row['tratamiento']} - ${row['monto_ars']:,.0f}",
            axis=1
        )
        
        # Opción de eliminación individual
        st.markdown("#### 🎯 Eliminación Individual")
        
        consulta_eliminar = st.selectbox(
            "🔍 Seleccionar consulta a eliminar:",
            options=range(len(df_para_eliminar)),
            format_func=lambda x: df_para_eliminar.iloc[x]['display'],
            key="consulta_eliminar"
        )
        
        if consulta_eliminar is not None:
            consulta_datos = df_para_eliminar.iloc[consulta_eliminar]
            
            # Mostrar detalles de la consulta a eliminar
            with st.expander("👁️ Ver detalles de la consulta", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**📅 Fecha:** {consulta_datos['fecha'].strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"**👤 Paciente:** {consulta_datos['paciente']}")
                    st.write(f"**🦷 Tratamiento:** {consulta_datos['tratamiento']}")
                with col2:
                    st.write(f"**💰 Monto:** ${consulta_datos['monto_ars']:,.0f} ARS")
                    st.write(f"**💳 Medio de Pago:** {consulta_datos['medio_pago']}")
            
            # Confirmación de eliminación
            confirmar = st.checkbox("✅ Confirmo que deseo eliminar esta consulta permanentemente")
            
            if confirmar:
                if st.button("🗑️ ELIMINAR CONSULTA", type="secondary"):
                    # Usar la función delete_consulta del DataManager
                    if data_manager.delete_consulta(consulta_eliminar):
                        st.success("✅ Consulta eliminada exitosamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar la consulta")
        
        # Eliminación masiva
        st.markdown("---")
        st.markdown("#### 🧹 Eliminación Masiva")
        
        with st.expander("⚙️ Eliminar Todas las Consultas (PELIGROSO)"):
            st.error("🚨 **MUY PELIGROSO:** Esta acción eliminará TODAS sus consultas registradas.")
            
            confirmaciones = []
            confirmaciones.append(st.checkbox("☑️ Entiendo que se eliminarán TODAS mis consultas"))
            confirmaciones.append(st.checkbox("☑️ Confirmo que he hecho una copia de respaldo"))
            confirmaciones.append(st.checkbox("☑️ Realmente quiero eliminar todo"))
            
            if all(confirmaciones):
                codigo_confirmacion = st.text_input(
                    "🔐 Escriba 'ELIMINAR TODO' para confirmar:",
                    placeholder="Escriba exactamente: ELIMINAR TODO"
                )
                
                if codigo_confirmacion == "ELIMINAR TODO":
                    if st.button("🗑️ EJECUTAR ELIMINACIÓN MASIVA", type="secondary"):
                        if data_manager.delete_all_consultas():
                            st.success("✅ Todas las consultas han sido eliminadas")
                            st.rerun()
                        else:
                            st.error("❌ Error al realizar la eliminación masiva")


def aplicar_filtros_visualizacion(df, mostrar_desde, cantidad, ordenar_por):
    """Aplica filtros de visualización a las consultas"""
    df_resultado = df.copy()
    
    # Filtrar por período
    if mostrar_desde == "Este mes":
        fecha_actual = datetime.now()
        df_resultado = df_resultado[
            (df_resultado['fecha'].dt.month == fecha_actual.month) &
            (df_resultado['fecha'].dt.year == fecha_actual.year)
        ]
    elif mostrar_desde == "Último mes":
        fecha_mes_pasado = datetime.now().replace(day=1) - pd.DateOffset(months=1)
        df_resultado = df_resultado[
            (df_resultado['fecha'].dt.month == fecha_mes_pasado.month) &
            (df_resultado['fecha'].dt.year == fecha_mes_pasado.year)
        ]
    elif mostrar_desde == "Este año":
        fecha_actual = datetime.now()
        df_resultado = df_resultado[df_resultado['fecha'].dt.year == fecha_actual.year]
    
    # Ordenar
    if ordenar_por == "Fecha (desc)":
        df_resultado = df_resultado.sort_values('fecha', ascending=False)
    elif ordenar_por == "Fecha (asc)":
        df_resultado = df_resultado.sort_values('fecha', ascending=True)
    elif ordenar_por == "Monto (desc)":
        df_resultado = df_resultado.sort_values('monto_ars', ascending=False)
    elif ordenar_por == "Monto (asc)":
        df_resultado = df_resultado.sort_values('monto_ars', ascending=True)
    elif ordenar_por == "Paciente":
        df_resultado = df_resultado.sort_values('paciente')
    elif ordenar_por == "Tratamiento":
        df_resultado = df_resultado.sort_values('tratamiento')
    
    # Limitar cantidad
    if cantidad != "Todas":
        df_resultado = df_resultado.head(int(cantidad))
    
    return df_resultado


def aplicar_filtros_busqueda(df, paciente, tratamiento, medio_pago, fecha_desde, fecha_hasta, rango_montos):
    """Aplica filtros de búsqueda avanzada"""
    df_resultado = df.copy()
    
    # Filtro por paciente
    if paciente:
        df_resultado = df_resultado[
            df_resultado['paciente'].str.contains(paciente, case=False, na=False)
        ]
    
    # Filtro por tratamiento
    if tratamiento != "Todos":
        df_resultado = df_resultado[df_resultado['tratamiento'] == tratamiento]
    
    # Filtro por medio de pago
    if medio_pago != "Todos":
        df_resultado = df_resultado[df_resultado['medio_pago'] == medio_pago]
    
    # Filtro por fechas
    df_resultado = df_resultado[
        (df_resultado['fecha'].dt.date >= fecha_desde) &
        (df_resultado['fecha'].dt.date <= fecha_hasta)
    ]
    
    # Filtro por montos
    df_resultado = df_resultado[
        (df_resultado['monto_ars'] >= rango_montos[0]) &
        (df_resultado['monto_ars'] <= rango_montos[1])
    ]
    
    return df_resultado


def formatear_tabla_consultas(df):
    """Formatea la tabla de consultas para mejor visualización"""
    df_formato = df.copy()
    
    # Formatear fecha
    df_formato['Fecha'] = df_formato['fecha'].dt.strftime('%d/%m/%Y')
    df_formato['Hora'] = df_formato['fecha'].dt.strftime('%H:%M')
    
    # Formatear monto
    df_formato['Monto'] = df_formato['monto_ars'].apply(lambda x: f"${x:,.0f}")
    
    # Renombrar columnas
    df_formato = df_formato.rename(columns={
        'paciente': 'Paciente',
        'tratamiento': 'Tratamiento',
        'medio_pago': 'Medio de Pago'
    })
    
    # Seleccionar columnas finales
    return df_formato[['Fecha', 'Hora', 'Paciente', 'Tratamiento', 'Monto', 'Medio de Pago']]

if __name__ == "__main__":
    main()

#v5.0
# # 1 - imports
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime, date
# import json
# import os
# import re
# import hashlib
# from typing import Dict, List, Tuple
# import numpy as np

# # 2 - Configuración de la página
# st.set_page_config(
#     page_title="Manny App - Sistema de Gestión de Consultorios de Salud",
#     page_icon="🏥",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # 3 - CSS personalizado
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         color: #1e3a8a;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
#     .metric-card {
#         background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
#         padding: 1rem;
#         border-radius: 0.5rem;
#         color: white;
#         text-align: center;
#         margin: 0.5rem 0;
#     }
#     .cost-analysis-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 1.5rem;
#         border-radius: 1rem;
#         color: white;
#         margin: 1rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # 4 - UserManager
# class UserManager:
#     def __init__(self):
#         self.users_file = "usuarios.json"
#         self.data_folder = "data"
#         self.init_system()
    
#     def init_system(self):
#         if not os.path.exists(self.data_folder):
#             os.makedirs(self.data_folder)
        
#         if not os.path.exists(self.users_file):
#             usuarios_default = {
#                 "admin": {
#                     "password_hash": self.hash_password("Homero123"),
#                     "nombre": "Dr. Administrador",
#                     "email": "admin@manny.com",
#                     "especialidad": "odontologia",
#                     "plan": "premium",
#                     "fecha_registro": datetime.now().isoformat()
#                 }
#             }
#             self.save_users(usuarios_default)
#             for user_id in usuarios_default.keys():
#                 self.create_user_folder(user_id)
    
#     def hash_password(self, password):
#         return hashlib.sha256(password.encode()).hexdigest()
    
#     def load_users(self):
#         try:
#             with open(self.users_file, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         except:
#             return {}
    
#     def save_users(self, users_data):
#         with open(self.users_file, 'w', encoding='utf-8') as f:
#             json.dump(users_data, f, ensure_ascii=False, indent=2)
    
#     def validate_user(self, username, password):
#         users = self.load_users()
#         if username not in users:
#             return False, "Usuario no encontrado"
#         password_hash = self.hash_password(password)
#         if users[username]["password_hash"] != password_hash:
#             return False, "Contraseña incorrecta"
#         return True, "Login exitoso"
    
#     def get_user_info(self, username):
#         users = self.load_users()
#         return users.get(username, {})
    
#     def create_user_folder(self, user_id):
#         user_folder = os.path.join(self.data_folder, user_id)
#         if not os.path.exists(user_folder):
#             os.makedirs(user_folder)
#             initial_data = {
#                 'consultas': [],
#                 'config': {
#                     'costo_por_hora': 29000,
#                     'margen_ganancia': 0.40,
#                     'tipo_cambio_usd_ars': 1335.0,
#                     'horas_anuales_trabajadas': 1100
#                 },
#                 'equipos': [],
#                 'gastos_fijos': []
#             }
#             data_file = os.path.join(user_folder, 'dental_data.json')
#             with open(data_file, 'w', encoding='utf-8') as f:
#                 json.dump(initial_data, f, ensure_ascii=False, indent=2, default=str)

# # 5 - DataManager expandido con análisis de costos
# class DataManager:
#     def __init__(self, user_id=None):
#         if user_id:
#             self.data_file = os.path.join("data", user_id, "dental_data.json")
#         else:
#             self.data_file = "dental_data.json"
#         self.user_id = user_id
#         self.load_data()
    
#     def load_data(self):
#         if os.path.exists(self.data_file):
#             try:
#                 with open(self.data_file, 'r', encoding='utf-8') as f:
#                     data = json.load(f)
#                     self.consultas = pd.DataFrame(data.get('consultas', []))
#                     self.config = data.get('config', self.get_default_config())
#                     self.equipos = data.get('equipos', [])
#                     self.gastos_fijos = data.get('gastos_fijos', [])
#             except Exception as e:
#                 st.error(f"Error cargando datos: {e}")
#                 self.init_default_data()
#         else:
#             self.init_default_data()
    
#     def init_default_data(self):
#         self.consultas = pd.DataFrame(columns=['fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago'])
#         self.config = self.get_default_config()
#         self.equipos = []
#         self.gastos_fijos = []
    
#     def get_default_config(self):
#         return {
#             'costo_por_hora': 29000,
#             'margen_ganancia': 0.40,
#             'tipo_cambio_usd_ars': 1335.0,
#             'horas_anuales_trabajadas': 1100
#         }
    
#     def save_data(self):
#         try:
#             os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
#             data = {
#                 'consultas': self.consultas.to_dict('records'),
#                 'config': self.config,
#                 'equipos': self.equipos,
#                 'gastos_fijos': self.gastos_fijos
#             }
#             with open(self.data_file, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, ensure_ascii=False, indent=2, default=str)
#             return True
#         except Exception as e:
#             st.error(f"Error guardando datos: {e}")
#             return False
    
#     def add_consulta(self, paciente, tratamiento, monto_ars, medio_pago):
#         nueva_consulta = {
#             'fecha': datetime.now().isoformat(),
#             'paciente': paciente,
#             'tratamiento': tratamiento,
#             'monto_ars': monto_ars,
#             'medio_pago': medio_pago
#         }
#         if self.consultas.empty:
#             self.consultas = pd.DataFrame([nueva_consulta])
#         else:
#             self.consultas = pd.concat([self.consultas, pd.DataFrame([nueva_consulta])], ignore_index=True)
#         self.save_data()
#         return nueva_consulta
    
#     def add_equipo(self, nombre, monto_usd, años_vida_util, fecha_compra, observaciones=""):
#         nuevo_equipo = {
#             'id': len(self.equipos) + 1,
#             'nombre': nombre,
#             'monto_compra_usd': float(monto_usd),
#             'años_vida_util': int(años_vida_util),
#             'fecha_compra': fecha_compra.isoformat() if isinstance(fecha_compra, date) else fecha_compra,
#             'observaciones': observaciones,
#             'activo': True,
#             'fecha_creacion': datetime.now().isoformat()
#         }
#         self.equipos.append(nuevo_equipo)
#         self.save_data()
#         return nuevo_equipo
    
#     def add_gasto_fijo(self, concepto, monto_mensual_ars):
#         nuevo_gasto = {
#             'id': len(self.gastos_fijos) + 1,
#             'concepto': concepto,
#             'monto_mensual_ars': float(monto_mensual_ars),
#             'activo': True,
#             'fecha_creacion': datetime.now().isoformat()
#         }
#         self.gastos_fijos.append(nuevo_gasto)
#         self.save_data()
#         return nuevo_gasto
    
#     def delete_equipo(self, equipo_id):
#         """Eliminar equipo por ID"""
#         self.equipos = [e for e in self.equipos if e.get('id') != equipo_id]
#         self.save_data()
#         return True
    
#     def delete_gasto_fijo(self, gasto_id):
#         """Eliminar gasto fijo por ID"""
#         self.gastos_fijos = [g for g in self.gastos_fijos if g.get('id') != gasto_id]
#         self.save_data()
#         return True
    
#     def calcular_costo_hora_real(self):
#         """Cálculo integral del costo por hora basado en equipos y gastos fijos"""
        
#         # 1. Costos de equipos (amortización con inflación 4% anual)
#         costo_equipos_anual_usd = 0
#         for equipo in self.equipos:
#             if equipo.get('activo', True):
#                 # Amortización con inflación
#                 costo_reposicion = equipo['monto_compra_usd'] * (1.04 ** equipo['años_vida_util'])
#                 amortizacion_anual = costo_reposicion / equipo['años_vida_util']
#                 costo_equipos_anual_usd += amortizacion_anual
        
#         # Convertir USD a ARS
#         tipo_cambio = self.config.get('tipo_cambio_usd_ars', 1335)
#         costo_equipos_anual_ars = costo_equipos_anual_usd * tipo_cambio
        
#         # 2. Gastos fijos anuales (ARS)
#         costo_gastos_anual_ars = sum([
#             gasto['monto_mensual_ars'] * 12 
#             for gasto in self.gastos_fijos 
#             if gasto.get('activo', True)
#         ])
        
#         # 3. Cálculo final
#         costo_total_anual = costo_equipos_anual_ars + costo_gastos_anual_ars
#         horas_anuales = self.config.get('horas_anuales_trabajadas', 1100)
        
#         costo_hora = costo_total_anual / horas_anuales if horas_anuales > 0 else 0
        
#         return {
#             'costo_hora_ars': costo_hora,
#             'costo_equipos_anual': costo_equipos_anual_ars,
#             'costo_gastos_anual': costo_gastos_anual_ars,
#             'costo_total_anual': costo_total_anual,
#             'horas_anuales': horas_anuales,
#             'cantidad_equipos': len([e for e in self.equipos if e.get('activo', True)]),
#             'cantidad_gastos': len([g for g in self.gastos_fijos if g.get('activo', True)])
#         }
    
#     def get_resumen(self):
#         if self.consultas.empty:
#             return {
#                 'total_consultas': 0,
#                 'ingreso_total': 0,
#                 'promedio_consulta': 0,
#                 'tratamiento_popular': 'N/A',
#                 'ingresos_mes': 0
#             }
        
#         if not self.consultas.empty:
#             self.consultas['fecha'] = pd.to_datetime(self.consultas['fecha'])
        
#         total_consultas = len(self.consultas)
#         ingreso_total = self.consultas['monto_ars'].sum()
#         promedio_consulta = ingreso_total / total_consultas if total_consultas > 0 else 0
        
#         tratamiento_popular = 'N/A'
#         if not self.consultas.empty:
#             tratamientos = self.consultas['tratamiento'].value_counts()
#             if not tratamientos.empty:
#                 tratamiento_popular = tratamientos.index[0]
        
#         fecha_actual = datetime.now()
#         mes_actual = self.consultas[
#             (self.consultas['fecha'].dt.month == fecha_actual.month) &
#             (self.consultas['fecha'].dt.year == fecha_actual.year)
#         ]
#         ingresos_mes = mes_actual['monto_ars'].sum() if not mes_actual.empty else 0
        
#         return {
#             'total_consultas': total_consultas,
#             'ingreso_total': round(ingreso_total, 0),
#             'promedio_consulta': round(promedio_consulta, 0),
#             'tratamiento_popular': tratamiento_popular,
#             'ingresos_mes': round(ingresos_mes, 0)
#         }

# # 6 - Funciones de análisis de costos
# def show_configuracion_costos(data_manager):
#     """Página de configuración de costos"""
#     st.title("⚙️ Configuración de Costos")
    
#     tab1, tab2, tab3 = st.tabs(["🔧 Equipos", "🏢 Gastos Fijos", "⚙️ Parámetros"])
    
#     with tab1:
#         st.subheader("🔧 Equipamiento del Consultorio")
        
#         # Mostrar equipos actuales con botones de eliminar
#         if data_manager.equipos:
#             st.markdown("**Equipos registrados:**")
            
#             for equipo in data_manager.equipos:
#                 col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
#                 with col1:
#                     st.write(f"**{equipo['nombre']}**")
#                 with col2:
#                     st.write(f"${equipo['monto_compra_usd']:,.0f} USD")
#                 with col3:
#                     st.write(f"{equipo['años_vida_util']} años")
#                 with col4:
#                     fecha_compra = pd.to_datetime(equipo['fecha_compra']).strftime('%d/%m/%Y')
#                     st.write(fecha_compra)
#                 with col5:
#                     if st.button("🗑️", key=f"del_equipo_{equipo['id']}", help="Eliminar equipo"):
#                         data_manager.delete_equipo(equipo['id'])
#                         st.success("Equipo eliminado")
#                         st.rerun()
#         else:
#             st.info("No hay equipos registrados aún.")
        
#         # Formulario para nuevo equipo
#         with st.form("nuevo_equipo"):
#             st.markdown("**Agregar Nuevo Equipo**")
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 nombre_equipo = st.text_input("Nombre del Equipo *", placeholder="Ej: Sillón Dental")
#                 monto_usd = st.number_input("Precio pagado (USD) *", min_value=0.0, step=100.0, value=1000.0)
            
#             with col2:
#                 años_vida = st.selectbox("Vida Útil (años)", [3, 5, 7, 8, 10], index=1)
#                 fecha_compra = st.date_input("Fecha de Compra", value=date.today())
            
#             observaciones = st.text_area("Observaciones (opcional)")
            
#             if st.form_submit_button("💾 Agregar Equipo", type="primary"):
#                 if nombre_equipo and monto_usd > 0:
#                     data_manager.add_equipo(nombre_equipo, monto_usd, años_vida, fecha_compra, observaciones)
#                     st.success("✅ Equipo agregado correctamente")
#                     st.rerun()
#                 else:
#                     st.error("❌ Complete los campos obligatorios")
    
#     with tab2:
#         st.subheader("🏢 Gastos Fijos Mensuales")
        
#         # Mostrar gastos actuales con botones de eliminar
#         if data_manager.gastos_fijos:
#             st.markdown("**Gastos fijos registrados:**")
            
#             for gasto in data_manager.gastos_fijos:
#                 col1, col2, col3 = st.columns([4, 3, 1])
                
#                 with col1:
#                     st.write(f"**{gasto['concepto']}**")
#                 with col2:
#                     st.write(f"${gasto['monto_mensual_ars']:,.0f} ARS/mes")
#                 with col3:
#                     if st.button("🗑️", key=f"del_gasto_{gasto['id']}", help="Eliminar gasto"):
#                         data_manager.delete_gasto_fijo(gasto['id'])
#                         st.success("Gasto eliminado")
#                         st.rerun()
            
#             st.markdown("---")
#             total_mensual = sum([g['monto_mensual_ars'] for g in data_manager.gastos_fijos if g.get('activo', True)])
#             st.metric("💰 Total Gastos Fijos", f"${total_mensual:,.0f} ARS/mes")
#         else:
#             st.info("No hay gastos fijos registrados aún.")
        
#         # Formulario para nuevo gasto
#         with st.form("nuevo_gasto"):
#             st.markdown("**Agregar Nuevo Gasto Fijo**")
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 concepto = st.text_input("Concepto *", placeholder="Ej: Alquiler")
#             with col2:
#                 monto_mensual = st.number_input("Monto mensual (ARS) *", min_value=0.0, step=1000.0, value=50000.0)
            
#             if st.form_submit_button("💾 Agregar Gasto", type="primary"):
#                 if concepto and monto_mensual > 0:
#                     data_manager.add_gasto_fijo(concepto, monto_mensual)
#                     st.success("✅ Gasto agregado correctamente")
#                     st.rerun()
#                 else:
#                     st.error("❌ Complete los campos obligatorios")
    
#     with tab3:
#         st.subheader("⚙️ Parámetros de Trabajo")
        
#         with st.form("parametros"):
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 nuevas_horas = st.number_input(
#                     "Horas anuales trabajadas",
#                     min_value=500,
#                     max_value=2000,
#                     value=data_manager.config.get('horas_anuales_trabajadas', 1100),
#                     step=50,
#                     help="Horas productivas anuales (descontando vacaciones, días no trabajados, etc.)"
#                 )
                
#                 nuevo_margen = st.slider(
#                     "Margen de ganancia objetivo (%)",
#                     min_value=10,
#                     max_value=200,
#                     value=int(data_manager.config.get('margen_ganancia', 0.4) * 100),
#                     step=5
#                 ) / 100
            
#             with col2:
#                 nuevo_tc = st.number_input(
#                     "Tipo de cambio USD/ARS",
#                     min_value=100.0,
#                     max_value=5000.0,
#                     value=data_manager.config.get('tipo_cambio_usd_ars', 1335.0),
#                     step=10.0,
#                     help="Para convertir equipos en USD a ARS"
#                 )
            
#             if st.form_submit_button("💾 Actualizar Parámetros", type="primary"):
#                 data_manager.config.update({
#                     'horas_anuales_trabajadas': nuevas_horas,
#                     'margen_ganancia': nuevo_margen,
#                     'tipo_cambio_usd_ars': nuevo_tc
#                 })
#                 data_manager.save_data()
#                 st.success("✅ Parámetros actualizados exitosamente")
#                 st.rerun()

# def show_analisis_costos(data_manager, user_info):
#     """Página de análisis de costos integral"""
#     st.title("💰 Análisis de Costos y Rentabilidad")
    
#     especialidad = user_info.get('especialidad', 'odontologia')
#     especialidad_emoji = {
#         'odontologia': '🦷',
#         'dermatologia': '🧴',
#         'kinesiologia': '🏃‍♂️'
#     }.get(especialidad, '🏥')
    
#     st.markdown(f"### {especialidad_emoji} {especialidad.title()}")
    
#     # Calcular métricas de costos
#     costos_analysis = data_manager.calcular_costo_hora_real()
    
#     # Verificar si tiene costos configurados
#     if costos_analysis['costo_total_anual'] == 0:
#         st.warning("⚠️ No tiene equipos ni gastos fijos configurados. Vaya a 'Configuración Costos' para comenzar.")
#         st.info("💡 El análisis de costos le permitirá conocer su costo real por hora y optimizar sus precios.")
#         return
    
#     # Métricas principales
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("💰 Costo Real/Hora", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
#     with col2:
#         precio_minimo = costos_analysis['costo_hora_ars'] * 1.5  # 50% margen
#         st.metric("📊 Precio Mín. (50%)", f"${precio_minimo:,.0f} ARS")
    
#     with col3:
#         precio_optimo = costos_analysis['costo_hora_ars'] * 2  # 100% margen
#         st.metric("🎯 Precio Óptimo (100%)", f"${precio_optimo:,.0f} ARS")
    
#     with col4:
#         resumen = data_manager.get_resumen()
#         if resumen['promedio_consulta'] > 0:
#             consultas_breakeven = costos_analysis['costo_total_anual'] / resumen['promedio_consulta']
#             st.metric("⚖️ Consultas Break-Even", f"{consultas_breakeven:,.0f} /año")
#         else:
#             st.metric("⚖️ Consultas Break-Even", "Sin datos")
    
#     # Gráfico de composición de costos
#     if costos_analysis['costo_total_anual'] > 0:
#         st.subheader("📊 Composición de Costos Anuales")
        
#         costos_data = pd.DataFrame([
#             {"Categoría": "Equipos (Amortización)", "Monto": costos_analysis['costo_equipos_anual']},
#             {"Categoría": "Gastos Fijos", "Monto": costos_analysis['costo_gastos_anual']}
#         ])
        
#         col1, col2 = st.columns([2, 1])
        
#         with col1:
#             fig_costos = px.pie(
#                 costos_data, 
#                 values='Monto', 
#                 names='Categoría',
#                 title=f"Total Anual: ${costos_analysis['costo_total_anual']:,.0f} ARS",
#                 color_discrete_sequence=['#3b82f6', '#ef4444']
#             )
#             st.plotly_chart(fig_costos, use_container_width=True)
        
#         with col2:
#             st.markdown("**📈 Resumen de Configuración**")
#             st.metric("🔧 Equipos", costos_analysis['cantidad_equipos'])
#             st.metric("🏢 Gastos Fijos", costos_analysis['cantidad_gastos'])
#             st.metric("⏰ Horas Anuales", costos_analysis['horas_anuales'])
    
#     # Análisis de rentabilidad actual
#     if resumen['total_consultas'] > 0:
#         st.subheader("📈 Análisis de Rentabilidad Actual")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.markdown("**💵 Ingresos vs Costos**")
#             ingresos_anuales = resumen['ingreso_total'] * 12  # Proyección anual
#             margen_real = ((ingresos_anuales - costos_analysis['costo_total_anual']) / ingresos_anuales * 100) if ingresos_anuales > 0 else 0
            
#             if margen_real > 50:
#                 st.success(f"✅ Margen excelente: {margen_real:.1f}%")
#             elif margen_real > 25:
#                 st.warning(f"⚠️ Margen aceptable: {margen_real:.1f}%")
#             else:
#                 st.error(f"🚨 Margen bajo: {margen_real:.1f}%")
        
#         with col2:
#             st.markdown("**⏰ Eficiencia Horaria**")
#             consultas_mes = resumen['total_consultas'] / max(1, len(data_manager.consultas['fecha'].dt.month.unique()) if not data_manager.consultas.empty else 1)
#             eficiencia = (consultas_mes * 12) / costos_analysis['horas_anuales'] if costos_analysis['horas_anuales'] > 0 else 0
            
#             st.metric("Consultas por Hora Disponible", f"{eficiencia:.2f}")

# # 7 - Funciones de interfaz (actualizadas)
# def show_dashboard(data_manager, user_info):
#     especialidad = user_info.get('especialidad', 'odontologia')
#     especialidad_emoji = {
#         'odontologia': '🦷',
#         'dermatologia': '🧴', 
#         'kinesiologia': '🏃‍♂️'
#     }.get(especialidad, '🏥')
    
#     st.subheader(f"📊 Dashboard - {user_info.get('nombre', 'Usuario')} {especialidad_emoji}")
    
#     # Análisis de costos en el dashboard
#     costos_analysis = data_manager.calcular_costo_hora_real()
    
#     # Mostrar alerta si tiene costos configurados
#     if costos_analysis['costo_total_anual'] > 0:
#         st.markdown(f"""
#         <div class="cost-analysis-card">
#             <h3>💰 Análisis de Costos Automático</h3>
#             <p>Su costo real por hora: <strong>${costos_analysis['costo_hora_ars']:,.0f} ARS</strong></p>
#             <p>Precio mínimo recomendado (50% margen): <strong>${costos_analysis['costo_hora_ars'] * 1.5:,.0f} ARS</strong></p>
#         </div>
#         """, unsafe_allow_html=True)
#     else:
#         st.info("💡 Configure sus equipos y gastos fijos para obtener análisis de costos automático.")
    
#     # Dashboard original
#     resumen = data_manager.get_resumen()
    
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("💰 Ingresos Totales", f"${resumen['ingreso_total']:,.0f} ARS")
    
#     with col2:
#         st.metric("👥 Total Consultas", resumen['total_consultas'])
    
#     with col3:
#         st.metric("📊 Promedio/Consulta", f"${resumen['promedio_consulta']:,.0f} ARS")
    
#     with col4:
#         st.metric("🔥 Más Popular", resumen['tratamiento_popular'])
    
#     if not data_manager.consultas.empty:
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.subheader("📈 Ingresos por Mes")
#             df_monthly = data_manager.consultas.copy()
#             df_monthly['fecha'] = pd.to_datetime(df_monthly['fecha'])
#             df_monthly['mes'] = df_monthly['fecha'].dt.to_period('M')
#             monthly_income = df_monthly.groupby('mes')['monto_ars'].sum().reset_index()
#             monthly_income['mes'] = monthly_income['mes'].astype(str)
            
#             fig_monthly = px.bar(monthly_income, x='mes', y='monto_ars', title="Ingresos Mensuales")
#             st.plotly_chart(fig_monthly, use_container_width=True)
        
#         with col2:
#             st.subheader("🥧 Tratamientos")
#             tratamientos = data_manager.consultas['tratamiento'].value_counts()
#             fig_pie = px.pie(values=tratamientos.values, names=tratamientos.index)
#             st.plotly_chart(fig_pie, use_container_width=True)
#     else:
#         st.info("No hay consultas registradas aún.")

# def show_calculadora_inteligente(data_manager):
#     """Calculadora inteligente con análisis de costos automático"""
#     st.title("🧮 Calculadora Inteligente de Precios")
    
#     # Análisis de costos disponibles
#     costos_analysis = data_manager.calcular_costo_hora_real()
#     tiene_costos_configurados = costos_analysis['costo_total_anual'] > 0
    
#     if tiene_costos_configurados:
#         st.success(f"✅ Usando su costo real calculado: ${costos_analysis['costo_hora_ars']:,.0f} ARS/hora")
#     else:
#         st.warning("⚠️ Configure equipos y gastos fijos para cálculos más precisos")
    
#     # Formulario principal
#     with st.form("calculadora_inteligente"):
#         col1, col2 = st.columns([2, 1])
        
#         with col1:
#             st.subheader("📋 Parámetros del Tratamiento")
            
#             # Selección de tratamiento con opción personalizada
#             lista_tratamientos = [
#                 "Consulta", "Limpieza", "Operatoria Simple", "Operatoria Compleja", 
#                 "Endodoncia", "Corona", "Extracción Simple", "Extracción Compleja", "Otro"
#             ]
            
#             tratamiento_base = st.selectbox("Tipo de Tratamiento", lista_tratamientos)
            
#             if tratamiento_base == "Otro":
#                 tratamiento_seleccionado = st.text_input(
#                     "Especificar tratamiento:",
#                     placeholder="Ej: Blanqueamiento, Implante, etc."
#                 )
#                 if not tratamiento_seleccionado:
#                     tratamiento_seleccionado = "Personalizado"
#             else:
#                 tratamiento_seleccionado = tratamiento_base
            
#             # Tiempos estimados por tratamiento
#             tiempos_estandar = {
#                 "Consulta": 0.5,
#                 "Limpieza": 1.0,
#                 "Operatoria Simple": 1.5,
#                 "Operatoria Compleja": 2.5,
#                 "Endodoncia": 3.0,
#                 "Corona": 2.0,
#                 "Extracción Simple": 0.75,
#                 "Extracción Compleja": 2.0,
#                 "Personalizado": 1.0
#             }
            
#             tiempo_sugerido = tiempos_estandar.get(tratamiento_seleccionado, 1.0)
            
#             time_hours = st.number_input(
#                 "Tiempo estimado (horas)",
#                 min_value=0.1,
#                 max_value=8.0,
#                 value=tiempo_sugerido,
#                 step=0.25,
#                 help="Tiempo que demora realizar el tratamiento"
#             )
            
#             materials_ars = st.number_input(
#                 "Costo de materiales (ARS)",
#                 min_value=0.0,
#                 value=5000.0,
#                 step=1000.0,
#                 help="Costo total de insumos para este tratamiento"
#             )
        
#         with col2:
#             st.subheader("⚙️ Configuración de Costos")
            
#             # Toggle para usar costo automático o manual
#             if tiene_costos_configurados:
#                 usar_costo_real = st.checkbox(
#                     "Usar costo real calculado",
#                     value=True,
#                     help="Basado en sus equipos y gastos fijos configurados"
#                 )
                
#                 if usar_costo_real:
#                     costo_hora_usar = costos_analysis['costo_hora_ars']
#                     st.metric("Costo/Hora Real", f"${costo_hora_usar:,.0f} ARS")
#                 else:
#                     costo_hora_usar = st.number_input(
#                         "Costo por hora manual (ARS)",
#                         min_value=5000.0,
#                         value=29000.0,
#                         step=1000.0
#                     )
#                     st.warning("Usando costo manual en lugar del calculado")
#             else:
#                 usar_costo_real = False
#                 costo_hora_usar = st.number_input(
#                     "Costo por hora (ARS)",
#                     min_value=5000.0,
#                     value=29000.0,
#                     step=1000.0,
#                     help="Configure equipos y gastos para cálculo automático"
#                 )
        
#         calcular = st.form_submit_button("🧮 Calcular Recomendaciones", type="primary")
        
#         if calcular:
#             # Cálculo base
#             costo_mano_obra = time_hours * costo_hora_usar
#             costo_total = costo_mano_obra + materials_ars
            
#             # Recomendaciones con diferentes márgenes
#             margenes = {
#                 "Supervivencia (25%)": 0.25,
#                 "Competitivo (50%)": 0.50,
#                 "Premium (75%)": 0.75,
#                 "Especialista (100%)": 1.00
#             }
            
#             st.markdown("---")
#             st.subheader("💰 Análisis de Costos")
            
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Mano de Obra", f"${costo_mano_obra:,.0f} ARS")
#             with col2:
#                 st.metric("Materiales", f"${materials_ars:,.0f} ARS")
#             with col3:
#                 st.metric("Costo Total", f"${costo_total:,.0f} ARS")
            
#             st.subheader("📊 Recomendaciones de Precios")
            
#             recomendaciones = []
#             for nombre_margen, porcentaje_margen in margenes.items():
#                 precio_final = costo_total * (1 + porcentaje_margen)
#                 ganancia = precio_final - costo_total
                
#                 recomendaciones.append({
#                     "Margen": nombre_margen,
#                     "Precio": f"${precio_final:,.0f} ARS",
#                     "Ganancia": f"${ganancia:,.0f} ARS",
#                     "Valor": precio_final
#                 })
            
#             # Mostrar recomendaciones en columnas
#             col1, col2 = st.columns(2)
            
#             for i, rec in enumerate(recomendaciones):
#                 col = col1 if i % 2 == 0 else col2
                
#                 with col:
#                     # Color según el margen
#                     if "Supervivencia" in rec["Margen"]:
#                         color = "🟡"
#                     elif "Competitivo" in rec["Margen"]:
#                         color = "🟢"
#                     elif "Premium" in rec["Margen"]:
#                         color = "🔵"
#                     else:  # Especialista
#                         color = "🟣"
                    
#                     recomendado = "← RECOMENDADO" if "Competitivo" in rec["Margen"] else ""
                    
#                     st.markdown(f"""
#                     **{color} {rec["Margen"]} {recomendado}**
#                     - Precio: {rec["Precio"]}
#                     - Ganancia: {rec["Ganancia"]}
#                     """)
            
#             # Búsqueda en registros históricos
#             st.subheader("📋 Histórico de Este Tratamiento")
            
#             if not data_manager.consultas.empty:
#                 # Buscar tratamientos exactos o similares
#                 tratamientos_exactos = data_manager.consultas[
#                     data_manager.consultas['tratamiento'].str.lower() == tratamiento_seleccionado.lower()
#                 ]
                
#                 if not tratamientos_exactos.empty:
#                     st.markdown("**Registros anteriores encontrados:**")
                    
#                     # Mostrar últimos 5 registros
#                     ultimos_registros = tratamientos_exactos.tail(5).sort_values('fecha', ascending=False)
                    
#                     for _, registro in ultimos_registros.iterrows():
#                         fecha_registro = pd.to_datetime(registro['fecha']).strftime('%d/%m/%Y')
                        
#                         col1, col2, col3 = st.columns([2, 2, 2])
#                         with col1:
#                             st.write(f"**{registro['paciente']}**")
#                         with col2:
#                             st.write(f"${registro['monto_ars']:,.0f} ARS")
#                         with col3:
#                             st.write(fecha_registro)
                    
#                     # Estadísticas del histórico
#                     precio_promedio = tratamientos_exactos['monto_ars'].mean()
#                     precio_ultimo = tratamientos_exactos.iloc[-1]['monto_ars']
                    
#                     st.markdown("---")
#                     col1, col2, col3 = st.columns(3)
                    
#                     with col1:
#                         st.metric("Precio Promedio Histórico", f"${precio_promedio:,.0f} ARS")
#                     with col2:
#                         st.metric("Último Precio Cobrado", f"${precio_ultimo:,.0f} ARS")
#                     with col3:
#                         total_realizados = len(tratamientos_exactos)
#                         st.metric("Veces Realizadas", total_realizados)
                    
#                     # Comparación con recomendaciones actuales
#                     precio_competitivo = costo_total * 1.5
                    
#                     if precio_ultimo < costo_total:
#                         st.error(f"⚠️ Su último precio (${precio_ultimo:,.0f}) estaba por debajo del costo actual")
#                     elif precio_ultimo < precio_competitivo:
#                         diferencia = precio_competitivo - precio_ultimo
#                         st.warning(f"💡 Puede aumentar ${diferencia:,.0f} respecto al último precio cobrado")
#                     else:
#                         st.success("✅ Su último precio estaba bien posicionado")
                        
#                 else:
#                     st.info(f"No se encontraron registros anteriores de '{tratamiento_seleccionado}'")
#                     st.info("Una vez que registre este tratamiento, aparecerá en el histórico para futuras consultas")
#             else:
#                 st.info("No hay consultas registradas aún para mostrar histórico")

# def extraer_monto_numerico(monto_str):
#     """Extrae valor numérico de string de monto"""
#     try:
#         if pd.isna(monto_str):
#             return 0
        
#         monto_clean = str(monto_str).strip()
        
#         # Remover símbolos comunes de moneda
#         monto_clean = re.sub(r'[$€£¥₹₽₩¢]', '', monto_clean)
#         monto_clean = re.sub(r'[^\d.,\-]', '', monto_clean)
        
#         if not monto_clean:
#             return 0
        
#         # Manejar números negativos
#         es_negativo = monto_clean.startswith('-')
#         monto_clean = monto_clean.lstrip('-')
        
#         # Determinar si el último punto/coma son decimales
#         if ',' in monto_clean and '.' in monto_clean:
#             if monto_clean.rfind(',') > monto_clean.rfind('.'):
#                 monto_clean = monto_clean.replace('.', '').replace(',', '.')
#             else:
#                 monto_clean = monto_clean.replace(',', '')
#         elif ',' in monto_clean:
#             if monto_clean.count(',') == 1 and len(monto_clean.split(',')[1]) <= 2:
#                 monto_clean = monto_clean.replace(',', '.')
#             else:
#                 monto_clean = monto_clean.replace(',', '')
        
#         resultado = float(monto_clean)
#         return -resultado if es_negativo else resultado
        
#     except Exception as e:
#         st.warning(f"No se pudo procesar monto '{monto_str}': {e}")
#         return 0

# def normalizar_fecha_flexible(fecha_valor):
#     """Normaliza fechas de múltiples formatos"""
#     try:
#         if pd.isna(fecha_valor):
#             return datetime.now().isoformat()
        
#         fecha_str = str(fecha_valor).strip()
        
#         formatos_fecha = [
#             '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y', '%d.%m.%Y', '%d.%m.%y',
#             '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
#             '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y_%m_%d',
#             '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d-%m-%Y %H:%M:%S', '%d-%m-%Y %H:%M',
#             '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
#             '%d de %B de %Y', '%d %B %Y', '%B %d, %Y', '%d %b %Y',
#         ]
        
#         for formato in formatos_fecha:
#             try:
#                 fecha_parsed = datetime.strptime(fecha_str, formato)
#                 return fecha_parsed.isoformat()
#             except ValueError:
#                 continue
        
#         try:
#             fecha_pandas = pd.to_datetime(fecha_str, dayfirst=True, errors='coerce')
#             if not pd.isna(fecha_pandas):
#                 return fecha_pandas.isoformat()
#         except:
#             pass
        
#         st.warning(f"No se pudo procesar fecha '{fecha_valor}', usando fecha actual")
#         return datetime.now().isoformat()
        
#     except Exception as e:
#         st.warning(f"Error procesando fecha '{fecha_valor}': {e}")
#         return datetime.now().isoformat()

# def show_migration_tool(data_manager):
#     """Herramienta de migración flexible para cualquier CSV"""
#     st.title("📥 Migración de Datos desde CSV")
    
#     st.markdown("""
#     **Migración Universal de CSV**
    
#     Esta herramienta puede trabajar con cualquier archivo CSV:
#     - Mapea automáticamente las columnas de tu archivo
#     - Convierte formatos de fecha y moneda
#     - Todo en pesos argentinos
#     - Vista previa antes de migrar
#     """)
    
#     uploaded_file = st.file_uploader(
#         "Sube tu archivo CSV", 
#         type=['csv'],
#         help="Sube cualquier archivo CSV con datos de consultas"
#     )
    
#     if uploaded_file is not None:
#         try:
#             # Detectar encoding
#             encoding_options = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
#             df = None
#             encoding_usado = None
            
#             for encoding in encoding_options:
#                 try:
#                     df = pd.read_csv(uploaded_file, encoding=encoding)
#                     encoding_usado = encoding
#                     break
#                 except UnicodeDecodeError:
#                     continue
            
#             if df is None:
#                 st.error("No se pudo leer el archivo. Verifica el formato.")
#                 return
            
#             st.success(f"Archivo cargado correctamente (encoding: {encoding_usado})")
            
#             # Vista previa del archivo
#             with st.expander("Vista Previa del Archivo", expanded=True):
#                 col1, col2, col3 = st.columns(3)
#                 with col1:
#                     st.metric("Total Registros", len(df))
#                 with col2:
#                     st.metric("Columnas", len(df.columns))
#                 with col3:
#                     st.metric("Tamaño", f"{uploaded_file.size / 1024:.1f} KB")
                
#                 st.markdown("**Primeras 5 filas:**")
#                 st.dataframe(df.head(), use_container_width=True)
                
#                 st.markdown("**Columnas disponibles:**")
#                 st.write(", ".join(df.columns.tolist()))
            
#             # Mapeo de columnas
#             st.subheader("Mapeo de Columnas")
#             st.markdown("Indica qué columna de tu CSV corresponde a cada campo:")
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.markdown("**Campos Obligatorios:**")
                
#                 col_paciente = st.selectbox(
#                     "Columna de Pacientes *",
#                     options=['-- Seleccionar --'] + df.columns.tolist()
#                 )
                
#                 col_tratamiento = st.selectbox(
#                     "Columna de Tratamientos *",
#                     options=['-- Seleccionar --'] + df.columns.tolist()
#                 )
                
#                 col_monto = st.selectbox(
#                     "Columna de Montos (ARS) *",
#                     options=['-- Seleccionar --'] + df.columns.tolist()
#                 )
            
#             with col2:
#                 st.markdown("**Campos Opcionales:**")
                
#                 col_fecha = st.selectbox(
#                     "Columna de Fechas",
#                     options=['-- Usar fecha actual --'] + df.columns.tolist()
#                 )
                
#                 col_medio_pago = st.selectbox(
#                     "Columna de Medio de Pago",
#                     options=['-- Usar "No especificado" --'] + df.columns.tolist()
#                 )
            
#             # Vista previa del mapeo
#             if (col_paciente != '-- Seleccionar --' and 
#                 col_tratamiento != '-- Seleccionar --' and 
#                 col_monto != '-- Seleccionar --'):
                
#                 st.subheader("Vista Previa del Mapeo")
                
#                 muestra = df.head(5).copy()
#                 preview_data = []
                
#                 for _, row in muestra.iterrows():
#                     if col_fecha == '-- Usar fecha actual --':
#                         fecha_procesada = datetime.now().strftime('%d/%m/%Y')
#                     else:
#                         fecha_raw = row[col_fecha]
#                         fecha_iso = normalizar_fecha_flexible(fecha_raw)
#                         fecha_procesada = datetime.fromisoformat(fecha_iso).strftime('%d/%m/%Y')
                    
#                     monto_raw = row[col_monto]
#                     monto_procesado = extraer_monto_numerico(monto_raw)
                    
#                     if col_medio_pago == '-- Usar "No especificado" --':
#                         medio_pago = "No especificado"
#                     else:
#                         medio_pago = str(row[col_medio_pago]) if pd.notna(row[col_medio_pago]) else "No especificado"
                    
#                     preview_data.append({
#                         'Fecha': fecha_procesada,
#                         'Paciente': str(row[col_paciente]),
#                         'Tratamiento': str(row[col_tratamiento]),
#                         'Monto Original': str(monto_raw),
#                         'Monto ARS': f"${monto_procesado:,.0f}",
#                         'Medio de Pago': medio_pago
#                     })
                
#                 preview_df = pd.DataFrame(preview_data)
#                 st.dataframe(preview_df, use_container_width=True)
                
#                 # Estadísticas pre-migración
#                 col1, col2, col3, col4 = st.columns(4)
                
#                 with col1:
#                     pacientes_unicos = df[col_paciente].nunique()
#                     st.metric("Pacientes Únicos", pacientes_unicos)
                
#                 with col2:
#                     tratamientos_unicos = df[col_tratamiento].nunique()
#                     st.metric("Tipos de Tratamiento", tratamientos_unicos)
                
#                 with col3:
#                     montos_procesados = df[col_monto].apply(extraer_monto_numerico)
#                     total_estimado = montos_procesados.sum()
#                     st.metric("Total Estimado", f"${total_estimado:,.0f} ARS")
                
#                 with col4:
#                     registros_validos = len(df.dropna(subset=[col_paciente, col_tratamiento, col_monto]))
#                     st.metric("Registros Válidos", registros_validos)
                
#                 # Botón de migración
#                 st.markdown("---")
                
#                 col1, col2 = st.columns([3, 1])
                
#                 with col1:
#                     st.markdown("### ¿Todo se ve correcto?")
#                     st.markdown("Revisa la vista previa y las estadísticas antes de proceder.")
                
#                 with col2:
#                     if st.button("Ejecutar Migración", type="primary", use_container_width=True):
#                         with st.spinner("Migrando datos..."):
#                             resultado = ejecutar_migracion_flexible(
#                                 df=df,
#                                 col_paciente=col_paciente,
#                                 col_tratamiento=col_tratamiento,
#                                 col_monto=col_monto,
#                                 col_fecha=col_fecha if col_fecha != '-- Usar fecha actual --' else None,
#                                 col_medio_pago=col_medio_pago if col_medio_pago != '-- Usar "No especificado" --' else None,
#                                 data_manager=data_manager
#                             )
                        
#                         if resultado['success']:
#                             st.success("Migración completada exitosamente!")
                            
#                             col1, col2, col3 = st.columns(3)
#                             with col1:
#                                 st.metric("Registros Migrados", resultado['migrados'])
#                             with col2:
#                                 st.metric("Errores", resultado['errores'])
#                             with col3:
#                                 st.metric("Total Migrado", f"${resultado['total_ars']:,.0f} ARS")
                            
#                             if resultado['errores'] > 0:
#                                 st.warning(f"{resultado['errores']} registros tuvieron problemas y no se migraron")
                            
#                             st.info("Recarga la página para ver los datos migrados en el Dashboard")
                            
#                             if st.button("Recargar Aplicación"):
#                                 st.rerun()
                        
#                         else:
#                             st.error(f"Error en la migración: {resultado['error']}")
            
#             else:
#                 st.info("Por favor selecciona al menos las columnas obligatorias para continuar")
        
#         except Exception as e:
#             st.error(f"Error procesando el archivo: {e}")
    
#     else:
#         st.info("Sube un archivo CSV para comenzar")

# def ejecutar_migracion_flexible(df, col_paciente, col_tratamiento, col_monto, 
#                                col_fecha=None, col_medio_pago=None, data_manager=None):
#     """Ejecuta la migración flexible solo con pesos argentinos"""
    
#     try:
#         consultas_migradas = []
#         errores = 0
#         total_ars = 0
        
#         for index, row in df.iterrows():
#             try:
#                 if col_fecha:
#                     fecha = normalizar_fecha_flexible(row[col_fecha])
#                 else:
#                     fecha = datetime.now().isoformat()
                
#                 paciente = str(row[col_paciente]).strip() if pd.notna(row[col_paciente]) else f'Paciente_{index+1}'
#                 tratamiento = str(row[col_tratamiento]).strip() if pd.notna(row[col_tratamiento]) else 'Consulta'
#                 monto_numerico = extraer_monto_numerico(row[col_monto])
                
#                 if monto_numerico <= 0:
#                     errores += 1
#                     continue
                
#                 if col_medio_pago:
#                     medio_pago = str(row[col_medio_pago]).strip() if pd.notna(row[col_medio_pago]) else 'No especificado'
#                 else:
#                     medio_pago = 'No especificado'
                
#                 consulta = {
#                     'fecha': fecha,
#                     'paciente': paciente,
#                     'tratamiento': tratamiento,
#                     'monto_ars': round(monto_numerico, 0),
#                     'medio_pago': medio_pago
#                 }
                
#                 consultas_migradas.append(consulta)
#                 total_ars += monto_numerico
                
#             except Exception as e:
#                 errores += 1
#                 st.warning(f"Error en fila {index+1}: {e}")
#                 continue
        
#         if consultas_migradas:
#             for consulta in consultas_migradas:
#                 nueva_fila = {
#                     'fecha': consulta['fecha'],
#                     'paciente': consulta['paciente'], 
#                     'tratamiento': consulta['tratamiento'],
#                     'monto_ars': consulta['monto_ars'],
#                     'medio_pago': consulta['medio_pago']
#                 }
                
#                 if data_manager.consultas.empty:
#                     data_manager.consultas = pd.DataFrame([nueva_fila])
#                 else:
#                     data_manager.consultas = pd.concat([data_manager.consultas, pd.DataFrame([nueva_fila])], ignore_index=True)
            
#             data_manager.save_data()
        
#         return {
#             'success': True,
#             'migrados': len(consultas_migradas),
#             'errores': errores,
#             'total_ars': round(total_ars, 0)
#         }
        
#     except Exception as e:
#         return {
#             'success': False,
#             'error': str(e),
#             'migrados': 0,
#             'errores': 0,
#             'total_ars': 0
#         }

# def show_nueva_consulta(data_manager):
#     st.subheader("➕ Registrar Nueva Consulta")
    
#     with st.form("nueva_consulta"):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             paciente = st.text_input("Nombre del Paciente *", placeholder="Ej: Juan Pérez")
#             tratamiento = st.selectbox("Tipo de Tratamiento *", 
#                 ["Consulta", "Limpieza", "Operatoria Simple", "Endodoncia", "Otro"])
        
#         with col2:
#             monto_ars = st.number_input("Monto en ARS *", min_value=0.0, step=1000.0, value=30000.0)
#             medio_pago = st.selectbox("Medio de Pago *", 
#                 ["Efectivo", "Transferencia", "Débito", "Crédito", "Otros"])
        
#         submitted = st.form_submit_button("✅ Registrar Consulta", type="primary")
        
#         if submitted:
#             if paciente and tratamiento and monto_ars > 0:
#                 try:
#                     data_manager.add_consulta(paciente, tratamiento, monto_ars, medio_pago)
#                     st.success(f"✅ Consulta registrada: {paciente} - ${monto_ars:,.0f} ARS")
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"❌ Error: {e}")
#             else:
#                 st.error("❌ Complete todos los campos obligatorios")

# def show_login():
#     st.title("🏥 Manny App - Sistema de Gestión de Consultorios")
    
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         with st.form("login_form"):
#             st.write("🔐 Ingresar al Sistema")
            
#             username = st.text_input("Usuario", placeholder="Ingrese su usuario")
#             password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            
#             show_demo = st.checkbox("Mostrar credenciales de prueba")
#             if show_demo:
#                 st.info("**Usuario:** admin | **Contraseña:** Homero123")
            
#             login_button = st.form_submit_button("🚀 Ingresar", use_container_width=True)
            
#             if login_button:
#                 if username and password:
#                     user_manager = UserManager()
#                     is_valid, message = user_manager.validate_user(username, password)
                    
#                     if is_valid:
#                         st.session_state.authenticated = True
#                         st.session_state.user_id = username
#                         st.session_state.user_info = user_manager.get_user_info(username)
#                         st.success(f"✅ {message}")
#                         st.rerun()
#                     else:
#                         st.error(f"❌ {message}")
#                 else:
#                     st.warning("⚠️ Complete todos los campos")

# def main():
#     if 'authenticated' not in st.session_state or not st.session_state.authenticated:
#         show_login()
#         return
    
#     user_id = st.session_state.user_id
#     user_info = st.session_state.user_info
    
#     # Header
#     col1, col2, col3 = st.columns([3, 1, 1])
    
#     with col1:
#         especialidad = user_info.get('especialidad', 'odontologia')
#         especialidad_emoji = {'odontologia': '🦷', 'dermatologia': '🧴', 'kinesiologia': '🏃‍♂️'}.get(especialidad, '🏥')
#         st.markdown(f'<h1 class="main-header">Manny App - {especialidad.title()} {especialidad_emoji}</h1>', unsafe_allow_html=True)
    
#     with col2:
#         st.write(f"👤 {user_info.get('nombre', user_id)}")
    
#     with col3:
#         if st.button("🚪 Cerrar Sesión"):
#             for key in list(st.session_state.keys()):
#                 del st.session_state[key]
#             st.rerun()
    
#     # DataManager
#     if 'data_manager' not in st.session_state:
#         st.session_state.data_manager = DataManager(user_id=user_id)
    
#     data_manager = st.session_state.data_manager
    
#     # Sidebar
#     with st.sidebar:
#         st.markdown(f"""
#         <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%); border-radius: 0.5rem; margin-bottom: 1rem; color: white;'>
#         <h3>🏥 Manny App</h3>
#         <p style='margin: 0; font-size: 0.9em;'>{especialidad.title()}</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         menu = st.selectbox("📋 Menú Principal", 
#                            ["🏠 Dashboard", "➕ Nueva Consulta", "🧮 Calculadora Inteligente", "💰 Análisis de Costos", "⚙️ Configuración Costos", "📥 Importar Datos"])
        
#         st.markdown("---")
#         resumen = data_manager.get_resumen()
#         st.metric("💰 Ingresos", f"${resumen['ingreso_total']:,.0f} ARS")
#         st.metric("📊 Consultas", resumen['total_consultas'])
        
#         # Mostrar costo por hora si está configurado
#         costos_analysis = data_manager.calcular_costo_hora_real()
#         if costos_analysis['costo_total_anual'] > 0:
#             st.markdown("---")
#             st.metric("🔧 Costo/Hora Real", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
#     # Router de páginas
#     if menu == "🏠 Dashboard":
#         show_dashboard(data_manager, user_info)
#     elif menu == "➕ Nueva Consulta":
#         show_nueva_consulta(data_manager)
#     elif menu == "🧮 Calculadora Inteligente":
#         show_calculadora_inteligente(data_manager)
#     elif menu == "💰 Análisis de Costos":
#         show_analisis_costos(data_manager, user_info)
#     elif menu == "⚙️ Configuración Costos":
#         show_configuracion_costos(data_manager)
#     elif menu == "📥 Importar Datos":
#         show_migration_tool(data_manager)

# if __name__ == "__main__":
#     main()

# # v4.0
# # 1 - imports
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime, date
# import json
# import os
# import re
# import hashlib
# from typing import Dict, List, Tuple
# import numpy as np

# # 2 - Configuración de la página
# st.set_page_config(
#     page_title="Manny App - Sistema de Gestión de Consultorios de Salud",
#     page_icon="🏥",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # 3 - CSS personalizado
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         color: #1e3a8a;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
#     .metric-card {
#         background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
#         padding: 1rem;
#         border-radius: 0.5rem;
#         color: white;
#         text-align: center;
#         margin: 0.5rem 0;
#     }
#     .cost-analysis-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 1.5rem;
#         border-radius: 1rem;
#         color: white;
#         margin: 1rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # 4 - UserManager
# class UserManager:
#     def __init__(self):
#         self.users_file = "usuarios.json"
#         self.data_folder = "data"
#         self.init_system()
    
#     def init_system(self):
#         if not os.path.exists(self.data_folder):
#             os.makedirs(self.data_folder)
        
#         if not os.path.exists(self.users_file):
#             usuarios_default = {
#                 "admin": {
#                     "password_hash": self.hash_password("Homero123"),
#                     "nombre": "Dr. Administrador",
#                     "email": "admin@manny.com",
#                     "especialidad": "odontologia",
#                     "plan": "premium",
#                     "fecha_registro": datetime.now().isoformat()
#                 }
#             }
#             self.save_users(usuarios_default)
#             for user_id in usuarios_default.keys():
#                 self.create_user_folder(user_id)
    
#     def hash_password(self, password):
#         return hashlib.sha256(password.encode()).hexdigest()
    
#     def load_users(self):
#         try:
#             with open(self.users_file, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         except:
#             return {}
    
#     def save_users(self, users_data):
#         with open(self.users_file, 'w', encoding='utf-8') as f:
#             json.dump(users_data, f, ensure_ascii=False, indent=2)
    
#     def validate_user(self, username, password):
#         users = self.load_users()
#         if username not in users:
#             return False, "Usuario no encontrado"
#         password_hash = self.hash_password(password)
#         if users[username]["password_hash"] != password_hash:
#             return False, "Contraseña incorrecta"
#         return True, "Login exitoso"
    
#     def get_user_info(self, username):
#         users = self.load_users()
#         return users.get(username, {})
    
#     def create_user_folder(self, user_id):
#         user_folder = os.path.join(self.data_folder, user_id)
#         if not os.path.exists(user_folder):
#             os.makedirs(user_folder)
#             initial_data = {
#                 'consultas': [],
#                 'config': {
#                     'costo_por_hora': 29000,
#                     'margen_ganancia': 0.40,
#                     'tipo_cambio_usd_ars': 1335.0,
#                     'horas_anuales_trabajadas': 1100
#                 },
#                 'equipos': [],
#                 'gastos_fijos': []
#             }
#             data_file = os.path.join(user_folder, 'dental_data.json')
#             with open(data_file, 'w', encoding='utf-8') as f:
#                 json.dump(initial_data, f, ensure_ascii=False, indent=2, default=str)

# # 5 - DataManager expandido con análisis de costos
# class DataManager:
#     def __init__(self, user_id=None):
#         if user_id:
#             self.data_file = os.path.join("data", user_id, "dental_data.json")
#         else:
#             self.data_file = "dental_data.json"
#         self.user_id = user_id
#         self.load_data()
    
#     def load_data(self):
#         if os.path.exists(self.data_file):
#             try:
#                 with open(self.data_file, 'r', encoding='utf-8') as f:
#                     data = json.load(f)
#                     self.consultas = pd.DataFrame(data.get('consultas', []))
#                     self.config = data.get('config', self.get_default_config())
#                     self.equipos = data.get('equipos', [])
#                     self.gastos_fijos = data.get('gastos_fijos', [])
#             except Exception as e:
#                 st.error(f"Error cargando datos: {e}")
#                 self.init_default_data()
#         else:
#             self.init_default_data()
    
#     def init_default_data(self):
#         self.consultas = pd.DataFrame(columns=['fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago'])
#         self.config = self.get_default_config()
#         self.equipos = []
#         self.gastos_fijos = []
    
#     def get_default_config(self):
#         return {
#             'costo_por_hora': 29000,
#             'margen_ganancia': 0.40,
#             'tipo_cambio_usd_ars': 1335.0,
#             'horas_anuales_trabajadas': 1100
#         }
    
#     def save_data(self):
#         try:
#             os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
#             data = {
#                 'consultas': self.consultas.to_dict('records'),
#                 'config': self.config,
#                 'equipos': self.equipos,
#                 'gastos_fijos': self.gastos_fijos
#             }
#             with open(self.data_file, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, ensure_ascii=False, indent=2, default=str)
#             return True
#         except Exception as e:
#             st.error(f"Error guardando datos: {e}")
#             return False
    
#     def add_consulta(self, paciente, tratamiento, monto_ars, medio_pago):
#         nueva_consulta = {
#             'fecha': datetime.now().isoformat(),
#             'paciente': paciente,
#             'tratamiento': tratamiento,
#             'monto_ars': monto_ars,
#             'medio_pago': medio_pago
#         }
#         if self.consultas.empty:
#             self.consultas = pd.DataFrame([nueva_consulta])
#         else:
#             self.consultas = pd.concat([self.consultas, pd.DataFrame([nueva_consulta])], ignore_index=True)
#         self.save_data()
#         return nueva_consulta
    
#     def add_equipo(self, nombre, monto_usd, años_vida_util, fecha_compra, observaciones=""):
#         nuevo_equipo = {
#             'id': len(self.equipos) + 1,
#             'nombre': nombre,
#             'monto_compra_usd': float(monto_usd),
#             'años_vida_util': int(años_vida_util),
#             'fecha_compra': fecha_compra.isoformat() if isinstance(fecha_compra, date) else fecha_compra,
#             'observaciones': observaciones,
#             'activo': True,
#             'fecha_creacion': datetime.now().isoformat()
#         }
#         self.equipos.append(nuevo_equipo)
#         self.save_data()
#         return nuevo_equipo
    
#     def add_gasto_fijo(self, concepto, monto_mensual_ars):
#         nuevo_gasto = {
#             'id': len(self.gastos_fijos) + 1,
#             'concepto': concepto,
#             'monto_mensual_ars': float(monto_mensual_ars),
#             'activo': True,
#             'fecha_creacion': datetime.now().isoformat()
#         }
#         self.gastos_fijos.append(nuevo_gasto)
#         self.save_data()
#         return nuevo_gasto
    
#     def delete_equipo(self, equipo_id):
#         """Eliminar equipo por ID"""
#         self.equipos = [e for e in self.equipos if e.get('id') != equipo_id]
#         self.save_data()
#         return True
    
#     def delete_gasto_fijo(self, gasto_id):
#         """Eliminar gasto fijo por ID"""
#         self.gastos_fijos = [g for g in self.gastos_fijos if g.get('id') != gasto_id]
#         self.save_data()
#         return True
    
#     def calcular_costo_hora_real(self):
#         """Cálculo integral del costo por hora basado en equipos y gastos fijos"""
        
#         # 1. Costos de equipos (amortización con inflación 4% anual)
#         costo_equipos_anual_usd = 0
#         for equipo in self.equipos:
#             if equipo.get('activo', True):
#                 # Amortización con inflación
#                 costo_reposicion = equipo['monto_compra_usd'] * (1.04 ** equipo['años_vida_util'])
#                 amortizacion_anual = costo_reposicion / equipo['años_vida_util']
#                 costo_equipos_anual_usd += amortizacion_anual
        
#         # Convertir USD a ARS
#         tipo_cambio = self.config.get('tipo_cambio_usd_ars', 1335)
#         costo_equipos_anual_ars = costo_equipos_anual_usd * tipo_cambio
        
#         # 2. Gastos fijos anuales (ARS)
#         costo_gastos_anual_ars = sum([
#             gasto['monto_mensual_ars'] * 12 
#             for gasto in self.gastos_fijos 
#             if gasto.get('activo', True)
#         ])
        
#         # 3. Cálculo final
#         costo_total_anual = costo_equipos_anual_ars + costo_gastos_anual_ars
#         horas_anuales = self.config.get('horas_anuales_trabajadas', 1100)
        
#         costo_hora = costo_total_anual / horas_anuales if horas_anuales > 0 else 0
        
#         return {
#             'costo_hora_ars': costo_hora,
#             'costo_equipos_anual': costo_equipos_anual_ars,
#             'costo_gastos_anual': costo_gastos_anual_ars,
#             'costo_total_anual': costo_total_anual,
#             'horas_anuales': horas_anuales,
#             'cantidad_equipos': len([e for e in self.equipos if e.get('activo', True)]),
#             'cantidad_gastos': len([g for g in self.gastos_fijos if g.get('activo', True)])
#         }
    
#     def get_resumen(self):
#         if self.consultas.empty:
#             return {
#                 'total_consultas': 0,
#                 'ingreso_total': 0,
#                 'promedio_consulta': 0,
#                 'tratamiento_popular': 'N/A',
#                 'ingresos_mes': 0
#             }
        
#         if not self.consultas.empty:
#             self.consultas['fecha'] = pd.to_datetime(self.consultas['fecha'])
        
#         total_consultas = len(self.consultas)
#         ingreso_total = self.consultas['monto_ars'].sum()
#         promedio_consulta = ingreso_total / total_consultas if total_consultas > 0 else 0
        
#         tratamiento_popular = 'N/A'
#         if not self.consultas.empty:
#             tratamientos = self.consultas['tratamiento'].value_counts()
#             if not tratamientos.empty:
#                 tratamiento_popular = tratamientos.index[0]
        
#         fecha_actual = datetime.now()
#         mes_actual = self.consultas[
#             (self.consultas['fecha'].dt.month == fecha_actual.month) &
#             (self.consultas['fecha'].dt.year == fecha_actual.year)
#         ]
#         ingresos_mes = mes_actual['monto_ars'].sum() if not mes_actual.empty else 0
        
#         return {
#             'total_consultas': total_consultas,
#             'ingreso_total': round(ingreso_total, 0),
#             'promedio_consulta': round(promedio_consulta, 0),
#             'tratamiento_popular': tratamiento_popular,
#             'ingresos_mes': round(ingresos_mes, 0)
#         }

# # 6 - Funciones de análisis de costos
# def show_configuracion_costos(data_manager):
#     """Página de configuración de costos"""
#     st.title("⚙️ Configuración de Costos")
    
#     tab1, tab2, tab3 = st.tabs(["🔧 Equipos", "🏢 Gastos Fijos", "⚙️ Parámetros"])
    
#     with tab1:
#         st.subheader("🔧 Equipamiento del Consultorio")
        
#         # Mostrar equipos actuales con botones de eliminar
#         if data_manager.equipos:
#             st.markdown("**Equipos registrados:**")
            
#             for equipo in data_manager.equipos:
#                 col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
#                 with col1:
#                     st.write(f"**{equipo['nombre']}**")
#                 with col2:
#                     st.write(f"${equipo['monto_compra_usd']:,.0f} USD")
#                 with col3:
#                     st.write(f"{equipo['años_vida_util']} años")
#                 with col4:
#                     fecha_compra = pd.to_datetime(equipo['fecha_compra']).strftime('%d/%m/%Y')
#                     st.write(fecha_compra)
#                 with col5:
#                     if st.button("🗑️", key=f"del_equipo_{equipo['id']}", help="Eliminar equipo"):
#                         data_manager.delete_equipo(equipo['id'])
#                         st.success("Equipo eliminado")
#                         st.rerun()
#         else:
#             st.info("No hay equipos registrados aún.")
        
#         # Formulario para nuevo equipo
#         with st.form("nuevo_equipo"):
#             st.markdown("**Agregar Nuevo Equipo**")
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 nombre_equipo = st.text_input("Nombre del Equipo *", placeholder="Ej: Sillón Dental")
#                 monto_usd = st.number_input("Precio pagado (USD) *", min_value=0.0, step=100.0, value=1000.0)
            
#             with col2:
#                 años_vida = st.selectbox("Vida Útil (años)", [3, 5, 7, 8, 10], index=1)
#                 fecha_compra = st.date_input("Fecha de Compra", value=date.today())
            
#             observaciones = st.text_area("Observaciones (opcional)")
            
#             if st.form_submit_button("💾 Agregar Equipo", type="primary"):
#                 if nombre_equipo and monto_usd > 0:
#                     data_manager.add_equipo(nombre_equipo, monto_usd, años_vida, fecha_compra, observaciones)
#                     st.success("✅ Equipo agregado correctamente")
#                     st.rerun()
#                 else:
#                     st.error("❌ Complete los campos obligatorios")
    
#     with tab2:
#         st.subheader("🏢 Gastos Fijos Mensuales")
        
#         # Mostrar gastos actuales con botones de eliminar
#         if data_manager.gastos_fijos:
#             st.markdown("**Gastos fijos registrados:**")
            
#             for gasto in data_manager.gastos_fijos:
#                 col1, col2, col3 = st.columns([4, 3, 1])
                
#                 with col1:
#                     st.write(f"**{gasto['concepto']}**")
#                 with col2:
#                     st.write(f"${gasto['monto_mensual_ars']:,.0f} ARS/mes")
#                 with col3:
#                     if st.button("🗑️", key=f"del_gasto_{gasto['id']}", help="Eliminar gasto"):
#                         data_manager.delete_gasto_fijo(gasto['id'])
#                         st.success("Gasto eliminado")
#                         st.rerun()
            
#             st.markdown("---")
#             total_mensual = sum([g['monto_mensual_ars'] for g in data_manager.gastos_fijos if g.get('activo', True)])
#             st.metric("💰 Total Gastos Fijos", f"${total_mensual:,.0f} ARS/mes")
#         else:
#             st.info("No hay gastos fijos registrados aún.")
        
#         # Formulario para nuevo gasto
#         with st.form("nuevo_gasto"):
#             st.markdown("**Agregar Nuevo Gasto Fijo**")
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 concepto = st.text_input("Concepto *", placeholder="Ej: Alquiler")
#             with col2:
#                 monto_mensual = st.number_input("Monto mensual (ARS) *", min_value=0.0, step=1000.0, value=50000.0)
            
#             if st.form_submit_button("💾 Agregar Gasto", type="primary"):
#                 if concepto and monto_mensual > 0:
#                     data_manager.add_gasto_fijo(concepto, monto_mensual)
#                     st.success("✅ Gasto agregado correctamente")
#                     st.rerun()
#                 else:
#                     st.error("❌ Complete los campos obligatorios")
    
#     with tab3:
#         st.subheader("⚙️ Parámetros de Trabajo")
        
#         with st.form("parametros"):
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 nuevas_horas = st.number_input(
#                     "Horas anuales trabajadas",
#                     min_value=500,
#                     max_value=2000,
#                     value=data_manager.config.get('horas_anuales_trabajadas', 1100),
#                     step=50,
#                     help="Horas productivas anuales (descontando vacaciones, días no trabajados, etc.)"
#                 )
                
#                 nuevo_margen = st.slider(
#                     "Margen de ganancia objetivo (%)",
#                     min_value=10,
#                     max_value=200,
#                     value=int(data_manager.config.get('margen_ganancia', 0.4) * 100),
#                     step=5
#                 ) / 100
            
#             with col2:
#                 nuevo_tc = st.number_input(
#                     "Tipo de cambio USD/ARS",
#                     min_value=100.0,
#                     max_value=5000.0,
#                     value=data_manager.config.get('tipo_cambio_usd_ars', 1335.0),
#                     step=10.0,
#                     help="Para convertir equipos en USD a ARS"
#                 )
            
#             if st.form_submit_button("💾 Actualizar Parámetros", type="primary"):
#                 data_manager.config.update({
#                     'horas_anuales_trabajadas': nuevas_horas,
#                     'margen_ganancia': nuevo_margen,
#                     'tipo_cambio_usd_ars': nuevo_tc
#                 })
#                 data_manager.save_data()
#                 st.success("✅ Parámetros actualizados exitosamente")
#                 st.rerun()

# def show_analisis_costos(data_manager, user_info):
#     """Página de análisis de costos integral"""
#     st.title("💰 Análisis de Costos y Rentabilidad")
    
#     especialidad = user_info.get('especialidad', 'odontologia')
#     especialidad_emoji = {
#         'odontologia': '🦷',
#         'dermatologia': '🧴',
#         'kinesiologia': '🏃‍♂️'
#     }.get(especialidad, '🏥')
    
#     st.markdown(f"### {especialidad_emoji} {especialidad.title()}")
    
#     # Calcular métricas de costos
#     costos_analysis = data_manager.calcular_costo_hora_real()
    
#     # Verificar si tiene costos configurados
#     if costos_analysis['costo_total_anual'] == 0:
#         st.warning("⚠️ No tiene equipos ni gastos fijos configurados. Vaya a 'Configuración Costos' para comenzar.")
#         st.info("💡 El análisis de costos le permitirá conocer su costo real por hora y optimizar sus precios.")
#         return
    
#     # Métricas principales
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("💰 Costo Real/Hora", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
#     with col2:
#         precio_minimo = costos_analysis['costo_hora_ars'] * 1.5  # 50% margen
#         st.metric("📊 Precio Mín. (50%)", f"${precio_minimo:,.0f} ARS")
    
#     with col3:
#         precio_optimo = costos_analysis['costo_hora_ars'] * 2  # 100% margen
#         st.metric("🎯 Precio Óptimo (100%)", f"${precio_optimo:,.0f} ARS")
    
#     with col4:
#         resumen = data_manager.get_resumen()
#         if resumen['promedio_consulta'] > 0:
#             consultas_breakeven = costos_analysis['costo_total_anual'] / resumen['promedio_consulta']
#             st.metric("⚖️ Consultas Break-Even", f"{consultas_breakeven:,.0f} /año")
#         else:
#             st.metric("⚖️ Consultas Break-Even", "Sin datos")
    
#     # Gráfico de composición de costos
#     if costos_analysis['costo_total_anual'] > 0:
#         st.subheader("📊 Composición de Costos Anuales")
        
#         costos_data = pd.DataFrame([
#             {"Categoría": "Equipos (Amortización)", "Monto": costos_analysis['costo_equipos_anual']},
#             {"Categoría": "Gastos Fijos", "Monto": costos_analysis['costo_gastos_anual']}
#         ])
        
#         col1, col2 = st.columns([2, 1])
        
#         with col1:
#             fig_costos = px.pie(
#                 costos_data, 
#                 values='Monto', 
#                 names='Categoría',
#                 title=f"Total Anual: ${costos_analysis['costo_total_anual']:,.0f} ARS",
#                 color_discrete_sequence=['#3b82f6', '#ef4444']
#             )
#             st.plotly_chart(fig_costos, use_container_width=True)
        
#         with col2:
#             st.markdown("**📈 Resumen de Configuración**")
#             st.metric("🔧 Equipos", costos_analysis['cantidad_equipos'])
#             st.metric("🏢 Gastos Fijos", costos_analysis['cantidad_gastos'])
#             st.metric("⏰ Horas Anuales", costos_analysis['horas_anuales'])
    
#     # Análisis de rentabilidad actual
#     if resumen['total_consultas'] > 0:
#         st.subheader("📈 Análisis de Rentabilidad Actual")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.markdown("**💵 Ingresos vs Costos**")
#             ingresos_anuales = resumen['ingreso_total'] * 12  # Proyección anual
#             margen_real = ((ingresos_anuales - costos_analysis['costo_total_anual']) / ingresos_anuales * 100) if ingresos_anuales > 0 else 0
            
#             if margen_real > 50:
#                 st.success(f"✅ Margen excelente: {margen_real:.1f}%")
#             elif margen_real > 25:
#                 st.warning(f"⚠️ Margen aceptable: {margen_real:.1f}%")
#             else:
#                 st.error(f"🚨 Margen bajo: {margen_real:.1f}%")
        
#         with col2:
#             st.markdown("**⏰ Eficiencia Horaria**")
#             consultas_mes = resumen['total_consultas'] / max(1, len(data_manager.consultas['fecha'].dt.month.unique()) if not data_manager.consultas.empty else 1)
#             eficiencia = (consultas_mes * 12) / costos_analysis['horas_anuales'] if costos_analysis['horas_anuales'] > 0 else 0
            
#             st.metric("Consultas por Hora Disponible", f"{eficiencia:.2f}")

# # 7 - Funciones de interfaz (actualizadas)
# def show_dashboard(data_manager, user_info):
#     especialidad = user_info.get('especialidad', 'odontologia')
#     especialidad_emoji = {
#         'odontologia': '🦷',
#         'dermatologia': '🧴', 
#         'kinesiologia': '🏃‍♂️'
#     }.get(especialidad, '🏥')
    
#     st.subheader(f"📊 Dashboard - {user_info.get('nombre', 'Usuario')} {especialidad_emoji}")
    
#     # Análisis de costos en el dashboard
#     costos_analysis = data_manager.calcular_costo_hora_real()
    
#     # Mostrar alerta si tiene costos configurados
#     if costos_analysis['costo_total_anual'] > 0:
#         st.markdown(f"""
#         <div class="cost-analysis-card">
#             <h3>💰 Análisis de Costos Automático</h3>
#             <p>Su costo real por hora: <strong>${costos_analysis['costo_hora_ars']:,.0f} ARS</strong></p>
#             <p>Precio mínimo recomendado (50% margen): <strong>${costos_analysis['costo_hora_ars'] * 1.5:,.0f} ARS</strong></p>
#         </div>
#         """, unsafe_allow_html=True)
#     else:
#         st.info("💡 Configure sus equipos y gastos fijos para obtener análisis de costos automático.")
    
#     # Dashboard original
#     resumen = data_manager.get_resumen()
    
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("💰 Ingresos Totales", f"${resumen['ingreso_total']:,.0f} ARS")
    
#     with col2:
#         st.metric("👥 Total Consultas", resumen['total_consultas'])
    
#     with col3:
#         st.metric("📊 Promedio/Consulta", f"${resumen['promedio_consulta']:,.0f} ARS")
    
#     with col4:
#         st.metric("🔥 Más Popular", resumen['tratamiento_popular'])
    
#     if not data_manager.consultas.empty:
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.subheader("📈 Ingresos por Mes")
#             df_monthly = data_manager.consultas.copy()
#             df_monthly['fecha'] = pd.to_datetime(df_monthly['fecha'])
#             df_monthly['mes'] = df_monthly['fecha'].dt.to_period('M')
#             monthly_income = df_monthly.groupby('mes')['monto_ars'].sum().reset_index()
#             monthly_income['mes'] = monthly_income['mes'].astype(str)
            
#             fig_monthly = px.bar(monthly_income, x='mes', y='monto_ars', title="Ingresos Mensuales")
#             st.plotly_chart(fig_monthly, use_container_width=True)
        
#         with col2:
#             st.subheader("🥧 Tratamientos")
#             tratamientos = data_manager.consultas['tratamiento'].value_counts()
#             fig_pie = px.pie(values=tratamientos.values, names=tratamientos.index)
#             st.plotly_chart(fig_pie, use_container_width=True)
#     else:
#         st.info("No hay consultas registradas aún.")

# def show_calculadora_inteligente(data_manager):
#     """Calculadora inteligente con análisis de costos automático"""
#     st.title("🧮 Calculadora Inteligente de Precios")
    
#     # Análisis de costos disponibles
#     costos_analysis = data_manager.calcular_costo_hora_real()
#     tiene_costos_configurados = costos_analysis['costo_total_anual'] > 0
    
#     if tiene_costos_configurados:
#         st.success(f"✅ Usando su costo real calculado: ${costos_analysis['costo_hora_ars']:,.0f} ARS/hora")
#     else:
#         st.warning("⚠️ Configure equipos y gastos fijos para cálculos más precisos")
    
#     # Formulario principal
#     with st.form("calculadora_inteligente"):
#         col1, col2 = st.columns([2, 1])
        
#         with col1:
#             st.subheader("📋 Parámetros del Tratamiento")
            
#             # Selección de tratamiento con opción personalizada
#             lista_tratamientos = [
#                 "Consulta", "Limpieza", "Operatoria Simple", "Operatoria Compleja", 
#                 "Endodoncia", "Corona", "Extracción Simple", "Extracción Compleja", "Otro"
#             ]
            
#             tratamiento_base = st.selectbox("Tipo de Tratamiento", lista_tratamientos)
            
#             if tratamiento_base == "Otro":
#                 tratamiento_seleccionado = st.text_input(
#                     "Especificar tratamiento:",
#                     placeholder="Ej: Blanqueamiento, Implante, etc."
#                 )
#                 if not tratamiento_seleccionado:
#                     tratamiento_seleccionado = "Personalizado"
#             else:
#                 tratamiento_seleccionado = tratamiento_base
            
#             # Tiempos estimados por tratamiento
#             tiempos_estandar = {
#                 "Consulta": 0.5,
#                 "Limpieza": 1.0,
#                 "Operatoria Simple": 1.5,
#                 "Operatoria Compleja": 2.5,
#                 "Endodoncia": 3.0,
#                 "Corona": 2.0,
#                 "Extracción Simple": 0.75,
#                 "Extracción Compleja": 2.0,
#                 "Personalizado": 1.0
#             }
            
#             tiempo_sugerido = tiempos_estandar.get(tratamiento_seleccionado, 1.0)
            
#             time_hours = st.number_input(
#                 "Tiempo estimado (horas)",
#                 min_value=0.1,
#                 max_value=8.0,
#                 value=tiempo_sugerido,
#                 step=0.25,
#                 help="Tiempo que demora realizar el tratamiento"
#             )
            
#             materials_ars = st.number_input(
#                 "Costo de materiales (ARS)",
#                 min_value=0.0,
#                 value=5000.0,
#                 step=1000.0,
#                 help="Costo total de insumos para este tratamiento"
#             )
        
#         with col2:
#             st.subheader("⚙️ Configuración de Costos")
            
#             # Toggle para usar costo automático o manual
#             if tiene_costos_configurados:
#                 usar_costo_real = st.checkbox(
#                     "Usar costo real calculado",
#                     value=True,
#                     help="Basado en sus equipos y gastos fijos configurados"
#                 )
                
#                 if usar_costo_real:
#                     costo_hora_usar = costos_analysis['costo_hora_ars']
#                     st.metric("Costo/Hora Real", f"${costo_hora_usar:,.0f} ARS")
#                 else:
#                     costo_hora_usar = st.number_input(
#                         "Costo por hora manual (ARS)",
#                         min_value=5000.0,
#                         value=29000.0,
#                         step=1000.0
#                     )
#                     st.warning("Usando costo manual en lugar del calculado")
#             else:
#                 usar_costo_real = False
#                 costo_hora_usar = st.number_input(
#                     "Costo por hora (ARS)",
#                     min_value=5000.0,
#                     value=29000.0,
#                     step=1000.0,
#                     help="Configure equipos y gastos para cálculo automático"
#                 )
        
#         calcular = st.form_submit_button("🧮 Calcular Recomendaciones", type="primary")
        
#         if calcular:
#             # Cálculo base
#             costo_mano_obra = time_hours * costo_hora_usar
#             costo_total = costo_mano_obra + materials_ars
            
#             # Recomendaciones con diferentes márgenes
#             margenes = {
#                 "Supervivencia (25%)": 0.25,
#                 "Competitivo (50%)": 0.50,
#                 "Premium (75%)": 0.75,
#                 "Especialista (100%)": 1.00
#             }
            
#             st.markdown("---")
#             st.subheader("💰 Análisis de Costos")
            
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Mano de Obra", f"${costo_mano_obra:,.0f} ARS")
#             with col2:
#                 st.metric("Materiales", f"${materials_ars:,.0f} ARS")
#             with col3:
#                 st.metric("Costo Total", f"${costo_total:,.0f} ARS")
            
#             st.subheader("📊 Recomendaciones de Precios")
            
#             recomendaciones = []
#             for nombre_margen, porcentaje_margen in margenes.items():
#                 precio_final = costo_total * (1 + porcentaje_margen)
#                 ganancia = precio_final - costo_total
                
#                 recomendaciones.append({
#                     "Margen": nombre_margen,
#                     "Precio": f"${precio_final:,.0f} ARS",
#                     "Ganancia": f"${ganancia:,.0f} ARS",
#                     "Valor": precio_final
#                 })
            
#             # Mostrar recomendaciones en columnas
#             col1, col2 = st.columns(2)
            
#             for i, rec in enumerate(recomendaciones):
#                 col = col1 if i % 2 == 0 else col2
                
#                 with col:
#                     # Color según el margen
#                     if "Supervivencia" in rec["Margen"]:
#                         color = "🟡"
#                     elif "Competitivo" in rec["Margen"]:
#                         color = "🟢"
#                     elif "Premium" in rec["Margen"]:
#                         color = "🔵"
#                     else:  # Especialista
#                         color = "🟣"
                    
#                     recomendado = "← RECOMENDADO" if "Competitivo" in rec["Margen"] else ""
                    
#                     st.markdown(f"""
#                     **{color} {rec["Margen"]} {recomendado}**
#                     - Precio: {rec["Precio"]}
#                     - Ganancia: {rec["Ganancia"]}
#                     """)
            
#             # Búsqueda en registros históricos
#             st.subheader("📋 Histórico de Este Tratamiento")
            
#             if not data_manager.consultas.empty:
#                 # Buscar tratamientos exactos o similares
#                 tratamientos_exactos = data_manager.consultas[
#                     data_manager.consultas['tratamiento'].str.lower() == tratamiento_seleccionado.lower()
#                 ]
                
#                 if not tratamientos_exactos.empty:
#                     st.markdown("**Registros anteriores encontrados:**")
                    
#                     # Mostrar últimos 5 registros
#                     ultimos_registros = tratamientos_exactos.tail(5).sort_values('fecha', ascending=False)
                    
#                     for _, registro in ultimos_registros.iterrows():
#                         fecha_registro = pd.to_datetime(registro['fecha']).strftime('%d/%m/%Y')
                        
#                         col1, col2, col3 = st.columns([2, 2, 2])
#                         with col1:
#                             st.write(f"**{registro['paciente']}**")
#                         with col2:
#                             st.write(f"${registro['monto_ars']:,.0f} ARS")
#                         with col3:
#                             st.write(fecha_registro)
                    
#                     # Estadísticas del histórico
#                     precio_promedio = tratamientos_exactos['monto_ars'].mean()
#                     precio_ultimo = tratamientos_exactos.iloc[-1]['monto_ars']
                    
#                     st.markdown("---")
#                     col1, col2, col3 = st.columns(3)
                    
#                     with col1:
#                         st.metric("Precio Promedio Histórico", f"${precio_promedio:,.0f} ARS")
#                     with col2:
#                         st.metric("Último Precio Cobrado", f"${precio_ultimo:,.0f} ARS")
#                     with col3:
#                         total_realizados = len(tratamientos_exactos)
#                         st.metric("Veces Realizadas", total_realizados)
                    
#                     # Comparación con recomendaciones actuales
#                     precio_competitivo = costo_total * 1.5
                    
#                     if precio_ultimo < costo_total:
#                         st.error(f"⚠️ Su último precio (${precio_ultimo:,.0f}) estaba por debajo del costo actual")
#                     elif precio_ultimo < precio_competitivo:
#                         diferencia = precio_competitivo - precio_ultimo
#                         st.warning(f"💡 Puede aumentar ${diferencia:,.0f} respecto al último precio cobrado")
#                     else:
#                         st.success("✅ Su último precio estaba bien posicionado")
                        
#                 else:
#                     st.info(f"No se encontraron registros anteriores de '{tratamiento_seleccionado}'")
#                     st.info("Una vez que registre este tratamiento, aparecerá en el histórico para futuras consultas")
#             else:
#                 st.info("No hay consultas registradas aún para mostrar histórico")

# def show_nueva_consulta(data_manager):
#     st.subheader("➕ Registrar Nueva Consulta")
    
#     with st.form("nueva_consulta"):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             paciente = st.text_input("Nombre del Paciente *", placeholder="Ej: Juan Pérez")
#             tratamiento = st.selectbox("Tipo de Tratamiento *", 
#                 ["Consulta", "Limpieza", "Operatoria Simple", "Endodoncia", "Otro"])
        
#         with col2:
#             monto_ars = st.number_input("Monto en ARS *", min_value=0.0, step=1000.0, value=30000.0)
#             medio_pago = st.selectbox("Medio de Pago *", 
#                 ["Efectivo", "Transferencia", "Débito", "Crédito", "Otros"])
        
#         submitted = st.form_submit_button("✅ Registrar Consulta", type="primary")
        
#         if submitted:
#             if paciente and tratamiento and monto_ars > 0:
#                 try:
#                     data_manager.add_consulta(paciente, tratamiento, monto_ars, medio_pago)
#                     st.success(f"✅ Consulta registrada: {paciente} - ${monto_ars:,.0f} ARS")
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"❌ Error: {e}")
#             else:
#                 st.error("❌ Complete todos los campos obligatorios")

# def show_login():
#     st.title("🏥 Manny App - Sistema de Gestión de Consultorios")
    
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         with st.form("login_form"):
#             st.write("🔐 Ingresar al Sistema")
            
#             username = st.text_input("Usuario", placeholder="Ingrese su usuario")
#             password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            
#             show_demo = st.checkbox("Mostrar credenciales de prueba")
#             if show_demo:
#                 st.info("**Usuario:** admin | **Contraseña:** Homero123")
            
#             login_button = st.form_submit_button("🚀 Ingresar", use_container_width=True)
            
#             if login_button:
#                 if username and password:
#                     user_manager = UserManager()
#                     is_valid, message = user_manager.validate_user(username, password)
                    
#                     if is_valid:
#                         st.session_state.authenticated = True
#                         st.session_state.user_id = username
#                         st.session_state.user_info = user_manager.get_user_info(username)
#                         st.success(f"✅ {message}")
#                         st.rerun()
#                     else:
#                         st.error(f"❌ {message}")
#                 else:
#                     st.warning("⚠️ Complete todos los campos")

# def main():
#     if 'authenticated' not in st.session_state or not st.session_state.authenticated:
#         show_login()
#         return
    
#     user_id = st.session_state.user_id
#     user_info = st.session_state.user_info
    
#     # Header
#     col1, col2, col3 = st.columns([3, 1, 1])
    
#     with col1:
#         especialidad = user_info.get('especialidad', 'odontologia')
#         especialidad_emoji = {'odontologia': '🦷', 'dermatologia': '🧴', 'kinesiologia': '🏃‍♂️'}.get(especialidad, '🏥')
#         st.markdown(f'<h1 class="main-header">Manny App - {especialidad.title()} {especialidad_emoji}</h1>', unsafe_allow_html=True)
    
#     with col2:
#         st.write(f"👤 {user_info.get('nombre', user_id)}")
    
#     with col3:
#         if st.button("🚪 Cerrar Sesión"):
#             for key in list(st.session_state.keys()):
#                 del st.session_state[key]
#             st.rerun()
    
#     # DataManager
#     if 'data_manager' not in st.session_state:
#         st.session_state.data_manager = DataManager(user_id=user_id)
    
#     data_manager = st.session_state.data_manager
    
#     # Sidebar
#     with st.sidebar:
#         st.markdown(f"""
#         <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%); border-radius: 0.5rem; margin-bottom: 1rem; color: white;'>
#         <h3>🏥 Manny App</h3>
#         <p style='margin: 0; font-size: 0.9em;'>{especialidad.title()}</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         menu = st.selectbox("📋 Menú Principal", 
#                            ["🏠 Dashboard", "➕ Nueva Consulta", "🧮 Calculadora Inteligente", "💰 Análisis de Costos", "⚙️ Configuración Costos"])
        
#         st.markdown("---")
#         resumen = data_manager.get_resumen()
#         st.metric("💰 Ingresos", f"${resumen['ingreso_total']:,.0f} ARS")
#         st.metric("📊 Consultas", resumen['total_consultas'])
        
#         # Mostrar costo por hora si está configurado
#         costos_analysis = data_manager.calcular_costo_hora_real()
#         if costos_analysis['costo_total_anual'] > 0:
#             st.markdown("---")
#             st.metric("🔧 Costo/Hora Real", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
#     # Router de páginas
#     if menu == "🏠 Dashboard":
#         show_dashboard(data_manager, user_info)
#     elif menu == "➕ Nueva Consulta":
#         show_nueva_consulta(data_manager)
#     elif menu == "🧮 Calculadora Inteligente":
#         show_calculadora_inteligente(data_manager)
#     elif menu == "💰 Análisis de Costos":
#         show_analisis_costos(data_manager, user_info)
#     elif menu == "⚙️ Configuración Costos":
#         show_configuracion_costos(data_manager)

# if __name__ == "__main__":
#     main()

# # #V3.0 lite
# # 1 - imports
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime, date
# import json
# import os
# import re
# import hashlib
# from typing import Dict, List, Tuple
# import numpy as np

# # 2 - Configuración de la página
# st.set_page_config(
#     page_title="Manny App - Sistema de Gestión de Consultorios de Salud",
#     page_icon="🏥",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # 3 - CSS personalizado
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         color: #1e3a8a;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
#     .metric-card {
#         background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
#         padding: 1rem;
#         border-radius: 0.5rem;
#         color: white;
#         text-align: center;
#         margin: 0.5rem 0;
#     }
#     .cost-analysis-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 1.5rem;
#         border-radius: 1rem;
#         color: white;
#         margin: 1rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # 4 - UserManager
# class UserManager:
#     def __init__(self):
#         self.users_file = "usuarios.json"
#         self.data_folder = "data"
#         self.init_system()
    
#     def init_system(self):
#         if not os.path.exists(self.data_folder):
#             os.makedirs(self.data_folder)
        
#         if not os.path.exists(self.users_file):
#             usuarios_default = {
#                 "admin": {
#                     "password_hash": self.hash_password("Homero123"),
#                     "nombre": "Dr. Administrador",
#                     "email": "admin@manny.com",
#                     "especialidad": "odontologia",
#                     "plan": "premium",
#                     "fecha_registro": datetime.now().isoformat()
#                 }
#             }
#             self.save_users(usuarios_default)
#             for user_id in usuarios_default.keys():
#                 self.create_user_folder(user_id)
    
#     def hash_password(self, password):
#         return hashlib.sha256(password.encode()).hexdigest()
    
#     def load_users(self):
#         try:
#             with open(self.users_file, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         except:
#             return {}
    
#     def save_users(self, users_data):
#         with open(self.users_file, 'w', encoding='utf-8') as f:
#             json.dump(users_data, f, ensure_ascii=False, indent=2)
    
#     def validate_user(self, username, password):
#         users = self.load_users()
#         if username not in users:
#             return False, "Usuario no encontrado"
#         password_hash = self.hash_password(password)
#         if users[username]["password_hash"] != password_hash:
#             return False, "Contraseña incorrecta"
#         return True, "Login exitoso"
    
#     def get_user_info(self, username):
#         users = self.load_users()
#         return users.get(username, {})
    
#     def create_user_folder(self, user_id):
#         user_folder = os.path.join(self.data_folder, user_id)
#         if not os.path.exists(user_folder):
#             os.makedirs(user_folder)
#             initial_data = {
#                 'consultas': [],
#                 'config': {
#                     'costo_por_hora': 29000,
#                     'margen_ganancia': 0.40,
#                     'tipo_cambio_usd_ars': 1335.0,
#                     'horas_anuales_trabajadas': 1100
#                 },
#                 'equipos': [],
#                 'gastos_fijos': []
#             }
#             data_file = os.path.join(user_folder, 'dental_data.json')
#             with open(data_file, 'w', encoding='utf-8') as f:
#                 json.dump(initial_data, f, ensure_ascii=False, indent=2, default=str)

# # 5 - DataManager expandido con análisis de costos
# class DataManager:
#     def __init__(self, user_id=None):
#         if user_id:
#             self.data_file = os.path.join("data", user_id, "dental_data.json")
#         else:
#             self.data_file = "dental_data.json"
#         self.user_id = user_id
#         self.load_data()

#     def update_equipo(self, equipo_id, nombre, monto_usd, años_vida_util, fecha_compra, observaciones):
#         for i, equipo in enumerate(self.equipos):
#             if equipo['id'] == equipo_id:
#                 self.equipos[i].update({
#                     'nombre': nombre,
#                     'monto_compra_usd': float(monto_usd),
#                     'años_vida_util': int(años_vida_util),
#                     'fecha_compra': fecha_compra.isoformat() if isinstance(fecha_compra, date) else fecha_compra,
#                     'observaciones': observaciones
#                 })
#                 break
#         self.save_data()

#     def update_gasto_fijo(self, gasto_id, concepto, monto_mensual_ars):
#         for i, gasto in enumerate(self.gastos_fijos):
#             if gasto['id'] == gasto_id:
#                 self.gastos_fijos[i].update({
#                     'concepto': concepto,
#                     'monto_mensual_ars': float(monto_mensual_ars)
#                 })
#                 break
#         self.save_data()
    
#     def load_data(self):
#         if os.path.exists(self.data_file):
#             try:
#                 with open(self.data_file, 'r', encoding='utf-8') as f:
#                     data = json.load(f)
#                     self.consultas = pd.DataFrame(data.get('consultas', []))
#                     self.config = data.get('config', self.get_default_config())
#                     self.equipos = data.get('equipos', [])
#                     self.gastos_fijos = data.get('gastos_fijos', [])
#             except Exception as e:
#                 st.error(f"Error cargando datos: {e}")
#                 self.init_default_data()
#         else:
#             self.init_default_data()
    
#     def init_default_data(self):
#         self.consultas = pd.DataFrame(columns=['fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago'])
#         self.config = self.get_default_config()
#         self.equipos = []
#         self.gastos_fijos = []
    
#     def get_default_config(self):
#         return {
#             'costo_por_hora': 29000,
#             'margen_ganancia': 0.40,
#             'tipo_cambio_usd_ars': 1335.0,
#             'horas_anuales_trabajadas': 1100
#         }
    
#     def save_data(self):
#         try:
#             os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
#             data = {
#                 'consultas': self.consultas.to_dict('records'),
#                 'config': self.config,
#                 'equipos': self.equipos,
#                 'gastos_fijos': self.gastos_fijos
#             }
#             with open(self.data_file, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, ensure_ascii=False, indent=2, default=str)
#             return True
#         except Exception as e:
#             st.error(f"Error guardando datos: {e}")
#             return False
    
#     def add_consulta(self, paciente, tratamiento, monto_ars, medio_pago):
#         nueva_consulta = {
#             'fecha': datetime.now().isoformat(),
#             'paciente': paciente,
#             'tratamiento': tratamiento,
#             'monto_ars': monto_ars,
#             'medio_pago': medio_pago
#         }
#         if self.consultas.empty:
#             self.consultas = pd.DataFrame([nueva_consulta])
#         else:
#             self.consultas = pd.concat([self.consultas, pd.DataFrame([nueva_consulta])], ignore_index=True)
#         self.save_data()
#         return nueva_consulta
    
#     def add_equipo(self, nombre, monto_usd, años_vida_util, fecha_compra, observaciones=""):
#         nuevo_equipo = {
#             'id': len(self.equipos) + 1,
#             'nombre': nombre,
#             'monto_compra_usd': float(monto_usd),
#             'años_vida_util': int(años_vida_util),
#             'fecha_compra': fecha_compra.isoformat() if isinstance(fecha_compra, date) else fecha_compra,
#             'observaciones': observaciones,
#             'activo': True,
#             'fecha_creacion': datetime.now().isoformat()
#         }
#         self.equipos.append(nuevo_equipo)
#         self.save_data()
#         return nuevo_equipo
    
#     def add_gasto_fijo(self, concepto, monto_mensual_ars):
#         nuevo_gasto = {
#             'id': len(self.gastos_fijos) + 1,
#             'concepto': concepto,
#             'monto_mensual_ars': float(monto_mensual_ars),
#             'activo': True,
#             'fecha_creacion': datetime.now().isoformat()
#         }
#         self.gastos_fijos.append(nuevo_gasto)
#         self.save_data()
#         return nuevo_gasto
    
#     def delete_equipo(self, equipo_id):
#         """Eliminar equipo por ID"""
#         self.equipos = [e for e in self.equipos if e.get('id') != equipo_id]
#         self.save_data()
#         return True
    
#     def delete_gasto_fijo(self, gasto_id):
#         """Eliminar gasto fijo por ID"""
#         self.gastos_fijos = [g for g in self.gastos_fijos if g.get('id') != gasto_id]
#         self.save_data()
#         return True
    
#     def calcular_costo_hora_real(self):
#         """Cálculo integral del costo por hora basado en equipos y gastos fijos"""
        
#         # 1. Costos de equipos (amortización con inflación 4% anual)
#         costo_equipos_anual_usd = 0
#         for equipo in self.equipos:
#             if equipo.get('activo', True):
#                 # Amortización con inflación
#                 costo_reposicion = equipo['monto_compra_usd'] * (1.04 ** equipo['años_vida_util'])
#                 amortizacion_anual = costo_reposicion / equipo['años_vida_util']
#                 costo_equipos_anual_usd += amortizacion_anual
        
#         # Convertir USD a ARS
#         tipo_cambio = self.config.get('tipo_cambio_usd_ars', 1335)
#         costo_equipos_anual_ars = costo_equipos_anual_usd * tipo_cambio
        
#         # 2. Gastos fijos anuales (ARS)
#         costo_gastos_anual_ars = sum([
#             gasto['monto_mensual_ars'] * 12 
#             for gasto in self.gastos_fijos 
#             if gasto.get('activo', True)
#         ])
        
#         # 3. Cálculo final
#         costo_total_anual = costo_equipos_anual_ars + costo_gastos_anual_ars
#         horas_anuales = self.config.get('horas_anuales_trabajadas', 1100)
        
#         costo_hora = costo_total_anual / horas_anuales if horas_anuales > 0 else 0
        
#         return {
#             'costo_hora_ars': costo_hora,
#             'costo_equipos_anual': costo_equipos_anual_ars,
#             'costo_gastos_anual': costo_gastos_anual_ars,
#             'costo_total_anual': costo_total_anual,
#             'horas_anuales': horas_anuales,
#             'cantidad_equipos': len([e for e in self.equipos if e.get('activo', True)]),
#             'cantidad_gastos': len([g for g in self.gastos_fijos if g.get('activo', True)])
#         }
    
#     def get_resumen(self):
#         if self.consultas.empty:
#             return {
#                 'total_consultas': 0,
#                 'ingreso_total': 0,
#                 'promedio_consulta': 0,
#                 'tratamiento_popular': 'N/A',
#                 'ingresos_mes': 0
#             }
        
#         if not self.consultas.empty:
#             self.consultas['fecha'] = pd.to_datetime(self.consultas['fecha'])
        
#         total_consultas = len(self.consultas)
#         ingreso_total = self.consultas['monto_ars'].sum()
#         promedio_consulta = ingreso_total / total_consultas if total_consultas > 0 else 0
        
#         tratamiento_popular = 'N/A'
#         if not self.consultas.empty:
#             tratamientos = self.consultas['tratamiento'].value_counts()
#             if not tratamientos.empty:
#                 tratamiento_popular = tratamientos.index[0]
        
#         fecha_actual = datetime.now()
#         mes_actual = self.consultas[
#             (self.consultas['fecha'].dt.month == fecha_actual.month) &
#             (self.consultas['fecha'].dt.year == fecha_actual.year)
#         ]
#         ingresos_mes = mes_actual['monto_ars'].sum() if not mes_actual.empty else 0
        
#         return {
#             'total_consultas': total_consultas,
#             'ingreso_total': round(ingreso_total, 0),
#             'promedio_consulta': round(promedio_consulta, 0),
#             'tratamiento_popular': tratamiento_popular,
#             'ingresos_mes': round(ingresos_mes, 0)
#         }

# # 6 - Funciones de análisis de costos
# def show_configuracion_costos(data_manager):
#     """Página de configuración de costos"""
#     st.title("⚙️ Configuración de Costos")
    
#     tab1, tab2, tab3 = st.tabs(["🔧 Equipos", "🏢 Gastos Fijos", "⚙️ Parámetros"])
    
#     with tab1:
#         st.subheader("🔧 Equipamiento del Consultorio")
        
#         # Mostrar equipos actuales con botones de eliminar
#         if data_manager.equipos:
#             st.markdown("**Equipos registrados:**")
            
#             for equipo in data_manager.equipos:
#                 col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
                
#                 with col1:
#                     st.write(f"**{equipo['nombre']}**")
#                 with col2:
#                     st.write(f"${equipo['monto_compra_usd']:,.0f} USD")
#                 with col3:
#                     st.write(f"{equipo['años_vida_util']} años")
#                 with col4:
#                     fecha_compra = pd.to_datetime(equipo['fecha_compra']).strftime('%d/%m/%Y')
#                     st.write(fecha_compra)
#                 with col5:
#                     if st.button("✏️", key=f"edit_equipo_{equipo['id']}", help="Editar equipo"):
#                         st.session_state[f'editing_equipo_{equipo["id"]}'] = True
#                         st.rerun()
#                 with col6:
#                     if st.button("🗑️", key=f"del_equipo_{equipo['id']}", help="Eliminar equipo"):
#                         data_manager.delete_equipo(equipo['id'])
#                         st.success("Equipo eliminado")
#                         st.rerun()
#         else:
#             st.info("No hay equipos registrados aún.")
        
#         # Formulario para nuevo equipo
#         with st.form("nuevo_equipo"):
#             st.markdown("**Agregar Nuevo Equipo**")
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 nombre_equipo = st.text_input("Nombre del Equipo *", placeholder="Ej: Sillón Dental")
#                 monto_usd = st.number_input("Precio pagado (USD) *", min_value=0.0, step=100.0, value=1000.0)
            
#             with col2:
#                 años_vida = st.selectbox("Vida Útil (años)", [3, 5, 7, 8, 10], index=1)
#                 fecha_compra = st.date_input("Fecha de Compra", value=date.today())
            
#             observaciones = st.text_area("Observaciones (opcional)")
            
#             if st.form_submit_button("💾 Agregar Equipo", type="primary"):
#                 if nombre_equipo and monto_usd > 0:
#                     data_manager.add_equipo(nombre_equipo, monto_usd, años_vida, fecha_compra, observaciones)
#                     st.success("✅ Equipo agregado correctamente")
#                     # Limpiar session_state de los campos del formulario
#                     st.rerun()
#                 else:
#                     st.error("❌ Complete los campos obligatorios")
    
#     with tab2:
#         st.subheader("🏢 Gastos Fijos Mensuales")
        
#         # Mostrar gastos actuales con botones de eliminar
#         if data_manager.gastos_fijos:
#             st.markdown("**Gastos fijos registrados:**")
            
#             for gasto in data_manager.gastos_fijos:
#                 col1, col2, col3 = st.columns([4, 3, 1])
                
#                 with col1:
#                     st.write(f"**{gasto['concepto']}**")
#                 with col2:
#                     st.write(f"${gasto['monto_mensual_ars']:,.0f} ARS/mes")
#                 with col3:
#                     if st.button("🗑️", key=f"del_gasto_{gasto['id']}", help="Eliminar gasto"):
#                         data_manager.delete_gasto_fijo(gasto['id'])
#                         st.success("Gasto eliminado")
#                         st.rerun()
            
#             st.markdown("---")
#             total_mensual = sum([g['monto_mensual_ars'] for g in data_manager.gastos_fijos if g.get('activo', True)])
#             st.metric("💰 Total Gastos Fijos", f"${total_mensual:,.0f} ARS/mes")
#         else:
#             st.info("No hay gastos fijos registrados aún.")
        
#         # Formulario para nuevo gasto
#         with st.form("nuevo_gasto"):
#             st.markdown("**Agregar Nuevo Gasto Fijo**")
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 concepto = st.text_input("Concepto *", placeholder="Ej: Alquiler")
#             with col2:
#                 monto_mensual = st.number_input("Monto mensual (ARS) *", min_value=0.0, step=1000.0, value=50000.0)
            
#             if st.form_submit_button("💾 Agregar Gasto", type="primary"):
#                 if concepto and monto_mensual > 0:
#                     data_manager.add_gasto_fijo(concepto, monto_mensual)
#                     st.success("✅ Gasto agregado correctamente")
#                     # Limpiar session_state de los campos del formulario
#                     for key in st.session_state.keys():
#                         if key.startswith('FormSubmitter:nuevo_gasto'):
#                             del st.session_state[key]
#                     st.rerun()
#                 else:
#                     st.error("❌ Complete los campos obligatorios")
    
#     with tab3:
#         st.subheader("⚙️ Parámetros de Trabajo")
        
#         with st.form("parametros"):
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 nuevas_horas = st.number_input(
#                     "Horas anuales trabajadas",
#                     min_value=500,
#                     max_value=2000,
#                     value=data_manager.config.get('horas_anuales_trabajadas', 1100),
#                     step=50,
#                     help="Horas productivas anuales (descontando vacaciones, días no trabajados, etc.)"
#                 )
                
#                 nuevo_margen = st.slider(
#                     "Margen de ganancia objetivo (%)",
#                     min_value=10,
#                     max_value=200,
#                     value=int(data_manager.config.get('margen_ganancia', 0.4) * 100),
#                     step=5
#                 ) / 100
            
#             with col2:
#                 nuevo_tc = st.number_input(
#                     "Tipo de cambio USD/ARS",
#                     min_value=100.0,
#                     max_value=5000.0,
#                     value=data_manager.config.get('tipo_cambio_usd_ars', 1335.0),
#                     step=10.0,
#                     help="Para convertir equipos en USD a ARS"
#                 )
            
#             if st.form_submit_button("💾 Actualizar Parámetros", type="primary"):
#                 data_manager.config.update({
#                     'horas_anuales_trabajadas': nuevas_horas,
#                     'margen_ganancia': nuevo_margen,
#                     'tipo_cambio_usd_ars': nuevo_tc
#                 })
#                 data_manager.save_data()
#                 st.success("✅ Parámetros actualizados exitosamente")
#                 st.rerun()

# def show_analisis_costos(data_manager, user_info):
#     """Página de análisis de costos integral"""
#     st.title("💰 Análisis de Costos y Rentabilidad")
    
#     especialidad = user_info.get('especialidad', 'odontologia')
#     especialidad_emoji = {
#         'odontologia': '🦷',
#         'dermatologia': '🧴',
#         'kinesiologia': '🏃‍♂️'
#     }.get(especialidad, '🏥')
    
#     st.markdown(f"### {especialidad_emoji} {especialidad.title()}")
    
#     # Calcular métricas de costos
#     costos_analysis = data_manager.calcular_costo_hora_real()
    
#     # Verificar si tiene costos configurados
#     if costos_analysis['costo_total_anual'] == 0:
#         st.warning("⚠️ No tiene equipos ni gastos fijos configurados. Vaya a 'Configuración Costos' para comenzar.")
#         st.info("💡 El análisis de costos le permitirá conocer su costo real por hora y optimizar sus precios.")
#         return
    
#     # Métricas principales
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("💰 Costo Real/Hora", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
#     with col2:
#         precio_minimo = costos_analysis['costo_hora_ars'] * 1.5  # 50% margen
#         st.metric("📊 Precio Mín. (50%)", f"${precio_minimo:,.0f} ARS")
    
#     with col3:
#         precio_optimo = costos_analysis['costo_hora_ars'] * 2  # 100% margen
#         st.metric("🎯 Precio Óptimo (100%)", f"${precio_optimo:,.0f} ARS")
    
#     with col4:
#         resumen = data_manager.get_resumen()
#         if resumen['promedio_consulta'] > 0:
#             consultas_breakeven = costos_analysis['costo_total_anual'] / resumen['promedio_consulta']
#             st.metric("⚖️ Consultas Break-Even", f"{consultas_breakeven:,.0f} /año")
#         else:
#             st.metric("⚖️ Consultas Break-Even", "Sin datos")
    
#     # Gráfico de composición de costos
#     if costos_analysis['costo_total_anual'] > 0:
#         st.subheader("📊 Composición de Costos Anuales")
        
#         costos_data = pd.DataFrame([
#             {"Categoría": "Equipos (Amortización)", "Monto": costos_analysis['costo_equipos_anual']},
#             {"Categoría": "Gastos Fijos", "Monto": costos_analysis['costo_gastos_anual']}
#         ])
        
#         col1, col2 = st.columns([2, 1])
        
#         with col1:
#             fig_costos = px.pie(
#                 costos_data, 
#                 values='Monto', 
#                 names='Categoría',
#                 title=f"Total Anual: ${costos_analysis['costo_total_anual']:,.0f} ARS",
#                 color_discrete_sequence=['#3b82f6', '#ef4444']
#             )
#             st.plotly_chart(fig_costos, use_container_width=True)
        
#         with col2:
#             st.markdown("**📈 Resumen de Configuración**")
#             st.metric("🔧 Equipos", costos_analysis['cantidad_equipos'])
#             st.metric("🏢 Gastos Fijos", costos_analysis['cantidad_gastos'])
#             st.metric("⏰ Horas Anuales", costos_analysis['horas_anuales'])
    
#     # Análisis de rentabilidad actual
#     if resumen['total_consultas'] > 0:
#         st.subheader("📈 Análisis de Rentabilidad Actual")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.markdown("**💵 Ingresos vs Costos**")
#             ingresos_anuales = resumen['ingreso_total'] * 12  # Proyección anual
#             margen_real = ((ingresos_anuales - costos_analysis['costo_total_anual']) / ingresos_anuales * 100) if ingresos_anuales > 0 else 0
            
#             if margen_real > 50:
#                 st.success(f"✅ Margen excelente: {margen_real:.1f}%")
#             elif margen_real > 25:
#                 st.warning(f"⚠️ Margen aceptable: {margen_real:.1f}%")
#             else:
#                 st.error(f"🚨 Margen bajo: {margen_real:.1f}%")
        
#         with col2:
#             st.markdown("**⏰ Eficiencia Horaria**")
#             consultas_mes = resumen['total_consultas'] / max(1, len(data_manager.consultas['fecha'].dt.month.unique()) if not data_manager.consultas.empty else 1)
#             eficiencia = (consultas_mes * 12) / costos_analysis['horas_anuales'] if costos_analysis['horas_anuales'] > 0 else 0
            
#             st.metric("Consultas por Hora Disponible", f"{eficiencia:.2f}")

# # 7 - Funciones de interfaz (actualizadas)
# def show_dashboard(data_manager, user_info):
#     especialidad = user_info.get('especialidad', 'odontologia')
#     especialidad_emoji = {
#         'odontologia': '🦷',
#         'dermatologia': '🧴', 
#         'kinesiologia': '🏃‍♂️'
#     }.get(especialidad, '🏥')
    
#     st.subheader(f"📊 Dashboard - {user_info.get('nombre', 'Usuario')} {especialidad_emoji}")
    
#     # Análisis de costos en el dashboard
#     costos_analysis = data_manager.calcular_costo_hora_real()
    
#     # Mostrar alerta si tiene costos configurados
#     if costos_analysis['costo_total_anual'] > 0:
#         st.markdown(f"""
#         <div class="cost-analysis-card">
#             <h3>💰 Análisis de Costos Automático</h3>
#             <p>Su costo real por hora: <strong>${costos_analysis['costo_hora_ars']:,.0f} ARS</strong></p>
#             <p>Precio mínimo recomendado (50% margen): <strong>${costos_analysis['costo_hora_ars'] * 1.5:,.0f} ARS</strong></p>
#         </div>
#         """, unsafe_allow_html=True)
#     else:
#         st.info("💡 Configure sus equipos y gastos fijos para obtener análisis de costos automático.")
    
#     # Dashboard original
#     resumen = data_manager.get_resumen()
    
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("💰 Ingresos Totales", f"${resumen['ingreso_total']:,.0f} ARS")
    
#     with col2:
#         st.metric("👥 Total Consultas", resumen['total_consultas'])
    
#     with col3:
#         st.metric("📊 Promedio/Consulta", f"${resumen['promedio_consulta']:,.0f} ARS")
    
#     with col4:
#         st.metric("🔥 Más Popular", resumen['tratamiento_popular'])
    
#     if not data_manager.consultas.empty:
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.subheader("📈 Ingresos por Mes")
#             df_monthly = data_manager.consultas.copy()
#             df_monthly['fecha'] = pd.to_datetime(df_monthly['fecha'])
#             df_monthly['mes'] = df_monthly['fecha'].dt.to_period('M')
#             monthly_income = df_monthly.groupby('mes')['monto_ars'].sum().reset_index()
#             monthly_income['mes'] = monthly_income['mes'].astype(str)
            
#             fig_monthly = px.bar(monthly_income, x='mes', y='monto_ars', title="Ingresos Mensuales")
#             st.plotly_chart(fig_monthly, use_container_width=True)
        
#         with col2:
#             st.subheader("🥧 Tratamientos")
#             tratamientos = data_manager.consultas['tratamiento'].value_counts()
#             fig_pie = px.pie(values=tratamientos.values, names=tratamientos.index)
#             st.plotly_chart(fig_pie, use_container_width=True)
#     else:
#         st.info("No hay consultas registradas aún.")

# def show_nueva_consulta(data_manager):
#     st.subheader("➕ Registrar Nueva Consulta")
    
#     with st.form("nueva_consulta"):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             paciente = st.text_input("Nombre del Paciente *", placeholder="Ej: Juan Pérez")
#             tratamiento = st.selectbox("Tipo de Tratamiento *", 
#                 ["Consulta", "Limpieza", "Operatoria Simple", "Endodoncia", "Otro"])
        
#         with col2:
#             monto_ars = st.number_input("Monto en ARS *", min_value=0.0, step=1000.0, value=30000.0)
#             medio_pago = st.selectbox("Medio de Pago *", 
#                 ["Efectivo", "Transferencia", "Débito", "Crédito", "Otros"])
        
#         submitted = st.form_submit_button("✅ Registrar Consulta", type="primary")
        
#         if submitted:
#             if paciente and tratamiento and monto_ars > 0:
#                 try:
#                     data_manager.add_consulta(paciente, tratamiento, monto_ars, medio_pago)
#                     st.success(f"✅ Consulta registrada: {paciente} - ${monto_ars:,.0f} ARS")
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"❌ Error: {e}")
#             else:
#                 st.error("❌ Complete todos los campos obligatorios")

# def show_login():
#     st.title("🏥 Manny App - Sistema de Gestión de Consultorios")
    
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         with st.form("login_form"):
#             st.write("🔐 Ingresar al Sistema")
            
#             username = st.text_input("Usuario", placeholder="Ingrese su usuario")
#             password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            
#             show_demo = st.checkbox("Mostrar credenciales de prueba")
#             if show_demo:
#                 st.info("**Usuario:** admin | **Contraseña:** Homero123")
            
#             login_button = st.form_submit_button("🚀 Ingresar", use_container_width=True)
            
#             if login_button:
#                 if username and password:
#                     user_manager = UserManager()
#                     is_valid, message = user_manager.validate_user(username, password)
                    
#                     if is_valid:
#                         st.session_state.authenticated = True
#                         st.session_state.user_id = username
#                         st.session_state.user_info = user_manager.get_user_info(username)
#                         st.success(f"✅ {message}")
#                         st.rerun()
#                     else:
#                         st.error(f"❌ {message}")
#                 else:
#                     st.warning("⚠️ Complete todos los campos")

# def main():
#     if 'authenticated' not in st.session_state or not st.session_state.authenticated:
#         show_login()
#         return
    
#     user_id = st.session_state.user_id
#     user_info = st.session_state.user_info
    
#     # Header
#     col1, col2, col3 = st.columns([3, 1, 1])
    
#     with col1:
#         especialidad = user_info.get('especialidad', 'odontologia')
#         especialidad_emoji = {'odontologia': '🦷', 'dermatologia': '🧴', 'kinesiologia': '🏃‍♂️'}.get(especialidad, '🏥')
#         st.markdown(f'<h1 class="main-header">Manny App - {especialidad.title()} {especialidad_emoji}</h1>', unsafe_allow_html=True)
    
#     with col2:
#         st.write(f"👤 {user_info.get('nombre', user_id)}")
    
#     with col3:
#         if st.button("🚪 Cerrar Sesión"):
#             for key in list(st.session_state.keys()):
#                 del st.session_state[key]
#             st.rerun()
    
#     # DataManager
#     if 'data_manager' not in st.session_state:
#         st.session_state.data_manager = DataManager(user_id=user_id)
    
#     data_manager = st.session_state.data_manager
    
#     # Sidebar
#     with st.sidebar:
#         st.markdown(f"""
#         <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%); border-radius: 0.5rem; margin-bottom: 1rem; color: white;'>
#         <h3>🏥 Manny App</h3>
#         <p style='margin: 0; font-size: 0.9em;'>{especialidad.title()}</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         menu = st.selectbox("📋 Menú Principal", 
#                            ["🏠 Dashboard", "➕ Nueva Consulta", "💰 Análisis de Costos", "⚙️ Configuración Costos"])
        
#         st.markdown("---")
#         resumen = data_manager.get_resumen()
#         st.metric("💰 Ingresos", f"${resumen['ingreso_total']:,.0f} ARS")
#         st.metric("📊 Consultas", resumen['total_consultas'])
        
#         # Mostrar costo por hora si está configurado
#         costos_analysis = data_manager.calcular_costo_hora_real()
#         if costos_analysis['costo_total_anual'] > 0:
#             st.markdown("---")
#             st.metric("🔧 Costo/Hora Real", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
#     # Router de páginas
#     if menu == "🏠 Dashboard":
#         show_dashboard(data_manager, user_info)
#     elif menu == "➕ Nueva Consulta":
#         show_nueva_consulta(data_manager)
#     elif menu == "💰 Análisis de Costos":
#         show_analisis_costos(data_manager, user_info)
#     elif menu == "⚙️ Configuración Costos":
#         show_configuracion_costos(data_manager)

# if __name__ == "__main__":
#     main()

# V3.0
# # 1 - imports
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime, date
# import json
# import os
# import re
# import hashlib
# from typing import Dict, List, Tuple
# import numpy as np

# # 2 - Configuración de la página
# st.set_page_config(
#     page_title="Manny App - Sistema de Gestión de Consultorios de Salud",
#     page_icon="🏥",  # Icono más universal para salud
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # 3 - CSS personalizado
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         color: #1e3a8a;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
#     .metric-card {
#         background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
#         padding: 1rem;
#         border-radius: 0.5rem;
#         color: white;
#         text-align: center;
#         margin: 0.5rem 0;
#     }
#     .alert-success {
#         background-color: #dcfce7;
#         border: 1px solid #16a34a;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin: 1rem 0;
#     }
#     .alert-warning {
#         background-color: #fef3c7;
#         border: 1px solid #d97706;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin: 1rem 0;
#     }
#     .alert-error {
#         background-color: #fee2e2;
#         border: 1px solid #dc2626;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin: 1rem 0;
#     }
#     .cost-analysis-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 1.5rem;
#         border-radius: 1rem;
#         color: white;
#         margin: 1rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # 4 - UserManager (Mantener igual)
# class UserManager:
#     """Maneja autenticación y usuarios del sistema"""
    
#     def __init__(self):
#         self.users_file = "usuarios.json"
#         self.data_folder = "data"
#         self.init_system()
    
#     def init_system(self):
#         """Inicializa el sistema creando archivos necesarios"""
#         if not os.path.exists(self.data_folder):
#             os.makedirs(self.data_folder)
        
#         if not os.path.exists(self.users_file):
#             usuarios_default = {
#                 "admin": {
#                     "password_hash": self.hash_password("Homero123"),
#                     "nombre": "Dr. Administrador",
#                     "email": "admin@manny.com",
#                     "especialidad": "odontologia",
#                     "plan": "premium",
#                     "fecha_registro": datetime.now().isoformat()
#                 },
#                 "demo1": {
#                     "password_hash": self.hash_password("Homero123"),
#                     "nombre": "Dr. Demo Uno",
#                     "email": "demo1@manny.com",
#                     "especialidad": "odontologia",
#                     "plan": "trial",
#                     "fecha_registro": datetime.now().isoformat()
#                 },
#                 "demo2": {
#                     "password_hash": self.hash_password("Homero123"),
#                     "nombre": "Dra. Demo Dos",
#                     "email": "demo2@manny.com",
#                     "especialidad": "dermatologia",
#                     "plan": "trial",
#                     "fecha_registro": datetime.now().isoformat()
#                 }
#             }
            
#             self.save_users(usuarios_default)
            
#             for user_id in usuarios_default.keys():
#                 self.create_user_folder(user_id)
    
#     def hash_password(self, password):
#         return hashlib.sha256(password.encode()).hexdigest()
    
#     def load_users(self):
#         try:
#             with open(self.users_file, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         except:
#             return {}
    
#     def save_users(self, users_data):
#         with open(self.users_file, 'w', encoding='utf-8') as f:
#             json.dump(users_data, f, ensure_ascii=False, indent=2)
    
#     def validate_user(self, username, password):
#         users = self.load_users()
        
#         if username not in users:
#             return False, "Usuario no encontrado"
        
#         password_hash = self.hash_password(password)
        
#         if users[username]["password_hash"] != password_hash:
#             return False, "Contraseña incorrecta"
        
#         return True, "Login exitoso"
    
#     def get_user_info(self, username):
#         users = self.load_users()
#         return users.get(username, {})
    
#     def create_user_folder(self, user_id):
#         user_folder = os.path.join(self.data_folder, user_id)
        
#         if not os.path.exists(user_folder):
#             os.makedirs(user_folder)
            
#             initial_data = {
#                 'consultas': [],
#                 'config': {
#                     'costo_por_hora': 29000,
#                     'margen_ganancia': 0.40,
#                     'region': 'Interior NOA/NEA',
#                     'tipo_cambio_usd_ars': 1335.0,
#                     'horas_anuales_trabajadas': 1100
#                 },
#                 'equipos': [],
#                 'gastos_fijos': [],
#                 'insumos': []
#             }
            
#             data_file = os.path.join(user_folder, 'dental_data.json')
#             with open(data_file, 'w', encoding='utf-8') as f:
#                 json.dump(initial_data, f, ensure_ascii=False, indent=2, default=str)

# # 5 - DataManager Expandido
# class DataManager:
#     """Manejo de datos del consultorio con análisis de costos"""
    
#     def __init__(self, user_id=None):
#         if user_id:
#             self.data_file = os.path.join("data", user_id, "dental_data.json")
#         else:
#             self.data_file = "dental_data.json"
#         self.user_id = user_id
#         self.load_data()
    
#     def load_data(self):
#         if os.path.exists(self.data_file):
#             try:
#                 with open(self.data_file, 'r', encoding='utf-8') as f:
#                     data = json.load(f)
#                     self.consultas = pd.DataFrame(data.get('consultas', []))
#                     self.config = data.get('config', self.get_default_config())
#                     self.equipos = data.get('equipos', [])
#                     self.gastos_fijos = data.get('gastos_fijos', [])
#                     self.insumos = data.get('insumos', [])
#             except Exception as e:
#                 st.error(f"Error cargando datos: {e}")
#                 self.init_default_data()
#         else:
#             self.init_default_data()
    
#     def init_default_data(self):
#         self.consultas = pd.DataFrame(columns=[
#             'fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago'
#         ])
#         self.config = self.get_default_config()
#         self.equipos = []
#         self.gastos_fijos = []
#         self.insumos = []
    
#     def get_default_config(self):
#         return {
#             'costo_por_hora': 29000,
#             'margen_ganancia': 0.40,
#             'region': 'Interior NOA/NEA',
#             'tipo_cambio_usd_ars': 1335.0,
#             'horas_anuales_trabajadas': 1100,
#             'dias_trabajo_semana': 5,
#             'horas_dia_promedio': 5.5
#         }
    
#     def save_data(self):
#         try:
#             os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
#             data = {
#                 'consultas': self.consultas.to_dict('records'),
#                 'config': self.config,
#                 'equipos': self.equipos,
#                 'gastos_fijos': self.gastos_fijos,
#                 'insumos': self.insumos
#             }
#             with open(self.data_file, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, ensure_ascii=False, indent=2, default=str)
#             return True
#         except Exception as e:
#             st.error(f"Error guardando datos: {e}")
#             return False
    
#     def add_consulta(self, paciente, tratamiento, monto_ars, medio_pago):
#         nueva_consulta = {
#             'fecha': datetime.now().isoformat(),
#             'paciente': paciente,
#             'tratamiento': tratamiento,
#             'monto_ars': monto_ars,
#             'medio_pago': medio_pago
#         }
        
#         if self.consultas.empty:
#             self.consultas = pd.DataFrame([nueva_consulta])
#         else:
#             self.consultas = pd.concat([self.consultas, pd.DataFrame([nueva_consulta])], ignore_index=True)
        
#         self.save_data()
#         return nueva_consulta
    
#     def add_equipo(self, nombre, monto_usd, años_vida_util, fecha_compra, observaciones=""):
#         nuevo_equipo = {
#             'id': len(self.equipos) + 1,
#             'nombre': nombre,
#             'monto_compra_usd': float(monto_usd),
#             'años_vida_util': int(años_vida_util),
#             'fecha_compra': fecha_compra.isoformat() if isinstance(fecha_compra, date) else fecha_compra,
#             'observaciones': observaciones,
#             'activo': True,
#             'fecha_creacion': datetime.now().isoformat()
#         }
#         self.equipos.append(nuevo_equipo)
#         self.save_data()
#         return nuevo_equipo
    
#     def add_gasto_fijo(self, concepto, monto_mensual_ars):
#         nuevo_gasto = {
#             'id': len(self.gastos_fijos) + 1,
#             'concepto': concepto,
#             'monto_mensual_ars': float(monto_mensual_ars),
#             'activo': True,
#             'fecha_creacion': datetime.now().isoformat()
#         }
#         self.gastos_fijos.append(nuevo_gasto)
#         self.save_data()
#         return nuevo_gasto
    
#     def calcular_costo_hora_real(self):
#         """Cálculo integral del costo por hora"""
        
#         # 1. Costos de equipos (amortización con inflación)
#         costo_equipos_anual_usd = 0
#         for equipo in self.equipos:
#             if equipo.get('activo', True):
#                 # Amortización con 4% inflación anual
#                 costo_reposicion = equipo['monto_compra_usd'] * (1.04 ** equipo['años_vida_util'])
#                 amortizacion_anual = costo_reposicion / equipo['años_vida_util']
#                 costo_equipos_anual_usd += amortizacion_anual
        
#         # Convertir a ARS
#         tipo_cambio = self.config.get('tipo_cambio_usd_ars', 1335)
#         costo_equipos_anual_ars = costo_equipos_anual_usd * tipo_cambio
        
#         # 2. Gastos fijos anuales
#         costo_gastos_anual_ars = sum([
#             gasto['monto_mensual_ars'] * 12 
#             for gasto in self.gastos_fijos 
#             if gasto.get('activo', True)
#         ])
        
#         # 3. Total anual y por hora
#         costo_total_anual = costo_equipos_anual_ars + costo_gastos_anual_ars
#         horas_anuales = self.config.get('horas_anuales_trabajadas', 1100)
        
#         return {
#             'costo_hora_ars': costo_total_anual / horas_anuales,
#             'costo_equipos_anual': costo_equipos_anual_ars,
#             'costo_gastos_anual': costo_gastos_anual_ars,
#             'costo_total_anual': costo_total_anual,
#             'horas_anuales': horas_anuales
#         }
    
#     def get_resumen(self):
#         if self.consultas.empty:
#             return {
#                 'total_consultas': 0,
#                 'ingreso_total': 0,
#                 'promedio_consulta': 0,
#                 'tratamiento_popular': 'N/A',
#                 'ingresos_mes': 0
#             }
        
#         if not self.consultas.empty:
#             self.consultas['fecha'] = pd.to_datetime(self.consultas['fecha'])
        
#         total_consultas = len(self.consultas)
#         ingreso_total = self.consultas['monto_ars'].sum()
#         promedio_consulta = ingreso_total / total_consultas if total_consultas > 0 else 0
        
#         tratamiento_popular = 'N/A'
#         if not self.consultas.empty:
#             tratamientos = self.consultas['tratamiento'].value_counts()
#             if not tratamientos.empty:
#                 tratamiento_popular = tratamientos.index[0]
        
#         fecha_actual = datetime.now()
#         mes_actual = self.consultas[
#             (self.consultas['fecha'].dt.month == fecha_actual.month) &
#             (self.consultas['fecha'].dt.year == fecha_actual.year)
#         ]
#         ingresos_mes = mes_actual['monto_ars'].sum() if not mes_actual.empty else 0
        
#         return {
#             'total_consultas': total_consultas,
#             'ingreso_total': round(ingreso_total, 0),
#             'promedio_consulta': round(promedio_consulta, 0),
#             'tratamiento_popular': tratamiento_popular,
#             'ingresos_mes': round(ingresos_mes, 0)
#         }

# # 6 - Funciones auxiliares (mantener las existentes)
# def calculate_price_optimized(time_hours: float, materials_ars: float, cost_per_hour: float, margin: float = 0.40):
#     """Calcular precio optimizado en pesos"""
#     if time_hours <= 0 or materials_ars < 0:
#         raise ValueError("Horas debe ser > 0 y materiales >= 0")
    
#     labor_cost = time_hours * cost_per_hour
#     total_cost = labor_cost + materials_ars
#     final_price = total_cost * (1 + margin)
    
#     return {
#         'time_hours': time_hours,
#         'cost_per_hour': cost_per_hour,
#         'mano_obra': round(labor_cost, 0),
#         'materiales': materials_ars,
#         'costo_total': round(total_cost, 0),
#         'precio_final': round(final_price, 0),
#         'margen': margin * 100
#     }

# def extraer_monto_numerico(monto_str):
#     """Extrae valor numérico de string de monto"""
#     try:
#         if pd.isna(monto_str):
#             return 0
        
#         monto_clean = str(monto_str).strip()
#         monto_clean = re.sub(r'[$€£¥₹₽₩¢]', '', monto_clean)
#         monto_clean = re.sub(r'[^\d.,\-]', '', monto_clean)
        
#         if not monto_clean:
#             return 0
        
#         es_negativo = monto_clean.startswith('-')
#         monto_clean = monto_clean.lstrip('-')
        
#         if ',' in monto_clean and '.' in monto_clean:
#             if monto_clean.rfind(',') > monto_clean.rfind('.'):
#                 monto_clean = monto_clean.replace('.', '').replace(',', '.')
#             else:
#                 monto_clean = monto_clean.replace(',', '')
#         elif ',' in monto_clean:
#             if monto_clean.count(',') == 1 and len(monto_clean.split(',')[1]) <= 2:
#                 monto_clean = monto_clean.replace(',', '.')
#             else:
#                 monto_clean = monto_clean.replace(',', '')
        
#         resultado = float(monto_clean)
#         return -resultado if es_negativo else resultado
        
#     except Exception as e:
#         st.warning(f"No se pudo procesar monto '{monto_str}': {e}")
#         return 0

# def normalizar_fecha_flexible(fecha_valor):
#     """Normaliza fechas de múltiples formatos"""
#     try:
#         if pd.isna(fecha_valor):
#             return datetime.now().isoformat()
        
#         fecha_str = str(fecha_valor).strip()
        
#         formatos_fecha = [
#             '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y', '%d.%m.%Y', '%d.%m.%y',
#             '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
#             '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y_%m_%d',
#             '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d-%m-%Y %H:%M:%S', '%d-%m-%Y %H:%M',
#             '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
#             '%d de %B de %Y', '%d %B %Y', '%B %d, %Y', '%d %b %Y',
#         ]
        
#         for formato in formatos_fecha:
#             try:
#                 fecha_parsed = datetime.strptime(fecha_str, formato)
#                 return fecha_parsed.isoformat()
#             except ValueError:
#                 continue
        
#         try:
#             fecha_pandas = pd.to_datetime(fecha_str, dayfirst=True, errors='coerce')
#             if not pd.isna(fecha_pandas):
#                 return fecha_pandas.isoformat()
#         except:
#             pass
        
#         st.warning(f"No se pudo procesar fecha '{fecha_valor}', usando fecha actual")
#         return datetime.now().isoformat()
        
#     except Exception as e:
#         st.warning(f"Error procesando fecha '{fecha_valor}': {e}")
#         return datetime.now().isoformat()

# # 7 - Nueva funcionalidad de análisis de costos
# def show_analisis_costos_avanzado(data_manager, user_info):
#     """Página de análisis de costos integral"""
#     st.title("💰 Análisis de Costos y Rentabilidad")
    
#     especialidad = user_info.get('especialidad', 'odontologia')
#     especialidad_emoji = {
#         'odontologia': '🦷',
#         'dermatologia': '🧴',
#         'kinesiologia': '🏃‍♂️'
#     }.get(especialidad, '🏥')
    
#     st.markdown(f"### {especialidad_emoji} {especialidad.title()}")
    
#     # Calcular métricas de costos
#     costos_analysis = data_manager.calcular_costo_hora_real()
    
#     # Métricas principales
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("💰 Costo Real/Hora", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
#     with col2:
#         precio_minimo = costos_analysis['costo_hora_ars'] * 1.5  # 50% margen
#         st.metric("📊 Precio Mín. (50%)", f"${precio_minimo:,.0f} ARS")
    
#     with col3:
#         precio_optimo = costos_analysis['costo_hora_ars'] * 2  # 100% margen
#         st.metric("🎯 Precio Óptimo (100%)", f"${precio_optimo:,.0f} ARS")
    
#     with col4:
#         horas_breakeven = costos_analysis['costo_total_anual'] / (data_manager.get_resumen()['promedio_consulta'] or 1)
#         st.metric("⚖️ Consultas Break-Even", f"{horas_breakeven:,.0f} /año")
    
#     # Gráfico de composición de costos
#     if costos_analysis['costo_total_anual'] > 0:
#         st.subheader("📊 Composición de Costos Anuales")
        
#         costos_data = pd.DataFrame([
#             {"Categoría": "Equipos (Amortización)", "Monto": costos_analysis['costo_equipos_anual']},
#             {"Categoría": "Gastos Fijos", "Monto": costos_analysis['costo_gastos_anual']}
#         ])
        
#         fig_costos = px.pie(
#             costos_data, 
#             values='Monto', 
#             names='Categoría',
#             title=f"Total Anual: ${costos_analysis['costo_total_anual']:,.0f} ARS",
#             color_discrete_sequence=['#3b82f6', '#ef4444']
#         )
#         st.plotly_chart(fig_costos, use_container_width=True)
    
#     # Análisis de rentabilidad actual
#     resumen = data_manager.get_resumen()
#     if resumen['total_consultas'] > 0:
#         st.subheader("📈 Análisis de Rentabilidad Actual")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.markdown("**💵 Ingresos vs Costos**")
#             ingresos_anuales = resumen['ingreso_total'] * 12  # Proyección anual
#             margen_real = ((ingresos_anuales - costos_analysis['costo_total_anual']) / ingresos_anuales * 100) if ingresos_anuales > 0 else 0
            
#             if margen_real > 50:
#                 st.success(f"✅ Margen excelente: {margen_real:.1f}%")
#             elif margen_real > 25:
#                 st.warning(f"⚠️ Margen aceptable: {margen_real:.1f}%")
#             else:
#                 st.error(f"🚨 Margen bajo: {margen_real:.1f}%")
        
#         with col2:
#             st.markdown("**⏰ Eficiencia Horaria**")
#             consultas_mes = resumen['total_consultas'] / max(1, len(data_manager.consultas['fecha'].dt.month.unique()) if not data_manager.consultas.empty else 1)
#             eficiencia = (consultas_mes * 12) / costos_analysis['horas_anuales'] if costos_analysis['horas_anuales'] > 0 else 0
            
#             st.metric("Consultas por Hora Disponible", f"{eficiencia:.2f}")

# def show_configuracion_costos(data_manager):
#     """Página de configuración de costos"""
#     st.title("⚙️ Configuración de Costos")
    
#     tab1, tab2, tab3, tab4 = st.tabs(["🔧 Equipos", "🏢 Gastos Fijos", "⚙️ Parámetros", "💱 Tipo de Cambio"])
    
#     with tab1:
#         st.subheader("🔧 Equipamiento del Consultorio")
        
#         # Mostrar equipos actuales
#         if data_manager.equipos:
#             equipos_df = pd.DataFrame(data_manager.equipos)
#             equipos_df['monto_compra_usd'] = equipos_df['monto_compra_usd'].apply(lambda x: f"${x:,.0f} USD")
#             equipos_df['fecha_compra'] = pd.to_datetime(equipos_df['fecha_compra']).dt.strftime('%d/%m/%Y')
            
#             st.dataframe(
#                 equipos_df[['nombre', 'monto_compra_usd', 'años_vida_util', 'fecha_compra', 'observaciones']],
#                 use_container_width=True
#             )
#         else:
#             st.info("No hay equipos registrados aún.")
        
#         # Formulario para nuevo equipo
#         with st.form("nuevo_equipo"):
#             st.markdown("**Agregar Nuevo Equipo**")
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 nombre_equipo = st.text_input("Nombre del Equipo *", placeholder="Ej: Sillón Dental")
#                 monto_usd = st.number_input("Precio pagado (USD) *", min_value=0.0, step=100.0, value=1000.0)
            
#             with col2:
#                 años_vida = st.selectbox("Vida Útil (años)", [3, 5, 7, 8, 10], index=1)
#                 fecha_compra = st.date_input("Fecha de Compra", value=date.today())
            
#             observaciones = st.text_area("Observaciones (opcional)")
            
#             if st.form_submit_button("💾 Agregar Equipo", type="primary"):
#                 if nombre_equipo and monto_usd > 0:
#                     data_manager.add_equipo(nombre_equipo, monto_usd, años_vida, fecha_compra, observaciones)
#                     st.success("✅ Equipo agregado correctamente")
#                     st.rerun()
#                 else:
#                     st.error("❌ Complete los campos obligatorios")
    
#     with tab2:
#         st.subheader("🏢 Gastos Fijos Mensuales")
        
#         # Mostrar gastos actuales
#         if data_manager.gastos_fijos:
#             gastos_df = pd.DataFrame(data_manager.gastos_fijos)
#             gastos_df['monto_mensual_ars'] = gastos_df['monto_mensual_ars'].apply(lambda x: f"${x:,.0f} ARS")
            
#             st.dataframe(
#                 gastos_df[['concepto', 'monto_mensual_ars']],
#                 use_container_width=True
#             )
            
#             total_mensual = sum([g['monto_mensual_ars'] for g in data_manager.gastos_fijos if g.get('activo', True)])
#             st.metric("💰 Total Gastos Fijos", f"${total_mensual:,.0f} ARS/mes")
#         else:
#             st.info("No hay gastos fijos registrados aún.")
        
#         # Formulario para nuevo gasto
#         with st.form("nuevo_gasto"):
#             st.markdown("**Agregar Nuevo Gasto Fijo**")
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 concepto = st.text_input("Concepto *", placeholder="Ej: Alquiler")
#             with col2:
#                 monto_mensual = st.number_input("Monto mensual (ARS) *", min_value=0.0, step=1000.0, value=50000.0)
            
#             if st.form_submit_button("💾 Agregar Gasto", type="primary"):
#                 if concepto and monto_mensual > 0:
#                     data_manager.add_gasto_fijo(concepto, monto_mensual)
#                     st.success("✅ Gasto agregado correctamente")
#                     st.rerun()
#                 else:
#                     st.error("❌ Complete los campos obligatorios")
    
#     with tab3:
#         st.subheader("⚙️ Parámetros de Trabajo")
        
#         with st.form("parametros"):
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.markdown("**⏰ Configuración Temporal**")
#                 nuevas_horas = st.number_input(
#                     "Horas anuales trabajadas",
#                     min_value=500,
#                     max_value=2000,
#                     value=data_manager.config.get('horas_anuales_trabajadas', 1100),
#                     step=50
#                 )
                
#                 dias_semana = st.slider(
#                     "Días trabajo por semana",
#                     min_value=3,
#                     max_value=7,
#                     value=data_manager.config.get('dias_trabajo_semana', 5)
#                 )
            
#             with col2:
#                 st.markdown("**💰 Configuración Económica**")
#                 nuevo_margen = st.slider(
#                     "Margen de ganancia objetivo (%)",
#                     min_value=10,
#                     max_value=200,
#                     value=int(data_manager.config.get('margen_ganancia', 0.4) * 100),
#                     step=5
#                 ) / 100
                
#                 nueva_region = st.selectbox(
#                     "Región",
#                     ["CABA", "GBA Norte", "GBA Sur", "La Plata", "Córdoba Capital", 
#                      "Rosario", "Mendoza", "Tucumán", "Interior Pampeano", 
#                      "Interior NOA/NEA", "Patagonia Norte", "Patagonia Sur"],
#                     index=10  # Interior NOA/NEA por defecto
#                 )
            
#             if st.form_submit_button("💾 Actualizar Parámetros", type="primary"):
#                 data_manager.config.update({
#                     'horas_anuales_trabajadas': nuevas_horas,
#                     'dias_trabajo_semana': dias_semana,
#                     'margen_ganancia': nuevo_margen,
#                     'region': nueva_region
#                 })
#                 data_manager.save_data()
#                 st.success("✅ Parámetros actualizados correctamente")
#                 st.rerun()
   
#     with tab4:
#         st.subheader("💱 Tipo de Cambio USD/ARS")
        
#         actual_tc = data_manager.config.get('tipo_cambio_usd_ars', 1335.0)
#         st.metric("Tipo de cambio actual", f"${actual_tc:,.0f} ARS por USD")
        
#         with st.form("tipo_cambio"):
#             nuevo_tc = st.number_input(
#                 "Nuevo tipo de cambio (ARS por USD)",
#                 min_value=100.0,
#                 max_value=5000.0,
#                 value=actual_tc,
#                 step=10.0
#             )
            
#             if st.form_submit_button("💾 Actualizar Tipo de Cambio", type="primary"):
#                 data_manager.config['tipo_cambio_usd_ars'] = nuevo_tc
#                 data_manager.save_data()
#                 st.success("Tipo de cambio actualizado")
#                 st.rerun()

#     # 8 - Funciones de interfaz existentes (adaptadas)
#     def show_dashboard_enhanced(data_manager, user_info):
#         """Dashboard mejorado con análisis de costos"""
#     especialidad = user_info.get('especialidad', 'odontologia')
#     especialidad_emoji = {
#         'odontologia': '🦷',
#         'dermatologia': '🧴', 
#         'kinesiologia': '🏃‍♂️'
#     }.get(especialidad, '🏥')
    
#     st.subheader(f"📊 Dashboard - {user_info.get('nombre', 'Usuario')} {especialidad_emoji}")
    
#     # Análisis de costos en el dashboard
#     costos_analysis = data_manager.calcular_costo_hora_real()
    
#     # Mostrar alerta si tiene costos configurados
#     if costos_analysis['costo_total_anual'] > 0:
#         st.markdown("""
#         <div class="cost-analysis-card">
#             <h3>💰 Análisis de Costos Automático</h3>
#             <p>Su costo real por hora: <strong>${:,.0f} ARS</strong></p>
#             <p>Precio mínimo recomendado (50% margen): <strong>${:,.0f} ARS</strong></p>
#         </div>
#         """.format(costos_analysis['costo_hora_ars'], costos_analysis['costo_hora_ars'] * 1.5), unsafe_allow_html=True)
    
#     # Dashboard original
#     resumen = data_manager.get_resumen()
    
#     plan = user_info.get('plan', 'trial')
#     if plan == 'trial':
#         st.info("Plan de prueba activo. Sus datos son privados y están separados de otros usuarios.")
#     elif plan == 'premium':
#         st.success("Plan Premium activo. Acceso completo a todas las funcionalidades.")
    
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric(
#             "Ingresos Totales",
#             f"${resumen['ingreso_total']:,.0f} ARS",
#             delta=f"${resumen['ingresos_mes']:,.0f} este mes"
#         )
    
#     with col2:
#         st.metric("Total Consultas", resumen['total_consultas'])
    
#     with col3:
#         st.metric("Promedio/Consulta", f"${resumen['promedio_consulta']:,.0f} ARS")
    
#     with col4:
#         st.metric("Más Popular", resumen['tratamiento_popular'])
    
#     # Gráficos existentes
#     if not data_manager.consultas.empty:
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.subheader("Ingresos por Mes")
            
#             df_monthly = data_manager.consultas.copy()
#             df_monthly['fecha'] = pd.to_datetime(df_monthly['fecha'])
#             df_monthly['mes'] = df_monthly['fecha'].dt.to_period('M')
#             monthly_income = df_monthly.groupby('mes')['monto_ars'].sum().reset_index()
#             monthly_income['mes'] = monthly_income['mes'].astype(str)
            
#             fig_monthly = px.bar(
#                 monthly_income, 
#                 x='mes', 
#                 y='monto_ars',
#                 title="Ingresos Mensuales (ARS)",
#                 color='monto_ars',
#                 color_continuous_scale='Blues'
#             )
#             fig_monthly.update_layout(showlegend=False)
#             st.plotly_chart(fig_monthly, use_container_width=True)
        
#         with col2:
#             st.subheader("Tratamientos Realizados")
            
#             tratamientos = data_manager.consultas['tratamiento'].value_counts()
            
#             fig_pie = px.pie(
#                 values=tratamientos.values,
#                 names=tratamientos.index,
#                 title="Distribución de Tratamientos"
#             )
#             st.plotly_chart(fig_pie, use_container_width=True)
        
#         st.subheader("Últimas Consultas")
        
#         recent_consultas = data_manager.consultas.tail(10).copy()
#         if not recent_consultas.empty:
#             recent_consultas['fecha'] = pd.to_datetime(recent_consultas['fecha']).dt.strftime('%d/%m/%Y %H:%M')
#             recent_consultas = recent_consultas[['fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago']]
#             recent_consultas.columns = ['Fecha', 'Paciente', 'Tratamiento', 'Monto (ARS)', 'Medio de Pago']
#             st.dataframe(recent_consultas, use_container_width=True)
    
#     else:
#         st.info("No hay consultas registradas aún. Comience agregando su primera consulta!")

#     # Mantener funciones existentes
#     def show_nueva_consulta(data_manager):
#         """Formulario para nueva consulta"""
#     st.subheader("Registrar Nueva Consulta")
    
#     with st.form("nueva_consulta"):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             paciente = st.text_input("Nombre del Paciente *", placeholder="Ej: Juan Pérez")
#             tratamiento = st.selectbox(
#                 "Tipo de Tratamiento *",
#                 ["Consulta", "Consulta de Urgencia", "Limpieza", "Operatoria Simple", 
#                     "Operatoria Compleja", "Endodoncia Unirradicular", "Endodoncia Multirradicular",
#                     "Placa Estabilizadora", "Provisorio", "Corona Metálica", "Corona de Porcelana",
#                     "Extracción Simple", "Extracción Compleja", "Otro"]
#             )
        
#         with col2:
#             monto_ars = st.number_input("Monto en ARS *", min_value=0.0, step=1000.0, value=30000.0)
#             medio_pago = st.selectbox(
#                 "Medio de Pago *",
#                 ["Efectivo", "Transferencia", "Débito", "Crédito", "Mercado Pago", "Otros"]
#             )
        
#         submitted = st.form_submit_button("Registrar Consulta", type="primary")
        
#         if submitted:
#             if paciente and tratamiento and monto_ars > 0:
#                 try:
#                     nueva_consulta = data_manager.add_consulta(paciente, tratamiento, monto_ars, medio_pago)
#                     st.success(f"Consulta registrada: {paciente} - {tratamiento} - ${monto_ars:,.0f} ARS")
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"Error al registrar consulta: {e}")
#             else:
#                 st.error("Por favor complete todos los campos obligatorios (*)")

#     def show_calculadora_precios(data_manager):
#         """Calculadora de precios con costo real calculado"""
#     st.subheader("Calculadora de Precios Inteligente")
    
#     # Obtener costo real por hora
#     costos_analysis = data_manager.calcular_costo_hora_real()
#     costo_real_hora = costos_analysis['costo_hora_ars']
    
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         with st.form("calculadora"):
#             st.write("Parámetros del Tratamiento")
            
#             time_hours = st.number_input(
#                 "Tiempo estimado (horas) *", 
#                 min_value=0.1, 
#                 max_value=10.0, 
#                 value=1.0, 
#                 step=0.25
#             )
            
#             materials_ars = st.number_input(
#                 "Costo de materiales (ARS) *", 
#                 min_value=0.0, 
#                 value=5000.0, 
#                 step=500.0
#             )
            
#             usar_costo_real = st.checkbox("Usar costo real por hora calculado", value=True)
            
#             if not usar_costo_real:
#                 costo_hora_manual = st.number_input(
#                     "Costo por hora manual (ARS)",
#                     min_value=1000.0,
#                     value=29000.0,
#                     step=1000.0
#                 )
#                 costo_hora_usar = costo_hora_manual
#             else:
#                 costo_hora_usar = costo_real_hora
            
#             calcular = st.form_submit_button("Calcular Precio", type="primary")
            
#             if calcular:
#                 try:
#                     resultado = calculate_price_optimized(
#                         time_hours, 
#                         materials_ars, 
#                         costo_hora_usar,
#                         data_manager.config['margen_ganancia']
#                     )
                    
#                     st.session_state.ultimo_calculo = resultado
                    
#                 except Exception as e:
#                     st.error(f"Error en cálculo: {e}")
    
#     with col2:
#         st.write("Información de Costos")
#         if costo_real_hora > 0:
#             st.metric("Costo Real/Hora", f"${costo_real_hora:,.0f} ARS")
#         else:
#             st.warning("Configure equipos y gastos fijos para calcular su costo real")
        
#         st.metric("Margen Configurado", f"{data_manager.config['margen_ganancia']*100:.0f}%")
    
#     if hasattr(st.session_state, 'ultimo_calculo'):
#         resultado = st.session_state.ultimo_calculo
        
#         st.markdown("---")
#         st.subheader("Resultado del Cálculo")
        
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric("Mano de Obra", f"${resultado['mano_obra']:,.0f} ARS")
        
#         with col2:
#             st.metric("Materiales", f"${resultado['materiales']:,.0f} ARS")
        
#         with col3:
#             st.metric("Costo Total", f"${resultado['costo_total']:,.0f} ARS")
        
#         with col4:
#             st.metric("Precio Final", f"${resultado['precio_final']:,.0f} ARS")

#     # Mantener funciones de reportes y migración existentes
#     def show_reportes(data_manager):
#         """Reportes detallados"""
#     st.subheader("Reportes Detallados")
    
#     if data_manager.consultas.empty:
#         st.info("No hay datos suficientes para generar reportes. Agregue algunas consultas primero.")
#         return
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         fecha_inicio = st.date_input("Fecha Inicio", value=date.today().replace(day=1))
    
#     with col2:
#         fecha_fin = st.date_input("Fecha Fin", value=date.today())
    
#     df_filtrado = data_manager.consultas.copy()
#     df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'])
#     df_filtrado = df_filtrado[
#         (df_filtrado['fecha'].dt.date >= fecha_inicio) & 
#         (df_filtrado['fecha'].dt.date <= fecha_fin)
#     ]
    
#     if df_filtrado.empty:
#         st.warning("No hay datos en el rango de fechas seleccionado")
#         return
    
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("Consultas", len(df_filtrado))
    
#     with col2:
#         ingresos_periodo = df_filtrado['monto_ars'].sum()
#         st.metric("Ingresos", f"${ingresos_periodo:,.0f} ARS")
    
#     with col3:
#         promedio_periodo = df_filtrado['monto_ars'].mean()
#         st.metric("Promedio", f"${promedio_periodo:,.0f} ARS")
    
#     with col4:
#         dias_periodo = (fecha_fin - fecha_inicio).days + 1
#         consultas_por_dia = len(df_filtrado) / dias_periodo
#         st.metric("Consultas/Día", f"{consultas_por_dia:.1f}")
    
#     # Resto del código de reportes existente...
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.subheader("Evolución Diaria")
        
#         df_diario = df_filtrado.groupby(df_filtrado['fecha'].dt.date).agg({
#             'monto_ars': 'sum',
#             'paciente': 'count'
#         }).reset_index()
#         df_diario.columns = ['fecha', 'ingresos', 'consultas']
        
#         fig_daily = go.Figure()
#         fig_daily.add_trace(go.Scatter(
#             x=df_diario['fecha'],
#             y=df_diario['ingresos'],
#             mode='lines+markers',
#             name='Ingresos ARS',
#             line=dict(color='#3b82f6')
#         ))
        
#         fig_daily.update_layout(
#             title="Ingresos Diarios",
#             xaxis_title="Fecha",
#             yaxis_title="Ingresos (ARS)"
#         )
#         st.plotly_chart(fig_daily, use_container_width=True)
    
#     with col2:
#         st.subheader("Medios de Pago")
        
#         medios_pago = df_filtrado.groupby('medio_pago')['monto_ars'].sum()
        
#         fig_payment = px.pie(
#             values=medios_pago.values,
#             names=medios_pago.index,
#             title="Distribución por Medio de Pago"
#         )
#         st.plotly_chart(fig_payment, use_container_width=True)

#     def show_migration_tool_flexible(data_manager):
#         """Herramienta de migración flexible para cualquier CSV"""
#     st.subheader("Migración Flexible de Datos")
    
#     st.markdown("""
#     **Migración Universal de CSV**
    
#     Esta herramienta puede trabajar con cualquier archivo CSV:
#     - Mapea automáticamente las columnas de tu archivo
#     - Convierte formatos de fecha y moneda
#     - Todo en pesos argentinos
#     - Vista previa antes de migrar
#     """)
    
#     uploaded_file = st.file_uploader(
#         "Sube tu archivo CSV", 
#         type=['csv'],
#         help="Sube cualquier archivo CSV con datos de consultas"
#     )
    
#     if uploaded_file is not None:
#         try:
#             # Detectar encoding
#             encoding_options = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
#             df = None
#             encoding_usado = None
            
#             for encoding in encoding_options:
#                 try:
#                     df = pd.read_csv(uploaded_file, encoding=encoding)
#                     encoding_usado = encoding
#                     break
#                 except UnicodeDecodeError:
#                     continue
            
#             if df is None:
#                 st.error("No se pudo leer el archivo. Verifica el formato.")
#                 return
            
#             st.success(f"Archivo cargado correctamente (encoding: {encoding_usado})")
            
#             # Vista previa del archivo
#             with st.expander("Vista Previa del Archivo", expanded=True):
#                 col1, col2, col3 = st.columns(3)
#                 with col1:
#                     st.metric("Total Registros", len(df))
#                 with col2:
#                     st.metric("Columnas", len(df.columns))
#                 with col3:
#                     st.metric("Tamaño", f"{uploaded_file.size / 1024:.1f} KB")
                
#                 st.markdown("**Primeras 5 filas:**")
#                 st.dataframe(df.head(), use_container_width=True)
                
#                 st.markdown("**Columnas disponibles:**")
#                 st.write(", ".join(df.columns.tolist()))
            
#             # Mapeo de columnas
#             st.subheader("Mapeo de Columnas")
#             st.markdown("Indica qué columna de tu CSV corresponde a cada campo:")
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.markdown("**Campos Obligatorios:**")
                
#                 col_paciente = st.selectbox(
#                     "Columna de Pacientes *",
#                     options=['-- Seleccionar --'] + df.columns.tolist()
#                 )
                
#                 col_tratamiento = st.selectbox(
#                     "Columna de Tratamientos *",
#                     options=['-- Seleccionar --'] + df.columns.tolist()
#                 )
                
#                 col_monto = st.selectbox(
#                     "Columna de Montos (ARS) *",
#                     options=['-- Seleccionar --'] + df.columns.tolist()
#                 )
            
#             with col2:
#                 st.markdown("**Campos Opcionales:**")
                
#                 col_fecha = st.selectbox(
#                     "Columna de Fechas",
#                     options=['-- Usar fecha actual --'] + df.columns.tolist()
#                 )
                
#                 col_medio_pago = st.selectbox(
#                     "Columna de Medio de Pago",
#                     options=['-- Usar "No especificado" --'] + df.columns.tolist()
#                 )
            
#             # Vista previa del mapeo
#             if (col_paciente != '-- Seleccionar --' and 
#                 col_tratamiento != '-- Seleccionar --' and 
#                 col_monto != '-- Seleccionar --'):
                
#                 st.subheader("Vista Previa del Mapeo")
                
#                 muestra = df.head(5).copy()
#                 preview_data = []
                
#                 for _, row in muestra.iterrows():
#                     if col_fecha == '-- Usar fecha actual --':
#                         fecha_procesada = datetime.now().strftime('%d/%m/%Y')
#                     else:
#                         fecha_raw = row[col_fecha]
#                         fecha_iso = normalizar_fecha_flexible(fecha_raw)
#                         fecha_procesada = datetime.fromisoformat(fecha_iso).strftime('%d/%m/%Y')
                    
#                     monto_raw = row[col_monto]
#                     monto_procesado = extraer_monto_numerico(monto_raw)
                    
#                     if col_medio_pago == '-- Usar "No especificado" --':
#                         medio_pago = "No especificado"
#                     else:
#                         medio_pago = str(row[col_medio_pago]) if pd.notna(row[col_medio_pago]) else "No especificado"
                    
#                     preview_data.append({
#                         'Fecha': fecha_procesada,
#                         'Paciente': str(row[col_paciente]),
#                         'Tratamiento': str(row[col_tratamiento]),
#                         'Monto Original': str(monto_raw),
#                         'Monto ARS': f"${monto_procesado:,.0f}",
#                         'Medio de Pago': medio_pago
#                     })
                
#                 preview_df = pd.DataFrame(preview_data)
#                 st.dataframe(preview_df, use_container_width=True)
                
#                 # Estadísticas pre-migración
#                 col1, col2, col3, col4 = st.columns(4)
                
#                 with col1:
#                     pacientes_unicos = df[col_paciente].nunique()
#                     st.metric("Pacientes Únicos", pacientes_unicos)
                
#                 with col2:
#                     tratamientos_unicos = df[col_tratamiento].nunique()
#                     st.metric("Tipos de Tratamiento", tratamientos_unicos)
                
#                 with col3:
#                     montos_procesados = df[col_monto].apply(extraer_monto_numerico)
#                     total_estimado = montos_procesados.sum()
#                     st.metric("Total Estimado", f"${total_estimado:,.0f} ARS")
                
#                 with col4:
#                     registros_validos = len(df.dropna(subset=[col_paciente, col_tratamiento, col_monto]))
#                     st.metric("Registros Válidos", registros_validos)
                
#                 # Botón de migración
#                 st.markdown("---")
                
#                 col1, col2 = st.columns([3, 1])
                
#                 with col1:
#                     st.markdown("### ¿Todo se ve correcto?")
#                     st.markdown("Revisa la vista previa y las estadísticas antes de proceder.")
                
#                 with col2:
#                     if st.button("Ejecutar Migración", type="primary", use_container_width=True):
#                         with st.spinner("Migrando datos..."):
#                             resultado = ejecutar_migracion_flexible(
#                                 df=df,
#                                 col_paciente=col_paciente,
#                                 col_tratamiento=col_tratamiento,
#                                 col_monto=col_monto,
#                                 col_fecha=col_fecha if col_fecha != '-- Usar fecha actual --' else None,
#                                 col_medio_pago=col_medio_pago if col_medio_pago != '-- Usar "No especificado" --' else None,
#                                 data_manager=data_manager
#                             )
                        
#                         if resultado['success']:
#                             st.success("Migración completada exitosamente!")
                            
#                             col1, col2, col3 = st.columns(3)
#                             with col1:
#                                 st.metric("Registros Migrados", resultado['migrados'])
#                             with col2:
#                                 st.metric("Errores", resultado['errores'])
#                             with col3:
#                                 st.metric("Total Migrado", f"${resultado['total_ars']:,.0f} ARS")
                            
#                             if resultado['errores'] > 0:
#                                 st.warning(f"{resultado['errores']} registros tuvieron problemas y no se migraron")
                            
#                             st.info("Recarga la página para ver los datos migrados en el Dashboard")
                            
#                             if st.button("Recargar Aplicación"):
#                                 st.rerun()
                        
#                         else:
#                             st.error(f"Error en la migración: {resultado['error']}")
            
#             else:
#                 st.info("Por favor selecciona al menos las columnas obligatorias para continuar")
        
#         except Exception as e:
#             st.error(f"Error procesando el archivo: {e}")
    
#     else:
#         st.info("Sube un archivo CSV para comenzar")

#     def ejecutar_migracion_flexible(df, col_paciente, col_tratamiento, col_monto, 
#                                 col_fecha=None, col_medio_pago=None, data_manager=None):
#         """Ejecuta la migración flexible solo con pesos argentinos"""
    
#     try:
#         consultas_migradas = []
#         errores = 0
#         total_ars = 0
        
#         for index, row in df.iterrows():
#             try:
#                 if col_fecha:
#                     fecha = normalizar_fecha_flexible(row[col_fecha])
#                 else:
#                     fecha = datetime.now().isoformat()
                
#                 paciente = str(row[col_paciente]).strip() if pd.notna(row[col_paciente]) else f'Paciente_{index+1}'
#                 tratamiento = str(row[col_tratamiento]).strip() if pd.notna(row[col_tratamiento]) else 'Consulta'
#                 monto_numerico = extraer_monto_numerico(row[col_monto])
                
#                 if monto_numerico <= 0:
#                     errores += 1
#                     continue
                
#                 if col_medio_pago:
#                     medio_pago = str(row[col_medio_pago]).strip() if pd.notna(row[col_medio_pago]) else 'No especificado'
#                 else:
#                     medio_pago = 'No especificado'
                
#                 consulta = {
#                     'fecha': fecha,
#                     'paciente': paciente,
#                     'tratamiento': tratamiento,
#                     'monto_ars': round(monto_numerico, 0),
#                     'medio_pago': medio_pago
#                 }
                
#                 consultas_migradas.append(consulta)
#                 total_ars += monto_numerico
                
#             except Exception as e:
#                 errores += 1
#                 st.warning(f"Error en fila {index+1}: {e}")
#                 continue
        
#         if consultas_migradas:
#             for consulta in consultas_migradas:
#                 nueva_fila = {
#                     'fecha': consulta['fecha'],
#                     'paciente': consulta['paciente'], 
#                     'tratamiento': consulta['tratamiento'],
#                     'monto_ars': consulta['monto_ars'],
#                     'medio_pago': consulta['medio_pago']
#                 }
                
#                 if data_manager.consultas.empty:
#                     data_manager.consultas = pd.DataFrame([nueva_fila])
#                 else:
#                     data_manager.consultas = pd.concat([data_manager.consultas, pd.DataFrame([nueva_fila])], ignore_index=True)
            
#             data_manager.save_data()
        
#         return {
#             'success': True,
#             'migrados': len(consultas_migradas),
#             'errores': errores,
#             'total_ars': round(total_ars, 0)
#         }
        
#     except Exception as e:
#         return {
#             'success': False,
#             'error': str(e),
#             'migrados': 0,
#             'errores': 0,
#             'total_ars': 0
#         }

#     def show_login():
#         """Pantalla de login"""
#     st.title("Manny App - Sistema de Gestión de Consultorios de Salud")
    
#     with st.expander("Información del Sistema"):
#         st.markdown("""
#         **Manny App - Sistema de Gestión Profesional**
        
#         **Especialidades soportadas:**
#         - Odontología
#         - Dermatología  
#         - Kinesiología
#         - Más especialidades próximamente
        
#         **Características:**
#         - Dashboard con métricas en tiempo real
#         - Análisis de costos automático
#         - Gestión de consultas y pacientes
#         - Calculadora de precios inteligente
#         - Control de equipos y gastos fijos
#         - Reportes detallados y exportación
#         - Sistema multi-usuario con datos separados
        
#         **Acceso:**
#         - Cada usuario tiene sus propios datos privados
#         - Sistema de autenticación seguro
#         - Datos completamente separados entre usuarios
#         """)
    
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         with st.form("login_form"):
#             st.write("Ingresar al Sistema")
            
#             username = st.text_input("Usuario", placeholder="Ingrese su usuario")
#             password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            
#             show_demo_hint = st.checkbox("Mostrar usuarios de demo")
            
#             if show_demo_hint:
#                 st.info("""
#                 **Usuarios de prueba disponibles:**
                
#                 **Administrador**: `admin` / `Homero123` (Odontólogo)
#                 **Demo 1**: `demo1` / `Homero123` (Odontólogo)  
#                 **Demo 2**: `demo2` / `Homero123` (Dermatólogo)
                
#                 Solo para evaluación del sistema
#                 """)
            
#             login_button = st.form_submit_button("Ingresar", use_container_width=True)
            
#             if login_button:
#                 if username and password:
#                     user_manager = UserManager()
#                     is_valid, message = user_manager.validate_user(username, password)
                    
#                     if is_valid:
#                         st.session_state.authenticated = True
#                         st.session_state.user_id = username
#                         st.session_state.user_info = user_manager.get_user_info(username)
                        
#                         st.success(f"{message}")
#                         st.rerun()
#                     else:
#                         st.error(f"{message}")
#                         if "Usuario no encontrado" in message:
#                             st.info("Tip: Verifique el nombre de usuario. Para demo, active el checkbox superior.")
#                 else:
#                     st.warning("Por favor complete todos los campos")
    
#     st.markdown("---")
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         st.markdown("""
#         <div style='text-align: center; color: #666; font-size: 0.8em;'>
#         ¿Necesita acceso? Contacte al administrador del sistema<br>
#         Sistema seguro - Datos protegidos y privados
#         </div>
#         """, unsafe_allow_html=True)

#     def main():
#         if 'authenticated' not in st.session_state or not st.session_state.authenticated:
#             show_login()
#         else:
#             show_main()
#         return
    
#     user_id = st.session_state.user_id
#     user_info = st.session_state.user_info
    
#     # Header
#     col1, col2, col3 = st.columns([3, 1, 1])
    
#     with col1:
#        especialidad = user_info.get('especialidad', 'salud')
#        especialidad_emoji = {
#            'odontologia': '🦷',
#            'dermatologia': '🧴', 
#            'kinesiologia': '🏃‍♂️'
#        }.get(especialidad, '🏥')
       
#        st.markdown(f'<h1 class="main-header">Manny App - {especialidad.title()} {especialidad_emoji}</h1>', unsafe_allow_html=True)
   
#     with col2:
#         st.write(f"{user_info.get('nombre', user_id)}")
    
#     with col3:
#         if st.button("Cerrar Sesión"):
#             for key in list(st.session_state.keys()):
#                 del st.session_state[key]
#             st.rerun()
    
#     # Inicializar DataManager
#     if 'data_manager' not in st.session_state:
#         st.session_state.data_manager = DataManager(user_id=user_id)
    
#     data_manager = st.session_state.data_manager
    
#     # Sidebar con menú expandido
#     with st.sidebar:
#         st.markdown(f"""
#         <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%); border-radius: 0.5rem; margin-bottom: 1rem; color: white;'>
#         <h3>Manny App</h3>
#         <p style='margin: 0; font-size: 0.9em;'>{especialidad.title()}</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         menu = st.selectbox(
#             "Menú Principal",
#             [
#                 "🏠 Dashboard", 
#                 "➕ Nueva Consulta", 
#                 "💰 Análisis de Costos",
#                 "⚙️ Configuración Costos",
#                 "🧮 Calculadora de Precios", 
#                 "📈 Reportes", 
#                 "📥 Migrar Datos"
#             ]
#         )
        
#         st.markdown("---")
        
#         # Métricas en sidebar
#         resumen = data_manager.get_resumen()
#         st.metric("Ingresos Totales", f"${resumen['ingreso_total']:,.0f} ARS")
#         st.metric("Consultas", resumen['total_consultas'])
#         st.metric("Promedio", f"${resumen['promedio_consulta']:,.0f} ARS")
        
#         # Mostrar costo por hora si está configurado
#         costos_analysis = data_manager.calcular_costo_hora_real()
#         if costos_analysis['costo_total_anual'] > 0:
#             st.markdown("---")
#             st.metric("Costo/Hora Real", f"${costos_analysis['costo_hora_ars']:,.0f} ARS")
    
#     # Router de páginas
#     if menu == "🏠 Dashboard":
#         show_dashboard_enhanced(data_manager, user_info)
#     elif menu == "➕ Nueva Consulta":
#         show_nueva_consulta(data_manager)
#     elif menu == "💰 Análisis de Costos":
#         show_analisis_costos_avanzado(data_manager, user_info)
#     elif menu == "⚙️ Configuración Costos":
#         show_configuracion_costos(data_manager)
#     elif menu == "🧮 Calculadora de Precios":
#         show_calculadora_precios(data_manager)
#     elif menu == "📈 Reportes":
#         show_reportes(data_manager)
#     elif menu == "📥 Migrar Datos":
#         show_migration_tool_flexible(data_manager)

#         if __name__ == "__main__":
#             main()

# V2.0

# 1 - imports
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime, date
# import json
# import os
# import re
# import hashlib
# from typing import Dict, List, Tuple
# import numpy as np



# # 2 - Configuración de la página
# st.set_page_config(
#     page_title="Gestión de Consultorios Odontológicos v2.0",
#     page_icon="🦷",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # 3 - CSS personalizado
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         color: #1e3a8a;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
#     .metric-card {
#         background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
#         padding: 1rem;
#         border-radius: 0.5rem;
#         color: white;
#         text-align: center;
#         margin: 0.5rem 0;
#     }
#     .alert-success {
#         background-color: #dcfce7;
#         border: 1px solid #16a34a;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin: 1rem 0;
#     }
#     .alert-warning {
#         background-color: #fef3c7;
#         border: 1px solid #d97706;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin: 1rem 0;
#     }
#     .alert-error {
#         background-color: #fee2e2;
#         border: 1px solid #dc2626;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin: 1rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # 4 - UserManager
# class UserManager:
#     """Maneja autenticación y usuarios del sistema"""
    
#     def __init__(self):
#         self.users_file = "usuarios.json"
#         self.data_folder = "data"
#         self.init_system()
    
#     def init_system(self):
#         """Inicializa el sistema creando archivos necesarios"""
#         if not os.path.exists(self.data_folder):
#             os.makedirs(self.data_folder)
        
#         if not os.path.exists(self.users_file):
#             usuarios_default = {
#                 "admin": {
#                     "password_hash": self.hash_password("Homero123"),
#                     "nombre": "Dr. Administrador",
#                     "email": "admin@dental.com",
#                     "plan": "premium",
#                     "fecha_registro": datetime.now().isoformat()
#                 },
#                 "demo1": {
#                     "password_hash": self.hash_password("Homero123"),
#                     "nombre": "Dr. Demo Uno",
#                     "email": "demo1@dental.com",
#                     "plan": "trial",
#                     "fecha_registro": datetime.now().isoformat()
#                 },
#                 "demo2": {
#                     "password_hash": self.hash_password("Homero123"),
#                     "nombre": "Dra. Demo Dos",
#                     "email": "demo2@dental.com",
#                     "plan": "trial",
#                     "fecha_registro": datetime.now().isoformat()
#                 }
#             }
            
#             self.save_users(usuarios_default)
            
#             for user_id in usuarios_default.keys():
#                 self.create_user_folder(user_id)
    
#     def hash_password(self, password):
#         return hashlib.sha256(password.encode()).hexdigest()
    
#     def load_users(self):
#         try:
#             with open(self.users_file, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         except:
#             return {}
    
#     def save_users(self, users_data):
#         with open(self.users_file, 'w', encoding='utf-8') as f:
#             json.dump(users_data, f, ensure_ascii=False, indent=2)
    
#     def validate_user(self, username, password):
#         users = self.load_users()
        
#         if username not in users:
#             return False, "Usuario no encontrado"
        
#         password_hash = self.hash_password(password)
        
#         if users[username]["password_hash"] != password_hash:
#             return False, "Contraseña incorrecta"
        
#         return True, "Login exitoso"
    
#     def get_user_info(self, username):
#         users = self.load_users()
#         return users.get(username, {})
    
#     def create_user_folder(self, user_id):
#         user_folder = os.path.join(self.data_folder, user_id)
        
#         if not os.path.exists(user_folder):
#             os.makedirs(user_folder)
            
#             initial_data = {
#                 'consultas': [],
#                 'config': {
#                     'costo_por_hora': 29000,  # En pesos
#                     'margen_ganancia': 0.40
# #                    'region': 'Interior NOA/NEA'
#                 }
#             }
            
#             data_file = os.path.join(user_folder, 'dental_data.json')
#             with open(data_file, 'w', encoding='utf-8') as f:
#                 json.dump(initial_data, f, ensure_ascii=False, indent=2, default=str)

# # 5 - DataManager
# class DataManager:
#     """Manejo de datos del consultorio - Solo pesos argentinos"""
    
#     def __init__(self, user_id=None):
#         if user_id:
#             self.data_file = os.path.join("data", user_id, "dental_data.json")
#         else:
#             self.data_file = "dental_data.json"
#         self.load_data()
    
#     def load_data(self):
#         if os.path.exists(self.data_file):
#             try:
#                 with open(self.data_file, 'r', encoding='utf-8') as f:
#                     data = json.load(f)
#                     self.consultas = pd.DataFrame(data.get('consultas', []))
#                     self.config = data.get('config', self.get_default_config())
#             except Exception as e:
#                 st.error(f"Error cargando datos: {e}")
#                 self.init_default_data()
#         else:
#             self.init_default_data()
    
#     def init_default_data(self):
#         self.consultas = pd.DataFrame(columns=[
#             'fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago'
#         ])
#         self.config = self.get_default_config()
    
#     def get_default_config(self):
#         return {
#             'costo_por_hora': 29000,  # En pesos
#             'margen_ganancia': 0.40
# #            'region': 'Interior NOA/NEA'
#         }
    
#     def save_data(self):
#         try:
#             os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
#             data = {
#                 'consultas': self.consultas.to_dict('records'),
#                 'config': self.config
#             }
#             with open(self.data_file, 'w', encoding='utf-8') as f:
#                 json.dump(data, f, ensure_ascii=False, indent=2, default=str)
#             return True
#         except Exception as e:
#             st.error(f"Error guardando datos: {e}")
#             return False
    
#     def add_consulta(self, paciente, tratamiento, monto_ars, medio_pago):
#         nueva_consulta = {
#             'fecha': datetime.now().isoformat(),
#             'paciente': paciente,
#             'tratamiento': tratamiento,
#             'monto_ars': monto_ars,
#             'medio_pago': medio_pago
#         }
        
#         if self.consultas.empty:
#             self.consultas = pd.DataFrame([nueva_consulta])
#         else:
#             self.consultas = pd.concat([self.consultas, pd.DataFrame([nueva_consulta])], ignore_index=True)
        
#         self.save_data()
#         return nueva_consulta
    
#     def get_resumen(self):
#         if self.consultas.empty:
#             return {
#                 'total_consultas': 0,
#                 'ingreso_total': 0,
#                 'promedio_consulta': 0,
#                 'tratamiento_popular': 'N/A',
#                 'ingresos_mes': 0
#             }
        
#         if not self.consultas.empty:
#             self.consultas['fecha'] = pd.to_datetime(self.consultas['fecha'])
        
#         total_consultas = len(self.consultas)
#         ingreso_total = self.consultas['monto_ars'].sum()
#         promedio_consulta = ingreso_total / total_consultas if total_consultas > 0 else 0
        
#         tratamiento_popular = 'N/A'
#         if not self.consultas.empty:
#             tratamientos = self.consultas['tratamiento'].value_counts()
#             if not tratamientos.empty:
#                 tratamiento_popular = tratamientos.index[0]
        
#         fecha_actual = datetime.now()
#         mes_actual = self.consultas[
#             (self.consultas['fecha'].dt.month == fecha_actual.month) &
#             (self.consultas['fecha'].dt.year == fecha_actual.year)
#         ]
#         ingresos_mes = mes_actual['monto_ars'].sum() if not mes_actual.empty else 0
        
#         return {
#             'total_consultas': total_consultas,
#             'ingreso_total': round(ingreso_total, 0),
#             'promedio_consulta': round(promedio_consulta, 0),
#             'tratamiento_popular': tratamiento_popular,
#             'ingresos_mes': round(ingresos_mes, 0)
#         }

# # 6 - Funciones auxiliares
# def calculate_price_optimized(time_hours: float, materials_ars: float, cost_per_hour: float, margin: float = 0.40):
#     """Calcular precio optimizado en pesos"""
#     if time_hours <= 0 or materials_ars < 0:
#         raise ValueError("Horas debe ser > 0 y materiales >= 0")
    
#     labor_cost = time_hours * cost_per_hour
#     total_cost = labor_cost + materials_ars
#     final_price = total_cost * (1 + margin)
    
#     return {
#         'time_hours': time_hours,
#         'cost_per_hour': cost_per_hour,
#         'mano_obra': round(labor_cost, 0),
#         'materiales': materials_ars,
#         'costo_total': round(total_cost, 0),
#         'precio_final': round(final_price, 0),
#         'margen': margin * 100
#     }

# def extraer_monto_numerico(monto_str):
#     """Extrae valor numérico de string de monto"""
#     try:
#         if pd.isna(monto_str):
#             return 0
        
#         monto_clean = str(monto_str).strip()
        
#         # Remover símbolos comunes de moneda
#         monto_clean = re.sub(r'[$€£¥₹₽₩¢]', '', monto_clean)
#         monto_clean = re.sub(r'[^\d.,\-]', '', monto_clean)
        
#         if not monto_clean:
#             return 0
        
#         # Manejar números negativos
#         es_negativo = monto_clean.startswith('-')
#         monto_clean = monto_clean.lstrip('-')
        
#         # Determinar si el último punto/coma son decimales
#         if ',' in monto_clean and '.' in monto_clean:
#             if monto_clean.rfind(',') > monto_clean.rfind('.'):
#                 monto_clean = monto_clean.replace('.', '').replace(',', '.')
#             else:
#                 monto_clean = monto_clean.replace(',', '')
#         elif ',' in monto_clean:
#             if monto_clean.count(',') == 1 and len(monto_clean.split(',')[1]) <= 2:
#                 monto_clean = monto_clean.replace(',', '.')
#             else:
#                 monto_clean = monto_clean.replace(',', '')
        
#         resultado = float(monto_clean)
#         return -resultado if es_negativo else resultado
        
#     except Exception as e:
#         st.warning(f"No se pudo procesar monto '{monto_str}': {e}")
#         return 0

# def normalizar_fecha_flexible(fecha_valor):
#     """Normaliza fechas de múltiples formatos"""
#     try:
#         if pd.isna(fecha_valor):
#             return datetime.now().isoformat()
        
#         fecha_str = str(fecha_valor).strip()
        
#         formatos_fecha = [
#             '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y', '%d.%m.%Y', '%d.%m.%y',
#             '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
#             '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y_%m_%d',
#             '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d-%m-%Y %H:%M:%S', '%d-%m-%Y %H:%M',
#             '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
#             '%d de %B de %Y', '%d %B %Y', '%B %d, %Y', '%d %b %Y',
#         ]
        
#         for formato in formatos_fecha:
#             try:
#                 fecha_parsed = datetime.strptime(fecha_str, formato)
#                 return fecha_parsed.isoformat()
#             except ValueError:
#                 continue
        
#         try:
#             fecha_pandas = pd.to_datetime(fecha_str, dayfirst=True, errors='coerce')
#             if not pd.isna(fecha_pandas):
#                 return fecha_pandas.isoformat()
#         except:
#             pass
        
#         st.warning(f"No se pudo procesar fecha '{fecha_valor}', usando fecha actual")
#         return datetime.now().isoformat()
        
#     except Exception as e:
#         st.warning(f"Error procesando fecha '{fecha_valor}': {e}")
#         return datetime.now().isoformat()

# def show_migration_tool_flexible(data_manager):
#     """Herramienta de migración flexible para cualquier CSV"""
#     st.subheader("📥 Migración Flexible de Datos")
    
#     st.markdown("""
#     **🚀 Migración Universal de CSV**
    
#     Esta herramienta puede trabajar con cualquier archivo CSV:
#     - ✅ Mapea automáticamente las columnas de tu archivo
#     - 🔄 Convierte formatos de fecha y moneda
#     - 💰 Todo en pesos argentinos
#     - 📊 Vista previa antes de migrar
#     """)
    
#     uploaded_file = st.file_uploader(
#         "📁 Sube tu archivo CSV", 
#         type=['csv'],
#         help="Sube cualquier archivo CSV con datos de consultas"
#     )
    
#     if uploaded_file is not None:
#         try:
#             # Detectar encoding
#             encoding_options = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
#             df = None
#             encoding_usado = None
            
#             for encoding in encoding_options:
#                 try:
#                     df = pd.read_csv(uploaded_file, encoding=encoding)
#                     encoding_usado = encoding
#                     break
#                 except UnicodeDecodeError:
#                     continue
            
#             if df is None:
#                 st.error("❌ No se pudo leer el archivo. Verifica el formato.")
#                 return
            
#             st.success(f"✅ Archivo cargado correctamente (encoding: {encoding_usado})")
            
#             # Vista previa del archivo
#             with st.expander("👀 Vista Previa del Archivo", expanded=True):
#                 col1, col2, col3 = st.columns(3)
#                 with col1:
#                     st.metric("📊 Total Registros", len(df))
#                 with col2:
#                     st.metric("📋 Columnas", len(df.columns))
#                 with col3:
#                     st.metric("💾 Tamaño", f"{uploaded_file.size / 1024:.1f} KB")
                
#                 st.markdown("**Primeras 5 filas:**")
#                 st.dataframe(df.head(), use_container_width=True)
                
#                 st.markdown("**Columnas disponibles:**")
#                 st.write(", ".join(df.columns.tolist()))
            
#             # Mapeo de columnas
#             st.subheader("🗺️ Mapeo de Columnas")
#             st.markdown("Indica qué columna de tu CSV corresponde a cada campo:")
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.markdown("**📋 Campos Obligatorios:**")
                
#                 col_paciente = st.selectbox(
#                     "👤 Columna de Pacientes *",
#                     options=['-- Seleccionar --'] + df.columns.tolist()
#                 )
                
#                 col_tratamiento = st.selectbox(
#                     "🦷 Columna de Tratamientos *",
#                     options=['-- Seleccionar --'] + df.columns.tolist()
#                 )
                
#                 col_monto = st.selectbox(
#                     "💰 Columna de Montos (ARS) *",
#                     options=['-- Seleccionar --'] + df.columns.tolist()
#                 )
            
#             with col2:
#                 st.markdown("**📅 Campos Opcionales:**")
                
#                 col_fecha = st.selectbox(
#                     "📅 Columna de Fechas",
#                     options=['-- Usar fecha actual --'] + df.columns.tolist()
#                 )
                
#                 col_medio_pago = st.selectbox(
#                     "💳 Columna de Medio de Pago",
#                     options=['-- Usar "No especificado" --'] + df.columns.tolist()
#                 )
            
#             # Vista previa del mapeo
#             if (col_paciente != '-- Seleccionar --' and 
#                 col_tratamiento != '-- Seleccionar --' and 
#                 col_monto != '-- Seleccionar --'):
                
#                 st.subheader("👁️ Vista Previa del Mapeo")
                
#                 muestra = df.head(5).copy()
#                 preview_data = []
                
#                 for _, row in muestra.iterrows():
#                     if col_fecha == '-- Usar fecha actual --':
#                         fecha_procesada = datetime.now().strftime('%d/%m/%Y')
#                     else:
#                         fecha_raw = row[col_fecha]
#                         fecha_iso = normalizar_fecha_flexible(fecha_raw)
#                         fecha_procesada = datetime.fromisoformat(fecha_iso).strftime('%d/%m/%Y')
                    
#                     monto_raw = row[col_monto]
#                     monto_procesado = extraer_monto_numerico(monto_raw)
                    
#                     if col_medio_pago == '-- Usar "No especificado" --':
#                         medio_pago = "No especificado"
#                     else:
#                         medio_pago = str(row[col_medio_pago]) if pd.notna(row[col_medio_pago]) else "No especificado"
                    
#                     preview_data.append({
#                         'Fecha': fecha_procesada,
#                         'Paciente': str(row[col_paciente]),
#                         'Tratamiento': str(row[col_tratamiento]),
#                         'Monto Original': str(monto_raw),
#                         'Monto ARS': f"${monto_procesado:,.0f}",
#                         'Medio de Pago': medio_pago
#                     })
                
#                 preview_df = pd.DataFrame(preview_data)
#                 st.dataframe(preview_df, use_container_width=True)
                
#                 # Estadísticas pre-migración
#                 col1, col2, col3, col4 = st.columns(4)
                
#                 with col1:
#                     pacientes_unicos = df[col_paciente].nunique()
#                     st.metric("👥 Pacientes Únicos", pacientes_unicos)
                
#                 with col2:
#                     tratamientos_unicos = df[col_tratamiento].nunique()
#                     st.metric("🦷 Tipos de Tratamiento", tratamientos_unicos)
                
#                 with col3:
#                     montos_procesados = df[col_monto].apply(extraer_monto_numerico)
#                     total_estimado = montos_procesados.sum()
#                     st.metric("💰 Total Estimado", f"${total_estimado:,.0f} ARS")
                
#                 with col4:
#                     registros_validos = len(df.dropna(subset=[col_paciente, col_tratamiento, col_monto]))
#                     st.metric("✅ Registros Válidos", registros_validos)
                
#                 # Botón de migración
#                 st.markdown("---")
                
#                 col1, col2 = st.columns([3, 1])
                
#                 with col1:
#                     st.markdown("### 🚀 ¿Todo se ve correcto?")
#                     st.markdown("Revisa la vista previa y las estadísticas antes de proceder.")
                
#                 with col2:
#                     if st.button("🚀 Ejecutar Migración", type="primary", use_container_width=True):
#                         with st.spinner("⏳ Migrando datos..."):
#                             resultado = ejecutar_migracion_flexible(
#                                 df=df,
#                                 col_paciente=col_paciente,
#                                 col_tratamiento=col_tratamiento,
#                                 col_monto=col_monto,
#                                 col_fecha=col_fecha if col_fecha != '-- Usar fecha actual --' else None,
#                                 col_medio_pago=col_medio_pago if col_medio_pago != '-- Usar "No especificado" --' else None,
#                                 data_manager=data_manager
#                             )
                        
#                         if resultado['success']:
#                             st.success("✅ ¡Migración completada exitosamente!")
                            
#                             col1, col2, col3 = st.columns(3)
#                             with col1:
#                                 st.metric("📥 Registros Migrados", resultado['migrados'])
#                             with col2:
#                                 st.metric("❌ Errores", resultado['errores'])
#                             with col3:
#                                 st.metric("💰 Total Migrado", f"${resultado['total_ars']:,.0f} ARS")
                            
#                             if resultado['errores'] > 0:
#                                 st.warning(f"⚠️ {resultado['errores']} registros tuvieron problemas y no se migraron")
                            
#                             st.info("🔄 Recarga la página para ver los datos migrados en el Dashboard")
                            
#                             if st.button("🔄 Recargar Aplicación"):
#                                 st.rerun()
                        
#                         else:
#                             st.error(f"❌ Error en la migración: {resultado['error']}")
            
#             else:
#                 st.info("👆 Por favor selecciona al menos las columnas obligatorias para continuar")
        
#         except Exception as e:
#             st.error(f"❌ Error procesando el archivo: {e}")
    
#     else:
#         st.info("📁 Sube un archivo CSV para comenzar")

# def ejecutar_migracion_flexible(df, col_paciente, col_tratamiento, col_monto, 
#                                col_fecha=None, col_medio_pago=None, data_manager=None):
#     """Ejecuta la migración flexible solo con pesos argentinos"""
    
#     try:
#         consultas_migradas = []
#         errores = 0
#         total_ars = 0
        
#         for index, row in df.iterrows():
#             try:
#                 if col_fecha:
#                     fecha = normalizar_fecha_flexible(row[col_fecha])
#                 else:
#                     fecha = datetime.now().isoformat()
                
#                 paciente = str(row[col_paciente]).strip() if pd.notna(row[col_paciente]) else f'Paciente_{index+1}'
#                 tratamiento = str(row[col_tratamiento]).strip() if pd.notna(row[col_tratamiento]) else 'Consulta'
#                 monto_numerico = extraer_monto_numerico(row[col_monto])
                
#                 if monto_numerico <= 0:
#                     errores += 1
#                     continue
                
#                 if col_medio_pago:
#                     medio_pago = str(row[col_medio_pago]).strip() if pd.notna(row[col_medio_pago]) else 'No especificado'
#                 else:
#                     medio_pago = 'No especificado'
                
#                 consulta = {
#                     'fecha': fecha,
#                     'paciente': paciente,
#                     'tratamiento': tratamiento,
#                     'monto_ars': round(monto_numerico, 0),
#                     'medio_pago': medio_pago
#                 }
                
#                 consultas_migradas.append(consulta)
#                 total_ars += monto_numerico
                
#             except Exception as e:
#                 errores += 1
#                 st.warning(f"Error en fila {index+1}: {e}")
#                 continue
        
#         if consultas_migradas:
#             for consulta in consultas_migradas:
#                 nueva_fila = {
#                     'fecha': consulta['fecha'],
#                     'paciente': consulta['paciente'], 
#                     'tratamiento': consulta['tratamiento'],
#                     'monto_ars': consulta['monto_ars'],
#                     'medio_pago': consulta['medio_pago']
#                 }
                
#                 if data_manager.consultas.empty:
#                     data_manager.consultas = pd.DataFrame([nueva_fila])
#                 else:
#                     data_manager.consultas = pd.concat([data_manager.consultas, pd.DataFrame([nueva_fila])], ignore_index=True)
            
#             data_manager.save_data()
        
#         return {
#             'success': True,
#             'migrados': len(consultas_migradas),
#             'errores': errores,
#             'total_ars': round(total_ars, 0)
#         }
        
#     except Exception as e:
#         return {
#             'success': False,
#             'error': str(e),
#             'migrados': 0,
#             'errores': 0,
#             'total_ars': 0
#         }

# def show_migration_tool(data_manager):
#     """Wrapper para la función de migración flexible"""
#     show_migration_tool_flexible(data_manager)

# def show_dashboard(data_manager, user_info):
#     """Dashboard principal solo en pesos"""
#     st.subheader(f"📊 Dashboard - {user_info.get('nombre', 'Usuario')}")
    
#     resumen = data_manager.get_resumen()
    
#     plan = user_info.get('plan', 'trial')
#     if plan == 'trial':
#         st.info("🎯 Plan de prueba activo. Sus datos son privados y están separados de otros usuarios.")
#     elif plan == 'premium':
#         st.success("⭐ Plan Premium activo. Acceso completo a todas las funcionalidades.")
    
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric(
#             "💰 Ingresos Totales",
#             f"${resumen['ingreso_total']:,.0f} ARS",
#             delta=f"${resumen['ingresos_mes']:,.0f} este mes"
#         )
    
#     with col2:
#         st.metric("👥 Total Consultas", resumen['total_consultas'])
    
#     with col3:
#         st.metric("📊 Promedio/Consulta", f"${resumen['promedio_consulta']:,.0f} ARS")
    
#     with col4:
#         st.metric("🔥 Más Popular", resumen['tratamiento_popular'])
    
#     if not data_manager.consultas.empty:
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.subheader("📈 Ingresos por Mes")
            
#             df_monthly = data_manager.consultas.copy()
#             df_monthly['fecha'] = pd.to_datetime(df_monthly['fecha'])
#             df_monthly['mes'] = df_monthly['fecha'].dt.to_period('M')
#             monthly_income = df_monthly.groupby('mes')['monto_ars'].sum().reset_index()
#             monthly_income['mes'] = monthly_income['mes'].astype(str)
            
#             fig_monthly = px.bar(
#                 monthly_income, 
#                 x='mes', 
#                 y='monto_ars',
#                 title="Ingresos Mensuales (ARS)",
#                 color='monto_ars',
#                 color_continuous_scale='Blues'
#             )
#             fig_monthly.update_layout(showlegend=False)
#             st.plotly_chart(fig_monthly, use_container_width=True)
        
#         with col2:
#             st.subheader("🥧 Tratamientos Realizados")
            
#             tratamientos = data_manager.consultas['tratamiento'].value_counts()
            
#             fig_pie = px.pie(
#                 values=tratamientos.values,
#                 names=tratamientos.index,
#                 title="Distribución de Tratamientos"
#             )
#             st.plotly_chart(fig_pie, use_container_width=True)
        
#         st.subheader("📋 Últimas Consultas")
        
#         recent_consultas = data_manager.consultas.tail(10).copy()
#         if not recent_consultas.empty:
#             recent_consultas['fecha'] = pd.to_datetime(recent_consultas['fecha']).dt.strftime('%d/%m/%Y %H:%M')
#             recent_consultas = recent_consultas[['fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago']]
#             recent_consultas.columns = ['Fecha', 'Paciente', 'Tratamiento', 'Monto (ARS)', 'Medio de Pago']
#             st.dataframe(recent_consultas, use_container_width=True)
    
#     else:
#         st.info("No hay consultas registradas aún. ¡Comience agregando su primera consulta!")

# def show_nueva_consulta(data_manager):
#     """Formulario para nueva consulta solo en pesos"""
#     st.subheader("Registrar Nueva Consulta")
    
#     with st.form("nueva_consulta"):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             paciente = st.text_input("Nombre del Paciente *", placeholder="Ej: Juan Pérez")
#             tratamiento = st.selectbox(
#                 "Tipo de Tratamiento *",
#                 ["Consulta", "Consulta de Urgencia", "Limpieza", "Operatoria Simple", 
#                  "Operatoria Compleja", "Endodoncia Unirradicular", "Endodoncia Multirradicular",
#                  "Placa Estabilizadora", "Provisorio", "Corona Metálica", "Corona de Porcelana",
#                  "Extracción Simple", "Extracción Compleja", "Otro"]
#             )
        
#         with col2:
#             monto_ars = st.number_input("Monto en ARS *", min_value=0.0, step=1000.0, value=30000.0)
#             medio_pago = st.selectbox(
#                 "Medio de Pago *",
#                 ["Efectivo", "Transferencia", "Débito", "Crédito", "Mercado Pago", "Otros"]
#             )
        
#         submitted = st.form_submit_button("Registrar Consulta", type="primary")
        
#         if submitted:
#             if paciente and tratamiento and monto_ars > 0:
#                 try:
#                     nueva_consulta = data_manager.add_consulta(paciente, tratamiento, monto_ars, medio_pago)
#                     st.success(f"Consulta registrada: {paciente} - {tratamiento} - ${monto_ars:,.0f} ARS")
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"Error al registrar consulta: {e}")
#             else:
#                 st.error("Por favor complete todos los campos obligatorios (*)")

# def show_calculadora_precios(data_manager):
#     """Calculadora de precios solo en pesos"""
#     st.subheader("Calculadora de Precios")
    
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         with st.form("calculadora"):
#             st.write("Parámetros del Tratamiento")
            
#             time_hours = st.number_input(
#                 "Tiempo estimado (horas) *", 
#                 min_value=0.1, 
#                 max_value=10.0, 
#                 value=1.0, 
#                 step=0.25
#             )
            
#             materials_ars = st.number_input(
#                 "Costo de materiales (ARS) *", 
#                 min_value=0.0, 
#                 value=5000.0, 
#                 step=500.0
#             )
            
#             tratamiento_calc = st.text_input(
#                 "Nombre del tratamiento (opcional)", 
#                 placeholder="Ej: Operatoria simple"
#             )
            
#             calcular = st.form_submit_button("Calcular Precio", type="primary")
            
#             if calcular:
#                 try:
#                     resultado = calculate_price_optimized(
#                         time_hours, 
#                         materials_ars, 
#                         data_manager.config['costo_por_hora'],
#                         data_manager.config['margen_ganancia']
#                     )
                    
#                     st.session_state.ultimo_calculo = resultado
                    
#                 except Exception as e:
#                     st.error(f"Error en cálculo: {e}")
    
#     with col2:
#         st.write("Configuración Actual")
#         st.metric("Costo por Hora", f"${data_manager.config['costo_por_hora']:,.0f} ARS")
#         st.metric("Margen", f"{data_manager.config['margen_ganancia']*100:.0f}%")
    
#     if hasattr(st.session_state, 'ultimo_calculo'):
#         resultado = st.session_state.ultimo_calculo
        
#         st.markdown("---")
#         st.subheader("Resultado del Cálculo")
        
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric("Mano de Obra", f"${resultado['mano_obra']:,.0f} ARS")
        
#         with col2:
#             st.metric("Materiales", f"${resultado['materiales']:,.0f} ARS")
        
#         with col3:
#             st.metric("Costo Total", f"${resultado['costo_total']:,.0f} ARS")
        
#         with col4:
#             st.metric("Precio Final", f"${resultado['precio_final']:,.0f} ARS")

# def show_configuracion(data_manager):
#     """Configuración del sistema solo en pesos"""
#     st.subheader("Configuración del Sistema")
    
#     with st.form("configuracion"):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.write("Configuración Profesional")
            
#             nuevo_costo = st.number_input(
#                 "Costo por Hora (ARS)",
#                 min_value=1000.0,
#                 value=float(data_manager.config['costo_por_hora']),
#                 step=1000.0
#             )
            
#             nuevo_margen = st.slider(
#                 "Margen de Ganancia (%)",
#                 min_value=10,
#                 max_value=100,
#                 value=int(data_manager.config['margen_ganancia'] * 100),
#                 step=5
#             ) / 100
        
        
#         guardar = st.form_submit_button("Guardar Configuración", type="primary")
        
#         if guardar:
#             data_manager.config.update({
#                 'costo_por_hora': nuevo_costo,
#                 'margen_ganancia': nuevo_margen
# #                'region': nueva_region
#             })
            
#             if data_manager.save_data():
#                 st.success("Configuración guardada exitosamente")
#                 st.rerun()
#             else:
#                 st.error("Error al guardar configuración")

# def show_reportes(data_manager):
#     """Reportes solo en pesos"""
#     st.subheader("Reportes Detallados")
    
#     if data_manager.consultas.empty:
#         st.info("No hay datos suficientes para generar reportes. Agregue algunas consultas primero.")
#         return
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         fecha_inicio = st.date_input("Fecha Inicio", value=date.today().replace(day=1))
    
#     with col2:
#         fecha_fin = st.date_input("Fecha Fin", value=date.today())
    
#     df_filtrado = data_manager.consultas.copy()
#     df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'])
#     df_filtrado = df_filtrado[
#         (df_filtrado['fecha'].dt.date >= fecha_inicio) & 
#         (df_filtrado['fecha'].dt.date <= fecha_fin)
#     ]
    
#     if df_filtrado.empty:
#         st.warning("No hay datos en el rango de fechas seleccionado")
#         return
    
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("Consultas", len(df_filtrado))
    
#     with col2:
#         ingresos_periodo = df_filtrado['monto_ars'].sum()
#         st.metric("Ingresos", f"${ingresos_periodo:,.0f} ARS")
    
#     with col3:
#         promedio_periodo = df_filtrado['monto_ars'].mean()
#         st.metric("Promedio", f"${promedio_periodo:,.0f} ARS")
    
#     with col4:
#         dias_periodo = (fecha_fin - fecha_inicio).days + 1
#         consultas_por_dia = len(df_filtrado) / dias_periodo
#         st.metric("Consultas/Día", f"{consultas_por_dia:.1f}")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.subheader("Evolución Diaria")
        
#         df_diario = df_filtrado.groupby(df_filtrado['fecha'].dt.date).agg({
#             'monto_ars': 'sum',
#             'paciente': 'count'
#         }).reset_index()
#         df_diario.columns = ['fecha', 'ingresos', 'consultas']
        
#         fig_daily = go.Figure()
#         fig_daily.add_trace(go.Scatter(
#             x=df_diario['fecha'],
#             y=df_diario['ingresos'],
#             mode='lines+markers',
#             name='Ingresos ARS',
#             line=dict(color='#3b82f6')
#         ))
        
#         fig_daily.update_layout(
#             title="Ingresos Diarios",
#             xaxis_title="Fecha",
#             yaxis_title="Ingresos (ARS)"
#         )
#         st.plotly_chart(fig_daily, use_container_width=True)
    
#     with col2:
#         st.subheader("Medios de Pago")
        
#         medios_pago = df_filtrado.groupby('medio_pago')['monto_ars'].sum()
        
#         fig_payment = px.pie(
#             values=medios_pago.values,
#             names=medios_pago.index,
#             title="Distribución por Medio de Pago"
#         )
#         st.plotly_chart(fig_payment, use_container_width=True)
    
#     st.subheader("Detalle de Consultas")
    
#     df_display = df_filtrado.copy()
#     df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y %H:%M')
#     df_display = df_display[['fecha', 'paciente', 'tratamiento', 'monto_ars', 'medio_pago']]
#     df_display.columns = ['Fecha', 'Paciente', 'Tratamiento', 'Monto ARS', 'Medio Pago']
    
#     df_display['Monto ARS'] = df_display['Monto ARS'].apply(lambda x: f"${x:,.0f}")
    
#     st.dataframe(df_display, use_container_width=True)
    
#     if st.button("Exportar Reporte a CSV"):
#         csv = df_display.to_csv(index=False, encoding='utf-8-sig')
#         st.download_button(
#             label="Descargar CSV",
#             data=csv,
#             file_name=f"reporte_dental_{fecha_inicio}_{fecha_fin}.csv",
#             mime="text/csv"
#         )

# def show_login():
#     """Pantalla de login"""
#     st.title("Sistema de Gestión de Consultorios Odontológicos - Login")
    
#     with st.expander("Información del Sistema"):
#         st.markdown("""
#         **Sistema de Gestión Dental v2.0**
        
#         **Características:**
#         - Dashboard con métricas en tiempo real
#         - Gestión de consultas y pacientes
#         - Calculadora de precios profesional
#         - Reportes detallados y exportación
#         - Sistema multi-usuario con datos separados
#         - Todo en pesos argentinos
        
#         **Acceso:**
#         - Cada usuario tiene sus propios datos privados
#         - Sistema de autenticación seguro
#         - Datos completamente separados entre usuarios
        
#         **Soporte:**
#         - Para obtener credenciales de acceso, contacte al administrador
#         - Demo disponible para evaluación
#         """)
    
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         with st.form("login_form"):
#             st.write("Ingresar al Sistema")
            
#             username = st.text_input("Usuario", placeholder="Ingrese su usuario")
#             password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            
#             show_demo_hint = st.checkbox("Mostrar usuarios de demo")
            
#             if show_demo_hint:
#                 st.info("""
#                 **Usuarios de prueba disponibles:**
                
#                 **Administrador**: `admin` / `admin123`
#                 **Demo 1**: `demo1` / `demo123`  
#                 **Demo 2**: `demo2` / `demo123`
                
#                 Solo para evaluación del sistema
#                 """)
            
#             login_button = st.form_submit_button("Ingresar", use_container_width=True)
            
#             if login_button:
#                 if username and password:
#                     user_manager = UserManager()
#                     is_valid, message = user_manager.validate_user(username, password)
                    
#                     if is_valid:
#                         st.session_state.authenticated = True
#                         st.session_state.user_id = username
#                         st.session_state.user_info = user_manager.get_user_info(username)
                        
#                         st.success(f"{message}")
#                         st.rerun()
#                     else:
#                         st.error(f"{message}")
#                         if "Usuario no encontrado" in message:
#                             st.info("Tip: Verifique el nombre de usuario. Para demo, active el checkbox superior.")
#                 else:
#                     st.warning("Por favor complete todos los campos")
    
#     st.markdown("---")
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         st.markdown("""
#         <div style='text-align: center; color: #666; font-size: 0.8em;'>
#         ¿Necesita acceso? Contacte al administrador del sistema<br>
#         Sistema seguro - Datos protegidos y privados
#         </div>
#         """, unsafe_allow_html=True)

# def main():
#     if 'authenticated' not in st.session_state or not st.session_state.authenticated:
#         show_login()
#         return
    
#     user_id = st.session_state.user_id
#     user_info = st.session_state.user_info
    
#     col1, col2, col3 = st.columns([3, 1, 1])
    
#     with col1:
#         st.markdown('<h1 class="main-header">Sistema de Gestión de Consultorios Odontológicos v2.0</h1>', unsafe_allow_html=True)
    
#     with col2:
#         st.write(f"{user_info.get('nombre', user_id)}")
    
#     with col3:
#         if st.button("Cerrar Sesión"):
#             for key in list(st.session_state.keys()):
#                 del st.session_state[key]
#             st.rerun()
    
#     if 'data_manager' not in st.session_state:
#         st.session_state.data_manager = DataManager(user_id=user_id)
    
#     data_manager = st.session_state.data_manager
    
#     with st.sidebar:
#         st.markdown("""
#         <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%); border-radius: 0.5rem; margin-bottom: 1rem; color: white;'>
#         <h3>Dental v2.0</h3>
#         <p style='margin: 0; font-size: 0.9em;'>Sistema de Gestión</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         menu = st.selectbox(
#             "Menú Principal",
#             ["🏠 Dashboard", "➕ Nueva Consulta", "💰 Calculadora de Precios", 
#      "⚙️ Configuración", "📈 Reportes", "📥 Migrar Datos"]
#         )
        
#         st.markdown("---")
        
#         resumen = data_manager.get_resumen()
#         st.metric("Ingresos Totales", f"${resumen['ingreso_total']:,.0f} ARS")
#         st.metric("Consultas", resumen['total_consultas'])
#         st.metric("Promedio", f"${resumen['promedio_consulta']:,.0f} ARS")
    
#     if menu == "🏠 Dashboard":
#         show_dashboard(data_manager, user_info)
#     elif menu == "➕ Nueva Consulta":
#         show_nueva_consulta(data_manager)
#     elif menu == "💰 Calculadora de Precios":
#         show_calculadora_precios(data_manager)
#     elif menu == "⚙️ Configuración":
#         show_configuracion(data_manager)
#     elif menu == "⚙️ Reportes":
#         show_reportes(data_manager)
#     elif menu == "📥 Migrar Datos":
#         show_migration_tool(data_manager)

# if __name__ == "__main__":
#     main()