#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 CYBER ULTRA 5M - TELEGRAM BOT
🧠 Algorithm: 6-Engine Ensemble (from freeuse.html)
   • Markov Chain (1st + 2nd order)
   • Frequency (contrarian)
   • Streak Reversal
   • Alternator
   • Fibonacci Weighted
   • Pattern Memory
📊 WIN/LOSS/JACKPOT Tracking
👤 Owner: Tarek (@Tarek3o)
"""

import asyncio
import time
import requests
import os
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

try:
    from telegram import Bot
    from telegram.error import TelegramError, TimedOut, NetworkError
except ImportError:
    print("❌ python-telegram-bot not installed! Run: pip install python-telegram-bot")
    exit(1)

# ==================== কনফিগ ====================
BOT_TOKEN = "8632082751:AAEcUqV8hFs-Id0E9uL0ltvW-e6ybZkKcJ0"
CHAT_ID = "6678981102"  # Tarek (@Tarek3o)

# ✅ 5 MIN WINGO API
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_5M/GetHistoryIssuePage.json"

# Engine Accuracy Tracker (persistent)
ENGINE_STATS_FILE = "engine_stats.json"

# ==================== ওয়েব সার্ভার ====================
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"CYBER ULTRA 5M BOT is running!")
    def log_message(self, format, *args):
        pass

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

def keep_alive():
    while True:
        try:
            time.sleep(600)
            port = int(os.environ.get("PORT", 8080))
            requests.get(f"http://localhost:{port}/", timeout=5)
        except:
            pass

threading.Thread(target=keep_alive, daemon=True).start()

# ==================== বট ====================
bot = Bot(token=BOT_TOKEN)

# ==================== ENGINE ACCURACY TRACKER ====================
def load_engine_stats():
    """Load persistent engine accuracy from disk"""
    try:
        if os.path.exists(ENGINE_STATS_FILE):
            with open(ENGINE_STATS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        "markov":    {"win": 0, "loss": 0, "total": 0, "weight": 1.0},
        "frequency": {"win": 0, "loss": 0, "total": 0, "weight": 1.0},
        "streak":    {"win": 0, "loss": 0, "total": 0, "weight": 1.0},
        "alternator":{"win": 0, "loss": 0, "total": 0, "weight": 1.0},
        "fibonacci": {"win": 0, "loss": 0, "total": 0, "weight": 1.0},
        "pattern":   {"win": 0, "loss": 0, "total": 0, "weight": 1.0}
    }

def save_engine_stats(stats):
    try:
        with open(ENGINE_STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save engine stats: {e}")

def update_engine_weights(stats):
    """Adjust weights based on win rate"""
    for name, s in stats.items():
        if s["total"] >= 5:
            rate = s["win"] / s["total"]
            s["weight"] = max(0.4, min(2.0, rate * 2))
    return stats

engine_stats = load_engine_stats()

# ==================== NUMBER HELPERS ====================
def classify(n):
    return "BIG" if int(n) >= 5 else "SMALL"

def get_color_name(n):
    return "RED" if int(n) % 2 == 0 else "GREEN"

# ═══════════════════════════════════════════════════════════
# 🧠 ENGINE 1: MARKOV CHAIN (1st + 2nd order)
# ═══════════════════════════════════════════════════════════
def markov_engine(nums):
    """nums = [newest, ..., oldest]"""
    seq = nums[::-1]  # chronological
    if len(seq) < 5:
        return None
    
    trans1, trans2 = {}, {}
    for i in range(len(seq) - 1):
        cur, nxt = seq[i], seq[i+1]
        if cur not in trans1: trans1[cur] = {}
        trans1[cur][nxt] = trans1[cur].get(nxt, 0) + 1
    for i in range(len(seq) - 2):
        key = f"{seq[i]}_{seq[i+1]}"
        nxt = seq[i+2]
        if key not in trans2: trans2[key] = {}
        trans2[key][nxt] = trans2[key].get(nxt, 0) + 1
    
    last, prev = seq[-1], seq[-2]
    key2 = f"{prev}_{last}"
    
    best_num, best_score = None, 0
    if key2 in trans2:
        for n, cnt in trans2[key2].items():
            score = cnt * 2
            if score > best_score:
                best_score, best_num = score, int(n)
    if best_num is None and last in trans1:
        for n, cnt in trans1[last].items():
            if cnt > best_score:
                best_score, best_num = cnt, int(n)
    if best_num is None:
        return None
    
    return {
        "name": "markov",
        "number": best_num,
        "size": classify(best_num),
        "color": get_color_name(best_num),
        "confidence": min(85, 50 + best_score * 5)
    }

# ═══════════════════════════════════════════════════════════
# 🧠 ENGINE 2: FREQUENCY (contrarian least-picked)
# ═══════════════════════════════════════════════════════════
def frequency_engine(nums):
    recent = nums[:20]
    freq = {}
    for n in recent:
        freq[n] = freq.get(n, 0) + 1
    
    big_digits = [5, 6, 7, 8, 9]
    small_digits = [0, 1, 2, 3, 4]
    
    big_min, small_min = float('inf'), float('inf')
    big_pick, small_pick = None, None
    
    for n in big_digits:
        f = freq.get(n, 0)
        if f < big_min:
            big_min, big_pick = f, n
    for n in small_digits:
        f = freq.get(n, 0)
        if f < small_min:
            small_min, small_pick = f, n
    
    big_count = sum(1 for n in recent if n >= 5)
    small_count = len(recent) - big_count
    
    predict_big = big_count <= small_count
    pick_num = big_pick if predict_big else small_pick
    
    return {
        "name": "frequency",
        "number": pick_num,
        "size": "BIG" if predict_big else "SMALL",
        "color": get_color_name(pick_num),
        "confidence": 60 + abs(big_count - small_count) * 2
    }

# ═══════════════════════════════════════════════════════════
# 🧠 ENGINE 3: STREAK REVERSAL
# ═══════════════════════════════════════════════════════════
def streak_engine(nums):
    recent = nums[:15]
    if len(recent) < 3:
        return None
    
    streak = 1
    last_type = "B" if recent[0] >= 5 else "S"
    for i in range(1, len(recent)):
        t = "B" if recent[i] >= 5 else "S"
        if t == last_type:
            streak += 1
        else:
            break
    
    if streak >= 3:
        rev_type = "S" if last_type == "B" else "B"
        candidates = [5,6,7,8,9] if rev_type == "B" else [0,1,2,3,4]
        freq = {n: 0 for n in candidates}
        for n in recent:
            if n in freq:
                freq[n] += 1
        pick = min(candidates, key=lambda n: freq[n])
        
        return {
            "name": "streak",
            "number": pick,
            "size": "BIG" if rev_type == "B" else "SMALL",
            "color": get_color_name(pick),
            "confidence": min(88, 55 + streak * 6)
        }
    return None

# ═══════════════════════════════════════════════════════════
# 🧠 ENGINE 4: ALTERNATOR
# ═══════════════════════════════════════════════════════════
def alternator_engine(nums):
    recent = nums[:12]
    if len(recent) < 4:
        return None
    
    flips = 0
    for i in range(1, len(recent)):
        a = "B" if recent[i-1] >= 5 else "S"
        b = "B" if recent[i] >= 5 else "S"
        if a != b:
            flips += 1
    
    ratio = flips / (len(recent) - 1)
    if ratio >= 0.65:
        last_big = recent[0] >= 5
        next_side = "SMALL" if last_big else "BIG"
        candidates = [5,6,7,8,9] if next_side == "BIG" else [0,1,2,3,4]
        pick = candidates[hash(str(recent)) % len(candidates)]
        return {
            "name": "alternator",
            "number": pick,
            "size": next_side,
            "color": get_color_name(pick),
            "confidence": 62 + round(ratio * 20)
        }
    return None

# ═══════════════════════════════════════════════════════════
# 🧠 ENGINE 5: FIBONACCI WEIGHTED
# ═══════════════════════════════════════════════════════════
def fibonacci_engine(nums):
    recent = nums[:10]
    if len(recent) < 3:
        return None
    
    fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    weighted = {}
    for i in range(min(10, len(recent))):
        weighted[i] = weighted.get(i, 0) + fib[i] * recent[i]
    
    # Pick LEAST weighted number
    least_num, least_w = None, float('inf')
    for d, w in weighted.items():
        if w < least_w:
            least_w, least_num = w, int(d)
    
    pick = least_num
    return {
        "name": "fibonacci",
        "number": pick,
        "size": classify(pick),
        "color": get_color_name(pick),
        "confidence": 58
    }

# ═══════════════════════════════════════════════════════════
# 🧠 ENGINE 6: PATTERN MEMORY
# ═══════════════════════════════════════════════════════════
def pattern_engine(nums):
    recent = nums[:15]
    if len(recent) < 8:
        return None
    
    types = ["B" if n >= 5 else "S" for n in recent]
    
    for length in range(5, 1, -1):
        key = "".join(types[:length])
        matches = {}
        for i in range(1, len(recent) - length - 1):
            sub = "".join(types[i:i+length])
            if sub == key:
                next_t = types[i-1]
                matches[next_t] = matches.get(next_t, 0) + 1
        
        best_t, best_c = None, 0
        for t, c in matches.items():
            if c > best_c:
                best_c, best_t = c, t
        
        if best_t and best_c >= 2:
            candidates = [5,6,7,8,9] if best_t == "B" else [0,1,2,3,4]
            pick = candidates[hash(key) % len(candidates)]
            return {
                "name": "pattern",
                "number": pick,
                "size": "BIG" if best_t == "B" else "SMALL",
                "color": get_color_name(pick),
                "confidence": 62 + best_c * 4
            }
    return None

# ═══════════════════════════════════════════════════════════
# 🎯 MASTER ENSEMBLE — Weighted Voting
# ═══════════════════════════════════════════════════════════
def master_predict(nums):
    """6-engine weighted ensemble prediction"""
    global engine_stats
    
    engines = [
        markov_engine(nums),
        frequency_engine(nums),
        streak_engine(nums),
        alternator_engine(nums),
        fibonacci_engine(nums),
        pattern_engine(nums)
    ]
    engines = [e for e in engines if e is not None]
    
    if not engines:
        pick = nums[0] if nums else 5
        return {
            "size": classify(pick),
            "number": pick,
            "color": get_color_name(pick),
            "confidence": 50,
            "engines_used": 0,
            "engine_votes": {}
        }
    
    # Save votes for accuracy tracking
    last_votes = {e["name"]: e for e in engines}
    
    # Weighted voting
    big_score, small_score = 0, 0
    big_votes, small_votes = {}, {}
    
    for e in engines:
        w = engine_stats[e["name"]]["weight"] if e["name"] in engine_stats else 1.0
        conf = e["confidence"] / 100
        weight = w * conf
        
        if e["size"] == "BIG":
            big_score += weight
            big_votes[e["number"]] = big_votes.get(e["number"], 0) + weight
        else:
            small_score += weight
            small_votes[e["number"]] = small_votes.get(e["number"], 0) + weight
    
    is_big = big_score >= small_score
    total_score = big_score + small_score
    confidence = round((max(big_score, small_score) / total_score) * 100) if total_score > 0 else 50
    
    votes = big_votes if is_big else small_votes
    if votes:
        best_num = max(votes, key=votes.get)
    else:
        candidates = [5,6,7,8,9] if is_big else [0,1,2,3,4]
        best_num = candidates[hash(str(nums)) % len(candidates)]
    
    return {
        "size": "BIG" if is_big else "SMALL",
        "number": best_num,
        "color": get_color_name(best_num),
        "confidence": min(97, confidence),
        "engines_used": len(engines),
        "engine_names": [e["name"] for e in engines],
        "engine_votes": last_votes
    }

def update_engine_accuracy(actual_num, last_votes):
    """After result, update each engine's win/loss"""
    global engine_stats
    
    actual_size = classify(actual_num)
    for name, vote in last_votes.items():
        if name not in engine_stats:
            engine_stats[name] = {"win": 0, "loss": 0, "total": 0, "weight": 1.0}
        is_win = (vote["size"] == actual_size)
        engine_stats[name]["total"] += 1
        if is_win:
            engine_stats[name]["win"] += 1
        else:
            engine_stats[name]["loss"] += 1
    
    engine_stats = update_engine_weights(engine_stats)
    save_engine_stats(engine_stats)

# ==================== ডেটা ট্র্যাকিং ====================
total_wins = 0
total_losses = 0
total_jackpots = 0
total_rounds = 0
current_streak = 0
best_win_streak = 0
worst_loss_streak = 0

hourly_wins = 0
hourly_losses = 0
hourly_rounds = 0
hourly_best_win_streak = 0
hourly_worst_loss_streak = 0

last_predicted_period = None
last_predicted_signal = None
last_predicted_num = None
last_engine_votes = {}
prediction_sent_for_period = {}
last_result_sent = False

# ==================== API ====================
def fetch_api_data():
    try:
        url = API_URL + "?t=" + str(int(time.time() * 1000))
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("data", {}).get("list", [])
    except Exception as e:
        print(f"API Error: {e}")
    return []

# ==================== Telegram সেন্ড ====================
async def send_message(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        return True
    except Exception as e:
        print(f"Send error: {e}")
        return False

# ==================== হাওয়ারলি রিপোর্ট ====================
async def send_hourly_report():
    global hourly_wins, hourly_losses, hourly_rounds
    global hourly_best_win_streak, hourly_worst_loss_streak
    global total_wins, total_losses, total_rounds, total_jackpots
    global best_win_streak, worst_loss_streak
    
    if hourly_rounds == 0:
        return
    
    hourly_win_rate = (hourly_wins / hourly_rounds * 100) if hourly_rounds > 0 else 0
    total_win_rate = (total_wins / total_rounds * 100) if total_rounds > 0 else 0
    
    # Top engines
    top_engines = sorted(
        engine_stats.items(),
        key=lambda x: x[1]["win"] / max(1, x[1]["total"]),
        reverse=True
    )[:3]
    engine_info = "\n".join([
        f"  • {name.upper()}: `{s['win']}/{s['total']}` ({round(s['win']/max(1,s['total'])*100)}%)"
        for name, s in top_engines if s["total"] > 0
    ]) or "  • Not enough data yet"
    
    report_msg = (
        f"📊 *HOURLY REPORT - CYBER ULTRA 5M*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 *TIME:* {datetime.now().strftime('%I:%M %p')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 *HOURLY ROUNDS:* `{hourly_rounds}`\n"
        f"✅ *HOURLY WINS:* `{hourly_wins}`\n"
        f"❌ *HOURLY LOSSES:* `{hourly_losses}`\n"
        f"📈 *HOURLY WIN RATE:* `{hourly_win_rate:.1f}%`\n"
        f"🔥 *BEST WIN STREAK:* `{hourly_best_win_streak}x`\n"
        f"📉 *WORST LOSS STREAK:* `{hourly_worst_loss_streak}x`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *TOTAL ROUNDS:* `{total_rounds}`\n"
        f"✅ *TOTAL WINS:* `{total_wins}`\n"
        f"❌ *TOTAL LOSSES:* `{total_losses}`\n"
        f"💎 *JACKPOTS:* `{total_jackpots}`\n"
        f"📈 *TOTAL WIN RATE:* `{total_win_rate:.1f}%`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 *TOP ENGINES:*\n{engine_info}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Owner: @Tarek3o\n"
        f"⚡ CYBER ULTRA 5M BOT"
    )
    
    await send_message(report_msg)
    
    hourly_wins = 0
    hourly_losses = 0
    hourly_rounds = 0
    hourly_best_win_streak = 0
    hourly_worst_loss_streak = 0

# ==================== মেইন লুপ ====================
async def prediction_bot():
    global total_wins, total_losses, total_jackpots, total_rounds
    global hourly_wins, hourly_losses, hourly_rounds
    global hourly_best_win_streak, hourly_worst_loss_streak
    global current_streak, best_win_streak, worst_loss_streak
    global last_predicted_period, last_predicted_signal, last_predicted_num
    global prediction_sent_for_period, last_result_sent, last_engine_votes

    print("🔥 CYBER ULTRA 5M BOT STARTED...")
    print(f"👤 Owner: Tarek (@Tarek3o) | Chat ID: {CHAT_ID}")
    print("🧠 Algorithm: 6-Engine Ensemble")
    print("📡 MODE: 5 MIN WINGO")

    await send_message(
        "🔥 *CYBER ULTRA 5M BOT* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *OWNER:* Tarek (@Tarek3o)\n"
        "🧠 *ALGORITHM:* 6-Engine Ensemble\n"
        "  • Markov Chain (1st+2nd)\n"
        "  • Frequency (contrarian)\n"
        "  • Streak Reversal\n"
        "  • Alternator\n"
        "  • Fibonacci Weighted\n"
        "  • Pattern Memory\n"
        "📡 *MODE:* 5 MIN WINGO\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ WAITING FOR FIRST SIGNAL...\n"
        "⚡ BOT ONLINE ✅"
    )

    last_hour_time = time.time()

    while True:
        try:
            # ✅ 5 MIN = 300 সেকেন্ড
            current_sec = int(time.time()) % 300
            sleep_time = 300 - current_sec + 5
            print(f"⏳ অপেক্ষা {sleep_time} সেকেন্ড...")
            await asyncio.sleep(sleep_time)

            raw_list = fetch_api_data()
            if not raw_list:
                print("⚠️ API ডেটা নেই")
                continue

            history_numbers = []
            for h in raw_list[:30]:
                history_numbers.append(int(h['number']))
            
            latest_issue = str(raw_list[0]['issueNumber'])
            actual_num = int(raw_list[0]['number'])
            actual_type = classify(actual_num)

            print(f"📡 PERIOD: {latest_issue}, NUMBER: {actual_num}")

            # ==================== RESULT CHECK ====================
            if last_predicted_period == latest_issue and last_predicted_signal is not None and not last_result_sent:
                is_win = (last_predicted_signal == actual_type)
                is_jackpot = (last_predicted_num == actual_num)
                
                if is_jackpot:
                    total_jackpots += 1
                    total_wins += 1
                    hourly_wins += 1
                    status = "💎 JACKPOT"
                    current_streak = current_streak + 1 if current_streak >= 0 else 1
                elif is_win:
                    total_wins += 1
                    hourly_wins += 1
                    status = "✅ WIN"
                    current_streak = current_streak + 1 if current_streak >= 0 else 1
                else:
                    total_losses += 1
                    hourly_losses += 1
                    status = "❌ LOSS"
                    current_streak = current_streak - 1 if current_streak <= 0 else -1
                
                # Update streaks
                if current_streak > best_win_streak: best_win_streak = current_streak
                if current_streak > hourly_best_win_streak: hourly_best_win_streak = current_streak
                if current_streak < 0:
                    if abs(current_streak) > worst_loss_streak: worst_loss_streak = abs(current_streak)
                    if abs(current_streak) > hourly_worst_loss_streak: hourly_worst_loss_streak = abs(current_streak)
                
                total_rounds += 1
                hourly_rounds += 1
                
                # Update engine accuracy
                if last_engine_votes:
                    update_engine_accuracy(actual_num, last_engine_votes)
                
                total_win_rate = (total_wins / total_rounds * 100) if total_rounds > 0 else 0
                streak_emoji = "🔥" if current_streak > 0 else "📉" if current_streak < 0 else "⏸️"
                
                result_msg = (
                    f"🎯 *RESULT UPDATE*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 PERIOD: `#{latest_issue[-5:]}`\n"
                    f"🎯 PREDICTED: `{last_predicted_signal}` → `{last_predicted_num}`\n"
                    f"🎰 ACTUAL: `{actual_num}` (`{actual_type}`)\n"
                    f"📌 RESULT: `{status}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 WIN RATE: `{total_win_rate:.1f}%` ({total_wins}W/{total_losses}L)\n"
                    f"💎 JACKPOTS: `{total_jackpots}`\n"
                    f"{streak_emoji} STREAK: `{current_streak:+d}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ CYBER ULTRA 5M BOT"
                )
                
                await send_message(result_msg)
                last_result_sent = True
                print(f"📊 Result: {status}")
                
                last_predicted_period = None
                last_predicted_signal = None
                last_predicted_num = None
                last_engine_votes = {}
                
                if time.time() - last_hour_time >= 3600:
                    await send_hourly_report()
                    last_hour_time = time.time()

            # ==================== NEW PREDICTION ====================
            next_period = str(int(latest_issue) + 1)
            
            if not prediction_sent_for_period.get(next_period, False):
                pred = master_predict(history_numbers)
                
                if pred:
                    last_engine_votes = pred.get("engine_votes", {})
                    streak_emoji = "🔥" if current_streak > 0 else "📉" if current_streak < 0 else "⏸️"
                    
                    engine_list = ", ".join(pred.get("engine_names", []))
                    
                    prediction_msg = (
                        f"🔥 *CYBER ULTRA 5M PREDICTION* 🔥\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 PERIOD: `#{next_period[-5:]}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 PREDICTION: `{pred['size']}`\n"
                        f"🔢 TARGET NUMBER: `{pred['number']}`\n"
                        f"🎨 COLOR: `{pred['color']}`\n"
                        f"📊 CONFIDENCE: `{pred['confidence']}%`\n"
                        f"🧠 ENGINES: `{pred['engines_used']}/6`\n"
                        f"⚙️ Active: _{engine_list}_\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"{streak_emoji} STREAK: `{current_streak:+d}`\n"
                        f"📈 WIN RATE: `{(total_wins/total_rounds*100) if total_rounds > 0 else 0:.1f}%`\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"⏳ RESULT AWAITING...\n"
                        f"⚡ CYBER ULTRA 5M BOT"
                    )
                    
                    last_predicted_period = next_period
                    last_predicted_signal = pred['size']
                    last_predicted_num = pred['number']
                    prediction_sent_for_period[next_period] = True
                    last_result_sent = False
                    
                    await send_message(prediction_msg)
                    print(f"✅ Prediction: {next_period} → {pred['size']} ({pred['number']}) [{pred['engines_used']} engines]")
                    
                    if len(prediction_sent_for_period) > 10:
                        oldest = min(prediction_sent_for_period.keys())
                        del prediction_sent_for_period[oldest]

        except Exception as e:
            print(f"❌ Loop Error: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(5)

# ==================== স্টার্ট ====================
if __name__ == '__main__':
    print("🔥 CYBER ULTRA 5M BOT")
    print("━━━━━━━━━━━━━━━━━━━━")
    print(f"👤 Owner: Tarek (@Tarek3o)")
    print(f"🆔 Chat ID: {CHAT_ID}")
    print("🧠 6-Engine Ensemble (from freeuse.html)")
    print("📡 MODE: 5 MIN WINGO")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    try:
        asyncio.run(prediction_bot())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
