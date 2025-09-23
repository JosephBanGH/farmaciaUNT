import streamlit as st
from controladores.database import Database
import datetime

def dashboard():
    st.title("Dashboard - Sistema de Gestión de Farmacias")

    db = Database()

    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)

    total_medicamentos = len(db.get_medicamentos())
    total_stock = sum(med['stock'] for med in db.get_medicamentos())
    medicamentos_bajo_stock = len([m for m in db.get_medicamentos() if m['stock'] <= m['stock_minimo']])
    alertas_vencimiento = len(db.sp_alertas_vencimiento())

    with col1:
        st.metric("Total Medicamentos", total_medicamentos)
    with col2:
        st.metric("Total en Stock", total_stock)
    with col3:
        st.metric("Bajo Stock", medicamentos_bajo_stock, delta_color="inverse")
    with col4:
        st.metric("Próximos a Vencer", alertas_vencimiento, delta_color="inverse")

    # Alertas importantes
    st.subheader("Alertas Importantes")

    if medicamentos_bajo_stock > 0:
        st.warning(f"{medicamentos_bajo_stock} medicamentos tienen stock bajo")

    if alertas_vencimiento > 0:
        st.error(f"{alertas_vencimiento} medicamentos próximos a vencer")

    if medicamentos_bajo_stock == 0 and alertas_vencimiento == 0:
        st.success("No hay alertas importantes")

def reportes_ventas():
    st.header("Reportes de Ventas")
    
    db = Database()
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha Inicio", value=datetime.now().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha Fin", value=datetime.now())
    
    if st.button("Generar Reporte"):
        ventas = db.sp_obtener_reportes_ventas(fecha_inicio, fecha_fin)
        
        if ventas:
            st.subheader(f"Ventas del {fecha_inicio} al {fecha_fin}")
            
            total_ventas = sum(venta['total'] for venta in ventas)
            total_impuestos = sum(venta['impuesto'] for venta in ventas)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Ventas", f"${total_ventas:.2f}")
            with col2:
                st.metric("Total Impuestos", f"${total_impuestos:.2f}")
            
            for venta in ventas:
                with st.expander(f"Venta #{venta['id']} - ${venta['total']:.2f} - {venta['fecha_venta'].strftime('%Y-%m-%d %H:%M')}"):
                    st.write(f"**Vendedor:** {venta['vendedor']}")
                    if venta['cliente']:
                        st.write(f"**Cliente:** {venta['cliente']}")
                    st.write(f"**Total:** ${venta['total']:.2f}")
                    st.write(f"**Impuestos:** ${venta['impuesto']:.2f}")
        else:
            st.info("No hay ventas en el período seleccionado")