import pytz
from googletrans import Translator
from highrise import BaseBot, __main__
from highrise.models import *
from highrise.models import GetMessagesRequest
from asyncio import run as arun
try:
    from highrise.webapi import WebAPI as WebApi
except ImportError:
    try:
        from highrise.webapi import WebApi
    except ImportError:
        WebApi = None



def getclothes(category):
    """Returns clothing items based on category"""
    clothes_data = {
        'help': "Available categories: hair (eq h), top (eq t), pant (eq p), skirt (eq s), shoe (eq sh), back hair (eq b)",
        'hair': "Front hair options available - use eq b for back hair",
        'top': "Shirt/top clothing items",
        'pant': "Pants and bottom wear",
        'skirt': "Skirt options", 
        'shoe': "Footwear options"
    }
    return clothes_data.get(category, "Category not found")

from flask import Flask, jsonify, render_template_string, request
from threading import Thread
from highrise.__main__ import main, BotDefinition
from emotes import *
import random
import asyncio
import time
from datetime import datetime, timedelta
import importlib
import json
import os

app = Flask(__name__)
bot_instance = None  # مرجع لمثيل البوت

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/keep-alive')
def keep_alive():
    return "alive", 200

@app.route('/')
def home():
    return render_template_string("""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Highrise Bot - لوحة التحكم</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --primary: #7c3aed; --primary-dark: #5b21b6; --bg: #0f0f1a; --card-bg: #1a1a2e; --card-border: #2d2d4e; --text: #e2e8f0; --muted: #94a3b8; --accent: #a78bfa; }
        * { box-sizing: border-box; }
        body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #4c1d95, #7c3aed, #a78bfa); padding: 50px 0 40px; text-align: center; position: relative; overflow: hidden; }
        .header::before { content: ''; position: absolute; inset: 0; background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"); }
        .header h1 { font-size: 2.2rem; font-weight: 800; letter-spacing: 1px; text-shadow: 0 2px 10px rgba(0,0,0,0.3); }
        .header p { color: rgba(255,255,255,0.8); font-size: 1.05rem; }
        .stat-badge { background: rgba(255,255,255,0.15); border-radius: 50px; padding: 6px 20px; display: inline-block; margin: 4px; font-size: 0.9rem; backdrop-filter: blur(5px); }
        .nav-tabs-custom { background: var(--card-bg); border-bottom: 1px solid var(--card-border); padding: 0 20px; display: flex; gap: 5px; overflow-x: auto; }
        .nav-tabs-custom button { background: none; border: none; color: var(--muted); padding: 14px 22px; cursor: pointer; font-size: 0.95rem; border-bottom: 3px solid transparent; white-space: nowrap; transition: all 0.2s; }
        .nav-tabs-custom button:hover { color: var(--accent); }
        .nav-tabs-custom button.active { color: var(--accent); border-bottom-color: var(--accent); }
        .tab-content-custom { display: none; }
        .tab-content-custom.active { display: block; }
        .container-main { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
        .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px; padding: 24px; margin-bottom: 20px; }
        .card h5 { color: var(--accent); margin-bottom: 16px; font-weight: 700; font-size: 1rem; text-transform: uppercase; letter-spacing: 0.5px; }
        .cmd-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
        .cmd-item { background: rgba(124,58,237,0.08); border: 1px solid rgba(124,58,237,0.2); border-radius: 12px; padding: 14px 16px; display: flex; flex-direction: column; gap: 4px; transition: all 0.2s; }
        .cmd-item:hover { background: rgba(124,58,237,0.15); border-color: rgba(124,58,237,0.4); transform: translateY(-1px); }
        .cmd-name { font-family: monospace; font-size: 1rem; font-weight: 700; color: #c4b5fd; direction: ltr; text-align: left; }
        .cmd-desc { font-size: 0.85rem; color: var(--muted); }
        .cmd-tag { display: inline-block; background: rgba(124,58,237,0.3); color: #ddd6fe; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; margin-top: 4px; width: fit-content; }
        .stat-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px; padding: 20px; text-align: center; }
        .stat-num { font-size: 2rem; font-weight: 800; color: var(--accent); }
        .stat-label { color: var(--muted); font-size: 0.85rem; margin-top: 4px; }
        .form-control, .form-select { background: #0f0f1a; border: 1px solid var(--card-border); color: var(--text); border-radius: 10px; padding: 10px 14px; }
        .form-control:focus, .form-select:focus { background: #0f0f1a; border-color: var(--primary); color: var(--text); box-shadow: 0 0 0 3px rgba(124,58,237,0.2); }
        .form-select option { background: #1a1a2e; }
        .btn-primary-custom { background: linear-gradient(135deg, var(--primary), var(--accent)); border: none; color: white; border-radius: 10px; padding: 10px 20px; font-weight: 600; cursor: pointer; width: 100%; transition: all 0.2s; }
        .btn-primary-custom:hover { opacity: 0.9; transform: translateY(-1px); }
        .online-dot { width: 10px; height: 10px; background: #22c55e; border-radius: 50%; display: inline-block; margin-left: 6px; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .section-header { font-size: 1.3rem; font-weight: 700; color: var(--text); margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--card-border); }
        .badge-admin { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; }
        .badge-vip { background: rgba(234,179,8,0.2); color: #fde047; border: 1px solid rgba(234,179,8,0.3); border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; }
        .badge-all { background: rgba(34,197,94,0.2); color: #86efac; border: 1px solid rgba(34,197,94,0.3); border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; }
        .badge-owner { background: rgba(251,191,36,0.2); color: #fcd34d; border: 1px solid rgba(251,191,36,0.4); border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; }
        ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: var(--bg); } ::-webkit-scrollbar-thumb { background: var(--card-border); border-radius: 3px; }
        .search-box { background: rgba(124,58,237,0.08); border: 1px solid rgba(124,58,237,0.3); border-radius: 12px; padding: 10px 16px; color: var(--text); width: 100%; margin-bottom: 20px; font-size: 0.95rem; }
        .search-box:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(124,58,237,0.2); }
        .no-results { text-align: center; color: var(--muted); padding: 40px; }
        .ctrl-section-title { font-size: 1rem; font-weight: 700; color: var(--accent); margin: 24px 0 12px; padding-right: 12px; border-right: 3px solid var(--accent); }
        .ctrl-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 8px; }
        .ctrl-card h5 { color: var(--text); font-size: 0.9rem; }
        .ctrl-btn { width: 100%; background: linear-gradient(135deg, var(--primary), var(--accent)); border: none; color: white; border-radius: 10px; padding: 10px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-size: 0.9rem; }
        .ctrl-btn:hover { opacity: 0.88; transform: translateY(-1px); }
        .ctrl-btn-danger { background: linear-gradient(135deg, #dc2626, #ef4444) !important; }
        .ctrl-btn-warning { background: linear-gradient(135deg, #d97706, #f59e0b) !important; }
        .ctrl-btn-success { background: linear-gradient(135deg, #16a34a, #22c55e) !important; }
        .ctrl-btn-sm { background: rgba(124,58,237,0.2); border: 1px solid rgba(124,58,237,0.4); color: var(--text); border-radius: 8px; padding: 7px 14px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; width: 100%; }
        .ctrl-btn-sm:hover { background: rgba(124,58,237,0.35); }
        .ctrl-status { font-size: 0.8rem; text-align: center; min-height: 20px; margin-top: 8px; }
    </style>
</head>
<body>

<div class="header">
    <h1>🤖 Highrise Bot</h1>
    <p>لوحة تحكم البوت الذكي</p>
    <div style="margin-top:12px">
        <span class="stat-badge"><span class="online-dot"></span> البوت متصل</span>
        <span class="stat-badge">👑 @_king_man_1</span>
        <span class="stat-badge" id="hdr-points">⭐ ...</span>
        <span class="stat-badge" id="hdr-vip">💎 ...</span>
    </div>
</div>

<div class="nav-tabs-custom">
    <button class="active" onclick="switchTab('commands')">📋 الأوامر</button>
    <button onclick="switchTab('control')">🎛️ التحكم</button>
    <button onclick="switchTab('outfits')">👗 الملابس المحفوظة</button>
    <button onclick="switchTab('stats')">📊 الإحصائيات</button>
</div>

<!-- تبويب الأوامر -->
<div id="tab-commands" class="tab-content-custom active">
<div class="container-main">

    <input type="text" class="search-box" id="searchBox" placeholder="🔍 ابحث عن أمر..." oninput="filterCommands()">

    <!-- أوامر الجميع -->
    <div class="card cmd-section">
        <h5>🟢 أوامر الجميع</h5>
        <div class="cmd-grid" id="grid-all">
            <div class="cmd-item" data-search="نام sleep نوم sleep2 رقص dance حركات emotes">
                <span class="cmd-name">نام / sleep</span>
                <span class="cmd-desc">حركة نوم (الشخصية تنام على الأرض)</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="نام @username sleep @">
                <span class="cmd-name">نام @username</span>
                <span class="cmd-desc">تنويم مستخدم آخر في الغرفة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="نوم sleep2">
                <span class="cmd-name">نوم / sleep2</span>
                <span class="cmd-desc">حركة نوم ثانية (وضعية مختلفة)</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="نوم @username sleep2 @">
                <span class="cmd-name">نوم @username</span>
                <span class="cmd-desc">تطبيق حركة النوم الثانية على مستخدم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="جوست ghost حركة">
                <span class="cmd-name">جوست / ghost</span>
                <span class="cmd-desc">حركة الشبح</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="بوسه بوسة kiss بوس">
                <span class="cmd-name">بوسه / kiss</span>
                <span class="cmd-desc">حركة إرسال بوسة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="خجول خجل shy">
                <span class="cmd-name">خجول / خجل / shy</span>
                <span class="cmd-desc">حركة الخجل</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تس تسس snake">
                <span class="cmd-name">تس / تسس</span>
                <span class="cmd-desc">حركة الأفعى</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تس @username تسس @">
                <span class="cmd-name">تس @username</span>
                <span class="cmd-desc">تطبيق حركة الأفعى على مستخدم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="ضفدع frog">
                <span class="cmd-name">ضفدع</span>
                <span class="cmd-desc">حركة الضفدع</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="ضفدع @username">
                <span class="cmd-name">ضفدع @username</span>
                <span class="cmd-desc">تطبيق حركة الضفدع على مستخدم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="رقصني dance رقص">
                <span class="cmd-name">رقصني [رقم]</span>
                <span class="cmd-desc">رقصة بحسب الرقم المحدد</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="ارقص dance">
                <span class="cmd-name">ارقص</span>
                <span class="cmd-desc">رقصة عامة للشخصية</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="floss forever فلوس فور ايفر">
                <span class="cmd-name">floss forever / فلوس فور ايفر</span>
                <span class="cmd-desc">رقصة Floss بشكل مستمر</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="dance floor دانس فلور">
                <span class="cmd-name">dance floor / دانس فلور</span>
                <span class="cmd-desc">رقصة Dance Floor المستمرة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="0 stop توقف ايقاف">
                <span class="cmd-name">0 / stop / توقف</span>
                <span class="cmd-desc">إيقاف الحركة الحالية</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="وقف ارقص ايقاف ارقص stop dance">
                <span class="cmd-name">وقف ارقص / ايقاف ارقص</span>
                <span class="cmd-desc">إيقاف الرقص المستمر</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="ترجمة translate">
                <span class="cmd-name">ترجمة [نص]</span>
                <span class="cmd-desc">ترجمة نص إلى العربية</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="مكانك run position">
                <span class="cmd-name">مكانك؟ / run</span>
                <span class="cmd-desc">معرفة موقعك الحالي في الغرفة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تابع follow @username">
                <span class="cmd-name">تابع @username</span>
                <span class="cmd-desc">جعل البوت يتابع مستخدماً بشكل مستمر</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="وقف تابع stop follow ايقاف متابعة">
                <span class="cmd-name">وقف تابع / ايقاف تابع</span>
                <span class="cmd-desc">إيقاف متابعة المستخدم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="نقاط @username points other user">
                <span class="cmd-name">نقاط @username</span>
                <span class="cmd-desc">عرض نقاط مستخدم آخر في الغرفة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="رسالة خاصة whisper private message DM">
                <span class="cmd-name">رسالة @username [نص]</span>
                <span class="cmd-desc">إرسال رسالة خاصة لمستخدم في الغرفة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="جرب emote try test">
                <span class="cmd-name">جرب [رقم/اسم]</span>
                <span class="cmd-desc">تجربة حركة بالرقم أو الاسم مباشرة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضحك laugh lol emote">
                <span class="cmd-name">اضحك / ضحك</span>
                <span class="cmd-desc">حركة الضحك</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="صفق clap applause تصفيق">
                <span class="cmd-name">صفق / تصفيق</span>
                <span class="cmd-desc">حركة التصفيق</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="رد greet wave تحية">
                <span class="cmd-name">رد / سلم</span>
                <span class="cmd-desc">حركة التحية والترحيب</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
        </div>
    </div>

    <!-- أوامر الملابس -->
    <div class="card cmd-section">
        <h5>👗 أوامر الملابس</h5>
        <div class="cmd-grid" id="grid-clothes">
            <div class="cmd-item" data-search="!equip @username نسخ ملابس">
                <span class="cmd-name">!equip @username</span>
                <span class="cmd-desc">نسخ ملابس مستخدم (حتى لو خارج الغرفة)</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="!equip item_id ارتداء قطعة">
                <span class="cmd-name">!equip [item_id]</span>
                <span class="cmd-desc">ارتداء قطعة ملابس بمعرفها</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف item اضافة">
                <span class="cmd-name">اضف [item_id]</span>
                <span class="cmd-desc">إضافة قطعة ملابس للمظهر</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اخلع item خلع">
                <span class="cmd-name">اخلع [item_id]</span>
                <span class="cmd-desc">خلع قطعة ملابس من المظهر</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف شعر hair">
                <span class="cmd-name">اضف شعر [id]</span>
                <span class="cmd-desc">إضافة شعر بالمعرف</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف قبعة hat">
                <span class="cmd-name">اضف قبعة [id]</span>
                <span class="cmd-desc">إضافة قبعة بالمعرف</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف تيشيرت shirt top">
                <span class="cmd-name">اضف تيشيرت [id]</span>
                <span class="cmd-desc">إضافة قميص/تيشيرت بالمعرف</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف بنطال pant">
                <span class="cmd-name">اضف بنطال [id]</span>
                <span class="cmd-desc">إضافة بنطلون بالمعرف</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف حذاء shoe">
                <span class="cmd-name">اضف حذاء [id]</span>
                <span class="cmd-desc">إضافة حذاء بالمعرف</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف عيون eyes">
                <span class="cmd-name">اضف عيون [id]</span>
                <span class="cmd-desc">إضافة عيون بالمعرف</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف ملامح face features">
                <span class="cmd-name">اضف ملامح [id]</span>
                <span class="cmd-desc">إضافة ملامح وجه بالمعرف</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير لون البشرة skin">
                <span class="cmd-name">تغيير لون البشرة [رقم]</span>
                <span class="cmd-desc">تغيير لون بشرة الشخصية</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير لون الشعر hair color">
                <span class="cmd-name">تغيير لون الشعر [id]</span>
                <span class="cmd-desc">تغيير لون الشعر</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير عيون eyes change">
                <span class="cmd-name">تغيير عيون [id]</span>
                <span class="cmd-desc">تغيير شكل العيون</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير النظارات glasses">
                <span class="cmd-name">تغيير النظارات [id]</span>
                <span class="cmd-desc">تغيير النظارات</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير الحواجب eyebrows">
                <span class="cmd-name">تغيير الحواجب [id]</span>
                <span class="cmd-desc">تغيير شكل الحواجب</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير الفم mouth lips">
                <span class="cmd-name">تغيير الفم [id]</span>
                <span class="cmd-desc">تغيير شكل الفم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير لون الفم mouth color">
                <span class="cmd-name">تغيير لون الفم [id]</span>
                <span class="cmd-desc">تغيير لون الشفاه</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="حفظ البس outfit save">
                <span class="cmd-name">حفظ البس [اسم]</span>
                <span class="cmd-desc">حفظ المظهر الحالي باسم مخصص</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="البس outfit load">
                <span class="cmd-name">البس [اسم]</span>
                <span class="cmd-desc">ارتداء مظهر محفوظ مسبقاً</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="حذف البس outfit delete">
                <span class="cmd-name">حذف البس [اسم]</span>
                <span class="cmd-desc">حذف مظهر محفوظ</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير تيشيرت shirt">
                <span class="cmd-name">تغيير تيشيرت [id]</span>
                <span class="cmd-desc">تغيير القميص مباشرة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير بنطال pant">
                <span class="cmd-name">تغيير بنطال [id]</span>
                <span class="cmd-desc">تغيير البنطلون مباشرة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
        </div>
    </div>

    <!-- أوامر VIP -->
    <div class="card cmd-section">
        <h5>💎 أوامر VIP والمسموح لهم</h5>
        <div class="cmd-grid" id="grid-vip">
            <div class="cmd-item" data-search="فوق صعدني up طلعني teleport">
                <span class="cmd-name">فوق / صعدني / up</span>
                <span class="cmd-desc">نقل البوت لأعلى / انتقال</span>
                <span class="badge-vip cmd-tag">VIP</span>
            </div>
            <div class="cmd-item" data-search="!invite دعوة">
                <span class="cmd-name">!invite</span>
                <span class="cmd-desc">دعوة لإرسال دعوة للغرفة</span>
                <span class="badge-vip cmd-tag">VIP</span>
            </div>
            <div class="cmd-item" data-search="!wallet محفظة gold">
                <span class="cmd-name">!wallet</span>
                <span class="cmd-desc">عرض رصيد محفظة البوت</span>
                <span class="badge-vip cmd-tag">VIP</span>
            </div>
            <div class="cmd-item" data-search="!tipme gold إهداء">
                <span class="cmd-name">!tipme [مبلغ]g</span>
                <span class="cmd-desc">إهداء ذهب للمستخدم</span>
                <span class="badge-vip cmd-tag">VIP</span>
            </div>
            <div class="cmd-item" data-search="!tipall gold إهداء الجميع">
                <span class="cmd-name">!tipall [مبلغ]g</span>
                <span class="cmd-desc">إهداء ذهب لجميع أفراد الغرفة</span>
                <span class="badge-vip cmd-tag">VIP</span>
            </div>
            <div class="cmd-item" data-search="حفظ save position مكان">
                <span class="cmd-name">حفظ</span>
                <span class="cmd-desc">حفظ الموقع الحالي للبوت</span>
                <span class="badge-vip cmd-tag">VIP</span>
            </div>
        </div>
    </div>

    <!-- أوامر الإدارة -->
    <div class="card cmd-section">
        <h5>🔴 أوامر الإدارة</h5>
        <div class="cmd-grid" id="grid-admin">
            <div class="cmd-item" data-search="!kick طرد kick">
                <span class="cmd-name">!kick @username</span>
                <span class="cmd-desc">طرد مستخدم من الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="!mute كتم mute">
                <span class="cmd-name">!mute @username</span>
                <span class="cmd-desc">كتم مستخدم في الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="!unmute فك كتم unmute">
                <span class="cmd-name">!unmute @username</span>
                <span class="cmd-desc">فك كتم مستخدم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="!ban حظر ban">
                <span class="cmd-name">!ban @username</span>
                <span class="cmd-desc">حظر مستخدم من الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="!unban فك حظر unban">
                <span class="cmd-name">!unban @username</span>
                <span class="cmd-desc">فك حظر مستخدم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="!summon استدعاء summon">
                <span class="cmd-name">!summon @username</span>
                <span class="cmd-desc">استدعاء مستخدم للغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="تحذير @username warning">
                <span class="cmd-name">تحذير @username</span>
                <span class="cmd-desc">إعطاء تحذير لمستخدم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="ازاله تحذير @username remove warning">
                <span class="cmd-name">ازاله تحذير @username</span>
                <span class="cmd-desc">إزالة تحذير من مستخدم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="تحذيراته warnings count">
                <span class="cmd-name">تحذيراته @username</span>
                <span class="cmd-desc">عرض عدد تحذيرات مستخدم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="!info معلومات user info">
                <span class="cmd-name">!info @username</span>
                <span class="cmd-desc">عرض معلومات مستخدم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="vvip @ ترقية vip">
                <span class="cmd-name">vvip @username</span>
                <span class="cmd-desc">منح مستخدم رتبة VVIP</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="لورد @ lord ترقية">
                <span class="cmd-name">لورد @username</span>
                <span class="cmd-desc">منح مستخدم رتبة لورد</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="اعلان announcement">
                <span class="cmd-name">اعلان [نص]</span>
                <span class="cmd-desc">إرسال إعلان في الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="حمايه حماية @username protect">
                <span class="cmd-name">حماية @username</span>
                <span class="cmd-desc">تفعيل/إيقاف حماية مستخدم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="وداع @username goodbye farewell">
                <span class="cmd-name">وداع @username</span>
                <span class="cmd-desc">إضافة رسالة وداع لمستخدم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="حذف وداع @username delete goodbye">
                <span class="cmd-name">حذف وداع @username</span>
                <span class="cmd-desc">حذف رسالة الوداع الخاصة بمستخدم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="حفظ مكان save location">
                <span class="cmd-name">حفظ مكان [اسم]</span>
                <span class="cmd-desc">حفظ موقع محدد باسم</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="احداثيات @username coordinates">
                <span class="cmd-name">احداثيات @username</span>
                <span class="cmd-desc">عرض إحداثيات مستخدم في الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="السجن سجن jail prison">
                <span class="cmd-name">السجن / سجن</span>
                <span class="cmd-desc">إرسال مستخدم إلى السجن</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="طرد الكل kick all">
                <span class="cmd-name">طرد الكل</span>
                <span class="cmd-desc">طرد جميع المستخدمين العاديين من الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="ايقاف الاعلان stop announcement">
                <span class="cmd-name">ايقاف الاعلان</span>
                <span class="cmd-desc">إيقاف الإعلان التلقائي المتكرر</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="ريست rest اعادة">
                <span class="cmd-name">ريست / rest</span>
                <span class="cmd-desc">إعادة ضبط حالة البوت</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="منشوراتي منشورات posts">
                <span class="cmd-name">منشوراتي</span>
                <span class="cmd-desc">عرض منشورات الغرفة الخاصة بك</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="منشورات @username posts other">
                <span class="cmd-name">منشورات @username</span>
                <span class="cmd-desc">عرض منشورات مستخدم معين</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="spam رسالة مكررة repeat">
                <span class="cmd-name">spam [رسالة]</span>
                <span class="cmd-desc">بدء تكرار رسالة معينة في الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="nospam ايقاف تكرار stop spam">
                <span class="cmd-name">nospam</span>
                <span class="cmd-desc">إيقاف تكرار الرسائل</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="move تحريك x y z coordinates">
                <span class="cmd-name">move [x] [y] [z]</span>
                <span class="cmd-desc">نقل البوت لإحداثيات معينة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="تثبيت fix lock position">
                <span class="cmd-name">تثبيت [x] [y] [z]</span>
                <span class="cmd-desc">تثبيت البوت في موقع محدد</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="go حرر unfix تحرير">
                <span class="cmd-name">go / حرر / unfix</span>
                <span class="cmd-desc">إلغاء تثبيت البوت وتحريره</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="بدل degis طابق floor change">
                <span class="cmd-name">بدل [رقم الطابق]</span>
                <span class="cmd-desc">تغيير طابق البوت في الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="الكل vip منح للجميع grant all">
                <span class="cmd-name">الكل vip</span>
                <span class="cmd-desc">منح رتبة VIP لجميع المستخدمين في الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="اضف مكان لورد lord location add">
                <span class="cmd-name">اضف مكان لورد</span>
                <span class="cmd-desc">إضافة موقع البوت الحالي كمكان للورد</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="كتم صوت voice mute ban audio">
                <span class="cmd-name">كتم صوت @username</span>
                <span class="cmd-desc">حظر صوت مستخدم في الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="فك كتم صوت voice unmute unban audio">
                <span class="cmd-name">فك كتم صوت @username</span>
                <span class="cmd-desc">فك حظر صوت مستخدم في الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="الكل رقصة all emote dance everyone apply">
                <span class="cmd-name">الكل [رقم الحركة]</span>
                <span class="cmd-desc">تطبيق حركة/رقصة محددة على جميع أفراد الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="رسالة خاصة للكل pm all broadcast خاص">
                <span class="cmd-name">رسالة للكل [نص]</span>
                <span class="cmd-desc">إرسال رسالة خاصة لجميع المستخدمين في الغرفة</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="احصائيات stats room info معلومات الغرفة">
                <span class="cmd-name">احصائيات</span>
                <span class="cmd-desc">عرض إحصائيات الغرفة الكاملة (نقاط، VIP، أدمن)</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="متصدرين leaderboard top points ranking">
                <span class="cmd-name">متصدرين / المتصدرون</span>
                <span class="cmd-desc">عرض أفضل 10 مستخدمين بالنقاط</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
            <div class="cmd-item" data-search="اطلق سراح release free jail unimprison">
                <span class="cmd-name">اطلق @username</span>
                <span class="cmd-desc">إطلاق سراح مستخدم مسجون قبل انتهاء مدته</span>
                <span class="badge-admin cmd-tag">مشرف</span>
            </div>
        </div>
    </div>

    <!-- أوامر المعلومات -->
    <div class="card cmd-section">
        <h5>ℹ️ أوامر المعلومات والأدوات</h5>
        <div class="cmd-grid" id="grid-info">
            <div class="cmd-item" data-search="نقاطي points score نقاط">
                <span class="cmd-name">نقاطي</span>
                <span class="cmd-desc">عرض رصيد نقاطك في الغرفة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="!xp xp نقاط experience">
                <span class="cmd-name">!xp</span>
                <span class="cmd-desc">عرض مستوى XP الخاص بك</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="الوقت توقيت time ساعة">
                <span class="cmd-name">الوقت / توقيت / time</span>
                <span class="cmd-desc">عرض الوقت الحالي</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="ping بينج استجابة bot alive">
                <span class="cmd-name">ping</span>
                <span class="cmd-desc">التحقق من استجابة البوت</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احسب calculate حاسبة حساب">
                <span class="cmd-name">احسب [عملية حسابية]</span>
                <span class="cmd-desc">حاسبة - حساب عمليات رياضية</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اي دي id معرف user id">
                <span class="cmd-name">اي دي / id @username</span>
                <span class="cmd-desc">عرض معرف مستخدم في الغرفة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="الاحداثيات bot coordinates position">
                <span class="cmd-name">الاحداثيات</span>
                <span class="cmd-desc">عرض الإحداثيات الحالية للبوت</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="vip check vip status حالة">
                <span class="cmd-name">vip / !vip</span>
                <span class="cmd-desc">عرض قائمة مستخدمي VIP في الغرفة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="floors طوابق list floors">
                <span class="cmd-name">floors / طوابق / الطوابق</span>
                <span class="cmd-desc">عرض قائمة طوابق الغرفة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="list emotes حركات قائمة">
                <span class="cmd-name">list [اسم حركة]</span>
                <span class="cmd-desc">البحث عن حركات متاحة بالاسم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="شرح امر explain command help">
                <span class="cmd-name">شرح [اسم الأمر]</span>
                <span class="cmd-desc">عرض شرح تفصيلي لأمر معين</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
        </div>
    </div>

    <!-- أوامر المالك -->
    <div class="card cmd-section">
        <h5>👑 أوامر المالك</h5>
        <div class="cmd-grid" id="grid-owner">
            <div class="cmd-item" data-search="!restart ريستارت اعادة تشغيل">
                <span class="cmd-name">!restart / ريستارت</span>
                <span class="cmd-desc">إعادة تشغيل البوت بالكامل</span>
                <span class="badge-owner cmd-tag">المالك</span>
            </div>
            <div class="cmd-item" data-search="!تابعني room_id غرفة اخرى">
                <span class="cmd-name">!تابعني [room_id]</span>
                <span class="cmd-desc">نقل البوت إلى غرفة أخرى</span>
                <span class="badge-owner cmd-tag">المالك</span>
            </div>
            <div class="cmd-item" data-search="لهجة dialect مصرية عراقية خليجية شامية">
                <span class="cmd-name">لهجة [لهجة]</span>
                <span class="cmd-desc">تغيير لهجة ردود البوت (مصرية، عراقية، خليجية، شامية، فصحى)</span>
                <span class="badge-owner cmd-tag">المالك</span>
            </div>
            <div class="cmd-item" data-search="اذهب room_id owner move غرفة">
                <span class="cmd-name">اذهب [room_id]</span>
                <span class="cmd-desc">الانتقال إلى غرفة محددة</span>
                <span class="badge-owner cmd-tag">المالك</span>
            </div>
        </div>
    </div>

    <!-- اختصارات الملابس -->
    <div class="card cmd-section">
        <h5>⚡ اختصارات تجهيز الملابس (DM)</h5>
        <div class="cmd-grid" id="grid-equip-shortcuts">
            <div class="cmd-item" data-search="eq h hair شعر اختصار">
                <span class="cmd-name">eq h [id]</span>
                <span class="cmd-desc">اختصار: تغيير الشعر الأمامي</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq fh back hair شعر خلفي">
                <span class="cmd-name">eq fh [id]</span>
                <span class="cmd-desc">اختصار: تغيير الشعر الخلفي</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq t top shirt قميص">
                <span class="cmd-name">eq t [id]</span>
                <span class="cmd-desc">اختصار: تغيير القميص</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq p pant بنطلون">
                <span class="cmd-name">eq p [id]</span>
                <span class="cmd-desc">اختصار: تغيير البنطلون</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq s shoe حذاء">
                <span class="cmd-name">eq s [id]</span>
                <span class="cmd-desc">اختصار: تغيير الحذاء</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq sh skin بشرة لون">
                <span class="cmd-name">eq sh [id]</span>
                <span class="cmd-desc">اختصار: تغيير لون البشرة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq b body جسم">
                <span class="cmd-name">eq b [id]</span>
                <span class="cmd-desc">اختصار: تغيير شكل الجسم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq so socks جوارب">
                <span class="cmd-name">eq so [id]</span>
                <span class="cmd-desc">اختصار: تغيير الجوارب</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq a accessory اكسسوار">
                <span class="cmd-name">eq a [id]</span>
                <span class="cmd-desc">اختصار: تغيير الاكسسوار</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq eb eyebrow حواجب">
                <span class="cmd-name">eq eb [id]</span>
                <span class="cmd-desc">اختصار: تغيير الحواجب</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq e eye عيون">
                <span class="cmd-name">eq e [id]</span>
                <span class="cmd-desc">اختصار: تغيير العيون</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq n nose أنف">
                <span class="cmd-name">eq n [id]</span>
                <span class="cmd-desc">اختصار: تغيير الأنف</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq m mouth فم">
                <span class="cmd-name">eq m [id]</span>
                <span class="cmd-desc">اختصار: تغيير الفم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="eq fr freckles نمش بقع">
                <span class="cmd-name">eq fr [id]</span>
                <span class="cmd-desc">اختصار: تغيير النمش</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="evemo emote vip حركة خاصة">
                <span class="cmd-name">evemo</span>
                <span class="cmd-desc">عرض قائمة حركات VIP المتاحة (عبر الرسائل الخاصة)</span>
                <span class="badge-vip cmd-tag">VIP</span>
            </div>
        </div>
    </div>

    <!-- خلع وإزالة القطع -->
    <div class="card cmd-section">
        <h5>🗑️ خلع وإزالة القطع</h5>
        <div class="cmd-grid" id="grid-remove-cloth">
            <div class="cmd-item" data-search="احذف شعر remove hair خلع">
                <span class="cmd-name">احذف شعر</span>
                <span class="cmd-desc">إزالة الشعر الأمامي</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف قبعة remove hat cap خلع">
                <span class="cmd-name">احذف قبعة / احذف قبعه</span>
                <span class="cmd-desc">إزالة القبعة</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف تيشيرت remove top shirt خلع">
                <span class="cmd-name">احذف تيشيرت</span>
                <span class="cmd-desc">إزالة القميص / التيشيرت</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف بنطال remove pant خلع">
                <span class="cmd-name">احذف بنطال</span>
                <span class="cmd-desc">إزالة البنطلون</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف حذاء remove shoe خلع">
                <span class="cmd-name">احذف حذاء</span>
                <span class="cmd-desc">إزالة الحذاء</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف عين eye remove خلع">
                <span class="cmd-name">احذف عين</span>
                <span class="cmd-desc">إزالة تغيير العيون</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف فم mouth remove لون فم خلع">
                <span class="cmd-name">احذف فم / احذف لون فم</span>
                <span class="cmd-desc">إزالة تغيير الفم أو لونه</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف وشم tattoo remove خلع">
                <span class="cmd-name">احذف وشم</span>
                <span class="cmd-desc">إزالة الوشم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف اكسسوار accessory remove خلع">
                <span class="cmd-name">احذف اكسسوار / احذف الاكسسوار</span>
                <span class="cmd-desc">إزالة الاكسسوار</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف يد hand remove glove خلع">
                <span class="cmd-name">احذف يد</span>
                <span class="cmd-desc">إزالة القفاز / يد</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف دب bear remove خلع">
                <span class="cmd-name">احذف دب</span>
                <span class="cmd-desc">إزالة الدب الشخصي</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف نظارات glasses remove خلع">
                <span class="cmd-name">احذف نظارات</span>
                <span class="cmd-desc">إزالة النظارات</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف انف nose remove خلع">
                <span class="cmd-name">احذف انف / احذف أنف</span>
                <span class="cmd-desc">إزالة تغيير الأنف</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف حاجب eyebrow remove خلع">
                <span class="cmd-name">احذف حاجب</span>
                <span class="cmd-desc">إزالة تغيير الحاجب</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف اختفاء invisible remove خلع">
                <span class="cmd-name">احذف اختفاء / احذف الاختفاء</span>
                <span class="cmd-desc">إزالة تأثير الاختفاء</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف ملمح feature face remove خلع">
                <span class="cmd-name">احذف ملمح</span>
                <span class="cmd-desc">إزالة ملمح الوجه</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احذف لبس outfit remove number رقم خلع">
                <span class="cmd-name">احذف لبس [رقم]</span>
                <span class="cmd-desc">حذف بدلة محفوظة برقمها</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اخلع item id معرف remove unequip">
                <span class="cmd-name">اخلع [id القطعة]</span>
                <span class="cmd-desc">خلع قطعة ملابس محددة بمعرفها</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
        </div>
    </div>

    <!-- ملابس متقدمة -->
    <div class="card cmd-section">
        <h5>🌟 ملابس متقدمة (اضف / تغيير)</h5>
        <div class="cmd-grid" id="grid-adv-cloth">
            <div class="cmd-item" data-search="اضف وشم tattoo add">
                <span class="cmd-name">اضف وشم [id]</span>
                <span class="cmd-desc">إضافة وشم بمعرف محدد</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف اكسسوار accessory add">
                <span class="cmd-name">اضف اكسسوار [id]</span>
                <span class="cmd-desc">إضافة اكسسوار بمعرف محدد</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف يد hand glove add">
                <span class="cmd-name">اضف يد [id]</span>
                <span class="cmd-desc">إضافة قفاز / يد بمعرف محدد</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف دب bear add">
                <span class="cmd-name">اضف دب [id]</span>
                <span class="cmd-desc">إضافة دب بمعرف محدد</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف انف nose add">
                <span class="cmd-name">اضف انف [id] / اضف أنف [id]</span>
                <span class="cmd-desc">إضافة شكل أنف بمعرف محدد</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف حاجب eyebrow add">
                <span class="cmd-name">اضف حاجب [id]</span>
                <span class="cmd-desc">إضافة شكل حاجب بمعرف محدد</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="اضف اختفاء invisible add">
                <span class="cmd-name">اضف اختفاء [id]</span>
                <span class="cmd-desc">إضافة تأثير اختفاء بمعرف محدد</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير وشم tattoo change">
                <span class="cmd-name">تغيير وشم [id]</span>
                <span class="cmd-desc">تغيير الوشم الحالي</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير اكسسوار accessory change">
                <span class="cmd-name">تغيير اكسسوار [id]</span>
                <span class="cmd-desc">تغيير الاكسسوار الحالي</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير يد hand change">
                <span class="cmd-name">تغيير يد [id]</span>
                <span class="cmd-desc">تغيير القفاز / اليد الحالية</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير ملامح features face change">
                <span class="cmd-name">تغيير ملامح [id]</span>
                <span class="cmd-desc">تغيير ملامح الوجه</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير لون الحواجب eyebrow color change">
                <span class="cmd-name">تغيير لون الحواجب [كود اللون]</span>
                <span class="cmd-desc">تغيير لون الحواجب</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="تغيير لون الفم mouth color change">
                <span class="cmd-name">تغيير لون الفم [كود اللون]</span>
                <span class="cmd-desc">تغيير لون الفم</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="رقصات list emotes dances available">
                <span class="cmd-name">رقصات</span>
                <span class="cmd-desc">عرض قائمة الحركات/الرقصات المتاحة (في الخاص)</span>
                <span class="badge-all cmd-tag">للجميع</span>
            </div>
            <div class="cmd-item" data-search="احداثيات @ coords user position">
                <span class="cmd-name">احداثيات @[اسم المستخدم]</span>
                <span class="cmd-desc">عرض إحداثيات مستخدم معين في الغرفة</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="ارجع back return saved position">
                <span class="cmd-name">ارجع</span>
                <span class="cmd-desc">إرجاع البوت لآخر موقع محفوظ له</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
        </div>
    </div>

    <!-- أوامر إدارية متقدمة -->
    <div class="card cmd-section">
        <h5>⚙️ أوامر إدارية متقدمة</h5>
        <div class="cmd-grid" id="grid-adv-admin">
            <div class="cmd-item" data-search="قول say bot speak room text message">
                <span class="cmd-name">قول [نص]</span>
                <span class="cmd-desc">جعل البوت يقول نصاً بصوته في الغرفة</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="قفل الغرفة lock room close">
                <span class="cmd-name">قفل الغرفة</span>
                <span class="cmd-desc">منع المستخدمين الجدد من الدخول</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="افتح الغرفة unlock room open">
                <span class="cmd-name">افتح الغرفة</span>
                <span class="cmd-desc">السماح للجميع بالدخول مجدداً</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="كتم الكل mute all voice hours">
                <span class="cmd-name">كتم الكل [ساعات]</span>
                <span class="cmd-desc">كتم صوت الجميع لعدد معين من الساعات</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="الغاء كتم الكل unmute all voice">
                <span class="cmd-name">الغاء كتم الكل</span>
                <span class="cmd-desc">إلغاء كتم صوت الجميع</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="اضافه محمي protected add special user">
                <span class="cmd-name">اضافه محمي @[اسم]</span>
                <span class="cmd-desc">إضافة مستخدم لقائمة المحميين (لا يُطرد أو يُحظر)</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="ازاله محمي protected remove unprotect">
                <span class="cmd-name">ازاله محمي @[اسم]</span>
                <span class="cmd-desc">إزالة مستخدم من قائمة المحميين</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="قائمة المحاميين protected list show">
                <span class="cmd-name">قائمة المحاميين</span>
                <span class="cmd-desc">عرض قائمة المستخدمين المحميين</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="اضافه ترحيب welcome add custom user">
                <span class="cmd-name">اضافه ترحيب @[اسم] [نص]</span>
                <span class="cmd-desc">إضافة رسالة ترحيب خاصة لمستخدم عند دخوله</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="وداع @ farewell add custom user">
                <span class="cmd-name">وداع @[اسم] [نص]</span>
                <span class="cmd-desc">إضافة رسالة وداع خاصة لمستخدم عند خروجه</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="حذف وداع @ farewell delete remove">
                <span class="cmd-name">حذف وداع @[اسم]</span>
                <span class="cmd-desc">حذف رسالة وداع خاصة لمستخدم</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="اطفاء shutdown bot owner off">
                <span class="cmd-name">اطفاء</span>
                <span class="cmd-desc">إطفاء البوت بالكامل (للمالك فقط)</span>
                <span class="badge-owner cmd-tag">المالك</span>
            </div>
            <div class="cmd-item" data-search="اعادة تشغيل restart bot reboot">
                <span class="cmd-name">اعادة تشغيل</span>
                <span class="cmd-desc">إعادة تشغيل البوت عبر الغرفة</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="حماية protect user shield">
                <span class="cmd-name">حماية @[اسم] / حمايه @[اسم]</span>
                <span class="cmd-desc">تفعيل الحماية لمستخدم (لا يُطرد أو يُحظر)</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="+x -x +y -y +z -z move adjust position">
                <span class="cmd-name">+x / -x / +y / -y / +z / -z</span>
                <span class="cmd-desc">تحريك البوت خطوة واحدة في الاتجاه المحدد</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
        </div>
    </div>

    <!-- نظام السجن والإطلاق -->
    <div class="card cmd-section">
        <h5>⛓️ نظام السجن والإطلاق</h5>
        <div class="cmd-grid" id="grid-jail">
            <div class="cmd-item" data-search="سجن @ jail user lock imprison">
                <span class="cmd-name">سجن @[اسم]</span>
                <span class="cmd-desc">سجن مستخدم لمدة 5 دقائق (لا يستطيع التنقل)</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="السجن go jail location room">
                <span class="cmd-name">السجن</span>
                <span class="cmd-desc">إرسال مستخدم إلى منطقة السجن في الغرفة</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="اطلق @ release free jail سراح">
                <span class="cmd-name">اطلق @[اسم]</span>
                <span class="cmd-desc">الإفراج عن مستخدم مسجون قبل انتهاء مدته</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="مسجون jailed users list prison">
                <span class="cmd-name">المسجونون</span>
                <span class="cmd-desc">عرض قائمة المستخدمين المسجونين حالياً</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
        </div>
    </div>

    <!-- VIP2 والاشتراكات -->
    <div class="card cmd-section">
        <h5>💎 VIP2 والاشتراكات الخاصة</h5>
        <div class="cmd-grid" id="grid-vip2-swm">
            <div class="cmd-item" data-search="!addvip addvip vip2 add hearts قلوب">
                <span class="cmd-name">!addvip @[اسم]</span>
                <span class="cmd-desc">إضافة مستخدم لقائمة VIP القلوب (VIP2)</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="!delvip delvip removevip vip2 remove hearts قلوب">
                <span class="cmd-name">!delvip @[اسم]</span>
                <span class="cmd-desc">إزالة مستخدم من قائمة VIP القلوب</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="vip2 list قائمة VIP قلوب hearts">
                <span class="cmd-name">vip2 list</span>
                <span class="cmd-desc">عرض قائمة مستخدمي VIP القلوب</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="addswm !addswm welcome subscription رسالة ترحيب خاص">
                <span class="cmd-name">addswm @[اسم] [نص]</span>
                <span class="cmd-desc">إضافة رسالة ترحيب خاصة لمستخدم عند دخوله</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="removeswm !removeswm welcome remove حذف ترحيب">
                <span class="cmd-name">removeswm @[اسم]</span>
                <span class="cmd-desc">حذف رسالة الترحيب الخاصة لمستخدم</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="swm list !swm list قائمة الترحيبات">
                <span class="cmd-name">swm list</span>
                <span class="cmd-desc">عرض قائمة كل الترحيبات الخاصة المسجلة</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="all رقم emote dance everyone كل الغرفة رقصة للكل">
                <span class="cmd-name">all [رقم الحركة]</span>
                <span class="cmd-desc">تطبيق حركة/رقصة على جميع أفراد الغرفة</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="الكل vip everyone vip dance رقصة VIP للجميع">
                <span class="cmd-name">الكل vip</span>
                <span class="cmd-desc">تطبيق حركة VIP على كل أفراد الغرفة</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
        </div>
    </div>

    <!-- إدارة الأدمن والرتب -->
    <div class="card cmd-section">
        <h5>🎖️ إدارة الأدمن والرتب</h5>
        <div class="cmd-grid" id="grid-mod">
            <div class="cmd-item" data-search="!mod mod add admin moderator مشرف إضافة">
                <span class="cmd-name">!mod @[اسم]</span>
                <span class="cmd-desc">إضافة مستخدم كمشرف في البوت</span>
                <span class="badge-owner cmd-tag">المالك</span>
            </div>
            <div class="cmd-item" data-search="!delmod delmod remove admin moderator مشرف حذف">
                <span class="cmd-name">!delmod @[اسم]</span>
                <span class="cmd-desc">حذف مستخدم من قائمة المشرفين</span>
                <span class="badge-owner cmd-tag">المالك</span>
            </div>
            <div class="cmd-item" data-search="!adminlist adminlist قائمة المشرفين list admins">
                <span class="cmd-name">!adminlist</span>
                <span class="cmd-desc">عرض قائمة جميع المشرفين في البوت</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="!desig desig designation special title لقب">
                <span class="cmd-name">!desig @[اسم]</span>
                <span class="cmd-desc">تعيين لقب/منصب خاص لمستخدم</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="!deldesig deldesig remove designation حذف لقب">
                <span class="cmd-name">!deldesig @[اسم]</span>
                <span class="cmd-desc">حذف اللقب الخاص لمستخدم</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
            <div class="cmd-item" data-search="!add add admin special user إضافة خاص">
                <span class="cmd-name">!add @[اسم]</span>
                <span class="cmd-desc">إضافة مستخدم خاص (special user)</span>
                <span class="badge-owner cmd-tag">المالك</span>
            </div>
            <div class="cmd-item" data-search="!remove remove special user إزالة خاص">
                <span class="cmd-name">!remove @[اسم]</span>
                <span class="cmd-desc">إزالة مستخدم خاص</span>
                <span class="badge-owner cmd-tag">المالك</span>
            </div>
            <div class="cmd-item" data-search="Special_list قائمة الخاصين list special users">
                <span class="cmd-name">Special_list</span>
                <span class="cmd-desc">عرض قائمة المستخدمين الخاصين</span>
                <span class="badge-admin cmd-tag">أدمن</span>
            </div>
        </div>
    </div>

    <div id="no-results" class="no-results" style="display:none;">
        <h4>🔍 لا توجد نتائج</h4>
        <p>جرب كلمة بحث أخرى</p>
    </div>
</div>
</div>

<!-- تبويب التحكم -->
<div id="tab-control" class="tab-content-custom">
<div class="container-main">

    <!-- قسم الرسائل والإعلانات -->
    <div class="ctrl-section-title">💬 الرسائل والإعلانات</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>📨 إرسال رسالة للغرفة</h5>
            <input type="text" id="chat-msg" class="form-control mb-2" placeholder="اكتب رسالتك هنا...">
            <button onclick="sendMessage()" class="ctrl-btn">إرسال</button>
            <div id="send-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📢 إرسال إعلان رسمي</h5>
            <input type="text" id="announce-text" class="form-control mb-2" placeholder="نص الإعلان...">
            <button onclick="doAnnounce()" class="ctrl-btn">إعلان</button>
            <div id="announce-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم إدارة المستخدمين -->
    <div class="ctrl-section-title">🛡️ إدارة المستخدمين</div>
    <div style="margin-bottom:12px">
        <select id="mod-user-select" class="form-select" style="max-width:100%">
            <option value="">-- اختر مستخدم من الغرفة --</option>
        </select>
        <button onclick="refreshUsers()" class="ctrl-btn-sm" style="margin-top:8px">🔄 تحديث قائمة المستخدمين</button>
        <div id="users-status" class="ctrl-status"></div>
    </div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>👢 طرد مستخدم</h5>
            <input type="text" id="kick-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doMod('kick')" class="ctrl-btn ctrl-btn-danger">طرد</button>
            <div id="kick-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔨 حظر مستخدم</h5>
            <input type="text" id="ban-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="number" id="ban-minutes" class="form-control mb-2" placeholder="المدة بالدقائق (افتراضي 60)" min="1">
            <button onclick="doMod('ban')" class="ctrl-btn ctrl-btn-danger">حظر</button>
            <div id="ban-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔇 كتم مستخدم</h5>
            <input type="text" id="mute-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="number" id="mute-minutes" class="form-control mb-2" placeholder="المدة بالدقائق (افتراضي 10)" min="1">
            <button onclick="doMod('mute')" class="ctrl-btn ctrl-btn-warning">كتم</button>
            <div id="mute-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔊 فك كتم مستخدم</h5>
            <input type="text" id="unmute-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doMod('unmute')" class="ctrl-btn ctrl-btn-success">فك الكتم</button>
            <div id="unmute-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📩 استدعاء مستخدم</h5>
            <input type="text" id="summon-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doMod('summon')" class="ctrl-btn">استدعاء</button>
            <div id="summon-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم الملابس -->
    <div class="ctrl-section-title">👗 الملابس</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>👕 ارتداء قطعة ملابس</h5>
            <select id="clothing-category" class="form-select mb-2">
                <option value="hair">شعر أمامي</option>
                <option value="back_hair">شعر خلفي</option>
                <option value="top">قميص</option>
                <option value="pant">بنطلون</option>
                <option value="shoe">حذاء</option>
            </select>
            <input type="text" id="clothing-id" class="form-control mb-2" placeholder="معرف القطعة (item_id)">
            <button onclick="wearClothing()" class="ctrl-btn">ارتداء</button>
            <div id="clothing-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🪞 نسخ ملابس مستخدم</h5>
            <input type="text" id="equip-user" class="form-control mb-2" placeholder="اسم المستخدم (حتى خارج الغرفة)">
            <button onclick="doEquipUser()" class="ctrl-btn">نسخ الملابس</button>
            <div id="equip-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم الحركات -->
    <div class="ctrl-section-title">🎭 حركات البوت</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🎬 حركة سريعة</h5>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px;">
                <button onclick="doDance('sleep')" class="ctrl-btn-sm">😴 نام</button>
                <button onclick="doDance('ghost')" class="ctrl-btn-sm">👻 جوست</button>
                <button onclick="doDance('kiss')" class="ctrl-btn-sm">💋 بوسة</button>
                <button onclick="doDance('shy')" class="ctrl-btn-sm">😊 خجول</button>
                <button onclick="doDance('dance')" class="ctrl-btn-sm">💃 رقص</button>
                <button onclick="doDance('wave')" class="ctrl-btn-sm">👋 سلام</button>
                <button onclick="doDance('yes')" class="ctrl-btn-sm">✅ موافق</button>
                <button onclick="doDance('think')" class="ctrl-btn-sm">🤔 تفكير</button>
                <button onclick="doDance('happy')" class="ctrl-btn-sm">😄 سعيد</button>
                <button onclick="doDance('sad')" class="ctrl-btn-sm">😢 حزين</button>
                <button onclick="doDance('stop')" class="ctrl-btn-sm ctrl-btn-danger" style="grid-column:span 3">⏹️ إيقاف الحركة</button>
            </div>
            <div id="dance-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🕹️ إرسال حركة بالمعرف</h5>
            <input type="text" id="emote-id" class="form-control mb-2" placeholder="معرف الحركة (emote_id)">
            <button onclick="doEmote()" class="ctrl-btn">إرسال حركة</button>
            <div id="emote-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم إدارة الغرفة -->
    <div class="ctrl-section-title">🔒 إدارة الغرفة</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🚪 قفل / فتح الغرفة</h5>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                <button onclick="doRoomControl('lock')" class="ctrl-btn ctrl-btn-danger">🔒 قفل</button>
                <button onclick="doRoomControl('unlock')" class="ctrl-btn ctrl-btn-success">🔓 فتح</button>
            </div>
            <div id="room-lock-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔇 كتم / فك كتم الجميع</h5>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                <button onclick="doRoomControl('mute_all')" class="ctrl-btn ctrl-btn-warning">🔇 كتم الكل</button>
                <button onclick="doRoomControl('unmute_all')" class="ctrl-btn ctrl-btn-success">🔊 فك الكتم</button>
            </div>
            <div id="room-mute-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📍 موقع البوت</h5>
            <button onclick="doRoomControl('go_home')" class="ctrl-btn">🏠 ارجع لمكانك</button>
            <div id="room-pos-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم اللهجة والإعلانات -->
    <div class="ctrl-section-title">🗣️ اللهجة والإعلانات</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🗣️ تغيير لهجة البوت</h5>
            <select id="dialect-select" class="form-select mb-2">
                <option value="فصحى">فصحى (افتراضية)</option>
                <option value="عراقية">عراقية 🇮🇶</option>
                <option value="مصرية">مصرية 🇪🇬</option>
                <option value="خليجية">خليجية 🇸🇦</option>
                <option value="شامية">شامية 🇸🇾</option>
            </select>
            <button onclick="changeDialect()" class="ctrl-btn">تغيير اللهجة</button>
            <div id="dialect-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📣 الإعلانات التلقائية</h5>
            <button onclick="doStopAnnouncement()" class="ctrl-btn ctrl-btn-danger">🛑 إيقاف الإعلان</button>
            <div id="announce-stop-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>👗 خلع الملابس</h5>
            <button onclick="doStripAll()" class="ctrl-btn ctrl-btn-warning">🚫 اخلع الكل</button>
            <div id="strip-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم VIP -->
    <div class="ctrl-section-title">💎 إدارة VIP</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>➕ إضافة VIP</h5>
            <input type="text" id="add-vip-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="manageVip('add')" class="ctrl-btn ctrl-btn-success">إضافة VIP</button>
            <div id="add-vip-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>➖ حذف VIP</h5>
            <input type="text" id="remove-vip-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="manageVip('remove')" class="ctrl-btn ctrl-btn-danger">حذف VIP</button>
            <div id="remove-vip-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم التحذيرات -->
    <div class="ctrl-section-title">⚠️ إدارة التحذيرات</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>⚠️ إعطاء تحذير</h5>
            <input type="text" id="warn-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doWarning('add')" class="ctrl-btn ctrl-btn-warning">تحذير</button>
            <div id="warn-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>✅ إزالة تحذير</h5>
            <input type="text" id="unwarn-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doWarning('remove')" class="ctrl-btn ctrl-btn-success">إزالة تحذير</button>
            <div id="unwarn-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔍 عرض تحذيرات مستخدم</h5>
            <input type="text" id="check-warn-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doWarning('check')" class="ctrl-btn">فحص التحذيرات</button>
            <div id="check-warn-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم إدارة البوت -->
    <div class="ctrl-section-title">🤖 إدارة البوت</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🔄 إعادة تشغيل البوت</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">سيتوقف البوت ويعيد الاتصال تلقائياً</p>
            <button onclick="doBotAction('restart')" class="ctrl-btn ctrl-btn-danger">🔄 إعادة التشغيل</button>
            <div id="restart-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>👢 طرد الجميع</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">طرد كل المستخدمين العاديين (يُبقي الأدمن)</p>
            <button onclick="doBotAction('kick_all')" class="ctrl-btn ctrl-btn-danger">👢 طرد الكل</button>
            <div id="kick-all-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🧹 مسح الشات</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">إرسال أسطر فارغة لمسح المحادثة</p>
            <button onclick="doBotAction('clear_chat')" class="ctrl-btn ctrl-btn-warning">🧹 مسح</button>
            <div id="clear-chat-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>💨 إبعاد الجميع</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">نقل الجميع لمواقع عشوائية في الغرفة</p>
            <button onclick="doBotAction('push_away')" class="ctrl-btn ctrl-btn-warning">💨 ابعدهم</button>
            <div id="push-away-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم التنقل -->
    <div class="ctrl-section-title">📍 التنقل والحركة</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🚀 الانتقال لمستخدم</h5>
            <input type="text" id="tp-to-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doTeleport('go_to')" class="ctrl-btn">روح</button>
            <div id="tp-to-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🧲 سحب مستخدم</h5>
            <input type="text" id="pull-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doTeleport('pull')" class="ctrl-btn">اسحب</button>
            <div id="pull-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🌊 سحب الجميع</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">جلب جميع المستخدمين لموقع البوت</p>
            <button onclick="doTeleport('pull_all')" class="ctrl-btn">هات الكل</button>
            <div id="pull-all-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🎤 دعوة للمايك</h5>
            <input type="text" id="mic-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doTeleport('mic')" class="ctrl-btn ctrl-btn-success">مايك</button>
            <div id="mic-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم إدارة الأدمن -->
    <div class="ctrl-section-title">👨‍💼 إدارة الأدمن</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>➕ إضافة أدمن</h5>
            <input type="text" id="add-admin-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="manageAdmin('add')" class="ctrl-btn ctrl-btn-success">إضافة أدمن</button>
            <div id="add-admin-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>➖ حذف أدمن</h5>
            <input type="text" id="remove-admin-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="manageAdmin('remove')" class="ctrl-btn ctrl-btn-danger">حذف أدمن</button>
            <div id="remove-admin-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📋 قائمة الأدمن</h5>
            <button onclick="manageAdmin('list')" class="ctrl-btn">عرض القائمة</button>
            <div id="list-admin-status" class="ctrl-status" style="min-height:30px;text-align:right;font-size:0.8rem;word-break:break-word"></div>
        </div>
    </div>

    <!-- قسم السبام -->
    <div class="ctrl-section-title">💬 تكرار الرسائل</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🔁 بدء تكرار رسالة</h5>
            <input type="text" id="spam-msg" class="form-control mb-2" placeholder="الرسالة المراد تكرارها...">
            <button onclick="doSpam('start')" class="ctrl-btn">▶️ بدء التكرار</button>
            <div id="spam-start-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>⏹️ إيقاف التكرار</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">إيقاف تكرار الرسائل نهائياً</p>
            <button onclick="doSpam('stop')" class="ctrl-btn ctrl-btn-danger">⏹️ إيقاف</button>
            <div id="spam-stop-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم المعلومات السريعة -->
    <div class="ctrl-section-title">📡 معلومات سريعة</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🏓 بينج البوت</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">التحقق من استجابة البوت وسرعته</p>
            <button onclick="doQuickInfo('ping')" class="ctrl-btn">🏓 Ping</button>
            <div id="ping-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🕐 الوقت الحالي</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">عرض التوقيت الحالي للبوت</p>
            <button onclick="doQuickInfo('time')" class="ctrl-btn">🕐 الوقت</button>
            <div id="quicktime-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📍 إحداثيات البوت</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">عرض موقع البوت الحالي في الغرفة</p>
            <button onclick="doQuickInfo('coords')" class="ctrl-btn">📍 الإحداثيات</button>
            <div id="coords-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>💎 قائمة VIP</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">عرض جميع مستخدمي VIP</p>
            <button onclick="doQuickInfo('viplist')" class="ctrl-btn">💎 VIP List</button>
            <div id="viplist-status" class="ctrl-status" style="font-size:0.78rem;word-break:break-word;min-height:30px;text-align:right;"></div>
        </div>
        <div class="card ctrl-card">
            <h5>👥 المستخدمون في الغرفة</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">عدد الموجودين حالياً</p>
            <button onclick="doQuickInfo('roomusers')" class="ctrl-btn">👥 عرض العدد</button>
            <div id="roomusers-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>⭐ نقاط البوت</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">عرض إجمالي نقاط البوت المخزنة</p>
            <button onclick="doQuickInfo('totalpoints')" class="ctrl-btn">⭐ النقاط</button>
            <div id="totalpoints-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم تحريك البوت -->
    <div class="ctrl-section-title">🎮 تحريك البوت بدقة</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🚀 نقل لإحداثيات</h5>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; margin-bottom:8px;">
                <input type="number" id="move-x" class="form-control" placeholder="X" step="0.5">
                <input type="number" id="move-y" class="form-control" placeholder="Y" step="0.5">
                <input type="number" id="move-z" class="form-control" placeholder="Z" step="0.5">
            </div>
            <button onclick="doMoveBot('move')" class="ctrl-btn">🚀 انتقل</button>
            <div id="move-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📌 تثبيت في موقع</h5>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; margin-bottom:8px;">
                <input type="number" id="fix-x" class="form-control" placeholder="X" step="0.5">
                <input type="number" id="fix-y" class="form-control" placeholder="Y" step="0.5">
                <input type="number" id="fix-z" class="form-control" placeholder="Z" step="0.5">
            </div>
            <button onclick="doMoveBot('fix')" class="ctrl-btn ctrl-btn-warning">📌 تثبيت</button>
            <div id="fix-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔓 تحرير البوت</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">إلغاء تثبيت البوت وتحريره بحرية</p>
            <button onclick="doMoveBot('unfix')" class="ctrl-btn ctrl-btn-success">🔓 تحرير</button>
            <div id="unfix-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم الحاسبة -->
    <div class="ctrl-section-title">🧮 الحاسبة</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🧮 حساب عملية رياضية</h5>
            <input type="text" id="calc-expr" class="form-control mb-2" placeholder="مثال: 500 * 3 + 100">
            <button onclick="doCalculate()" class="ctrl-btn">= احسب</button>
            <div id="calc-status" class="ctrl-status" style="font-size:1rem;font-weight:bold;"></div>
        </div>
    </div>

    <!-- قسم إدارة اللورد -->
    <div class="ctrl-section-title">👑 إدارة اللورد</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>➕ منح رتبة لورد</h5>
            <input type="text" id="add-lord-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="manageLord('add')" class="ctrl-btn ctrl-btn-success">👑 منح لورد</button>
            <div id="add-lord-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>➖ سحب رتبة لورد</h5>
            <input type="text" id="remove-lord-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="manageLord('remove')" class="ctrl-btn ctrl-btn-danger">❌ سحب لورد</button>
            <div id="remove-lord-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📋 قائمة اللورد</h5>
            <button onclick="manageLord('list')" class="ctrl-btn">عرض القائمة</button>
            <div id="list-lord-status" class="ctrl-status" style="min-height:30px;text-align:right;font-size:0.8rem;word-break:break-word"></div>
        </div>
    </div>

    <!-- قسم نقاط المستخدمين -->
    <div class="ctrl-section-title">⭐ نقاط المستخدمين</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🔍 عرض نقاط مستخدم</h5>
            <input type="text" id="check-points-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doPointsAction('check')" class="ctrl-btn">🔍 فحص النقاط</button>
            <div id="check-points-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>➕ إضافة نقاط</h5>
            <input type="text" id="add-points-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="number" id="add-points-amount" class="form-control mb-2" placeholder="عدد النقاط..." min="1">
            <button onclick="doPointsAction('add')" class="ctrl-btn ctrl-btn-success">➕ إضافة</button>
            <div id="add-points-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>➖ خصم نقاط</h5>
            <input type="text" id="remove-points-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="number" id="remove-points-amount" class="form-control mb-2" placeholder="عدد النقاط..." min="1">
            <button onclick="doPointsAction('remove')" class="ctrl-btn ctrl-btn-danger">➖ خصم</button>
            <div id="remove-points-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم المحميين -->
    <div class="ctrl-section-title">🛡️ إدارة المحميين</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>➕ إضافة محمي</h5>
            <input type="text" id="add-protected-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doProtected('add')" class="ctrl-btn ctrl-btn-success">🛡️ إضافة محمي</button>
            <div id="add-protected-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>➖ إزالة محمي</h5>
            <input type="text" id="remove-protected-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doProtected('remove')" class="ctrl-btn ctrl-btn-danger">❌ إزالة المحمي</button>
            <div id="remove-protected-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📋 قائمة المحميين</h5>
            <button onclick="doProtected('list')" class="ctrl-btn">📋 عرض القائمة</button>
            <div id="list-protected-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم الترحيب الخاص -->
    <div class="ctrl-section-title">🎉 رسائل الترحيب الخاصة</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>➕ إضافة ترحيب خاص</h5>
            <input type="text" id="welcome-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="text" id="welcome-text" class="form-control mb-2" placeholder="نص رسالة الترحيب...">
            <button onclick="doWelcome('add')" class="ctrl-btn ctrl-btn-success">🎉 إضافة</button>
            <div id="add-welcome-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🗑️ حذف ترحيب خاص</h5>
            <input type="text" id="del-welcome-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doWelcome('remove')" class="ctrl-btn ctrl-btn-danger">🗑️ حذف</button>
            <div id="del-welcome-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📋 عدد الترحيبات</h5>
            <button onclick="doWelcome('list')" class="ctrl-btn">📋 عرض الإحصائية</button>
            <div id="list-welcome-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم الوداع الخاص -->
    <div class="ctrl-section-title">👋 رسائل الوداع الخاصة</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>➕ إضافة وداع خاص</h5>
            <input type="text" id="farewell-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="text" id="farewell-text" class="form-control mb-2" placeholder="نص رسالة الوداع...">
            <button onclick="doFarewell('add')" class="ctrl-btn ctrl-btn-success">👋 إضافة</button>
            <div id="add-farewell-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🗑️ حذف وداع خاص</h5>
            <input type="text" id="del-farewell-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doFarewell('remove')" class="ctrl-btn ctrl-btn-danger">🗑️ حذف</button>
            <div id="del-farewell-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📋 قائمة الوداعات</h5>
            <button onclick="doFarewell('list')" class="ctrl-btn">📋 عرض الوداعات</button>
            <div id="list-farewell-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم السجن -->
    <div class="ctrl-section-title">⛓️ نظام السجن</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🔒 سجن مستخدم</h5>
            <input type="text" id="jail-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="number" id="jail-minutes" class="form-control mb-2" placeholder="المدة بالدقائق (افتراضي 5)" min="1" max="120">
            <button onclick="doJail('jail')" class="ctrl-btn ctrl-btn-danger">⛓️ سجن</button>
            <div id="jail-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔓 إطلاق سراح</h5>
            <input type="text" id="release-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doJail('release')" class="ctrl-btn ctrl-btn-success">🔓 إطلاق</button>
            <div id="release-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📋 المسجونون الآن</h5>
            <button onclick="doJail('list')" class="ctrl-btn">👁️ عرض المسجونين</button>
            <div id="jail-list-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم اشتراكات SWM -->
    <div class="ctrl-section-title">📢 اشتراكات الترحيب (SWM)</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>➕ إضافة اشتراك SWM</h5>
            <input type="text" id="swm-add-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="text" id="swm-add-text" class="form-control mb-2" placeholder="نص الترحيب الخاص (اختياري)...">
            <button onclick="doSwm('add')" class="ctrl-btn ctrl-btn-success">➕ إضافة SWM</button>
            <div id="swm-add-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>➖ حذف اشتراك SWM</h5>
            <input type="text" id="swm-remove-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doSwm('remove')" class="ctrl-btn ctrl-btn-danger">➖ حذف SWM</button>
            <div id="swm-remove-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📋 قائمة SWM</h5>
            <button onclick="doSwm('list')" class="ctrl-btn">📋 عرض قائمة SWM</button>
            <div id="swm-list-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم إدارة المشرفين -->
    <div class="ctrl-section-title">🎖️ إدارة المشرفين</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>➕ إضافة مشرف</h5>
            <input type="text" id="add-mod-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doModAdmin('add')" class="ctrl-btn ctrl-btn-success">🎖️ إضافة مشرف</button>
            <div id="add-mod-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>➖ إزالة مشرف</h5>
            <input type="text" id="remove-mod-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doModAdmin('remove')" class="ctrl-btn ctrl-btn-danger">❌ إزالة مشرف</button>
            <div id="remove-mod-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📋 قائمة المشرفين</h5>
            <button onclick="doModAdmin('list')" class="ctrl-btn">📋 عرض المشرفين</button>
            <div id="mod-list-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم المواقع المحفوظة -->
    <div class="ctrl-section-title">📍 المواقع المحفوظة</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>📋 عرض المواقع</h5>
            <button onclick="doLocations('list')" class="ctrl-btn">📋 قائمة المواقع</button>
            <div id="locations-list-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🚀 انتقل لموقع محفوظ</h5>
            <input type="text" id="goto-location" class="form-control mb-2" placeholder="اسم الموقع...">
            <button onclick="doLocations('goto')" class="ctrl-btn ctrl-btn-success">🚀 انتقل</button>
            <div id="goto-location-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🗑️ حذف موقع</h5>
            <input type="text" id="del-location" class="form-control mb-2" placeholder="اسم الموقع...">
            <button onclick="doLocations('delete')" class="ctrl-btn ctrl-btn-danger">🗑️ حذف موقع</button>
            <div id="del-location-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم الرسائل الخاصة -->
    <div class="ctrl-section-title">📤 إرسال رسالة خاصة</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>📤 رسالة خاصة لمستخدم</h5>
            <input type="text" id="pm-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="text" id="pm-text" class="form-control mb-2" placeholder="نص الرسالة الخاصة...">
            <button onclick="doPrivateMsg()" class="ctrl-btn ctrl-btn-success">📤 إرسال</button>
            <div id="pm-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📡 رسالة جماعية خاصة</h5>
            <input type="text" id="pm-all-text" class="form-control mb-2" placeholder="الرسالة لجميع المستخدمين...">
            <button onclick="doPrivateMsgAll()" class="ctrl-btn">📡 إرسال للكل</button>
            <div id="pm-all-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم متابعة المستخدمين -->
    <div class="ctrl-section-title">🔁 متابعة المستخدمين</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🔁 متابعة مستخدم</h5>
            <input type="text" id="follow-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doFollow('start')" class="ctrl-btn ctrl-btn-success">▶️ بدء المتابعة</button>
            <div id="follow-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>⏹️ إيقاف المتابعة</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">إيقاف متابعة المستخدم الحالي</p>
            <button onclick="doFollow('stop')" class="ctrl-btn ctrl-btn-danger">⏹️ إيقاف</button>
            <div id="unfollow-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔍 معلومات مستخدم</h5>
            <input type="text" id="info-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doUserInfo()" class="ctrl-btn">🔍 عرض المعلومات</button>
            <div id="info-status" class="ctrl-status" style="min-height:30px;text-align:right;font-size:0.8rem;word-break:break-word"></div>
        </div>
    </div>

    <!-- قسم تغيير الطابق -->
    <div class="ctrl-section-title">🏢 تغيير الطابق والانتقال</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🏢 تغيير طابق البوت</h5>
            <select id="floor-select" class="form-select mb-2">
                <option value="1">الطابق 1</option>
                <option value="2">الطابق 2</option>
                <option value="3">الطابق 3</option>
                <option value="4">الطابق 4</option>
                <option value="5">الطابق 5</option>
            </select>
            <button onclick="doChangeFloor()" class="ctrl-btn">🏢 انتقل للطابق</button>
            <div id="floor-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🎮 تحريك اتجاهي</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">تحريك البوت خطوة واحدة في الاتجاه المطلوب</p>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; margin-bottom:6px;">
                <button onclick="doDirectionalMove('+x')" class="ctrl-btn-sm">← X+</button>
                <button onclick="doDirectionalMove('+y')" class="ctrl-btn-sm">↑ Y+</button>
                <button onclick="doDirectionalMove('+z')" class="ctrl-btn-sm">↗ Z+</button>
                <button onclick="doDirectionalMove('-x')" class="ctrl-btn-sm">→ X-</button>
                <button onclick="doDirectionalMove('-y')" class="ctrl-btn-sm">↓ Y-</button>
                <button onclick="doDirectionalMove('-z')" class="ctrl-btn-sm">↙ Z-</button>
            </div>
            <div id="dir-move-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>💾 حفظ موقع محدد</h5>
            <input type="text" id="save-loc-name" class="form-control mb-2" placeholder="اسم الموقع...">
            <button onclick="doLocations('save')" class="ctrl-btn ctrl-btn-success">💾 حفظ الموقع الحالي</button>
            <div id="save-location-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم إهداء الذهب -->
    <div class="ctrl-section-title">💰 إهداء الذهب</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>💰 إهداء ذهب لمستخدم</h5>
            <input type="text" id="tip-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <input type="number" id="tip-amount" class="form-control mb-2" placeholder="مقدار الذهب (g)..." min="1">
            <button onclick="doTipUser()" class="ctrl-btn ctrl-btn-success">💰 إهداء</button>
            <div id="tip-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>💎 عرض رصيد المحفظة</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">عرض رصيد ذهب البوت الحالي</p>
            <button onclick="doWalletInfo()" class="ctrl-btn">💎 عرض الرصيد</button>
            <div id="wallet-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم تطبيق حركة على الكل -->
    <div class="ctrl-section-title">🎯 تطبيق حركة على الجميع</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🎯 تطبيق حركة على الكل</h5>
            <input type="text" id="all-emote-id" class="form-control mb-2" placeholder="رقم الحركة أو معرفها...">
            <button onclick="doAllEmote()" class="ctrl-btn">🎯 طبق على الجميع</button>
            <div id="all-emote-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔇 حظر صوتي لمستخدم</h5>
            <input type="text" id="voiceban-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                <button onclick="doVoiceBan('ban')" class="ctrl-btn ctrl-btn-warning">🔇 حظر صوت</button>
                <button onclick="doVoiceBan('unban')" class="ctrl-btn ctrl-btn-success">🔊 فك حظر</button>
            </div>
            <div id="voiceban-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🎖️ ترقية/تنزيل مستخدم</h5>
            <input type="text" id="rank-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <select id="rank-select" class="form-select mb-2">
                <option value="vvip">VVIP</option>
                <option value="lord">لورد</option>
                <option value="vip">VIP</option>
            </select>
            <button onclick="doRankUser()" class="ctrl-btn ctrl-btn-success">🎖️ منح الرتبة</button>
            <div id="rank-status" class="ctrl-status"></div>
        </div>
    </div>

    <!-- قسم نقاط مستخدم محدد -->
    <div class="ctrl-section-title">🏆 لوحة المتصدرين والنقاط</div>
    <div class="ctrl-grid">
        <div class="card ctrl-card">
            <h5>🏆 أعلى المستخدمين نقاطاً</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">عرض أفضل 10 مستخدمين بالنقاط</p>
            <button onclick="doLeaderboard()" class="ctrl-btn">🏆 عرض المتصدرين</button>
            <div id="leaderboard-status" class="ctrl-status" style="min-height:30px;text-align:right;font-size:0.78rem;word-break:break-word;"></div>
        </div>
        <div class="card ctrl-card">
            <h5>🔄 إعادة ضبط نقاط مستخدم</h5>
            <input type="text" id="reset-points-user" class="form-control mb-2" placeholder="اسم المستخدم...">
            <button onclick="doPointsAction('reset')" class="ctrl-btn ctrl-btn-danger">🔄 إعادة ضبط</button>
            <div id="reset-points-status" class="ctrl-status"></div>
        </div>
        <div class="card ctrl-card">
            <h5>📊 إحصائيات الغرفة الكاملة</h5>
            <p style="font-size:0.8rem;color:var(--muted);margin-bottom:8px">عرض ملخص شامل عن حالة الغرفة</p>
            <button onclick="doRoomStats()" class="ctrl-btn">📊 إحصائيات شاملة</button>
            <div id="room-stats-status" class="ctrl-status" style="min-height:30px;text-align:right;font-size:0.78rem;word-break:break-word;"></div>
        </div>
    </div>

</div>
</div>

<!-- تبويب الملابس المحفوظة -->
<div id="tab-outfits" class="tab-content-custom">
<div class="container-main">
    <div class="section-header">👗 الملابس المحفوظة</div>
    <div id="outfits-status-msg" class="ctrl-status" style="margin-bottom:16px;font-size:0.9rem;"></div>
    <div id="outfits-grid" style="display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:14px;">
        <div style="color:var(--muted); text-align:center; padding:40px; grid-column:span 4;">جاري تحميل الملابس...</div>
    </div>
</div>
</div>

<!-- تبويب الإحصائيات -->
<div id="tab-stats" class="tab-content-custom">
<div class="container-main">
    <div class="row mb-4">
        <div class="col-md-4 mb-3">
            <div class="stat-card">
                <div class="stat-num" id="points-count">...</div>
                <div class="stat-label">⭐ مجموع النقاط</div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="stat-card">
                <div class="stat-num" id="vip-count">...</div>
                <div class="stat-label">💎 مستخدمو VIP</div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="stat-card">
                <div class="stat-num" id="admin-count">...</div>
                <div class="stat-label">🛡️ المشرفون</div>
            </div>
        </div>
    </div>
    <div class="card">
        <h5>📊 حالة البوت</h5>
        <div style="display:flex; flex-direction:column; gap:12px;">
            <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid var(--card-border);">
                <span style="color:var(--muted)">الحالة</span>
                <span><span class="online-dot"></span> متصل ونشط</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid var(--card-border);">
                <span style="color:var(--muted)">المطور</span>
                <span style="color:var(--accent)">@_king_man_1</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid var(--card-border);">
                <span style="color:var(--muted)">إجمالي الأوامر</span>
                <span style="color:var(--accent)">150+</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:10px 0;">
                <span style="color:var(--muted)">المنصة</span>
                <span>Highrise</span>
            </div>
        </div>
    </div>
</div>
</div>

<script>
    function switchTab(name) {
        document.querySelectorAll('.tab-content-custom').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.nav-tabs-custom button').forEach(b => b.classList.remove('active'));
        document.getElementById('tab-' + name).classList.add('active');
        event.target.classList.add('active');
        if (name === 'stats') updateStats();
        if (name === 'outfits') loadOutfits();
    }

    function loadOutfits() {
        fetch('/outfits')
            .then(r => r.json())
            .then(data => {
                const grid = document.getElementById('outfits-grid');
                if (!data.outfits || data.outfits.length === 0) {
                    grid.innerHTML = '<div style="color:var(--muted);text-align:center;padding:40px;grid-column:span 4;">لا توجد ملابس محفوظة</div>';
                    return;
                }
                grid.innerHTML = data.outfits.map(o => `
                    <div class="card" style="padding:14px;text-align:center;cursor:pointer;border:1px solid rgba(124,58,237,0.2);transition:all 0.2s;" 
                         onmouseover="this.style.borderColor='rgba(124,58,237,0.6)'" 
                         onmouseout="this.style.borderColor='rgba(124,58,237,0.2)'">
                        <div style="font-size:2rem;margin-bottom:8px;">👗</div>
                        <div style="font-weight:700;color:var(--accent);font-size:0.9rem;margin-bottom:4px;">${o.name}</div>
                        <div style="font-size:0.75rem;color:var(--muted);margin-bottom:10px;">${o.count} قطعة</div>
                        <button onclick="wearOutfit(${o.slot})" class="ctrl-btn" style="padding:7px 10px;font-size:0.82rem;">
                            ارتداء
                        </button>
                        <div id="outfit-status-${o.slot}" class="ctrl-status" style="font-size:0.75rem;min-height:16px;margin-top:4px;"></div>
                    </div>
                `).join('');
            })
            .catch(() => {
                document.getElementById('outfits-grid').innerHTML = '<div style="color:#ef4444;text-align:center;padding:40px;grid-column:span 4;">خطأ في تحميل الملابس</div>';
            });
    }

    function wearOutfit(slot) {
        const statusEl = document.getElementById('outfit-status-' + slot);
        if (statusEl) { statusEl.style.color = 'var(--muted)'; statusEl.innerText = '...'; }
        fetch('/wear-outfit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({slot: slot})
        })
        .then(r => r.json())
        .then(d => {
            if (statusEl) {
                statusEl.style.color = d.success ? '#22c55e' : '#ef4444';
                statusEl.innerText = d.success ? '✅ تم' : '❌ ' + (d.error || 'خطأ');
                setTimeout(() => { statusEl.innerText = ''; }, 3000);
            }
        })
        .catch(() => {
            if (statusEl) { statusEl.style.color = '#ef4444'; statusEl.innerText = '❌ خطأ'; setTimeout(() => { statusEl.innerText = ''; }, 3000); }
        });
    }

    function ctrlStatus(id, msg, ok) {
        const el = document.getElementById(id);
        if (!el) return;
        el.style.color = ok ? '#22c55e' : '#ef4444';
        el.innerText = msg;
        setTimeout(() => { el.innerText = ''; }, 3000);
    }

    function doAnnounce() {
        const text = document.getElementById('announce-text').value.trim();
        if (!text) return;
        fetch('/announce', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({text}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('announce-status', d.success ? '✅ تم إرسال الإعلان' : '❌ ' + d.error, d.success);
            if (d.success) document.getElementById('announce-text').value = '';
        });
    }

    function doMod(action) {
        const inputMap = { kick: 'kick-user', ban: 'ban-user', mute: 'mute-user', unmute: 'unmute-user', summon: 'summon-user' };
        const selUser = document.getElementById('mod-user-select').value;
        let username = (document.getElementById(inputMap[action])?.value || selUser || '').trim().replace('@','');
        if (!username) { ctrlStatus(action + '-status', '❌ أدخل اسم المستخدم', false); return; }
        const body = { username };
        if (action === 'ban') body.minutes = parseInt(document.getElementById('ban-minutes').value) || 60;
        if (action === 'mute') body.minutes = parseInt(document.getElementById('mute-minutes').value) || 10;
        const endpointMap = { kick: '/kick', ban: '/ban', mute: '/mute', unmute: '/unmute', summon: '/summon' };
        fetch(endpointMap[action], { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(action + '-status', d.success ? '✅ تم تنفيذ الأمر' : '❌ ' + d.error, d.success);
            if (d.success && document.getElementById(inputMap[action])) document.getElementById(inputMap[action]).value = '';
        });
    }

    function doEquipUser() {
        const username = document.getElementById('equip-user').value.trim().replace('@','');
        if (!username) { ctrlStatus('equip-status', '❌ أدخل اسم المستخدم', false); return; }
        fetch('/equip-user', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('equip-status', d.success ? '✅ جاري نسخ الملابس...' : '❌ ' + d.error, d.success);
            if (d.success) document.getElementById('equip-user').value = '';
        });
    }

    function doEmote() {
        const emote_id = document.getElementById('emote-id').value.trim();
        if (!emote_id) { ctrlStatus('emote-status', '❌ أدخل معرف الحركة', false); return; }
        fetch('/emote', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({emote_id}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('emote-status', d.success ? '✅ تم إرسال الحركة' : '❌ ' + d.error, d.success);
        });
    }

    function doDance(action) {
        fetch('/dance-cmd', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({action}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('dance-status', d.success ? '✅ تم' : '❌ ' + d.error, d.success);
        });
    }

    function doRoomControl(action) {
        const statusMap = {lock:'room-lock-status', unlock:'room-lock-status', mute_all:'room-mute-status', unmute_all:'room-mute-status', go_home:'room-pos-status'};
        fetch('/room-control', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({action}) })
        .then(r => r.json()).then(d => {
            ctrlStatus(statusMap[action], d.success ? '✅ تم' : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(statusMap[action], '❌ خطأ في الاتصال', false));
    }

    function changeDialect() {
        const dialect = document.getElementById('dialect-select').value;
        fetch('/set-dialect', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({dialect}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('dialect-status', d.success ? '✅ تم تغيير اللهجة إلى: ' + dialect : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus('dialect-status', '❌ خطأ في الاتصال', false));
    }

    function doStopAnnouncement() {
        fetch('/stop-announcement', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('announce-stop-status', d.success ? '✅ تم إيقاف الإعلان' : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus('announce-stop-status', '❌ خطأ في الاتصال', false));
    }

    function doStripAll() {
        fetch('/strip-outfit', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('strip-status', d.success ? '✅ تم خلع الملابس' : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus('strip-status', '❌ خطأ في الاتصال', false));
    }

    function manageVip(action) {
        const inputId = action === 'add' ? 'add-vip-user' : 'remove-vip-user';
        const statusId = action === 'add' ? 'add-vip-status' : 'remove-vip-status';
        const username = document.getElementById(inputId).value.trim().replace('@','');
        if (!username) { ctrlStatus(statusId, '❌ أدخل اسم المستخدم', false); return; }
        fetch('/manage-vip', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({action, username}) })
        .then(r => r.json()).then(d => {
            ctrlStatus(statusId, d.success ? '✅ ' + d.message : '❌ ' + (d.error||'خطأ'), d.success);
            if (d.success) document.getElementById(inputId).value = '';
        }).catch(() => ctrlStatus(statusId, '❌ خطأ في الاتصال', false));
    }

    function doWarning(action) {
        let inputId, statusId;
        if (action === 'add') { inputId = 'warn-user'; statusId = 'warn-status'; }
        else if (action === 'remove') { inputId = 'unwarn-user'; statusId = 'unwarn-status'; }
        else { inputId = 'check-warn-user'; statusId = 'check-warn-status'; }
        const username = document.getElementById(inputId).value.trim().replace('@','');
        if (!username) { ctrlStatus(statusId, '❌ أدخل اسم المستخدم', false); return; }
        fetch('/warning', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({action, username}) })
        .then(r => r.json()).then(d => {
            ctrlStatus(statusId, d.success ? '✅ ' + d.message : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(statusId, '❌ خطأ في الاتصال', false));
    }

    function doBotAction(action) {
        const statusMap = {restart:'restart-status', kick_all:'kick-all-status', clear_chat:'clear-chat-status', push_away:'push-away-status'};
        const sid = statusMap[action];
        ctrlStatus(sid, '⏳ جاري التنفيذ...', true);
        fetch('/bot-action', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({action}) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doTeleport(action) {
        const inputMap = {go_to:'tp-to-user', pull:'pull-user', pull_all:null, mic:'mic-user'};
        const statusMap = {go_to:'tp-to-status', pull:'pull-status', pull_all:'pull-all-status', mic:'mic-status'};
        const sid = statusMap[action];
        let username = '';
        if (inputMap[action]) {
            username = document.getElementById(inputMap[action]).value.trim().replace('@','');
            if (!username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
        }
        fetch('/teleport-action', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({action, username}) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function manageAdmin(action) {
        const inputMap = {add:'add-admin-user', remove:'remove-admin-user', list:null};
        const statusMap = {add:'add-admin-status', remove:'remove-admin-status', list:'list-admin-status'};
        const sid = statusMap[action];
        let username = '';
        if (inputMap[action]) {
            username = document.getElementById(inputMap[action]).value.trim().replace('@','');
            if (!username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
        }
        fetch('/manage-admin', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({action, username}) })
        .then(r => r.json()).then(d => {
            if (action === 'list' && d.success) {
                const el = document.getElementById(sid);
                el.style.color = '#a78bfa';
                el.innerText = d.admins && d.admins.length > 0 ? '📋 ' + d.admins.join('، ') : 'لا يوجد أدمن';
            } else {
                ctrlStatus(sid, d.success ? '✅ ' + d.message : '❌ ' + (d.error||'خطأ'), d.success);
            }
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doSpam(action) {
        const sid = action === 'start' ? 'spam-start-status' : 'spam-stop-status';
        let body = {action};
        if (action === 'start') {
            const msg = document.getElementById('spam-msg').value.trim();
            if (!msg) { ctrlStatus(sid, '❌ أدخل الرسالة', false); return; }
            body.message = msg;
        }
        fetch('/spam-control', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
            if (d.success && action === 'start') document.getElementById('spam-msg').value = '';
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doQuickInfo(action) {
        const ids = {ping:'ping-status', time:'quicktime-status', coords:'coords-status', viplist:'viplist-status', roomusers:'roomusers-status', totalpoints:'totalpoints-status'};
        const sid = ids[action];
        if (!sid) return;
        document.getElementById(sid).innerText = '⏳ جاري...';
        fetch('/quick-info', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({action}) })
        .then(r => r.json()).then(d => {
            const el = document.getElementById(sid);
            if (d.success) { el.style.color = '#22c55e'; el.innerText = d.message; }
            else { el.style.color = '#ef4444'; el.innerText = '❌ ' + (d.error||'خطأ'); }
            if (action !== 'viplist') setTimeout(() => { el.innerText = ''; }, 5000);
        }).catch(() => { document.getElementById(sid).innerText = '❌ خطأ في الاتصال'; });
    }

    function doMoveBot(action) {
        const ids = {move:'move-status', fix:'fix-status', unfix:'unfix-status'};
        const sid = ids[action];
        let body = {action};
        if (action === 'move' || action === 'fix') {
            const prefix = action === 'move' ? 'move' : 'fix';
            const x = parseFloat(document.getElementById(prefix+'-x').value);
            const y = parseFloat(document.getElementById(prefix+'-y').value);
            const z = parseFloat(document.getElementById(prefix+'-z').value);
            if (isNaN(x) || isNaN(y) || isNaN(z)) { ctrlStatus(sid, '❌ أدخل الإحداثيات X, Y, Z', false); return; }
            body.x = x; body.y = y; body.z = z;
        }
        fetch('/move-bot', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doCalculate() {
        const expr = document.getElementById('calc-expr').value.trim();
        if (!expr) { ctrlStatus('calc-status', '❌ أدخل عملية حسابية', false); return; }
        fetch('/calculate', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({expression: expr}) })
        .then(r => r.json()).then(d => {
            const el = document.getElementById('calc-status');
            if (d.success) { el.style.color = '#a78bfa'; el.innerText = '= ' + d.result; }
            else { el.style.color = '#ef4444'; el.innerText = '❌ ' + (d.error||'خطأ في الحساب'); }
        }).catch(() => ctrlStatus('calc-status', '❌ خطأ في الاتصال', false));
    }

    function manageLord(action) {
        const ids = {add:'add-lord-status', remove:'remove-lord-status', list:'list-lord-status'};
        const sid = ids[action];
        let body = {action};
        if (action === 'add') body.username = document.getElementById('add-lord-user').value.trim().replace(/^@/,'');
        if (action === 'remove') body.username = document.getElementById('remove-lord-user').value.trim().replace(/^@/,'');
        fetch('/manage-lord', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            const el = document.getElementById(sid);
            if (d.success) {
                el.style.color = '#22c55e';
                el.innerText = d.message || '✅ تم';
                if (action === 'add') document.getElementById('add-lord-user').value = '';
                if (action === 'remove') document.getElementById('remove-lord-user').value = '';
            } else { el.style.color = '#ef4444'; el.innerText = '❌ ' + (d.error||'خطأ'); }
            setTimeout(() => { el.innerText = ''; }, 5000);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doPointsAction(action) {
        const ids = {check:'check-points-status', add:'add-points-status', remove:'remove-points-status', reset:'reset-points-status'};
        const sid = ids[action];
        let body = {action};
        if (action === 'check') body.username = document.getElementById('check-points-user').value.trim().replace(/^@/,'');
        if (action === 'add') {
            body.username = document.getElementById('add-points-user').value.trim().replace(/^@/,'');
            body.amount = parseInt(document.getElementById('add-points-amount').value);
        }
        if (action === 'remove') {
            body.username = document.getElementById('remove-points-user').value.trim().replace(/^@/,'');
            body.amount = parseInt(document.getElementById('remove-points-amount').value);
        }
        if (action === 'reset') {
            body.username = document.getElementById('reset-points-user').value.trim().replace(/^@/,'');
            if (!body.username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
        }
        fetch('/manage-points', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function refreshUsers() {
        const statusEl = document.getElementById('users-status');
        statusEl.style.color = 'var(--muted)';
        statusEl.innerText = '🔄 جاري جلب المستخدمين...';
        fetch('/room-users').then(r => r.json()).then(d => {
            const sel = document.getElementById('mod-user-select');
            sel.innerHTML = '<option value="">-- اختر مستخدم من الغرفة --</option>';
            if (d.users && d.users.length > 0) {
                d.users.forEach(u => {
                    const opt = document.createElement('option');
                    opt.value = u.username;
                    opt.textContent = u.username;
                    sel.appendChild(opt);
                });
                statusEl.style.color = '#22c55e';
                statusEl.innerText = '✅ ' + d.users.length + ' مستخدم في الغرفة';
            } else {
                statusEl.style.color = 'var(--muted)';
                statusEl.innerText = 'لا يوجد مستخدمون في الغرفة';
            }
            setTimeout(() => { statusEl.innerText = ''; }, 4000);
        });
    }

    function doProtected(action) {
        const ids = {add:'add-protected-status', remove:'remove-protected-status', list:'list-protected-status'};
        const sid = ids[action];
        let body = {action};
        if (action === 'add') body.username = document.getElementById('add-protected-user').value.trim().replace(/^@/,'');
        if (action === 'remove') body.username = document.getElementById('remove-protected-user').value.trim().replace(/^@/,'');
        fetch('/manage-protected', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doWelcome(action) {
        const ids = {add:'add-welcome-status', remove:'del-welcome-status', list:'list-welcome-status'};
        const sid = ids[action];
        let body = {action};
        if (action === 'add') {
            body.username = document.getElementById('welcome-user').value.trim().replace(/^@/,'');
            body.text = document.getElementById('welcome-text').value.trim();
        }
        if (action === 'remove') body.username = document.getElementById('del-welcome-user').value.trim().replace(/^@/,'');
        fetch('/special-welcome', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doFarewell(action) {
        const ids = {add:'add-farewell-status', remove:'del-farewell-status', list:'list-farewell-status'};
        const sid = ids[action];
        let body = {action};
        if (action === 'add') {
            body.username = document.getElementById('farewell-user').value.trim().replace(/^@/,'');
            body.text = document.getElementById('farewell-text').value.trim();
        }
        if (action === 'remove') body.username = document.getElementById('del-farewell-user').value.trim().replace(/^@/,'');
        fetch('/special-farewell', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    document.getElementById('mod-user-select').addEventListener('change', function() {
        const v = this.value;
        if (!v) return;
        ['kick-user','ban-user','mute-user','unmute-user','summon-user','equip-user','warn-user','unwarn-user','check-warn-user','add-vip-user','remove-vip-user','tp-to-user','pull-user','mic-user','add-admin-user','remove-admin-user','add-lord-user','remove-lord-user','check-points-user','add-points-user','remove-points-user','add-protected-user','remove-protected-user','welcome-user','del-welcome-user','farewell-user','del-farewell-user','pm-user','follow-user','info-user','tip-user','voiceban-user','rank-user','reset-points-user','jail-user','release-user','add-mod-user','remove-mod-user','swm-add-user','swm-remove-user'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = v;
        });
    });

    function filterCommands() {
        const q = document.getElementById('searchBox').value.toLowerCase();
        const items = document.querySelectorAll('.cmd-item');
        let found = 0;
        document.querySelectorAll('.cmd-section').forEach(s => {
            let sectionFound = 0;
            s.querySelectorAll('.cmd-item').forEach(item => {
                const text = (item.dataset.search + ' ' + item.innerText).toLowerCase();
                const show = !q || text.includes(q);
                item.style.display = show ? '' : 'none';
                if (show) { found++; sectionFound++; }
            });
            s.style.display = sectionFound > 0 || !q ? '' : 'none';
        });
        document.getElementById('no-results').style.display = (found === 0 && q) ? 'block' : 'none';
    }

    function updateStats() {
        fetch('/stats')
            .then(r => r.json())
            .then(data => {
                const p = data.total_points || 0;
                const v = data.vip_users || 0;
                const a = data.admins || 0;
                document.getElementById('points-count').innerText = p.toLocaleString();
                document.getElementById('vip-count').innerText = v;
                document.getElementById('admin-count').innerText = a;
                document.getElementById('hdr-points').innerText = '⭐ ' + p.toLocaleString() + ' نقطة';
                document.getElementById('hdr-vip').innerText = '💎 ' + v + ' VIP';
            }).catch(() => {});
    }

    function sendMessage() {
        const msg = document.getElementById('chat-msg').value;
        if (!msg) return;
        const statusDiv = document.getElementById('send-status');
        statusDiv.style.color = 'var(--muted)';
        statusDiv.innerText = 'جاري الإرسال...';
        fetch('/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        }).then(r => r.json()).then(data => {
            if (data.success) {
                statusDiv.style.color = '#22c55e';
                statusDiv.innerText = '✅ تم الإرسال!';
                document.getElementById('chat-msg').value = '';
            } else {
                statusDiv.style.color = '#ef4444';
                statusDiv.innerText = '❌ فشل: ' + data.error;
            }
            setTimeout(() => { statusDiv.innerText = ''; }, 3000);
        });
    }

    function wearClothing() {
        const category = document.getElementById('clothing-category').value;
        const item_id = document.getElementById('clothing-id').value;
        if (!item_id) return;
        const statusDiv = document.getElementById('clothing-status');
        statusDiv.style.color = 'var(--muted)';
        statusDiv.innerText = 'جاري التبديل...';
        fetch('/wear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category: category, item_id: item_id })
        }).then(r => r.json()).then(data => {
            if (data.success) {
                statusDiv.style.color = '#22c55e';
                statusDiv.innerText = '✅ تم تغيير الملابس!';
                document.getElementById('clothing-id').value = '';
            } else {
                statusDiv.style.color = '#ef4444';
                statusDiv.innerText = '❌ خطأ: ' + data.error;
            }
            setTimeout(() => { statusDiv.innerText = ''; }, 3000);
        });
    }

    function doPrivateMsg() {
        const username = document.getElementById('pm-user').value.trim().replace(/^@/,'');
        const text = document.getElementById('pm-text').value.trim();
        if (!username || !text) { ctrlStatus('pm-status', '❌ أدخل اسم المستخدم والرسالة', false); return; }
        fetch('/private-message', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username, text}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('pm-status', d.success ? '✅ تم إرسال الرسالة الخاصة' : '❌ ' + (d.error||'خطأ'), d.success);
            if (d.success) { document.getElementById('pm-user').value = ''; document.getElementById('pm-text').value = ''; }
        }).catch(() => ctrlStatus('pm-status', '❌ خطأ في الاتصال', false));
    }

    function doPrivateMsgAll() {
        const text = document.getElementById('pm-all-text').value.trim();
        if (!text) { ctrlStatus('pm-all-status', '❌ أدخل نص الرسالة', false); return; }
        fetch('/private-message-all', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({text}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('pm-all-status', d.success ? '✅ ' + (d.message||'تم الإرسال للجميع') : '❌ ' + (d.error||'خطأ'), d.success);
            if (d.success) document.getElementById('pm-all-text').value = '';
        }).catch(() => ctrlStatus('pm-all-status', '❌ خطأ في الاتصال', false));
    }

    function doFollow(action) {
        const sid = action === 'start' ? 'follow-status' : 'unfollow-status';
        let body = {action};
        if (action === 'start') {
            const username = document.getElementById('follow-user').value.trim().replace(/^@/,'');
            if (!username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
            body.username = username;
        }
        fetch('/follow-user', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doUserInfo() {
        const username = document.getElementById('info-user').value.trim().replace(/^@/,'');
        if (!username) { ctrlStatus('info-status', '❌ أدخل اسم المستخدم', false); return; }
        const el = document.getElementById('info-status');
        el.style.color = 'var(--muted)'; el.innerText = '⏳ جاري البحث...';
        fetch('/user-info', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username}) })
        .then(r => r.json()).then(d => {
            if (d.success) { el.style.color = '#a78bfa'; el.innerText = d.message; }
            else { el.style.color = '#ef4444'; el.innerText = '❌ ' + (d.error||'خطأ'); }
        }).catch(() => { el.style.color = '#ef4444'; el.innerText = '❌ خطأ في الاتصال'; });
    }

    function doChangeFloor() {
        const floor = document.getElementById('floor-select').value;
        fetch('/change-floor', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({floor: parseInt(floor)}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('floor-status', d.success ? '✅ ' + (d.message||'تم الانتقال للطابق ' + floor) : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus('floor-status', '❌ خطأ في الاتصال', false));
    }

    function doDirectionalMove(dir) {
        fetch('/directional-move', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({direction: dir}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('dir-move-status', d.success ? '✅ تم التحريك ' + dir : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus('dir-move-status', '❌ خطأ في الاتصال', false));
    }

    function doTipUser() {
        const username = document.getElementById('tip-user').value.trim().replace(/^@/,'');
        const amount = parseInt(document.getElementById('tip-amount').value);
        if (!username || !amount || amount < 1) { ctrlStatus('tip-status', '❌ أدخل اسم المستخدم والمبلغ', false); return; }
        fetch('/tip-user', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username, amount}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('tip-status', d.success ? '✅ ' + (d.message||'تم الإهداء') : '❌ ' + (d.error||'خطأ'), d.success);
            if (d.success) { document.getElementById('tip-user').value = ''; document.getElementById('tip-amount').value = ''; }
        }).catch(() => ctrlStatus('tip-status', '❌ خطأ في الاتصال', false));
    }

    function doWalletInfo() {
        fetch('/wallet-info', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('wallet-status', d.success ? '💰 ' + (d.message||'') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus('wallet-status', '❌ خطأ في الاتصال', false));
    }

    function doAllEmote() {
        const emote = document.getElementById('all-emote-id').value.trim();
        if (!emote) { ctrlStatus('all-emote-status', '❌ أدخل رقم أو معرف الحركة', false); return; }
        fetch('/all-emote', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({emote}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('all-emote-status', d.success ? '✅ ' + (d.message||'تم تطبيق الحركة على الجميع') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus('all-emote-status', '❌ خطأ في الاتصال', false));
    }

    function doVoiceBan(action) {
        const username = document.getElementById('voiceban-user').value.trim().replace(/^@/,'');
        if (!username) { ctrlStatus('voiceban-status', '❌ أدخل اسم المستخدم', false); return; }
        fetch('/voice-ban', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({action, username}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('voiceban-status', d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus('voiceban-status', '❌ خطأ في الاتصال', false));
    }

    function doRankUser() {
        const username = document.getElementById('rank-user').value.trim().replace(/^@/,'');
        const rank = document.getElementById('rank-select').value;
        if (!username) { ctrlStatus('rank-status', '❌ أدخل اسم المستخدم', false); return; }
        fetch('/grant-rank', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username, rank}) })
        .then(r => r.json()).then(d => {
            ctrlStatus('rank-status', d.success ? '✅ ' + (d.message||'تم منح الرتبة') : '❌ ' + (d.error||'خطأ'), d.success);
            if (d.success) document.getElementById('rank-user').value = '';
        }).catch(() => ctrlStatus('rank-status', '❌ خطأ في الاتصال', false));
    }

    function doLeaderboard() {
        const el = document.getElementById('leaderboard-status');
        el.style.color = 'var(--muted)'; el.innerText = '⏳ جاري التحميل...';
        fetch('/leaderboard', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({}) })
        .then(r => r.json()).then(d => {
            if (d.success && d.data) { el.style.color = '#a78bfa'; el.innerText = d.data; }
            else { el.style.color = '#ef4444'; el.innerText = '❌ ' + (d.error||'خطأ'); }
        }).catch(() => { el.style.color = '#ef4444'; el.innerText = '❌ خطأ في الاتصال'; });
    }

    function doRoomStats() {
        const el = document.getElementById('room-stats-status');
        el.style.color = 'var(--muted)'; el.innerText = '⏳ جاري التحميل...';
        fetch('/room-full-stats', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({}) })
        .then(r => r.json()).then(d => {
            if (d.success) { el.style.color = '#a78bfa'; el.innerText = d.message; }
            else { el.style.color = '#ef4444'; el.innerText = '❌ ' + (d.error||'خطأ'); }
        }).catch(() => { el.style.color = '#ef4444'; el.innerText = '❌ خطأ في الاتصال'; });
    }

    function doLocations(action) {
        const statusMap = {list:'locations-list-status', goto:'goto-location-status', delete:'del-location-status', save:'save-location-status'};
        const sid = statusMap[action];
        let body = {action};
        if (action === 'goto') body.name = document.getElementById('goto-location').value.trim();
        if (action === 'delete') body.name = document.getElementById('del-location').value.trim();
        if (action === 'save') body.name = document.getElementById('save-loc-name').value.trim();
        if ((action === 'goto' || action === 'delete' || action === 'save') && !body.name) {
            ctrlStatus(sid, '❌ أدخل اسم الموقع', false); return;
        }
        fetch('/manage-locations', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            const el = document.getElementById(sid);
            if (d.success) {
                el.style.color = action === 'list' ? '#a78bfa' : '#22c55e';
                el.innerText = d.message || '✅ تم';
                if (action === 'goto') document.getElementById('goto-location').value = '';
                if (action === 'delete') document.getElementById('del-location').value = '';
                if (action === 'save') document.getElementById('save-loc-name').value = '';
            } else { el.style.color = '#ef4444'; el.innerText = '❌ ' + (d.error||'خطأ'); }
            setTimeout(() => { el.innerText = ''; }, 5000);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doJail(action) {
        const statusMap = {jail:'jail-status', release:'release-status', list:'jail-list-status'};
        const sid = statusMap[action];
        let body = {action};
        if (action === 'jail') {
            body.username = document.getElementById('jail-user').value.trim().replace(/^@/,'');
            body.minutes = parseInt(document.getElementById('jail-minutes').value) || 5;
            if (!body.username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
        }
        if (action === 'release') {
            body.username = document.getElementById('release-user').value.trim().replace(/^@/,'');
            if (!body.username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
        }
        fetch('/jail-control', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doSwm(action) {
        const statusMap = {add:'swm-add-status', remove:'swm-remove-status', list:'swm-list-status'};
        const sid = statusMap[action];
        let body = {action};
        if (action === 'add') {
            body.username = document.getElementById('swm-add-user').value.trim().replace(/^@/,'');
            body.text = document.getElementById('swm-add-text').value.trim();
            if (!body.username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
        }
        if (action === 'remove') {
            body.username = document.getElementById('swm-remove-user').value.trim().replace(/^@/,'');
            if (!body.username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
        }
        fetch('/swm-control', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            ctrlStatus(sid, d.success ? '✅ ' + (d.message||'تم') : '❌ ' + (d.error||'خطأ'), d.success);
            if (d.success && action === 'add') { document.getElementById('swm-add-user').value = ''; document.getElementById('swm-add-text').value = ''; }
            if (d.success && action === 'remove') document.getElementById('swm-remove-user').value = '';
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    function doModAdmin(action) {
        const statusMap = {add:'add-mod-status', remove:'remove-mod-status', list:'mod-list-status'};
        const sid = statusMap[action];
        let body = {action};
        if (action === 'add') {
            body.username = document.getElementById('add-mod-user').value.trim().replace(/^@/,'');
            if (!body.username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
        }
        if (action === 'remove') {
            body.username = document.getElementById('remove-mod-user').value.trim().replace(/^@/,'');
            if (!body.username) { ctrlStatus(sid, '❌ أدخل اسم المستخدم', false); return; }
        }
        fetch('/manage-moderator', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) })
        .then(r => r.json()).then(d => {
            const el = document.getElementById(sid);
            if (d.success) {
                el.style.color = action === 'list' ? '#a78bfa' : '#22c55e';
                el.innerText = d.message || '✅ تم';
                if (action === 'add') document.getElementById('add-mod-user').value = '';
                if (action === 'remove') document.getElementById('remove-mod-user').value = '';
            } else { el.style.color = '#ef4444'; el.innerText = '❌ ' + (d.error||'خطأ'); }
            setTimeout(() => { el.innerText = ''; }, 5000);
        }).catch(() => ctrlStatus(sid, '❌ خطأ في الاتصال', false));
    }

    setInterval(updateStats, 10000);
    updateStats();
</script>
</body>
</html>
    """)

@app.route('/stats')
def stats():
    try:
        with open('user_points.json', 'r') as f:
            points = len(json.load(f))
        with open('vip_list.json', 'r') as f:
            vips = len(json.load(f))
        with open('admins.json', 'r') as f:
            admins = len(json.load(f))
    except:
        points, vips, admins = 0, 0, 0
        
    return jsonify({
        "total_points": points,
        "vip_users": vips,
        "admins": admins
    })

@app.route('/send', methods=['POST'])
def send_message():
    global bot_instance
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({"success": False, "error": "Empty message"})
    
    if not bot_instance or not hasattr(bot_instance, 'highrise') or not bot_instance.highrise:
        return jsonify({"success": False, "error": "البوت غير متصل بالروم حالياً"})
    
    try:
        loop = None
        if hasattr(bot_instance, 'loop_ref') and bot_instance.loop_ref:
            loop = bot_instance.loop_ref
        
        if not loop:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                pass
        
        if loop and loop.is_running():
            # إرسال الرسالة باستخدام الوسائل المتاحة في SDK مباشرة
            def send_via_sdk():
                asyncio.run_coroutine_threadsafe(bot_instance.highrise.chat(message), loop)
            
            loop.call_soon_threadsafe(send_via_sdk)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "محرك البوت متوقف، يرجى إعادة تشغيل البوت"})
    except Exception as e:
        return jsonify({"success": False, "error": f"خطأ: {str(e)}"})

@app.route('/wear', methods=['POST'])
def wear_item():
    global bot_instance
    data = request.json
    category = data.get('category')
    item_id = data.get('item_id')
    
    if not item_id:
        return jsonify({"success": False, "error": "ID is missing"})
    
    if not bot_instance or not hasattr(bot_instance, 'highrise') or not bot_instance.highrise:
        return jsonify({"success": False, "error": "البوت غير متصل"})

    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if not loop:
            try:
                loop = asyncio.get_event_loop()
            except Exception:
                pass
        if loop and loop.is_running():
            current_category = category
            current_item_id = item_id.strip()

            async def update_outfit(cat, i_id):
                try:
                    current_outfit = await bot_instance.highrise.get_my_outfit()
                    new_outfit = list(current_outfit.outfit)
                    from highrise.models import Item as HRItem
                    new_outfit = [it for it in new_outfit if it.id != i_id]
                    new_outfit.append(HRItem(type="clothing", amount=1, id=i_id))
                    await bot_instance.highrise.set_outfit(new_outfit)
                    await bot_instance.highrise.chat(f"👗 تم ارتداء القطعة: {i_id}")
                    print(f"Outfit updated: {i_id}")
                except Exception as e:
                    print(f"Error updating outfit: {e}")

            asyncio.run_coroutine_threadsafe(update_outfit(current_category, current_item_id), loop)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "محرك البوت غير جاهز"})
    except Exception as e:
        print(f"Main wear_item error: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/outfits', methods=['GET'])
def get_outfits():
    try:
        with open("saved_outfits.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        outfits = []
        for slot_key in sorted(data.keys(), key=lambda x: int(x)):
            items = data[slot_key]
            if items:
                outfits.append({"slot": int(slot_key), "name": f"لبسة {slot_key}", "count": len(items)})
        return jsonify({"success": True, "outfits": outfits})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "outfits": []})

@app.route('/wear-outfit', methods=['POST'])
def wear_outfit():
    global bot_instance
    data = request.json
    slot = str(data.get('slot', ''))
    if not slot:
        return jsonify({"success": False, "error": "رقم اللبسة مفقود"})
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    try:
        with open("saved_outfits.json", "r", encoding="utf-8") as f:
            saved = json.load(f)
        if slot not in saved or not saved[slot]:
            return jsonify({"success": False, "error": f"لا توجد لبسة برقم {slot}"})
        items_data = saved[slot]
        loop = getattr(bot_instance, 'loop_ref', None)
        if not loop:
            try:
                loop = asyncio.get_event_loop()
            except Exception:
                pass
        if loop and loop.is_running():
            async def apply_outfit():
                try:
                    from highrise.models import Item as OutfitItem
                    outfit_items = [OutfitItem(id=d["id"], type=d["type"], amount=d["amount"], active_palette=d.get("active_palette")) for d in items_data]
                    await bot_instance.highrise.set_outfit(outfit_items)
                    await bot_instance.highrise.chat(f"👗 تم ارتداء اللبسة رقم {slot}")
                    print(f"[واجهة] تم ارتداء اللبسة رقم {slot}")
                except Exception as e:
                    print(f"[واجهة] خطأ في ارتداء اللبسة {slot}: {e}")
            asyncio.run_coroutine_threadsafe(apply_outfit(), loop)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "محرك البوت غير جاهز"})
    except Exception as e:
        print(f"wear_outfit error: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/room-control', methods=['POST'])
def room_control():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if not loop:
            try: loop = asyncio.get_event_loop()
            except: pass
        if not loop or not loop.is_running():
            return jsonify({"success": False, "error": "محرك البوت غير جاهز"})
        if action == 'lock':
            bot_instance.room_locked = True
            asyncio.run_coroutine_threadsafe(bot_instance.highrise.chat("🔒 تم قفل الغرفة من لوحة التحكم."), loop)
        elif action == 'unlock':
            bot_instance.room_locked = False
            asyncio.run_coroutine_threadsafe(bot_instance.highrise.chat("🔓 تم فتح الغرفة من لوحة التحكم."), loop)
        elif action == 'mute_all':
            bot_instance.mute_all_active = True
            asyncio.run_coroutine_threadsafe(bot_instance.highrise.chat("🔇 تم كتم الجميع من لوحة التحكم."), loop)
        elif action == 'unmute_all':
            bot_instance.mute_all_active = False
            asyncio.run_coroutine_threadsafe(bot_instance.highrise.chat("🔊 تم فك الكتم من لوحة التحكم."), loop)
        elif action == 'go_home':
            async def go_home_async():
                try:
                    if bot_instance.bot_start_position:
                        await bot_instance.highrise.teleport(bot_instance.highrise.my_id, bot_instance.bot_start_position)
                        await bot_instance.highrise.chat("🏠 رجعت لمكاني!")
                except Exception as e:
                    print(f"go_home error: {e}")
            asyncio.run_coroutine_threadsafe(go_home_async(), loop)
        else:
            return jsonify({"success": False, "error": "أمر غير معروف"})
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/set-dialect', methods=['POST'])
def set_dialect():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    dialect = data.get('dialect', '').strip()
    allowed = ["فصحى", "عراقية", "مصرية", "خليجية", "شامية"]
    if dialect not in allowed:
        return jsonify({"success": False, "error": "لهجة غير معروفة"})
    bot_instance.dialect = dialect
    async def notify_dialect():
        await bot_instance.highrise.chat(f"🗣️ تم تغيير اللهجة إلى: {dialect}")
    _run_async(notify_dialect())
    return jsonify({"success": True, "message": f"تم تغيير اللهجة إلى {dialect}"})

@app.route('/stop-announcement', methods=['POST'])
def stop_announcement():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    try:
        bot_instance.announcement_message = ""
        if hasattr(bot_instance, 'announcement_task') and bot_instance.announcement_task:
            bot_instance.announcement_task.cancel()
            bot_instance.announcement_task = None
        async def notify_stop():
            await bot_instance.highrise.chat("🛑 تم إيقاف الإعلانات التلقائية")
        _run_async(notify_stop())
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/strip-outfit', methods=['POST'])
def strip_outfit():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if not loop:
            try: loop = asyncio.get_event_loop()
            except: pass
        if not loop or not loop.is_running():
            return jsonify({"success": False, "error": "محرك البوت غير جاهز"})
        async def do_strip():
            try:
                from highrise.models import Item as HRItem
                body_items = ["body-flesh", "body-fat", "body-slim", "body-tall"]
                current = await bot_instance.highrise.get_my_outfit()
                kept = [it for it in current.outfit if any(it.id.startswith(b) for b in body_items)]
                await bot_instance.highrise.set_outfit(kept)
                await bot_instance.highrise.chat("🚫 تم خلع جميع الملابس")
            except Exception as e:
                print(f"strip error: {e}")
        asyncio.run_coroutine_threadsafe(do_strip(), loop)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/manage-vip', methods=['POST'])
def manage_vip():
    global bot_instance
    if not bot_instance:
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    if not username:
        return jsonify({"success": False, "error": "الرجاء إدخال اسم المستخدم"})
    try:
        if not hasattr(bot_instance, 'vip_list'):
            bot_instance.vip_list = []
        if action == 'add':
            if any(u.lower() == username.lower() for u in bot_instance.vip_list):
                return jsonify({"success": False, "error": f"@{username} موجود في VIP بالفعل"})
            bot_instance.vip_list.append(username)
            bot_instance.save_vip_list()
            async def chat_vip_add():
                await bot_instance.highrise.chat(f"💎 تم إضافة @{username} إلى قائمة VIP")
            _run_async(chat_vip_add())
            return jsonify({"success": True, "message": f"تم إضافة @{username} إلى VIP"})
        elif action == 'remove':
            match = next((u for u in bot_instance.vip_list if u.lower() == username.lower()), None)
            if not match:
                return jsonify({"success": False, "error": f"@{username} غير موجود في VIP"})
            bot_instance.vip_list.remove(match)
            bot_instance.save_vip_list()
            async def chat_vip_remove():
                await bot_instance.highrise.chat(f"💎 تم حذف @{username} من قائمة VIP")
            _run_async(chat_vip_remove())
            return jsonify({"success": True, "message": f"تم حذف @{username} من VIP"})
        else:
            return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/warning', methods=['POST'])
def manage_warning():
    global bot_instance
    if not bot_instance:
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    if not username:
        return jsonify({"success": False, "error": "الرجاء إدخال اسم المستخدم"})
    try:
        if not hasattr(bot_instance, 'user_warnings'):
            bot_instance.user_warnings = {}
        user_key = username.lower()
        existing = next((k for k in bot_instance.user_warnings if k.lower() == user_key or k == user_key), None)
        if action == 'add':
            key = existing or username
            bot_instance.user_warnings[key] = bot_instance.user_warnings.get(key, 0) + 1
            count = bot_instance.user_warnings[key]
            async def chat_warn_add():
                await bot_instance.highrise.chat(f"⚠️ تحذير {count}/3 لـ @{username}")
            _run_async(chat_warn_add())
            return jsonify({"success": True, "message": f"تحذير {count}/3 لـ @{username}"})
        elif action == 'remove':
            if not existing:
                return jsonify({"success": False, "error": f"لا توجد تحذيرات لـ @{username}"})
            current = bot_instance.user_warnings.get(existing, 0)
            if current > 0:
                bot_instance.user_warnings[existing] = current - 1
            new_count = max(0, current - 1)
            async def chat_warn_remove():
                await bot_instance.highrise.chat(f"✅ تم إزالة تحذير من @{username} ({new_count}/3)")
            _run_async(chat_warn_remove())
            return jsonify({"success": True, "message": f"تم تقليل تحذيرات @{username} إلى {new_count}/3"})
        elif action == 'check':
            count = bot_instance.user_warnings.get(existing, 0) if existing else 0
            async def chat_warn_check():
                await bot_instance.highrise.chat(f"🔍 تحذيرات @{username}: {count}/3")
            _run_async(chat_warn_check())
            return jsonify({"success": True, "message": f"تحذيرات @{username}: {count}/3"})
        else:
            return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/bot-action', methods=['POST'])
def bot_action():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    try:
        if action == 'restart':
            async def do_restart_chat():
                await bot_instance.highrise.chat("🔄 جاري إعادة تشغيل البوت...")
            _run_async(do_restart_chat())
            import threading, os, time
            def _exit_after():
                time.sleep(1.5)
                os._exit(1)
            threading.Thread(target=_exit_after, daemon=True).start()
            return jsonify({"success": True, "message": "جاري إعادة التشغيل... سيعود البوت خلال ثوانٍ"})
        elif action == 'kick_all':
            async def do_kick_all():
                await bot_instance.highrise.chat("⚠️ جاري طرد جميع المستخدمين العاديين...")
                room_users = await bot_instance.highrise.get_room_users()
                kicked = 0
                for u, _ in room_users.content:
                    if u.username in bot_instance.owners or u.username in bot_instance.admins or u.id == bot_instance.bot_id:
                        continue
                    try:
                        await bot_instance.highrise.moderate_room(u.id, "kick")
                        kicked += 1
                        import asyncio as _a; await _a.sleep(0.5)
                    except: pass
                await bot_instance.highrise.chat(f"✅ تم طرد {kicked} مستخدم")
            _run_async(do_kick_all())
            return jsonify({"success": True, "message": "جاري طرد الجميع..."})
        elif action == 'clear_chat':
            async def do_clear():
                await bot_instance.highrise.chat("🧹 مسح الشات...")
                import asyncio as _a
                for _ in range(20):
                    await bot_instance.highrise.chat("\n\n\n\n\n")
                    await _a.sleep(0.3)
            _run_async(do_clear())
            return jsonify({"success": True, "message": "جاري مسح الشات"})
        elif action == 'push_away':
            async def do_push():
                await bot_instance.highrise.chat("💨 جاري إبعاد الجميع...")
                import random, asyncio as _a
                from highrise import Position
                room_users = await bot_instance.highrise.get_room_users()
                count = 0
                for u, _ in room_users.content:
                    if u.username in bot_instance.owners or u.username in bot_instance.admins or u.id == bot_instance.bot_id:
                        continue
                    try:
                        x = random.uniform(0, 15)
                        z = random.uniform(0, 15)
                        await bot_instance.highrise.teleport(u.id, Position(x, 0, z, "FrontRight"))
                        count += 1
                        await _a.sleep(0.2)
                    except: pass
                await bot_instance.highrise.chat(f"✅ تم إبعاد {count} مستخدم")
            _run_async(do_push())
            return jsonify({"success": True, "message": "جاري إبعاد الجميع..."})
        else:
            return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/teleport-action', methods=['POST'])
def teleport_action():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    try:
        if action == 'go_to':
            if not username:
                return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
            async def do_goto():
                from highrise import Position
                room_users = await bot_instance.highrise.get_room_users()
                target = next((u for u, _ in room_users.content if u.username.lower() == username.lower()), None)
                if not target:
                    await bot_instance.highrise.chat(f"❌ المستخدم @{username} غير موجود في الغرفة")
                    return
                pos = next((p for u, p in room_users.content if u.id == target.id), None)
                if pos and hasattr(pos, 'x'):
                    await bot_instance.highrise.teleport(bot_instance.bot_id, pos)
                    await bot_instance.highrise.chat(f"🚀 انتقلت إلى @{username}")
            _run_async(do_goto())
            return jsonify({"success": True, "message": f"جاري الانتقال لـ @{username}"})
        elif action == 'pull':
            if not username:
                return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
            async def do_pull():
                from highrise import Position
                room_users = await bot_instance.highrise.get_room_users()
                target = next((u for u, _ in room_users.content if u.username.lower() == username.lower()), None)
                if not target:
                    await bot_instance.highrise.chat(f"❌ المستخدم @{username} غير موجود في الغرفة")
                    return
                bot_pos = next((p for u, p in room_users.content if u.id == bot_instance.bot_id), None)
                if bot_pos and hasattr(bot_pos, 'x'):
                    await bot_instance.highrise.teleport(target.id, bot_pos)
                    await bot_instance.highrise.chat(f"🧲 تم سحب @{username}")
            _run_async(do_pull())
            return jsonify({"success": True, "message": f"جاري سحب @{username}"})
        elif action == 'pull_all':
            async def do_pull_all():
                import asyncio as _a
                from highrise import Position
                room_users = await bot_instance.highrise.get_room_users()
                bot_pos = next((p for u, p in room_users.content if u.id == bot_instance.bot_id), None)
                if not bot_pos or not hasattr(bot_pos, 'x'):
                    bot_pos = Position(5.0, 0, 5.0, "FrontRight")
                count = 0
                for u, _ in room_users.content:
                    if u.id == bot_instance.bot_id: continue
                    try:
                        await bot_instance.highrise.teleport(u.id, bot_pos)
                        count += 1
                        await _a.sleep(0.3)
                    except: pass
                await bot_instance.highrise.chat(f"🌊 تم جلب {count} مستخدم")
            _run_async(do_pull_all())
            return jsonify({"success": True, "message": "جاري سحب الجميع..."})
        elif action == 'mic':
            if not username:
                return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
            async def do_mic():
                room_users = await bot_instance.highrise.get_room_users()
                target = next((u for u, _ in room_users.content if u.username.lower() == username.lower()), None)
                if not target:
                    await bot_instance.highrise.chat(f"❌ المستخدم @{username} غير موجود في الغرفة")
                    return
                try:
                    await bot_instance.highrise.invite_speaker(target.id)
                    await bot_instance.highrise.chat(f"🎤 تم إرسال دعوة المايك لـ @{username}")
                except Exception as e:
                    await bot_instance.highrise.chat(f"❌ خطأ: {e}")
            _run_async(do_mic())
            return jsonify({"success": True, "message": f"جاري دعوة @{username} للمايك"})
        else:
            return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/manage-admin', methods=['POST'])
def manage_admin():
    global bot_instance
    if not bot_instance:
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    try:
        if action == 'list':
            admins = list(bot_instance.admins) if hasattr(bot_instance, 'admins') else []
            return jsonify({"success": True, "admins": admins, "message": f"{len(admins)} أدمن"})
        if not username:
            return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
        if action == 'add':
            already = any(a.lower() == username.lower() for a in bot_instance.admins)
            if already:
                return jsonify({"success": False, "error": f"@{username} موجود مسبقاً في قائمة الأدمن"})
            if username in bot_instance.owners:
                return jsonify({"success": False, "error": f"@{username} مالك وله صلاحيات أعلى"})
            bot_instance.admins.append(username)
            bot_instance.save_admins()
            async def chat_add_admin():
                await bot_instance.highrise.chat(f"✅ تم إضافة @{username} كأدمن للبوت!")
            _run_async(chat_add_admin())
            return jsonify({"success": True, "message": f"تم إضافة @{username} كأدمن"})
        elif action == 'remove':
            match = next((a for a in bot_instance.admins if a.lower() == username.lower()), None)
            if not match:
                return jsonify({"success": False, "error": f"@{username} غير موجود في قائمة الأدمن"})
            bot_instance.admins.remove(match)
            bot_instance.save_admins()
            async def chat_rem_admin():
                await bot_instance.highrise.chat(f"❌ تم حذف @{username} من قائمة الأدمن")
            _run_async(chat_rem_admin())
            return jsonify({"success": True, "message": f"تم حذف @{username} من الأدمن"})
        else:
            return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/spam-control', methods=['POST'])
def spam_control():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    try:
        if action == 'start':
            msg = data.get('message', '').strip()
            if not msg:
                return jsonify({"success": False, "error": "أدخل نص الرسالة"})
            import asyncio as _asyncio
            bot_instance.spam_message = msg
            bot_instance.spam_active = True
            if bot_instance.spam_task and not bot_instance.spam_task.done():
                loop = getattr(bot_instance, 'loop_ref', None)
                if loop:
                    loop.call_soon_threadsafe(bot_instance.spam_task.cancel)
            async def start_spam():
                await bot_instance.highrise.chat(f"🔁 بدء تكرار: {msg}")
                bot_instance.spam_task = _asyncio.create_task(bot_instance.spam_loop())
            _run_async(start_spam())
            return jsonify({"success": True, "message": f"بدأ تكرار الرسالة"})
        elif action == 'stop':
            bot_instance.spam_active = False
            if bot_instance.spam_task and not bot_instance.spam_task.done():
                loop = getattr(bot_instance, 'loop_ref', None)
                if loop:
                    loop.call_soon_threadsafe(bot_instance.spam_task.cancel)
            async def stop_spam():
                await bot_instance.highrise.chat("⏹️ تم إيقاف تكرار الرسائل")
            _run_async(stop_spam())
            return jsonify({"success": True, "message": "تم إيقاف التكرار"})
        else:
            return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/quick-info', methods=['POST'])
def quick_info():
    global bot_instance
    import datetime
    data = request.json
    action = data.get('action', '')
    try:
        if action == 'ping':
            if not _bot_ready():
                return jsonify({"success": False, "error": "البوت غير متصل"})
            msg = "🏓 Pong! البوت يعمل بشكل ممتاز ✅"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        elif action == 'time':
            now = datetime.datetime.now().strftime('%H:%M:%S - %Y/%m/%d')
            msg = f"🕐 الوقت الحالي: {now}"
            if _bot_ready():
                _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        elif action == 'coords':
            if not _bot_ready():
                return jsonify({"success": False, "error": "البوت غير متصل"})
            pos = getattr(bot_instance, 'current_position', None) or getattr(bot_instance, 'bot_start_position', None)
            if pos:
                msg = f"📍 موقع البوت: X={pos.x:.1f} Y={pos.y:.1f} Z={pos.z:.1f}"
            else:
                msg = "📍 الموقع غير متاح حالياً"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        elif action == 'viplist':
            if not _bot_ready():
                return jsonify({"success": False, "error": "البوت غير متصل"})
            vips = list(getattr(bot_instance, 'vip_list', []))
            if not vips:
                msg = "💎 لا يوجد مستخدمو VIP حالياً"
            else:
                msg = "💎 VIP: " + " | ".join([f"@{v}" for v in vips[:15]])
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        elif action == 'roomusers':
            if not _bot_ready():
                return jsonify({"success": False, "error": "البوت غير متصل"})
            async def get_room_count():
                try:
                    room_users = await bot_instance.highrise.get_room_users()
                    count = len(room_users.content) if room_users and room_users.content else 0
                    await bot_instance.highrise.chat(f"👥 عدد المستخدمين في الغرفة: {count}")
                except Exception as e:
                    print(f"roomusers error: {e}")
            _run_async(get_room_count())
            return jsonify({"success": True, "message": "👥 جاري جلب عدد المستخدمين..."})
        elif action == 'totalpoints':
            if not _bot_ready():
                return jsonify({"success": False, "error": "البوت غير متصل"})
            points_data = getattr(bot_instance, 'user_points', {})
            total = sum(v for v in points_data.values() if isinstance(v, (int, float))) if points_data else 0
            msg = f"⭐ إجمالي النقاط المخزنة: {total:,}"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/move-bot', methods=['POST'])
def move_bot():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    try:
        if action == 'move':
            x = float(data.get('x', 0))
            y = float(data.get('y', 0))
            z = float(data.get('z', 0))
            async def do_move():
                from highrise import Position
                pos = Position(x, y, z)
                await bot_instance.highrise.teleport(bot_instance.highrise.my_id, pos)
                await bot_instance.highrise.chat(f"🚀 انتقلت إلى ({x:.1f}, {y:.1f}, {z:.1f})")
            _run_async(do_move())
            return jsonify({"success": True, "message": f"🚀 انتقلت لـ ({x:.1f}, {y:.1f}, {z:.1f})"})
        elif action == 'fix':
            x = float(data.get('x', 0))
            y = float(data.get('y', 0))
            z = float(data.get('z', 0))
            from highrise import Position
            bot_instance.fixed_position = Position(x, y, z)
            bot_instance.position_fixed = True
            async def do_fix():
                from highrise import Position
                await bot_instance.highrise.teleport(bot_instance.highrise.my_id, Position(x, y, z))
                await bot_instance.highrise.chat(f"📌 تم تثبيت موقعي على ({x:.1f}, {y:.1f}, {z:.1f})")
            _run_async(do_fix())
            return jsonify({"success": True, "message": f"📌 تثبيت عند ({x:.1f}, {y:.1f}, {z:.1f})"})
        elif action == 'unfix':
            bot_instance.position_fixed = False
            bot_instance.fixed_position = None
            async def do_unfix():
                await bot_instance.highrise.chat("🔓 تم تحرير البوت من التثبيت!")
            _run_async(do_unfix())
            return jsonify({"success": True, "message": "🔓 تم تحرير البوت"})
        return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/calculate', methods=['POST'])
def calculate():
    global bot_instance
    data = request.json
    expr = data.get('expression', '').strip()
    if not expr:
        return jsonify({"success": False, "error": "أدخل عملية حسابية"})
    try:
        allowed = set('0123456789+-*/().% ')
        if not all(c in allowed for c in expr):
            return jsonify({"success": False, "error": "رموز غير مسموحة - استخدم أرقاماً وعمليات حسابية فقط"})
        result = eval(expr, {"__builtins__": {}}, {})
        msg = f"🧮 {expr} = {result}"
        if _bot_ready():
            _run_async(bot_instance.highrise.chat(msg))
        return jsonify({"success": True, "result": result})
    except ZeroDivisionError:
        return jsonify({"success": False, "error": "لا يمكن القسمة على صفر"})
    except Exception:
        return jsonify({"success": False, "error": "عملية حسابية غير صحيحة"})

@app.route('/manage-lord', methods=['POST'])
def manage_lord():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    lord_file = "lord_users.json"
    try:
        try:
            with open(lord_file, 'r', encoding='utf-8') as f:
                lords = json.load(f)
        except Exception:
            lords = []
        if action == 'list':
            if not lords:
                msg = "👑 لا يوجد لورد حالياً"
            else:
                msg = "👑 اللورد: " + " | ".join([f"@{l}" for l in lords])
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        if not username:
            return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
        if action == 'add':
            if any(l.lower() == username.lower() for l in lords):
                return jsonify({"success": False, "error": f"@{username} لورد بالفعل"})
            lords.append(username)
            with open(lord_file, 'w', encoding='utf-8') as f:
                json.dump(lords, f, ensure_ascii=False)
            if hasattr(bot_instance, 'vip_list') and username not in bot_instance.vip_list:
                bot_instance.vip_list.append(username)
                if hasattr(bot_instance, 'save_vip_list'):
                    bot_instance.save_vip_list()
            async def chat_add_lord():
                await bot_instance.highrise.chat(f"👑 تم منح @{username} رتبة لورد!")
            _run_async(chat_add_lord())
            return jsonify({"success": True, "message": f"✅ تم منح @{username} رتبة لورد"})
        elif action == 'remove':
            match = next((l for l in lords if l.lower() == username.lower()), None)
            if not match:
                return jsonify({"success": False, "error": f"@{username} ليس في قائمة اللورد"})
            lords.remove(match)
            with open(lord_file, 'w', encoding='utf-8') as f:
                json.dump(lords, f, ensure_ascii=False)
            async def chat_rem_lord():
                await bot_instance.highrise.chat(f"❌ تم سحب رتبة لورد من @{username}")
            _run_async(chat_rem_lord())
            return jsonify({"success": True, "message": f"✅ تم سحب رتبة لورد من @{username}"})
        return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/manage-points', methods=['POST'])
def manage_points():
    global bot_instance
    if not bot_instance:
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    try:
        points_data = getattr(bot_instance, 'user_points', {})
        if action == 'check':
            if not username:
                return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
            pts = points_data.get(username, 0)
            msg = f"⭐ نقاط @{username}: {pts:,}"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        elif action == 'add':
            if not username:
                return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
            amount = int(data.get('amount', 0))
            if amount <= 0:
                return jsonify({"success": False, "error": "أدخل عدد نقاط صحيح"})
            points_data[username] = points_data.get(username, 0) + amount
            if hasattr(bot_instance, 'save_points'):
                bot_instance.save_points()
            msg = f"⭐ تمت إضافة {amount} نقطة لـ @{username} (المجموع: {points_data[username]:,})"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        elif action == 'remove':
            if not username:
                return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
            amount = int(data.get('amount', 0))
            if amount <= 0:
                return jsonify({"success": False, "error": "أدخل عدد نقاط صحيح"})
            current = points_data.get(username, 0)
            points_data[username] = max(0, current - amount)
            if hasattr(bot_instance, 'save_points'):
                bot_instance.save_points()
            msg = f"⭐ تم خصم {amount} نقطة من @{username} (المجموع: {points_data[username]:,})"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/manage-protected', methods=['POST'])
def manage_protected():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    try:
        protected = getattr(bot_instance, 'special_protected', [])
        if action == 'list':
            if not protected:
                msg = "🛡️ قائمة المحميين فارغة"
            else:
                msg = "🛡️ المحميون: " + " | ".join([f"@{u}" for u in protected])
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        if not username:
            return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
        if action == 'add':
            if any(u.lower() == username.lower() for u in protected):
                return jsonify({"success": False, "error": f"@{username} محمي بالفعل"})
            protected.append(username)
            if hasattr(bot_instance, 'save_special_protected'):
                bot_instance.save_special_protected()
            msg = f"🛡️ تمت إضافة @{username} للمحميين"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        elif action == 'remove':
            match = next((u for u in protected if u.lower() == username.lower()), None)
            if not match:
                return jsonify({"success": False, "error": f"@{username} غير موجود في المحميين"})
            protected.remove(match)
            if hasattr(bot_instance, 'save_special_protected'):
                bot_instance.save_special_protected()
            msg = f"❌ تمت إزالة @{username} من المحميين"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/special-welcome', methods=['POST'])
def special_welcome():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    text = data.get('text', '').strip()
    try:
        welcomes = getattr(bot_instance, 'special_welcomes', {})
        if action == 'list':
            count = len(welcomes)
            msg = f"🎉 عدد الترحيبات الخاصة: {count}"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        if not username:
            return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
        if action == 'add':
            if not text:
                return jsonify({"success": False, "error": "أدخل نص رسالة الترحيب"})
            welcomes[username] = text
            if hasattr(bot_instance, 'save_special_welcomes'):
                bot_instance.save_special_welcomes()
            msg = f"🎉 تمت إضافة ترحيب خاص لـ @{username}"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        elif action == 'remove':
            match = next((k for k in welcomes if k.lower() == username.lower()), None)
            if not match:
                return jsonify({"success": False, "error": f"لا يوجد ترحيب خاص لـ @{username}"})
            del welcomes[match]
            if hasattr(bot_instance, 'save_special_welcomes'):
                bot_instance.save_special_welcomes()
            msg = f"🗑️ تم حذف الترحيب الخاص لـ @{username}"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/special-farewell', methods=['POST'])
def special_farewell():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    text = data.get('text', '').strip()
    try:
        farewells = getattr(bot_instance, 'special_farewells', {})
        if action == 'list':
            if not farewells:
                msg = "👋 لا توجد وداعات خاصة مسجلة"
            else:
                names = " | ".join([f"@{k}" for k in list(farewells.keys())[:10]])
                msg = f"👋 الوداعات الخاصة ({len(farewells)}): {names}"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        if not username:
            return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
        if action == 'add':
            if not text:
                return jsonify({"success": False, "error": "أدخل نص رسالة الوداع"})
            farewells[username] = text
            if hasattr(bot_instance, 'save_special_farewells'):
                bot_instance.save_special_farewells()
            msg = f"👋 تمت إضافة وداع خاص لـ @{username}"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        elif action == 'remove':
            match = next((k for k in farewells if k.lower() == username.lower()), None)
            if not match:
                return jsonify({"success": False, "error": f"لا يوجد وداع خاص لـ @{username}"})
            del farewells[match]
            if hasattr(bot_instance, 'save_special_farewells'):
                bot_instance.save_special_farewells()
            msg = f"🗑️ تم حذف الوداع الخاص لـ @{username}"
            _run_async(bot_instance.highrise.chat(msg))
            return jsonify({"success": True, "message": msg})
        return jsonify({"success": False, "error": "أمر غير معروف"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def _run_async(coro):
    global bot_instance
    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if not loop:
            import asyncio as _asyncio
            try:
                loop = _asyncio.get_event_loop()
            except Exception:
                pass
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, loop)
            return True
        else:
            import asyncio as _aio
            import inspect
            if inspect.iscoroutine(coro):
                coro.close()
    except Exception as e:
        print(f"_run_async error: {e}")
    return False

def _bot_ready():
    global bot_instance
    return bot_instance and hasattr(bot_instance, 'highrise') and bot_instance.highrise

@app.route('/kick', methods=['POST'])
def kick_user():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    if not username:
        return jsonify({"success": False, "error": "الرجاء إدخال اسم المستخدم"})
    async def do_kick():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    await bot_instance.highrise.moderate_room(u.id, "kick")
                    await bot_instance.highrise.chat(f"👢 تم طرد @{username}")
                    return
            await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"kick error: {e}")
    _run_async(do_kick())
    return jsonify({"success": True})

@app.route('/ban', methods=['POST'])
def ban_user():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    minutes = int(data.get('minutes', 60))
    if not username:
        return jsonify({"success": False, "error": "الرجاء إدخال اسم المستخدم"})
    async def do_ban():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    await bot_instance.highrise.moderate_room(u.id, "ban", minutes * 60)
                    await bot_instance.highrise.chat(f"🔨 تم حظر @{username} لمدة {minutes} دقيقة")
                    return
            await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"ban error: {e}")
    _run_async(do_ban())
    return jsonify({"success": True})

@app.route('/mute', methods=['POST'])
def mute_user():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    minutes = int(data.get('minutes', 10))
    if not username:
        return jsonify({"success": False, "error": "الرجاء إدخال اسم المستخدم"})
    async def do_mute():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    await bot_instance.highrise.moderate_room(u.id, "mute", minutes * 60)
                    await bot_instance.highrise.chat(f"🔇 تم كتم @{username} لمدة {minutes} دقيقة")
                    return
            await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"mute error: {e}")
    _run_async(do_mute())
    return jsonify({"success": True})

@app.route('/unmute', methods=['POST'])
def unmute_user():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    if not username:
        return jsonify({"success": False, "error": "الرجاء إدخال اسم المستخدم"})
    async def do_unmute():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    await bot_instance.highrise.moderate_room(u.id, "mute", 0)
                    await bot_instance.highrise.chat(f"🔊 تم فك كتم @{username}")
                    return
            await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"unmute error: {e}")
    _run_async(do_unmute())
    return jsonify({"success": True})

@app.route('/summon', methods=['POST'])
def summon_user():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    if not username:
        return jsonify({"success": False, "error": "الرجاء إدخال اسم المستخدم"})
    async def do_summon():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    await bot_instance.highrise.move_user_to_room(u.id, bot_instance.room_id)
                    await bot_instance.highrise.chat(f"📩 تم استدعاء @{username}")
                    return
            await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"summon error: {e}")
    _run_async(do_summon())
    return jsonify({"success": True})

@app.route('/announce', methods=['POST'])
def announce():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"success": False, "error": "الرجاء إدخال نص الإعلان"})
    msg = f"📢 إعلان: {text}"
    async def do_announce():
        await bot_instance.highrise.chat(msg)
    _run_async(do_announce())
    return jsonify({"success": True})

@app.route('/emote', methods=['POST'])
def send_emote():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    emote_id = data.get('emote_id', '').strip()
    if not emote_id:
        return jsonify({"success": False, "error": "الرجاء اختيار حركة"})
    async def do_emote():
        try:
            await bot_instance.highrise.send_emote(emote_id)
        except Exception as e:
            print(f"emote error: {e}")
    _run_async(do_emote())
    return jsonify({"success": True})

@app.route('/equip-user', methods=['POST'])
def equip_from_user():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    if not username:
        return jsonify({"success": False, "error": "الرجاء إدخال اسم المستخدم"})
    async def do_equip():
        try:
            user_info = await bot_instance.webapi.get_user(username)
            if user_info and hasattr(user_info, 'user') and user_info.user:
                uid = user_info.user.user_id
                outfit = await bot_instance.highrise.get_user_outfit(uid)
                await bot_instance.highrise.set_outfit(outfit=outfit.outfit)
                await bot_instance.highrise.chat(f"✅ تم نسخ ملابس @{username}")
            else:
                await bot_instance.highrise.chat(f"❌ لم يتم العثور على @{username}")
        except Exception as e:
            print(f"equip-user error: {e}")
            await bot_instance.highrise.chat(f"❌ خطأ أثناء نسخ الملابس")
    _run_async(do_equip())
    return jsonify({"success": True})

@app.route('/dance-cmd', methods=['POST'])
def dance_cmd():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '').strip()
    emote_map = {
        'stop':   ("idle-loop-sitfloor", "⏹️ تم إيقاف الحركة"),
        'sleep':  ("idle-floorsleeping", "😴 البوت نائم"),
        'ghost':  ("emote-float", "👻 وضع الجوست"),
        'kiss':   ("emote-kiss", "💋 بوسة من البوت"),
        'shy':    ("emote-shy", "😊 البوت خجول"),
        'dance':  ("idle-loop-tapdance", "💃 البوت يرقص"),
        'wave':   ("emote-wave", "👋 البوت يسلم"),
        'yes':    ("emote-yes", "✅ البوت موافق"),
        'think':  ("emote-think", "🤔 البوت يفكر"),
        'sad':    ("emote-sad", "😢 البوت حزين"),
        'happy':  ("idle-loop-happy", "😄 البوت سعيد"),
    }
    async def do_dance():
        try:
            if action in emote_map:
                emote_id, chat_msg = emote_map[action]
                await bot_instance.highrise.send_emote(emote_id)
                await bot_instance.highrise.chat(chat_msg)
        except Exception as e:
            print(f"dance-cmd error: {e}")
    _run_async(do_dance())
    return jsonify({"success": True})

@app.route('/room-users', methods=['GET'])
def room_users():
    global bot_instance
    if not _bot_ready():
        return jsonify({"success": False, "users": []})
    result = {"users": []}
    done = asyncio.Event()
    async def fetch():
        try:
            ru = await bot_instance.highrise.get_room_users()
            result["users"] = [{"username": u.username, "id": u.id} for u, _ in ru.content if u.id != bot_instance.bot_id]
        except Exception as e:
            print(f"room-users error: {e}")
        done.set()
    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if not loop:
            try:
                loop = asyncio.get_event_loop()
            except Exception:
                pass
        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(fetch(), loop)
            future.result(timeout=5)
        else:
            print("room-users: loop not running")
    except Exception as e:
        print(f"room-users fetch error: {e}")
    return jsonify({"success": True, "users": result["users"]})

@app.route('/private-message', methods=['POST'])
def private_message():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    text = data.get('text', '').strip()
    if not username or not text:
        return jsonify({"success": False, "error": "أدخل اسم المستخدم والرسالة"})
    async def do_pm():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    await bot_instance.highrise.send_whisper(u.id, text)
                    return
            await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"private-message error: {e}")
    _run_async(do_pm())
    return jsonify({"success": True})

@app.route('/private-message-all', methods=['POST'])
def private_message_all():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"success": False, "error": "أدخل نص الرسالة"})
    async def do_pm_all():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.id != bot_instance.bot_id:
                    try:
                        await bot_instance.highrise.send_whisper(u.id, text)
                    except Exception:
                        pass
        except Exception as e:
            print(f"private-message-all error: {e}")
    _run_async(do_pm_all())
    return jsonify({"success": True, "message": "تم إرسال الرسالة للجميع"})

@app.route('/follow-user', methods=['POST'])
def follow_user_route():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    async def do_follow():
        try:
            if action == 'stop':
                bot_instance.following_user = None
                await bot_instance.highrise.chat("⏹️ توقف عن المتابعة")
                return
            room_users = await bot_instance.highrise.get_room_users()
            for u, pos in room_users.content:
                if u.username.lower() == username.lower():
                    bot_instance.following_user = u.id
                    await bot_instance.highrise.teleport(bot_instance.bot_id, pos)
                    await bot_instance.highrise.chat(f"🔁 يتابع @{username}")
                    return
            await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"follow-user error: {e}")
    _run_async(do_follow())
    return jsonify({"success": True, "message": "تم" if action == 'stop' else f"يتابع {username}"})

@app.route('/user-info', methods=['POST'])
def user_info_route():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    if not username:
        return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
    result = {"done": False, "msg": ""}
    done_event = asyncio.Event()
    async def do_info():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, pos in room_users.content:
                if u.username.lower() == username.lower():
                    points = 0
                    try:
                        with open('user_points.json', 'r') as f:
                            pts = json.load(f)
                            points = pts.get(u.username, pts.get(u.id, 0))
                    except Exception:
                        pass
                    vip_status = "❌"
                    try:
                        with open('vip_list.json', 'r') as f:
                            vips = json.load(f)
                            if u.username in vips or u.id in vips:
                                vip_status = "✅"
                    except Exception:
                        pass
                    result["msg"] = f"👤 {u.username}\n🆔 {u.id}\n📍 ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})\n⭐ نقاط: {points}\n💎 VIP: {vip_status}"
                    result["done"] = True
                    return
            result["msg"] = f"❌ @{username} غير موجود في الغرفة"
            result["done"] = True
        except Exception as e:
            result["msg"] = f"خطأ: {e}"
            result["done"] = True
        finally:
            done_event.set()
    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(do_info(), loop)
            future.result(timeout=5)
    except Exception as e:
        print(f"user-info error: {e}")
    if result["done"]:
        return jsonify({"success": True, "message": result["msg"]})
    return jsonify({"success": False, "error": "فشل جلب المعلومات"})

@app.route('/change-floor', methods=['POST'])
def change_floor():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    floor = int(data.get('floor', 1))
    floor_positions = {
        1: Position(10.5, 6, 4),
        2: Position(9, 10, 3.50),
        3: Position(13.5, 15.10, 3.50),
        4: Position(13.5, 19.0, 3.50),
        5: Position(13.5, 23.0, 3.50),
    }
    if floor not in floor_positions:
        return jsonify({"success": False, "error": "رقم الطابق غير صحيح"})
    pos = floor_positions[floor]
    async def do_floor():
        try:
            await bot_instance.highrise.teleport(bot_instance.bot_id, pos)
        except Exception as e:
            print(f"change-floor error: {e}")
    _run_async(do_floor())
    return jsonify({"success": True, "message": f"تم الانتقال للطابق {floor}"})

@app.route('/directional-move', methods=['POST'])
def directional_move():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    direction = data.get('direction', '')
    async def do_dir_move():
        try:
            ru = await bot_instance.highrise.get_room_users()
            bot_pos = None
            for u, pos in ru.content:
                if u.id == bot_instance.bot_id:
                    bot_pos = pos
                    break
            if not bot_pos:
                return
            step = 1.0
            x, y, z = bot_pos.x, bot_pos.y, bot_pos.z
            if direction == '+x': x += step
            elif direction == '-x': x -= step
            elif direction == '+y': y += step
            elif direction == '-y': y -= step
            elif direction == '+z': z += step
            elif direction == '-z': z -= step
            await bot_instance.highrise.teleport(bot_instance.bot_id, Position(x, y, z))
        except Exception as e:
            print(f"directional-move error: {e}")
    _run_async(do_dir_move())
    return jsonify({"success": True})

@app.route('/tip-user', methods=['POST'])
def tip_user():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    amount = int(data.get('amount', 0))
    if not username or amount < 1:
        return jsonify({"success": False, "error": "أدخل اسم المستخدم والمبلغ"})
    async def do_tip():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    await bot_instance.highrise.tip_user(u.id, f"gold_bar_{amount}")
                    await bot_instance.highrise.chat(f"💰 تم إهداء {amount}g لـ @{username}")
                    return
            await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"tip-user error: {e}")
    _run_async(do_tip())
    return jsonify({"success": True, "message": f"تم إهداء {amount}g لـ {username}"})

@app.route('/wallet-info', methods=['POST'])
def wallet_info():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    result = {"msg": "", "done": False}
    async def do_wallet():
        try:
            wallet = await bot_instance.highrise.get_wallet()
            gold = next((c.amount for c in wallet.content if c.type == "gold"), 0)
            result["msg"] = f"💎 رصيد البوت: {gold}g"
            result["done"] = True
        except Exception as e:
            result["msg"] = f"خطأ: {e}"
            result["done"] = True
    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(do_wallet(), loop)
            future.result(timeout=5)
    except Exception as e:
        print(f"wallet-info error: {e}")
    if result["done"]:
        return jsonify({"success": True, "message": result["msg"]})
    return jsonify({"success": False, "error": "فشل جلب الرصيد"})

@app.route('/all-emote', methods=['POST'])
def all_emote():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    emote = data.get('emote', '').strip()
    if not emote:
        return jsonify({"success": False, "error": "أدخل معرف الحركة"})
    async def do_all_emote():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.id != bot_instance.bot_id:
                    try:
                        emote_id = f"emote-{emote}" if emote.isdigit() else emote
                        await bot_instance.highrise.send_emote(emote_id, u.id)
                    except Exception:
                        pass
        except Exception as e:
            print(f"all-emote error: {e}")
    _run_async(do_all_emote())
    return jsonify({"success": True, "message": f"تم تطبيق الحركة {emote} على الجميع"})

@app.route('/voice-ban', methods=['POST'])
def voice_ban():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    if not username:
        return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
    async def do_voice_ban():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    mod_action = "voice_mute" if action == 'ban' else "voice_unmute"
                    await bot_instance.highrise.moderate_room(u.id, mod_action)
                    msg = f"🔇 تم حظر صوت @{username}" if action == 'ban' else f"🔊 تم فك حظر صوت @{username}"
                    await bot_instance.highrise.chat(msg)
                    return
            await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"voice-ban error: {e}")
    _run_async(do_voice_ban())
    return jsonify({"success": True})

@app.route('/grant-rank', methods=['POST'])
def grant_rank():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    username = data.get('username', '').lstrip('@').strip()
    rank = data.get('rank', '')
    if not username or not rank:
        return jsonify({"success": False, "error": "أدخل اسم المستخدم والرتبة"})
    async def do_rank():
        try:
            if rank == 'vip':
                try:
                    with open('vip_list.json', 'r') as f:
                        vips = json.load(f)
                except Exception:
                    vips = []
                if username not in vips:
                    vips.append(username)
                    with open('vip_list.json', 'w') as f:
                        json.dump(vips, f)
                await bot_instance.highrise.chat(f"💎 تم منح رتبة VIP لـ @{username}")
            elif rank == 'vvip':
                room_users = await bot_instance.highrise.get_room_users()
                for u, _ in room_users.content:
                    if u.username.lower() == username.lower():
                        vvip_pos = Position(x=14.5, y=6.25, z=27.0)
                        await bot_instance.highrise.teleport(u.id, vvip_pos)
                        await bot_instance.highrise.chat(f"🚀 تم نقل @{username} إلى منطقة VVIP")
                        return
                await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
            elif rank == 'lord':
                room_users = await bot_instance.highrise.get_room_users()
                for u, _ in room_users.content:
                    if u.username.lower() == username.lower():
                        lord_pos = None
                        if hasattr(bot_instance, 'teleport_locations') and 'لورد' in bot_instance.teleport_locations:
                            lord_pos = bot_instance.teleport_locations['لورد']
                        else:
                            lord_pos = Position(x=4.7, y=16.5, z=4.5)
                        await bot_instance.highrise.teleport(u.id, lord_pos)
                        await bot_instance.highrise.chat(f"👑 تم نقل @{username} إلى منطقة اللورد")
                        return
                await bot_instance.highrise.chat(f"❌ @{username} غير موجود في الغرفة")
        except Exception as e:
            print(f"grant-rank error: {e}")
    _run_async(do_rank())
    return jsonify({"success": True, "message": f"تم منح رتبة {rank} لـ {username}"})

@app.route('/leaderboard', methods=['POST'])
def leaderboard():
    try:
        with open('user_points.json', 'r') as f:
            pts = json.load(f)
        sorted_pts = sorted(pts.items(), key=lambda x: x[1], reverse=True)[:10]
        lines = ["🏆 أعلى 10 مستخدمين:"]
        medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
        for i, (name, score) in enumerate(sorted_pts):
            lines.append(f"{medals[i]} {name}: {score} نقطة")
        return jsonify({"success": True, "data": "\n".join(lines)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/room-full-stats', methods=['POST'])
def room_full_stats():
    stats = {}
    try:
        with open('user_points.json', 'r') as f: pts = json.load(f)
        stats['total_points'] = sum(pts.values())
        stats['users_with_points'] = len(pts)
    except Exception: stats['total_points'] = 0; stats['users_with_points'] = 0
    try:
        with open('vip_list.json', 'r') as f: vips = json.load(f)
        stats['vip_count'] = len(vips)
    except Exception: stats['vip_count'] = 0
    try:
        with open('admins.json', 'r') as f: admins = json.load(f)
        stats['admin_count'] = len(admins)
    except Exception: stats['admin_count'] = 0
    try:
        with open('jailed_users.json', 'r') as f: jailed = json.load(f)
        stats['jailed_count'] = len(jailed)
    except Exception: stats['jailed_count'] = 0
    msg = (f"📊 إحصائيات الغرفة:\n"
           f"⭐ إجمالي النقاط: {stats['total_points']}\n"
           f"👥 مستخدمون بنقاط: {stats['users_with_points']}\n"
           f"💎 VIP: {stats['vip_count']}\n"
           f"🛡️ أدمن: {stats['admin_count']}\n"
           f"⛓️ مسجونون: {stats['jailed_count']}")
    return jsonify({"success": True, "message": msg})

@app.route('/manage-locations', methods=['POST'])
def manage_locations():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    name = data.get('name', '').strip()
    if action == 'list':
        try:
            locs = list(bot_instance.teleport_locations.keys()) if hasattr(bot_instance, 'teleport_locations') else []
            if not locs:
                return jsonify({"success": True, "message": "لا توجد مواقع محفوظة"})
            return jsonify({"success": True, "message": "📍 المواقع: " + "، ".join(locs)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    if not name:
        return jsonify({"success": False, "error": "أدخل اسم الموقع"})
    result = {"done": False, "msg": ""}
    async def do_loc():
        try:
            if action == 'goto':
                if hasattr(bot_instance, 'teleport_locations') and name in bot_instance.teleport_locations:
                    pos = bot_instance.teleport_locations[name]
                    await bot_instance.highrise.teleport(bot_instance.bot_id, pos)
                    result["msg"] = f"✅ انتقل إلى موقع '{name}'"
                else:
                    result["msg"] = f"❌ الموقع '{name}' غير موجود"
            elif action == 'delete':
                if hasattr(bot_instance, 'teleport_locations') and name in bot_instance.teleport_locations:
                    del bot_instance.teleport_locations[name]
                    bot_instance.save_teleport_locations()
                    result["msg"] = f"✅ تم حذف موقع '{name}'"
                else:
                    result["msg"] = f"❌ الموقع '{name}' غير موجود"
            elif action == 'save':
                ru = await bot_instance.highrise.get_room_users()
                for u, pos in ru.content:
                    if u.id == bot_instance.bot_id:
                        if not hasattr(bot_instance, 'teleport_locations'):
                            bot_instance.teleport_locations = {}
                        bot_instance.teleport_locations[name] = pos
                        bot_instance.save_teleport_locations()
                        result["msg"] = f"✅ تم حفظ موقع '{name}'"
                        return
                result["msg"] = "❌ لم يتم العثور على موقع البوت"
            result["done"] = True
        except Exception as e:
            result["msg"] = f"خطأ: {e}"
            result["done"] = True
    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(do_loc(), loop)
            future.result(timeout=5)
    except Exception as e:
        print(f"manage-locations error: {e}")
    return jsonify({"success": True, "message": result["msg"]})

@app.route('/jail-control', methods=['POST'])
def jail_control():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    minutes = int(data.get('minutes', 5))
    if action == 'list':
        try:
            with open('jailed_users.json', 'r') as f:
                jailed = json.load(f)
            if not jailed:
                return jsonify({"success": True, "message": "لا يوجد مسجونون حالياً"})
            names = list(jailed.keys()) if isinstance(jailed, dict) else jailed
            return jsonify({"success": True, "message": "⛓️ المسجونون: " + "، ".join(names)})
        except Exception:
            return jsonify({"success": True, "message": "لا يوجد مسجونون"})
    if not username:
        return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
    result = {"done": False, "msg": ""}
    async def do_jail():
        try:
            room_users = await bot_instance.highrise.get_room_users()
            target_user = None
            for u, _ in room_users.content:
                if u.username.lower() == username.lower():
                    target_user = u
                    break
            if not target_user:
                result["msg"] = f"❌ @{username} غير موجود في الغرفة"
                result["done"] = True
                return
            if action == 'jail':
                jail_pos = Position(x=50.5, y=0, z=2.5, facing='FrontLeft')
                await bot_instance.highrise.teleport(target_user.id, jail_pos)
                bot_instance.jail_user(target_user.id, minutes)
                await bot_instance.highrise.chat(f"🔒 تم سجن @{username} لمدة {minutes} دقيقة ⛓️")
                result["msg"] = f"⛓️ تم سجن @{username} لمدة {minutes} دقيقة"
            elif action == 'release':
                if target_user.id in bot_instance.jailed_users:
                    del bot_instance.jailed_users[target_user.id]
                await bot_instance.highrise.chat(f"🔓 تم إطلاق سراح @{username}")
                result["msg"] = f"🔓 تم إطلاق سراح @{username}"
            result["done"] = True
        except Exception as e:
            print(f"jail-control error: {e}")
            result["msg"] = str(e)
            result["done"] = True
    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(do_jail(), loop)
            future.result(timeout=8)
    except Exception as e:
        print(f"jail-control timeout: {e}")
    msg = result["msg"] or (f"⛓️ تم سجن @{username} لمدة {minutes} دقيقة" if action == 'jail' else f"🔓 تم إطلاق سراح @{username}")
    return jsonify({"success": True, "message": msg})

@app.route('/swm-control', methods=['POST'])
def swm_control():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    text = data.get('text', '').strip()
    if action == 'list':
        try:
            welcomes = getattr(bot_instance, 'special_welcomes', {})
            if not welcomes:
                return jsonify({"success": True, "message": "لا توجد اشتراكات SWM حالياً"})
            names = list(welcomes.keys())
            return jsonify({"success": True, "message": "📢 اشتراكات SWM:\n" + "\n".join(f"• {n}" for n in names)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    if not username:
        return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
    try:
        if action == 'add':
            if not hasattr(bot_instance, 'special_welcomes'):
                bot_instance.special_welcomes = {}
            welcome_text = text if text else f"@{username} مرحباً بك! 🎉"
            bot_instance.special_welcomes[username] = welcome_text
            if hasattr(bot_instance, 'save_special_welcomes'):
                bot_instance.save_special_welcomes()
            return jsonify({"success": True, "message": f"✅ تم إضافة SWM لـ @{username}"})
        elif action == 'remove':
            if hasattr(bot_instance, 'special_welcomes') and username in bot_instance.special_welcomes:
                del bot_instance.special_welcomes[username]
                if hasattr(bot_instance, 'save_special_welcomes'):
                    bot_instance.save_special_welcomes()
                return jsonify({"success": True, "message": f"✅ تم حذف SWM لـ @{username}"})
            else:
                return jsonify({"success": False, "error": f"@{username} غير موجود في قائمة SWM"})
    except Exception as e:
        print(f"swm-control error: {e}")
        return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "error": "إجراء غير معروف"})

@app.route('/manage-moderator', methods=['POST'])
def manage_moderator():
    if not _bot_ready():
        return jsonify({"success": False, "error": "البوت غير متصل"})
    data = request.json
    action = data.get('action', '')
    username = data.get('username', '').lstrip('@').strip()
    if action == 'list':
        try:
            with open('admins.json', 'r') as f:
                mods = json.load(f)
            if not mods:
                return jsonify({"success": True, "message": "لا يوجد مشرفون"})
            return jsonify({"success": True, "message": "🎖️ المشرفون: " + "، ".join(mods)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    if not username:
        return jsonify({"success": False, "error": "أدخل اسم المستخدم"})
    result = {"done": False, "msg": ""}
    async def do_mod():
        try:
            target_user_id = None
            try:
                user_info = await bot_instance.webapi.get_users(username=username, limit=1)
                if user_info and hasattr(user_info, 'users') and user_info.users:
                    target_user_id = user_info.users[0].user_id
            except Exception:
                pass
            if not target_user_id:
                room_users = await bot_instance.highrise.get_room_users()
                for ru, _ in room_users.content:
                    if ru.username.lower() == username.lower():
                        target_user_id = ru.id
                        break
            if not target_user_id:
                result["msg"] = f"❌ لم يتم العثور على @{username}"
                result["done"] = True
                return
            permissions = await bot_instance.highrise.get_room_privilege(target_user_id)
            if action == 'add':
                permissions.moderator = True
                await bot_instance.highrise.change_room_privilege(target_user_id, permissions)
                await bot_instance.highrise.chat(f"🎖️ تم ترقية @{username} إلى مشرف")
                result["msg"] = f"✅ تم إضافة @{username} كمشرف"
            elif action == 'remove':
                permissions.moderator = False
                await bot_instance.highrise.change_room_privilege(target_user_id, permissions)
                await bot_instance.highrise.chat(f"🚫 تم إزالة صلاحيات الإشراف عن @{username}")
                result["msg"] = f"✅ تم إزالة @{username} من المشرفين"
            result["done"] = True
        except Exception as e:
            print(f"manage-moderator error: {e}")
            result["msg"] = str(e)
            result["done"] = True
    try:
        loop = getattr(bot_instance, 'loop_ref', None)
        if loop and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(do_mod(), loop)
            future.result(timeout=8)
    except Exception as e:
        print(f"manage-moderator timeout: {e}")
    msg = result["msg"] or (f"✅ تم إضافة @{username} كمشرف" if action == 'add' else f"✅ تم إزالة @{username} من المشرفين")
    success = not result["msg"].startswith("❌") if result["msg"] else True
    return jsonify({"success": success, "message": msg, "error": msg if not success else None})

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def self_ping_loop():
    import urllib.request
    import time as _time
    _time.sleep(30)
    while True:
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/ping", timeout=10)
        except Exception:
            pass
        try:
            urllib.request.urlopen("http://127.0.0.1:8080/ping", timeout=10)
        except Exception:
            pass
        _time.sleep(240)

class Bot(BaseBot):
    def __init__(self):
        super().__init__()
        # تسجيل مثيل البوت عالمياً فور الإنشاء
        global bot_instance
        bot_instance = self
        try:
            if WebApi:
                self.webapi = WebApi()
                print("WebApi initialized successfully")
            else:
                self.webapi = None
                print("WebApi is not available")
        except Exception as e:
            print(f"WebApi initialization failed: {e}")
            self.webapi = None
        self.emote_looping = False
        self.user_emote_loops = {}
        self.loop_task = None
        self.dance_active = True
        self.is_teleporting_dict = {}
        self.following_user = None
        self.following_user_id = None
        self.following_username = None
        self.original_room_id = RunBot.room_id  # الغرفة الأصلية
        self.pending_follow = False  # حالة الانتقال للغرفة الجديدة
        self.kus = {}
        self.user_positions = {} 
        self.position_tasks = {} 
        self.owners = ["_king_man_1" , "LORD_2007"]  # قائمة الأونرز
        self.owner_id = None  # Will be set when we get the owner's user ID
        self.silent_mode = False  # وضع الصمت
        self.frozen_users = {}  # المستخدمون المجمّدون
        self.warn_count = {}  # عدد التحذيرات لكل مستخدم
        self.special_welcomes = self.load_special_welcomes()  # قاموس الترحيبات الخاصة
        self.spam_active = False  # حالة الـ spam
        self.spam_message = ""  # الرسالة المراد تكرارها
        self.spam_task = None  # مهمة الـ spam
        self.start_time = None  # وقت دخول البوت للروم
        self.receiver_username = None  # متغير لحفظ اسم المستقبل
        self.bot_id = None  # معرف البوت
        self.vips = []  # قائمة المستخدمين المميزين
        self.saved_position = None  # موقع المستخدم المحفوظ
        self.saved_user_id = None  # معرف المستخدم الذي حفظ الموقع
        self.bot_start_position = self.load_bot_position()  # موقع البوت المحفوظ
        self.vip_list = self.load_vip_list()  # قائمة VIP المحفوظة من الملف
        self.teleport_locations = self.load_teleport_locations()
        self.admins = self.load_admins()  # قائمة الأدمن
        self.teleport_on_click = {}  # قاموس لتتبع حالة النقل التلقائي لكل مستخدم (False افتراضياً)
        self.user_last_floor = {}  # قاموس لتتبع آخر طابق لكل مستخدم
        self.special_protected = self.load_special_protected()  # قائمة المحميين الخاصين
        self.jailed_users = {}  # قاموس للمستخدمين المسجونين مؤقتاً {user_id: end_time}
        self.user_points = self.load_user_points()  # قاموس لنقاط المستخدمين
        self.vip_uses = self.load_vip_uses()  # تتبع عدد استخدامات VIP المتبقية
        self.user_warnings = self.load_user_warnings()  # نظام التحذيرات
        self.special_farewells = self.load_special_farewells()  # قاموس الوداع الخاص
        self.owner_protected = False  # حماية المالك من الأوامر
        self.shoe_rotation = self.load_shoe_rotation()  # قائمة تدوير الأحذية (قديم)
        self.current_shoe_index = self.shoe_rotation.get("current_index", 0)  # الحذاء الحالي
        self.shoes_list = self.load_shoes_list()  # قائمة الأحذية الجديدة
        self.shoes_index = 0  # رقم الحذاء الحالي
        self.announcement_message = ""
        self.announcement_task = None
        self.room_locked = False
        self.subscribers = self.load_subscribers()  # {user_id: username} للمستخدمين المشتركين
        self.subscription_task = None
        self.mute_all_active = False
        self.chat_locked = False
        self.admin_log = []  # سجل آخر الإجراءات الإدارية
        self.last_heartbeat = time.time()  # آخر نبضة حياة للاتصال
        self.translator = Translator()
        self.saved_outfits = self.load_saved_outfits()  # ملابس محفوظة
        self.eyes_list = self.load_eyes_list()  # قائمة العيون
        self.tshirts_list = self.load_tshirts_list()  # قائمة التيشيرتات
        self.hair_list = self.load_hair_list()  # قائمة التسريحات
        self.glasses_list = self.load_glasses_list()  # قائمة النظارات
        self.eyebrows_list = self.load_eyebrows_list()  # قائمة الحواجب
        self.mouth_list = self.load_mouth_list()  # قائمة الفم
        self.lip_color_list = self.load_lip_color_list()  # قائمة لون الفم
        self.pants_list = self.load_pants_list()  # قائمة البناطيل
        self.nose_list = self.load_nose_list()  # قائمة الأنوف
        self.hand_list = self.load_hand_list()  # قائمة الأيدي
        self.bear_list = self.load_bear_list()  # قائمة الدببة
        self.accessories_list = self.load_accessories_list()  # قائمة الإكسسوارات
        self.tattoo_list = self.load_tattoo_list()  # قائمة الوشوم
        self.features_list = self.load_features_list()  # قائمة الملامح
        self.invisible_list = self.load_invisible_list()  # قائمة الاختفاء
        self.hat_list = self.load_hat_list()  # قائمة القبعات
        self.disguise_mode = False
        self.disguise_task = None
        self.laugh_active = False
        self.laugh_task = None
        self.ghost_active = False
        self.ghost_task = None
        self.dialect = "فصحى"  # اللهجة الحالية: فصحى، عراقية، مصرية، خليجية، شامية
        self.filtered_words = self.load_filtered_words()  # قائمة الكلمات المحظورة
        self.autokick_minutes = 0  # 0 = معطل، أي رقم آخر = عدد دقائق الخمول قبل الطرد
        self.autokick_task = None  # مهمة الطرد التلقائي
        self.user_last_active = {}  # {user_id: timestamp} آخر نشاط لكل مستخدم
        self.bot_lang = self.load_bot_lang()  # لغة ردود البوت: ar أو en (محفوظة)
        self.user_lang_prefs = self.load_user_lang_prefs()  # تفضيلات لغة كل مستخدم
        self.tip_history = self.load_tip_history()  # {username: total_amount} إجمالي تبرعات كل مستخدم
        self.user_wallets = self.load_user_wallets()  # {user_id: balance} محفظة كل مستخدم
        self.pending_bot_purchases = {}  # {user_id: {"step": "waiting_room", "package": "...", "amount": 0}}
        self.bot_shop_orders = self.load_bot_shop_orders()
        self.auto_tip_active = False        # تفعيل الإكرامية التلقائية لجميع المستخدمين
        self.auto_tip_amount = 0            # مبلغ الإكرامية التلقائية
        self.auto_tip_vip_active = False    # تفعيل التبرع التلقائي للأعضاء المميزين
        self.auto_tip_vip_amount = 0        # مبلغ التبرع التلقائي للأعضاء المميزين
        self.bot_blacklist = self.load_blacklist()  # القائمة السوداء - محظوري البوت نهائياً
        self.dance_zone_active = False          # تفعيل منطقة الرقص
        self.dance_zone_pos = None              # مركز منطقة الرقص (Position)
        self.dance_zone_radius = 4.0            # نصف قطر منطقة الرقص
        self.dance_zone_users = set()           # معرفات المستخدمين الموجودين حالياً في المنطقة
        self.dance_zone_scanner_task = None     # مهمة المسح الدوري لمنطقة الرقص

    # ==================== باقات متجر البوت ====================
    BOT_PACKAGES = {
        1:     {"name": "⏱️ ساعة واحدة",  "duration": "1 ساعة",  "hours": 1},
        3000:  {"name": "⏱️ 3 ساعات",      "duration": "3 ساعات", "hours": 3},
        10000: {"name": "📅 يوم كامل",      "duration": "24 ساعة", "hours": 24},
        50000: {"name": "📅 أسبوع كامل",   "duration": "7 أيام",  "hours": 168},
    }

    haricler = ["_king_man_1", "", "", "", "", "", "", "", ""]

    dans = [
        "dance-floss",    
    ]

    name_ad = ["_king_man_1"]  # قائمة الأسماء المسموح لها باستخدام الريآكشن

    def is_user_protected(self, username: str) -> bool:
        """التحقق مما إذا كان المستخدم محميًا"""
        if not username:
            return False
        username_lower = username.lower()
        # حماية الأونرز
        if any(o.lower() == username_lower for o in self.owners):
            return True
        # حماية المحميين الخاصين
        if any(p.lower() == username_lower for p in self.special_protected):
            return True
        # حماية البوت نفسه
        if hasattr(self, 'bot_id') and username_lower == "highrise_bot":
            return True
        return False

    # ==================== نظام اللهجات ====================
    DIALECT_MAPS = {
        "عراقية": {
            "أنا": "أني", "أنت": "إنت", "أنتَ": "إنت", "أنتِ": "إنتِ",
            "هو": "هو", "هي": "هي", "نحن": "إحنا", "أنتم": "إنتو",
            "هم": "هم", "ماذا": "شنو", "لماذا": "ليش", "كيف": "شلون",
            "أين": "وين", "متى": "شوقت", "من": "مني", "ما": "ماكو",
            "لا": "لا", "نعم": "أي", "ربما": "بلكي", "الآن": "هسه",
            "جيد": "زين", "ممتاز": "رائح", "مرحبا": "هلو", "شكراً": "مشكور",
            "تفضل": "تفضل", "حسناً": "زين", "فقط": "بس", "هذا": "هاذا",
            "هذه": "هاذي", "ذلك": "ذاك", "تلك": "تلك", "الذي": "الي",
            "التي": "الي", "ماهو": "شنو", "ماهي": "شنو", "قليل": "شوية",
            "كثير": "هواية", "بعد": "بعدين", "قبل": "قبل",
            "يريد": "يريد", "أريد": "أريد", "تريد": "تريد",
            "موجود": "موجود", "غير موجود": "ماكو", "لا يوجد": "ماكو",
            "يوجد": "اكو", "طيب": "زين", "صح": "صاح",
        },
        "مصرية": {
            "أنا": "أنا", "أنت": "إنت", "أنتَ": "إنت", "أنتِ": "إنتِ",
            "نحن": "إحنا", "أنتم": "إنتو", "ماذا": "إيه", "لماذا": "ليه",
            "كيف": "إزاي", "أين": "فين", "متى": "إمتى", "من": "مين",
            "لا": "لأ", "نعم": "أيوه", "ربما": "يمكن", "الآن": "دلوقتي",
            "جيد": "كويس", "ممتاز": "تمام", "مرحبا": "أهلاً", "شكراً": "شكراً",
            "تفضل": "اتفضل", "حسناً": "تمام", "فقط": "بس", "هذا": "ده",
            "هذه": "دي", "ذلك": "ده", "تلك": "دي", "الذي": "اللي",
            "التي": "اللي", "قليل": "شوية", "كثير": "أوي",
            "بعد": "بعدين", "موجود": "موجود", "لا يوجد": "مفيش",
            "يوجد": "فيه", "طيب": "طب", "صح": "صح",
        },
        "خليجية": {
            "أنا": "أنا", "أنت": "إنت", "أنتَ": "إنت", "أنتِ": "إنتي",
            "نحن": "إحنا", "أنتم": "إنتو", "ماذا": "وش", "لماذا": "ليش",
            "كيف": "كيف", "أين": "وين", "متى": "متى", "من": "منو",
            "لا": "لا", "نعم": "إي", "ربما": "يمكن", "الآن": "الحين",
            "جيد": "زين", "ممتاز": "عالي", "مرحبا": "هلا", "شكراً": "مشكور",
            "تفضل": "تفضل", "حسناً": "زين", "فقط": "بس", "هذا": "هذا",
            "هذه": "هذي", "الذي": "اللي", "التي": "اللي",
            "قليل": "شوي", "كثير": "واجد", "بعد": "بعدين",
            "موجود": "موجود", "لا يوجد": "مافي", "يوجد": "في",
            "طيب": "طيب", "صح": "صح",
        },
        "شامية": {
            "أنا": "أنا", "أنت": "إنت", "أنتَ": "إنت", "أنتِ": "إنتِ",
            "نحن": "نحنا", "أنتم": "إنتو", "ماذا": "شو", "لماذا": "ليش",
            "كيف": "كيف", "أين": "وين", "متى": "إيمتى", "من": "مين",
            "لا": "لا", "نعم": "أيه", "ربما": "يمكن", "الآن": "هلق",
            "جيد": "منيح", "ممتاز": "عظيم", "مرحبا": "مرحبا", "شكراً": "شكراً",
            "تفضل": "تفضل", "حسناً": "تمام", "فقط": "بس", "هذا": "هاد",
            "هذه": "هاي", "ذلك": "هداك", "الذي": "اللي", "التي": "اللي",
            "قليل": "شوي", "كثير": "كتير", "بعد": "بعدين",
            "موجود": "موجود", "لا يوجد": "ما في", "يوجد": "في",
            "طيب": "طيب", "صح": "صح",
        },
        "فصحى": {},  # بدون تغيير
    }

    def apply_dialect(self, text: str) -> str:
        """تطبيق اللهجة المختارة على النص"""
        if self.dialect == "فصحى" or self.dialect not in self.DIALECT_MAPS:
            return text
        word_map = self.DIALECT_MAPS[self.dialect]
        for original, replacement in word_map.items():
            text = text.replace(original, replacement)
        return text

    async def say(self, message: str) -> None:
        """إرسال رسالة عامة مع تطبيق اللهجة"""
        await self.highrise.chat(self.apply_dialect(message))

    # ==================== نهاية نظام اللهجات ====================

    def load_user_warnings(self):
        """تحميل التحذيرات من الملف"""
        try:
            if os.path.exists("user_warnings.json"):
                with open("user_warnings.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading warnings: {e}")
            return {}

    def save_user_warnings(self):
        """حفظ التحذيرات في الملف"""
        try:
            with open("user_warnings.json", "w", encoding="utf-8") as f:
                json.dump(self.user_warnings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving warnings: {e}")

    def load_special_welcomes(self):
        """تحميل الترحيبات الخاصة من الملف"""
        try:
            if os.path.exists("special_welcomes.json"):
                with open("special_welcomes.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading special welcomes: {e}")
            return {}

    def save_special_welcomes(self):
        """حفظ الترحيبات الخاصة في الملف"""
        try:
            with open("special_welcomes.json", "w", encoding="utf-8") as f:
                json.dump(self.special_welcomes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving special welcomes: {e}")

    def load_special_farewells(self):
        """تحميل الوداعات الخاصة من الملف"""
        try:
            if os.path.exists("special_farewells.json"):
                with open("special_farewells.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading special farewells: {e}")
            return {}

    def save_special_farewells(self):
        """حفظ الوداعات الخاصة في الملف"""
        try:
            with open("special_farewells.json", "w", encoding="utf-8") as f:
                json.dump(self.special_farewells, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving special farewells: {e}")

    def load_shoes_list(self):
        """تحميل قائمة الأحذية من shoes_list.json كـ dict"""
        try:
            if os.path.exists("shoes_list.json"):
                with open("shoes_list.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "shoes" in data and isinstance(data["shoes"], list):
                    return {str(i+1): v for i, v in enumerate(data["shoes"])}
                elif isinstance(data, dict):
                    return {k: v for k, v in data.items() if k.isdigit()}
            return {}
        except Exception as e:
            print(f"Error loading shoes_list: {e}")
            return {}

    def save_shoes_list(self):
        """حفظ قائمة الأحذية في shoes_list.json كـ dict"""
        try:
            with open("shoes_list.json", "w", encoding="utf-8") as f:
                json.dump(self.shoes_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving shoes list: {e}")

    def save_shoes_index(self):
        """لم يعد مستخدماً - الأحذية تعمل الآن بالمفتاح"""
        pass

    def load_shoe_rotation(self):
        """تحميل قائمة تدوير الأحذية من الملف"""
        try:
            if os.path.exists("shoe_rotation.json"):
                with open("shoe_rotation.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return {"shoes": [], "current_index": 0}
        except Exception as e:
            print(f"Error loading shoe rotation: {e}")
            return {"shoes": [], "current_index": 0}

    def save_shoe_rotation(self):
        """حفظ قائمة تدوير الأحذية في الملف"""
        try:
            data = {
                "shoes": self.shoe_rotation.get("shoes", []),
                "current_index": self.current_shoe_index
            }
            with open("shoe_rotation.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving shoe rotation: {e}")

    def load_bot_position(self):
        """تحميل موقع البوت من الملف"""
        try:
            if os.path.exists("bot_position.json"):
                with open("bot_position.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("position"):
                        pos = data["position"]
                        return Position(pos["x"], pos["y"], pos["z"], pos.get("facing", "FrontRight"))
            return None
        except Exception as e:
            print(f"Error loading bot position: {e}")
            return None

    def save_bot_position(self, position):
        """حفظ موقع البوت في الملف"""
        try:
            position_data = {
                "position": {
                    "x": position.x,
                    "y": position.y,
                    "z": position.z,
                    "facing": position.facing
                }
            }
            with open("bot_position.json", "w", encoding="utf-8") as f:
                json.dump(position_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving bot position: {e}") 

    def load_bot_lang(self):
        """تحميل لغة البوت من الملف"""
        try:
            if os.path.exists("bot_lang.json"):
                with open("bot_lang.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("lang", "ar")
            return "ar"
        except Exception as e:
            print(f"Error loading bot_lang: {e}")
            return "ar"

    def save_bot_lang(self):
        """حفظ لغة البوت في الملف"""
        try:
            with open("bot_lang.json", "w", encoding="utf-8") as f:
                json.dump({"lang": self.bot_lang}, f, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving bot_lang: {e}")

    def load_user_lang_prefs(self):
        """تحميل تفضيلات لغة المستخدمين"""
        try:
            if os.path.exists("user_lang_prefs.json"):
                with open("user_lang_prefs.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading user_lang_prefs: {e}")
            return {}

    def save_user_lang_prefs(self):
        """حفظ تفضيلات لغة المستخدمين"""
        try:
            with open("user_lang_prefs.json", "w", encoding="utf-8") as f:
                json.dump(self.user_lang_prefs, f, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving user_lang_prefs: {e}")

    def get_user_lang(self, user_id: str) -> str:
        """جلب لغة مستخدم معين (يعود للغة البوت العامة إن لم يحدد)"""
        return self.user_lang_prefs.get(user_id, self.bot_lang)

    def load_teleport_locations(self):
        """تحميل مواقع التنقل من ملف"""
        try:
            if os.path.exists("teleport_locations.json"):
                with open("teleport_locations.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # تحويل البيانات المحملة إلى قاموس من المواقع
                    locations = {}
                    for name, pos_data in data.items():
                        locations[name] = Position(pos_data["x"], pos_data["y"], pos_data["z"])
                    return locations
            return {}
        except Exception as e:
            print(f"Error loading teleport locations: {e}")
            return {}

    def save_teleport_locations(self):
        """حفظ مواقع التنقل في ملف"""
        try:
            # تحويل البيانات إلى تنسيق قابل للحفظ في JSON
            data = {}
            for name, position in self.teleport_locations.items():
                data[name] = {
                    "x": position.x,
                    "y": position.y,
                    "z": position.z
                }
            with open("teleport_locations.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving teleport locations: {e}")

    def load_special_protected(self):
        """تحميل قائمة المحميين الخاصين من الملف"""
        try:
            if os.path.exists("special_protected.json"):
                with open("special_protected.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading special protected: {e}")
            return []

    def save_special_protected(self):
        """حفظ قائمة المحميين الخاصين في الملف"""
        try:
            with open("special_protected.json", "w", encoding="utf-8") as f:
                json.dump(self.special_protected, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving special protected: {e}")

    def load_admins(self):
        """تحميل قائمة الأدمن من الملف"""
        try:
            if os.path.exists("admins.json"):
                with open("admins.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading admins: {e}")
            return []

    def save_admins(self):
        """حفظ قائمة الأدمن في الملف"""
        try:
            with open("admins.json", "w", encoding="utf-8") as f:
                json.dump(self.admins, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving admins: {e}")

    def load_filtered_words(self):
        """تحميل قائمة الكلمات المحظورة"""
        try:
            if os.path.exists("filtered_words.json"):
                with open("filtered_words.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading filtered_words: {e}")
            return []

    def save_filtered_words(self):
        """حفظ قائمة الكلمات المحظورة"""
        try:
            with open("filtered_words.json", "w", encoding="utf-8") as f:
                json.dump(self.filtered_words, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving filtered_words: {e}")

    def load_tip_history(self):
        """تحميل سجل التبرعات"""
        try:
            if os.path.exists("tip_history.json"):
                with open("tip_history.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading tip_history: {e}")
            return {}

    def save_tip_history(self):
        """حفظ سجل التبرعات"""
        try:
            with open("tip_history.json", "w", encoding="utf-8") as f:
                json.dump(self.tip_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving tip_history: {e}")

    def load_user_wallets(self):
        """تحميل محافظ المستخدمين"""
        try:
            if os.path.exists("user_wallets.json"):
                with open("user_wallets.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading user_wallets: {e}")
            return {}

    def save_user_wallets(self):
        """حفظ محافظ المستخدمين"""
        try:
            with open("user_wallets.json", "w", encoding="utf-8") as f:
                json.dump(self.user_wallets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving user_wallets: {e}")

    def load_bot_shop_orders(self):
        """تحميل طلبات متجر البوت"""
        try:
            if os.path.exists("bot_shop_orders.json"):
                with open("bot_shop_orders.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading bot_shop_orders: {e}")
            return []

    def save_bot_shop_orders(self):
        """حفظ طلبات متجر البوت"""
        try:
            with open("bot_shop_orders.json", "w", encoding="utf-8") as f:
                json.dump(self.bot_shop_orders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving bot_shop_orders: {e}")

    async def autokick_loop(self):
        """حلقة الطرد التلقائي للمستخدمين غير النشطين"""
        try:
            while self.autokick_minutes > 0:
                await asyncio.sleep(60)
                if self.autokick_minutes <= 0:
                    break
                import time as _time
                now = _time.time()
                limit = self.autokick_minutes * 60
                try:
                    room_users = await self.highrise.get_room_users()
                    for u, _ in room_users.content:
                        if u.id == self.bot_id:
                            continue
                        _ul = u.username.lower()
                        if any(o.lower() == _ul for o in self.owners) or any(a.lower() == _ul for a in self.admins):
                            continue
                        last = self.user_last_active.get(u.id, now)
                        if (now - last) >= limit:
                            try:
                                await self.highrise.moderate_room(u.id, "kick")
                                lang_msg = f"👢 @{u.username} was kicked for inactivity ({self.autokick_minutes} min)" if self.bot_lang == "en" else f"👢 تم طرد @{u.username} بسبب عدم النشاط لمدة {self.autokick_minutes} دقيقة"
                                await self.highrise.chat(lang_msg)
                            except Exception:
                                pass
                except Exception as e:
                    print(f"autokick_loop error: {e}")
        except asyncio.CancelledError:
            pass

    async def is_user_allowed(self, user):
        """التحقق مما إذا كان المستخدم مالكاً أو مشرفاً"""
        uname_lower = user.username.lower()
        if any(o.lower() == uname_lower for o in self.owners):
            return True
        if any(a.lower() == uname_lower for a in self.admins):
            return True
        return False

    def is_user_jailed(self, user_id):
        """فحص إذا كان المستخدم مسجون مؤقتاً"""
        if user_id not in self.jailed_users:
            return False
        
        import time as time_module
        current_time = time_module.time()
        if current_time >= self.jailed_users[user_id]:
            # انتهت مدة السجن
            del self.jailed_users[user_id]
            return False
        
        return True

    def jail_user(self, user_id, duration_minutes=5):
        """سجن المستخدم لمدة معينة (افتراضياً 5 دقائق)"""
        import time as time_module
        current_time = time_module.time()
        end_time = current_time + (duration_minutes * 60)
        self.jailed_users[user_id] = end_time

    def load_user_points(self):
        """تحميل نقاط المستخدمين من الملف"""
        try:
            if os.path.exists("user_points.json"):
                with open("user_points.json", "r", encoding="utf-8") as f:  
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading user points: {e}")
            return {}

    def load_vip_uses(self):
        """تحميل استخدامات VIP من الملف"""
        try:
            if os.path.exists("vip_uses.json"):
                with open("vip_uses.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading vip uses: {e}")
            return {}

    def save_vip_uses(self):
        """حفظ استخدامات VIP في الملف"""
        try:
            with open("vip_uses.json", "w", encoding="utf-8") as f:
                json.dump(self.vip_uses, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving vip uses: {e}")

    def load_vip_list(self):
        """تحميل قائمة VIP من الملف"""
        try:
            if os.path.exists("vip_list.json"):
                with open("vip_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading VIP list: {e}")
            return []

    def save_vip_list(self):
        """حفظ قائمة VIP في الملف"""
        try:
            with open("vip_list.json", "w", encoding="utf-8") as f:
                json.dump(self.vip_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving VIP list: {e}")

    def load_blacklist(self):
        """تحميل القائمة السوداء من الملف"""
        try:
            if os.path.exists("bot_blacklist.json"):
                with open("bot_blacklist.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading blacklist: {e}")
            return []

    def save_blacklist(self):
        """حفظ القائمة السوداء في الملف"""
        try:
            with open("bot_blacklist.json", "w", encoding="utf-8") as f:
                json.dump(self.bot_blacklist, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving blacklist: {e}")

    def load_saved_outfits(self):
        """تحميل الألبسة المحفوظة من الملف"""
        try:
            if os.path.exists("saved_outfits.json"):
                with open("saved_outfits.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading saved outfits: {e}")
        return {}

    def save_saved_outfits(self):
        """حفظ الألبسة في الملف"""
        try:
            with open("saved_outfits.json", "w", encoding="utf-8") as f:
                json.dump(self.saved_outfits, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving outfits: {e}")

    async def copy_outfits_from_room(self, notify_chat=False):
        """نسخ ملابس جميع المستخدمين في الغرفة وحفظها كأرقام"""
        try:
            room_users = await self.highrise.get_room_users()
            slot = 1
            saved_count = 0
            for room_user, _ in room_users.content:
                if room_user.id == self.bot_id:
                    continue
                try:
                    outfit_resp = await self.highrise.get_user_outfit(room_user.id)
                    if hasattr(outfit_resp, 'message'):
                        continue
                    items_data = [
                        {"id": item.id, "type": item.type, "amount": item.amount, "active_palette": item.active_palette}
                        for item in outfit_resp.outfit
                    ]
                    if not items_data:
                        continue
                    # ابحث عن رقم غير مستخدم
                    while str(slot) in self.saved_outfits:
                        slot += 1
                    self.saved_outfits[str(slot)] = items_data
                    saved_count += 1
                    print(f"[نسخ ملابس] تم حفظ لبسة {room_user.username} في رقم {slot}")
                    slot += 1
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"[نسخ ملابس] فشل جلب لبسة {room_user.username}: {e}")
            self.save_saved_outfits()
            return saved_count
        except Exception as e:
            print(f"[نسخ ملابس] خطأ عام: {e}")
            return 0

    def load_subscribers(self):
        """تحميل قائمة المشتركين من الملف"""
        try:
            if os.path.exists("subscribers.json"):
                with open("subscribers.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading subscribers: {e}")
        return {}

    def save_subscribers(self):
        """حفظ قائمة المشتركين في الملف"""
        try:
            with open("subscribers.json", "w", encoding="utf-8") as f:
                json.dump(self.subscribers, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving subscribers: {e}")

    def load_eyes_list(self):
        """تحميل قائمة العيون من الملف"""
        try:
            if os.path.exists("eyes_list.json"):
                with open("eyes_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading eyes list: {e}")
        return {}

    def save_eyes_list(self):
        """حفظ قائمة العيون في الملف"""
        try:
            with open("eyes_list.json", "w", encoding="utf-8") as f:
                json.dump(self.eyes_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving eyes list: {e}")

    def load_tshirts_list(self):
        """تحميل قائمة التيشيرتات من الملف"""
        try:
            if os.path.exists("tshirts_list.json"):
                with open("tshirts_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading tshirts list: {e}")
        return {}

    def save_tshirts_list(self):
        """حفظ قائمة التيشيرتات في الملف"""
        try:
            with open("tshirts_list.json", "w", encoding="utf-8") as f:
                json.dump(self.tshirts_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving tshirts list: {e}")

    def load_bear_list(self):
        """تحميل قائمة الدببة من الملف"""
        try:
            if os.path.exists("bear_list.json"):
                with open("bear_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading bear list: {e}")
        return {}

    def save_bear_list(self):
        """حفظ قائمة الدببة في الملف"""
        try:
            with open("bear_list.json", "w", encoding="utf-8") as f:
                json.dump(self.bear_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving bear list: {e}")

    def load_accessories_list(self):
        """تحميل قائمة الإكسسوارات من الملف"""
        try:
            if os.path.exists("accessories_list.json"):
                with open("accessories_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading accessories list: {e}")
        return {}

    def save_accessories_list(self):
        """حفظ قائمة الإكسسوارات في الملف"""
        try:
            with open("accessories_list.json", "w", encoding="utf-8") as f:
                json.dump(self.accessories_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving accessories list: {e}")

    def load_tattoo_list(self):
        """تحميل قائمة الوشوم من الملف"""
        try:
            if os.path.exists("tattoo_list.json"):
                with open("tattoo_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading tattoo list: {e}")
        return {}

    def save_tattoo_list(self):
        """حفظ قائمة الوشوم في الملف"""
        try:
            with open("tattoo_list.json", "w", encoding="utf-8") as f:
                json.dump(self.tattoo_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving tattoo list: {e}")

    def load_nose_list(self):
        try:
            if os.path.exists("nose_list.json"):
                with open("nose_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading nose list: {e}")
        return {}

    def save_nose_list(self):
        try:
            with open("nose_list.json", "w", encoding="utf-8") as f:
                json.dump(self.nose_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving nose list: {e}")

    def load_hand_list(self):
        try:
            if os.path.exists("hand_list.json"):
                with open("hand_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading hand list: {e}")
        return {}

    def save_hand_list(self):
        try:
            with open("hand_list.json", "w", encoding="utf-8") as f:
                json.dump(self.hand_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving hand list: {e}")

    def load_features_list(self):
        try:
            if os.path.exists("features_list.json"):
                with open("features_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading features list: {e}")
        return {}

    def save_features_list(self):
        try:
            with open("features_list.json", "w", encoding="utf-8") as f:
                json.dump(self.features_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving features list: {e}")

    def load_invisible_list(self):
        try:
            if os.path.exists("invisible_list.json"):
                with open("invisible_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading invisible list: {e}")
        return {}

    def save_invisible_list(self):
        try:
            with open("invisible_list.json", "w", encoding="utf-8") as f:
                json.dump(self.invisible_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving invisible list: {e}")

    def load_hat_list(self):
        try:
            if os.path.exists("hat_list.json"):
                with open("hat_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading hat list: {e}")
        return {}

    def save_hat_list(self):
        try:
            with open("hat_list.json", "w", encoding="utf-8") as f:
                json.dump(self.hat_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving hat list: {e}")

    def load_pants_list(self):
        try:
            if os.path.exists("pants_list.json"):
                with open("pants_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading pants list: {e}")
        return {}

    def save_pants_list(self):
        try:
            with open("pants_list.json", "w", encoding="utf-8") as f:
                json.dump(self.pants_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving pants list: {e}")

    def load_glasses_list(self):
        try:
            if os.path.exists("glasses_list.json"):
                with open("glasses_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading glasses list: {e}")
        return {}

    def save_glasses_list(self):
        try:
            with open("glasses_list.json", "w", encoding="utf-8") as f:
                json.dump(self.glasses_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving glasses list: {e}")

    def load_eyebrows_list(self):
        try:
            if os.path.exists("eyebrows_list.json"):
                with open("eyebrows_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading eyebrows list: {e}")
        return {}

    def save_eyebrows_list(self):
        try:
            with open("eyebrows_list.json", "w", encoding="utf-8") as f:
                json.dump(self.eyebrows_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving eyebrows list: {e}")

    def load_mouth_list(self):
        try:
            if os.path.exists("mouth_list.json"):
                with open("mouth_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading mouth list: {e}")
        return {}

    def save_mouth_list(self):
        try:
            with open("mouth_list.json", "w", encoding="utf-8") as f:
                json.dump(self.mouth_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving mouth list: {e}")

    def load_lip_color_list(self):
        try:
            if os.path.exists("lip_color_list.json"):
                with open("lip_color_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading lip color list: {e}")
        return {}

    def save_lip_color_list(self):
        try:
            with open("lip_color_list.json", "w", encoding="utf-8") as f:
                json.dump(self.lip_color_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving lip color list: {e}")

    def load_hair_list(self):
        """تحميل قائمة التسريحات من الملف"""
        try:
            if os.path.exists("hair_list.json"):
                with open("hair_list.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading hair list: {e}")
        return {}

    def save_hair_list(self):
        """حفظ قائمة التسريحات في الملف"""
        try:
            with open("hair_list.json", "w", encoding="utf-8") as f:
                json.dump(self.hair_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving hair list: {e}")

    def save_user_points(self):
        """حفظ نقاط المستخدمين في الملف"""
        try:
            with open("user_points.json", "w", encoding="utf-8") as f:
                json.dump(self.user_points, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving user points: {e}")

    def add_user_points(self, user_id, points):
        """إضافة نقاط للمستخدم"""
        if user_id not in self.user_points:
            self.user_points[user_id] = 0
        self.user_points[user_id] += points
        self.save_user_points()

    def get_user_points(self, user_id):
        """الحصول على نقاط المستخدم"""
        return self.user_points.get(user_id, 0)

    def calculate_user_level(self, points):
        """حساب مستوى المستخدم بناءً على النقاط - النظام الصعب (متدرج الصعوبة)"""
        if points < 100:
            return 0  # قبل المستوى الأول
        elif points < 2500:
            return 1  # صعب الوصول للمستوى 1
        elif points < 8000:
            return 2  # صعب جداً للمستوى 2
        elif points < 18000:
            return 3  # صعب جداً جداً للمستوى 3
        elif points < 35000:
            return 4  # تحدي كبير للمستوى 4
        elif points < 60000:
            return 5  # تحدي أكبر للمستوى 5
        elif points < 95000:
            return 6  # صعوبة متقدمة
        elif points < 140000:
            return 7  # صعوبة عالية
        elif points < 200000:
            return 8  # صعوبة عالية جداً
        elif points < 275000:
            return 9  # تحدي للخبراء
        elif points < 370000:
            return 10  # للمحترفين فقط
        elif points < 490000:
            return 11  # تحدي الأبطال
        elif points < 640000:
            return 12  # للأسطوريين
        elif points < 820000:
            return 13  # مستوى إمبراطوري
        elif points < 1050000:
            return 14  # مستوى أسطوري
        elif points < 1350000:
            return 15  # مستوى إلهي
        elif points < 1750000:
            return 16  # الحد الأقصى - مستوى الآلهة
        else:
            return 16  # الحد الأقصى

    def get_points_for_next_level(self, current_points):
        """حساب النقاط المطلوبة للمستوى التالي - النظام الصعب"""
        level = self.calculate_user_level(current_points)
        
        if level == 0:
            return 100
        elif level == 1:
            return 2500
        elif level == 2:
            return 8000
        elif level == 3:
            return 18000
        elif level == 4:
            return 35000
        elif level == 5:
            return 60000
        elif level == 6:
            return 95000
        elif level == 7:
            return 140000
        elif level == 8:
            return 200000
        elif level == 9:
            return 275000
        elif level == 10:
            return 370000
        elif level == 11:
            return 490000
        elif level == 12:
            return 640000
        elif level == 13:
            return 820000
        elif level == 14:
            return 1050000
        elif level == 15:
            return 1350000
        elif level == 16:
            return 1750000
        else:
            return 1750000  # الحد الأقصى

    

    async def on_emote(self, user: User, emote_id: str, receiver: User | None) -> None:
      pass

    async def on_user_move(self, user: User, pos: Position | AnchorPosition) -> None:
        """معالجة حركة المستخدمين - للنقل التلقائي بالنقر مع إيقاف ذكي"""
        
        # تجاهل حركة البوت نفسه
        if user.id == self.bot_id:
            return
            
        # تأكد من تهيئة القواميس المطلوبة
        if not hasattr(self, 'teleport_on_click'):
            self.teleport_on_click = {}
        if not hasattr(self, 'user_last_floor'):
            self.user_last_floor = {}
            
        # ==================== فحص منطقة الرقص ====================
        if (hasattr(self, 'dance_zone_active') and self.dance_zone_active and
                self.dance_zone_pos is not None and isinstance(pos, Position)):
            try:
                cx = self.dance_zone_pos.x
                cz = self.dance_zone_pos.z
                dist = ((pos.x - cx) ** 2 + (pos.z - cz) ** 2) ** 0.5
                in_zone = dist <= self.dance_zone_radius

                if in_zone:
                    # المستخدم دخل المنطقة — ابدأ رقصه إذا لم يكن يرقص بالفعل
                    if user.id not in self.dance_zone_users:
                        self.dance_zone_users.add(user.id)
                        asyncio.create_task(self.start_dance_zone_loop(user.id))
                else:
                    # المستخدم خرج من المنطقة — أوقف رقصه إذا كان في وضع dance_zone
                    if user.id in self.dance_zone_users:
                        self.dance_zone_users.discard(user.id)
                        if self.user_emote_loops.get(user.id) == "dance_zone":
                            await self.stop_emote_loop(user.id)
            except Exception as _dz_move_err:
                print(f"[DanceZone] خطأ on_user_move: {_dz_move_err}")

        # فحص إذا كان المستخدم مجمّداً وإعادته لمكانه
        if user.id in self.frozen_users and isinstance(pos, Position):
            frozen_pos = self.frozen_users[user.id]
            try:
                await self.highrise.teleport(user.id, frozen_pos)
            except Exception as e:
                print(f"Error freezing {user.username}: {e}")

        # فحص إذا كان النقل التلقائي مفعل للمستخدم وكان المكان Position عادي
        # وتأكد من أن المستخدم فعّل هذه الميزة بوعي
        if (user.id in self.teleport_on_click and 
            self.teleport_on_click[user.id] == True and 
            isinstance(pos, Position)):
            
            try:
                # نقل المستخدم للمكان الذي نقر عليه
                await self.highrise.teleport(user.id, pos)
            except Exception as e:
                print(f"Error in auto-teleport for {user.username}: {e}")
                # في حالة الخطأ، أوقف النقل التلقائي للمستخدم
                if user.id in self.teleport_on_click:
                    self.teleport_on_click[user.id] = False

    async def on_reaction(self, user: User, reaction: Reaction, receiver: User) -> None:
        if reaction == "sleep" and user.username in self.name_ad:
            r_username = self.receiver_username
            print(f"receiver: {r_username}")
            list = await self.highrise.get_room_users()
            username_targ = user.username
            for user_obj, position in list.content:
                if user_obj.username == username_targ:
                    print(f"User: {user_obj.username}")
                    print(f"id: {user_obj.id}")
                    positions = f"{position.x}, {position.y}, {position.z}"
                    await self.highrise.teleport(
                        receiver.id,
                        Position(x=position.x, y=position.y, z=position.z - 1))

    async def watchdog_loop(self):
        """مراقب الاتصال - يكتشف الانقطاع ويعيد الاتصال تلقائياً"""
        await asyncio.sleep(30)
        while True:
            try:
                elapsed = time.time() - self.last_heartbeat
                if elapsed > 90:
                    print(f"[Watchdog] لم يصل أي حدث منذ {int(elapsed)} ثانية. إعادة الاتصال...")
                    os._exit(0)
            except Exception as e:
                print(f"[Watchdog] خطأ: {e}")
            await asyncio.sleep(30)

    async def restart_bot_periodically(self):
        """إعادة تشغيل البوت تلقائياً كل 5 دقائق لضمان الفصل الفعلي"""
        while True:
            await asyncio.sleep(300)
            print("Force-restarting bot process for a clean reconnect...")
            try:
                await self.highrise.chat("🔄 Periodic restart to maintain connection stability..." if self.bot_lang == "en" else "🔄 إعادة تشغيل دورية للحفاظ على استقرار الاتصال...")
                await asyncio.sleep(1) 
            except:
                pass
            os._exit(0)

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        global bot_instance
        bot_instance = self
        self.loop_ref = asyncio.get_running_loop()
        self.last_heartbeat = time.time()
        print("hi im alive?")

        # ====== تنظيف البوتات العالقة عند بدء التشغيل ======
        # عند إعادة تشغيل البوت الرئيسي، خيوط البوتات الفرعية تنتهي
        # لكن نحتفظ ببيانات المشتري إذا كان لا يزال لديه وقت متبقٍ
        try:
            _bots = load_sub_bots()
            _changed = False
            for _b in _bots:
                if _b["status"] in ("busy", "paused"):
                    _expires_str = _b.get("expires_at")
                    _remaining = 0
                    if _expires_str:
                        try:
                            _exp_dt = datetime.strptime(_expires_str, "%Y-%m-%d %H:%M:%S")
                            _remaining = max(0, (_exp_dt - datetime.now()).total_seconds())
                        except Exception:
                            _remaining = 0

                    if _remaining > 0:
                        # المشتري لا يزال لديه وقت - نحتفظ ببياناته ونضعه paused
                        _b["status"] = "paused"
                        _b["remaining_seconds"] = _remaining
                        print(f"[Startup] البوت #{_b['id']} محفوظ للمشتري {_b.get('buyer')} ({int(_remaining//3600)}h {int((_remaining%3600)//60)}m متبقية)")
                    else:
                        # انتهت المدة - نحرر البوت بالكامل
                        print(f"[Startup] تحرير البوت #{_b['id']} (منتهي الصلاحية)")
                        _b["status"] = "available"
                        _b["room_id"] = None
                        _b["buyer"] = None
                        _b["buyer_id"] = None
                        _b["expires_at"] = None
                        _b["remaining_seconds"] = None
                    _changed = True
            if _changed:
                save_sub_bots(_bots)
                print("[Startup] تم تحديث حالة البوتات عند إعادة التشغيل")
        except Exception as _e:
            print(f"[Startup] خطأ في تنظيف البوتات: {_e}")
        self.start_time = datetime.now()  # تسجيل وقت دخول البوت
        self.bot_id = session_metadata.user_id  # حفظ معرف البوت
        
        # حفظ معلومات الغرفة من session_metadata
        try:
            # Attempt to access properties based on common SDK patterns
            self.room_id = getattr(self, "room_id", "Unknown")
            if self.room_id == "Unknown":
                self.room_id = getattr(session_metadata, "room_id", "Unknown")
            
            self.room_name = getattr(session_metadata.room_info, "room_name", "Unknown")
            self.room_owner_id = getattr(session_metadata.room_info, "owner_id", "Unknown")
            
            # If owner_id is a UUID, we might want to get the username later, 
            # but for now let's just store what we have.
        except Exception as e:
            print(f"Error extracting room info from metadata: {e}")
            self.room_id = "Unknown"
            self.room_name = "Unknown"
            self.room_owner_id = "Unknown"
        
        print(f"Bot started with ID: {self.bot_id}")  # للتأكد من حفظ المعرف
        print(f"Room ID: {self.room_id}, Name: {self.room_name}, Owner: {self.room_owner_id}")

        # التأكد من تهيئة webapi إذا لم يتم ذلك في __init__
        # ملاحظة: في النسخة 24.1.0، self.webapi متاح تلقائياً في BaseBot
        if not hasattr(self, 'webapi') or self.webapi is None:
            try:
                if WebApi:
                    self.webapi = WebApi()
                    print("WebApi initialized in on_start")
                else:
                    # محاولة البحث عن الكائن المدمج في النسخة الجديدة
                    print("Checking for built-in webapi...")
            except Exception as e:
                print(f"WebApi initialization failed: {e}")

        # انتظار للتأكد من أن الروم جاهزة لاستقبال أوامر النقل
        await asyncio.sleep(10)

        try:
            # إعادة تحميل الموقع من الملف للتأكد من قراءة أحدث نسخة
            self.bot_start_position = self.load_bot_position()
            
            # انتقال البوت للموقع المحفوظ أو الافتراضي
            if self.bot_start_position:
                print(f"Teleporting bot to saved position: {self.bot_start_position}")
                await self.highrise.teleport(session_metadata.user_id, self.bot_start_position)
            else:
                print("No saved position found, using default")
                await self.highrise.teleport(session_metadata.user_id, Position(5.0, 0, 0.5, "FrontRight"))
        except Exception as e:
            print(f"Error teleporting bot on start: {e}")

        # التحقق من الصلاحيات إذا كان البوت في وضع المتابعة
        if RunBot.pending_follow:
            RunBot.pending_follow = False
            try:
                priv = await self.highrise.get_room_privilege(self.bot_id)
                is_mod = getattr(priv, 'moderator', False)
                is_designer = getattr(priv, 'designer', False)
                if is_mod and is_designer:
                    print(f"[Follow] البوت انتقل بنجاح - مشرف ومصمم في الغرفة الجديدة")
                    try:
                        owner_info = await self.webapi.get_users(username=self.owners[0], limit=1)
                        if owner_info.users:
                            await self.highrise.send_message(owner_info.users[0].user_id, "✅ البوت انتقل للغرفة الجديدة بنجاح.\nلديه صلاحيات مشرف ومصمم.")
                    except Exception:
                        pass
                else:
                    print(f"[Follow] البوت ليس مشرفاً ومصمماً في الغرفة الجديدة، الرجوع للغرفة الأصلية")
                    try:
                        owner_info = await self.webapi.get_users(username=self.owners[0], limit=1)
                        if owner_info.users:
                            await self.highrise.send_message(owner_info.users[0].user_id, "❌ البوت لا يملك صلاحيات مشرف ومصمم في الغرفة الجديدة.\nجاري الرجوع للغرفة الأصلية.")
                    except Exception:
                        pass
                    RunBot.room_id = RunBot.original_room_id
                    raise Exception("لا توجد صلاحيات كافية - الرجوع للغرفة الأصلية")
            except Exception as e:
                print(f"[Follow] خطأ في التحقق من الصلاحيات: {e}")
                if "الرجوع للغرفة الأصلية" in str(e):
                    raise

        # إرسال رسالة دعاية لصانع البوت عند الدخول
        try:
            await self.highrise.chat("🤖 Bot started successfully by @_king_man_1" if self.bot_lang == "en" else "🤖 تم تشغيل البوت بنجاح بواسطة @_king_man_1")
            await self.highrise.chat("✨ For professional bots contact @_king_man_1" if self.bot_lang == "en" else "✨ لصنع بوتات احترافية تواصل مع المطور @_king_man_1")
        except Exception as e:
            print(f"Error sending start-up advertisement: {e}")

        # تسجيل مثيل البوت عالمياً فور جاهزيته
        self.loop_ref = asyncio.get_event_loop()
        bot_instance = self

        # بدء الحلقات الدورية مع معالجة الأخطاء
        try:
            self.loop_task = asyncio.create_task(self.loop())
            self.subscription_task = asyncio.create_task(self.subscription_loop())
            self.watchdog_task = asyncio.create_task(self.watchdog_loop())
            print("Background tasks started successfully")
        except Exception as e:
            print(f"Error starting background tasks: {e}")



    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        import time as _tj
        self.user_last_active[user.id] = _tj.time()
        self.last_heartbeat = time.time()
        if self.room_locked:
            if not (user.username in self.owners or user.username in self.admins):
                try:
                    await self.highrise.moderate_room(user.id, "kick")
                    await self.highrise.chat(f"❌ Sorry @{user.username}, the room is currently locked." if self.bot_lang == "en" else f"❌ المعذرة @{user.username}، الغرفة مقفلة حالياً.")
                    return
                except Exception as e:
                    print(f"Error kicking user in locked room: {e}")

        # انتظار نصف ثانية قبل إرسال القلوب التلقائية
        await asyncio.sleep(0.5)

        # إرسال قلب واحد لكل مستخدم يدخل الروم (حتى لو كان له ترحيب خاص)
        try:
            # التأكد من وجود معرف المستخدم ومعرف البوت
            if user.id and self.bot_id and user.id != self.bot_id:
                # إرسال قلب واحد
                await self.highrise.react("heart", user.id)
            else:
                pass
        except Exception as e:
            print(f"Error sending heart to new user {user.username}: {e}")
            # لا تتوقف عن معالجة الترحيب حتى لو فشل إرسال القلب

        # تحديد رسالة الترحيب بناءً على نوع المستخدم
        try:
            # أولاً: فحص إذا كان المستخدم لديه ترحيب خاص (أولوية عالية)
            # فحص بحساسية الأحرف وبدونها
            special_welcome_found = False
            welcome_message = None
            
            # فحص مباشر (حساس للأحرف)
            if user.username in self.special_welcomes:
                welcome_message = self.special_welcomes[user.username]
                special_welcome_found = True
            else:
                # فحص غير حساس للأحرف
                for saved_username, saved_message in self.special_welcomes.items():
                    if saved_username.lower() == user.username.lower():
                        welcome_message = saved_message
                        special_welcome_found = True
                        break
            
            if not special_welcome_found:
                # ثانياً: فحص صلاحيات المستخدم للترحيب الافتراضي
                user_privileges = await self.highrise.get_room_privilege(user.id)
                is_moderator = user_privileges.moderator
                is_owner = user.username in self.owners

                if is_moderator or is_owner:
                    # رسالة ترحيب خاصة للمشرفين والأونرز
                    welcome_message = f"@{user.username} دخل المشرف أقوى تحية ♥❤🫡"
                else:
                    # رسائل ترحيب عشوائية للمستخدمين العاديين
                    welcome_messages = [
                        f"@{user.username} حي من جانا ♥",
                        f"@{user.username} منور رومك 😉❤",
                        f"@{user.username} حي من جانا 💋",
                        f"@{user.username} تقدم يعسل تحت امرك 😉❤",
                        f"@{user.username} وصل العسل 💋",
                        f"@{user.username} صلّ على النبي ❤️",
                        f"@{user.username} اررررحب دخل الصاروخ 😍",
                        f"@{user.username} خش مسي على الناس متتكسفش ❣️",
                        f"@{user.username} اهلا بكم في رومنا 💋",
                        f"@{user.username} نورت رومك يا حب ♥اررررحب دخل المطنوخ 💋",
                        f"@{user.username} المز دخل الروم ولعها🤩😍",
                        f"@{user.username} الحلو الي دخل👋😁❣️",
                        f"@{user.username} ولع الروم يا جامد♥️💋"
                    ]
                    # اختيار رسالة ترحيب عشوائية
                    welcome_message = random.choice(welcome_messages)

        except Exception as e:
            print(f"Error checking user privileges: {e}")
            # في حالة الخطأ، فحص الترحيب الخاص أولاً
            special_welcome_found = False
            
            # فحص مباشر
            if user.username in self.special_welcomes:
                welcome_message = self.special_welcomes[user.username]
                special_welcome_found = True
            else:
                # فحص غير حساس للأحرف
                for saved_username, saved_message in self.special_welcomes.items():
                    if saved_username.lower() == user.username.lower():
                        welcome_message = saved_message
                        special_welcome_found = True
                        break
            
            if not special_welcome_found:
                if self.bot_lang == "en":
                    welcome_message = f"Welcome @{user.username} 🌺"
                else:
                    welcome_message = f"حياك الله @{user.username} 🌺"

        # إرسال رسالة الترحيب
        await self.highrise.chat(welcome_message)
        
        # إضافة نقاط للمستخدم عند دخول الروم (10 نقاط)
        self.add_user_points(user.id, 10)

        # ==================== الإكرامية التلقائية لجميع المستخدمين ====================
        if self.auto_tip_active and self.auto_tip_amount > 0 and user.id != self.bot_id:
            try:
                bars_dictionary = {
                    10000: "gold_bar_10k",
                    5000: "gold_bar_5000",
                    1000: "gold_bar_1k",
                    500: "gold_bar_500",
                    100: "gold_bar_100",
                    50: "gold_bar_50",
                    10: "gold_bar_10",
                    5: "gold_bar_5",
                    1: "gold_bar_1"
                }
                fees_dictionary = {
                    10000: 1000, 5000: 500, 1000: 100,
                    500: 50, 100: 10, 50: 5, 10: 1, 5: 1, 1: 1
                }
                bot_wallet = await self.highrise.get_wallet()
                bot_amount = bot_wallet.content[0].amount
                tip_bars = []
                total_cost = 0
                remaining = self.auto_tip_amount
                for bar_value in sorted(bars_dictionary.keys(), reverse=True):
                    if remaining >= bar_value:
                        count = remaining // bar_value
                        remaining %= bar_value
                        tip_bars.extend([bars_dictionary[bar_value]] * count)
                        total_cost += count * (bar_value + fees_dictionary[bar_value])
                if total_cost <= bot_amount and tip_bars:
                    for bar in tip_bars:
                        await self.highrise.tip_user(user.id, bar)
                    await self.highrise.chat(f"🎁 إكرامية تلقائية: تم إرسال {self.auto_tip_amount} ذهب لـ @{user.username}!")
                else:
                    print(f"[AutoTip] رصيد البوت غير كافي للإكرامية التلقائية ({bot_amount} < {total_cost})")
            except Exception as _at_err:
                print(f"[AutoTip] خطأ في الإكرامية التلقائية: {_at_err}")

        # ==================== التبرع التلقائي للأعضاء المميزين ====================
        if self.auto_tip_vip_active and self.auto_tip_vip_amount > 0 and user.id != self.bot_id:
            try:
                is_vip_user = (
                    user.username in self.vip_list or
                    any(v.lower() == user.username.lower() for v in self.vip_list) or
                    user.username in self.vips
                )
                if is_vip_user:
                    bars_dictionary = {
                        10000: "gold_bar_10k",
                        5000: "gold_bar_5000",
                        1000: "gold_bar_1k",
                        500: "gold_bar_500",
                        100: "gold_bar_100",
                        50: "gold_bar_50",
                        10: "gold_bar_10",
                        5: "gold_bar_5",
                        1: "gold_bar_1"
                    }
                    fees_dictionary = {
                        10000: 1000, 5000: 500, 1000: 100,
                        500: 50, 100: 10, 50: 5, 10: 1, 5: 1, 1: 1
                    }
                    bot_wallet = await self.highrise.get_wallet()
                    bot_amount = bot_wallet.content[0].amount
                    tip_bars = []
                    total_cost = 0
                    remaining = self.auto_tip_vip_amount
                    for bar_value in sorted(bars_dictionary.keys(), reverse=True):
                        if remaining >= bar_value:
                            count = remaining // bar_value
                            remaining %= bar_value
                            tip_bars.extend([bars_dictionary[bar_value]] * count)
                            total_cost += count * (bar_value + fees_dictionary[bar_value])
                    if total_cost <= bot_amount and tip_bars:
                        for bar in tip_bars:
                            await self.highrise.tip_user(user.id, bar)
                        await self.highrise.chat(f"⭐ تبرع تلقائي VIP: تم إرسال {self.auto_tip_vip_amount} ذهب للعضو المميز @{user.username}!")
                    else:
                        print(f"[AutoTipVIP] رصيد البوت غير كافي للتبرع التلقائي ({bot_amount} < {total_cost})")
            except Exception as _atv_err:
                print(f"[AutoTipVIP] خطأ في التبرع التلقائي للأعضاء المميزين: {_atv_err}")

    async def on_user_leave(self, user: User) -> None:
        try:
            farewell_message = None
            # أولاً: فحص إذا كان المستخدم لديه وداع خاص
            if user.username in self.special_farewells:
                farewell_message = self.special_farewells[user.username]
            else:
                # فحص غير حساس للأحرف
                for saved_username, saved_message in self.special_farewells.items():
                    if saved_username.lower() == user.username.lower():
                        farewell_message = saved_message
                        break
            
            if farewell_message:
                # التأكد من احتواء الرسالة المخصصة على المنشن إذا لم يكن موجوداً
                if f"@{user.username}" not in farewell_message:
                    farewell_message = f"@{user.username} {farewell_message}"
            else:
                # قائمة رسائل الوداع العشوائية الافتراضية
                if self.bot_lang == "en":
                    farewell_messages = [
                        f"Goodbye @{user.username}, see you soon! 👋❤️",
                        f"Farewell @{user.username}, it was great having you! ✨",
                        f"Take care @{user.username}, hope to see you again! 🌹",
                        f"Bye @{user.username}, thanks for visiting! 😊",
                        f"See you later @{user.username}! 💋👋"
                    ]
                else:
                    farewell_messages = [
                        f"في أمان الله @{user.username} ننتظر عودتك! 👋❤️",
                        f"وداعاً @{user.username} سعدنا بوجودك معنا ✨",
                        f"ترافقتك السلامة @{user.username} إلى اللقاء القريب 🌹",
                        f"نشوفك على خير @{user.username} شكراً لزيارتك 😊",
                        f"باي @{user.username} خلي بالك من نفسك 💋👋"
                    ]
                farewell_message = random.choice(farewell_messages)
            
            await self.highrise.chat(farewell_message)
        except Exception as e:
            print(f"Error in on_user_leave for {user.username}: {e}")

        user_id = user.id
        if user_id in self.user_emote_loops:
            await self.stop_emote_loop(user_id)
        if hasattr(self, 'dance_zone_users'):
            self.dance_zone_users.discard(user_id)

    async def on_user_kick(self, user: User, moderator: User) -> None:
        """Called when a user is kicked by a moderator"""
        if self.bot_lang == "en":
            kick_message = f"🦵 @{user.username} was kicked by moderator @{moderator.username}"
        else:
            kick_message = f"🦵 تم طرد المستخدم @{user.username} بواسطة المشرف @{moderator.username}"
        
        # Send notification to the room
        await self.highrise.chat(kick_message)
        
        # Send private message to the kicked user
        try:
            if self.bot_lang == "en":
                private_kick_message = f"🦵 You were kicked from the room by moderator @{moderator.username}"
            else:
                private_kick_message = f"🦵 تم طردك من الروم بواسطة المشرف @{moderator.username}"
            await self.highrise.send_direct_message(user.id, private_kick_message)
        except Exception as e:
            print(f"Error sending private kick message to {user.username}: {e}")
        
        # Send special notification to @_king_man_1 via conversation_id (send_message)
        try:
            # محاولة العثور على @_king_man_1 عبر WebAPI
            fjia_user_info = await self.webapi.get_users(username="_king_man_1", limit=1)
            if fjia_user_info.users:
                fjia_user_id = fjia_user_info.users[0].user_id
                
                # إنشاء رسالة إشعار خاصة لـ fjia
                fjia_notification = f"🚨 إشعار طرد:\n👤 المطرود: @{user.username}\n🛡️ المشرف: @{moderator.username}\n⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # إرسال الرسالة عبر send_message (conversation_id)
                await self.highrise.send_message(fjia_user_id, fjia_notification)
                print(f"Special kick notification sent to @fjia via conversation_id about {user.username}")
            else:
                print("Could not find @fjia user via WebAPI")
                
        except Exception as e:
            print(f"Error sending special notification to @fjia via send_message: {e}")
            # كبديل، محاولة إرسال عبر الطرق الأخرى
            try:
                # البحث في الروم الحالي
                room_users = await self.highrise.get_room_users()
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == "fjia":
                        fjia_notification = f"🚨 طرد: @{user.username} بواسطة @{moderator.username}"
                        await self.highrise.send_whisper(room_user.id, fjia_notification)
                        print(f"Whisper notification sent to @fjia (fallback)")
                        break
            except Exception as fallback_error:
                print(f"Fallback notification to @fjia also failed: {fallback_error}")
        
        # Send private notifications to owners
        await self.send_moderation_notification(kick_message)

    async def on_user_ban(self, user: User, moderator: User) -> None:
        """Called when a user is banned by a moderator"""
        ban_message = f"🚫 تم حظر المستخدم @{user.username} بواسطة المشرف @{moderator.username}"
        
        # Send notification to the room
        await self.highrise.chat(ban_message)
        
        # Send private message to the banned user
        try:
            private_ban_message = f"🚫 تم حظرك من الروم بواسطة المشرف @{moderator.username}"
            await self.highrise.send_direct_message(user.id, private_ban_message)
        except Exception as e:
            print(f"Error sending private ban message to {user.username}: {e}")
        
        # Send special notification to @fjia via conversation_id (send_message)
        try:
            # محاولة العثور على @fjia عبر WebAPI
            fjia_user_info = await self.webapi.get_users(username="fjia", limit=1)
            if fjia_user_info.users:
                fjia_user_id = fjia_user_info.users[0].user_id
                
                # إنشاء رسالة إشعار خاصة لـ fjia
                fjia_notification = f"🚨 إشعار حظر:\n👤 المحظور: @{user.username}\n🛡️ المشرف: @{moderator.username}\n⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # إرسال الرسالة عبر send_message (conversation_id)
                await self.highrise.send_message(fjia_user_id, fjia_notification)
                print(f"Special ban notification sent to @fjia via conversation_id about {user.username}")
            else:
                print("Could not find @fjia user via WebAPI")
                
        except Exception as e:
            print(f"Error sending special notification to @fjia via send_message: {e}")
            # كبديل، محاولة إرسال عبر الطرق الأخرى
            try:
                # البحث في الروم الحالي
                room_users = await self.highrise.get_room_users()
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == "fjia":
                        fjia_notification = f"🚨 حظر: @{user.username} بواسطة @{moderator.username}"
                        await self.highrise.send_whisper(room_user.id, fjia_notification)
                        print(f"Whisper notification sent to @fjia (fallback)")
                        break
            except Exception as fallback_error:
                print(f"Fallback notification to @fjia also failed: {fallback_error}")
        
        # Send private notifications to owners
        await self.send_moderation_notification(ban_message)

    async def on_user_mute(self, user: User, moderator: User) -> None:
        """Called when a user is muted by a moderator"""
        mute_message = f"🔇 تم كتم المستخدم @{user.username} بواسطة المشرف @{moderator.username}"
        
        # Send notification to the room
        await self.highrise.chat(mute_message)
        
        # Send private message to the muted user
        try:
            private_mute_message = f"🔇 تم كتمك في الروم بواسطة المشرف @{moderator.username}"
            await self.highrise.send_direct_message(user.id, private_mute_message)
        except Exception as e:
            print(f"Error sending private mute message to {user.username}: {e}")
        
        # Send special notification to @fjia via conversation_id (send_message)
        try:
            # محاولة العثور على @fjia عبر WebAPI
            fjia_user_info = await self.webapi.get_users(username="fjia", limit=1)
            if fjia_user_info.users:
                fjia_user_id = fjia_user_info.users[0].user_id
                
                # إنشاء رسالة إشعار خاصة لـ fjia
                fjia_notification = f"🚨 إشعار كتم:\n👤 المكتوم: @{user.username}\n🛡️ المشرف: @{moderator.username}\n⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # إرسال الرسالة عبر send_message (conversation_id)
                await self.highrise.send_message(fjia_user_id, fjia_notification)
                print(f"Special mute notification sent to @fjia via conversation_id about {user.username}")
            else:
                print("Could not find @fjia user via WebAPI")
                
        except Exception as e:
            print(f"Error sending special notification to @fjia via send_message: {e}")
            # كبديل، محاولة إرسال عبر الطرق الأخرى
            try:
                # البحث في الروم الحالي
                room_users = await self.highrise.get_room_users()
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == "fjia":
                        fjia_notification = f"🚨 كتم: @{user.username} بواسطة @{moderator.username}"
                        await self.highrise.send_whisper(room_user.id, fjia_notification)
                        print(f"Whisper notification sent to @fjia (fallback)")
                        break
            except Exception as fallback_error:
                print(f"Fallback notification to @fjia also failed: {fallback_error}")
        
        # Send private notifications to owners
        await self.send_moderation_notification(mute_message)

    async def on_user_unmute(self, user: User, moderator: User) -> None:
        """Called when a user is unmuted by a moderator"""
        unmute_message = f"🔊 تم إلغاء كتم المستخدم @{user.username} بواسطة المشرف @{moderator.username}"
        
        # Send notification to the room
        await self.highrise.chat(unmute_message)
        
        # Send private message to the unmuted user
        try:
            private_unmute_message = f"🔊 تم إلغاء كتمك في الروم بواسطة المشرف @{moderator.username}"
            await self.highrise.send_direct_message(user.id, private_unmute_message)
        except Exception as e:
            print(f"Error sending private unmute message to {user.username}: {e}")
        
        # Send special notification to @fjia via conversation_id (send_message)
        try:
            # محاولة العثور على @fjia عبر WebAPI
            fjia_user_info = await self.webapi.get_users(username="fjia", limit=1)
            if fjia_user_info.users:
                fjia_user_id = fjia_user_info.users[0].user_id
                
                # إنشاء رسالة إشعار خاصة لـ fjia
                fjia_notification = f"🚨 إشعار إلغاء كتم:\n👤 المستخدم: @{user.username}\n🛡️ المشرف: @{moderator.username}\n⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # إرسال الرسالة عبر send_message (conversation_id)
                await self.highrise.send_message(fjia_user_id, fjia_notification)
                print(f"Special unmute notification sent to @fjia via conversation_id about {user.username}")
            else:
                print("Could not find @fjia user via WebAPI")
                
        except Exception as e:
            print(f"Error sending special notification to @fjia via send_message: {e}")
            # كبديل، محاولة إرسال عبر الطرق الأخرى
            try:
                # البحث في الروم الحالي
                room_users = await self.highrise.get_room_users()
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == "fjia":
                        fjia_notification = f"🚨 إلغاء كتم: @{user.username} بواسطة @{moderator.username}"
                        await self.highrise.send_whisper(room_user.id, fjia_notification)
                        print(f"Whisper notification sent to @fjia (fallback)")
                        break
            except Exception as fallback_error:
                print(f"Fallback notification to @fjia also failed: {fallback_error}")
        
        # Send private notifications to owners
        await self.send_moderation_notification(unmute_message)

    async def on_message(self, user_id: str, conversation_id: str,
                       is_new_conversation: bool) -> None:
        message = ""
        try:
            response = await self.highrise.get_messages(conversation_id)
            if isinstance(response, GetMessagesRequest.GetMessagesResponse) and response.messages:
                message = response.messages[0].content
        except Exception as e:
            print(f"[DM] Error fetching messages: {e}")
            return
        print(f"[DM] from user_id={user_id}: {repr(message)}")

        # ==================== أمر تابعني عبر DM (للأونر فقط) ====================
        if message.strip().startswith("!تابعني"):
            is_owner_dm_follow = False
            try:
                sender_info = await self.webapi.get_user(user_id)
                if sender_info and sender_info.user and sender_info.user.username in self.owners:
                    is_owner_dm_follow = True
            except Exception as e:
                print(f"[Follow] خطأ في التحقق من الأونر: {e}")
            if is_owner_dm_follow:
                parts = message.strip().split()
                if len(parts) >= 2:
                    new_room_id = parts[1].strip()
                    RunBot.pending_follow = True
                    RunBot.room_id = new_room_id
                    print(f"[Follow] الأونر طلب الانتقال للغرفة: {new_room_id}")
                    await self.highrise.send_message(conversation_id, f"⏳ جاري الانتقال للغرفة: {new_room_id}\nسيتم التحقق من الصلاحيات عند الدخول...")
                    raise Exception(f"[Follow] الانتقال لغرفة جديدة: {new_room_id}")
                else:
                    await self.highrise.send_message(conversation_id, "⚠️ الصيغة الصحيحة: !تابعني [room_id]")
                    return
            else:
                print(f"[Follow] المستخدم {user_id} ليس أونر، تجاهل الأمر")

        # ==================== أمر اذهب عبر DM ====================
        if message.strip().startswith("اذهب "):
            is_owner_go = False
            try:
                sender_info = await self.webapi.get_user(user_id)
                if sender_info and sender_info.user and sender_info.user.username in self.owners:
                    is_owner_go = True
            except Exception:
                pass
            if is_owner_go:
                new_room_id = message.strip().split("اذهب ", 1)[1].strip()
                if new_room_id:
                    RunBot.pending_follow = False
                    RunBot.room_id = new_room_id
                    print(f"[اذهب] الانتقال للغرفة: {new_room_id}")
                    await self.highrise.send_message(conversation_id, f"⏳ جاري الانتقال للغرفة: {new_room_id}")
                    raise Exception(f"[اذهب] الانتقال لغرفة: {new_room_id}")
                else:
                    await self.highrise.send_message(conversation_id, "⚠️ الصيغة الصحيحة: اذهب [room_id]")
                return

        # ====== أمر المالك: حفظ يوزر البوت الفرعي ======
        # الصيغة: يوزر 1 bot_username
        if message.strip().startswith("يوزر "):
            try:
                sender_info = await self.webapi.get_user(user_id)
                is_owner = sender_info and sender_info.user and sender_info.user.username in self.owners
            except Exception:
                is_owner = False
            if is_owner:
                parts = message.strip().split()
                if len(parts) == 3:
                    try:
                        bot_num = int(parts[1])
                        bot_uname = parts[2].lstrip("@")
                        _bots = load_sub_bots()
                        found = False
                        for _b in _bots:
                            if _b["id"] == bot_num:
                                _b["username"] = bot_uname
                                found = True
                                break
                        if found:
                            save_sub_bots(_bots)
                            await self.highrise.send_message(conversation_id,
                                f"✅ تم حفظ يوزر البوت #{bot_num}: @{bot_uname}")
                        else:
                            await self.highrise.send_message(conversation_id,
                                f"❌ لم يُوجد بوت برقم {bot_num}")
                    except ValueError:
                        await self.highrise.send_message(conversation_id,
                            "⚠️ الصيغة الصحيحة: يوزر [رقم_البوت] [اليوزر]\nمثال: يوزر 1 bot_username")
                else:
                    # عرض قائمة البوتات الحالية
                    _bots = load_sub_bots()
                    lines = ["🤖 قائمة البوتات:"]
                    for _b in _bots:
                        if _b.get("token"):
                            uname = _b.get("username", "غير محدد")
                            status = _b["status"]
                            lines.append(f"#{_b['id']} | @{uname} | {status}")
                    await self.highrise.send_message(conversation_id, "\n".join(lines))
                return

        # ====== أمر المالك: إضافة وقت للإيجار ======
        # الصيغة: وقت @username ساعات
        if message.strip().startswith("وقت "):
            try:
                sender_info = await self.webapi.get_user(user_id)
                is_owner = sender_info and sender_info.user and sender_info.user.username in self.owners
            except Exception:
                is_owner = False
            if is_owner:
                parts = message.strip().split()
                if len(parts) >= 3:
                    try:
                        target_username = parts[1].lstrip("@")
                        extra_hours = float(parts[2])
                        if extra_hours <= 0:
                            raise ValueError("يجب أن تكون الساعات أكبر من صفر")
                        extra_seconds = extra_hours * 3600

                        bots = load_sub_bots()
                        target_bot = None

                        # البحث عن بوت نشط أو موقوف مؤقتاً للمستخدم
                        for _b in bots:
                            _buyer = _b.get("buyer", "")
                            if _buyer and _buyer.lower() == target_username.lower():
                                if _b["status"] in ("busy", "paused"):
                                    target_bot = _b
                                    break

                        if target_bot:
                            if target_bot["status"] == "busy":
                                # بوت نشط: تمديد expires_at
                                old_expires = datetime.strptime(target_bot["expires_at"], "%Y-%m-%d %H:%M:%S")
                                new_expires = old_expires + timedelta(seconds=extra_seconds)
                                target_bot["expires_at"] = new_expires.strftime("%Y-%m-%d %H:%M:%S")
                                save_sub_bots(bots)

                                # تحديث في bot_shop_orders أيضاً
                                for _ord in self.bot_shop_orders:
                                    if _ord.get("buyer", "").lower() == target_username.lower() and _ord.get("status") == "active":
                                        _ord["expires_at"] = target_bot["expires_at"]
                                self.save_bot_shop_orders()

                                remaining = max(0, (new_expires - datetime.now()).total_seconds())
                                h_left = int(remaining // 3600)
                                m_left = int((remaining % 3600) // 60)

                                await self.highrise.send_message(conversation_id,
                                    f"✅ تم إضافة {extra_hours:.0f} ساعة للمستخدم @{target_username}\n"
                                    f"🤖 البوت #{target_bot['id']}\n"
                                    f"⏰ ينتهي الآن في: {target_bot['expires_at']}\n"
                                    f"⏳ الوقت الكلي المتبقي: {h_left}h {m_left}m"
                                )

                                # إخبار المستخدم
                                try:
                                    target_user_info = await self.webapi.get_users(username=target_username, limit=1)
                                    if target_user_info.users:
                                        target_uid = target_user_info.users[0].user_id
                                        await self.highrise.send_message_bulk([target_uid],
                                            f"🎁 تمت إضافة {extra_hours:.0f} ساعة لبوتك!\n"
                                            f"⏳ الوقت المتبقي الآن: {h_left}h {m_left}m\n"
                                            f"⏰ ينتهي في: {target_bot['expires_at']}"
                                        )
                                except Exception:
                                    pass

                            elif target_bot["status"] == "paused":
                                # بوت موقوف: إضافة للوقت المتبقي
                                old_remaining = target_bot.get("remaining_seconds", 0) or 0
                                new_remaining = old_remaining + extra_seconds
                                target_bot["remaining_seconds"] = new_remaining
                                save_sub_bots(bots)

                                h_left = int(new_remaining // 3600)
                                m_left = int((new_remaining % 3600) // 60)

                                await self.highrise.send_message(conversation_id,
                                    f"✅ تم إضافة {extra_hours:.0f} ساعة للمستخدم @{target_username}\n"
                                    f"🤖 البوت #{target_bot['id']} (موقوف مؤقتاً)\n"
                                    f"⏳ الوقت المتبقي الآن: {h_left}h {m_left}m"
                                )

                                # إخبار المستخدم
                                try:
                                    target_user_info = await self.webapi.get_users(username=target_username, limit=1)
                                    if target_user_info.users:
                                        target_uid = target_user_info.users[0].user_id
                                        await self.highrise.send_message_bulk([target_uid],
                                            f"🎁 تمت إضافة {extra_hours:.0f} ساعة لبوتك!\n"
                                            f"⏳ الوقت المتبقي الآن: {h_left}h {m_left}m\n"
                                            f"▶️ أرسل 'تشغيل' لإعادة تشغيل البوت."
                                        )
                                except Exception:
                                    pass
                        else:
                            await self.highrise.send_message(conversation_id,
                                f"❌ لا يوجد بوت نشط أو موقوف للمستخدم @{target_username}\n"
                                f"تأكد من صحة الاسم."
                            )
                    except ValueError as ve:
                        await self.highrise.send_message(conversation_id,
                            f"⚠️ خطأ: {ve}\n"
                            f"الصيغة الصحيحة: وقت @username عدد_الساعات\n"
                            f"مثال: وقت @LORD_2007 24"
                        )
                else:
                    await self.highrise.send_message(conversation_id,
                        f"⚠️ الصيغة الصحيحة: وقت @username عدد_الساعات\n"
                        f"مثال: وقت @LORD_2007 24"
                    )
                return

        # ====== أمر شراء باقة من المحفظة ======
        _purchase_map = {
            "شراء ساعة":      {"name": "⏱️ ساعة واحدة",  "hours": 1,   "price": 1},
            "شراء ساعه":      {"name": "⏱️ ساعة واحدة",  "hours": 1,   "price": 1},
            "شراء 3 ساعات":   {"name": "⏱️ 3 ساعات",     "hours": 3,   "price": 3000},
            "شراء ثلاث ساعات":{"name": "⏱️ 3 ساعات",     "hours": 3,   "price": 3000},
            "شراء يوم":       {"name": "📅 يوم كامل",     "hours": 24,  "price": 10000},
            "شراء أسبوع":     {"name": "📅 أسبوع كامل",  "hours": 168, "price": 50000},
            "شراء اسبوع":     {"name": "📅 أسبوع كامل",  "hours": 168, "price": 50000},
        }
        _msg_clean = message.strip().lower()
        _matched_pkg = None
        for _cmd, _pkg in _purchase_map.items():
            if _msg_clean == _cmd.lower():
                _matched_pkg = _pkg
                break

        if _matched_pkg:
            _wallet_bal = self.user_wallets.get(user_id, 0)
            _pkg_price  = _matched_pkg["price"]
            _pkg_hours  = _matched_pkg["hours"]
            _pkg_name   = _matched_pkg["name"]

            if _wallet_bal < _pkg_price:
                _needed = _pkg_price - _wallet_bal
                await self.highrise.send_message(conversation_id,
                    f"❌ رصيدك غير كافٍ!\n\n"
                    f"💲 رصيدك الحالي: {_wallet_bal:,} ذهب\n"
                    f"💰 سعر الباقة: {_pkg_price:,} ذهب\n"
                    f"⚠️ تحتاج: {_needed:,} ذهب إضافية\n\n"
                    f"💡 أرسل هذا المبلغ للبوت لشحن رصيدك."
                )
                return

            # الرصيد كافٍ - فحص إذا كان عنده بوت نشط
            _bots_now = load_sub_bots()
            _active_bot = next((b for b in _bots_now if b.get("buyer_id") == user_id and b["status"] in ("busy", "paused")), None)

            if _active_bot:
                # تمديد الوقت مباشرة
                extra_secs = _pkg_hours * 3600
                if _active_bot["status"] == "busy":
                    old_exp = datetime.strptime(_active_bot["expires_at"], "%Y-%m-%d %H:%M:%S")
                    new_exp = old_exp + timedelta(seconds=extra_secs)
                    _active_bot["expires_at"] = new_exp.strftime("%Y-%m-%d %H:%M:%S")
                    save_sub_bots(_bots_now)
                    for _ord in self.bot_shop_orders:
                        if _ord.get("buyer_id") == user_id and _ord.get("status") == "active":
                            _ord["expires_at"] = _active_bot["expires_at"]
                    self.save_bot_shop_orders()
                    rem = max(0, int((new_exp - datetime.now()).total_seconds()))
                    h = rem // 3600; m = (rem % 3600) // 60
                    time_info = f"⏳ الوقت الكلي المتبقي: {h}h {m}m\n⏰ ينتهي في: {_active_bot['expires_at']}"
                else:
                    old_rem = _active_bot.get("remaining_seconds", 0) or 0
                    new_rem = old_rem + extra_secs
                    _active_bot["remaining_seconds"] = new_rem
                    save_sub_bots(_bots_now)
                    h = int(new_rem // 3600); m = int((new_rem % 3600) // 60)
                    time_info = f"⏳ الوقت الكلي المتبقي: {h}h {m}m\n▶️ أرسل 'تشغيل' لإعادة تشغيل البوت."

                # خصم من المحفظة
                self.user_wallets[user_id] = _wallet_bal - _pkg_price
                self.save_user_wallets()

                await self.highrise.send_message(conversation_id,
                    f"✅ تم تمديد اشتراكك بنجاح!\n\n"
                    f"📦 الباقة: {_pkg_name}\n"
                    f"💰 المبلغ المخصوم: {_pkg_price:,} ذهب\n"
                    f"💲 رصيدك المتبقي: {self.user_wallets[user_id]:,} ذهب\n"
                    f"🤖 البوت: @{_active_bot.get('username', '')}\n"
                    f"{time_info}"
                )
                print(f"[Wallet] @{user_id} اشترى {_pkg_name} من المحفظة - خُصم {_pkg_price}")
            else:
                # لا يوجد بوت نشط - بدء إيجار جديد
                _next_bot = get_available_sub_bot()
                if not _next_bot:
                    await self.highrise.send_message(conversation_id,
                        f"⚠️ جميع البوتات مشغولة حالياً!\n"
                        f"💲 رصيدك محفوظ: {_wallet_bal:,} ذهب\n"
                        f"🔄 حاول مجدداً لاحقاً."
                    )
                    return

                # خصم من المحفظة وبدء إجراء الإيجار
                self.user_wallets[user_id] = _wallet_bal - _pkg_price
                self.save_user_wallets()

                _bot_username = _next_bot.get("username")
                self.pending_bot_purchases[user_id] = {
                    "step": "waiting_room",
                    "package": _pkg_name,
                    "duration": f"{_pkg_hours} ساعة",
                    "hours": _pkg_hours,
                    "amount": 0,
                    "username": "",
                    "assigned_bot_id": _next_bot["id"],
                    "assigned_bot_token": _next_bot["token"],
                    "assigned_bot_username": _bot_username,
                }

                _all_bots_status = load_sub_bots()
                _real_bots = [b for b in _all_bots_status if b.get("token")]
                _status_lines = ""
                for _sb in _real_bots:
                    _sb_name = _sb.get("username", f"Bot #{_sb['id']}")
                    _status_lines += f"🔴 @{_sb_name} — مشغول\n" if _sb["status"] == "busy" else f"🟢 @{_sb_name} — متاح\n"

                await self.highrise.send_message(conversation_id,
                    f"✅ تم خصم {_pkg_price:,} ذهب من رصيدك!\n"
                    f"💲 رصيدك المتبقي: {self.user_wallets[user_id]:,} ذهب\n\n"
                    f"📦 الباقة: {_pkg_name}\n"
                    f"🤖 البوت المخصص لك: @{_bot_username}\n\n"
                    f"📊 حالة البوتات:\n{_status_lines}\n"
                    f"⚠️ خطوة مهمة قبل إرسال معرف الغرفة:\n"
                    f"1️⃣ افتح غرفتك في Highrise\n"
                    f"2️⃣ ادخل إعدادات الغرفة (Room Settings)\n"
                    f"3️⃣ أضف @{_bot_username} كـ Designer (مشرف ومصمم)\n"
                    f"4️⃣ ثم أرسل لي معرف الغرفة"
                )
                print(f"[Wallet] @{user_id} بدأ إيجار جديد بـ {_pkg_name} من المحفظة")
            return

        # ====== أوامر إيقاف/تشغيل البوت المستأجر عبر DM ======
        msg_stripped = message.strip()
        if msg_stripped in ["ايقاف", "ايقاف البوت", "وقف", "وقف البوت", "إيقاف", "إيقاف البوت"]:
            bots = load_sub_bots()
            buyer_active_bot = next((b for b in bots if b.get("buyer_id") == user_id and b["status"] == "busy"), None)
            buyer_paused_bot = next((b for b in bots if b.get("buyer_id") == user_id and b["status"] == "paused"), None)
            if buyer_active_bot:
                expires_dt = datetime.strptime(buyer_active_bot["expires_at"], "%Y-%m-%d %H:%M:%S")
                remaining = max(0, (expires_dt - datetime.now()).total_seconds())
                hours_left = int(remaining // 3600)
                mins_left = int((remaining % 3600) // 60)
                SUB_BOT_PAUSE_SIGNALS[buyer_active_bot["id"]] = True
                await self.highrise.send_message(conversation_id,
                    f"⏸️ جاري إيقاف البوت #{buyer_active_bot['id']} مؤقتاً...\n"
                    f"⏳ الوقت المتبقي: {hours_left}h {mins_left}m\n"
                    f"⚠️ الوقت يستمر في الحساب أثناء الإيقاف.\n"
                    f"▶️ أرسل 'تشغيل' لإعادة تشغيل البوت."
                )
            elif buyer_paused_bot:
                await self.highrise.send_message(conversation_id, "⏸️ بوتك متوقف مؤقتاً بالفعل.\n▶️ أرسل 'تشغيل' لإعادة تشغيله.")
            else:
                await self.highrise.send_message(conversation_id, "❌ لا يوجد بوت نشط لك حالياً.\n💡 اشترِ باقة جديدة لتفعيل البوت.")
            return

        if msg_stripped in ["تشغيل", "تشغيل البوت", "تفعيل", "تفعيل البوت"]:
            bots = load_sub_bots()
            buyer_paused_bot = next((b for b in bots if b.get("buyer_id") == user_id and b["status"] == "paused"), None)
            buyer_active_bot = next((b for b in bots if b.get("buyer_id") == user_id and b["status"] == "busy"), None)
            if buyer_paused_bot:
                remaining_seconds = buyer_paused_bot.get("remaining_seconds", 0)
                if remaining_seconds and remaining_seconds > 0:
                    hours_remaining = remaining_seconds / 3600
                    expires_at = deploy_sub_bot(
                        bot_id=buyer_paused_bot["id"],
                        token=buyer_paused_bot["token"],
                        room_id=buyer_paused_bot["room_id"],
                        buyer=buyer_paused_bot["buyer"],
                        buyer_id=user_id,
                        hours=hours_remaining
                    )
                    hours_left = int(remaining_seconds // 3600)
                    mins_left = int((remaining_seconds % 3600) // 60)
                    await self.highrise.send_message(conversation_id,
                        f"▶️ تم إعادة تشغيل البوت #{buyer_paused_bot['id']}!\n"
                        f"🏠 الغرفة: {buyer_paused_bot['room_id']}\n"
                        f"⏳ الوقت المتبقي: {hours_left}h {mins_left}m\n"
                        f"⏰ ينتهي في: {expires_at}"
                    )
                else:
                    buyer_paused_bot["status"] = "available"
                    buyer_paused_bot["room_id"] = None
                    buyer_paused_bot["buyer"] = None
                    buyer_paused_bot["buyer_id"] = None
                    buyer_paused_bot["expires_at"] = None
                    buyer_paused_bot["remaining_seconds"] = None
                    save_sub_bots(bots)
                    await self.highrise.send_message(conversation_id, "❌ انتهت مدة إيجارك.\n💡 اشترِ باقة جديدة لتفعيل البوت.")
            elif buyer_active_bot:
                expires_dt = datetime.strptime(buyer_active_bot["expires_at"], "%Y-%m-%d %H:%M:%S")
                remaining = max(0, (expires_dt - datetime.now()).total_seconds())
                hours_left = int(remaining // 3600)
                mins_left = int((remaining % 3600) // 60)
                await self.highrise.send_message(conversation_id,
                    f"✅ بوتك يعمل بالفعل!\n"
                    f"🤖 البوت #{buyer_active_bot['id']}\n"
                    f"⏳ الوقت المتبقي: {hours_left}h {mins_left}m\n"
                    f"⏸️ أرسل 'ايقاف' لإيقافه مؤقتاً."
                )
            else:
                # ======= البحث في الطلبات المحفوظة بعد إعادة تشغيل البوت =======
                valid_order = None
                valid_remaining = 0
                for _ord in reversed(self.bot_shop_orders):
                    if _ord.get("buyer_id") != user_id:
                        continue
                    _exp_str = _ord.get("expires_at")
                    _room = _ord.get("room_id")
                    if not _exp_str or not _room:
                        continue
                    try:
                        _exp_dt = datetime.strptime(_exp_str, "%Y-%m-%d %H:%M:%S")
                        _rem = (_exp_dt - datetime.now()).total_seconds()
                        if _rem > 0:
                            valid_order = _ord
                            valid_remaining = _rem
                            break
                    except Exception:
                        continue

                if valid_order:
                    _hours_rem = valid_remaining / 3600
                    _hours_left = int(valid_remaining // 3600)
                    _mins_left = int((valid_remaining % 3600) // 60)
                    _saved_token = valid_order.get("bot_token")
                    _saved_bot_id = valid_order.get("bot_id")
                    _saved_room = valid_order.get("room_id")
                    _saved_uname = valid_order.get("bot_username", "")

                    # التحقق أن البوت المحفوظ لا يزال متاحاً (ليس مشغولاً بمستخدم آخر)
                    _bots_now = load_sub_bots()
                    _saved_bot_data = next((b for b in _bots_now if b["id"] == _saved_bot_id and b.get("token") == _saved_token), None)
                    if _saved_bot_data and _saved_bot_data["status"] == "busy" and _saved_bot_data.get("buyer_id") != user_id:
                        # البوت المحفوظ مشغول بمستخدم آخر، جرّب بوتاً آخر متاحاً
                        _saved_bot_data = get_available_sub_bot()
                        if _saved_bot_data:
                            _saved_token = _saved_bot_data["token"]
                            _saved_bot_id = _saved_bot_data["id"]
                            _saved_uname = _saved_bot_data.get("username", "")
                        else:
                            _saved_bot_data = None

                    if _saved_token and _saved_bot_id and _saved_room and _saved_bot_data:
                        expires_at = deploy_sub_bot(
                            bot_id=_saved_bot_id,
                            token=_saved_token,
                            room_id=_saved_room,
                            buyer=valid_order.get("buyer", ""),
                            buyer_id=user_id,
                            hours=_hours_rem
                        )
                        # تحديث الطلب ببيانات البوت الجديدة
                        valid_order["bot_id"] = _saved_bot_id
                        valid_order["bot_token"] = _saved_token
                        valid_order["bot_username"] = _saved_uname
                        valid_order["expires_at"] = expires_at
                        self.save_bot_shop_orders()
                        _uname_line = f"🤖 البوت: @{_saved_uname}\n" if _saved_uname else ""
                        await self.highrise.send_message(conversation_id,
                            f"✅ تم إعادة تشغيل البوت!\n\n"
                            f"{_uname_line}"
                            f"🏠 الغرفة: {_saved_room}\n"
                            f"⏳ الوقت المتبقي: {_hours_left}h {_mins_left}m\n"
                            f"⏰ ينتهي في: {expires_at}\n\n"
                            f"⏸️ أرسل 'ايقاف' لإيقافه مؤقتاً."
                        )
                    else:
                        await self.highrise.send_message(conversation_id,
                            f"⚠️ لديك وقت متبقي ({_hours_left}h {_mins_left}m) لكن جميع البوتات مشغولة الآن.\n"
                            f"حاول مجدداً لاحقاً أو تواصل مع المالك."
                        )
                else:
                    await self.highrise.send_message(conversation_id, "❌ لا يوجد بوت نشط أو وقت متبقٍ لك.\n💡 اشترِ باقة جديدة لتفعيل البوت.")
            return

        # ====== متجر البوت - استقبال معرف الغرفة (حالة انتظار) ======
        if user_id in self.pending_bot_purchases and self.pending_bot_purchases[user_id].get("step") == "waiting_room":
            # تجاهل رسائل النظام التلقائية من Highrise
            system_msgs = ["لقد حصلت على نصيحة", "you received a tip", "تلقيت إكرامية",
                           "tip received", "تبرع", "إكرامية", "نصيحة"]
            if any(s in message.lower() for s in system_msgs):
                print(f"[Shop] تجاهل رسالة نظام تلقائية: {message}")
                return

            purchase = self.pending_bot_purchases[user_id]
            raw_msg = message.strip()

            # استخراج Room ID وInvite ID إذا أرسل المستخدم رابطاً كاملاً
            room_id = raw_msg
            invite_id = None
            if "high.rs" in raw_msg or "highrise" in raw_msg.lower() or "http" in raw_msg:
                try:
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(raw_msg)
                    params = parse_qs(parsed.query)
                    extracted_id = params.get("id", [None])[0]
                    extracted_invite = params.get("invite_id", [None])[0]
                    if extracted_id:
                        room_id = extracted_id
                        invite_id = extracted_invite
                        print(f"[Shop] تم استخراج Room ID: {room_id} | Invite ID: {invite_id}")
                    else:
                        await self.highrise.send_message(conversation_id,
                            f"⚠️ لم أستطع استخراج معرف الغرفة من هذا الرابط.\n"
                            f"أرسل معرف الغرفة مباشرة (Room ID) مثال: 6990fc95f837018b8250a706")
                        return
                except Exception as _url_err:
                    print(f"[Shop] خطأ في تحليل الرابط: {_url_err}")

            # التحقق أن المعرف ليس فارغاً
            if not room_id or len(room_id) < 10:
                await self.highrise.send_message(conversation_id,
                    f"⚠️ معرف الغرفة غير صحيح.\n"
                    f"أرسل معرف الغرفة (Room ID) مثال: 6990fc95f837018b8250a706")
                return

            del self.pending_bot_purchases[user_id]

            # البحث عن بوت - استخدام البوت المخصص عشوائياً مسبقاً أو إعادة المحاولة
            if purchase.get("assigned_bot_id") and purchase.get("assigned_bot_token"):
                bots = load_sub_bots()
                assigned_bot_data = next((b for b in bots if b["id"] == purchase["assigned_bot_id"]), None)
                if assigned_bot_data and assigned_bot_data["status"] == "available":
                    available_bot = assigned_bot_data
                else:
                    available_bot = get_available_sub_bot()
            else:
                available_bot = get_available_sub_bot()

            order_id = f"ORD-{int(time.time())}"
            order = {
                "order_id": order_id,
                "buyer": purchase["username"],
                "buyer_id": user_id,
                "package": purchase["package"],
                "duration": purchase["duration"],
                "hours": purchase["hours"],
                "amount_paid": purchase["amount"],
                "room_id": room_id,
                "status": "active" if available_bot else "queued",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            if purchase.get("amount", 0) > 0:
                self.bot_shop_orders.append(order)
                self.save_bot_shop_orders()

            if available_bot:
                expires_at = deploy_sub_bot(
                    bot_id=available_bot["id"],
                    token=available_bot["token"],
                    room_id=room_id,
                    buyer=purchase["username"],
                    buyer_id=user_id,
                    hours=purchase["hours"],
                    invite_id=invite_id
                )
                # حفظ expires_at وبيانات البوت في الطلب للاستخدام بعد إعادة التشغيل
                for _ord in self.bot_shop_orders:
                    if _ord["order_id"] == order_id:
                        _ord["expires_at"] = expires_at
                        _ord["bot_id"] = available_bot["id"]
                        _ord["bot_token"] = available_bot["token"]
                        _ord["bot_username"] = available_bot.get("username", "")
                        _ord["room_id"] = room_id
                        break
                self.save_bot_shop_orders()

                _deployed_username = available_bot.get("username", "")
                _username_line = f"🤖 يوزر البوت: @{_deployed_username}\n" if _deployed_username else ""
                buyer_msg = (
                    f"🎉 تم تفعيل البوت بنجاح!\n\n"
                    f"📦 الباقة: {purchase['package']} ({purchase['duration']})\n"
                    f"🆔 معرف الغرفة: {room_id}\n"
                    f"{_username_line}"
                    f"⏰ ينتهي في: {expires_at}\n\n"
                    f"💡 اكتب 'اوامر' في الغرفة للمساعدة\n"
                    f"⏸️ أرسل 'ايقاف' هنا لإيقاف البوت مؤقتاً\n"
                    f"▶️ أرسل 'تشغيل' هنا لإعادة تشغيله\n"
                    f"⚠️ الوقت يستمر في الحساب حتى أثناء الإيقاف\n"
                    f"🔢 رقم طلبك: {order_id}"
                )
            else:
                buyer_msg = (
                    f"⚠️ جميع البوتات مشغولة حالياً!\n\n"
                    f"📦 الباقة: {purchase['package']} ({purchase['duration']})\n"
                    f"🆔 معرف الغرفة: {room_id}\n\n"
                    f"📞 تواصل مع @_king_man_1 لمعرفة موعد توفر البوت\n"
                    f"🔢 رقم طلبك: {order_id}"
                )

            await self.highrise.send_message(conversation_id, buyer_msg)
            return

        try:
            if message.lower() == "!equip help" or message.lower() == "equip":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id, f"Equip Help 🆘: {getclothes('help')}")
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq h":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Hairs 👱‍♂️: {getclothes('hair')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <hairname> in the room to equip / !remove <hairname> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq t":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Shirts 🎽: {getclothes('top')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <topname> in the room to equip / !remove <topname> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq p":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Pants 👖: {getclothes('pant')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <pantname> in the room to equip / !remove <pantname> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq s":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Skirts 🩳: {getclothes('skirt')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <skirtname> in the room to equip / !remove <skirtname> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq sh":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Shoes 👟: {getclothes('shoe')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <shoename> in the room to equip / !remove <shoename> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq b":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Back hair 👱‍♂️:'Short Short Fro', 'Box Braids', 'Long Undercut Dreads', 'Undercut Dreads', 'Side Swept Fro', 'Long Buzzed Fro', 'Short Buzzed Fro', 'Curly Undercut', 'Tight Curls', 'Loose Curls', 'Shaggy Curls', 'Short Curls', 'Medium Wavy Cut', 'Short Wavy Cut', 'Wavy Undercut', 'Wavy Side Part', 'Shaggy Side Part', 'Combed Back Waves', 'Blown Back Waves', 'Short Straight', 'Side Combed Straight', 'Straight Slicked Back', 'Buzz Cut', 'Shaggy Crew Cut', 'Faux Hawk', 'Shaggy Straight', 'Straight Side Part', 'Combed Back Undercut', 'Upward Swoosh', 'Side Swept Undercut', 'Side Swept', 'Crew Cut', 'Over Shoulder Wavy Short', 'Over Shoulder Wavy Long', 'Over Shoulder Straight Short', 'Over Shoulder Straight Bangs', 'Over Shoulder Straight Long', 'Over Shoulder Pony', 'Over Shoulder Curly', 'Over Shoulder Coily', 'Over Shoulder Braid'"
                    )
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n'Wavy Long Bob', 'Sweet Curl Waves', 'Poofy Bob', 'Short Beach Waves', 'Long Beach Waves', 'Long Glamour Waves', 'Chunky Waves', 'Wavy Short', 'Wavy Medium', 'Wavy Low Pony', 'Wavy High Pony', 'Wavy Pixie', 'Wavy Long', 'Top Knot Back', 'Straight Short Low Pigtails', 'Straight Short High Pigtails', 'Straight Short', 'Straight Medium', 'Straight Low Pony', 'Straight Long Low Pigtails', 'Straight Long', 'Straight High Pony', 'Straight Pixie', 'Sleek Straight Pony', 'Sleek Straight Medium', 'Sleek Straight Long', 'Sleek Straight Short', 'Bettie Waves', 'Marilyn Curls', 'Loose Coily Short', 'Loose Coily Medium', 'Loose Coily Long', 'Long Wavy Half Bun', 'Half Pony', 'Dreads Medium', 'Dreads Low Pony', 'Dreads Long', 'Dreads High Pony', 'Dreads Extra Short', 'Dreads Short', 'Double Top Knots Back', 'Low Double Buns', 'Curly Short Low Pigtails', 'Curly Short High Pigtails', 'Curly No Bangs Back', 'Curly Medium', 'Curly Low Pony', 'Curly Long High Pigtails', 'Curly Long', 'Curly High Pony', 'Curly Pixie', 'Coily Short', 'Coily Pinapple Hair', 'Coily Medium', 'Coily Low Pony', 'Coily Long', 'Coily High Pony', 'Bald', 'Low Bun', 'High Bun', 'Afro Short', 'Afro Pom Poms Back', 'Afro Medium', 'Afro Long', 'Afro High Pony'"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq so":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Sock 🧦: {getclothes('sock')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <sockname> in the room to equip / !remove <sockname> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq a":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Accesories 🧣: {getclothes('assec')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <assessoriesname> in the room to equip / !remove <assessoriesname> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")
                
            elif message.lower() == "eq fh":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Face hairs 👱‍♀️: {getclothes('face')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <facehairname> in the room to equip / !remove <facehairname> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq eb":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Eyebrows 👁‍🗨: {getclothes('eyebrow')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <eyebrowname> in the room to equip / !remove <eyebrowname> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq e":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Eyes 👁: {getclothes('eye')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <eyename> in the room to equip / !remove <eyename> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq n":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Noses 👃: {getclothes('nose')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <nosename> in the room to equip / !remove <nosename> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq m":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Mouth 👄: {getclothes('mouth')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <mouthname> in the room to equip / !remove <mouthname> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower() == "eq fr":
                if user_id == self.owner_id:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Here are the list of Freckles ☺: {getclothes('freckle')}")
                    await self.highrise.send_message(
                        conversation_id,
                        f"\n\nUsage ⌨: Type !equip <frecklename> in the room to equip / !remove <frecklename> in the room to remove \n Note that the names are case sensitive"
                    )
                else:
                    await self.highrise.send_message(
                        conversation_id,
                        f"Sorry, you don't have access to this command")

            elif message.lower().startswith("تغيير الحذاء "):
                if user_id == self.owner_id or user_id in self.admins:
                    try:
                        parts = message.split()
                        if len(parts) >= 3:
                            shoe_id = parts[2].strip()
                            
                            async def quick_wear(i_id):
                                try:
                                    from highrise.models import Item as HRItem2
                                    # جلب الملابس الحالية
                                    current_outfit = await self.highrise.get_my_outfit()
                                    new_outfit = []
                                    
                                    # فلترة الملابس الحالية لإزالة أي حذاء قديم (الحذاء معرفه يبدأ بـ shoes-)
                                    for item in current_outfit.outfit:
                                        if hasattr(item, 'id') and item.id.startswith("shoes-"):
                                            continue
                                        new_outfit.append(item)
                                    
                                    # إضافة الحذاء الجديد - جميع الملابس في Highrise type="clothing"
                                    new_outfit.append(HRItem2(type="clothing", amount=1, id=i_id))
                                    
                                    # تعيين الملابس الجديدة
                                    await self.highrise.set_outfit(new_outfit)
                                    print(f"Successfully changed shoes to {i_id}")
                                    
                                    # إرسال رسالة تأكيد في الروم للتأكد من الرؤية
                                    await self.highrise.chat(f"👞 Shoes changed to ID: {i_id}" if self.bot_lang == "en" else f"👞 تم تغيير حذائي إلى المعرف: {i_id}")
                                except Exception as e:
                                    print(f"Error changing shoes: {e}")
                                    await self.highrise.chat(f"❌ Failed to change shoes: {e}" if self.bot_lang == "en" else f"❌ فشل تغيير الحذاء: {e}")
                            
                            asyncio.create_task(quick_wear(shoe_id))
                            await self.highrise.send_message(conversation_id, f"✅ جاري معالجة تغيير الحذاء إلى: {shoe_id}...")
                    except Exception as e:
                        print(f"Error in shoe change command: {e}")
                else:
                    await self.highrise.send_message(conversation_id, "عذراً، هذا الأمر للمطور والمشرفين فقط")

            elif message.lower() == "نقاطي":
                # Get user info from conversation
                try:
                    # Find the user by their ID to get username
                    room_users = await self.highrise.get_room_users()
                    requesting_user = None
                    for room_user, _ in room_users.content:
                        if room_user.id == user_id:
                            requesting_user = room_user
                            break
                    
                    if requesting_user:
                        user_points = self.get_user_points(user_id)
                        user_level = self.calculate_user_level(user_points)
                        next_level_points = self.get_points_for_next_level(user_points)
                        
                        # عرض النقاط بالشكل الجديد
                        if user_level == 16:
                            # الحد الأقصى
                            await self.highrise.send_message(
                                conversation_id, 
                                f"Points:\n@{requesting_user.username}, {user_points}XP/70000XP, Level: {user_level}"
                            )
                        elif user_level == 0:
                            # قبل المستوى الأول
                            await self.highrise.send_message(
                                conversation_id, 
                                f"Points:\n@{requesting_user.username}, {user_points}XP/30XP, Level: {user_level}"
                            )
                        else:
                            # مستويات عادية
                            await self.highrise.send_message(
                                conversation_id, 
                                f"Points:\n@{requesting_user.username}, {user_points}XP/{next_level_points}XP, Level: {user_level}"
                            )
                    else:
                        await self.highrise.send_message(
                            conversation_id, 
                            "❌ لم أتمكن من العثور عليك في الروم"
                        )
                except Exception as e:
                    print(f"Error in نقاطي command: {e}")
                    await self.highrise.send_message(
                        conversation_id, 
                        f"❌ حدث خطأ في استرجاع نقاطك"
                    )

            elif message.lower() == "!xp":
                # Get user info from conversation
                try:
                    # This is a DM, so we need to find the user by their ID
                    room_users = await self.highrise.get_room_users()
                    requesting_user = None
                    for room_user, _ in room_users.content:
                        if room_user.id == user_id:
                            requesting_user = room_user
                            break
                    
                    # Check if user is owner only
                    is_owner = requesting_user and requesting_user.username in self.owners
                    
                    if is_owner:
                        # Get all users with points and create leaderboard
                        if not self.user_points:
                            await self.highrise.send_message(conversation_id, "📊 No XP data available yet")
                            return

                        # Create leaderboard with user info
                        leaderboard_data = []
                        
                        # Get all room users first for username lookup
                        room_user_map = {}
                        for room_user, _ in room_users.content:
                            room_user_map[room_user.id] = room_user.username

                        # Process all users with points
                        for user_id_key, points in self.user_points.items():
                            # Skip bot's own points
                            if user_id_key == self.bot_id:
                                continue
                                
                            username = room_user_map.get(user_id_key, f"Unknown_User_{user_id_key[:8]}")
                            current_level = self.calculate_user_level(points)
                            next_level_points = self.get_points_for_next_level(points)
                            remaining_points = max(0, next_level_points - points)
                            
                            leaderboard_data.append({
                                'username': username,
                                'points': points,
                                'level': current_level,
                                'remaining': remaining_points,
                                'next_level_points': next_level_points
                            })

                        # Sort by points (highest first)
                        leaderboard_data.sort(key=lambda x: x['points'], reverse=True)
                        
                        if not leaderboard_data:
                            await self.highrise.send_message(conversation_id, "📊 No users with XP found")
                            return

                        # Create leaderboard message
                        leaderboard_msg = "🏆 XP Leaderboard (Owner Only):\n\n"
                        
                        for i, user_data in enumerate(leaderboard_data[:20], 1):  # Top 20 users
                            username = user_data['username']
                            points = user_data['points']
                            level = user_data['level']
                            remaining = user_data['remaining']
                            next_level_points = user_data['next_level_points']
                            
                            # Medal emojis for top 3
                            if i == 1:
                                rank_emoji = "🥇"
                            elif i == 2:
                                rank_emoji = "🥈"
                            elif i == 3:
                                rank_emoji = "🥉"
                            else:
                                rank_emoji = f"{i}."
                            
                            # Format based on if they're at max level or not
                            if level >= 16:  # Max level
                                leaderboard_msg += f"{rank_emoji} @{username}\n"
                                leaderboard_msg += f"   💎 {points} XP | Level {level} (MAX)\n\n"
                            else:
                                leaderboard_msg += f"{rank_emoji} @{username}\n"
                                leaderboard_msg += f"   ⚡ {points} XP | Level {level}\n"
                                leaderboard_msg += f"   📈 Need {remaining} more for Level {level + 1}\n"
                                leaderboard_msg += f"   🎯 Next: {next_level_points} XP\n\n"

                        # Split message if too long
                        if len(leaderboard_msg) > 4000:
                            # Send first part
                            first_part = leaderboard_msg[:3500]
                            last_newline = first_part.rfind('\n\n')
                            if last_newline != -1:
                                first_part = first_part[:last_newline]
                            
                            await self.highrise.send_message(conversation_id, first_part + "\n\n[Continued...]")
                            
                            # Send second part
                            remaining_msg = leaderboard_msg[len(first_part):]
                            await self.highrise.send_message(conversation_id, "[Continued...]\n" + remaining_msg)
                        else:
                            await self.highrise.send_message(conversation_id, leaderboard_msg)
                        
                        # Summary message
                        total_users = len(leaderboard_data)
                        avg_points = sum(user['points'] for user in leaderboard_data) / total_users
                        max_level_users = sum(1 for user in leaderboard_data if user['level'] >= 16)
                        
                        summary = f"📊 Summary:\n"
                        summary += f"👥 Total Users: {total_users}\n"
                        summary += f"📈 Average XP: {avg_points:.1f}\n"
                        summary += f"💎 Max Level Users: {max_level_users}\n"
                        summary += f"🎯 Highest XP: {leaderboard_data[0]['points']} (@{leaderboard_data[0]['username']})"
                        
                        await self.highrise.send_message(conversation_id, summary)
                        
                    else:
                        await self.highrise.send_message(
                            conversation_id, "❌ This command is only available to bot owners")
                            
                except Exception as e:
                    print(f"Error in !XP command: {e}")
                    await self.highrise.send_message(
                        conversation_id, "❌ Error occurred while generating XP leaderboard")

            elif message.lower() == "evemo":
                # Get user info from conversation
                try:
                    # This is a DM, so we need to find the user by their ID
                    room_users = await self.highrise.get_room_users()
                    requesting_user = None
                    for room_user, _ in room_users.content:
                        if room_user.id == user_id:
                            requesting_user = room_user
                            break
                    
                    # Check if user is owner or has admin privileges
                    is_owner = requesting_user and requesting_user.username in self.owners
                    is_admin = requesting_user and any(requesting_user.username.lower() == admin.lower() for admin in self.admins)
                    
                    if is_owner or is_admin:
                        dance_list = []
                        
                        # جمع الرقصات من emote_mapping
                        from emotes import emote_mapping
                        for key, value in emote_mapping.items():
                            if "dance" in value["value"]:
                                dance_list.append(f"{key}: {value['value']}")
                        
                        # ترتيب القائمة حسب الرقم
                        dance_list.sort(key=lambda x: int(x.split(':')[0]) if x.split(':')[0].isdigit() else float('inf'))
                        
                        # تقسيم القائمة إلى مجموعات صغيرة لتجنب تجاوز حد الرسالة
                        chunk_size = 20
                        for i in range(0, len(dance_list), chunk_size):
                            chunk = dance_list[i:i+chunk_size]
                            message_text = "🕺 All Dances 💃:\n" + "\n".join(chunk)
                            await self.highrise.send_message(conversation_id, message_text)
                        
                        await self.highrise.send_message(
                            conversation_id,
                            "\n\nUsage ⌨: Type !emote <number> in the room to perform the dance\nExample: !emote 23 for icecream dance"
                        )
                    else:
                        await self.highrise.send_message(
                            conversation_id, f"Sorry, you don't have access to this command")
                except Exception as e:
                    print(f"Error in evemo command: {e}")
                    await self.highrise.send_message(
                        conversation_id, f"Error occurred while processing the command")

            elif message.lower().startswith("hi"):
                await self.highrise.send_message(
                    conversation_id,
                    "Hey, How's your day? ☺ \nTo show you list of available options, type help"
                )

            elif message.lower().strip() in ["شراء بوت", "شراء البوت", "متجر البوت", "متجر", "buy bot", "buybot", "shop", "اشتري بوت", "اشتري البوت"]:
                if self.bot_lang == "en":
                    shop_msg = (
                        f"🤖 Welcome to the Bot Store!\n\n"
                        f"💎 Available Packages:\n\n"
                        f"⏱️ 1 Hour       ← Send 1 gold\n"
                        f"⏱️ 3 Hours      ← Send 3,000 gold\n"
                        f"📅 Full Day     ← Send 10,000 gold\n"
                        f"📅 Full Week   ← Send 50,000 gold\n\n"
                        f"📌 How to buy:\n"
                        f"1️⃣ Send the required gold to this bot\n"
                        f"2️⃣ The bot will ask for your room name\n"
                        f"3️⃣ Send the room name and it will be activated!\n\n"
                        f"📞 For help: @_king_man_1"
                    )
                else:
                    shop_msg = (
                        f"🤖 أهلاً في متجر البوت!\n\n"
                        f"💎 الباقات المتاحة:\n\n"
                        f"⏱️ ساعة واحدة    ← أرسل 1 ذهب\n"
                        f"⏱️ 3 ساعات         ← أرسل 3,000 ذهب\n"
                        f"📅 يوم كامل         ← أرسل 10,000 ذهب\n"
                        f"📅 أسبوع كامل    ← أرسل 50,000 ذهب\n\n"
                        f"📌 طريقة الشراء:\n"
                        f"1️⃣ أرسل المبلغ المطلوب ذهباً لهذا البوت\n"
                        f"2️⃣ سيطلب منك البوت اسم الغرفة\n"
                        f"3️⃣ أرسل اسم الغرفة وسيتم التفعيل!\n\n"
                        f"📞 للمساعدة: @_king_man_1"
                    )
                await self.highrise.send_message(conversation_id, shop_msg)

            elif message.strip().lower() in ["en", "english", "انجليزي", "إنجليزي"]:
                self.bot_lang = "en"
                self.save_bot_lang()
                self.user_lang_prefs[user_id] = "en"
                self.save_user_lang_prefs()
                await self.highrise.send_message(conversation_id, "✅ Bot language changed to English 🇺🇸\nAll responses will now be in English.")

            elif message.strip().lower() in ["ar", "arabic", "عربي", "عربية"]:
                self.bot_lang = "ar"
                self.save_bot_lang()
                self.user_lang_prefs[user_id] = "ar"
                self.save_user_lang_prefs()
                await self.highrise.send_message(conversation_id, "✅ تم تغيير لغة البوت إلى العربية 🇸🇦\nجميع الردود ستكون بالعربية الآن.")

            elif message.lower().strip() in ["رصيدي", "رصيد", "طلباتي", "طلباتى", "my balance", "mybalance", "myorders"]:
                _bal = self.user_wallets.get(user_id, 0)
                balance_msg = (
                    f"💲 رصيدك: {_bal:,} ذهب\n\n"
                    f"يمكنك إعطاء هذا البوت لزيادة رصيدك."
                )
                await self.highrise.send_message(conversation_id, balance_msg)

            elif message.lower().strip() in ["وقتي", "وقت", "الوقت المتبقي", "remaining", "mytime", "my time"]:
                _bots_data = load_sub_bots()
                _user_bot = next((b for b in _bots_data if b.get("buyer_id") == user_id and b["status"] in ("busy", "paused")), None)
                user_active = [o for o in self.bot_shop_orders if o.get("buyer_id") == user_id and o.get("status") == "active" and o.get("expires_at")]
                if not _user_bot and not user_active:
                    await self.highrise.send_message(conversation_id,
                        "⏰ ليس لديك أي بوت نشط حالياً.\n\n🛒 لشراء بوت اكتب: شراء بوت"
                    )
                else:
                    now = datetime.now()
                    if _user_bot:
                        bot_uname = _user_bot.get("username", "غير محدد")
                        bot_status = "نشط ✅" if _user_bot["status"] == "busy" else "موقوف مؤقتاً ⏸️"
                        if _user_bot["status"] == "busy" and _user_bot.get("expires_at"):
                            exp_dt = datetime.strptime(_user_bot["expires_at"], "%Y-%m-%d %H:%M:%S")
                            secs = max(0, int((exp_dt - now).total_seconds()))
                            h = secs // 3600
                            m = (secs % 3600) // 60
                            time_left = f"{h} ساعة و {m} دقيقة" if h > 0 else f"{m} دقيقة"
                            expires_line = f"⏰ ينتهي في: {_user_bot['expires_at']}\n"
                        elif _user_bot["status"] == "paused" and _user_bot.get("remaining_seconds"):
                            secs = max(0, int(_user_bot["remaining_seconds"]))
                            h = secs // 3600
                            m = (secs % 3600) // 60
                            time_left = f"{h} ساعة و {m} دقيقة" if h > 0 else f"{m} دقيقة"
                            expires_line = ""
                        else:
                            time_left = "غير محدد"
                            expires_line = ""
                        time_msg = (
                            f"🤖 معلومات بوتك:\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"👤 يوزر البوت: @{bot_uname}\n"
                            f"📊 الحالة: {bot_status}\n"
                            f"⏳ الوقت المتبقي: {time_left}\n"
                            f"{expires_line}"
                        )
                    else:
                        ord_ = user_active[0]
                        bot_uname = ord_.get("bot_username", "غير محدد")
                        try:
                            exp_dt = datetime.strptime(ord_["expires_at"], "%Y-%m-%d %H:%M:%S")
                            secs = max(0, int((exp_dt - now).total_seconds()))
                            h = secs // 3600
                            m = (secs % 3600) // 60
                            time_left = f"{h} ساعة و {m} دقيقة" if h > 0 else f"{m} دقيقة"
                            expires_str = ord_["expires_at"]
                        except Exception:
                            time_left = "غير محدد"
                            expires_str = ""
                        time_msg = (
                            f"🤖 معلومات بوتك:\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"👤 يوزر البوت: @{bot_uname}\n"
                            f"⏳ الوقت المتبقي: {time_left}\n"
                            f"⏰ ينتهي في: {expires_str}\n"
                        )
                    await self.highrise.send_message(conversation_id, time_msg)

            else:
                await self.highrise.send_message(
                    conversation_id,
                    f"I can't understand your message, type help for further assistance..\n\n🛒 لشراء بوت لغرفتك اكتب: buybot"
                )

            commands_keywords = ["اوامر", "أوامر", "الاوامر", "الأوامر", "مساعدة", "مساعده", "help", "امر", "commands"]
            if message.strip() in commands_keywords or message.strip().lower() in commands_keywords:
                print(f"[DM-COMMANDS] Sending commands to user_id={user_id}")
                is_owner_dm = False
                is_mod_dm = False
                is_vip_dm = False
                try:
                    room_users_dm = await self.highrise.get_room_users()
                    for ru, _ in room_users_dm.content:
                        if ru.id == user_id:
                            is_owner_dm = ru.username in self.owners
                            is_vip_dm = ru.username in self.vips
                            break
                    priv_dm = await self.highrise.get_room_privilege(user_id)
                    is_mod_dm = priv_dm.moderator
                except Exception:
                    pass

                await self.highrise.send_message(conversation_id,
"🤖 أوامر البوت - الجزء 1 (الرقص)\n\n• رقم 1-223 للرقص الفوري\n• loop [رقم] رقص مستمر\n• رقصني رقص عشوائي\n• ارقص [رقم] رقص محدد\n• dance floor رقص عشوائي مستمر\n• floss forever رقصة فلوس مستمرة\n• 0 / stop / توقف إيقاف الرقص\n• nodance إيقاف رقصات الجميع\n• nofloss إيقاف الفلوس")
                await asyncio.sleep(2)

                await self.highrise.send_message(conversation_id,
"❤️ الجزء 2 (التفاعل والمواقع)\n\n• h @user [عدد] إرسال قلوب\n• h all قلوب للجميع\n• wink @user غمزة\n• like @user إعجاب\n• كف @user صفعة مرحة\n• اسحر @user سحر مرح\n• بوسه / kiss قبلة\n\n📍 المواقع:\n• نص وسط الروم\n• فوق للأعلى\n• تحت للأسفل\n• vip منطقة VIP\n• الطوابق عرض الطوابق")
                await asyncio.sleep(2)

                await self.highrise.send_message(conversation_id,
"ℹ️ الجزء 3 (المعلومات)\n\n• info @user معلومات المستخدم\n• ping فحص الاتصال\n• time مدة تشغيل البوت\n• list قائمة الرقصات\n• نقاطي عرض نقاطك\n• ترجمة [نص] ترجمة نص\n• احداثيات @user إحداثيات المستخدم\n• تحذيراته @user عرض تحذيرات المستخدم")
                await asyncio.sleep(2)

                await self.highrise.send_message(conversation_id,
"👗 الجزء 4 (الملابس)\n\n• اضف [معرف] إضافة ملبس\n• اخلع [معرف] خلع ملبس\n• اخلع الكل خلع كل الملابس\n• اضف شعر [رقم] إضافة شعر\n• اضف تيشيرت [رقم] إضافة قميص\n• اضف عين [رقم] إضافة عيون\n• اضف قبعة [رقم] إضافة قبعة\n• اضف الاكسسوار [رقم] إضافة اكسسوار\n• اضف البنطال [رقم] إضافة بنطال\n• اضف الفم [رقم] إضافة فم\n• اضف النظارات [رقم] إضافة نظارات\n• اضف الوشم [رقم] إضافة وشم\n• مخزوني عرض المخزون")
                await asyncio.sleep(2)

                if is_owner_dm or is_mod_dm:
                    await self.highrise.send_message(conversation_id,
"🛡️ الجزء 5 (المشرفين - النقل)\n\n• tel / روح @user انتقال للمستخدم\n• اسحب @user جلب المستخدم\n• follow / الحق @user متابعة\n• move @u1 @u2 نقل مستخدم\n• بدل @user تبديل المواقع\n• مرجح @user تحريك عشوائي\n• وقف @user إيقاف التحريك\n• ودي @user إرسال لموقع عشوائي\n• fix @user تثبيت موقع\n• go @user إلغاء التثبيت\n• جيب الكل جلب الجميع\n• ابعد الكل إبعاد الجميع")
                    await asyncio.sleep(2)

                    await self.highrise.send_message(conversation_id,
"🛡️ الجزء 6 (المشرفين - الإدارة)\n\n• !kick @user طرد\n• !ban @user [دقائق] حظر\n• !unban @user فك الحظر\n• !mute @user [دقائق] كتم\n• !unmute @user فك الكتم\n• تحذير @user تحذير\n• ازاله تحذير @user إزالة تحذير\n• السجن / سجن @user سجن\n• حمايه @user حماية مستخدم\n• حفظ حفظ موقع البوت\n• مكانك إرجاع البوت لمكانه\n• افتح / قفل الغرفة فتح وقفل")
                    await asyncio.sleep(2)

                    await self.highrise.send_message(conversation_id,
"🛡️ الجزء 7 (المشرفين - VIP والإعلانات)\n\n• addvip @user إضافة VIP تصميم\n• removevip @user إزالة VIP تصميم\n• !addvip @user إضافة VIP قلوب\n• !removevip @user إزالة VIP قلوب\n• addswm @user رسالة ترحيب خاص\n• removeswm @user حذف ترحيب\n• all [رقم] رقصة للجميع\n• الكل vip رقصة VIP للجميع\n• spam رسالة تكرار رسائل\n• nospam إيقاف التكرار\n• اعلان رسالة إعلان مستمر\n• vip2 list قائمة VIP القلوب\n• swm list قائمة الترحيبات\n• !adminlist قائمة المشرفين")
                    await asyncio.sleep(2)

                await self.highrise.send_message(conversation_id,
f"🌟 صلاحيتك: {'أونر 👑' if is_owner_dm else 'مشرف 🛡️' if is_mod_dm else 'VIP ⭐' if is_vip_dm else 'مستخدم عادي'}\nتابع صاحب البوت: @_king_man_1")

        except Exception as e:
            print(f"[DM] on_message error: {e}")
            try:
                await self.highrise.send_message(conversation_id, f"❌ خطأ: {e}")
            except Exception:
                pass


    async def announcement_loop(self):
        """حلقة لإرسال الإعلانات التلقائية كل دقيقتين"""
        while self.announcement_message:
            try:
                await self.highrise.chat(f"📢 Announcement: {self.announcement_message}" if self.bot_lang == "en" else f"📢 إعلان: {self.announcement_message}")
                await asyncio.sleep(120)  # الانتظار لمدة دقيقتين (120 ثانية)
            except Exception as e:
                print(f"Error in announcement loop: {e}")
                await asyncio.sleep(10)

    async def subscription_loop(self):
        """حلقة إرسال دعوات للمشتركين كل دقيقتين"""
        while True:
            await asyncio.sleep(120)  # انتظر دقيقتين
            if not self.subscribers:
                continue
            try:
                user_ids = set(self.subscribers.keys())
                invite_text = "الروم معتم ادخل عشان ينور"
                success_count = 0

                # جلب جميع المحادثات الحالية للبوت
                conversations_resp = await self.highrise.get_conversations()
                if isinstance(conversations_resp, Exception) or hasattr(conversations_resp, 'message'):
                    print(f"[Subscription] خطأ في جلب المحادثات: {conversations_resp}")
                    continue

                conversations = getattr(conversations_resp, 'conversations', [])

                # تتبع المشتركين الذين تم إرسال دعوة لهم
                reached_users = set()

                for conv in conversations:
                    member_ids = {m.id for m in getattr(conv, 'members', [])}
                    matched = member_ids & user_ids
                    if not matched:
                        continue
                    try:
                        res = await self.highrise.send_message(
                            conv.id,
                            invite_text,
                            "invite",
                            self.room_id,
                        )
                        if res is not None:
                            print(f"[Subscription] فشل الإرسال في المحادثة {conv.id}: {res}")
                        else:
                            reached_users |= matched
                            success_count += len(matched)
                    except Exception as e:
                        print(f"[Subscription] استثناء في المحادثة {conv.id}: {e}")

                # للمشتركين الذين لا توجد محادثة معهم بعد، جرب send_message_bulk كـ fallback
                unreached = user_ids - reached_users
                for uid in unreached:
                    try:
                        res = await self.highrise.send_message_bulk(
                            [uid], invite_text, "invite", self.room_id
                        )
                        if res is None:
                            success_count += 1
                        else:
                            print(f"[Subscription] fallback فشل لـ {uid}: {res}")
                    except Exception as e:
                        print(f"[Subscription] fallback استثناء لـ {uid}: {e}")

                print(f"[Subscription] تم إرسال دعوة لـ {success_count}/{len(user_ids)} مشترك")
            except Exception as e:
                print(f"[Subscription] خطأ في إرسال الدعوات: {e}")

    async def on_chat(self, user: User, message: str) -> None:
        """On a received room-wide chat."""
        import time
        self.last_heartbeat = time.time()
        
        # منع الدردشة إذا كان الكتم العام مفعلاً
        if hasattr(self, 'mute_all_active') and self.mute_all_active:
            # السماح فقط للملاك والمشرفين بالكلام
            if not await self.is_user_allowed(user):
                return

        # منع الدردشة إذا كان قفل الدردشة مفعلاً
        if hasattr(self, 'chat_locked') and self.chat_locked:
            # السماح فقط للملاك والمشرفين بالكتابة
            if not await self.is_user_allowed(user):
                return

        # Command execution flag to ensure only one command runs
        command_executed = False
        original_message = message.strip()

        # ==================== تحديث نشاط المستخدم (لنظام autokick) ====================
        import time as _time_module
        self.user_last_active[user.id] = _time_module.time()

        # ==================== فحص القائمة السوداء ====================
        if hasattr(self, 'bot_blacklist') and any(b.lower() == user.username.lower() for b in self.bot_blacklist):
            return

        # ==================== وضع الصمت ====================
        if self.silent_mode:
            _uname_s = user.username.lower()
            _is_owner_or_admin = any(_uname_s == o.lower() for o in self.owners) or any(_uname_s == a.lower() for a in self.admins)
            if not _is_owner_or_admin:
                return

        # ==================== فلتر الكلمات المحظورة ====================
        _uname_l = user.username.lower()
        if self.filtered_words and not any(o.lower() == _uname_l for o in self.owners) and not any(a.lower() == _uname_l for a in self.admins):
            msg_lower = original_message.lower()
            for bad_word in self.filtered_words:
                if bad_word.lower() in msg_lower:
                    try:
                        await self.highrise.moderate_room(user.id, "kick")
                        if self.bot_lang == "en":
                            await self.highrise.chat(f"🚫 @{user.username} was kicked for using a banned word.")
                        else:
                            await self.highrise.chat(f"🚫 @{user.username} was kicked for using a banned word." if self.bot_lang == "en" else f"🚫 تم طرد @{user.username} بسبب استخدام كلمة محظورة.")
                    except Exception as e:
                        print(f"filter kick error: {e}")
                    return

        # ==================== أمر !filter (للأونر والأدمن فقط) ====================
        if original_message.lower().startswith("!filter") and await self.is_user_allowed(user):
            parts = original_message.split(maxsplit=2)
            sub = parts[1].lower() if len(parts) > 1 else ""
            if sub == "list":
                if not self.filtered_words:
                    await self.highrise.chat("📋 قائمة الكلمات المحظورة فارغة حالياً." if self.bot_lang == "ar" else "📋 The filter list is empty.")
                else:
                    words_str = " | ".join(self.filtered_words)
                    await self.highrise.chat(f"🔴 الكلمات المحظورة ({len(self.filtered_words)}):\n{words_str}" if self.bot_lang == "ar" else f"🔴 Banned words ({len(self.filtered_words)}): {words_str}")
            elif sub == "add" and len(parts) > 2:
                word = parts[2].strip().lower()
                if word in [w.lower() for w in self.filtered_words]:
                    await self.highrise.chat(f"⚠️ الكلمة '{word}' موجودة بالفعل في القائمة." if self.bot_lang == "ar" else f"⚠️ '{word}' is already in the filter list.")
                else:
                    self.filtered_words.append(word)
                    self.save_filtered_words()
                    await self.highrise.chat(f"✅ تم إضافة '{word}' إلى قائمة الكلمات المحظورة." if self.bot_lang == "ar" else f"✅ '{word}' added to filter list.")
            elif sub == "remove" and len(parts) > 2:
                word = parts[2].strip().lower()
                before = len(self.filtered_words)
                self.filtered_words = [w for w in self.filtered_words if w.lower() != word]
                if len(self.filtered_words) < before:
                    self.save_filtered_words()
                    await self.highrise.chat(f"✅ تم حذف '{word}' من قائمة الكلمات المحظورة." if self.bot_lang == "ar" else f"✅ '{word}' removed from filter list.")
                else:
                    await self.highrise.chat(f"❌ الكلمة '{word}' غير موجودة في القائمة." if self.bot_lang == "ar" else f"❌ '{word}' not found in filter list.")
            else:
                await self.highrise.chat("📋 أوامر الفلتر:\n• !filter list - عرض القائمة\n• !filter add [كلمة] - إضافة كلمة\n• !filter remove [كلمة] - حذف كلمة" if self.bot_lang == "ar" else "📋 Filter commands:\n• !filter list\n• !filter add [word]\n• !filter remove [word]")
            return

        # ==================== أمر !autokick (للأونر والأدمن فقط) ====================
        if original_message.lower().startswith("!autokick") and await self.is_user_allowed(user):
            parts = original_message.split()
            if len(parts) < 2:
                status = f"مفعل ({self.autokick_minutes} دقيقة)" if self.autokick_minutes > 0 else "معطل"
                await self.highrise.chat(f"⏱️ الطرد التلقائي: {status}\nالاستخدام: !autokick [دقائق] | !autokick 0 لإيقافه" if self.bot_lang == "ar" else f"⏱️ Auto-kick: {'enabled ('+str(self.autokick_minutes)+' min)' if self.autokick_minutes > 0 else 'disabled'}\nUsage: !autokick [minutes] | !autokick 0 to disable")
            else:
                try:
                    minutes = int(parts[1])
                    self.autokick_minutes = minutes
                    if self.autokick_task:
                        self.autokick_task.cancel()
                        self.autokick_task = None
                    if minutes > 0:
                        self.autokick_task = asyncio.create_task(self.autokick_loop())
                        await self.highrise.chat(f"✅ تم تفعيل الطرد التلقائي: {minutes} دقيقة من الخمول." if self.bot_lang == "ar" else f"✅ Auto-kick enabled: {minutes} minutes of inactivity.")
                    else:
                        await self.highrise.chat("⏹️ تم إيقاف الطرد التلقائي." if self.bot_lang == "ar" else "⏹️ Auto-kick disabled.")
                except ValueError:
                    await self.highrise.chat("❌ يجب إدخال رقم صحيح. مثال: !autokick 10" if self.bot_lang == "ar" else "❌ Please enter a valid number. Example: !autokick 10")
            return

        # ==================== أمر تغيير لغة البوت بالكامل (للجميع) ====================
        if original_message.strip().lower() in ["en", "english", "انجليزي", "إنجليزي"]:
            self.bot_lang = "en"
            self.save_bot_lang()
            self.user_lang_prefs[user.id] = "en"
            self.save_user_lang_prefs()
            await self.highrise.chat("✅ Bot language changed to English 🇺🇸\nAll responses will now be in English.")
            return
        if original_message.strip().lower() in ["ar", "arabic", "عربي", "عربية"]:
            self.bot_lang = "ar"
            self.save_bot_lang()
            self.user_lang_prefs[user.id] = "ar"
            self.save_user_lang_prefs()
            await self.highrise.chat("✅ Bot language changed to Arabic 🇸🇦\nAll responses will now be in Arabic." if self.bot_lang == "en" else "✅ تم تغيير لغة البوت إلى العربية 🇸🇦\nجميع الردود ستكون بالعربية الآن.")
            return

        # ==================== أمر !lang (للأونر والأدمن فقط) ====================
        if (original_message.lower().startswith("!lang") or original_message.lower().startswith("تغيير اللغه")) and await self.is_user_allowed(user):
            parts = original_message.split()
            if len(parts) < 2:
                await self.highrise.chat(f"🌐 اللغة الحالية: {'العربية' if self.bot_lang == 'عربي' else 'الإنجليزية'}\nاستخدم: !lang ar أو !lang en" if self.bot_lang == "ar" else f"🌐 Current language: {'Arabic' if self.bot_lang == 'ar' else 'English'}\nUse: !lang ar or !lang en")
            else:
                lang = parts[1].lower()
                if lang in ("ar", "arabic", "عربي", "عربية", "arc"):
                    self.bot_lang = "ar"
                    self.save_bot_lang()
                    await self.highrise.chat("✅ Bot language changed to Arabic 🇸🇦" if self.bot_lang == "en" else "✅ تم تغيير لغة البوت إلى العربية 🇸🇦")
                elif lang in ("en", "english", "انجليزي", "إنجليزية"):
                    self.bot_lang = "en"
                    self.save_bot_lang()
                    await self.highrise.chat("✅ Bot language changed to English 🇺🇸")
                else:
                    await self.highrise.chat("❌ اللغات المتاحة: ar (العربية) | en (الإنجليزية)" if self.bot_lang == "ar" else "❌ Available languages: ar (Arabic) | en (English)")
            return

        # ==================== أمر !get (للجميع - عرض إجمالي تبرعات لاعب) ====================
        if original_message.lower().startswith("تبرعاته") and len(original_message.split()) > 1:
            parts = original_message.split()
            target = parts[1].lstrip("@").strip()
            total = self.tip_history.get(target, self.tip_history.get(target.lower(), 0))
            if total > 0:
                if self.bot_lang == "en":
                    await self.highrise.chat(f"💰 @{target} total donations to the bot: {total} gold 🥇")
                else:
                    await self.highrise.chat(f"💰 @{target} total donations to bot: {total} gold 🥇" if self.bot_lang == "en" else f"💰 إجمالي تبرعات @{target} للبوت: {total} ذهب 🥇")
            else:
                if self.bot_lang == "en":
                    await self.highrise.chat(f"ℹ️ No donation records found for @{target}.")
                else:
                    await self.highrise.chat(f"ℹ️ No donation records found for @{target}." if self.bot_lang == "en" else f"ℹ️ لا توجد سجلات تبرعات لـ @{target}.")
            return

        # ==================== أمر تابعني (أولوية عليا - للأونر فقط) ====================
        # ==================== أمر إعادة التشغيل (للأونر فقط) ====================
        if original_message in ["!restart", "ريستارت", "اعاده التشغيل", "إعادة التشغيل"] and user.username in self.owners:
            await self.highrise.chat(f"🔄 Restarting bot by @{user.username}..." if self.bot_lang == "en" else f"🔄 جاري إعادة تشغيل البوت بأمر @{user.username}...")
            import os as _os
            _os._exit(0)

        if original_message.startswith("!تابعني") and user.username in self.owners:
            parts = original_message.split()
            if len(parts) >= 2:
                new_room_id = parts[1].strip()
                RunBot.pending_follow = True
                RunBot.room_id = new_room_id
                print(f"[Follow] الأونر طلب الانتقال للغرفة: {new_room_id}")
                await self.highrise.chat(f"⏳ Moving to the new room..." if self.bot_lang == "en" else f"⏳ جاري الانتقال للغرفة الجديدة...")
                raise Exception(f"[Follow] الانتقال لغرفة جديدة: {new_room_id}")
            else:
                await self.highrise.chat("⚠️ Correct format: !تابعني [room_id]" if self.bot_lang == "en" else "⚠️ الصيغة الصحيحة: !تابعني [room_id]")
            return

        # ==================== أمر اللهجة (للأونر والأدمن) ====================
        if original_message.startswith("لهجة") and await self.is_user_allowed(user):
            parts = original_message.split(maxsplit=1)
            available = ["فصحى", "عراقية", "مصرية", "خليجية", "شامية"]
            if len(parts) == 1:
                # عرض اللهجة الحالية والمتاحة
                await self.highrise.chat(
                    f"🗣️ اللهجة الحالية: {self.dialect}\n"
                    f"📋 اللهجات المتاحة: {' | '.join(available)}\n"
                    f"💡 مثال: لهجة عراقية"
                )
            else:
                chosen = parts[1].strip()
                if chosen in available:
                    self.dialect = chosen
                    if chosen == "فصحى":
                        await self.highrise.chat(f"✅ Dialect changed to: {chosen} (no change)" if self.bot_lang == "en" else f"✅ تم تغيير اللهجة إلى: {chosen} (بدون تغيير)")
                    else:
                        await self.highrise.chat(f"✅ Dialect changed to: {chosen} 🎙️" if self.bot_lang == "en" else f"✅ تم تغيير اللهجة إلى: {chosen} 🎙️")
                else:
                    await self.highrise.chat(
                        f"❌ لهجة غير موجودة!\n"
                        f"📋 اللهجات المتاحة: {' | '.join(available)}"
                    )
            return

        # ==================== أمر اذهب (للأونر فقط) ====================
        if original_message.startswith("اذهب ") and user.username in self.owners:
            target = original_message.split("اذهب ", 1)[1].strip()
            if target:
                # أولاً: تحقق إذا كان الاسم موقعاً محفوظاً
                if target in self.teleport_locations:
                    try:
                        target_pos = self.teleport_locations[target]
                        await self.highrise.teleport(user.id, target_pos)
                        await self.highrise.send_whisper(user.id, f"✈️ تم نقلك إلى '{target}'")
                    except Exception as e:
                        print(f"Error teleporting to location {target}: {e}")
                    return
                # ثانياً: إذا لم يكن موقعاً، استخدمه كـ room_id للانتقال للغرفة
                RunBot.pending_follow = False
                RunBot.room_id = target
                print(f"[اذهب] الانتقال للغرفة: {target}")
                await self.highrise.chat(f"⏳ Moving to room..." if self.bot_lang == "en" else f"⏳ جاري الانتقال للغرفة...")
                raise Exception(f"[اذهب] الانتقال لغرفة: {target}")
            else:
                await self.highrise.chat("⚠️ Correct format: اذهب [place name] or اذهب [room_id]" if self.bot_lang == "en" else "⚠️ الصيغة الصحيحة: اذهب [اسم المكان] أو اذهب [room_id]")
            return

        # ==================== أوامر حفظ ومكان البوت (أولوية عليا) ====================

        if original_message == "حفظ" and await self.is_user_allowed(user):
            try:
                room_users = await self.highrise.get_room_users()
                # نحفظ مكان المستخدم الذي أرسل الأمر
                user_pos = None
                for room_user, position in room_users.content:
                    if room_user.id == user.id:
                        user_pos = position
                        break
                if user_pos and isinstance(user_pos, Position):
                    self.bot_start_position = user_pos
                    self.save_bot_position(user_pos)
                    await self.highrise.teleport(self.bot_id, user_pos)
                    await self.highrise.chat(f"✅ Location saved | X:{user_pos.x} Z:{user_pos.z}" if self.bot_lang == "en" else f"✅ تم حفظ الموقع | X:{user_pos.x} Z:{user_pos.z}")
                    print(f"[حفظ] تم حفظ الموقع: {user_pos}")
                else:
                    await self.highrise.chat("❌ Could not detect your location, try again" if self.bot_lang == "en" else "❌ لم أتمكن من تحديد موقعك، حاول مرة أخرى")
            except Exception as e:
                print(f"Error in حفظ command: {e}")
                await self.highrise.chat("❌ An error occurred while saving" if self.bot_lang == "en" else "❌ حدث خطأ أثناء الحفظ")
            return

        if original_message in ["مكانك؟", "مكانك?", "run", "مكانك"] or "مكانك" in original_message:
            print(f"[مكانك] تم استقبال الأمر من {user.username} | الموقع المحفوظ: {self.bot_start_position}")
            if self.bot_start_position:
                try:
                    await self.highrise.walk_to(self.bot_start_position)
                    await self.highrise.chat("This is my spot 🖐️😴" if self.bot_lang == "en" else "هاذا هو مكاني 🖐️😴")
                except Exception as e:
                    print(f"[مكانك] خطأ في الانتقال: {e}")
                    try:
                        await self.highrise.teleport(self.bot_id, self.bot_start_position)
                    except Exception:
                        await self.highrise.chat("❌ An error occurred during teleport" if self.bot_lang == "en" else "❌ حدث خطأ أثناء الانتقال")
            else:
                await self.highrise.chat("Starting location not set yet ❌" if self.bot_lang == "en" else "لم يتم تحديد موقع البداية بعد ❌")
            return

        # ==================== أوامر مباشرة (مبكرة لتجنب الـ return المبكرة) ====================

        # اضف عيون [eye_id] أو اضف عيون [n] [eye_id]
        if original_message.startswith("اضف عيون ") or original_message.startswith("اضف العيون "):
            if await self.is_user_allowed(user):
                try:
                    prefix = "اضف العيون " if original_message.startswith("اضف العيون ") else "اضف عيون "
                    remainder = original_message.replace(prefix, "").strip()
                    parts = remainder.split()
                    if len(parts) == 2 and (parts[0].isdigit() or parts[1].isdigit()):
                        # صيغة: اضف عيون [n] [eye_id] أو اضف عيون [eye_id] [n]
                        if parts[0].isdigit():
                            num, eye_id = parts[0], parts[1]
                        else:
                            eye_id, num = parts[0], parts[1]
                        self.eyes_list[num] = eye_id
                        self.save_eyes_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة العيون رقم {num} بمعرّف: {eye_id}")
                    elif len(parts) >= 1:
                        # صيغة: اضف عيون [eye_id] - تطبيق مباشر
                        eye_id = remainder
                        from highrise.models import Item as DirectEyeItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("eye-")]
                        new_outfit.append(DirectEyeItem(type="clothing", amount=1, id=eye_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تلبيس العيون:\n{eye_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف عيون 5 eye-n_xxx")
                except Exception as e:
                    print(f"Error equipping eye: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تلبيس العيون")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # ==================== أمر اضف ملامح (مبكر لتجنب مشاكل lowercase) ====================
        if original_message.startswith("اضف ملامح ") or original_message.startswith("اضف ملمح ") or original_message.startswith("اضف الملامح "):
            if await self.is_user_allowed(user):
                try:
                    for pfx in ["اضف الملامح ", "اضف ملامح ", "اضف ملمح "]:
                        if original_message.startswith(pfx):
                            parts = original_message.replace(pfx, "").strip().split()
                            break
                    if len(parts) == 2 and parts[0].isdigit():
                        num, feature_id = parts[0], parts[1]
                    elif len(parts) == 2 and parts[1].isdigit():
                        feature_id, num = parts[0], parts[1]
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف ملامح 5 freckle-n_xxx")
                        return
                    self.features_list[num] = feature_id
                    self.save_features_list()
                    await self.highrise.send_whisper(user.id, f"✅ تم إضافة الملامح رقم {num} بمعرّف: {feature_id}")
                except Exception as e:
                    print(f"Error adding feature: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة الملامح")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # ==================== أمر اضف اختفاء (مبكر لتجنب مشاكل lowercase) ====================
        if original_message.startswith("اضف اختفاء ") or original_message.startswith("اضف الاختفاء "):
            if await self.is_user_allowed(user):
                try:
                    prefix = "اضف الاختفاء " if original_message.startswith("اضف الاختفاء ") else "اضف اختفاء "
                    parts = original_message.replace(prefix, "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num, item_id = parts[0], parts[1]
                    elif len(parts) == 2 and parts[1].isdigit():
                        item_id, num = parts[0], parts[1]
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف اختفاء 5 item-n_xxx")
                        return
                    self.invisible_list[num] = item_id
                    self.save_invisible_list()
                    await self.highrise.send_whisper(user.id, f"✅ تم إضافة الاختفاء رقم {num} بمعرّف: {item_id}")
                except Exception as e:
                    print(f"Error adding invisible: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة الاختفاء")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # ==================== أمر اضف قبعة (مبكر لتجنب مشاكل lowercase) ====================
        if original_message.startswith("اضف قبعة ") or original_message.startswith("اضف القبعة ") or original_message.startswith("اضف قبعه ") or original_message.startswith("اضف القبعه "):
            if await self.is_user_allowed(user):
                try:
                    for pfx in ["اضف القبعة ", "اضف قبعة ", "اضف القبعه ", "اضف قبعه "]:
                        if original_message.startswith(pfx):
                            parts = original_message.replace(pfx, "").strip().split()
                            break
                    if len(parts) == 2 and parts[0].isdigit():
                        num, hat_id = parts[0], parts[1]
                    elif len(parts) == 2 and parts[1].isdigit():
                        hat_id, num = parts[0], parts[1]
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف قبعة 5 hat-n_xxx")
                        return
                    self.hat_list[num] = hat_id
                    self.save_hat_list()
                    await self.highrise.send_whisper(user.id, f"✅ تم إضافة القبعة رقم {num} بمعرّف: {hat_id}")
                except Exception as e:
                    print(f"Error adding hat: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة القبعة")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # ==================== أمر اضف تيشيرت (مبكر لتجنب مشاكل lowercase) ====================
        if original_message.startswith("اضف تيشيرت ") or original_message.startswith("اضف التيشيرت "):
            if await self.is_user_allowed(user):
                try:
                    prefix = "اضف التيشيرت " if original_message.startswith("اضف التيشيرت ") else "اضف تيشيرت "
                    parts = original_message.replace(prefix, "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num, shirt_id = parts[0], parts[1]
                    elif len(parts) == 2 and parts[1].isdigit():
                        shirt_id, num = parts[0], parts[1]
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف تيشيرت 5 shirt-n_xxx")
                        return
                    self.tshirts_list[num] = shirt_id
                    self.save_tshirts_list()
                    await self.highrise.send_whisper(user.id, f"✅ تم إضافة التيشيرت رقم {num} بمعرّف: {shirt_id}")
                except Exception as e:
                    print(f"Error adding tshirt: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة التيشيرت")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # ==================== أمر اضف شعر (مبكر لتجنب مشاكل lowercase) ====================
        if original_message.startswith("اضف شعر ") or original_message.startswith("اضف الشعر "):
            if await self.is_user_allowed(user):
                try:
                    prefix = "اضف الشعر " if original_message.startswith("اضف الشعر ") else "اضف شعر "
                    parts = original_message.replace(prefix, "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num, hair_id = parts[0], parts[1]
                    elif len(parts) == 2 and parts[1].isdigit():
                        hair_id, num = parts[0], parts[1]
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف شعر 5 hair_front-n_xxx")
                        return
                    if hair_id.startswith("hair_front"):
                        front_id = hair_id
                        back_id = hair_id.replace("hair_front", "hair_back")
                    elif hair_id.startswith("hair_back"):
                        back_id = hair_id
                        front_id = hair_id.replace("hair_back", "hair_front")
                    else:
                        front_id = hair_id
                        back_id = hair_id
                    self.hair_list[num] = {"front": front_id, "back": back_id}
                    self.save_hair_list()
                    await self.highrise.send_whisper(user.id, f"✅ تم إضافة الشعر رقم {num} بمعرّف: {hair_id}")
                except Exception as e:
                    print(f"Error adding hair: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة الشعر")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # ==================== أمر عرض مخزون البوت ====================
        if original_message.lower() in ["مخزوني", "مخزون البوت", "inventory"]:
            if await self.is_user_allowed(user):
                try:
                    inventory_resp = await self.highrise.get_inventory()
                    items = inventory_resp.items
                    if not items:
                        await self.highrise.send_whisper(user.id, "📦 مخزون البوت فارغ")
                    else:
                        total = len(items)
                        lines = [f"📦 مخزون البوت ({total} قطعة):"]
                        for itm in items[:30]:
                            lines.append(f"• {itm.id}")
                        if total > 30:
                            lines.append(f"... و{total - 30} قطعة أخرى")
                        await self.highrise.send_whisper(user.id, "\n".join(lines))
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ خطأ: {str(e)[:120]}")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # ==================== أمر اضف مباشر (بدون رقم) ====================
        if original_message.startswith("اضف "):
            item_id = original_message.replace("اضف ", "").strip()
            if "-" in item_id and " " not in item_id:
                if await self.is_user_allowed(user):
                    try:
                        from highrise.models import Item as DirectItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        existing_ids = [i.id for i in current_outfit]
                        if item_id in existing_ids:
                            await self.highrise.send_whisper(user.id, f"⚠️ القطعة موجودة بالفعل في الزي:\n{item_id}")
                        else:
                            current_outfit.append(DirectItem(type="clothing", amount=1, id=item_id))
                            await self.highrise.set_outfit(outfit=current_outfit)
                            await self.highrise.send_whisper(user.id, f"✅ تم إضافة القطعة مباشرة:\n{item_id}")
                    except Exception as e:
                        print(f"Error adding item directly: {e}")
                        await self.highrise.send_whisper(user.id, "❌ حدث خطأ، تأكد من صحة المعرف")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                return

        # ==================== أمر اخلع الكل ====================
        if original_message in ["اخلع الكل", "خلع الكل", "اخلع كل شيء"]:
            if await self.is_user_allowed(user):
                try:
                    my_outfit_response = await self.highrise.get_my_outfit()
                    current_outfit = list(my_outfit_response.outfit)
                    # الاحتفاظ بقطع الجسم الأساسية فقط (لون البشرة وما شابه)
                    body_items = [item for item in current_outfit if item.id.startswith("body-")]
                    await self.highrise.set_outfit(outfit=body_items)
                    removed = len(current_outfit) - len(body_items)
                    await self.highrise.send_whisper(user.id, f"✅ تم خلع {removed} قطعة بنجاح")
                except Exception as e:
                    print(f"Error removing all items: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء خلع الملابس")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # ==================== أمر اخلع (مبكر لتجنب الـ return المبكرة) ====================
        if original_message.startswith("اخلع "):
            if await self.is_user_allowed(user):
                try:
                    item_id = original_message.replace("اخلع ", "").strip()
                    from highrise.models import Item as RemoveItem
                    my_outfit_response = await self.highrise.get_my_outfit()
                    current_outfit = list(my_outfit_response.outfit)
                    new_outfit = [item for item in current_outfit if item.id != item_id]
                    if len(new_outfit) == len(current_outfit):
                        ids = "\n".join(f"• {i.id}" for i in current_outfit)
                        await self.highrise.send_whisper(user.id, f"❌ لم يُعثر على المعرف:\n{item_id}\n\n📋 الزي الحالي:\n{ids}")
                    else:
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم خلع القطعة:\n{item_id}")
                except Exception as e:
                    print(f"Error removing item: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء خلع القطعة")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # ==================== أوامر تدوير الأحذية ====================
        # أمر تغيير الحذاء بالرقم من shoes_list.json
        if original_message.lower() == "تغيير الحذاء" or original_message.lower().startswith("تغيير الحذاء "):
            if user.username.lower() in [owner.lower() for owner in self.owners] or user.username in self.admins:
                if not self.shoes_list:
                    await self.highrise.send_whisper(user.id, "⚠️ قائمة الأحذية فارغة. استخدم: اضف حذاء 1 shoes-n_xxx")
                    return

                parts = original_message.strip().split()
                if len(parts) >= 3 and parts[2].isdigit():
                    num = parts[2]
                    if num in self.shoes_list:
                        shoe_id = self.shoes_list[num]
                    else:
                        available = ", ".join(sorted(self.shoes_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available}")
                        return
                elif len(parts) == 2 and parts[1].isdigit():
                    num = parts[1]
                    if num in self.shoes_list:
                        shoe_id = self.shoes_list[num]
                    else:
                        available = ", ".join(sorted(self.shoes_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available}")
                        return
                else:
                    await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: تغيير الحذاء 5")
                    return

                if "&" in shoe_id:
                    shoe_id = shoe_id.split("&")[0].strip()

                display_name = shoe_id.replace("shoes-n_", "").replace("shoes-", "").replace("-", " ").replace("_", " ")
                await self.highrise.chat(f"👟 Shoe #{num}\n📋 {display_name}" if self.bot_lang == "en" else f"👟 الحذاء رقم {num}\n📋 {display_name}")

                async def do_shoe_change(s_id):
                    try:
                        from highrise.models import Item as HRItem
                        resp = await self.highrise.get_my_outfit()
                        new_outfit = [itm for itm in resp.outfit if not (hasattr(itm, 'id') and itm.id.startswith("shoes-"))]
                        new_outfit.append(HRItem(type="clothing", amount=1, id=s_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        print(f"[SHOE] Changed to: {s_id}")
                    except Exception as e:
                        print(f"[SHOE] set_outfit failed: {e}")

                asyncio.ensure_future(do_shoe_change(shoe_id))
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر للمالك والمشرفين فقط")
            return

        # أمر إضافة حذاء للقائمة بالرقم
        if original_message.startswith("اضف حذاء "):
            if user.username.lower() in [owner.lower() for owner in self.owners] or user.username in self.admins:
                parts = original_message.replace("اضف حذاء ", "").strip().split()
                if len(parts) == 2:
                    if parts[0].isdigit():
                        num, shoe_id = parts[0], parts[1]
                    elif parts[1].isdigit():
                        shoe_id, num = parts[0], parts[1]
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف حذاء 5 shoes-n_xxx")
                        return
                    self.shoes_list[num] = shoe_id
                    self.save_shoes_list()
                    await self.highrise.send_whisper(user.id, f"✅ تم إضافة الحذاء رقم {num} بمعرّف: {shoe_id}")
                else:
                    await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف حذاء 5 shoes-n_xxx")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر للمالك والمشرفين فقط")
            return

        # أمر حذف حذاء من القائمة بالرقم
        if original_message.startswith("احذف حذاء "):
            if user.username.lower() in [owner.lower() for owner in self.owners] or user.username in self.admins:
                num = original_message.replace("احذف حذاء ", "").strip()
                if num in self.shoes_list:
                    del self.shoes_list[num]
                    self.save_shoes_list()
                    await self.highrise.send_whisper(user.id, f"✅ تم حذف الحذاء رقم {num} من القائمة")
                else:
                    await self.highrise.send_whisper(user.id, f"⚠️ لا يوجد حذاء برقم {num}")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر للمالك والمشرفين فقط")
            return

        # أمر عرض قائمة الأحذية
        if original_message.lower() == "قائمة الأحذية":
            if user.username.lower() in [owner.lower() for owner in self.owners] or user.username in self.admins:
                if self.shoes_list:
                    total = len(self.shoes_list)
                    msg = f"👟 قائمة الأحذية ({total}):\n"
                    for num in sorted(self.shoes_list.keys(), key=lambda x: int(x)):
                        s_id = self.shoes_list[num]
                        name = s_id.replace("shoes-n_", "").replace("shoes-", "").replace("-", " ").replace("_", " ")[:25]
                        msg += f"{num}. {name}\n"
                    await self.highrise.chat(msg.strip())
                else:
                    await self.highrise.chat("👟 Shoe list is empty. Use: اضف حذاء 1 shoes-n_xxx" if self.bot_lang == "en" else "👟 قائمة الأحذية فارغة. استخدم: اضف حذاء 1 shoes-n_xxx")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر للمالك والمشرفين فقط")
            return

        # أمر تحميل أحذية المخزون تلقائياً
        if original_message.lower() == "تحميل أحذيتي":
            if user.username.lower() in [owner.lower() for owner in self.owners] or user.username in self.admins:
                try:
                    inventory_resp = await self.highrise.get_inventory()
                    inv_shoes = [itm.id for itm in inventory_resp.items if hasattr(itm, 'id') and itm.id.startswith("shoes-")]
                    free_shoes = [
                        "shoes-n_whitedans","shoes-n_starteritems2019flatswhite",
                        "shoes-n_starteritems2019flatspink","shoes-n_starteritems2019flatsblack",
                        "shoes-n_starteritems2018conversewhite","shoes-n_room32019socksneakersgrey",
                        "shoes-n_room32019socksneakersblack","shoes-n_room22019socks",
                        "shoes-n_room22019kneehighsblack","shoes-n_room12019sneakerspink",
                        "shoes-n_room12019sneakersblack","shoes-n_room12019hightopsred",
                        "shoes-n_room12019hightopsblack","shoes-n_room12019bootsbrown",
                        "shoes-n_room12019bootsblack","shoes-n_platformsneakerblack",
                        "shoes-n_drstompsbootswhite","shoes-n_converse_black","shoes-n_converse"
                    ]
                    all_shoes = list(dict.fromkeys(inv_shoes + free_shoes))
                    new_dict = {str(i+1): s for i, s in enumerate(all_shoes)}
                    self.shoes_list = new_dict
                    self.save_shoes_list()
                    await self.highrise.send_whisper(user.id, f"✅ تم تحميل {len(all_shoes)} حذاء\nاستخدم: تغيير الحذاء [رقم]")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ خطأ في تحميل المخزون: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر للمالك والمشرفين فقط")
            return

        # أمر عرض حذاء البوت الحالي (المعرف الحقيقي)
        if original_message.lower() == "حذاء البوت":
            if user.username.lower() in [owner.lower() for owner in self.owners] or user.username in self.admins:
                try:
                    resp = await self.highrise.get_my_outfit()
                    shoes_found = [itm.id for itm in resp.outfit if hasattr(itm, 'id') and itm.id.startswith("shoes-")]
                    if shoes_found:
                        await self.highrise.send_whisper(user.id, f"👟 حذاء البوت الحالي:\n{shoes_found[0]}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ البوت لا يرتدي حذاءً الآن")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ خطأ: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر للمالك والمشرفين فقط")
            return
        # ================================================================

        # Handle حمايه command - protect/unprotect owner
        if original_message.lower() == "حمايه":
            if user.username.lower() in [owner.lower() for owner in self.owners]:
                self.owner_protected = not self.owner_protected
                status = "مفعلة ✅" if self.owner_protected else "معطلة ❌"
                await self.highrise.chat(f"🛡️ Owner protection is now {status}" if self.bot_lang == "en" else f"🛡️ حماية المالك الآن {status}")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك فقط")
            return

        # أمر حمايه @username - لإضافة/إزالة حماية مستخدم (للمالك فقط)
        if original_message.startswith("حمايه @") or original_message.startswith("حماية @"):
            if user.username in self.owners:
                try:
                    target_username = original_message.split("@", 1)[1].strip()
                    is_already_protected = any(p.lower() == target_username.lower() for p in self.special_protected)
                    if is_already_protected:
                        # إزالة الحماية
                        self.special_protected = [p for p in self.special_protected if p.lower() != target_username.lower()]
                        self.save_special_protected()
                        await self.highrise.chat(f"🔓 Protection removed from @{target_username}" if self.bot_lang == "en" else f"🔓 تم إزالة الحماية عن @{target_username}")
                    else:
                        # إضافة الحماية
                        self.special_protected.append(target_username)
                        self.save_special_protected()
                        await self.highrise.chat(f"🛡️ Protection activated for @{target_username}" if self.bot_lang == "en" else f"🛡️ تم تفعيل الحماية على @{target_username}")
                except Exception as e:
                    print(f"Error in حمايه command: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تنفيذ الأمر")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك فقط")
            return
        
        # Handle افتح command directly
        if original_message.lower() == "افتح":
            # فحص الصلاحيات: مالك البوت أو مالك الغرفة أو مشرف Highrise أو مشرف البوت
            try:
                user_privileges = await self.highrise.get_room_privilege(user.id)
            except Exception:
                user_privileges = None
            is_bot_owner = user.username in self.owners
            is_bot_admin = any(admin.lower() == user.username.lower() for admin in self.admins)
            is_room_moderator = user_privileges.moderator if user_privileges else False
            is_room_owner = hasattr(self, 'room_owner_id') and user.id == self.room_owner_id

            if not (is_bot_owner or is_bot_admin or is_room_moderator or is_room_owner):
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                return

            try:
                # محاولة طلب المايك من جميع المستخدمين في الروم
                room_users = await self.highrise.get_room_users()
                success_count = 0
                error_count = 0
                
                for room_user, position in room_users.content:
                    try:
                        await self.highrise.add_user_to_voice(room_user.id)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Voice request to {room_user.username}: {e}")
                
                await self.highrise.chat(f"🎙️ Live stream activated by @{user.username}" if self.bot_lang == "en" else f"🎙️ تم تفعيل البث المباشر بواسطة @{user.username}")
                await self.highrise.chat(f"✨ Mic requests sent ({success_count} succeeded). Please accept in the popup!" if self.bot_lang == "en" else f"✨ تم إرسال طلب المايك للمستخدمين ({success_count} نجح). يرجى قبول الطلب في النافذة المنبثقة!")
            except Exception as e:
                print(f"Error in افتح command: {e}")
                await self.highrise.chat(f"❌ An error occurred: {str(e)}" if self.bot_lang == "en" else f"❌ حدث خطأ: {str(e)}")
            return

        # ==================== أمر لايف ====================
        if original_message.strip() == "لايف" and await self.is_user_allowed(user):
            try:
                result = await self.highrise.buy_voice_time("bot_wallet_only")
                if result in ("success", "only_token_bought"):
                    await self.highrise.chat("🔴 Live stream activated!" if self.bot_lang == "en" else "🔴 تم تفعيل البث المباشر!")
                elif result == "insufficient_funds":
                    await self.highrise.chat("❌ Insufficient bot balance to activate live." if self.bot_lang == "en" else "❌ رصيد البوت غير كافٍ لتفعيل اللايف.")
                else:
                    await self.highrise.chat(f"⚠️ Result: {result}" if self.bot_lang == "en" else f"⚠️ النتيجة: {result}")
            except Exception as e:
                print(f"Error in لايف command: {e}")
                await self.highrise.chat(f"❌ An error occurred: {str(e)}" if self.bot_lang == "en" else f"❌ حدث خطأ: {str(e)}")
            return

        if original_message.strip() in ["وقف لايف", "ايقاف لايف", "إيقاف لايف"] and await self.is_user_allowed(user):
            try:
                await self.highrise.remove_user_from_voice(self.bot_id)
                await self.highrise.chat("⭕ Live stream stopped." if self.bot_lang == "en" else "⭕ تم إيقاف البث المباشر.")
            except Exception as e:
                print(f"Error in وقف لايف command: {e}")
                await self.highrise.chat(f"❌ An error occurred: {str(e)}" if self.bot_lang == "en" else f"❌ حدث خطأ: {str(e)}")
            return

        if original_message.startswith("ترجمة "):
            text_to_translate = original_message.split("ترجمة ", 1)[1].strip()
            if text_to_translate:
                try:
                    # اكتشاف اللغة تلقائياً
                    detected = self.translator.detect(text_to_translate)
                    # إذا كانت اللغة المكتشفة هي العربية، نترجم للإنجليزية، والعكس صحيح
                    dest_lang = 'en' if detected.lang == 'ar' else 'ar'
                    
                    translation = self.translator.translate(text_to_translate, dest=dest_lang)
                    
                    lang_name = "الإنجليزية" if dest_lang == 'en' else "العربية"
                    await self.highrise.chat(f"🌐 Translation ({lang_name}): {translation.text}" if self.bot_lang == "en" else f"🌐 الترجمة ({lang_name}): {translation.text}")
                except Exception as e:
                    print(f"Translation error: {e}")
                    await self.highrise.chat("❌ Sorry, a translation error occurred." if self.bot_lang == "en" else "❌ عذراً، حدث خطأ أثناء الترجمة.")
            return

        # Priority command handling - these commands must execute first and exclusively
        priority_commands = [
            "!remove", "!removevip", "!delvip", "!add", "!addvip", "!addswm", "!removeswm", "وداع @", "حذف وداع @",
            "!adminlist", "adminlist", "!mod", "!delmod", "!desig", "!deldesig", "اطفاء", "افتح", "قفل الغرفة", "افتح الغرفة", "قفل الدردشة", "فتح الدردشة", "كتم الكل", "الغاء كتم الكل", "قول", "الكل vip", "الاجرائات", "!join", "ارجع",
            "حفظ البس", "البس", "حذف البس", "احذف لبس", "نسخ ملابس", "البسات", "لبسات"
        ]
        
        # Check for priority commands first
        for priority_cmd in priority_commands:
            if original_message.lower().startswith(priority_cmd.lower()):
                # الكل vip command handler
                if original_message.lower() == "الكل vip":
                    if await self.is_user_allowed(user):
                        try:
                            vip_pos = Position(x=12.50, y=0, z=24.0, facing='FrontRight')
                            room_users = await self.highrise.get_room_users()
                            for target_user, position in room_users.content:
                                try:
                                    await self.highrise.teleport(target_user.id, vip_pos)
                                except Exception as e:
                                    print(f"Error teleporting {target_user.username}: {e}")
                            await self.highrise.chat(f"🚀 Everyone moved to VIP zone by @{user.username}" if self.bot_lang == "en" else f"🚀 تم نقل الجميع إلى منطقة VIP بواسطة @{user.username}")
                        except Exception as e:
                            print(f"Error in teleport all to vip: {e}")
                            await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء النقل")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                # أمر البسات / لبسات لعرض عدد اللبسات المحفوظة
                if original_message.strip() in ("البسات", "لبسات"):
                    count = len(self.saved_outfits)
                    if count == 0:
                        await self.highrise.send_whisper(user.id, "📭 لا توجد لبسات محفوظة بعد.")
                    else:
                        sorted_slots = sorted(self.saved_outfits.keys(), key=lambda x: int(x) if x.isdigit() else 0)
                        await self.highrise.send_whisper(user.id, f"👗 عدد اللبسات المحفوظة: {count}")
                        chunk_size = 20
                        for i in range(0, len(sorted_slots), chunk_size):
                            chunk = sorted_slots[i:i + chunk_size]
                            await self.highrise.send_whisper(user.id, " ".join(chunk))
                    return

                # نسخ ملابس جميع المستخدمين في الغرفة
                if original_message.strip() == "نسخ ملابس":
                    if await self.is_user_allowed(user):
                        try:
                            await self.highrise.send_whisper(user.id, "⏳ جاري نسخ ملابس المستخدمين في الغرفة...")
                            saved = await self.copy_outfits_from_room()
                            if saved > 0:
                                await self.highrise.send_whisper(user.id, f"✅ تم حفظ {saved} لبسة بنجاح! استخدم 'البس [رقم]' لارتدائها.")
                            else:
                                await self.highrise.send_whisper(user.id, "❌ لم يتم العثور على ملابس لحفظها.")
                        except Exception as e:
                            print(f"Error in نسخ ملابس command: {e}")
                            await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء نسخ الملابس")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                    return

                # حفظ البس {n}
                if original_message.startswith("حفظ البس "):
                    if await self.is_user_allowed(user):
                        parts = original_message.strip().split()
                        if len(parts) == 3 and parts[2].isdigit():
                            slot = parts[2]
                            try:
                                outfit_resp = await self.highrise.get_my_outfit()
                                items_data = [{"id": item.id, "type": item.type, "amount": item.amount, "active_palette": item.active_palette} for item in outfit_resp.outfit]
                                self.saved_outfits[slot] = items_data
                                self.save_saved_outfits()
                                await self.highrise.send_whisper(user.id, f"✅ تم حفظ اللبسة رقم {slot} بنجاح!")
                            except Exception as e:
                                print(f"Error saving outfit {slot}: {e}")
                                await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حفظ اللبسة")
                        else:
                            await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: حفظ البس 1")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                # البس {n}
                if original_message.startswith("البس "):
                    if await self.is_user_allowed(user):
                        parts = original_message.strip().split()
                        if len(parts) == 2 and parts[1].isdigit():
                            slot = parts[1]
                            if slot in self.saved_outfits:
                                try:
                                    from highrise.models import Item as OutfitItem
                                    items_data = self.saved_outfits[slot]
                                    outfit_items = [OutfitItem(id=d["id"], type=d["type"], amount=d["amount"], active_palette=d.get("active_palette")) for d in items_data]
                                    await self.highrise.set_outfit(outfit_items)
                                    await self.highrise.send_whisper(user.id, f"✅ تم ارتداء اللبسة رقم {slot}!")
                                except Exception as e:
                                    print(f"Error equipping outfit {slot}: {e}")
                                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء ارتداء اللبسة")
                            else:
                                await self.highrise.send_whisper(user.id, f"❌ لا توجد لبسة محفوظة برقم {slot}. استخدم 'حفظ البس {slot}' أولاً")
                        else:
                            await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: البس 1")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                # حذف البس {n}
                if original_message.startswith("حذف البس "):
                    if await self.is_user_allowed(user):
                        parts = original_message.strip().split()
                        if len(parts) == 3 and parts[2].isdigit():
                            slot = parts[2]
                            if slot in self.saved_outfits:
                                del self.saved_outfits[slot]
                                self.save_saved_outfits()
                                await self.highrise.send_whisper(user.id, f"✅ تم حذف اللبسة رقم {slot} بنجاح!")
                            else:
                                await self.highrise.send_whisper(user.id, f"❌ لا توجد لبسة محفوظة برقم {slot}")
                        else:
                            await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: حذف البس 1")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                # احذف لبس {n}
                if original_message.startswith("احذف لبس "):
                    if await self.is_user_allowed(user):
                        slot = original_message.replace("احذف لبس ", "").strip()
                        if slot.isdigit():
                            if slot in self.saved_outfits:
                                del self.saved_outfits[slot]
                                self.save_saved_outfits()
                                await self.highrise.send_whisper(user.id, f"✅ تم حذف اللبسة رقم {slot} بنجاح!")
                            else:
                                await self.highrise.send_whisper(user.id, f"❌ لا توجد لبسة محفوظة برقم {slot}")
                        else:
                            await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: احذف لبس 8")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                # Add special farewell command
                if original_message.startswith("وداع @"):
                    if await self.is_user_allowed(user):
                        try:
                            parts = original_message.split(" ", 2)
                            if len(parts) >= 3:
                                target_user = parts[1].replace("@", "").strip()
                                farewell_text = parts[2].strip()
                                self.special_farewells[target_user] = farewell_text
                                self.save_special_farewells()
                                await self.highrise.chat(f"✅ Special farewell added for @{target_user} successfully." if self.bot_lang == "en" else f"✅ تم إضافة وداع خاص لـ @{target_user} بنجاح.")
                            else:
                                await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: وداع @username نص الوداع")
                        except Exception as e:
                            print(f"Error adding special farewell: {e}")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                # Remove special farewell command
                if original_message.startswith("حذف وداع @"):
                    if await self.is_user_allowed(user):
                        target_user = original_message.replace("حذف وداع @", "").strip()
                        if target_user in self.special_farewells:
                            del self.special_farewells[target_user]
                            self.save_special_farewells()
                            await self.highrise.chat(f"✅ Special farewell deleted for @{target_user}." if self.bot_lang == "en" else f"✅ تم حذف الوداع الخاص لـ @{target_user}.")
                        else:
                            # Search case-insensitive
                            found = False
                            for saved_user in list(self.special_farewells.keys()):
                                if saved_user.lower() == target_user.lower():
                                    del self.special_farewells[saved_user]
                                    self.save_special_farewells()
                                    await self.highrise.chat(f"✅ Special farewell deleted for @{target_user}." if self.bot_lang == "en" else f"✅ تم حذف الوداع الخاص لـ @{target_user}.")
                                    found = True
                                    break
                            if not found:
                                await self.highrise.send_whisper(user.id, f"❌ لا يوجد وداع خاص مسجل للمستخدم @{target_user}")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                # Say command handler
                if original_message.lower().startswith("قول"):
                    if command_executed: continue
                    text_to_say = original_message[3:].strip()
                    if text_to_say:
                        await self.highrise.chat(text_to_say)
                    command_executed = True
                    return

                # Restart command handler
                if original_message.lower() == "اعادة تشغيل":
                    if await self.is_user_allowed(user):
                        await self.highrise.chat(f"🔄 Restarting bot by @{user.username}... Please wait 5 seconds" if self.bot_lang == "en" else f"🔄 جاري إعادة تشغيل البوت بواسطة @{user.username}... يرجى الانتظار 5 ثوانٍ")
                        # إيقاف المهام الخلفية أولاً
                        if hasattr(self, 'loop_task') and self.loop_task:
                            self.loop_task.cancel()
                        if hasattr(self, 'announcement_task') and self.announcement_task:
                            self.announcement_task.cancel()
                        
                        await asyncio.sleep(2)
                        # الخروج لضمان إعادة التشغيل من قبل ريبليت
                        os._exit(0)
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                # Shutdown command handler
                if original_message.lower() == "اطفاء":
                    if user.username in self.owners:
                        await self.highrise.chat(f"⚠️ Bot is being shut down by @{user.username}..." if self.bot_lang == "en" else f"⚠️ يتم الآن إطفاء البوت بواسطة @{user.username}...")
                        await asyncio.sleep(1)
                        os._exit(0)
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك فقط")
                    return

                if original_message.lower().startswith("كتم الكل"):
                    if await self.is_user_allowed(user):
                        self.mute_all_active = True
                        try:
                            # البحث عن الرقم في الرسالة (مثلاً: كتم الكل 24)
                            parts = original_message.split()
                            duration_hours = "غير محددة"
                            
                            # محاولة استخراج الرقم إذا وجد
                            for part in parts:
                                if part.isdigit():
                                    duration_hours = part
                                    break

                            room_users = await self.highrise.get_room_users()
                            for target_user, position in room_users.content:
                                if target_user.username not in self.owners:
                                    try:
                                        await self.highrise.remove_user_from_voice(target_user.id)
                                    except Exception as e:
                                        print(f"Error muting user {target_user.username}: {e}")
                            
                            msg = f"🔇 تم كتم صوت الجميع بواسطة @{user.username}"
                            if duration_hours != "غير محددة":
                                msg += f" لمدة {duration_hours} ساعة"
                            msg += " (باستثناء الملاك)"
                            
                            await self.highrise.chat(msg)
                        except Exception as e:
                            print(f"Error in mute all: {e}")
                            await self.highrise.send_whisper(user.id, f"❌ حدث خطأ أثناء الكتم: {str(e)}")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                if original_message.lower() == "الغاء كتم الكل":
                    if await self.is_user_allowed(user):
                        self.mute_all_active = False
                        try:
                            room_users = await self.highrise.get_room_users()
                            for target_user, position in room_users.content:
                                try:
                                    await self.highrise.add_user_to_voice(target_user.id)
                                except Exception as e:
                                    print(f"Error unmuting user {target_user.username}: {e}")
                            await self.highrise.chat(f"🔊 All users unmuted by @{user.username}. You can speak now." if self.bot_lang == "en" else f"🔊 تم إلغاء كتم صوت الجميع بواسطة @{user.username}. يمكنكم التحدث الآن.")
                        except Exception as e:
                            print(f"Error in unmute all: {e}")
                            await self.highrise.send_whisper(user.id, f"❌ حدث خطأ أثناء إلغاء الكتم: {str(e)}")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                if original_message.lower() == "قفل الغرفة":
                    if await self.is_user_allowed(user):
                        self.room_locked = True
                        await self.highrise.chat(f"🔒 Room locked by @{user.username}. No one can enter now." if self.bot_lang == "en" else f"🔒 تم قفل الغرفة بواسطة @{user.username}. لن يتمكن أحد من الدخول الآن.")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                if original_message.lower() == "افتح الغرفة":
                    if await self.is_user_allowed(user):
                        self.room_locked = False
                        await self.highrise.chat(f"🔓 Room unlocked by @{user.username}. Everyone is welcome now." if self.bot_lang == "en" else f"🔓 تم فتح الغرفة بواسطة @{user.username}. الجميع مرحب بهم الآن.")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                if original_message.lower() == "قفل الدردشة":
                    if await self.is_user_allowed(user):
                        self.chat_locked = True
                        await self.highrise.chat(f"🔒 Chat locked by @{user.username}. No one can write now." if self.bot_lang == "en" else f"🔒 تم قفل الدردشة بواسطة @{user.username}. لا يمكن لأحد الكتابة الآن.")
                        try:
                            room_users = await self.highrise.get_room_users()
                            for target_user, _ in room_users.content:
                                if target_user.id == self.bot_id:
                                    continue
                                if target_user.username in self.owners or target_user.username in self.admins:
                                    continue
                                try:
                                    await self.highrise.moderate_room(target_user.id, "mute", 3600)
                                except Exception as e:
                                    print(f"[قفل الدردشة] خطأ في كتم {target_user.username}: {e}")
                        except Exception as e:
                            print(f"[قفل الدردشة] خطأ في جلب المستخدمين: {e}")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                if original_message.lower() == "فتح الدردشة":
                    if await self.is_user_allowed(user):
                        self.chat_locked = False
                        await self.highrise.chat(f"🔓 Chat unlocked by @{user.username}. Everyone can write now." if self.bot_lang == "en" else f"🔓 تم فتح الدردشة بواسطة @{user.username}. يمكن للجميع الكتابة الآن.")
                        try:
                            room_users = await self.highrise.get_room_users()
                            for target_user, _ in room_users.content:
                                if target_user.id == self.bot_id:
                                    continue
                                if target_user.username in self.owners or target_user.username in self.admins:
                                    continue
                                try:
                                    await self.highrise.moderate_room(target_user.id, "mute", 1)
                                except Exception as e:
                                    print(f"[فتح الدردشة] خطأ في رفع كتم {target_user.username}: {e}")
                        except Exception as e:
                            print(f"[فتح الدردشة] خطأ في جلب المستخدمين: {e}")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                if original_message.lower() == "الاجرائات":
                    if await self.is_user_allowed(user):
                        if not self.admin_log:
                            await self.highrise.chat((f"📋 No admin actions recorded yet." if self.bot_lang == "en" else f"📋 لا توجد إجراءات إدارية مسجلة حتى الآن."))
                        else:
                            lines = ["📋 آخر الإجراءات الإدارية:"]
                            for entry in reversed(self.admin_log[-10:]):
                                lines.append(f"• [{entry['time']}] {entry['action']} @{entry['target']} بواسطة @{entry['by']}")
                            await self.highrise.chat("\n".join(lines))
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                if original_message.lower().startswith("!join"):
                    if await self.is_user_allowed(user):
                        parts = original_message.split()
                        if len(parts) < 2:
                            await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: !join [room_id]")
                        else:
                            new_room_id = parts[1].strip()
                            await self.highrise.chat(f"⏳ Moving to room: {new_room_id}\nPermissions will be checked on entry..." if self.bot_lang == "en" else f"⏳ جاري الانتقال للغرفة: {new_room_id}\nسيتم التحقق من صلاحيات (مشرف + مصمم) عند الدخول...")
                            RunBot.previous_room_id = RunBot.room_id
                            RunBot.room_id = new_room_id
                            raise Exception(f"[!join] الانتقال لغرفة جديدة: {new_room_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                if original_message.lower() == "ارجع":
                    if await self.is_user_allowed(user):
                        prev = RunBot.previous_room_id
                        if not prev:
                            await self.highrise.send_whisper(user.id, "ℹ️ لم يتم الانتقال لأي غرفة بعد عبر !join.")
                        elif RunBot.room_id == prev:
                            await self.highrise.send_whisper(user.id, "ℹ️ البوت موجود بالفعل في الغرفة السابقة.")
                        else:
                            await self.highrise.chat((f"🏠 Returning to previous room by @{user.username}..." if self.bot_lang == "en" else f"🏠 جاري العودة للغرفة السابقة بواسطة @{user.username}..."))
                            RunBot.room_id = prev
                            RunBot.previous_room_id = None
                            raise Exception(f"[ارجع] العودة للغرفة السابقة: {prev}")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return

                if original_message.lower() == "افتح":
                    if await self.is_user_allowed(user):
                        await self.highrise.chat(f"🎙️ Live stream activated by @{user.username}" if self.bot_lang == "en" else f"🎙️ تم تفعيل البث المباشر بواسطة @{user.username}")
                        await self.highrise.chat((f"✨ Live stream is now available for everyone. Please accept the mic request to participate." if self.bot_lang == "en" else f"✨ البث المباشر متاح للجميع الآن. يرجى قبول طلب المايك للمشاركة."))
                    else:
                        await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    command_executed = True
                    return

                command_executed = True
                break
        
        # If it's a priority command, skip all other processing and go directly to command handling
        if command_executed:
            # Skip points addition and other processing for priority commands
            pass
        else:
            # نظام التحذيرات
            if message.startswith("تحذيراته"):
                try:
                    parts = message.split()
                    target_username = ""
                    if len(parts) > 1:
                        target_username = parts[1].replace("@", "").strip()
                    else:
                        target_username = user.username
                    
                    room_users = await self.highrise.get_room_users()
                    target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                    
                    if target_user:
                        user_id = target_user.id
                        warnings_count = self.user_warnings.get(user_id, 0)
                        await self.highrise.chat((f"• User @{target_username} has {warnings_count}/3 warnings." if self.bot_lang == "en" else f"• المستخدم @{target_username} لديه {warnings_count}/3 تحذيرات."))
                    else:
                        # إذا لم يكن في الغرفة، نبحث في القاموس إذا كان المفتاح هو username (بعض الأنظمة تفعل ذلك)
                        # لكن هنا نرى أن النظام يستخدم user_id
                        await self.highrise.chat((f"• User @{target_username} is not in the room currently." if self.bot_lang == "en" else f"• المستخدم @{target_username} غير موجود في الغرفة حالياً."))
                except Exception as e:
                    print(f"Error in warnings check: {e}")
                return

            if message.startswith("تحذير @"):
                if await self.is_user_allowed(user):
                    try:
                        parts = message.split()
                        if len(parts) >= 2:
                            target_username = parts[1][1:].strip()
                            room_users = await self.highrise.get_room_users()
                            target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                            
                            if target_user:
                                if target_user.username in self.owners:
                                    await self.highrise.send_whisper(user.id, "❌ لا يمكنك تحذير الأونر")
                                    return

                                # التحقق من الصلاحيات - لا يمكن تحذير من له نفس الرتبة أو أعلى
                                is_target_admin = target_user.username in self.admins
                                is_sender_owner = user.username in self.owners
                                
                                if is_target_admin and not is_sender_owner:
                                    await self.highrise.send_whisper(user.id, "❌ لا يمكنك تحذير مشرف آخر")
                                    return

                                user_id = target_user.id
                                if user_id not in self.user_warnings:
                                    self.user_warnings[user_id] = 0
                                
                                self.user_warnings[user_id] += 1
                                current_warnings = self.user_warnings[user_id]
                                self.save_user_warnings()
                                
                                if current_warnings >= 3:
                                    await self.highrise.chat((f"🚫 @{target_username} was kicked for exceeding 3 warnings" if self.bot_lang == "en" else f"🚫 تم طرد @{target_username} لتجاوزه 3 تحذيرات"))
                                    try:
                                        # استخدام معرف المستخدم للمطرود (user_id) وتحديد الطرد (kick)
                                        # ملاحظة: في بعض إصدارات SDK يتم استخدام moderate_room_user أو moderate_room
                                        await self.highrise.moderate_room_user(user_id, "kick")
                                    except Exception as e:
                                        print(f"Error kicking user via moderate_room_user: {e}")
                                        try:
                                            # محاولة الطرد باستخدام الطريقة البديلة في حال فشل الأولى
                                            await self.highrise.moderate_room(user_id, "kick")
                                        except Exception as e2:
                                            print(f"Error kicking user via moderate_room: {e2}")
                                    
                                    # تصفير العداد بعد الطرد
                                    self.user_warnings[user_id] = 0
                                    self.save_user_warnings()
                                else:
                                    await self.highrise.chat((f"⚠️ Warning @{target_username} ({current_warnings}/3) by @{user.username}" if self.bot_lang == "en" else f"⚠️ تحذير @{target_username} ({current_warnings}/3) بواسطة @{user.username}"))
                                    self.admin_log.append({"action": f"تحذير ({current_warnings}/3)", "target": target_username, "by": user.username, "time": datetime.now().strftime("%H:%M")})
                                    if len(self.admin_log) > 20:
                                        self.admin_log.pop(0)
                            else:
                                await self.highrise.send_whisper(user.id, f"❌ المستخدم @{target_username} غير موجود")
                    except Exception as e:
                        print(f"Error in warning command: {e}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                return

            if message.startswith("ازاله تحذير @"):
                if await self.is_user_allowed(user):
                    try:
                        parts = message.split()
                        if len(parts) >= 3: # ازاله + تحذير + @username
                            target_username = parts[2][1:].strip()
                            room_users = await self.highrise.get_room_users()
                            target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                            
                            if target_user:
                                user_id = target_user.id
                                if user_id in self.user_warnings and self.user_warnings[user_id] > 0:
                                    self.user_warnings[user_id] -= 1
                                    current_warnings = self.user_warnings[user_id]
                                    self.save_user_warnings()
                                    await self.highrise.chat(f"✅ Warning removed from @{target_username}. Current: ({current_warnings}/3)" if self.bot_lang == "en" else f"✅ تم إزالة تحذير من @{target_username}. التحذيرات الحالية: ({current_warnings}/3)")
                                else:
                                    await self.highrise.send_whisper(user.id, f"ℹ️ المستخدم @{target_username} ليس لديه تحذيرات")
                            else:
                                await self.highrise.send_whisper(user.id, f"❌ المستخدم @{target_username} غير موجود")
                    except Exception as e:
                        print(f"Error in remove warning command: {e}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                return

            # فحص أمر ريست في بداية المعالجة
            if message.lower().strip() in ["ريست", "rest"]:
                user_id = user.id
                # إيقاف أي loop نشط أولاً
                if user_id in self.user_emote_loops:
                    await self.stop_emote_loop(user_id)
                    await asyncio.sleep(0.2)
                
                # بدء رقصة الجلوس للمستخدم
                await self.start_rest_emote_loop(user_id)
                return  # إنهاء المعالجة هنا

            # أمر vvip للنقل للإحداثيات (للمشرفين فقط)
            if message.startswith("vvip @"):
                if await self.is_user_allowed(user):
                    try:
                        parts = message.split()
                        if len(parts) >= 2:
                            target_username = parts[1][1:].strip()
                            room_users = await self.highrise.get_room_users()
                            target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                            
                            if target_user:
                                # إحداثيات المنطقة الافتراضية (يمكنك تعديلها هنا)
                                default_pos = Position(x=14.5, y=6.25, z=27.0) 
                                await self.highrise.teleport(target_user.id, default_pos)
                                await self.highrise.chat((f"🚀 @{target_username} moved to private zone by @{user.username}" if self.bot_lang == "en" else f"🚀 تم نقل @{target_username} إلى المنطقة الخاصة بواسطة @{user.username}"))
                            else:
                                await self.highrise.send_whisper(user.id, f"❌ المستخدم @{target_username} غير موجود في الغرفة")
                    except Exception as e:
                        print(f"Error in vvip command: {e}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                return

            # أمر vvip بدون @ (لنقل المشرف/الأونر نفسه)
            if message.strip().lower() == "vvip":
                if await self.is_user_allowed(user):
                    try:
                        vvip_pos = Position(x=14.5, y=6.25, z=27.0)
                        await self.highrise.teleport(user.id, vvip_pos)
                        await self.highrise.send_whisper(user.id, "✅ تم نقلك إلى منطقة VVIP")
                    except Exception as e:
                        print(f"Error in vvip self command: {e}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                return

            # أمر الإعلان التلقائي (للمشرفين فقط)
            if message.startswith("اعلان "):
                if await self.is_user_allowed(user):
                    new_announcement = message.replace("اعلان ", "").strip()
                    if new_announcement:
                        self.announcement_message = new_announcement
                        await self.highrise.chat(f"✅ Auto-announcement set every 2 minutes: {new_announcement}" if self.bot_lang == "en" else f"✅ تم ضبط الإعلان التلقائي كل دقيقتين: {new_announcement}")
                        # إيقاف المهمة القديمة إن وجدت وبدء واحدة جديدة
                        if self.announcement_task:
                            self.announcement_task.cancel()
                        self.announcement_task = asyncio.create_task(self.announcement_loop())
                    else:
                        await self.highrise.send_whisper(user.id, "📝 يرجى كتابة نص الإعلان بعد الكلمة")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                return

            if message.strip() == "ايقاف الاعلان":
                if await self.is_user_allowed(user):
                    self.announcement_message = ""
                    if self.announcement_task:
                        self.announcement_task.cancel()
                        self.announcement_task = None
                    await self.highrise.chat("🛑 Auto-announcements stopped" if self.bot_lang == "en" else "🛑 تم إيقاف الإعلانات التلقائية")
                return

            # أمر طرد الكل (للمالك فقط)
            if message.strip() == "طرد الكل":
                if user.username in self.owners:
                    try:
                        await self.highrise.chat("⚠️ Kicking all regular users from the room..." if self.bot_lang == "en" else "⚠️ جاري طرد جميع المستخدمين العاديين من الغرفة...")
                        room_users = await self.highrise.get_room_users()
                        kicked_count = 0
                        for target_user, position in room_users.content:
                            # عدم طرد الأونرز، الأدمن، أو البوت نفسه
                            is_owner = target_user.username in self.owners
                            is_admin = target_user.username in self.admins
                            is_bot = target_user.id == self.bot_id
                            
                            if not is_owner and not is_admin and not is_bot:
                                try:
                                    # محاولة استخدام moderate_room أولاً فهي الأكثر شيوعاً في SDK
                                    try:
                                        await self.highrise.moderate_room(target_user.id, "kick")
                                    except:
                                        # محاولة الطريقة البديلة إذا كانت موجودة
                                        if hasattr(self.highrise, 'moderate_room_user'):
                                            await self.highrise.moderate_room_user(target_user.id, "kick")
                                        else:
                                            raise Exception("No moderation method found")
                                            
                                    kicked_count += 1
                                    await asyncio.sleep(0.5) 
                                except Exception as e:
                                    print(f"Error kicking {target_user.username}: {e}")
                        
                        await self.highrise.chat(f"✅ Done. {kicked_count} user(s) kicked." if self.bot_lang == "en" else f"✅ تمت العملية. تم طرد {kicked_count} مستخدم.")
                    except Exception as e:
                        print(f"Error in kick all command: {e}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك فقط")
                return

            # أمر حفظ أي مكان باسم مخصص (للمشرفين والملاك)
            if message.startswith("حفظ مكان "):
                if await self.is_user_allowed(user):
                    try:
                        location_name = message.replace("حفظ مكان ", "").strip()
                        if not location_name:
                            await self.highrise.send_whisper(user.id, "📝 يرجى كتابة اسم للمكان، مثال: حفظ مكان المايك")
                            return

                        room_users = await self.highrise.get_room_users()
                        user_pos = next((p for u, p in room_users.content if u.id == user.id), None)
                        
                        if user_pos and isinstance(user_pos, Position):
                            self.teleport_locations[location_name] = user_pos
                            self.save_teleport_locations()
                            await self.highrise.chat(f"✅ Location '{location_name}' saved successfully @{user.username}" if self.bot_lang == "en" else f"✅ تم حفظ موقع '{location_name}' بنجاح @{user.username}")
                        else:
                            await self.highrise.send_whisper(user.id, "❌ تعذر تحديد موقعك الحالي")
                    except Exception as e:
                        print(f"Error saving location: {e}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                return

            # أمر حفظ [اسم] لحفظ موقع المستخدم الحالي (للمشرفين والملاك)
            if original_message.startswith("حفظ ") and not original_message.startswith("حفظ مكان"):
                if await self.is_user_allowed(user):
                    try:
                        location_name = original_message[4:].strip()
                        if not location_name:
                            await self.highrise.send_whisper(user.id, "📝 يرجى كتابة اسم للمكان، مثال: حفظ لورد")
                            return

                        room_users = await self.highrise.get_room_users()
                        user_pos = next((p for u, p in room_users.content if u.id == user.id), None)

                        if user_pos and isinstance(user_pos, Position):
                            self.teleport_locations[location_name] = user_pos
                            self.save_teleport_locations()
                            await self.highrise.chat(f"📍 Location '{location_name}' saved! @{user.username}" if self.bot_lang == "en" else f"📍 تم حفظ مكان '{location_name}' بنجاح! @{user.username}")
                        else:
                            await self.highrise.send_whisper(user.id, "❌ تعذر تحديد موقعك الحالي")
                    except Exception as e:
                        print(f"Error in حفظ command: {e}")
                        await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حفظ المكان")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                return

            # أمر حذف [اسم] لحذف موقع محفوظ (للمشرفين والملاك)
            if original_message.startswith("حذف ") and not original_message.startswith("حذف قائمه"):
                if await self.is_user_allowed(user):
                    try:
                        location_name = original_message[4:].strip()
                        if not location_name:
                            await self.highrise.send_whisper(user.id, "📝 يرجى كتابة اسم المكان، مثال: حذف لورد")
                            return
                        if location_name in self.teleport_locations:
                            del self.teleport_locations[location_name]
                            self.save_teleport_locations()
                            await self.highrise.chat(f"🗑️ Location '{location_name}' deleted! @{user.username}" if self.bot_lang == "en" else f"🗑️ تم حذف مكان '{location_name}' بنجاح! @{user.username}")
                        else:
                            if self.teleport_locations:
                                available = "، ".join(self.teleport_locations.keys())
                                await self.highrise.send_whisper(user.id, f"❌ المكان '{location_name}' غير موجود.\n📋 المواقع المتاحة: {available}")
                            else:
                                await self.highrise.send_whisper(user.id, "❌ لا توجد مواقع محفوظة بعد.")
                    except Exception as e:
                        print(f"Error in حذف command: {e}")
                        await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف المكان")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                return

            # أمر اذهب [اسم] للانتقال لموقع محفوظ (لجميع المستخدمين)
            if original_message.startswith("اذهب "):
                try:
                    location_name = original_message[5:].strip()
                    if not location_name:
                        await self.highrise.send_whisper(user.id, "📝 يرجى كتابة اسم المكان، مثال: اذهب لورد")
                        return

                    if location_name in self.teleport_locations:
                        target_pos = self.teleport_locations[location_name]
                        await self.highrise.teleport(user.id, target_pos)
                        await self.highrise.send_whisper(user.id, f"✈️ تم نقلك إلى '{location_name}'")
                    else:
                        if self.teleport_locations:
                            available = "، ".join(self.teleport_locations.keys())
                            await self.highrise.send_whisper(user.id, f"❌ المكان '{location_name}' غير موجود.\n📋 المواقع المتاحة: {available}")
                        else:
                            await self.highrise.send_whisper(user.id, "❌ لا توجد مواقع محفوظة بعد.")
                except Exception as e:
                    print(f"Error in اذهب command: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء الانتقال")
                return

            # ==================== اون الكل (للأدمن والأونر فقط) ====================
            # اون الكل          ← ينقل الجميع لموقع البوت الحالي
            # اون الكل [مكان]   ← ينقل الجميع لمكان محفوظ
            if message.strip() == "اون الكل" or original_message.startswith("اون الكل "):
                if await self.is_user_allowed(user):
                    try:
                        loc_part = original_message.strip()[8:].strip()  # ما بعد "اون الكل"
                        room_users = await self.highrise.get_room_users()

                        # تحديد موقع الهدف
                        if loc_part and loc_part in self.teleport_locations:
                            target_pos = self.teleport_locations[loc_part]
                        elif loc_part:
                            available = "، ".join(self.teleport_locations.keys()) if self.teleport_locations else "لا توجد مواقع"
                            await self.highrise.send_whisper(user.id, f"❌ المكان '{loc_part}' غير موجود.\n📋 المواقع: {available}")
                            return
                        else:
                            # موقع البوت الحالي
                            target_pos = next((p for u, p in room_users.content if u.id == self.bot_id), None)
                            if not target_pos or not hasattr(target_pos, 'x'):
                                target_pos = Position(5.0, 0.0, 5.0, "FrontRight")

                        count = 0
                        for u, _ in room_users.content:
                            if u.id == self.bot_id:
                                continue
                            try:
                                await self.highrise.teleport(u.id, target_pos)
                                count += 1
                                await asyncio.sleep(0.3)
                            except Exception:
                                pass

                        dest_name = loc_part if loc_part else "موقع البوت"
                        await self.highrise.chat(f"✅ تم نقل {count} مستخدم إلى {dest_name}")
                    except Exception as e:
                        print(f"Error in اون الكل: {e}")
                        await self.highrise.chat("❌ حدث خطأ أثناء نقل الجميع")
                else:
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
                return

            # التفاعل مع ذكر اسم لورد
            if "لورد" in message or "lord" in message.lower():
                # التحقق إذا كانت الرسالة هي "لورد" فقط أو "لورد @username"
                is_pure_lord = message.strip() == "لورد"
                is_target_lord = message.startswith("لورد @")
                
                if (is_pure_lord or is_target_lord) and "لورد" in self.teleport_locations:
                    try:
                        target_pos = self.teleport_locations["لورد"]
                        if is_pure_lord:
                            await self.highrise.teleport(user.id, target_pos)
                            await self.highrise.send_whisper(user.id, "✨ تم نقلك إلى مكان لورد")
                        else:
                            # نقل شخص آخر (للمشرفين)
                            if await self.is_user_allowed(user):
                                parts = message.split()
                                target_username = parts[1][1:].strip()
                                room_users = await self.highrise.get_room_users()
                                target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                                if target_user:
                                    await self.highrise.teleport(target_user.id, target_pos)
                                else:
                                    await self.highrise.send_whisper(user.id, f"❌ المستخدم @{target_username} غير موجود")
                            else:
                                await self.highrise.send_whisper(user.id, "❌ ليس لديك صلاحية لنقل الآخرين")
                        return
                    except Exception as e:
                        print(f"Error teleporting to lord: {e}")

            # أمر منشوراتي ومنشورات المستخدم
            if message.lower().startswith("منشوراتي") or message.lower().startswith("منشورات @"):
                try:
                    target_username = ""
                    if message.lower().startswith("منشوراتي"):
                        target_username = user.username
                    else:
                        parts = message.split("@")
                        if len(parts) > 1:
                            target_username = parts[1].strip().split()[0]
                        else:
                            await self.highrise.send_whisper(user.id, "⚠️ يرجى منشن المستخدم بشكل صحيح")
                            return

                    if not self.webapi:
                        # محاولة إعادة تهيئة WebApi إذا كان متاحاً
                        try:
                            from highrise.webapi import WebApi
                            self.webapi = WebApi()
                        except:
                            await self.highrise.send_whisper(user.id, "❌ خدمة الويب غير متوفرة في هذا الإصدار من البوت")
                            return

                    # الحصول على معلومات المستخدم من الويب
                    try:
                        user_search = await self.webapi.get_users(username=target_username, limit=1)
                        if not user_search or not user_search.users:
                            await self.highrise.send_whisper(user.id, f"❌ لم يتم العثور على المستخدم @{target_username} في قاعدة بيانات Highrise")
                            return
                        target_user_id = user_search.users[0].user_id
                    except Exception as e:
                        print(f"WebAPI get_users failed for {target_username}: {e}")
                        await self.highrise.send_whisper(user.id, f"❌ عذراً، لا يمكنني الوصول لبيانات المستخدم @{target_username} حالياً")
                        return
                    
                    # جلب منشورات المستخدم
                    posts_response = None
                    try:
                        posts_response = await self.webapi.get_posts(user_id=target_user_id, limit=50)
                    except Exception as web_err:
                        # إذا فشل جلب المنشورات (مثل 404 أو حساب خاص)، نعرض عدد المنشورات 0
                        print(f"WebAPI get_posts failed for {target_username}: {web_err}")
                        await self.highrise.chat(f"👤 @{target_username} posts:\n• Post count: 0\n• No public posts available" if self.bot_lang == "en" else f"👤 منشورات @{target_username}:\n• عدد المنشورات: 0\n• لا توجد منشورات عامة لعرض التفاعلات")
                        return
                    
                    if not posts_response or not posts_response.posts:
                        await self.highrise.chat(f"👤 @{target_username} posts:\n• Post count: 0\n• No public posts" if self.bot_lang == "en" else f"👤 منشورات @{target_username}:\n• عدد المنشورات: 0\n• لا توجد منشورات عامة لعرض التفاعلات")
                        return

                    total_posts = posts_response.total
                    max_likes = 0
                    
                    for post in posts_response.posts:
                        if hasattr(post, 'num_likes') and post.num_likes > max_likes:
                            max_likes = post.num_likes

                    await self.highrise.chat(f"👤 @{target_username} posts:\n• Total: {total_posts}\n• Most likes: {max_likes} ❤️" if self.bot_lang == "en" else f"👤 منشورات @{target_username}:\n• عدد المنشورات الفعلي: {total_posts}\n• أكثر عدد لايكات على منشور: {max_likes} ❤️")
                    
                except Exception as e:
                    print(f"Error in posts command: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ غير متوقع أثناء جلب البيانات")
                return
                
                # الرد التلقائي إذا لم يتم النقل أو كانت رسالة عادية تحتوي على كلمة لورد
                if "لورد" in message or "lord" in message.lower():
                    try:
                        await self.highrise.react("heart", user.id)
                        await self.highrise.send_emote("emote-kissing-bound", user.id)
                        await self.highrise.chat(f"I adore you my lord 🙊❤️ @{user.username}" if self.bot_lang == "en" else f"اموت عليك لوردي🙊❤️ @{user.username}")
                    except Exception as e:
                        print(f"Error reacting to lord mention: {e}")
                    return

            # أمر حفظ مكان لورد (للمالك فقط - للسرعة)
            if message.strip() == "اضف مكان لورد":
                message = "حفظ مكان لورد" # تحويله للأمر العام
            # أمر نقاطي في الروم (معالجة أولاً قبل إضافة النقاط)
            if message.lower().strip() == "نقاطي":
                try:
                    user_points = self.get_user_points(user.id)
                    user_level = self.calculate_user_level(user_points)
                    next_level_points = self.get_points_for_next_level(user_points)
                    ulang = self.get_user_lang(user.id)

                    if ulang == "en":
                        if user_level == 16:
                            points_message = f"⭐ Points:\n@{user.username}\n{user_points}XP / 70000XP\nLevel: {user_level} (MAX)"
                        elif user_level == 0:
                            points_message = f"⭐ Points:\n@{user.username}\n{user_points}XP / 30XP\nLevel: {user_level}"
                        else:
                            points_message = f"⭐ Points:\n@{user.username}\n{user_points}XP / {next_level_points}XP\nLevel: {user_level}"
                    else:
                        if user_level == 16:
                            points_message = f"⭐ نقاطك:\n@{user.username}\n{user_points} نقطة / 70000 نقطة\nالمستوى: {user_level} (الحد الأقصى)"
                        elif user_level == 0:
                            points_message = f"⭐ نقاطك:\n@{user.username}\n{user_points} نقطة / 30 نقطة\nالمستوى: {user_level}"
                        else:
                            points_message = f"⭐ نقاطك:\n@{user.username}\n{user_points} نقطة / {next_level_points} نقطة\nالمستوى: {user_level}"

                    await self.highrise.send_whisper(user.id, points_message)
                    print(f"Sent points info as whisper for {user.username}: {points_message}")

                except Exception as e:
                    print(f"Error in نقاطي command: {e}")
                    ulang = self.get_user_lang(user.id)
                    await self.highrise.send_whisper(user.id, "❌ Error retrieving your points." if ulang == "en" else "❌ حدث خطأ في عرض النقاط")
                return

            # إضافة نقاط للمستخدم عند كتابة رسالة في الروم (40 نقطة لكل رسالة)
            # تجنب إضافة نقاط للبوت نفسه وتجنب إضافة نقاط لأمر نقاطي
            if user.id != self.bot_id and message.lower().strip() != "نقاطي":
                self.add_user_points(user.id, 40)
            
        if message.lower().strip() == "!xp":
            try:
                if not self.user_points:
                    await self.highrise.chat("📊 No XP data available yet")
                    return

                leaderboard_data = []
                for user_id_key, points in self.user_points.items():
                    if user_id_key == self.bot_id:
                        continue
                    
                    current_level = self.calculate_user_level(points)
                    leaderboard_data.append({
                        'user_id': user_id_key,
                        'points': points,
                        'level': current_level
                    })

                leaderboard_data.sort(key=lambda x: x['points'], reverse=True)
                
                if not leaderboard_data:
                    await self.highrise.chat("📊 No users with XP found")
                    return

                # Get usernames for the top users
                room_users = await self.highrise.get_room_users()
                room_user_map = {u.id: u.username for u, p in room_users.content}

                leaderboard_msg = "🏆 XP Leaderboard:\n"
                # Reduce to top 5 to avoid "Message too long" error
                for i, user_data in enumerate(leaderboard_data[:5], 1):
                    username = room_user_map.get(user_data['user_id'], f"User_{user_data['user_id'][:5]}")
                    leaderboard_msg += f"{i}. @{username}: {user_data['points']} XP (Lv {user_data['level']})\n"
                
                await self.highrise.chat(leaderboard_msg)
            except Exception as e:
                print(f"Error in !xp: {e}")
                await self.highrise.chat("❌ Error generating leaderboard")
            return

        # أمر احسب (Calculator)
        if message.lower().startswith("احسب "):
            try:
                expression = message[5:].strip()
                # تنظيف التعبير الرياضي للسماح فقط بالأرقام والعمليات الأساسية
                allowed_chars = "0123456789+-*/(). "
                if all(char in allowed_chars for char in expression):
                    # استخدام eval بحذر مع فحص الأحرف المسموح بها
                    result = eval(expression)
                    await self.highrise.chat(f"🔢 Calculation result: {expression} = {result}" if self.bot_lang == "en" else f"🔢 نتيجة الحساب: {expression} = {result}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ يرجى استخدام أرقام وعمليات رياضية صحيحة فقط (+, -, *, /)")
            except ZeroDivisionError:
                await self.highrise.send_whisper(user.id, "❌ لا يمكن القسمة على صفر")
            except Exception:
                await self.highrise.send_whisper(user.id, "❌ تعبير رياضي غير صحيح")
            return

        # أمر الوقت (Time for countries)
        if message.lower().strip() in ["الوقت", "توقيت", "time"]:
            try:
                countries_tz = {
                    "السعودية 🇸🇦": "Asia/Riyadh",
                    "مصر 🇪🇬": "Africa/Cairo",
                    "الإمارات 🇦🇪": "Asia/Dubai",
                    "العراق 🇮🇶": "Asia/Baghdad",
                    "المغرب 🇲🇦": "Africa/Casablanca",
                    "الجزائر 🇩🇿": "Africa/Algiers",
                    "تونس 🇹🇳": "Africa/Tunis",
                    "ليبيا 🇱🇾": "Africa/Tripoli",
                    "السودان 🇸🇩": "Africa/Khartoum",
                    "اليمن 🇾🇪": "Asia/Aden",
                    "سوريا 🇸🇾": "Asia/Damascus",
                    "لبنان 🇱🇧": "Asia/Beirut",
                    "الأردن 🇯🇴": "Asia/Amman",
                    "فلسطين 🇵🇸": "Asia/Gaza",
                    "الكويت 🇰🇼": "Asia/Kuwait",
                    "قطر 🇶🇦": "Asia/Qatar",
                    "البحرين 🇧🇭": "Asia/Bahrain",
                    "عمان 🇴🇲": "Asia/Muscat",
                    "موريتانيا 🇲🇷": "Africa/Nouakchott",
                    "الصومال 🇸🇴": "Africa/Mogadishu",
                    "جيبوتي 🇩🇯": "Africa/Djibouti",
                    "جزر القمر 🇰🇲": "Indian/Comoro"
                }
                
                response_parts = []
                for country, tz_name in countries_tz.items():
                    tz = pytz.timezone(tz_name)
                    now = datetime.now(tz)
                    response_parts.append(f"{country}: {now.strftime('%I:%M %p')}")
                
                # إرسال كل دولة في رسالة منفصلة
                header = "⏰ الوقت الحالي في الدول العربية:"
                await self.highrise.chat(header)
                await asyncio.sleep(0.5)
                
                for part in response_parts:
                    await self.highrise.chat(f"🕒 {part}")
                    await asyncio.sleep(0.7) # فاصل زمني لتجنب الحظر والسبام
            except Exception as e:
                print(f"Error in الوقت command: {e}")
            return

        # أمر الإحداثيات (للمشرفين فقط)
        if message.strip() == "الاحداثيات":
            if await self.is_user_allowed(user):
                try:
                    room_users = await self.highrise.get_room_users()
                    user_pos = next((p for u, p in room_users.content if u.id == user.id), None)
                    if user_pos and isinstance(user_pos, Position):
                        coords_msg = f"📍 إحداثياتك الحقيقية:\nX: {user_pos.x:.2f}, Y: {user_pos.y:.2f}, Z: {user_pos.z:.2f}\nالمواجهة: {user_pos.facing}"
                        await self.highrise.chat(coords_msg)
                    else:
                        await self.highrise.send_whisper(user.id, "❌ تعذر تحديد إحداثياتك")
                except Exception as e:
                    print(f"Error in الاحداثيات command: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
            return

        # أمر إحداثيات مستخدم معين (للمشرفين فقط)
        if message.startswith("احداثيات @"):
            if await self.is_user_allowed(user):
                try:
                    parts = message.split()
                    if len(parts) >= 2:
                        target_username = parts[1][1:].strip()
                        room_users = await self.highrise.get_room_users()
                        target_user_data = next(((u, p) for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                        
                        if target_user_data:
                            target_user, target_pos = target_user_data
                            if target_pos and isinstance(target_pos, Position):
                                coords_msg = f"📍 إحداثيات @{target_username}:\nX: {target_pos.x:.2f}, Y: {target_pos.y:.2f}, Z: {target_pos.z:.2f}"
                                await self.highrise.chat(coords_msg)
                            else:
                                await self.highrise.send_whisper(user.id, f"❌ تعذر تحديد إحداثيات @{target_username}")
                        else:
                            await self.highrise.send_whisper(user.id, f"❌ المستخدم @{target_username} غير موجود")
                except Exception as e:
                    print(f"Error in احداثيات @ command: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمشرفين فقط")
            return

        # أمر الحصول على المعرف (ID)
        if message.lower().startswith("اي دي") or message.lower().startswith("id"):
            try:
                parts = message.split()
                if len(parts) == 1:
                    # إظهار معرف المستخدم الذي أرسل الأمر
                    await self.highrise.chat(f"🆔 Your ID is: {user.id}" if self.bot_lang == "en" else f"🆔 معرفك هو: {user.id}")
                elif len(parts) >= 2 and parts[1].startswith("@"):
                    # إظهار معرف المستخدم المستهدف
                    target_username = parts[1][1:].strip()
                    room_users = await self.highrise.get_room_users()
                    target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                    
                    if target_user:
                        await self.highrise.chat(f"🆔 @{target_username}'s ID is: {target_user.id}" if self.bot_lang == "en" else f"🆔 معرف @{target_username} هو: {target_user.id}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ المستخدم @{target_username} غير موجود في الغرفة")
            except Exception as e:
                print(f"Error in ID command: {e}")
            return

        # نظام شرح الأوامر الشامل
        if message.lower().startswith("شرح "):
            cmd_to_explain = message.replace("شرح ", "").strip()
            
            explanations = {
                # أوامر الطوابق
                "طلعني": "أمر للانتقال السريع للطوابق. استخدم: 'طلعني 1' أو 'طلعني 2' أو 'طلعني 3'.",
                "طوابق": "يعرض قائمة الطوابق المتاحة وأرقامها.",
                "floors": "مرادف لأمر 'طوابق' لعرض الطوابق المتاحة.",
                
                # أوامر الرقص المستهدف
                "بوسة": "يرسل بوسة لمستخدم محدد. استخدم: 'بوسة @username'.",
                "ريست": "يجعل مستخدم محدد يجلس. استخدم: 'ريست @username'.",
                "جوست": "ينفذ حركة الجوست لمستخدم محدد. استخدم: 'جوست @username'.",
                "خجول": "يجعل مستخدم محدد ينفذ حركة الخجل. استخدم: 'خجول @username'.",
                "ضفدع": "يجعل مستخدم محدد ينفذ حركة الضفدع. استخدم: 'ضفدع @username'.",
                "تسس": "يجعل مستخدم محدد ينفذ حركة التسس (اللعنة). استخدم: 'تسس @username'.",
                "غبي": "يجعل مستخدم محدد ينفذ حركة الغباء/الحيرة. استخدم: 'غبي @username'.",
                "عضلات": "يجعل مستخدم محدد يتباهى بعضلاته. استخدم: 'عضلات @username'.",
                "حزن": "يجعل مستخدم محدد يحزن. استخدم: 'حزن @username'.",
                
                # أوامر الرقص الجماعي (للمشرفين)
                "الكل ريست": "يجعل جميع الحضور يجلسون في وقت واحد.",
                "الكل بوسة": "يجعل جميع الحضور يرسلون بوسات في وقت واحد.",
                "الكل خجول": "يجعل جميع الحضور ينفذون حركة الخجل.",
                "الكل جوست": "يجعل جميع الحضور ينفذون حركة الجوست.",
                "الكل ضفدع": "يجعل جميع الحضور ينفذون حركة الضفدع.",
                "الكل تسس": "يجعل جميع الحضور ينفذون حركة التسس.",
                "الكل غبي": "يجعل جميع الحضور ينفذون حركة الغباء.",
                "الكل عضلات": "يجعل جميع الحضور يتباهون بعضلاتهم.",
                "الكل تفكير": "يجعل جميع الحضور ينفذون حركة التفكير.",
                "الكل حزن": "يجعل جميع الحضور يحزنون.",
                "الكل ضحك": "يجعل جميع الحضور يضحكون.",
                "الكل قلب": "يجعل جميع الحضور يشكلون قلباً بأيديهم.",
                "الكل زومبي": "يجعل جميع الحضور ينفذون حركة الزومبي.",
                "الكل رقص": "يجعل جميع الحضور يرقصون رقصة الفلوس (Floss).",
                "stopall": "إيقاف الرقص للجميع في الروم.",
                "all": "يجعل الجميع يرقصون رقصة معينة برقمها. استخدم: 'all [رقم الرقصة]'.",
                "loopall": "بدء رقص جماعي مستمر. استخدم: 'loopall [رقم الرقصة]'.",
                
                # أوامر الإدارة (للمشرفين والأونرز)
                "اسحب": "يجلب مستخدم معين لموقعك. استخدم: 'اسحب @username'.",
                "جيبلي": "البوت يمشي لعند المستخدم أولاً ثم يجيبه لموقعك. استخدم: 'جيبلي @username'.",
                "tel": "ينقلك لموقع مستخدم معين. استخدم: 'tel @username'.",
                "روح": "مرادف لأمر 'tel' للانتقال لمستخدم معين.",
                "go": "مرادف لأمر 'tel' للانتقال لمستخدم معين.",
                "tp": "مرادف لأمر 'tel' للانتقال لمستخدم معين.",
                "وديني": "مرادف لأمر 'tel' للانتقال لمستخدم معين.",
                "follow": "يجعل البوت يتبع مستخدماً معيناً. استخدم: 'follow @username'. للإنهاء: 'stop follow'.",
                "!mod": "إضافة أدمن جديد للبوت. استخدم: '!mod @username'.",
                "!delmod": "حذف أدمن من البوت. استخدم: '!delmod @username'.",
                "!addvip": "إضافة مستخدم لقائمة VIP. استخدم: '!addvip @username'.",
                "!removevip": "إزالة مستخدم من قائمة VIP. استخدم: '!removevip @username'.",
                "!addswm": "إضافة ترحيب خاص لمستخدم. استخدم: '!addswm @username نص الترحيب'.",
                "!removeswm": "حذف الترحيب الخاص لمستخدم. استخدم: '!removeswm @username'.",
                "spam": "بدء تكرار رسالة. استخدم: 'spam نص الرسالة'. للإيقاف: 'nospam'.",
                "move": "نقل مستخدم لموقع مستخدم آخر. استخدم: 'move @user1 @user2'.",
                "تعال يا بوت": "أمر لجعل البوت يأتي لموقعك الحالي.",
                "ارجع يا بوت": "أمر لجعل البوت يعود لموقعه الأصلي المحفوظ.",
                "ابعدهم": "أمر خاص للمالك @_king_man_1 لإبعاد الجميع عن موقعه.",
                "جيب الكل": "أمر خاص للمالك @_king_man_1 لسحب جميع الحضور لموقعه الحالي.",
                "مايك": "أمر لنقل مستخدم معين لموقع المايك. استخدم: 'مايك @username'.",
                "سجن": "ينقلك لمنطقة السجن (للمشرفين فقط).",
                
                # أوامر عامة وإضافات
                "نقاطي": "يعرض نقاطك، مستواك (0-16)، والنقاط المطلوبة للمستوى التالي.",
                "ping": "لفحص سرعة اتصال البوت واستجابته بالملي ثانية.",
                "time": "يعرض المدة التي قضاها البوت في الروم منذ تشغيله.",
                "list": "عرض قائمة الرقصات المتاحة مع أرقامها.",
                "vip": "ينقلك مباشرة لمنطقة الـ VIP (إذا كنت تملك الصلاحية).",
                "فوق": "ينقلك للطابق العلوي/منطقة الـ VIP.",
                "تحت": "ينقلك للطابق السفلي.",
                "up": "مرادف لأمر 'فوق'.",
                "down": "مرادف لأمر 'تحت'.",
                "0": "إيقاف الرقص الحالي الخاص بك.",
                "stop": "إيقاف الرقص الحالي الخاص بك.",
                "floss": "تنفيذ رقصة الفلوس (Floss).",
                "rest": "تنفيذ حركة الجلوس.",
                "ghost": "تنفيذ حركة الجوست.",
                "floss forever": "بدء رقصة الفلوس بشكل مستمر.",
                "dance floor": "بدء رقصة معينة بشكل مستمر."
            }
            
            if cmd_to_explain in explanations:
                await self.highrise.chat(f"📖 **Command help ({cmd_to_explain}):**\n{explanations[cmd_to_explain]}" if self.bot_lang == "en" else f"📖 **شرح أمر ({cmd_to_explain}):**\n{explanations[cmd_to_explain]}")
            else:
                await self.highrise.chat(f"❌ Sorry, no help found for '{cmd_to_explain}'. Check the command list for the exact name." if self.bot_lang == "en" else f"❌ عذراً، لم أجد شرحاً للأمر '{cmd_to_explain}'. تأكد من كتابة الاسم كما هو في قائمة الأوامر.")
            return

        # فحص أوامر الرقص الجماعي
        all_emotes = {
            "الكل ريست": "sit-open",
            "الكل بوسة": "emote-kissing-bound",
            "الكل خجول": "emote-shy",
            "الكل جوست": "emote-ghost-idle",
            "الكل ضفدع": "emote-frog",
            "الكل تسس": "emote-snake",
            "الكل تس": "emote-snake",
            "الكل غبي": "emote-confused",
            "الكل عضلات": "emoji-flex",
            "الكل تفكير": "emote-thinking",
            "الكل حزن": "emote-sad",
            "الكل ضحك": "emote-laughing",
            "الكل قلب": "emote-heartshape",
            "الكل زومبي": "emote-zombierun",
            "الكل رقص": "dance-floss"
        }
        
        for cmd_name, emote_id in all_emotes.items():
            if message.lower().strip() == cmd_name:
                if await self.is_user_allowed(user):
                    try:
                        room_users = await self.highrise.get_room_users()
                        for target_user, _ in room_users.content:
                            if target_user.id != self.bot_id:
                                await self.highrise.send_emote(emote_id, target_user.id)
                    except Exception as e:
                        print(f"Error sending all emote {cmd_name}: {e}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ ليس لديك صلاحية لاستخدام هذا الأمر")
                return

        # فحص أوامر الرقص المستهدفة
        target_emotes = {
            "بوسة": "emote-kissing-bound",
            "ريست": "sit-open",
            "جوست": "emote-ghost-idle",
            "خجول": "emote-shy",
            "ضفدع": "emote-frog",
            "تسس": "emote-snake",
            "تس": "emote-snake",
            "غبي": "emote-confused",
            "عضلات": "emoji-flex",
            "حزن": "emote-sad",
            "مرجحه": "idle-dance-swinging",
            "مرجحة": "idle-dance-swinging"
        }
        
        for cmd_name, emote_id in target_emotes.items():
            if message.lower().startswith(f"{cmd_name} @"):
                parts = message.split()
                if len(parts) >= 2 and parts[1].startswith("@"):
                    target_username = parts[1][1:].strip()
                    # فحص الحماية قبل تنفيذ الأمر
                    if self.is_user_protected(target_username):
                        await self.highrise.send_whisper(user.id, f"🛡️ المستخدم @{target_username} محمي ولا يمكن استخدام هذا الأمر عليه")
                        return
                    room_users = await self.highrise.get_room_users()
                    target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                    
                    if target_user:
                        try:
                            await self.highrise.send_emote(emote_id, target_user.id)
                        except Exception as e:
                            print(f"Error sending target emote {cmd_name}: {e}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ المستخدم @{target_username} غير موجود")
                return

        # Reset command_executed for non-priority commands
        command_executed = False

        if not command_executed and message.lower().startswith("floss"):
            await self.highrise.send_emote("dance-floss", user.id)
            command_executed = True
            return

        # رد البوت على رسائل الحب والإطراء
        if not command_executed and message.startswith(("i love you bot","بوت بحبك","بوت","بوت اا","البوت جامد"," لورد","بحبك","سراج")):
            await self.highrise.react("heart", user.id)
            command_executed = True

        # رقصة الانحناء للكلمات الترحيبية
        if not command_executed:
            bow_words = ["ولكم", "تو", "تي", "منور", "نورك", "وب"]
            if any(word in message.lower() for word in bow_words):
                await self.highrise.send_emote("emote-bow", user.id)
                command_executed = True


        isimler1 = [
            "\n1 - ",
            "\n2 - ",
            "\n3 - ",
            "\n4 - ",
            "\n5 - ",
        ]
        isimler2 = [
            "\n6 - ",
            "\n7 - ",
            "\n8 - ",
            "\n9 - ",
            "\n10 - ",
        ]
        isimler3 = [
            "\n11 - ",
            "\n12 - ",
            "\n13 - ",
            "\n14 - ",
            "\n15 - ",
        ]
        isimler4 = [
            "\n16 - ",
            "\n17 - ",
            "\n18 - ",
            "\n19 - ",
            "\n20 - ",
        ]
        isimler5 = [
            "\n21 - ",
            "\n22 - ",
            "\n23 - ",
            "\n24 - ",
            "\n25 - ",
            "\n26 - "

            # Diğer isimler buraya eklenecek
        ]


        if not command_executed and message.lower().startswith("list"):
            await self.highrise.chat("\n".join(isimler1))
            await self.highrise.chat("\n".join(isimler2))
            await self.highrise.chat("\n".join(isimler3))
            await self.highrise.chat("\n".join(isimler4))
            await self.highrise.chat("\n".join(isimler5))
            await self.highrise.chat(f"\n\n Follow bot owner @_king_man_1" if self.bot_lang == "en" else f"\n\n تابعو صاحب بوت @_king_man_1")
            command_executed = True

        message = message.lower()
        
        if not command_executed and message in ["floors", "طوابق", "الطوابق"]:
            floors_help = "🏢 **الطوابق المتاحة:**\n"
            floors_help += "اكتب 'طلعني' متبوعة برقم الطابق:\n"
            floors_help += "طلعني 1 - الطابق الأول\n"
            floors_help += "طلعني 2 - الطابق الثاني\n"
            floors_help += "طلعني 3 - الطابق الثالث"
            await self.highrise.chat(floors_help)
            command_executed = True
            return
        
        if not command_executed and message.startswith("طلعن٧٨ي "):
            try:
                floor_num = message.replace("طلع٧٨ني", "").strip()
                
                floor_positions = {
                    "1": Position(10.5, 6,4),
                    "2": Position(9, 10,3.50),
                    "3": Position(13.5, 15.10, 3.50)
                }
                
                if floor_num in floor_positions:
                    if self.is_user_jailed(user.id):
                        import time as time_module
                        remaining_time = int((self.jailed_users[user.id] - time_module.time()) / 60)
                        await self.highrise.chat(f"🔒 @{user.username} is jailed! Cannot use teleport commands for {remaining_time + 1} more minutes" if self.bot_lang == "en" else f"🔒 @{user.username} مسجون! لا يمكنك استخدام أوامر النقل لمدة {remaining_time + 1} دقيقة أخرى")
                        return
                    
                    await self.teleport(user, floor_positions[floor_num])
                    command_executed = True
                else:
                    await self.highrise.chat(f"❌ Invalid floor number! Use: طلعني 1 or طلعني 2 or طلعني 3" if self.bot_lang == "en" else f"❌ رقم الطابق غير صحيح! استخدم: طلعني 1 أو طلعني 2 أو طلعني 3")
            except Exception as e:
                await self.highrise.chat(f"❌ Error teleporting to floor: {e}" if self.bot_lang == "en" else f"❌ خطأ في الانتقال للطابق: {e}")
            return

        self.teleport_locations = {            
            "نتالتنمص": Position(14.5, 8.35, 5.5),
            "وستابفتزط": Position(14.2, 8.35, 5.5),  
            "فوق": Position(12.5, 6.75, 8.5),   
            "تحت": Position(9.0, 0.0, 5.),
            "down": Position(10.5, 0.0, 9.5),
            "up": Position(13.5, 7.75, 3.5),
            "فنبنبزببوق1": Position(1, 15, 3.1),
            "طل٧٨٥عني": Position(13.5, 7.75, 3.5),
            "صعدني": Position(14, 14.85, 6),
            "vr": Position(19.5, 19.25, 0.5),
            "فوررررق2ffff": Position(13.5, 13.5, 4.5),
            "طلللللعني2": Position(13.5, 13.5, 4.5),
            "صعييسسدني2": Position(13.5, 13.5, 4.5)
        } 

        

        # فحص الانتقال للأماكن المحفوظة (شخصي أو لمستخدم آخر)
        if not command_executed:
            # دمج المواقع الثابتة مع المواقع المحملة من الملف
            all_locations = self.teleport_locations.copy()
            
            for location_name, position in all_locations.items():
                if message.lower() == location_name.lower():
                    # فحص إذا كان المستخدم مسجون
                    if self.is_user_jailed(user.id):
                        import time as time_module
                        remaining_time = int((self.jailed_users[user.id] - time_module.time()) / 60)
                        await self.highrise.chat(f"🔒 @{user.username} is jailed! Cannot use teleport commands for {remaining_time + 1} more minutes" if self.bot_lang == "en" else f"🔒 @{user.username} مسجون! لا يمكنك استخدام أوامر النقل لمدة {remaining_time + 1} دقيقة أخرى")
                        return
                    
                    # انتقال شخصي
                    try:
                        await self.teleport(user, position)
                        command_executed = True
                        return
                    except Exception as e:
                        await self.highrise.chat(f"❌ Error teleporting to {location_name}: {e}" if self.bot_lang == "en" else f"❌ خطأ في الانتقال إلى {location_name}: {e}")
                    return

            # فحص أوامر إرسال المستخدمين للأماكن المحفوظة (منفصل)
            for location_name, position in all_locations.items():
                if message.lower().startswith(f"{location_name.lower()} @"):
                    # إرسال مستخدم آخر (للمشرفين فقط)
                    if await self.is_user_allowed(user):
                        parts = message.split()
                        if len(parts) >= 2 and parts[1].startswith("@"):
                            target_username = parts[1][1:].strip()

                            # البحث عن المستخدم في الغرفة
                            room_users = await self.highrise.get_room_users()
                            target_user = None
                            for room_user, _ in room_users.content:
                                if room_user.username.lower() == target_username.lower():
                                    target_user = room_user
                                    break

                            if target_user:
                                try:
                                    await self.highrise.teleport(target_user.id, position)
                                except Exception as e:
                                    await self.highrise.chat(f"❌ Error teleporting @{target_username} to {location_name}: {e}" if self.bot_lang == "en" else f"❌ خطأ في نقل @{target_username} إلى {location_name}: {e}")
                            else:
                                await self.highrise.chat(f"❌ User {target_username} is not in the room" if self.bot_lang == "en" else f"❌ المستخدم {target_username} غير موجود في الغرفة")
                        else:
                            await self.highrise.chat(f"📝 Usage: {location_name} @username" if self.bot_lang == "en" else f"📝 استخدم: {location_name} @username")
                    else:
                        await self.highrise.chat("❌ You do not have permission to teleport other users" if self.bot_lang == "en" else "❌ ليس لديك صلاحية لإرسال مستخدمين آخرين")
                    return

        if not command_executed and message in ["Vip","vip","!Vip","!vip"]:
            user_privileges = await self.highrise.get_room_privilege(user.id)
            is_moderator = user_privileges.moderator
            is_owner = user.username in self.owners
            is_admin = user.username.lower() in [a.lower() for a in self.admins]

            if is_moderator or is_owner or is_admin:
                try:
                    await self.highrise.teleport(user.id, Position(11.5, 1.25, 22.0))
                    await self.highrise.send_whisper(user.id, "✅ تم نقلك إلى منطقة VIP")
                    command_executed = True
                    return
                except Exception as e:
                    await self.highrise.chat(f"❌ Teleport error: {e}" if self.bot_lang == "en" else f"❌ خطأ في النقل: {e}")
                    return
            command_executed = True

        if message in ["السجن","سجن","Vvisjsgsp","VsbshsVIP"]:
            user_privileges = await self.highrise.get_room_privilege(user.id)
            if (user_privileges.moderator) or (user.username in self.haricler):
                try:
                    await self.highrise.teleport(f"{user.id}", Position(x=2.5, y=16.25, z=2.5, facing='FrontLeft'))
                    return
                except:
                    print("error 3")
            else:
                try:
                    await self.highrise.send_whisper(user.id, "مشرفين فقط.")
                    return
                except:
                    print("error 4")

        if message in ["فوق","صعدني","up","طلعني"]:
            # فحص حماية المالك
            if self.owner_protected and user.username.lower() in [owner.lower() for owner in self.owners]:
                await self.highrise.chat("🛡️ The owner is currently protected and this command cannot be used on them" if self.bot_lang == "en" else "🛡️ المالك محمي حالياً ولا يمكن استخدام هذا الأمر عليه")
                return
            user_privileges = await self.highrise.get_room_privilege(user.id)
            if (user_privileges.moderator) or (user.username in self.owners):
                try:
                    await self.highrise.teleport(f"{user.id}", Position(x=7.5, y=11.0, z=2.5, facing='FrontLeft'))
                    return
                except:
                    print("error 3")
            else:
                try:
                    await self.highrise.send_whisper(user.id, "ادفع 10 جولد للبوت عشان تدخل vip معانا.")
                    return
                except:
                    print("error 4")

        if not command_executed and message.lower() == "ping":
            import time
            start_time = time.time()
            # قياس وقت الاستجابة بإرسال رسالة بسيطة
            await self.highrise.chat("🏓 Pong!")
            end_time = time.time()
            ping_time = round((end_time - start_time) * 1000, 2)  # تحويل إلى ميلي ثانية
            await self.highrise.chat(f"📊 Ping: {ping_time}ms" if self.bot_lang == "en" else f"📊 البينج: {ping_time}ms")
            command_executed = True
            return

        if message.lower() == "time":
            if self.start_time:
                current_time = datetime.now()
                uptime = current_time - self.start_time

                # حساب الأيام والساعات والدقائق والثواني
                days = uptime.days
                hours, remainder = divmod(uptime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                # إنشاء رسالة الوقت
                time_parts = []
                if days > 0:
                    time_parts.append(f"{days} يوم")
                if hours > 0:
                    time_parts.append(f"{hours} ساعة")
                if minutes > 0:
                    time_parts.append(f"{minutes} دقيقة")
                if seconds > 0:
                    time_parts.append(f"{seconds} ثانية")

                if time_parts:
                    time_message = " و ".join(time_parts)
                    await self.highrise.chat(f"⏰ Bot has been in the room for: {time_message}" if self.bot_lang == "en" else f"⏰ البوت موجود في الروم منذ: {time_message}")
                else:
                    await self.highrise.chat("⏰ Bot just entered the room" if self.bot_lang == "en" else "⏰ البوت دخل الروم منذ لحظات")
            else:
                await self.highrise.chat("⏰ Cannot determine when bot entered the room" if self.bot_lang == "en" else "⏰ لا يمكن تحديد وقت دخول البوت للروم")

        if message.lower().startswith("spam "):
            if await self.is_user_allowed(user):
                # استخراج الرسالة المراد تكرارها
                spam_text = message[5:].strip()  # إزالة "spam " من بداية الرسالة
                if spam_text:
                    self.spam_message = spam_text
                    self.spam_active = True

                    # إيقاف أي spam سابق
                    if self.spam_task and not self.spam_task.done():
                        self.spam_task.cancel()

                    # بدء spam جديد
                    self.spam_task = asyncio.create_task(self.spam_loop())
                    await self.highrise.chat(f"Start: {spam_text}" if self.bot_lang == "en" else f"بدء: {spam_text}")
                else:
                    await self.highrise.chat("Type spam followed by the message to repeat" if self.bot_lang == "en" else "اكتب spam متبوعة بالرسالة المراد تكرارها")
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")

        if message.lower() == "nospam":
            if await self.is_user_allowed(user):
                self.spam_active = False
                if self.spam_task and not self.spam_task.done():
                    self.spam_task.cancel()
                await self.highrise.chat("Message repetition stopped" if self.bot_lang == "en" else "تم إيقاف تكرار الرسائل")
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")

        # فحص صلاحيات الأدمن للأوامر التالية
        user_privileges = await self.highrise.get_room_privilege(user.id)
        # Check bot admin with case insensitive comparison
        is_bot_admin = any(user.username.lower() == admin.lower() for admin in self.admins)
        is_admin_or_above = (user_privileges.moderator) or (user.username in self.owners) or is_bot_admin
        
        # فحص صلاحيات الأدمن العادي (بدون أوامر الإدارة المتقدمة)
        is_basic_admin = is_bot_admin

        if message.lower().startswith("move ") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) != 3:
                await self.highrise.chat((f"Type move @user1 @user2 to move user1 to user2's location" if self.bot_lang == "en" else f"اكتب move @user1 @user2 لنقل user1 إلى موقع user2"))
                return

            # استخراج اسماء المستخدمين
            source_username = parts[1].replace("@", "").strip()
            target_username = parts[2].replace("@", "").strip()

            # فحص الحماية الخاصة
            if self.is_user_protected(source_username):
                await self.highrise.chat(f"❌ @{source_username} is protected and cannot be moved" if self.bot_lang == "en" else f"❌ @{source_username} محمي ولا يمكن نقله")
                return

            # الحصول على قائمة المستخدمين في الغرفة
            room_users = await self.highrise.get_room_users()

            source_user = None
            target_position = None

            # البحث عن المستخدم المصدر والهدف
            for room_user, position in room_users.content:
                if room_user.username.lower() == source_username.lower():
                    source_user = room_user
                elif room_user.username.lower() == target_username.lower():
                    target_position = position

            if source_user is None:
                await self.highrise.chat(f"User {source_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {source_username} غير موجود في الغرفة")
                return

            if target_position is None:
                await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")
                return

            try:
                # نقل المستخدم المصدر إلى موقع المستخدم الهدف
                new_position = Position(
                    target_position.x + 1,  # إضافة مسافة صغيرة لتجنب التداخل
                    target_position.y, 
                    target_position.z,
                    target_position.facing
                )
                await self.highrise.teleport(source_user.id, new_position)
                await self.highrise.chat(f"{source_username} moved to {target_username}'s position ✅" if self.bot_lang == "en" else f"تم نقل {source_username} إلى موقع {target_username} ✅")
            except Exception as e:
                await self.highrise.chat(f"Error moving user: {e}" if self.bot_lang == "en" else f"خطأ في نقل المستخدم: {e}")

        if message.lower().startswith("تثبيت") and await self.is_user_allowed(user):
            target_username = message.split("@")[-1].strip()
            room_users = await self.highrise.get_room_users()
            user_info = next((info for info in room_users.content if info[0].username.lower() == target_username.lower()), None)

            if user_info:
                target_user_obj, initial_position = user_info
                task = asyncio.create_task(self.reset_target_position(target_user_obj, initial_position))

                if target_user_obj.id not in self.position_tasks:
                    self.position_tasks[target_user_obj.id] = []
                self.position_tasks[target_user_obj.id].append(task)
                await self.highrise.chat(f"{target_username}'s position frozen ✅" if self.bot_lang == "en" else f"تم تثبيت موقع {target_username} ✅")

        # أوامر إلغاء التثبيت (go, حرر, unfix)
        unfix_commands = ["go", "حرر", "unfix" , "الغاء_التثبيت "]
        if await self.is_user_allowed(user) and any(message.lower().startswith(cmd) for cmd in unfix_commands):
            target_username = message.split("@")[-1].strip()
            room_users = await self.highrise.get_room_users()
            target_user_obj = next((user_obj for user_obj, _ in room_users.content if user_obj.username.lower() == target_username.lower()), None)

            if target_user_obj:
                tasks = self.position_tasks.pop(target_user_obj.id, [])
                for task in tasks:
                    task.cancel()
                print(f"Breaking position monitoring loop for {target_username}")
                await self.highrise.chat(f"{target_username} position unfrozen ✅" if self.bot_lang == "en" else f"تم تحرير {target_username} من تثبيت الموقع ✅")
            else:
                print(f"User {target_username} not found in the room.")
                await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")

        if message.lower().startswith("!info ") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) != 2 or not parts[1].startswith("@"):
                await self.highrise.chat("Type !info @username" if self.bot_lang == "en" else "اكتب !info @username")
                return

            target_username = parts[1][1:].strip()  # إزالة @ من بداية الاسم
            await self.get_detailed_userinfo(user, target_username)

        elif message.lower().startswith("info"):
            target_username = message.split("@")[-1].strip()
            await self.userinfo(user, target_username)


        if message.startswith("+x") or message.startswith("-x"):
            await self.adjust_position(user, message, 'x')
        elif message.startswith("+y") or message.startswith("-y"):
            await self.adjust_position(user, message, 'y')
        elif message.startswith("+z") or message.startswith("-z"):
            await self.adjust_position(user, message, 'z')


        allowed_commands = ["بدل", "degis", "değiş","değis","degiş"] 
        if any(message.lower().startswith(command) for command in allowed_commands) and await self.is_user_allowed(user):
            target_username = message.split("@")[-1].strip()

            if target_username not in self.haricler and not self.is_user_protected(target_username):
                await self.switch_users(user, target_username)
            elif self.is_user_protected(target_username):
                await self.highrise.chat(f"❌ @{target_username} is protected and cannot be swapped" if self.bot_lang == "en" else f"❌ @{target_username} محمي ولا يمكن تبديل موقعه")
            else:
                print(f"{target_username} is in the exclusion list and won't be affected by the switch.")

        # أمر إبعاد جميع المستخدمين عن المالك - للمالك فقط
        if message.lower() == "ابعدهم" or message.lower() == "ابعد الكل":
            if user.username in self.owners:
                try:
                    # الحصول على موقع المالك
                    room_users = await self.highrise.get_room_users()
                    owner_position = None
                    for room_user, position in room_users.content:
                        if room_user.id == user.id:
                            owner_position = position
                            break
                    
                    if owner_position:
                        kicked_count = 0
                        for room_user, position in room_users.content:
                            # عدم إبعاد المالك أو البوت أو المستخدمين المحميين
                            if (room_user.id != user.id and 
                                room_user.id != self.bot_id and 
                                not self.is_user_protected(room_user.username)):
                                
                                # حساب مسافة بسيطة أو مجرد نقلهم لمكان بعيد عشوائي
                                # سنقوم بنقلهم لمكان بعيد في الروم
                                await self.highrise.teleport(room_user.id, Position(random.randint(0, 5), 0, random.randint(0, 5)))
                                kicked_count += 1
                                await asyncio.sleep(0.2)
                        
                        await self.highrise.chat(f"✅ Pushed {kicked_count} users away from you @{user.username}" if self.bot_lang == "en" else f"✅ تم إبعاد {kicked_count} مستخدم عنك يا لورد @{user.username}")
                    else:
                        await self.highrise.chat("❌ Could not determine your position" if self.bot_lang == "en" else "❌ لم أتمكن من تحديد موقعك")
                except Exception as e:
                    print(f"Error in ابعدهم command: {e}")
                    await self.highrise.chat("❌ An error occurred while executing the command" if self.bot_lang == "en" else "❌ حدث خطأ أثناء تنفيذ الأمر")
            else:
                await self.highrise.chat("⚠️ This command is for owner @_king_man_1 only" if self.bot_lang == "en" else "⚠️ هذا الأمر مخصص للمالك @_king_man_1 فقط")
            return

        # أمر حفظ موقع البوت
        if (message.lower() == "حفظ المكان" or message.lower() == "save place") and (user.username in self.owners or await self.is_user_allowed(user)):
            try:
                # محاولة الحصول على موقع البوت من قائمة المستخدمين
                room_users = await self.highrise.get_room_users()
                bot_pos = next((p for u, p in room_users.content if u.id == self.bot_id), None)
                
                # إذا لم نجد موقع البوت (أحياناً لا يظهر في القائمة)، نستخدم موقع مرسل الأمر كبديل قريب
                if not bot_pos:
                    bot_pos = next((p for u, p in room_users.content if u.id == user.id), None)

                if bot_pos and isinstance(bot_pos, Position):
                    self.save_bot_position(bot_pos)
                    self.bot_start_position = bot_pos
                    await self.highrise.chat(f"✅ Location saved! ({bot_pos.x:.1f}, {bot_pos.y:.1f}, {bot_pos.z:.1f})" if self.bot_lang == "en" else f"✅ تم حفظ الموقع بنجاح! ({bot_pos.x:.1f}, {bot_pos.y:.1f}, {bot_pos.z:.1f})")
                else:
                    await self.highrise.chat("❌ Could not determine location. Try moving then retry." if self.bot_lang == "en" else "❌ عذراً، لم أتمكن من تحديد الموقع. حاول التحرك قليلاً ثم أعد الأمر.")
            except Exception as e:
                print(f"Error saving bot position: {e}")
                await self.highrise.chat("❌ Technical error while saving location." if self.bot_lang == "en" else "❌ حدث خطأ تقني أثناء حفظ الموقع.")
            return

        # أمر طلب مايك من مستخدم معين
        if message.lower().startswith("مايك @") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) >= 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()
                
                room_users = await self.highrise.get_room_users()
                target_user = next((u for u, p in room_users.content if u.username.lower() == target_username.lower()), None)
                
                if target_user:
                    try:
                        # استخدام الوظيفة الرسمية لدعوة المستخدم للمايك
                        # سيظهر للمستخدم نافذة منبثقة تطلب منه الانضمام للبث الصوتي
                        await self.highrise.add_user_to_voice(target_user.id)
                        await self.highrise.send_whisper(user.id, f"✅ تم إرسال طلب انضمام للمايك (نافذة منبثقة) لـ @{target_username}")
                    except Exception as e:
                        print(f"Error in mic request command: {e}")
                        # fallback to whisper if the specific function fails
                        await self.highrise.send_whisper(target_user.id, f"🎤 @{user.username} يطلب منك الصعود للمايك")
                        await self.highrise.send_whisper(user.id, f"⚠️ حدثت مشكلة في الطلب الرسمي، تم إرسال رسالة خاصة بدلاً من ذلك لـ @{target_username}")
                else:
                    await self.highrise.send_whisper(user.id, f"❌ المستخدم @{target_username} غير موجود")
            return

        # أوامر الانتقال للمستخدمين (tel, روح, go, tp) - للمشرفين فقط
        teleport_commands = ["tel", "روح", "go", "tp" , "وديني"]
        if await self.is_user_allowed(user) and any(message.lower().startswith(cmd) for cmd in teleport_commands):
          target_username = message.split("@")[-1].strip()
          await self.teleport_to_user(user, target_username)

        # أمر مسح الدردشة
        if message.strip() == "مسح" and await self.is_user_allowed(user):
            for _ in range(15):
                await self.highrise.chat(".\n\n\n\n\n\n\n\n\n\n.")
            await self.highrise.chat(f"🧹 Chat cleared by @{user.username}" if self.bot_lang == "en" else f"🧹 تمت تصفية الدردشة بواسطة @{user.username}")
            return

        # أمر معلومات الغرفة
        if message.strip() == "الغرفة" or message.strip() == "room":
            try:
                # Use cached info from on_start
                room_name = getattr(self, "room_name", "Unknown")
                room_id = getattr(self, "room_id", "Unknown")
                room_owner_id = getattr(self, "room_owner_id", "Unknown")
                
                # Try to get the username of the owner if it's an ID
                owner_display = room_owner_id
                try:
                    # In some SDK versions, room_users.content is a list of (User, Position)
                    room_users_resp = await self.highrise.get_room_users()
                    room_users = room_users_resp.content
                    user_count = len(room_users)
                    for room_user, _ in room_users:
                        if room_user.id == room_owner_id:
                            owner_display = room_user.username
                            break
                except:
                    user_count = "Unknown"

                # تنسيق معلومات الغرفة
                info_text = (
                    f"🏠 معلومات الغرفة:\n"
                    f"📝 الاسم: {room_name}\n"
                    f"🆔 الايدي: {room_id}\n"
                    f"👑 المالك: @{owner_display}\n"
                    f"👥 عدد اللاعبين: {user_count}"
                )
                await self.highrise.chat(info_text)
            except Exception as e:
                print(f"Error fetching room info: {e}")
                await self.highrise.chat("❌ Could not fetch room info at this time." if self.bot_lang == "en" else "❌ عذراً، لم أتمكن من جلب معلومات الغرفة حالياً.")
            return
          
        # أوامر جلب المستخدمين (اسحب ومرادفاتها) - للمشرفين والأدمن
        pull_commands = ["اسحب", "جيب", "هات", "get", "br", "b", "B"]
        if await self.is_user_allowed(user) and any(message.lower().startswith(cmd) for cmd in pull_commands):
            target_username = message.split("@")[-1].strip()
            if target_username not in self.haricler and not self.is_user_protected(target_username):
                await self.teleport_user_next_to(target_username, user)
            elif self.is_user_protected(target_username):
                await self.highrise.chat(f"❌ @{target_username} Special user")

        # أمر جيبلي @username - البوت يمشي خطوة بخطوة للمستخدم ثم يجيبه يلحقه للمشرف
        if await self.is_user_allowed(user) and message.lower().startswith("جيبلي") and "@" in message:
            target_username = message.split("@")[-1].strip()
            if self.is_user_protected(target_username):
                await self.highrise.chat(f"❌ @{target_username} Special user")
            elif target_username in self.haricler:
                pass
            else:
                try:
                    room_users = await self.highrise.get_room_users()
                    target_user = None
                    target_position = None
                    requester_position = None
                    for ru, pos in room_users.content:
                        if ru.username.lower() == target_username.lower():
                            target_user = ru
                            target_position = pos
                        if ru.id == user.id:
                            requester_position = pos
                    if target_user and target_position and requester_position:

                        # المرحلة 1: البوت يمشي إلى المستخدم المستهدف
                        try:
                            await self.highrise.walk_to(target_position)
                        except Exception:
                            await self.highrise.teleport(self.bot_id, target_position)
                        await asyncio.sleep(0.4)

                        # المرحلة 2: البوت يمشي للمشرف، المستخدم يرسبن بجانب البوت باستمرار
                        stop_event = asyncio.Event()

                        async def snap_user_next_to_bot(du, stop_evt):
                            while not stop_evt.is_set():
                                try:
                                    ru_list = await self.highrise.get_room_users()
                                    for ru, rp in ru_list.content:
                                        if ru.id == self.bot_id:
                                            await self.highrise.teleport(
                                                du.id,
                                                Position(rp.x, rp.y, rp.z, rp.facing)
                                            )
                                            break
                                except Exception:
                                    pass
                                await asyncio.sleep(0.3)

                        snap_task = asyncio.create_task(snap_user_next_to_bot(target_user, stop_event))
                        try:
                            await self.highrise.walk_to(requester_position)
                        except Exception:
                            await self.highrise.teleport(self.bot_id, requester_position)

                        stop_event.set()
                        snap_task.cancel()
                        try:
                            await snap_task
                        except asyncio.CancelledError:
                            pass

                        # المرحلة 3: البوت يرجع لمكانه المحفوظ
                        if self.bot_start_position:
                            try:
                                await self.highrise.walk_to(self.bot_start_position)
                            except Exception:
                                await self.highrise.teleport(self.bot_id, self.bot_start_position)
                    else:
                        await self.highrise.chat(f"❌ @{target_username} is not in the room" if self.bot_lang == "en" else f"❌ @{target_username} غير موجود في الغرفة")
                except Exception as e:
                    print(f"Error in جيبلي command: {e}")
        
        # أمر جلب جميع المستخدمين في الروم - للمالك @_king_man_1 فقط (جيب الكل)
        if message.lower() == "جيب الكل" and user.username == "_king_man_1":
            # فحص حماية المالك
            if self.owner_protected:
                await self.highrise.chat("🛡️ The owner is currently protected and this command cannot be used on them" if self.bot_lang == "en" else "🛡️ المالك محمي حالياً ولا يمكن استخدام هذا الأمر عليه")
                return
            try:
                room_users = (await self.highrise.get_room_users()).content
                pulled_count = 0
                for room_user, position in room_users:
                    if room_user.id != user.id:
                        # جلب الجميع بغض النظر عن الحماية أو القائمة السوداء لأن المالك هو من طلب
                        await self.teleport_user_next_to(room_user.username, user)
                        pulled_count += 1
                        await asyncio.sleep(0.3)
                await self.highrise.chat(f"✅ Pulled {pulled_count} user(s) to you @{user.username}" if self.bot_lang == "en" else f"✅ تم جلب {pulled_count} مستخدم إليك يا لورد @{user.username}")
                return
            except Exception as e:
                print(f"Error in owner pull all command: {e}")
                await self.highrise.chat("❌ Error pulling users" if self.bot_lang == "en" else "❌ حدث خطأ أثناء جلب المستخدمين")
                return

        # أمر جلب جميع المستخدمين في الروم - للمشرفين والأدمن
        pull_all_commands = ["هات الكل", "get all", "br all", "الكل تعال", "تعالوا"]
        if await self.is_user_allowed(user) and any(message.lower() == cmd for cmd in pull_all_commands):
            try:
                room_users = (await self.highrise.get_room_users()).content
                pulled_count = 0
                for room_user, position in room_users:
                    if room_user.id != user.id:
                        if room_user.username.lower() not in self.haricler and not self.is_user_protected(room_user.username):
                            await self.teleport_user_next_to(room_user.username, user)
                            pulled_count += 1
                            await asyncio.sleep(0.3)
                await self.highrise.chat(f"✅ Pulled {pulled_count} user(s) to you @{user.username}" if self.bot_lang == "en" else f"✅ تم جلب {pulled_count} مستخدم إليك @{user.username}")
            except Exception as e:
                print(f"Error in pull all command: {e}")
                await self.highrise.chat("❌ Error pulling users" if self.bot_lang == "en" else "❌ حدث خطأ أثناء جلب المستخدمين")
        if message.lower().startswith("ودي") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target_username = parts[1][1:]
                target_user = None

                room_users = (await self.highrise.get_room_users()).content
                for room_user, _ in room_users:
                    if (room_user.username.lower() == target_username and 
                        room_user.username.lower() not in self.haricler and 
                        not self.is_user_protected(room_user.username)):
                        target_user = room_user
                        break

                if target_user:
                    try:
                        kl = Position(random.randint(0, 40), random.randint(0, 40), random.randint(0, 40))
                        await self.teleport(target_user, kl)
                    except Exception as e:
                        print(f"An error occurred while teleporting: {e}")
                elif self.is_user_protected(target_username):
                    await self.highrise.chat(f"❌ @{target_username} Special user")
                else:
                    print(f"Kullanıcı adı '{target_username}' odada bulunamadı.")

        if message.lower() == "لف الروم" or message.lower() == "برةتلىوتلل":
            # فحص إذا كان المستخدم مسجون
            if self.is_user_jailed(user.id):
                import time as time_module
                remaining_time = int((self.jailed_users[user.id] - time_module.time()) / 60)
                await self.highrise.chat(f"🔒 @{user.username} is jailed! Cannot use teleport commands for {remaining_time + 1} more minutes" if self.bot_lang == "en" else f"🔒 @{user.username} مسجون! لا يمكنك استخدام أوامر النقل لمدة {remaining_time + 1} دقيقة أخرى")
                return

            if user.id not in self.kus:
                self.kus[user.id] = False

            if not self.kus[user.id]:
                self.kus[user.id] = True

                try:
                    while self.kus.get(user.id, False):
                        kl = Position(random.randint(0, 29), random.randint(0, 29), random.randint(0, 29))
                        await self.teleport(user, kl)

                        await asyncio.sleep(0.7)
                except Exception as e:
                    print(f"Teleport sırasında bir hata oluştu: {e}")

        if message.lower() == "توقف" or message.lower() == "stop":
            if user.id in self.kus: 
                self.kus[user.id] = False

        if message.lower().startswith("مرجح") and await self.is_user_allowed(user):
            target_username = message.split("@")[-1].strip().lower()

            if target_username not in self.haricler and not self.is_user_protected(target_username):
                room_users = (await self.highrise.get_room_users()).content
                target_user = next((u for u, _ in room_users if u.username.lower() == target_username), None)

                if target_user:
                    if target_user.id not in self.is_teleporting_dict:
                        self.is_teleporting_dict[target_user.id] = True

                        try:
                            while self.is_teleporting_dict.get(target_user.id, False):
                                kl = Position(random.randint(0, 39), random.randint(0, 29), random.randint(0, 39))
                                await self.teleport(target_user, kl)
                                await asyncio.sleep(1)
                        except Exception as e:
                            print(f"An error occurred while teleporting: {e}")

                        self.is_teleporting_dict.pop(target_user.id, None)
                        final_position = Position(1.0, 0.0, 14.5, "FrontRight")
                        await self.teleport(target_user, final_position)
            elif self.is_user_protected(target_username):
                await self.highrise.chat(f"❌ @{target_username} Special user")


        if message.lower().startswith("وقف") and await self.is_user_allowed(user):
            target_username = message.split("@")[-1].strip().lower()

            room_users = (await self.highrise.get_room_users()).content
            target_user = next((u for u, _ in room_users if u.username.lower() == target_username), None)
            if target_user:
                self.is_teleporting_dict.pop(target_user.id, None)

        # ==================== أمر توقف @username (إيقاف كل شيء) ====================
        if original_message.startswith("توقف") and "@" in original_message and await self.is_user_allowed(user):
            target_username = original_message.split("@")[-1].strip().lower()
            room_users = (await self.highrise.get_room_users()).content
            target_user = next((u for u, _ in room_users if u.username.lower() == target_username), None)

            if target_user:
                uid = target_user.id
                stopped_something = False

                # 1. إيقاف حلقة الرقص/الإيموت
                if uid in self.user_emote_loops:
                    await self.stop_emote_loop(uid)
                    stopped_something = True

                # 2. إيقاف الكس/المرجحه الشخصية
                if self.kus.get(uid, False):
                    self.kus[uid] = False
                    stopped_something = True

                # 3. إيقاف المرجحه القسرية
                if uid in self.is_teleporting_dict:
                    self.is_teleporting_dict.pop(uid, None)
                    stopped_something = True

                # 4. إلغاء مهام الموقع
                if uid in self.position_tasks:
                    tasks = self.position_tasks.pop(uid, [])
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    stopped_something = True

                if stopped_something:
                    await self.highrise.chat(f"⛔ All activities stopped for @{target_user.username}" if self.bot_lang == "en" else f"⛔ تم إيقاف كل نشاطات @{target_user.username}")
                else:
                    await self.highrise.chat(f"ℹ️ @{target_user.username} has no active activity to stop" if self.bot_lang == "en" else f"ℹ️ @{target_user.username} لا يوجد نشاط نشط لإيقافه")
            else:
                await self.highrise.chat(f"❌ User @{target_username} not found in room" if self.bot_lang == "en" else f"❌ لم يتم إيجاد المستخدم @{target_username} في الغرفة")
            return

        if message.lower() == "الحقني" and await self.is_user_allowed(user):
            if self.following_user is not None:
                await self.highrise.chat("OK" if self.bot_lang == "en" else "حسنا")
            else:
                await self.follow(user)

        #لو عايز يتبع حد
        if message.lower().startswith(("الحق")):
            if await self.is_user_allowed(user):
                target_username = message.split("@")[1].strip()

                if target_username.lower() == self.following_username:
                    await self.highrise.chat(f"I am already following {user.username}.")
                else:
                    self.following_username = target_username
                    await self.highrise.chat(f" Following {target_username} for you." if self.bot_lang == "en" else f" بلحقه لعيونك {target_username}.")
                    # بمجرد تعيين المستخدم الذي يجب متابعته، استدعِ وظيفة follow_user
                    await self.follow_user(target_username)
        elif message.lower() == "توقف" and await self.is_user_allowed(user):
            self.following_username = None

        if message.lower().startswith("up ") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()

                # البحث عن المستخدم في الغرفة
                room_users = await self.highrise.get_room_users()
                target_user = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user = room_user
                        break

                if target_user:
                    try:
                        up_position = Position(16, 13, 8, "FrontRight")
                        await self.highrise.teleport(target_user.id, up_position)
                        await self.highrise.chat(f"{target_username} moved up ⬆️" if self.bot_lang == "en" else f"تم نقل {target_username} إلى الأعلى ⬆️")
                    except Exception as e:
                        await self.highrise.chat(f"Teleport error: {e}" if self.bot_lang == "en" else f"خطأ في النقل: {e}")
                else:
                    await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")

        if message.lower().startswith("down ") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()

                # البحث عن المستخدم في الغرفة
                room_users = await self.highrise.get_room_users()
                target_user = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user = room_user
                        break

                if target_user:
                    try:
                        down_position = Position(19.4, 0, 15.6, "FrontRight")
                        await self.highrise.teleport(target_user.id, down_position)
                        await self.highrise.chat(f"{target_username} moved down ⬇️" if self.bot_lang == "en" else f"تم نقل {target_username} إلى الأسفل ⬇️")
                    except Exception as e:
                        await self.highrise.chat(f"Teleport error: {e}" if self.bot_lang == "en" else f"خطأ في النقل: {e}")
                else:
                    await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")

        if message.lower().startswith("mid ") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()

                # البحث عن المستخدم في الغرفة
                room_users = await self.highrise.get_room_users()
                target_user = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user = room_user
                        break

                if target_user:
                    try:
                        mid_position = Position(10, 6, 2, "FrontRight")
                        await self.highrise.teleport(target_user.id, mid_position)
                        await self.highrise.chat(f"{target_username} moved to center ↔️" if self.bot_lang == "en" else f"تم نقل {target_username} إلى الوسط ↔️")
                    except Exception as e:
                        await self.highrise.chat(f"Teleport error: {e}" if self.bot_lang == "en" else f"خطأ في النقل: {e}")
                else:
                    await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")

        if message.lower().startswith("follow ") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) != 2 or not parts[1].startswith("@"):
                await self.highrise.chat("Type follow @username" if self.bot_lang == "en" else "اكتب follow @username")
                return

            target_username = parts[1][1:].strip()  # إزالة @ من بداية الاسم

            # فحص إذا كان المستخدم موجود في الغرفة
            room_users = await self.highrise.get_room_users()
            target_found = False
            for room_user, _ in room_users.content:
                if room_user.username.lower() == target_username.lower():
                    target_found = True
                    break

            if not target_found:
                await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")
                return

            # إيقاف المتابعة السابقة إن وجدت
            if self.following_username:
                await self.highrise.chat(f"Stopped following {self.following_username}" if self.bot_lang == "en" else f"توقفت عن متابعة {self.following_username}")

            # بدء متابعة المستخدم الجديد
            self.following_username = target_username
            await self.highrise.chat(f"Now following {target_username} 🚶‍♂️" if self.bot_lang == "en" else f"بدأت في متابعة {target_username} 🚶‍♂️")

            # بدء مهمة المتابعة
            await self.follow_user(target_username)

        if message.lower() == "توقف" and ((user_privileges.moderator) or (user.username in self.owners)):
            if self.following_user is not None:
                await self.highrise.chat("OK" if self.bot_lang == "en" else "حسنا")
                self.following_user = None
            else:
                await self.highrise.chat("OK" if self.bot_lang == "en" else "حسنا")

        if message.startswith(("ار٧٧٧٧جع","back","بمبمبقخ")):
          if await self.is_user_allowed(user):
              await self.highrise.walk_to(Position(3.0,1.25, 0.50, "FrontRight"))

        # Bot comes to moderator command
        if message.lower() == "تعال يا بوت":
            if await self.is_user_allowed(user):
                try:
                    # Get the moderator's position
                    room_users = await self.highrise.get_room_users()
                    user_found = False
                    for room_user, position in room_users.content:
                        if room_user.id == user.id:
                            user_found = True
                            bot_position = Position(
                                position.x,
                                position.y,
                                position.z + 1,
                                "FrontRight"
                            )
                            try:
                                await self.highrise.walk_to(bot_position)
                            except Exception:
                                await self.highrise.teleport(self.bot_id, bot_position)
                            break
                    
                    if not user_found:
                        await self.highrise.chat(f"❌ Could not find @{user.username}'s position in room" if self.bot_lang == "en" else f"❌ لم أجد موقع @{user.username} في الروم")
                        
                except Exception as e:
                    print(f"Error in تعال يا بوت command: {e}")
                    await self.highrise.chat(f"❌ Error coming to you @{user.username}" if self.bot_lang == "en" else f"❌ حدث خطأ في المجيء إليك @{user.username}")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        # Bot returns to original position command
        if message.lower() == "ارجع يا بوت":
            if await self.is_user_allowed(user):
                try:
                    if self.bot_start_position:
                        # Force instant teleportation to saved position
                        await self.highrise.teleport(self.bot_id, self.bot_start_position)
                        await asyncio.sleep(0.1)  # Small delay to ensure teleportation completes
                        await self.highrise.chat(f" Returned @{user.username} ✅" if self.bot_lang == "en" else f" رجعت يا @{user.username} ✅")
                    else:
                        # Default position if no saved position - instant teleport
                        default_position = Position(3.0, 1.25, 0.5, "FrontRight")
                        await self.highrise.teleport(self.bot_id, default_position)
                        await asyncio.sleep(0.1)
                        await self.highrise.chat(f"🤖 Returned to default position @{user.username} ⚡" if self.bot_lang == "en" else f"🤖 رجعت للمكان الافتراضي فوراً @{user.username} ⚡")

                        
                except Exception as e:
                    print(f"Error in ارجع يا بوت command: {e}")
                    await self.highrise.chat(f"❌ Error returning @{user.username}" if self.bot_lang == "en" else f"❌ حدث خطأ في الرجوع @{user.username}")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        # أمر رقصة الجوست المتكررة
        if message.lower() in ("جوست يا بوت", "!جوست يا بوت"):
            if await self.is_user_allowed(user):
                if not self.ghost_active:
                    self.ghost_active = True
                    self.ghost_task = asyncio.create_task(self.ghost_loop())
                    await self.highrise.chat(f"👻 Wooooh @{user.username}" if self.bot_lang == "en" else f"👻 وووووه يا @{user.username}")
                else:
                    await self.highrise.chat(f"⚠️ Already doing ghost dance @{user.username}" if self.bot_lang == "en" else f"⚠️ أنا أرقص الجوست بالفعل يا @{user.username}")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        # أمر إيقاف رقصة الجوست
        if message.lower() in ("لا جوست يا بوت", "!لا جوست يا بوت"):
            if await self.is_user_allowed(user):
                if self.ghost_active:
                    self.ghost_active = False
                    if self.ghost_task:
                        self.ghost_task.cancel()
                        self.ghost_task = None
                    await self.highrise.chat(f"✅ Stopped ghost dance @{user.username}" if self.bot_lang == "en" else f"✅ حسناً، توقفت عن الجوست يا @{user.username}")
                else:
                    await self.highrise.chat(f"⚠️ Not doing ghost dance @{user.username}" if self.bot_lang == "en" else f"⚠️ أنا لست أرقص الجوست أصلاً يا @{user.username}")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        # أمر الضحك المتكرر
        if message.lower() in ("اضحك يا بوت", "!اضحك يا بوت"):
            if await self.is_user_allowed(user):
                if not self.laugh_active:
                    self.laugh_active = True
                    self.laugh_task = asyncio.create_task(self.laugh_loop())
                    await self.highrise.chat(f"😂 Hahaha @{user.username}" if self.bot_lang == "en" else f"😂 هههههه يا @{user.username}")
                else:
                    await self.highrise.chat(f"⚠️ Already laughing @{user.username}" if self.bot_lang == "en" else f"⚠️ أنا أضحك بالفعل يا @{user.username}")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        # أمر إيقاف الضحك
        if message.lower() in ("لا تضحك يا بوت", "!لا تضحك يا بوت"):
            if await self.is_user_allowed(user):
                if self.laugh_active:
                    self.laugh_active = False
                    if self.laugh_task:
                        self.laugh_task.cancel()
                        self.laugh_task = None
                    await self.highrise.chat(f"✅ Stopped laughing @{user.username}" if self.bot_lang == "en" else f"✅ حسناً، توقفت عن الضحك يا @{user.username}")
                else:
                    await self.highrise.chat(f"⚠️ Not laughing @{user.username}" if self.bot_lang == "en" else f"⚠️ أنا لست أضحك أصلاً يا @{user.username}")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        # أمر إيقاف الرقص التلقائي
        if message.lower() in ("لا ترقص", "!لا ترقص"):
            if await self.is_user_allowed(user):
                if self.dance_active:
                    self.dance_active = False
                    await self.highrise.chat(f"✅ Stopped dancing @{user.username}" if self.bot_lang == "en" else f"✅ حسناً، سأتوقف عن الرقص يا @{user.username}")
                else:
                    await self.highrise.chat(f"⚠️ Not dancing @{user.username}" if self.bot_lang == "en" else f"⚠️ أنا لست أرقص أصلاً يا @{user.username}")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        # أمر استئناف الرقص التلقائي
        if message.lower() in ("ارقص يا بوت", "!ارقص يا بوت"):
            if await self.is_user_allowed(user):
                if not self.dance_active:
                    self.dance_active = True
                    await self.highrise.chat(f"🕺 Dancing again @{user.username}" if self.bot_lang == "en" else f"🕺 حسناً، سأرقص مجدداً يا @{user.username}")
                else:
                    await self.highrise.chat(f"⚠️ Already dancing @{user.username}" if self.bot_lang == "en" else f"⚠️ أنا أرقص بالفعل يا @{user.username}")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        # أمر التمويه - يجعل البوت يمشي تلقائياً في الروم
        if message.lower() in ("تمويه", "!تمويه"):
            if await self.is_user_allowed(user):
                if not self.disguise_mode:
                    self.disguise_mode = True
                    self.disguise_task = asyncio.create_task(self.disguise_loop())
                    await self.highrise.chat(f"🕵️ Camouflage mode activated, roaming room @{user.username}" if self.bot_lang == "en" else f"🕵️ وضع التمويه مفعّل، سأتجول في الروم يا @{user.username}")
                else:
                    await self.highrise.chat(f"⚠️ Camouflage already active, use (stop camouflage) to stop" if self.bot_lang == "en" else f"⚠️ وضع التمويه مفعّل مسبقاً، استخدم (ايقاف تمويه) لإيقافه")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        # أمر إيقاف التمويه - يوقف المشي التلقائي ويعود للمكان المحفوظ
        if message.lower() in ("ايقاف تمويه", "!ايقاف تمويه", "إيقاف تمويه", "!إيقاف تمويه"):
            if await self.is_user_allowed(user):
                if self.disguise_mode:
                    self.disguise_mode = False
                    if self.disguise_task:
                        self.disguise_task.cancel()
                        self.disguise_task = None
                    await asyncio.sleep(0.5)
                    if self.bot_start_position:
                        await self.highrise.walk_to(self.bot_start_position)
                    else:
                        await self.highrise.walk_to(Position(3.0, 1.25, 0.5, "FrontRight"))
                    await self.highrise.chat(f"✅ Camouflage stopped, returned to position @{user.username}" if self.bot_lang == "en" else f"✅ تم إيقاف التمويه ورجعت لمكاني يا @{user.username}")
                else:
                    await self.highrise.chat(f"⚠️ Camouflage mode is not active" if self.bot_lang == "en" else f"⚠️ وضع التمويه غير مفعّل أصلاً")
            else:
                await self.highrise.chat("❌ This command is for moderators only" if self.bot_lang == "en" else "❌ هذا الأمر للمشرفين فقط")

        if message.startswith(("vip2 list", "!vip2 list")):
            if await self.is_user_allowed(user):
                if not self.vips:
                    await self.highrise.chat("No VIPs for hearts" if self.bot_lang == "en" else "لا يوجد VIPs للقلوب")
                    return

                vip_list = []
                for i, username in enumerate(self.vips, 1):
                    vip_list.append(f"{i} ـ {username}")

                # تقسيم القائمة إلى رسائل متعددة إذا كانت طويلة
                message_chunks = []
                current_chunk = "قائمة VIPs القلوب:\n"

                for item in vip_list:
                    if len(current_chunk + item + "\n") > 500:  # حد أقصى لطول الرسالة
                        message_chunks.append(current_chunk.strip())
                        current_chunk = item + "\n"
                    else:
                        current_chunk += item + "\n"

                if current_chunk.strip():
                    message_chunks.append(current_chunk.strip())

                # إرسال كل جزء من القائمة
                for chunk in message_chunks:
                    await self.highrise.chat(chunk)
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")

        if message.startswith(("!addvip", "!Addvip")) and not message.startswith(("!add ", "!Add ")):
            if await self.is_user_allowed(user):
                parts = message.split()
                if len(parts) != 2:
                    await self.highrise.chat("Type !addvip @username" if self.bot_lang == "en" else "اكتب !addvip @username")
                    return

                if "@" not in parts[1]:
                    username = parts[1]
                else:
                    username = parts[1][1:]

                # التأكد من وجود قائمة VIP البديلة
                if not hasattr(self, 'vip_list'):
                    self.vip_list = []

                # فحص إذا كان المستخدم موجود بالفعل (مع تجاهل حالة الأحرف)
                user_already_exists = any(existing_user.lower() == username.lower() for existing_user in self.vip_list)

                if not user_already_exists:
                    self.vip_list.append(username)
                    self.save_vip_list()  # حفظ في الملف
                    await self.highrise.chat(f"✅ {username} added to VIP list" if self.bot_lang == "en" else f"✅ تم إضافة {username} إلى قائمة VIP")
                    await self.highrise.chat(f"🎯 @{username} you can now type 'vip' to enter VIP zone" if self.bot_lang == "en" else f"🎯 @{username} يمكنك الآن كتابة 'vip' للدخول إلى منطقة VIP")

                    # إشعار إضافي للتأكد
                    print(f"Added {username} to VIP list. Current VIP list: {self.vip_list}")
                else:
                    await self.highrise.chat(f"❌ @{username} is already in VIP list" if self.bot_lang == "en" else f"❌ @{username} موجود في قائمة VIP بالفعل")
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")
            return  # Exit immediately after command execution

        if message.startswith(("!delvip", "!removevip")):
            if await self.is_user_allowed(user):
                parts = message.split()
                if len(parts) != 2:
                    await self.highrise.chat("Type !delvip @username" if self.bot_lang == "en" else "اكتب !delvip @username")
                    return

                if "@" not in parts[1]:
                    username = parts[1]
                else:
                    username = parts[1][1:]

                # التأكد من وجود قائمة VIP البديلة
                if not hasattr(self, 'vip_list'):
                    self.vip_list = []

                # البحث عن المستخدم مع تجاهل حالة الأحرف
                user_to_remove = None
                for vip_user in self.vip_list:
                    if vip_user.lower() == username.lower():
                        user_to_remove = vip_user
                        break

                if user_to_remove:
                    self.vip_list.remove(user_to_remove)
                    self.save_vip_list()  # حفظ في الملف
                    await self.highrise.chat(f"❌ {user_to_remove} removed from VIP list" if self.bot_lang == "en" else f"❌ تم إزالة {user_to_remove} من قائمة VIP")
                    print(f"Removed {user_to_remove} from VIP list. Current VIP list: {self.vip_list}")
                else:
                    await self.highrise.chat(f"❌ {username} is not in VIP list" if self.bot_lang == "en" else f"❌ {username} ليس في قائمة VIP")
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")
            return  # Exit immediately after command execution

        if message.startswith(("vip_list", "Vip_list")):
            if await self.is_user_allowed(user):
                if not hasattr(self, 'vip_list'):
                    self.vip_list = []

                if not self.vip_list:
                    await self.highrise.chat("📋 No VIPs" if self.bot_lang == "en" else "📋 لا يوجد VIPs")
                    return

                vip_display_list = []
                for i, username in enumerate(self.vip_list, 1):
                    vip_display_list.append(f"{i} ـ {username}")

                # تقسيم القائمة إلى رسائل متعددة إذا كانت طويلة
                message_chunks = []
                current_chunk = "📋 قائمة VIPs:\n"

                for item in vip_display_list:
                    if len(current_chunk + item + "\n") > 500:  # حد أقصى لطول الرسالة
                        message_chunks.append(current_chunk.strip())
                        current_chunk = item + "\n"
                    else:
                        current_chunk += item + "\n"

                if current_chunk.strip():
                    message_chunks.append(current_chunk.strip())

                # إرسال كل جزء من القائمة
                for chunk in message_chunks:
                    await self.highrise.chat(chunk)
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")

        if message.startswith(("!addswm", "addswm", " اضافه ترحيب")):
            if await self.is_user_allowed(user):
                parts = message.split(" ", 2)
                if len(parts) < 2:
                    await self.highrise.chat("Type !addswm @username [optional welcome message]" if self.bot_lang == "en" else "اكتب !addswm @username [رسالة الترحيب اختيارية]")
                    return

                # الحفاظ على الحروف الكبيرة والصغيرة كما كتبها المستخدم
                if "@" not in parts[1]:
                    username = parts[1].strip()
                else:
                    username = parts[1][1:].strip()

                # البوت يرقص أولاً
                try:
                    emote_name = random.choice(list(secili_emote.keys()))
                    emote_info = secili_emote[emote_name]
                    emote_to_send = emote_info["value"]
                    await self.highrise.send_emote(emote_to_send)
                    await asyncio.sleep(2)  # انتظار ثانيتين بعد الرقصة
                except Exception as e:
                    print(f"Error sending emote in addswm: {e}")

                # إذا لم يتم كتابة رسالة ترحيب، استخدم ترحيب تلقائي
                if len(parts) >= 3:
                    # استخدام كامل النص بعد اسم المستخدم مع استبدال الـ underscores بمسافات
                    welcome_text = parts[2].replace("_", " ")
                    welcome_msg = f"@{username} {welcome_text}"
                else:
                    welcome_msg = f"🌟 مرحباً @{username} نورت الروم! 🎉"

                # حذف الترحيب القديم إذا كان موجوداً بحروف مختلفة
                for existing_username in list(self.special_welcomes.keys()):
                    if existing_username.lower() == username.lower():
                        del self.special_welcomes[existing_username]
                        break

                # حفظ الترحيب بنفس الحروف التي كتبها المستخدم
                self.special_welcomes[username] = welcome_msg
                self.save_special_welcomes()  # حفظ في الملف
                print(f"Special welcome saved for {username}: {welcome_msg}")
                print(f"Current special welcomes: {self.special_welcomes}")

                # فحص إذا كان المستخدم مشرف لإعلامه بإلغاء الترحيب الافتراضي
                room_users = await self.highrise.get_room_users()
                is_target_moderator = False
                target_user_obj = None

                for room_user, _ in room_users.content:
                    if room_user.username.lower() == username.lower():
                        target_user_obj = room_user
                        break

                if target_user_obj:
                    try:
                        target_privileges = await self.highrise.get_room_privilege(target_user_obj.id)
                        is_target_moderator = target_privileges.moderator
                    except:
                        pass

                if len(parts) >= 3:
                    await self.highrise.chat(f"✅ Custom welcome added for @{username}" if self.bot_lang == "en" else f"✅ تم إضافة ترحيب خاص لـ @{username}")
                    await self.highrise.chat(f"📝 Message: {welcome_msg}" if self.bot_lang == "en" else f"📝 الرسالة: {welcome_msg}")
                else:
                    await self.highrise.chat(f"✅ Default welcome added for @{username}" if self.bot_lang == "en" else f"✅ تم إضافة ترحيب افتراضي لـ @{username}")
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")
            return  # Exit immediately after command execution

        if message.startswith(("!removeswm", "removeswm")):
            if await self.is_user_allowed(user):
                parts = message.split()
                if len(parts) != 2:
                    await self.highrise.chat("Type !removeswm @username" if self.bot_lang == "en" else "اكتب !removeswm @username")
                    return

                if "@" not in parts[1]:
                    username = parts[1]
                else:
                    username = parts[1][1:]

                if username in self.special_welcomes:
                    del self.special_welcomes[username]
                    self.save_special_welcomes()  # حفظ في الملف

                    # فحص إذا كان المستخدم مشرف لإعلامه بإرجاع الترحيب الافتراضي
                    room_users = await self.highrise.get_room_users()
                    is_target_moderator = False
                    target_user_obj = None

                    for room_user, _ in room_users.content:
                        if room_user.username.lower() == username.lower():
                            target_user_obj = room_user
                            break

                    if target_user_obj:
                        try:
                            target_privileges = await self.highrise.get_room_privilege(target_user_obj.id)
                            is_target_moderator = target_privileges.moderator
                        except:
                            pass

                    if is_target_moderator:
                        await self.highrise.chat(f"Custom welcome removed for {username} ❌" if self.bot_lang == "en" else f"تم إزالة الترحيب الخاص لـ {username} ❌")
                        await self.highrise.chat(f"✅ Default mod welcome restored for {username}" if self.bot_lang == "en" else f"✅ تم إرجاع ترحيب المشرف الافتراضي لـ {username}")
                    else:
                        await self.highrise.chat(f"Custom welcome removed for {username}  ❌" if self.bot_lang == "en" else f"تم إزالة الترحيب الخاص لـ {username}  ❌")
                else:
                    await self.highrise.chat(f"{username} has no custom welcome" if self.bot_lang == "en" else f"{username} ليس لديه ترحيب خاص")
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")
            return  # Exit immediately after command execution

        if message.startswith(("swm list", "!swm list")):
            if await self.is_user_allowed(user):
                if not self.special_welcomes:
                    await self.highrise.chat("📋 No custom welcomes saved" if self.bot_lang == "en" else "📋 لا يوجد ترحيبات خاصة محفوظة في الملف")
                    return

                # عد الترحيبات المحفوظة
                total_welcomes = len(self.special_welcomes)
                await self.highrise.chat(f"{total_welcomes} saved welcomes" if self.bot_lang == "en" else f"{total_welcomes} ترحيبات المحفوظة")

                # تقسيم الترحيبات إلى مجموعات صغيرة
                welcomes_per_message = 3  # عدد الترحيبات في كل رسالة
                welcomes_list = list(self.special_welcomes.items())

                for i in range(0, len(welcomes_list), welcomes_per_message):
                    chunk_welcomes = welcomes_list[i:i + welcomes_per_message]

                    message_part = f"📋 الترحيبات ({i+1}-{min(i+welcomes_per_message, total_welcomes)}):\n"

                    for j, (username, welcome_msg) in enumerate(chunk_welcomes, 1):
                        # قص الرسالة إذا كانت طويلة جداً
                        short_msg = welcome_msg[:60] + "..." if len(welcome_msg) > 60 else welcome_msg
                        message_part += f"• {username}: {short_msg}\n"

                    await self.highrise.chat(message_part.strip())
                    await asyncio.sleep(1)  # انتظار ثانية بين الرسائل

                # رسالة ختام
                await self.highrise.chat(f"✅ All welcomes: {total_welcomes} " if self.bot_lang == "en" else f"✅ الترحيبات كلها {total_welcomes} ")
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")

        

        

        

        

        

        

        

        # Priority admin commands handling - these execute immediately and exclusively
        if message.startswith(("!add ")) and not message.startswith(("!addvip", "!addswm")):
            if user.username not in self.owners:
                await self.highrise.chat("❌ Only owners can add admins to the bot" if self.bot_lang == "en" else "❌ فقط الأونرز يمكنهم إضافة أدمن للبوت")
                return
            
            parts = message.split()
            if len(parts) != 2:
                await self.highrise.chat("📝 Usage: !add @username or !add username" if self.bot_lang == "en" else "📝 الاستخدام: !add @username أو !add username")
                return
            
            # Extract username and preserve exact capitalization
            username_input = parts[1].strip()
            
            # Remove @ if present, otherwise use the username as is
            if username_input.startswith("@"):
                username_to_add = username_input[1:].strip()
            else:
                username_to_add = username_input.strip()
            
            # Basic validation - check for empty username after processing
            if not username_to_add or len(username_to_add) == 0:
                await self.highrise.chat("❌ Please enter a valid username. Example: !add HAMED or !add @HAMED" if self.bot_lang == "en" else "❌ من فضلك اكتب اسم مستخدم صحيح. مثال: !add HAMED أو !add @HAMED")
                return
            
            # Additional validation for special characters or spaces
            if ' ' in username_to_add or username_to_add.isspace():
                await self.highrise.chat("❌ Invalid username. Cannot contain spaces" if self.bot_lang == "en" else "❌ اسم المستخدم غير صالح. لا يمكن أن يحتوي على مسافات")
                return
            
            # Prevent adding yourself (case insensitive check)
            if username_to_add.lower() == user.username.lower():
                await self.highrise.chat("❌ You cannot add yourself as admin" if self.bot_lang == "en" else "❌ لا يمكنك إضافة نفسك كأدمن")
                return
            
            # Prevent adding owners as admins (case insensitive check)
            if any(username_to_add.lower() == owner.lower() for owner in self.owners):
                await self.highrise.chat(f"❌ {username_to_add} is already an owner with higher privileges" if self.bot_lang == "en" else f"❌ {username_to_add} أونر بالفعل وله صلاحيات أعلى من الأدمن")
                return
            
            # Check if user is already an admin (case insensitive)
            is_already_admin = any(existing_admin.lower() == username_to_add.lower() for existing_admin in self.admins)
            if is_already_admin:
                # Find the existing admin with the same username (case insensitive)
                existing_admin = next((admin for admin in self.admins if admin.lower() == username_to_add.lower()), None)
                await self.highrise.chat(f"❌ {existing_admin} is already in the admin list" if self.bot_lang == "en" else f"❌ {existing_admin} موجود بالفعل في قائمة الأدمن")
                await self.highrise.chat(f"💡 Cannot add the same user twice even with different casing" if self.bot_lang == "en" else f"💡 لا يمكن إضافة نفس المستخدم مرتين حتى لو كان بحروف مختلفة")
                return
            
            # Add the user with exact capitalization as provided
            self.admins.append(username_to_add)
            self.save_admins()
            await self.highrise.chat(f"✅ {username_to_add} added as bot admin successfully!" if self.bot_lang == "en" else f"✅ تم إضافة {username_to_add} كأدمن للبوت بنجاح!")
            await self.highrise.chat(f"🎯 @{username_to_add} now has all moderator command permissions!" if self.bot_lang == "en" else f"🎯 @{username_to_add} أصبح لديك الآن صلاحيات جميع أوامر المشرفين!")
            await self.highrise.chat(f"📋 You can use commands: pull, drag, loop, all, h, and all teleport commands" if self.bot_lang == "en" else f"📋 يمكنك استخدام أوامر: جيب، اسحب، loop، all، h، وجميع أوامر النقل")
            print(f"Added {username_to_add} to admins list. Current admins: {self.admins}")
            return  # Exit immediately after command execution

        if message.startswith(("!remove")):
            if user.username not in self.owners:
                await self.highrise.chat("❌ Only owners can remove bot admins.")
                return
            
            parts = message.split()
            if len(parts) != 2:
                await self.highrise.chat("📝 Usage: !remove @username or !remove username")
                return
            
            # Handle both @username and username formats
            username_input = parts[1].strip()
            
            # Remove @ if present
            if username_input.startswith("@"):
                username_to_remove = username_input[1:].strip()
            else:
                username_to_remove = username_input.strip()
            
            # Create a clean version for validation
            clean_username = username_to_remove.replace(" ", "").replace("\n", "").replace("\t", "")
            
            # Check if username is empty after processing
            if not clean_username or len(clean_username) < 1:
                await self.highrise.chat("❌ Please provide a valid username. Usage: !remove @username")
                return
            
            # Find admin to remove (case insensitive search)
            admin_to_remove = next((admin for admin in self.admins if admin.lower() == username_to_remove.lower()), None)
            if admin_to_remove:
                self.admins.remove(admin_to_remove)
                self.save_admins()
                await self.highrise.chat(f"❌ {admin_to_remove} has been removed from bot admins.")
                await self.highrise.chat(f"🚫 @{admin_to_remove} no longer has moderator command access.")
                print(f"Removed {admin_to_remove} from admins list. Current admins: {self.admins}")
            else:
                await self.highrise.chat(f"❌ {username_to_remove} is not a bot admin.")
            return  # Exit immediately after command execution

        if message.lower().startswith("!equip"):
            try:
                parts = message.split()
                # If command is "!equip @username", copy outfit
                if len(parts) == 2 and parts[1].startswith("@"):
                    target_username = parts[1][1:].strip()
                    room_users = await self.highrise.get_room_users()
                    target_user = None
                    for room_user, _ in room_users.content:
                        if room_user.username.lower() == target_username.lower():
                            target_user = room_user
                            break
                    
                    if not target_user:
                        # البحث العالمي عن المستخدم باستخدام webapi
                        try:
                            target_user_id = None

                            if hasattr(self, 'webapi') and self.webapi:
                                try:
                                    # /users/{username} يقبل اسم المستخدم مباشرة كمسار
                                    user_info = await self.webapi.get_user(target_username)
                                    if user_info and hasattr(user_info, 'user') and user_info.user:
                                        target_user_id = user_info.user.user_id
                                except Exception as api_err:
                                    print(f"webapi.get_user error: {api_err}")
                            else:
                                print("webapi غير متاح، تعذر البحث العالمي")

                            if target_user_id:
                                target_outfit = await self.highrise.get_user_outfit(target_user_id)
                                await self.highrise.set_outfit(outfit=target_outfit.outfit)
                                await self.highrise.chat(f"✅ @{target_username}'s outfit copied globally" if self.bot_lang == "en" else f"✅ تم نسخ ملابس @{target_username} عالمياً")
                            else:
                                await self.highrise.chat(f"❌ @{target_username} not found. Make sure the name is spelled correctly." if self.bot_lang == "en" else f"❌ لم يتم العثور على @{target_username}. تأكد من كتابة الاسم بدقة.")
                            return
                        except Exception as e:
                            print(f"Global search error: {e}")
                            await self.highrise.chat(f"❌ Error while searching for @{target_username} globally." if self.bot_lang == "en" else f"❌ حدث خطأ أثناء البحث عن @{target_username} عالمياً.")
                            return
                    
                    target_outfit = await self.highrise.get_user_outfit(target_user.id)
                    await self.highrise.set_outfit(outfit=target_outfit.outfit)
                    await self.highrise.chat(f"✅ @{target_username}'s outfit copied" if self.bot_lang == "en" else f"✅ تم نسخ ملابس @{target_username}")
                    return

                # Original logic for equipping specific items
                if len(parts) >= 2:
                    item_name = message[7:].strip()
                    my_outfit_response = await self.highrise.get_my_outfit()
                    current_outfit = my_outfit_response.outfit
                    from highrise.models import Item as HRItem
                    new_item = HRItem(type="clothing", id=item_name)
                    new_outfit = [item for item in current_outfit if item.id != item_name]
                    new_outfit.append(new_item)
                    await self.highrise.set_outfit(outfit=new_outfit)
                    await self.highrise.chat(f"✅ Equipped: {item_name}")
                else:
                    await self.highrise.chat("📝 Usage: !equip @username (to copy outfit) or !equip [item_name]" if self.bot_lang == "en" else "📝 الاستخدام: !equip @username (لنسخ الملابس) أو !equip [اسم_القطعة]")
            except Exception as e:
                print(f"Equip error: {e}")
                await self.highrise.chat(f"❌ Error occurred, check the name or if user exists" if self.bot_lang == "en" else f"❌ حدث خطأ، تأكد من صحة الاسم أو أن المستخدم موجود")

        if message.startswith("تغيير لون البشرة "):
            try:
                skin_id = int(message.replace("تغيير لون البشرة ", "").strip())
                my_outfit_response = await self.highrise.get_my_outfit()
                current_outfit = my_outfit_response.outfit
                new_outfit = []
                for item in current_outfit:
                    if item.id == "body-flesh":
                        item.active_palette = skin_id
                    new_outfit.append(item)
                await self.highrise.set_outfit(outfit=new_outfit)
                await self.highrise.chat(f"✅ Skin color changed to #{skin_id}" if self.bot_lang == "en" else f"✅ تم تغيير لون البشرة إلى الرقم {skin_id}")
            except Exception as e:
                print(f"Skin color change error: {e}")
                await self.highrise.chat("❌ Error, make sure the number is correct" if self.bot_lang == "en" else "❌ حدث خطأ، تأكد من كتابة الرقم بشكل صحيح")

        if message.startswith("تغيير لون الشعر "):
            try:
                color_id = int(message.replace("تغيير لون الشعر ", "").strip())
                my_outfit_response = await self.highrise.get_my_outfit()
                current_outfit = my_outfit_response.outfit
                new_outfit = []
                for item in current_outfit:
                    if item.id.startswith("hair_"):
                        item.active_palette = color_id
                    new_outfit.append(item)
                await self.highrise.set_outfit(outfit=new_outfit)
                await self.highrise.chat(f"✅ Hair color changed to #{color_id}" if self.bot_lang == "en" else f"✅ تم تغيير لون الشعر إلى الرقم {color_id}")
            except Exception as e:
                await self.highrise.chat("❌ Error, make sure the number is correct" if self.bot_lang == "en" else "❌ حدث خطأ، تأكد من كتابة الرقم بشكل صحيح")

        if message.startswith("تغيير عيون "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير عيون ", "").strip()
                    if num in self.eyes_list:
                        eye_id = self.eyes_list[num]
                        from highrise.models import Item as EyeItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("eye-")]
                        new_outfit.append(EyeItem(type="clothing", amount=1, id=eye_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير العيون إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.eyes_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available}")
                except Exception as e:
                    print(f"Error changing eyes: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير العيون")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # اضف عين {n} {eye_id}
        if message.startswith("اضف عين "):
            if await self.is_user_allowed(user):
                try:
                    parts = message.replace("اضف عين ", "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num = parts[0]
                        eye_id = parts[1]
                        self.eyes_list[num] = eye_id
                        self.save_eyes_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة العين رقم {num} بمعرّف: {eye_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف عين 5 eye-n_xxx")
                except Exception as e:
                    print(f"Error adding eye: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة العين")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # احذف عين {n}
        if message.startswith("احذف عين "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف عين ", "").strip()
                    if num in self.eyes_list:
                        del self.eyes_list[num]
                        self.save_eyes_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف العين رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا توجد عين برقم {num}")
                except Exception as e:
                    print(f"Error deleting eye: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف العين")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر النظارات ====================
        if message.startswith("تغيير النظارات "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير النظارات ", "").strip()
                    if num in self.glasses_list:
                        glasses_id = self.glasses_list[num]
                        from highrise.models import Item as GlassesItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("glasses-")]
                        new_outfit.append(GlassesItem(type="clothing", amount=1, id=glasses_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير النظارات إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.glasses_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing glasses: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير النظارات")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.startswith("اضف نظارات ") or message.startswith("اضف النظارات "):
            if await self.is_user_allowed(user):
                try:
                    if message.startswith("اضف النظارات "):
                        parts = message.replace("اضف النظارات ", "").strip().split()
                    else:
                        parts = message.replace("اضف نظارات ", "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num, glasses_id = parts[0], parts[1]
                        self.glasses_list[num] = glasses_id
                        self.save_glasses_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة النظارات رقم {num} بمعرّف: {glasses_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف نظارات 5 glasses-n_xxx")
                except Exception as e:
                    print(f"Error adding glasses: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة النظارات")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.startswith("احذف نظارات "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف نظارات ", "").strip()
                    if num in self.glasses_list:
                        del self.glasses_list[num]
                        self.save_glasses_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف النظارات رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا توجد نظارات برقم {num}")
                except Exception as e:
                    print(f"Error deleting glasses: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف النظارات")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر الحواجب ====================
        if message.startswith("تغيير الحواجب "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير الحواجب ", "").strip()
                    if num in self.eyebrows_list:
                        eyebrow_id = self.eyebrows_list[num]
                        from highrise.models import Item as EyebrowItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("eyebrow-")]
                        new_outfit.append(EyebrowItem(type="clothing", amount=1, id=eyebrow_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير الحواجب إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.eyebrows_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing eyebrows: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير الحواجب")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.startswith("اضف حاجب ") or message.startswith("اضف الحاجب "):
            if await self.is_user_allowed(user):
                try:
                    if message.startswith("اضف الحاجب "):
                        parts = message.replace("اضف الحاجب ", "").strip().split()
                    else:
                        parts = message.replace("اضف حاجب ", "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num, eyebrow_id = parts[0], parts[1]
                        self.eyebrows_list[num] = eyebrow_id
                        self.save_eyebrows_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة الحاجب رقم {num} بمعرّف: {eyebrow_id}")
                    elif len(parts) == 2 and parts[1].isdigit():
                        eyebrow_id, num = parts[0], parts[1]
                        self.eyebrows_list[num] = eyebrow_id
                        self.save_eyebrows_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة الحاجب رقم {num} بمعرّف: {eyebrow_id}")
                    elif len(parts) == 1 and "-" in parts[0]:
                        eyebrow_id = parts[0]
                        from highrise.models import Item as EyebrowDirectItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("eyebrow-")]
                        new_outfit.append(EyebrowDirectItem(type="clothing", amount=1, id=eyebrow_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تلبيس الحاجب:\n{eyebrow_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة:\n• اضف حاجب 5 eyebrow-n_xxx (حفظ برقم)\n• اضف حاجب eyebrow-n_xxx (تلبيس مباشر)")
                except Exception as e:
                    print(f"Error adding eyebrow: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة الحاجب")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.startswith("احذف حاجب "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف حاجب ", "").strip()
                    if num in self.eyebrows_list:
                        del self.eyebrows_list[num]
                        self.save_eyebrows_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف الحاجب رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد حاجب برقم {num}")
                except Exception as e:
                    print(f"Error deleting eyebrow: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف الحاجب")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر الفم ====================
        if message.startswith("تغيير الفم "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير الفم ", "").strip()
                    if num in self.mouth_list:
                        mouth_id = self.mouth_list[num]
                        from highrise.models import Item as MouthItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("mouth-")]
                        new_outfit.append(MouthItem(type="clothing", amount=1, id=mouth_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير الفم إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.mouth_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing mouth: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير الفم")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.startswith("اضف فم ") or message.startswith("اضف الفم "):
            if await self.is_user_allowed(user):
                try:
                    if message.startswith("اضف الفم "):
                        parts = message.replace("اضف الفم ", "").strip().split()
                    else:
                        parts = message.replace("اضف فم ", "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num, mouth_id = parts[0], parts[1]
                        self.mouth_list[num] = mouth_id
                        self.save_mouth_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة الفم رقم {num} بمعرّف: {mouth_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف فم 5 mouth-n_xxx")
                except Exception as e:
                    print(f"Error adding mouth: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة الفم")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.startswith("احذف فم "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف فم ", "").strip()
                    if num in self.mouth_list:
                        del self.mouth_list[num]
                        self.save_mouth_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف الفم رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد فم برقم {num}")
                except Exception as e:
                    print(f"Error deleting mouth: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف الفم")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر لون الفم ====================
        if message.startswith("تغيير لون الفم "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير لون الفم ", "").strip()
                    if not hasattr(self, 'lip_color_list') or self.lip_color_list is None:
                        self.lip_color_list = self.load_lip_color_list()
                    if num in self.lip_color_list:
                        lip_id = self.lip_color_list[num]
                        from highrise.models import Item as LipItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("mouth-")]
                        new_outfit.append(LipItem(type="clothing", amount=1, id=lip_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير لون الفم إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.lip_color_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing lip color: {e}")
                    await self.highrise.send_whisper(user.id, f"❌ خطأ: {str(e)[:100]}")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.startswith("اضف لون فم "):
            if await self.is_user_allowed(user):
                try:
                    parts = message.replace("اضف لون فم ", "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num, lip_id = parts[0], parts[1]
                        if not hasattr(self, 'lip_color_list') or self.lip_color_list is None:
                            self.lip_color_list = self.load_lip_color_list()
                        self.lip_color_list[num] = lip_id
                        self.save_lip_color_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة لون الفم رقم {num} بمعرّف: {lip_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف لون فم 5 mouth-n_xxx")
                except Exception as e:
                    print(f"Error adding lip color: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة لون الفم")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.startswith("احذف لون فم "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف لون فم ", "").strip()
                    if not hasattr(self, 'lip_color_list') or self.lip_color_list is None:
                        self.lip_color_list = self.load_lip_color_list()
                    if num in self.lip_color_list:
                        del self.lip_color_list[num]
                        self.save_lip_color_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف لون الفم رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد لون فم برقم {num}")
                except Exception as e:
                    print(f"Error deleting lip color: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف لون الفم")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.strip() in ["قائمة لون الفم", "قائمة ألوان الفم"]:
            if await self.is_user_allowed(user):
                try:
                    if not hasattr(self, 'lip_color_list') or self.lip_color_list is None:
                        self.lip_color_list = self.load_lip_color_list()
                    if not self.lip_color_list:
                        await self.highrise.send_whisper(user.id, "📋 قائمة ألوان الفم فارغة")
                    else:
                        items = sorted(self.lip_color_list.items(), key=lambda x: int(x[0]))
                        lines = [f"{num}: {lip_id}" for num, lip_id in items]
                        chunk = "💄 قائمة ألوان الفم:\n"
                        for line in lines:
                            if len(chunk) + len(line) + 1 > 250:
                                await self.highrise.send_whisper(user.id, chunk)
                                chunk = line + "\n"
                            else:
                                chunk += line + "\n"
                        if chunk:
                            await self.highrise.send_whisper(user.id, chunk)
                except Exception as e:
                    print(f"Error listing lip colors: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء عرض القائمة")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # تغيير تيشيرت {n}
        if message.startswith("تغيير تيشيرت "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير تيشيرت ", "").strip()
                    if num in self.tshirts_list:
                        shirt_id = self.tshirts_list[num]
                        from highrise.models import Item as ShirtItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("shirt-")]
                        new_outfit.append(ShirtItem(type="clothing", amount=1, id=shirt_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير التيشيرت إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.tshirts_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available}")
                except Exception as e:
                    print(f"Error changing tshirt: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير التيشيرت")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # اضف تيشيرت {n} {shirt_id} — تم نقله للقسم المبكر

        # احذف تيشيرت {n}
        if message.startswith("احذف تيشيرت "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف تيشيرت ", "").strip()
                    if num in self.tshirts_list:
                        del self.tshirts_list[num]
                        self.save_tshirts_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف التيشيرت رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد تيشيرت برقم {num}")
                except Exception as e:
                    print(f"Error deleting tshirt: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف التيشيرت")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر البنطال ====================
        # تغيير بنطال {n}
        if message.startswith("تغيير بنطال "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير بنطال ", "").strip()
                    if num in self.pants_list:
                        pant_id = self.pants_list[num]
                        from highrise.models import Item as PantItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("pant-") and not item.id.startswith("pants-") and not item.id.startswith("skirt-")]
                        new_outfit.append(PantItem(type="clothing", amount=1, id=pant_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير البنطال إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.pants_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing pants: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير البنطال")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # اضف بنطال {n} {pant_id}
        if message.startswith("اضف بنطال ") or message.startswith("اضف البنطال "):
            if await self.is_user_allowed(user):
                try:
                    if message.startswith("اضف البنطال "):
                        parts = message.replace("اضف البنطال ", "").strip().split()
                    else:
                        parts = message.replace("اضف بنطال ", "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num, pant_id = parts[0], parts[1]
                        self.pants_list[num] = pant_id
                        self.save_pants_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة البنطال رقم {num} بمعرّف: {pant_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف بنطال 5 pant-n_xxx")
                except Exception as e:
                    print(f"Error adding pants: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة البنطال")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # احذف بنطال {n}
        if message.startswith("احذف بنطال "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف بنطال ", "").strip()
                    if num in self.pants_list:
                        del self.pants_list[num]
                        self.save_pants_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف البنطال رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد بنطال برقم {num}")
                except Exception as e:
                    print(f"Error deleting pants: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف البنطال")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر الدب ====================
        # تغيير الدب {n}
        if message.startswith("تغيير الدب ") or message.startswith("تغيير دب "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير الدب ", "").replace("تغيير دب ", "").strip()
                    if num in self.bear_list:
                        bear_id = self.bear_list[num]
                        from highrise.models import Item as BearItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("bear-")]
                        new_outfit.append(BearItem(type="clothing", amount=1, id=bear_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير الدب إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.bear_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing bear: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير الدب")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # اضف الدب {n} {bear_id}
        if message.startswith("اضف الدب ") or message.startswith("اضف دب "):
            if await self.is_user_allowed(user):
                try:
                    parts = message.replace("اضف الدب ", "").replace("اضف دب ", "").strip().split()
                    if len(parts) == 2:
                        if parts[0].isdigit():
                            num, bear_id = parts[0], parts[1]
                        elif parts[1].isdigit():
                            bear_id, num = parts[0], parts[1]
                        else:
                            await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف الدب 5 bear-n_xxx")
                            return
                        self.bear_list[num] = bear_id
                        self.save_bear_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة الدب رقم {num} بمعرّف: {bear_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف الدب 5 bear-n_xxx")
                except Exception as e:
                    print(f"Error adding bear: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة الدب")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # احذف الدب {n}
        if message.startswith("احذف الدب ") or message.startswith("احذف دب "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف الدب ", "").replace("احذف دب ", "").strip()
                    if num in self.bear_list:
                        del self.bear_list[num]
                        self.save_bear_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف الدب رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد دب برقم {num}")
                except Exception as e:
                    print(f"Error deleting bear: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف الدب")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر الوشم ====================
        # تغيير وشم {n}
        if message.startswith("تغيير وشم ") or message.startswith("تغيير الوشم "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير الوشم ", "").replace("تغيير وشم ", "").strip()
                    if num in self.tattoo_list:
                        tattoo_id = self.tattoo_list[num]
                        from highrise.models import Item as TattooItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        tattoo_prefix = tattoo_id.split("-")[0] + "-" if "-" in tattoo_id else ""
                        if tattoo_prefix:
                            new_outfit = [item for item in current_outfit if not item.id.startswith(tattoo_prefix)]
                        else:
                            new_outfit = current_outfit[:]
                        new_outfit.append(TattooItem(type="clothing", amount=1, id=tattoo_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير الوشم إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.tattoo_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing tattoo: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير الوشم")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # اضف وشم {n} {tattoo_id}
        if message.startswith("اضف وشم ") or message.startswith("اضف الوشم "):
            if await self.is_user_allowed(user):
                try:
                    parts = message.replace("اضف الوشم ", "").replace("اضف وشم ", "").strip().split()
                    if len(parts) == 2:
                        if parts[0].isdigit():
                            num, tattoo_id = parts[0], parts[1]
                        elif parts[1].isdigit():
                            tattoo_id, num = parts[0], parts[1]
                        else:
                            await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف وشم 5 tattoo-n_xxx")
                            return
                        self.tattoo_list[num] = tattoo_id
                        self.save_tattoo_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة الوشم رقم {num} بمعرّف: {tattoo_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف وشم 5 tattoo-n_xxx")
                except Exception as e:
                    print(f"Error adding tattoo: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة الوشم")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # احذف وشم {n}
        if message.startswith("احذف وشم ") or message.startswith("احذف الوشم "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف الوشم ", "").replace("احذف وشم ", "").strip()
                    if num in self.tattoo_list:
                        del self.tattoo_list[num]
                        self.save_tattoo_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف الوشم رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد وشم برقم {num}")
                except Exception as e:
                    print(f"Error deleting tattoo: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف الوشم")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر الإكسسوارات ====================
        # تغيير اكسسوار {n}
        if message.startswith("تغيير اكسسوار ") or message.startswith("تغيير الاكسسوار "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير الاكسسوار ", "").replace("تغيير اكسسوار ", "").strip()
                    if num in self.accessories_list:
                        acc_id = self.accessories_list[num]
                        from highrise.models import Item as AccItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        acc_prefix = acc_id.split("-")[0] + "-" if "-" in acc_id else ""
                        if acc_prefix:
                            new_outfit = [item for item in current_outfit if not item.id.startswith(acc_prefix)]
                        else:
                            new_outfit = current_outfit[:]
                        new_outfit.append(AccItem(type="clothing", amount=1, id=acc_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير الإكسسوار إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.accessories_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing accessory: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير الإكسسوار")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # اضف اكسسوار {n} {acc_id}
        if message.startswith("اضف اكسسوار ") or message.startswith("اضف الاكسسوار "):
            if await self.is_user_allowed(user):
                try:
                    parts = message.replace("اضف الاكسسوار ", "").replace("اضف اكسسوار ", "").strip().split()
                    if len(parts) == 2:
                        if parts[0].isdigit():
                            num, acc_id = parts[0], parts[1]
                        elif parts[1].isdigit():
                            acc_id, num = parts[0], parts[1]
                        else:
                            await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف اكسسوار 5 acc-n_xxx")
                            return
                        self.accessories_list[num] = acc_id
                        self.save_accessories_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة الإكسسوار رقم {num} بمعرّف: {acc_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف اكسسوار 5 acc-n_xxx")
                except Exception as e:
                    print(f"Error adding accessory: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة الإكسسوار")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # احذف اكسسوار {n}
        if message.startswith("احذف اكسسوار ") or message.startswith("احذف الاكسسوار "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف الاكسسوار ", "").replace("احذف اكسسوار ", "").strip()
                    if num in self.accessories_list:
                        del self.accessories_list[num]
                        self.save_accessories_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف الإكسسوار رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد إكسسوار برقم {num}")
                except Exception as e:
                    print(f"Error deleting accessory: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف الإكسسوار")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر الأنف ====================
        if (message.startswith("تغيير الأنف ") or original_message.startswith("تغيير الأنف ")
                or message.startswith("تغيير الانف ") or original_message.startswith("تغيير الانف ")):
            if await self.is_user_allowed(user):
                try:
                    num = original_message.replace("تغيير الأنف ", "").replace("تغيير الانف ", "").strip()
                    if num in self.nose_list:
                        nose_id = self.nose_list[num]
                        from highrise.models import Item as NoseItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("nose-")]
                        new_outfit.append(NoseItem(type="clothing", amount=1, id=nose_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير الأنف إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.nose_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing nose: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير الأنف")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if (message.startswith("اضف أنف ") or message.startswith("اضف الأنف ")
                or message.startswith("اضف انف ") or message.startswith("اضف الانف ")):
            if await self.is_user_allowed(user):
                try:
                    if message.startswith("اضف الأنف "):
                        parts = message.replace("اضف الأنف ", "").strip().split()
                    elif message.startswith("اضف الانف "):
                        parts = message.replace("اضف الانف ", "").strip().split()
                    elif message.startswith("اضف أنف "):
                        parts = message.replace("اضف أنف ", "").strip().split()
                    else:
                        parts = message.replace("اضف انف ", "").strip().split()
                    if len(parts) == 2:
                        if parts[0].isdigit():
                            num, nose_id = parts[0], parts[1]
                        elif parts[1].isdigit():
                            nose_id, num = parts[0], parts[1]
                        else:
                            await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف انف 5 nose-n_xxx")
                            return
                        self.nose_list[num] = nose_id
                        self.save_nose_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة الأنف رقم {num} بمعرّف: {nose_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف انف 5 nose-n_xxx")
                except Exception as e:
                    print(f"Error adding nose: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة الأنف")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if original_message.startswith("احذف أنف ") or original_message.startswith("احذف انف "):
            if await self.is_user_allowed(user):
                try:
                    num = original_message.replace("احذف أنف ", "").replace("احذف انف ", "").strip()
                    if num in self.nose_list:
                        del self.nose_list[num]
                        self.save_nose_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف الأنف رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد أنف برقم {num}")
                except Exception as e:
                    print(f"Error deleting nose: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف الأنف")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر اليد ====================
        if original_message.startswith("تغيير اليد "):
            if await self.is_user_allowed(user):
                try:
                    num = original_message.replace("تغيير اليد ", "").strip()
                    if num in self.hand_list:
                        hand_id = self.hand_list[num]
                        from highrise.models import Item as HandItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("hand-")]
                        new_outfit.append(HandItem(type="clothing", amount=1, id=hand_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير اليد إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.hand_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing hand: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير اليد")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if original_message.startswith("اضف يد ") or original_message.startswith("اضف اليد "):
            if await self.is_user_allowed(user):
                try:
                    prefix = "اضف اليد " if original_message.startswith("اضف اليد ") else "اضف يد "
                    parts = original_message.replace(prefix, "").strip().split()
                    if len(parts) == 2 and parts[0].isdigit():
                        num, hand_id = parts[0], parts[1]
                        self.hand_list[num] = hand_id
                        self.save_hand_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم إضافة اليد رقم {num} بمعرّف: {hand_id}")
                    else:
                        await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: اضف يد 5 hand-n_xxx")
                except Exception as e:
                    print(f"Error adding hand: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء إضافة اليد")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if original_message.startswith("احذف يد "):
            if await self.is_user_allowed(user):
                try:
                    num = original_message.replace("احذف يد ", "").strip()
                    if num in self.hand_list:
                        del self.hand_list[num]
                        self.save_hand_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف اليد رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد يد برقم {num}")
                except Exception as e:
                    print(f"Error deleting hand: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف اليد")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر الملامح ====================
        if original_message.startswith("تغيير ملامح ") or original_message.startswith("تغيير الملامح "):
            if await self.is_user_allowed(user):
                try:
                    num = original_message.replace("تغيير الملامح ", "").replace("تغيير ملامح ", "").strip()
                    if num in self.features_list:
                        feature_id = self.features_list[num]
                        from highrise.models import Item as FeatureItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("freckle-")]
                        new_outfit.append(FeatureItem(type="clothing", amount=1, id=feature_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير الملامح إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.features_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available if available else 'لا يوجد'}")
                except Exception as e:
                    print(f"Error changing features: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير الملامح")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # اضف ملامح — تم نقله للقسم المبكر

        if original_message.startswith("احذف ملمح "):
            if await self.is_user_allowed(user):
                try:
                    num = original_message.replace("احذف ملمح ", "").strip()
                    if num in self.features_list:
                        del self.features_list[num]
                        self.save_features_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف الملمح رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد ملمح برقم {num}")
                except Exception as e:
                    print(f"Error deleting feature: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف الملمح")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر الاختفاء ====================
        if original_message.startswith("تغيير اختفاء ") or original_message.startswith("تغيير الاختفاء "):
            if await self.is_user_allowed(user):
                try:
                    nums_str = original_message.replace("تغيير الاختفاء ", "").replace("تغيير اختفاء ", "").strip()
                    nums = nums_str.split()
                    from highrise.models import Item as InvisibleItem
                    my_outfit_response = await self.highrise.get_my_outfit()
                    new_outfit = list(my_outfit_response.outfit)
                    applied = []
                    not_found = []
                    for num in nums:
                        if num in self.invisible_list:
                            item_id = self.invisible_list[num]
                            existing_ids = [i.id for i in new_outfit]
                            if item_id not in existing_ids:
                                new_outfit.append(InvisibleItem(type="clothing", amount=1, id=item_id))
                            applied.append(num)
                        else:
                            not_found.append(num)
                    if applied:
                        await self.highrise.set_outfit(outfit=new_outfit)
                        msg = f"✅ تم إضافة الاختفاء: {', '.join(applied)}"
                        if not_found:
                            msg += f"\n⚠️ أرقام غير موجودة: {', '.join(not_found)}"
                        await self.highrise.send_whisper(user.id, msg)
                    else:
                        available = ", ".join(sorted(self.invisible_list.keys(), key=lambda x: int(x))) if self.invisible_list else "لا يوجد"
                        await self.highrise.send_whisper(user.id, f"⚠️ لا توجد أرقام صحيحة. المتاحة: {available}")
                except Exception as e:
                    print(f"Error changing invisible: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير الاختفاء")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if original_message.startswith("احذف اختفاء "):
            if await self.is_user_allowed(user):
                try:
                    num = original_message.replace("احذف اختفاء ", "").strip()
                    if num in self.invisible_list:
                        del self.invisible_list[num]
                        self.save_invisible_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف الاختفاء رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد اختفاء برقم {num}")
                except Exception as e:
                    print(f"Error deleting invisible: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف الاختفاء")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # ==================== أوامر القبعة ====================
        if original_message.startswith("تغيير قبعة ") or original_message.startswith("تغيير القبعة ") or original_message.startswith("تغيير قبعه ") or original_message.startswith("تغيير القبعه "):
            if await self.is_user_allowed(user):
                try:
                    num = original_message.replace("تغيير القبعة ", "").replace("تغيير قبعة ", "").replace("تغيير القبعه ", "").replace("تغيير قبعه ", "").strip()
                    if num in self.hat_list:
                        hat_id = self.hat_list[num]
                        from highrise.models import Item as HatItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("hat-")]
                        new_outfit.append(HatItem(type="clothing", amount=1, id=hat_id))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير القبعة إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.hat_list.keys(), key=lambda x: int(x))) if self.hat_list else "لا يوجد"
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available}")
                except Exception as e:
                    print(f"Error changing hat: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير القبعة")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if original_message.startswith("احذف قبعة ") or original_message.startswith("احذف قبعه "):
            if await self.is_user_allowed(user):
                try:
                    num = original_message.replace("احذف قبعة ", "").replace("احذف قبعه ", "").strip()
                    if num in self.hat_list:
                        del self.hat_list[num]
                        self.save_hat_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف القبعة رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا توجد قبعة برقم {num}")
                except Exception as e:
                    print(f"Error deleting hat: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف القبعة")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # تغيير شعر {n}
        if message.startswith("تغيير شعر "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("تغيير شعر ", "").strip()
                    if num in self.hair_list:
                        hair = self.hair_list[num]
                        from highrise.models import Item as HairItem
                        my_outfit_response = await self.highrise.get_my_outfit()
                        current_outfit = list(my_outfit_response.outfit)
                        new_outfit = [item for item in current_outfit if not item.id.startswith("hair_front-") and not item.id.startswith("hair_back-")]
                        new_outfit.append(HairItem(type="clothing", amount=1, id=hair["front"]))
                        new_outfit.append(HairItem(type="clothing", amount=1, id=hair["back"]))
                        await self.highrise.set_outfit(outfit=new_outfit)
                        await self.highrise.send_whisper(user.id, f"✅ تم تغيير الشعر إلى رقم {num}")
                    else:
                        available = ", ".join(sorted(self.hair_list.keys(), key=lambda x: int(x)))
                        await self.highrise.send_whisper(user.id, f"⚠️ رقم غير موجود. الأرقام المتاحة: {available}")
                except Exception as e:
                    print(f"Error changing hair: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء تغيير الشعر")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        # اضف شعر {n} {hair_id} — تم نقله للقسم المبكر

        # احذف شعر {n}
        if message.startswith("احذف شعر "):
            if await self.is_user_allowed(user):
                try:
                    num = message.replace("احذف شعر ", "").strip()
                    if num in self.hair_list:
                        del self.hair_list[num]
                        self.save_hair_list()
                        await self.highrise.send_whisper(user.id, f"✅ تم حذف الشعر رقم {num}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ لا يوجد شعر برقم {num}")
                except Exception as e:
                    print(f"Error deleting hair: {e}")
                    await self.highrise.send_whisper(user.id, "❌ حدث خطأ أثناء حذف الشعر")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")

        if message.startswith("تغيير لون العيون "):
            try:
                color_id = int(message.replace("تغيير لون العيون ", "").strip())
                my_outfit_response = await self.highrise.get_my_outfit()
                current_outfit = my_outfit_response.outfit
                new_outfit = []
                for item in current_outfit:
                    if item.id.startswith("eye-"):
                        item.active_palette = color_id
                    new_outfit.append(item)
                await self.highrise.set_outfit(outfit=new_outfit)
                await self.highrise.chat(f"✅ Eye color changed to #{color_id}" if self.bot_lang == "en" else f"✅ تم تغيير لون العيون إلى الرقم {color_id}")
            except Exception as e:
                await self.highrise.chat("❌ Error, make sure the number is correct" if self.bot_lang == "en" else "❌ حدث خطأ، تأكد من كتابة الرقم بشكل صحيح")

        if message.startswith("تغيير لون الحواجب "):
            try:
                color_id = int(message.replace("تغيير لون الحواجب ", "").strip())
                my_outfit_response = await self.highrise.get_my_outfit()
                current_outfit = my_outfit_response.outfit
                new_outfit = []
                for item in current_outfit:
                    if item.id.startswith("eyebrow-"):
                        item.active_palette = color_id
                    new_outfit.append(item)
                await self.highrise.set_outfit(outfit=new_outfit)
                await self.highrise.chat(f"✅ Eyebrow color changed to #{color_id}" if self.bot_lang == "en" else f"✅ تم تغيير لون الحواجب إلى الرقم {color_id}")
            except Exception as e:
                await self.highrise.chat("❌ Error, make sure the number is correct" if self.bot_lang == "en" else "❌ حدث خطأ، تأكد من كتابة الرقم بشكل صحيح")

        if message.startswith(("!adminlist", "adminlist")):
            if user.username not in self.owners:
                await self.highrise.chat("❌ Only owners can view the admin list.")
                return
            
            if not self.admins:
                await self.highrise.chat("📋 No bot admins found.")
                return

            admin_display_list = []
            for i, username in enumerate(self.admins, 1):
                admin_display_list.append(f"{i}. {username}")

            # تقسيم القائمة إلى رسائل متعددة إذا كانت طويلة
            message_chunks = []
            current_chunk = "👑 Bot Admins List:\n"

            for item in admin_display_list:
                if len(current_chunk + item + "\n") > 500:  # حد أقصى لطول الرسالة
                    message_chunks.append(current_chunk.strip())
                    current_chunk = item + "\n"
                else:
                    current_chunk += item + "\n"

            if current_chunk.strip():
                message_chunks.append(current_chunk.strip())

            # إرسال كل جزء من القائمة
            for chunk in message_chunks:
                await self.highrise.chat(chunk)
                
            await self.highrise.chat(f"📊 Total bot admins: {len(self.admins)}")
            return  # Exit immediately after command execution

        if message.startswith(("!mod")):
            is_bot_owner = user.username in self.owners
            is_room_owner = hasattr(self, 'room_owner_id') and user.id == self.room_owner_id
            if not is_bot_owner and not is_room_owner:
                await self.highrise.chat("❌ This command is for bot owner or room owner only." if self.bot_lang == "en" else "❌ هذا الأمر مخصص لمالك البوت أو مالك الغرفة فقط.")
                return
            parts = message.split()
            if len(parts) != 2:
                await self.highrise.chat("Usage: !mod @username")
                return
            command, username = parts
            if "@" not in username:
                username = username
            else:
                username = username[1:]
            try:
                # First try searching for the user
                user_info = await self.webapi.get_users(username = username, limit=1)
                
                # If we get a result from webapi
                if user_info and hasattr(user_info, 'users') and user_info.users:
                    target_user_id = user_info.users[0].user_id
                else:
                    # If webapi fails or returns empty, try to find user in the room
                    target_user_id = None
                    try:
                        room_users = await self.highrise.get_room_users()
                        for room_user, pos in room_users.content:
                            if room_user.username.lower() == username.lower():
                                target_user_id = room_user.id
                                break
                    except:
                        pass
                    
                    if not target_user_id:
                        await self.highrise.chat(f"User '{username}' not found. Make sure they are in the room or the name is correct.")
                        return
            except Exception:
                # Fallback to room users if webapi throws any error
                target_user_id = None
                try:
                    room_users = await self.highrise.get_room_users()
                    for room_user, pos in room_users.content:
                        if room_user.username.lower() == username.lower():
                            target_user_id = room_user.id
                            break
                except:
                    pass
                
                if not target_user_id:
                    await self.highrise.chat("Could not find user. Please make sure the name is correct.")
                    return
            #promote user to moderator
            permissions = (await self.highrise.get_room_privilege(target_user_id))
            permissions.moderator = True
            try:
                await self.highrise.change_room_privilege(target_user_id, permissions)
                await self.highrise.chat(f"{username} has been promoted to moderator.")
            except Exception as e:
                await self.highrise.chat(f"Error: {e}")
                return

        if message.startswith(("!delmod")):
            is_bot_owner = user.username in self.owners
            is_room_owner = hasattr(self, 'room_owner_id') and user.id == self.room_owner_id
            if not is_bot_owner and not is_room_owner:
                await self.highrise.chat("❌ This command is for bot owner or room owner only." if self.bot_lang == "en" else "❌ هذا الأمر مخصص لمالك البوت أو مالك الغرفة فقط.")
                return
            parts = message.split()
            if len(parts) != 2:
                await self.highrise.chat("Usage: !delmod @username")
                return
            command, username = parts
            if "@" not in username:
                username = username
            else:
                username = username[1:]
            try:
                # First try searching for the user
                user_info = await self.webapi.get_users(username = username, limit=1)
                
                # If we get a result from webapi
                if user_info and hasattr(user_info, 'users') and user_info.users:
                    target_user_id = user_info.users[0].user_id
                else:
                    # If webapi fails or returns empty, try to find user in the room
                    target_user_id = None
                    try:
                        room_users = await self.highrise.get_room_users()
                        for room_user, pos in room_users.content:
                            if room_user.username.lower() == username.lower():
                                target_user_id = room_user.id
                                break
                    except:
                        pass
                    
                    if not target_user_id:
                        await self.highrise.chat(f"User '{username}' not found. Make sure they are in the room or the name is correct.")
                        return
            except Exception:
                # Fallback to room users if webapi throws any error
                target_user_id = None
                try:
                    room_users = await self.highrise.get_room_users()
                    for room_user, pos in room_users.content:
                        if room_user.username.lower() == username.lower():
                            target_user_id = room_user.id
                            break
                except:
                    pass
                
                if not target_user_id:
                    await self.highrise.chat("Could not find user. Please make sure the name is correct.")
                    return
            #demote user from moderator
            permissions = (await self.highrise.get_room_privilege(target_user_id))
            permissions.moderator = False
            try:
                await self.highrise.change_room_privilege(target_user_id, permissions)
                await self.highrise.chat(f"{username} has been demoted from moderator.")
            except Exception as e:
                await self.highrise.chat(f"Error: {e}")
                return

        if message.startswith(("!desig")):
            if user.username not in self.owners:
                await self.highrise.chat("You do not have permission to use this command.")
                return
            parts = message.split()
            if len(parts) != 2:
                await self.highrise.chat("Usage: !desig @username")
                return
            command, username = parts
            if "@" not in username:
                username = username
            else:
                username = username[1:]
            try:
                # First try searching for the user
                user_info = await self.webapi.get_users(username = username, limit=1)
                
                # If we get a result from webapi
                if user_info and hasattr(user_info, 'users') and user_info.users:
                    target_user_id = user_info.users[0].user_id
                else:
                    # If webapi fails or returns empty, try to find user in the room
                    target_user_id = None
                    try:
                        room_users = await self.highrise.get_room_users()
                        for room_user, pos in room_users.content:
                            if room_user.username.lower() == username.lower():
                                target_user_id = room_user.id
                                break
                    except:
                        pass
                    
                    if not target_user_id:
                        await self.highrise.chat(f"User '{username}' not found. Make sure they are in the room or the name is correct.")
                        return
            except Exception:
                # Fallback to room users if webapi throws any error
                target_user_id = None
                try:
                    room_users = await self.highrise.get_room_users()
                    for room_user, pos in room_users.content:
                        if room_user.username.lower() == username.lower():
                            target_user_id = room_user.id
                            break
                except:
                    pass
                
                if not target_user_id:
                    await self.highrise.chat("Could not find user. Please make sure the name is correct.")
                    return
            #promote user to designer
            permissions = (await self.highrise.get_room_privilege(target_user_id))
            permissions.designer = True
            try:
                await self.highrise.change_room_privilege(target_user_id, permissions)
                await self.highrise.chat(f"{username} has been promoted to designer.")
            except Exception as e:
                await self.highrise.chat(f"Error: {e}")
                return

        if message.startswith(("!deldesig")):
            if user.username not in self.owners:
                await self.highrise.chat("You do not have permission to use this command.")
                return
            parts = message.split()
            if len(parts) != 2:
                await self.highrise.chat("Usage: !deldesig @username")
                return
            command, username = parts
            if "@" not in username:
                username = username
            else:
                username = username[1:]
            try:
                # First try searching for the user
                user_info = await self.webapi.get_users(username = username, limit=1)
                
                # If we get a result from webapi
                if user_info and hasattr(user_info, 'users') and user_info.users:
                    target_user_id = user_info.users[0].user_id
                else:
                    # If webapi fails or returns empty, try to find user in the room
                    target_user_id = None
                    try:
                        room_users = await self.highrise.get_room_users()
                        for room_user, pos in room_users.content:
                            if room_user.username.lower() == username.lower():
                                target_user_id = room_user.id
                                break
                    except:
                        pass
                    
                    if not target_user_id:
                        await self.highrise.chat(f"User '{username}' not found. Make sure they are in the room or the name is correct.")
                        return
            except Exception:
                # Fallback to room users if webapi throws any error
                target_user_id = None
                try:
                    room_users = await self.highrise.get_room_users()
                    for room_user, pos in room_users.content:
                        if room_user.username.lower() == username.lower():
                            target_user_id = room_user.id
                            break
                except:
                    pass
                
                if not target_user_id:
                    await موself.highrise.chat("Could not find user. Please make sure the name is correct.")
                    return
            #demote user from designer
            permissions = (await self.highrise.get_room_privilege(target_user_id))
            permissions.designer = False
            try:
                await self.highrise.change_room_privilege(target_user_id, permissions)
                await self.highrise.chat(f"{username} has been demoted from designer.")
            except Exception as e:
                await self.highrise.chat(f"Error: {e}")
                return

        

        


        


        

        

        message = message.strip().lower()
        # حفظ موقع المستخدم الذي كتب الأمر
        # تريجر جولي / lilith.Bat
        if "جولي" in message or "lilith.bat" in message.lower() or "@lilith.bat" in message.lower():
            try:
                await self.highrise.send_emote("emote-kiss", user.id)
                await asyncio.sleep(0.5)
                await self.highrise.chat("Coming to you @LILITH.BAT 😘" if self.bot_lang == "en" else "جولي يا حلو @LILITH.BAT 😘")
                for _ in range(5):
                    await self.highrise.react("heart", user.id)
                    await asyncio.sleep(0.3)
            except Exception as e:
                print(f"Error in جولي trigger: {e}")
            return

        if message == "حفظ" and await self.is_user_allowed(user):
            room_users = await self.highrise.get_room_users()
            bot_pos_found = False
            for room_user, position in room_users.content:
                if room_user.id == self.bot_id:
                    self.bot_start_position = position
                    self.save_bot_position(position)
                    await self.highrise.chat(f"✅ Bot position saved | X:{position.x} Z:{position.z}" if self.bot_lang == "en" else f"✅ تم حفظ موقع البوت | X:{position.x} Z:{position.z}")
                    bot_pos_found = True
                    break
            if not bot_pos_found:
                await self.highrise.chat("❌ Could not determine my position, try again" if self.bot_lang == "en" else "❌ لم أتمكن من تحديد موقعي، حاول مرة أخرى")
            return

        # البوت يذهب إلى الموقع المحفوظ
        if message in ["مكانك؟", "مكانك?", "run"]:
            if self.bot_start_position:
                try:
                    await self.highrise.walk_to(self.bot_start_position)
                    await self.highrise.chat("This is my spot 🖐️😴" if self.bot_lang == "en" else "هاذا هو مكاني 🖐️😴")
                except Exception as e:
                    print(f"Error walking bot to saved position: {e}")
                    try:
                        await self.highrise.teleport(self.bot_id, self.bot_start_position)
                    except Exception:
                        await self.highrise.chat("❌ An error occurred during teleport" if self.bot_lang == "en" else "❌ حدث خطأ أثناء الانتقال")
            else:
                await self.highrise.chat("Starting location not set yet ❌" if self.bot_lang == "en" else "لم يتم تحديد موقع البداية بعد ❌")
            return

        message = message.strip().lower()
        user_id = user.id

        if message.startswith("loop"):
            # فحص إذا كان الأمر يحتوي على @ (للمستخدمين الآخرين)
            if "@" in message and await self.is_user_allowed(user):
                # استخراج اسم الرقصة والمستخدمين
                parts = message.split("@")
                emote_part = parts[0].replace("loop", "").strip()
                
                # جمع جميع أسماء المستخدمين من الرسالة
                target_usernames = []
                for i in range(1, len(parts)):
                    username = parts[i].strip().split()[0]  # أخذ أول كلمة فقط في حالة وجود مسافات
                    if username:
                        target_usernames.append(username)
                
                if target_usernames:
                    # البحث عن المستخدمين في الغرفة
                    room_users = await self.highrise.get_room_users()
                    found_users = []
                    protected_users = []
                    not_found_users = []
                    
                    for target_username in target_usernames:
                        user_found = False
                        for room_user, _ in room_users.content:
                            if room_user.username.lower() == target_username.lower():
                                # فحص الحماية الخاصة
                                if self.is_user_protected(target_username):
                                    protected_users.append(target_username)
                                else:
                                    found_users.append((room_user, target_username))
                                user_found = True
                                break
                        
                        if not user_found:
                            not_found_users.append(target_username)
                    
                    # بدء الرقص للمستخدمين المذكورين أولاً
                    successful_users = []
                    for room_user, username in found_users:
                        try:
                            # إيقاف أي loop سابق للمستخدم المستهدف
                            if room_user.id in self.user_emote_loops:
                                await self.stop_emote_loop(room_user.id)
                            
                            # انتظار قصير للتأكد من توقف الloop السابق
                            await asyncio.sleep(0.1)
                            
                            # بدء loop جديد للمستخدم المستهدف
                            await self.start_emote_loop(room_user.id, emote_part)
                            successful_users.append(username)
                            print(f"Started loop {emote_part} for {username}")
                        except Exception as e:
                            print(f"Error starting loop for {username}: {e}")
                    
                    # إضافة المستخدم الذي كتب الأمر للقائمة بعد بدء loops للآخرين
                    sender_added = False
                    try:
                        # إيقاف أي loop سابق للمستخدم الذي كتب الأمر
                        if user.id in self.user_emote_loops:
                            await self.stop_emote_loop(user.id)
                        
                        # انتظار قصير
                        await asyncio.sleep(0.1)
                        
                        # بدء loop للمستخدم الذي كتب الأمر
                        await self.start_emote_loop(user.id, emote_part)
                        sender_added = True
                        print(f"Started loop {emote_part} for command sender {user.username}")
                    except Exception as e:
                        print(f"Error starting loop for command sender {user.username}: {e}")
                    
                    # إرسال رسائل التأكيد
                    all_dancing = []
                    if sender_added:
                        all_dancing.append(f"@{user.username}")
                    if successful_users:
                        all_dancing.extend([f"@{u}" for u in successful_users])
                    
                    if all_dancing:
                        users_list = ", ".join(all_dancing)
                        await self.highrise.chat(f"🎭 The dancing start {emote_part} users: {users_list}")
                    
                    if protected_users:
                        protected_list = ", ".join([f"@{u}" for u in protected_users])
                        await self.highrise.chat(f"❌ Protected users: {protected_list}" if self.bot_lang == "en" else f"❌ المستخدمون المحميون: {protected_list}")
                    
                    if not_found_users:
                        notfound_list = ", ".join([f"@{u}" for u in not_found_users])
                        await self.highrise.chat(f"❌ Users not found: {notfound_list}" if self.bot_lang == "en" else f"❌ المستخدمون غير موجودون: {notfound_list}")
                else:
                    await self.highrise.chat("❌ No valid usernames found" if self.bot_lang == "en" else "❌ لم يتم العثور على أسماء مستخدمين صحيحة")
                return
            else:
                # الأمر العادي للمستخدم نفسه
                emote_name = message.replace("loop", "").strip()
                # إيقاف أي loop سابق
                if user_id in self.user_emote_loops:
                    await self.stop_emote_loop(user_id)
                # بدء loop جديد دائم
                await self.start_emote_loop(user_id, emote_name)

        if message in ["0", "stop", "توقف"]:
            if user_id in self.user_emote_loops:
                if self.user_emote_loops[user_id] == "رقصني":
                    await self.stop_random_emote_loop(user_id)
                else:
                    await self.stop_emote_loop(user_id)
            return

        if message == "رقصني" or message.startswith("رقصني "):
            # فحص حماية المالك
            if self.owner_protected and user.username.lower() in [owner.lower() for owner in self.owners]:
                await self.highrise.chat("🛡️ Owner is protected, emotes cannot be used on them" if self.bot_lang == "en" else "🛡️ المالك محمي حالياً ولا يمكن استخدام الرقصات عليه")
                return
            # رقصني [معرّف] أو رقصني loop [معرّف]
            if message.startswith("رقصني "):
                rest = message.replace("رقصني ", "").strip()
                # رقصني loop [معرّف] - رقص مستمر
                if rest.startswith("loop "):
                    emote_id = rest.replace("loop ", "").strip()
                    if emote_id:
                        if user_id in self.user_emote_loops:
                            await self.stop_emote_loop(user_id)
                            await asyncio.sleep(0.2)
                        # loop مباشر بالمعرّف
                        self.user_emote_loops[user_id] = emote_id
                        async def _user_emote_id_loop(uid=user_id, eid=emote_id):
                            while self.user_emote_loops.get(uid) == eid:
                                try:
                                    await self.highrise.send_emote(eid, uid)
                                    await asyncio.sleep(6)
                                except Exception as e:
                                    print(f"User emote loop error: {e}")
                                    await asyncio.sleep(2)
                        asyncio.create_task(_user_emote_id_loop())
                # رقصني [معرّف] - رقصة واحدة فقط
                elif rest:
                    try:
                        await self.highrise.send_emote(rest, user_id)
                    except Exception as e:
                        await self.highrise.send_whisper(user.id, f"❌ معرّف الرقصة غير صحيح: {str(e)[:100]}")
                return
            # رقصني وحدها - رقص عشوائي
            if user_id not in self.user_emote_loops:
                await self.start_random_emote_loop(user_id)
            return

        # ==================== إيقاف رقص البوت ====================
        if message in ["وقف ارقص", "ايقاف ارقص", "stop ارقص"]:
            if await self.is_user_allowed(user):
                self.emote_looping = False
                await self.highrise.send_whisper(user.id, "✅ تم إيقاف رقص البوت")
            return

        # ==================== توقف المرجحه ====================
        if message.startswith("توقف المرجحه") or message.startswith("توقف المرجحة"):
            # توقف المرجحه @username (للمشرفين)
            if "@" in message:
                if not await self.is_user_allowed(user):
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return
                target_username = message.split("@", 1)[1].strip()
                try:
                    room_users = await self.highrise.get_room_users()
                    target_id = None
                    for ru, _ in room_users.content:
                        if ru.username.lower() == target_username.lower():
                            target_id = ru.id
                            break
                    if target_id:
                        await self.stop_emote_loop(target_id)
                        await self.highrise.send_whisper(user.id, f"✅ تم إيقاف المرجحة لـ @{target_username}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ المستخدم @{target_username} غير موجود في الغرفة")
                except Exception as e:
                    print(f"Error in توقف المرجحه: {e}")
            else:
                # توقف المرجحه بدون @ → يوقف جميع المستخدمين النشطين (للمشرفين)
                if not await self.is_user_allowed(user):
                    await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
                    return
                all_ids = list(self.user_emote_loops.keys())
                count = len(all_ids)
                for uid in all_ids:
                    await self.stop_emote_loop(uid)
                await self.highrise.send_whisper(user.id, f"✅ تم إيقاف المرجحة لـ {count} مستخدم")
            return

        # ==================== أمر ارقص للبوت ====================
        if message.startswith("ارقص ") or message == "ارقص":
            if await self.is_user_allowed(user):
                if message == "ارقص":
                    await self.highrise.send_whisper(user.id, "⚠️ الصيغة: ارقص [معرّف] أو ارقص loop [معرّف]\nمثال: ارقص emote-dance-tiktok3\nمثال: ارقص loop emote-dance-blackpink")
                    return
                rest = message.replace("ارقص ", "").strip()
                # ارقص loop [معرّف]
                if rest.startswith("loop "):
                    emote_id = rest.replace("loop ", "").strip()
                    if self.emote_looping:
                        self.emote_looping = False
                        await asyncio.sleep(0.3)
                    self.emote_looping = True
                    # حساب مدة الرقصة من emote_mapping إذا موجودة، وإلا 5 ثوان
                    emote_time = 5
                    for v in emote_mapping.values():
                        if v.get("value") == emote_id:
                            emote_time = v.get("time", 5)
                            break
                    await self.highrise.send_whisper(user.id, f"✅ البوت يرقص بشكل مستمر:\n{emote_id}")
                    async def bot_dance_loop():
                        while self.emote_looping:
                            try:
                                await self.highrise.send_emote(emote_id)
                                await asyncio.sleep(emote_time)
                            except Exception as e:
                                print(f"Bot dance loop error: {e}")
                                await asyncio.sleep(2)
                    asyncio.create_task(bot_dance_loop())
                else:
                    # ارقص مرة واحدة بالمعرّف مباشرة
                    emote_id = rest.strip()
                    try:
                        await self.highrise.send_emote(emote_id)
                        await self.highrise.send_whisper(user.id, f"✅ تم تنفيذ الرقصة:\n{emote_id}")
                    except Exception as e:
                        await self.highrise.send_whisper(user.id, f"❌ فشل تنفيذ الرقصة: {str(e)[:120]}\nتأكد من صحة معرّف الرقصة")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        if message in ["جوست", "ghost"]:
            if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "ghost":
                await self.stop_emote_loop(user_id)
            else:
                await self.start_ghost_emote_loop(user_id)
            return
        
        # أمر بوسه/بوسة - رقصة رقم 96
        if message in ["بوسه", "بوسة", "kiss", "بوس"]:
            if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "kiss":
                await self.stop_emote_loop(user_id)
            else:
                await self.start_kiss_emote_loop(user_id)
            return
        
        # أمر خجول - رقصة رقم 73
        if message in ["خجول", "خجل", "shy"]:
            if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "shy":
                await self.stop_emote_loop(user_id)
            else:
                await self.start_shy_emote_loop(user_id)
            return

        # أمر نام - رقصة رقم 150
        if message in ["نام", "sleep"] or message.lower().startswith("نام @") or message.lower().startswith("sleep @"):
            parts = message.split()
            if len(parts) > 1 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()
                if self.is_user_protected(target_username):
                    await self.highrise.send_whisper(user.id, f"🛡️ المستخدم @{target_username} محمي ولا يمكن استخدام هذا الأمر عليه")
                    return
                room_users = await self.highrise.get_room_users()
                target_user_id = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user_id = room_user.id
                        break
                if target_user_id:
                    await self.highrise.send_emote("idle-floorsleeping", target_user_id)
                else:
                    await self.highrise.chat(f"❌ User @{target_username} is not in the room" if self.bot_lang == "en" else f"❌ المستخدم @{target_username} غير موجود في الغرفة")
            else:
                if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "sleep_loop":
                    await self.stop_emote_loop(user_id)
                else:
                    await self.start_sleep_emote_loop(user_id)
            return

        # أمر تس - رقصة رقم 10
        if message.lower() in ("تس", "تسس") or message.lower().startswith("تس @") or message.lower().startswith("تسس @"):
            emote_to_send = "emote-snake"  # رقصة رقم 10
            parts = message.split()
            target_user_id = None
            
            if len(parts) > 1 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()
                if self.is_user_protected(target_username):
                    await self.highrise.send_whisper(user.id, f"🛡️ المستخدم @{target_username} محمي ولا يمكن استخدام هذا الأمر عليه")
                    return
                room_users = await self.highrise.get_room_users()
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user_id = room_user.id
                        break
                
                if target_user_id:
                    try:
                        await self.highrise.send_emote(emote_to_send, target_user_id)
                    except Exception as e:
                        print(f"Error sending emote to target: {e}")
                else:
                    await self.highrise.chat(f"❌ User @{target_username} not found" if self.bot_lang == "en" else f"❌ المستخدم @{target_username} غير موجود")
            else:
                # للمستخدم نفسه
                try:
                    await self.highrise.send_emote(emote_to_send, user.id)
                except Exception as e:
                    print(f"Error sending emote to self: {e}")
            return

        # أمر ضفدع - رقصة رقم 17
        if message.startswith("ضفدع"):
            emote_to_send = "emote-frog"  # رقصة رقم 17
            parts = message.split()
            target_user_id = None
            
            if len(parts) > 1 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()
                if self.is_user_protected(target_username):
                    await self.highrise.send_whisper(user.id, f"🛡️ المستخدم @{target_username} محمي ولا يمكن استخدام هذا الأمر عليه")
                    return
                room_users = await self.highrise.get_room_users()
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user_id = room_user.id
                        break
                
                if target_user_id:
                    try:
                        await self.highrise.send_emote(emote_to_send, target_user_id)
                    except Exception as e:
                        print(f"Error sending frog emote to target: {e}")
                else:
                    await self.highrise.chat(f"❌ User @{target_username} not found" if self.bot_lang == "en" else f"❌ المستخدم @{target_username} غير موجود")
            else:
                # للمستخدم نفسه
                try:
                    await self.highrise.send_emote(emote_to_send, user.id)
                except Exception as e:
                    print(f"Error sending frog emote to self: {e}")
            return

        # أمر نوم - رقصة رقم 152
        if message in ["نوم", "sleep2"] or message.lower().startswith("نوم @") or message.lower().startswith("sleep2 @"):
            parts = message.split()
            if len(parts) > 1 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()
                if self.is_user_protected(target_username):
                    await self.highrise.send_whisper(user.id, f"🛡️ المستخدم @{target_username} محمي ولا يمكن استخدام هذا الأمر عليه")
                    return
                room_users = await self.highrise.get_room_users()
                target_user_id = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user_id = room_user.id
                        break
                if target_user_id:
                    await self.highrise.send_emote("idle-floorsleeping2", target_user_id)
                else:
                    await self.highrise.chat(f"❌ User @{target_username} is not in the room" if self.bot_lang == "en" else f"❌ المستخدم @{target_username} غير موجود في الغرفة")
            else:
                if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "sleep2_loop":
                    await self.stop_emote_loop(user_id)
                else:
                    await self.start_sleep2_emote_loop(user_id)
            return

        

        if message in ["floss forever", "فلوس فور ايفر"]:
            if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "floss":
                await self.stop_emote_loop(user_id)
            else:
                await self.start_floss_emote_loop(user_id)
            return

        if message in ["nofloss", "نو فلوس"]:
            if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "floss":
                await self.stop_emote_loop(user_id)
            return

        if message in ["dance floor", "دانس فلور"]:
            # فحص حماية المالك
            if self.owner_protected and user.username.lower() in [owner.lower() for owner in self.owners]:
                await self.highrise.chat("🛡️ Owner is protected, emotes cannot be used on them" if self.bot_lang == "en" else "🛡️ المالك محمي حالياً ولا يمكن استخدام الرقصات عليه")
                return
            if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "dance_floor":
                await self.stop_emote_loop(user_id)
            else:
                await self.start_dance_floor_loop(user_id)
            return

        if message in ["nodance", "نو دانس"]:
            if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "dance_floor":
                await self.stop_emote_loop(user_id)
            return


        message = message.strip().lower()

        if "@" in message:
            parts = message.split("@")
            if len(parts) < 2:
                return

            emote_name = parts[0].strip()
            target_username = parts[1].strip()

            if emote_name in emote_mapping:
                response = await self.highrise.get_room_users()
                users = [content[0] for content in response.content]
                usernames = [user.username.lower() for user in users]

                if target_username not in usernames:
                    return

                user_id = next((u.id for u in users if u.username.lower() == target_username), None)
                if not user_id:
                    return

                await self.handle_emote_command(user.id, emote_name)
                await self.handle_emote_command(user_id, emote_name)


        if not command_executed:
            for emote_name, emote_info in emote_mapping.items():
                if message.lower() == emote_name.lower():
                    # إذا كان المستخدم لديه loop نشط، إيقافه أولاً
                    if user_id in self.user_emote_loops:
                        await self.stop_emote_loop(user_id)

                    # إذا كان الرقم فقط، ارقص مرة واحدة
                    # إذا كان مع "loop"، ابدأ الـ loop
                    if message.startswith("loop"):
                        await self.start_emote_loop(user_id, emote_name)
                    else:
                        # رقص واحد فقط
                        emote_to_send = emote_info["value"]
                        try:
                            await self.highrise.send_emote(emote_to_send, user_id)
                            # إضافة نقاط للمستخدم عند استخدام الرقصات (5 نقاط)
                            self.add_user_points(user_id, 5)
                        except Exception as e:
                            print(f"Error sending single emote: {e}")
                    command_executed = True
                    break


        if message.lower() == "h all" and await self.is_user_allowed(user):
            # إرسال قلب لجميع المستخدمين في الروم (مرة واحدة)
            room_users = (await self.highrise.get_room_users()).content
            tasks = []
            for room_user, _ in room_users:
                # تجنب إرسال قلب للبوت نفسه
                if room_user.id != self.bot_id:
                    tasks.append(self.highrise.react("heart", room_user.id))
            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                error_message = f"خطأ في إرسال القلوب: {e}"
                await self.highrise.send_whisper(user.id, error_message)

        if message.lower() == "r" and await self.is_user_allowed(user):
            # إرسال قلوب متتالية لجميع المستخدمين في الروم
            room_users = (await self.highrise.get_room_users()).content
            users_to_send = []
            for room_user, _ in room_users:
                # تجنب إرسال قلب للبوت نفسه
                if room_user.id != self.bot_id:
                    users_to_send.append(room_user)

            if users_to_send:
                try:
                    # إرسال 3 جولات من القلوب
                    for round_num in range(3):
                        for room_user in users_to_send:
                            try:
                                await self.highrise.react("heart", room_user.id)
                                await asyncio.sleep(0.3)  # انتظار بين كل قلب
                            except Exception as e:
                                print(f"Error sending heart to {room_user.username}: {e}")
                                continue
                        # انتظار بين الجولات
                        if round_num < 2:  # لا نحتاج انتظار بعد الجولة الأخيرة
                            await asyncio.sleep(1)


                except Exception as e:
                    error_message = f"خطأ في إرسال القلوب المتتالية: {e}"
                    await self.highrise.send_whisper(user.id, error_message)

        if message.lower().startswith("all ") and await self.is_user_allowed(user):
            emote_name = message.replace("all", "").strip()
            if emote_name in emote_mapping:
                emote_to_send = emote_mapping[emote_name]["value"]
                room_users = (await self.highrise.get_room_users()).content
                tasks = []
                for room_user, _ in room_users:
                    tasks.append(self.highrise.send_emote(emote_to_send, room_user.id))
                try:
                    await asyncio.gather(*tasks)
                except Exception as e:
                    error_message = f"Error sending emotes: {e}"
                    await self.highrise.send_whisper(user.id, error_message)
            else:
                await self.highrise.send_whisper(user.id, "Invalid emote name: {}".format(emote_name))

        # أمر loop للجميع - رقص جماعي مستمر
        if message.lower().startswith("loopall ") and await self.is_user_allowed(user):
            emote_name = message.replace("loopall", "").strip()
            if emote_name in emote_mapping:
                room_users = (await self.highrise.get_room_users()).content
                success_count = 0
                
                for room_user, _ in room_users:
                    # تجنب إجبار الأونرز والمحميين على الرقص
                    if (room_user.username in self.owners or 
                        self.is_user_protected(room_user.username) or
                        room_user.id == self.bot_id):
                        continue
                    
                    # إيقاف أي loop سابق
                    if room_user.id in self.user_emote_loops:
                        await self.stop_emote_loop(room_user.id)
                    
                    # بدء loop جديد
                    await self.start_emote_loop(room_user.id, emote_name)
                    success_count += 1
                
                await self.highrise.chat(f"🎭 {success_count} user(s) started group dance {emote_name}" if self.bot_lang == "en" else f"🎭 بدأ {success_count} مستخدم في الرقص الجماعي {emote_name}")
            else:
                await self.highrise.chat(f"❌ Invalid emote: {emote_name}" if self.bot_lang == "en" else f"❌ رقصة غير صحيحة: {emote_name}")

        # أمر all loop [رقم] - رقص جماعي مستمر بالرقم
        if message.lower().startswith("all loop ") and await self.is_user_allowed(user):
            num = message[len("all loop"):].strip()
            if num in emote_mapping:
                emote_name = num
                room_users = (await self.highrise.get_room_users()).content
                success_count = 0
                for room_user, _ in room_users:
                    if (room_user.username in self.owners or
                        self.is_user_protected(room_user.username) or
                        room_user.id == self.bot_id):
                        continue
                    if room_user.id in self.user_emote_loops:
                        await self.stop_emote_loop(room_user.id)
                    await self.start_emote_loop(room_user.id, emote_name)
                    success_count += 1
                emote_value = emote_mapping[num]["value"]
                await self.highrise.chat(f"🎭 Everyone dancing #{num} ({emote_value}) - {success_count} users" if self.bot_lang == "en" else f"🎭 الكل يرقص رقصة رقم {num} ({emote_value}) - {success_count} مستخدم")
            else:
                await self.highrise.send_whisper(user.id, f"❌ رقم الرقصة {num} غير موجود. الأرقام المتاحة من 1 إلى {max(emote_mapping.keys(), key=int)}")

        # أمر إيقاف الرقص للجميع
        if message.lower() in ["stopall", "0all"] and await self.is_user_allowed(user):
            room_users = (await self.highrise.get_room_users()).content
            stopped_count = 0
            
            for room_user, _ in room_users:
                if room_user.id in self.user_emote_loops:
                    await self.stop_emote_loop(room_user.id)
                    stopped_count += 1
            
            await self.highrise.chat(f"⏹️ Dance stopped for {stopped_count} user(s)" if self.bot_lang == "en" else f"⏹️ تم إيقاف الرقص عن {stopped_count} مستخدم")

        # أمر dance party - رقص عشوائي جماعي
        if message.lower() in ["رقص الكل", "party dance"] and await self.is_user_allowed(user):
            # فحص حماية المالك
            if self.owner_protected:
                await self.highrise.chat("🛡️ The owner is currently protected and this command cannot be used on them" if self.bot_lang == "en" else "🛡️ المالك محمي حالياً ولا يمكن استخدام هذا الأمر عليه")
                return
            room_users = (await self.highrise.get_room_users()).content
            success_count = 0
            
            for room_user, _ in room_users:
                # تجنب إجبار الأونرز والمحميين على الرقص
                if (room_user.username in self.owners or 
                    self.is_user_protected(room_user.username) or
                    room_user.id == self.bot_id):
                    continue
                
                # إيقاف أي loop سابق
                if room_user.id in self.user_emote_loops:
                    await self.stop_emote_loop(room_user.id)
                
                # بدء رقص عشوائي
                await self.start_random_emote_loop(room_user.id)
                success_count += 1
            
            await self.highrise.chat(f"🎉 Dance party started! {success_count} users dancing" if self.bot_lang == "en" else f"🎉 بدأت حفلة الرقص! {success_count} مستخدم يرقصون")

        # أمر توقيف مستخدم محدد من الرقص
        if message.lower().startswith("stop ") and "@" in message and await self.is_user_allowed(user):
            target_username = message.split("@")[-1].strip()
            
            room_users = (await self.highrise.get_room_users()).content
            target_user = None
            for room_user, _ in room_users:
                if room_user.username.lower() == target_username.lower():
                    target_user = room_user
                    break
            
            if target_user and target_user.id in self.user_emote_loops:
                await self.stop_emote_loop(target_user.id)
                await self.highrise.chat(f"⏹️ Dance stopped for @{target_username}" if self.bot_lang == "en" else f"⏹️ تم إيقاف رقص @{target_username}")
            elif target_user:
                await self.highrise.chat(f"❌ @{target_username} is not dancing currently" if self.bot_lang == "en" else f"❌ @{target_username} لا يرقص حالياً")
            else:
                await self.highrise.chat(f"❌ User @{target_username} not found" if self.bot_lang == "en" else f"❌ المستخدم @{target_username} غير موجود")


        message = message.strip().lower()

        try:
            if message.lstrip().startswith(("اسحر")):
                response = await self.highrise.get_room_users()
                users = [content[0] for content in response.content]
                usernames = [user.username.lower() for user in users]
                parts = message[1:].split()
                args = parts[1:]

                if len(args) >= 1 and args[0][0] == "@" and args[0][1:].lower() in usernames:
                    user_id = next((u.id for u in users if u.username.lower() == args[0][1:].lower()), None)

                    if message.lower().startswith("اسحر"):
                        await self.highrise.send_emote("emote-telekinesis", user.id)
                        await self.highrise.send_emote("emote-gravity", user.id)
        except Exception as e:
            print(f"An error occurred: {e}")

        if message.startswith("rd") or message.startswith("رقصات"):
            try:
                emote_name = random.choice(list(secili_emote.keys()))
                emote_to_send = secili_emote[emote_name]["value"]
                await self.highrise.send_emote(emote_to_send, user.id)
            except:
                print("Dans emote gönderilirken bir hata oluştu.")

        if message.lower().startswith("equip ") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) < 2 or not parts[1].startswith("@"):
                await self.highrise.chat("❌ Usage: equip @username")
                return

            target_username = parts[1][1:]  # Remove @ symbol

            # البحث عن المستخدم في قاعدة البيانات أولاً
            try:
                if hasattr(self, 'webapi') and self.webapi:
                    user_info = await self.webapi.get_users(username=target_username, limit=1)
                    if not user_info.users:
                        await self.highrise.chat("❌ User not found!" if self.bot_lang == "en" else "❌ المستخدم غير موجود!")
                        return

                    target_user_id = user_info.users[0].user_id

                    # محاولة الحصول على ملابس المستخدم
                    target_outfit = await self.highrise.get_user_outfit(target_user_id)
                    if not target_outfit or not target_outfit.outfit:
                        await self.highrise.chat("❌ Cannot get this user's outfit!" if self.bot_lang == "en" else "❌ لا يمكن الحصول على ملابس هذا المستخدم!")
                        return

                    # تطبيق الملابس على البوت
                    await self.highrise.set_outfit(outfit=target_outfit.outfit)
                    await self.highrise.chat(f"🎭 Bot is now wearing @{target_username}'s outfit!" if self.bot_lang == "en" else f"🎭 البوت ارتدى ملابس @{target_username}!")
                else:
                    await self.highrise.chat("❌ WebAPI service is not available" if self.bot_lang == "en" else "❌ خدمة WebAPI غير متاحة")

            except Exception as e:
                print(f"Error copying outfit: {e}")
                await self.highrise.chat("❌ Error copying outfit!" if self.bot_lang == "en" else "❌ حدث خطأ أثناء نسخ الملابس!")

        if message.lower().startswith("e ") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) >= 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()
                
                # If three parts, the first mentioned user is the one who will copy (target1)
                # and the second is the source (target2). 
                # If two parts, the bot copies the user.
                if len(parts) >= 3 and parts[2].startswith("@"):
                    source_username = parts[2][1:].strip()
                    requester_username = target_username
                else:
                    source_username = target_username
                    requester_username = user.username

                try:
                    # Search for source user
                    room_users = await self.highrise.get_room_users()
                    source_user = next((u for u, p in room_users.content if u.username.lower() == source_username.lower()), None)
                    
                    source_id = None
                    if source_user:
                        source_id = source_user.id
                        print(f"DEBUG: Found {source_username} in room with ID: {source_id}")
                    else:
                        # Global search
                        await self.highrise.chat(f"🔍 {source_username} not in room, searching globally..." if self.bot_lang == "en" else f"🔍 المستخدم {source_username} ليس في الروم، جاري البحث عنه عالمياً...")
                        try:
                            search_results = await self.webapi.get_users(username=source_username, limit=1)
                            if search_results and hasattr(search_results, 'users') and search_results.users:
                                source_id = search_results.users[0].user_id
                                print(f"DEBUG: Found {source_username} globally with ID: {source_id}")
                            else:
                                await self.highrise.chat(f"❌ Could not find {source_username}. Make sure to enter the username correctly." if self.bot_lang == "en" else f"❌ تعذر العثور على {source_username}. تأكد من كتابة اسم المستخدم (Username) بشكل صحيح.")
                                return
                        except Exception as search_err:
                            print(f"DEBUG: Global search failed for {source_username}: {search_err}")
                            await self.highrise.chat(f"❌ Error searching for {source_username}" if self.bot_lang == "en" else f"❌ خطأ أثناء البحث عن {source_username}")
                            return

                    # Get outfit
                    try:
                        print(f"DEBUG: Fetching outfit for ID: {source_id}")
                        source_outfit = await self.highrise.get_user_outfit(source_id)
                    except Exception as e:
                        print(f"DEBUG: get_user_outfit failed for {source_id}: {e}")
                        if "404" in str(e):
                             await self.highrise.chat(f"❌ No outfit found for {source_username}. Account may be private or not found." if self.bot_lang == "en" else f"❌ لم يتم العثور على ملابس للمستخدم {source_username}. قد يكون الحساب خاصاً أو غير موجود.")
                        else:
                             await self.highrise.chat(f"❌ Technical error fetching outfit: {str(e)}" if self.bot_lang == "en" else f"❌ خطأ تقني عند جلب الملابس: {str(e)}")
                        return

                    if not source_outfit or not source_outfit.outfit:
                        await self.highrise.chat(f"❌ Could not fetch {source_username}'s outfit (account may be private or no outfit)" if self.bot_lang == "en" else f"❌ تعذر جلب ملابس {source_username} (ربما حسابه خاص أو لا يرتدي شيئاً)")
                        return

                    # Bot wears the outfit
                    try:
                        await self.highrise.set_outfit(outfit=source_outfit.outfit)
                    except Exception as e:
                        await self.highrise.chat(f"❌ Bot failed to wear outfit: {str(e)}" if self.bot_lang == "en" else f"❌ فشل البوت في ارتداء الملابس: {str(e)}")
                        return

                    await self.highrise.chat(f"🎭 Successfully copied {source_username}'s outfit!" if self.bot_lang == "en" else f"🎭 تم نسخ ملابس {source_username} بنجاح!")
                    
                    # Try to find requester in room to give feedback
                    if requester_username.lower() != self.owners[0].lower():
                         await self.highrise.chat(f"👤 @{requester_username}, you can now copy the outfit from the bot" if self.bot_lang == "en" else f"👤 @{requester_username}، يمكنك الآن نسخ الملابس من البوت")

                except Exception as e:
                    print(f"Error in outfit copying: {e}")
                    await self.highrise.chat(f"❌ Failed to fetch outfit. Make sure the name is correct." if self.bot_lang == "en" else f"❌ فشل جلب الملابس. تأكد من كتابة الاسم بشكل صحيح.")
            else:
                await self.highrise.chat("📝 Usage: e @username" if self.bot_lang == "en" else "📝 الاستخدام: e @username")

        if message.lower().startswith("q "):
            if await self.is_user_allowed(user):
                # استخراج معرف الآيتم من الرسالة
                item_id = message.split("q ", 1)[1].strip()

                if not item_id:
                    await self.highrise.chat("❌ Type q followed by the item ID" if self.bot_lang == "en" else "❌ اكتب q متبوعة بمعرف الآيتم")
                    await self.highrise.chat("💡 Example: q watch-n_room12019watch" if self.bot_lang == "en" else "💡 مثال: q watch-n_room12019watch")
                    return

                # الحصول على الآيتم الحالي للبوت
                try:
                    from highrise.models import Item, ItemType, Outfit

                    # إنشاء الآيتم الجديد كقطعة ملابس
                    clothing_item = Item(
                        type=ItemType.clothing,
                        amount=1,
                        id=item_id
                    )

                    # إلباس البوت الآيتم كطقم كامل (هذا يضمن التغيير الفوري)
                    await self.highrise.set_outfit(outfit=[clothing_item])
                    await self.highrise.chat(f"👕 Bot is now wearing item {item_id}! ✨" if self.bot_lang == "en" else f"👕 تم إلباس البوت الآيتم {item_id} بنجاح! ✨")
                    print(f"Item {item_id} equipped successfully via set_outfit([item])")

                except Exception as e:
                    print(f"Error in q command (set_outfit): {e}")
                    await self.highrise.chat(f"✅ Attempted to wear item: {item_id}" if self.bot_lang == "en" else f"✅ تم محاولة إلباس الآيتم: {item_id}")
                    await self.highrise.chat("💡 If the item doesn't appear, make sure:" if self.bot_lang == "en" else "💡 إذا لم يظهر الآيتم، تأكد من:")
                    await self.highrise.chat("• The item ID is correct" if self.bot_lang == "en" else "• أن معرف الآيتم صحيح")
                    await self.highrise.chat("• The item is available in the Highrise store" if self.bot_lang == "en" else "• أن الآيتم متاح في متجر Highrise")
                    await self.highrise.chat("• The item is of type clothing" if self.bot_lang == "en" else "• أن الآيتم من نوع clothing")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # الأمر القديم q بدون معرف (للساعة)
        elif message.lower() == "q":
            if await self.is_user_allowed(user):
                try:
                    # معرف الساعة الافتراضي
                    item_id = "watch-n_room12019watch"
                    from highrise.models import Item, ItemType

                    clothing_item = Item(
                        type=ItemType.clothing,
                        amount=1,
                        id=item_id
                    )

                    await self.highrise.set_outfit(outfit=[clothing_item])
                    await self.highrise.chat(f"⌚ Bot is now wearing the default watch! ✨" if self.bot_lang == "en" else f"⌚ تم إلباس البوت الساعة الافتراضية بنجاح! ✨")
                    await self.highrise.chat("💡 To wear a custom item use: q [item_id]" if self.bot_lang == "en" else "💡 لإلباس آيتم مخصص استخدم: q [معرف_الآيتم]")

                except Exception as e:
                    print(f"Error in q command (default watch): {e}")
                    await self.highrise.chat("⌚ Attempted to wear the default watch" if self.bot_lang == "en" else "⌚ تم محاولة إلباس الساعة الافتراضية")
                    await self.highrise.chat("💡 To wear another item try: q [item_id]" if self.bot_lang == "en" else "💡 لإلباس آيتم آخر جرب: q [معرف_الآيتم]")
            else:
                await self.highrise.send_whisper(user.id, "❌ هذا الأمر مخصص للمالك والمشرفين فقط")
            return

        # أمر عرض لوحة الصدارة للنقاط
        if message.lower() in ["نقاط الروم", "لوحة الصدارة", "top points"]:
            try:
                if not self.user_points:
                    await self.highrise.chat("📊 No points saved yet" if self.bot_lang == "en" else "📊 لا توجد نقاط محفوظة بعد")
                    return

                # الحصول على قائمة المستخدمين في الروم مع نقاطهم
                room_users = await self.highrise.get_room_users()
                room_user_points = []

                for room_user, _ in room_users.content:
                    if room_user.id in self.user_points and room_user.id != self.bot_id:
                        points = self.user_points[room_user.id]
                        room_user_points.append((room_user.username, points))

                if not room_user_points:
                    await self.highrise.chat("📊 No points for users in the room" if self.bot_lang == "en" else "📊 لا توجد نقاط للمستخدمين في الروم")
                    return

                # ترتيب المستخدمين حسب النقاط (الأعلى أولاً)
                room_user_points.sort(key=lambda x: x[1], reverse=True)

                # عرض أفضل 5 مستخدمين
                top_users = room_user_points[:5]
                leaderboard_msg = "🏆 لوحة الصدارة - أفضل 5 مستخدمين:\n"
                
                medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                for i, (username, points) in enumerate(top_users):
                    medal = medals[i] if i < len(medals) else f"{i+1}️⃣"
                    level = self.calculate_user_level(points)
                    leaderboard_msg += f"{medal} @{username}: {points} XP (مستوى {level})\n"

                await self.highrise.chat(leaderboard_msg.strip())

            except Exception as e:
                print(f"Error in leaderboard command: {e}")
                await self.highrise.chat("❌ Error displaying leaderboard" if self.bot_lang == "en" else "❌ حدث خطأ في عرض لوحة الصدارة")

        # Commands display in English when user types اوامر
        if message.lower().strip() in ["اوامر", "أوامر", "الاوامر", "الأوامر"]:
            # Send English commands list in chat with 3-second intervals
            user_privileges = await self.highrise.get_room_privilege(user.id)
            is_owner = user.username in self.owners
            is_moderator = user_privileges.moderator
            is_admin = any(user.username.lower() == admin.lower() for admin in self.admins)

            try:
                # Part 1: Introduction and dance commands
                part1 = f"🤖 Bot Commands for @{user.username}:\n\n🎭 Dance Commands:\n• Type 1-140 for dance\n• loop [number] - continuous dance\n• رقصني - random dance\n• جوست/ghost - ghost dance\n• ريست/rest - sit continuously\n• 0 or stop - stop dance"

                await self.highrise.chat(part1)
                await asyncio.sleep(3)  # Wait 3 seconds

                # Part 2: Heart commands
                max_hearts = "50" if is_owner or is_moderator else "25" if is_admin else "5"
                part2 = f"❤️ Heart Commands:\n• h @username [count] - send hearts (max: {max_hearts})\n• w @username [count] - send wink\n• l @username [count] - send like\n\n📍 Quick Locations:\n• فوق/up - go up\n• تحت/down - go down\n• vip - enter VIP area"

                await self.highrise.chat(part2)
                await asyncio.sleep(3)

                # Part 3: Fun and info commands
                part3 = "🎪 Fun Commands:\n• كف @username - playful slap\n• اسحر @username - magic spell\n\nℹ️ Info Commands:\n• info @username - user info\n• ping - connection speed\n• time - bot uptime\n• list - dance numbers"

                await self.highrise.chat(part3)
                await asyncio.sleep(3)

                # Part 4: Self-control
                permission_text = "Owner" if is_owner else "Moderator" if is_moderator else "Admin" if is_admin else "User"
                part4 = f"🔄 Self Control:\n• لف الروم - random tour\n• توقف/stop - stop activity\n\n🎯 Your Permission: {permission_text}"

                await self.highrise.chat(part4)
                await asyncio.sleep(3)

                # Moderator/Admin commands (if user has permission)
                if is_owner or is_moderator or is_admin:
                    mod_part1 = "🛡️ Staff Commands - Part 1:\n• tel\وديني @user - teleport to user\n• اسحب @user - bring user\n• move @user1 @user2 - move user1 to user2\n• بدل @user - switch positions\n• follow @user - follow user"

                    await self.highrise.chat(mod_part1)
                    await asyncio.sleep(3)

                    mod_part2 = "🛡️ Staff Commands - Part 2:\n• h all [count] - hearts for all\n• all [number] - dance for all\n• fix @user - lock position\n• go @user - unlock position\n• vip @user - send to VIP"

                    await self.highrise.chat(mod_part2)
                    await asyncio.sleep(3)

                    mod_part3 = "🛡️ Staff Commands - Part 3:\n• !addswm @user message - special welcome\n• !removeswm @user - remove welcome\n• addvip @user - add VIP\n• !delvip @user - remove VIP\n• equip @user - copy outfit"

                    await self.highrise.chat(mod_part3)
                    await asyncio.sleep(3)

                # Owner-only commands
                if is_owner:
                    owner_part = "👑 Owner Commands:\n• !add @user - add bot admin\n• !remove @user - remove admin\n• !mod @user - give moderator\n• !delmod @user - remove moderator\n• !info @user - detailed info"

                    await self.highrise.chat(owner_part)
                    await asyncio.sleep(3)

                # Final message
                final_message = "🌟 Additional Info:\n• Follow bot owner: @_king_man_1\n• Use commands carefully!\n• Thank you for using the bot\n\n💡 All commands work in chat"

                await self.highrise.chat(final_message)

            except Exception as e:
                print(f"Error sending commands list in chat: {e}")
                # In case of error, send short message
                try:
                    error_message = "❌ Error displaying commands.\n\n🔧 Basic Commands:\n• Type 1-140 for dance\n• h @username - send heart\n• info @username - user info\n• ping - check connection\n\n📞 Help: @_king_man_1"
                    await self.highrise.chat(error_message)
                except Exception as chat_error:
                    print(f"Failed to send error message in chat: {chat_error}")
            
            return  # End of اوامر command processing

        if message.lower().startswith("كف "):
            parts = message.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()

                # فحص الحماية أولاً
                if self.is_user_protected(target_username):
                    await self.highrise.send_whisper(user.id, f"🛡️ المستخدم @{target_username} محمي ولا يمكن استخدام هذا الأمر عليه")
                    return

                # البحث عن المستخدم في الغرفة
                room_users = await self.highrise.get_room_users()
                target_user = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user = room_user
                        break

                if target_user:
                    try:
                        # الشخص الذي كتب الأمر يعمل رقصة الضربة
                        await self.highrise.send_emote("emote-slap", user.id)

                        # انتظار أقصر لسرعة أكبر
                        await asyncio.sleep(0.8)
                        await self.highrise.send_emote("emote-deathdrop", target_user.id)

                        await self.highrise.chat(f"👋 @{user.username} slapped @{target_username}! 💥" if self.bot_lang == "en" else f"👋 @{user.username} صفع @{target_username}! 💥")
                    except Exception as e:
                        await self.highrise.chat(f"Slap error: {e}" if self.bot_lang == "en" else f"خطأ في الصفعة: {e}")
                else:
                    await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")
            else:
                await self.highrise.chat("Type كف @username" if self.bot_lang == "en" else "اكتب كف @username")

        if message.lower().startswith(("heart", "h ", "love", "w", "l")):
            try:
                parts = message.split()
                reaction_type = "heart"  # افتراضي

                # تحديد نوع الرد بدقة
                first_word = parts[0].lower()
                if first_word == "w":
                    reaction_type = "wink"
                elif first_word == "l":
                    reaction_type = "thumbs"
                elif first_word in ["heart", "h", "love"]:
                    reaction_type = "heart"

                # فحص وجود معامل ثاني
                if len(parts) >= 2:
                    privileges = await self.highrise.get_room_privilege(user.id)
                    second_param = parts[1].lower()

                    # أمر "all" للمشرفين فقط
                    if second_param == "all" and await self.is_user_allowed(user):
                        count = 1
                        if len(parts) >= 3:
                            try:
                                requested_count = int(parts[2])
                                count = min(requested_count, 50)  # حد أقصى 50 للجميع
                            except ValueError:
                                await self.highrise.chat(f"❌ Wrong number. Example: {reaction_type} all 5" if self.bot_lang == "en" else f"❌ رقم خاطئ. مثال: {reaction_type} all 5")
                                return

                        roomUsers = (await self.highrise.get_room_users()).content
                        sent_count = 0
                        total_reactions = 0

                        for roomUser, _ in roomUsers:
                            # تجنب إرسال للبوت أو لنفس المرسل
                            if roomUser.id != self.bot_id and roomUser.id != user.id:
                                try:
                                    for _ in range(count):
                                        await self.highrise.react(reaction_type, roomUser.id)
                                        total_reactions += 1
                                        await asyncio.sleep(0.3)  # زيادة سرعة أفضل
                                    sent_count += 1
                                except Exception as e:
                                    print(f"Error sending reaction to {roomUser.username}: {e}")
                                    continue

                        emoji = "❤️" if reaction_type == "heart" else ("😉" if reaction_type == "wink" else "👍")
                        await self.highrise.chat(f"{emoji} Sent {total_reactions} {reaction_type} to {sent_count} users in the room" if self.bot_lang == "en" else f"{emoji} تم إرسال {total_reactions} {reaction_type} لـ {sent_count} مستخدم في الروم")

                    # أمر @ للمستخدم المحدد
                    elif parts[1].startswith("@"):
                        target_username = parts[1][1:].strip()
                        count = 100  # تغيير القيمة الافتراضية إلى 100 قلب

                        # تحديد العدد والحد الأقصى
                        if len(parts) >= 3:
                            try:
                                requested_count = int(parts[2])

                                # تحديد الحد الأقصى حسب الصلاحيات
                                if privileges.moderator or user.username in self.owners:
                                    max_count = 50
                                elif user.username in self.admins:
                                    max_count = 25
                                elif user.username in self.vips:
                                    max_count = 15
                                else:
                                    max_count = 5

                                count = min(requested_count, max_count)

                                if requested_count > max_count:
                                    role = "مشرف/أونر" if (privileges.moderator or user.username in self.owners) else ("أدمن" if user.username in self.admins else ("VIP" if user.username in self.vips else "مستخدم عادي"))
                                    await self.highrise.chat(f"⚠️ Your max as {role}: {max_count}" if self.bot_lang == "en" else f"⚠️ الحد الأقصى لك كـ{role}: {max_count}")

                            except ValueError:
                                await self.highrise.chat(f"❌ Invalid number. Example: {reaction_type} @{target_username} 3" if self.bot_lang == "en" else f"❌ رقم غير صحيح. مثال: {reaction_type} @{target_username} 3")
                                return

                        # البحث عن المستخدم
                        room_users = await self.highrise.get_room_users()
                        target_id = None

                        for room_user, _ in room_users.content:
                            if room_user.username.lower() == target_username.lower():
                                target_id = room_user.id
                                break

                        if target_id:
                            # منع إرسال قلوب للبوت
                            if target_id == self.bot_id:
                                await self.highrise.chat("❌ Cannot send reactions to the bot" if self.bot_lang == "en" else "❌ لا يمكن إرسال ردود للبوت")
                                return

                            try:
                                success_count = 0
                                for i in range(count):
                                    try:
                                        await self.highrise.react(reaction_type, target_id)
                                        success_count += 1
                                        await asyncio.sleep(0.1)  # سرعة أفضل - 0.1 ثانية بين كل قلب
                                    except Exception as single_error:
                                        print(f"Error sending reaction {i+1}: {single_error}")
                                        break

                                if success_count > 0:
                                    # إضافة نقاط للمستخدم عند إرسال ردود الفعل (2 نقطة لكل رد فعل)
                                    self.add_user_points(user.id, success_count * 2)
                                else:
                                    await self.highrise.chat(f"❌ Failed to send {reaction_type} to @{target_username}" if self.bot_lang == "en" else f"❌ فشل في إرسال {reaction_type} لـ @{target_username}")

                            except Exception as e:
                                await self.highrise.chat(f"❌ Send error: {str(e)[:50]}" if self.bot_lang == "en" else f"❌ خطأ في الإرسال: {str(e)[:50]}")
                        else:
                            await self.highrise.chat(f"❌ User @{target_username} is not in the room" if self.bot_lang == "en" else f"❌ المستخدم @{target_username} غير موجود في الروم")

                    else:
                        # رسائل المساعدة
                        role_limits = ""
                        if privileges.moderator or user.username in self.owners:
                            role_limits = " (حد أقصى: 50)"
                        elif user.username in self.admins:
                            role_limits = " (حد أقصى: 25)"
                        elif user.username in self.vips:
                            role_limits = " (حد أقصى: 15)"
                        else:
                            role_limits = " (حد أقصى: 5)"

                        # Heart command help message removed
                else:
                    # لا يوجد معامل ثاني
                    await self.highrise.chat(f"💡 Use: {reaction_type} @username [optional count]" if self.bot_lang == "en" else f"💡 استخدم: {reaction_type} @username [عدد اختياري]")

            except Exception as e:
                print(f"Error in heart system: {e}")
                await self.highrise.chat("❌ Error in reaction system" if self.bot_lang == "en" else "❌ حدث خطأ في نظام القلوب")

        

        # أوامر إرسال المستخدمين للأماكن الخاصة (للمشرفين فقط)
        # أمر vip @user
        if message.lower().startswith("vip ") and "@" in message and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) >= 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()

                # البحث عن المستخدم في الغرفة
                room_users = await self.highrise.get_room_users()
                target_user = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user = room_user
                        break

                if target_user:
                    try:
                        vip_position = Position(x=11.50, y=1.25 , z=22.0, facing='FrontRight')
                        await self.highrise.teleport(target_user.id, vip_position)
                    except Exception as e:
                        await self.highrise.chat(f"Teleport error: {e}" if self.bot_lang == "en" else f"خطأ في النقل: {e}")
                else:
                    await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")
            else:
                await self.highrise.chat("📝 Usage: vip @username" if self.bot_lang == "en" else "📝 استخدم: vip @username")

        # أمر mod @user
        elif message.lower().startswith("سجن") and "@" in message and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) >= 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()

                # البحث عن المستخدم في الغرفة
                room_users = await self.highrise.get_room_users()
                target_user = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user = room_user
                        break

                if target_user:
                    # فحص الحماية الخاصة
                    if self.is_user_protected(target_username):
                        await self.highrise.chat(f"❌ @{target_username} is protected and cannot be jailed" if self.bot_lang == "en" else f"❌ @{target_username} محمي ولا يمكن سجنه")
                        return

                    try:
                        # نقل المستخدم إلى السجن
                        mod_position = Position(x=50.5, y=0, z=2.5, facing='FrontLeft')
                        await self.highrise.teleport(target_user.id, mod_position)
                        
                        # سجن المستخدم مؤقتاً (منع أوامر النقل لمدة 5 دقائق)
                        self.jail_user(target_user.id, 5)
                        
                        await self.highrise.chat(f"🔒 @{target_username} jailed for 5 minutes ⛓️" if self.bot_lang == "en" else f"🔒 تم سجن @{target_username} لمدة 5 دقائق ⛓️")
                        await self.highrise.chat(f"⚠️ Cannot use teleport commands until time is up" if self.bot_lang == "en" else f"⚠️ لن يتمكن من استخدام أوامر النقل حتى انتهاء المدة")
                    except Exception as e:
                        await self.highrise.chat(f"Teleport error: {e}" if self.bot_lang == "en" else f"خطأ في النقل: {e}")
                else:
                    await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")
            else:
                await self.highrise.chat("📝 Usage: سجن @username" if self.bot_lang == "en" else "📝 استخدم: سجن @username")

        # أمر vip3 @user
        elif message.lower().startswith("vip3 ") and "@" in message and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) >= 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()

                # البحث عن المستخدم في الغرفة
                room_users = await self.highrise.get_room_users()
                target_user = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user = room_user
                        break

                if target_user:
                    try:
                        vip3_position = Position(x=4.7, y=16.5, z=4.5, facing='FrontLeft')
                        await self.highrise.teleport(target_user.id, vip3_position)
                        await self.highrise.chat(f"💎 {target_username} moved to VIP3 zone 🌟" if self.bot_lang == "en" else f"💎 تم نقل {target_username} إلى منطقة VIP3 🌟")
                    except Exception as e:
                        await self.highrise.chat(f"Teleport error: {e}" if self.bot_lang == "en" else f"خطأ في النقل: {e}")
                else:
                    await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")
            else:
                await self.highrise.chat("📝 Usage: vip3 @username" if self.bot_lang == "en" else "📝 استخدم: vip3 @username")

        

        # أوامر Summon (للمشرفين فقط)
        if (message.startswith("Summon") or 
            message.startswith("Summom") or 
            message.startswith("!summom") or
            message.startswith("/summom") or
            message.startswith("/summon") or 
            message.startswith("!summon")):
            if await self.is_user_allowed(user):
                target_username = message.split("@")[-1].strip()
                await self.teleport_user_next_to(target_username, user)

        # أوامر Wallet (للمشرفين فقط)
        if (message.startswith("Carteira") or 
            message.startswith("Wallet") or    
            message.startswith("!wallet") or       
            message.startswith("carteira")):
            if await self.is_user_allowed(user):
                wallet = (await self.highrise.get_wallet()).content
                await self.highrise.send_whisper(user.id, f"AMOUNT : {wallet[0].amount} {wallet[0].type}")
                await self.highrise.send_emote("emote-blowkisses")

        if message.startswith("!wallet"):
            if await self.is_user_allowed(user):
                wallet = (await self.highrise.get_wallet()).content
                await self.highrise.send_whisper(user.id, f"bot have {wallet[0].amount} {wallet[0].type}")
            else: 
                await self.highrise.send_whisper(user.id, f"your not mod")

        elif message.startswith("!kick") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) < 2:
                await self.highrise.chat("Usage: !kick @username")
                return

            mention = parts[1]
            username_to_kick = mention.lstrip('@')  # Remove the '@' symbol from the mention
            
            # فحص الحماية الخاصة
            if self.is_user_protected(username_to_kick):
                await self.highrise.chat(f"❌ @{username_to_kick} is protected and cannot be kicked" if self.bot_lang == "en" else f"❌ @{username_to_kick} محمي ولا يمكن طرده")
                return
            
            response = await self.highrise.get_room_users()
            users = [content[0] for content in response.content]  # Extract the User objects
            user_ids = [user.id for user in users]  # Extract the user IDs

            if username_to_kick.lower() in [user.username.lower() for user in users]:
                user_index = [user.username.lower() for user in users].index(username_to_kick.lower())
                user_id_to_kick = user_ids[user_index]
                
                try:
                    await self.highrise.moderate_room(user_id_to_kick, "kick")
                    await self.highrise.chat(f"{mention} Kicked from the room.")
                    self.admin_log.append({"action": "طرد", "target": username_to_kick, "by": user.username, "time": datetime.now().strftime("%H:%M")})
                    if len(self.admin_log) > 20:
                        self.admin_log.pop(0)
                except Exception as e:
                    await self.highrise.chat(f"❌ Error kicking {mention}: {e}" if self.bot_lang == "en" else f"❌ خطأ في طرد {mention}: {e}")
            else:
                await self.highrise.chat(f"❌ User {mention} is not in the room" if self.bot_lang == "en" else f"❌ المستخدم {mention} غير موجود في الغرفة")

        elif message.startswith("!mute") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) < 2:
                await self.highrise.chat("Usage: !mute @username [minutes]")
                return

            mention = parts[1]
            username_to_mute = mention.lstrip('@')
            
            # فحص الحماية الخاصة
            if self.is_user_protected(username_to_mute):
                await self.highrise.chat(f"❌ @{username_to_mute} is protected and cannot be muted" if self.bot_lang == "en" else f"❌ @{username_to_mute} محمي ولا يمكن كتمه")
                return
            
            # تحديد مدة الكتم (افتراضي 60 دقيقة)
            mute_duration = 3600  # 1 hour in seconds
            if len(parts) >= 3:
                try:
                    minutes = int(parts[2])
                    mute_duration = minutes * 60
                except ValueError:
                    await self.highrise.chat("❌ Mute duration must be a number (in minutes)" if self.bot_lang == "en" else "❌ مدة الكتم يجب أن تكون رقم (بالدقائق)")
                    return
            
            response = await self.highrise.get_room_users()
            users = [content[0] for content in response.content]
            user_ids = [user.id for user in users]

            if username_to_mute.lower() in [user.username.lower() for user in users]:
                user_index = [user.username.lower() for user in users].index(username_to_mute.lower())
                user_id_to_mute = user_ids[user_index]
                
                try:
                    await self.highrise.moderate_room(user_id_to_mute, "mute", mute_duration)
                    minutes_display = mute_duration // 60
                    await self.highrise.chat(f"Mute {mention} For {minutes_display} minutes.")
                except Exception as e:
                    await self.highrise.chat(f"❌ Error muting {mention}: {e}" if self.bot_lang == "en" else f"❌ خطأ في كتم {mention}: {e}")
            else:
                await self.highrise.chat(f"❌ User {mention} is not in the room" if self.bot_lang == "en" else f"❌ المستخدم {mention} غير موجود في الغرفة")

        elif message.startswith("!unmute") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) < 2:
                await self.highrise.chat("Usage: !unmute @username")
                return

            mention = parts[1]
            username_to_unmute = mention.lstrip('@')
            response = await self.highrise.get_room_users()
            users = [content[0] for content in response.content]
            user_ids = [user.id for user in users]

            if username_to_unmute.lower() in [user.username.lower() for user in users]:
                user_index = [user.username.lower() for user in users].index(username_to_unmute.lower())
                user_id_to_unmute = user_ids[user_index]
                
                try:
                    await self.highrise.moderate_room(user_id_to_unmute, "mute", 1)  # Unmute by setting 1 second
                    await self.highrise.chat(f"{mention} unmuted from the room.")
                except Exception as e:
                    await self.highrise.chat(f"❌ Error unmuting {mention}: {e}" if self.bot_lang == "en" else f"❌ خطأ في إلغاء كتم {mention}: {e}")
            else:
                await self.highrise.chat(f"❌ User {mention} is not in the room" if self.bot_lang == "en" else f"❌ المستخدم {mention} غير موجود في الغرفة")

        elif message.startswith("!ban") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) < 2:
                await self.highrise.chat("Usage: !ban @username [minutes]")
                return

            mention = parts[1]
            username_to_ban = mention.lstrip('@')
            
            # فحص الحماية الخاصة
            if self.is_user_protected(username_to_ban):
                await self.highrise.chat(f"❌ @{username_to_ban} is protected and cannot be banned" if self.bot_lang == "en" else f"❌ @{username_to_ban} محمي ولا يمكن حظره")
                return
            
            # تحديد مدة الحظر (افتراضي 60 دقيقة)
            ban_duration = 3600  # 1 hour in seconds
            if len(parts) >= 3:
                try:
                    minutes = int(parts[2])
                    ban_duration = minutes * 60
                except ValueError:
                    await self.highrise.chat("❌ Ban duration must be a number (in minutes)" if self.bot_lang == "en" else "❌ مدة الحظر يجب أن تكون رقم (بالدقائق)")
                    return
            
            response = await self.highrise.get_room_users()
            users = [content[0] for content in response.content]
            user_ids = [user.id for user in users]

            if username_to_ban.lower() in [user.username.lower() for user in users]:
                user_index = [user.username.lower() for user in users].index(username_to_ban.lower())
                user_id_to_ban = user_ids[user_index]
                
                try:
                    await self.highrise.moderate_room(user_id_to_ban, "ban", ban_duration)
                    minutes_display = ban_duration // 60
                    await self.highrise.chat(f"baned  {mention} for {minutes_display} minutes.")
                    self.admin_log.append({"action": f"حظر ({minutes_display} دقيقة)", "target": username_to_ban, "by": user.username, "time": datetime.now().strftime("%H:%M")})
                    if len(self.admin_log) > 20:
                        self.admin_log.pop(0)
                except Exception as e:
                    await self.highrise.chat(f"❌ Error banning {mention}: {e}" if self.bot_lang == "en" else f"❌ خطأ في حظر {mention}: {e}")
            else:
                await self.highrise.chat(f"❌ User {mention} is not in the room" if self.bot_lang == "en" else f"❌ المستخدم {mention} غير موجود في الغرفة")

        elif message.startswith("!unban") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) < 2:
                await self.highrise.chat("Usage: !unban @username")
                return

            mention = parts[1]
            username_to_unban = mention.lstrip('@')
            
            # للـ unban نحتاج user_id، يمكن البحث عنه عبر WebAPI
            try:
                user_info = await self.webapi.get_users(username=username_to_unban, limit=1)
                if user_info.users:
                    user_id_to_unban = user_info.users[0].user_id
                    await self.highrise.moderate_room(user_id_to_unban, "unban")
                    await self.highrise.chat(f"{mention} unbanned from the room.")
                else:
                    await self.highrise.chat(f"❌ User {mention} not found" if self.bot_lang == "en" else f"❌ المستخدم {mention} غير موجود")
            except Exception as e:
                await self.highrise.chat(f"❌ Error unbanning {mention}: {e}" if self.bot_lang == "en" else f"❌ خطأ في إلغاء حظر {mention}: {e}")

        # أوامر البقشيش العشوائي (للمشرفين فقط)
        if message == ("/tip 1 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            # Shuffle the list to ensure randomness
            random.shuffle(roomUsers)
            # Select the first users
            selected_users = roomUsers[:1]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:  # تجنب إرسال بقشيش للبوت نفسه
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:2]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 3 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:3]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 4 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:4]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 5 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:5]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 6 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:6]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 7 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:7]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 8 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:8]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 9 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:9]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 10 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:10]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 20 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:20]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 40 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:40]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        if message == ("/tip 60 5g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:60]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_5")
                    await self.highrise.chat(f"Tipped {roomUser.username} 5 gold.")

        # tip 10g commands
        if message == ("/tip 1 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:1]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 2 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:2]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 3 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:3]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 4 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:4]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 5 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:5]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 6 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:6]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 7 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:7]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 8 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:8]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 9 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:9]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 10 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:10]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 20 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:20]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 40 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:40]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        if message == ("/tip 60 10g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:60]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_10")
                    await self.highrise.chat(f"Tipped {roomUser.username} 10 gold.")

        # tip 1g commands
        if message == ("/tip 1 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:1]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 2 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:2]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 3 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:3]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 4 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:4]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 5 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:5]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 6 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:6]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 7 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:7]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 8 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:8]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 9 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:9]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 10 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:10]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 20 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:20]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 40 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:40]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        if message == ("/tip 60 1g") and await self.is_user_allowed(user):
            roomUsers = (await self.highrise.get_room_users()).content
            random.shuffle(roomUsers)
            selected_users = roomUsers[:60]
            for roomUser, _ in selected_users:
                if roomUser.id != self.bot_id:
                    await self.highrise.tip_user(roomUser.id, "gold_bar_1")
                    await self.highrise.chat(f"Tipped {roomUser.username} 1 gold.")

        # أوامر البقشيش (للمشرفين فقط)
        if message.lower().startswith("!tipall ") and await self.is_user_allowed(user):
            parts = message.split(" ")
            if len(parts) != 2:
                await self.highrise.chat("❌ Use: !tipall [amount]" if self.bot_lang == "en" else "❌ استخدم: !tipall [المبلغ]")
                return
            
            # فحص صحة المبلغ
            try:
                amount = int(parts[1])
                if amount <= 0:
                    await self.highrise.chat((f"❌ Amount must be greater than zero" if self.bot_lang == "en" else f"❌ يجب أن يكون المبلغ أكبر من صفر"))
                    return
            except ValueError:
                await self.highrise.chat("❌ Invalid amount" if self.bot_lang == "en" else "❌ المبلغ غير صحيح")
                return
            
            # فحص رصيد البوت
            try:
                bot_wallet = await self.highrise.get_wallet()
                bot_amount = bot_wallet.content[0].amount
                if bot_amount < amount:
                    await self.highrise.chat((f"❌ Insufficient bot balance. Current balance: {bot_amount}" if self.bot_lang == "en" else f"❌ رصيد البوت غير كافي. الرصيد الحالي: {bot_amount}"))
                    return
                
                # الحصول على جميع المستخدمين في الروم
                room_users = await self.highrise.get_room_users()
                users_count = len(room_users.content)
                
                # حساب إجمالي المبلغ المطلوب
                total_tip_amount = amount * users_count
                if bot_amount < total_tip_amount:
                    await self.highrise.chat(f"❌ Insufficient bot balance to send {amount} to {users_count} users" if self.bot_lang == "en" else f"❌ رصيد البوت غير كافي لإرسال {amount} لـ {users_count} مستخدم")
                    await self.highrise.chat(f"💰 Required: {total_tip_amount} | Available: {bot_amount}" if self.bot_lang == "en" else f"💰 المطلوب: {total_tip_amount} | المتاح: {bot_amount}")
                    return
                
                # قاموس قضبان الذهب
                bars_dictionary = {
                    10000: "gold_bar_10k",
                    5000: "gold_bar_5000", 
                    1000: "gold_bar_1k",
                    500: "gold_bar_500",
                    100: "gold_bar_100",
                    50: "gold_bar_50",
                    10: "gold_bar_10",
                    5: "gold_bar_5",
                    1: "gold_bar_1"
                }
                
                fees_dictionary = {
                    10000: 1000,
                    5000: 500,
                    1000: 100, 
                    500: 50,
                    100: 10,
                    50: 5,
                    10: 1,
                    5: 1,
                    1: 1
                }
                
                # إرسال البقشيش لكل مستخدم
                successful_tips = 0
                await self.highrise.chat(f"💰 Sending {amount} gold to {users_count} users..." if self.bot_lang == "en" else f"💰 بدء إرسال {amount} ذهب لـ {users_count} مستخدم...")
                
                for room_user, pos in room_users.content:
                    # تجنب إرسال بقشيش للبوت نفسه
                    if room_user.id == self.bot_id:
                        continue
                        
                    # تحويل المبلغ إلى قضبان ذهب
                    tip = []
                    remaining_amount = amount
                    total_cost = 0
                    
                    for bar_value in sorted(bars_dictionary.keys(), reverse=True):
                        if remaining_amount >= bar_value:
                            bar_count = remaining_amount // bar_value
                            remaining_amount = remaining_amount % bar_value
                            for i in range(bar_count):
                                tip.append(bars_dictionary[bar_value])
                                total_cost += bar_value + fees_dictionary[bar_value]
                    
                    # التأكد من كفاية الرصيد
                    current_wallet = await self.highrise.get_wallet()
                    current_amount = current_wallet.content[0].amount
                    if total_cost > current_amount:
                        await self.highrise.chat(f"❌ Sending stopped - insufficient balance at {room_user.username}" if self.bot_lang == "en" else f"❌ توقف الإرسال - رصيد غير كافي عند المستخدم {room_user.username}")
                        break
                    
                    # إرسال البقشيش
                    try:
                        for bar in tip:
                            await self.highrise.tip_user(room_user.id, bar)
                        successful_tips += 1
                    except Exception as e:
                        await self.highrise.chat((f"❌ Failed to send tip to {room_user.username}" if self.bot_lang == "en" else f"❌ فشل إرسال بقشيش لـ {room_user.username}"))
                        continue
                
                await self.highrise.chat((f"✅ Sent {amount} gold to {successful_tips} user(s) successfully!" if self.bot_lang == "en" else f"✅ تم إرسال {amount} ذهب لـ {successful_tips} مستخدم بنجاح!"))
                
            except Exception as e:
                await self.highrise.chat((f"❌ Error sending tip: {str(e)}" if self.bot_lang == "en" else f"❌ خطأ في إرسال البقشيش: {str(e)}"))

        # أمر شراء تعزيز (من محفظة البوت)
        if message.lower().strip() == "تعزيز":
            if await self.is_user_allowed(user):
                try:
                    # فحص رصيد البوت
                    bot_wallet = await self.highrise.get_wallet()
                    bot_amount = bot_wallet.content[0].amount
                    
                    boost_cost = 100 # تكلفة التعزيز الفعلي هي 100 ذهب 
                    
                    if bot_amount < boost_cost:
                        await self.highrise.chat((f"❌ Insufficient bot balance for boost. Required: {boost_cost} gold, Available: {bot_amount} gold" if self.bot_lang == "en" else f"❌ رصيد البوت غير كافي لشراء التعزيز. الرصيد المطلوب: {boost_cost} جولد، الرصيد الحالي: {bot_amount} جولد"))
                        return

                    # إرسال 100 جولد لشراء تعزيز (Boost)
                    # ملاحظة: يتم إرسال جولد بار بقيمة 100
                    await self.highrise.tip_user(self.bot_id, "gold_bar_100")
                    await self.highrise.chat((f"⚡ Room boost purchased successfully by @{user.username} from bot wallet!" if self.bot_lang == "en" else f"⚡ تم شراء تعزيز للغرفة بنجاح بواسطة @{user.username} من محفظة البوت!"))
                except Exception as e:
                    print(f"Error buying boost: {e}")
                    await self.highrise.chat((f"❌ Error while trying to purchase boost" if self.bot_lang == "en" else f"❌ حدث خطأ أثناء محاولة شراء التعزيز"))
            else:
                await self.highrise.chat((f"❌ This command is for moderators only" if self.bot_lang == "en" else f"❌ هذا الأمر مخصص للمشرفين فقط"))
            return

        if message.lower().startswith("!tipme ") and await self.is_user_allowed(user):
            try:
                parts = message.split(" ")
                if len(parts) != 2:
                    await self.highrise.chat((f"❌ Use: !tipme [amount]" if self.bot_lang == "en" else f"❌ استخدم: !tipme [المبلغ]"))
                    return
                    
                amount = int(parts[1])
                if amount <= 0:
                    await self.highrise.chat((f"❌ Amount must be greater than zero" if self.bot_lang == "en" else f"❌ يجب أن يكون المبلغ أكبر من صفر"))
                    return
                
                bars_dictionary = {
                    10000: "gold_bar_10k",
                    5000: "gold_bar_5000",
                    1000: "gold_bar_1k", 
                    500: "gold_bar_500",
                    100: "gold_bar_100",
                    50: "gold_bar_50",
                    10: "gold_bar_10",
                    5: "gold_bar_5",
                    1: "gold_bar_1"
                }
                
                fees_dictionary = {
                    10000: 1000,
                    5000: 500,
                    1000: 100,
                    500: 50, 
                    100: 10,
                    50: 5,
                    10: 1,
                    5: 1,
                    1: 1
                }
                
                # فحص رصيد البوت
                bot_wallet = await self.highrise.get_wallet()
                bot_amount = bot_wallet.content[0].amount
                
                if bot_amount < amount:
                    await self.highrise.chat((f"❌ Insufficient bot balance. Current balance: {bot_amount}" if self.bot_lang == "en" else f"❌ رصيد البوت غير كافي. الرصيد الحالي: {bot_amount}"))
                    return
                
                # تحويل المبلغ إلى قضبان وحساب التكلفة الإجمالية
                tip = []
                total_cost = 0
                remaining_amount = amount
                
                for bar_value in sorted(bars_dictionary.keys(), reverse=True):
                    if remaining_amount >= bar_value:
                        bar_count = remaining_amount // bar_value
                        remaining_amount %= bar_value
                        tip.extend([bars_dictionary[bar_value]] * bar_count)
                        total_cost += bar_count * (bar_value + fees_dictionary[bar_value])
                
                if total_cost > bot_amount:
                    await self.highrise.chat((f"❌ Insufficient bot balance to send the required amount" if self.bot_lang == "en" else f"❌ رصيد البوت غير كافي لإرسال المبلغ المطلوب"))
                    await self.highrise.chat((f"💰 Total cost: {total_cost} | Available: {bot_amount}" if self.bot_lang == "en" else f"💰 التكلفة الإجمالية: {total_cost} | المتاح: {bot_amount}"))
                    return
                
                # إرسال البقشيش للمستخدم
                for bar in tip:
                    await self.highrise.tip_user(user.id, bar)
                
                await self.highrise.chat((f"💰 Sent {amount} gold to @{user.username} successfully!" if self.bot_lang == "en" else f"💰 تم إرسال {amount} ذهب لـ @{user.username} بنجاح!"))
                
            except (IndexError, ValueError):
                await self.highrise.chat((f"❌ Invalid tip amount. Enter a valid number" if self.bot_lang == "en" else f"❌ مبلغ البقشيش غير صحيح. اكتب رقم صحيح"))
            except Exception as e:
                await self.highrise.chat((f"❌ Error sending tip: {str(e)}" if self.bot_lang == "en" else f"❌ خطأ في إرسال البقشيش: {str(e)}"))

        # ==================== تشغيل اكراميه تلقائيه (للأدمن والأونر) ====================
        if message.strip().startswith("تشغيل اكراميه تلقائيه") and await self.is_user_allowed(user):
            parts = message.strip().split()
            if len(parts) < 4:
                await self.highrise.chat("❌ استخدم: تشغيل اكراميه تلقائيه [المبلغ]")
            else:
                try:
                    amount = int(parts[3])
                    if amount <= 0:
                        await self.highrise.chat("❌ يجب أن يكون المبلغ أكبر من صفر")
                    else:
                        self.auto_tip_active = True
                        self.auto_tip_amount = amount
                        await self.highrise.chat(f"✅ تم تشغيل الاكراميه التلقائيه 💰\nسيتلقى كل داخل {amount} ذهب تلقائياً!")
                except ValueError:
                    await self.highrise.chat("❌ المبلغ غير صحيح، أدخل رقماً صحيحاً")

        # ==================== تعطيل اكراميه تلقائيه (للأدمن والأونر) ====================
        if message.strip() == "تعطيل اكراميه تلقائيه" and await self.is_user_allowed(user):
            self.auto_tip_active = False
            self.auto_tip_amount = 0
            await self.highrise.chat("🔴 تم تعطيل الاكراميه التلقائيه")

        # ==================== تشغيل تبرع vip (للأدمن والأونر) ====================
        if message.strip().startswith("تشغيل تبرع vip") and await self.is_user_allowed(user):
            parts = message.strip().split()
            if len(parts) < 4:
                await self.highrise.chat("❌ استخدم: تشغيل تبرع vip [المبلغ]")
            else:
                try:
                    amount = int(parts[3])
                    if amount <= 0:
                        await self.highrise.chat("❌ يجب أن يكون المبلغ أكبر من صفر")
                    else:
                        self.auto_tip_vip_active = True
                        self.auto_tip_vip_amount = amount
                        await self.highrise.chat(f"✅ تم تشغيل التبرع التلقائي للأعضاء المميزين ⭐\nسيتلقى كل عضو مميز {amount} ذهب عند دخوله!")
                except ValueError:
                    await self.highrise.chat("❌ المبلغ غير صحيح، أدخل رقماً صحيحاً")

        # ==================== تعطيل تبرع vip (للأدمن والأونر) ====================
        if message.strip() == "تعطيل تبرع vip" and await self.is_user_allowed(user):
            self.auto_tip_vip_active = False
            self.auto_tip_vip_amount = 0
            await self.highrise.chat("🔴 تم تعطيل التبرع التلقائي للأعضاء المميزين")

        # ==================== تعيين منطقة رقص (للأدمن والأونر) ====================
        if message.strip().startswith("تعيين منطقة رقص") and await self.is_user_allowed(user):
            parts = original_message.strip().split()
            radius = 4.0
            if len(parts) >= 4:
                try:
                    radius = float(parts[3])
                except ValueError:
                    pass
            try:
                room_users = await self.highrise.get_room_users()
                bot_pos = next((pos for ru, pos in room_users.content if ru.id == self.bot_id and isinstance(pos, Position)), None)
                if bot_pos is None:
                    bot_pos = self.bot_start_position
                if bot_pos is None:
                    await self.highrise.chat("❌ تعذّر تحديد موقع البوت الحالي. حدد الموقع يدوياً.")
                else:
                    self.dance_zone_pos = bot_pos
                    self.dance_zone_radius = radius
                    await self.highrise.chat(
                        f"📍 تم تعيين منطقة الرقص عند موقع البوت\n"
                        f"الإحداثيات: ({bot_pos.x:.1f}, {bot_pos.y:.1f}, {bot_pos.z:.1f})\n"
                        f"نصف القطر: {radius} وحدة\n"
                        f"اكتب: تشغيل منطقة رقص — لتفعيلها"
                    )
            except Exception as _dz_e:
                await self.highrise.chat(f"❌ خطأ: {_dz_e}")

        # ==================== تشغيل منطقة رقص (للأدمن والأونر) ====================
        if message.strip() == "تشغيل منطقة رقص" and await self.is_user_allowed(user):
            if self.dance_zone_pos is None:
                await self.highrise.chat("❌ لم يتم تعيين منطقة رقص بعد.\nاستخدم: تعيين منطقة رقص")
            else:
                self.dance_zone_active = True
                self.dance_zone_users.clear()
                # إيقاف المسح القديم إن وجد وبدء مسح جديد
                if self.dance_zone_scanner_task and not self.dance_zone_scanner_task.done():
                    self.dance_zone_scanner_task.cancel()
                self.dance_zone_scanner_task = asyncio.create_task(self.dance_zone_scanner())
                await self.highrise.chat(
                    f"✅ تم تشغيل منطقة الرقص 💃\n"
                    f"الإحداثيات: ({self.dance_zone_pos.x:.1f}, {self.dance_zone_pos.z:.1f})\n"
                    f"نصف القطر: {self.dance_zone_radius} وحدة\n"
                    f"كل من يذهب للمنطقة سيرقص جميع الرقصات تلقائياً!\n"
                    f"لإيقاف الرقص اكتب: 0 أو توقف"
                )

        # ==================== تعطيل منطقة رقص (للأدمن والأونر) ====================
        if message.strip() == "تعطيل منطقة رقص" and await self.is_user_allowed(user):
            self.dance_zone_active = False
            # إيقاف المسح الدوري
            if self.dance_zone_scanner_task and not self.dance_zone_scanner_task.done():
                self.dance_zone_scanner_task.cancel()
                self.dance_zone_scanner_task = None
            # إيقاف رقص جميع المستخدمين في المنطقة
            for uid in list(self.dance_zone_users):
                if self.user_emote_loops.get(uid) == "dance_zone":
                    await self.stop_emote_loop(uid)
            self.dance_zone_users.clear()
            await self.highrise.chat("🔴 تم تعطيل منطقة الرقص وإيقاف رقص الجميع")

        # ==================== رقصة منطقة [اسم] (للأدمن والأونر) ====================
        if message.strip().startswith("رقصة منطقة") and await self.is_user_allowed(user):
            parts = original_message.strip().split()
            free_dance_choices = {
                "hyped":      "emote-hyped",
                "celebrate":  "emote-celebrate",
                "step":       "emote-celebrationstep",
                "timejump":   "emote-timejump",
                "float":      "emote-float",
                "gravity":    "emote-gravity",
                "zombie":     "emote-zombierun",
                "snake":      "emote-snake",
                "frog":       "emote-frog",
                "punk":       "emote-punkguitar",
                "boxer":      "emote-boxer",
                "skate":      "emote-iceskating",
                "astronaut":  "emote-astronaut",
                "launch":     "emote-launch",
            }
            if len(parts) < 3:
                names = " | ".join(free_dance_choices.keys())
                await self.highrise.chat(f"💃 استخدم: رقصة منطقة [اسم]\nالأسماء المتاحة:\n{names}")
            else:
                key = parts[2].lower()
                if key in free_dance_choices:
                    self.dance_zone_emote = free_dance_choices[key]
                    await self.highrise.chat(f"✅ تم تغيير رقصة المنطقة إلى: {key} ({self.dance_zone_emote})")
                elif key in free_emotes:
                    self.dance_zone_emote = free_emotes[key]["value"]
                    await self.highrise.chat(f"✅ تم تغيير رقصة المنطقة إلى: {self.dance_zone_emote}")
                else:
                    names = " | ".join(free_dance_choices.keys())
                    await self.highrise.chat(f"❌ اسم غير صحيح. الأسماء المتاحة:\n{names}")

        # ==================== اضافه قائمه @username (للأدمن والأونر) ====================
        if message.strip().startswith("اضافه قائمه") and await self.is_user_allowed(user):
            parts = original_message.strip().split()
            if len(parts) < 3:
                await self.highrise.chat("❌ استخدم: اضافه قائمه @اسم_المستخدم")
            else:
                target = parts[2].lstrip("@")
                if not hasattr(self, 'bot_blacklist'):
                    self.bot_blacklist = []
                if any(b.lower() == target.lower() for b in self.bot_blacklist):
                    await self.highrise.chat(f"⚠️ @{target} موجود بالفعل في القائمة السوداء")
                else:
                    self.bot_blacklist.append(target)
                    self.save_blacklist()
                    await self.highrise.chat(f"🚫 تم إضافة @{target} إلى القائمة السوداء\nلن يتمكن من استخدام البوت نهائياً")

        # ==================== حذف قائمه @username (للأدمن والأونر) ====================
        if message.strip().startswith("حذف قائمه") and await self.is_user_allowed(user):
            parts = original_message.strip().split()
            if len(parts) < 3:
                await self.highrise.chat("❌ استخدم: حذف قائمه @اسم_المستخدم")
            else:
                target = parts[2].lstrip("@")
                if not hasattr(self, 'bot_blacklist'):
                    self.bot_blacklist = []
                match = next((b for b in self.bot_blacklist if b.lower() == target.lower()), None)
                if match:
                    self.bot_blacklist.remove(match)
                    self.save_blacklist()
                    await self.highrise.chat(f"✅ تم حذف @{target} من القائمة السوداء")
                else:
                    await self.highrise.chat(f"⚠️ @{target} غير موجود في القائمة السوداء")

        # ==================== عرض القائمة السوداء (للأدمن والأونر) ====================
        if message.strip() == "عرض قائمه" and await self.is_user_allowed(user):
            if not hasattr(self, 'bot_blacklist') or not self.bot_blacklist:
                await self.highrise.chat("📋 القائمة السوداء فارغة")
            else:
                lines = [f"{i}. {u}" for i, u in enumerate(self.bot_blacklist, 1)]
                header = f"🚫 القائمة السوداء ({len(self.bot_blacklist)} مستخدم):\n"
                chunk = header
                for line in lines:
                    if len(chunk) + len(line) + 1 > 250:
                        await self.highrise.chat(chunk)
                        chunk = line + "\n"
                    else:
                        chunk += line + "\n"
                if chunk.strip():
                    await self.highrise.chat(chunk.strip())

        # إضافة أمر addtele لحفظ الأماكن (متاح لجميع المستخدمين)
        if message.lower().startswith("addtele "):
            parts = message.split()
            if len(parts) >= 2:
                location_name = parts[1]
                room_users = await self.highrise.get_room_users()
                user_position = None

                for room_user, position in room_users.content:
                    if room_user.id == user.id:
                        user_position = position
                        break

                if user_position:
                    # تحديث موقع في الذاكرة
                    self.teleport_locations[location_name] = user_position
                    # حفظ في الملف
                    self.save_teleport_locations()
                    await self.highrise.chat((f"📍 Location '{location_name}' saved successfully ✅" if self.bot_lang == "en" else f"📍 تم حفظ الموقع '{location_name}' بنجاح ✅"))
                    await self.highrise.chat((f"💡 Type '{location_name}' to teleport to this location" if self.bot_lang == "en" else f"💡 اكتب '{location_name}' للانتقال إلى هذا المكان"))
                    await self.highrise.chat((f"🎯 Or type '{location_name} @user' to send someone else" if self.bot_lang == "en" else f"🎯 أو اكتب '{location_name} @user' لإرسال شخص آخر"))
                else:
                    await self.highrise.chat((f"❌ Your location was not found" if self.bot_lang == "en" else f"❌ لم يتم العثور على موقعك"))
            else:
                await self.highrise.chat((f"📝 Usage: addtele location_name" if self.bot_lang == "en" else f"📝 استخدم: addtele اسم_المكان"))
                await self.highrise.chat((f"💡 Example: addtele dance_hall" if self.bot_lang == "en" else f"💡 مثال: addtele صالة_الرقص"))

        # إضافة أمر removetele لحذف الأماكن المحفوظة
        if message.lower().startswith("removetele "):
            if user.username in self.owners:
                parts = message.split()
                if len(parts) >= 2:
                    location_name = parts[1]
                    
                    if location_name in self.teleport_locations:
                        del self.teleport_locations[location_name]
                        self.save_teleport_locations()
                        await self.highrise.chat((f"Location {location_name} deleted ❌" if self.bot_lang == "en" else f"تم حذف الموقع {location_name} ❌"))
                    else:
                        await self.highrise.chat((f"Location {location_name} not found in list" if self.bot_lang == "en" else f"الموقع {location_name} غير موجود في القائمة"))
                else:
                    await self.highrise.chat((f"Please specify the location name to delete" if self.bot_lang == "en" else f"الرجاء تحديد اسم الموقع المراد حذفه"))
            else:
                await self.highrise.chat("You do not have permission to use this command" if self.bot_lang == "en" else "ليس لديك صلاحية لاستخدام هذا الأمر")

        # إضافة أمر لإرسال المستخدمين إلى الأماكن المحفوظة
        if message.lower().startswith("teleport ") and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) >= 3 and parts[1].startswith("@"):
                target_username = parts[1][1:]
                location_name = parts[2]

                if location_name in self.teleport_locations:
                    room_users = await self.highrise.get_room_users()
                    target_user = None
                    for room_user, _ in room_users.content:
                        if room_user.username.lower() == target_username.lower():
                            target_user = room_user
                            break

                    if target_user:
                        await self.highrise.teleport(target_user.id, self.teleport_locations[location_name])
                        await self.highrise.chat((f"@{target_username} sent to {location_name} ✅" if self.bot_lang == "en" else f"تم إرسال @{target_username} إلى {location_name} ✅"))
                    else:
                        await self.highrise.chat((f"User @{target_username} not found" if self.bot_lang == "en" else f"المستخدم @{target_username} غير موجود"))
                else:
                    await self.highrise.chat((f"Location {location_name} not found" if self.bot_lang == "en" else f"الموقع {location_name} غير موجود"))

        # أمر لعرض قائمة الأماكن المحفوظة
        if message.lower().strip() in ["places", "اماكن", "مواقع", "locations"]:
            if not self.teleport_locations:
                await self.highrise.chat((f"📋 No saved locations" if self.bot_lang == "en" else f"📋 لا توجد أماكن محفوظة"))
                return
            
            places_list = []
            for i, (location_name, position) in enumerate(self.teleport_locations.items(), 1):
                places_list.append(f"{i}. {location_name}")
            
            # إرسال القائمة في رسالة واحدة مختصرة
            leaderboard_msg = "📍 الأماكن المحفوظة:\n" + "\n".join(places_list)
            if len(leaderboard_msg) > 500:
                leaderboard_msg = leaderboard_msg[:497] + "..."
            
            await self.highrise.chat(leaderboard_msg)
            await self.highrise.chat((f"💡 Type a location name to teleport there" if self.bot_lang == "en" else f"💡 اكتب اسم المكان للانتقال إليه"))
            return

        # التحقق إذا كانت الرسالة عبارة عن اسم مكان محفوظ للانتقال إليه
        if message.strip() in self.teleport_locations:
            try:
                # التحقق إذا كان هناك تاق لمستخدم آخر
                parts = message.split()
                target_user = user
                
                if len(parts) >= 2 and parts[1].startswith("@"):
                    # هذا الجزء معالج بالفعل في كود teleport، لكننا سنضيفه هنا للسرعة
                    target_username = parts[1][1:].strip()
                    room_users = await self.highrise.get_room_users()
                    for room_user, _ in room_users.content:
                        if room_user.username.lower() == target_username.lower():
                            target_user = room_user
                            break
                
                await self.highrise.teleport(target_user.id, self.teleport_locations[message.strip()])
                if target_user.id != user.id:
                    await self.highrise.chat((f"✅ @{target_user.username} moved to {message.strip()}" if self.bot_lang == "en" else f"✅ تم نقل @{target_user.username} إلى {message.strip()}"))
                return
            except Exception as e:
                print(f"Error teleporting to saved location: {e}")

        # أمر تفعيل النقل التلقائي بالنقر الذكي
        if message.lower() in ["on", "!on"]:
            self.teleport_on_click[user.id] = True
            await self.highrise.chat((f"🎯 Smart teleport activated for @{user.username}" if self.bot_lang == "en" else f"🎯 تم تفعيل النقل الذكي لـ @{user.username}"))
            await self.highrise.chat((f"💡 Tap anywhere to teleport there!" if self.bot_lang == "en" else f"💡 اضغط على أي مكان وسيتم نقلك إليه!"))

        # أمر تفعيل النقل الذكي لجميع المستخدمين في الغرفة (للمشرفين والمالك فقط)
        if message.lower() in ["on all", "!on all"]:
            _uname_check = user.username.lower()
            _is_allowed = any(_uname_check == o.lower() for o in self.owners) or any(_uname_check == a.lower() for a in self.admins)
            if _is_allowed:
                try:
                    room_users = (await self.highrise.get_room_users()).content
                    count = 0
                    for room_user, _ in room_users:
                        self.teleport_on_click[room_user.id] = True
                        count += 1
                    await self.highrise.chat((f"🎯 Smart teleport activated for all {count} users in the room!" if self.bot_lang == "en" else f"🎯 تم تفعيل النقل الذكي لجميع المستخدمين في الغرفة ({count} مستخدم)!"))
                    await self.highrise.chat((f"💡 Everyone can now tap anywhere to teleport!" if self.bot_lang == "en" else f"💡 الجميع الآن يستطيع الضغط على أي مكان وسيتم نقله إليه!"))
                except Exception as e:
                    print(f"Error activating on all: {e}")
                    await self.highrise.chat((f"❌ Failed to activate for all users." if self.bot_lang == "en" else f"❌ فشل تفعيل النقل لجميع المستخدمين."))
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # ==================== أوامر المشرفين والمالك ====================
        _uname = user.username.lower()
        _is_mod = any(_uname == o.lower() for o in self.owners) or any(_uname == a.lower() for a in self.admins)

        # 1. إيقاف الانتقال السريع لجميع المستخدمين
        if message.lower() in ["off all", "!off all"]:
            if _is_mod:
                try:
                    room_users = (await self.highrise.get_room_users()).content
                    count = 0
                    for room_user, _ in room_users:
                        self.teleport_on_click[room_user.id] = False
                        count += 1
                    await self.highrise.chat(f"❌ تم إيقاف النقل الذكي لجميع المستخدمين ({count} مستخدم)!" if self.bot_lang != "en" else f"❌ Smart teleport disabled for all {count} users!")
                except Exception as e:
                    print(f"Error off all: {e}")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # 2. عرض عدد المستخدمين في الغرفة
        if message.lower() in ["عدد", "count", "!count"]:
            if _is_mod:
                try:
                    room_users = (await self.highrise.get_room_users()).content
                    count = len(room_users)
                    await self.highrise.chat(f"👥 عدد المستخدمين في الغرفة الآن: {count}" if self.bot_lang != "en" else f"👥 Users in room right now: {count}")
                except Exception as e:
                    print(f"Error count: {e}")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # 3. قائمة أسماء المستخدمين في الغرفة
        if message.lower() in ["قائمة", "list", "!list"]:
            if _is_mod:
                try:
                    room_users = (await self.highrise.get_room_users()).content
                    names = [ru.username for ru, _ in room_users]
                    chunk = ""
                    for name in names:
                        if len(chunk) + len(name) + 3 > 200:
                            await self.highrise.chat(f"👤 {chunk}")
                            chunk = name
                        else:
                            chunk = chunk + ", " + name if chunk else name
                    if chunk:
                        await self.highrise.chat(f"👤 {chunk}")
                except Exception as e:
                    print(f"Error list: {e}")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # 4. إرسال إعلان للجميع
        if message.lower().startswith("إعلان ") or message.lower().startswith("اعلان "):
            if _is_mod:
                announcement = message[6:].strip() if message.lower().startswith("إعلان ") else message[6:].strip()
                if announcement:
                    await self.highrise.chat(f"📢 إعلان من @{user.username}: {announcement}" if self.bot_lang != "en" else f"📢 Announcement from @{user.username}: {announcement}")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # 5. تفعيل وضع الصمت (البوت لا يرد على الأوامر العادية)
        if message.lower() in ["وضع صامت", "silent", "!silent"]:
            if _is_mod:
                self.silent_mode = True
                await self.highrise.chat(f"🔇 تم تفعيل وضع الصمت، البوت لن يرد على الأوامر العادية." if self.bot_lang != "en" else f"🔇 Silent mode ON. Bot will ignore regular commands.")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # 6. إيقاف وضع الصمت
        if message.lower() in ["وضع نشط", "unsilent", "!unsilent"]:
            if _is_mod:
                self.silent_mode = False
                await self.highrise.chat(f"🔊 تم إيقاف وضع الصمت، البوت عاد للعمل بشكل طبيعي." if self.bot_lang != "en" else f"🔊 Silent mode OFF. Bot is active again.")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # 7. تجميد مستخدم (إبقاؤه في مكانه)
        if message.lower().startswith("تجميد @") or message.lower().startswith("!تجميد @"):
            if _is_mod:
                try:
                    prefix = "تجميد @" if message.lower().startswith("تجميد @") else "!تجميد @"
                    target_name = message[len(prefix):].strip()
                    room_users = (await self.highrise.get_room_users()).content
                    target = next((ru for ru, _ in room_users if ru.username.lower() == target_name.lower()), None)
                    if target:
                        target_pos = next((pos for ru, pos in room_users if ru.id == target.id), None)
                        if target_pos:
                            self.frozen_users[target.id] = target_pos
                            await self.highrise.chat(f"🧊 تم تجميد @{target.username}، لن يستطيع التحرك." if self.bot_lang != "en" else f"🧊 @{target.username} has been frozen.")
                    else:
                        await self.highrise.chat(f"❌ لم يتم العثور على @{target_name} في الغرفة." if self.bot_lang != "en" else f"❌ @{target_name} not found in room.")
                except Exception as e:
                    print(f"Error freeze: {e}")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # 8. تحرير مستخدم مجمّد
        if message.lower().startswith("تحرير @") or message.lower().startswith("!تحرير @"):
            if _is_mod:
                prefix = "تحرير @" if message.lower().startswith("تحرير @") else "!تحرير @"
                target_name = message[len(prefix):].strip()
                try:
                    room_users = (await self.highrise.get_room_users()).content
                    target = next((ru for ru, _ in room_users if ru.username.lower() == target_name.lower()), None)
                    if target and target.id in self.frozen_users:
                        del self.frozen_users[target.id]
                        await self.highrise.chat(f"✅ تم تحرير @{target.username}، يمكنه التحرك الآن." if self.bot_lang != "en" else f"✅ @{target.username} has been unfrozen.")
                    else:
                        await self.highrise.chat(f"❌ @{target_name} غير مجمّد أصلاً." if self.bot_lang != "en" else f"❌ @{target_name} is not frozen.")
                except Exception as e:
                    print(f"Error unfreeze: {e}")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # 9. جمع جميع المستخدمين عند موقع البوت
        if message.lower() in ["جمع الكل", "gather", "!gather"]:
            if _is_mod:
                try:
                    room_users = (await self.highrise.get_room_users()).content
                    bot_pos = None
                    for ru, pos in room_users:
                        if ru.id == self.bot_id:
                            bot_pos = pos
                            break
                    if bot_pos:
                        gathered = 0
                        for ru, _ in room_users:
                            if ru.id != self.bot_id:
                                try:
                                    await self.highrise.teleport(ru.id, bot_pos)
                                    gathered += 1
                                except:
                                    pass
                        await self.highrise.chat(f"🫂 تم جمع {gathered} مستخدم عند موقع البوت!" if self.bot_lang != "en" else f"🫂 Gathered {gathered} users to bot's location!")
                    else:
                        await self.highrise.chat(f"❌ لم يتم العثور على موقع البوت." if self.bot_lang != "en" else f"❌ Could not find bot's position.")
                except Exception as e:
                    print(f"Error gather: {e}")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # 10. تحذير مستخدم (بعد 3 تحذيرات يتم طرده)
        if message.lower().startswith("تحذير @") or message.lower().startswith("!تحذير @"):
            if _is_mod:
                try:
                    prefix = "تحذير @" if message.lower().startswith("تحذير @") else "!تحذير @"
                    target_name = message[len(prefix):].strip()
                    room_users = (await self.highrise.get_room_users()).content
                    target = next((ru for ru, _ in room_users if ru.username.lower() == target_name.lower()), None)
                    if target:
                        self.warn_count[target.id] = self.warn_count.get(target.id, 0) + 1
                        warns = self.warn_count[target.id]
                        if warns >= 3:
                            await self.highrise.chat(f"🚫 @{target.username} وصل لـ 3 تحذيرات وتم طرده!" if self.bot_lang != "en" else f"🚫 @{target.username} reached 3 warnings and was kicked!")
                            await self.highrise.kick(target.id)
                            self.warn_count[target.id] = 0
                        else:
                            remaining = 3 - warns
                            await self.highrise.chat(f"⚠️ تحذير لـ @{target.username}! ({warns}/3) - {remaining} تحذير متبقي قبل الطرد." if self.bot_lang != "en" else f"⚠️ Warning to @{target.username}! ({warns}/3) - {remaining} warning(s) left before kick.")
                            await self.highrise.send_whisper(target.id, f"⚠️ لقد تلقيت تحذيراً من الإدارة ({warns}/3). بعد 3 تحذيرات سيتم طردك." if self.bot_lang != "en" else f"⚠️ You received a warning from staff ({warns}/3). At 3 warnings you will be kicked.")
                    else:
                        await self.highrise.chat(f"❌ لم يتم العثور على @{target_name} في الغرفة." if self.bot_lang != "en" else f"❌ @{target_name} not found in room.")
                except Exception as e:
                    print(f"Error warn: {e}")
            else:
                await self.highrise.chat(f"⛔ @{user.username} هذا الأمر للمشرفين والمالك فقط." if self.bot_lang != "en" else f"⛔ @{user.username} Moderators and owners only.")

        # ==================== نهاية أوامر المشرفين والمالك ====================

        # أوامر إلغاء تفعيل النقل التلقائي بالنقر
        if message.lower() in ["off", "!off"]:
            if user.id in self.teleport_on_click:
                self.teleport_on_click[user.id] = False
                await self.highrise.chat((f"❌ Smart teleport disabled for @{user.username}" if self.bot_lang == "en" else f"❌ تم إيقاف النقل الذكي لـ @{user.username}"))
            else:
                await self.highrise.chat((f"@{user.username} Smart teleport is not active" if self.bot_lang == "en" else f"@{user.username} النقل الذكي غير مفعل أصلاً"))

        # أمر فحص حالة النقل التلقائي
        if message.lower() == "status":
            if user.id in self.teleport_on_click and self.teleport_on_click[user.id]:
                current_floor = "غير محدد"
                if hasattr(self, 'user_last_floor') and user.id in self.user_last_floor:
                    current_floor = str(self.user_last_floor[user.id])
                await self.highrise.chat((f"🎯 Smart teleport is active for @{user.username}" if self.bot_lang == "en" else f"🎯 النقل الذكي مفعل لـ @{user.username}"))
                await self.highrise.chat(f"📍 Current floor: {current_floor}" if self.bot_lang == "en" else f"📍 الطابق الحالي: {current_floor}")
            else:
                await self.highrise.chat(f"❌ Smart teleport is disabled for @{user.username}" if self.bot_lang == "en" else f"❌ النقل الذكي معطل لـ @{user.username}")

        # أمر فحص حالة السجن
        if message.lower() == "jail status":
            if self.is_user_jailed(user.id):
                import time as time_module
                remaining_time = int((self.jailed_users[user.id] - time_module.time()) / 60)
                await self.highrise.chat(f"🔒 @{user.username} is jailed for {remaining_time + 1} more minutes" if self.bot_lang == "en" else f"🔒 @{user.username} مسجون لمدة {remaining_time + 1} دقيقة أخرى")
            else:
                await self.highrise.chat(f"✅ @{user.username} is not jailed" if self.bot_lang == "en" else f"✅ @{user.username} ليس مسجوناً")

        # أمر إطلاق سراح مبكر (للمشرفين فقط)
        if message.lower().startswith("اطلاق") and "@" in message and await self.is_user_allowed(user):
            parts = message.split()
            if len(parts) >= 2 and parts[1].startswith("@"):
                target_username = parts[1][1:].strip()
                
                # البحث عن المستخدم في الغرفة
                room_users = await self.highrise.get_room_users()
                target_user = None
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        target_user = room_user
                        break

                if target_user:
                    if self.is_user_jailed(target_user.id):
                        del self.jailed_users[target_user.id]
                        await self.highrise.chat(f"🔓 @{target_username} has been released early" if self.bot_lang == "en" else f"🔓 تم إطلاق سراح @{target_username} مبكراً")
                    else:
                        await self.highrise.chat(f"❌ @{target_username} is not jailed" if self.bot_lang == "en" else f"❌ @{target_username} ليس مسجوناً")
                else:
                    await self.highrise.chat(f"❌ User {target_username} is not in the room" if self.bot_lang == "en" else f"❌ المستخدم {target_username} غير موجود في الغرفة")
            else:
                await self.highrise.chat("📝 Usage: اطلاق @username" if self.bot_lang == "en" else "📝 استخدم: اطلاق @username")

        # أمر !invite لإرسال دعوات حقيقية بزر الدخول لجميع المشتركين (للمشرفين فقط)
        if message.lower().startswith("دعوة") and await self.is_user_allowed(user):
            try:
                invite_text = "تعال انضم إلينا في الغرفة! 🎉"

                if not self.subscribers:
                    await self.highrise.chat("❌ No subscribers to send invites to. Ask users to type: اشتراك" if self.bot_lang == "en" else "❌ لا يوجد مشتركون لإرسال الدعوة لهم. اطلب من المستخدمين كتابة: اشتراك")
                    return

                await self.highrise.chat(f"📨 @{user.username} is sending invites to subscribers..." if self.bot_lang == "en" else f"📨 @{user.username} يرسل دعوات للمشتركين...")

                subscriber_ids = set(self.subscribers.keys())
                success_count = 0
                fail_count = 0

                # إرسال عبر المحادثات الموجودة أولاً
                conversations_resp = await self.highrise.get_conversations()
                reached = set()

                if not isinstance(conversations_resp, Exception) and not hasattr(conversations_resp, 'message'):
                    conversations = getattr(conversations_resp, 'conversations', [])
                    for conv in conversations:
                        member_ids = {m.id for m in getattr(conv, 'members', [])}
                        matched = member_ids & subscriber_ids
                        if not matched:
                            continue
                        try:
                            res = await self.highrise.send_message(
                                conv.id,
                                invite_text,
                                "invite",
                                self.room_id,
                            )
                            if res is None:
                                reached |= matched
                                success_count += len(matched)
                            else:
                                print(f"[!invite] فشل conv {conv.id}: {res}")
                        except Exception as e:
                            print(f"[!invite] استثناء conv {conv.id}: {e}")

                # للمشتركين بدون محادثة جرب send_message_bulk
                unreached = subscriber_ids - reached
                for uid in unreached:
                    try:
                        res = await self.highrise.send_message_bulk(
                            [uid], invite_text, "invite", self.room_id
                        )
                        if res is None:
                            success_count += 1
                        else:
                            fail_count += 1
                            print(f"[!invite] bulk فشل لـ {uid}: {res}")
                    except Exception as e:
                        fail_count += 1
                        print(f"[!invite] bulk استثناء لـ {uid}: {e}")
                    await asyncio.sleep(0.5)

                await self.highrise.chat(
                    f"✅ تم إرسال الدعوة لـ {success_count} مشترك"
                    + (f" | ❌ فشل: {fail_count}" if fail_count else "")
                )

            except Exception as e:
                print(f"Error in !invite command: {e}")
                await self.highrise.chat("❌ Error sending invites" if self.bot_lang == "en" else "❌ حدث خطأ في إرسال الدعوات")

        elif message.lower() == "دعوة" and not await self.is_user_allowed(user):
            await self.highrise.chat("❌ !invite command is for moderators only" if self.bot_lang == "en" else "❌ أمر !invite متاح للمشرفين فقط")

        # ==================== أمر الاشتراك ====================
        if message.strip() == "اشتراك":
            if user.id in self.subscribers:
                await self.highrise.send_whisper(user.id, "✅ أنت مشترك بالفعل! ستصلك دعوة كل دقيقتين.")
            else:
                self.subscribers[user.id] = user.username
                self.save_subscribers()
                await self.highrise.send_whisper(user.id, f"🎉 تم تسجيلك في الاشتراك يا @{user.username}!\nستصلك دعوة للغرفة كل دقيقتين تلقائياً.\nلإلغاء الاشتراك أرسل: إلغاء اشتراك")
                await self.highrise.chat(f"📬 @{user.username} subscribed successfully!" if self.bot_lang == "en" else f"📬 @{user.username} تم تسجيلك في الاشتراك بنجاح!")
                # فتح محادثة DM مع المستخدم لضمان وصول الدعوات لاحقاً
                try:
                    await self.highrise.send_message_bulk(
                        [user.id],
                        f"مرحباً @{user.username}! تم تسجيلك في الاشتراك. ستصلك دعوات للغرفة تلقائياً.",
                        "text",
                    )
                except Exception as e:
                    print(f"[Subscription] لم يمكن فتح محادثة مع {user.username}: {e}")
                print(f"[Subscription] {user.username} اشترك")

        elif message.strip() in ("إلغاء اشتراك", "الغاء اشتراك", "إلغاء الاشتراك", "الغاء الاشتراك"):
            if user.id in self.subscribers:
                del self.subscribers[user.id]
                self.save_subscribers()
                await self.highrise.send_whisper(user.id, f"👋 تم إلغاء اشتراكك يا @{user.username}. يمكنك الاشتراك مجدداً في أي وقت.")
                await self.highrise.chat(f"📭 @{user.username} unsubscribed." if self.bot_lang == "en" else f"📭 @{user.username} تم إلغاء اشتراكك.")
                print(f"[Subscription] {user.username} ألغى الاشتراك")
            else:
                await self.highrise.send_whisper(user.id, "❌ أنت لست مشتركاً حالياً. أرسل: اشتراك للتسجيل.")

        # أمر عرض قائمة المشتركين (للمشرفين فقط)
        if message.strip() == "!مشتركين" and await self.is_user_allowed(user):
            count = len(self.subscribers)
            if count == 0:
                await self.highrise.chat("📭 No subscribers currently." if self.bot_lang == "en" else "📭 لا يوجد مشتركون حالياً.")
            else:
                names = "، ".join(self.subscribers.values())
                await self.highrise.chat(f"📋 Subscribers ({count}): {names}" if self.bot_lang == "en" else f"📋 المشتركون ({count}): {names}")

        # أمر تفريغ قائمة المشتركين (للملاك فقط)
        if message.strip() == "!مسح مشتركين" and user.username in self.owners:
            count = len(self.subscribers)
            self.subscribers.clear()
            self.save_subscribers()
            await self.highrise.chat(f"🗑️ Subscriber list cleared ({count} subscribers)." if self.bot_lang == "en" else f"🗑️ تم مسح قائمة المشتركين ({count} مشترك).")

        # أمر عرض قائمة المحميين الخاصين
        if message.startswith(("اضافه محمي", "addspecial")):
            if user.username in self.owners:
                parts = message.split()
                if len(parts) != 2:
                    await self.highrise.chat("📝 Usage: اضافه محمي @username" if self.bot_lang == "en" else "📝 الاستخدام: اضافه محمي @username")
                    return

                if "@" not in parts[1]:
                    username = parts[1]
                else:
                    username = parts[1][1:]

                # فحص إذا كان المستخدم محمي بالفعل (مع تجاهل حالة الأحرف)
                is_already_protected = any(existing_user.lower() == username.lower() for existing_user in self.special_protected)

                if not is_already_protected:
                    self.special_protected.append(username)
                    self.save_special_protected()
                
                else:
                    # العثور على الاسم الموجود للعرض الصحيح
                    existing_user = next((user for user in self.special_protected if user.lower() == username.lower()), username)
                    await self.highrise.chat(f"❌ {existing_user} is already in the protected list" if self.bot_lang == "en" else f"❌ {existing_user} موجود في قائمة المحميين بالفعل")
            else:
                await self.highrise.chat("❌ You do not have permission (owners only)" if self.bot_lang == "en" else "❌ ليس لديك صلاحية لاستخدام هذا الأمر (أونرز فقط)")

        if message.startswith(("ازاله محمي", "removespecial")):
            if user.username in self.owners:
                parts = message.split()
                if len(parts) != 2:
                    await self.highrise.chat("📝 Usage: !removespecial @username" if self.bot_lang == "en" else "📝 الاستخدام: !removespecial @username")
                    return

                if "@" not in parts[1]:
                    username = parts[1]
                else:
                    username = parts[1][1:]

                # البحث عن المستخدم مع تجاهل حالة الأحرف
                user_to_remove = None
                for protected_user in self.special_protected:
                    if protected_user.lower() == username.lower():
                        user_to_remove = protected_user
                        break

                if user_to_remove:
                    self.special_protected.remove(user_to_remove)
                    self.save_special_protected()

                else:
                    await self.highrise.chat(f"❌ {username} is not in the special protected list" if self.bot_lang == "en" else f"❌ {username} ليس في قائمة المحميين الخاصين")
            else:
                await self.highrise.chat("❌ You do not have permission (owners only)" if self.bot_lang == "en" else "❌ ليس لديك صلاحية لاستخدام هذا الأمر (أونرز فقط)")

        if message.startswith(("قائمة المحاميين", "Special_list")):
            if user.username in self.owners:
                if not self.special_protected:
                    await self.highrise.chat("📋 No special protected users" if self.bot_lang == "en" else "📋 لا يوجد محميين خاصين")
                    return

                protected_display_list = []
                for i, username in enumerate(self.special_protected, 1):
                    protected_display_list.append(f"{i} ـ {username}")

                # تقسيم القائمة إلى رسائل متعددة إذا كانت طويلة
                message_chunks = []
                current_chunk = "🛡️ قائمة المحميين الخاصين:\n"

                for item in protected_display_list:
                    if len(current_chunk + item + "\n") > 500:  # حد أقصى لطول الرسالة
                        message_chunks.append(current_chunk.strip())
                        current_chunk = item + "\n"
                    else:
                        current_chunk += item + "\n"

                if current_chunk.strip():
                    message_chunks.append(current_chunk.strip())

                # إرسال كل جزء من القائمة
                for chunk in message_chunks:
                    await self.highrise.chat(chunk)
            else:
                await self.highrise.chat("❌ You do not have permission (owners only)" if self.bot_lang == "en" else "❌ ليس لديك صلاحية لاستخدام هذا الأمر (أونرز فقط)")

        # أمر إعادة تعيين جميع النقاط إلى صفر (للأونرز فقط)
        if message.lower() == "تصفير":
            if user.username in self.owners:
                try:
                    # عدد المستخدمين قبل الإعادة تعيين
                    users_count = len(self.user_points)
                    
                    # إعادة تعيين جميع النقاط إلى صفر
                    self.user_points.clear()
                    self.save_user_points()
                    
                    await self.highrise.chat(f"📊 Points cleared for {users_count} user(s)" if self.bot_lang == "en" else f"📊 تم مسح نقاط {users_count} مستخدم")

                    
                except Exception as e:
                    print(f"Error resetting all points: {e}")
                    await self.highrise.chat("❌ Error resetting points" if self.bot_lang == "en" else "❌ حدث خطأ في إعادة تعيين النقاط")
            else:
                await self.highrise.chat("❌ This command is for owners only" if self.bot_lang == "en" else "❌ هذا الأمر متاح للأونرز فقط")

        

#Numaralı emotlar numaralı emotlar

    async def handle_emote_command(self, user_id: str, emote_name: str) -> None:
        if emote_name in emote_mapping:
            emote_info = emote_mapping[emote_name]
            emote_to_send = emote_info["value"]

            try:
                await self.highrise.send_emote(emote_to_send, user_id)
            except Exception as e:
                print(f"Error sending emote: {e}")


    async def start_emote_loop(self, user_id: str, emote_name: str) -> None:
        if emote_name in emote_mapping:
            # إيقاف أي loop سابق فوراً
            await self.stop_emote_loop(user_id)

            # Mark the user as having an active loop
            self.user_emote_loops[user_id] = emote_name
            emote_info = emote_mapping[emote_name]
            emote_to_send = emote_info["value"]
            emote_time = emote_info["time"]
            
            print(f"Starting emote loop {emote_name} for user {user_id}")

            # Create the loop task
            async def loop_task():
                while self.user_emote_loops.get(user_id) == emote_name:
                    try:
                        await self.highrise.send_emote(emote_to_send, user_id)
                        await asyncio.sleep(emote_time)
                    except Exception as e:
                        if "Target user not in room" in str(e):
                            print(f"User {user_id} left room, stopping emote loop")
                            break
                        print(f"Error in emote loop for {user_id}: {e}")
                        await asyncio.sleep(2)
                
                # Clean up when loop ends
                if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == emote_name:
                    del self.user_emote_loops[user_id]
                print(f"Emote loop ended for user {user_id}")
            
            # Start the loop as a separate task and store it
            task = asyncio.create_task(loop_task())
            if not hasattr(self, 'user_emote_tasks'):
                self.user_emote_tasks = {}
            self.user_emote_tasks[user_id] = task

    async def stop_emote_loop(self, user_id: str) -> None:
        # إزالة من القاموس لإيقاف الحلقة
        if user_id in self.user_emote_loops:
            self.user_emote_loops.pop(user_id)
        # إلغاء الـ task فوراً
        if hasattr(self, 'user_emote_tasks') and user_id in self.user_emote_tasks:
            task = self.user_emote_tasks.pop(user_id)
            if not task.done():
                task.cancel()



#paid emotes paid emotes paid emote

    async def emote_loop(self):
        while True:
            try:
                emote_name = random.choice(list(free_emotes.keys()))
                emote_to_send = free_emotes[emote_name]["value"]
                emote_time = free_emotes[emote_name]["time"]

                await self.highrise.send_emote(emote_id=emote_to_send)
                await asyncio.sleep(emote_time)
            except Exception as e:
                print("Error sending emote:", e)
                await asyncio.sleep(10)  # انتظار في حالة الخطأ 



#Ulti Ulti Ulti Ulti Ulti Ulti Ulti

    async def start_random_emote_loop(self, user_id: str) -> None:
        self.user_emote_loops[user_id] = "dans"
        while self.user_emote_loops.get(user_id) == "dans":
            try:
                emote_name = random.choice(list(secili_emote.keys()))
                emote_info = secili_emote[emote_name]
                emote_to_send = emote_info["value"]
                emote_time = emote_info["time"]
                await self.highrise.send_emote(emote_to_send, user_id)
                await asyncio.sleep(emote_time)
            except Exception as e:
                print(f"Error sending random emote: {e}")

    async def stop_random_emote_loop(self, user_id: str) -> None:
        if user_id in self.user_emote_loops:
            del self.user_emote_loops[user_id]

    async def start_ghost_emote_loop(self, user_id: str) -> None:
        """بدء حلقة رقصة الشبح الدائمة - محسّنة للسرعة"""
        self.user_emote_loops[user_id] = "ghost"
        while self.user_emote_loops.get(user_id) == "ghost":
            try:
                await self.highrise.send_emote("emote-ghost-idle", user_id)
                await asyncio.sleep(9.5)  # مدة أقصر للاستجابة الأسرع
            except Exception as e:
                if "Target user not in room" in str(e):
                    print(f"{user_id} ليس في الروم، توقف إرسال الرقصة.")
                    break
                print(f"Error sending ghost emote: {e}")
                break

    async def start_kiss_emote_loop(self, user_id: str) -> None:
        """بدء حلقة رقصة البوسة المستمرة"""
        self.user_emote_loops[user_id] = "kiss"
        while self.user_emote_loops.get(user_id) == "kiss":
            try:
                await self.highrise.send_emote("emote-kissing-bound", user_id)
                await asyncio.sleep(4.0)
            except Exception as e:
                if "Target user not in room" in str(e): break
                print(f"Error in kiss loop: {e}")
                break

    async def start_shy_emote_loop(self, user_id: str) -> None:
        """بدء حلقة رقصة الخجل المستمرة"""
        self.user_emote_loops[user_id] = "shy"
        while self.user_emote_loops.get(user_id) == "shy":
            try:
                await self.highrise.send_emote("emote-shy2", user_id)
                await asyncio.sleep(4.5)
            except Exception as e:
                if "Target user not in room" in str(e): break
                print(f"Error in shy loop: {e}")
                break

    async def start_sleep_emote_loop(self, user_id: str) -> None:
        """بدء حلقة النوم 150 المستمرة"""
        self.user_emote_loops[user_id] = "sleep_loop"
        while self.user_emote_loops.get(user_id) == "sleep_loop":
            try:
                await self.highrise.send_emote("idle-floorsleeping", user_id)
                await asyncio.sleep(3.5)
            except Exception as e:
                if "Target user not in room" in str(e): break
                print(f"Error in sleep loop: {e}")
                break

    async def start_sleep2_emote_loop(self, user_id: str) -> None:
        """بدء حلقة النوم 152 المستمرة"""
        self.user_emote_loops[user_id] = "sleep2_loop"
        while self.user_emote_loops.get(user_id) == "sleep2_loop":
            try:
                await self.highrise.send_emote("idle-floorsleeping2", user_id)
                await asyncio.sleep(3.5)
            except Exception as e:
                if "Target user not in room" in str(e): break
                print(f"Error in sleep2 loop: {e}")
                break

    async def start_rest_emote_loop(self, user_id: str) -> None:
        """بدء حلقة الجلوس الدائمة - محسّنة للسرعة"""
        self.user_emote_loops[user_id] = "rest"
        print(f"Starting rest loop for user {user_id}")
        
        while self.user_emote_loops.get(user_id) == "rest":
            try:
                await self.highrise.send_emote("sit-open", user_id)
                await asyncio.sleep(14.0)  # مدة أقصر للاستجابة الأسرع
            except Exception as e:
                if "Target user not in room" in str(e):
                    print(f"{user_id} ليس في الروم، توقف إرسال الرقصة.")
                    break
                print(f"Error sending rest emote: {e}")
                await asyncio.sleep(2)  # انتظار قبل المحاولة مرة أخرى
        
        # تنظيف عند انتهاء الloop
        if user_id in self.user_emote_loops and self.user_emote_loops[user_id] == "rest":
            del self.user_emote_loops[user_id]
        print(f"Rest loop ended for user {user_id}")

    async def start_floss_emote_loop(self, user_id: str) -> None:
        """بدء حلقة رقصة floss الدائمة"""
        self.user_emote_loops[user_id] = "floss"
        while self.user_emote_loops.get(user_id) == "floss":
            try:
                await self.highrise.send_emote("dance-floss", user_id)
                await asyncio.sleep(21.3)  # مدة رقصة floss
            except Exception as e:
                if "Target user not in room" in str(e):
                    print(f"{user_id} ليس في الروم، توقف إرسال الرقصة.")
                    break
                print(f"Error sending floss emote: {e}")
                break

    async def start_dance_floor_loop(self, user_id: str) -> None:
        """بدء حلقة الرقصات العشوائية"""
        from emotes import emote_mapping
        self.user_emote_loops[user_id] = "dance_floor"
        while self.user_emote_loops.get(user_id) == "dance_floor":
            try:
                # اختيار رقصة عشوائية من emotes.py
                emote_name = random.choice(list(emote_mapping.keys()))
                emote_info = emote_mapping[emote_name]
                emote_value = emote_info["value"]
                emote_time = emote_info.get("time", 10)  # وقت افتراضي 10 ثواني

                await self.highrise.send_emote(emote_value, user_id)
                await asyncio.sleep(emote_time)  # انتظار مدة الرقصة
            except Exception as e:
                if "Target user not in room" in str(e):
                    print(f"{user_id} ليس في الروم، توقف إرسال الرقصة.")
                    break
                print(f"Error sending dance floor emote: {e}")
                await asyncio.sleep(5)  # انتظار قصير في حالة الخطأ
                break



  #Genel Genel Genel Genel Genel

    async def send_emote(self, emote_to_send: str, user_id: str) -> None:
        await self.highrise.send_emote(emote_to_send, user_id)

    async def send_moderation_notification(self, message: str) -> None:
        """إرسال إشعارات الإشراف للأونرز عبر الرسائل الخاصة"""
        owners_to_notify = ["_king_man_1"]  # الأونرز المطلوب إشعارهم
        
        for owner_username in owners_to_notify:
            try:
                # محاولة العثور على الأونر عبر WebAPI أولاً
                owner_id = None
                if hasattr(self, 'webapi') and self.webapi:
                    try:
                        user_info = await self.webapi.get_users(username=owner_username, limit=1)
                        if user_info.users:
                            owner_id = user_info.users[0].user_id
                    except Exception as api_error:
                        print(f"WebAPI lookup failed for {owner_username}: {api_error}")
                
                # إذا لم نحصل على المعرف عبر WebAPI، ابحث في الروم
                if not owner_id:
                    room_users = await self.highrise.get_room_users()
                    for room_user, _ in room_users.content:
                        if room_user.username.lower() == owner_username.lower():
                            owner_id = room_user.id
                            break
                
                # إذا وجدنا المعرف، أرسل الرسالة الخاصة
                if owner_id:
                    try:
                        # محاولة إرسال رسالة خاصة مباشرة
                        try:
                            await self.highrise.send_direct_message(owner_id, f"🚨 إشعار إشراف:\n{message}")
                            print(f"Direct message sent to {owner_username}")
                        except Exception as dm_error:
                            # إذا فشلت الرسالة المباشرة، استخدم الهمس
                            try:
                                await self.highrise.send_whisper(owner_id, f"🚨 إشعار: {message}")
                                print(f"Whisper sent to {owner_username}")
                            except Exception as whisper_error:
                                print(f"Failed to send whisper to {owner_username}: {whisper_error}")
                                # كبديل أخير، إرسال في الشات العام مع تاج
                                await self.highrise.chat(f"🚨 Special notification for @{owner_username}:" if self.bot_lang == "en" else f"🚨 إشعار خاص لـ @{owner_username}:")
                                await self.highrise.chat(message)
                            
                    except Exception as general_error:
                        print(f"General error notifying {owner_username}: {general_error}")
                        # كبديل أخير، إرسال في الشات العام
                        await self.highrise.chat(f"🚨 Notification for @{owner_username}: {message}" if self.bot_lang == "en" else f"🚨 إشعار لـ @{owner_username}: {message}")
                else:
                    print(f"Could not find {owner_username} to send notification")
                    
            except Exception as e:
                print(f"Error in moderation notification system for {owner_username}: {e}")
                # في حالة فشل كل شيء، أرسل في الشات العام
                try:
                    await self.highrise.chat(f"🚨 Urgent notification for @{owner_username}:" if self.bot_lang == "en" else f"🚨 إشعار عاجل لـ @{owner_username}:")
                    await self.highrise.chat(message)
                except:
                    print(f"Complete failure to notify {owner_username}")

        # ==================== تنبيه الأوامر الناقصة ====================
        bare_command_hints = {
            "تغيير النظارات":   "تغيير النظارات [رقم]  —  مثال: تغيير النظارات 3",
            "اضف نظارات":      "اضف نظارات [رقم] [ID]  —  مثال: اضف نظارات 3 glasses-n_xxx",
            "اضف النظارات":    "اضف نظارات [رقم] [ID]  —  مثال: اضف نظارات 3 glasses-n_xxx",
            "احذف نظارات":     "احذف نظارات [رقم]  —  مثال: احذف نظارات 3",
            "تغيير الحواجب":   "تغيير الحواجب [رقم]  —  مثال: تغيير الحواجب 3",
            "اضف حاجب":       "اضف حاجب [رقم] [ID]  —  مثال: اضف حاجب 3 eyebrow-n_xxx",
            "اضف الحاجب":     "اضف حاجب [رقم] [ID]  —  مثال: اضف حاجب 3 eyebrow-n_xxx",
            "احذف حاجب":      "احذف حاجب [رقم]  —  مثال: احذف حاجب 3",
            "تغيير الفم":      "تغيير الفم [رقم]  —  مثال: تغيير الفم 3",
            "اضف فم":         "اضف فم [رقم] [ID]  —  مثال: اضف فم 3 mouth-n_xxx",
            "اضف الفم":       "اضف فم [رقم] [ID]  —  مثال: اضف فم 3 mouth-n_xxx",
            "احذف فم":        "احذف فم [رقم]  —  مثال: احذف فم 3",
            "تغيير عيون":     "تغيير عيون [رقم]  —  مثال: تغيير عيون 3",
            "اضف عين":        "اضف عين [رقم] [ID]  —  مثال: اضف عين 3 eye-n_xxx",
            "احذف عين":       "احذف عين [رقم]  —  مثال: احذف عين 3",
            "تغيير تيشيرت":   "تغيير تيشيرت [رقم]  —  مثال: تغيير تيشيرت 3",
            "اضف تيشيرت":    "اضف تيشيرت [رقم] [ID]  —  مثال: اضف تيشيرت 3 shirt-n_xxx",
            "احذف تيشيرت":   "احذف تيشيرت [رقم]  —  مثال: احذف تيشيرت 3",
            "تغيير شعر":     "تغيير شعر [رقم]  —  مثال: تغيير شعر 3",
            "اضف شعر":       "اضف شعر [رقم] [ID]  —  مثال: اضف شعر 3 hair_front-n_xxx",
            "اضف الشعر":     "اضف شعر [رقم] [ID]  —  مثال: اضف شعر 3 hair_front-n_xxx",
            "احذف شعر":      "احذف شعر [رقم]  —  مثال: احذف شعر 3",
            "تغيير الحذاء":   "تغيير الحذاء [رقم]  —  مثال: تغيير الحذاء 3",
            "اضف حذاء":      "اضف حذاء [ID]  —  مثال: اضف حذاء shoe-n_xxx",
            "احذف حذاء":     "احذف حذاء [رقم]  —  مثال: احذف حذاء 3",
            "تغيير بنطال":   "تغيير بنطال [رقم]  —  مثال: تغيير بنطال 3",
            "اضف بنطال":     "اضف بنطال [رقم] [ID]  —  مثال: اضف بنطال 3 pant-n_xxx",
            "اضف البنطال":   "اضف بنطال [رقم] [ID]  —  مثال: اضف بنطال 3 pant-n_xxx",
            "احذف بنطال":    "احذف بنطال [رقم]  —  مثال: احذف بنطال 3",
            "اخلع":          "اخلع [ID]  —  مثال: اخلع shirt-n_xxx",
            "تغيير الأنف":   "تغيير الأنف [رقم]  —  مثال: تغيير الأنف 3",
            "اضف أنف":      "اضف أنف [رقم] [ID]  —  مثال: اضف أنف 3 nose-n_xxx",
            "اضف الأنف":    "اضف أنف [رقم] [ID]  —  مثال: اضف أنف 3 nose-n_xxx",
            "احذف أنف":     "احذف أنف [رقم]  —  مثال: احذف أنف 3",
            "تغيير اليد":   "تغيير اليد [رقم]  —  مثال: تغيير اليد 3",
            "اضف يد":       "اضف يد [رقم] [ID]  —  مثال: اضف يد 3 hand-n_xxx",
            "اضف اليد":     "اضف يد [رقم] [ID]  —  مثال: اضف يد 3 hand-n_xxx",
            "احذف يد":      "احذف يد [رقم]  —  مثال: احذف يد 3",
            "تغيير ملامح":  "تغيير ملامح [رقم]  —  مثال: تغيير ملامح 3",
            "تغيير الملامح": "تغيير ملامح [رقم]  —  مثال: تغيير ملامح 3",
            "اضف ملامح":   "اضف ملامح [رقم] [ID]  —  مثال: اضف ملامح 3 freckle-n_xxx",
            "اضف ملمح":    "اضف ملامح [رقم] [ID]  —  مثال: اضف ملامح 3 freckle-n_xxx",
            "اضف الملامح":  "اضف ملامح [رقم] [ID]  —  مثال: اضف ملامح 3 freckle-n_xxx",
            "احذف ملمح":   "احذف ملمح [رقم]  —  مثال: احذف ملمح 3",
            "تغيير اختفاء": "تغيير اختفاء [رقم]  —  مثال: تغيير اختفاء 3",
            "تغيير الاختفاء": "تغيير اختفاء [رقم]  —  مثال: تغيير اختفاء 3",
            "اضف اختفاء":  "اضف اختفاء [رقم] [ID]  —  مثال: اضف اختفاء 3 item-n_xxx",
            "اضف الاختفاء": "اضف اختفاء [رقم] [ID]  —  مثال: اضف اختفاء 3 item-n_xxx",
            "احذف اختفاء": "احذف اختفاء [رقم]  —  مثال: احذف اختفاء 3",
            "تغيير قبعة":  "تغيير قبعة [رقم]  —  مثال: تغيير قبعة 3",
            "تغيير القبعة": "تغيير قبعة [رقم]  —  مثال: تغيير قبعة 3",
            "اضف قبعة":   "اضف قبعة [رقم] [ID]  —  مثال: اضف قبعة 3 hat-n_xxx",
            "اضف القبعة":  "اضف قبعة [رقم] [ID]  —  مثال: اضف قبعة 3 hat-n_xxx",
            "احذف قبعة":  "احذف قبعة [رقم]  —  مثال: احذف قبعة 3",
        }
        if original_message in bare_command_hints:
            if await self.is_user_allowed(user):
                hint = bare_command_hints[original_message]
                await self.highrise.send_whisper(user.id, f"⚠️ خطأ في الأمر!\n✅ الصيغة الصحيحة:\n{hint}")

    async def on_whisper(self, user: User, message: str) -> None:
        """On a received room whisper."""
        msg = message.strip().lower()

        # أوامر قائمة الأوامر عبر الهمس
        if msg in ["اوامر", "أوامر", "الاوامر", "الأوامر", "مساعدة", "مساعده", "help", "امر"]:
            try:
                user_privileges = await self.highrise.get_room_privilege(user.id)
                is_owner = user.username in self.owners
                is_moderator = user_privileges.moderator
                is_vip = user.username in self.vips

                await self.highrise.send_whisper(user.id, "🤖 (1) الرقص:\n• رقم 1-223 للرقص\n• loop [رقم] مستمر\n• رقصني عشوائي\n• dance floor مستمر\n• 0/stop إيقاف")
                await asyncio.sleep(2)
                await self.highrise.send_whisper(user.id, "❤️ (2) التفاعل:\n• h @user [عدد] قلوب\n• h all للجميع\n• wink @user غمزة\n• like @user إعجاب\n• كف @user صفعة\n• اسحر @user سحر")
                await asyncio.sleep(2)
                await self.highrise.send_whisper(user.id, "📍 (3) المواقع:\n• نص وسط الروم\n• فوق للأعلى\n• تحت للأسفل\n• vip منطقة VIP\n• الطوابق عرض الطوابق")
                await asyncio.sleep(2)
                await self.highrise.send_whisper(user.id, "ℹ️ (4) معلومات:\n• info @user معلومات\n• ping فحص الاتصال\n• time مدة التشغيل\n• list قائمة الرقصات\n• نقاطي نقاطك\n• ترجمة [نص] ترجمة")
                await asyncio.sleep(2)
                await self.highrise.send_whisper(user.id, "👗 (5) الملابس:\n• اضف [معرف] إضافة\n• اخلع [معرف] خلع\n• اخلع الكل خلع الجميع\n• اضف شعر [رقم]\n• اضف عين [رقم]\n• مخزوني عرض المخزون")
                await asyncio.sleep(2)
                if is_owner or is_moderator:
                    await self.highrise.send_whisper(user.id, "🛡️ (6) مشرفين-نقل:\n• tel @user انتقال\n• اسحب @user جلب\n• follow @user متابعة\n• move @u1 @u2 نقل\n• جيب الكل جلب الجميع\n• مكانك رجوع البوت\n• حفظ حفظ المكان")
                    await asyncio.sleep(2)
                    await self.highrise.send_whisper(user.id, "🛡️ (7) مشرفين-إدارة:\n• !kick @user طرد\n• !ban @user حظر\n• !mute @user كتم\n• تحذير @user تحذير\n• addvip @user VIP\n• addswm @user رسالة ترحيب\n• all [رقم] رقص للجميع\n• spam رسالة تكرار")
                    await asyncio.sleep(2)
                final = f"🌟 صلاحيتك: {'أونر 👑' if is_owner else 'مشرف 🛡️' if is_moderator else 'VIP ⭐' if is_vip else 'مستخدم عادي'}\n@_king_man_1"
                await self.highrise.send_whisper(user.id, final)

            except Exception as e:
                print(f"Error sending commands via whisper: {e}")
            return

        # ==================== أمر تابعني (للأونر فقط) ====================
        if message.strip().startswith("!تابعني") and user.username in self.owners:
            parts = message.strip().split()
            if len(parts) >= 2:
                new_room_id = parts[1].strip()
                RunBot.pending_follow = True
                RunBot.room_id = new_room_id
                await self.highrise.send_whisper(user.id, f"⏳ جاري الانتقال للغرفة: {new_room_id}\nسيتم التحقق من الصلاحيات عند الدخول...")
                raise Exception(f"[Follow] الانتقال لغرفة جديدة: {new_room_id}")
            else:
                await self.highrise.send_whisper(user.id, "⚠️ الصيغة الصحيحة: !تابعني [room_id]")
            return

        # Only allow the "say" command for admins
        if await self.is_user_allowed(user) and message.startswith("say ") and len(message) > 4:
            try:
                broadcast_message = message[4:]
                await self.highrise.chat(broadcast_message)
            except:
                print("error broadcasting whisper message")

    async def on_direct_message(self, user: User, message: str) -> None:
        """On a received direct message."""
        print(f"[DM] from {user.username}: {message}")
        
        # فحص إذا كانت الرسالة تحتوي على "اوامر" أو "help" أو "مساعدة"
        if message.lower().strip() in ["اوامر", "أوامر", "الاوامر", "الأوامر", "help", "مساعدة", "مساعده", "commands", "امر"]:
            try:
                is_owner = user.username in self.owners
                is_vip = user.username in self.vips
                is_moderator = False
                try:
                    user_privileges = await self.highrise.get_room_privilege(user.id)
                    is_moderator = user_privileges.moderator
                except Exception:
                    pass
                # الرسالة الأولى: مقدمة وأوامر الرقص
                part1 = f"""🤖 أوامر البوت المتاحة لك:

🎭 **أوامر الرقص:**
• اكتب رقم من 1-140 للرقص الفوري
• loop [رقم] - رقص مستمر (مثال: loop 5)
• رقصني - رقص عشوائي متنوع
• جوست/ghost - رقصة الشبح الدائمة
• ريست/rest - جلوس مستمر
• floss forever - رقصة فلوس دائمة
• dance floor - رقص عشوائي مستمر
• 0 أو dur - إيقاف أي رقص مستمر
• rd أو رقصات - رقصة عشوائية واحدة"""

                await self.highrise.send_direct_message(user.id, part1)
                await asyncio.sleep(3)  # انتظار 3 ثواني

                # الرسالة الثانية: أوامر القلوب والمواقع
                part2 = f"""❤️ **أوامر القلوب:**
• h @username [عدد] - إرسال قلوب (حد أقصى: {"50" if is_owner or is_moderator else "15" if is_vip else "5"})
• wink @username [عدد] - إرسال غمزة
• like @username [عدد] - إرسال إعجاب

📍 **مواقع سريعة:**
• نص - الانتقال للوسط
• فوق/up - الانتقال للأعلى  
• تحت/down - الانتقال للأسفل
• vip - دخول منطقة VIP (حسب الصلاحية)"""

                await self.highrise.send_direct_message(user.id, part2)
                await asyncio.sleep(3)

                # الرسالة الثالثة: أوامر المرح والمعلومات
                part3 = f"""🎪 **أوامر المرح:**
• كف @username - صفعة مرحة
• اسحر @username - سحر مرح مع تأثيرات

ℹ️ **أوامر المعلومات:**
• info @username - معلومات أساسية للمستخدم
• ping - فحص سرعة الاتصال
• time - مدة تشغيل البوت
• list - عرض قائمة الرقصات المرقمة"""

                await self.highrise.send_direct_message(user.id, part3)
                await asyncio.sleep(3)

                # الرسالة الرابعة: أوامر التحكم الذاتي والصلاحيات
                part4 = f"""🔄 **أوامر التحكم الذاتي:**
• لف الروم - جولة عشوائية في الروم
• توقف/stop - إيقاف أي نشاط مستمر

🎯 **صلاحيتك الحالية:** {"أونر" if is_owner else "مشرف" if is_moderator else "VIP قلوب" if is_vip else "مستخدم عادي"}"""

                await self.highrise.send_direct_message(user.id, part4)
                await asyncio.sleep(3)

                # أوامر المشرفين والأونرز (إذا كان له صلاحية)
                if is_owner or is_moderator:
                    mod_part1 = """🛡️ **أوامر المشرفين - الجزء الأول:**
• tel/روح @username - انتقال للمستخدم
• اسحب @username - جلب المستخدم إليك
• move @user1 @user2 - نقل user1 لموقع user2
• up/down/mid @username - نقل لمواقع محددة
• بدل/degis @username - تبديل المواقع
• مرجح @username - تحريك عشوائي للمستخدم
• وقف @username - إيقاف التحريك
• ودي @username - إرسال لموقع عشوائي"""

                    await self.highrise.send_direct_message(user.id, mod_part1)
                    await asyncio.sleep(3)

                    mod_part2 = """🛡️ **أوامر المشرفين - الجزء الثاني:**
• follow @username - متابعة المستخدم
• fix @username - تثبيت موقع المستخدم
• go @username - إلغاء تثبيت الموقع
• الحق @username - متابعة المستخدم
• h all [عدد] - قلوب لجميع المستخدمين
• all [رقم رقصة] - رقصة لجميع المستخدمين
• kick @username - طرد المستخدم
• ban @username [دقائق] - حظر المستخدم"""

                    await self.highrise.send_direct_message(user.id, mod_part2)
                    await asyncio.sleep(3)

                    mod_part3 = """🛡️ **أوامر المشرفين - الجزء الثالث:**
• unban @username - فك الحظر
• mute @username [دقائق] - كتم المستخدم
• unmute @username - فك الكتم
• equip @username - نسخ ملابس المستخدم
• e @user1 @user2 - user1 ينسخ ملابس user2
• addvip/removevip @username - إدارة VIP التصميم
• addvip2/removevip2 @username - إدارة VIP القلوب
• addswm @username رسالة - ترحيب خاص"""

                    await self.highrise.send_direct_message(user.id, mod_part3)
                    await asyncio.sleep(3)

                    mod_part4 = """🛡️ **أوامر المشرفين - الجزء الأخير:**
• removeswm @username - حذف الترحيب الخاص
• spam رسالة - تكرار الرسائل
• nospam - إيقاف تكرار الرسائل

📋 **قوائم للمراجعة:**
• vip2 list - قائمة VIPs القلوب
• swm list - قائمة الترحيبات الخاصة"""

                    await self.highrise.send_direct_message(user.id, mod_part4)
                    await asyncio.sleep(3)

                # أوامر الأونرز فقط
                if is_owner:
                    owner_part = """👑 **أوامر الأونرز فقط:**
• addowner @username - إضافة أونر جديد
• add @username moderator/designer - إعطاء صلاحيات
• remove @username moderator/designer - سحب صلاحيات
• !info @username - معلومات مفصلة للمستخدم"""

                    await self.highrise.send_direct_message(user.id, owner_part)
                    await asyncio.sleep(3)

                # الرسالة الأخيرة
                final_message = """🌟 **معلومات إضافية:**
• تابع صاحب البوت: @_king_man_1
• استخدم الأوامر بحذر واستمتع بوقتك!
• شكراً لك على استخدام البوت

💡 **ملاحظة:** جميع الأوامر تعمل في الروم العادي، هذه القائمة للمساعدة فقط"""

                await self.highrise.send_direct_message(user.id, final_message)

            except Exception as e:
                print(f"Error sending commands list via DM: {e}")
                # في حالة الخطأ، إرسال رسالة قصيرة
                try:
                    error_message = """❌ حدث خطأ في عرض القائمة الكاملة.

🔧 **الأوامر الأساسية:**
• اكتب رقم من 1-140 للرقص
• h @username - إرسال قلب
• info @username - معلومات المستخدم
• ping - فحص الاتصال

📞 **للمساعدة:** تواصل مع @_king_man_1"""
                    await self.highrise.send_direct_message(user.id, error_message)
                except Exception as dm_error:
                    print(f"Failed to send error message via DM: {dm_error}")
                    # كبديل أخير، استخدام الهمس
                    try:
                        await self.highrise.send_whisper(user.id, "❌ حدث خطأ في إرسال الرسائل الخاصة. للمساعدة تواصل مع @_king_man_1")
                    except:
                        print("Failed to send error message via whisper as well")
        # ====== تغيير لغة البوت بالكامل ======
        elif message.strip().lower() in ["en", "english", "انجليزي", "إنجليزي"]:
            self.bot_lang = "en"
            self.save_bot_lang()
            self.user_lang_prefs[user.id] = "en"
            self.save_user_lang_prefs()
            await self.highrise.send_direct_message(user.id, "✅ Bot language changed to English 🇺🇸\nAll responses will now be in English.")

        elif message.strip().lower() in ["ar", "arabic", "عربي", "عربية"]:
            self.bot_lang = "ar"
            self.save_bot_lang()
            self.user_lang_prefs[user.id] = "ar"
            self.save_user_lang_prefs()
            await self.highrise.send_direct_message(user.id, "✅ تم تغيير لغة البوت إلى العربية 🇸🇦\nجميع الردود ستكون بالعربية الآن.")

        # ====== متجر البوت - عرض الباقات ======
        elif message.lower().strip() in ["شراء بوت", "شراء البوت", "متجر البوت", "متجر", "buy bot", "buybot", "shop", "بوت", "اشتري بوت", "اشتري البوت"]:
            ulang = self.get_user_lang(user.id)
            if ulang == "en":
                shop_msg = (
                    f"🤖 Welcome @{user.username} to the Bot Store!\n\n"
                    f"💎 Available Packages:\n\n"
                    f"⏱️ 1 Hour       ← Send 1 gold\n"
                    f"⏱️ 3 Hours      ← Send 3,000 gold\n"
                    f"📅 Full Day     ← Send 10,000 gold\n"
                    f"📅 Full Week   ← Send 50,000 gold\n\n"
                    f"📌 How to buy:\n"
                    f"1️⃣ Send the required gold to this bot\n"
                    f"2️⃣ The bot will ask for your room name\n"
                    f"3️⃣ Send the room name and it will be activated!\n\n"
                    f"📞 For help: @_king_man_1"
                )
            else:
                shop_msg = (
                    f"🤖 مرحباً @{user.username} في متجر البوت!\n\n"
                    f"💎 الباقات المتاحة:\n\n"
                    f"⏱️ ساعة واحدة   ← أرسل 1 ذهب\n"
                    f"⏱️ 3 ساعات       ← أرسل 3,000 ذهب\n"
                    f"📅 يوم كامل       ← أرسل 10,000 ذهب\n"
                    f"📅 أسبوع كامل   ← أرسل 50,000 ذهب\n\n"
                    f"📌 طريقة الشراء:\n"
                    f"1️⃣ أرسل المبلغ المطلوب ذهباً لهذا البوت\n"
                    f"2️⃣ سيطلب منك البوت اسم الغرفة\n"
                    f"3️⃣ أرسل اسم الغرفة وسيتم التفعيل!\n\n"
                    f"📞 للمساعدة: @_king_man_1"
                )
            await self.highrise.send_direct_message(user.id, shop_msg)

        # ====== متجر البوت - رصيد المستخدم ======
        elif message.lower().strip() in ["رصيدي", "رصيد", "طلباتي", "طلباتى", "my balance", "mybalance", "myorders"]:
            user_orders = [o for o in self.bot_shop_orders if o.get("buyer_id") == user.id]
            total_paid = sum(o.get("amount_paid", 0) for o in user_orders)
            if total_paid > 0:
                balance_msg = (
                    f"💲 رصيدك: {total_paid:,} ذهب\n\n"
                    f"يمكنك إعطاء هذا البوت لزيادة رصيدك."
                )
            else:
                balance_msg = (
                    f"💲 رصيدك: 0 ذهب\n\n"
                    f"يمكنك إعطاء هذا البوت لزيادة رصيدك."
                )
            await self.highrise.send_direct_message(user.id, balance_msg)

        # ====== متجر البوت - الوقت المتبقي ======
        elif message.lower().strip() in ["وقتي", "وقت", "الوقت المتبقي", "remaining", "mytime", "my time"]:
            _bots_data = load_sub_bots()
            _user_bot = next((b for b in _bots_data if b.get("buyer_id") == user.id and b["status"] in ("busy", "paused")), None)
            user_active = [o for o in self.bot_shop_orders if o.get("buyer_id") == user.id and o.get("status") == "active" and o.get("expires_at")]
            if not _user_bot and not user_active:
                await self.highrise.send_direct_message(user.id,
                    "⏰ ليس لديك أي بوت نشط حالياً.\n\n🛒 لشراء بوت اكتب: شراء بوت"
                )
            else:
                now = datetime.now()
                if _user_bot:
                    bot_uname = _user_bot.get("username", "غير محدد")
                    bot_status = "نشط ✅" if _user_bot["status"] == "busy" else "موقوف مؤقتاً ⏸️"
                    if _user_bot["status"] == "busy" and _user_bot.get("expires_at"):
                        exp_dt = datetime.strptime(_user_bot["expires_at"], "%Y-%m-%d %H:%M:%S")
                        secs = max(0, int((exp_dt - now).total_seconds()))
                        h = secs // 3600
                        m = (secs % 3600) // 60
                        time_left = f"{h} ساعة و {m} دقيقة" if h > 0 else f"{m} دقيقة"
                        expires_line = f"⏰ ينتهي في: {_user_bot['expires_at']}\n"
                    elif _user_bot["status"] == "paused" and _user_bot.get("remaining_seconds"):
                        secs = max(0, int(_user_bot["remaining_seconds"]))
                        h = secs // 3600
                        m = (secs % 3600) // 60
                        time_left = f"{h} ساعة و {m} دقيقة" if h > 0 else f"{m} دقيقة"
                        expires_line = ""
                    else:
                        time_left = "غير محدد"
                        expires_line = ""
                    time_msg = (
                        f"🤖 معلومات بوتك:\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"👤 يوزر البوت: @{bot_uname}\n"
                        f"📊 الحالة: {bot_status}\n"
                        f"⏳ الوقت المتبقي: {time_left}\n"
                        f"{expires_line}"
                    )
                else:
                    ord_ = user_active[0]
                    bot_uname = ord_.get("bot_username", "غير محدد")
                    try:
                        exp_dt = datetime.strptime(ord_["expires_at"], "%Y-%m-%d %H:%M:%S")
                        secs = max(0, int((exp_dt - now).total_seconds()))
                        h = secs // 3600
                        m = (secs % 3600) // 60
                        time_left = f"{h} ساعة و {m} دقيقة" if h > 0 else f"{m} دقيقة"
                        expires_str = ord_["expires_at"]
                    except Exception:
                        time_left = "غير محدد"
                        expires_str = ""
                    time_msg = (
                        f"🤖 معلومات بوتك:\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"👤 يوزر البوت: @{bot_uname}\n"
                        f"⏳ الوقت المتبقي: {time_left}\n"
                        f"⏰ ينتهي في: {expires_str}\n"
                    )
                await self.highrise.send_direct_message(user.id, time_msg)

        # ====== متجر البوت - استقبال اسم الغرفة ======
        elif user.id in self.pending_bot_purchases and self.pending_bot_purchases[user.id].get("step") == "waiting_room":
            purchase = self.pending_bot_purchases[user.id]
            room_name = message.strip()

            # البحث عن الغرفة في Highrise
            room_id = None
            try:
                rooms_result = await self.webapi.get_rooms(query=room_name, limit=5)
                if rooms_result.rooms:
                    room_id = rooms_result.rooms[0].room_id
                    found_room_name = rooms_result.rooms[0].room_name
                else:
                    found_room_name = room_name
            except Exception as e:
                print(f"Room search error: {e}")
                found_room_name = room_name

            # تسجيل الطلب
            order = {
                "order_id": f"ORD-{int(time.time())}",
                "buyer": purchase["username"],
                "buyer_id": user.id,
                "package": purchase["package"],
                "duration": purchase["duration"],
                "hours": purchase["hours"],
                "amount_paid": purchase["amount"],
                "room_name": found_room_name,
                "room_id": room_id,
                "status": "pending_activation",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.bot_shop_orders.append(order)
            self.save_bot_shop_orders()

            # حذف الحالة المعلقة
            del self.pending_bot_purchases[user.id]

            # الرسالة النهائية للمشتري
            if self.bot_lang == "en":
                if room_id:
                    buyer_msg = (
                        f"✅ Your order has been registered successfully!\n\n"
                        f"📦 Package: {purchase['package']} ({purchase['duration']})\n"
                        f"🏠 Room Name: {found_room_name}\n"
                        f"🆔 Room ID: {room_id}\n\n"
                        f"📋 Next Steps:\n"
                        f"1️⃣ Make the bot a moderator & designer in your room\n"
                        f"2️⃣ Room ID: {room_id}\n"
                        f"3️⃣ The bot will be activated soon by @_king_man_1\n\n"
                        f"🔢 Your order number: {order['order_id']}"
                    )
                else:
                    buyer_msg = (
                        f"✅ Your order has been registered successfully!\n\n"
                        f"📦 Package: {purchase['package']} ({purchase['duration']})\n"
                        f"🏠 Room Name: {found_room_name}\n\n"
                        f"⚠️ The room was not found automatically.\n"
                        f"📞 Contact @_king_man_1 to complete the activation\n"
                        f"🔢 Your order number: {order['order_id']}"
                    )
            else:
                if room_id:
                    buyer_msg = (
                        f"✅ تم تسجيل طلبك بنجاح!\n\n"
                        f"📦 الباقة: {purchase['package']} ({purchase['duration']})\n"
                        f"🏠 اسم الغرفة: {found_room_name}\n"
                        f"🆔 ايدي الغرفة: {room_id}\n\n"
                        f"📋 الخطوات التالية:\n"
                        f"1️⃣ اجعل البوت مشرف ومصمم في غرفتك\n"
                        f"2️⃣ ايدي الغرفة: {room_id}\n"
                        f"3️⃣ سيتم تفعيل البوت قريباً من قبل @_king_man_1\n\n"
                        f"🔢 رقم طلبك: {order['order_id']}"
                    )
                else:
                    buyer_msg = (
                        f"✅ تم تسجيل طلبك بنجاح!\n\n"
                        f"📦 الباقة: {purchase['package']} ({purchase['duration']})\n"
                        f"🏠 اسم الغرفة: {found_room_name}\n\n"
                        f"⚠️ لم يتم العثور على الغرفة تلقائياً.\n"
                        f"📞 تواصل مع @_king_man_1 لإكمال التفعيل\n"
                        f"🔢 رقم طلبك: {order['order_id']}"
                    )
            await self.highrise.send_direct_message(user.id, buyer_msg)

            # إعلام المالك باسم الغرفة وايديها
            for owner_username in self.owners:
                try:
                    owner_info = await self.webapi.get_users(username=owner_username, limit=1)
                    if owner_info.users:
                        owner_id_str = owner_info.users[0].user_id
                        owner_final = (
                            f"✅ طلب بوت جاهز للتفعيل!\n"
                            f"🔢 رقم الطلب: {order['order_id']}\n"
                            f"👤 المشتري: @{purchase['username']}\n"
                            f"📦 الباقة: {purchase['package']} ({purchase['duration']})\n"
                            f"💰 المبلغ: {purchase['amount']:,} ذهب\n"
                            f"🏠 الغرفة: {found_room_name}\n"
                            f"🆔 ايدي الغرفة: {room_id if room_id else 'غير معروف - يحتاج بحث يدوي'}"
                        )
                        await self.highrise.send_direct_message(owner_id_str, owner_final)
                except Exception as e:
                    print(f"Failed to notify owner {owner_username}: {e}")

        else:
            # رد على الرسائل الأخرى
            if self.bot_lang == "en":
                await self.highrise.send_direct_message(user.id, f"""🤖 Hello @{user.username}!

📋 To view the full command list, type: **help**

🛒 To buy a bot for your room, type: **buy bot**

💡 Quick commands:
• Type a number from 1-140 to dance
• h @username - send a heart
• info @username - user info
• ping - check connection

🎯 Bot owner: @_king_man_1""")
            else:
                await self.highrise.send_direct_message(user.id, f"""🤖 مرحباً @{user.username}!

📋 لعرض قائمة الأوامر الكاملة، اكتب: **اوامر**

🛒 لشراء بوت لغرفتك، اكتب: **شراء بوت**

💡 أوامر سريعة:
• اكتب رقم من 1-140 للرقص
• h @username - إرسال قلب
• info @username - معلومات المستخدم
• ping - فحص الاتصال

🎯 صاحب البوت: @_king_man_1""")

    async def is_user_allowed(self, user: User) -> bool:
        user_privileges = await self.highrise.get_room_privilege(user.id)
        # Check if user is bot admin (case insensitive)
        is_bot_admin = any(user.username.lower() == admin.lower() for admin in self.admins)
        return user_privileges.moderator or user.username in self.owners or is_bot_admin

    async def is_user_admin_or_above(self, user: User) -> bool:
        """فحص إذا كان المستخدم أدمن أو أعلى"""
        user_privileges = await self.highrise.get_room_privilege(user.id)
        return user_privileges.moderator or user.username in self.owners or user.username in self.admins

#gellllbbb

    async def moderate_room(
        self,
        user_id: str,
        action: Literal["kick", "ban", "unban", "mute"],
        action_length: int | None = None,
    ) -> None:
        """Moderate a user in the room."""

    async def get_detailed_userinfo(self, user: User, target_username: str) -> None:
        try:
            # Dual search system: Try WebAPI first, then fallback to room users
            user_info = None
            try:
                web_users = await self.webapi.get_users(username=target_username, limit=1)
                if web_users.users:
                    user_info = web_users.users[0]
            except Exception as e:
                print(f"WebAPI search failed for info: {e}")

            if not user_info:
                # Fallback to room users
                room_users = await self.highrise.get_room_users()
                for room_user, _ in room_users.content:
                    if room_user.username.lower() == target_username.lower():
                        user_info = room_user
                        break
            
            if not user_info:
                await self.highrise.chat(f"❌ User {target_username} not found" if self.bot_lang == "en" else f"❌ المستخدم {target_username} غير موجود")
                return

            user_id = user_info.user_id if hasattr(user_info, 'user_id') else user_info.id
            
            try:
                detailed_info = await self.webapi.get_user(user_id)
            except Exception as e:
                # If get_user fails with 404, we show basic info from room/search
                if "404" in str(e):
                    await self.highrise.chat(f"📋 @{target_username} info:\n👤 Name: {user_info.username}\n🆔 ID: {user_id}\n⚠️ Cannot fetch extra details (404)" if self.bot_lang == "en" else f"📋 معلومات @{target_username}:\n👤 الاسم: {user_info.username}\n🆔 المعرف: {user_id}\n⚠️ لا يمكن جلب تفاصيل إضافية حالياً (404)")
                    return
                raise e

            # معلومات أساسية
            username = detailed_info.user.username
            display_name = getattr(detailed_info.user, "display_name", "غير محدد") or "غير محدد"
            bio = detailed_info.user.bio or "لا يوجد بايو"

            # إحصائيات
            followers = detailed_info.user.num_followers or 0
            following = detailed_info.user.num_following or 0
            friends = detailed_info.user.num_friends or 0

            # معلومات إضافية
            country = detailed_info.user.country_code or "غير محدد"
            joined_at = detailed_info.user.joined_at.strftime("%Y/%m/%d") if detailed_info.user.joined_at else "غير محدد"

            # حساب عدد الأيام منذ التسجيل
            if detailed_info.user.joined_at:
                joined_date = detailed_info.user.joined_at.date()
                today = datetime.now().date()
                days_since_joined = (today - joined_date).days
            else:
                days_since_joined = "غير محدد"

            # آخر ظهور
            if detailed_info.user.last_online_in:
                last_online = detailed_info.user.last_online_in.strftime("%Y/%m/%d %H:%M")
            else:
                last_online = "غير محدد"

            # الفريق
            crew_name = detailed_info.user.crew.name if detailed_info.user.crew else "لا يوجد فريق"

            # تجميع المعلومات في رسالة واحدة (مختصرة لتجنب طول الرسالة)
            info_message = f"""
📋 معلومات @{username}:
👤 {display_name}
📊 {followers:,} متابع | {following:,} يتابع | {friends:,} صديق
🌍 {country} | 📅 {joined_at} ({days_since_joined} يوم)
🕐 آخر ظهور: {last_online}
👥 الفريق: {crew_name}
💫 ID: {user_id}
            """

            await self.highrise.chat(info_message.strip())

        except Exception as e:
            await self.highrise.chat(f"❌ Error fetching user info: {str(e)}" if self.bot_lang == "en" else f"❌ خطأ في جلب معلومات المستخدم: {str(e)}")
            print(f"Error getting user info: {e}")

    async def userinfo(self, user: User, target_username: str) -> None:
        user_info = await self.webapi.get_users(username=target_username, limit=1)

        if not user_info.users:
            await self.highrise.chat("User not found" if self.bot_lang == "en" else "المستخدم غير موجود")
            return

        user_id = user_info.users[0].user_id

        user_info = await self.webapi.get_user(user_id)

        number_of_followers = user_info.user.num_followers
        number_of_friends = user_info.user.num_friends
        country_code = user_info.user.country_code
        outfit = user_info.user.outfit
        bio = user_info.user.bio
        active_room = user_info.user.active_room
        crew = user_info.user.crew
        number_of_following = user_info.user.num_following
        joined_at = user_info.user.joined_at.strftime("%d/%m/%Y %H:%M:%S")

        joined_date = user_info.user.joined_at.date()
        today = datetime.now().date()
        days_played = (today - joined_date).days

        last_login = user_info.user.last_online_in.strftime("%d/%m/%Y %H:%M:%S") if user_info.user.last_online_in else "Son giriş bilgisi mevcut değil"

        await self.highrise.chat(f"Username: {target_username}\n Followers: {number_of_followers}\n Friends: {number_of_friends}\n Joined: {joined_at}\n Days played: {days_played}" if self.bot_lang == "en" else f"اسم المستخدم: {target_username}\n عدد المتابعين: {number_of_followers}\n عدد الاصدقاء: {number_of_friends}\n انضم منذ: {joined_at}\n عدد ايام اللعب: {days_played}")

    async def follow(self, user: User, message: str = ""):
        self.following_user = user  
        while self.following_user == user:
            room_users = (await self.highrise.get_room_users()).content
            for room_user, position in room_users:
                if room_user.id == user.id:
                    user_position = position
                    break
            if user_position is not None and isinstance(user_position, Position):
                nearby_position = Position(user_position.x + 1.0, user_position.y, user_position.z)
                await self.highrise.walk_to(nearby_position)

            await asyncio.sleep(0.5) 

    async def follow_user(self, target_username: str):
      while self.following_username == target_username:
          # ابحث عن موقع المستخدم المستهدف في الغرفة
          response = await self.highrise.get_room_users()
          target_user_position = None
          for user_info in response.content:
              if user_info[0].username.lower() == target_username.lower():
                  target_user_position = user_info[1]
                  break

          if target_user_position and type(target_user_position) != AnchorPosition:
              await self.highrise.walk_to(Position(target_user_position.x , target_user_position.y, target_user_position.z -1))

              await asyncio.sleep(1)  # انتظر 5 ثواني مثلاً

    async def adjust_position(self, user: User, message: str, axis: str) -> None:
        try:
            adjustment = int(message[2:])
            if message.startswith("-"):
                adjustment *= -1

            room_users = await self.highrise.get_room_users()
            user_position = None

            for user_obj, user_position in room_users.content:
                if user_obj.id == user.id:
                    break

            if user_position:
                new_position = None

                if axis == 'x':
                    new_position = Position(user_position.x + adjustment, user_position.y, user_position.z, user_position.facing)
                elif axis == 'y':
                    new_position = Position(user_position.x, user_position.y + adjustment, user_position.z, user_position.facing)
                elif axis == 'z':
                    new_position = Position(user_position.x, user_position.y, user_position.z + adjustment, user_position.facing)
                else:
                    print(f"Unsupported axis: {axis}")
                    return

                await self.teleport(user, new_position)

        except ValueError:
            print("Invalid adjustment value. Please use +x/-x, +y/-y, or +z/-z followed by an integer.")
        except Exception as e:
            print(f"An error occurred during position adjustment: {e}")

    async def switch_users(self, user: User, target_username: str) -> None:
        try:
            room_users = await self.highrise.get_room_users()

            maker_position = None
            target_user_obj = None
            target_position = None

            # البحث عن موقع المستخدم الذي كتب الأمر
            for room_user, position in room_users.content:
                if room_user.id == user.id:
                    maker_position = position
                    break

            # البحث عن المستخدم المستهدف وموقعه
            for room_user, position in room_users.content:
                if room_user.username.lower() == target_username.lower():
                    target_user_obj = room_user
                    target_position = position
                    break

            if maker_position and target_position and target_user_obj:
                # تبديل المواقع
                await self.teleport(user, Position(target_position.x + 0.0001, target_position.y, target_position.z, target_position.facing))
                await self.teleport(target_user_obj, Position(maker_position.x + 0.0001, maker_position.y, maker_position.z, maker_position.facing))
                await self.highrise.chat(f"Positions swapped: @{user.username} and @{target_username} ✅" if self.bot_lang == "en" else f"تم تبديل مواقع @{user.username} و @{target_username} ✅")
            else:
                await self.highrise.chat(f"User {target_username} is not in the room" if self.bot_lang == "en" else f"المستخدم {target_username} غير موجود في الغرفة")

        except Exception as e:
            print(f"An error occurred during user switch: {e}")
            await self.highrise.chat("Error swapping positions" if self.bot_lang == "en" else "حدث خطأ في تبديل المواقع")

    async def teleport(self, user: User, position: Position):
        try:
            await self.highrise.teleport(user.id, position)
        except Exception as e:
            print(f"Caught Teleport Error: {e}")

    async def teleport_to_user(self, user: User, target_username: str) -> None:
        try:
            room_users = await self.highrise.get_room_users()
            for target, position in room_users.content:
                if target.username.lower() == target_username.lower():
                    z = position.z
                    new_z = z - 1
                    await self.teleport(user, Position(position.x, position.y, new_z, position.facing))
                    break
        except Exception as e:
            print(f"An error occurred while teleporting to {target_username}: {e}")

    async def teleport_user_next_to(self, target_username: str, requester_user: User) -> None:
        try:

            room_users = await self.highrise.get_room_users()
            requester_position = None
            for user, position in room_users.content:
                if user.id == requester_user.id:
                    requester_position = position
                    break



            for user, position in room_users.content:
                if user.username.lower() == target_username.lower():
                    z = requester_position.z
                    new_z = z + 1  
                    await self.teleport(user, Position(requester_position.x, requester_position.y, new_z, requester_position.facing))
                    break
        except Exception as e:
            print(f"An error occurred while teleporting {target_username} next to {requester_user.username}: {e}")

    async def on_tip(self, sender: User, receiver: User, tip: CurrencyItem | Item) -> None:
        print(f"{sender.username} tipped {receiver.username} an amount of {tip.amount}")

        # تسجيل التبرع في سجل التبرعات
        try:
            amount = tip.amount if hasattr(tip, 'amount') else 0
            if amount > 0:
                self.tip_history[sender.username] = self.tip_history.get(sender.username, 0) + amount
                self.save_tip_history()
        except Exception as e:
            print(f"tip_history error: {e}")
        
        # فحص إذا كان البقشيش للبوت
        if receiver.id == self.bot_id or receiver.username == "Casino_Masr_Bot":
            tip_amount = tip.amount if hasattr(tip, 'amount') else 0

            # ====== إضافة كل تيب لمحفظة المستخدم ======
            if tip_amount > 0:
                old_bal = self.user_wallets.get(sender.id, 0)
                new_bal = old_bal + tip_amount
                self.user_wallets[sender.id] = new_bal
                self.save_user_wallets()
                try:
                    await self.highrise.send_message_bulk([sender.id],
                        f"💰 تم إضافة {tip_amount:,} ذهب لرصيدك!\n"
                        f"💲 رصيدك الحالي: {new_bal:,} ذهب\n\n"
                        f"📦 لشراء باقة اكتب:\n"
                        f"• شراء ساعة ({1:,} ذهب)\n"
                        f"• شراء 3 ساعات ({3000:,} ذهب)\n"
                        f"• شراء يوم ({10000:,} ذهب)\n"
                        f"• شراء أسبوع ({50000:,} ذهب)"
                    )
                    print(f"[Wallet] أضيف {tip_amount} للمحفظة - @{sender.username} | الرصيد: {new_bal}")
                except Exception as _dm_err:
                    print(f"[Wallet] خطأ إرسال إشعار المحفظة: {_dm_err}")
                return

            # ====== نظام VIP العادي (للمبالغ التي لا تطابق باقات البوت) ======
            if tip_amount >= 10:
                uses_to_add = int((tip_amount / 10) * 3)
                
                if sender.id not in self.vip_uses:
                    self.vip_uses[sender.id] = 0
                self.vip_uses[sender.id] += uses_to_add
                self.save_vip_uses()
                
                if self.bot_lang == "en":
                    await self.highrise.chat(f"✅ Thank you @{sender.username}! You received {uses_to_add} VIP uses for {tip_amount} gold.")
                    await self.highrise.send_whisper(sender.id, f"💎 You can now use the 'vip' command to teleport to Zone 3 ({self.vip_uses[sender.id]} uses remaining).")
                else:
                    await self.highrise.chat(f"✅ Thank you @{sender.username}! You got {uses_to_add} VIP uses for {tip_amount} gold." if self.bot_lang == "en" else f"✅ شكراً @{sender.username}! حصلت على {uses_to_add} استخدام لأمر VIP مقابل {tip_amount} ذهب.")
                    await self.highrise.send_whisper(sender.id, f"💎 يمكنك الآن استخدام أمر 'vip' للانتقال للمنطقة 3 ({self.vip_uses[sender.id]} مرة متبقية).")
                return

    async def reset_target_position(self, target_user_obj: User, initial_position: Position) -> None:
        try:
            while True:
                room_users = await self.highrise.get_room_users()
                current_position = next((position for user, position in room_users.content if user.id == target_user_obj.id), None)

                if current_position and current_position != initial_position:
                    await self.teleport(target_user_obj, initial_position)

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"An error occurred during position monitoring: {e}")

    async def spam_loop(self) -> None:
        """حلقة تكرار الرسائل"""
        try:
            while self.spam_active and self.spam_message:
                await self.highrise.chat(self.spam_message)
                await asyncio.sleep(3)  # انتظار 3 ثوانِ بين كل رسالة
        except asyncio.CancelledError:
            print("Spam loop cancelled")
        except Exception as e:
            print(f"Error in spam loop: {e}")
            self.spam_active = False

    async def ghost_loop(self) -> None:
        """حلقة رقصة الجوست المتكررة للبوت"""
        try:
            while self.ghost_active:
                try:
                    await self.highrise.send_emote("emote-ghost-idle")
                except Exception as e:
                    print(f"Ghost emote error: {e}")
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("Ghost loop cancelled")
        except Exception as e:
            print(f"Error in ghost loop: {e}")
            self.ghost_active = False

    async def laugh_loop(self) -> None:
        """حلقة الضحك المتكررة للبوت"""
        try:
            while self.laugh_active:
                try:
                    await self.highrise.send_emote("emote-laughing")
                except Exception as e:
                    print(f"Laugh emote error: {e}")
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            print("Laugh loop cancelled")
        except Exception as e:
            print(f"Error in laugh loop: {e}")
            self.laugh_active = False

    async def disguise_loop(self) -> None:
        """حلقة التمويه - يمشي البوت تلقائياً في الروم"""
        walk_positions = [
            Position(2.5, 0.0, 2.5, "FrontRight"),
            Position(5.0, 0.0, 5.0, "FrontLeft"),
            Position(8.0, 0.0, 8.0, "FrontRight"),
            Position(3.0, 0.0, 10.0, "FrontLeft"),
            Position(10.0, 0.0, 3.0, "FrontRight"),
            Position(6.0, 0.0, 12.0, "FrontLeft"),
            Position(12.0, 0.0, 6.0, "FrontRight"),
            Position(4.0, 0.0, 14.0, "FrontLeft"),
            Position(14.0, 0.0, 4.0, "FrontRight"),
            Position(7.0, 0.0, 7.0, "FrontLeft"),
            Position(9.0, 0.0, 11.0, "FrontRight"),
            Position(11.0, 0.0, 9.0, "FrontLeft"),
        ]
        try:
            while self.disguise_mode:
                target = random.choice(walk_positions)
                try:
                    await self.highrise.walk_to(target)
                except Exception as e:
                    print(f"Disguise walk error: {e}")
                await asyncio.sleep(random.randint(5, 12))
        except asyncio.CancelledError:
            print("Disguise loop cancelled")
        except Exception as e:
            print(f"Error in disguise loop: {e}")
            self.disguise_mode = False

    async def dance_zone_scanner(self) -> None:
        """مسح دوري كل 3 ثوانٍ لاكتشاف من دخل/خرج منطقة الرقص وتشغيل/إيقاف رقصهم"""
        await asyncio.sleep(1)
        while self.dance_zone_active and self.dance_zone_pos is not None:
            try:
                cx = self.dance_zone_pos.x
                cz = self.dance_zone_pos.z
                r  = self.dance_zone_radius
                room_users = await self.highrise.get_room_users()
                current_in_zone = set()

                for ru, pos in room_users.content:
                    if ru.id == self.bot_id:
                        continue
                    if not isinstance(pos, Position):
                        continue
                    dist = ((pos.x - cx) ** 2 + (pos.z - cz) ** 2) ** 0.5
                    if dist <= r:
                        current_in_zone.add(ru.id)
                        # بدء الرقص إذا لم يكن يرقص بالفعل
                        if ru.id not in self.dance_zone_users:
                            self.dance_zone_users.add(ru.id)
                            asyncio.create_task(self.start_dance_zone_loop(ru.id))
                            print(f"[DanceZone] بدء رقص {ru.username}")

                # إيقاف من خرج من المنطقة
                left_zone = self.dance_zone_users - current_in_zone
                for uid in left_zone:
                    self.dance_zone_users.discard(uid)
                    if self.user_emote_loops.get(uid) == "dance_zone":
                        await self.stop_emote_loop(uid)
                        print(f"[DanceZone] إيقاف رقص مستخدم غادر المنطقة {uid}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[DanceZone] خطأ في المسح الدوري: {e}")
            await asyncio.sleep(3)

    async def start_dance_zone_loop(self, user_id: str) -> None:
        """بدء حلقة رقص منطقة الرقص - يمر على الرقصات المجانية فقط بالتسلسل"""
        await self.stop_emote_loop(user_id)
        self.user_emote_loops[user_id] = "dance_zone"
        free_emotes_list = list(free_emotes.values())

        async def _loop():
            idx = 0
            while self.user_emote_loops.get(user_id) == "dance_zone":
                if not free_emotes_list:
                    await asyncio.sleep(2)
                    continue
                info = free_emotes_list[idx % len(free_emotes_list)]
                idx += 1
                try:
                    await self.highrise.send_emote(info["value"], user_id)
                    print(f"[DanceZone] ✅ إرسال {info['value']} → {user_id}")
                    await asyncio.sleep(max(info["time"], 2))
                except asyncio.CancelledError:
                    return
                except Exception as _e:
                    err = str(_e)
                    print(f"[DanceZone] ❌ خطأ {info['value']} → {user_id}: {err}")
                    if "not in room" in err.lower() or "target user" in err.lower():
                        self.dance_zone_users.discard(user_id)
                        self.user_emote_loops.pop(user_id, None)
                        return
                    await asyncio.sleep(1)

        if not hasattr(self, 'user_emote_tasks'):
            self.user_emote_tasks = {}
        task = asyncio.create_task(_loop())
        self.user_emote_tasks[user_id] = task

    async def loop(self) -> None:
        """حلقة الرقص التلقائية للبوت"""
        await asyncio.sleep(10)
        while True:
            try:
                if self.dance_active and self.dans:
                    emote_id = random.choice(self.dans)
                    await self.highrise.send_emote(emote_id)
                    self.last_heartbeat = time.time()
                elif not self.dance_active:
                    self.last_heartbeat = time.time()
                    await asyncio.sleep(5)
                    continue
                else:
                    print("No dance emotes available")
                await asyncio.sleep(21)
            except Exception as e:
                print(f"Error in dance loop: {e}")
                await asyncio.sleep(21)

    

      


    async def run(self, room_id, token) -> None:
        await __main__.main(self, room_id, token)
class WebServer():

  def __init__(self):
    self.app = Flask(__name__)

    @self.app.route('/')
    def index() -> str:
      return "Alive"

  def run(self) -> None:
    self.app.run(host='0.0.0.0', port=8080)

  def keep_alive(self):
    t = Thread(target=self.run)
    t.start()

# ==================== نظام إدارة البوتات الفرعية ====================

SUB_BOT_THREADS = {}  # {bot_id: threading.Thread}
SUB_BOT_PAUSE_SIGNALS = {}  # {bot_id: True} - إشارة لإيقاف البوت مؤقتاً

def load_sub_bots():
    try:
        if os.path.exists("sub_bots.json"):
            with open("sub_bots.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading sub_bots: {e}")
    return []

def save_sub_bots(bots):
    try:
        with open("sub_bots.json", "w", encoding="utf-8") as f:
            json.dump(bots, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving sub_bots: {e}")

def get_available_sub_bot():
    import random
    bots = load_sub_bots()
    available = [b for b in bots if b["status"] == "available" and b.get("token")]
    if not available:
        return None
    return random.choice(available)

def release_sub_bot(bot_id):
    bots = load_sub_bots()
    for bot in bots:
        if bot["id"] == bot_id:
            # لا تعيد التعيين إذا كان البوت في وضع الإيقاف المؤقت
            if bot.get("status") == "paused":
                break
            bot["status"] = "available"
            bot["room_id"] = None
            bot["buyer"] = None
            bot["buyer_id"] = None
            bot["expires_at"] = None
            bot["remaining_seconds"] = None
            break
    save_sub_bots(bots)
    if bot_id in SUB_BOT_THREADS:
        del SUB_BOT_THREADS[bot_id]
    print(f"[SubBot #{bot_id}] تم تحرير البوت وأصبح متاحاً")

def deploy_sub_bot(bot_id, token, room_id, buyer, hours, buyer_id=None, invite_id=None):
    """تشغيل بوت فرعي في غرفة المشتري"""
    import threading as _threading
    from datetime import timedelta

    # تحديث الحالة في الملف
    bots = load_sub_bots()
    expires_at = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    for bot in bots:
        if bot["id"] == bot_id:
            bot["status"] = "busy"
            bot["room_id"] = room_id
            bot["buyer"] = buyer
            bot["buyer_id"] = buyer_id
            bot["expires_at"] = expires_at
            bot["remaining_seconds"] = None
            break
    save_sub_bots(bots)

    def run_bot():
        import os as _os
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print(f"[SubBot #{bot_id}] بدء التشغيل في الغرفة: {room_id}")
        if invite_id:
            _os.environ["HR_INVITE_ID"] = invite_id
            print(f"[SubBot #{bot_id}] استخدام invite-id: {invite_id}")
        permission_error = False
        try:
            sub = SubBot(bot_id, expires_at)
            loop.run_until_complete(
                main([BotDefinition(sub, room_id, token)])
            )
        except Exception as e:
            err_str = str(e)
            print(f"[SubBot #{bot_id}] انتهى: {err_str}")
            if "designer rights" in err_str.lower() or "invited to enter" in err_str.lower() or "designer" in err_str.lower():
                permission_error = True
        finally:
            loop.close()
            release_sub_bot(bot_id)

        # إخبار المشتري بخطأ الصلاحيات وإتاحة المحاولة مجدداً
        if permission_error and buyer_id:
            print(f"[SubBot #{bot_id}] خطأ صلاحيات - جاري إعادة المشتري للانتظار")
            try:
                global bot_instance
                # إعادة المشتري فوراً لحالة الانتظار (بدون انتظار الإشعار)
                if bot_instance:
                    # اختيار بوت متاح عشوائي جديد للمحاولة التالية
                    _retry_new_bot = get_available_sub_bot()
                    _retry_entry = {
                        "step": "waiting_room",
                        "package": f"إعادة محاولة ({hours}h)",
                        "duration": f"{hours} ساعة",
                        "hours": hours,
                        "amount": 0,
                        "username": buyer,
                    }
                    if _retry_new_bot:
                        _retry_entry["assigned_bot_id"] = _retry_new_bot["id"]
                        _retry_entry["assigned_bot_token"] = _retry_new_bot["token"]
                        _retry_entry["assigned_bot_username"] = _retry_new_bot.get("username", "")
                    bot_instance.pending_bot_purchases[buyer_id] = _retry_entry
                    print(f"[SubBot #{bot_id}] تم إعادة المشتري {buyer} لحالة الانتظار")

                main_loop = getattr(bot_instance, 'loop_ref', None) if bot_instance else None
                print(f"[SubBot #{bot_id}] loop_ref موجود: {main_loop is not None}")

                if main_loop and not main_loop.is_closed():
                    _new_bot_uname = _retry_new_bot.get("username") if _retry_new_bot else None
                    _uname_line = f"🤖 يوزر البوت الجديد: @{_new_bot_uname}\n\n" if _new_bot_uname else ""
                    notify_msg = (
                        f"❌ فشل دخول البوت للغرفة!\n\n"
                        f"⚠️ البوت لا يملك صلاحية دخول غرفتك.\n\n"
                        f"{_uname_line}"
                        f"✅ الحل - أضف البوت كـ Designer:\n"
                        f"1️⃣ افتح غرفتك في Highrise\n"
                        f"2️⃣ اضغط ⚙️ إعدادات الغرفة\n"
                        f"3️⃣ اختر Designers ثم Add Designer\n"
                        f"4️⃣ ابحث عن @{_new_bot_uname or 'البوت'} وأضفه\n\n"
                        f"✅ بعد الإضافة أرسل لي معرف الغرفة مجدداً:\n"
                        f"🔁 {room_id}\n\n"
                        f"⚠️ لم يُخصم وقتك، يمكنك المحاولة مجدداً."
                    )

                    async def notify_buyer():
                        try:
                            await bot_instance.highrise.send_message_bulk([buyer_id], notify_msg)
                            print(f"[SubBot #{bot_id}] تم إرسال إشعار الصلاحيات للمشتري {buyer}")
                        except Exception as e1:
                            print(f"[SubBot #{bot_id}] فشل send_message_bulk: {e1}")
                            try:
                                await bot_instance.highrise.send_direct_message(buyer_id, notify_msg)
                                print(f"[SubBot #{bot_id}] تم الإرسال عبر send_direct_message")
                            except Exception as e2:
                                print(f"[SubBot #{bot_id}] فشل send_direct_message أيضاً: {e2}")

                    future = asyncio.run_coroutine_threadsafe(notify_buyer(), main_loop)
                    try:
                        future.result(timeout=10)
                    except Exception as fut_err:
                        print(f"[SubBot #{bot_id}] خطأ في نتيجة Future: {fut_err}")
                else:
                    print(f"[SubBot #{bot_id}] loop_ref غير متاح أو مغلق - لا يمكن إرسال الإشعار")
            except Exception as outer_err:
                print(f"[SubBot #{bot_id}] خطأ خارجي في الإشعار: {outer_err}")

    t = _threading.Thread(target=run_bot, daemon=True, name=f"SubBot-{bot_id}")
    SUB_BOT_THREADS[bot_id] = t
    t.start()
    print(f"[SubBot #{bot_id}] تم التشغيل - الغرفة: {room_id} - المشتري: {buyer} - المدة: {hours}h")
    return expires_at


class SubBot(Bot):
    """بوت فرعي مستأجر - يحتوي على جميع أوامر البوت الرئيسي ويعمل لمدة محددة"""

    def __init__(self, bot_id: int, expires_at: str):
        super().__init__()
        self.bot_id_num = bot_id
        self.expires_at = expires_at
        self._expiry_task = None

    async def on_start(self, session_metadata) -> None:
        # تشغيل كل تهيئة البوت الرئيسي (يحمّل الأوامر والإعدادات) بدون تغيير global bot_instance
        self.loop_ref = asyncio.get_running_loop()
        self.last_heartbeat = time.time()
        self.start_time = datetime.now()
        self.bot_id = session_metadata.user_id
        try:
            self.room_id = getattr(self, "room_id", "Unknown")
            if self.room_id == "Unknown":
                self.room_id = getattr(session_metadata, "room_id", "Unknown")
            self.room_name = getattr(session_metadata.room_info, "room_name", "Unknown")
            self.room_owner_id = getattr(session_metadata.room_info, "owner_id", "Unknown")
        except Exception as e:
            print(f"[SubBot #{self.bot_id_num}] خطأ في معلومات الغرفة: {e}")

        if not hasattr(self, 'webapi') or self.webapi is None:
            try:
                if WebApi:
                    self.webapi = WebApi()
            except Exception:
                pass

        print(f"[SubBot #{self.bot_id_num}] ✅ متصل بالغرفة: {self.room_id}")

        # حفظ يوزر البوت الفرعي في sub_bots.json لعرضه للمشتري مستقبلاً
        try:
            user_info = await self.webapi.get_user(self.bot_id)
            sub_username = None
            if user_info and hasattr(user_info, 'user') and user_info.user:
                sub_username = user_info.user.username
            elif user_info and hasattr(user_info, 'username'):
                sub_username = user_info.username
            if sub_username:
                _bots = load_sub_bots()
                for _b in _bots:
                    if _b["id"] == self.bot_id_num:
                        _b["username"] = sub_username
                        break
                save_sub_bots(_bots)
                print(f"[SubBot #{self.bot_id_num}] يوزر البوت: @{sub_username}")
        except Exception as _ue:
            print(f"[SubBot #{self.bot_id_num}] خطأ في حفظ اليوزر: {_ue}")

        # إعلان الدخول للغرفة
        try:
            remaining_seconds = max(0, (datetime.strptime(self.expires_at, "%Y-%m-%d %H:%M:%S") - datetime.now()).total_seconds())
            hours_left = int(remaining_seconds // 3600)
            mins_left = int((remaining_seconds % 3600) // 60)
            await self.highrise.chat(
                f"🤖 البوت #{self.bot_id_num} دخل الغرفة! ⏳ المدة المتبقية: {hours_left}h {mins_left}m"
            )
        except Exception as e:
            print(f"[SubBot #{self.bot_id_num}] خطأ chat: {e}")

        # مهمة انتهاء الإيجار
        self._expiry_task = asyncio.create_task(self._wait_for_expiry())

    async def _wait_for_expiry(self):
        try:
            expires = datetime.strptime(self.expires_at, "%Y-%m-%d %H:%M:%S")
            while True:
                remaining = (expires - datetime.now()).total_seconds()
                # فحص انتهاء المدة
                if remaining <= 0:
                    print(f"[SubBot #{self.bot_id_num}] انتهت مدة الإيجار.")
                    try:
                        await self.highrise.chat("⏰ Rental period ended. Thank you for using our services! 🤖" if self.bot_lang == "en" else "⏰ انتهت مدة الإيجار. شكراً لاستخدامك خدماتنا! 🤖")
                    except Exception:
                        pass
                    raise Exception(f"[SubBot #{self.bot_id_num}] انتهت مدة الإيجار")
                # فحص إشارة الإيقاف المؤقت
                if SUB_BOT_PAUSE_SIGNALS.get(self.bot_id_num):
                    del SUB_BOT_PAUSE_SIGNALS[self.bot_id_num]
                    print(f"[SubBot #{self.bot_id_num}] استقبال إشارة الإيقاف المؤقت. متبقي: {int(remaining)}s")
                    # حفظ الوقت المتبقي في الملف كـ "paused"
                    try:
                        bots = load_sub_bots()
                        for b in bots:
                            if b["id"] == self.bot_id_num:
                                b["status"] = "paused"
                                b["remaining_seconds"] = int(remaining)
                                break
                        save_sub_bots(bots)
                    except Exception as save_err:
                        print(f"[SubBot #{self.bot_id_num}] خطأ حفظ الإيقاف: {save_err}")
                    try:
                        await self.highrise.chat("⏸️ Bot paused. Can be restarted via direct messages." if self.bot_lang == "en" else "⏸️ تم إيقاف البوت مؤقتاً. يمكن إعادة تشغيله عبر الرسائل الخاصة.")
                    except Exception:
                        pass
                    # إيقاف حلقة الحدث لإخراج البوت فعلياً من الغرفة
                    print(f"[SubBot #{self.bot_id_num}] جاري إخراج البوت من الغرفة...")
                    self.loop_ref.stop()
                    return
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass


class RunBot():
  room_id = "6990fc95f837018b8250a706"
  original_room_id = "69c00fad01bb6681f9d52a76"  # الغرفة الأصلية (لا تتغير)
  previous_room_id = None  # الغرفة السابقة قبل !join
  pending_follow = False  # حالة الانتقال للغرفة الجديدة
  bot_token = "b2ebe278307b858a1a39b9df18536fe742bba24a1ed2cd9dd8a69bbe3204a120"
  bot_file = "main"
  bot_class = "Bot"

  def __init__(self) -> None:
    # Ensure the Bot instance can access the room_id
    bot_instance = Bot()
    # Explicitly set the room_id from the class variable to the bot instance
    bot_instance.room_id = RunBot.room_id
    self.definitions = [
        BotDefinition(bot_instance, RunBot.room_id, self.bot_token)
    ] 

  def run_loop(self) -> None:
    while True:
      try:
        # إنشاء نسخة جديدة من البوت مع room_id الحالي (قد يتغير عند المتابعة لغرفة جديدة)
        current_room_id = RunBot.room_id
        bot_instance = Bot()
        bot_instance.room_id = current_room_id
        definitions = [BotDefinition(bot_instance, current_room_id, self.bot_token)]
        arun(main(definitions)) 
        print("Bot session ended normally, waiting 2 seconds before reconnecting...")
      except Exception as e:
        import traceback
        print("Caught an exception:")
        traceback.print_exc()
        print("Waiting 2 seconds before reconnecting...")
      time.sleep(2)


if __name__ == "__main__":
  flask_thread = Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  ping_thread = Thread(target=self_ping_loop)
  ping_thread.daemon = True
  ping_thread.start()

  is_deployed = os.environ.get("REPLIT_DEPLOYMENT", "") == "1"
  dev_bot_enabled = os.environ.get("DEV_BOT_ENABLED", "") == "1"

  if is_deployed or dev_bot_enabled:
    WebServer().keep_alive()
    RunBot().run_loop()
  else:
    print(">>> وضع التطوير: لوحة التحكم فقط (البوت يعمل في النسخة المنشورة)")
    print(">>> Dev mode: Dashboard only (bot runs in deployed version)")
    print(">>> لتشغيل البوت في التطوير: ضع DEV_BOT_ENABLED=1")
    import asyncio
    asyncio.get_event_loop().run_forever()