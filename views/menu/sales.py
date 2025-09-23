import streamlit as st
from database.database import Database
import json
from datetime import datetime

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
                    with st.expander(f"{med['nombre']} - ${med['precio']:.2f} (Stock: {med['stock']})"):
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
                                    'precio': float(med['precio']),
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
            
            # Información del cliente
            cliente_id = st.number_input("ID Cliente (opcional)", min_value=0, value=0)
            
            if st.button("Procesar Venta"):
                detalles = []
                for item in st.session_state['carrito']:
                    detalles.append({
                        'medicamento_id': item['medicamento_id'],
                        'cantidad': item['cantidad'],
                        'precio': item['precio']
                    })
                
                if db.sp_generar_venta(cliente_id if cliente_id > 0 else None, st.session_state['user']['id'], detalles):
                    st.success("Venta procesada correctamente")
                    st.session_state['carrito'] = []  # Vaciar carrito
                else:
                    st.error("Error al procesar la venta")
            
            if st.button("Vaciar Carrito"):
                st.session_state['carrito'] = []
                st.experimental_rerun()
        else:
            st.info("El carrito está vacío")
