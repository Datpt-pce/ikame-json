---
title: "Lottie JSON cho in-app: từ layer thiết kế đến bàn giao developer"
date: 2026-10-05
tags:
  - technology
  - lottie
  - motion-design
  - developer-handoff
domain: Technology
status: reviewed
related:
  - "[[lottie-animation|Lottie Animation]]"
  - "[[bodymovin|Bodymovin]]"
  - "[[lottiefiles|LottieFiles]]"
  - "[[dotlottie|dotLottie]]"
  - "[[lottie-runtime-compatibility|Lottie Runtime Compatibility]]"
  - "[[design-handoff|Design Handoff]]"
---

## Tóm tắt

[[lottie-animation|Lottie]] không phải là video được “đổi đuôi” sang JSON. Nó là một mô hình dữ liệu animation: canvas, layer, shape, keyframe, asset và quan hệ giữa chúng được player diễn giải lại ở runtime. Vì vậy, một file chạy đúng trong After Effects hoặc trong preview của [[lottiefiles|LottieFiles]] vẫn chưa đủ để kết luận rằng nó sẽ chạy đúng trong app. Điều cần bàn giao là **một animation đã được thiết kế theo năng lực của đúng player/renderer đích, kèm contract triển khai và bằng chứng QA trên runtime đó**.

Quy trình bền vững là:

> Chốt runtime và hành vi → kiểm tra layer đầu vào → chuẩn hóa artwork → animate bằng tập tính năng tương thích → export bản gốc → kiểm tra feature → tối ưu có kiểm soát → QA trên player/device đích → bàn giao file + contract + bằng chứng.

## 1. Mô hình đúng về Lottie JSON

### 1.1. Trong JSON có gì?

Theo tài liệu định dạng, object gốc của Lottie chứa kích thước canvas (`w`, `h`), frame rate (`fr`), vùng thời gian (`ip`, `op`), danh sách `layers`, `assets`, phiên bản exporter `v`, marker và metadata. `ip` là inclusive còn `op` là exclusive; thời lượng có thể suy ra là `(op - ip) / fr` giây. `v` là phiên bản [[bodymovin|Bodymovin]]/exporter, **không phải version phát hành của asset trong dự án**. [Lottie Docs — Animation](https://lottiefiles.github.io/lottie-docs/composition/)

Lottie Animation Community đã công bố specification 1.0 năm 2024 và tiếp tục mở rộng chuẩn. Trong chuẩn LAC, `ver` là phiên bản specification đích dạng số `MMmmpp`; đây là field khác với `v` dạng chuỗi của Bodymovin JSON lịch sử. Vì vậy schema giúp kiểm tra cấu trúc, nhưng không thay thế kiểm tra khả năng render của player cụ thể. [Lottie Animation Format specification](https://lottie.github.io/lottie-spec/latest/) [LAC — công bố Lottie 1.0](https://lottie.github.io/news/announcing-lottie-specification-1.0/)

Expressions không thuộc tập chuẩn hóa cốt lõi và có thể thực thi code trong một số renderer. Nếu sản phẩm không cần expression, hãy bake chuyển động cần thiết rồi export không có expression; trên lottie-web, dev có thể tắt chúng bằng `rendererSettings.runExpressions: false`. [Lottie specification — expressions](https://lottie.github.io/lottie-spec/latest/) [lottie-web — Renderer Settings](https://github.com/airbnb/lottie-web/wiki/Renderer-Settings)

### 1.2. Vì sao cùng một JSON có thể hiển thị khác nhau?

Player không phát một chuỗi frame dựng sẵn; nó tái dựng animation. Web có các renderer SVG, Canvas và HTML với bảng tính năng khác nhau. Android, iOS Core Animation, iOS Main Thread và Windows cũng không hỗ trợ hoàn toàn giống nhau. Ví dụ, bảng chính thức hiện liệt kê khác biệt ở repeater, trim path, mask mode, matte, merge path và nhiều hiệu ứng. Đây là vấn đề [[lottie-runtime-compatibility|tương thích runtime Lottie]], không chỉ là lỗi export. [Airbnb — bảng supported features đa nền tảng](https://github.com/airbnb/lottie/blob/master/supported-features.md) [lottie-web — khác biệt SVG/Canvas/HTML](https://github.com/airbnb/lottie-web/wiki/Features)

Trên iOS, chế độ `automatic` ưu tiên Core Animation nhưng tự rơi về Main Thread khi animation dùng tính năng không tương thích. Core Animation có đặc tính hiệu năng tốt hơn nhưng không hỗ trợ mọi tính năng; Main Thread hỗ trợ rộng hơn nhưng có CPU overhead và có thể mất frame khi main thread bận. [Lottie iOS — `RenderingEngineOption`](https://github.com/airbnb/lottie-ios/blob/master/Sources/Public/Configuration/RenderingEngineOption.swift)

Trên Android, mask và matte có chi phí render đáng kể; chi phí tăng theo diện tích giao nhau. Merge Paths có điều kiện hỗ trợ riêng và có overhead. [Airbnb Lottie Android — performance, image và merge path](https://github.com/airbnb/lottie/blob/master/android.md)

**Kết luận thực hành:** “Lottie hỗ trợ tính năng X” là câu chưa đủ. Câu hỏi đúng là “player nào, phiên bản nào, renderer nào, OS/API nào hỗ trợ X và đã được test bằng chính file này chưa?”.

## 2. Contract cần chốt trước khi nhận layer

Đây là bước giảm nhiều vòng sửa nhất. Trước khi animate, designer cần lấy từ PM/dev tối thiểu các thông tin sau:

| Nhóm | Câu hỏi cần chốt | Vì sao ảnh hưởng file |
|---|---|---|
| Nền tảng | Web, iOS, Android, React Native hay engine khác? | Mỗi player có matrix hỗ trợ khác nhau. |
| Runtime | Package/player và version chính xác? Web dùng SVG, Canvas, HTML hay dotLottie runtime? | Renderer quyết định tính năng và cách tải asset. |
| Kích thước | Khung hiển thị logic, tỉ lệ, `contain`/`cover`/`fill`, có resize không? | Quyết định canvas, crop và safe area. |
| Hành vi | Autoplay, loop, số vòng, tốc độ, play once, reverse, scrub theo progress hay event? | Quyết định timeline, marker và contract điều khiển. |
| Trạng thái | Cần `idle`, `success`, `error`, `pressed` trong một file hay nhiều file? | Có thể dùng marker/segment, nhiều JSON hoặc dotLottie/state machine. |
| Tuỳ biến | Dev cần đổi màu, text, ảnh, theme hay locale ở runtime? | Cần thống nhất slot/keypath/font; không nên “vá JSON” tùy hứng sau export. |
| Asset | File nằm trong app bundle, tải CDN hay remote config? Offline có phải hoạt động không? | Quyết định JSON + folder ảnh, base64 hay `.lottie`. |
| Hiệu năng | File-size budget, thời gian first frame, số animation chạy đồng thời, thiết bị thấp nhất? | Quyết định số path, mask, raster, frame rate và cách đóng gói. |
| Truy cập | Animation trang trí hay truyền thông tin? Có reduced motion, poster/fallback và mô tả không? | Ảnh hưởng bản thay thế và logic tích hợp. |

Nếu dev chưa chốt runtime/version, hãy coi đó là **blocker kỹ thuật**, không phải chi tiết để xử lý cuối quy trình. Feature Support Checker của LottieFiles so sánh theo player và version, chính thức thừa nhận animation có thể khác giữa web, iOS và Android. [LottieFiles — Feature Support Checker](https://help.lottiefiles.com/hc/en-us/articles/15171713588761-Feature-Support-Checker)

## 3. Nhận và audit layer đầu vào

### 3.1. Checklist chung cho PSD, AI và Figma

Trước khi mở After Effects, kiểm tra:

- Canvas/frame đúng tỉ lệ đích; không để artwork cần crop nằm ngoài safe area mà không có chủ đích.
- Mỗi phần cần animate độc lập phải là layer/group độc lập.
- Tên layer ngắn, duy nhất và có nghĩa: `icon_star`, `label_reward`, `mask_avatar`, không dùng chuỗi `Layer 12 copy 4`.
- Không có layer ẩn, bản nháp, guide, ảnh thừa hoặc asset ngoài canvas không dùng.
- Anchor dự kiến nằm ở tâm xoay/co giãn thực tế, không chỉ ở tâm toàn composition.
- Blend mode, clipping mask, blur, shadow, layer style, adjustment layer và font lạ được đánh dấu để quyết định giữ, tái dựng hay loại bỏ.
- Vector quá nhiều điểm neo được đơn giản hóa trước khi animate; ảnh raster được crop/resize đúng kích thước dùng thực tế.
- Quyền sử dụng font, ảnh và thành phần bên thứ ba đã rõ. LottieFiles lưu ý người tạo chỉ sở hữu output khi có quyền đối với mọi asset dùng trong animation. [LottieFiles for After Effects](https://lottiefiles.com/plugins/after-effects)

### 3.2. PSD

After Effects có thể nhập PSD theo dạng composition và giữ layer. Adobe khuyên chuẩn bị và đặt tên layer kỹ; nhóm layer Photoshop sẽ vào AE như nested composition. Chọn **Composition — Retain Layer Sizes** để từng layer giữ kích thước nội dung, giúp anchor point gần đúng tâm vật thể hơn và transform tự nhiên hơn. [Adobe — Preparing and importing still images](https://helpx.adobe.com/after-effects/desktop/import-files/import-still-images/preparing-importing-still-images.html)

PSD là raster-first. Không nên kỳ vọng logo, icon hoặc chữ trong PSD tự biến thành vector Lottie hiệu quả. Nếu thành phần vốn là vector, xin lại AI/SVG/Figma hoặc dựng lại bằng shape. Nếu buộc dùng ảnh, crop và nén trước khi import.

### 3.3. AI/SVG

Với Illustrator nhiều layer, nhập dạng composition để giữ layer; nếu cần anchor theo từng object, dùng **Retain Layer Sizes**. Chuyển layer vector cần animate sang native shape bằng **Create Shapes from Vector Layer**. Adobe cảnh báo freeform gradient và blend mode từ Illustrator không được giữ nguyên khi chuyển; file hàng nghìn path có thể nhập chậm. [Adobe — Create and customize shapes](https://helpx.adobe.com/after-effects/desktop/drawing-painting-and-paths/shapes-and-shape-attributes/creating-shapes-masks.html)

Airbnb khuyên chuyển Illustrator/EPS/SVG/PDF thành shape layer và gỡ asset vector gốc khỏi composition sau khi chuyển, vì shape layer là vùng Lottie hoạt động tốt nhất. Đồng thời tránh path keyframe không cần thiết, Autotrace và keyframe trên mọi frame vì chúng làm tăng dữ liệu và chi phí render. [Airbnb — Creating Lottie animations](https://github.com/airbnb/lottie/blob/master/after-effects.md)

### 3.4. Figma

Có hai route hợp lệ:

1. **Figma → LottieFiles for Figma** cho preset/prototype phù hợp tập tính năng plugin.
2. **Figma → SVG/AI → After Effects → LottieFiles plugin** khi cần motion timing, rig hoặc timeline chi tiết hơn.

LottieFiles for Figma khuyên dùng tính năng tương thích, giảm số layer, nhóm phần liên quan, đặt tên frame rõ ràng và kiểm tra size. Plugin có thể xuất Lottie JSON hoặc dotLottie, nhưng output “production-ready” vẫn cần kiểm tra ở runtime đích. [LottieFiles for Figma — Getting started](https://help.lottiefiles.com/hc/en-us/articles/4490589769625-getting-started) [Best practices](https://help.lottiefiles.com/hc/en-us/articles/30798913049369-how-to-get-the-best-results)

## 4. Xây composition trong After Effects

### 4.1. Thiết lập nền

- Dùng canvas 1× theo kích thước logic của asset trong app. Airbnb giải thích pixel trong AE được quy đổi thành point trên iOS và dp trên Android; xuất composition phóng lớn tùy tiện không tạo lợi ích tương đương video 2×/3×. [Airbnb — Export at 1x](https://github.com/airbnb/lottie/blob/master/after-effects.md#export-at-1x)
- Chốt `fr`, `ip`, `op` sớm. 30 fps thường đủ cho UI motion; 60 fps chỉ nên dùng khi sản phẩm thật sự cần và target device chịu được. Đây là khuyến nghị thiết kế, không phải giới hạn của format.
- Dùng transform, opacity, shape path có kiểm soát và easing rõ ràng. Ưu tiên parenting/null thay vì sao chép cùng keyframe cho nhiều layer; tài liệu Airbnb chỉ ra keyframe lặp làm tăng dữ liệu JSON. [Airbnb — Keep it Simple](https://github.com/airbnb/lottie/blob/master/after-effects.md#keep-it-simple)
- Mỗi precomp phải có mục đích: component tái sử dụng, vùng loop hoặc cô lập một chuyển động; tránh precomp sâu chỉ để “dọn timeline”.

### 4.2. Tầng tương thích

Không nên ghi nhớ một danh sách “hỗ trợ/không hỗ trợ” bất biến. Hãy dùng ba tầng:

**Tầng an toàn tương đối:**

- Position, scale, rotation, opacity, anchor point.
- Shape cơ bản, fill/stroke đơn giản, path và easing thông thường.
- Solid, null, parenting, precomp vừa phải.

**Tầng cần đối chiếu matrix và test sớm:**

- Repeater, trim paths, merge paths.
- Gradient, dash, mask mode, track matte/luma matte.
- Blend mode, text animator, glyph/font text.
- Blur/shadow/tint/fill effect.
- Expression hoặc rig từ Duik/Limber/RubberHose.

**Tầng nên xem là red flag nếu chưa có bằng chứng target-runtime:**

- Camera/light/3D layer, adjustment layer, layer style.
- Video và image sequence.
- Plugin/effect bên thứ ba chưa bake.
- Expression phức tạp hoặc time stretching.

LottieFiles mô tả transform, basic mask, solid/null và basic time remapping là nhóm được hỗ trợ; nhiều effect, 3D, adjustment layer, layer style và expression phức tạp là không hoặc chỉ hỗ trợ một phần. Đây là bản tóm tắt, còn quyết định cuối phải dựa trên bảng tính năng theo player/version. [LottieFiles — Supported After Effects Features](https://help.lottiefiles.com/supported-after-effects-features) [Supported Lottie Features](https://lottiefiles.com/supported-features)

Nếu dùng rig bên thứ ba, bake expression sang keyframe rồi test lại; LottieFiles nêu rõ các rig expression-driven có thể không export đúng. [LottieFiles — Character Tools](https://help.lottiefiles.com/using-character-tools)

### 4.3. Raster image

Lottie JSON hỗ trợ hai cách:

- **Embedded:** `e: 1`, `u` rỗng, `p` là data URL base64.
- **External:** `e: 0`, `u` là đường dẫn folder/URL và `p` là filename.

Đây là hành vi được mô tả trực tiếp trong schema/assets docs. [Lottie Docs — Assets](https://lottiefiles.github.io/lottie-docs/assets/)

Trade-off:

| Cách | Ưu điểm | Rủi ro |
|---|---|---|
| Base64 trong JSON | Một file, ít lỗi thiếu asset | JSON lớn; base64 và ảnh không biến raster thành vector; khó cache/nén ảnh độc lập. |
| JSON + ảnh ngoài | JSON nhỏ, ảnh có thể tối ưu/cache riêng | Dev phải giữ đúng path và filename; dễ hỏng khi đổi folder/CDN. |
| dotLottie | Một gói nén chứa JSON và asset | Chỉ dùng khi runtime đích hỗ trợ đúng phiên bản dotLottie cần dùng. |

LottieFiles khuyên PNG cho transparency, JPEG cho ảnh không cần transparency, resize đúng kích thước, nén trước khi import và ưu tiên vector khi có thể. [LottieFiles — Image Handling Best Practices](https://help.lottiefiles.com/image-handling-best-practices-)

Trên Android, nếu dùng external image, dev cần giữ filename và cấu hình image assets folder hoặc cung cấp image động theo API của player. [Airbnb Lottie Android — Images](https://github.com/airbnb/lottie/blob/master/android.md#images)

### 4.4. Text và font

Bodymovin/lottie-web có hai chiến lược text:

- **Glyph:** chữ được chuyển thành shape; không cần font ở runtime; chỉ các ký tự dùng thực tế được nhúng vào JSON.
- **Text data:** giữ chuỗi text; runtime phải tải đúng font trước khi animation render để đo glyph đúng.

[lottie-web — Text](https://github.com/airbnb/lottie-web/wiki/Text)

Chọn glyph khi copy cố định, ít ký tự và độ giống thiết kế quan trọng. Chọn text data khi cần localization/runtime text, nhưng phải giao kèm font contract, fallback, quyền nhúng font và test chuỗi dài. Glyph không tự giải quyết localization: ký tự chưa export sẽ không xuất hiện.

## 5. Export bằng LottieFiles for After Effects

### 5.1. Vòng export đúng

1. Lưu source AEP và duplicate composition “clean export”.
2. Preview trong plugin; xem warning/indicator.
3. Export **bản gốc chưa optimize** trước.
4. Chạy Feature Checker cho đúng web/iOS/Android/player version.
5. So sánh visual với AE; nếu sai, cô lập từng layer/precomp để tìm feature gây lỗi.
6. Chỉ sau khi bản gốc pass mới xuất Optimized JSON/dotLottie.
7. Regression-test bản optimized như một artifact khác, không mặc định nó tương đương.

Plugin chính thức hỗ trợ Lottie JSON, Optimized JSON, dotLottie và Optimized dotLottie; có preview, feature checker và render graph. [LottieFiles for After Effects](https://lottiefiles.com/plugins/after-effects)

Nếu export treo, LottieFiles khuyên tạm tắt layer/tính năng không hỗ trợ, rút ngắn composition, đơn giản nested precomp/expression/effect, xóa layer ẩn hoặc không dùng, rồi bật lại từng phần để cô lập lỗi. [LottieFiles — Animation Render Stuck](https://help.lottiefiles.com/troubleshooting-animation-render-stuck-)

### 5.2. JSON hay [[dotlottie|dotLottie]]?

**Chọn JSON khi:**

- Cần tương thích rộng với player đã có trong app.
- Dev muốn diff/inspect JSON hoặc app chỉ hỗ trợ Bodymovin JSON.
- Animation thuần vector, một file và không cần theme/state machine.

**Chọn dotLottie khi:**

- Cần gói một hoặc nhiều animation cùng image/font/theme/state machine.
- Muốn một file nén, ít rủi ro thất lạc external asset.
- Dev đã xác nhận dotLottie runtime và spec version được hỗ trợ.

dotLottie là ZIP Deflate có `manifest.json`. Spec v1 dùng `animations/` và `images/`; v2 đổi sang các folder rút gọn `a/`, `i/`, thêm theme, state machine và font, đồng thời dùng `initial` để chỉ asset mở đầu. Spec chính thức khuyên v2 cho dự án mới nhưng gọi v1 là phiên bản “widely supported”. Điều này có nghĩa **không được đồng nhất “mới nhất” với “phù hợp app hiện tại”**. [dotLottie specification overview](https://www.dotlottie.io/spec/) [dotLottie v2 specification](https://dotlottie.io/spec/2.0/) [dotLottie v1 specification](https://dotlottie.io/spec/1.0/)

LottieFiles nêu dotLottie có thể đóng gói JSON, image và font. Tuy nhiên câu “backward compatible” ở trang giới thiệu không nên được hiểu là mọi Lottie player cũ đều tự đọc `.lottie`; runtime phải có năng lực giải nén/đọc manifest tương ứng. Đây là suy luận từ yêu cầu cấu trúc spec và API player, cần xác nhận với dev. [LottieFiles — Lottie and dotLottie](https://help.lottiefiles.com/what-is-lottie-and-dotlottie)

### 5.3. Tối ưu theo nguyên nhân, không chỉ theo số KB

Thứ tự ưu tiên:

1. Xóa layer, keyframe, precomp, shape và asset không dùng.
2. Giảm số vertex/path trước khi giảm frame rate.
3. Dùng parenting/reuse thay cho keyframe trùng.
4. Giới hạn vùng mask/matte; tránh mask phủ toàn canvas nếu chỉ che một vùng nhỏ.
5. Raster: crop/resize/nén theo kích thước render; không phóng ảnh nhỏ lên.
6. Kiểm tra text: glyph có thể tăng JSON; font text tạo dependency runtime.
7. Dùng optimized export hoặc dotLottie sau khi baseline pass.
8. Đo trên target device; file nhỏ hơn không tự động đồng nghĩa render nhanh hơn.

Airbnb nhấn mạnh số node, path quá lớn và path animation dày làm giảm hiệu năng; Android docs nêu mask/matte/merge path là điểm nóng. LottieFiles Optimizer giảm file size, nhưng trang sản phẩm không công bố rằng mọi trường hợp đều giữ tuyệt đối cùng output trên mọi renderer, nên cần regression QA. [lottie-web README — performance recommendations](https://github.com/airbnb/lottie-web#performance) [LottieFiles — Optimized JSON](https://help.lottiefiles.com/hc/en-us/articles/9517248780313-Downloading-an-optimized-JSON-File)

## 6. QA trước khi bàn giao

### Gate 1 — cấu trúc

- File parse được như JSON hoặc `.lottie` mở được như package hợp lệ.
- `w`, `h`, `fr`, `ip`, `op` đúng contract; duration tính lại đúng.
- Không có `assets` mồ côi hoặc path trỏ tới file thiếu.
- JSON được kiểm bằng [LAC Lottie Validator](https://lottie.github.io/validator/) hoặc schema chính thức; schema pass không có nghĩa renderer pass. [Lottie JSON Schema](https://lottie.github.io/lottie-spec/latest/specs/schema/)
- Với dotLottie: `manifest.json`, animation ID, initial asset và folder đúng spec version.

### Gate 2 — feature compatibility

- Lưu screenshot/export report từ Feature Support Checker.
- Không chỉ xem “green tổng thể”; đọc từng feature mà file thực sự dùng.
- Ghi player + version đã chọn. Nếu dev nâng/hạ version, chạy lại gate.

### Gate 3 — visual

So với AE ở tối thiểu:

- frame đầu;
- 25%, 50%, 75% timeline;
- frame cuối trước `op`;
- điểm loop nối về đầu;
- nền sáng, nền tối và checkerboard transparency;
- tỉ lệ `contain`/`cover`/resize thực tế.

Kiểm tra riêng: clipping, mask/matte, stroke cap/join, gradient, text baseline, màu/alpha, pivot, thứ tự layer và frame bị nháy.

### Gate 4 — hành vi

- Autoplay/loop/play once đúng.
- Pause/resume khi app vào background/foreground đúng yêu cầu.
- Segment/marker bắt đầu và kết thúc đúng frame.
- Speed/reverse/scrub không nhảy frame.
- Trigger hoàn thành không bắn lặp hoặc mất.
- Loading/error/fallback đã có. lottie-web cung cấp các event như `complete`, `loopComplete`, `data_ready`, `data_failed`, `loaded_images`; dotLottie web có `load`, `loadError`, `frame`, `complete`, `loop`. [lottie-web README — Events](https://github.com/airbnb/lottie-web#events) [dotLottie web — official README](https://github.com/LottieFiles/dotlottie-web)

### Gate 5 — runtime và device thật

Ma trận tối thiểu phải chứa đúng các target đã ký contract, ví dụ:

| Target | Player/renderer | OS/browser | Thiết bị | Visual | Hành vi | Perf |
|---|---|---|---|---|---|---|
| Web | lottie-web SVG `x.y.z` | Chrome/Safari hỗ trợ thấp nhất | desktop + mobile | pass/fail | pass/fail | số đo |
| iOS | Lottie iOS `x.y.z`, automatic | iOS thấp nhất | máy thấp + máy phổ biến | pass/fail | pass/fail | số đo |
| Android | Lottie Android `x.y.z` | API thấp nhất | máy thấp + máy phổ biến | pass/fail | pass/fail | số đo |

LottieFiles cho phép preview mobile qua QR và khuyên test thiết bị thật để thấy vấn đề hiệu năng/kích thước màn hình. Đây là smoke test hữu ích, nhưng app build với package/version cụ thể vẫn là acceptance cuối. [LottieFiles — Test on Mobile Devices](https://help.lottiefiles.com/hc/en-us/articles/8705456865689-QR-Code)

### Gate 6 — hiệu năng

Không đặt một ngưỡng KB/FPS chung cho mọi app. Ghi số đo theo budget dự án:

- byte tải xuống và byte sau giải nén;
- thời gian download/decode/first frame;
- frame time/FPS trên thiết bị thấp nhất;
- CPU/memory khi chạy một animation và khi chạy đồng thời theo màn hình thật;
- jank khi scroll, chuyển route hoặc main thread bận;
- cache hit/miss nếu tải remote.

Android sample app có render graph và render time per layer; iOS có thể tự đổi engine khi dùng automatic, nên ghi lại engine thực tế nếu performance là acceptance. [Airbnb Lottie Android — Render Graph](https://github.com/airbnb/lottie/blob/master/android.md#render-graph) [Lottie iOS — rendering engine](https://github.com/airbnb/lottie-ios/blob/master/Sources/Public/Configuration/RenderingEngineOption.swift)

### Gate 7 — accessibility và fallback

- Nếu chỉ trang trí: dev đánh dấu bỏ khỏi accessibility tree.
- Nếu truyền tải ý nghĩa: bàn giao text tương đương hoặc trạng thái UI không phụ thuộc riêng vào animation.
- Có static poster/end state khi animation bị tắt, lỗi tải hoặc người dùng bật reduced motion.
- Tránh loop chuyển động mạnh vô hạn nếu không cần.
- Với lottie-web SVG, `title` và `description` có thể tạo phần tử phục vụ assistive technology. [lottie-web — loadAnimation options](https://github.com/airbnb/lottie-web/wiki/loadAnimation-options)
- LottieFiles Accessibility Analyzer kiểm tra cả motion/timing, contrast và text; dùng như công cụ phát hiện, không thay thế test trong app. [LottieFiles — Accessibility Analyzer](https://help.lottiefiles.com/hc/en-us/articles/43259873084569-Lottie-Accessibility-Analyzer)

## 7. Gói bàn giao cho developer

### 7.1. Thành phần bắt buộc

```text
reward-burst/
├─ reward-burst_v1.2.0.json        # hoặc .lottie
├─ reward-burst_v1.2.0.aep         # source có thể chỉnh sửa
├─ assets/                         # chỉ khi JSON dùng external assets
├─ reward-burst_poster.png         # fallback/reference
├─ reward-burst_reference.mp4      # visual intent, không dùng làm runtime truth
├─ feature-check_v1.2.0.png        # hoặc PDF/report
└─ HANDOFF.md                      # contract dưới đây
```

Đây là **khuyến nghị vận hành suy ra từ nhu cầu truy vết**, không phải cấu trúc bắt buộc của Lottie spec.

### 7.2. Nội dung `HANDOFF.md`

```yaml
asset_id: reward-burst
release: 1.2.0
format: lottie-json        # hoặc dotlottie-v1 / dotlottie-v2
sha256: <hash-của-file-bàn-giao>
canvas: 360x360
fps: 30
in_frame: 0
out_frame: 72
duration_seconds: 2.4

target_runtime:
  web: lottie-web <exact-version> / svg
  ios: lottie-ios <exact-version> / automatic
  android: lottie-android <exact-version>

playback:
  autoplay: false
  loop: false
  trigger: reward_claimed
  completion: show_reward_total
  background_behavior: pause_and_restore

layout:
  fit: contain
  alignment: center
  transparent_background: true

segments_or_markers:
  intro: 0-18
  burst: 19-54
  settle: 55-71

runtime_overrides:
  none: true

assets:
  embedded: true
  external_files: []

fallback:
  poster: reward-burst_poster.png
  reduced_motion: final_frame

qa:
  feature_checker: pass
  web_target: pass
  ios_target: pass
  android_target: pass
  performance_budget: pass

known_limitations:
  - "Không phát đồng thời quá 6 instance trên màn hình thiết bị thấp nhất đã test."
```

`sha256`, Semantic Versioning và tên file ở đây là quy ước nhóm nên áp dụng để tránh dev lấy nhầm file; Lottie không định nghĩa release version của asset. Dùng LottieFiles Version History nếu team làm việc trên workspace: hệ thống giữ các version cũ và cho phép restore. [LottieFiles — Version History](https://help.lottiefiles.com/hc/en-us/articles/7912008974745-Upload-a-newer-animation-version-or-check-version-history)

Nếu dùng Asset CDN của LottieFiles, handoff phải pin version và có phương án khi quota/CDN lỗi. LottieFiles cho phép chọn JSON/dotLottie và version ở màn hình handoff, nhưng tài liệu cũng nói asset có thể bị vô hiệu khi vượt quota. [LottieFiles — Handoff & Embed](https://help.lottiefiles.com/hc/en-us/articles/8704650653593-handoff-embed)

### 7.3. Quy tắc version đề xuất

- Patch `1.2.0 → 1.2.1`: tối ưu size hoặc sửa sai nhỏ, không đổi canvas/timing/marker contract.
- Minor `1.2.0 → 1.3.0`: thêm marker/state/theme hoặc thay timing có tương thích ngược theo contract.
- Major `1.x → 2.0.0`: đổi format/runtime requirement, canvas semantics, marker name hoặc hành vi tích hợp.

Đây là quy ước suy luận theo Semantic Versioning, không phải field trong Lottie JSON. Không dùng field `v` của JSON làm release number.

## 8. Troubleshooting theo triệu chứng

| Triệu chứng | Nguyên nhân thường gặp | Cách cô lập/sửa |
|---|---|---|
| Đúng trong AE, sai trong app | Feature không có ở player/renderer/version đích | Chạy Feature Checker; export từng nửa layer; test lại đúng runtime. |
| Export đứng ở “rendering” | Composition quá dài/phức tạp; expression/effect/layer không hỗ trợ | Tắt layer nghi ngờ; xóa hidden/unused; đơn giản precomp; update plugin. |
| Mất ảnh | JSON dùng external asset nhưng folder/path/filename bị đổi | Kiểm tra `assets[].u`, `p`, `e`; giữ folder hoặc cấu hình `assetsPath`/imageAssetsFolder. |
| JSON quá lớn | Base64 image, glyph nhiều ký tự, quá nhiều vertex/keyframe | Crop/nén raster; cân nhắc external/dotLottie; đơn giản path; kiểm tra glyph. |
| Chữ sai font/vỡ layout | Export text data nhưng font tải trễ/khác weight; chuỗi locale dài | Load đúng font trước player; test locale; hoặc dùng glyph cho copy cố định. |
| Loop nháy một frame | Frame cuối trùng/không khớp frame đầu; contract `op` hiểu sai | So frame `op - 1` với `ip`; không coi `op` là một frame hiển thị cần lặp lại. |
| Mask/matte giật trên Android | Diện tích matte lớn hoặc nhiều mask/matte | Thu nhỏ bounds, chia shape, loại matte không cần; đo render graph. |
| iOS chạy đúng nhưng tốn CPU | Animation rơi về Main Thread vì feature không hợp Core Animation | Ghi nhận engine thực tế; đơn giản feature hoặc chấp nhận fallback có budget. |
| Web SVG đúng, Canvas sai | Renderer feature support khác nhau | Pin renderer trong contract; không đổi renderer chỉ để “thử nhanh” mà không regression test. |
| `.lottie` không load | Player chỉ nhận JSON hoặc đọc spec version khác | Xác nhận dotLottie v1/v2 và runtime package; fallback sang JSON nếu cần. |
| Runtime đổi màu/text không ổn | Dev dựa vào tên/keypath không ổn định hoặc file optimized đổi cấu trúc | Chốt slot/keypath contract trước export; test override trên chính artifact cuối. |

Với web external asset, lottie-web hỗ trợ `assetsPath` để thay root path, còn `path` và `animationData` là hai cách nạp animation khác nhau. [lottie-web — loadAnimation options](https://github.com/airbnb/lottie-web/wiki/loadAnimation-options)

## 9. Ba ví dụ thực hành tăng dần độ khó

### Ví dụ 1 — cơ bản: spinner thuần vector

**Đề bài**

Dev cần spinner 48×48, chạy web/iOS/Android, nền trong suốt, loop vô hạn. Budget nội bộ: file dưới 20 KB; không có runtime customization.

**Lời giải**

1. Chốt player/version với dev; chỉ dùng ellipse/shape, stroke, rotation/trim path đã xác nhận trên cả ba target.
2. Composition 48×48, 30 fps, 30 frame = 1 giây.
3. Một shape layer, ít vertex, không mask, effect, raster hoặc text.
4. Export original JSON; chạy Feature Checker; xem frame 0, 15, 29 và nối 29→0.
5. Export optimized JSON; so lại cùng các frame trên ba runtime.
6. Bàn giao `spinner_v1.0.0.json`, AEP, poster, contract loop/autoplay và matrix pass.

**Insight**

Spinner là trường hợp JSON đơn giản phù hợp hơn dotLottie: gói nén và manifest không tạo lợi ích rõ nếu chỉ có một animation vector rất nhỏ. Tối ưu quan trọng nhất là loop liền, không phải ép thêm vài byte.

### Ví dụ 2 — trung cấp: onboarding từ PSD/Figma có ảnh và text

**Đề bài**

Một màn onboarding 360×360 gồm nhân vật vector, ảnh avatar raster và headline cần dịch sang 8 ngôn ngữ. Web dùng lottie-web SVG; app native dùng Lottie iOS/Android. Animation play once, sau đó giữ end frame.

**Lời giải**

1. Audit layer: xin nhân vật ở SVG/AI thay vì giữ raster trong PSD; avatar được crop đúng kích thước; text không bake vào artwork.
2. Import vector theo layer, convert thành AE shape; avatar là một image asset; headline tách khỏi Lottie và để UI native render nếu có thể.
3. Nếu bắt buộc animate text trong Lottie, dùng text data và giao font/locale test contract; không dùng glyph vì 8 ngôn ngữ có tập ký tự lớn và copy thay đổi.
4. Test hai phương án asset:
   - JSON + ảnh ngoài nếu app bundle/CDN đã có quy ước asset path;
   - dotLottie nếu cả ba runtime xác nhận cùng đọc được version chọn.
5. Test nền sáng/tối, 8 locale, mạng lỗi/offline, end-frame hold, font tải chậm và thiết bị Android thấp.
6. Handoff kèm external asset manifest hoặc một `.lottie`, font contract, fallback poster và version pin.

**Insight**

Mục tiêu “một file duy nhất” có thể làm JSON phình vì base64 và glyph. Tách headline sang UI native thường tốt hơn cho localization/accessibility; dotLottie phù hợp khi cần đóng gói avatar nhưng chỉ sau khi runtime được xác nhận.

### Ví dụ 3 — nâng cao: reward animation tương tác, theme và nhiều trạng thái

**Đề bài**

GameFi app cần component reward có `idle`, `press`, `burst`, `settle`, light/dark theme và màu rarity thay đổi ở runtime. Web mới dùng dotLottie runtime hỗ trợ v2; mobile app hiện dùng Lottie JSON player cũ. Sáu card có thể xuất hiện đồng thời.

**Lời giải**

1. Không ép một artifact cho mọi nền tảng. Chia contract:
   - Web: dotLottie v2 có animation/theme/state machine nếu runtime/version đã support.
   - Mobile hiện tại: JSON riêng, marker/segment và state do app điều khiển; lên kế hoạch migrate runtime nếu giá trị đủ lớn.
2. Thiết kế shared motion grammar nhưng export hai artifact từ cùng source composition.
3. Chỉ rarity color là override; mọi property target phải có slot/keypath ổn định và được test sau optimize.
4. Giảm mask/matte, giữ bounds nhỏ; đo 1 và 6 instance cùng lúc, trên thiết bị thấp nhất.
5. Test state transition bị ngắt giữa chừng: user tap nhanh, app background, card rời viewport, mạng trả kết quả muộn.
6. Handoff manifest nêu rõ mapping event → state/marker, allowed transition, artifact theo nền tảng, runtime version, budget và fallback.

**Insight**

Độ khó không nằm ở hiệu ứng đẹp mà ở **state ownership**. Animation file mô tả motion; app vẫn phải sở hữu business state. dotLottie v2 có thể đóng gói theme/state machine, nhưng không hợp lý nếu buộc mobile player cũ nâng cấp ngoài kế hoạch. Hai artifact có chung source và contract rõ thường an toàn hơn một file “đa năng” chưa được runtime hỗ trợ.

## 10. Checklist rút gọn dùng hằng ngày

### Trước khi animate

- [ ] Có target platform, player, version và renderer.
- [ ] Có canvas/layout/playback/interactivity contract.
- [ ] Có budget file/perf và thiết bị thấp nhất.
- [ ] Layer được đặt tên, nhóm, bỏ rác; vector/raster/font đã phân loại.
- [ ] Feature rủi ro được đánh dấu và thử bằng một spike ngắn.

### Trước khi export

- [ ] Composition 1×, đúng fps/duration.
- [ ] Không có hidden/unused layer hoặc asset mồ côi.
- [ ] Expression/rig cần thiết đã bake và test.
- [ ] Mask/matte/path/raster đã tối giản.
- [ ] Text/glyph/font strategy đã chốt.

### Trước khi gửi dev

- [ ] Original artifact pass trước khi optimize.
- [ ] Optimized artifact được regression-test riêng.
- [ ] Feature Checker theo đúng library/version.
- [ ] Visual/behavior/perf pass trong app hoặc sample app dùng runtime đích.
- [ ] File, AEP, asset, poster, reference, report và `HANDOFF.md` đủ.
- [ ] Tên release/version không dùng nhầm field `v` trong JSON.
- [ ] Có fallback, reduced-motion behavior và known limitations.

## 11. Điều đã xác minh và phần còn phụ thuộc dự án

### Dữ kiện từ nguồn chính thức

- Lottie là JSON animation model; renderer/platform có feature support khác nhau.
- Lottie JSON có thể embed image bằng data URL hoặc tham chiếu file ngoài.
- Text có thể xuất thành glyph hoặc text data phụ thuộc font runtime.
- LottieFiles AE plugin xuất JSON/optimized JSON/dotLottie và có feature checker/preview.
- dotLottie v1 và v2 có cấu trúc/spec khác nhau; v2 thêm theme/state machine/font.
- Android mask/matte có thể là điểm nóng; iOS automatic có thể đổi sang Main Thread.

### Khuyến nghị/suy luận cần team xác nhận

- Cấu trúc folder, SHA-256 và SemVer trong handoff là quy ước vận hành đề xuất.
- 30 fps, ngưỡng file size, số instance và device matrix không có một giá trị đúng cho mọi app.
- Việc tách text ra UI native, chọn JSON hay dotLottie, embed hay external asset phụ thuộc localization, offline, CDN và runtime.
- LottieFiles preview/feature checker là cổng QA quan trọng nhưng build app trên target device mới là acceptance cuối.

## Liên kết

- [[lottie-animation|Lottie Animation]] — mô hình dữ liệu và cấu trúc animation được bàn giao.
- [[bodymovin|Bodymovin]] — exporter After Effects và ý nghĩa của field phiên bản `v`.
- [[lottiefiles|LottieFiles]] — bộ công cụ preview, compatibility check, tối ưu và handoff.
- [[dotlottie|dotLottie]] — lựa chọn container khi runtime và spec version đã được chốt.
- [[lottie-runtime-compatibility|Lottie Runtime Compatibility]] — acceptance gate theo platform/player/version/renderer/device.
- [[design-handoff|Design Handoff]] — cách xem animation như contract hành vi và bằng chứng, không chỉ là file hình.

## Nguồn chính thức

- [LottieFiles for After Effects](https://lottiefiles.com/plugins/after-effects)
- [LottieFiles — Supported Features](https://lottiefiles.com/supported-features)
- [LottieFiles Help — After Effects](https://help.lottiefiles.com/design-plugins)
- [Airbnb — Creating Lottie animations](https://github.com/airbnb/lottie/blob/master/after-effects.md)
- [Airbnb — Supported features across renderers](https://github.com/airbnb/lottie/blob/master/supported-features.md)
- [Airbnb — Lottie Android](https://github.com/airbnb/lottie/blob/master/android.md)
- [Airbnb — Lottie iOS source/docs](https://github.com/airbnb/lottie-ios)
- [Airbnb — lottie-web](https://github.com/airbnb/lottie-web)
- [Lottie human-readable format docs](https://lottiefiles.github.io/lottie-docs/)
- [Lottie format specification](https://lottiefiles.github.io/lottie-spec/)
- [dotLottie specification](https://www.dotlottie.io/spec/)
- [LottieFiles — dotLottie web player](https://github.com/LottieFiles/dotlottie-web)
- [Adobe — After Effects import and shape workflow](https://helpx.adobe.com/after-effects/desktop/import-files/import-still-images/preparing-importing-still-images.html)
