# Modelos probabilisticos (STD 4.6)

- **4.6.1 Red de Petri:** lugares P1-P12 y transiciones T1-T11; rutas *happy path*, concurrencia del router (OR-join) y resiliencia P12->T11->P1.
- **4.6.2 Teoria de colas:** tasa de entrada (RNF002), buffer webhook/Redis, capacidad de servicio (RNF001: latencia menor a 5 s), saturacion.

**Para que sirve:** validar el diseno ante concurrencia y cuellos de botella **sin** sustituir a pruebas de carga en produccion.

Los tests aqui solo **documentan** cobertura minima de rutas esperadas en el modelo (constantes), para evitar falsos negativos hasta disponer de simulador formal.
