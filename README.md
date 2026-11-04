# agent_BA_DBA

Dự án triển khai và quản lý hai AI Agent: **Business Analyst (BA)** và **Database Administrator (DBA)** thuộc hệ thống phối hợp đa tác tử (Multi-Agent System), tuân thủ kiến trúc **Shared-Nothing** và giao tiếp 100% qua chuẩn **HTTP REST API v1** với **Bearer Token Authentication**.

---

## 📁 Cấu trúc thư mục

```text
agent_BA_DBA/
│
├── agents/
│   ├── ba/                      # Mã nguồn, API FastAPI và công cụ phân tích của BA Agent (ba-01)
│   └── dba/                     # Mã nguồn, API FastAPI và công cụ sinh Schema của DBA Agent (dba-01)
│
├── scripts/
│   ├── start_agents.py          # Khởi động đồng thời cả 2 Agent với healthcheck tự động
│   ├── test_connection.py       # Bộ kiểm thử tích hợp E2E toàn bộ luồng BA -> DBA
│   └── configure_lan.py         # Tiện ích tự động hóa cấu hình kết nối mạng LAN / VPN
│
├── config/
│   └── agents.yaml              # Cấu hình định tuyến cổng, endpoints, token của các Agent
│
├── docs/
│   ├── ARCHITECTURE.md          # Tài liệu kiến trúc Multi-Agent & sơ đồ tuần tự chi tiết
│   └── CONNECTIVITY_GUIDE.md    # Cẩm nang kết nối mạng đa máy (LAN & Tailscale VPN)
│
├── README.md                    # Hướng dẫn dự án
│
└── .gitignore                   # Cấu hình bỏ qua của Git (.env, cache, logs, database)
```

---

## 🚀 Hướng dẫn nhanh

### 1. Phân bổ Agent và Cổng
- **BA Agent (`ba-01`)**: Port `8003` (FastAPI)
- **DBA Agent (`dba-01`)**: Port `8004` (FastAPI)

### 2. Khởi chạy hệ thống Multi-Agent
Khởi động đồng thời cả hai Agent với một lệnh duy nhất:

```bash
python scripts/start_agents.py
```

### 3. Chạy kiểm thử tích hợp E2E (BA -> DBA)
Chạy bộ test kiểm tra kết nối, xác thực token, xuất SRS và sinh Database Schema:

```bash
python scripts/test_connection.py
```

### 4. Thiết lập mạng nội bộ LAN / VPN
Chi tiết cấu hình xem tại [ARCHITECTURE.md](file:///D:/agent_BA_DBA/docs/ARCHITECTURE.md) và [CONNECTIVITY_GUIDE.md](file:///D:/agent_BA_DBA/CONNECTIVITY_GUIDE.md).
