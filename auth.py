import streamlit as st
from database import Database

def login():
    st.title("Inicio de Sesión - Sistema de Gestión de Farmacias")
    
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")
        
        if submit:
            db = Database()
            user = db.get_usuario_por_username(username)
            
            if user and db.check_password(password, user['password_hash']):
                st.session_state['logged_in'] = True
                st.session_state['user'] = {
                    'id': user['id'],
                    'username': user['username'],
                    'perfil': user['perfil']
                }
                st.success(f"Bienvenido, {user['username']}!")
                st.rerun()  # ✅ actualizado
            else:
                st.error("Usuario o contraseña incorrectos")
    
    # Opción para recuperar contraseña
    if st.button("¿Olvidaste tu contraseña?"):
        st.info("Por favor contacta al administrador del sistema para restablecer tu contraseña.")

def logout():
    if 'logged_in' in st.session_state:
        del st.session_state['logged_in']
    if 'user' in st.session_state:
        del st.session_state['user']
    st.rerun()  # ✅ actualizado

def show_user_profile():
    if 'user' in st.session_state:
        user = st.session_state['user']
        st.sidebar.write(f"Usuario: {user['username']}")
        st.sidebar.write(f"Perfil: {user['perfil']}")
        if st.sidebar.button("Cerrar Sesión"):
            logout()
