import streamlit as st
from database import Database
from datetime import datetime

def gestion_inventario():
    st.header("Gestión de Inventario")
    
    db = Database()
    
    # Pestañas para diferentes funcionalidades
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Medicamentos", "Agregar Medicamento", "Actualizar Stock", "Movimientos", "Alertas"])
    
    with tab1:
        st.subheader("Lista de Medicamentos")
        medicamentos = db.get_medicamentos()
        
        if medicamentos:
            for med in medicamentos:
                with st.expander(f"{med['nombre']} - Stock: {med['stock']}"):
                    st.write(f"**Principio Activo:** {med['principio_activo']}")
                    st.write(f"**Laboratorio:** {med['laboratorio']}")
                    st.write(f"**Precio:** ${med['precio']:.2f}")
                    st.write(f"**Stock Mínimo:** {med['stock_minimo']}")
                    st.write(f"**Lote:** {med['lote']}")
                    if med['fecha_vencimiento']:
                        st.write(f"**Fecha Vencimiento:** {med['fecha_vencimiento']}")
                    
                    # Botones de acción
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Editar", key=f"edit_{med['id']}"):
                            st.session_state['editar_medicamento'] = med['id']
                    with col2:
                        if st.button("Eliminar", key=f"delete_{med['id']}"):
                            if db.delete_medicamento(med['id']):
                                st.success("Medicamento eliminado correctamente")
                                st.experimental_rerun()
                            else:
                                st.error("Error al eliminar el medicamento")
        else:
            st.info("No hay medicamentos en el inventario")
    
    with tab2:
        st.subheader("Agregar Nuevo Medicamento")
        with st.form("nuevo_medicamento"):
            nombre = st.text_input("Nombre del Medicamento")
            descripcion = st.text_area("Descripción")
            principio_activo = st.text_input("Principio Activo")
            laboratorio = st.text_input("Laboratorio")
            col1, col2, col3 = st.columns(3)
            with col1:
                precio = st.number_input("Precio", min_value=0.0, format="%.2f")
            with col2:
                stock = st.number_input("Stock Inicial", min_value=0)
            with col3:
                stock_minimo = st.number_input("Stock Mínimo", min_value=0, value=10)
            lote = st.text_input("Número de Lote")
            fecha_vencimiento = st.date_input("Fecha de Vencimiento")
            
            submitted = st.form_submit_button("Guardar Medicamento")
            if submitted:
                if db.insert_medicamento(nombre, descripcion, principio_activo, laboratorio, precio, stock, stock_minimo, lote, fecha_vencimiento):
                    st.success("Medicamento agregado correctamente")
                    # Registrar movimiento de entrada inicial
                    db.sp_actualizar_stock(
                        db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id'],
                        stock, 
                        'entrada', 
                        'Stock inicial', 
                        st.session_state['user']['id']
                    )
                else:
                    st.error("Error al agregar el medicamento")
    
    with tab3:
        st.subheader("Actualizar Stock")
        medicamentos = db.get_medicamentos()
        if medicamentos:
            medicamento_options = {f"{m['nombre']} (Stock: {m['stock']})": m['id'] for m in medicamentos}
            selected_med = st.selectbox("Seleccionar Medicamento", options=list(medicamento_options.keys()))
            medicamento_id = medicamento_options[selected_med]
            
            col1, col2 = st.columns(2)
            with col1:
                tipo_movimiento = st.radio("Tipo de Movimiento", ["Entrada", "Salida"])
            with col2:
                cantidad = st.number_input("Cantidad", min_value=1)
            
            motivo = st.text_input("Motivo del movimiento")
            
            if st.button("Registrar Movimiento"):
                tipo = "entrada" if tipo_movimiento == "Entrada" else "salida"
                if db.sp_actualizar_stock(medicamento_id, cantidad, tipo, motivo, st.session_state['user']['id']):
                    st.success("Movimiento registrado correctamente")
                else:
                    st.error("Error al registrar el movimiento")
        else:
            st.info("No hay medicamentos en el inventario")
    
    with tab4:
        st.subheader("Historial de Movimientos")
        movimientos = db.get_movimientos_inventario()
        if movimientos:
            for mov in movimientos:
                st.write(f"**{mov['medicamento_nombre']}** - {mov['tipo'].capitalize()} de {mov['cantidad']} unidades")
                st.write(f"Motivo: {mov['motivo']} - Por: {mov['usuario_nombre']}")
                st.write(f"Fecha: {mov['fecha_movimiento'].strftime('%Y-%m-%d %H:%M')}")
                st.divider()
        else:
            st.info("No hay movimientos registrados")
    
    with tab5:
        st.subheader("Alertas de Inventario")
        
        # Alertas de stock bajo
        st.write("### Stock Bajo")
        medicamentos_bajo_stock = [m for m in db.get_medicamentos() if m['stock'] <= m['stock_minimo']]
        if medicamentos_bajo_stock:
            for med in medicamentos_bajo_stock:
                st.warning(f"{med['nombre']} - Stock: {med['stock']} (Mínimo: {med['stock_minimo']})")
        else:
            st.success("No hay medicamentos con stock bajo")
        
        # Alertas de vencimiento
        st.write("### Próximos a Vencer")
        alertas_vencimiento = db.sp_alertas_vencimiento()
        if alertas_vencimiento:
            for alerta in alertas_vencimiento:
                dias_restantes = alerta.get("dias_restantes", None)
        
                if dias_restantes is None:
                    st.warning(f"{alerta['nombre']} - Lote {alerta['lote']} no tiene fecha de vencimiento registrada.")
                elif dias_restantes < 0:
                    st.error(f"⚠️ {alerta['nombre']} - Lote {alerta['lote']} VENCIDO el {alerta['fecha_vencimiento']}")
                elif dias_restantes < 7:
                    st.error(f"🚨 {alerta['nombre']} - Lote {alerta['lote']} vence en {dias_restantes} días")
                elif dias_restantes < 30:
                    st.warning(f"{alerta['nombre']} - Lote {alerta['lote']} vence en {dias_restantes} días")
                else:
                    st.info(f"{alerta['nombre']} - Lote {alerta['lote']} vence en {dias_restantes} días")
        else:
            st.success("No hay medicamentos próximos a vencer")
