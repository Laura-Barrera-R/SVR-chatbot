import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Optional, Dict, List, Tuple

def closed_events_by_month(df, months: Optional[List[int]] = None, show_chart: bool = True, 
                          chart_type: str = 'bar') -> Tuple[str, Dict]:
    """
    Cuenta eventos CLOSED por mes. Flexible para cualquier mes o rango de meses.
    """
    df = df.copy()
    
    # Convertir fecha
    fecha_col = df['event_start_datetime']
    if pd.api.types.is_numeric_dtype(fecha_col):
        df['event_start_datetime'] = pd.to_datetime(fecha_col, unit='D', origin='1899-12-30')
    else:
        df['event_start_datetime'] = fecha_col.astype(str).str.strip()
        df['event_start_datetime'] = pd.to_datetime(df['event_start_datetime'], errors='coerce')
    
    # Filtrar eventos CLOSED con fecha valida
    mask = (
        (df['event_state'].str.upper() == "CLOSED") &
        (df['event_start_datetime'].notnull())
    )
    df_closed = df[mask].copy()
    
    # Extraer mes
    df_closed['mes'] = df_closed['event_start_datetime'].dt.month
    
    # Filtrar por meses especificos si se proporcionan
    if months:
        df_closed = df_closed[df_closed['mes'].isin(months)]
    
    # Contar por mes
    counts = df_closed.groupby('mes').size().sort_index()
    
    # Mapear nombres de meses
    month_names = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    counts_dict = {month_names.get(k, str(k)): int(v) for k, v in counts.items()}
    
    if show_chart and len(counts) > 0:
        plt.figure(figsize=(10, 6))
        x_labels = [month_names.get(m, str(m)) for m in counts.index]
        
        if chart_type == 'pie':
            plt.pie(counts.values, labels=x_labels, autopct='%1.1f%%', startangle=90)
            plt.title('Distribucion de Eventos CLOSED', fontsize=14)
        elif chart_type == 'line':
            plt.plot(range(len(counts)), counts.values, marker='o', linewidth=2, 
                    markersize=8, color='#4C72B0')
            plt.xticks(range(len(counts)), x_labels, rotation=45, ha='right')
            plt.xlabel('Mes', fontsize=12)
            plt.ylabel('Cantidad de eventos CLOSED', fontsize=12)
            plt.title('Eventos CLOSED por Mes', fontsize=14)
            plt.grid(True, alpha=0.3)
        else:  # bar por defecto
            plt.bar(x_labels, counts.values, color='#4C72B0')
            plt.xlabel('Mes', fontsize=12)
            plt.ylabel('Cantidad de eventos CLOSED', fontsize=12)
            
            if months and len(months) <= 3:
                month_str = ', '.join([month_names.get(m, str(m)) for m in sorted(months)])
                plt.title(f'Eventos CLOSED en {month_str}', fontsize=14)
            else:
                plt.title('Eventos CLOSED por Mes', fontsize=14)
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig('cerrados_por_mes.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        return "Grafico guardado en cerrados_por_mes.png", counts_dict
    elif len(counts) == 0:
        return "No se encontraron eventos CLOSED", {}
    else:
        return "Datos procesados", counts_dict


def events_by_severity(df, severities: Optional[List[str]] = None, show_chart: bool = True, 
                       chart_type: str = 'bar') -> Tuple[str, Dict]:
    """
    Cuenta eventos UNICOS por severidad.
    """
    if severities is None:
        severities = ['WARNING', 'CRITICAL']
    
    severities = [s.upper() for s in severities]
    
    mask = df['event_severity'].str.upper().isin(severities)
    df_filtered = df[mask].copy()
    
    if len(df_filtered) == 0:
        return f"No se encontraron eventos con severidades: {', '.join(severities)}", {}
    
    df_filtered['severity_clean'] = df_filtered['event_severity'].str.upper()
    df_filtered['event_id_str'] = df_filtered['event_id'].astype(str)
    
    df_unique = df_filtered.drop_duplicates(subset=['event_id_str', 'severity_clean'])
    
    counts = df_unique['severity_clean'].value_counts()
    counts = counts.reindex(severities, fill_value=0)
    
    counts_dict = {k: int(v) for k, v in counts.items()}
    
    if show_chart and len(counts) > 0:
        plt.figure(figsize=(8, 6))
        
        colors = {
            'WARNING': '#FFB347',
            'CRITICAL': '#FF6347',
            'MAJOR': '#FF8C00',
            'MINOR': '#FFD700',
            'INFO': '#87CEEB'
        }
        chart_colors = [colors.get(s, '#888888') for s in counts.index]
        
        if chart_type == 'pie':
            plt.pie(counts.values, labels=counts.index, autopct='%1.1f%%', 
                   colors=chart_colors, startangle=90)
            plt.title('Distribucion de Eventos por Severidad', fontsize=14)
        elif chart_type == 'line':
            plt.plot(counts.index, counts.values, marker='o', linewidth=2, 
                    markersize=8, color=chart_colors[0])
            plt.xlabel('Severidad', fontsize=12)
            plt.ylabel('Cantidad de eventos unicos', fontsize=12)
            plt.title('Eventos por Severidad', fontsize=14)
            plt.grid(True, alpha=0.3)
        else:
            plt.bar(counts.index, counts.values, color=chart_colors)
            plt.xlabel('Severidad', fontsize=12)
            plt.ylabel('Cantidad de eventos unicos', fontsize=12)
            plt.title('Eventos por Severidad', fontsize=14)
        
        plt.tight_layout()
        plt.savefig('eventos_por_severidad.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        return "Grafico guardado en eventos_por_severidad.png", counts_dict
    else:
        return "Datos procesados", counts_dict


def open_tickets_by_month(df, months: Optional[List[int]] = None, show_chart: bool = True,
                          chart_type: str = 'bar') -> Tuple[str, Dict]:
    """
    Cuenta eventos OPEN por mes.
    """
    df = df.copy()
    
    fecha_col = df['event_start_datetime']
    if pd.api.types.is_numeric_dtype(fecha_col):
        df['event_start_datetime'] = pd.to_datetime(fecha_col, unit='D', origin='1899-12-30')
    else:
        df['event_start_datetime'] = fecha_col.astype(str).str.strip()
        df['event_start_datetime'] = pd.to_datetime(df['event_start_datetime'], errors='coerce')
    
    mask = (
        (df['event_state'].str.upper() == 'OPEN') &
        (df['event_start_datetime'].notnull())
    )
    df_open = df[mask].copy()
    
    if len(df_open) == 0:
        return "No se encontraron eventos OPEN", {}
    
    df_open['month'] = df_open['event_start_datetime'].dt.month
    
    if months:
        df_open = df_open[df_open['month'].isin(months)]
    
    df_open['event_id_str'] = df_open['event_id'].astype(str)
    df_open_unique = df_open.drop_duplicates(subset=['event_id_str'])
    counts = df_open_unique['month'].value_counts().sort_index()
    
    month_names = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    counts_dict = {month_names.get(k, str(k)): int(v) for k, v in counts.items()}
    
    if show_chart and len(counts) > 0:
        plt.figure(figsize=(10, 6))
        labels = [month_names.get(m, str(m)) for m in counts.index]
        
        if chart_type == 'pie':
            plt.pie(counts.values, labels=labels, autopct='%1.1f%%', startangle=90)
            plt.title('Distribucion de Eventos OPEN por Mes', fontsize=14)
        elif chart_type == 'line':
            plt.plot(range(len(counts)), counts.values, marker='o', linewidth=2, markersize=8)
            plt.xticks(range(len(counts)), labels, rotation=45, ha='right')
            plt.xlabel('Mes', fontsize=12)
            plt.ylabel('Eventos OPEN', fontsize=12)
            plt.title('Eventos OPEN por Mes', fontsize=14)
            plt.grid(True, alpha=0.3)
        else:
            plt.bar(range(len(counts)), counts.values, color='#2E8B57')
            plt.xticks(range(len(counts)), labels, rotation=45, ha='right')
            plt.xlabel('Mes', fontsize=12)
            plt.ylabel('Eventos OPEN', fontsize=12)
            plt.title('Eventos OPEN por Mes', fontsize=14)
        
        plt.tight_layout()
        plt.savefig('tickets_abiertos_por_mes.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        return "Grafico guardado en tickets_abiertos_por_mes.png", counts_dict
    else:
        return "Datos procesados", counts_dict


def events_by_state(df, states: Optional[List[str]] = None, show_chart: bool = True,
                   chart_type: str = 'bar') -> Tuple[str, Dict]:
    """
    Cuenta eventos por estado (OPEN, CLOSED, etc.)
    """
    df = df.copy()
    
    if states:
        states_upper = [s.upper() for s in states]
        mask = df['event_state'].str.upper().isin(states_upper)
        df_filtered = df[mask]
    else:
        df_filtered = df
    
    if len(df_filtered) == 0:
        return "No se encontraron eventos", {}
    
    df_filtered['event_id_str'] = df_filtered['event_id'].astype(str)
    df_unique = df_filtered.drop_duplicates(subset=['event_id_str'])
    
    counts = df_unique['event_state'].str.upper().value_counts()
    counts_dict = {k: int(v) for k, v in counts.items()}
    
    if show_chart and len(counts) > 0:
        plt.figure(figsize=(8, 6))
        
        colors = {'OPEN': '#FF6B6B', 'CLOSED': '#4ECDC4', 'PENDING': '#FFD93D'}
        chart_colors = [colors.get(s, '#95E1D3') for s in counts.index]
        
        if chart_type == 'pie':
            plt.pie(counts.values, labels=counts.index, autopct='%1.1f%%',
                   colors=chart_colors, startangle=90)
            plt.title('Distribucion de Eventos por Estado', fontsize=14)
        else:
            plt.bar(counts.index, counts.values, color=chart_colors)
            plt.xlabel('Estado', fontsize=12)
            plt.ylabel('Cantidad de eventos', fontsize=12)
            plt.title('Eventos por Estado', fontsize=14)
        
        plt.tight_layout()
        plt.savefig('eventos_por_estado.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        return "Grafico guardado en eventos_por_estado.png", counts_dict
    else:
        return "Datos procesados", counts_dict


QUERY_FUNCTIONS = {
    'closed_events_by_month': closed_events_by_month,
    'events_by_severity': events_by_severity,
    'open_tickets_by_month': open_tickets_by_month,
    'events_by_state': events_by_state
}