"""
Vista para gestionar pagos y procesar ventas
"""
import streamlit as st
from models.modelo import Database
from models.comprobantes import GeneradorComprobantes
from datetime import datetime, timedelta
import base64

def procesar_pago():
    """Interfaz principal para procesar pagos y emitir comprobantes"""
    st.header("💰 Procesar Pago")
    
    db = Database()
    
    # Verificar que hay productos en el carrito
    if 'carrito' not in st.session_state or not st.session_state['carrito']:
        st.warning("⚠️ El carrito está vacío. Por favor, agregue productos desde 'Punto de Venta' primero.")
        st.info("💡 Vaya a la sección 'Punto de Venta' para agregar productos al carrito.")
        return
    
    # Calcular totales
    total = 0
    subtotal = 0
    
    st.markdown("### 🛍️ Resumen de la Compra")
    
    for item in st.session_state['carrito']:
        item_subtotal = item['precio'] * item['cantidad']
        subtotal += item_subtotal
    
    impuesto = subtotal * 0.18
    total = subtotal + impuesto
    
    # Mostrar resumen
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.markdown("""
        **Resumen:**
        - Subtotal:
        - IGV (18%):
        - **Total:**
        """)
    with col_res2:
        st.markdown(f"""
        **&nbsp;**
        - ${subtotal:.2f}
        - ${impuesto:.2f}
        - **${total:.2f}**
        """)
    
    st.divider()
    
    # Verificar interacciones medicamentosas
    medicamento_ids = [item['medicamento_id'] for item in st.session_state['carrito']]
    if len(medicamento_ids) > 1:
        interacciones = db.verificar_interacciones_medicamentosas(medicamento_ids)
        if interacciones:
            st.error("⚠️ **ALERTA: Interacciones Medicamentosas Detectadas**")
            for interaccion in interacciones:
                severidad_color = {
                    'alta': '🟥 CRÍTICO',
                    'media': '🟧 PRECAUCIÓN',
                    'baja': '🟨 MONITOREO'
                }
                st.warning(f"""
                **{interaccion['medicamento1_nombre']}** + **{interaccion['medicamento2_nombre']}**
                
                **Severidad:** {severidad_color.get(interaccion['severidad'], 'Información')}
                **Tipo:** {interaccion['tipo_interaccion'].upper()}
                **Descripción:** {interaccion['descripcion']}
                """)
    
    # Información del cliente
    st.subheader("👤 Información del Cliente")
    
    # Opción de buscar cliente existente o crear uno nuevo
    opcion_cliente = st.radio("Seleccionar cliente:", ["Buscar Cliente", "Cliente General", "Registrar Nuevo Cliente"])
    
    cliente_id = None
    cliente_datos = {}
    
    if opcion_cliente == "Buscar Cliente":
        busqueda_cliente = st.text_input("Buscar por DNI, nombre, email o teléfono:")
        if busqueda_cliente:
            clientes_encontrados = db.buscar_cliente(busqueda_cliente)
            if clientes_encontrados:
                cliente_seleccionado = st.selectbox(
                    "Seleccionar cliente:",
                    options=range(len(clientes_encontrados)),
                    format_func=lambda x: f"{clientes_encontrados[x]['nombre_completo']} - {clientes_encontrados[x]['tipo_documento']}: {clientes_encontrados[x]['numero_documento']}"
                )
                cliente_seleccionado = clientes_encontrados[cliente_seleccionado]
                cliente_id = cliente_seleccionado['id']
                cliente_datos['nombre'] = cliente_seleccionado['nombre_completo']
                
                # Mostrar historial de compras
                if st.checkbox("Mostrar historial de compras"):
                    historial = db.get_historial_cliente(cliente_id, 5)
                    if historial:
                        st.markdown("**Últimas compras:**")
                        for compra in historial:
                            st.caption(f"📅 {compra['fecha_venta']} - ${compra['total']:.2f} ({compra['total_productos']} productos)")
    elif opcion_cliente == "Registrar Nuevo Cliente":
        st.info("Funcionalidad de registro de nuevo cliente en desarrollo")
    
    # Tipo de comprobante
    st.subheader("📄 Tipo de Comprobante")
    tipo_comprobante = st.selectbox(
        "Seleccione el tipo de comprobante:",
        ["Boleta", "Factura"],
        help="Boleta: Consumidor final. Factura: Requiere RUC."
    )
    
    # Datos adicionales para factura
    if tipo_comprobante == "Factura":
        st.write("**Datos para Factura:**")
        col_a, col_b = st.columns(2)
        with col_a:
            cliente_datos['nombre'] = st.text_input("Razón Social")
            cliente_datos['ruc'] = st.text_input("RUC", max_chars=11)
        with col_b:
            cliente_datos['direccion'] = st.text_input("Dirección")
    elif not cliente_id:
        cliente_datos['nombre'] = st.text_input("Nombre del Cliente", value="Cliente General")
    
    # Botones de acción
    col_btn1, col_btn2 = st.columns([1, 1])
    
    with col_btn1:
        if st.button("🗑️ Cancelar y Volver", use_container_width=True):
            st.info("Operación cancelada. El carrito se mantiene intacto.")
    
    with col_btn2:
        if st.button("✅ Procesar Venta y Emitir Comprobante", type="primary", use_container_width=True):
            # Validaciones
            if tipo_comprobante == "Factura" and (not cliente_datos.get('ruc') or len(cliente_datos.get('ruc', '')) != 11):
                st.error("⚠️ Para emitir una factura, debe ingresar un RUC válido de 11 dígitos")
            else:
                # Verificar medicamentos que requieren receta
                medicamentos_receta = [item for item in st.session_state['carrito'] if item.get('requiere_receta')]
                if medicamentos_receta:
                    with st.spinner("Procesando venta..."):
                        confirmar_receta = st.warning(f"⚠️ **ATENCIÓN:** Esta venta incluye {len(medicamentos_receta)} medicamento(s) que requieren receta médica:")
                        for med in medicamentos_receta:
                            st.write(f"- {med['nombre']}")
                        if not st.session_state.get('confirmado_receta', False):
                            st.session_state['mostrar_confirmacion'] = True
                            if st.button("✅ Confirmar que el cliente presenta receta médica", key="confirm_receta", type="primary"):
                                st.session_state['confirmado_receta'] = True
                                st.session_state['mostrar_confirmacion'] = False
                                st.rerun()
                            return
                    
                    st.session_state['confirmado_receta'] = False  # Reset para próxima venta
                
                # Procesar venta
                detalles = []
                for item in st.session_state['carrito']:
                    detalles.append({
                        'medicamento_id': item['medicamento_id'],
                        'cantidad': item['cantidad'],
                        'precio': item['precio']
                    })
                
                try:
                    # Procesar venta
                    if db.sp_generar_venta(cliente_id if cliente_id else None, st.session_state['user']['id'], detalles):
                        # Obtener el ID de la última venta
                        ventas_recientes = db.get_ventas_recientes(1)
                        if ventas_recientes:
                            venta_id = ventas_recientes[0]['id']
                            
                            # Generar comprobante
                            generador = GeneradorComprobantes()
                            
                            # Preparar detalles para el comprobante
                            detalles_comprobante = []
                            for item in st.session_state['carrito']:
                                detalles_comprobante.append({
                                    'nombre': item['nombre'],
                                    'cantidad': item['cantidad'],
                                    'precio': item['precio']
                                })
                            
                            try:
                                if tipo_comprobante == "Boleta":
                                    # Obtener último número de boleta
                                    ultimo_numero = db.get_ultimo_numero_comprobante('boleta')
                                    nuevo_numero = ultimo_numero + 1
                                    
                                    # Generar boleta
                                    pdf_bytes = generador.generar_boleta(
                                        venta_id=venta_id,
                                        numero_boleta=nuevo_numero,
                                        cliente_nombre=cliente_datos.get('nombre', 'Cliente General'),
                                        detalles=detalles_comprobante,
                                        total=total,
                                        fecha=datetime.now()
                                    )
                                    
                                    # Guardar comprobante
                                    ruta_archivo = generador.guardar_comprobante(pdf_bytes, 'B', nuevo_numero)
                                    numero_comprobante = generador.generar_numero_comprobante('B', nuevo_numero)
                                    
                                else:  # Factura
                                    # Obtener último número de factura
                                    ultimo_numero = db.get_ultimo_numero_comprobante('factura')
                                    nuevo_numero = ultimo_numero + 1
                                    
                                    # Calcular IGV
                                    subtotal_igv = subtotal
                                    igv = impuesto
                                    
                                    # Generar factura
                                    pdf_bytes = generador.generar_factura(
                                        venta_id=venta_id,
                                        numero_factura=nuevo_numero,
                                        cliente_datos=cliente_datos,
                                        detalles=detalles_comprobante,
                                        subtotal=subtotal_igv,
                                        igv=igv,
                                        total=total,
                                        fecha=datetime.now()
                                    )
                                    
                                    # Guardar comprobante
                                    ruta_archivo = generador.guardar_comprobante(pdf_bytes, 'F', nuevo_numero)
                                    numero_comprobante = generador.generar_numero_comprobante('F', nuevo_numero)
                                
                                # Registrar comprobante en la base de datos
                                db.registrar_comprobante(
                                    venta_id=venta_id,
                                    tipo_comprobante=tipo_comprobante.lower(),
                                    numero_comprobante=numero_comprobante,
                                    ruta_archivo=ruta_archivo
                                )
                                
                                st.success(f"✅ Venta procesada correctamente. {tipo_comprobante} N° {numero_comprobante} emitida.")
                                
                                # Mostrar botón de descarga
                                with open(ruta_archivo, 'rb') as f:
                                    pdf_data = f.read()
                                    b64 = base64.b64encode(pdf_data).decode()
                                    href = f'<a href="data:application/pdf;base64,{b64}" download="{numero_comprobante}.pdf">📄 Descargar {tipo_comprobante}</a>'
                                    st.markdown(href, unsafe_allow_html=True)
                                
                                # Vaciar carrito
                                st.session_state['carrito'] = []
                                st.session_state['confirmado_receta'] = False
                                
                            except Exception as e:
                                st.error(f"Error al generar el comprobante: {str(e)}")
                                print(f"Error detallado: {e}")
                        else:
                            st.error("Error: No se pudo obtener el ID de la venta")
                    else:
                        st.error("Error al procesar la venta. Verifique el stock disponible.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

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

def pagos_main():
    """Función principal que decide qué mostrar: procesar pago o historial"""
    st.title("📄 Gestión de Pagos")
    # Tabs para separar Procesar Pago y Historial
    tab1, tab2 = st.tabs(["💰 Procesar Pago", "📋 Historial"])
    
    with tab1:
        procesar_pago()
    
    with tab2:
        mostrar_historial_pagos()

if __name__ == "__main__":
    pagos_main()
