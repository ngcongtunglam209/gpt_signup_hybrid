//! i18n — chuỗi giao diện người dùng Việt/Anh.
//!
//! Single source cho mọi text gửi user. Admin command vẫn tiếng Anh (operator).
//! `Lang` lưu trong Settings store theo user_id (bảng `user_lang`).

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Lang {
    Vi,
    En,
}

impl Lang {
    pub fn from_code(s: &str) -> Option<Lang> {
        match s.trim().to_lowercase().as_str() {
            "vi" => Some(Lang::Vi),
            "en" => Some(Lang::En),
            _ => None,
        }
    }
    pub fn code(self) -> &'static str {
        match self {
            Lang::Vi => "vi",
            Lang::En => "en",
        }
    }
}

/// Chọn theo lang: (vi, en).
fn pick(lang: Lang, vi: &str, en: &str) -> String {
    match lang {
        Lang::Vi => vi.to_string(),
        Lang::En => en.to_string(),
    }
}

// ─── Language picker ────────────────────────────────────────────────────

pub fn choose_language() -> &'static str {
    "🌐 Chọn ngôn ngữ / Choose your language:"
}

pub fn language_set(lang: Lang) -> String {
    pick(lang, "✅ Đã đặt ngôn ngữ: Tiếng Việt", "✅ Language set: English")
}

// ─── Welcome / help ───────────────────────────────────────────────────

pub fn welcome(lang: Lang) -> String {
    pick(
        lang,
        "👋 *UPI QR Bot*\n\n\
         Gửi cho bot 1 trong 2:\n\
         • File `session.json` lấy từ https://chatgpt.com/api/auth/session\n\
         • Hoặc tài khoản dạng `email|password|2fa_secret` (gửi nhiều dòng = nhiều tiến trình)\n\n\
         Bạn chạy được tối đa *5 tiến trình* cùng lúc. Mỗi tiến trình hiển thị ở 1 tin riêng kèm nút Dừng.\n\n\
         Chọn thao tác:",
        "👋 *UPI QR Bot*\n\n\
         Send the bot one of:\n\
         • A `session.json` file from https://chatgpt.com/api/auth/session\n\
         • Or accounts as `email|password|2fa_secret` (multiple lines = multiple processes)\n\n\
         You can run up to *5 processes* at once. Each process shows in its own message with a Stop button.\n\n\
         Pick an action:",
    )
}

// ─── Button labels ──────────────────────────────────────────────────────

pub fn btn_status(lang: Lang) -> String {
    pick(lang, "📊 Trạng thái", "📊 Status")
}
pub fn btn_stop_all(lang: Lang) -> String {
    pick(lang, "🛑 Dừng hết", "🛑 Stop all")
}
pub fn btn_help(lang: Lang) -> String {
    pick(lang, "❓ Trợ giúp", "❓ Help")
}
pub fn btn_settings(lang: Lang) -> String {
    pick(lang, "⚙️ Cài đặt", "⚙️ Settings")
}
pub fn btn_stop_this(lang: Lang) -> String {
    pick(lang, "🛑 Dừng tiến trình này", "🛑 Stop this process")
}
pub fn btn_language(lang: Lang) -> String {
    pick(lang, "🌐 Ngôn ngữ", "🌐 Language")
}
pub fn btn_board_refresh(lang: Lang) -> String {
    pick(lang, "🔄 Làm mới", "🔄 Refresh")
}
pub fn btn_board_stop(lang: Lang, email: &str) -> String {
    pick(lang, &format!("🛑 {}", email), &format!("🛑 {}", email))
}

// ─── Board ────────────────────────────────────────────────────────────

/// Note "proxy chậm — skip cho job này" gắn sau dòng probe khi latency vượt
/// ngưỡng cấu hình.
pub fn proxy_skip_slow(lang: Lang, latency_ms: u64, limit_ms: u64) -> String {
    pick(
        lang,
        &format!(" · ⚠️ chậm ({}ms > {}ms) → bỏ qua cho job này", latency_ms, limit_ms),
        &format!(" · ⚠️ slow ({}ms > {}ms) → skipped for this job", latency_ms, limit_ms),
    )
}

/// Note "proxy chậm nhưng vẫn dùng" — trường hợp pool không còn proxy nhanh
/// nào, fallback dùng line slow để job không bị block.
pub fn proxy_slow_fallback(lang: Lang, latency_ms: u64, limit_ms: u64) -> String {
    pick(
        lang,
        &format!(" · 🐢 chậm ({}ms > {}ms) — vẫn dùng (không có proxy nhanh)", latency_ms, limit_ms),
        &format!(" · 🐢 slow ({}ms > {}ms) — used anyway (no fast proxy)", latency_ms, limit_ms),
    )
}

/// Cảnh báo cho card pre-flight: pool user toàn dead → job sẽ chạy DIRECT
/// (không block, đỡ hơn chặn user vì proxy chết).
pub fn proxy_pool_all_dead_direct(lang: Lang) -> String {
    pick(
        lang,
        "⚠️ Pool proxy toàn dead — job sẽ chạy DIRECT (không proxy).",
        "⚠️ All pool proxies dead — job will run DIRECT (no proxy).",
    )
}

pub fn board_stopped_toast(lang: Lang, ok: bool) -> String {
    if ok {
        pick(lang, "🛑 Đã dừng tiến trình.", "🛑 Process stopped.")
    } else {
        pick(lang, "ℹ️ Tiến trình đã kết thúc / không thuộc về bạn.", "ℹ️ Process already finished / not yours.")
    }
}

// ─── Settings menu ────────────────────────────────────────────────────

pub fn settings_title(lang: Lang) -> String {
    pick(lang, "⚙️ Cài đặt", "⚙️ Settings")
}

// ─── Submit / validation ────────────────────────────────────────────────

pub fn invalid_session_json(lang: Lang) -> String {
    pick(
        lang,
        "❌ JSON không hợp lệ. Chỉ nhận file `session.json` lấy từ \
         https://chatgpt.com/api/auth/session (phải có `accessToken` + `user`), \
         hoặc combo `email|password|2fa_secret`.",
        "❌ Invalid JSON. Only accept `session.json` from \
         https://chatgpt.com/api/auth/session (must contain `accessToken` + `user`), \
         or combo `email|password|2fa_secret`.",
    )
}

pub fn invalid_combo(lang: Lang) -> String {
    pick(
        lang,
        "❌ Sai định dạng. Gửi 1 tài khoản mỗi lần dạng `email|password|2fa_secret`, \
         hoặc gửi file `session.json`.",
        "❌ Wrong format. Send one account at a time as `email|password|2fa_secret`, \
         or send a `session.json` file.",
    )
}

/// Header khi nhận batch nhiều dòng combo. `accepted` = số job sẽ tạo,
/// `invalid` = dòng sai bị bỏ, `dropped` = dòng vượt cap/user bị bỏ.
pub fn combo_batch_received(lang: Lang, accepted: usize, invalid: usize, dropped: usize) -> String {
    let mut vi = format!("📥 Nhận {} tài khoản — tạo tiến trình cho từng cái...", accepted);
    let mut en = format!("📥 Received {} accounts — creating a process for each...", accepted);
    if invalid > 0 {
        vi.push_str(&format!("\n⚠️ Bỏ {} dòng sai định dạng.", invalid));
        en.push_str(&format!("\n⚠️ Skipped {} invalid line(s).", invalid));
    }
    if dropped > 0 {
        vi.push_str(&format!("\n⚠️ Vượt giới hạn {} tiến trình/lần — bỏ {} dòng dư.", accepted, dropped));
        en.push_str(&format!("\n⚠️ Over the {} processes/batch limit — dropped {} extra line(s).", accepted, dropped));
    }
    pick(lang, &vi, &en)
}

pub fn need_input(lang: Lang) -> String {    pick(
        lang,
        "📄 Gửi file `session.json` hoặc dán combo `email|password|2fa`.",
        "📄 Send a `session.json` file or paste combo `email|password|2fa`.",
    )
}

/// Caption file session.json gửi lại user sau khi login từ combo thành công.
pub fn reuse_session_caption(lang: Lang, email: &str) -> String {
    pick(
        lang,
        &format!(
            "💾 Session của {} đã đăng nhập xong.\nLần sau hãy GỬI THẲNG file session.json này \
             cho bot (thay vì combo) để chạy nhanh hơn và đỡ rủi ro đăng nhập lại.",
            email
        ),
        &format!(
            "💾 Session for {} is ready.\nNext time, send THIS session.json file to the bot \
             (instead of the combo) for faster runs and to avoid re-login.",
            email
        ),
    )
}

pub fn session_no_email(lang: Lang) -> String {
    pick(
        lang,
        "❌ Session thiếu email. File `session.json` phải có `user.email` hợp lệ \
         (đây là định danh tài khoản). Lấy lại session từ \
         https://chatgpt.com/api/auth/session rồi gửi lại.",
        "❌ Session has no email. The `session.json` must contain a valid \
         `user.email` (account identifier). Re-fetch from \
         https://chatgpt.com/api/auth/session and resend.",
    )
}

// ─── Admission ────────────────────────────────────────────────────────

pub fn duplicate_account(lang: Lang, email: &str) -> String {
    pick(
        lang,
        &format!(
            "⚠️ Tài khoản {} đang chạy/trong hàng chờ rồi. Đợi tiến trình hiện tại \
             xong (hoặc /stop) trước khi gửi lại tài khoản này.",
            email
        ),
        &format!(
            "⚠️ Account {} is already running/queued. Wait for the current process \
             to finish (or /stop) before resubmitting this account.",
            email
        ),
    )
}

pub fn max_concurrent(lang: Lang, max: u32) -> String {
    pick(
        lang,
        &format!("⚠️ Bạn đang chạy tối đa {} tiến trình. Đợi 1 tiến trình xong rồi gửi tiếp.", max),
        &format!("⚠️ You're already running {} processes. Wait for one to finish before sending more.", max),
    )
}

pub fn cooldown(lang: Lang, secs: u64) -> String {
    pick(
        lang,
        &format!("⏱ Chờ {}s rồi thử lại.", secs),
        &format!("⏱ Cooldown — wait {}s before retrying.", secs),
    )
}

pub fn queue_full(lang: Lang, pending: usize, capacity: usize) -> String {
    pick(
        lang,
        &format!("🚫 Hàng chờ đầy ({}/{}). Bot đang bận, thử lại sau ít phút.", pending, capacity),
        &format!("🚫 Queue full ({}/{}). Bot is busy, retry in a few minutes.", pending, capacity),
    )
}

pub fn queue_closed(lang: Lang) -> String {
    pick(lang, "🚫 Hàng chờ đã đóng.", "🚫 Queue closed.")
}

// ─── Job lifecycle ────────────────────────────────────────────────────

pub fn job_received(lang: Lang, email: &str) -> String {
    pick(
        lang,
        &format!("🚀 Đã nhận tài khoản\nEmail: {}\nĐang vào hàng chờ...", email),
        &format!("🚀 Account received\nEmail: {}\nQueueing...", email),
    )
}

pub fn qr_caption(lang: Lang, email: &str, expires: &str) -> String {
    pick(
        lang,
        &format!("✅ UPI QR\nEmail: {}\nHết hạn: {}", email, expires),
        &format!("✅ UPI QR\nEmail: {}\nExpires: {}", email, expires),
    )
}

/// Tin nhắn riêng kèm link thanh toán (gửi sau ảnh QR khi thành công).
pub fn payment_link_msg(lang: Lang, url: &str) -> String {
    pick(
        lang,
        &format!("💳 Link thanh toán:\n{}", url),
        &format!("💳 Payment link:\n{}", url),
    )
}

// ─── Stop ─────────────────────────────────────────────────────────────

pub fn stopped_this(lang: Lang) -> String {
    pick(lang, "🛑 Đã dừng tiến trình này.", "🛑 This process was stopped.")
}

pub fn stop_not_found(lang: Lang) -> String {
    pick(lang, "ℹ️ Tiến trình đã kết thúc hoặc không tồn tại.", "ℹ️ Process already finished or not found.")
}

pub fn stopped_all(lang: Lang, n: usize) -> String {
    if n == 0 {
        pick(lang, "ℹ️ Không có tiến trình nào để dừng.", "ℹ️ No running processes to stop.")
    } else {
        pick(
            lang,
            &format!("🛑 Đã dừng {} tiến trình của bạn.", n),
            &format!("🛑 Stopped {} of your processes.", n),
        )
    }
}

// ─── Access ───────────────────────────────────────────────────────────

pub fn banned(lang: Lang) -> String {
    pick(lang, "⛔ Bạn đã bị admin chặn.", "⛔ You have been blocked by the admin.")
}

pub fn not_whitelisted(lang: Lang) -> String {
    pick(lang, "⛔ Tài khoản chưa được cấp quyền. Liên hệ admin.", "⛔ Account not whitelisted. Contact the admin.")
}

pub fn unknown_command(lang: Lang, cmd: &str) -> String {
    pick(
        lang,
        &format!("❓ Lệnh không hợp lệ: {}\n\nGõ /help để xem danh sách.", cmd),
        &format!("❓ Unknown command: {}\n\nType /help for the list.", cmd),
    )
}

pub fn status_online(lang: Lang) -> String {
    pick(lang, "✅ Bot đang hoạt động.", "✅ Bot online.")
}

// ─── Proxy: buttons ───────────────────────────────────────────────────

pub fn btn_proxy_check(lang: Lang) -> String {
    pick(lang, "🔍 Kiểm tra trạng thái", "🔍 Check live status")
}
pub fn btn_proxy_remove(lang: Lang) -> String {
    pick(lang, "🗑 Xóa proxy", "🗑 Remove proxy")
}

// ─── Proxy: /proxy_set ────────────────────────────────────────────────

/// Render danh sách proxy (đã mask) dạng đánh số, kèm hướng dẫn nút.
pub fn proxy_show_pool(lang: Lang, masked: &[String]) -> String {
    let mut listing = String::new();
    for (i, m) in masked.iter().enumerate() {
        listing.push_str(&format!("{}. {}\n", i + 1, m));
    }
    pick(
        lang,
        &format!(
            "🌐 Pool proxy của bạn ({}/10):\n{}\nBot xoay proxy ngẫu nhiên trong pool. \
             Pre-flight tự loại bỏ proxy chết/chậm trước mỗi job.\n\n\
             Đổi pool: /proxy_set\n<line 1>\n<line 2>\n...",
            masked.len(),
            listing
        ),
        &format!(
            "🌐 Your proxy pool ({}/10):\n{}\nThe bot rotates proxies randomly across the pool. \
             Pre-flight removes dead/slow proxies before each job.\n\n\
             To change: /proxy_set\n<line 1>\n<line 2>\n...",
            masked.len(),
            listing
        ),
    )
}

pub fn proxy_set_usage_multi(lang: Lang) -> String {
    pick(
        lang,
        "ℹ️ Bạn chưa đặt proxy nào.\n\n\
         Cách dùng (1 hoặc NHIỀU dòng, tối đa 10):\n\
         /proxy_set host1:port1\nhost2:port2:user:pass\nhttp://u:p@host3:port3\n\n\
         Hỗ trợ template {SID} cho sticky session.",
        "ℹ️ You haven't set any proxy yet.\n\n\
         Usage (1 or MORE lines, up to 10):\n\
         /proxy_set host1:port1\nhost2:port2:user:pass\nhttp://u:p@host3:port3\n\n\
         Supports {SID} placeholder for sticky sessions.",
    )
}

pub fn proxy_set_ok_pool(
    lang: Lang,
    masked: &[String],
    from_step: u32,
    dropped: usize,
    invalid: usize,
) -> String {
    let mut listing = String::new();
    for (i, m) in masked.iter().enumerate() {
        listing.push_str(&format!("{}. {}\n", i + 1, m));
    }
    let mut notes = String::new();
    if dropped > 0 {
        match lang {
            Lang::Vi => notes.push_str(&format!("\n⚠️ Vượt giới hạn 10 dòng — đã bỏ {} dòng cuối.", dropped)),
            Lang::En => notes.push_str(&format!("\n⚠️ Over the 10-line cap — dropped {} extra line(s).", dropped)),
        }
    }
    if invalid > 0 {
        match lang {
            Lang::Vi => notes.push_str(&format!("\n⚠️ Bỏ {} dòng sai định dạng.", invalid)),
            Lang::En => notes.push_str(&format!("\n⚠️ Skipped {} invalid line(s).", invalid)),
        }
    }
    pick(
        lang,
        &format!(
            "✅ Đã lưu pool proxy của bạn ({} dòng):\n{}\n\
             Job tiếp theo sẽ xoay ngẫu nhiên trong pool, ghi đè pool chung từ step {} trở đi.{}",
            masked.len(),
            listing,
            from_step,
            notes
        ),
        &format!(
            "✅ Saved your proxy pool ({} lines):\n{}\n\
             Your next job will rotate randomly through this pool, overriding the global pool from step {} onward.{}",
            masked.len(),
            listing,
            from_step,
            notes
        ),
    )
}

pub fn proxy_empty_line(lang: Lang) -> String {
    pick(lang, "❌ Dòng proxy rỗng.", "❌ Empty proxy line.")
}

pub fn proxy_invalid_format(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!(
            "❌ Định dạng proxy không hợp lệ: {}\n\n\
             Hỗ trợ:\n\
             • host:port\n\
             • host:port:user:pass\n\
             • scheme://user:pass@host:port",
            err
        ),
        &format!(
            "❌ Invalid proxy format: {}\n\n\
             Supported:\n\
             • host:port\n\
             • host:port:user:pass\n\
             • scheme://user:pass@host:port",
            err
        ),
    )
}

pub fn proxy_save_failed(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Lưu thất bại: {}", err),
        &format!("❌ Save failed: {}", err),
    )
}

// ─── Proxy: /proxy_remove + callbacks ─────────────────────────────────

pub fn proxy_removed_global(lang: Lang) -> String {
    pick(
        lang,
        "🧹 Đã xóa proxy của bạn. Job tiếp theo sẽ dùng pool chung của admin (hoặc DIRECT).",
        "🧹 Your proxy has been removed. Your next job will use the admin's global pool (or DIRECT).",
    )
}

pub fn proxy_removed_direct(lang: Lang) -> String {
    pick(
        lang,
        "🧹 Đã xóa proxy của bạn. Job tiếp theo sẽ chạy DIRECT (hoặc dùng pool chung của admin).",
        "🧹 Your proxy has been removed. Your next job will run DIRECT (or use the admin's global pool).",
    )
}

pub fn proxy_none_to_remove(lang: Lang) -> String {
    pick(
        lang,
        "ℹ️ Bạn chưa đặt proxy nào để xóa.",
        "ℹ️ You don't have a proxy set to remove.",
    )
}

pub fn proxy_not_set(lang: Lang) -> String {
    pick(lang, "ℹ️ Bạn chưa đặt proxy.", "ℹ️ You haven't set a proxy yet.")
}

pub fn proxy_remove_failed(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Xóa thất bại: {}", err),
        &format!("❌ Remove failed: {}", err),
    )
}

pub fn db_error(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Lỗi DB: {}", err),
        &format!("❌ DB error: {}", err),
    )
}

// ─── Proxy: probe result card ─────────────────────────────────────────

pub fn proxy_probe_card(
    lang: Lang,
    ok: bool,
    status: &str,
    masked_line: &str,
    latency_ms: u64,
    detail_label_value: &str,
    endpoint: &str,
) -> String {
    let icon = if ok { "✅" } else { "❌" };
    pick(
        lang,
        &format!(
            "{} Kiểm tra proxy: {}\n\
             Dòng: {}\n\
             Độ trễ: {} ms\n\
             {}\n\
             Endpoint: {}\n",
            icon, status, masked_line, latency_ms, detail_label_value, endpoint
        ),
        &format!(
            "{} Proxy probe: {}\n\
             Line: {}\n\
             Latency: {} ms\n\
             {}\n\
             Endpoint: {}\n",
            icon, status, masked_line, latency_ms, detail_label_value, endpoint
        ),
    )
}

/// Nhãn dòng detail trong probe card (Exit IP khi OK, Detail khi lỗi).
pub fn proxy_probe_detail(lang: Lang, ok: bool, value: &str) -> String {
    if ok {
        pick(lang, &format!("IP ra: {}", value), &format!("Exit IP: {}", value))
    } else {
        pick(lang, &format!("Chi tiết: {}", value), &format!("Detail: {}", value))
    }
}

// ─── Short toasts (answerCallbackQuery) ───────────────────────────────

pub fn toast_blocked(lang: Lang) -> String {
    pick(lang, "Bạn đã bị chặn", "You are blocked")
}
pub fn toast_not_whitelisted(lang: Lang) -> String {
    pick(lang, "Chưa được cấp quyền", "Not whitelisted")
}
pub fn toast_probing(lang: Lang) -> String {
    pick(lang, "Đang kiểm tra...", "Probing...")
}
pub fn toast_removed(lang: Lang) -> String {
    pick(lang, "Đã xóa", "Removed")
}
pub fn toast_nothing_to_remove(lang: Lang) -> String {
    pick(lang, "Không có gì để xóa", "Nothing to remove")
}
pub fn toast_db_error(lang: Lang) -> String {
    pick(lang, "Lỗi DB", "DB error")
}
pub fn toast_unknown_action(lang: Lang) -> String {
    pick(lang, "Hành động không xác định", "Unknown action")
}

pub fn admin_only(lang: Lang) -> String {
    pick(lang, "⛔ Lệnh chỉ dành cho admin.", "⛔ Admin-only command.")
}

// ─── Admin notifications (system → admin DM / notify target) ───────────

pub fn admin_note_blocked_proxy_dead(
    lang: Lang,
    username: &str,
    user_id: i64,
    email: &str,
    proxy_block: &str,
) -> String {
    pick(
        lang,
        &format!(
            "⛔ Job bị chặn (proxy chết)\nTừ: @{} (id {})\nEmail: {}\n{}",
            username, user_id, email, proxy_block
        ),
        &format!(
            "⛔ Job blocked (proxy down)\nFrom: @{} (id {})\nEmail: {}\n{}",
            username, user_id, email, proxy_block
        ),
    )
}

pub fn admin_note_new_process(
    lang: Lang,
    username: &str,
    user_id: i64,
    email: &str,
    auth_kind: &str,
    queue_pos: usize,
) -> String {
    pick(
        lang,
        &format!(
            "🆕 Tiến trình mới\nTừ: @{} (id {})\nEmail: {}\nNguồn: {}\nHàng chờ: ~{}",
            username, user_id, email, auth_kind, queue_pos
        ),
        &format!(
            "🆕 New process\nFrom: @{} (id {})\nEmail: {}\nSource: {}\nQueue: ~{}",
            username, user_id, email, auth_kind, queue_pos
        ),
    )
}

pub fn admin_note_qr_success(
    lang: Lang,
    username: &str,
    user_id: i64,
    email: &str,
    elapsed_s: f64,
) -> String {
    pick(
        lang,
        &format!(
            "🆕 QR thành công\nTừ: @{} (id {})\nEmail: {}\nThời gian: {:.1}s",
            username, user_id, email, elapsed_s
        ),
        &format!(
            "🆕 QR success\nFrom: @{} (id {})\nEmail: {}\nElapsed: {:.1}s",
            username, user_id, email, elapsed_s
        ),
    )
}

pub fn admin_note_user_set_proxy(
    lang: Lang,
    line_count: usize,
    username: &str,
    user_id: i64,
    raw: &str,
    masked: &str,
) -> String {
    pick(
        lang,
        &format!(
            "🌐 User đặt pool proxy ({} dòng)\nTừ: @{} (id {})\nRaw: {}\nMasked: {}",
            line_count, username, user_id, raw, masked
        ),
        &format!(
            "🌐 User set proxy pool ({} lines)\nFrom: @{} (id {})\nRaw: {}\nMasked: {}",
            line_count, username, user_id, raw, masked
        ),
    )
}

// ─── Admin: /stopall + /flushall ──────────────────────────────────────

pub fn admin_stopall_done(lang: Lang, n: usize) -> String {
    pick(
        lang,
        &format!("🛑 Đã dừng {} tiến trình của tất cả user.", n),
        &format!("🛑 Stopped {} process(es) across all users.", n),
    )
}

pub fn admin_flushall_done(lang: Lang, jobs: usize, cards: usize, buffers: usize) -> String {
    pick(
        lang,
        &format!(
            "🧹 Đã flush sạch.\n• Job đã hủy: {}\n• Board entries: {}\n• Buffer text đang chờ: {}",
            jobs, cards, buffers
        ),
        &format!(
            "🧹 Flushed all.\n• Cancelled jobs: {}\n• Board entries cleared: {}\n• Pending text buffers cleared: {}",
            jobs, cards, buffers
        ),
    )
}

// ─── Admin: /set_notify, /notify_remove, /notify_test ──────────────────

pub fn admin_notify_show_with_topic(lang: Lang, chat_id: i64, thread_id: i64) -> String {
    pick(
        lang,
        &format!(
            "🔔 Notify hiện tại: chat_id={} · topic={}\n\n\
             Đặt lại: /set_notify <chat_id> [thread_id] hoặc dán link topic\n\
             Xóa: /notify_remove · Test: /notify_test",
            chat_id, thread_id
        ),
        &format!(
            "🔔 Notify target: chat_id={} · topic={}\n\n\
             Change: /set_notify <chat_id> [thread_id] or paste a topic link\n\
             Remove: /notify_remove · Test: /notify_test",
            chat_id, thread_id
        ),
    )
}

pub fn admin_notify_show_root(lang: Lang, chat_id: i64) -> String {
    pick(
        lang,
        &format!(
            "🔔 Notify hiện tại: chat_id={} (root)\n\n\
             Đặt lại: /set_notify <chat_id> [thread_id] hoặc dán link topic\n\
             Xóa: /notify_remove · Test: /notify_test",
            chat_id
        ),
        &format!(
            "🔔 Notify target: chat_id={} (root)\n\n\
             Change: /set_notify <chat_id> [thread_id] or paste a topic link\n\
             Remove: /notify_remove · Test: /notify_test",
            chat_id
        ),
    )
}

pub fn admin_notify_show_unset(lang: Lang) -> String {
    pick(
        lang,
        "🔔 Notify chưa cấu hình — đang fallback về ADMIN_CHAT_ID (nếu có).\n\n\
         Cách 1: /set_notify <chat_id> [thread_id]\n\
         Cách 2: /set_notify <link topic>  (vd https://t.me/c/2123456789/45)\n\n\
         Mẹo: forward 1 tin nhắn từ topic cho @userinfobot để lấy ID.",
        "🔔 Notify not configured — falling back to ADMIN_CHAT_ID (if set).\n\n\
         Way 1: /set_notify <chat_id> [thread_id]\n\
         Way 2: /set_notify <topic link>  (e.g. https://t.me/c/2123456789/45)\n\n\
         Tip: forward a message from the topic to @userinfobot to get IDs.",
    )
}

pub fn admin_notify_set_bad_format(lang: Lang) -> String {
    pick(
        lang,
        "❌ Sai format. Dùng: /set_notify <chat_id> [thread_id] hoặc dán link topic.",
        "❌ Wrong format. Use: /set_notify <chat_id> [thread_id] or paste a topic link.",
    )
}

pub fn admin_notify_set_probe_text(lang: Lang, chat_id: i64, thread_id: Option<i64>) -> String {
    pick(
        lang,
        &format!(
            "✅ Notify target đã set bởi admin. chat_id={} thread={:?}",
            chat_id, thread_id
        ),
        &format!(
            "✅ Notify target set by admin. chat_id={} thread={:?}",
            chat_id, thread_id
        ),
    )
}

pub fn admin_notify_set_ok(lang: Lang, chat_id: i64, thread_id: Option<i64>) -> String {
    let topic = thread_id
        .map(|t| t.to_string())
        .unwrap_or_else(|| "—".into());
    pick(
        lang,
        &format!(
            "✅ Đã set notify target: chat_id={} · topic={}\nĐã gửi 1 tin test vào đó.",
            chat_id, topic
        ),
        &format!(
            "✅ Notify target set: chat_id={} · topic={}\nA test message was sent there.",
            chat_id, topic
        ),
    )
}

pub fn admin_notify_set_fail(
    lang: Lang,
    chat_id: i64,
    thread_id: Option<i64>,
    err: &str,
) -> String {
    pick(
        lang,
        &format!(
            "⚠️ Đã lưu chat_id={} topic={:?} NHƯNG gửi test FAIL: {}\n\
             Kiểm tra: bot đã được add vào group/topic + có quyền gửi tin chưa?",
            chat_id, thread_id, err
        ),
        &format!(
            "⚠️ Saved chat_id={} topic={:?} BUT test send FAILED: {}\n\
             Check: is the bot added to the group/topic and allowed to post?",
            chat_id, thread_id, err
        ),
    )
}

pub fn admin_notify_remove_ok(lang: Lang) -> String {
    pick(
        lang,
        "🗑 Đã xóa notify target. Quay lại fallback ADMIN_CHAT_ID (nếu có).",
        "🗑 Notify target removed. Falling back to ADMIN_CHAT_ID (if set).",
    )
}

pub fn admin_notify_remove_none(lang: Lang) -> String {
    pick(
        lang,
        "ℹ️ Chưa có notify target nào để xóa.",
        "ℹ️ No notify target to remove.",
    )
}

pub fn admin_notify_remove_db_err(lang: Lang) -> String {
    pick(
        lang,
        "❌ Lỗi DB khi xóa notify target.",
        "❌ DB error while removing notify target.",
    )
}

pub fn admin_notify_test_unset(lang: Lang) -> String {
    pick(
        lang,
        "ℹ️ Chưa có notify target. Dùng /set_notify hoặc set ADMIN_CHAT_ID.",
        "ℹ️ No notify target. Use /set_notify or set ADMIN_CHAT_ID.",
    )
}

pub fn admin_notify_test_body(
    lang: Lang,
    chat_id: i64,
    thread_id: Option<i64>,
    clock: &str,
) -> String {
    pick(
        lang,
        &format!(
            "🧪 Test notify\nchat_id={} thread={:?}\nThời gian: {}",
            chat_id, thread_id, clock
        ),
        &format!(
            "🧪 Test notify\nchat_id={} thread={:?}\nTime: {}",
            chat_id, thread_id, clock
        ),
    )
}

pub fn admin_notify_test_ok(lang: Lang, chat_id: i64, thread_id: Option<i64>) -> String {
    let topic = thread_id
        .map(|t| t.to_string())
        .unwrap_or_else(|| "—".into());
    pick(
        lang,
        &format!("✅ Gửi test OK vào chat_id={} topic={}", chat_id, topic),
        &format!("✅ Test sent OK to chat_id={} topic={}", chat_id, topic),
    )
}

pub fn admin_notify_test_fail(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Gửi test FAIL: {}", err),
        &format!("❌ Test send FAILED: {}", err),
    )
}

// ─── Admin: /ban + /unban + /banlist ───────────────────────────────────

pub fn admin_ban_usage(lang: Lang) -> String {
    pick(
        lang,
        "Cách dùng: /ban <@username | id> [lý do]\nVD: /ban @vippro  ·  /ban 2314324",
        "Usage: /ban <@username | id> [reason]\nE.g.: /ban @vippro  ·  /ban 2314324",
    )
}

pub fn admin_ban_cant_ban_admin(lang: Lang) -> String {
    pick(lang, "⚠️ Không thể ban admin.", "⚠️ Cannot ban the admin.")
}

pub fn admin_unban_usage(lang: Lang) -> String {
    pick(
        lang,
        "Cách dùng: /unban <@username | id>",
        "Usage: /unban <@username | id>",
    )
}

pub fn admin_banlist_empty(lang: Lang) -> String {
    pick(lang, "✅ Không có user nào bị ban.", "✅ No users are banned.")
}

// ─── Admin: /chat + /notify ────────────────────────────────────────────

pub fn admin_notify_broadcast_usage(lang: Lang) -> String {
    pick(
        lang,
        "Cách dùng: /notify <nội dung>\n(Hỗ trợ xuống dòng + format chữ.)",
        "Usage: /notify <message>\n(Supports line breaks + text formatting.)",
    )
}

pub fn admin_notify_broadcast_start(lang: Lang, total: usize) -> String {
    pick(
        lang,
        &format!("📢 Đang broadcast tới {} user...", total),
        &format!("📢 Broadcasting to {} users...", total),
    )
}

pub fn admin_notify_broadcast_done(lang: Lang, ok: usize, fail: usize, pruned: usize) -> String {
    pick(
        lang,
        &format!(
            "✅ Broadcast xong\nGửi OK: {}\nThất bại: {}\nPrune user đã chặn bot: {}",
            ok, fail, pruned
        ),
        &format!(
            "✅ Broadcast done\nSent OK: {}\nFailed: {}\nPruned users who blocked the bot: {}",
            ok, fail, pruned
        ),
    )
}

pub fn admin_chat_usage_short(lang: Lang) -> String {
    pick(
        lang,
        "Cách dùng: /chat <@username | id> <nội dung>",
        "Usage: /chat <@username | id> <message>",
    )
}

pub fn admin_chat_usage_long(lang: Lang) -> String {
    pick(
        lang,
        "Cách dùng: /chat <@username | id> <nội dung>\nVD: /chat @vippro hello  ·  /chat 2314324 QR đã sẵn sàng",
        "Usage: /chat <@username | id> <message>\nE.g.: /chat @vippro hello  ·  /chat 2314324 your QR is ready",
    )
}

pub fn admin_chat_empty_message(lang: Lang) -> String {
    pick(
        lang,
        "❌ Tin nhắn rỗng. Cách dùng: /chat <@username | id> <nội dung>",
        "❌ Empty message. Usage: /chat <@username | id> <message>",
    )
}

// ─── Admin: /proxy_login_set + /proxy_login_remove ────────────────────

pub fn admin_login_proxy_set_ok(
    lang: Lang,
    upper_step: u32,
    masked: &str,
    probe_card: &str,
) -> String {
    pick(
        lang,
        &format!(
            "✅ Login proxy đã set (áp cho step 1..{} của mọi user).\n{}\n\n{}",
            upper_step, masked, probe_card
        ),
        &format!(
            "✅ Login proxy set (applied to step 1..{} for all users).\n{}\n\n{}",
            upper_step, masked, probe_card
        ),
    )
}

pub fn admin_login_proxy_remove_ok(lang: Lang) -> String {
    pick(
        lang,
        "🧹 Đã xóa login proxy. Segment login giờ chạy DIRECT (hoặc pool global env).",
        "🧹 Login proxy removed. Login segment now runs DIRECT (or env global pool).",
    )
}

// ─── Admin: generic action results ────────────────────────────────────

pub fn admin_user_list_read_err(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Không đọc được danh sách user: {}", err),
        &format!("❌ Could not read user list: {}", err),
    )
}

pub fn admin_username_resolve_err(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Lỗi resolve username: {}", err),
        &format!("❌ Username resolve error: {}", err),
    )
}

pub fn admin_username_not_seen_chat(lang: Lang, username: &str) -> String {
    pick(
        lang,
        &format!(
            "❌ Chưa thấy @{} kết nối bot — không resolve được user_id.\n\
             Dùng id số nếu biết: /chat <id> <nội dung>",
            username
        ),
        &format!(
            "❌ Haven't seen @{} connect to the bot — cannot resolve user_id.\n\
             Use the numeric id if you know it: /chat <id> <message>",
            username
        ),
    )
}

pub fn admin_username_not_seen_ban(lang: Lang, username: &str) -> String {
    pick(
        lang,
        &format!(
            "❌ Chưa thấy @{} kết nối bot — không resolve được user_id.\n\
             Ban theo id số nếu biết: /ban <id> [lý do]",
            username
        ),
        &format!(
            "❌ Haven't seen @{} connect to the bot — cannot resolve user_id.\n\
             Ban by numeric id if you know it: /ban <id> [reason]",
            username
        ),
    )
}

pub fn admin_msg_sent(lang: Lang, target_id: i64, uname_disp: &str) -> String {
    pick(
        lang,
        &format!("✅ Đã gửi tin tới user_id {}{}.", target_id, uname_disp),
        &format!("✅ Message sent to user_id {}{}.", target_id, uname_disp),
    )
}

pub fn admin_send_failed(lang: Lang, hint: &str, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Gửi thất bại{}: {}", hint, err),
        &format!("❌ Send failed{}: {}", hint, err),
    )
}

pub fn admin_ban_failed(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Ban thất bại: {}", err),
        &format!("❌ Ban failed: {}", err),
    )
}

pub fn admin_user_id_not_found(lang: Lang, token: &str) -> String {
    pick(
        lang,
        &format!("❌ Không tìm thấy user_id cho '{}'.", token),
        &format!("❌ Could not find user_id for '{}'.", token),
    )
}

pub fn admin_unban_ok(lang: Lang, target_id: i64) -> String {
    pick(
        lang,
        &format!("✅ Đã gỡ ban user_id {}.", target_id),
        &format!("✅ Unbanned user_id {}.", target_id),
    )
}

pub fn admin_unban_failed(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Gỡ ban thất bại: {}", err),
        &format!("❌ Unban failed: {}", err),
    )
}

pub fn admin_banlist_read_err(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Không đọc được danh sách ban: {}", err),
        &format!("❌ Could not read ban list: {}", err),
    )
}

pub fn admin_banlist_header(lang: Lang, count: usize) -> String {
    pick(
        lang,
        &format!("🚫 User bị ban ({}):\n", count),
        &format!("🚫 Banned users ({}):\n", count),
    )
}

pub fn admin_ban_ok(
    lang: Lang,
    target_id: i64,
    uname_disp: &str,
    reason_disp: &str,
    stopped: usize,
) -> String {
    pick(
        lang,
        &format!(
            "🚫 Đã ban user_id {}{}{}\nĐã dừng {} job đang chạy của user.",
            target_id, uname_disp, reason_disp, stopped
        ),
        &format!(
            "🚫 Banned user_id {}{}{}\nStopped {} running job(s) of the user.",
            target_id, uname_disp, reason_disp, stopped
        ),
    )
}

pub fn admin_invalid_proxy_format(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Format proxy không hợp lệ: {}", err),
        &format!("❌ Invalid proxy format: {}", err),
    )
}

pub fn admin_remove_failed(lang: Lang, err: &str) -> String {
    pick(
        lang,
        &format!("❌ Xóa thất bại: {}", err),
        &format!("❌ Remove failed: {}", err),
    )
}
