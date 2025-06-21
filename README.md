# AnyDeskStatTrackerPY

# 🔍 AnyDesk Favorites Status Tracker

Este projeto em Python permite analisar a seção de favoritos do AnyDesk e detectar **o status de conexão (online/offline)** de cada computador, utilizando uma combinação de:

- 🧠 Leitura inteligente de logs (`ad.trace`)
- 🔍 OCR com Tesseract
- 🖼️ Captura e análise visual de tela (OpenCV + PyAutoGUI)
- ⚙️ Verificação de arquivos de configuração (`user.conf`, `system.conf`)
- 📊 Geração de relatório JSON com os resultados

---

## 📂 Estrutura do Projeto

```
├── status.py # Script principal
├── show_all.png # Imagem do botão "Show All" (para clique automático)
├── pure_black.png # Imagem preta para limpar as thumbnails
├── favorites_status.json # Arquivo de saída com os resultados
├── README.md # Este arquivo


---
```
## 🚀 Como Funciona

1. **Limpa as imagens de miniaturas** (thumbnails) substituindo por fundo preto.
2. **Abre o AnyDesk** e clica no botão "Show All".
3. **Captura a tela** e analisa visualmente os cards com OpenCV.
4. **Faz OCR com Tesseract** para extrair nome/ID.
5. **Cruza os dados com `user.conf`** para validar os favoritos.
6. **Analisa o `ad.trace`** para determinar se cada ID está online/offline.
7. **Gera um relatório JSON** com nome, ID, posição na tela e status.

---

## ✅ Pré-requisitos

- Python 3.8+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado e configurado
- Módulos Python:
  ```bash
  pip install pytesseract pygetwindow pyautogui opencv-python pillow psutil
** Configurações**
Certifique-se de ajustar no status.py os seguintes caminhos:
```
ANYDESK_PATH = r"T:\\AnyDesk\\AnyDesk.exe"
USER_CONF_PATH = r"C:\\Users\\seu_usuario\\AppData\\Roaming\\AnyDesk\\user.conf"
THUMBNAILS_FOLDER = r"C:\\Users\\seu_usuario\\AppData\\Roaming\\AnyDesk\\thumbnails"
SYSTEM_CONF_PATH = r"C:\\Users\\seu_usuario\\AppData\\Roaming\\AnyDesk\\system.conf"
TRACE_LOG_PATH = r"C:\\Users\\seu_usuario\\AppData\\Roaming\\AnyDesk\\ad.trace"
```
Como Usar
Abra o AnyDesk manualmente pelo script ou deixe fechado.

Coloque o script status.py, pure_black.png e show_all.png na mesma pasta.

Execute o script como administrador:
```
python status.py
```
Verifique o resultado no arquivo favorites_status.json.
Exemplo do json:
```
{
  "favorites_count": 2,
  "computers": [
    {
      "name": "MacBook",
      "connection_id": "1417833481",
      "status": "online",
      "position": {
        "x": 100,
        "y": 740,
        "width": 230,
        "height": 160
      },
      "raw_text": "MacBook 141 782 6281"
    }
  ]
}
```
