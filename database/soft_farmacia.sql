-- farmacia_db_mejorada.sql
-- Versión mejorada de la base de datos de la farmacia
-- Fecha: 2025-10-28

-- Configuración de caracteres
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Crear base de datos
DROP DATABASE IF EXISTS farmacia_db_mejorada;
CREATE DATABASE farmacia_db_mejorada 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE farmacia_db_mejorada;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS `usuarios` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `usuario` VARCHAR(50) NOT NULL,
    `contrasena_hash` VARCHAR(255) NOT NULL,
    `email` VARCHAR(100) NOT NULL,
    `nombres` VARCHAR(100) NOT NULL,
    `apellidos` VARCHAR(100) NOT NULL,
    `perfil` ENUM('Administrador', 'Farmacéutico', 'Cajero', 'Cliente') NOT NULL,
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `fecha_creacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_usuarios_usuario` (`usuario`),
    UNIQUE KEY `uk_usuarios_email` (`email`),
    KEY `idx_usuarios_perfil` (`perfil`),
    KEY `idx_usuarios_activo` (`activo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de clientes (extensión de usuarios)
CREATE TABLE IF NOT EXISTS `clientes` (
    `id` INT UNSIGNED NOT NULL,
    `tipo_documento` ENUM('DNI', 'RUC', 'CE', 'PASAPORTE') NOT NULL,
    `numero_documento` VARCHAR(20) NOT NULL,
    `direccion` TEXT,
    `telefono` VARCHAR(20),
    `fecha_nacimiento` DATE,
    `genero` ENUM('Masculino', 'Femenino', 'Otro'),
    `puntos_acumulados` INT NOT NULL DEFAULT 0,
    `fecha_creacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_clientes_documento` (`tipo_documento`, `numero_documento`),
    CONSTRAINT `fk_clientes_usuario` 
        FOREIGN KEY (`id`) REFERENCES `usuarios` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de proveedores
CREATE TABLE IF NOT EXISTS `proveedores` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(100) NOT NULL,
    `contacto` VARCHAR(100),
    `telefono` VARCHAR(20),
    `email` VARCHAR(100),
    `direccion` TEXT,
    `ruc` VARCHAR(20),
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `fecha_creacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_proveedores_ruc` (`ruc`),
    KEY `idx_proveedores_activo` (`activo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de categorías de productos
CREATE TABLE IF NOT EXISTS `categorias` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(50) NOT NULL,
    `descripcion` TEXT,
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_categorias_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de medicamentos
CREATE TABLE IF NOT EXISTS `medicamentos` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `categoria_id` INT UNSIGNED,
    `codigo_barras` VARCHAR(50),
    `nombre` VARCHAR(100) NOT NULL,
    `descripcion` TEXT,
    `principio_activo` VARCHAR(100),
    `laboratorio` VARCHAR(100),
    `precio_venta` DECIMAL(10, 2),
    `precio_compra` DECIMAL(10, 2),
    `stock` INT NOT NULL DEFAULT 0,
    `stock_minimo` INT NOT NULL DEFAULT 10,
    `requiere_receta` BOOLEAN NOT NULL DEFAULT FALSE,
    `temperatura` VARCHAR(50),
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    `fecha_creacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_medicamentos_codigo` (`codigo_barras`),
    KEY `idx_medicamentos_nombre` (`nombre`),
    KEY `idx_medicamentos_activo` (`activo`),
    KEY `idx_medicamentos_stock` (`stock`),
    KEY `fk_medicamentos_categoria` (`categoria_id`),
    CONSTRAINT `fk_medicamentos_categoria` 
        FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT `chk_medicamentos_precio` CHECK (`precio_venta` >= 0 AND `precio_compra` >= 0),
    CONSTRAINT `chk_medicamentos_stock` CHECK (`stock` >= 0),
    CONSTRAINT `chk_medicamentos_stock_minimo` CHECK (`stock_minimo` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de lotes
CREATE TABLE IF NOT EXISTS `lotes` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `medicamento_id` INT UNSIGNED NOT NULL,
    `proveedor_id` INT UNSIGNED NOT NULL,
    `numero_lote` VARCHAR(50) NOT NULL,
    `fecha_vencimiento` DATE NOT NULL,
    `fecha_fabricacion` DATE,
    `cantidad_inicial` INT NOT NULL,
    `cantidad_actual` INT NOT NULL,
    `precio_compra` DECIMAL(10, 2) NOT NULL,
    `fecha_ingreso` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `activo` BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_lotes_numero` (`numero_lote`),
    KEY `idx_lotes_medicamento` (`medicamento_id`),
    KEY `idx_lotes_vencimiento` (`fecha_vencimiento`),
    KEY `idx_lotes_activo` (`activo`),
    CONSTRAINT `fk_lotes_medicamento` 
        FOREIGN KEY (`medicamento_id`) REFERENCES `medicamentos` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_lotes_proveedor` 
        FOREIGN KEY (`proveedor_id`) REFERENCES `proveedores` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT `chk_lotes_cantidades` CHECK (`cantidad_inicial` > 0 AND `cantidad_actual` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de ventas
CREATE TABLE IF NOT EXISTS `ventas` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `cliente_id` INT UNSIGNED,
    `usuario_id` INT UNSIGNED NOT NULL,
    `subtotal` DECIMAL(10, 2) NOT NULL,
    `impuesto` DECIMAL(10, 2) NOT NULL,
    `descuento` DECIMAL(10, 2) NOT NULL DEFAULT 0,
    `total` DECIMAL(10, 2) NOT NULL,
    `estado` ENUM('pendiente', 'completada', 'anulada') NOT NULL DEFAULT 'completada',
    `observaciones` TEXT,
    `fecha_venta` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_ventas_cliente` (`cliente_id`),
    KEY `idx_ventas_usuario` (`usuario_id`),
    KEY `idx_ventas_fecha` (`fecha_venta`),
    KEY `idx_ventas_estado` (`estado`),
    CONSTRAINT `fk_ventas_cliente` 
        FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT `fk_ventas_usuario` 
        FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT `chk_ventas_importes` CHECK (`subtotal` >= 0 AND `impuesto` >= 0 AND `descuento` >= 0 AND `total` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de detalles de venta
CREATE TABLE IF NOT EXISTS `detalles_venta` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `venta_id` INT UNSIGNED NOT NULL,
    `medicamento_id` INT UNSIGNED NOT NULL,
    `lote_id` INT UNSIGNED,
    `cantidad` INT NOT NULL,
    `precio_unitario` DECIMAL(10, 2) NOT NULL,
    `descuento` DECIMAL(10, 2) NOT NULL DEFAULT 0,
    `subtotal` DECIMAL(10, 2) NOT NULL,
    `impuesto` DECIMAL(10, 2) NOT NULL,
    `total` DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_detalles_venta_venta` (`venta_id`),
    KEY `idx_detalles_venta_medicamento` (`medicamento_id`),
    KEY `idx_detalles_venta_lote` (`lote_id`),
    CONSTRAINT `fk_detalles_venta_venta` 
        FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_detalles_venta_medicamento` 
        FOREIGN KEY (`medicamento_id`) REFERENCES `medicamentos` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT `fk_detalles_venta_lote` 
        FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT `chk_detalles_venta_cantidad` CHECK (`cantidad` > 0),
    CONSTRAINT `chk_detalles_venta_importes` CHECK (
        `precio_unitario` >= 0 AND 
        `descuento` >= 0 AND 
        `subtotal` >= 0 AND 
        `impuesto` >= 0 AND 
        `total` >= 0
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de comprobantes
CREATE TABLE IF NOT EXISTS `comprobantes` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `venta_id` INT UNSIGNED NOT NULL,
    `tipo_comprobante` ENUM('boleta', 'factura', 'ticket') NOT NULL,
    `serie` VARCHAR(10) NOT NULL,
    `numero` VARCHAR(20) NOT NULL,
    `ruta_archivo` VARCHAR(255) NOT NULL,
    `estado` ENUM('pendiente', 'emitido', 'anulado') NOT NULL DEFAULT 'pendiente',
    `fecha_emision` TIMESTAMP NULL DEFAULT NULL,
    `fecha_creacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_comprobantes_serie_numero` (`serie`, `numero`),
    UNIQUE KEY `uk_comprobantes_venta` (`venta_id`, `tipo_comprobante`),
    KEY `idx_comprobantes_fecha` (`fecha_emision`),
    CONSTRAINT `fk_comprobantes_venta` 
        FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de movimientos de inventario
CREATE TABLE IF NOT EXISTS `movimientos_inventario` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `tipo_movimiento` ENUM('entrada', 'salida', 'ajuste', 'devolucion', 'perdida') NOT NULL,
    `medicamento_id` INT UNSIGNED NOT NULL,
    `lote_id` INT UNSIGNED,
    `cantidad` INT NOT NULL,
    `motivo` VARCHAR(200),
    `referencia_id` INT UNSIGNED,
    `referencia_tipo` VARCHAR(50),
    `usuario_id` INT UNSIGNED NOT NULL,
    `fecha_movimiento` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_movimientos_medicamento` (`medicamento_id`),
    KEY `idx_movimientos_lote` (`lote_id`),
    KEY `idx_movimientos_referencia` (`referencia_tipo`, `referencia_id`),
    KEY `idx_movimientos_fecha` (`fecha_movimiento`),
    CONSTRAINT `fk_movimientos_medicamento` 
        FOREIGN KEY (`medicamento_id`) REFERENCES `medicamentos` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_movimientos_lote` 
        FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT `fk_movimientos_usuario` 
        FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de reclamos y devoluciones
CREATE TABLE IF NOT EXISTS `reclamos` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `venta_id` INT UNSIGNED NOT NULL,
    `cliente_id` INT UNSIGNED NOT NULL,
    `usuario_id` INT UNSIGNED NOT NULL,
    `tipo` ENUM('reclamo', 'devolucion') NOT NULL,
    `descripcion` TEXT NOT NULL,
    `estado` ENUM('pendiente', 'en_proceso', 'resuelto', 'rechazado') NOT NULL DEFAULT 'pendiente',
    `solucion` TEXT,
    `fecha_reclamo` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_resolucion` TIMESTAMP NULL DEFAULT NULL,
    `fecha_creacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_reclamos_venta` (`venta_id`),
    KEY `idx_reclamos_cliente` (`cliente_id`),
    KEY `idx_reclamos_usuario` (`usuario_id`),
    KEY `idx_reclamos_estado` (`estado`),
    KEY `idx_reclamos_fecha` (`fecha_reclamo`),
    CONSTRAINT `fk_reclamos_venta` 
        FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT `fk_reclamos_cliente` 
        FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT `fk_reclamos_usuario` 
        FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de cierres de caja
CREATE TABLE IF NOT EXISTS `cierres_caja` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `usuario_id` INT UNSIGNED NOT NULL,
    `fecha_apertura` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_cierre` TIMESTAMP NULL DEFAULT NULL,
    `monto_inicial` DECIMAL(10, 2) NOT NULL,
    `monto_final` DECIMAL(10, 2),
    `monto_efectivo` DECIMAL(10, 2),
    `monto_tarjeta` DECIMAL(10, 2),
    `monto_otros` DECIMAL(10, 2),
    `diferencia` DECIMAL(10, 2),
    `estado` ENUM('abierta', 'cerrada', 'en_revision') NOT NULL DEFAULT 'abierta',
    `observaciones` TEXT,
    PRIMARY KEY (`id`),
    KEY `idx_cierres_usuario` (`usuario_id`),
    KEY `idx_cierres_fecha` (`fecha_apertura`),
    KEY `idx_cierres_estado` (`estado`),
    CONSTRAINT `fk_cierres_usuario` 
        FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Vistas
CREATE OR REPLACE VIEW `vista_ventas_detalladas` AS
SELECT 
    v.id,
    v.fecha_venta,
    CONCAT(u.nombres, ' ', u.apellidos) AS vendedor,
    CONCAT(c.nombres, ' ', c.apellidos) AS cliente,
    v.subtotal,
    v.impuesto,
    v.descuento,
    v.total,
    v.estado,
    COUNT(dv.id) AS total_items
FROM 
    ventas v
    JOIN usuarios u ON v.usuario_id = u.id
    LEFT JOIN clientes cl ON v.cliente_id = cl.id
    LEFT JOIN usuarios c ON cl.id = c.id
    LEFT JOIN detalles_venta dv ON v.id = dv.venta_id
GROUP BY 
    v.id;

CREATE OR REPLACE VIEW `vista_inventario` AS
SELECT 
    m.id,
    m.codigo_barras,
    m.nombre,
    c.nombre AS categoria,
    m.principio_activo,
    m.laboratorio,
    m.precio_venta,
    m.precio_compra,
    m.stock,
    m.stock_minimo,
    m.requiere_receta,
    m.activo,
    GROUP_CONCAT(DISTINCT p.nombre SEPARATOR ', ') AS proveedores
FROM 
    medicamentos m
    LEFT JOIN categorias c ON m.categoria_id = c.id
    LEFT JOIN lotes l ON m.id = l.medicamento_id
    LEFT JOIN proveedores p ON l.proveedor_id = p.id
GROUP BY 
    m.id;

-- Triggers
DELIMITER //

-- Actualizar stock al insertar un detalle de venta
CREATE TRIGGER `tr_detalle_venta_insert` AFTER INSERT ON `detalles_venta`
FOR EACH ROW
BEGIN
    -- Actualizar stock del medicamento
    UPDATE medicamentos 
    SET stock = stock - NEW.cantidad,
        fecha_actualizacion = NOW()
    WHERE id = NEW.medicamento_id;
    
    -- Actualizar cantidad en el lote si se especificó
    IF NEW.lote_id IS NOT NULL THEN
        UPDATE lotes 
        SET cantidad_actual = cantidad_actual - NEW.cantidad,
            fecha_actualizacion = NOW()
        WHERE id = NEW.lote_id;
    END IF;
END//

-- Actualizar stock al eliminar un detalle de venta
CREATE TRIGGER `tr_detalle_venta_delete` AFTER DELETE ON `detalles_venta`
FOR EACH ROW
BEGIN
    -- Revertir stock del medicamento
    UPDATE medicamentos 
    SET stock = stock + OLD.cantidad,
        fecha_actualizacion = NOW()
    WHERE id = OLD.medicamento_id;
    
    -- Revertir cantidad en el lote si se especificó
    IF OLD.lote_id IS NOT NULL THEN
        UPDATE lotes 
        SET cantidad_actual = cantidad_actual + OLD.cantidad,
            fecha_actualizacion = NOW()
        WHERE id = OLD.lote_id;
    END IF;
END//

-- Actualizar stock al modificar un detalle de venta
CREATE TRIGGER `tr_detalle_venta_update` AFTER UPDATE ON `detalles_venta`
FOR EACH ROW
BEGIN
    -- Si cambió el medicamento o el lote, revertir el stock anterior
    IF OLD.medicamento_id != NEW.medicamento_id OR OLD.lote_id != NEW.lote_id THEN
        -- Revertir stock anterior
        UPDATE medicamentos 
        SET stock = stock + OLD.cantidad,
            fecha_actualizacion = NOW()
        WHERE id = OLD.medicamento_id;
        
        IF OLD.lote_id IS NOT NULL THEN
            UPDATE lotes 
            SET cantidad_actual = cantidad_actual + OLD.cantidad,
                fecha_actualizacion = NOW()
            WHERE id = OLD.lote_id;
        END IF;
        
        -- Aplicar nuevo stock
        UPDATE medicamentos 
        SET stock = stock - NEW.cantidad,
            fecha_actualizacion = NOW()
        WHERE id = NEW.medicamento_id;
        
        IF NEW.lote_id IS NOT NULL THEN
            UPDATE lotes 
            SET cantidad_actual = cantidad_actual - NEW.cantidad,
                fecha_actualizacion = NOW()
            WHERE id = NEW.lote_id;
        END IF;
    -- Si solo cambió la cantidad
    ELSIF OLD.cantidad != NEW.cantidad THEN
        -- Calcular la diferencia
        DECLARE diferencia INT;
        SET diferencia = OLD.cantidad - NEW.cantidad;
        
        -- Ajustar stock según la diferencia
        UPDATE medicamentos 
        SET stock = stock + diferencia,
            fecha_actualizacion = NOW()
        WHERE id = NEW.medicamento_id;
        
        IF NEW.lote_id IS NOT NULL THEN
            UPDATE lotes 
            SET cantidad_actual = cantidad_actual + diferencia,
                fecha_actualizacion = NOW()
            WHERE id = NEW.lote_id;
        END IF;
    END IF;
END//

-- Actualizar fechas de actualización
CREATE TRIGGER `tr_usuarios_before_update` BEFORE UPDATE ON `usuarios`
FOR EACH ROW
BEGIN
    SET NEW.fecha_actualizacion = NOW();
END//

CREATE TRIGGER `tr_clientes_before_update` BEFORE UPDATE ON `clientes`
FOR EACH ROW
BEGIN
    SET NEW.fecha_actualizacion = NOW();
END//

CREATE TRIGGER `tr_medicamentos_before_update` BEFORE UPDATE ON `medicamentos`
FOR EACH ROW
BEGIN
    SET NEW.fecha_actualizacion = NOW();
END//

CREATE TRIGGER `tr_ventas_before_update` BEFORE UPDATE ON `ventas`
FOR EACH ROW
BEGIN
    SET NEW.fecha_actualizacion = NOW();
END//

CREATE TRIGGER `tr_comprobantes_before_update` BEFORE UPDATE ON `comprobantes`
FOR EACH ROW
BEGIN
    SET NEW.fecha_actualizacion = NOW();
END//

DELIMITER ;

-- Insertar datos iniciales
-- Insertar usuario administrador por defecto (contraseña: admin123)
INSERT INTO `usuarios` (`usuario`, `contrasena_hash`, `email`, `nombres`, `apellidos`, `perfil`, `activo`) 
VALUES ('admin', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin@farmacia.com', 'Administrador', 'del Sistema', 'Administrador', 1);

-- Insertar categorías de productos
INSERT INTO `categorias` (`nombre`, `descripcion`) VALUES
('Analgésicos', 'Medicamentos para el alivio del dolor'),
('Antibióticos', 'Medicamentos para tratar infecciones bacterianas'),
('Antiinflamatorios', 'Medicamentos para reducir la inflamación'),
('Antialérgicos', 'Medicamentos para tratar alergias'),
('Vitaminas', 'Suplementos vitamínicos y minerales');

-- Insertar proveedores
INSERT INTO `proveedores` (`nombre`, `contacto`, `telefono`, `email`, `direccion`, `ruc`, `activo`) VALUES
('Farmacéutica Nacional S.A.', 'Juan Pérez', '987654321', 'jperez@farmaceutica.com', 'Av. Principal 123, Lima', '20123456789', 1),
('Laboratorios Salud S.A.C.', 'María Gómez', '987654322', 'mgomez@salud.com', 'Calle Los Pinos 456, Lima', '20123456780', 1),
('Distribuidora Médica E.I.R.L.', 'Carlos López', '987654323', 'clopez@dime.com.pe', 'Jr. San Martín 789, Lima', '20123456781', 1);

-- Establecer permisos
GRANT ALL PRIVILEGES ON farmacia_db_mejorada.* TO 'tu_usuario'@'localhost' IDENTIFIED BY 'tu_contraseña';
FLUSH PRIVILEGES;

-- Habilitar verificación de claves foráneas
SET FOREIGN_KEY_CHECKS = 1;

-- Mensaje de éxito
SELECT 'Base de datos creada exitosamente' AS mensaje;