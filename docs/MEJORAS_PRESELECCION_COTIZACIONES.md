# Mejoras en Preselección de Cotizaciones

## Descripción
Se ha implementado la funcionalidad para preseleccionar automáticamente los campos de empresa, cliente y vendedor en el formulario de creación de cotizaciones mediante parámetros de URL.

## Funcionalidad Implementada

### 1. Preselección por Parámetros de URL

La URL de creación de cotizaciones ahora soporta los siguientes parámetros:

- `company_profile`: ID del perfil de empresa a preseleccionar
- `client`: ID del cliente a preseleccionar  
- `salesperson`: ID del vendedor a preseleccionar

#### Ejemplos de URLs:
```
# Preseleccionar empresa
http://localhost:8000/quotations/create/?company_profile=1

# Preseleccionar cliente
http://localhost:8000/quotations/create/?client=3

# Preseleccionar vendedor
http://localhost:8000/quotations/create/?salesperson=2

# Combinar múltiples preselecciones
http://localhost:8000/quotations/create/?company_profile=1&client=3&salesperson=2
```

### 2. Mejoras en la Vista

En `apps/quotations/views.py`, clase `QuotationCreateView`:

- **Método `get_initial()`**: Modificado para leer los parámetros de la URL y preseleccionar los campos correspondientes
- **Método `get_context_data()`**: Añadido para proporcionar información sobre elementos preseleccionados al template

### 3. Mejoras en el Template

En `templates/quotations/form.html`:

- **Alert informativo**: Muestra qué elementos han sido preseleccionados
- **Badges en labels**: Indica visualmente cuándo un campo está preseleccionado
- **Textos de ayuda dinámicos**: Informa al usuario sobre la preselección y permite cambiarla

### 4. Integración con Otros Templates

- **`templates/core/company/detail.html`**: El botón "Nueva Cotización" ahora preselecciona automáticamente la empresa
- **`templates/clients/detail.html`**: Los botones de "Nueva Cotización" preseleccionan automáticamente el cliente

## Características Técnicas

### Validación y Manejo de Errores
- Si se proporciona un ID inválido o inexistente, se ignora silenciosamente sin mostrar errores
- Los campos sin preseleccionar mantienen su comportamiento normal
- La empresa sigue teniendo una preselección por defecto si no se especifica una

### Experiencia de Usuario
- **Indicadores visuales**: Badges de colores diferentes para cada tipo de preselección
- **Información contextual**: Alert que muestra claramente qué se ha preseleccionado
- **Flexibilidad**: El usuario puede cambiar cualquier campo preseleccionado
- **Textos dinámicos**: Los mensajes de ayuda se adaptan según haya preselección o no

### Seguridad
- Validación de tipos de datos (ValueError)
- Verificación de existencia de objetos (DoesNotExist)
- Solo se consideran vendedores activos (`is_active=True`)

## Casos de Uso

1. **Desde perfil de empresa**: Crear cotización con empresa preseleccionada
2. **Desde perfil de cliente**: Crear cotización con cliente preseleccionado
3. **Flujo integrado**: Enlaces desde diferentes partes del sistema que preseleccionan contexto relevante
4. **URLs directas**: Bookmarks o enlaces externos con preselecciones específicas

## Beneficios

- **Eficiencia**: Reduce clics y tiempo de entrada de datos
- **Contexto**: Mantiene el contexto de navegación del usuario
- **Usabilidad**: Interfaz más intuitiva y amigable
- **Flexibilidad**: No fuerza selecciones, solo las sugiere
- **Integración**: Se integra naturalmente con el flujo existente de la aplicación 