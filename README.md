# Quotify - Sistema de Gestión de Cotizaciones

Sistema completo para gestionar clientes y cotizaciones de servicios, desarrollado con Django.

## 🚀 Características

- **Gestión de Clientes**: Registro completo de información de clientes
- **Catálogo de Servicios**: Organización por categorías con precios e impuestos
- **Cotizaciones Completas**: Generación automática de números de cotización
- **Cálculos Automáticos**: Subtotales, impuestos y totales
- **Interface Administrativa**: Panel completo para gestión
- **Escalable**: Estructura modular para futuras expansiones

## 📁 Estructura del Proyecto

```
quotify/
├── apps/
│   ├── core/           # Configuraciones del sistema
│   ├── clients/        # Gestión de clientes
│   ├── services/       # Catálogo de servicios
│   └── quotations/     # Sistema de cotizaciones
├── templates/          # Plantillas HTML
├── static/            # Archivos estáticos (CSS, JS, imágenes)
├── media/             # Archivos subidos por usuarios
└── quotify/           # Configuración principal de Django
```

## 🛠️ Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <repository-url>
   cd quotify
   ```

2. **Crear y activar entorno virtual**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   ```bash
   cp env.example .env
   # Editar .env con tus configuraciones
   ```

5. **Ejecutar migraciones**:
   ```bash
   python manage.py migrate
   ```

6. **Crear superusuario**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Ejecutar servidor**:
   ```bash
   python manage.py runserver
   ```

## 🎯 Uso

### Acceso al Sistema
- **Admin**: http://localhost:8000/admin/
- **Usuario**: admin
- **Contraseña**: admin123

### Configuración Inicial

1. **Configurar Perfil de la Empresa**:
   - Ir a Admin → Core → Company profiles
   - Añadir información de tu empresa

2. **Crear Categorías de Servicios**:
   - Ir a Admin → Services → Service categories
   - Ejemplo: "Sistemas de Riego", "Jardinería", "Piscinas"

3. **Añadir Servicios**:
   - Ir a Admin → Services → Services
   - Configurar precios, unidades e impuestos

4. **Registrar Clientes**:
   - Ir a Admin → Clients → Clients
   - Añadir información completa de contacto

5. **Crear Cotizaciones**:
   - Ir a Admin → Quotations → Quotations
   - Seleccionar cliente y añadir servicios

## 🔧 Desarrollo con VSCode

El proyecto incluye configuraciones para VSCode:

- **Ejecutar servidor**: `Ctrl+Shift+P` → "Debug: Select and Start Debugging" → "Django: Run Server"
- **Debug**: Usar "Django: Debug Server" para debugging con breakpoints
- **Tests**: Usar "Django: Run Tests"

## 📊 Modelos Principales

### Cliente (Client)
- Información de contacto completa
- Dirección
- Historial de cotizaciones

### Servicio (Service)
- Nombre y descripción
- Precio unitario y unidad de medida
- Tasa de impuesto
- Categorización

### Cotización (Quotation)
- Número automático (S00001, S00002, etc.)
- Cliente asociado
- Fechas de cotización y expiración
- Estados: Borrador, Enviada, Aceptada, Rechazada, Expirada
- Términos de pago personalizables

### Item de Cotización (QuotationItem)
- Servicio asociado
- Cantidad y precio unitario
- Cálculos automáticos de impuestos

## 🎨 Personalización

### Añadir Nuevos Campos
1. Modificar modelos en `apps/[app]/models.py`
2. Crear migración: `python manage.py makemigrations`
3. Aplicar migración: `python manage.py migrate`
4. Actualizar admin en `apps/[app]/admin.py`

### Configurar Empresa
- Logo, dirección, términos de pago por defecto
- Tasa de impuesto predeterminada
- Configuraciones del sistema

## 📈 Próximas Funcionalidades

- [ ] Generación de PDFs de cotizaciones
- [ ] Interface web pública para clientes
- [ ] Dashboard con estadísticas
- [ ] Notificaciones por email
- [ ] API REST
- [ ] Reportes avanzados
- [ ] Integración con sistemas de facturación

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte o preguntas, crear un issue en el repositorio del proyecto.
