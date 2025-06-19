# Developer Documentation

本文件針對本專案的開發者，說明架構、開發環境、啟動流程、目錄結構、常見問題與貢獻方式。

---

## 系統架構

本系統採用微服務架構，主要元件如下：
- **Web**：Streamlit 前端，提供知識庫操作介面。
- **Core**：FastAPI，負責向量化、檢索、Qdrant 操作。
- **Backend**：FastAPI，負責業務邏輯、用戶管理、知識庫管理。
- **Qdrant**：向量資料庫。
- **MongoDB**：儲存知識庫與文件中繼資料。
- **MinIO**：物件儲存，存放原始文件。

架構圖請參考 `/docs/assets/arch.png`。

---

## 目錄結構說明

- `src/`：主要程式碼與部署腳本
  - `core/`：向量化與檢索 API
  - `backend/`：業務邏輯 API
  - `web/`：Streamlit 前端
  - `docker-compose.yaml`：多服務協同啟動
  - `install_everything.sh`、`setup.sh`：安裝與初始化腳本
- `docs/`：技術文件、API 文件、架構圖
- `test_file/`：測試用 PDF 文件

---

## 開發環境安裝

1. **安裝 Docker 與 Docker Compose**
   - 建議執行 `src/install_everything.sh`，自動安裝所有依賴。
   - macOS 用戶可手動安裝 Docker Desktop。

2. **建立環境變數檔**

   ```bash
   cp src/.env-template src/.env
   # 並根據需求修改內容
   ```

3. **建立資料目錄**

   ```bash
   sudo mkdir -p /data/qdrant-data /data/minio-data /data/mongo-data
   sudo chmod -R 777 /data
   ```

4. **啟動服務**

   ```bash
   cd src
   bash setup.sh
   # 或手動執行 docker-compose up -d --build
   ```

5. **前端入口**
   - 預設網址：<http://localhost:4321>

---

## 主要元件說明

- **Web** (`src/web/`)
  - Streamlit 實作，支援登入/註冊、知識庫管理、文件上傳與查詢。
- **Core** (`src/core/`)
  - FastAPI，負責文件向量化、Qdrant 檢索、混合查詢。
- **Backend** (`src/backend/`)
  - FastAPI，負責用戶管理、知識庫 CRUD、MinIO/MongoDB 操作。
- **Qdrant**
  - 向量資料庫，支援高效向量檢索與混合查詢。
- **MongoDB**
  - 儲存知識庫、文件中繼資料。
- **MinIO**
  - 物件儲存，存放原始文件。

---

## API 文件

請參考 `/docs/api.md`，內含完整 API 規格與範例。

---

## 常見問題

- 啟動失敗請檢查 Docker 是否安裝、資料夾權限、環境變數是否正確。
- 若需重設環境，請刪除 `/data` 目錄後重新執行 `setup.sh`。

---

## 貢獻方式

1. Fork 本專案，建立新分支。
2. 開發與測試。
3. 提交 Pull Request，說明修改內容。

---

如有問題請聯絡專案維護者。
