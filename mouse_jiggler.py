#!/usr/bin/env python3
"""
Mouse Jiggler - Simuliert Mausbewegungen mit systemnahen APIs.
Windows: SendInput API | macOS: CoreGraphics (Quartz) Events, cliclick Fallback
"""

import time
import random
import sys
import platform
import ctypes
import subprocess
import shutil
from ctypes import wintypes, Structure, Union, POINTER, byref, sizeof
from datetime import datetime, time as dt_time
from typing import Tuple, Optional

# Backend-Tracking für macOS (cgevent oder cliclick)
_macos_backend = "cgevent"


# ============================================================================
# Windows SendInput Implementation
# ============================================================================

if platform.system() == "Windows":
    # Konstanten für SendInput
    INPUT_MOUSE = 0
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_ABSOLUTE = 0x8000

    # Windows Virtual Key Codes (für zukünftige Erweiterungen)
    VK_LBUTTON = 0x01
    VK_RBUTTON = 0x02

    class MOUSEINPUT(Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
        ]

    class KEYBDINPUT(Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
        ]

    class HARDWAREINPUT(Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD)
        ]

    class INPUT_UNION(Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
            ("hi", HARDWAREINPUT)
        ]

    class INPUT(Structure):
        _fields_ = [
            ("type", wintypes.DWORD),
            ("union", INPUT_UNION)
        ]

    def get_screen_size():
        """Ermittelt die Bildschirmgröße für absolute Mauskoordinaten."""
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    def send_mouse_move_relative(dx: int, dy: int):
        """
        Sendet relative Mausbewegung via SendInput.

        Args:
            dx: Relative Bewegung in X-Richtung (Pixel)
            dy: Relative Bewegung in Y-Richtung (Pixel)
        """
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.dx = dx
        inp.union.mi.dy = dy
        inp.union.mi.mouseData = 0
        inp.union.mi.dwFlags = MOUSEEVENTF_MOVE  # Relative Bewegung
        inp.union.mi.time = 0
        inp.union.mi.dwExtraInfo = None

        # Sende das Input-Event
        result = ctypes.windll.user32.SendInput(1, byref(inp), sizeof(inp))
        if result == 0:
            raise ctypes.WinError()
        return result

    def send_mouse_move_absolute(x: int, y: int):
        """
        Sendet absolute Mausbewegung via SendInput.
        Koordinaten werden auf 0-65535 normalisiert.

        Args:
            x: Absolute X-Position (Bildschirmkoordinaten)
            y: Absolute Y-Position (Bildschirmkoordinaten)
        """
        screen_x, screen_y = get_screen_size()

        # Normalisiere auf 0-65535 Bereich
        normalized_x = int(x * 65535 / screen_x)
        normalized_y = int(y * 65535 / screen_y)

        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.dx = normalized_x
        inp.union.mi.dy = normalized_y
        inp.union.mi.mouseData = 0
        inp.union.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        inp.union.mi.time = 0
        inp.union.mi.dwExtraInfo = None

        result = ctypes.windll.user32.SendInput(1, byref(inp), sizeof(inp))
        if result == 0:
            raise ctypes.WinError()
        return result

    def get_cursor_position() -> Tuple[int, int]:
        """Ermittelt die aktuelle Mausposition via GetCursorPos."""
        point = wintypes.POINT()
        if ctypes.windll.user32.GetCursorPos(byref(point)):
            return (point.x, point.y)
        raise ctypes.WinError()

    def send_mouse_move_smooth(dx: int, dy: int, steps: int = 3, delay: float = 0.005):
        """
        Sanfte Mausbewegung in mehreren Schritten.

        Args:
            dx: Gesamte relative Bewegung X
            dy: Gesamte relative Bewegung Y
            steps: Anzahl der Zwischenschritte
            delay: Verzögerung zwischen Schritten in Sekunden
        """
        for i in range(1, steps + 1):
            step_x = dx * i // steps - dx * (i - 1) // steps
            step_y = dy * i // steps - dy * (i - 1) // steps

            if step_x != 0 or step_y != 0:
                send_mouse_move_relative(step_x, step_y)

            if i < steps:
                time.sleep(delay)


# ============================================================================
# macOS CoreGraphics (Quartz) Implementation + cliclick Fallback
# ============================================================================

elif platform.system() == "Darwin":
    # Versuche Quartz zu laden
    _has_quartz = False
    try:
        import Quartz
        from Quartz import (
            CGEventCreateMouseEvent,
            CGEventPost,
            CGEventGetLocation,
            CGEventSetIntegerValueField,
            kCGEventMouseMoved,
            kCGHIDEventTap,
            kCGMouseEventDeltaX,
            kCGMouseEventDeltaY,
        )
        _has_quartz = True
    except ImportError:
        _has_quartz = False

    # Prüfe ob cliclick verfügbar ist
    _cliclick_path = shutil.which("cliclick")

    if not _has_quartz and not _cliclick_path:
        print("❌ Weder pyobjc-framework-Quartz noch cliclick verfügbar.")
        print("   Option 1: uv pip install pyobjc-framework-Quartz")
        print("   Option 2: brew install cliclick")
        sys.exit(1)

    def _cliclick_get_position() -> Tuple[int, int]:
        """Ermittelt Mausposition via cliclick."""
        result = subprocess.run(
            [_cliclick_path, "p:."],
            capture_output=True, text=True
        )
        # Output kann Warning enthalten, Position ist letzte Zeile im Format "x,y"
        lines = result.stdout.strip().splitlines()
        pos_line = lines[-1] if lines else result.stdout.strip()
        parts = pos_line.split(",")
        return (int(parts[0]), int(parts[1]))

    def _cliclick_move_relative(dx: int, dy: int):
        """Bewegt Maus relativ via cliclick."""
        # cliclick relative move: m:+dx,+dy
        sign_x = f"+{dx}" if dx >= 0 else str(dx)
        sign_y = f"+{dy}" if dy >= 0 else str(dy)
        subprocess.run(
            [_cliclick_path, f"m:{sign_x},{sign_y}"],
            capture_output=True
        )

    def _cliclick_move_absolute(x: int, y: int):
        """Bewegt Maus absolut via cliclick."""
        subprocess.run(
            [_cliclick_path, f"m:{x},{y}"],
            capture_output=True
        )

    def _detect_backend() -> str:
        """Erkennt ob CGEvent funktioniert, sonst Fallback auf cliclick."""
        global _macos_backend

        if not _has_quartz:
            if _cliclick_path:
                _macos_backend = "cliclick"
                return "cliclick"
            else:
                raise RuntimeError("Kein Backend verfügbar")

        # Teste ob CGEvent tatsächlich funktioniert (Permissions)
        try:
            pos_before = _cgevent_get_position()
            event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (0, 0), 0)
            CGEventSetIntegerValueField(event, kCGMouseEventDeltaX, 10)
            CGEventSetIntegerValueField(event, kCGMouseEventDeltaY, 10)
            CGEventPost(kCGHIDEventTap, event)
            time.sleep(0.05)
            pos_after = _cgevent_get_position()

            if pos_before != pos_after:
                _macos_backend = "cgevent"
                return "cgevent"
            elif _cliclick_path:
                _macos_backend = "cliclick"
                return "cliclick"
            else:
                _macos_backend = "cgevent"
                return "cgevent"
        except Exception:
            if _cliclick_path:
                _macos_backend = "cliclick"
                return "cliclick"
            _macos_backend = "cgevent"
            return "cgevent"

    def _cgevent_get_position() -> Tuple[int, int]:
        """Ermittelt Mausposition via CoreGraphics."""
        loc = CGEventGetLocation(None)
        return (int(loc.x), int(loc.y))

    def get_cursor_position() -> Tuple[int, int]:
        """Ermittelt aktuelle Mausposition (Backend-abhängig)."""
        if _macos_backend == "cliclick":
            return _cliclick_get_position()
        return _cgevent_get_position()

    def send_mouse_move_relative(dx: int, dy: int):
        """Sendet relative Mausbewegung (Backend-abhängig)."""
        if _macos_backend == "cliclick":
            _cliclick_move_relative(dx, dy)
            return

        event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (0, 0), 0)
        CGEventSetIntegerValueField(event, kCGMouseEventDeltaX, dx)
        CGEventSetIntegerValueField(event, kCGMouseEventDeltaY, dy)
        CGEventPost(kCGHIDEventTap, event)

    def send_mouse_move_absolute(x: int, y: int):
        """Sendet absolute Mausbewegung (Backend-abhängig)."""
        if _macos_backend == "cliclick":
            _cliclick_move_absolute(x, y)
            return

        event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), 0)
        CGEventPost(kCGHIDEventTap, event)

    def send_mouse_move_smooth(dx: int, dy: int, steps: int = 3, delay: float = 0.005):
        """Sanfte Mausbewegung in mehreren Schritten."""
        if _macos_backend == "cliclick":
            # cliclick: weniger Schritte da subprocess-Overhead
            reduced_steps = max(1, steps // 2)
            for i in range(1, reduced_steps + 1):
                step_x = dx * i // reduced_steps - dx * (i - 1) // reduced_steps
                step_y = dy * i // reduced_steps - dy * (i - 1) // reduced_steps
                if step_x != 0 or step_y != 0:
                    _cliclick_move_relative(step_x, step_y)
                if i < reduced_steps:
                    time.sleep(delay * 2)
            return

        for i in range(1, steps + 1):
            step_x = dx * i // steps - dx * (i - 1) // steps
            step_y = dy * i // steps - dy * (i - 1) // steps
            if step_x != 0 or step_y != 0:
                send_mouse_move_relative(step_x, step_y)
            if i < steps:
                time.sleep(delay)


# ============================================================================
# Gemeinsame Klassen
# ============================================================================

class TimeWindow:
    """Klasse für Zeitfenster-Verwaltung."""

    def __init__(self, start_time: str = "09:00", end_time: str = "17:00"):
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)
        self.is_active = True

    def _parse_time(self, time_str: str) -> dt_time:
        """Parst Zeit-String in time-Objekt."""
        try:
            hours, minutes = map(int, time_str.split(":"))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError
            return dt_time(hours, minutes)
        except (ValueError, AttributeError):
            print(f"❌ Ungültiges Zeitformat: '{time_str}'. Verwende HH:MM (24h)")
            sys.exit(1)

    def is_within_window(self) -> bool:
        """Prüft ob aktuelle Zeit im Zeitfenster liegt."""
        if not self.is_active:
            return True

        current_time = datetime.now().time()

        if self.start_time <= self.end_time:
            return self.start_time <= current_time <= self.end_time
        else:
            return current_time >= self.start_time or current_time <= self.end_time

    def get_next_activation(self) -> Optional[datetime]:
        """Berechnet den nächsten Aktivierungszeitpunkt."""
        if not self.is_active:
            return None

        now = datetime.now()
        current_time = now.time()

        if self.is_within_window():
            return now

        start_dt = datetime.combine(now.date(), self.start_time)

        if current_time > self.end_time and self.start_time <= self.end_time:
            start_dt = datetime.combine(
                datetime.fromordinal(now.date().toordinal() + 1).date(),
                self.start_time
            )
        elif current_time > self.end_time and self.start_time > self.end_time:
            if current_time < self.start_time:
                start_dt = datetime.combine(now.date(), self.start_time)
            else:
                start_dt = datetime.combine(
                    datetime.fromordinal(now.date().toordinal() + 1).date(),
                    self.start_time
                )

        return start_dt

    def get_status_message(self) -> str:
        """Gibt Status-Nachricht zurück."""
        if not self.is_active:
            return "Zeitfenster deaktiviert - 24/7 aktiv"

        current_time = datetime.now().time()
        in_window = self.is_within_window()

        start_str = self.start_time.strftime("%H:%M")
        end_str = self.end_time.strftime("%H:%M")
        current_str = current_time.strftime("%H:%M")

        if in_window:
            return f"✅ Aktiv ({start_str}-{end_str}) - Aktuell: {current_str}"
        else:
            next_activation = self.get_next_activation()
            if next_activation:
                wait_minutes = (next_activation - datetime.now()).total_seconds() / 60
                return (f"⏸️  Inaktiv ({start_str}-{end_str}) - Aktuell: {current_str}"
                        f" - Nächste Aktivierung: {next_activation.strftime('%H:%M')}"
                        f" (in {wait_minutes:.0f} Min.)")
            return f"⏸️  Inaktiv ({start_str}-{end_str}) - Aktuell: {current_str}"


class MouseJiggler:
    """
    Mouse Jiggler mit systemnahen APIs.
    Windows: SendInput (kernel32/user32)
    macOS: CoreGraphics (Quartz) / cliclick
    """

    def __init__(self, time_window: Optional[TimeWindow] = None):
        self.os_type = platform.system()
        self.time_window = time_window or TimeWindow()

        # Auf macOS: Backend erkennen (CGEvent vs cliclick)
        if self.os_type == "Darwin":
            backend = _detect_backend()
            print(f"🖱️  Mouse Jiggler ({self.os_type}) — Backend: {backend}")
            if backend == "cliclick":
                print("   ℹ️  CGEvent nicht verfügbar, nutze cliclick als Fallback")
        else:
            print(f"🖱️  Mouse Jiggler ({self.os_type})")

        print(f"   Windows: SendInput API | macOS: CGEvent/cliclick")
        print("   Drücke Ctrl+C zum Beenden...")

    def jiggle(self,
               duration_minutes: float = 60,
               interval_seconds: float = 30,
               movement_range: int = 3,
               smooth_steps: int = 4,
               pattern: str = "random"):
        """
        Führt die Mausbewegung aus.

        Args:
            duration_minutes: Gesamtdauer in Minuten (None = unendlich)
            interval_seconds: Intervall zwischen Bewegungen in Sekunden
            movement_range: Maximale Bewegung in Pixeln pro Richtung
            smooth_steps: Anzahl der Schritte für sanfte Bewegung
            pattern: Bewegungsmuster ("random", "circle", "zigzag")
        """
        print(f"📋 Dauer: {'unendlich' if duration_minutes is None else f'{duration_minutes} Minuten'}")
        print(f"⏱️  Intervall: {interval_seconds}s | Bewegung: ±{movement_range}px | Schritte: {smooth_steps}")
        print(f"🕐 {self.time_window.get_status_message()}")
        print("-" * 50)

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60) if duration_minutes else None
        movement_count = 0
        pattern_step = 0

        try:
            while True:
                # Prüfe ob Zeitlimit erreicht
                if end_time and time.time() >= end_time:
                    print("\n⏰ Zeitlimit erreicht. Beende Mouse Jiggler.")
                    break

                # Prüfe ob wir im aktiven Zeitfenster sind
                if self.time_window.is_within_window():
                    try:
                        # Wähle Bewegungsmuster
                        if pattern == "random":
                            dx, dy = self._random_movement(movement_range)
                        elif pattern == "circle":
                            dx, dy = self._circle_movement(pattern_step, movement_range)
                            pattern_step += 1
                        elif pattern == "zigzag":
                            dx, dy = self._zigzag_movement(pattern_step, movement_range)
                            pattern_step += 1
                        else:
                            dx, dy = self._random_movement(movement_range)

                        # Führe Bewegung aus und zurück (Cursor bleibt an Ort)
                        current_pos = get_cursor_position()
                        send_mouse_move_smooth(dx, dy, smooth_steps, 0.003)
                        time.sleep(0.02)
                        send_mouse_move_smooth(-dx, -dy, smooth_steps, 0.003)

                        # Zeige Status
                        elapsed = time.time() - start_time
                        movement_count += 1

                        print(f"✅ #{movement_count}: "
                              f"({current_pos[0]},{current_pos[1]}) "
                              f"Δ({dx:+d},{dy:+d})↔ "
                              f"[{elapsed:.0f}s] {datetime.now().strftime('%H:%M:%S')}",
                              end="\r")

                    except Exception as e:
                        print(f"\n⚠️  Fehler bei Bewegung: {e}")
                        time.sleep(1)
                        continue

                else:
                    # Außerhalb des Zeitfensters
                    elapsed = time.time() - start_time
                    status = self.time_window.get_status_message()

                    next_activation = self.time_window.get_next_activation()
                    if next_activation:
                        wait_seconds = max(1, min(
                            (next_activation - datetime.now()).total_seconds(),
                            interval_seconds
                        ))
                        print(f"{status} [{elapsed:.0f}s]   ", end="\r")
                        time.sleep(wait_seconds)
                    else:
                        time.sleep(interval_seconds)
                    continue

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print(f"\n\n🛑 Mouse Jiggler gestoppt. {movement_count} Bewegungen ausgeführt.")
        except Exception as e:
            print(f"\n❌ Fehler: {e}")
            sys.exit(1)

    def _random_movement(self, range_px: int) -> Tuple[int, int]:
        """Zufällige Bewegung."""
        dx = random.randint(-range_px, range_px)
        dy = random.randint(-range_px, range_px)
        # Vermeide 0,0 Bewegung
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 1])
        return dx, dy

    def _circle_movement(self, step: int, radius: int) -> Tuple[int, int]:
        """Kreisförmige Bewegung."""
        import math
        angle = (step * 0.5) % (2 * math.pi)
        dx = int(radius * math.cos(angle))
        dy = int(radius * math.sin(angle))
        return dx, dy

    def _zigzag_movement(self, step: int, amplitude: int) -> Tuple[int, int]:
        """Zickzack-Bewegung."""
        dx = 2
        dy = amplitude if (step // 3) % 2 == 0 else -amplitude
        return dx, dy


# ============================================================================
# Hilfsfunktionen
# ============================================================================

def test_send_input():
    """Testet die SendInput/CGEvent/cliclick Funktionalität."""
    print("🧪 Teste Maus-API...")

    # Auf macOS: Backend-Erkennung durchführen
    if platform.system() == "Darwin":
        backend = _detect_backend()
        print(f"   Backend: {backend}")

    try:
        pos_before = get_cursor_position()
        print(f"   Position vorher: {pos_before}")

        # Teste relative Bewegung
        send_mouse_move_relative(5, 5)
        time.sleep(0.1)
        pos_after = get_cursor_position()
        print(f"   Position nachher: {pos_after}")

        if pos_before != pos_after:
            print("   ✅ Mausbewegung erfolgreich!")
        else:
            print("   ⚠️  Keine Bewegung erkannt (kann normal sein bei kleinen Werten)")

    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        if platform.system() == "Windows":
            print("   💡 Stelle sicher, dass das Script mit normalen Benutzerrechten läuft")
        elif platform.system() == "Darwin":
            print("   💡 Stelle sicher, dass Terminal/IDE Zugriff auf Eingabehilfen hat")
            print("   Systemeinstellungen → Datenschutz & Sicherheit → Eingabehilfen")


def main():
    """Hauptfunktion mit erweiterten Kommandozeilen-Argumenten."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Mouse Jiggler mit systemnahen APIs (SendInput/CGEvent)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s                                    # Standard: 60 Min., 30s, random ±3px
  %(prog)s -d 0 -i 45                        # Unendlich, alle 45s
  %(prog)s --pattern circle -r 5             # Kreisbewegung, ±5px
  %(prog)s --pattern zigzag                  # Zickzack-Bewegung
  %(prog)s --smooth 6 -i 20                  # Sehr sanft (6 Schritte), alle 20s
  %(prog)s --test                            # API-Test ohne Jiggling
  %(prog)s -d 120 --time-start 08:00 --time-end 18:00 -r 4
        """
    )

    # Grundlegende Parameter
    parser.add_argument("-d", "--duration", type=float, default=0,
                        help="Dauer in Minuten (0 = unendlich)")
    parser.add_argument("-i", "--interval", type=float, default=30,
                        help="Intervall zwischen Bewegungen in Sekunden (Standard: 30)")

    # Bewegungs-Parameter
    parser.add_argument("-r", "--range", type=int, default=3,
                        help="Maximale Bewegung in Pixeln (Standard: 3)")
    parser.add_argument("-s", "--smooth", type=int, default=4,
                        help="Schritte für sanfte Bewegung (Standard: 4)")
    parser.add_argument("-p", "--pattern", type=str, default="random",
                        choices=["random", "circle", "zigzag"],
                        help="Bewegungsmuster (Standard: random)")

    # Zeitfenster
    parser.add_argument("--time-start", type=str, default="09:00",
                        help="Startzeit für aktives Fenster (HH:MM, Standard: 09:00)")
    parser.add_argument("--time-end", type=str, default="17:00",
                        help="Endzeit für aktives Fenster (HH:MM, Standard: 17:00)")
    parser.add_argument("--no-time-window", action="store_true",
                        help="Deaktiviert Zeitfenster (24/7 aktiv)")

    # Spezielle Modi
    parser.add_argument("--test", action="store_true",
                        help="Testet die Maus-API und beendet")
    parser.add_argument("--status", action="store_true",
                        help="Zeigt nur den aktuellen Zeitfenster-Status an")

    args = parser.parse_args()

    # API Test-Modus
    if args.test:
        print(f"🖥️  Plattform: {platform.system()} {platform.machine()}")
        print(f"🐍 Python: {sys.version}")
        test_send_input()
        return

    # Status-Modus
    if args.status:
        time_window = TimeWindow(
            "00:00" if args.no_time_window else args.time_start,
            "23:59" if args.no_time_window else args.time_end
        )
        if args.no_time_window:
            time_window.is_active = False
        print(f"🕐 {time_window.get_status_message()}")
        return

    # Erstelle Zeitfenster
    time_window = TimeWindow(args.time_start, args.time_end)
    if args.no_time_window:
        time_window.is_active = False

    # Starte Jiggler
    jiggler = MouseJiggler(time_window)
    jiggler.jiggle(
        duration_minutes=args.duration if args.duration > 0 else None,
        interval_seconds=args.interval,
        movement_range=args.range,
        smooth_steps=args.smooth,
        pattern=args.pattern
    )


if __name__ == "__main__":
    main()
