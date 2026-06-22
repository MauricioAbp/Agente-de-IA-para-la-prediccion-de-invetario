CREATE DATABASE IF NOT EXISTS sistema_inventario_ml;
USE sistema_inventario_ml;

CREATE TABLE productos(
	id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    stock_actual INT NOT NULL DEFAULT 0,
    costo_almacenamiento_diario DECIMAL(10,2) NOT NULL,
    precio_venta DECIMAL(10,2) NOT NULL
);

CREATE TABLE historial_ventas(
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT,
    fecha DATE NOT NULL,
    cantidad_vendida INT NOT NULL,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE registro_acciones_agente(
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT,
    fecha DATE NOT NULL,
    estado_stock_inicial INT NOT NULL,
    accion_compra INT NOT NULL,
    recompensa_obtenida DECIMAL(10,2)NOT NULL,
    FOREIGN KEY(producto_id) REFERENCES productos(id)
);

INSERT INTO productos(nombre, sku, stock_actual, costo_almacenamiento_diario, precio_venta)
VALUES('Cafe Premiun CAF-101','CAF-101',30,0.50,15.00);
INSERT INTO historial_ventas(producto_id, fecha, cantidad_vendida)VALUES
(1, '2026-05-11', 12), 
(1, '2026-05-12', 8),  
(1, '2026-05-13', 15), 
(1, '2026-05-14', 4),  
(1, '2026-05-15', 20), 
(1, '2026-05-16', 18), 
(1, '2026-05-17', 0), 
(1, '2026-05-18', 10), 
(1, '2026-05-19', 5),  
(1, '2026-05-20', 7),  
(1, '2026-05-21', 3), 
(1, '2026-05-22', 22), 
(1, '2026-05-23', 15), 
(1, '2026-05-24', 0);  

SELECT * FROM historial_ventas;