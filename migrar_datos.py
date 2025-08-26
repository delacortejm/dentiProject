import pandas as pd
import json
from datetime import datetime
import re

def migrar_datos_consultorio():
    """Migra datos específicos del CSV de consultorio"""
    
    print("🦷 Iniciando migración de datos del consultorio...")
    
    try:
        # Leer el CSV
        df = pd.read_csv('ingresos.csv')
        
        print(f"📊 Archivo cargado: {len(df)} registros encontrados")
        print(f"📋 Columnas: {list(df.columns)}")
        
        # Configuración por defecto
        config = {
            'costo_por_hora': 21.68,
            'tipo_cambio': 1335,  # Ajustar según fecha actual
            'horas_anuales': 520,
            'margen_ganancia': 0.40,
            'region': 'Interior NOA/NEA',
            'factor_regional': 0.95
        }
        
        consultas_migradas = []
        errores = 0
        
        for index, row in df.iterrows():
            try:
                # Extraer datos de cada fila
                fecha = normalizar_fecha(row['Fecha'])
                paciente = str(row['Paciente']).strip() if pd.notna(row['Paciente']) else f'Paciente_{index}'
                tratamiento = str(row['Tratamiento']).strip() if pd.notna(row['Tratamiento']) else 'Consulta'
                monto_str = str(row['Monto Total']).strip() if pd.notna(row['Monto Total']) else '0'
                medio_pago = str(row['Medio de Pago']).strip() if pd.notna(row['Medio de Pago']) else 'Efectivo'
                
                # Extraer monto numérico (remover $ y ,)
                monto_numerico = extraer_monto(monto_str)
                
                if monto_numerico <= 0:
                    print(f"⚠️ Fila {index+1}: Monto inválido '{monto_str}', saltando...")
                    errores += 1
                    continue
                
                # Determinar moneda basado en el monto (lógica argentina)
                if monto_numerico > 1000:  # Montos >$1000 = ARS
                    monto_ars = monto_numerico
                    monto_usd = monto_numerico / config['tipo_cambio']
                else:  # Montos ≤$1000 = USD
                    monto_usd = monto_numerico
                    monto_ars = monto_numerico * config['tipo_cambio']
                
                consulta = {
                    'fecha': fecha,
                    'paciente': paciente,
                    'tratamiento': tratamiento,
                    'monto_ars': round(monto_ars, 2),
                    'monto_usd': round(monto_usd, 2),
                    'medio_pago': medio_pago
                }
                
                consultas_migradas.append(consulta)
                
                # Log cada 20 registros
                if (index + 1) % 20 == 0:
                    print(f"   Procesados {index + 1}/{len(df)} registros...")
                
            except Exception as e:
                print(f"❌ Error en fila {index+1}: {e}")
                errores += 1
                continue
        
        # Crear estructura de datos final
        datos_finales = {
            'consultas': consultas_migradas,
            'config': config,
            'metadata': {
                'fecha_migracion': datetime.now().isoformat(),
                'archivo_origen': 'ingresos.csv',
                'registros_procesados': len(df),
                'registros_migrados': len(consultas_migradas),
                'errores': errores,
                'rango_fechas': obtener_rango_fechas(consultas_migradas)
            }
        }
        
        # Guardar archivo JSON
        with open('dental_data.json', 'w', encoding='utf-8') as f:
            json.dump(datos_finales, f, ensure_ascii=False, indent=2, default=str)
        
        # Reporte final
        print("\n" + "="*60)
        print("✅ MIGRACIÓN COMPLETADA")
        print(f"📊 Registros originales: {len(df)}")
        print(f"✅ Registros migrados: {len(consultas_migradas)}")
        print(f"❌ Errores: {errores}")
        
        if len(consultas_migradas) > 0:
            print(f"📅 Rango de fechas: {datos_finales['metadata']['rango_fechas']['desde']} - {datos_finales['metadata']['rango_fechas']['hasta']}")
            print(f"💰 Ingreso total: ${sum(c['monto_usd'] for c in consultas_migradas):.2f} USD")
            print(f"📊 Promedio por consulta: ${(sum(c['monto_usd'] for c in consultas_migradas) / len(consultas_migradas)):.2f} USD")
        
        print(f"📁 Archivo generado: dental_data.json")
        print("\n🚀 Ejecuta 'streamlit run app.py' para ver tus datos migrados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error crítico en migración: {e}")
        return False

def normalizar_fecha(fecha_valor):
    """Normaliza diferentes formatos de fecha"""
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
            '%d-%m-%Y %H:%M:%S',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for formato in formatos:
            try:
                fecha_parsed = datetime.strptime(fecha_str, formato)
                return fecha_parsed.isoformat()
            except:
                continue
        
        # Si no funciona ningún formato, intentar con pandas
        try:
            fecha_pandas = pd.to_datetime(fecha_str, dayfirst=True)
            return fecha_pandas.isoformat()
        except:
            pass
        
        print(f"⚠️ No se pudo parsear fecha: '{fecha_valor}', usando fecha actual")
        return datetime.now().isoformat()
        
    except Exception as e:
        print(f"⚠️ Error parseando fecha '{fecha_valor}': {e}")
        return datetime.now().isoformat()

def extraer_monto(monto_str):
    """Extrae el valor numérico de un string de monto"""
    try:
        if pd.isna(monto_str):
            return 0
        
        # Convertir a string y limpiar
        monto_clean = str(monto_str).strip()
        
        # Remover símbolos comunes
        monto_clean = re.sub(r'[$\s,.]', '', monto_clean)
        
        # Si quedó vacío
        if not monto_clean:
            return 0
        
        # Intentar convertir a float
        # Si tiene coma como decimal, reemplazar
        if ',' in monto_clean and monto_clean.count(',') == 1:
            monto_clean = monto_clean.replace(',', '.')
        
        return float(monto_clean)
        
    except Exception as e:
        print(f"⚠️ Error extrayendo monto de '{monto_str}': {e}")
        return 0

def obtener_rango_fechas(consultas):
    """Obtiene el rango de fechas de las consultas"""
    try:
        if not consultas:
            return {'desde': 'N/A', 'hasta': 'N/A'}
        
        fechas = [datetime.fromisoformat(c['fecha']) for c in consultas]
        fecha_min = min(fechas)
        fecha_max = max(fechas)
        
        return {
            'desde': fecha_min.strftime('%d/%m/%Y'),
            'hasta': fecha_max.strftime('%d/%m/%Y')
        }
    except:
        return {'desde': 'N/A', 'hasta': 'N/A'}

def analizar_csv_antes_migracion():
    """Analiza el CSV antes de migrar para detectar problemas"""
    try:
        df = pd.read_csv('Mis finanzas   Consultorio.csv')
        
        print("🔍 ANÁLISIS PREVIO DEL CSV")
        print("=" * 50)
        print(f"📊 Total registros: {len(df)}")
        print(f"📋 Columnas: {list(df.columns)}")
        
        # Analizar cada columna
        for col in df.columns:
            valores_unicos = df[col].nunique()
            valores_nulos = df[col].isna().sum()
            print(f"\n📌 {col}:")
            print(f"   Valores únicos: {valores_unicos}")
            print(f"   Valores nulos: {valores_nulos}")
            
            # Mostrar ejemplos
            ejemplos = df[col].dropna().head(3).tolist()
            print(f"   Ejemplos: {ejemplos}")
        
        # Análisis específico de montos
        print(f"\n💰 ANÁLISIS DE MONTOS:")
        montos_ejemplo = df['Monto Total'].dropna().head(10)
        for i, monto in enumerate(montos_ejemplo):
            monto_numerico = extraer_monto(monto)
            print(f"   {monto} → {monto_numerico}")
        
        # Análisis de fechas
        print(f"\n📅 ANÁLISIS DE FECHAS:")
        fechas_ejemplo = df['Fecha'].dropna().head(5)
        for fecha in fechas_ejemplo:
            fecha_normalizada = normalizar_fecha(fecha)
            print(f"   {fecha} → {fecha_normalizada}")
        
        print("\n" + "="*50)
        print("¿Los datos se ven correctos? (s/n)")
        
    except Exception as e:
        print(f"❌ Error analizando CSV: {e}")

# Ejecución principal
if __name__ == "__main__":
    print("🦷 MIGRADOR DE DATOS DEL CONSULTORIO")
    print("=" * 60)
    
    # Primero analizar
    print("\n1️⃣ Analizando estructura de datos...")
    analizar_csv_antes_migracion()
    
    respuesta = input("\n¿Proceder con la migración? (s/n): ").lower()
    
    if respuesta == 's':
        print("\n2️⃣ Ejecutando migración...")
        if migrar_datos_consultorio():
            print("\n🎉 ¡Listo! Ahora puedes ejecutar 'streamlit run app.py'")
        else:
            print("\n❌ Error en la migración")
    else:
        print("❌ Migración cancelada")