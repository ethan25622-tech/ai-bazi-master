# OpenClaw Mobile Quick Commands / OpenClaw 手机端快捷命令

Use this when you are away from the computer and want OpenClaw to run local
tests, then send the result back to your phone for copying into Claude/GPT.

当你不在电脑前，但想让 OpenClaw 运行本地脚本、再把结果发回手机复制到
Claude/GPT 时，可以参考这个文件。

Ask OpenClaw on your phone to run commands in this folder:

请让手机上的 OpenClaw 在项目目录里运行命令：

```powershell
cd /d "<your cloned ai-bazi-master folder>"
```

## Simplest Phone Commands / 最简单手机命令

For daily use, send short free-text commands through `m.cmd`.

日常使用可以直接通过 `m.cmd` 发短命令：

```powershell
.\m.cmd 验收
.\m.cmd 全测
.\m.cmd 提示词 1990-1-1 12:00 男 2028 事业怎么样
.\m.cmd 报告 1990-1-1 12点 男 2028年7月
.\m.cmd 回答 1990-1-1 12点 男 2028 事业怎么样
```

For Telegram copying, prefix the command with `复制` or `tg`. It will split the
output into code blocks that are easier to copy on mobile.

如果要方便 Telegram 复制，可以在命令前加 `复制` 或 `tg`，输出会被拆成更适合手机复制的代码块：

```powershell
.\m.cmd 复制 提示词 1990-1-1 12:00 男 2028 事业怎么样
.\m.cmd tg 报告 1990-1-1 12点 男 2028年7月
```

If no mode is written, `m.cmd` defaults to `提示词`, because that is usually the
most useful phone flow for copying into Claude/GPT.

如果不写模式，`m.cmd` 默认按 `提示词` 处理，因为手机端最常见的需求是复制给
Claude/GPT。

## If OpenClaw Cannot Run Shell Commands / 如果 OpenClaw 不能执行命令

If Telegram OpenClaw says it cannot execute shell commands, use the local
Telegram runner instead.

如果 Telegram 里的 OpenClaw 提示不能执行 shell 命令，可以改用本地 Telegram 机器人：

1. Create a bot with Telegram `@BotFather` and copy the bot token.
2. On the Windows computer, start PowerShell in this folder.
3. Either double-click `启动TG机器人.cmd`, or run:

1. 在 Telegram 里用 `@BotFather` 创建机器人，并复制 bot token。
2. 在 Windows 电脑上进入本项目目录，打开 PowerShell。
3. 双击 `启动TG机器人.cmd`，或运行：

```powershell
set TELEGRAM_BOT_TOKEN=123456:ABC_your_token_here
.\tg_bot.cmd
```

Then open your new Telegram bot on the phone and send:

然后在手机上打开你的 Telegram 机器人，发送：

```text
复制 1990-1-1 12:00 男 2028 事业怎么样
```

Keep the PowerShell window open while testing. The bot runs the local scripts on
this computer and sends the result back to Telegram.

测试时保持 PowerShell 窗口打开。机器人会在这台电脑上运行本地脚本，并把结果发回
Telegram。

## Full Phone Commands / 完整手机命令

Generate a GPT/Claude prompt and return it to the phone:

生成 GPT/Claude 提示词并发回手机：

```powershell
.\mobile.cmd prompt --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --question "事业怎么样"
```

Generate the prompt, return it to the phone, and also copy it on the PC:

生成提示词、发回手机，并同时复制到电脑剪贴板：

```powershell
.\mobile.cmd prompt-copy --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --question "事业怎么样"
```

Run the final project acceptance check:

运行最终项目验收：

```powershell
.\mobile.cmd status
```

Run the full validation suite:

运行完整验证：

```powershell
.\mobile.cmd validate
```

Generate the readable local report:

生成本地可读报告：

```powershell
.\mobile.cmd report --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --target-month 7
```

Ask one question and return only the local reply:

只问一个问题，并只返回本地回答：

```powershell
.\mobile.cmd reply --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --question "事业怎么样"
```

## Phone Message Template / 手机消息模板

Send this to OpenClaw from the phone:

从手机发给 OpenClaw：

```text
在 Windows PowerShell 里运行：
cd /d "<your cloned ai-bazi-master folder>"
.\mobile.cmd prompt --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --question "事业怎么样"

把完整输出原样发回给我，不要总结。
```

If the output is too long for one mobile message, ask OpenClaw to send it in
numbered chunks.

如果输出太长，让 OpenClaw 分段编号发回。
