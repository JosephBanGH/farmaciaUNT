# HU9: Gestión de Reportes de Ventas
# Sistema de Gestión de Farmacias - Sprint 2
# Implementación completa con gráficos interactivos y exportación

import streamlit as st
from models.modelo import Database
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

def dashboard():
    """Dashboard principal con métricas generales"""
    st.title("📊 Dashboard - Sistema de Gestión de Farmacias")
    db = Database()
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
    st.subheader("⚠️ Alertas Importantes")
    if medicamentos_bajo_stock > 0:
        st.warning(f"🔴 {medicamentos_bajo_stock} medicamentos tienen stock bajo")
    if alertas_vencimiento > 0:
        st.error(f"⏰ {alertas_vencimiento} medicamentos próximos a vencer")
    if medicamentos_bajo_stock == 0 and alertas_vencimiento == 0:
        st.success("✅ No hay alertas importantes")

def reportes_ventas():
    """Módulo principal de reportes - HU9"""
    st.title("📈 Gestión de Reportes de Ventas")
    if st.session_state.get('user', {}).get('perfil') != 'Administrador':
        st.error("⛔ Acceso denegado. Solo administradores.")
        return
    db = Database()
    st.markdown("---")
    tipo_reporte = st.selectbox("🔍 Tipo de Reporte", ["Ventas", "Stock", "Medicamentos", "Financiero"])
    st.markdown("---")
    if tipo_reporte == "Ventas":
        reporte_ventas(db)
    elif tipo_reporte == "Stock":
        reporte_stock(db)
    elif tipo_reporte == "Medicamentos":
        reporte_medicamentos(db)
    elif tipo_reporte == "Financiero":
        reporte_financiero(db)

def reporte_ventas(db):
    """Reporte detallado de ventas con gráficos"""
    st.subheader("💰 Reporte de Ventas")
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha Inicio", value=datetime.now().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha Fin", value=datetime.now())
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha inicial debe ser menor o igual a la final")
        return
    if st.button("🔄 Generar Reporte", type="primary"):
        resumen = db.get_resumen_ventas(fecha_inicio, fecha_fin)
        if not resumen or resumen['total_transacciones'] == 0:
            st.info("ℹ️ No hay ventas en el período seleccionado")
            return
        st.markdown("### 📊 Resumen Ejecutivo")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Ventas", f"S/. {resumen['total_ventas']:.2f}")
        with col2:
            st.metric("Transacciones", f"{resumen['total_transacciones']}")
        with col3:
            st.metric("Ticket Promedio", f"S/. {resumen['ticket_promedio']:.2f}")
        with col4:
            st.metric("Impuestos", f"S/. {resumen['total_impuestos']:.2f}")
        ventas_dia = db.get_ventas_por_dia(fecha_inicio, fecha_fin)
        if ventas_dia:
            df_ventas = pd.DataFrame(ventas_dia)
            fig = px.line(df_ventas, x='fecha', y='total_vendido', title='Ventas por Día',
                         labels={'fecha': 'Fecha', 'total_vendido': 'Total (S/.)'}, markers=True)
            st.plotly_chart(fig, use_container_width=True)
        productos_top = db.get_productos_mas_vendidos(fecha_inicio, fecha_fin, 10)
        if productos_top:
            st.markdown("### 🏆 Top 10 Productos Más Vendidos")
            df_top = pd.DataFrame(productos_top)
            fig2 = px.bar(df_top, x='nombre', y='cantidad_vendida', title='Productos Más Vendidos',
                         labels={'nombre': 'Producto', 'cantidad_vendida': 'Cantidad'})
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df_top, use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Exportar CSV"):
                    csv = df_top.to_csv(index=False).encode('utf-8')
                    st.download_button("Descargar CSV", csv, "reporte_ventas.csv", "text/csv")
            with col2:
                if st.button("📄 Exportar PDF"):
                    pdf = generar_pdf_ventas(resumen, productos_top, fecha_inicio, fecha_fin)
                    st.download_button("Descargar PDF", pdf, "reporte_ventas.pdf", "application/pdf")
        ventas_farm = db.get_ventas_por_farmaceutico(fecha_inicio, fecha_fin)
        if ventas_farm:
            st.markdown("### 👥 Ventas por Farmacéutico")
            df_farm = pd.DataFrame(ventas_farm)
            fig3 = px.pie(df_farm, values='total_vendido', names='farmaceutico', title='Distribución de Ventas')
            st.plotly_chart(fig3, use_container_width=True)

def reporte_stock(db):
    """Reporte de movimientos de stock y alertas"""
    st.subheader("📦 Reporte de Stock")
    tab1, tab2, tab3 = st.tabs(["Alertas", "Movimientos", "Próximos a Vencer"])
    with tab1:
        st.markdown("### ⚠️ Productos con Stock Bajo")
        productos_bajo = db.get_productos_bajo_stock()
        if productos_bajo:
            df_bajo = pd.DataFrame(productos_bajo)
            for _, row in df_bajo.iterrows():
                color = "🔴" if row['nivel_alerta'] == 'CRÍTICO' else "🟡" if row['nivel_alerta'] == 'MUY BAJO' else "🟠"
                st.warning(f"{color} **{row['nombre']}** - Stock: {row['stock']} | Mínimo: {row['stock_minimo']} | Nivel: {row['nivel_alerta']}")
            st.dataframe(df_bajo, use_container_width=True)
            if st.button("📥 Exportar Alertas CSV"):
                csv = df_bajo.to_csv(index=False).encode('utf-8')
                st.download_button("Descargar", csv, "alertas_stock.csv", "text/csv")
        else:
            st.success("✅ No hay productos con stock bajo")
    with tab2:
        st.markdown("### 📋 Movimientos de Inventario")
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Desde", value=datetime.now() - timedelta(days=30), key="mov_inicio")
        with col2:
            fecha_fin = st.date_input("Hasta", value=datetime.now(), key="mov_fin")
        tipo_mov = st.selectbox("Tipo", ["Todos", "entrada", "salida", "ajuste", "devolucion", "perdida"])
        movimientos = db.get_movimientos_inventario_filtrado(
            fecha_inicio, fecha_fin, None if tipo_mov == "Todos" else tipo_mov
        )
        if movimientos:
            df_mov = pd.DataFrame(movimientos)
            st.dataframe(df_mov, use_container_width=True)
            fig = px.histogram(df_mov, x='tipo', title='Movimientos por Tipo')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay movimientos en el período")
    with tab3:
        st.markdown("### ⏰ Medicamentos Próximos a Vencer (30 días)")
        alertas = db.sp_alertas_vencimiento()
        if alertas:
            df_alertas = pd.DataFrame(alertas)
            st.dataframe(df_alertas, use_container_width=True)
            if st.button("📥 Exportar Vencimientos CSV"):
                csv = df_alertas.to_csv(index=False).encode('utf-8')
                st.download_button("Descargar", csv, "medicamentos_vencer.csv", "text/csv")
        else:
            st.success("✅ No hay medicamentos próximos a vencer")

def reporte_medicamentos(db):
    """Reporte de medicamentos y análisis"""
    st.subheader("💊 Reporte de Medicamentos")
    medicamentos = db.get_medicamentos()
    if medicamentos:
        df_med = pd.DataFrame(medicamentos)
        st.markdown(f"### Total de Medicamentos: {len(df_med)}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Stock Total", f"{df_med['stock'].sum()}")
        with col2:
            st.metric("Valor Inventario", f"S/. {(df_med['precio_venta'] * df_med['stock']).sum():.2f}")
        with col3:
            st.metric("Precio Promedio", f"S/. {df_med['precio_venta'].mean():.2f}")
        st.dataframe(df_med[['nombre', 'laboratorio', 'stock', 'stock_minimo', 'precio_venta']], use_container_width=True)
        fig = px.scatter(df_med, x='stock', y='precio_venta', hover_data=['nombre'], 
                        title='Relación Stock vs Precio', labels={'stock': 'Stock', 'precio_venta': 'Precio (S/.)'})
        st.plotly_chart(fig, use_container_width=True)
        if st.button("📥 Exportar Medicamentos CSV"):
            csv = df_med.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar", csv, "medicamentos.csv", "text/csv")

def reporte_financiero(db):
    """Reporte financiero consolidado"""
    st.subheader("💵 Reporte Financiero")
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Desde", value=datetime.now().replace(day=1), key="fin_inicio")
    with col2:
        fecha_fin = st.date_input("Hasta", value=datetime.now(), key="fin_fin")
    if st.button("🔄 Generar Reporte Financiero", type="primary"):
        resumen = db.get_resumen_ventas(fecha_inicio, fecha_fin)
        if resumen and resumen['total_transacciones'] > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Ingresos Totales", f"S/. {resumen['total_ventas']:.2f}")
                st.metric("Venta Mínima", f"S/. {resumen['venta_minima']:.2f}")
            with col2:
                st.metric("Impuestos", f"S/. {resumen['total_impuestos']:.2f}")
                st.metric("Venta Máxima", f"S/. {resumen['venta_maxima']:.2f}")
            with col3:
                st.metric("Descuentos", f"S/. {resumen['total_descuentos']:.2f}")
                st.metric("Ticket Promedio", f"S/. {resumen['ticket_promedio']:.2f}")
            ventas_dia = db.get_ventas_por_dia(fecha_inicio, fecha_fin)
            if ventas_dia:
                df = pd.DataFrame(ventas_dia)
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df['fecha'], y=df['total_vendido'], name='Ventas'))
                fig.update_layout(title='Evolución de Ventas', xaxis_title='Fecha', yaxis_title='Total (S/.)')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos financieros en el período")

def generar_pdf_ventas(resumen, productos, fecha_inicio, fecha_fin):
    """Genera PDF del reporte de ventas"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elementos = []
    estilos = getSampleStyleSheet()
    titulo = Paragraph(f"<b>Reporte de Ventas</b><br/>{fecha_inicio} al {fecha_fin}", estilos['Title'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 0.3*inch))
    datos_resumen = [
        ['Métrica', 'Valor'],
        ['Total Ventas', f"S/. {resumen['total_ventas']:.2f}"],
        ['Transacciones', str(resumen['total_transacciones'])],
        ['Ticket Promedio', f"S/. {resumen['ticket_promedio']:.2f}"],
        ['Impuestos', f"S/. {resumen['total_impuestos']:.2f}"]
    ]
    tabla_resumen = Table(datos_resumen)
    tabla_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 0.3*inch))
    if productos:
        elementos.append(Paragraph("<b>Top Productos</b>", estilos['Heading2']))
        datos_prod = [['Producto', 'Cantidad', 'Total']]
        for p in productos[:5]:
            datos_prod.append([p['nombre'], str(p['cantidad_vendida']), f"S/. {p['total_vendido']:.2f}"])
        tabla_prod = Table(datos_prod)
        tabla_prod.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elementos.append(tabla_prod)
    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()