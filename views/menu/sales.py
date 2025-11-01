import streamlit as st
from models.modelo import Database
from models.comprobantes import GeneradorComprobantes
import json
from datetime import datetime
import base64

def punto_venta():
    st.header("Punto de Venta")
    
    db = Database()
    
    # Inicializar carrito en session_state si no existe
    if 'carrito' not in st.session_state:
        st.session_state['carrito'] = []
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Productos Disponibles")
        medicamentos = db.get_medicamentos()
        
        if medicamentos:
            for med in medicamentos:
                if med['stock'] > 0:  # Solo mostrar productos con stock disponible
                    with st.expander(f"{med['nombre']} - ${med['precio_venta']:.2f} (Stock: {med['stock']})"):
                        st.write(f"**Principio Activo:** {med['principio_activo']}")
                        cantidad = st.number_input("Cantidad", min_value=1, max_value=med['stock'], key=f"cant_{med['id']}")
                        if st.button("Agregar al Carrito", key=f"add_{med['id']}"):
                            # Verificar si el producto ya está en el carrito
                            encontrado = False
                            for item in st.session_state['carrito']:
                                if item['medicamento_id'] == med['id']:
                                    item['cantidad'] += cantidad
                                    encontrado = True
                                    break
                            
                            if not encontrado:
                                st.session_state['carrito'].append({
                                    'medicamento_id': med['id'],
                                    'nombre': med['nombre'],
                                    'precio': float(med['precio_venta']),
                                    'cantidad': cantidad
                                })
                            st.success("Producto agregado al carrito")
                            st.rerun()
            if st.session_state['user']['perfil'] in ['Administrador', 'Farmacéutico']:
                st.button("Mandar a caja", on_click=lambda: st.rerun(), icon="👛")
        else:
            st.info("No hay medicamentos disponibles")
    
    with col2:
        st.subheader("Carrito de Compra")
        
        if st.session_state['carrito']:
            total = 0
            for item in st.session_state['carrito']:
                subtotal = item['precio'] * item['cantidad']
                total += subtotal
                st.write(f"{item['nombre']} x{item['cantidad']} = ${subtotal:.2f}")
            
            st.write(f"**Total: ${total:.2f}**")
            
            #----------------------------------------
            # Información del cliente
            st.subheader("Datos del Cliente")
            cliente_id = st.number_input("ID Cliente (opcional)", min_value=0, value=0)
            
            # Tipo de comprobante
            tipo_comprobante = st.selectbox(
                "Tipo de Comprobante",
                ["Boleta", "Factura"],
                help="Seleccione el tipo de comprobante a emitir"
            )
            
            # Datos adicionales para factura
            cliente_datos = {}
            if tipo_comprobante == "Factura":
                st.write("**Datos para Factura:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    cliente_datos['nombre'] = st.text_input("Razón Social", value="Cliente General")
                    cliente_datos['ruc'] = st.text_input("RUC", max_chars=11)
                with col_b:
                    cliente_datos['direccion'] = st.text_input("Dirección")
            else:
                cliente_datos['nombre'] = st.text_input("Nombre del Cliente", value="Cliente General")
            
            if st.button("Procesar Venta y Emitir Comprobante", type="primary"):
                # Validaciones
                if tipo_comprobante == "Factura" and (not cliente_datos.get('ruc') or len(cliente_datos.get('ruc', '')) != 11):
                    st.error("Para emitir una factura, debe ingresar un RUC válido de 11 dígitos")
                else:
                    detalles = []
                    for item in st.session_state['carrito']:
                        detalles.append({
                            'medicamento_id': item['medicamento_id'],
                            'cantidad': item['cantidad'],
                            'precio': item['precio']
                        })
                    
                    # Procesar venta
                    if db.sp_generar_venta(cliente_id, st.session_state['user']['id'], detalles):
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
                                    subtotal = total / 1.18
                                    igv = total - subtotal
                                    
                                    # Generar factura
                                    pdf_bytes = generador.generar_factura(
                                        venta_id=venta_id,
                                        numero_factura=nuevo_numero,
                                        cliente_datos=cliente_datos,
                                        detalles=detalles_comprobante,
                                        subtotal=subtotal,
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
                                
                            except Exception as e:
                                st.error(f"Error al generar el comprobante: {str(e)}")
                                print(f"Error detallado: {e}")
                        else:
                            st.error("Error: No se pudo obtener el ID de la venta")
                    else:
                        st.error("Error al procesar la venta")
            
            if st.button("Vaciar Carrito"):
                st.session_state['carrito'] = []
                st.rerun()
                #------------------------------------
        else:
            st.info("El carrito está vacío")
