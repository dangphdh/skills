# My Agent Skills

Bộ sưu tập agent skills dùng cho ZCode / Claude-style agents. Mỗi skill là một thư mục chứa `SKILL.md` (định nghĩa skill) và tùy chọn thư mục `references/` (tài liệu bổ trợ).

Source gốc các skill đang chạy: `C:\Users\Dang Pham\.agents\skills\`

## Skills

| Skill | Mô tả |
|---|---|
| `deep-research` | Nghiên cứu chuyên sâu nhiều vòng với trích dẫn nguồn, dùng parallel research subagents + web search. Xuất báo cáo markdown có trích dẫn. |
| `find-skills` | Giúp khám phá và cài đặt agent skills từ hệ sinh thái mở khi cần mở rộng khả năng. |
| `kids-curriculum` | Thiết kế chương trình học + bài giảng + workbook Toán và Tiếng Anh cho học sinh lớp 3–5 (theo Chương trình GDPT 2018), xuất PDF/DOCX. |

## Cập nhật khi chỉnh sửa skills

Repo này là bản lưu (snapshot) của `.agents\skills`. Khi sửa skill ở source gốc, đồng bộ vào repo:

```bash
# từ thư mục D:\Personal\skills
cp -r "$USERPROFILE/.agents/skills/<tên-skill>" .
git add -A
git commit -m "update <tên-skill>"
git push
```

## Thêm skill mới

1. Copy thư mục skill (chứa `SKILL.md`) vào repo này.
2. Commit + push.
3. Copy vào `C:\Users\Dang Pham\.agents\skills\` để agent sử dụng.
