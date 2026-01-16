# Ecommerce Internal System

A Django-based internal management system for ecommerce operations with role-based access control, product catalog, order management, and audit logging.

## Features

- **Role-based Access Control** (Admin, Staff, Viewer)
- **Product Catalog** with image uploads and inventory tracking
- **Order Management** with validated state transitions
- **Audit Logging** for all critical operations
- **Session-based Cart** (7-day expiry)
- **Bootstrap 5 UI** with responsive design
- **Comprehensive Testing** (>80% code coverage)

## Quick Start

### 1. Prerequisites

- Python 3.9+
- PostgreSQL (optional, SQLite3 default)
- Redis (optional, for sessions)

### 2. Installation

```bash
# Clone repository
git clone <repository-url>
cd ecommerce

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env file with your settings
# Set DEBUG=True for development
# Set SECRET_KEY to a secure value

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Generate fake data (optional)
python manage.py generate_fake_data --products 50 --orders 20
3. Development Server
bash
python manage.py runserver
Visit http://localhost:8000

4. Testing
bash
# Run all tests
python manage.py test

# Run tests with coverage
coverage run manage.py test
coverage report -m
Deployment
1. Production Settings
Update .env file:

text
DEBUG=False
SECRET_KEY=<your-secure-secret-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=ecommerce
DB_USER=youruser
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
2. Gunicorn
bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn ecommerce.wsgi:application -c gunicorn.conf.py
3. Systemd Service
Create /etc/systemd/system/ecommerce.service:

ini
[Unit]
Description=Ecommerce Internal System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/ecommerce
Environment="PATH=/path/to/ecommerce/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=ecommerce.settings"
ExecStart=/path/to/ecommerce/venv/bin/gunicorn ecommerce.wsgi:application -c gunicorn.conf.py

[Install]
WantedBy=multi-user.target
bash
sudo systemctl daemon-reload
sudo systemctl start ecommerce
sudo systemctl enable ecommerce
4. Nginx Configuration
/etc/nginx/sites-available/ecommerce:

nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /static/ {
        alias /path/to/ecommerce/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /path/to/ecommerce/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
User Roles
Role	Permissions
Viewer	View products and orders only
Staff	View + Create/Edit products and orders
Admin	All permissions + User management + System settings
Order Workflow
Draft → Order created but not submitted

Pending → Order submitted, awaiting processing

Processing → Order being prepared, stock deducted

Shipped → Order shipped to customer

Delivered → Order completed

Cancelled → Order cancelled at any point before delivery

API Endpoints
/health/ - System health check

/admin/ - Django admin interface

/products/ - Product management

/orders/ - Order management

/users/ - User authentication

Management Commands
bash
# Generate fake data for testing
python manage.py generate_fake_data --products 100 --orders 50

# Export orders to CSV
python manage.py export_orders_csv --status delivered --date-from 2024-01-01

# Check system health
python manage.py check --deploy
Security
CSRF protection enabled

Login required for all views

File upload validation (2MB max, JPG/PNG only)

SQL injection protection via Django ORM

XSS protection via template auto-escaping

Clickjacking protection via X-Frame-Options

Secure password validation

Monitoring
Sentry integration (via SENTRY_DSN env var)

File logging at logs/django.log

Health check endpoint at /health/

Audit logging for all critical operations

Backup & Maintenance
Daily Tasks
Check system logs for errors

Verify database backups

Monitor disk space usage

Weekly Tasks
Clean up old session data

Review audit logs

Update dependencies

Database Backup
bash
# PostgreSQL
pg_dump ecommerce > backup_$(date +%Y%m%d).sql

# SQLite
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
Troubleshooting
Common Issues
Static files not loading

Run python manage.py collectstatic

Check Nginx/Apache configuration

Verify file permissions

Database connection errors

Check .env file settings

Verify database service is running

Check network connectivity

Permission denied errors

Verify file permissions in media/ and staticfiles/

Check SELinux/AppArmor settings

Logs Location
Application logs: logs/django.log

Gunicorn logs: System journal (journalctl -u ecommerce)

Nginx logs: /var/log/nginx/error.log

Support
For issues and feature requests, please contact:

System Administrator: admin@example.com

Technical Support: support@example.com

License
Proprietary - Internal Use Only

## Production Deployment

### Quick Deployment with Docker (Recommended)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Create superuser (optional, remove in production)
# RUN echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin@example.com', 'password123')" | python manage.py shell

EXPOSE 8000

CMD ["gunicorn", "ecommerce.wsgi:application", "--bind", "0.0.0.0:8000"]
Manual Deployment
Clone repository:

bash
git clone <your-repo-url>
cd ecommerce
Set up virtual environment:

bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Configure environment:

bash
cp .env.production.example .env
# Edit .env with your production values
Set up PostgreSQL:

bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb ecommerce_production
sudo -u postgres createuser ecommerce_user
sudo -u postgres psql -c "ALTER USER ecommerce_user WITH PASSWORD 'your-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ecommerce_production TO ecommerce_user;"
Run migrations:

bash
python manage.py migrate
Collect static files:

bash
python manage.py collectstatic --noinput
Create superuser:

bash
python manage.py createsuperuser
Set up Gunicorn:

bash
# Install gunicorn if not in requirements
pip install gunicorn

# Test run
gunicorn ecommerce.wsgi:application -c gunicorn.conf.py
Set up systemd service:

bash
sudo nano /etc/systemd/system/ecommerce.service
Add:

ini
[Unit]
Description=Ecommerce System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/ecommerce
Environment="PATH=/path/to/ecommerce/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=ecommerce.settings"
ExecStart=/path/to/ecommerce/venv/bin/gunicorn ecommerce.wsgi:application -c gunicorn.conf.py

[Install]
WantedBy=multi-user.target
Set up Nginx:

nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /static/ {
        alias /path/to/ecommerce/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /path/to/ecommerce/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
SSL Certificate (Let's Encrypt)
bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
Monitoring
Logs:

Application logs: logs/django.log

Gunicorn logs: journalctl -u ecommerce

Nginx logs: /var/log/nginx/error.log

Health check endpoint: https://yourdomain.com/health/

Backup:

bash
# Database backup
pg_dump ecommerce_production > backup_$(date +%Y%m%d).sql

# Media backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
Troubleshooting
Static files not loading: Check Nginx configuration and file permissions

Database errors: Verify PostgreSQL service is running and .env settings

Permission errors: Check ownership of media/ and staticfiles/ directories

Email not working: Verify SMTP settings in .env file
