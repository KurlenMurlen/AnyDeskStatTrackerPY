import os
import json
import time
import socket
import psutil
import cv2
import numpy as np
from PIL import Image, ImageGrab
import pygetwindow as gw
import pyautogui
import pytesseract
import subprocess

# === CONFIGURAÇÕES ===
ANYDESK_PATH = r"T:\\AnyDesk\\AnyDesk.exe"
JSON_OUTPUT = "favorites_status.json"
USER_CONF_PATH = r"C:\\Users\\tarso\\AppData\\Roaming\\AnyDesk\\user.conf"
THUMBNAILS_FOLDER = r"C:\\Users\\tarso\\AppData\\Roaming\\AnyDesk\\thumbnails"
PURE_BLACK_PATH = "pure_black.png"
SYSTEM_CONF_PATH = r"C:\\Users\\tarso\\AppData\\Roaming\\AnyDesk\\system.conf"
TRACE_LOG_PATH = r"C:\\Users\\tarso\\AppData\\Roaming\\AnyDesk\\ad.trace"
pytesseract.pytesseract.tesseract_cmd = r'T:\\Tesseract\\tesseract.exe'

# === LIMPEZA ===
def clean_thumbnails():
    if os.path.exists(PURE_BLACK_PATH):
        for filename in os.listdir(THUMBNAILS_FOLDER):
            file_path = os.path.join(THUMBNAILS_FOLDER, filename)
            if os.path.isfile(file_path):
                try:
                    os.replace(PURE_BLACK_PATH, file_path)
                except Exception as e:
                    print(f"Erro ao substituir {file_path}: {e}")

# === FAVORITOS ===
def extract_favorites_from_userconf(path=USER_CONF_PATH):
    favorites = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("ad.roster.favorites="):
                raw = line.split("=")[1]
                items = raw.strip().split(",")
                for i in range(0, len(items), 4):
                    if i + 3 < len(items):
                        favorites.append({
                            "id": items[i],
                            "name": items[i+2]
                        })
    return favorites

# === INTERFACE VISUAL ===
def open_anydesk():
    subprocess.Popen([ANYDESK_PATH])
    time.sleep(5)
    for _ in range(10):
        win = next((w for w in gw.getWindowsWithTitle('AnyDesk') if w.visible), None)
        if win:
            win.maximize()
            time.sleep(1)
            return win
        time.sleep(1)
    raise Exception("Janela do AnyDesk não encontrada")

def click_show_all():
    try:
        x, y = pyautogui.locateCenterOnScreen("show_all.png", confidence=0.2)
        pyautogui.click(x, y)
        time.sleep(1)
    except:
        print("Botão 'Show All' não encontrado")

# === CAPTURA VISUAL ===
def capture_window(win):
    return ImageGrab.grab(bbox=(win.left, win.top, win.left + win.width, win.top + win.height)), win.left, win.top

def find_cards(image_np):
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cards = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if 150 < w < 400 and 120 < h < 300 and y > 300:
            cards.append((x, y, w, h))
    return cards

def check_individual_statuses_from_trace(favorites, trace_path=TRACE_LOG_PATH):
    try:
        with open(trace_path, "r", encoding="utf-8", errors="ignore") as f:
            trace = f.read().lower()

        status_map = {}
        for fav in favorites:
            fid = fav["id"]
            if fid in trace:
                if f"session started" in trace and fid in trace:
                    status_map[fid] = "online"
                elif f"relayconnection established" in trace and fid in trace:
                    status_map[fid] = "online"
                elif f"session closed" in trace and fid in trace:
                    status_map[fid] = "offline"
                elif f"relay connection failed" in trace and fid in trace:
                    status_map[fid] = "offline"
                else:
                    status_map[fid] = "unknown"
            else:
                status_map[fid] = "unknown"
        return status_map
    except Exception:
        return {fav["id"]: "unknown" for fav in favorites}

def extract_text(card_img):
    pil_img = Image.fromarray(card_img)
    text = pytesseract.image_to_string(pil_img).strip()
    return ' '.join(text.replace('\n', ' ').split())

def match_favorite_id(card_text, favorites):
    for fav in favorites:
        if fav["id"] in card_text or fav["name"].lower() in card_text.lower():
            return fav
    return {"id": "Unknown", "name": "Unknown"}

# === STATUS: MÚLTIPLAS MÉTRICAS ===
def check_trace_log_status(path=TRACE_LOG_PATH):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
            if "relayconnection established" in content and "session started" in content:
                return "online"
            elif "relay connection failed" in content or "session closed" in content:
                return "offline"
        return "unknown"
    except Exception:
        return "unknown"

def check_system_conf_status(path=SYSTEM_CONF_PATH):
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "ad.anynet.relay.state=2" in line:
                    return "online"
        return "offline"
    except Exception:
        return "unknown"

def check_anydesk_process_connection():
    try:
        for p in psutil.process_iter(['pid', 'name']):
            if "anydesk" in p.info['name'].lower():
                conns = p.connections(kind='inet')
                for c in conns:
                    if c.status == psutil.CONN_ESTABLISHED:
                        return "online"
        return "offline"
    except Exception:
        return "unknown"

def ping_anydesk_relay(path=SYSTEM_CONF_PATH):
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("ad.anynet.last_relay="):
                    host = line.split("=")[1].split(":")[0]
                    try:
                        socket.create_connection((host, 443), timeout=2)
                        return "online"
                    except:
                        return "offline"
        return "unknown"
    except Exception:
        return "unknown"

def determine_anydesk_status():
    metrics = {
        "log_trace": check_trace_log_status(),
        "process_conn": check_anydesk_process_connection(),
        "ping_relay": ping_anydesk_relay(),
        "system_conf": check_system_conf_status()
    }

    positives = [k for k, v in metrics.items() if v == "online"]
    negatives = [k for k, v in metrics.items() if v == "offline"]

    print("🧠 Diagnóstico:")
    for k, v in metrics.items():
        print(f" - {k}: {v}")

    if positives:
        return "online"
    elif negatives and not positives:
        return "offline"
    else:
        return "unknown"

# === ANÁLISE FINAL ===
def analyze_favorites(win, favorites):
    individual_statuses = check_individual_statuses_from_trace(favorites)
    screenshot, offset_x, offset_y = capture_window(win)
    image_np = np.array(screenshot)
    card_regions = find_cards(image_np)

    results = []
    seen_ids = set()
    anydesk_status = determine_anydesk_status()

    for x, y, w, h in card_regions:
        card_img = image_np[y:y+h, x:x+w]
        text = extract_text(card_img)
        fav = match_favorite_id(text, favorites)
        identifier = (fav["id"], fav["name"])

        if identifier not in seen_ids:
            seen_ids.add(identifier)
            results.append({
                "name": fav["name"],
                "connection_id": fav["id"],
                "status": individual_statuses.get(fav["id"], "unknown"),
                "position": {
                    "x": int(x + offset_x),
                    "y": int(y + offset_y),
                    "width": int(w),
                    "height": int(h)
                },
                "raw_text": text
            })

    return {
        "favorites_count": len(results),
        "computers": results
    }

def save_results(data):
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Resultados salvos em {JSON_OUTPUT}")

# === EXECUÇÃO PRINCIPAL ===
def main():
    try:
        print("Limpando thumbnails...")
        clean_thumbnails()

        print("Extraindo favoritos...")
        favorites = extract_favorites_from_userconf()

        print("Abrindo AnyDesk...")
        win = open_anydesk()
        click_show_all()

        print("Analisando cards e status...")
        data = analyze_favorites(win, favorites)

        save_results(data)
        print("✅ Concluído com sucesso!")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
