-- Production-like Database Schema and Data
-- E-Commerce Application Database

-- Users table (customers and employees)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    credit_card_last4 VARCHAR(4),
    role VARCHAR(50) DEFAULT 'customer',
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    sku VARCHAR(100) UNIQUE,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    shipping_address TEXT,
    tracking_number VARCHAR(100),
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment transactions table
CREATE TABLE IF NOT EXISTS payment_transactions (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    status VARCHAR(50),
    gateway_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(255),
    resource VARCHAR(255),
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DEMO ONLY — all passwords and personal data below are fake, for vulnerability demonstration purposes only
INSERT INTO users (email, password, first_name, last_name, phone, address, city, state, zip_code, credit_card_last4, role, total_orders, total_spent) VALUES
('john.doe@email.com', 'password123', 'John', 'Doe', '555-0101', '123 Main St', 'New York', 'NY', '10001', '4532', 'customer', 15, 2847.50),
('jane.smith@email.com', 'pass456', 'Jane', 'Smith', '555-0102', '456 Oak Ave', 'Los Angeles', 'CA', '90001', '5421', 'customer', 8, 1234.75),
('mike.johnson@email.com', 'mike2024', 'Mike', 'Johnson', '555-0103', '789 Pine Rd', 'Chicago', 'IL', '60601', '4916', 'customer', 23, 4521.30),
('sarah.williams@email.com', 'sarah123', 'Sarah', 'Williams', '555-0104', '321 Elm St', 'Houston', 'TX', '77001', '4024', 'customer', 12, 1876.90),
('david.brown@email.com', 'david456', 'David', 'Brown', '555-0105', '654 Maple Dr', 'Phoenix', 'AZ', '85001', '5105', 'customer', 19, 3245.60),
('emily.davis@email.com', 'emily789', 'Emily', 'Davis', '555-0106', '987 Cedar Ln', 'Philadelphia', 'PA', '19101', '4539', 'customer', 7, 987.25),
('chris.miller@email.com', 'chris2024', 'Chris', 'Miller', '555-0107', '147 Birch Way', 'San Antonio', 'TX', '78201', '4485', 'customer', 31, 5678.40),
('lisa.wilson@email.com', 'lisa123', 'Lisa', 'Wilson', '555-0108', '258 Spruce Ct', 'San Diego', 'CA', '92101', '4716', 'customer', 14, 2134.80),
('admin@company.com', 'admin2024', 'Admin', 'User', '555-0001', '1 Corporate Plaza', 'Seattle', 'WA', '98101', NULL, 'admin', 0, 0.00),
('support@company.com', 'support2024', 'Support', 'Team', '555-0002', '1 Corporate Plaza', 'Seattle', 'WA', '98101', NULL, 'support', 0, 0.00),
('robert.taylor@email.com', 'robert456', 'Robert', 'Taylor', '555-0109', '369 Willow St', 'Dallas', 'TX', '75201', '5234', 'customer', 9, 1456.70),
('jennifer.anderson@email.com', 'jennifer789', 'Jennifer', 'Anderson', '555-0110', '741 Ash Blvd', 'San Jose', 'CA', '95101', '4929', 'customer', 16, 2987.35),
('william.thomas@email.com', 'william123', 'William', 'Thomas', '555-0111', '852 Poplar Ave', 'Austin', 'TX', '78701', '4556', 'customer', 11, 1789.50),
('amanda.jackson@email.com', 'amanda456', 'Amanda', 'Jackson', '555-0112', '963 Hickory Rd', 'Jacksonville', 'FL', '32099', '5678', 'customer', 20, 3876.90),
('james.white@email.com', 'james789', 'James', 'White', '555-0113', '159 Walnut Dr', 'Fort Worth', 'TX', '76101', '4812', 'customer', 6, 876.40);

-- Insert realistic product data
INSERT INTO products (name, description, category, price, stock_quantity, sku) VALUES
('Wireless Bluetooth Headphones', 'Premium noise-cancelling headphones with 30hr battery', 'Electronics', 149.99, 245, 'ELEC-WBH-001'),
('Smart Watch Pro', 'Fitness tracking smartwatch with heart rate monitor', 'Electronics', 299.99, 178, 'ELEC-SWP-002'),
('Laptop Backpack', 'Water-resistant backpack with laptop compartment', 'Accessories', 59.99, 432, 'ACC-LBP-003'),
('USB-C Charging Cable', '6ft braided USB-C fast charging cable', 'Electronics', 19.99, 1250, 'ELEC-UCC-004'),
('Portable Power Bank', '20000mAh portable charger with dual USB ports', 'Electronics', 39.99, 567, 'ELEC-PPB-005'),
('Wireless Mouse', 'Ergonomic wireless mouse with precision tracking', 'Electronics', 29.99, 823, 'ELEC-WM-006'),
('Mechanical Keyboard', 'RGB backlit mechanical gaming keyboard', 'Electronics', 89.99, 156, 'ELEC-MK-007'),
('Phone Case Premium', 'Shockproof protective case for smartphones', 'Accessories', 24.99, 945, 'ACC-PCP-008'),
('Screen Protector', 'Tempered glass screen protector 3-pack', 'Accessories', 14.99, 1567, 'ACC-SP-009'),
('Webcam HD 1080p', 'Full HD webcam with built-in microphone', 'Electronics', 79.99, 234, 'ELEC-WHD-010'),
('Desk Lamp LED', 'Adjustable LED desk lamp with USB charging port', 'Home', 34.99, 456, 'HOME-DL-011'),
('Coffee Maker', 'Programmable 12-cup coffee maker', 'Home', 69.99, 189, 'HOME-CM-012'),
('Yoga Mat Premium', 'Extra thick non-slip exercise yoga mat', 'Sports', 44.99, 678, 'SPORT-YM-013'),
('Water Bottle Insulated', '32oz stainless steel insulated water bottle', 'Sports', 27.99, 892, 'SPORT-WB-014'),
('Running Shoes', 'Lightweight breathable running shoes', 'Sports', 119.99, 234, 'SPORT-RS-015');

-- Insert realistic order data
INSERT INTO orders (user_id, total, status, shipping_address, tracking_number, payment_method, payment_status, created_at) VALUES
(1, 179.98, 'completed', '123 Main St, New York, NY 10001', 'TRK1234567890', 'credit_card', 'completed', '2024-03-15 10:23:45'),
(1, 89.99, 'shipped', '123 Main St, New York, NY 10001', 'TRK1234567891', 'credit_card', 'completed', '2024-03-18 14:56:12'),
(2, 299.99, 'completed', '456 Oak Ave, Los Angeles, CA 90001', 'TRK1234567892', 'paypal', 'completed', '2024-03-10 09:15:33'),
(3, 149.99, 'pending', '789 Pine Rd, Chicago, IL 60601', NULL, 'credit_card', 'pending', '2024-03-20 16:42:18'),
(4, 94.98, 'shipped', '321 Elm St, Houston, TX 77001', 'TRK1234567893', 'credit_card', 'completed', '2024-03-17 11:28:54'),
(5, 199.98, 'completed', '654 Maple Dr, Phoenix, AZ 85001', 'TRK1234567894', 'credit_card', 'completed', '2024-03-12 13:45:22'),
(6, 59.99, 'completed', '987 Cedar Ln, Philadelphia, PA 19101', 'TRK1234567895', 'paypal', 'completed', '2024-03-14 08:33:17'),
(7, 329.97, 'shipped', '147 Birch Way, San Antonio, TX 78201', 'TRK1234567896', 'credit_card', 'completed', '2024-03-19 15:12:44'),
(8, 119.99, 'pending', '258 Spruce Ct, San Diego, CA 92101', NULL, 'credit_card', 'pending', '2024-03-20 17:55:09'),
(11, 74.98, 'completed', '369 Willow St, Dallas, TX 75201', 'TRK1234567897', 'credit_card', 'completed', '2024-03-16 10:18:36'),
(12, 209.98, 'shipped', '741 Ash Blvd, San Jose, CA 95101', 'TRK1234567898', 'paypal', 'completed', '2024-03-18 12:47:23'),
(13, 89.99, 'completed', '852 Poplar Ave, Austin, TX 78701', 'TRK1234567899', 'credit_card', 'completed', '2024-03-11 14:22:51'),
(14, 449.97, 'shipped', '963 Hickory Rd, Jacksonville, FL 32099', 'TRK1234567900', 'credit_card', 'completed', '2024-03-19 09:38:14'),
(15, 44.99, 'pending', '159 Walnut Dr, Fort Worth, TX 76101', NULL, 'paypal', 'pending', '2024-03-20 18:15:42');

-- Insert order items
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 149.99),
(1, 4, 1, 19.99),
(2, 7, 1, 89.99),
(3, 2, 1, 299.99),
(4, 1, 1, 149.99),
(5, 8, 2, 24.99),
(5, 9, 3, 14.99),
(6, 3, 1, 59.99),
(6, 5, 1, 39.99),
(6, 6, 1, 29.99),
(6, 4, 1, 19.99),
(7, 3, 1, 59.99),
(8, 2, 1, 299.99),
(8, 4, 1, 19.99),
(9, 15, 1, 119.99),
(10, 11, 1, 34.99),
(10, 5, 1, 39.99),
(11, 10, 1, 79.99),
(11, 1, 1, 149.99),
(12, 7, 1, 89.99),
(13, 2, 1, 299.99),
(13, 1, 1, 149.99),
(14, 13, 1, 44.99);

-- Insert payment transactions
INSERT INTO payment_transactions (order_id, amount, payment_method, transaction_id, status, gateway_response) VALUES
(1, 179.98, 'credit_card', 'ch_3MtwBwLkdIwHu7ix0B3tqA7p', 'success', '{"status": "succeeded", "card_brand": "visa"}'),
(2, 89.99, 'credit_card', 'ch_3MtwBwLkdIwHu7ix0B3tqA8q', 'success', '{"status": "succeeded", "card_brand": "mastercard"}'),
(3, 299.99, 'paypal', 'PAYID-MXYZ123ABC456', 'success', '{"status": "COMPLETED", "payer_email": "jane.smith@email.com"}'),
(5, 94.98, 'credit_card', 'ch_3MtwBwLkdIwHu7ix0B3tqA9r', 'success', '{"status": "succeeded", "card_brand": "visa"}'),
(6, 199.98, 'credit_card', 'ch_3MtwBwLkdIwHu7ix0B3tqB0s', 'success', '{"status": "succeeded", "card_brand": "amex"}'),
(7, 59.99, 'paypal', 'PAYID-MXYZ789DEF012', 'success', '{"status": "COMPLETED", "payer_email": "emily.davis@email.com"}'),
(8, 329.97, 'credit_card', 'ch_3MtwBwLkdIwHu7ix0B3tqB1t', 'success', '{"status": "succeeded", "card_brand": "visa"}'),
(10, 74.98, 'credit_card', 'ch_3MtwBwLkdIwHu7ix0B3tqB2u', 'success', '{"status": "succeeded", "card_brand": "mastercard"}'),
(11, 209.98, 'paypal', 'PAYID-MXYZ345GHI678', 'success', '{"status": "COMPLETED", "payer_email": "jennifer.anderson@email.com"}'),
(12, 89.99, 'credit_card', 'ch_3MtwBwLkdIwHu7ix0B3tqB3v', 'success', '{"status": "succeeded", "card_brand": "visa"}'),
(13, 449.97, 'credit_card', 'ch_3MtwBwLkdIwHu7ix0B3tqB4w', 'success', '{"status": "succeeded", "card_brand": "discover"}');

-- Insert audit logs
INSERT INTO audit_logs (user_id, action, resource, ip_address, user_agent) VALUES
(1, 'LOGIN', '/api/auth/login', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
(1, 'VIEW_ORDER', '/api/orders/1', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
(2, 'LOGIN', '/api/auth/login', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'),
(3, 'CREATE_ORDER', '/api/orders', '192.168.1.102', 'Mozilla/5.0 (X11; Linux x86_64)'),
(9, 'LOGIN', '/api/auth/login', '10.0.0.50', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
(9, 'VIEW_CUSTOMERS', '/api/admin/users', '10.0.0.50', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
(4, 'UPDATE_PROFILE', '/api/users/4', '192.168.1.103', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)'),
(5, 'LOGIN', '/api/auth/login', '192.168.1.104', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
(6, 'CREATE_ORDER', '/api/orders', '192.168.1.105', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'),
(7, 'LOGIN', '/api/auth/login', '192.168.1.106', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64)');

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_payment_transactions_order_id ON payment_transactions(order_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
