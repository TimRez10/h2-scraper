CREATE TABLE regulation_policy_urls (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    link VARCHAR(400) NOT NULL UNIQUE,
    title VARCHAR(250),
    news_type VARCHAR(50),
    source VARCHAR(50),
    date_published DATETIME NOT NULL,
    region VARCHAR(50),
    rel_score TINYINT,
    h2_mentioned TINYINT,
    tags VARCHAR(150),
    classification VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX (date_published)
);
