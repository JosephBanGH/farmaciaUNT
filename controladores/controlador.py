from models.modelo import Database
import streamlit as st

def verificar_base_datos():
    try:
        db = Database()
        
        tablas_requeridas = ['usuarios', 'medicamentos', 'movimientos_inventario', 'ventas', 'detalles_venta', 'proveedores']
        procedures_requeridos = ['sp_crear_usuario', 'sp_actualizar_stock', 'sp_generar_venta', 'sp_obtener_reportes_ventas', 'sp_alertas_vencimiento']
        
        for tabla in tablas_requeridas:
            resultado = db.execute_query(f"SHOW TABLES LIKE '{tabla}'")
            if not resultado:
                st.error(f"❌ Tabla '{tabla}' no encontrada en la base de datos")
                return False
        
        for procedure in procedures_requeridos:
            resultado = db.execute_query(f"SHOW PROCEDURE STATUS WHERE Name = '{procedure}'")
            if not resultado:
                st.error(f"❌ Procedure '{procedure}' no encontrado en la base de datos")
                return False
        
        st.success("✅ Base de datos verificada correctamente")
        return True
        
    except Exception as e:
        st.error(f"❌ Error verificando la base de datos: {e}")
        return False
