import streamlit as st
from user.auth import logout
from database.database import Database

def perfil():
    st.header("Perfil de Usuario")
    st.write(f"**Nombre:** {st.session_state['user']['username']}")
    db = Database()
    usuario = db.get_usuario_por_username(st.session_state['user']['username'])
    st.write(f"**Email:** {usuario['email']}")
    st.write(f"**Perfil:** {usuario['perfil']}")

    st.subheader("Actualizar Información")
    with st.form("registro_form"):
        username = st.text_input("Usuario", value=usuario['username'])
        email = st.text_input("Correo", value=usuario['email'])
        password = st.text_input("Contraseña", type="password")
        perfil = st.selectbox("Perfil", ["Administrador", "Farmacéutico", "Cajero", "Cliente"], index=["Administrador", "Farmacéutico", "Cajero", "Cliente"].index(st.session_state['user']['perfil']))
        submit = st.form_submit_button("Actualizar")

        if submit:
            if not username or not email or not password:
                st.error("Todos los campos son obligatorios ⚠️")
                return

            if perfil is "Administrador" and st.session_state['user']['perfil'] != "Administrador":
                st.error("No puedes cambiar tu propio perfil a Administrador ❌")
                return

            try:
                success = db.sp_actualizar_usuario(username, email, perfil)
                if success:
                    st.success(f"Usuario {username} actualizado con éxito ✅")
                else:
                    st.error("Error al actualizar el usuario ❌")
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")


    if st.button("Cerrar Sesión"):
        logout()

def administracion():
    st.title("Administración del Sistema")
    
    # Solo administradores pueden acceder a esta sección
    if st.session_state['user']['perfil'] != 'Administrador':
        st.warning("No tienes permisos para acceder a esta sección")
        return
    
    tab1, tab2, tab3 = st.tabs(["Usuarios", "Proveedores", "Configuración"])
    
    with tab1:
        st.subheader("Gestión de Usuarios")
        db = Database()
        
        with st.form("nuevo_usuario"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_usuario = st.text_input("Nombre de usuario")
                email = st.text_input("Email")
            with col2:
                nueva_contrasena = st.text_input("Contraseña", type="password")
                perfil = st.selectbox("Perfil", ["Administrador", "Farmacéutico", "Cajero", "Cliente"])
            
            if st.form_submit_button("Crear Usuario"):
                if db.sp_crear_usuario(nuevo_usuario, nueva_contrasena, email, perfil):
                    st.success("Usuario creado correctamente")
                else:
                    st.error("Error al crear el usuario")
        
        st.subheader("Usuarios Existentes")
        usuarios = db.execute_query("SELECT * FROM usuarios WHERE activo = TRUE ORDER BY username")
        for usuario in usuarios:
            st.write(f"**{usuario['username']}** - {usuario['perfil']} - {usuario['email']}")
    
    with tab2:
        st.subheader("Gestión de Proveedores")
        db = Database()
        proveedores = db.get_proveedores()
        
        if proveedores:
            for prov in proveedores:
                with st.expander(prov['nombre']):
                    st.write(f"**Contacto:** {prov['contacto']}")
                    st.write(f"**Teléfono:** {prov['telefono']}")
                    st.write(f"**Email:** {prov['email']}")
                    st.write(f"**Dirección:** {prov['direccion']}")
        else:
            st.info("No hay proveedores registrados")
    
    with tab3:
        st.subheader("Configuración del Sistema")
        st.info("Aquí puedes configurar parámetros generales del sistema")