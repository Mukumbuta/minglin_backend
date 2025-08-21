#!/bin/bash

echo "🚀 Deploying minglin API (Django/PostGIS) to Production..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y nginx certbot python3-certbot-nginx git

# Check if we're already in the correct directory (has docker-compose.yml)
if [ -f "docker-compose.yml" ]; then
    echo "📁 Already in the correct directory..."
else
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
fi

# Create production .env if it doesn't exist
echo "🔍 Checking for .env file..."
if [ ! -f ".env" ]; then
    echo "📝 Creating production .env file..."
    cat > .env << EOF
SECRET_KEY=django-insecure-5_wgj*yo!9(l@aws28fj4vxaq+or(+1!s+7(^ch#*gp5_c(6$!
DEBUG=False
ALLOWED_HOSTS=*
POSTGRES_DB=minglin
POSTGRES_USER=minglin
POSTGRES_PASSWORD=Minglin2025!
CORS_ALLOW_ALL_ORIGINS=True
POSTGRES_HOST=db
POSTGRES_PORT=5432
PROBASE_URL=https://probasesms.com/api/json/multi/res/bulk/sms
PROBASE_USERNAME=All1Zed@12\$\$
PROBASE_PASSWORD=All1Zed@sms12\$\$
PROBASE_SENDER_ID=Tumingle
PROBASE_SOURCE=Tumingle
SENTRY_DSN=
EOF
    echo "✅ .env file created successfully"
    echo "⚠️  Please edit .env file with your actual values!"
else
    echo "📄 .env file already exists"
fi

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
        
        # CORS headers for mobile apps
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
        
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