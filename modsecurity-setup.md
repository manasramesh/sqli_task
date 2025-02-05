# ModSecurity WAF Setup with Nginx

## Step 1: Install Dependencies

```bash
sudo apt update
sudo apt install -y git build-essential libpcre3 libpcre3-dev zlib1g zlib1g-dev \
libssl-dev libxml2-dev libgeoip-dev libyajl-dev libcurl4-openssl-dev
```

## Step 2: Build ModSecurity

```bash
git clone --depth 1 https://github.com/SpiderLabs/ModSecurity
cd ModSecurity
git submodule init && git submodule update
./build.sh
./configure
make
sudo make install
```

## Step 3: Compile Nginx with ModSecurity Module

### Download Nginx Source & Connector

```bash
wget https://nginx.org/download/nginx-1.24.0.tar.gz
tar -xvzf nginx-1.24.0.tar.gz
git clone --depth 1 https://github.com/SpiderLabs/ModSecurity-nginx
```

### Compile Nginx

```bash
cd nginx-1.24.0
./configure --add-module=../ModSecurity-nginx \
            --with-http_ssl_module \
            --with-http_realip_module \
            --pid-path=/run/nginx.pid
make
sudo make install
```

### Replace Package Manager's Nginx Binary

```bash
sudo systemctl stop nginx
sudo mv /usr/sbin/nginx /usr/sbin/nginx.old  # Backup
sudo cp objs/nginx /usr/sbin/nginx  # Use compiled binary
```

## Step 4: Configure ModSecurity

```bash
sudo mkdir -p /etc/nginx/modsec
sudo cp ModSecurity/modsecurity.conf-recommended /etc/nginx/modsec/
sudo cp ModSecurity/unicode.mapping /etc/nginx/modsec/
```

Edit `/etc/nginx/modsec/modsecurity.conf`:

```nginx
SecRuleEngine On
SecAuditLog /var/log/nginx/modsec_audit.log
```

## Step 5: Set Up OWASP CRS (SQLi Focus)

```bash
sudo git clone --depth 1 https://github.com/coreruleset/coreruleset /etc/nginx/modsec/crs
sudo cp /etc/nginx/modsec/crs/crs-setup.conf.example /etc/nginx/modsec/crs-setup.conf
```

Edit `/etc/nginx/modsec/main.conf`:

```nginx
Include /etc/nginx/modsec/modsecurity.conf
Include /etc/nginx/modsec/crs-setup.conf
Include /etc/nginx/modsec/crs/rules/REQUEST-942-APPLICATION-ATTACK-SQLI.conf
```

## Step 6: Configure Nginx

### Add to Nginx Config 
In `/etc/nginx/sites-available/your-site`:

```nginx
server {
  modsecurity on;
  modsecurity_rules_file /etc/nginx/modsec/main.conf;
  # ... rest of your config
}
```

### Create PID Directory

```bash
sudo mkdir -p /run/nginx
sudo chown -R www-data:www-data /run/nginx
```

## Step 7: Fix Audit Logging

```bash
sudo touch /var/log/nginx/modsec_audit.log
sudo chown www-data:www-data /var/log/nginx/modsec_audit.log
sudo chmod 644 /var/log/nginx/modsec_audit.log
```

## Step 8: Systemd Service Setup

Edit `/lib/systemd/system/nginx.service`:

```ini
[Service]
PIDFile=/run/nginx.pid
TimeoutStartSec=300
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

## Step 9: Test & Post-Install Tuning

### Verify Nginx

```bash
sudo nginx -t && sudo systemctl restart nginx
```

### Test SQLi Blocking

```bash
curl -I "http://localhost/?id=1%20AND%201=1"
```

### Disable False Positive Rule (920350)
Create `/etc/nginx/modsec/custom.conf`:

```nginx
# Allow numeric IPs in Host header (disable Rule 920350)
SecRuleUpdateTargetById 920350 !REQUEST_HEADERS:Host
```

### Reload Configuration

```bash
sudo systemctl reload nginx
```