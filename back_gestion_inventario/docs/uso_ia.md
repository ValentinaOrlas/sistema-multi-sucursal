# Uso de IA en esta implementación

Herramienta: Codex, mediante instrucciones del usuario y edición del repositorio local.

## Instrucciones recibidas

- «revisa las tablas de base da datos».
- «Bueno comienza haciendo el back y me vas mostrando que vas haciendo».

## Aportes

Revisión del esquema existente, corrección de DTO incompletos, diseño de permisos por sucursal, servicios de inventario, compras, ventas y transferencias, migraciones, documentación y pruebas de integración. La implementación reutiliza los modelos y la estructura inicial del proyecto.

## Validación y ajustes

La ejecución de pruebas verificó rollback, cantidades decimales, promedio ponderado, recepción parcial y permisos. La prueba real con PostgreSQL detectó que una restricción se creaba antes que su nueva columna; se corrigió el orden. La prueba de migración con datos detectó un valor predeterminado `now()` incompatible con SQLite; se sustituyó por la función SQLAlchemy portable. Se añadieron pruebas concurrentes sobre PostgreSQL para validar ventas, recepciones y creación inicial de existencias.

Los cambios de esta sesión fueron generados con asistencia de IA. No se afirma que hayan recibido revisión humana: el usuario debe revisar y comprender las decisiones. No se ha calculado un porcentaje de asistencia sobre todo el repositorio; ya existía código previo.
