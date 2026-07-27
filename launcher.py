"""
Lanzador offline — Registro Quirúrgico Coloproctología (HUMS)

Arranca el servidor FastAPI en localhost y abre Chrome (o Edge) en modo
aplicación, sin barra de direcciones. La base de datos se guarda en la misma
carpeta que el ejecutable.

Pensado para uso desde una carpeta compartida: sólo permite una instancia
simultánea en toda la red. SQLite sobre SMB no garantiza los bloqueos de
fichero, así que el acceso concurrente se impide explícitamente en vez de
arriesgar una corrupción silenciosa de los datos.
"""

import os
import sys
import time
import socket
import getpass
import platform
import tempfile
import threading
import subprocess
from datetime import datetime

APP_NAME = "Registro Quirúrgico Coloproctología"
IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    import ctypes
    import msvcrt
else:
    import fcntl


# ── Rutas ────────────────────────────────────────────────────────────────────
def app_dir() -> str:
    """Carpeta del .exe cuando está empaquetado; del .py en desarrollo."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = app_dir()
DB_FILE = os.path.join(BASE_DIR, "coloproctologia.db")
LOCK_FILE = os.path.join(BASE_DIR, ".coloproctologia.lock")
OWNER_FILE = os.path.join(BASE_DIR, ".coloproctologia.owner")
LOG_FILE = os.path.join(BASE_DIR, "registro_app.log")


# ── Salida (en modo --noconsole sys.stdout es None) ──────────────────────────
def setup_output() -> None:
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        stream = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    except OSError:
        stream = open(os.devnull, "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream


def log(msg: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        print(f"[{stamp}] {msg}", flush=True)
    except Exception:
        pass


def hide_file(path: str) -> None:
    """
    Marca el fichero como oculto para que no despiste en la carpeta compartida.

    Ojo: en Windows, abrir un fichero oculto con modo "w" (CREATE_ALWAYS) da
    error de acceso. Quien escriba sobre un fichero oculto debe borrarlo antes.
    """
    if not IS_WINDOWS:
        return
    FILE_ATTRIBUTE_HIDDEN = 0x02
    try:
        ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN)
    except Exception:  # noqa: BLE001 - es cosmético, nunca debe impedir el arranque
        pass


def message_box(text: str, title: str = APP_NAME, error: bool = False) -> None:
    """Aviso al usuario. En modo ventana no hay consola donde imprimir."""
    if IS_WINDOWS:
        icon = 0x10 if error else 0x40  # MB_ICONERROR / MB_ICONINFORMATION
        ctypes.windll.user32.MessageBoxW(None, text, title, icon | 0x40000)
    else:
        log(f"{title}: {text}")


# ── Bloqueo de instancia única (funciona sobre carpeta de red) ───────────────
def _try_lock(fh) -> None:
    """Lanza OSError si otro proceso ya tiene el bloqueo."""
    fh.seek(0)
    if IS_WINDOWS:
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(fh) -> None:
    try:
        fh.seek(0)
        if IS_WINDOWS:
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


class SingleInstanceLock:
    """
    Bloqueo por rango de bytes sobre un fichero centinela. El sistema operativo
    lo libera solo si el proceso muere, así que un cierre inesperado no deja la
    aplicación bloqueada de forma permanente.
    """

    def __init__(self) -> None:
        self.fh = None

    def acquire(self) -> tuple[bool, str]:
        try:
            # Modo "a+" (OPEN_ALWAYS) sí funciona sobre ficheros ocultos
            self.fh = open(LOCK_FILE, "a+")
            # El fichero debe tener al menos 1 byte para poder bloquearlo
            self.fh.seek(0, os.SEEK_END)
            if self.fh.tell() == 0:
                self.fh.write("x")
                self.fh.flush()
            hide_file(LOCK_FILE)
        except OSError as e:
            return False, f"No se pudo acceder a la carpeta de la aplicación.\n\n{e}"

        try:
            _try_lock(self.fh)
        except OSError:
            holder = self._read_owner()
            try:
                self.fh.close()
            finally:
                self.fh = None
            return False, holder

        self._write_owner()
        return True, ""

    def release(self) -> None:
        if self.fh is None:
            return
        _unlock(self.fh)
        try:
            self.fh.close()
        except OSError:
            pass
        self.fh = None
        try:
            os.remove(OWNER_FILE)
        except OSError:
            pass

    @staticmethod
    def _write_owner() -> None:
        try:
            # Borrar primero: sobrescribir un fichero oculto con "w" falla en
            # Windows si no se repite el atributo al crearlo
            if os.path.exists(OWNER_FILE):
                os.remove(OWNER_FILE)
            with open(OWNER_FILE, "w", encoding="utf-8") as f:
                f.write(f"{getpass.getuser()}\n")
                f.write(f"{platform.node()}\n")
                f.write(datetime.now().strftime("%d/%m/%Y %H:%M"))
            hide_file(OWNER_FILE)
        except OSError:
            pass

    @staticmethod
    def _read_owner() -> str:
        try:
            with open(OWNER_FILE, encoding="utf-8") as f:
                parts = f.read().splitlines()
            user = parts[0] if len(parts) > 0 else "?"
            host = parts[1] if len(parts) > 1 else "?"
            since = parts[2] if len(parts) > 2 else "?"
            return f"Usuario: {user}\nEquipo: {host}\nDesde: {since}"
        except OSError:
            return "No se ha podido identificar quién la tiene abierta."


# ── Navegador ────────────────────────────────────────────────────────────────
def _from_registry(exe: str):
    try:
        import winreg
    except ImportError:
        return None
    key = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}"
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(root, key) as k:
                path, _ = winreg.QueryValueEx(k, None)
                if path and os.path.isfile(path):
                    return path
        except OSError:
            continue
    return None


def find_browser():
    """Devuelve (ruta, nombre). Chrome primero, Edge como alternativa."""
    if not IS_WINDOWS:
        for path, name in [
            ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "Chrome"),
            ("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", "Edge"),
            ("/usr/bin/google-chrome", "Chrome"),
            ("/usr/bin/microsoft-edge", "Edge"),
        ]:
            if os.path.isfile(path):
                return path, name
        return None, None

    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local = os.environ.get("LOCALAPPDATA", "")

    candidates = []
    for base in (pf, pf86, local):
        if base:
            candidates.append(
                (os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"), "Chrome")
            )
    for base in (pf86, pf):
        if base:
            candidates.append(
                (os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"), "Edge")
            )

    for path, name in candidates:
        if os.path.isfile(path):
            return path, name

    for exe, name in (("chrome.exe", "Chrome"), ("msedge.exe", "Edge")):
        path = _from_registry(exe)
        if path:
            return path, name

    return None, None


def launch_browser(browser: str, url: str):
    """
    Perfil dedicado en disco local: fuerza un proceso nuevo (así podemos
    esperar a que se cierre) y evita escribir el perfil en la unidad de red.
    """
    profile = os.path.join(tempfile.gettempdir(), "coloproctologia_perfil")
    args = [
        browser,
        f"--app={url}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-mode",
        "--window-size=1440,900",
    ]
    return subprocess.Popen(args)


# ── Servidor ─────────────────────────────────────────────────────────────────
def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_until_up(port: int, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.2)
    return False


def start_server(port: int):
    # database.py lee DB_PATH al importarse: hay que fijarlo ANTES
    os.environ["DB_PATH"] = DB_FILE

    import uvicorn
    from main import app

    # log_config=None: el formateador de uvicorn llama a isatty() sobre stdout,
    # que en un .exe sin consola no existe y hace petar el arranque
    config = uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="warning", log_config=None
    )
    server = uvicorn.Server(config)
    # Los manejadores de señales sólo funcionan en el hilo principal
    server.install_signal_handlers = lambda: None

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return server, thread


# ── Principal ────────────────────────────────────────────────────────────────
def main() -> int:
    setup_output()
    log(f"Iniciando desde {BASE_DIR}")

    lock = SingleInstanceLock()
    acquired, holder = lock.acquire()
    if not acquired:
        message_box(
            "La aplicación ya está abierta por otro usuario.\n\n"
            f"{holder}\n\n"
            "Sólo una persona puede usarla a la vez para no dañar la base de "
            "datos. Inténtalo de nuevo cuando la haya cerrado.",
            error=True,
        )
        log("Bloqueado: ya hay otra instancia activa")
        return 1

    browser_proc = None
    server = None
    try:
        port = free_port()
        log(f"Puerto {port} · BD {DB_FILE}")
        server, _ = start_server(port)

        if not wait_until_up(port):
            message_box(
                "El servidor interno no ha arrancado.\n\n"
                f"Revisa el archivo de registro:\n{LOG_FILE}",
                error=True,
            )
            return 1

        url = f"http://127.0.0.1:{port}"
        browser, name = find_browser()

        if browser:
            log(f"Abriendo en {name}")
            browser_proc = launch_browser(browser, url)
            started = time.time()
            browser_proc.wait()

            # Si el navegador delegó en una instancia previa y salió al
            # instante, mantenemos el servidor vivo con un diálogo modal.
            if time.time() - started < 3:
                log("El navegador salió de inmediato; esperando confirmación")
                message_box(
                    "La aplicación se ha abierto en el navegador.\n\n"
                    "Pulsa Aceptar aquí cuando termines para cerrarla "
                    "correctamente y liberarla para otros usuarios."
                )
        else:
            import webbrowser

            log("Chrome/Edge no encontrados; usando el navegador por defecto")
            webbrowser.open(url)
            message_box(
                "No se ha encontrado Chrome ni Edge, así que se ha abierto en "
                "el navegador predeterminado.\n\n"
                "Pulsa Aceptar aquí cuando termines para cerrar la aplicación."
            )

        return 0

    except Exception as e:  # noqa: BLE001 - último recurso, hay que informar
        log(f"ERROR: {e!r}")
        message_box(f"Error inesperado:\n\n{e}\n\nRegistro: {LOG_FILE}", error=True)
        return 1

    finally:
        if browser_proc and browser_proc.poll() is None:
            try:
                browser_proc.terminate()
            except OSError:
                pass
        if server is not None:
            server.should_exit = True
            time.sleep(1.0)
        lock.release()
        log("Cerrado")


if __name__ == "__main__":
    sys.exit(main())
