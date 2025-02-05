# SQL Injection Testing Environment

A comprehensive dual-application environment for demonstrating SQL injection vulnerabilities and security practices. The project consists of two applications:
- App1: Vulnerable application (intentionally contains SQL injection vulnerabilities)
- App2: Secure application (implements secure coding practices + ModSecurity WAF protection)

## Architecture Overview

```
/var/www/login_app/
├── app1/                    # Vulnerable Application
│   ├── app.py              # Flask application with SQL injection vulnerability
│   └── templates/
│       └── login.html      # Basic login form
├── app2/                    # Secured Application
│   ├── app.py              # Flask application with secure coding practices
│   └── templates/
│       └── login.html      # Login form with input validation
└── venv/                    # Python Virtual Environment

System Components:
├── Nginx                    # Reverse Proxy (Port 80)
│   └── ModSecurity WAF     # Web Application Firewall (for app2)
├── MySQL                    # Database Backend (Ports: 3306, 33060)
│   └── password_system     # Database name
├── Gunicorn (app1)         # WSGI Server (Port 8001)
└── Gunicorn (app2)         # WSGI Server (Port 8002)
```

## Security Features Comparison

### App1 (Vulnerable)
- Direct SQL query construction
- No input validation
- No prepared statements
- Vulnerable to SQL injection

### App2 (Secured)
- Secure coding practices:
  - Parameterized queries
  - Input validation
  - Error handling
  - Prepared statements
- ModSecurity WAF protection:
  - OWASP Core Rule Set (CRS)
  - SQL Injection protection
  - Request filtering
  - Security headers

## Prerequisites

- Ubuntu Server (20.04 LTS or higher recommended)
- Python 3.x
- Open ports:
  - 22 (SSH)
  - 80 (HTTP)
  - 3306 (MySQL - internal only)
- Minimum system requirements:
  - 2GB RAM
  - 20GB storage
  - 2 vCPUs

## Detailed Installation Guide

### 1. Initial System Setup

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install python3-pip python3-venv nginx mysql-server -y
```

### 2. MySQL Database Setup

```bash
# Start and enable MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql
sudo systemctl status mysql

# Secure MySQL installation
sudo mysql_secure_installation
# Follow the prompts:
# - Set root password: Jackychan@123
# - Remove anonymous users: Yes
# - Disallow root login remotely: Yes
# - Remove test database: Yes
# - Reload privilege tables: Yes

# Access MySQL
sudo mysql -u root -p
```

Database Configuration:
```sql
-- Create and use database
CREATE DATABASE IF NOT EXISTS password_system;
USE password_system;

-- Create passwords table
CREATE TABLE IF NOT EXISTS passwords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP NULL
);

-- Create performance index
CREATE INDEX idx_password ON passwords(password_hash);

-- Insert test data
INSERT INTO passwords (password_hash) VALUES
('Password123'),
('Admin555'),
('Test789'),
('User2024'),
('Login999');

-- Verify data
SELECT * FROM passwords;
```

### 3. Application Directory Setup

```bash
# Create application structure
sudo mkdir -p /var/www/login_app/{app1,app2}/templates
cd /var/www/login_app

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install flask mysql-connector-python gunicorn
```

### 4. Application Deployment

```bash
# Copy application files
sudo cp app1.py /var/www/login_app/app1/app.py
sudo cp app2.py /var/www/login_app/app2/app.py
sudo cp page1.html /var/www/login_app/app1/templates/login.html
sudo cp page2.html /var/www/login_app/app2/templates/login.html
```

### 5. Nginx Configuration

Create Nginx configuration file:
```bash
sudo nano /etc/nginx/sites-available/login_app
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name your_server_ip;  # Replace with your server IP or domain

    location /app1 {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /app2 {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # ModSecurity Configuration
        modsecurity on;
        modsecurity_rules_file /etc/nginx/modsec/main.conf;
    }
}
```

Enable the configuration:
```bash
sudo ln -s /etc/nginx/sites-available/login_app /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Systemd Service Configuration

Create App1 service file:
```bash
sudo nano /etc/systemd/system/login_app1.service
```

```ini
[Unit]
Description=Login App 1
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/login_app/app1
Environment="PATH=/var/www/login_app/venv/bin"
ExecStart=/var/www/login_app/venv/bin/gunicorn --workers 3 --bind localhost:8001 app:app

[Install]
WantedBy=multi-user.target
```

Create App2 service file:
```bash
sudo nano /etc/systemd/system/login_app2.service
```

```ini
[Unit]
Description=Login App 2
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/login_app/app2
Environment="PATH=/var/www/login_app/venv/bin"
ExecStart=/var/www/login_app/venv/bin/gunicorn --workers 3 --bind localhost:8002 app:app

[Install]
WantedBy=multi-user.target
```

Set permissions and start services:
```bash
# Set proper permissions
sudo chown -R www-data:www-data /var/www/login_app
sudo chmod -R 755 /var/www/login_app

# Start and enable services
sudo systemctl start login_app1 login_app2
sudo systemctl enable login_app1 login_app2

# Verify service status
sudo systemctl status login_app1
sudo systemctl status login_app2
```

### 7. ModSecurity WAF Setup

#### Install Dependencies
```bash
sudo apt install -y git build-essential libpcre3 libpcre3-dev zlib1g zlib1g-dev \
libssl-dev libxml2-dev libgeoip-dev libyajl-dev libcurl4-openssl-dev
```

#### Build and Install ModSecurity
```bash
# Clone and build ModSecurity
git clone --depth 1 https://github.com/SpiderLabs/ModSecurity
cd ModSecurity
git submodule init && git submodule update
./build.sh
./configure
make
sudo make install
```

#### Install Nginx with ModSecurity Module
```bash
# Download and extract Nginx source
wget https://nginx.org/download/nginx-1.24.0.tar.gz
tar -xvzf nginx-1.24.0.tar.gz

# Clone ModSecurity-nginx connector
git clone --depth 1 https://github.com/SpiderLabs/ModSecurity-nginx

# Compile Nginx with ModSecurity
cd nginx-1.24.0
./configure --add-module=../ModSecurity-nginx \
            --with-http_ssl_module \
            --with-http_realip_module \
            --pid-path=/run/nginx.pid
make
sudo make install

# Backup and replace Nginx binary
sudo systemctl stop nginx
sudo mv /usr/sbin/nginx /usr/sbin/nginx.old
sudo cp objs/nginx /usr/sbin/nginx
```

#### Configure ModSecurity
```bash
# Setup ModSecurity configuration directories
sudo mkdir -p /etc/nginx/modsec
sudo cp ModSecurity/modsecurity.conf-recommended /etc/nginx/modsec/modsecurity.conf
sudo cp ModSecurity/unicode.mapping /etc/nginx/modsec/

# Configure ModSecurity
sudo nano /etc/nginx/modsec/modsecurity.conf
```

Update the following settings:
```nginx
SecRuleEngine On
SecAuditLog /var/log/nginx/modsec_audit.log
```

#### Install OWASP CRS
```bash
# Clone OWASP CRS
sudo git clone --depth 1 https://github.com/coreruleset/coreruleset /etc/nginx/modsec/crs
sudo cp /etc/nginx/modsec/crs/crs-setup.conf.example /etc/nginx/modsec/crs-setup.conf

# Create main configuration file
sudo nano /etc/nginx/modsec/main.conf
```

Add the following:
```nginx
Include /etc/nginx/modsec/modsecurity.conf
Include /etc/nginx/modsec/crs-setup.conf
Include /etc/nginx/modsec/crs/rules/REQUEST-942-APPLICATION-ATTACK-SQLI.conf
```

#### Setup Logging
```bash
sudo touch /var/log/nginx/modsec_audit.log
sudo chown www-data:www-data /var/log/nginx/modsec_audit.log
sudo chmod 644 /var/log/nginx/modsec_audit.log
```

#### Update Systemd Service
```bash
sudo nano /lib/systemd/system/nginx.service
```

Add:
```ini
[Service]
PIDFile=/run/nginx.pid
TimeoutStartSec=300
```

Reload configurations:
```bash
sudo systemctl daemon-reload
sudo nginx -t
sudo systemctl restart nginx
```

## Testing the Applications

### Test Credentials
```
Username/Password combinations:
1. Password123
2. Admin555
3. Test789
4. User2024
5. Login999
```

### Access Points
- Vulnerable App: `http://your_server_ip/app1`
- Secure App: `http://your_server_ip/app2`

### SQL Injection Testing
1. Basic Tests:
   ```sql
   ' OR '1'='1
   ' UNION SELECT * FROM passwords--
   admin' --
   ```

2. WAF Testing (App2):
   ```
   curl -I "http://your_server_ip/app2/?id=1%20AND%201=1"
   ```

## Troubleshooting

1. Check service status:
   ```bash
   sudo systemctl status nginx
   sudo systemctl status login_app1
   sudo systemctl status login_app2
   sudo systemctl status mysql
   ```

2. View logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   sudo tail -f /var/log/nginx/modsec_audit.log
   sudo journalctl -u login_app1
   sudo journalctl -u login_app2
   ```

## Security Considerations

1. This setup is for educational purposes only
2. App1 contains intentional vulnerabilities
3. Do not expose App1 to public networks
4. Change default passwords in production
5. Keep all components updated
6. Monitor ModSecurity logs for attacks

## License

This project is for educational purposes only. Use at your own risk.

## Disclaimer

This project contains intentionally vulnerable code for educational purposes. Do not deploy App1 in a production environment.