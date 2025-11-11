# 📸 Actualizar Sistema con Imágenes de Productos

## ✅ Cambios Realizados

1. **Campo `imagen` agregado** al modelo `Producto`
2. **Optimización automática** de imágenes (máx. 800x800px, calidad 85%)
3. **Admin mejorado** con vista previa de imágenes
4. **Fix de promociones** - mejor validación de monto mínimo
5. **Serializer actualizado** con campo `imagen_url`

---

## 📥 PASOS EN EC2

### **PASO 1: Hacer Pull y Migrar**

```bash
cd /var/www/smartsales365
sudo git pull origin main

# Activar entorno virtual
source venv/bin/activate

# Aplicar migración
python manage.py migrate productos

# Verificar que se aplicó
python manage.py showmigrations productos
```

Deberías ver:
```
productos
 [X] 0001_initial
 [X] 0002_producto_imagen  ← Nueva migración
```

---

### **PASO 2: Verificar Pillow está instalado**

```bash
pip list | grep -i pillow
```

Si no está instalado:
```bash
pip install Pillow
```

---

### **PASO 3: Crear directorio de media (si no existe)**

```bash
sudo mkdir -p /var/www/smartsales365/media/productos
sudo chown -R ubuntu:ubuntu /var/www/smartsales365/media
sudo chmod -R 755 /var/www/smartsales365/media
```

---

### **PASO 4: Verificar configuración de Media en Nginx**

```bash
cat /etc/nginx/sites-enabled/smartsales365 | grep -A 5 "location /media"
```

Debería mostrar:
```nginx
location /media/ {
    alias /var/www/smartsales365/media/;
    expires 7d;
}
```

Si no está, agregarlo:
```bash
sudo nano /etc/nginx/sites-enabled/smartsales365
```

Agregar dentro del bloque `server` (después de `/static/`):
```nginx
location /media/ {
    alias /var/www/smartsales365/media/;
    expires 7d;
    add_header Cache-Control "public";
}
```

Reiniciar:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

### **PASO 5: Reiniciar Django**

```bash
sudo systemctl restart smartsales365
sudo systemctl status smartsales365
```

---

## 🧪 PROBAR EN ADMIN

1. Ve a: `https://smartsales365.duckdns.org/admin/productos/producto/`
2. Click en cualquier producto
3. Deberías ver:
   - Campo **"Imagen"** para subir archivo
   - Sección **"Vista Previa"** que muestra la imagen después de guardar
4. Sube una imagen
5. Guarda
6. La imagen se optimizará automáticamente

---

## 🔍 VERIFICAR QUE FUNCIONA

```bash
# Verificar que las imágenes se guardan
ls -lh /var/www/smartsales365/media/productos/

# Verificar desde el navegador
# https://smartsales365.duckdns.org/media/productos/tu-imagen.jpg
```

---

## 🐛 TROUBLESHOOTING

### Error: "Pillow no instalado"
```bash
pip install Pillow
sudo systemctl restart smartsales365
```

### Error: "Permission denied" al subir imagen
```bash
sudo chown -R ubuntu:ubuntu /var/www/smartsales365/media
sudo chmod -R 755 /var/www/smartsales365/media
```

### Error: "Media files no se sirven"
Verificar que Nginx tiene la configuración de `/media/` y reiniciar.

### Error: "Promociones no funcionan"
Verificar logs:
```bash
sudo journalctl -u smartsales365 -n 100 --no-pager | grep -i promocion
```

---

## 📋 CHECKLIST

- [ ] Pull del código realizado
- [ ] Migración aplicada (`python manage.py migrate productos`)
- [ ] Pillow instalado
- [ ] Directorio `/var/www/smartsales365/media/productos/` creado
- [ ] Permisos correctos en `/media/`
- [ ] Nginx configurado para servir `/media/`
- [ ] Django reiniciado
- [ ] Prueba de subir imagen en admin exitosa
- [ ] Imagen accesible desde navegador

---

**¡Listo!** Ahora puedes subir imágenes a los productos desde el admin de Django. 🎉

