# 📋 Resumen Rápido - Deploy AWS EC2

## 🎯 Pasos en Orden

### 1️⃣ Preparación (5 minutos)
- [ ] Crear `core/settings_production.py` ✅ (ya creado)
- [ ] Preparar `.env` con todas las variables

### 2️⃣ AWS Console (10 minutos)
- [ ] Crear EC2 (t3.micro o t3.small)
- [ ] Crear RDS PostgreSQL (db.t3.micro)
- [ ] Configurar Security Groups
- [ ] Obtener IP pública de EC2
- [ ] Obtener Endpoint de RDS

### 3️⃣ Configurar DNS (5 minutos)
- [ ] Apuntar dominio a IP de EC2
- [ ] Esperar propagación DNS

### 4️⃣ Conectar a EC2 (2 minutos)
```bash
ssh -i tu-archivo.pem ec2-user@tu-ip-publica
```

### 5️⃣ Instalar Dependencias (5 minutos)
```bash
# Ejecutar script de setup
bash scripts/setup_ec2.sh
```

### 6️⃣ Subir Código (5 minutos)
```bash
# Opción A: Git
git clone tu-repo /var/www/smartsales365

# Opción B: SCP (desde tu máquina)
scp -i archivo.pem -r proyecto ec2-user@ip:/var/www/smartsales365
```

### 7️⃣ Configurar Django (10 minutos)
```bash
cd /var/www/smartsales365
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Crear .env con todas las variables
nano .env

# Migraciones
python manage.py migrate
python manage.py collectstatic --noinput
```

### 8️⃣ Configurar Nginx (5 minutos)
```bash
sudo nano /etc/nginx/conf.d/smartsales365.conf
# (copiar configuración de la guía)
sudo nginx -t
sudo systemctl start nginx
```

### 9️⃣ Obtener SSL (5 minutos)
```bash
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

### 🔟 Configurar Gunicorn (5 minutos)
```bash
# Crear gunicorn_config.py
# Crear servicio systemd
sudo systemctl start smartsales365
sudo systemctl enable smartsales365
```

---

## 📝 Archivos Importantes

### `.env` en EC2
```env
DJANGO_SECRET_KEY=...
DB_HOST=tu-rds-endpoint.rds.amazonaws.com
DB_PASSWORD=...
STRIPE_SECRET_KEY=...
VAPID_PRIVATE_KEY=...
```

### `gunicorn_config.py`
```python
bind = "127.0.0.1:8000"
workers = 3
```

### `/etc/systemd/system/smartsales365.service`
```ini
[Unit]
Description=SmartSales365 Gunicorn

[Service]
User=ec2-user
WorkingDirectory=/var/www/smartsales365
ExecStart=/var/www/smartsales365/venv/bin/gunicorn core.wsgi:application
```

---

## ✅ Checklist Final

- [ ] EC2 corriendo
- [ ] RDS accesible desde EC2
- [ ] Código en `/var/www/smartsales365`
- [ ] `.env` configurado
- [ ] Migraciones ejecutadas
- [ ] Nginx configurado
- [ ] SSL obtenido
- [ ] Gunicorn corriendo
- [ ] Sitio accesible por HTTPS

---

## 🚀 Comandos Rápidos

### Reiniciar aplicación
```bash
sudo systemctl restart smartsales365
```

### Ver logs
```bash
tail -f /var/log/smartsales365/django.log
```

### Actualizar código
```bash
cd /var/www/smartsales365
git pull
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart smartsales365
```

---

## 💰 Costos Estimados (Región us-east-1)

- **EC2 t3.micro**: $0.0104/hora = ~$7.50/mes
- **RDS db.t3.micro**: $0.017/hora = ~$12.24/mes
- **Almacenamiento**: $0.115/GB = ~$2.30/mes (20GB)
- **Transferencia**: Primeros 100GB gratis

**Total aproximado: ~$22/mes** (Free Tier aplica los primeros 12 meses)

---

## 🆘 Ayuda Rápida

### Error 502 Bad Gateway
```bash
sudo systemctl status smartsales365
sudo journalctl -u smartsales365 -n 50
```

### No se conecta a RDS
- Verifica Security Group de RDS permite conexiones desde EC2
- Verifica endpoint y credenciales en `.env`

### SSL no funciona
- Verifica DNS apunta correctamente
- Renueva: `sudo certbot renew`

---

**Tiempo total estimado: ~1 hora** ⏱️

