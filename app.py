import streamlit as st
from streamlit_option_menu import option_menu
from auth import login, show_user_profile, logout
from inventory import gestion_inventario
from sales import punto_venta, reportes_ventas
from database import Database
from registro import registro   # 👈 importar el registro

def main():
    # Configuración de la página
    st.set_page_config(
        page_title="Sistema de Gestión de Farmacias",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Verificar si el usuario está autenticado
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        # Mostrar opciones de Login y Registro
        menu = st.sidebar.radio("Acceso", ["Iniciar Sesión", "Registrarse"])

        if menu == "Iniciar Sesión":
            login()
        elif menu == "Registrarse":
            registro()
        return
    
    # Mostrar perfil de usuario en sidebar
    show_user_profile()
    
    # Navegación principal
    with st.sidebar:
        selected = option_menu(
            menu_title="Menú Principal",
            options=["Dashboard", "Inventario", "Punto de Venta", "Reportes", "Administración"],
            icons=["house", "box", "cash-coin", "graph-up", "gear"],
            default_index=0,
        )
    
    # Contenido según la selección
    if selected == "Dashboard":
        st.title("Dashboard - Sistema de Gestión de Farmacias")
        
        db = Database()
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        total_medicamentos = len(db.get_medicamentos())
        total_stock = sum(med['stock'] for med in db.get_medicamentos())
        medicamentos_bajo_stock = len([m for m in db.get_medicamentos() if m['stock'] <= m['stock_minimo']])
        alertas_vencimiento = len(db.sp_alertas_vencimiento())
        
        with col1:
            st.metric("Total Medicamentos", total_medicamentos)
        with col2:
            st.metric("Total en Stock", total_stock)
        with col3:
            st.metric("Bajo Stock", medicamentos_bajo_stock, delta_color="inverse")
        with col4:
            st.metric("Próximos a Vencer", alertas_vencimiento, delta_color="inverse")
        
        # Alertas importantes
        st.subheader("Alertas Importantes")
        
        if medicamentos_bajo_stock > 0:
            st.warning(f"{medicamentos_bajo_stock} medicamentos tienen stock bajo")
        
        if alertas_vencimiento > 0:
            st.error(f"{alertas_vencimiento} medicamentos próximos a vencer")
        
        if medicamentos_bajo_stock == 0 and alertas_vencimiento == 0:
            st.success("No hay alertas importantes")
    
    elif selected == "Inventario":
        gestion_inventario()
    
    elif selected == "Punto de Venta":
        punto_venta()
    
    elif selected == "Reportes":
        reportes_ventas()
    
    elif selected == "Administración":
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

if __name__ == "__main__":
    main()

# python -m streamlit run app.py
#ultimo comentario