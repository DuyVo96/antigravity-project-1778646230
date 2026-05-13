# 📚 Hướng Dẫn Vận Hành Dựng Video (Dự án Slide)

Chào mừng bạn đến với nhà máy sản xuất Content tự động. Thay vì thao tác thủ công phức tạp, hệ thống này đã được tinh gọn đến mức tối giản nhất.

---

## 🛠 Bước 1: Cho Nguyên Liệu Vào Khuôn

Bạn chỉ cần để mắt tới đúng **2 file duy nhất** để cung cấp nguyên liệu:

### 1. File `links.txt` (Rổ chứa nền)
- Mở file lên và dán các đường link ảnh lấy từ Pinterest vào. 
- **Quy tắc:** Mỗi dòng 1 link. 
- **Công nghệ tự động:** Bạn không cần bận tâm tìm link nét. Dù bạn dán link lỗi hay link thu nhỏ `736x`, hệ thống sẽ tự động bắt ép Pinterest trả về file 4K gốc (`/originals/`).

### 2. File `content.txt` (Kịch bản thoại)
- Viết tất cả các chữ bạn muốn vắt ngang qua màn hình.
- **Quy tắc:** Cứ hết một cảnh / chuyển sang bức ảnh tiếp theo thì bạn nhấn **ENTER 2 lần** (Cách nhau bằng 1 dòng trống).
- **Công nghệ tự động:** Chữ sẽ tự động được thu thập, giãn dòng, bẻ dòng nếu quá dài, canh ngay chính giữa bức ảnh, và dập font **Montserrat** đổ bóng Dạ quang Neon siêu ngầu.

---

## 🚀 Bước 2: Bấm Nút Xuất Xưởng

Sau khi đã lưu 2 file trên, mở Terminal (hoặc cửa sổ dòng lệnh) lên và chỉ cần gõ đúng 1 dòng:

```bash
sh run.sh
```

**Hệ thống sẽ tự động chạy liên hoàn:**
1. Ráp kịch bản.
2. Tải ảnh nét.
3. Vẽ Canvas tự động.

👉 Vào thư mục `./output/gym/` để tận hưởng thành quả ngay sau khi lệnh chạy chớp nhoáng (chưa tới 3 giây!).

---

## ⏰ Bước 3: Lên Lịch Đăng TikTok (Automation 90%)

Sau khi đã ngâm cứu xong đống ảnh cực đẹp. Bạn muốn lên lịch đẩy mớ ảnh đó thẳng vào Hộp Nháp điện thoại để qua mặt thuật toán Bot (Chặn Spam)?

1. Vào `schedule.json`, cắm cờ gạch đầu dòng tên các slide (`slide_01.png...`), điền Cấp-caption mô tả video và đặt Lịch hẹn giờ quốc tế (UTC) lên sóng.
2. Mở Terminal chốt lệnh:

```bash
TIKTOK_INTEGRATION_ID=cmo2cyjfd0277qk0y9nsrmw37 node batch-schedule.js
```

*(Chi tiết về thuật toán lách Bot Postiz đã được giải ảo cụ thể trong file `GEMINI.md`)*.
