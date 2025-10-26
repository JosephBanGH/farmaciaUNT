import streamlit as st
from streamlit_option_menu import option_menu
from views.user.auth import login, show_user_profile, logout
from views.menu.inventory import gestion_inventario
from views.menu.sales import punto_venta
from models.modelo import Database
from views.user.registro import registro   # 👈 importar el registro
from views.user.users import perfil,administracion
from views.menu.reports import dashboard, reportes_ventas
from controladores.controlador import verificar_base_datos
   
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
    # Determinar opciones de menú según el perfil
    menu_options = ["Perfil","Dashboard", "Medicamentos", "Inventario", "Punto de Venta", "Reportes"]
    menu_icons = ["person-circle","house", "capsule", "box", "cash-coin", "graph-up"]
    #Administrador con todas las opciones
    if st.session_state['user']['perfil'] == 'Administrador':
        menu_options = ["Perfil","Dashboard", "Administración", "Medicamentos", "Inventario", "Punto de Venta", "Pedidos", "Pagos", "Reclamos y Devoluciones", "Cierre de caja", "Reportes"]
        menu_icons = ["person-circle","house", "person-circle","capsule", "box", "cash-coin", "send", "coin", "ban", "x-lg", "graph-up"]
    # elif st.session_state['user']['perfil'] == 'Farmacéutico':
    #     menu_options.remove("Pedidos")
    #     menu_icons.remove("send")
    elif st.session_state['user']['perfil'] == 'Cajero':
        menu_options = ["Perfil","Dashboard", "Pagos", "Reclamos y Devoluciones", "Cierre de caja", "Reportes"]
        menu_icons = ["person-circle","house", "coin", "ban", "x-lg", "graph-up"]
    elif st.session_state['user']['perfil']== 'Cliente':
        menu_options = ["Perfil","Dashboard", "Pedidos", "Pagos", "Reclamos y Devoluciones", "Reportes"]
        menu_icons = ["person-circle","house", "send", "coin", "ban", "x-lg", "graph-up"]
    with st.sidebar:
        selected = option_menu(
            menu_title="Menú Principal",
            options=menu_options,
            icons=menu_icons,
            default_index=0,
        )
    
    # Contenido según la selección
    if selected == "Perfil":
        perfil()
    elif selected == "Dashboard":
        dashboard();
    elif selected == "Medicamentos":
        from views.menu.ver_medicamentos import ver_medicamentos
        ver_medicamentos()
    elif selected == "Inventario":
        gestion_inventario()
    
    elif selected == "Punto de Venta":
        punto_venta()
    
    elif selected == "Reportes":
        reportes_ventas()
    
    elif selected == "Administración":
        administracion()

if __name__ == "__main__":
    main()

# python -m streamlit run app.py
#ultimo comentario