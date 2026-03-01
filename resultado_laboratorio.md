# Resultado del Laboratorio — Análisis de Seguridad en AWS

**Fecha:** 2026-03-01
**Archivos analizados:** `lambda_function.py`, `main.tf`

---

## Fallos encontrados y corregidos

### 1. Datos sensibles expuestos en logs — `lambda_function.py` · Severidad: Crítica

**Problema:** La función registraba en CloudWatch el evento completo (sin filtrar) y campos como `password` y `credit_card` extraídos de DynamoDB. Los logs son accesibles por múltiples roles de IAM y se retienen indefinidamente, lo que viola PCI-DSS y GDPR.

**Corrección:** Se añadió `sanitize_event()` para enmascarar campos sensibles con `'***'` antes de cualquier log, y se eliminaron por completo las lecturas y referencias a `password` y `credit_card`.

---

### 2. Sin validación de entrada (`user_id`) — `lambda_function.py` · Severidad: Media

**Problema:** El valor de `user_id` llegaba directamente del evento y se usaba como clave en DynamoDB sin ninguna comprobación de tipo, formato ni longitud, abriendo la puerta a datos malformados o manipulación de claves.

**Corrección:** Se añadió `validate_user_id()` con una regex que restringe el valor a caracteres alfanuméricos, guiones y un máximo de 64 caracteres, lanzando `ValueError` ante cualquier entrada inválida.

---

### 3. Acceso `s3:*` a cuenta externa — `main.tf` · Severidad: Crítica

**Problema:** La política del bucket otorgaba `s3:*` al root de otra cuenta AWS, lo que incluye borrar objetos, modificar la política del bucket, deshabilitar el versionado y escalar privilegios. Un compromiso de esa cuenta equivalía a control total del bucket.

**Corrección:** La acción se redujo a `["s3:GetObject", "s3:ListBucket"]`, aplicando el principio de mínimo privilegio.

---

### 4. Lectura pública anónima de objetos — `main.tf` · Severidad: Crítica

**Problema:** Un `Statement` con `Principal = "*"` permitía a cualquier persona en internet descargar cualquier objeto del bucket de producción sin necesidad de credenciales AWS.

**Corrección:** Se eliminó el `Statement` completo. El acceso ahora requiere identidad autenticada en AWS.

---

### 5. Block Public Access desactivado — `main.tf` · Severidad: Crítica

**Problema:** Las cuatro opciones de Block Public Access estaban en `false`, desactivando la capa de defensa principal de S3 contra exposición accidental. Cualquier ACL pública añadida por error hubiera surtido efecto inmediato.

**Corrección:** Los cuatro flags (`block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets`) se establecieron en `true`.

---

## Resumen

| # | Fallo | Archivo | Severidad |
|---|---|---|---|
| 1 | Datos sensibles en logs | `lambda_function.py` | Crítica |
| 2 | Sin validación de `user_id` | `lambda_function.py` | Media |
| 3 | `s3:*` a cuenta externa | `main.tf` | Crítica |
| 4 | Lectura pública de objetos | `main.tf` | Crítica |
| 5 | Block Public Access desactivado | `main.tf` | Crítica |
