You're absolutely right! Let me examine your project's configuration files to provide the exact steps needed for your VPS deployment.

Ran tool
Read file: OneClickSetup.md
Ran tool
Read file: scripts/install-tools.sh
Read file: scripts/install-tools.sh
Read file: server.js
Perfect! Now I understand your setup. You have a well-configured project with Docker containers and a one-click setup script. Here's the **exact steps** you need to follow on your VPS:

## 🚀 **VPS Deployment Steps (Using Your Existing Setup)**

### **Step 1: Initial Server Setup**
```bash
# Connect to your VPS
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Git
apt install git -y

# Install Nginx
apt install nginx -y

# Install Certbot for SSL
apt install certbot python3-certbot-nginx -y
```

### **Step 2: Clone Your Project**
```bash
# Clone your repository
git clone https://github.com/yourusername/minglin_backend.git
cd minglin_backend

# Make the install script executable
chmod +x scripts/install-tools.sh
```

### **Step 3: Run Your One-Click Setup**
```bash
# Run your existing setup script
bash scripts/install-tools.sh
```

### **Step 4: Create Production Environment File**
```bash
# Create .env file for production
nano .env
```

Add your production environment variables:
```env
NODE_ENV=production
PORT=5000
MONGO_URI=mongodb://mongo:27017/minglin_prod
JWT_SECRET=your-super-secure-jwt-secret-key-here
# Add other environment variables as needed
```

### **Step 5: Start Production Containers**
```bash
# Build and start production containers using your existing docker-compose.yml
docker compose up -d

# Check if containers are running
docker ps
```

### **Step 6: Configure Nginx as Reverse Proxy**
```bash
# Create Nginx configuration for your domain
sudo nano /etc/nginx/sites-available/api.tumingle.com
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name api.tumingle.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### **Step 7: Enable Nginx Site**
```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/api.tumingle.com /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### **Step 8: Configure Domain & SSL**
```bash
# Install SSL certificate
sudo certbot --nginx -d api.tumingle.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### **Step 9: Configure Firewall**
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Check status
sudo ufw status
```

### **Step 10: Test Your Deployment**
```bash
# Test your API
curl https://api.tumingle.com/api/v1/healthcheck

# View logs if needed
docker compose logs -f
```

---

## �� **Key Points About Your Setup:**

1. **Your `docker-compose.yml`** is already configured for production with:
   - Multi-stage Docker build
   - Non-root user for security
   - Health checks
   - Proper networking

2. **Your containers will run:**
   - API on port 5000 (internal)
   - MongoDB on port 27017 (internal)
   - Nginx will proxy external traffic to port 5000

3. **Your existing Makefile commands work:**
   ```bash
   # For production management
   docker compose up -d    # Start production
   docker compose down     # Stop production
   docker compose logs -f  # View logs
   ```

---

## 🔧 **Production Management Commands**

```bash
# Start production
docker compose up -d

# Stop production
docker compose down

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Update and redeploy
git pull
docker compose down
docker compose up -d --build
```

---

## 📝 **Summary of What Happens:**

1. **Nginx** listens on port 80/443 and proxies requests to `localhost:5000`
2. **Your API container** runs on port 5000 internally
3. **MongoDB container** runs on port 27017 internally
4. **SSL certificate** secures the connection
5. **Your existing Docker setup** handles everything else

**Your API will be available at: `https://api.tumingle.com`**

The beauty of your setup is that you're using the **same production Docker configuration** you already have, just with Nginx as a reverse proxy! 🎉