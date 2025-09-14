# Contexto General del Proyecto: Quotify

Última actualización: 2025-09-14

## 1) Visión y Propósito
Quotify es un sistema de gestión de cotizaciones basado en Django que permite:
- Registrar clientes y sus notas internas.
- Administrar un catálogo de servicios con categorías, precios, impuestos e imágenes.
- Generar cotizaciones con numeración automática, cálculo de impuestos y seguimiento de actividades.
- Centralizar la configuración de empresa y del sistema para consistencia visual y operativa.

Referencia rápida: ver `README.md` para pasos de instalación y uso.

## 2) Stack Tecnológico
- Backend: `Django 5.2.x`
- Base de datos: `PostgreSQL` por defecto (configurable vía `.env` en `quotify/settings.py` con `python-decouple`)
- Templates: Django Templates (`quotify/settings.py: TEMPLATES.DIRS -> templates/`)
- Estáticos: `static/` con `STATICFILES_DIRS` y `staticfiles/` como `STATIC_ROOT`
- Media: `media/` (cargada en desarrollo si `DEBUG=True`)
- Terceros:
  - `django-widget-tweaks` para personalizar formularios en templates
  - `Pillow` para manejo de imágenes
  - `reportlab` y `weasyprint` para generación de PDFs (aún no integrado en vistas)
  - `django-ordered-model` para ordenar imágenes en servicios
  - `python-decouple` para manejo de variables de entorno

Notas de dependencias:
- `requirements.txt` unificado con `Pillow==11.2.1`, `psycopg2-binary`, `django-ordered-model`, `python-decouple`.

## 3) Estructura Principal de Carpetas
- `apps/` aplicaciones Django del dominio
  - `apps/core/` configuración del sistema, perfiles de empresa, vendedores
  - `apps/clients/` clientes y notas internas
  - `apps/services/` catálogo de servicios y galería
  - `apps/quotations/` cotizaciones, items, imágenes adicionales y actividades (CRM)
- `templates/` plantillas HTML organizadas por app
- `static/` estilos y assets (ej: `css/company-profiles.css`)
- `media/` archivos subidos por usuarios (logo, fotos, etc.)
- `docs/` documentación funcional/técnica
- `quotify/` configuración del proyecto Django

Ver esquema en `README.md` sección “Estructura del Proyecto”.

## 4) Apps y Modelos Clave

### 4.1 `apps.core`
- `SalesPerson`: datos de vendedores, tasa de comisión, foto de perfil.
- `CompanyProfile`: identidad corporativa, branding, términos, T&C, colores, logos, métricas helper.
- `SystemSettings`: configuración del sistema (único registro), nombre, colores, prefijos, moneda, etc. Incluye `get_settings()` y validación para unicidad.

### 4.2 `apps.clients`
- `Client`: datos de contacto, dirección, foto, estado y timestamps. Helpers de conteo y `full_address`.
- `ClientNote`: notas internas con prioridad, tipo, seguimiento, visibilidad, y `resolved_at` automático.

### 4.3 `apps.services`
- `ServiceCategory`: categorías de servicios.
- `Service`: nombre, descripción, categoría, precio unitario, unidad, tasa de impuesto, imagen principal y notas.
- `ServiceImage` (gallery): imágenes adicionales ordenables por servicio usando `OrderedModel`.

### 4.4 `apps.quotations`
- `Quotation`: número autogenerado `S00001`, relación con `CompanyProfile`, `Client`, `SalesPerson`; fechas; estado; términos; notas; duplicación de datos de empresa; helpers de subtotal/IVA/total; expiración; anticipos y saldos.
- `QuotationItem`: referencia a `Service`, cantidad, precio unitario, tasa de impuesto; descripción e imagen personalizadas; helpers de subtotal/IVA/total.
- `QuotationItemImage`: imágenes adicionales por item.
- `QuotationPhotographicReport`: reporte fotográfico (antes/durante/después, etc.).
- `QuotationActivity`: registro de actividades/seguimiento (cambios de estado, notas, llamadas, correos, reuniones, pagos, recordatorios, etc.).

## 5) Relaciones y Diagrama Lógico (texto)
- `CompanyProfile (1) -- (N) Quotation`
- `Client (1) -- (N) Quotation`
- `SalesPerson (1) -- (N) Quotation`
- `Quotation (1) -- (N) QuotationItem`
- `Service (1) -- (N) QuotationItem`
- `Service (1) -- (N) ServiceImage`
- `Quotation (1) -- (N) QuotationPhotographicReport`
- `Quotation (1) -- (N) QuotationActivity`
- `Client (1) -- (N) ClientNote`

Índices relevantes:
- `ClientNote`: índices por `client`, `priority/is_resolved`, `follow_up_date`.
- `QuotationActivity`: índices por `quotation`, `activity_type`, `requires_follow_up/follow_up_date`.

## 6) URLs y Rutas
Archivo: `quotify/urls.py`
- `admin/` panel administrativo
- `accounts/` autenticación Django (`django.contrib.auth.urls`)
- `''` rutas de `apps.core`
- `clients/` rutas de `apps.clients`
- `services/` rutas de `apps.services`
- `quotations/` rutas de `apps.quotations`

En desarrollo (`DEBUG=True`) se sirven media: `MEDIA_URL` -> `MEDIA_ROOT`.

## 7) Configuraciones Clave (`quotify/settings.py`)
- Variables desde `.env` con `python-decouple` (`config`, `Csv`).
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` leídos del entorno.
- `DATABASES['default']` usa `django.db.backends.postgresql` y toma `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` del entorno.
- `INSTALLED_APPS` incluye `'ordered_model'`.
- `TEMPLATES.DIRS=[BASE_DIR/'templates']` y `APP_DIRS=True`.
- `STATIC_URL=/static/`, `STATICFILES_DIRS=[BASE_DIR/'static']`, `STATIC_ROOT=BASE_DIR/'staticfiles'`.
- `MEDIA_URL=/media/`, `MEDIA_ROOT=BASE_DIR/'media'`.
- `LOGIN_URL=/accounts/login/`, `LOGIN_REDIRECT_URL=/`, `LOGOUT_REDIRECT_URL=/accounts/login/`.
- Context processor custom: `apps.core.context_processors.system_settings`.

## 8) Flujos y Casos de Uso
- Creación de cotización:
  1. Elegir `CompanyProfile`, `Client`, `SalesPerson` (pueden preseleccionarse por URL; ver `docs/MEJORAS_PRESELECCION_COTIZACIONES.md`).
  2. Añadir `QuotationItem` desde `Service` (relleno de `unit_price`/`tax_rate` automático si faltan).
  3. Guardar: se autogenera `quotation_number` con prefijo `S` y relleno de info desde `CompanyProfile`.
  4. Seguimiento con `QuotationActivity` (automática o manual), evidencias con `QuotationPhotographicReport`.
- Gestión de perfiles de empresa: ver `docs/OPTIMIZACIONES_PERFILES_EMPRESA.md` para optimizaciones, métricas y UI mejorada.

## 9) Calidad, Mantenimiento y Estilo
- Migraciones: `python manage.py makemigrations && python manage.py migrate`
- Admin: configurar `admin.py` por app para mejorar experiencia de gestión.
- Plantillas: usar `widget_tweaks` para controles de formularios.
- Performance: preferir `select_related/prefetch_related` donde aplique (ya usado en vistas según docs en `docs/OPTIMIZACIONES_PERFILES_EMPRESA.md`).
- Única `SystemSettings`: método `save` evita múltiples instancias.

## 10) Checklist de Producción
- Mover `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, y credenciales a `.env` (listo).
- Configurar base de datos productiva (PostgreSQL recomendado) y `TIME_ZONE`.
- Servir estáticos con `collectstatic` y servidor web (Nginx) + almacenamiento (S3 o similar) para media.
- Revisar permisos y tamaños de subida de archivos (imágenes).
- Añadir `SECURE_*` headers/middleware (HTTPS) y CSRF configurado.

## 11) Tareas Pendientes Observadas
- Implementar generación de PDF desde vistas (aprovechando `reportlab/weasyprint`).
- Añadir tests básicos de modelos y vistas críticas.
- Considerar i18n: `LANGUAGE_CODE='es-mx'` y `TIME_ZONE='America/Merida'` si aplica al negocio.

## 12) Snippets Útiles
- Crear superusuario: `python manage.py createsuperuser`
- Ejecutar servidor: `python manage.py runserver`
- Cargar media en dev: `DEBUG=True` habilita `MEDIA_URL` via `static()` en `urls.py`.

## 13) Referencias
- `README.md`: instalación, uso, estructura.
- `docs/MEJORAS_PRESELECCION_COTIZACIONES.md`: preselección de empresa/cliente/vendedor por URL.
- `docs/OPTIMIZACIONES_PERFILES_EMPRESA.md`: dashboard y optimizaciones de perfiles de empresa.

---
Este documento sirve como referencia rápida para desarrollar, depurar y planificar nuevas funcionalidades en Quotify. Mantenerlo actualizado con cambios de modelo, dependencias y configuración.
