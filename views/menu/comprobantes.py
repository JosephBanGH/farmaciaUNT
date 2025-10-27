"""
Vista para gestionar y visualizar comprobantes de pago
"""
import streamlit as st
from models.modelo import Database
from models.comprobantes import GeneradorComprobantes
import pandas as pd
from datetime import datetime, timedelta
import base64
import os


def gestionar_comprobantes():
    """Vista principal para gestionar comprobantes"""
    st.title("📄 Gestión de Comprobantes")
    
    db = Database()
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Comprobantes", "🔍 Buscar Comprobante", "📊 Estadísticas"])
    
    with tab1:
        mostrar_lista_comprobantes(db)
    
    with tab2:
        buscar_comprobante(db)
    
    with tab3:
        mostrar_estadisticas(db)


def mostrar_lista_comprobantes(db):
    """Muestra la lista de comprobantes emitidos"""
    st.subheader("Lista de Comprobantes Emitidos")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_filtro = st.selectbox(
            "Tipo de Comprobante",
            ["Todos", "Boleta", "Factura"]
        )
    
    with col2:
        fecha_desde = st.date_input(
            "Desde",
            value=datetime.now() - timedelta(days=30)
        )
    
    with col3:
        fecha_hasta = st.date_input(
            "Hasta",
            value=datetime.now()
        )
    
    # Obtener comprobantes
    comprobantes = db.get_comprobantes(limit=100)
    
    if comprobantes:
        # Filtrar por tipo
        if tipo_filtro != "Todos":
            comprobantes = [c for c in comprobantes if c['tipo_comprobante'].lower() == tipo_filtro.lower()]
        
        # Filtrar por fecha
        comprobantes = [c for c in comprobantes 
                       if fecha_desde <= c['fecha_emision'].date() <= fecha_hasta]
        
        if comprobantes:
            st.info(f"Se encontraron {len(comprobantes)} comprobantes")
            
            # Mostrar en tabla
            for comp in comprobantes:
                with st.expander(
                    f"{comp['tipo_comprobante'].upper()} {comp['numero_comprobante']} - "
                    f"S/ {comp['total']:.2f} - {comp['fecha_emision'].strftime('%d/%m/%Y %H:%M')}"
                ):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Venta ID:** {comp['venta_id']}")
                        st.write(f"**Vendedor:** {comp['vendedor']}")
                        st.write(f"**Fecha:** {comp['fecha_emision'].strftime('%d/%m/%Y %H:%M:%S')}")
                        st.write(f"**Total:** S/ {comp['total']:.2f}")
                    
                    with col_b:
                        st.write(f"**Tipo:** {comp['tipo_comprobante'].upper()}")
                        st.write(f"**Número:** {comp['numero_comprobante']}")
                        
                        # Botón de descarga
                        if os.path.exists(comp['ruta_archivo']):
                            with open(comp['ruta_archivo'], 'rb') as f:
                                pdf_data = f.read()
                                st.download_button(
                                    label="📥 Descargar PDF",
                                    data=pdf_data,
                                    file_name=f"{comp['numero_comprobante']}.pdf",
                                    mime="application/pdf",
                                    key=f"download_{comp['id']}"
                                )
                        else:
                            st.warning("Archivo no encontrado")
                        
                        # Botón para ver detalles de la venta
                        if st.button("Ver Detalles de Venta", key=f"detalles_{comp['id']}"):
                            mostrar_detalles_venta(db, comp['venta_id'])
        else:
            st.warning("No se encontraron comprobantes con los filtros seleccionados")
    else:
        st.info("No hay comprobantes registrados")


def buscar_comprobante(db):
    """Busca un comprobante específico"""
    st.subheader("Buscar Comprobante")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_busqueda = st.selectbox(
            "Buscar por",
            ["Número de Comprobante", "ID de Venta"]
        )
    
    with col2:
        if tipo_busqueda == "Número de Comprobante":
            numero = st.text_input("Número de Comprobante (ej: B001-00000001)")
        else:
            venta_id = st.number_input("ID de Venta", min_value=1, step=1)
    
    if st.button("Buscar"):
        if tipo_busqueda == "Número de Comprobante" and numero:
            # Buscar por número de comprobante
            comprobantes = db.get_comprobantes(limit=1000)
            resultado = [c for c in comprobantes if c['numero_comprobante'] == numero]
            
            if resultado:
                comp = resultado[0]
                mostrar_comprobante_detallado(db, comp)
            else:
                st.error("No se encontró el comprobante")
        
        elif tipo_busqueda == "ID de Venta":
            # Buscar por ID de venta
            comp = db.get_comprobante_por_venta(venta_id)
            
            if comp:
                mostrar_comprobante_detallado(db, comp)
            else:
                st.error("No se encontró comprobante para esta venta")


def mostrar_comprobante_detallado(db, comprobante):
    """Muestra los detalles completos de un comprobante"""
    st.success("✅ Comprobante encontrado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Tipo", comprobante['tipo_comprobante'].upper())
        st.metric("Número", comprobante['numero_comprobante'])
        st.metric("Venta ID", comprobante['venta_id'])
    
    with col2:
        st.metric("Fecha Emisión", comprobante['fecha_emision'].strftime('%d/%m/%Y %H:%M'))
        
        # Obtener total de la venta
        venta = db.get_venta_por_id(comprobante['venta_id'])
        if venta:
            st.metric("Total", f"S/ {venta['total']:.2f}")
    
    # Mostrar detalles de la venta
    st.subheader("Detalles de la Venta")
    mostrar_detalles_venta(db, comprobante['venta_id'])
    
    # Botón de descarga
    if os.path.exists(comprobante['ruta_archivo']):
        with open(comprobante['ruta_archivo'], 'rb') as f:
            pdf_data = f.read()
            st.download_button(
                label="📥 Descargar Comprobante PDF",
                data=pdf_data,
                file_name=f"{comprobante['numero_comprobante']}.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("Archivo PDF no encontrado")


def mostrar_detalles_venta(db, venta_id):
    """Muestra los detalles de una venta"""
    venta = db.get_venta_por_id(venta_id)
    detalles = db.get_detalle_venta(venta_id)
    
    if venta and detalles:
        st.write("**Información de la Venta:**")
        st.write(f"- **Vendedor:** {venta.get('vendedor', 'N/A')}")
        st.write(f"- **Cliente:** {venta.get('cliente', 'Cliente General')}")
        st.write(f"- **Fecha:** {venta['fecha_venta'].strftime('%d/%m/%Y %H:%M:%S')}")
        
        st.write("**Productos:**")
        
        # Crear tabla de productos
        df = pd.DataFrame([{
            'Producto': d['medicamento_nombre'],
            'Cantidad': d['cantidad'],
            'Precio Unit.': f"S/ {d['precio_unitario']:.2f}",
            'Subtotal': f"S/ {d['subtotal']:.2f}"
        } for d in detalles])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.write(f"**Total: S/ {venta['total']:.2f}**")
    else:
        st.error("No se encontraron detalles de la venta")


def mostrar_estadisticas(db):
    """Muestra estadísticas de comprobantes emitidos"""
    st.subheader("📊 Estadísticas de Comprobantes")
    
    # Obtener comprobantes del último mes
    comprobantes = db.get_comprobantes(limit=1000)
    
    if comprobantes:
        # Filtrar último mes
        fecha_limite = datetime.now() - timedelta(days=30)
        comprobantes_mes = [c for c in comprobantes if c['fecha_emision'] >= fecha_limite]
        
        # Contar por tipo
        boletas = len([c for c in comprobantes_mes if c['tipo_comprobante'] == 'boleta'])
        facturas = len([c for c in comprobantes_mes if c['tipo_comprobante'] == 'factura'])
        
        # Calcular totales
        total_boletas = sum([c['total'] for c in comprobantes_mes if c['tipo_comprobante'] == 'boleta'])
        total_facturas = sum([c['total'] for c in comprobantes_mes if c['tipo_comprobante'] == 'factura'])
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Comprobantes", len(comprobantes_mes))
        
        with col2:
            st.metric("Boletas Emitidas", boletas)
        
        with col3:
            st.metric("Facturas Emitidas", facturas)
        
        with col4:
            st.metric("Total Facturado", f"S/ {total_boletas + total_facturas:.2f}")
        
        # Gráfico de distribución
        st.subheader("Distribución por Tipo")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write("**Cantidad de Comprobantes:**")
            st.bar_chart(pd.DataFrame({
                'Tipo': ['Boletas', 'Facturas'],
                'Cantidad': [boletas, facturas]
            }).set_index('Tipo'))
        
        with col_b:
            st.write("**Monto Total:**")
            st.bar_chart(pd.DataFrame({
                'Tipo': ['Boletas', 'Facturas'],
                'Monto': [total_boletas, total_facturas]
            }).set_index('Tipo'))
        
        # Comprobantes recientes
        st.subheader("Últimos 10 Comprobantes")
        df_recientes = pd.DataFrame([{
            'Fecha': c['fecha_emision'].strftime('%d/%m/%Y %H:%M'),
            'Tipo': c['tipo_comprobante'].upper(),
            'Número': c['numero_comprobante'],
            'Total': f"S/ {c['total']:.2f}",
            'Vendedor': c['vendedor']
        } for c in comprobantes_mes[:10]])
        
        st.dataframe(df_recientes, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de comprobantes para mostrar estadísticas")
