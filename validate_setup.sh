#!/bin/bash

# Validation script for Ecommerce System setup

echo "=== Ecommerce System Setup Validation ==="
echo ""

# Check Python version
echo "1. Checking Python version..."
python --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python not found"
    exit 1
fi

# Check Django installation
echo ""
echo "2. Checking Django installation..."
python -c "import django; print(f'Django {django.__version__}')"
if [ $? -ne 0 ]; then
    echo "ERROR: Django not installed"
    exit 1
fi

# Check directory structure
echo ""
echo "3. Checking directory structure..."
required_dirs=(
    "ecommerce"
    "users"
    "products" 
    "orders"
    "templates"
    "media"
    "users/templates/users"
    "products/templates/products"
    "orders/templates/orders"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir"
    else
        echo "✗ $dir (MISSING)"
    fi
done

# Check required files
echo ""
echo "4. Checking required files..."
required_files=(
    "manage.py"
    "requirements.txt"
    ".env.example"
    "ecommerce/settings.py"
    "ecommerce/urls.py"
    "ecommerce/wsgi.py"
    "users/models.py"
    "products/models.py"
    "orders/models.py"
    "gunicorn.conf.py"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (MISSING)"
    fi
done

# Check database migrations
echo ""
echo "5. Checking database migrations..."
python manage.py check
if [ $? -eq 0 ]; then
    echo "✓ Django system check passed"
else
    echo "✗ Django system check failed"
    exit 1
fi

# Try to make migrations
echo ""
echo "6. Checking for unapplied migrations..."
python manage.py makemigrations --check --dry-run
if [ $? -eq 0 ]; then
    echo "✓ No unapplied migrations"
else
    echo "✗ There are unapplied migrations"
fi

# Check test suite
echo ""
echo "7. Running test suite..."
python manage.py test --failfast
if [ $? -eq 0 ]; then
    echo "✓ All tests passed"
else
    echo "✗ Some tests failed"
fi

echo ""
echo "=== Validation Complete ==="
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure settings"
echo "2. Run: python manage.py migrate"
echo "3. Run: python manage.py createsuperuser"
echo "4. Run: python manage.py collectstatic"
echo "5. Run: python manage.py runserver"
echo ""
echo "For production:"
echo "1. Update .env with production settings"
echo "2. Configure gunicorn and nginx"
echo "3. Set up SSL certificates"
echo "4. Configure backup and monitoring"
