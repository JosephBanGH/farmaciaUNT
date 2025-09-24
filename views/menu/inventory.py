import streamlit as st
from models.modelo import Database
from datetime import datetime

def gestion_inventario():
    st.header("Gestión de Inventario")
    
    db = Database()
    
    # Pestañas para diferentes funcionalidades
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Medicamentos", "Agregar Medicamento", "Actualizar Stock", "Movimientos", "Alertas"])
    
    with tab1:
        st.subheader("Lista de Medicamentos")
        medicamentos = db.get_medicamentos_con_lotes()  # <-- Nuevo método

        if medicamentos:
            for med in medicamentos:
                if med['cantidad_actual'] != None:
                    with st.expander(f"{med['nombre']} - {med['numero_lote']} - Stock: {med['cantidad_actual']}"):
                        st.write(f"**Principio Activo:** {med['principio_activo']}")
                        st.write(f"**Laboratorio:** {med['laboratorio']}")
                        st.write(f"**Precio:** ${med['precio']:.2f}")
                        st.write(f"**Proveedor:** {med['proveedor']}")
                        st.write(f"**Stock Mínimo:** {med['stock_minimo']}")
                        st.write(f"**Lote:** {med['numero_lote']}")
                        st.write(f"**Fecha Vencimiento:** {med['fecha_vencimiento']}")

                        # Botones de acción
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Editar", key=f"edit_{med['lote_id']}"):
                                st.session_state['editar_lote_med'] = med['lote_id']
                        with col2:
                            if st.button("Eliminar", key=f"delete_{med['lote_id']}"):
                                if db.delete_lote_medicamento(med['lote_id']):
                                    st.success("Lote eliminado correctamente")
                                    st.rerun()
                                else:
                                    st.error("Error al eliminar el lote")
        else:
            st.info("No hay medicamentos en el inventario")

    # -------------------------------
    # TAB 2: Agregar Medicamento con Lote
    # -------------------------------
    with tab2:
        st.subheader("Agregar Nuevo Medicamento")
        with st.form("nuevo_medicamento"):
            nombre = st.text_input("Nombre del Medicamento")
            descripcion = st.text_area("Descripción")
            principio_activo = st.text_input("Principio Activo")
            laboratorio = st.text_input("Laboratorio")
            precio = st.number_input("Precio", min_value=0.0, format="%.2f")
            stock_minimo = st.number_input("Stock Mínimo", min_value=0, value=10)

            st.write("### Información del Lote")
            numero_lote = st.text_input("Número de Lote")
            proveedor_id = st.number_input("ID Proveedor", min_value=1)
            stock = st.number_input("Stock Inicial", min_value=0)
            fecha_vencimiento = st.date_input("Fecha de Vencimiento")

            submitted = st.form_submit_button("Guardar Medicamento con Lote")
            if submitted:
                if db.insert_medicamento_con_lote(
                    nombre, descripcion, principio_activo, laboratorio, precio, stock_minimo,
                    numero_lote, proveedor_id, stock, fecha_vencimiento
                ):
                    st.success("Medicamento y lote agregado correctamente")
                else:
                    st.error("Error al agregar medicamento y lote")

    # -------------------------------
    # TAB 3: Actualizar Stock
    # -------------------------------
    with tab3:
        st.subheader("Actualizar Stock por Lote")
        lotes = db.get_lotes_medicamentos()
        if lotes:
            options = {f"{l['nombre']} - {l['numero_lote']} (Stock: {l['cantidad_actual']})": l['id'] for l in lotes}
            selected = st.selectbox("Seleccionar Lote", options=list(options.keys()))
            lote_med_id = options[selected]

            tipo_movimiento = st.radio("Tipo de Movimiento", ["Entrada", "Salida"])
            cantidad = st.number_input("Cantidad", min_value=1)
            motivo = st.text_input("Motivo del movimiento")

            if st.button("Registrar Movimiento"):
                tipo = "entrada" if tipo_movimiento == "Entrada" else "salida"
                if db.sp_actualizar_stock_lote(lote_med_id, cantidad, tipo, motivo, st.session_state['user']['id']):
                    st.success("Movimiento registrado correctamente")
                else:
                    st.error("Error al registrar movimiento")
        else:
            st.info("No hay lotes en el inventario")
    
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
                nombre_med = alerta["medicamento"]
                numero_lote = alerta["numero_lote"]

                if dias_restantes is None:
                    st.warning(f"{nombre_med} - Lote {numero_lote} no tiene fecha de vencimiento registrada.")
                elif dias_restantes < 0:
                    st.error(f"⚠️ {nombre_med} - Lote {numero_lote} VENCIDO el {alerta['fecha_vencimiento']}")
                elif dias_restantes < 7:
                    st.error(f"🚨 {nombre_med} - Lote {numero_lote} vence en {dias_restantes} días")
                elif dias_restantes < 30:
                    st.warning(f"{nombre_med} - Lote {numero_lote} vence en {dias_restantes} días")
                else:
                    st.info(f"{nombre_med} - Lote {numero_lote} vence en {dias_restantes} días")
        else:
            st.success("No hay medicamentos próximos a vencer")
