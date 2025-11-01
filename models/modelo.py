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
    def get_medicamentos_con_lotes(self):
        query = """
        SELECT 
            m.id AS medicamento_id,
            m.nombre,
            m.descripcion,
            m.principio_activo,
            m.laboratorio,
            m.precio,
            m.stock,
            m.stock_minimo,
            l.id AS lote_id,
            l.numero_lote,
            l.fecha_vencimiento,
            l.cantidad_inicial,
            l.cantidad_actual,
            p.nombre AS proveedor
        FROM medicamentos m
        LEFT JOIN lotes l ON m.id = l.medicamento_id
        LEFT JOIN proveedores p ON l.proveedor_id = p.id
        WHERE m.activo = TRUE
        ORDER BY m.nombre, l.fecha_vencimiento
        """
        return self.execute_query(query)
    def get_lotes_medicamentos(self):
        query = """
        SELECT 
            l.id,
            l.numero_lote AS numero_lote,
            l.fecha_vencimiento,
            l.cantidad_actual,
            m.nombre
        FROM lotes l
        INNER JOIN medicamentos m ON l.medicamento_id = m.id
        ORDER BY m.nombre, l.fecha_vencimiento
        """
        return self.execute_query(query)
    def delete_lote_medicamento(self, lote_id):
        """
        Elimina un lote específico de la tabla lotes.
        """
        query = "DELETE FROM lotes WHERE id = %s"
        return self.execute_update(query, (lote_id,))
    def insert_medicamento_con_lote(self, nombre, descripcion, principio_activo, laboratorio, precio, stock_minimo,
                                    numero_lote, proveedor_id, cantidad_inicial, fecha_vencimiento):
        try:
            cursor = self.connection.cursor()

            # 1. Insertar medicamento
            insert_med = """
            INSERT INTO medicamentos (nombre, descripcion, principio_activo, laboratorio, precio, stock, stock_minimo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_med, (
                nombre, descripcion, principio_activo, laboratorio, precio, cantidad_inicial, stock_minimo
            ))
            medicamento_id = cursor.lastrowid  # id generado

            # 2. Insertar lote asociado
            self.execute_update(
            'sp_INGRESAR_LOTE',
                (medicamento_id, proveedor_id, numero_lote, fecha_vencimiento, cantidad_inicial, cantidad_inicial),
                True
            )

            self.connection.commit()
            cursor.close()
            return True

        except Error as e:
            print(f"❌ Error en insert_medicamento_con_lote: {e}")
            self.connection.rollback()
            return False


    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("MYSQLHOST", ""),
                database=os.getenv("MYSQLDATABASE", ""),
                user=os.getenv("MYSQLUSER", ""),
                password=os.getenv("MYSQLPASSWORD", ""),
                port=int(os.getenv("MYSQLPORT",))
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
    def sp_actualizar_usuario(self, username, email, perfil):
        # """Actualiza usuario con hash bcrypt"""
        # hashed_password = self.hash_password(password)
        return self.execute_update(
            'sp_actualizar_usuario',
            (username, email, perfil),
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
    
    def insert_medicamento(self, nombre, descripcion, principio_activo, laboratorio, precio, stock, stock_minimo):
        query = """
        INSERT INTO medicamentos (nombre, descripcion, principio_activo, laboratorio, precio, stock, stock_minimo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_update(query, (nombre, descripcion, principio_activo, laboratorio, precio, stock, stock_minimo))
    
    def update_medicamento(self, medicamento_id, nombre, descripcion, principio_activo, laboratorio, precio, stock_minimo):
        query = """
        UPDATE medicamentos 
        SET nombre = %s, descripcion = %s, principio_activo = %s, laboratorio = %s, precio = %s, 
            stock_minimo = %s
        WHERE id = %s
        """
        return self.execute_update(query, (nombre, descripcion, principio_activo, laboratorio, precio, stock_minimo, medicamento_id))
    
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
    
    def get_venta_por_id(self, venta_id):
        """Obtiene los detalles de una venta específica"""
        query = """
        SELECT v.*, u.username as vendedor, c.username as cliente
        FROM ventas v
        INNER JOIN usuarios u ON v.usuario_id = u.id
        LEFT JOIN usuarios c ON v.cliente_id = c.id
        WHERE v.id = %s
        """
        result = self.execute_query(query, (venta_id,))
        return result[0] if result else None
    
    def get_detalle_venta(self, venta_id):
        """Obtiene los detalles de productos de una venta"""
        query = """
        SELECT dv.*, m.nombre as medicamento_nombre
        FROM detalles_venta dv
        INNER JOIN medicamentos m ON dv.medicamento_id = m.id
        WHERE dv.venta_id = %s
        """
        return self.execute_query(query, (venta_id,))
    
    def registrar_comprobante(self, venta_id, tipo_comprobante, numero_comprobante, ruta_archivo):
        """
        Registra un comprobante emitido en la base de datos
        tipo_comprobante: 'boleta' o 'factura'
        """
        query = """
        INSERT INTO comprobantes (venta_id, tipo_comprobante, numero_comprobante, ruta_archivo, fecha_emision)
        VALUES (%s, %s, %s, %s, NOW())
        """
        return self.execute_update(query, (venta_id, tipo_comprobante, numero_comprobante, ruta_archivo))
    
    def get_ultimo_numero_comprobante(self, tipo):
        """
        Obtiene el último número de comprobante emitido
        tipo: 'boleta' o 'factura'
        """
        query = """
        SELECT MAX(CAST(SUBSTRING_INDEX(numero_comprobante, '-', -1) AS UNSIGNED)) as ultimo_numero
        FROM comprobantes
        WHERE tipo_comprobante = %s
        """
        result = self.execute_query(query, (tipo,))
        if result and result[0]['ultimo_numero']:
            return result[0]['ultimo_numero']
        return 0
    
    def get_comprobantes(self, limit=50):
        """Obtiene la lista de comprobantes emitidos"""
        query = """
        SELECT c.*, v.total, u.username as vendedor
        FROM comprobantes c
        INNER JOIN ventas v ON c.venta_id = v.id
        INNER JOIN usuarios u ON v.usuario_id = u.id
        ORDER BY c.fecha_emision DESC
        LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    def get_comprobante_por_venta(self, venta_id):
        """Obtiene el comprobante asociado a una venta"""
        query = """
        SELECT * FROM comprobantes WHERE venta_id = %s
        """
        result = self.execute_query(query, (venta_id,))
        return result[0] if result else None
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 Conexión a la base de datos cerrada")
