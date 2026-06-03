# OpenClaw Mobile Quick Commands

Use this when you are away from the computer and want OpenClaw to run local
tests, then send the result back to your phone for copying into Claude/GPT.

Ask OpenClaw on your phone to run commands in this folder:

```powershell
cd /d "<your cloned ai-bazi-master folder>"
```

## Simplest Phone Commands

For daily use, send short free-text commands through `m.cmd`:

```powershell
.\m.cmd 验收
.\m.cmd 全测
.\m.cmd 提示词 1990-1-1 12:00 男 2028 事业怎么样
.\m.cmd 报告 1990-1-1 12点 男 2028年7月
.\m.cmd 回答 1990-1-1 12点 男 2028 事业怎么样
```

For Telegram copying, prefix the command with `复制` or `tg`. It will split the
output into code blocks that are easier to copy on mobile:

```powershell
.\m.cmd 复制 提示词 1990-1-1 12:00 男 2028 事业怎么样
.\m.cmd tg 报告 1990-1-1 12点 男 2028年7月
```

If no mode is written, `m.cmd` defaults to `提示词`, because that is the most
useful phone flow for copying into Claude/GPT.

## If OpenClaw Cannot Run Shell Commands

If Telegram OpenClaw says it cannot execute shell commands, use the local
Telegram runner instead.

1. Create a bot with Telegram `@BotFather` and copy the bot token.
2. On the Windows computer, start PowerShell in this folder.
3. Either double-click `启动TG机器人.cmd`, or run:

```powershell
set TELEGRAM_BOT_TOKEN=123456:ABC_your_token_here
.\tg_bot.cmd
```

Then open your new Telegram bot on the phone and send:

```text
复制 1990-1-1 12:00 男 2028 事业怎么样
```

Keep the PowerShell window open while testing. The bot runs the local scripts on
this computer and sends the result back to Telegram.

## Full Phone Commands

Generate a GPT/Claude prompt and return it to the phone:

```powershell
.\mobile.cmd prompt --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --question "事业怎么样"
```

Generate the prompt, return it to the phone, and also copy it on the PC:

```powershell
.\mobile.cmd prompt-copy --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --question "事业怎么样"
```

Run the final project acceptance check:

```powershell
.\mobile.cmd status
```

Run the full validation suite:

```powershell
.\mobile.cmd validate
```

Generate the readable local report:

```powershell
.\mobile.cmd report --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --target-month 7
```

Ask one question and return only the local reply:

```powershell
.\mobile.cmd reply --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --question "事业怎么样"
```

## Phone Message Template

Send this to OpenClaw from the phone:

```text
在 Windows PowerShell 里运行：
cd /d "<your cloned ai-bazi-master folder>"
.\mobile.cmd prompt --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender 男 --target-year 2028 --question "事业怎么样"

把完整输出原样发回给我，不要总结。
```

If the output is too long for one mobile message, ask OpenClaw to send it in
numbered chunks.
