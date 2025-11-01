-- Migración para crear la tabla clientes como hija de usuarios

-- Primero, asegurémonos de que no exista la tabla clientes
DROP TABLE IF EXISTS clientes;

-- Crear la tabla clientes con una relación uno a uno con usuarios
CREATE TABLE clientes (
    id INT PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    tipo_documento ENUM('DNI', 'RUC', 'CE', 'PASAPORTE') NOT NULL,
    numero_documento VARCHAR(20) UNIQUE NOT NULL,
    direccion TEXT,
    telefono VARCHAR(20),
    fecha_nacimiento DATE,
    genero ENUM('Masculino', 'Femenino', 'Otro'),
    puntos_acumulados INT DEFAULT 0,
    FOREIGN KEY (id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Actualizar la tabla ventas para que haga referencia a la tabla clientes
ALTER TABLE ventas
MODIFY COLUMN cliente_id INT NULL,
DROP FOREIGN KEY ventas_ibfk_2; -- Eliminar la restricción anterior si existe

-- Agregar la nueva restricción de clave foránea
ALTER TABLE ventas
ADD CONSTRAINT fk_venta_cliente
FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL;

-- Crear un índice para mejorar el rendimiento en búsquedas por documento
CREATE INDEX idx_cliente_documento ON clientes(numero_documento);

-- Comentarios para documentación
ALTER TABLE clientes 
COMMENT = 'Tabla de clientes que extiende la información de usuarios con perfil Cliente';

-- Procedimiento almacenado para crear un nuevo cliente
DELIMITER $$
CREATE PROCEDURE sp_crear_cliente(
    IN p_username VARCHAR(50),
    IN p_password_hash VARCHAR(255),
    IN p_email VARCHAR(100),
    IN p_nombres VARCHAR(100),
    IN p_apellidos VARCHAR(100),
    IN p_tipo_documento ENUM('DNI', 'RUC', 'CE', 'PASAPORTE'),
    IN p_numero_documento VARCHAR(20),
    IN p_direccion TEXT,
    IN p_telefono VARCHAR(20),
    IN p_fecha_nacimiento DATE,
    IN p_genero ENUM('Masculino', 'Femenino', 'Otro')
)
BEGIN
    DECLARE v_usuario_id INT;
    
    START TRANSACTION;
    
    -- Insertar en la tabla usuarios
    INSERT INTO usuarios (username, password_hash, email, perfil, activo)
    VALUES (p_username, p_password_hash, p_email, 'Cliente', TRUE);
    
    SET v_usuario_id = LAST_INSERT_ID();
    
    -- Insertar en la tabla clientes
    INSERT INTO clientes (
        id, nombres, apellidos, tipo_documento, numero_documento,
        direccion, telefono, fecha_nacimiento, genero
    ) VALUES (
        v_usuario_id, p_nombres, p_apellidos, p_tipo_documento, p_numero_documento,
        p_direccion, p_telefono, p_fecha_nacimiento, p_genero
    );
    
    COMMIT;
END$$
DELIMITER ;

-- Procedimiento para actualizar datos del cliente
DELIMITER $$
CREATE PROCEDURE sp_actualizar_cliente(
    IN p_id INT,
    IN p_email VARCHAR(100),
    IN p_nombres VARCHAR(100),
    IN p_apellidos VARCHAR(100),
    IN p_direccion TEXT,
    IN p_telefono VARCHAR(20),
    IN p_fecha_nacimiento DATE,
    IN p_genero ENUM('Masculino', 'Femenino', 'Otro'),
    IN p_activo BOOLEAN
)
BEGIN
    START TRANSACTION;
    
    -- Actualizar datos en usuarios
    UPDATE usuarios 
    SET email = p_email,
        activo = p_activo
    WHERE id = p_id;
    
    -- Actualizar datos en clientes
    UPDATE clientes
    SET nombres = p_nombres,
        apellidos = p_apellidos,
        direccion = p_direccion,
        telefono = p_telefono,
        fecha_nacimiento = p_fecha_nacimiento,
        genero = p_genero
    WHERE id = p_id;
    
    COMMIT;
END$$
DELIMITER ;

-- Vista para obtener información completa de clientes
CREATE OR REPLACE VIEW vista_clientes AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.fecha_creacion,
    u.activo,
    c.nombres,
    c.apellidos,
    CONCAT(c.nombres, ' ', c.apellidos) as nombre_completo,
    c.tipo_documento,
    c.numero_documento,
    c.direccion,
    c.telefono,
    c.fecha_nacimiento,
    c.genero,
    c.puntos_acumulados
FROM usuarios u
JOIN clientes c ON u.id = c.id
WHERE u.perfil = 'Cliente';
