# Laboratorio de Seguridad en AWS con Claude Code

Laboratorio práctico del curso Claude Academy. El objetivo es identificar y corregir fallos de seguridad comunes en infraestructura AWS usando Claude Code como asistente de análisis.

## Qué hace este laboratorio

Se parte de dos archivos intencionalmente vulnerables:

- **`lambda_function.py`** — función AWS Lambda que consulta DynamoDB y procesa usuarios
- **`main.tf`** — configuración Terraform de un bucket S3 con política de acceso entre cuentas

Claude Code analiza ambos archivos, identifica los fallos, propone un diff explicado y aplica las correcciones.

## Fallos corregidos

| # | Fallo | Archivo | Severidad |
|---|---|---|---|
| 1 | Datos sensibles (`password`, `credit_card`) expuestos en logs de CloudWatch | `lambda_function.py` | Crítica |
| 2 | Sin validación de `user_id` antes de usarlo como clave en DynamoDB | `lambda_function.py` | Media |
| 3 | Política S3 con `s3:*` otorgada al root de otra cuenta | `main.tf` | Crítica |
| 4 | Acceso público anónimo de lectura (`Principal = "*"`) | `main.tf` | Crítica |
| 5 | Block Public Access completamente desactivado | `main.tf` | Crítica |

El reporte completo con descripción de cada problema y su corrección está en [`resultado_laboratorio.md`](./resultado_laboratorio.md).

## Archivos

```
.
├── lambda_function.py        # Lambda corregida (sanitización de logs + validación de entrada)
├── main.tf                   # Terraform corregido (mínimo privilegio + Block Public Access)
├── resultado_laboratorio.md  # Reporte de hallazgos y correcciones
└── CLAUDE.md                 # Contexto para Claude Code
```

## Conceptos practicados

- Principio de mínimo privilegio en políticas IAM/S3
- Sanitización de logs para cumplimiento PCI-DSS y GDPR
- Validación de entrada en funciones serverless
- Configuración segura de buckets S3 con Terraform
