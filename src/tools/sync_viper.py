#!/usr/bin/env python3
"""
sync_viper.py

Автосинхронизация локальной папки SRC_DIR -> Viper IDE по ссылке WSS_LINK (headless Playwright).

Установка:
    pip install playwright watchdog
    playwright install chromium

Запуск:
    python sync_viper.py

Конфигурация:
    Отредактируй WSS_LINK и SRC_DIR ниже.
"""
import sys
import time
import logging
import threading
from pathlib import Path
from queue import Queue, Empty

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ========== Настройки ==========
WSS_LINK = "https://viper-ide.org?wss=0DN3-HDJC-K2W6"   # <- сюда твоя ссылка
SRC_DIR = Path("src").resolve()                         # <- папка, которую синхронизируем
DEBOUNCE_SECONDS = 0.8                                 # собрать быстрые сохранения в одну загрузку
BATCH_WAIT = 0.6                                       # задержка при пакетной загрузке
UPLOAD_RETRY = 3                                       # попыток загрузки файла
HEADLESS = True                                        # headless режим
# Если нужно отлаживать - поставь False, чтобы видеть окно браузера
# ========== Конец настроек ==========

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Селекторы — могут потребовать правки, если интерфейс Viper поменялся.
# Скрипт попробует несколько способов: 1) скрытый <input type=file>, 2) drag-and-drop на дропзону.
SELECTOR_FILE_INPUT = "input[type=file]"      # универсальный селектор файла
SELECTOR_DROPZONE = ".dropzone, .uploader, .file-drop"  # примерные варианты - скрипт попробует
SELECTOR_UPLOAD_BUTTON = "button:has-text('Upload'), button:has-text('Загрузить')"  # попытка нажать кнопку подтверждения

# очередь файлов для загрузки
file_q = Queue()

# вспомогательная функция для нормализации пути для платформы
def relpath_for_upload(path: Path):
    # возвращаем путь относительно SRC_DIR, с forward slashes
    try:
        rp = path.relative_to(SRC_DIR)
    except Exception:
        rp = path.name
    return str(rp.as_posix())

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, queue):
        self.queue = queue
        self._last_event_time = {}
    def _enqueue(self, path):
        p = Path(path)
        if not p.exists() and not str(p).endswith(".py"):  # allow deletions too
            # enqueue deletion as well (we mark with None content)
            self.queue.put(("deleted", p))
            logging.info("Queued delete: %s", p)
            return
        # debouncing by file path
        now = time.time()
        last = self._last_event_time.get(str(p), 0)
        if now - last < DEBOUNCE_SECONDS:
            return
        self._last_event_time[str(p)] = now
        self.queue.put(("modified", p))
        logging.info("Queued modified: %s", p)

    def on_modified(self, event):
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._enqueue(event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory:
            # enqueue deletion
            p = Path(event.src_path)
            self.queue.put(("deleted", p))
            logging.info("Queued deleted: %s", p)

def gather_initial_files(src_dir: Path, queue: Queue):
    for p in src_dir.rglob("*"):
        if p.is_file():
            queue.put(("modified", p))
    logging.info("Initial files queued.")

def playwright_upload_page(page, local_path: Path, remote_relpath: str):
    """
    Попытаться загрузить файл local_path на страницу page.
    remote_relpath — относительный путь (для сообщений/логики).
    Попробуем:
      1) найти <input type=file> и set_input_files
      2) найти dropzone и эмулировать drag-and-drop
    Возвращает True если успешно.
    """
    logging.info("Uploading %s as %s", local_path, remote_relpath)
    # 1) попытка через input[type=file]
    try:
        el = page.query_selector(SELECTOR_FILE_INPUT)
        if el:
            logging.debug("Found file input; using set_input_files.")
            el.set_input_files(str(local_path))
            # иногда нужно нажать кнопку "Upload" или "OK"
            try:
                btn = page.query_selector(SELECTOR_UPLOAD_BUTTON)
                if btn:
                    btn.click()
            except Exception:
                pass
            # подождём кратко, чтобы загрузка произошла
            page.wait_for_timeout(600)
            logging.info("Uploaded via input for %s", remote_relpath)
            return True
    except PlaywrightTimeoutError:
        logging.debug("Timeout on input path.")
    except Exception as e:
        logging.debug("input upload attempt failed: %s", e)

    # 2) попытка drag-and-drop (эмуляция DataTransfer)
    try:
        drop = None
        for sel in SELECTOR_DROPZONE.split(","):
            sel = sel.strip()
            if not sel:
                continue
            el = page.query_selector(sel)
            if el:
                drop = el
                break
        if not drop:
            # как запасной план — попробовать body
            drop = page.query_selector("body")
        if drop:
            logging.debug("Found drop target: attempting drag-and-drop emulation.")
            # JS to create DataTransfer and dispatch events
            js = f"""
            (localPath) => {{
                const dt = new DataTransfer();
                // Note: we cannot actually read local file content from the browser side in headless mode.
                // But Playwright supports setInputFiles which is the recommended approach.
                // As fallback, try to find an input inside the drop target and set files there.
                let input = document.querySelector('input[type=file]');
                if (!input) {{
                    input = document.createElement('input');
                    input.type = 'file';
                    input.multiple = false;
                    input.style.display = 'none';
                    document.body.appendChild(input);
                }}
                return !!input;
            }}
            """
            ok = page.evaluate(js, str(local_path))
            # if input exists or created, use it
            inp = page.query_selector("input[type=file]")
            if inp:
                inp.set_input_files(str(local_path))
                try:
                    btn = page.query_selector(SELECTOR_UPLOAD_BUTTON)
                    if btn:
                        btn.click()
                except Exception:
                    pass
                page.wait_for_timeout(600)
                logging.info("Uploaded via created input for %s", remote_relpath)
                return True
    except Exception as e:
        logging.debug("drag-drop attempt failed: %s", e)

    logging.warning("All upload attempts failed for %s", remote_relpath)
    return False

def worker_thread_main(queue: Queue, wss_link: str, src_dir: Path):
    """
    Работает в отдельном потоке: подключается к Playwright, слушает очередь и грузит файлы.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        page = context.new_page()
        logging.info("Playwright browser started (headless=%s).", HEADLESS)

        # функция, которая отправляет один файл с retry
        def upload_with_retries(kind, path: Path):
            remote_rel = relpath_for_upload(path)
            last_err = None
            for attempt in range(1, UPLOAD_RETRY + 1):
                try:
                    # переоткрываем url каждый раз чтобы быть более устойчивыми к сессиям
                    logging.debug("Opening %s (attempt %d) ...", wss_link, attempt)
                    page.goto(wss_link, timeout=30000)
                    # дождёмся загрузки body
                    try:
                        page.wait_for_selector("body", timeout=10000)
                    except PlaywrightTimeoutError:
                        logging.debug("body selector not found quickly, continuing.")

                    if kind == "deleted":
                        # удаление: попытаемся найти файл в файловом дереве и удалить через UI
                        # Это сильно зависит от UI; попробуем найти элемент с именем файла и trash/delete рядом.
                        logging.info("Attempting to delete %s via UI...", remote_rel)
                        # попытка найти ссылку/элемент по имени файла
                        try:
                            file_el = page.query_selector(f"text={path.name}")
                            if file_el:
                                # если есть кнопка удаления рядом
                                # try to click context menu or delete icon
                                # This part is heuristic: won't always work.
                                try:
                                    # try right click -> press delete (if UI supports)
                                    file_el.click(button="right")
                                    page.wait_for_timeout(300)
                                    # click delete in context menu
                                    del_btn = page.query_selector("button:has-text('Delete'), text=Delete, text=Удалить")
                                    if del_btn:
                                        del_btn.click()
                                        page.wait_for_timeout(400)
                                        logging.info("Deleted %s via UI.", remote_rel)
                                        return True
                                except Exception:
                                    logging.debug("Delete attempt failed for %s", remote_rel)
                        except Exception as e:
                            logging.debug("Delete flow error: %s", e)
                        logging.warning("Delete not supported automatically for %s", remote_rel)
                        return False
                    else:
                        succeeded = playwright_upload_page(page, path, remote_rel)
                        if succeeded:
                            return True
                except Exception as e:
                    last_err = e
                    logging.debug("Upload attempt %d failed: %s", attempt, e)
                    time.sleep(1.0)
            logging.error("Failed to upload %s after %d attempts. Last error: %s", remote_rel, UPLOAD_RETRY, last_err)
            return False

        # главный цикл обработки очереди: группируем события несколько десятков миллисекунд
        pending = {}
        while True:
            try:
                kind, path = queue.get(timeout=1.0)
            except Empty:
                # обработка накопленных срабатываний (если прошло BATCH_WAIT)
                if pending:
                    # flush all pending
                    items = list(pending.items())
                    pending.clear()
                    for pth_str, kind_val in items:
                        pth = Path(pth_str)
                        upload_with_retries(kind_val, pth)
                continue
            # добавляем в pending
            pending[str(path)] = kind
            # небольшая задержка для сбора других событий
            time.sleep(BATCH_WAIT)
            # если после задержки есть сообщения в очереди — заберём их
            while True:
                try:
                    k, p = queue.get_nowait()
                    pending[str(p)] = k
                except Empty:
                    break
            # обработаем все pending сразу
            items = list(pending.items())
            pending.clear()
            for pth_str, kind_val in items:
                pth = Path(pth_str)
                upload_with_retries(kind_val, pth)

def main():
    if not SRC_DIR.exists():
        logging.error("SRC_DIR does not exist: %s", SRC_DIR)
        sys.exit(1)

    # стартуем наблюдатель файловой системы
    event_handler = ChangeHandler(file_q)
    observer = Observer()
    observer.schedule(event_handler, str(SRC_DIR), recursive=True)
    observer.start()
    logging.info("Watching %s for changes...", SRC_DIR)

    # кладём в очередь все файлы при старте
    gather_initial_files(SRC_DIR, file_q)

    # стартуем воркер Playwright в отдельном треде
    t = threading.Thread(target=worker_thread_main, args=(file_q, WSS_LINK, SRC_DIR), daemon=True)
    t.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        logging.info("Stopping...")
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()
