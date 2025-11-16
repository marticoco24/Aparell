## 🔧 FASE 0 – Lo que ya tienes hecho

Esto ya está ✅:

* Web para escribir mensajes (en tu PC).
* Backend Flask que guarda el último mensaje y lo sirve en `/ultimo_mensaje`.

Por ahora nos sirve **para probar el aparato** en casa (aunque luego lo subamos a un servidor en la nube).

---

## 🛒 FASE 1 – Qué material necesitas comprar

Para **1 aparato** (luego haces otro igual):

1. **Placa ESP32 “dev board”**
   Busca algo tipo:

   * `ESP32 DevKitC`
   * `NodeMCU-32S`
   * Cualquier “ESP32 development board” con USB.

   Que tenga:

   * Puerto USB normal (micro-USB o USB-C)
   * Botón BOOT / EN (suelen venir).

2. **Pantalla OLED I2C 0.96"**
   Busca:

   * `OLED 0.96 I2C 128x64 SSD1306`

   Normalmente tiene 4 pines: `VCC`, `GND`, `SCL`, `SDA`.

3. **2 LEDs normales** (por ejemplo blanco y rojo, o dos blancos).

4. **2 resistencias** para los LEDs
   Valor típico: **220 Ω** o **330 Ω**.

5. **Protoboard**
   Una placa blanca para montar el circuito sin soldar.

6. **Cables Dupont**
   Macho–macho (y un poco de macho–hembra por si acaso).

7. **Cable USB**
   Para conectar el ESP32 al PC.

Para el futuro (cuando todo funcione), ya pensaréis **caja bonita**, pero para empezar basta esto.

---

## 🖥️ FASE 2 – Preparar el entorno del ESP32 en tu PC

Lo vamos a hacer con **Arduino IDE** porque es más visual para empezar.

### 2.1. Instalar Arduino IDE

1. Ve a la web de Arduino (`arduino.cc → Software → Arduino IDE`).
2. Descarga la versión para Windows.
3. Instala normalmente (siguiente, siguiente…).

### 2.2. Añadir soporte para ESP32 en Arduino IDE

1. Abre **Arduino IDE**.

2. Arriba: **File → Preferences**.

3. En el campo: **“Additional Boards Manager URLs”** pega:

   ```text
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```

   (Si ya hay algo, pon una coma y luego este link).

4. Pulsa **OK**.

5. Ahora ve a:
   **Tools → Board → Boards Manager…**

6. Busca “esp32”.

7. Instala el paquete **“esp32 by Espressif Systems”**.

Cuando acabe, ya podrás elegir placas ESP32 desde Arduino.

---

## 📲 FASE 3 – Primer contacto con la placa

Cuando te llegue la placa:

### 3.1. Conectar el ESP32

1. Conecta el ESP32 al PC con el cable USB.
2. En Arduino IDE:

   * **Tools → Board → ESP32 Arduino →** el modelo que más se parezca a tu placa (por ejemplo “ESP32 Dev Module”).
   * **Tools → Port →** el puerto donde aparezca (COM3, COM4, etc. – si dudas, desconecta y vuelve a conectar para ver cuál aparece).

### 3.2. Probar un “Blink” (LED interno o externo)

Antes de meternos con WiFi:

1. En Arduino IDE:
   **File → Examples → 01.Basics → Blink**.
2. Modifica la línea del pin si hace falta (en muchas placas ESP32 el LED interno suele ser el GPIO2, pero eso depende de la placa; si no tiene LED interno, luego usaremos uno externo).
3. Sube el programa:

   * Botón **Upload** (flecha a la derecha arriba).
   * Mira la barra de abajo, debería compilar y subir sin error.

Si ves algún LED parpadear, genial. Si no, no pasa nada: más adelante usaremos LEDs externos y ahí controlamos todo.

---

## 🔌 FASE 4 – Conectar la pantalla y LEDs en la protoboard

Cuando ya sepas subir programas, montamos el circuito del primer aparato.

### 4.1. Conexión de la pantalla OLED I2C

En la protoboard:

* OLED `VCC` → 3V3 del ESP32.
* OLED `GND` → GND del ESP32.
* OLED `SCL` → GPIO22 del ESP32 (típico SCL).
* OLED `SDA` → GPIO21 del ESP32 (típico SDA).

*(Luego, si tu placa tiene otros pines I2C, lo adaptamos, pero esta es la combinación estándar).*

### 4.2. Conexión de los LEDs

Supongamos:

* **LED A (tu estado de conexión)** en el pin GPIO 4.
* **LED B (estado del otro / mensajes)** en el pin GPIO 2.

Conexión típica de un LED:

* Patilla larga del LED → **resistencia** (220–330Ω) → pin GPIO.
* Patilla corta del LED → **GND**.

Así:

* GPIO4 → resistencia → LED A → GND.
* GPIO2 → resistencia → LED B → GND.

---

## 🌐 FASE 5 – Primer programa “serio” del ESP32

Aquí ya hacemos cosas que hablan con el servidor.

Primero solo con **WiFi**, sin aún sacar texto en la pantalla.

### 5.1. Probar conexión WiFi (con el router de casa)

Antes de hotspots y móviles, más fácil:

1. En Arduino, escribe un sketch sencillo que:

   * Use tu WiFi de casa:

   ```cpp
   const char* ssid     = "NOMBRE_DE_TU_WIFI";
   const char* password = "CONTRASEÑA_DE_TU_WIFI";
   ```

   * Se conecte y muestre en el **Serial Monitor** si se ha conectado.

2. Abre **Tools → Serial Monitor** (arriba derecha), pon la misma velocidad (por ejemplo 115200) que en el código, y mira los mensajes.

Con eso validamos:

* que el ESP32 se conecta a una red WiFi,
* que eres capaz de ver mensajes por Serial.

### 5.2. Hacer un GET a tu backend local (`/ultimo_mensaje`)

Luego, modificamos el programa para que:

1. Tras conectarse a WiFi:

   * haga una petición HTTP a:

     ```text
     http://192.168.1.59:5000/ultimo_mensaje
     ```

     (la IP que te salía en Flask).
2. Reciba el JSON.
3. Lo imprima por Serial.

No hace falta entender perfecto el JSON, solo ver que llega algo como:

```json
{"id": 3, "text": "hola 💌", "is_read": false, ...}
```

Con eso ya tienes el **cableado completo**:

> ESP32 → WiFi → tu PC con Flask → responde JSON.

---

## 🖥️ FASE 6 – Mostrar el mensaje en la pantalla OLED y controlar LEDs

Cuando lo anterior funcione, añadimos:

1. **Librería para la pantalla OLED SSD1306** (en Arduino:

   * **Tools → Manage Libraries →** busca:

     * `Adafruit SSD1306`
     * `Adafruit GFX`
   * Instálalas.)

2. En el código:

   * Parseas el JSON para sacar `text`.
   * Inicializas la pantalla.
   * Escribes el `text` en la OLED (si es largo, lo partimos en varias líneas).

3. Para los LEDs:

   * LED A: se enciende cuando `WiFi.status() == WL_CONNECTED`.
   * LED B:

     * Si `has_unread` → animación fuerte un ratito.
     * Si no `has_unread` pero `other_online` → brillo suave (podemos hacer un “pwm” con `analogWrite` o un parpadeo lento).
     * Si nada → apagado.

> De momento, `has_unread` y `other_online` nos los inventamos (hardcode) para probar las animaciones de LED.
> Más adelante vendrán de un endpoint tipo `/estado`.

---

## ☁️ FASE 7 – Pasar del PC a un servidor en la nube

Cuando:

* el aparato ya sea capaz de:

  * conectarse a WiFi,
  * pedir un mensaje al backend,
  * mostrarlo,
  * usar LEDs en función de lo que devuelva el servidor,

entonces:

1. Cogemos tu app Flask.

2. La subimos a una plataforma (tipo Render / Railway / PythonAnywhere).

3. Obtienes una URL del estilo:

   ```text
   https://loquesea.tudominio.com/estado
   ```

4. En el ESP32 cambias la URL de `http://192.168.1.59:5000/...` por la URL pública.

Y ya está:
👉 cualquier aparato conectado a internet (a través del hotspot) podrá hablar con el servidor, estés tú en Barcelona o en Australia.

---