# 上传与使用说明

这是一份针对 `takagibit18/takagibit18` 的**覆盖更新包**，不是该仓库的完整克隆。没有修改或推送任何远端文件。不要把整个包当作新仓库替换掉旧仓库；保留未提及的文件。

## 先看效果

单文件 `sean_profile_preview.html` 可保存后用浏览器打开，不需要安装 Node、Python 或 npm 依赖。它会进入醒目标注的 DEMO DATA 模式。热力图可悬浮、点击固定日期、用方向键选择日期、按 Escape 取消固定；手机可横向滑动并点按。支持暂停、重播、深浅主题、系统减少动态效果。

包内 `docs/index.html` 是正式交互页，默认使用真实数据文件；首次同步前是“等待同步”，不以 0 或模拟值冒充实际记录。也可通过页面上的 Try interaction demo 临时试用动效。

## A. 更新 GitHub 个人主页

1. 解压 ZIP，将**解压后根目录里的文件和文件夹**上传/合并到 `takagibit18/takagibit18` 的根目录。不要只上传 ZIP，也不要多套一层 `repo/` 或 `sean_profile_upload/`。
2. 覆盖 README、同名更新脚本和同名工作流；其余是新增文件。务必包括 `.github/workflows/`，否则不会自动同步数据。网页上传使用 Add file → Upload files；使用本地 Git 时，复制到已克隆的仓库，检查 `git diff` 后正常提交即可，不需要 force push。
3. 提交到 `main` 后，查看 Actions → **Update contribution rhythm**。推送相关文件会触发首次执行，也可手动 Run workflow。成功后会提交真实 JSON/JS 数据和深浅主题 SVG；之后计划每日 02:25 UTC 更新。GitHub 的定时任务可能延迟或因仓库状态被停用，因此以工作流记录和数据时间戳为准。

本包没有抓到当前真实贡献数据，所以首次运行成功前会显示 Awaiting first sync。**不能把 `demo-data.js` 改名为 `data.js` 来填充正式主页。** 正式生成器拒绝发布 `status: demo` 的数据。

默认使用 GitHub Actions 自动提供的 `GITHUB_TOKEN`，没有要求另建 PAT，也没有把 Token 放进前端。若组织策略、分支保护或 Actions 权限阻止运行/提交，请先检查工作流的实际报错，不要为了绕过限制使用宽权限 Token 或 force push。

## B. 发布真正的悬浮交互网页

**GitHub README 的动画 SVG 不是可交互网页。** 每个格子的自定义浮层运行在 `docs/index.html` 中，不能原地嵌进 README。

最省事的托管路径：

1. 仓库 Settings → Pages → Build and deployment → Source，选择 **GitHub Actions**。
2. 进入 Actions，运行 **Publish interactive activity**。等部署成功，从 Pages 设置或该工作流结果中复制实际网址。首次上传若还没开启 Pages，这个部署工作流可能失败；开启后重跑即可，不影响已成功的贡献数据更新。
3. 在 README 的 Contribution Rhythm 区，把当前指向 GitHub 原生日历的 `<a href=...>` 改成刚刚取得的真实部署网址，也可加入 README 注释中给出的 Explore day by day 文本链接。

未设置自定义域名时，预计默认项目网址是 `https://takagibit18.github.io/takagibit18/`；**这个地址在打包时未部署、未验证，不应当作现成在线页面。** 默认 README 仍链接到有效的 GitHub 主页，不提前留下未部署的死链。

本包采用 Actions 发布 Pages，而非“从 main/docs 自动构建”。原因是数据工作流使用 GITHUB_TOKEN 提交产物，其 push 通常不会启动新的 push 工作流；Pages 工作流显式监听 Update contribution rhythm 的成功完成，保证后续数据同步能够发布到网站。

另一条路径是将 `docs/` 内的文件保持相对目录结构上传到你现有静态网站的一处子目录。它不需要应用服务器、数据库或 Node 运行时。但在你自己的服务器上，GitHub Actions 更新仓库之后，不会自动更新那个服务器；需要复用你的部署流程。

## 文件作用

| 文件 | 用途 |
|---|---|
| `README.md` | GitHub 个人简介；保留原有项目、评测、经历等主体 |
| `assets/hero-night*.jpg` | 重新排版的桌面/手机顶部横幅 |
| `assets/contribution-rhythm-*.svg` | 桌面/手机、深浅主题动画；`-still` 是减少动态效果时的回退 |
| `docs/index.html`, `style.css`, `app.js` | 独立悬浮交互页 |
| `docs/contributions.json` | 正式快照、日期、次数、等级、更新时间、来源 |
| `docs/data.js` | 正式快照的浏览器可读副本，使本地打开也不依赖 fetch |
| `docs/demo-data.js` | 明确隔离的演示样例，不是你的真实记录 |
| `docs/assets/night-city.jpg` | 复用个人主页末尾原图并压缩的背景 |
| `scripts/generate_contribution_rhythm.py` | 拉取、校验、按日期重建周分组、生成全部数据与 SVG |
| `scripts/build_preview.py` | 将网站打包成无需网络资源的单文件 HTML |
| `.github/workflows/contribution-rhythm.yml` | 每日/手动更新真实数据 |
| `.github/workflows/profile-pages.yml` | 可选的 GitHub Pages 发布 |
| `tests/` | 日期、数量、空数据和演示隔离等测试 |
| `IMPLEMENTATION_STATUS.md` | 已测内容、未验证项、素材来源 |

## 数据和动效约定

- 每个格子始终对应一个日期；填充色只表示 GitHub 返回的贡献等级。动画只作用于独立边缘层，不制造或增加活动。
- API 返回的贡献数不等于纯 commit 数；不从日历总数臆造 PR/review 分项。
- 以日期重新分周，周一到周日不会因简单挪动周日造成错位。跨周、跨年、闰日均有测试。
- API 响应必须覆盖整个请求区间，逐日总和必须等于总量。缺日、重复日期或错误响应都会让同步失败，不静默补零。
- 抓取和数据校验失败，不覆盖上一次成功快照。最后一天可能未结束，展示中明确提示；网站也提示可能过期的快照。
- README 在 `<picture>` 外层处理系统减少动态效果偏好，选择 `-still.svg`。不只依赖图片内部的媒体查询。

## 可选的本地开发命令

仅查看 HTML 不需要这些命令。修改生成器/测试时可用：

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/generate_contribution_rhythm.py --render-existing
python scripts/build_preview.py --demo --output profile-preview.html
```

重新拉取真实数据在 Actions 中运行最方便。不要把 Token 写进命令文件、README 或 HTML。

## 回滚

旧 `assets/hero-art.png` 和 `assets/contribution-rhythm.png` 没有被删除。上传前保留当前 README/脚本/工作流的提交；需要回滚时 revert 本次提交即可，不改写历史。

## 平台参考

- Profile README: https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme
- Pages 发布方式: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- SVG 图片环境限制: https://developer.mozilla.org/en-US/docs/Web/SVG/Guides/SVG_as_an_image
- Actions 触发约定: https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow
