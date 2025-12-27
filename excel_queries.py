import pandas as pd
import matplotlib.pyplot as plt

def closed_events_oct_nov(df, show_chart=True):
    df = df.copy()
    
    # CAMBIO CLAVE: Usar event_start_datetime en lugar de event_close_datetime
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
    
    # Debug para verificar
    print("\nDEBUG - Eventos CLOSED con fecha de inicio en Oct/Nov:")
    print(df_filtered[['event_start_datetime', 'mes', 'event_state']].to_string())
    
    # Contar por mes
    counts = df_filtered['mes'].value_counts().sort_index()
    
    # Mapear nombres de meses
    month_map = {10: "Octubre", 11: "Noviembre"}
    counts.index = counts.index.map(lambda x: month_map.get(x, str(x)))
    
    print(f"\nConteo final: {counts.to_dict()}")
    
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
    severities = ['WARNING', 'CRITICAL']
    mask = df['event_severity'].str.upper().isin(severities)
    
    # Garantiza orden WARNING, CRITICAL
    counts = df[mask]['event_severity'].str.upper().value_counts().reindex(severities, fill_value=0)
    
    if show_chart:
        plt.figure(figsize=(6,4))
        counts.plot(kind='bar', color=['#FFB347', '#FF6347'])
        plt.xlabel('Severidad')
        plt.ylabel('Cantidad de eventos')
        plt.title('Eventos por Severidad')
        plt.tight_layout()
        plt.savefig('eventos_warning_critical.png')
        plt.close()
        return "Gráfico guardado en eventos_warning_critical.png", counts.to_dict()
    else:
        return counts.to_dict()


def open_tickets_by_month(df, show_chart=True):
    df = df.copy()
    
    # Convertir la columna de fecha de inicio
    fecha_col = df['event_start_datetime']
    
    if pd.api.types.is_numeric_dtype(fecha_col):
        df['event_start_datetime'] = pd.to_datetime(fecha_col, unit='D', origin='1899-12-30')
    else:
        df['event_start_datetime'] = fecha_col.astype(str).str.strip()
        df['event_start_datetime'] = pd.to_datetime(df['event_start_datetime'], errors='coerce')
    
    # Filtrar eventos OPEN
    opened = df[df['event_state'].str.upper() == 'OPEN'].copy()
    opened = opened[opened['event_start_datetime'].notnull()]
    
    # Extraer mes
    opened['month'] = opened['event_start_datetime'].dt.month
    
    # Contar tickets únicos por mes
    counts = opened.groupby('month')['ticket_id'].nunique()
    
    if show_chart:
        plt.figure(figsize=(8,5))
        counts.plot(kind='bar')
        plt.xlabel('Mes')
        plt.ylabel('Tickets abiertos')
        plt.title('Tickets abiertos por mes')
        plt.tight_layout()
        plt.savefig('tickets_abiertos_por_mes.png')
        plt.close()
        return "Gráfico guardado en tickets_abiertos_por_mes.png", counts.to_dict()
    else:
        return counts.to_dict()


QUERY_FUNCTIONS = {
    'closed_events_oct_nov': closed_events_oct_nov,
    'events_by_severity': events_by_severity,
    'open_tickets_by_month': open_tickets_by_month
}