import streamlit as st
from streamlit_option_menu import option_menu
from auth import login, show_user_profile, logout
from inventory import gestion_inventario
from sales import punto_venta, reportes_ventas
from database import Database
from registro import registro   # 👈 importar el registro
from users import perfil,administracion

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
    menu_options = ["Perfil","Dashboard", "Medicamentos", "Inventario", "Punto de Venta", "Pedidos", "Reportes"]
    menu_icons = ["person-circle","house", "capsule", "box", "cash-coin", "send", "graph-up"]
    if st.session_state['user']['perfil'] == 'Administrador':
        menu_options.append("Administración")
        menu_icons.append("gear")
    elif st.session_state['user']['perfil'] == 'Farmacéutico':
        menu_options.remove("Pedidos")
        menu_icons.remove("send")
    elif st.session_state['user']['perfil'] == 'Cajero':
        menu_options = ["Perfil","Dashboard", "Pagos", "Reportes"]
        menu_icons = ["person-circle","house", "coin", "graph-up"]
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
        administracion()

if __name__ == "__main__":
    main()

# python -m streamlit run app.py
#ultimo comentario