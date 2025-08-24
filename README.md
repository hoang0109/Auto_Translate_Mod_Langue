# Factorio Mod Translator

## Giới thiệu
Factorio Mod Translator là một công cụ giúp bạn dịch các mod của trò chơi Factorio sang ngôn ngữ mong muốn bằng cách sử dụng DeepL API. Công cụ này hỗ trợ giao diện người dùng trực quan, cho phép bạn chọn mod, nhập mã API, và tùy chỉnh các thiết lập dịch.

## Tính năng chính
- Dịch các mod Factorio sang nhiều ngôn ngữ khác nhau.
- Hỗ trợ DeepL API (trả phí và miễn phí).
- Lưu và tải lại các thiết lập (ngôn ngữ, mã API, endpoint).
- Giao diện người dùng dễ sử dụng với các nút chức năng rõ ràng.

## Yêu cầu hệ thống
- Python 3.10 trở lên.
- Các thư viện Python:
  - `tkinter`
  - `requests`
  - `cryptography`
  - `configparser`

## Cách cài đặt
1. Tải xuống mã nguồn từ repository.
2. Cài đặt các thư viện cần thiết bằng lệnh:
   ```bash
   pip install requests cryptography
   ```
3. Chạy chương trình bằng lệnh:
   ```bash
   python mod_translator_gui.py
   ```

## Hướng dẫn sử dụng
1. **Chọn mod cần dịch**:
   - Nhấn nút "Add Files" để chọn các file mod (.zip).
   - Nếu muốn xóa file đã chọn, nhấn "Remove Selected".

2. **Nhập mã DeepL API**:
   - Nhập mã API vào ô "DeepL API Key".
   - Nhấn nút "Test DeepL API" để kiểm tra tính hợp lệ của mã API.

3. **Chọn ngôn ngữ đích**:
   - Chọn ngôn ngữ mong muốn từ danh sách "Target Language".

4. **Chọn endpoint DeepL**:
   - Chọn giữa "api.deepl.com" (trả phí) và "api-free.deepl.com" (miễn phí).

5. **Bắt đầu dịch**:
   - Nhấn nút "Start Translation" để bắt đầu quá trình dịch.
   - File mod đã dịch sẽ được lưu trong thư mục `output`.

## Lưu ý
- Đảm bảo mã API của bạn hợp lệ và endpoint được chọn đúng.
- Các thiết lập sẽ được tự động lưu khi bạn thoát chương trình.

## Liên hệ
Nếu bạn gặp vấn đề hoặc có câu hỏi, vui lòng liên hệ qua email: `hoang0109@example.com`.
