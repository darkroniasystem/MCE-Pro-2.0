# QWEN.md - Instrucciones para Qwen Code

## Proyecto
MCE Pro 2.0 - Media Cleaner & Enrichment

## Reglas de Lectura Obligatoria
Antes de cualquier acción, SIEMPRE lee:
1. instrucciones/00_MASTER_PLAN.md
2. instrucciones/01_ARCHITECTURE.md
3. instrucciones/02_CONTRACTS.md
4. CURRENT_WORK.md

## Reglas Inquebrantables
1. NUNCA modificar archivos en referencia/
2. NUNCA escribir directamente en mce_master salvo el módulo Publisher
3. NUNCA inventar contratos fuera de contracts/
4. NUNCA modificar arquitectura sin autorización explícita
5. NUNCA tocar archivos en assets/ manualmente
6. SIEMPRE ejecutar tests antes de declarar una tarea terminada
7. SIEMPRE actualizar CURRENT_WORK.md al terminar una tarea
8. SIEMPRE hacer commit descriptivo al terminar

## Flujo de Trabajo
1. Leer CURRENT_WORK.md para saber el estado actual
2. Leer instrucciones relevantes
3. Implementar cambios
4. Ejecutar tests
5. Actualizar CURRENT_WORK.md
6. Commit + Push
