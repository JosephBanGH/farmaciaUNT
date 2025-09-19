import streamlit as st
from database import Database

def registro():
    st.title("Registro de Usuario")

    with st.form("registro_form"):
        username = st.text_input("Usuario")
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")
        confirm_password = st.text_input("Confirmar Contraseña", type="password")
        perfil = st.selectbox("Perfil", ["Administrador", "Farmacéutico", "Cajero", "Cliente"])
        submit = st.form_submit_button("Registrar")

        if submit:
            if not username or not email or not password:
                st.error("Todos los campos son obligatorios ⚠️")
                return

            if password != confirm_password:
                st.error("Las contraseñas no coinciden ❌")
                return

            db = Database()

            # Verificar si ya existe el usuario o email
            existing_user = db.get_usuario_por_username(username)
            if existing_user:
                st.error("El usuario ya existe 🚫")
                return

            try:
                success = db.sp_crear_usuario(username, password, email, perfil)
                if success:
                    st.success(f"Usuario {username} creado con éxito ✅")
                else:
                    st.error("Error al crear el usuario ❌")
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
