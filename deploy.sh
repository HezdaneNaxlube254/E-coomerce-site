#!/bin/bash

echo "=== Ecommerce System Deployment Script ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Update system
echo "1. Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "2. Installing dependencies..."
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git

# Create system user
echo "3. Creating system user..."
if ! id "ecommerce" >/dev/null 2>&1; then
    useradd -m -s /bin/bash ecommerce
fi

# Clone or update code
echo "4. Setting up application..."
DEPLOY_DIR="/opt/ecommerce"
if [ -d "$DEPLOY_DIR" ]; then
    echo "   Updating existing installation..."
    cd $DEPLOY_DIR
    sudo -u ecommerce git pull
else
    echo "   Cloning repository..."
    mkdir -p $DEPLOY_DIR
    # Note: Replace with your actual repository URL
    # sudo -u ecommerce git clone <your-repo-url> $DEPLOY_DIR
    echo "   Please manually clone your repository to $DEPLOY_DIR"
    echo "   Then run: sudo -u ecommerce cp -r /path/to/your/local/copy/* $DEPLOY_DIR/"
    exit 1
fi

cd $DEPLOY_DIR

# Set up virtual environment
echo "5. Setting up Python environment..."
sudo -u ecommerce python3 -m venv venv
sudo -u ecommerce venv/bin/pip install --upgrade pip
sudo -u ecommerce venv/bin/pip install -r requirements.txt

# Set up environment file
echo "6. Configuring environment..."
if [ ! -f ".env" ]; then
    sudo -u ecommerce cp .env.example .env
    echo "   Please edit $DEPLOY_DIR/.env with production values"
    echo "   Then run this script again"
    exit 1
fi

# Set up database
echo "7. Setting up database..."
sudo -u postgres psql -c "CREATE DATABASE ecommerce_production;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER ecommerce_user WITH PASSWORD '$(grep DB_PASSWORD .env | cut -d= -f2)';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ecommerce_production TO ecommerce_user;"

# Run Django commands
echo "8. Running Django setup..."
sudo -u ecommerce venv/bin/python manage.py migrate
sudo -u ecommerce venv/bin/python manage.py collectstatic --noinput

# Set up Gunicorn service
echo "9. Setting up Gunicorn service..."
cat > /etc/systemd/system/ecommerce.service << SERVICE
[Unit]
Description=Ecommerce System
After=network.target postgresql.service

[Service]
User=ecommerce
Group=ecommerce
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=ecommerce.settings"
ExecStart=$DEPLOY_DIR/venv/bin/gunicorn ecommerce.wsgi:application -c gunicorn.conf.py

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable ecommerce
systemctl start ecommerce

# Set up Nginx
echo "10. Setting up Nginx..."
cat > /etc/nginx/sites-available/ecommerce << NGINX
server {
    listen 80;
    server_name _;
    
    location /static/ {
        alias $DEPLOY_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias $DEPLOY_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/ecommerce /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Create superuser: sudo -u ecommerce $DEPLOY_DIR/venv/bin/python manage.py createsuperuser"
echo "2. Set up SSL with Let's Encrypt: certbot --nginx"
echo "3. Configure firewall: ufw allow 80,443/tcp"
echo "4. Test the system: curl http://localhost/health/"
echo ""
echo "System will be available at: http://$(curl -s ifconfig.me)/"
