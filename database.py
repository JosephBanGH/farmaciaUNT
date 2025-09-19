import mysql.connector
from mysql.connector import Error
import streamlit as st
import bcrypt
import json
import os


class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("MYSQLHOST", "btkgltlwtq1ihq6ytfh6-mysql.services.clever-cloud.com"),
                database=os.getenv("MYSQLDATABASE", "btkgltlwtq1ihq6ytfh6"),
                user=os.getenv("MYSQLUSER", "upazlqy3bnwfzt9h"),
                password=os.getenv("MYSQLPASSWORD", "tBmoYwbesqroW7Xf38PE"),
                port=int(os.getenv("MYSQLPORT", 3306))
            )
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                print(f"✅ Conectado a MySQL Server versión {db_info}")
        except Error as e:
            print(f"❌ Error al conectar a MySQL: {e}")
            st.error(f"Error de conexión a la base de datos: {e}")

    def execute_query(self, query, params=None, procedure=False):
        try:
            if procedure:
                cursor = self.connection.cursor()
                if params:
                    cursor.callproc(query, params)
                else:
                    cursor.callproc(query)
    
                result = []
                for res in cursor.stored_results():
                    rows = res.fetchall()
                    col_names = [desc[0] for desc in res.description]
                    for row in rows:
                        result.append(dict(zip(col_names, row)))
                cursor.close()
                return result
            else:
                cursor = self.connection.cursor(dictionary=True)
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
                return result
        except Error as e:
            print(f"❌ Error ejecutando consulta {query}: {e}")
            st.error(f"Error en la consulta: {e}")
            return None
        
    def execute_update(self, query, params=None, procedure=False):
        try:
            cursor = self.connection.cursor()
            if procedure:
                if params:
                    cursor.callproc(query, params)
                else:
                    cursor.callproc(query)
            else:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
            
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Error ejecutando actualización {query}: {e}")
            self.connection.rollback()
            st.error(f"Error en la operación: {e}")
            return False
    
    # -------------------------
    # Seguridad: contraseñas
    # -------------------------
    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    # -------------------------
    # Stored Procedures
    # -------------------------
    def sp_crear_usuario(self, username, password, email, perfil):
        """Crea usuario con hash bcrypt"""
        hashed_password = self.hash_password(password)
        return self.execute_update(
            'sp_crear_usuario',
            (username, hashed_password, email, perfil),
            True
        )
    
    def sp_actualizar_stock(self, medicamento_id, cantidad, tipo, motivo, usuario_id):
        # tipo = 'entrada' o 'salida' (VARCHAR, no ENUM)
        return self.execute_update(
            'sp_actualizar_stock',
            (medicamento_id, cantidad, tipo, motivo, usuario_id),
            True
        )
    
    def sp_generar_venta(self, cliente_id, usuario_id, detalles):
        """Genera una venta a partir de un JSON de detalles"""
        try:
            detalles_json = json.dumps(detalles)
            return self.execute_update(
                'sp_generar_venta',
                (cliente_id, usuario_id, detalles_json),
                True
            )
        except Exception as e:
            print(f"❌ Error en sp_generar_venta: {e}")
            return False
    
    def sp_obtener_reportes_ventas(self, fecha_inicio, fecha_fin):
        return self.execute_query(
            'sp_obtener_reportes_ventas',
            (fecha_inicio, fecha_fin),
            True
        )
    
    def sp_alertas_vencimiento(self):
        return self.execute_query('sp_alertas_vencimiento', (), True)
    
    # -------------------------
    # Métodos de consulta
    # -------------------------
    def get_usuario_por_username(self, username):
        query = "SELECT * FROM usuarios WHERE username = %s AND activo = TRUE"
        result = self.execute_query(query, (username,))
        return result[0] if result else None
    
    def get_medicamentos(self):
        query = "SELECT * FROM medicamentos WHERE activo = TRUE ORDER BY nombre"
        return self.execute_query(query)
    
    def get_medicamento_por_id(self, medicamento_id):
        query = "SELECT * FROM medicamentos WHERE id = %s AND activo = TRUE"
        result = self.execute_query(query, (medicamento_id,))
        return result[0] if result else None
    
    def insert_medicamento(self, nombre, descripcion, principio_activo, laboratorio, precio, stock, stock_minimo, lote, fecha_vencimiento):
        query = """
        INSERT INTO medicamentos (nombre, descripcion, principio_activo, laboratorio, precio, stock, stock_minimo, lote, fecha_vencimiento)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_update(query, (nombre, descripcion, principio_activo, laboratorio, precio, stock, stock_minimo, lote, fecha_vencimiento))
    
    def update_medicamento(self, medicamento_id, nombre, descripcion, principio_activo, laboratorio, precio, stock_minimo, lote, fecha_vencimiento):
        query = """
        UPDATE medicamentos 
        SET nombre = %s, descripcion = %s, principio_activo = %s, laboratorio = %s, precio = %s, 
            stock_minimo = %s, lote = %s, fecha_vencimiento = %s
        WHERE id = %s
        """
        return self.execute_update(query, (nombre, descripcion, principio_activo, laboratorio, precio, stock_minimo, lote, fecha_vencimiento, medicamento_id))
    
    def delete_medicamento(self, medicamento_id):
        query = "UPDATE medicamentos SET activo = FALSE WHERE id = %s"
        return self.execute_update(query, (medicamento_id,))
    
    def get_movimientos_inventario(self):
        query = """
        SELECT mi.*, m.nombre as medicamento_nombre, u.username as usuario_nombre
        FROM movimientos_inventario mi
        INNER JOIN medicamentos m ON mi.medicamento_id = m.id
        INNER JOIN usuarios u ON mi.usuario_id = u.id
        ORDER BY mi.fecha_movimiento DESC
        LIMIT 100
        """
        return self.execute_query(query)
    
    def get_proveedores(self):
        query = "SELECT * FROM proveedores ORDER BY nombre"
        return self.execute_query(query)
    
    def get_ventas_recientes(self, limit=10):
        query = """
        SELECT v.*, u.username as vendedor, c.username as cliente
        FROM ventas v
        INNER JOIN usuarios u ON v.usuario_id = u.id
        LEFT JOIN usuarios c ON v.cliente_id = c.id
        ORDER BY v.fecha_venta DESC
        LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 Conexión a la base de datos cerrada")


# -------------------------
# Verificación de la BD
# -------------------------
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
