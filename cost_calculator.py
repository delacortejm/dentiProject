import streamlit as st
import pandas as pd
from datetime import datetime
import json

class CostCalculatorProfessional:
    """
    Calculadora de costos profesional para consultorios odontológicos
    Enfoque contable completo según mejores prácticas
    """
    
    def __init__(self):
        self.setup_default_costs()
    
    def setup_default_costs(self):
        """Configuración por defecto de costos para Argentina 2025"""
        self.default_costs = {
            # COSTOS FIJOS MENSUALES (en USD)
            'fijos': {
                'alquiler_consultorio': 400,  # USD promedio consultorio básico
                'servicios_publicos': 80,     # Luz, gas, agua, internet
                'seguros_profesionales': 50,  # Malpractice + ART
                'amortizacion_equipos': 200,  # Sillón, compresor, autoclave, etc
                'mantenimiento_equipos': 60,  # Service preventivo
                'software_sistemas': 30,      # Software de gestión
                'marketing_basico': 100,      # Presencia digital básica
                'limpieza_mantenimiento': 80, # Personal de limpieza
                'contabilidad_legal': 120,    # Contador + trámites
                'telefono_comunicaciones': 25 # Teléfono fijo + móvil
            },
            
            # COSTOS VARIABLES POR CONSULTA (en USD)
            'variables': {
                'insumos_descartables': 2.5,  # Guantes, baberos, vasos, etc
                'materiales_basicos': 3.0,    # Algodón, gasas, anestesia
                'instrumental_usa': 1.5,      # Agujas, fresas de un uso
                'laboratorio_promedio': 8.0,  # Cuando aplique (30% consultas)
                'radiografias': 2.0,          # Placas/digitales promedio
                'medicamentos': 1.0           # Recetas básicas
            },
            
            # COSTOS PERSONALES MENSUALES (en USD)
            'personales': {
                'sueldo_deseado': 2000,       # Objetivo personal profesional
                'aportes_jubilatorios': 300,  # 15% sobre ingresos brutos aprox
                'obra_social_privada': 80,    # Cobertura médica familiar
                'gastos_capacitacion': 100,   # Cursos, congresos, libros
                'gastos_profesionales': 150,  # Vestimenta, asociaciones, etc
                'reserva_vacaciones': 200,    # 15 días anuales
                'reserva_emergencias': 150    # Fondo contingencia
            },
            
            # PARÁMETROS OPERATIVOS
            'operativos': {
                'dias_trabajo_mes': 22,       # 5.5 días/semana promedio
                'horas_dia_productivas': 6,   # 8 horas - 2 administrativas
                'porcentaje_ocupacion': 0.75, # 75% ocupación realista
                'semanas_vacaciones': 3,      # Vacaciones anuales
                'dias_enfermedad': 5          # Días promedio por enfermedad
            }
        }
    
    def calculate_comprehensive_hourly_cost(self, custom_costs=None):
        """
        Calcula el costo por hora integral considerando todos los factores
        """
        costs = custom_costs if custom_costs else self.default_costs
        
        # 1. COSTOS FIJOS MENSUALES TOTALES
        total_fijos_mes = sum(costs['fijos'].values())
        
        # 2. COSTOS VARIABLES PROMEDIO POR CONSULTA
        costo_variable_consulta = sum(costs['variables'].values())
        
        # 3. COSTOS PERSONALES MENSUALES
        total_personales_mes = sum(costs['personales'].values())
        
        # 4. CALCULAR HORAS PRODUCTIVAS REALES
        dias_mes = costs['operativos']['dias_trabajo_mes']
        horas_dia = costs['operativos']['horas_dia_productivas']
        ocupacion = costs['operativos']['porcentaje_ocupacion']
        
        # Ajustar por vacaciones y enfermedad
        semanas_trabajo_ano = 52 - costs['operativos']['semanas_vacaciones']
        dias_enfermedad_ano = costs['operativos']['dias_enfermedad']
        dias_efectivos_ano = (semanas_trabajo_ano * 5.5) - dias_enfermedad_ano
        dias_efectivos_mes = dias_efectivos_ano / 12
        
        horas_productivas_mes = dias_efectivos_mes * horas_dia * ocupacion
        
        # 5. CALCULAR CONSULTAS PROMEDIO POR MES
        # Asumiendo 1 hora promedio por consulta
        consultas_mes = horas_productivas_mes
        
        # 6. COSTO TOTAL MENSUAL
        costo_total_mes = (
            total_fijos_mes + 
            total_personales_mes + 
            (costo_variable_consulta * consultas_mes)
        )
        
        # 7. COSTO POR HORA
        costo_por_hora = costo_total_mes / horas_productivas_mes
        
        return {
            'costo_por_hora': round(costo_por_hora, 2),
            'costo_total_mensual': round(costo_total_mes, 2),
            'horas_productivas_mes': round(horas_productivas_mes, 1),
            'consultas_estimadas_mes': round(consultas_mes, 0),
            'breakdown': {
                'fijos_mes': round(total_fijos_mes, 2),
                'personales_mes': round(total_personales_mes, 2),
                'variables_mes': round(costo_variable_consulta * consultas_mes, 2),
                'costo_variable_consulta': round(costo_variable_consulta, 2)
            },
            'dias_efectivos_mes': round(dias_efectivos_mes, 1)
        }
    
    def get_recommended_prices(self, costo_por_hora, margenes_objetivo):
        """
        Calcula precios recomendados según diferentes márgenes
        """
        precios = {}
        
        for tratamiento, tiempo_horas in self.tratamientos_tiempo.items():
            precio_base = costo_por_hora * tiempo_horas
            precios[tratamiento] = {}
            
            for margin_name, margin_pct in margenes_objetivo.items():
                precio_final = precio_base * (1 + margin_pct)
                precios[tratamiento][margin_name] = round(precio_final, 2)
        
        return precios
    
    @property
    def tratamientos_tiempo(self):
        """Tiempo promedio por tratamiento en horas"""
        return {
            'Consulta': 0.5,
            'Consulta de Urgencia': 0.75,
            'Limpieza': 1.0,
            'Operatoria Simple': 1.5,
            'Operatoria Compleja': 2.5,
            'Endodoncia Unirradicular': 3.0,
            'Endodoncia Multirradicular': 4.5,
            'Placa Estabilizadora': 2.0,
            'Provisorio': 1.0,
            'Corona Metálica': 3.5,
            'Corona de Porcelana': 4.0,
            'Extracción Simple': 0.75,
            'Extracción Compleja': 2.0
        }

def show_cost_calculator_professional():
    """Interfaz de Streamlit para la calculadora profesional"""
    
    st.title("🧮 Calculadora de Costos Profesional")
    st.markdown("### Enfoque contable integral para consultorios odontológicos")
    
    calculator = CostCalculatorProfessional()
    
    # Pestañas para organizar la interfaz
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Cálculo Rápido", 
        "⚙️ Configuración Detallada", 
        "📈 Precios Recomendados",
        "📋 Análisis Comparativo"
    ])
    
    with tab1:
        st.subheader("🚀 Cálculo con Valores por Defecto")
        st.markdown("*Basado en promedio del sector para Argentina 2025*")
        
        if st.button("🧮 Calcular Costo por Hora", type="primary"):
            resultado = calculator.calculate_comprehensive_hourly_cost()
            
            # Mostrar resultado principal
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "💰 Costo por Hora", 
                    f"${resultado['costo_por_hora']} USD",
                    help="Costo integral considerando todos los factores"
                )
            
            with col2:
                st.metric(
                    "💵 Costo Mensual Total", 
                    f"${resultado['costo_total_mensual']:,.0f} USD",
                    help="Todos los costos mensuales incluidos"
                )
            
            with col3:
                st.metric(
                    "⏰ Horas Productivas/Mes", 
                    f"{resultado['horas_productivas_mes']} hrs",
                    help="Horas reales de atención considerando ocupación"
                )
            
            # Breakdown detallado
            st.subheader("📊 Desglose de Costos")
            
            breakdown_data = {
                'Categoría': ['Costos Fijos', 'Costos Personales', 'Costos Variables'],
                'Monto (USD)': [
                    resultado['breakdown']['fijos_mes'],
                    resultado['breakdown']['personales_mes'],
                    resultado['breakdown']['variables_mes']
                ],
                'Porcentaje': [
                    (resultado['breakdown']['fijos_mes'] / resultado['costo_total_mensual']) * 100,
                    (resultado['breakdown']['personales_mes'] / resultado['costo_total_mensual']) * 100,
                    (resultado['breakdown']['variables_mes'] / resultado['costo_total_mensual']) * 100
                ]
            }
            
            df_breakdown = pd.DataFrame(breakdown_data)
            st.dataframe(df_breakdown, use_container_width=True)
            
            # Métricas operativas
            st.subheader("📈 Métricas Operativas")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("👥 Consultas Estimadas/Mes", f"{resultado['consultas_estimadas_mes']:.0f}")
            
            with col2:
                st.metric("📅 Días Efectivos/Mes", f"{resultado['dias_efectivos_mes']:.1f}")
            
            with col3:
                ingreso_minimo = resultado['costo_total_mensual']
                st.metric("💵 Ingreso Mínimo Necesario", f"${ingreso_minimo:,.0f} USD")
            
            # Alertas y recomendaciones
            st.subheader("🚨 Análisis y Recomendaciones")
            
            if resultado['costo_por_hora'] > 30:
                st.warning("⚠️ Costo por hora elevado. Considere optimizar costos fijos o aumentar eficiencia.")
            elif resultado['costo_por_hora'] < 15:
                st.success("✅ Estructura de costos competitiva para el sector.")
            else:
                st.info("💡 Costo por hora dentro del rango promedio del sector.")
            
            # Precio mínimo recomendado con margen de seguridad
            precio_minimo = resultado['costo_por_hora'] * 1.25  # 25% margen mínimo
            precio_optimo = resultado['costo_por_hora'] * 1.50  # 50% margen óptimo
            
            st.info(f"""
            💡 **Precios Recomendados por Hora:**
            - 🔴 Precio mínimo (25% margen): ${precio_minimo:.2f} USD
            - 🟢 Precio óptimo (50% margen): ${precio_optimo:.2f} USD
            """)
    
    with tab2:
        st.subheader("⚙️ Configuración Personalizada de Costos")
        st.markdown("*Ajuste los valores según su situación específica*")
        
        # Formulario de configuración personalizada
        with st.form("configuracion_costos"):
            
            # COSTOS FIJOS
            st.markdown("#### 🏢 Costos Fijos Mensuales (USD)")
            col1, col2 = st.columns(2)
            
            with col1:
                alquiler = st.number_input("🏠 Alquiler Consultorio", 
                                         value=calculator.default_costs['fijos']['alquiler_consultorio'], 
                                         min_value=0, step=50)
                servicios = st.number_input("⚡ Servicios Públicos", 
                                          value=calculator.default_costs['fijos']['servicios_publicos'], 
                                          min_value=0, step=10)
                seguros = st.number_input("🛡️ Seguros Profesionales", 
                                        value=calculator.default_costs['fijos']['seguros_profesionales'], 
                                        min_value=0, step=10)
                amortizacion = st.number_input("🦷 Amortización Equipos", 
                                             value=calculator.default_costs['fijos']['amortizacion_equipos'], 
                                             min_value=0, step=25)
                mantenimiento = st.number_input("🔧 Mantenimiento", 
                                              value=calculator.default_costs['fijos']['mantenimiento_equipos'], 
                                              min_value=0, step=10)
            
            with col2:
                software = st.number_input("💻 Software/Sistemas", 
                                         value=calculator.default_costs['fijos']['software_sistemas'], 
                                         min_value=0, step=5)
                marketing = st.number_input("📢 Marketing", 
                                          value=calculator.default_costs['fijos']['marketing_basico'], 
                                          min_value=0, step=25)
                limpieza = st.number_input("🧹 Limpieza", 
                                         value=calculator.default_costs['fijos']['limpieza_mantenimiento'], 
                                         min_value=0, step=20)
                contabilidad = st.number_input("📊 Contabilidad/Legal", 
                                             value=calculator.default_costs['fijos']['contabilidad_legal'], 
                                             min_value=0, step=25)
                comunicaciones = st.number_input("📞 Comunicaciones", 
                                                value=calculator.default_costs['fijos']['telefono_comunicaciones'], 
                                                min_value=0, step=5)
            
            # COSTOS PERSONALES
            st.markdown("#### 👤 Costos Personales Mensuales (USD)")
            col1, col2 = st.columns(2)
            
            with col1:
                sueldo_deseado = st.number_input("💰 Sueldo Deseado", 
                                               value=calculator.default_costs['personales']['sueldo_deseado'], 
                                               min_value=500, step=250)
                aportes = st.number_input("🏛️ Aportes Jubilatorios", 
                                        value=calculator.default_costs['personales']['aportes_jubilatorios'], 
                                        min_value=0, step=50)
                obra_social = st.number_input("🏥 Obra Social", 
                                            value=calculator.default_costs['personales']['obra_social_privada'], 
                                            min_value=0, step=20)
            
            with col2:
                capacitacion = st.number_input("📚 Capacitación", 
                                             value=calculator.default_costs['personales']['gastos_capacitacion'], 
                                             min_value=0, step=25)
                gastos_prof = st.number_input("👔 Gastos Profesionales", 
                                            value=calculator.default_costs['personales']['gastos_profesionales'], 
                                            min_value=0, step=25)
                vacaciones = st.number_input("🏖️ Reserva Vacaciones", 
                                           value=calculator.default_costs['personales']['reserva_vacaciones'], 
                                           min_value=0, step=50)
            
            # PARÁMETROS OPERATIVOS
            st.markdown("#### ⚙️ Parámetros Operativos")
            col1, col2 = st.columns(2)
            
            with col1:
                dias_mes = st.number_input("📅 Días Trabajo/Mes", 
                                         value=calculator.default_costs['operativos']['dias_trabajo_mes'], 
                                         min_value=15, max_value=30, step=1)
                horas_dia = st.number_input("⏰ Horas Productivas/Día", 
                                          value=calculator.default_costs['operativos']['horas_dia_productivas'], 
                                          min_value=4, max_value=12, step=1)
            
            with col2:
                ocupacion = st.slider("📊 % Ocupación Promedio", 
                                    min_value=50, max_value=100, 
                                    value=int(calculator.default_costs['operativos']['porcentaje_ocupacion']*100), 
                                    step=5) / 100
                semanas_vacaciones = st.number_input("🏖️ Semanas Vacaciones/Año", 
                                                   value=calculator.default_costs['operativos']['semanas_vacaciones'], 
                                                   min_value=0, max_value=8, step=1)
            
            calcular_personalizado = st.form_submit_button("🧮 Calcular con Configuración Personalizada", type="primary")
            
            if calcular_personalizado:
                # Crear configuración personalizada
                custom_costs = {
                    'fijos': {
                        'alquiler_consultorio': alquiler,
                        'servicios_publicos': servicios,
                        'seguros_profesionales': seguros,
                        'amortizacion_equipos': amortizacion,
                        'mantenimiento_equipos': mantenimiento,
                        'software_sistemas': software,
                        'marketing_basico': marketing,
                        'limpieza_mantenimiento': limpieza,
                        'contabilidad_legal': contabilidad,
                        'telefono_comunicaciones': comunicaciones
                    },
                    'variables': calculator.default_costs['variables'],  # Usar defaults para variables
                    'personales': {
                        'sueldo_deseado': sueldo_deseado,
                        'aportes_jubilatorios': aportes,
                        'obra_social_privada': obra_social,
                        'gastos_capacitacion': capacitacion,
                        'gastos_profesionales': gastos_prof,
                        'reserva_vacaciones': vacaciones,
                        'reserva_emergencias': calculator.default_costs['personales']['reserva_emergencias']
                    },
                    'operativos': {
                        'dias_trabajo_mes': dias_mes,
                        'horas_dia_productivas': horas_dia,
                        'porcentaje_ocupacion': ocupacion,
                        'semanas_vacaciones': semanas_vacaciones,
                        'dias_enfermedad': calculator.default_costs['operativos']['dias_enfermedad']
                    }
                }
                
                # Calcular con configuración personalizada
                resultado_personalizado = calculator.calculate_comprehensive_hourly_cost(custom_costs)
                
                # Mostrar resultados
                st.success("✅ Cálculo completado con su configuración personalizada")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("💰 Su Costo por Hora", f"${resultado_personalizado['costo_por_hora']} USD")
                
                with col2:
                    st.metric("💵 Costo Mensual Total", f"${resultado_personalizado['costo_total_mensual']:,.0f} USD")
                
                with col3:
                    st.metric("⏰ Horas Productivas", f"{resultado_personalizado['horas_productivas_mes']} hrs/mes")
                
                # Comparación con defaults
                resultado_default = calculator.calculate_comprehensive_hourly_cost()
                diferencia = ((resultado_personalizado['costo_por_hora'] / resultado_default['costo_por_hora']) - 1) * 100
                
                if diferencia > 10:
                    st.warning(f"⚠️ Su costo por hora es {diferencia:.1f}% mayor al promedio del sector")
                elif diferencia < -10:
                    st.info(f"💡 Su costo por hora es {abs(diferencia):.1f}% menor al promedio del sector")
                else:
                    st.success(f"✅ Su estructura está alineada con el sector ({diferencia:+.1f}%)")
                
                # Guardar configuración
                if st.button("💾 Guardar Configuración"):
                    try:
                        with open('my_cost_config.json', 'w') as f:
                            json.dump(custom_costs, f, indent=2)
                        st.success("✅ Configuración guardada exitosamente")
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {e}")
    
    with tab3:
        st.subheader("📈 Precios Recomendados por Tratamiento")
        
        # Obtener costo por hora (usar default o configuración personalizada si existe)
        try:
            if os.path.exists('my_cost_config.json'):
                with open('my_cost_config.json', 'r') as f:
                    custom_costs = json.load(f)
                resultado = calculator.calculate_comprehensive_hourly_cost(custom_costs)
                st.info("📁 Usando su configuración personalizada guardada")
            else:
                resultado = calculator.calculate_comprehensive_hourly_cost()
                st.info("📊 Usando configuración por defecto del sector")
        except:
            resultado = calculator.calculate_comprehensive_hourly_cost()
        
        costo_por_hora = resultado['costo_por_hora']
        
        # Definir márgenes objetivo
        margenes = {
            'Supervivencia (15%)': 0.15,
            'Mínimo Sector (25%)': 0.25,
            'Competitivo (40%)': 0.40,
            'Premium (60%)': 0.60,
            'Especialista (80%)': 0.80
        }
        
        # Crear tabla de precios
        precios_data = []
        
        for tratamiento, tiempo_horas in calculator.tratamientos_tiempo.items():
            costo_base = costo_por_hora * tiempo_horas
            
            fila = {
                'Tratamiento': tratamiento,
                'Tiempo (hrs)': tiempo_horas,
                'Costo Base': f"${costo_base:.2f}"
            }
            
            for margin_name, margin_pct in margenes.items():
                precio_final = costo_base * (1 + margin_pct)
                fila[margin_name] = f"${precio_final:.2f}"
            
            precios_data.append(fila)
        
        df_precios = pd.DataFrame(precios_data)
        
        # Mostrar tabla
        st.dataframe(df_precios, use_container_width=True)
        
        # Información adicional
        st.markdown("---")
        st.subheader("💡 Guía de Márgenes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔴 Supervivencia (15%)**
            - Solo cubre costos + mínima ganancia
            - Usar temporalmente o casos sociales
            
            **🟡 Mínimo Sector (25%)**
            - Entrada al mercado
            - Competencia con seguros sociales
            
            **🟢 Competitivo (40%)**
            - Margen estándar recomendado
            - Equilibrio precio-valor
            """)
        
        with col2:
            st.markdown("""
            **🔵 Premium (60%)**
            - Servicios diferenciados
            - Consultorio de alta gama
            
            **🟣 Especialista (80%)**
            - Tratamientos complejos
            - Alta especialización técnica
            """)
        
        # Exportar tabla de precios
        if st.button("📥 Exportar Tabla de Precios"):
            csv = df_precios.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="💾 Descargar CSV",
                data=csv,
                file_name=f"precios_recomendados_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with tab4:
        st.subheader("📋 Análisis Comparativo con Benchmarks")
        
        # Cargar benchmarks (simular datos del sector)
        benchmarks_sector = {
            'Consultorio Básico': {'costo_hora': 18.50, 'margen_promedio': 35},
            'Consultorio Estándar': {'costo_hora': 25.00, 'margen_promedio': 45},
            'Consultorio Premium': {'costo_hora': 35.00, 'margen_promedio': 60},
            'Especialista': {'costo_hora': 45.00, 'margen_promedio': 70}
        }
        
        # Calcular su posición
        resultado_usuario = calculator.calculate_comprehensive_hourly_cost()
        costo_usuario = resultado_usuario['costo_por_hora']
        
        # Crear tabla comparativa
        comparacion_data = []
        for tipo, datos in benchmarks_sector.items():
            diferencia = ((costo_usuario / datos['costo_hora']) - 1) * 100
            comparacion_data.append({
                'Tipo de Consultorio': tipo,
                'Costo/Hora Benchmark': f"${datos['costo_hora']:.2f}",
                'Su Costo/Hora': f"${costo_usuario:.2f}",
                'Diferencia (%)': f"{diferencia:+.1f}%",
                'Margen Típico (%)': f"{datos['margen_promedio']}%"
            })
        
        df_comparacion = pd.DataFrame(comparacion_data)
        st.dataframe(df_comparacion, use_container_width=True)
        
        # Análisis de posicionamiento
        st.subheader("🎯 Su Posicionamiento en el Mercado")
        
        posicion = "Estándar"  # Default
        if costo_usuario < 20:
            posicion = "Básico"
            color = "🟢"
            mensaje = "Estructura de costos competitiva. Buena base para crecimiento."
        elif costo_usuario < 30:
            posicion = "Estándar"
            color = "🔵"
            mensaje = "Posicionamiento equilibrado en el mercado."
        elif costo_usuario < 40:
            posicion = "Premium"
            color = "🟡"
            mensaje = "Estructura de costos elevada. Asegúrese de ofrecer valor diferenciado."
        else:
            posicion = "Especialista"
            color = "🟣"
            mensaje = "Costos de alta especialización. Justifique con servicios únicos."
        
        st.info(f"{color} **Categoría: {posicion}** - {mensaje}")
        
        # Recomendaciones estratégicas
        st.subheader("💡 Recomendaciones Estratégicas")
        
        if posicion == "Básico":
            st.success("""
            ✅ **Ventajas de su posición:**
            - Precios competitivos
            - Margen para crecimiento
            - Atractivo para seguros sociales
            
            🎯 **Estrategias recomendadas:**
            - Enfocarse en volumen de pacientes
            - Optimizar eficiencia operativa
            - Considerar servicios adicionales de bajo costo
            """)
        
        elif posicion == "Premium" or posicion == "Especialista":
            st.warning("""
            ⚠️ **Desafíos de su posición:**
            - Necesita diferenciación clara
            - Marketing más sofisticado
            - Justificar valor agregado
            
            🎯 **Estrategias recomendadas:**
            - Invertir en tecnología avanzada
            - Certificaciones especializadas
            - Experiencia de cliente premium
            - Tratamientos de alta complejidad
            """)
        
        else:  # Estándar
            st.info("""
            💡 **Posición equilibrada:**
            - Balance entre costo y calidad
            - Flexibilidad en estrategias
            - Mercado objetivo amplio
            
            🎯 **Opciones estratégicas:**
            - Optimizar costos para mayor margen
            - Diferenciarse en servicios específicos
            - Crecer en volumen o especialización
            """)

# Función principal para ejecutar la aplicación
if __name__ == "__main__":
    import os
    show_cost_calculator_professional()