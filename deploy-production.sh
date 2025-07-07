#!/bin/bash

echo "🚀 Deploying minglin API (Django/PostGIS) to Production..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y nginx certbot python3-certbot-nginx git

# Clone or update repository
if [ -d "minglin_backend" ]; then
    echo "📁 Updating existing repository..."
    cd minglin_backend
    git pull origin main
else
    echo "📁 Cloning repository..."
    git clone https://github.com/mukumbuta/minglin_backend.git
    cd minglin_backend
fi

# Run the existing setup script
# echo "🔧 Running one-click setup..."
# bash scripts/install-tools.sh

# Create production .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating production .env file..."
    cat > .env << EOF
SECRET_KEY=your-super-secure-django-secret-key-here
DEBUG=False
ALLOWED_HOSTS=api.tumingle.com,localhost,127.0.0.1
POSTGRES_DB=minglin_prod
POSTGRES_USER=minglin
POSTGRES_PASSWORD=your-secure-postgres-password
POSTGRES_HOST=db
POSTGRES_PORT=5432
SENTRY_DSN=
EOF
    echo "⚠️  Please edit .env file with your actual values!"
fi

# Start the containers using existing make command
echo "🚀 Starting containers..."
bash make prod-start

# Configure Nginx for Django
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/api.tumingle.com > /dev/null << EOF
server {
    listen 80;
    server_name api.tumingle.com;

    # Static files
    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /app/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeout settings for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/api.tumingle.com /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
sudo nginx -t && sudo systemctl restart nginx

# Configure firewall
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

echo "✅ Production deployment complete!"
echo "🌐 Your API will be available at: https://api.tumingle.com"
echo ""
echo "📋 Next steps:"
echo "1. Update your DNS to point api.tumingle.com to this server's IP"
echo "2. Run: sudo certbot --nginx -d api.tumingle.com"
echo "3. Edit .env file with your actual values"
echo ""
echo "🔧 Management commands:"
echo "  make prod-start    # Start production services"
echo "  make prod-stop     # Stop production services"
echo "  make prod-logs     # View production logs"
echo "  make prod-restart  # Restart production services" 