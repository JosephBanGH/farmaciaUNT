-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 28-10-2025 a las 20:46:01
-- Versión del servidor: 10.4.28-MariaDB
-- Versión de PHP: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `farmacia_db`
--

DELIMITER $$
--
-- Procedimientos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_actualizar_cliente` (IN `p_id` INT, IN `p_email` VARCHAR(100), IN `p_nombres` VARCHAR(100), IN `p_apellidos` VARCHAR(100), IN `p_direccion` TEXT, IN `p_telefono` VARCHAR(20), IN `p_fecha_nacimiento` DATE, IN `p_genero` ENUM('Masculino','Femenino','Otro'), IN `p_activo` BOOLEAN)   BEGIN
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

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_actualizar_stock` (IN `p_medicamento_id` INT, IN `p_cantidad` INT, IN `p_tipo` ENUM('entrada','salida'), IN `p_motivo` VARCHAR(200), IN `p_usuario_id` INT)   BEGIN
    DECLARE current_stock INT;
    
    START TRANSACTION;
    
    -- Obtener stock actual
    SELECT stock INTO current_stock FROM medicamentos WHERE id = p_medicamento_id FOR UPDATE;
    
    -- Actualizar stock según el tipo de movimiento
    IF p_tipo = 'entrada' THEN
        UPDATE medicamentos SET stock = current_stock + p_cantidad WHERE id = p_medicamento_id;
    ELSE
        IF current_stock >= p_cantidad THEN
            UPDATE medicamentos SET stock = current_stock - p_cantidad WHERE id = p_medicamento_id;
        ELSE
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock insuficiente';
        END IF;
    END IF;
    
    -- Registrar movimiento
    INSERT INTO movimientos_inventario (medicamento_id, tipo, cantidad, motivo, usuario_id)
    VALUES (p_medicamento_id, p_tipo, p_cantidad, p_motivo, p_usuario_id);
    
    COMMIT;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_actualizar_usuario` (IN `p_username` VARCHAR(50), IN `p_email` VARCHAR(100), IN `p_perfil` ENUM('Administrador','Farmacéutico','Cajero','Cliente'))   BEGIN
    UPDATE usuarios
    SET email=p_email, perfil=p_perfil
    where username=p_username;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_alertas_vencimiento` ()   BEGIN
    SELECT 
        l.id AS lote_id,
        m.nombre AS medicamento,
        l.numero_lote,
        l.fecha_vencimiento,
        DATEDIFF(l.fecha_vencimiento, CURDATE()) AS dias_restantes
    FROM lotes l
    INNER JOIN medicamentos m ON l.medicamento_id = m.id
    WHERE l.fecha_vencimiento IS NOT NULL 
      AND l.fecha_vencimiento <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
    ORDER BY l.fecha_vencimiento ASC;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_crear_cliente` (IN `p_username` VARCHAR(50), IN `p_password_hash` VARCHAR(255), IN `p_email` VARCHAR(100), IN `p_nombres` VARCHAR(100), IN `p_apellidos` VARCHAR(100), IN `p_tipo_documento` ENUM('DNI','RUC','CE','PASAPORTE'), IN `p_numero_documento` VARCHAR(20), IN `p_direccion` TEXT, IN `p_telefono` VARCHAR(20), IN `p_fecha_nacimiento` DATE, IN `p_genero` ENUM('Masculino','Femenino','Otro'))   BEGIN
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

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_crear_usuario` (IN `p_username` VARCHAR(50), IN `p_password_hash` VARCHAR(255), IN `p_email` VARCHAR(100), IN `p_perfil` ENUM('Administrador','Farmacéutico','Cajero','Cliente'))   BEGIN
    INSERT INTO usuarios (username, password_hash, email, perfil)
    VALUES (p_username, p_password_hash, p_email, p_perfil);
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_generar_venta` (IN `p_cliente_id` INT, IN `p_usuario_id` INT, IN `p_detalles` JSON)   BEGIN
    DECLARE v_total DECIMAL(10, 2) DEFAULT 0;
    DECLARE v_impuesto DECIMAL(10, 2) DEFAULT 0;
    DECLARE v_venta_id INT;
    DECLARE i INT DEFAULT 0;
    DECLARE num_items INT;
    DECLARE medicamento_id INT;
    DECLARE cantidad INT;
    DECLARE precio DECIMAL(10, 2);
    
    -- Calcular número de items
    SET num_items = JSON_LENGTH(p_detalles);
    
    START TRANSACTION;
    
    -- Calcular total e impuesto
    WHILE i < num_items DO
        SET medicamento_id = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].medicamento_id'));
        SET cantidad = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].cantidad'));
        SET precio = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].precio'));
        
        SET v_total = v_total + (cantidad * precio);
        SET i = i + 1;
    END WHILE;
    
    SET v_impuesto = v_total * 0.16; -- 16% de impuesto
    
    -- Insertar venta
    INSERT INTO ventas (cliente_id, total, impuesto, usuario_id)
    VALUES (p_cliente_id, v_total, v_impuesto, p_usuario_id);
    
    SET v_venta_id = LAST_INSERT_ID();
    
    -- Insertar detalles de venta y actualizar stock
    SET i = 0;
    WHILE i < num_items DO
        SET medicamento_id = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].medicamento_id'));
        SET cantidad = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].cantidad'));
        SET precio = JSON_EXTRACT(p_detalles, CONCAT('$[', i, '].precio'));
        
        INSERT INTO detalles_venta (venta_id, medicamento_id, cantidad, precio_unitario, subtotal)
        VALUES (v_venta_id, medicamento_id, cantidad, precio, cantidad * precio);
        
        -- Actualizar stock y registrar movimiento
        CALL sp_actualizar_stock(medicamento_id, cantidad, 'salida', 'Venta', p_usuario_id);
        
        SET i = i + 1;
    END WHILE;
    
    COMMIT;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_ingresar_lote` (IN `p_medicamento_id` INT, IN `p_proveedor_id` INT, IN `p_numero_lote` VARCHAR(50), IN `p_fecha_vencimiento` DATE, IN `p_cantidad_inicial` INT, IN `p_usuario_id` INT)   BEGIN
    DECLARE lote_id INT;

    START TRANSACTION;

    -- Insertar lote
    INSERT INTO lotes (medicamento_id, proveedor_id, numero_lote, fecha_vencimiento, cantidad_inicial, cantidad_actual)
    VALUES (p_medicamento_id, p_proveedor_id, p_numero_lote, p_fecha_vencimiento, p_cantidad_inicial, p_cantidad_inicial);

    SET lote_id = LAST_INSERT_ID();

    -- Actualizar stock del medicamento
    UPDATE medicamentos SET stock = stock + p_cantidad_inicial WHERE id = p_medicamento_id;

    -- Registrar movimiento de inventario
    INSERT INTO movimientos_inventario (medicamento_id, tipo, cantidad, motivo, usuario_id)
    VALUES (p_medicamento_id, 'entrada', p_cantidad_inicial, CONCAT('Ingreso de lote ', p_numero_lote), p_usuario_id);

    COMMIT;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_obtener_reportes_ventas` (IN `p_fecha_inicio` DATE, IN `p_fecha_fin` DATE)   BEGIN
    SELECT 
        v.id,
        v.fecha_venta,
        v.total,
        v.impuesto,
        u.username as vendedor,
        c.username as cliente
    FROM ventas v
    INNER JOIN usuarios u ON v.usuario_id = u.id
    LEFT JOIN usuarios c ON v.cliente_id = c.id
    WHERE DATE(v.fecha_venta) BETWEEN p_fecha_inicio AND p_fecha_fin
    ORDER BY v.fecha_venta DESC;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `clientes`
--

CREATE TABLE `clientes` (
  `id` int(11) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `tipo_documento` enum('DNI','RUC','CE','PASAPORTE') NOT NULL,
  `numero_documento` varchar(20) NOT NULL,
  `direccion` text DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `genero` enum('Masculino','Femenino','Otro') DEFAULT NULL,
  `puntos_acumulados` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Tabla de clientes que extiende la información de usuarios con perfil Cliente';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `comprobantes`
--

CREATE TABLE `comprobantes` (
  `id` int(11) NOT NULL,
  `venta_id` int(11) NOT NULL,
  `tipo_comprobante` enum('boleta','factura') NOT NULL,
  `numero_comprobante` varchar(50) NOT NULL,
  `ruta_archivo` varchar(255) NOT NULL,
  `fecha_emision` datetime NOT NULL DEFAULT current_timestamp(),
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabla para almacenar los comprobantes de pago emitidos (boletas y facturas)';

--
-- Volcado de datos para la tabla `comprobantes`
--

INSERT INTO `comprobantes` (`id`, `venta_id`, `tipo_comprobante`, `numero_comprobante`, `ruta_archivo`, `fecha_emision`, `activo`) VALUES
(1, 2, 'boleta', 'B001-00000001', 'comprobantes\\B_B001-00000001_20251027.pdf', '2025-10-27 00:24:53', 1),
(2, 3, 'factura', 'F001-00000001', 'comprobantes\\F_F001-00000001_20251027.pdf', '2025-10-27 01:19:44', 1),
(3, 4, 'factura', 'F001-00000002', 'comprobantes\\F_F001-00000002_20251027.pdf', '2025-10-27 01:22:32', 1),
(4, 5, 'boleta', 'B001-00000002', 'comprobantes\\B_B001-00000002_20251027.pdf', '2025-10-27 01:23:08', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalles_venta`
--

CREATE TABLE `detalles_venta` (
  `id` int(11) NOT NULL,
  `venta_id` int(11) NOT NULL,
  `medicamento_id` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `detalles_venta`
--

INSERT INTO `detalles_venta` (`id`, `venta_id`, `medicamento_id`, `cantidad`, `precio_unitario`, `subtotal`) VALUES
(1, 1, 1, 1, 5.50, 5.50),
(2, 1, 4, 1, 8.25, 8.25),
(3, 2, 3, 1, 12.90, 12.90),
(4, 2, 5, 2, 2.00, 4.00),
(5, 3, 1, 1, 5.50, 5.50),
(6, 4, 4, 1, 8.25, 8.25),
(7, 5, 2, 1, 7.80, 7.80);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `lotes`
--

CREATE TABLE `lotes` (
  `id` int(11) NOT NULL,
  `medicamento_id` int(11) NOT NULL,
  `proveedor_id` int(11) NOT NULL,
  `numero_lote` varchar(50) NOT NULL,
  `fecha_vencimiento` date NOT NULL,
  `cantidad_inicial` int(11) NOT NULL,
  `cantidad_actual` int(11) NOT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `lotes`
--

INSERT INTO `lotes` (`id`, `medicamento_id`, `proveedor_id`, `numero_lote`, `fecha_vencimiento`, `cantidad_inicial`, `cantidad_actual`, `fecha_creacion`) VALUES
(1, 1, 1, 'L001', '2024-12-31', 100, 100, '2025-09-24 21:50:42'),
(2, 2, 2, 'L002', '2025-06-30', 50, 50, '2025-09-24 21:50:42'),
(3, 3, 1, 'L003', '2024-11-30', 30, 30, '2025-09-24 21:50:42'),
(4, 4, 2, 'L004', '2025-01-15', 80, 80, '2025-09-24 21:50:42'),
(5, 5, 1, '123', '2025-09-24', 2, 2, '2025-09-24 21:53:38'),
(6, 6, 1, '124', '2025-09-24', 2, 2, '2025-09-24 21:56:44'),
(7, 13, 1, '01', '2025-10-28', 3, 3, '2025-10-28 06:08:56');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `medicamentos`
--

CREATE TABLE `medicamentos` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `principio_activo` varchar(100) DEFAULT NULL,
  `laboratorio` varchar(100) DEFAULT NULL,
  `precio` decimal(10,2) NOT NULL,
  `stock` int(11) NOT NULL DEFAULT 0,
  `stock_minimo` int(11) NOT NULL DEFAULT 10,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `medicamentos`
--

INSERT INTO `medicamentos` (`id`, `nombre`, `descripcion`, `principio_activo`, `laboratorio`, `precio`, `stock`, `stock_minimo`, `fecha_creacion`, `activo`) VALUES
(1, 'Paracetamol 500mg', 'Analgésico y antipirético', 'Paracetamol', 'Genfar', 5.50, 98, 20, '2025-09-24 21:50:42', 1),
(2, 'Ibuprofeno 400mg', 'Antiinflamatorio no esteroideo', 'Ibuprofeno', 'Bayer', 7.80, 49, 15, '2025-09-24 21:50:42', 1),
(3, 'Amoxicilina 500mg', 'Antibiótico de amplio espectro', 'Amoxicilina', 'Pfizer', 12.90, 29, 10, '2025-09-24 21:50:42', 1),
(4, 'Loratadina 10mg', 'Antihistamínico', 'Loratadina', 'Sanofi', 8.25, 78, 25, '2025-09-24 21:50:42', 1),
(5, 'Ibuprofeno', 'hola como estas', 'activina', 'actifarm', 2.00, 0, 10, '2025-09-24 21:53:38', 1),
(6, 'Ibuprofeno', 'hola como estas', 'activina', 'actifarm', 2.00, 2, 10, '2025-09-24 21:56:44', 1),
(13, 'Ibomoxilino', 'Hay algo que es ibumoxilino es bueno', 'farma', 'Pfizer', 2.00, 6, 10, '2025-10-28 06:08:56', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `movimientos_inventario`
--

CREATE TABLE `movimientos_inventario` (
  `id` int(11) NOT NULL,
  `medicamento_id` int(11) NOT NULL,
  `tipo` enum('entrada','salida') NOT NULL,
  `cantidad` int(11) NOT NULL,
  `motivo` varchar(200) DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  `fecha_movimiento` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `movimientos_inventario`
--

INSERT INTO `movimientos_inventario` (`id`, `medicamento_id`, `tipo`, `cantidad`, `motivo`, `usuario_id`, `fecha_movimiento`) VALUES
(1, 1, 'salida', 1, 'Venta', 1, '2025-09-24 21:52:55'),
(2, 4, 'salida', 1, 'Venta', 1, '2025-09-24 21:52:55'),
(3, 3, 'salida', 1, 'Venta', 2, '2025-10-27 05:24:53'),
(4, 5, 'salida', 2, 'Venta', 2, '2025-10-27 05:24:53'),
(5, 1, 'salida', 1, 'Venta', 4, '2025-10-27 06:19:44'),
(6, 4, 'salida', 1, 'Venta', 4, '2025-10-27 06:22:32'),
(7, 2, 'salida', 1, 'Venta', 4, '2025-10-27 06:23:08'),
(8, 13, 'entrada', 3, 'Ingreso de lote 01', 3, '2025-10-28 06:08:56');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `proveedores`
--

CREATE TABLE `proveedores` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `contacto` varchar(100) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `direccion` text DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `proveedores`
--

INSERT INTO `proveedores` (`id`, `nombre`, `contacto`, `telefono`, `email`, `direccion`, `fecha_creacion`) VALUES
(1, 'Distribuidora Médica S.A.', 'Juan Pérez', '1234-5678', 'ventas@dmedical.com', 'Av. Principal 123, Ciudad', '2025-09-24 21:50:42'),
(2, 'Farmacéutica Nacional', 'María González', '8765-4321', 'contacto@farmanacional.com', 'Calle Secundaria 456, Ciudad', '2025-09-24 21:50:42');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `perfil` enum('Administrador','Farmacéutico','Cajero','Cliente') NOT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `username`, `password_hash`, `email`, `perfil`, `fecha_creacion`, `activo`) VALUES
(1, 'joseph', '$2b$12$MrbQHVTW42rehXSDQLjG2eEBlaKilnh3XBoKQcDOJ5JfTAyYlBQfO', 'nmapowd@mdka.co', 'Administrador', '2025-09-24 21:52:34', 1),
(2, 'farma', '$2b$12$/s4WNfA9aVjBeotmB9RUVeWLDFix5MHiRUYy/tkdVnuXneXeup0KK', 'farma@dw.com', 'Farmacéutico', '2025-10-26 04:26:18', 1),
(3, 'caj', '$2b$12$shSSxls3AzaLxzntqxOBpuITJgd.Ey5kWFSEb5T/AM.BL7LERcmYq', 'caj@caj.com', 'Cajero', '2025-10-27 05:45:32', 1),
(4, 'administrador', '$2b$12$R9VJL6Ob.PhdDI.vk0RQPeQbHqikIifphlFmTdfUEwMzfqaINaI/e', 'a@farma.com', 'Administrador', '2025-10-27 05:53:16', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ventas`
--

CREATE TABLE `ventas` (
  `id` int(11) NOT NULL,
  `cliente_id` int(11) DEFAULT NULL,
  `total` decimal(10,2) NOT NULL,
  `impuesto` decimal(10,2) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `fecha_venta` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `ventas`
--

INSERT INTO `ventas` (`id`, `cliente_id`, `total`, `impuesto`, `usuario_id`, `fecha_venta`) VALUES
(1, 1, 13.75, 2.20, 1, '2025-09-24 21:52:55'),
(2, 1, 16.90, 2.70, 2, '2025-10-27 05:24:53'),
(3, NULL, 5.50, 0.88, 4, '2025-10-27 06:19:43'),
(4, NULL, 8.25, 1.32, 4, '2025-10-27 06:22:32'),
(5, NULL, 7.80, 1.25, 4, '2025-10-27 06:23:08');

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vista_clientes`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vista_clientes` (
`id` int(11)
,`username` varchar(50)
,`email` varchar(100)
,`fecha_creacion` timestamp
,`activo` tinyint(1)
,`nombres` varchar(100)
,`apellidos` varchar(100)
,`nombre_completo` varchar(201)
,`tipo_documento` enum('DNI','RUC','CE','PASAPORTE')
,`numero_documento` varchar(20)
,`direccion` text
,`telefono` varchar(20)
,`fecha_nacimiento` date
,`genero` enum('Masculino','Femenino','Otro')
,`puntos_acumulados` int(11)
);

-- --------------------------------------------------------

--
-- Estructura para la vista `vista_clientes`
--
DROP TABLE IF EXISTS `vista_clientes`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vista_clientes`  AS SELECT `u`.`id` AS `id`, `u`.`username` AS `username`, `u`.`email` AS `email`, `u`.`fecha_creacion` AS `fecha_creacion`, `u`.`activo` AS `activo`, `c`.`nombres` AS `nombres`, `c`.`apellidos` AS `apellidos`, concat(`c`.`nombres`,' ',`c`.`apellidos`) AS `nombre_completo`, `c`.`tipo_documento` AS `tipo_documento`, `c`.`numero_documento` AS `numero_documento`, `c`.`direccion` AS `direccion`, `c`.`telefono` AS `telefono`, `c`.`fecha_nacimiento` AS `fecha_nacimiento`, `c`.`genero` AS `genero`, `c`.`puntos_acumulados` AS `puntos_acumulados` FROM (`usuarios` `u` join `clientes` `c` on(`u`.`id` = `c`.`id`)) WHERE `u`.`perfil` = 'Cliente' ;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `clientes`
--
ALTER TABLE `clientes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `numero_documento` (`numero_documento`),
  ADD KEY `idx_cliente_documento` (`numero_documento`);

--
-- Indices de la tabla `comprobantes`
--
ALTER TABLE `comprobantes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `numero_comprobante` (`numero_comprobante`),
  ADD KEY `idx_venta_id` (`venta_id`),
  ADD KEY `idx_tipo_comprobante` (`tipo_comprobante`),
  ADD KEY `idx_fecha_emision` (`fecha_emision`),
  ADD KEY `idx_numero_comprobante` (`numero_comprobante`);

--
-- Indices de la tabla `detalles_venta`
--
ALTER TABLE `detalles_venta`
  ADD PRIMARY KEY (`id`),
  ADD KEY `venta_id` (`venta_id`),
  ADD KEY `medicamento_id` (`medicamento_id`);

--
-- Indices de la tabla `lotes`
--
ALTER TABLE `lotes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `medicamento_id` (`medicamento_id`),
  ADD KEY `proveedor_id` (`proveedor_id`);

--
-- Indices de la tabla `medicamentos`
--
ALTER TABLE `medicamentos`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `movimientos_inventario`
--
ALTER TABLE `movimientos_inventario`
  ADD PRIMARY KEY (`id`),
  ADD KEY `medicamento_id` (`medicamento_id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `proveedores`
--
ALTER TABLE `proveedores`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indices de la tabla `ventas`
--
ALTER TABLE `ventas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `fk_venta_cliente` (`cliente_id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `comprobantes`
--
ALTER TABLE `comprobantes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `detalles_venta`
--
ALTER TABLE `detalles_venta`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `lotes`
--
ALTER TABLE `lotes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `medicamentos`
--
ALTER TABLE `medicamentos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT de la tabla `movimientos_inventario`
--
ALTER TABLE `movimientos_inventario`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `proveedores`
--
ALTER TABLE `proveedores`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `ventas`
--
ALTER TABLE `ventas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `clientes`
--
ALTER TABLE `clientes`
  ADD CONSTRAINT `clientes_ibfk_1` FOREIGN KEY (`id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `comprobantes`
--
ALTER TABLE `comprobantes`
  ADD CONSTRAINT `comprobantes_ibfk_1` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `detalles_venta`
--
ALTER TABLE `detalles_venta`
  ADD CONSTRAINT `detalles_venta_ibfk_1` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`),
  ADD CONSTRAINT `detalles_venta_ibfk_2` FOREIGN KEY (`medicamento_id`) REFERENCES `medicamentos` (`id`);

--
-- Filtros para la tabla `lotes`
--
ALTER TABLE `lotes`
  ADD CONSTRAINT `lotes_ibfk_1` FOREIGN KEY (`medicamento_id`) REFERENCES `medicamentos` (`id`),
  ADD CONSTRAINT `lotes_ibfk_2` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedores` (`id`);

--
-- Filtros para la tabla `movimientos_inventario`
--
ALTER TABLE `movimientos_inventario`
  ADD CONSTRAINT `movimientos_inventario_ibfk_1` FOREIGN KEY (`medicamento_id`) REFERENCES `medicamentos` (`id`),
  ADD CONSTRAINT `movimientos_inventario_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `ventas`
--
ALTER TABLE `ventas`
  ADD CONSTRAINT `fk_venta_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
