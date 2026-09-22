# Arquitectura del reto 1

Cómo está organizado el "cerebro" del robot y cómo trabajamos los tres sin pisarnos.

## 1. Idea general

Un frame entra, una decisión sale. Todo el procesamiento ocurre dentro de `procesar_frame`, y el resto del programa solo se encarga de la cámara y de mostrar el resultado.

```
                 ┌─────────────── reto/pipeline.py ───────────────┐
 cámara  ──────► │ preprocesar → ROI línea  → linea.detectar      │
 (celular IP     │              → ROI señal → senales.detectar    │ ──► Decision
  o video)       │              → control.decidir(estado, ...)    │     (+ datos de
                 └───────────────────────────────────────────────┘      depuración)
                                        │
                                        ▼
                              overlay.dibujar (HUD y máscaras)
```

**Por qué así:** cada etapa se puede probar y explicar por separado (criterio de la rúbrica), y cada uno de nosotros trabaja en un archivo distinto sin conflictos de merge.

## 2. Módulos

| Archivo | Responsabilidad | Dueño |
|---|---|---|
| `reto/camara.py` | Abrir la fuente (webcam, URL del celular, video de archivo), reconectar, entregar frames | Santiago |
| `reto/pipeline.py` | Orquestar las etapas por frame | Daniel |
| `reto/linea.py` | Segmentar la línea guía y calcular la desviación | Daniel |
| `reto/senales.py` | Detectar los octágonos PARE y SIGA | Juan David |
| `reto/control.py` | Máquina de estados y decisión de movimiento | Juan David |
| `reto/overlay.py` | HUD y mosaico de depuración | quien lo necesite |
| `reto/config.py` | Todos los parámetros y umbrales en un solo lugar | los tres (calibración) |
| `reto/tipos.py` | Los contratos entre módulos | fijo, se cambia entre los tres |
| `main.py` | Línea de comandos y loop principal | Santiago |

**Regla:** nadie edita el archivo de otro sin avisar. Si necesitas algo de otro módulo, se acuerda el contrato en `tipos.py` y cada uno programa contra él.

## 3. Contratos

Están en `reto/tipos.py`. Mientras estos no cambien, los tres podemos avanzar en paralelo aunque el módulo del otro todavía no exista:

```python
detectar_linea(frame, config)   -> ResultadoLinea(detectada, centro_x, desviacion, area, mascara)
detectar_senal(frame, config)   -> ResultadoSenal(tipo, area, centro, vertices, contorno)
decidir(estado, linea, senal, config) -> Decision(accion, giro, razon)
```

- **`desviacion`** está normalizada entre −1 y 1: negativa = la línea está a la izquierda del centro, positiva = a la derecha, 0 = centrada. Así el control no depende de la resolución de la cámara.
- **`tipo`** es `"PARE"`, `"SIGA"` o `None`.
- **`accion`** es `RECTO`, `IZQUIERDA`, `DERECHA`, `PARAR` o `BUSCAR`.
- **`razon`** es texto para el HUD y para poder explicar en la sustentación por qué el robot hizo lo que hizo.

Si más adelante hay que mandarle la decisión a un robot físico, se agrega un `reto/actuador.py` que traduzca `Decision` a lo que entienda el hardware. Ningún otro módulo cambia.

## 4. Etapas, con las técnicas que usa cada una

### Preprocesamiento
Redimensionar a un ancho fijo (`ANCHO_PROCESO`) y suavizar. Procesar en pequeño baja el costo por frame y estabiliza los FPS, que es lo que decide si el control llega a tiempo. Técnicas: redimensionar (clase 1), GaussianBlur (clase 3).

### Línea guía
ROI en la franja inferior del frame → máscara de color (`inRange` en HSV o umbral en el canal L de Lab si la línea es oscura) → apertura + cierre para limpiar → contorno más grande → centroide por momentos → desviación normalizada. Técnicas: ROI (clase 1), HSV/Lab (clase 1), inRange (clase 2), morfología (clase 3), contornos y centroide (clase 3).

**Idea propia:** dos franjas en vez de una, una cercana y una lejana. La cercana dice cuánto corregir **ahora**; la lejana anticipa la curva que viene. Ver estrategia, abajo.

### Señales
ROI en la parte superior → máscaras de rojo (dos rangos de H, porque el rojo está en los dos extremos) y de verde → morfología → contornos → filtro por área → `approxPolyDP` → un octágono tiene entre 7 y 9 vértices, relación de aspecto cercana a 1 y circularidad alta. Técnicas: HSV (clase 1), inRange (clase 2), morfología (clase 3), contornos + approxPolyDP + boundingRect (clase 3).

**Validación en tres pasos** para no frenar con cualquier cosa roja: color, forma y **persistencia** (la señal tiene que aparecer en N frames seguidos). El área del contorno funciona como medida de distancia: solo se obedece cuando la señal está lo bastante cerca.

### Control
Máquina de estados:

| Estado | Qué hace | Cómo sale |
|---|---|---|
| `SIGUIENDO` | Gira proporcional a la desviación; zona muerta en el centro para no oscilar | PARE válido → `DETENIDO`; línea perdida N frames → `BUSCANDO` |
| `DETENIDO` | Acción `PARAR` durante los segundos que indique el docente | Se cumple el tiempo (o llega SIGA) → `SIGUIENDO` |
| `BUSCANDO` | Gira hacia el último lado donde se vio la línea | Vuelve a aparecer la línea → `SIGUIENDO` |

El estado `BUSCANDO` existe por un criterio explícito de la rúbrica: "capacidad del robot para recuperar la trayectoria". Además, cada señal obedecida entra en un tiempo de espera, para que la misma señal no dispare dos paradas seguidas.

## 5. Configuración y calibración

Todos los umbrales viven en `reto/config.py` (rangos HSV, tamaños de ROI, áreas mínimas, zona muerta, segundos de PARE, ancho de proceso). **Ningún número mágico dentro de la lógica.** Se puede sobrescribir con un JSON para calibrar el día de la carrera sin tocar el código:

```bash
uv run main.py --config config_pista.json
```

## 6. Estrategia: en qué nos diferenciamos

La rúbrica califica que la estrategia se distinga de la de los otros equipos. Estas son las candidatas, en orden de qué tan propias son:

1. **Calibrar los colores con K-Means (clase 4).** En vez de teclear rangos HSV a ojo, se corre K-Means sobre un frame de la pista real: los centroides son los colores dominantes (pista, línea, señales) y de ahí salen los rangos. Casi todos los equipos van a usar K-Means solo para posterizar imágenes, si es que lo usan. Nos deja recalibrar en segundos si el salón cambia de luz el día de la carrera, y es un uso de una técnica vista en clase que hay que defender bien.
2. **Control anticipativo con dos franjas.** La franja cercana corrige, la lejana anticipa. Es la diferencia entre un carro que zigzaguea y uno que entra suave a la curva, y se nota en el tiempo de recorrido.
3. **Validación de señales por color + forma + persistencia + área.** Menos falsos positivos que un simple "si hay rojo, pare".
4. **Telemetría y grabación de cada corrida.** El HUD y el registro de decisiones alimentan directo el póster y el análisis de resultados, que son dos criterios completos de la rúbrica.

Hay que elegir entre los tres cuáles entran y poder justificarlas; lo que se decida se escribe en `docs/decisiones/`.

## 7. Riesgos conocidos

| Riesgo | Mitigación |
|---|---|
| La luz del salón cambia y los rangos de color dejan de servir | Calibración con K-Means el mismo día; preferir H y S sobre V; probar Lab |
| Latencia o cortes del WiFi con la cámara del celular | Buffer de 1 frame, procesar en pequeño, mostrar FPS; `camara.py` ya reintenta |
| Algo rojo en el fondo (ropa, mueble) dispara un PARE | Validación por forma, área mínima y persistencia; ROI que no mire toda la escena |
| Se pierde la línea en una curva cerrada | Estado `BUSCANDO` hacia el último lado conocido |
| Cada máquina abre una cámara distinta | Fuente por `--fuente` o `CAMARA_URL`, nunca fija en el código |
| Los FPS caen y el control llega tarde | Medir siempre; bajar `ANCHO_PROCESO` antes que optimizar a ciegas |

## 8. Cómo trabajamos

- Una rama por persona (`santiago/camara`, `daniel/pipeline`, `juan/senales`), merge a `main` con revisión rápida del otro.
- Commits en español, cortos y en presente: `agrega deteccion de octagonos por color`.
- Antes de subir: que corra `uv run main.py --fuente datos/videos/<video>.mp4` sin romperse.
- Lo que se aprende en cada ensayo va a `docs/bitacora.md` el mismo día. De ahí sale el póster.
- Las decisiones que cambien el rumbo van a `docs/decisiones/` como un archivo corto.

## 9. Lo que falta

- [ ] Implementar `linea.detectar` (Daniel)
- [ ] Implementar `senales.detectar` (Juan David)
- [ ] Implementar `control.decidir` (Juan David)
- [ ] Descargar los videos del profesor a `datos/videos/` y calibrar con ellos
- [ ] Decidir qué estrategias de la sección 6 entran
- [ ] Definir cómo se le entrega la decisión al robot (¿hay hardware? ¿serial, HTTP?)
- [ ] Confirmar con el profesor los segundos exactos de la señal PARE
