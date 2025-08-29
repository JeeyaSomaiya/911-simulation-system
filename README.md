## Relevant Apache Configuration Files

### Apache Config File

/etc/apache2/sites-available/ai-call-simulator.conf

```bash
<VirtualHost *:80>
    ServerName 130.250.171.255
    DocumentRoot /var/www/ai-call-simulator/frontend

    <Directory /var/www/ai-call-simulator/frontend>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
        
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>

    ProxyPreserveHost On

    ProxyPass /api/ http://127.0.0.1:5000/api/
    ProxyPassReverse /api/ http://127.0.0.1:5000/api/

    ProxyPass /health http://127.0.0.1:5000/health
    ProxyPassReverse /health http://127.0.0.1:5000/health

    ErrorLog /var/www/ai-call-simulator/logs/error.log
    CustomLog /var/www/ai-call-simulator/logs/access.log combined
</VirtualHost>
```

### Flask Service File 

/etc/systemd/system/ai-call-simulator-flask.service

```bash
[Unit]
Description=Gunicorn instance to serve AI Call Simulator Flask app
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/ai-call-simulator/backend
ExecStart=/bin/bash -c 'source /var/www/ai-call-simulator/backend/venv/bin/activate && gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:app'
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=3
Environment=HF_HOME=/var/cache/huggingface
Environment=TRANSFORMERS_CACHE=/var/cache/huggingface

[Install]
WantedBy=multi-user.target
```

### LLM Access

/opt/models/Llama3.1-8B-Instruct-hf

*HuggingFace format LLM, copied from /home/ubuntu/.llama/checkpoints/Llama3.1-8B-Instruct-hf*
