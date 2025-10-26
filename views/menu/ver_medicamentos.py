import streamlit as st
from models.modelo import Database

def ver_medicamentos():
    st.header("Medicamentos")
    db = Database()
    medicamentos = db.get_medicamentos()

    # Buscador por nombre
    search = st.text_input("Buscar medicamento por nombre")
    if search:
        medicamentos = [m for m in medicamentos if search.lower() in m['nombre'].lower()]

    if medicamentos:
        for med in medicamentos:
            with st.container(border=True):
                st.subheader(f"{med['nombre']} (Stock: {med['stock']})")
                st.write(f"**Descripción:** {med['descripcion']}")
                st.write(f"**Principio Activo:** {med['principio_activo']}")
                st.write(f"**Laboratorio:** {med['laboratorio']}")
                st.write(f"**Precio:** ${med['precio']:.2f}")
                st.write(f"**Stock Mínimo:** {med['stock_minimo']}")
                st.write(f"**Fecha de Vencimiento:** {med.get('fecha_vencimiento', 'N/A')}")
    else:
        st.info("No se encontraron medicamentos.")

# Para usar en la app principal:
# ver_medicamentos()
