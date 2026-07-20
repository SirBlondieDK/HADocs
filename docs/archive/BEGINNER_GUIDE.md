# HADocs Beginner Guide

This guide is for people who are not technical.

The goal is simple:

> Start HADocs, connect it to Home Assistant, and open your report.

No coding knowledge is needed.

---

## What is HADocs?

HADocs looks at your Home Assistant setup and makes an easy report.

It helps answer questions like:

- Are any devices offline?
- What should I fix first?
- Which integrations have problems?
- Why is my smart home health score lower?
- What devices are missing rooms?

HADocs does **not** change anything in Home Assistant.

It only looks and writes a local report.

---

## What you need

You need:

1. A computer.
2. Python installed.
3. Home Assistant running.
4. A Home Assistant Long-Lived Access Token.

Do not worry if that sounds complicated. The steps below explain it.

---

# Step 1 - Download HADocs

Go to the HADocs GitHub page.

Click the green button:

```text
Code
```

Then click:

```text
Download ZIP
```

Unzip the folder somewhere easy, for example:

```text
C:\HomeAssistantDocs
```

---

# Step 2 - Open PowerShell

Open the HADocs folder.

Click in the address bar at the top of the folder window.

Type:

```text
powershell
```

Press Enter.

A blue/black window opens.

---

# Step 3 - Install what HADocs needs

Copy this command:

```powershell
py -3.14 -m pip install -r requirements.txt
```

Paste it into PowerShell.

Press Enter.

Wait until it finishes.

If it says something about already installed, that is okay.

---

# Step 4 - Test HADocs

Copy this command:

```powershell
py -3.14 -m pytest
```

Press Enter.

You want to see something like:

```text
passed
```

If you see a warning, that is usually okay.

If you see a big red error, copy the error and ask for help.

---

# Step 5 - Create a Home Assistant token

Open Home Assistant in your browser.

Click your profile picture/name in the bottom left.

Scroll down to:

```text
Long-Lived Access Tokens
```

Click:

```text
Create Token
```

Name it:

```text
HADocs
```

Copy the token.

Important:

You only see this token once.

Do not share it publicly.

---

# Step 6 - Start HADocs

In PowerShell, run:

```powershell
py -3.14 main.py
```

HADocs opens.

Fill in:

## Home Assistant URL

Example:

```text
http://homeassistant.local:8123
```

or your local IP, for example:

```text
http://192.168.68.129:8123
```

## Token

Paste the token from Home Assistant.

## Project name

Example:

```text
My Smart Home
```

Click:

```text
Generate documentation
```

---

# Step 7 - Open your report

When HADocs is finished, open:

```text
output/index.html
```

This is your main dashboard.

Start with:

1. Health Score
2. Main Root Cause
3. Fix These First
4. Root Causes
5. Maintenance

---

## What the numbers mean

## Health Score

A score from 0 to 100.

Higher is better.

Example:

```text
67/100
```

means:

Your smart home works, but some things need attention.

## Potential Score

This is what HADocs thinks your score could become after fixing the top issues.

Example:

```text
67 -> 85
```

## Repair Time

This is only an estimate.

Example:

```text
37 minutes
```

It does not mean exactly 37 minutes.

It means the fixes are probably not huge.

---

## What should I fix first?

Look for:

```text
Fix these first
```

Start with the first item.

HADocs tries to put the most important problems at the top.

Example:

```text
Mobile App devices
3 devices appear offline
```

This usually means:

Open the Home Assistant app on those phones/tablets and make sure it connects.

---

## What not to worry about

You do not need to understand:

- Python code
- Git
- JSON
- entities
- integration internals
- developer tools

Start with the dashboard.

Fix one thing at a time.

---

## Is HADocs safe?

Yes.

HADocs is read-only.

It does not:

- turn lights on or off
- change automations
- delete anything
- edit Home Assistant
- send your data to the cloud
- call AI services

Everything is local.

---

## Common problems

### PowerShell says Python was not found

Install Python from:

```text
python.org
```

Then restart PowerShell.

### HADocs cannot connect to Home Assistant

Check:

- Is Home Assistant running?
- Is the URL correct?
- Does the URL include `http://` or `https://`?
- Is the token copied correctly?

### The report looks scary

Do not panic.

Home Assistant can have many entities per device.

One offline phone can create 50+ unavailable entities.

That is why HADocs groups problems into root causes.

### I see many Mobile App problems

Open the Home Assistant Companion App on the affected phone/tablet.

Make sure it is connected to Wi-Fi and can reach Home Assistant.

### I see MQTT or Zigbee2MQTT problems

Check:

- Mosquitto broker
- Zigbee2MQTT
- Zigbee coordinator
- powered Zigbee devices

---

## The simplest possible workflow

```text
1. Run HADocs
2. Open output/index.html
3. Read "Fix these first"
4. Fix the first thing
5. Run HADocs again
6. See if the score improves
```

That is it.

---

## Ask for help

When asking for help, share:

- screenshot of the dashboard
- the first 3 root causes
- your Home Assistant URL type, not your token
- any error message

Never share your token.
