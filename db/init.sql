CREATE TABLE IF NOT EXISTS todos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task VARCHAR(255) NOT NULL,
    status ENUM('pending', 'completed', 'archived') DEFAULT 'pending',
    
    CONSTRAINT chk_task_not_empty CHECK (CHAR_LENGTH(TRIM(task)) > 0),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;