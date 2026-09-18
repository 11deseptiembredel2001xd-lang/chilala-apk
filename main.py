__version__ = "1.0.0"

"""
CHILALA VS JEYSON
Combate 2D en Pygame.

Jugador: Chilala (azul)
Rival: Jeyson (rojo)

Controles:
  A / D                mover
  W / ESPACIO         saltar
  F / ENTER / CLIC    disparar
  ESC                  salir / volver
  Flechas o A/D/W/S   seleccionar nivel en el menú

Niveles: 1 al 10. El Nivel 10 es el más difícil.
"""

import math
import random
import sys
import os
import json
import io
import wave
import struct
import pygame

# -------------------------------------------------
# Configuración
# -------------------------------------------------
ANCHO, ALTO = 960, 540
FPS = 60
SUELO_Y = ALTO - 62
GRAVEDAD = 0.62
SALTO_FUERZA = -13.2
VELOCIDAD_MOV = 5.1

VIDA_MAX = 100
DANO_BALA = 8
VEL_BALA = 11.5
COOLDOWN_DISPARO = 0.32

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Android usa un directorio privado escribible para guardar el progreso.
ARCHIVO_PROGRESO = os.path.join(os.path.expanduser("~"), "progreso_chilala.json") if (sys.platform == "android" or os.environ.get("ANDROID_ARGUMENT")) else os.path.join(BASE_DIR, "progreso_chilala.json")
NIVELES = [
    {"hp": 100, "dano": 7,  "velocidad": 4.2, "decision": (0.55, 0.90), "disparo": 0.035, "salto": 0.14, "distancia": 470},
    {"hp": 105, "dano": 8,  "velocidad": 4.5, "decision": (0.45, 0.78), "disparo": 0.045, "salto": 0.16, "distancia": 485},
    {"hp": 112, "dano": 8,  "velocidad": 4.8, "decision": (0.40, 0.70), "disparo": 0.055, "salto": 0.18, "distancia": 500},
    {"hp": 120, "dano": 9,  "velocidad": 5.1, "decision": (0.35, 0.62), "disparo": 0.065, "salto": 0.20, "distancia": 515},
    {"hp": 130, "dano": 9,  "velocidad": 5.4, "decision": (0.31, 0.56), "disparo": 0.075, "salto": 0.22, "distancia": 530},
    {"hp": 140, "dano": 10, "velocidad": 5.7, "decision": (0.28, 0.51), "disparo": 0.085, "salto": 0.24, "distancia": 545},
    {"hp": 150, "dano": 10, "velocidad": 6.0, "decision": (0.26, 0.47), "disparo": 0.095, "salto": 0.26, "distancia": 560},
    {"hp": 162, "dano": 11, "velocidad": 6.3, "decision": (0.23, 0.43), "disparo": 0.11,  "salto": 0.28, "distancia": 575},
    {"hp": 175, "dano": 12, "velocidad": 6.7, "decision": (0.21, 0.39), "disparo": 0.13,  "salto": 0.31, "distancia": 590},
    {"hp": 190, "dano": 13, "velocidad": 7.1, "decision": (0.18, 0.34), "disparo": 0.155, "salto": 0.34, "distancia": 610},
]
DIFICULTADES = ["Fácil", "Fácil +", "Normal", "Normal +", "Difícil", "Difícil +", "Muy difícil", "Experto", "Pesadilla", "Jefe final"]

# Colores
BLANCO = (245, 248, 255)
NEGRO = (8, 10, 16)
FONDO_1 = (12, 17, 35)
FONDO_2 = (30, 39, 67)
AZUL = (62, 135, 255)
AZUL_CLARO = (130, 196, 255)
ROJO = (241, 74, 88)
ROJO_CLARO = (255, 139, 147)
VERDE = (76, 220, 125)
AMARILLO = (255, 216, 80)
NARANJA = (255, 148, 55)
GRIS = (115, 126, 147)
GRIS_OSC = (38, 45, 61)
GRIS_MUY_OSC = (20, 25, 38)

pygame.init()
ES_ANDROID = sys.platform == "android" or bool(os.environ.get("ANDROID_ARGUMENT"))
_flags = pygame.SCALED | (pygame.FULLSCREEN if ES_ANDROID else 0)
pantalla = pygame.display.set_mode((ANCHO, ALTO), _flags)
pygame.display.set_caption("CHILALA VS JEYSON")
reloj = pygame.time.Clock()

fuente_titulo = pygame.font.SysFont("arial", 48, bold=True)
fuente_grande = pygame.font.SysFont("arial", 34, bold=True)
fuente_media = pygame.font.SysFont("arial", 22, bold=True)
fuente_pequena = pygame.font.SysFont("arial", 17)
fuente_nombre = pygame.font.SysFont("arial", 15, bold=True)
fuente_numero = pygame.font.SysFont("arial", 14, bold=True)

# -------------------------------------------------
# Audio
# -------------------------------------------------
class AudioManager:
    def __init__(self):
        self.ok = False
        self.sounds = {}
        self.music_path = os.path.join(BASE_DIR, "assets", "chilala_soundtrack.wav")
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.ok = True
            self._crear_audio_si_falta()
            self._cargar_sonidos()
        except pygame.error:
            self.ok = False

    def _wave_bytes(self, kind, duration=0.10, volume=0.30, freq=440):
        rate = 44100
        n = int(rate * duration)
        samples = bytearray()
        for i in range(n):
            t = i / rate
            if kind == "shoot":
                f = freq * (1.0 - 0.72 * t / max(duration, 1e-6))
                v = math.sin(2 * math.pi * f * t) * math.exp(-28 * t)
                v += 0.26 * math.sin(2 * math.pi * 95 * t) * math.exp(-18 * t)
            elif kind == "hit":
                v = (random.random() * 2 - 1) * math.exp(-34 * t)
                v += 0.55 * math.sin(2 * math.pi * 120 * t) * math.exp(-22 * t)
            elif kind == "jump":
                f = 180 + 460 * min(1.0, t / max(duration, 1e-6))
                v = math.sin(2 * math.pi * f * t) * math.exp(-12 * t)
            elif kind == "select":
                v = math.sin(2 * math.pi * 620 * t) * math.exp(-24 * t)
            elif kind == "win":
                f = 520 + 260 * t / max(duration, 1e-6)
                v = math.sin(2 * math.pi * f * t) * math.exp(-2.0 * t)
            else:
                v = 0.0
            s = max(-1.0, min(1.0, v * volume))
            samples.extend(struct.pack('<h', int(s * 32767)))
        return bytes(samples)

    def _crear_track(self, path):
        rate = 22050
        dur = 12.0
        tempo = 108.0
        notas = [261.63, 329.63, 392.00, 523.25, 392.00, 329.63, 293.66, 349.23]
        total = int(rate * dur)
        frames = bytearray()
        for i in range(total):
            t = i / rate
            beat = int(t * tempo / 60.0)
            base = notas[beat % len(notas)]
            v = 0.10 * math.sin(2 * math.pi * base * t)
            v += 0.045 * math.sin(2 * math.pi * base * 2 * t)
            bass = [130.81, 146.83, 164.81, 196.00][(beat // 2) % 4]
            v += 0.07 * math.sin(2 * math.pi * bass * t)
            kick_phase = (t * tempo / 60.0) % 1.0
            v += 0.025 * math.sin(2 * math.pi * 75 * t) * math.exp(-18 * kick_phase)
            frames.extend(struct.pack('<h', int(max(-1, min(1, v)) * 32767)))
        with wave.open(str(path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(frames)

    def _crear_audio_si_falta(self):
        os.makedirs(os.path.dirname(self.music_path), exist_ok=True)
        if not os.path.exists(self.music_path):
            self._crear_track(self.music_path)

    def _cargar_sonidos(self):
        self.sounds['disparo'] = pygame.mixer.Sound(buffer=self._wave_bytes('shoot', 0.10, 0.48, 660))
        self.sounds['impacto'] = pygame.mixer.Sound(buffer=self._wave_bytes('hit', 0.12, 0.34, 120))
        self.sounds['salto'] = pygame.mixer.Sound(buffer=self._wave_bytes('jump', 0.16, 0.25, 220))
        self.sounds['seleccionar'] = pygame.mixer.Sound(buffer=self._wave_bytes('select', 0.09, 0.18, 620))
        self.sounds['victoria'] = pygame.mixer.Sound(buffer=self._wave_bytes('win', 0.70, 0.22, 520))
        try:
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.set_volume(0.22)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def play(self, nombre):
        if self.ok and nombre in self.sounds:
            self.sounds[nombre].play()

    def stop_music(self):
        if self.ok:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass

    def pause_music(self):
        if self.ok:
            try:
                pygame.mixer.music.pause()
            except pygame.error:
                pass

    def resume_music(self):
        if self.ok:
            try:
                pygame.mixer.music.unpause()
            except pygame.error:
                pass

AUDIO = AudioManager()

# -------------------------------------------------
# Efectos
# -------------------------------------------------
def crear_estrellas():
    return [
        {
            "x": random.randrange(ANCHO),
            "y": random.randrange(18, SUELO_Y - 38),
            "r": random.choice([1, 1, 1, 2]),
            "brillo": random.randrange(90, 210),
            "fase": random.random() * math.tau,
        }
        for _ in range(75)
    ]


estrellas = crear_estrellas()
particulas = []


def crear_particulas(x, y, color, cantidad=8):
    for _ in range(cantidad):
        angulo = random.random() * math.tau
        velocidad = random.uniform(1.5, 4.5)
        particulas.append({
            "x": float(x),
            "y": float(y),
            "vx": math.cos(angulo) * velocidad,
            "vy": math.sin(angulo) * velocidad,
            "vida": random.uniform(0.25, 0.55),
            "max_vida": 0.55,
            "color": color,
            "r": random.randint(2, 4),
        })


def actualizar_particulas(dt):
    for p in particulas:
        p["vida"] -= dt
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.12
    particulas[:] = [p for p in particulas if p["vida"] > 0]


def dibujar_particulas(superficie):
    for p in particulas:
        vida = max(0.0, p["vida"] / p["max_vida"])
        radio = max(1, int(p["r"] * vida))
        pygame.draw.circle(superficie, p["color"], (int(p["x"]), int(p["y"])), radio)


# -------------------------------------------------
# Fondo
# -------------------------------------------------
def dibujar_fondo(superficie, tiempo):
    for y in range(SUELO_Y):
        t = y / max(1, SUELO_Y)
        color = (
            int(FONDO_1[0] + (FONDO_2[0] - FONDO_1[0]) * t),
            int(FONDO_1[1] + (FONDO_2[1] - FONDO_1[1]) * t),
            int(FONDO_1[2] + (FONDO_2[2] - FONDO_1[2]) * t),
        )
        pygame.draw.line(superficie, color, (0, y), (ANCHO, y))

    # Luna / foco detrás de la arena.
    pygame.draw.circle(superficie, (45, 55, 86), (ANCHO // 2, 115), 72)
    pygame.draw.circle(superficie, (58, 69, 105), (ANCHO // 2, 115), 55)

    for e in estrellas:
        brillo = int(e["brillo"] + 45 * math.sin(tiempo * 0.002 + e["fase"]))
        brillo = max(45, min(230, brillo))
        pygame.draw.circle(
            superficie,
            (brillo, brillo, min(255, brillo + 18)),
            (e["x"], e["y"]),
            e["r"],
        )

    # Edificios/siluetas del fondo.
    edificios = [
        (25, 80, 55), (125, 110, 95), (265, 75, 66),
        (390, 78, 110), (535, 100, 92), (680, 76, 68),
        (790, 120, 100), (900, 55, 76),
    ]
    for x, w, h in edificios:
        pygame.draw.rect(superficie, (17, 23, 40), (x, SUELO_Y - h, w, h))
        for wx in range(x + 12, x + w - 8, 18):
            for wy in range(SUELO_Y - h + 12, SUELO_Y - 10, 18):
                if random.random() < 0.04:
                    pygame.draw.rect(superficie, (53, 62, 83), (wx, wy, 6, 7))

    # Arena.
    pygame.draw.rect(superficie, (29, 35, 50), (0, SUELO_Y, ANCHO, ALTO - SUELO_Y))
    pygame.draw.line(superficie, GRIS, (0, SUELO_Y), (ANCHO, SUELO_Y), 2)
    for x in range(0, ANCHO, 48):
        pygame.draw.line(superficie, (38, 45, 60), (x, SUELO_Y + 5), (x + 22, ALTO), 1)


# -------------------------------------------------
# Plataformas
# -------------------------------------------------
class Plataforma:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def dibujar(self, superficie):
        sombra = self.rect.move(0, 5)
        pygame.draw.rect(superficie, (11, 14, 22), sombra, border_radius=8)
        pygame.draw.rect(superficie, GRIS_OSC, self.rect, border_radius=8)
        pygame.draw.rect(
            superficie,
            (96, 108, 132),
            (self.rect.x, self.rect.y, self.rect.w, 5),
            border_radius=5,
        )
        pygame.draw.rect(superficie, (67, 75, 94), self.rect, 2, border_radius=8)


def crear_plataformas(nivel):
    base = [
        Plataforma(125, SUELO_Y - 118, 195, 22),
        Plataforma(ANCHO - 320, SUELO_Y - 118, 195, 22),
        Plataforma(ANCHO // 2 - 100, SUELO_Y - 220, 200, 22),
    ]
    if nivel >= 2:
        base += [Plataforma(ANCHO // 2 - 305, SUELO_Y - 300, 125, 18), Plataforma(ANCHO // 2 + 180, SUELO_Y - 300, 125, 18)]
    if nivel >= 5:
        base += [Plataforma(42, SUELO_Y - 245, 105, 18), Plataforma(ANCHO - 147, SUELO_Y - 245, 105, 18)]
    if nivel >= 8:
        base += [Plataforma(ANCHO // 2 - 330, SUELO_Y - 390, 105, 16), Plataforma(ANCHO // 2 + 225, SUELO_Y - 390, 105, 16)]
    return base


# -------------------------------------------------
# Balas
# -------------------------------------------------
class Bala:
    def __init__(self, x, y, direccion, color, dueno, dano=DANO_BALA, velocidad=VEL_BALA):
        self.x = float(x)
        self.y = float(y)
        self.direccion = direccion
        self.color = color
        self.dueno = dueno
        self.dano = dano
        self.velocidad = velocidad
        self.radio = 5
        self.viva = True
        self.vida = 0.9

    def actualizar(self, dt):
        self.x += self.velocidad * self.direccion
        self.vida -= dt
        if self.x < -30 or self.x > ANCHO + 30 or self.vida <= 0:
            self.viva = False

    def rect(self):
        return pygame.Rect(
            int(self.x - self.radio), int(self.y - self.radio),
            self.radio * 2, self.radio * 2,
        )

    def dibujar(self, superficie):
        pos = (int(self.x), int(self.y))
        pygame.draw.line(
            superficie,
            self.color,
            (pos[0] - self.direccion * 14, pos[1]),
            pos,
            3,
        )
        pygame.draw.circle(superficie, self.color, pos, self.radio + 3)
        pygame.draw.circle(superficie, BLANCO, pos, 2)


# -------------------------------------------------
# Personajes
# -------------------------------------------------
class Personaje:
    ANCHO_P = 38
    ALTO_P = 56

    def __init__(self, nombre, x, y, color, color_claro, es_bot=False, vida_max=None, velocidad=VELOCIDAD_MOV, dano_bala=DANO_BALA):
        self.nombre = nombre
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.color = color
        self.color_claro = color_claro
        self.mirando = 1 if not es_bot else -1
        self.en_suelo = False
        self.vida_max = VIDA_MAX if vida_max is None else vida_max
        self.vida = self.vida_max
        self.velocidad = velocidad
        self.dano_bala = dano_bala
        self.es_bot = es_bot
        self.cooldown = 0.0
        self.tiempo_decision = 0.0
        self._mov_deseado = 0
        self.tiempo_golpe = 0.0
        self.tiempo_disparo = 0.0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.ANCHO_P, self.ALTO_P)

    def mover(self, dx):
        self.vx = dx * self.velocidad
        if dx:
            self.mirando = 1 if dx > 0 else -1

    def saltar(self):
        if self.en_suelo:
            self.vy = SALTO_FUERZA
            self.en_suelo = False
            crear_particulas(self.x + self.ANCHO_P / 2, self.y + self.ALTO_P, self.color_claro, 7)
            AUDIO.play("salto")

    def disparar(self, balas):
        if self.cooldown > 0 or self.vida <= 0:
            return

        cx = self.x + (self.ANCHO_P + 8 if self.mirando > 0 else -8)
        cy = self.y + self.ALTO_P * 0.36
        color_bala = AMARILLO if not self.es_bot else NARANJA
        dueno = "bot" if self.es_bot else "jugador"
        balas.append(Bala(cx, cy, self.mirando, color_bala, dueno, self.dano_bala, 11.5 if not self.es_bot else self.velocidad + 5.5))
        crear_particulas(cx, cy, color_bala, 5)
        AUDIO.play("disparo")
        self.cooldown = COOLDOWN_DISPARO
        self.tiempo_disparo = 0.08

    def recibir_dano(self, cantidad):
        self.vida = max(0, self.vida - cantidad)
        self.tiempo_golpe = 0.16
        crear_particulas(self.x + self.ANCHO_P / 2, self.y + self.ALTO_P * 0.4, self.color_claro, 10)
        AUDIO.play("impacto")

    def actualizar_fisica(self, dt, plataformas):
        self.vy += GRAVEDAD
        self.x += self.vx
        self.y += self.vy
        self.x = max(0, min(ANCHO - self.ANCHO_P, self.x))

        self.en_suelo = False
        rect_actual = self.rect()

        if self.y + self.ALTO_P >= SUELO_Y:
            self.y = SUELO_Y - self.ALTO_P
            self.vy = 0
            self.en_suelo = True

        for plat in plataformas:
            if rect_actual.colliderect(plat.rect) and self.vy >= 0:
                if rect_actual.bottom - self.vy <= plat.rect.top + 3:
                    self.y = plat.rect.top - self.ALTO_P
                    self.vy = 0
                    self.en_suelo = True

        # Frenado suave.
        self.vx *= 0.84
        if self.cooldown > 0:
            self.cooldown -= dt
        self.tiempo_golpe = max(0, self.tiempo_golpe - dt)
        self.tiempo_disparo = max(0, self.tiempo_disparo - dt)

    def dibujar_etiqueta(self, superficie):
        rect = self.rect()
        nombre_w = max(112, fuente_nombre.size(self.nombre)[0] + 28)
        nombre_h = 25
        nombre_x = rect.centerx - nombre_w // 2
        nombre_y = rect.y - 61

        # Conector visual entre la etiqueta y el personaje.
        pygame.draw.line(
            superficie,
            self.color,
            (rect.centerx, nombre_y + nombre_h),
            (rect.centerx, rect.y - 31),
            2,
        )

        # Placa con nombre.
        pygame.draw.rect(
            superficie,
            NEGRO,
            (nombre_x + 2, nombre_y + 2, nombre_w, nombre_h),
            border_radius=8,
        )
        pygame.draw.rect(
            superficie,
            self.color,
            (nombre_x, nombre_y, nombre_w, nombre_h),
            border_radius=8,
        )
        pygame.draw.rect(
            superficie,
            BLANCO,
            (nombre_x, nombre_y, nombre_w, nombre_h),
            1,
            border_radius=8,
        )
        texto = fuente_nombre.render(self.nombre, True, BLANCO)
        superficie.blit(texto, texto.get_rect(center=(rect.centerx, nombre_y + nombre_h // 2)))

        # Barra de vida sobre el personaje.
        barra_w, barra_h = 106, 9
        barra_x = rect.centerx - barra_w // 2
        barra_y = rect.y - 30
        pygame.draw.rect(
            superficie, NEGRO,
            (barra_x - 2, barra_y - 2, barra_w + 4, barra_h + 4),
            border_radius=5,
        )
        pygame.draw.rect(
            superficie, (61, 68, 82),
            (barra_x, barra_y, barra_w, barra_h),
            border_radius=4,
        )
        ancho = int(barra_w * self.vida / max(1, self.vida_max))
        if ancho > 0:
            pygame.draw.rect(
                superficie, self.color,
                (barra_x, barra_y, ancho, barra_h),
                border_radius=4,
            )

        # Porcentaje pequeño.
        pct = fuente_numero.render(f"{self.vida}/{self.vida_max}", True, BLANCO)
        superficie.blit(pct, pct.get_rect(center=(rect.centerx, barra_y + barra_h / 2)))

    def dibujar(self, superficie):
        rect = self.rect()

        # Sombra del personaje.
        pygame.draw.ellipse(
            superficie,
            (7, 10, 16),
            (rect.x - 8, rect.bottom - 3, rect.w + 16, 11),
        )

        color_cuerpo = BLANCO if self.tiempo_golpe > 0 else self.color
        pygame.draw.rect(superficie, color_cuerpo, rect, border_radius=9)
        pygame.draw.rect(
            superficie,
            self.color_claro,
            (rect.x + 4, rect.y + 4, rect.w - 8, 15),
            border_radius=5,
        )
        pygame.draw.rect(superficie, NEGRO, rect, 2, border_radius=9)

        # Visor / ojo.
        ojo_x = rect.x + (rect.w - 11 if self.mirando > 0 else 1)
        pygame.draw.circle(superficie, NEGRO, (ojo_x + 5, rect.y + 18), 4)

        # Arma.
        arma_x = rect.right if self.mirando > 0 else rect.left - 16
        arma_y = rect.y + int(self.ALTO_P * 0.35)
        pygame.draw.rect(superficie, NEGRO, (arma_x, arma_y, 16, 7), border_radius=3)

        # Flash del disparo.
        if self.tiempo_disparo > 0:
            flash_x = rect.right + 19 if self.mirando > 0 else rect.left - 19
            pygame.draw.circle(superficie, AMARILLO, (flash_x, arma_y + 3), 7)

        # La etiqueta se dibuja por último para que siempre sea legible.
        self.dibujar_etiqueta(superficie)


# -------------------------------------------------
# HUD
# -------------------------------------------------
def dibujar_barra_hud(superficie, x, y, w, h, vida, vida_max, color, nombre, etiqueta):
    pygame.draw.rect(superficie, (6, 9, 16), (x - 5, y - 5, w + 10, h + 10), border_radius=9)
    pygame.draw.rect(superficie, GRIS_OSC, (x, y, w, h), border_radius=6)

    ancho = int(w * max(0, vida) / max(1, vida_max))
    if ancho > 0:
        pygame.draw.rect(superficie, color, (x, y, ancho, h), border_radius=6)

    pygame.draw.rect(superficie, BLANCO, (x, y, w, h), 2, border_radius=6)

    nombre_img = fuente_media.render(nombre, True, BLANCO)
    superficie.blit(nombre_img, (x, y + h + 5))

    etiqueta_img = fuente_pequena.render(etiqueta, True, GRIS)
    superficie.blit(etiqueta_img, (x, y - 20))


def dibujar_hud(superficie, jugador, bot, nivel):
    dibujar_barra_hud(superficie, 24, 18, 292, 19, jugador.vida, jugador.vida_max, AZUL, jugador.nombre, "JUGADOR")
    dibujar_barra_hud(superficie, ANCHO - 316, 18, 292, 19, bot.vida, bot.vida_max, ROJO, bot.nombre, "RIVAL")

    pygame.draw.circle(superficie, GRIS_MUY_OSC, (ANCHO // 2, 31), 24)
    pygame.draw.circle(superficie, GRIS, (ANCHO // 2, 31), 24, 2)
    vs = fuente_media.render("VS", True, BLANCO)
    superficie.blit(vs, vs.get_rect(center=(ANCHO // 2, 31)))

    nivel_img = fuente_pequena.render(f"NIVEL {nivel}  •  {DIFICULTADES[nivel - 1].upper()}", True, AMARILLO)
    superficie.blit(nivel_img, nivel_img.get_rect(center=(ANCHO // 2, 70)))

    controles = fuente_pequena.render(
        "A/D mover  •  W/ESPACIO saltar  •  F/ENTER/Clic disparar  •  ESC salir",
        True, (180, 188, 204),
    )
    superficie.blit(controles, controles.get_rect(center=(ANCHO // 2, ALTO - 18)))


# -------------------------------------------------
# IA
# -------------------------------------------------
def ia_bot(bot, jugador, balas, dt, config):
    bot.tiempo_decision -= dt
    dx = jugador.x - bot.x
    distancia = abs(dx)

    if bot.tiempo_decision <= 0:
        bot.tiempo_decision = random.uniform(*config["decision"])

        if distancia > 285:
            bot._mov_deseado = 1 if dx > 0 else -1
        elif distancia < 125:
            bot._mov_deseado = -1 if dx > 0 else 1
        else:
            bot._mov_deseado = random.choice([-1, 0, 0, 1])

        if random.random() < config["salto"] and bot.en_suelo:
            bot.saltar()

    bot.mover(bot._mov_deseado)
    bot.mirando = 1 if dx > 0 else -1

    diferencia_altura = abs(
        (jugador.y + jugador.ALTO_P / 2) -
        (bot.y + bot.ALTO_P / 2)
    )
    alineado = diferencia_altura < 48 and distancia < config["distancia"]

    if alineado and random.random() < config["disparo"] * (1 + dt * 3):
        bot.disparar(balas)


# -------------------------------------------------
# Pantallas
# -------------------------------------------------
def pantalla_mensaje(titulo, subtitulo, color_titulo=BLANCO):
    esperando = True
    while esperando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                esperando = False
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                esperando = False

        pantalla.fill(NEGRO)
        for y in range(ALTO):
            t = y / max(1, ALTO)
            c = (
                int(9 + 17 * t),
                int(12 + 20 * t),
                int(25 + 32 * t),
            )
            pygame.draw.line(pantalla, c, (0, y), (ANCHO, y))

        panel = pygame.Rect(110, 92, ANCHO - 220, 350)
        pygame.draw.rect(pantalla, (11, 15, 26), panel.move(0, 6), border_radius=24)
        pygame.draw.rect(pantalla, GRIS_MUY_OSC, panel, border_radius=24)
        pygame.draw.rect(pantalla, GRIS_OSC, panel, 2, border_radius=24)

        # Título del juego.
        logo = fuente_pequena.render("ARENA 2D", True, GRIS)
        pantalla.blit(logo, logo.get_rect(center=(ANCHO // 2, 126)))

        t1 = fuente_titulo.render(titulo, True, color_titulo)
        pantalla.blit(t1, t1.get_rect(center=(ANCHO // 2, 185)))

        t2 = fuente_media.render(subtitulo, True, BLANCO)
        pantalla.blit(t2, t2.get_rect(center=(ANCHO // 2, 245)))

        c1 = fuente_pequena.render("CHILALA", True, AZUL_CLARO)
        c2 = fuente_pequena.render("VS", True, BLANCO)
        c3 = fuente_pequena.render("JEYSON", True, ROJO_CLARO)
        pantalla.blit(c1, c1.get_rect(center=(ANCHO // 2 - 125, 291)))
        pantalla.blit(c2, c2.get_rect(center=(ANCHO // 2, 291)))
        pantalla.blit(c3, c3.get_rect(center=(ANCHO // 2 + 125, 291)))

        pista = fuente_pequena.render(
            "Pulsa una tecla o haz clic para continuar",
            True, GRIS,
        )
        pantalla.blit(pista, pista.get_rect(center=(ANCHO // 2, 350)))

        pygame.display.flip()
        reloj.tick(FPS)


# -------------------------------------------------
# Selección de niveles
# -------------------------------------------------
def cargar_progreso():
    try:
        with open(ARCHIVO_PROGRESO, "r", encoding="utf-8") as f:
            data = json.load(f)
            nivel = int(data.get("mejor_nivel", 1))
            return max(1, min(10, nivel))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 1


def guardar_progreso(nivel):
    try:
        with open(ARCHIVO_PROGRESO, "w", encoding="utf-8") as f:
            json.dump({"mejor_nivel": max(1, min(10, int(nivel)))}, f)
    except OSError:
        pass


def dibujar_panel_nivel(superficie, rect, nivel, seleccionado, desbloqueado):
    if desbloqueado:
        fondo = (25, 35, 56) if not seleccionado else (40, 64, 98)
        borde = AZUL_CLARO if seleccionado else GRIS
        numero_color = BLANCO
    else:
        fondo = (20, 23, 31)
        borde = (58, 63, 74)
        numero_color = (90, 95, 105)

    pygame.draw.rect(superficie, (5, 8, 14), rect.move(0, 5), border_radius=14)
    pygame.draw.rect(superficie, fondo, rect, border_radius=14)
    pygame.draw.rect(superficie, borde, rect, 2, border_radius=14)

    numero = fuente_grande.render(str(nivel), True, numero_color)
    superficie.blit(numero, numero.get_rect(center=(rect.centerx, rect.centery - 10)))

    label = fuente_numero.render("BLOQUEADO" if not desbloqueado else DIFICULTADES[nivel - 1], True, numero_color)
    superficie.blit(label, label.get_rect(center=(rect.centerx, rect.bottom - 17)))


def seleccionar_nivel():
    seleccionado = 1
    mejor_nivel = cargar_progreso()
    ejecutando = True
    columnas = 5
    botones = []

    while ejecutando:
        botones.clear()
        ancho, alto = 132, 105
        margen_x = 54
        inicio_y = 150
        separacion_x = 24
        separacion_y = 20
        for i in range(10):
            fila = i // columnas
            col = i % columnas
            x = margen_x + col * (ancho + separacion_x)
            y = inicio_y + fila * (alto + separacion_y)
            botones.append(pygame.Rect(x, y, ancho, alto))

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if evento.key in (pygame.K_a, pygame.K_LEFT):
                    seleccionado = max(1, seleccionado - 1)
                elif evento.key in (pygame.K_d, pygame.K_RIGHT):
                    seleccionado = min(10, seleccionado + 1)
                elif evento.key in (pygame.K_w, pygame.K_UP):
                    seleccionado = max(1, seleccionado - 5)
                elif evento.key in (pygame.K_s, pygame.K_DOWN):
                    seleccionado = min(10, seleccionado + 5)
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    AUDIO.play("seleccionar")
                    return seleccionado
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for i, rect in enumerate(botones, start=1):
                    if rect.collidepoint(evento.pos):
                        AUDIO.play("seleccionar")
                        return i

        # Fondo de menú.
        dibujar_fondo(pantalla, pygame.time.get_ticks())
        velo = pygame.time.get_ticks() * 0.002
        titulo = fuente_titulo.render("SELECCIONA TU NIVEL", True, BLANCO)
        pantalla.blit(titulo, titulo.get_rect(center=(ANCHO // 2, 72)))
        sub = fuente_media.render("Chilala VS Jeyson  •  10 niveles de dificultad", True, GRIS)
        pantalla.blit(sub, sub.get_rect(center=(ANCHO // 2, 112)))

        for i, rect in enumerate(botones, start=1):
            # Todos los niveles se pueden elegir desde el menú; el progreso indica el nivel más alto ganado.
            seleccionado_flag = (i == seleccionado)
            dibujar_panel_nivel(pantalla, rect, i, seleccionado_flag, True)

        info = fuente_pequena.render(
            f"Nivel {seleccionado}: {DIFICULTADES[seleccionado - 1]}  •  Mejor nivel superado: {mejor_nivel}  •  ENTER/clic para jugar",
            True, BLANCO,
        )
        pantalla.blit(info, info.get_rect(center=(ANCHO // 2, ALTO - 24)))
        pygame.display.flip()
        reloj.tick(FPS)


# -------------------------------------------------
# Controles táctiles para Android
# -------------------------------------------------
touch_points = {}


def touch_xy(evento):
    """Convierte coordenadas normalizadas de FINGER* a la resolución lógica."""
    return int(evento.x * ANCHO), int(evento.y * ALTO)


def actualizar_touch_evento(evento):
    if evento.type == pygame.FINGERDOWN or evento.type == pygame.FINGERMOTION:
        touch_points[evento.finger_id] = touch_xy(evento)
    elif evento.type == pygame.FINGERUP:
        touch_points.pop(evento.finger_id, None)


def zonas_tactiles():
    """Devuelve zonas grandes y cómodas para jugar en teléfono."""
    y = ALTO - 96
    return {
        "izq": pygame.Rect(26, y, 82, 70),
        "der": pygame.Rect(120, y, 82, 70),
        "saltar": pygame.Rect(ANCHO - 205, y, 82, 70),
        "disparo": pygame.Rect(ANCHO - 102, y, 76, 70),
    }


def dibujar_controles_tactiles(superficie):
    if not ES_ANDROID:
        return
    zonas = zonas_tactiles()
    acciones = [("◀", "izq"), ("▶", "der"), ("↑", "saltar"), ("●", "disparo")]
    for texto, clave in acciones:
        r = zonas[clave]
        pulsado = any(r.collidepoint(pos) for pos in touch_points.values())
        fondo = (37, 53, 80) if not pulsado else (58, 88, 128)
        pygame.draw.rect(superficie, (7, 10, 17), r.move(0, 5), border_radius=18)
        pygame.draw.rect(superficie, fondo, r, border_radius=18)
        pygame.draw.rect(superficie, BLANCO, r, 2, border_radius=18)
        f = fuente_grande.render(texto, True, BLANCO)
        superficie.blit(f, f.get_rect(center=r.center))


def estado_controles_tactiles():
    zonas = zonas_tactiles()
    izquierda = any(zonas["izq"].collidepoint(pos) for pos in touch_points.values())
    derecha = any(zonas["der"].collidepoint(pos) for pos in touch_points.values())
    saltar = any(zonas["saltar"].collidepoint(pos) for pos in touch_points.values())
    disparar = any(zonas["disparo"].collidepoint(pos) for pos in touch_points.values())
    return izquierda, derecha, saltar, disparar


# -------------------------------------------------
# Partida
# -------------------------------------------------
def jugar(nivel):
    global particulas
    particulas = []

    config = NIVELES[nivel - 1]
    plataformas = crear_plataformas(nivel)
    jugador = Personaje(
        "Chilala", 100, SUELO_Y - Personaje.ALTO_P,
        AZUL, AZUL_CLARO, es_bot=False,
        vida_max=VIDA_MAX, velocidad=VELOCIDAD_MOV, dano_bala=DANO_BALA,
    )
    bot = Personaje(
        "Jeyson", ANCHO - 140, SUELO_Y - Personaje.ALTO_P,
        ROJO, ROJO_CLARO, es_bot=True,
        vida_max=config["hp"], velocidad=config["velocidad"], dano_bala=config["dano"],
    )
    balas = []
    corriendo = True
    resultado = None
    tiempo = 0.0
    salto_touch_prev = False
    disparo_touch_prev = False

    while corriendo:
        dt = min(reloj.tick(FPS) / 1000.0, 0.033)
        tiempo += dt

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if evento.key in (pygame.K_w, pygame.K_SPACE):
                    jugador.saltar()
                elif evento.key in (pygame.K_RETURN, pygame.K_f):
                    jugador.disparar(balas)

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                jugador.disparar(balas)
            elif ES_ANDROID and evento.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
                actualizar_touch_evento(evento)

        # Movimiento del jugador (teclado + táctil).
        teclas = pygame.key.get_pressed()
        dx = int(teclas[pygame.K_d]) - int(teclas[pygame.K_a])
        izq_touch, der_touch, salto_touch, disparo_touch = estado_controles_tactiles()
        if izq_touch:
            dx -= 1
        if der_touch:
            dx += 1
        dx = max(-1, min(1, dx))
        jugador.mover(dx)

        if salto_touch and not salto_touch_prev:
            jugador.saltar()
        if disparo_touch and not disparo_touch_prev:
            jugador.disparar(balas)
        salto_touch_prev = salto_touch
        disparo_touch_prev = disparo_touch

        # IA del rival.
        ia_bot(bot, jugador, balas, dt, config)

        jugador.actualizar_fisica(dt, plataformas)
        bot.actualizar_fisica(dt, plataformas)

        # Actualizar proyectiles.
        for bala in balas:
            bala.actualizar(dt)

        # Colisiones de proyectiles.
        objetivo_jugador = jugador.rect()
        objetivo_bot = bot.rect()
        for bala in balas:
            if not bala.viva:
                continue

            if bala.dueno == "bot" and objetivo_jugador.colliderect(bala.rect()):
                jugador.recibir_dano(bala.dano)
                bala.viva = False
            elif bala.dueno == "jugador" and objetivo_bot.colliderect(bala.rect()):
                bot.recibir_dano(bala.dano)
                bala.viva = False

        balas[:] = [b for b in balas if b.viva]
        actualizar_particulas(dt)

        if jugador.vida <= 0:
            corriendo = False
            resultado = "derrota"
        elif bot.vida <= 0:
            corriendo = False
            resultado = "victoria"

        # Dibujado.
        dibujar_fondo(pantalla, tiempo * 1000)

        for plat in plataformas:
            plat.dibujar(pantalla)

        dibujar_particulas(pantalla)
        for bala in balas:
            bala.dibujar(pantalla)

        jugador.dibujar(pantalla)
        bot.dibujar(pantalla)
        dibujar_hud(pantalla, jugador, bot, nivel)
        dibujar_controles_tactiles(pantalla)

        pygame.display.flip()

    return resultado


# -------------------------------------------------
# Programa principal
# -------------------------------------------------
def main():
    nivel = seleccionar_nivel()

    while True:
        resultado = jugar(nivel)
        if resultado == "victoria":
            AUDIO.play("victoria")
            if nivel < 10:
                guardar_progreso(max(cargar_progreso(), nivel + 1))
                pantalla_mensaje(
                    f"¡NIVEL {nivel} COMPLETADO!",
                    f"Nivel {nivel} superado. El Nivel {nivel + 1} está listo para jugar. Pulsa una tecla para continuar.",
                    AZUL_CLARO,
                )
            else:
                guardar_progreso(10)
                pantalla_mensaje(
                    "¡JEFE FINAL DERROTADO!",
                    "Completaste los 10 niveles. Pulsa una tecla para volver al menú.",
                    AMARILLO,
                )
        else:
            pantalla_mensaje(
                f"¡JEYSON GANA EL NIVEL {nivel}!",
                "Pulsa una tecla para volver a la selección de niveles.",
                ROJO_CLARO,
            )
        nivel = seleccionar_nivel()


if __name__ == "__main__":
    main()
