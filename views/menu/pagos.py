"""
Vista para gestionar y visualizar el historial de pagos
"""
import streamlit as st
from models.modelo import Database
from datetime import datetime, timedelta

def mostrar_historial_pagos():
    """Muestra el historial de pagos con opciones de filtrado"""
    st.title("📋 Historial de Pagos")
    
    db = Database()
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtro por rango de fechas (últimos 7 días por defecto)
        fecha_hoy = datetime.now().date()
        fecha_inicio = st.date_input(
            "Fecha de inicio",
            value=fecha_hoy - timedelta(days=7),
            max_value=fecha_hoy
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de fin",
            value=fecha_hoy,
            max_value=fecha_hoy
        )
    
    # Validar fechas
    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio no puede ser posterior a la fecha de fin")
        return
    
    # Obtener historial de pagos
    query = """
    SELECT 
        c.id,
        c.fecha_emision,
        c.tipo_comprobante,
        c.numero_comprobante,
        CONCAT(u.username) as cajero,
        CONCAT(cl.nombres, ' ', cl.apellidos) as cliente
    FROM comprobantes c
    INNER JOIN ventas v on v.id = c.venta_id
    JOIN usuarios u ON v.usuario_id = u.id
    LEFT JOIN clientes cl ON v.cliente_id = cl.id
    WHERE DATE(c.fecha_emision) BETWEEN %s AND %s
    ORDER BY c.fecha_emision DESC
    """
    
    try:
        resultados = db.execute_query(query, (fecha_inicio, fecha_fin))
        
        if not resultados:
            st.info("No se encontraron pagos en el rango de fechas seleccionado.")
            return
        
        # Mostrar resumen
        total_pagos = sum(float(pago[2]) for pago in resultados)
        st.metric("Total de pagos", f"S/ {total_pagos:.2f}")
        
        # Mostrar tabla de pagos
        st.subheader("Detalle de Pagos")
        
        # Crear DataFrame para mostrar en tabla
        import pandas as pd
        df = pd.DataFrame(resultados, columns=[
            'ID', 'Fecha', 'Monto', 'Tipo', 'Serie', 'Número', 'Cajero', 'Cliente'
        ])
        
        # Formatear columnas
        df['Monto'] = df['Monto'].apply(lambda x: f"S/ {x:.2f}")
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.strftime('%d/%m/%Y %H:%M')
        
        # Mostrar tabla con opciones de filtrado
        st.dataframe(
            df,
            column_config={
                "Monto": st.column_config.NumberColumn("Monto", format="S/ %.2f"),
                "Fecha": st.column_config.DatetimeColumn("Fecha", format="DD/MM/YYYY HH:mm")
            },
            hide_index=True,
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"Error al obtener el historial de pagos: {str(e)}")

if __name__ == "__main__":
    mostrar_historial_pagos()
