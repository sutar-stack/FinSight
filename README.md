# 💸 FinSight

> **Paste your bank SMS. Understand your money. Talk to your AI coach.**

FinSight turns the bank SMS messages already sitting on your phone into beautiful spending charts and personalised financial advice — zero bank integrations, zero manual entry, zero setup.

---

## 🧩 The Problem

Most people genuinely don't know where their money goes each month. Bank apps show raw transactions. Budgeting tools either need manual entry or complex integrations that take days to set up. Generic finance advice doesn't know *your* numbers.

FinSight solves this with the one thing every Indian smartphone already has: **bank SMS messages**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📩 **SMS Parser** | Understands 10+ Indian bank formats — HDFC, SBI, ICICI, Axis, Kotak, PNB and more |
| 🏷️ **Auto-Categoriser** | Instantly tags transactions: Food, Travel, Entertainment, Utilities, Investments… |
| 📊 **SpendLens Dashboard** | Pie and bar charts that make your spending patterns impossible to ignore |
| 🤖 **PocketCoach** | AI chat powered by Gemini 1.5 Flash — asks about *your* numbers, not generic tips |
| ⚡ **Zero Setup** | Paste SMS → get insights. No bank login, no OAuth, no waiting |

---

## 🛠️ Tech Stack

**Frontend**
- React + Vite
- Recharts for data visualisation
- Deployed on Vercel

**Backend**
- Python + Flask
- Google Gemini 1.5 Flash (AI coach)
- Deployed on Render

---

## 📁 Project Structure

```
finsight/
├── backend/
│   ├── app.py                  # Flask api and gemini setup
│   └── requirements.txt        # python dependencies
└── frontend/
    ├── src/                    # React components
    └── package.json            # node dependencies
```
