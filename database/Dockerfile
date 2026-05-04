FROM mysql:8.0

# Add your SQL initialization script
ADD ./create_table.sql /docker-entrypoint-initdb.d/1.sql

# Set environment variables for MySQL
ENV MYSQL_USER=h2
ENV MYSQL_PASSWORD=EXAMPLE-password
ENV MYSQL_DATABASE=h2_web_scraping
ENV MYSQL_ROOT_PASSWORD=EXAMPLE-root-password

# Expose port 3306 for MySQL
EXPOSE 3306
