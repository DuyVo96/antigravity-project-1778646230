# 🚀 Sổ Tay Tự Động Hoá TikTok: Dự án Slide - Hệ thống Postiz Hybrid

Tài liệu này ghi chép lại quy trình lõi (SOP) và các kinh nghiệm sống còn trong quá trình tự động hóa đăng Slideshow lên TikTok thông qua CLI của Postiz mà chúng ta đã rèn dũa được.

---

## 🛠 1. Bản Đồ Dây Chuyền Sản Xuất (Pipeline)

Hệ thống hoạt động theo mô hình **Tự động 90% (Máy làm) - 10% Bấm chốt (Người đăng)**.

1. **Sản xuất (Mẫu ảnh gốc):** Kịch bản chữ to nhỏ được nhập vào `slides-config.json`. Trình `generate-slides.js` sẽ tự động dập khuôn và xuất file hoàn thiện ra thư mục `./output/`.
2. **Kịch bản đăng tải:** Chỉnh định mức chữ (`caption`), ngày giờ báo động (`scheduledAt`) vào file thư ký `schedule.json`.
3. **Tự động Giao Liên (`batch-schedule.js`):** Script này làm nhiệm vụ:
   - Tự nhấc ảnh ném lên máy chủ Postiz CDN để lấy bộ link online.
   - Gói ghém tài liệu, cài đặt bùa chướng chống shadow-ban, và lập lệnh đẩy thẳng vào `QUEUE`.
4. **Cú Kết Liễu Human-Touch:** Đến đúng giờ (`HH:MM:ss Z`), Postiz nhồi mớ tài liệu đó vào Inbox/Bản Nháp trên ứng dụng TikTok điện thoại của bạn. Bạn mở app lên và chỉ cần 1 thao tác nhấn **POST** để qua mặt mọi thuật toán nhận diện.

---

## 🛡 2. Ba Bài Học Xương Máu Về Kỹ Thuật

Đây là 3 hố bom chúng ta đã giẫm phải và tốn công dọn dẹp để hệ thống vận hành trơn tru:

### ⛔️ A. Cạm Bẫy Bot Spam của TikTok (`DIRECT_POST` vs `UPLOAD`)
*   **Sai lầm:** Nếu set `"content_posting_method": "DIRECT_POST"`, TikTok sẽ biết bài này được đăng bằng IP của máy chủ. Cứ diễn ra nhiều lần, kênh bị dán nhãn là Bot ➡ Đóng băng View, giảm Reach thê thảm.
*   **Giải pháp (Đã ứng dụng):** Thiết lập cờ `"content_posting_method": "UPLOAD"` + `"privacy_level": "SELF_ONLY"`. Thủ thuật này tuồn ảnh thẳng vào hộp thư điện thoại. Việc nhấn nút đăng cuối cùng phải thực hiện trên máy điện thoại của chủ kênh nên được coi là "Nguồn sạch".

### ⛔️ B. Lỗi "Nuốt Tiền" ở môi trường gọi lệnh (Bash)
*   **Sai lầm:** Tham số Caption có chứa số tiền `$5k` bị Bash nghiễm nhiên tưởng là **Biến $5** nên đã tự động xoá xổ làm chỉ còn chữ `k` tụt lộ ra ngoài (*"I saved k in 6 slideths..."*).
*   **Giải pháp (Đã ứng dụng):** Bỏ lệnh trung gian thô `execSync`, chuyển sang dùng mảng phân tách Array thông qua lõi `execFileSync`, đồng thời chốt thêm một lệnh chạy `.replace(/\$/g, '\\$')` bằng Regex để tàng hình trước sự dòm ngó của Shell. Tiền của bạn không bao giờ thiếu một xu. 

### ⛔️ C. Lỗ hổng Mất Ảnh Của Bác Phục Vụ `postiz CLI`
*   **Sai lầm:** Nếu dùng vòng lặp cắm cờ mộc mạc kiểu `-m link1 -m link2`, Postiz sẽ bị quá tải thông tin, nó phủi tay huỷ hết 5 cờ cuối và chỉ lấy duy nhất ảnh đầu tiên (`slide_01.png`).
*   **Giải pháp (Đã ứng dụng):** Phải gộp toàn chùm link lại cách nhau bằng dấu phẩy dưới đúng 1 chiếc ô duy nhất: `-m "link1,link2,link3,...,link6"`. Khi chạy xong dòng lệnh xử lý bằng hàm `.join(',')`, 6 bức ảnh đã kết dính hoàn hảo thành Carousel.

---

## ▶️ 3. Thao Tác Chạy Cuối Cùng 

Bất cứ lúc nào muốn xả ảnh kho hàng, chỉ cần chạy đúng 1 lệnh (Nhớ lưu ý phải có biến môi trường ID kênh TikTok):

```bash
TIKTOK_INTEGRATION_ID=cmo2cyjfd0277qk0y9nsrmw37 node batch-schedule.js
```

Kiểm tra xem lịch đã vào chuồng chưa:
```bash
postiz posts:list
```

Chúc dự án Tự động hoá của bạn sớm thu hái View ngàn K ngàn M! 🚀
