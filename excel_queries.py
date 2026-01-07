import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def closed_events_oct_nov(df, show_chart=True):
    df = df.copy()
    
    # Usar event_start_datetime
    fecha_col = df['event_start_datetime']
    
    # Si es numérico (formato Excel), convertir desde el origen de Excel
    if pd.api.types.is_numeric_dtype(fecha_col):
        df['event_start_datetime'] = pd.to_datetime(fecha_col, unit='D', origin='1899-12-30')
    else:
        # Si es string, intentar parsear
        df['event_start_datetime'] = fecha_col.astype(str).str.strip()
        df['event_start_datetime'] = pd.to_datetime(df['event_start_datetime'], errors='coerce')
    
    # Filtrar eventos CLOSED con fecha de inicio válida
    mask = (
        (df['event_state'].str.upper() == "CLOSED") &
        (df['event_start_datetime'].notnull())
    )
    df_closed = df[mask].copy()
    
    # Extraer mes
    df_closed['mes'] = df_closed['event_start_datetime'].dt.month
    
    # Filtrar octubre y noviembre
    df_filtered = df_closed[df_closed['mes'].isin([10, 11])]
    
    # Contar por mes
    counts = df_filtered['mes'].value_counts().sort_index()
    
    # Mapear nombres de meses
    month_map = {10: "Octubre", 11: "Noviembre"}
    counts.index = counts.index.map(lambda x: month_map.get(x, str(x)))
    
    if show_chart:
        plt.figure(figsize=(6,4))
        counts.plot(kind='bar', color='#4C72B0')
        plt.xlabel('Mes')
        plt.ylabel('Cantidad de eventos CLOSED')
        plt.title('Eventos CLOSED en Octubre y Noviembre')
        plt.tight_layout()
        plt.savefig('cerrados_oct_nov.png')
        plt.close()
        return "Gráfico guardado en cerrados_oct_nov.png", counts.to_dict()
    else:
        return counts.to_dict()


def events_by_severity(df, show_chart=True):
    """
    Cuenta eventos ÚNICOS por severidad (WARNING y CRITICAL).
    Usa múltiples columnas para identificar eventos únicos correctamente.
    """
    severities = ['WARNING', 'CRITICAL']
    
    # Filtrar solo WARNING y CRITICAL
    mask = df['event_severity'].str.upper().isin(severities)
    df_filtered = df[mask].copy()
    
    # Normalizar la columna de severidad
    df_filtered['severity_clean'] = df_filtered['event_severity'].str.upper()
    
    # IMPORTANTE: Convertir event_id a string para evitar pérdida de precisión
    df_filtered['event_id_str'] = df_filtered['event_id'].astype(str)
    
    # Eliminar duplicados basados en event_id Y severity
    df_unique = df_filtered.drop_duplicates(subset=['event_id_str', 'severity_clean'])
    
    # Contar eventos únicos por severidad
    counts = df_unique['severity_clean'].value_counts()
    
    # Garantizar orden WARNING, CRITICAL
    counts = counts.reindex(severities, fill_value=0)
    
    if show_chart:
        plt.figure(figsize=(6,4))
        counts.plot(kind='bar', color=['#FFB347', '#FF6347'])
        plt.xlabel('Severidad')
        plt.ylabel('Cantidad de eventos únicos')
        plt.title('Eventos por Severidad')
        plt.tight_layout()
        plt.savefig('eventos_warning_critical.png')
        plt.close()
        return "Gráfico guardado en eventos_warning_critical.png", counts.to_dict()
    else:
        return counts.to_dict()


def open_tickets_by_month(df, show_chart=True):
    """
    Cuenta eventos OPEN por mes basándose en event_start_datetime.
    Similar a la lógica de closed_events_oct_nov pero para OPEN y todos los meses.
    """
    df = df.copy()
    
    # Convertir la columna de fecha de inicio
    fecha_col = df['event_start_datetime']
    
    if pd.api.types.is_numeric_dtype(fecha_col):
        df['event_start_datetime'] = pd.to_datetime(fecha_col, unit='D', origin='1899-12-30')
    else:
        df['event_start_datetime'] = fecha_col.astype(str).str.strip()
        df['event_start_datetime'] = pd.to_datetime(df['event_start_datetime'], errors='coerce')
    
    # Filtrar eventos OPEN con fecha válida
    mask = (
        (df['event_state'].str.upper() == 'OPEN') &
        (df['event_start_datetime'].notnull())
    )
    df_open = df[mask].copy()
    
    # Extraer mes
    df_open['month'] = df_open['event_start_datetime'].dt.month
    
    # Contar eventos OPEN por mes (no duplicados de event_id)
    # Primero eliminamos duplicados de event_id para contar eventos únicos
    df_open['event_id_str'] = df_open['event_id'].astype(str)
    df_open_unique = df_open.drop_duplicates(subset=['event_id_str'])
    
    # Contar eventos únicos por mes
    counts = df_open_unique['month'].value_counts().sort_index()
    
    # Mapear nombres de meses en español
    month_names = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    if show_chart:
        plt.figure(figsize=(10, 5))
        
        # Crear etiquetas con nombres de mes
        labels = [month_names.get(m, str(m)) for m in counts.index]
        
        plt.bar(range(len(counts)), counts.values, color='#2E8B57')
        plt.xlabel('Mes')
        plt.ylabel('Eventos OPEN')
        plt.title('Eventos OPEN por Mes')
        plt.xticks(range(len(counts)), labels, rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('tickets_abiertos_por_mes.png')
        plt.close()
        
        # Retornar con nombres de mes en el diccionario
        counts_dict = {month_names.get(k, str(k)): v for k, v in counts.to_dict().items()}
        return "Gráfico guardado en tickets_abiertos_por_mes.png", counts_dict
    else:
        counts_dict = {month_names.get(k, str(k)): v for k, v in counts.to_dict().items()}
        return counts_dict


QUERY_FUNCTIONS = {
    'closed_events_oct_nov': closed_events_oct_nov,
    'events_by_severity': events_by_severity,
    'open_tickets_by_month': open_tickets_by_month
}