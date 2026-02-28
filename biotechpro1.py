"""
BioMind AI - Fast Full-Stack Application (Groq Edition)
HOW TO RUN:
1. pip install fastapi uvicorn sqlalchemy groq passlib[bcrypt] python-jose[cryptography] python-multipart email-validator
2. Set your Groq API key on line 22
3. Run: python biotechpro1.py
4. Open browser: http://localhost:5000
"""

import json
import uuid
import itertools
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List

from groq import Groq
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import (Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, JSON, Enum as SAEnum, create_engine, func)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# ── CONFIGURATION ──────────────────────────────────────────────────────────────
DATABASE_URL             = "sqlite:///./biotech.db"
GROQ_API_KEY             = ""   # PUT YOUR KEY HERE
api_key = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"
SECRET_KEY               = "biomind-secret-key-change-in-production"
ALGORITHM                = "HS256"
ACCESS_TOKEN_EXPIRE_MINS = 1440
WEAK_THRESHOLD           = 0.60
STRONG_THRESHOLD         = 0.80
_qid_counter             = itertools.count(start=1)

INDUSTRY_BENCHMARKS = {
    "researcher":          {"PCR": 85, "CRISPR": 80, "Data Analysis": 75, "Scientific Writing": 80, "Bioinformatics": 70},
    "lab_technician":      {"PCR": 90, "Gel Electrophoresis": 90, "DNA Extraction": 85, "Lab Safety": 95, "Cell Culture": 80},
    "bioinformatician":    {"Python": 85, "R Programming": 80, "Bioinformatics": 90, "Statistics": 80, "Machine Learning": 70},
    "bioprocess_engineer": {"Fermentation": 85, "Process Design": 80, "Cell Culture": 85, "Regulatory": 70, "GMP": 80},
    "clinical_associate":  {"Clinical Trials": 85, "GCP": 90, "Regulatory": 80, "Data Analysis": 75, "Medical Writing": 75},
    "regulatory_affairs":  {"Regulatory": 90, "GMP": 85, "Documentation": 85, "Pharmacology": 75, "Risk Assessment": 80},
}

# ── FRONTEND HTML (Pure Vanilla JS - No Babel, No CDN, Instant Load) ──────────
FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>BioMind AI</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
:root{
  --bg:#020a14;--surface:#071828;--surface2:#0a2035;
  --border:#0f3050;--border2:#1a4a70;--accent:#00cfff;--accent2:#00ff99;
  --accent3:#ff7b3a;--text:#e8f4ff;--muted:#4d8aaa;--danger:#ff4560;
}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',sans-serif;min-height:100vh;}
::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-thumb{background:var(--accent);border-radius:2px;}
.hidden{display:none!important;}
#auth-page{min-height:100vh;display:flex;align-items:center;justify-content:center;}
.auth-box{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:40px;width:420px;max-width:95vw;}
.auth-title{font-size:22px;font-weight:700;color:var(--accent);text-align:center;letter-spacing:0.1em;margin-bottom:4px;}
.auth-sub{font-size:12px;color:var(--muted);text-align:center;margin-bottom:24px;}
.form-row{margin-bottom:14px;}
.label{font-size:11px;color:var(--muted);margin-bottom:5px;display:block;font-weight:600;}
.input,.select,.textarea{width:100%;background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:10px 14px;border-radius:8px;font-size:13px;outline:none;font-family:inherit;transition:border-color 0.2s;}
.input:focus,.select:focus,.textarea:focus{border-color:var(--accent);}
.select{cursor:pointer;} .textarea{resize:none;}
.auth-switch{text-align:center;margin-top:16px;font-size:12px;color:var(--muted);}
.auth-switch a{color:var(--accent);cursor:pointer;font-weight:600;}
.error-box{background:rgba(255,69,96,0.1);border:1px solid var(--danger);color:var(--danger);padding:10px 14px;border-radius:8px;font-size:12px;margin-bottom:14px;}
.success-box{background:rgba(0,255,153,0.08);border:1px solid var(--accent2);color:var(--accent2);padding:10px 14px;border-radius:8px;font-size:12px;margin-bottom:14px;}
#app-page{display:flex;height:100vh;overflow:hidden;}
.sidebar{width:220px;min-width:220px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;}
.logo-wrap{padding:20px 16px;border-bottom:1px solid var(--border);}
.logo-name{font-size:18px;font-weight:700;color:var(--accent);letter-spacing:0.1em;}
.logo-tag{font-size:9px;color:var(--muted);margin-top:3px;}
.nav{padding:12px 10px;flex:1;display:flex;flex-direction:column;gap:3px;}
.nav-section{font-size:9px;color:var(--muted);letter-spacing:0.12em;padding:8px 8px 5px;text-transform:uppercase;}
.nav-btn{display:flex;align-items:center;gap:10px;padding:11px 12px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:500;color:var(--muted);transition:all 0.15s;border:1px solid transparent;}
.nav-btn:hover{color:var(--text);border-color:var(--border);background:var(--surface2);}
.nav-btn.active{color:var(--accent);border-color:var(--border2);background:rgba(0,207,255,0.05);}
.nav-badge{margin-left:auto;font-size:9px;padding:2px 6px;border-radius:8px;background:var(--accent);color:var(--bg);font-weight:700;}
.profile-card{margin:10px;padding:14px;background:var(--surface2);border:1px solid var(--border);border-radius:10px;}
.pname{font-size:13px;font-weight:700;color:var(--text);}
.plevel{font-size:10px;color:var(--accent2);margin-top:2px;}
.pbar{margin-top:8px;background:var(--border);border-radius:3px;height:3px;}
.pfill{height:3px;border-radius:3px;background:linear-gradient(90deg,var(--accent),var(--accent2));width:35%;}
.pinst{font-size:10px;color:var(--muted);margin-top:5px;}
.logout-btn{width:100%;margin-top:8px;padding:6px;border-radius:7px;background:transparent;border:1px solid var(--border);color:var(--muted);font-size:11px;cursor:pointer;transition:all 0.2s;font-family:inherit;}
.logout-btn:hover{border-color:var(--danger);color:var(--danger);}
.main-area{flex:1;display:flex;flex-direction:column;overflow:hidden;}
.topbar{padding:16px 24px;border-bottom:1px solid var(--border);background:var(--surface);display:flex;align-items:center;justify-content:space-between;}
.page-title{font-size:17px;font-weight:700;color:var(--text);}
.page-desc{font-size:11px;color:var(--muted);margin-top:2px;}
.status-dot{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--accent2);padding:5px 10px;border-radius:16px;border:1px solid rgba(0,255,153,0.3);background:rgba(0,255,153,0.05);}
.dot{width:6px;height:6px;border-radius:50%;background:var(--accent2);animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.3;}}
.content{flex:1;overflow-y:auto;padding:24px;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:22px;margin-bottom:18px;}
.card:hover{border-color:var(--border2);}
.card-title{font-size:13px;font-weight:700;color:var(--accent);letter-spacing:0.06em;margin-bottom:4px;}
.card-sub{font-size:11px;color:var(--muted);margin-bottom:18px;}
.btn{padding:9px 20px;border-radius:8px;border:none;cursor:pointer;font-size:13px;font-weight:600;transition:all 0.15s;display:inline-flex;align-items:center;gap:6px;font-family:inherit;}
.btn-primary{background:linear-gradient(135deg,var(--accent),#0099cc);color:var(--bg);}
.btn-primary:hover{opacity:0.9;transform:translateY(-1px);}
.btn-green{background:linear-gradient(135deg,var(--accent2),#00cc77);color:var(--bg);}
.btn-outline{background:transparent;border:1px solid var(--border2);color:var(--text);}
.btn-outline:hover{border-color:var(--accent);color:var(--accent);}
.btn-sm{padding:6px 12px;font-size:12px;border-radius:7px;}
.btn:disabled{opacity:0.4;cursor:not-allowed;transform:none!important;}
.chat-wrap{max-height:380px;overflow-y:auto;display:flex;flex-direction:column;gap:12px;margin-bottom:14px;}
.msg{display:flex;gap:8px;} .msg.user{flex-direction:row-reverse;}
.avatar{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;background:var(--surface2);border:1px solid var(--border);color:var(--muted);}
.bubble{max-width:80%;padding:11px 15px;border-radius:10px;font-size:13px;line-height:1.7;white-space:pre-wrap;}
.msg.ai .bubble{background:var(--surface2);border:1px solid var(--border);}
.msg.user .bubble{background:rgba(0,207,255,0.08);border:1px solid rgba(0,207,255,0.2);color:var(--accent);}
.typing{display:flex;gap:4px;align-items:center;padding:11px 15px;background:var(--surface2);border:1px solid var(--border);border-radius:10px;}
.tdot{width:6px;height:6px;background:var(--accent);border-radius:50%;animation:td 1.2s infinite;}
.tdot:nth-child(2){animation-delay:0.2s;}.tdot:nth-child(3){animation-delay:0.4s;}
@keyframes td{0%,60%,100%{transform:translateY(0);}30%{transform:translateY(-5px);}}
.chat-input-row{display:flex;gap:8px;}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;}
.chip{padding:5px 11px;border-radius:16px;border:1px solid var(--border);cursor:pointer;font-size:11px;color:var(--muted);background:var(--surface2);transition:all 0.15s;font-family:inherit;}
.chip:hover{border-color:var(--accent);color:var(--accent);}
.q-text{font-size:14px;font-weight:600;line-height:1.6;margin-bottom:16px;color:var(--text);}
.opt{padding:12px 16px;border-radius:8px;border:1px solid var(--border);cursor:pointer;margin-bottom:8px;font-size:13px;transition:all 0.15s;background:var(--surface2);display:flex;align-items:center;gap:10px;}
.opt:hover:not(.locked){border-color:var(--accent);color:var(--accent);}
.opt.correct{border-color:var(--accent2)!important;color:var(--accent2);background:rgba(0,255,153,0.05);}
.opt.wrong{border-color:var(--danger)!important;color:var(--danger);background:rgba(255,69,96,0.05);}
.opt.locked{cursor:not-allowed;}
.opt-letter{width:24px;height:24px;border-radius:50%;border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;}
.exp-box{padding:12px 16px;border-radius:8px;background:rgba(0,255,153,0.05);border:1px solid rgba(0,255,153,0.25);font-size:12px;color:#88ffcc;margin-top:12px;line-height:1.7;}
.follow-box{padding:11px 16px;border-radius:8px;background:rgba(255,123,58,0.05);border:1px solid rgba(255,123,58,0.25);font-size:12px;color:var(--accent3);margin-top:8px;}
.score-row{display:flex;gap:10px;margin-bottom:16px;}
.score-pill{flex:1;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:10px 14px;}
.score-label{font-size:10px;color:var(--muted);}
.score-val{font-size:20px;font-weight:700;color:var(--accent);margin-top:2px;}
.scenario-badge{padding:12px 16px;border-radius:8px;background:rgba(198,120,255,0.06);border:1px solid rgba(198,120,255,0.25);font-size:13px;line-height:1.6;color:#e0b8ff;margin-bottom:14px;}
.lab-scene{padding:16px;background:var(--surface2);border-radius:10px;border-left:3px solid var(--accent3);font-size:13px;line-height:1.7;margin-bottom:14px;}
.lab-opt{padding:11px 16px;border-radius:8px;background:var(--surface2);border:1px solid var(--border);cursor:pointer;font-size:13px;transition:all 0.15s;margin-bottom:7px;display:flex;align-items:center;gap:8px;}
.lab-opt:hover{border-color:var(--accent3);color:var(--accent3);}
.lab-log{font-size:11px;color:var(--muted);background:#010810;padding:12px;border-radius:8px;border:1px solid var(--border);margin-top:12px;max-height:130px;overflow-y:auto;line-height:1.9;font-family:monospace;}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:11px;margin-bottom:18px;}
.stat-card{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:16px;text-align:center;}
.stat-num{font-size:26px;font-weight:700;color:var(--accent);}
.stat-lbl{font-size:10px;color:var(--muted);margin-top:3px;}
.barchart{margin-bottom:12px;}
.bar-label{font-size:11px;color:var(--muted);display:flex;justify-content:space-between;margin-bottom:4px;}
.bar-bg{background:var(--border);border-radius:3px;height:6px;}
.bar-fill{height:6px;border-radius:3px;transition:width 0.6s;}
.readiness-wrap{text-align:center;padding:16px 0;}
.readiness-num{font-size:56px;font-weight:700;line-height:1;}
.readiness-lbl{font-size:10px;color:var(--muted);letter-spacing:0.08em;margin-top:5px;}
.skill-chip{display:inline-block;padding:4px 10px;border-radius:16px;font-size:11px;margin:3px;border:1px solid;font-weight:500;}
.chip-good{border-color:var(--accent2);color:var(--accent2);}
.chip-bad{border-color:var(--danger);color:var(--danger);}
.road-step{display:flex;gap:12px;margin-bottom:14px;}
.road-dot{width:10px;height:10px;border-radius:50%;background:var(--accent);flex-shrink:0;margin-top:4px;}
.road-num{font-size:10px;color:var(--accent);font-weight:700;margin-bottom:2px;}
.road-text{font-size:13px;line-height:1.6;color:var(--text);}
.divider{height:1px;background:var(--border);margin:16px 0;}
.spinner-wrap{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:13px;padding:12px 0;}
.spinner{width:16px;height:16px;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin 0.7s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}
.flex{display:flex;} .gap8{gap:8px;} .gap10{gap:10px;} .wrap{flex-wrap:wrap;} .flex1{flex:1;}
.mb8{margin-bottom:8px;} .mb10{margin-bottom:10px;} .mb14{margin-bottom:14px;} .mb16{margin-bottom:16px;} .mb18{margin-bottom:18px;}
.mt8{margin-top:8px;} .mt12{margin-top:12px;} .mt14{margin-top:14px;} .mt16{margin-top:16px;}
</style>
</head>
<body>

<!-- AUTH PAGE -->
<div id="auth-page">
  <div class="auth-box">
    <div class="auth-title">BIOMIND AI</div>
    <div class="auth-sub">AI-Powered Biotechnology Learning Platform</div>
    <div id="auth-error" class="error-box hidden"></div>
    <div id="auth-ok" class="success-box hidden"></div>
    <div id="register-fields" class="hidden">
      <div class="form-row"><label class="label">FULL NAME</label><input class="input" id="reg-name" placeholder="Your name"/></div>
      <div class="form-row"><label class="label">INSTITUTION</label><input class="input" id="reg-inst" placeholder="Your college/company"/></div>
      <div class="form-row"><label class="label">LEVEL</label>
        <select class="select" id="reg-level">
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>
      </div>
    </div>
    <div class="form-row"><label class="label">EMAIL</label><input class="input" id="auth-email" type="email" placeholder="you@email.com"/></div>
    <div class="form-row"><label class="label">PASSWORD</label><input class="input" id="auth-pass" type="password" placeholder="Password"/></div>
    <button class="btn btn-primary" id="auth-btn" style="width:100%;justify-content:center;padding:12px;" onclick="authSubmit()">Login</button>
    <div class="auth-switch">
      <span id="auth-switch-text">No account? <a onclick="toggleAuth()">Register here</a></span>
    </div>
  </div>
</div>

<!-- APP PAGE -->
<div id="app-page" class="hidden">
  <div class="sidebar">
    <div class="logo-wrap">
      <div class="logo-name">BIOMIND AI</div>
      <div class="logo-tag">POWERED BY GROQ + LLAMA 3</div>
    </div>
    <nav class="nav">
      <div class="nav-section">MODULES</div>
      <div class="nav-btn active" id="nav-learn" onclick="navTo('learn')">AI Tutor</div>
      <div class="nav-btn" id="nav-quiz" onclick="navTo('quiz')">Quiz Engine</div>
      <div class="nav-btn" id="nav-lab" onclick="navTo('lab')">Virtual Lab <span class="nav-badge">NEW</span></div>
      <div class="nav-btn" id="nav-career" onclick="navTo('career')">Career Mentor</div>
      <div class="nav-btn" id="nav-analytics" onclick="navTo('analytics')">Analytics</div>
    </nav>
    <div class="profile-card">
      <div class="pname" id="prof-name"></div>
      <div class="plevel" id="prof-level"></div>
      <div class="pbar"><div class="pfill"></div></div>
      <div class="pinst" id="prof-inst"></div>
      <button class="logout-btn" onclick="logout()">Sign Out</button>
    </div>
  </div>
  <div class="main-area">
    <div class="topbar">
      <div>
        <div class="page-title" id="page-title">AI LEARNING TUTOR</div>
        <div class="page-desc" id="page-desc">Powered by Groq + Llama 3</div>
      </div>
      <div class="status-dot"><div class="dot"></div>GROQ CONNECTED</div>
    </div>
    <div class="content" id="main-content"></div>
  </div>
</div>

<script>
var TOKEN = localStorage.getItem('bm_token') || '';
var USER  = JSON.parse(localStorage.getItem('bm_user') || 'null');
var IS_LOGIN = true;

var TOPICS = ["PCR & DNA Amplification","Gel Electrophoresis","CRISPR-Cas9","Cell Culture","Bioinformatics Basics","Protein Folding","Fermentation Biotech","Stem Cell Biology","Drug Discovery Pipeline","Metagenomics"];
var ROLES  = [{v:"researcher",l:"Research Scientist"},{v:"lab_technician",l:"Lab Technician"},{v:"bioinformatician",l:"Bioinformatician"},{v:"bioprocess_engineer",l:"Bioprocess Engineer"},{v:"clinical_associate",l:"Clinical Research Associate"},{v:"regulatory_affairs",l:"Regulatory Affairs"}];
var LABS   = [{v:"pcr",l:"PCR"},{v:"gel_electrophoresis",l:"Gel Electrophoresis"},{v:"dna_extraction",l:"DNA Extraction"}];
var COLORS = ["#00cfff","#00ff99","#ff7b3a","#ff4560","#c678ff","#f0b429"];
var PAGE_META = {
  learn:     {t:"AI LEARNING TUTOR",    d:"Personalized lessons powered by Groq + Llama 3"},
  quiz:      {t:"QUIZ AND ASSESSMENT",  d:"LLM-generated questions with instant feedback"},
  lab:       {t:"VIRTUAL LAB",          d:"Decision-based experiment simulation"},
  career:    {t:"CAREER MENTOR",        d:"Industry skill-gap analysis and roadmap"},
  analytics: {t:"ANALYTICS DASHBOARD", d:"Performance tracking and improvement insights"}
};

// ── API HELPERS ────────────────────────────────────────────────────────────────
async function api(method, path, body) {
  var headers = {'Content-Type':'application/json'};
  if (TOKEN) headers['Authorization'] = 'Bearer ' + TOKEN;
  var res = await fetch(path, {method:method, headers:headers, body: body ? JSON.stringify(body) : undefined});
  var data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

async function apiForm(path, fields) {
  var form = new URLSearchParams(fields);
  var res = await fetch(path, {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:form});
  var data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Login failed');
  return data;
}

function spinner() { return '<div class="spinner-wrap"><div class="spinner"></div><span>Please wait...</span></div>'; }
function topicOpts() { return TOPICS.map(function(t){ return '<option>' + t + '</option>'; }).join(''); }

// ── AUTH ───────────────────────────────────────────────────────────────────────
function toggleAuth() {
  IS_LOGIN = !IS_LOGIN;
  document.getElementById('register-fields').classList.toggle('hidden', IS_LOGIN);
  document.getElementById('auth-btn').textContent = IS_LOGIN ? 'Login' : 'Create Account';
  document.getElementById('auth-switch-text').innerHTML = IS_LOGIN
    ? 'No account? <a onclick="toggleAuth()">Register here</a>'
    : 'Have account? <a onclick="toggleAuth()">Login here</a>';
  document.getElementById('auth-error').classList.add('hidden');
  document.getElementById('auth-ok').classList.add('hidden');
}

async function authSubmit() {
  var btn   = document.getElementById('auth-btn');
  var email = document.getElementById('auth-email').value.trim();
  var pass  = document.getElementById('auth-pass').value;
  var errEl = document.getElementById('auth-error');
  var okEl  = document.getElementById('auth-ok');
  errEl.classList.add('hidden');
  okEl.classList.add('hidden');
  btn.disabled = true;
  btn.textContent = 'Please wait...';
  try {
    if (IS_LOGIN) {
      var tok = await apiForm('/auth/login', {username:email, password:pass});
      TOKEN = tok.access_token;
      USER  = await api('GET', '/auth/me');
      localStorage.setItem('bm_token', TOKEN);
      localStorage.setItem('bm_user', JSON.stringify(USER));
      showApp();
    } else {
      var name  = document.getElementById('reg-name').value.trim();
      var inst  = document.getElementById('reg-inst').value.trim();
      var level = document.getElementById('reg-level').value;
      await api('POST', '/auth/register', {name:name, email:email, password:pass, institution:inst, level:level});
      okEl.textContent = 'Registered! Please login.';
      okEl.classList.remove('hidden');
      toggleAuth();
    }
  } catch(e) {
    errEl.textContent = e.message;
    errEl.classList.remove('hidden');
  }
  btn.disabled = false;
  btn.textContent = IS_LOGIN ? 'Login' : 'Create Account';
}

function logout() {
  TOKEN = ''; USER = null;
  localStorage.removeItem('bm_token');
  localStorage.removeItem('bm_user');
  document.getElementById('auth-page').classList.remove('hidden');
  document.getElementById('app-page').classList.add('hidden');
}

function showApp() {
  document.getElementById('auth-page').classList.add('hidden');
  document.getElementById('app-page').classList.remove('hidden');
  document.getElementById('prof-name').textContent  = USER.name;
  document.getElementById('prof-level').textContent = USER.level.toUpperCase();
  document.getElementById('prof-inst').textContent  = USER.institution || 'No institution';
  navTo('learn');
}

function navTo(page) {
  document.querySelectorAll('.nav-btn').forEach(function(b){ b.classList.remove('active'); });
  document.getElementById('nav-' + page).classList.add('active');
  document.getElementById('page-title').textContent = PAGE_META[page].t;
  document.getElementById('page-desc').textContent  = PAGE_META[page].d;
  var c = document.getElementById('main-content');
  c.innerHTML = '';
  if (page === 'learn')     renderLearn(c);
  if (page === 'quiz')      renderQuiz(c);
  if (page === 'lab')       renderLab(c);
  if (page === 'career')    renderCareer(c);
  if (page === 'analytics') renderAnalytics(c);
}

// ── LEARN ──────────────────────────────────────────────────────────────────────
var learnMsgs = [];

function renderLearn(c) {
  learnMsgs = [{role:'ai', text:'Hello ' + USER.name + '! I am your AI Biotech Tutor. Select a topic and click Generate Lesson!'}];
  var quick = ['Generate Lesson','Explain like I am 12','Give real-world example','Common mistakes?','Industry applications?'];
  c.innerHTML = '<div class="card">'
    + '<div class="card-title">ADAPTIVE AI TUTOR</div>'
    + '<div class="card-sub">Personalized lessons based on your level and weak areas.</div>'
    + '<div class="flex gap10 wrap mb14">'
    + '<select class="select" id="learn-topic">' + topicOpts() + '</select>'
    + '<select class="select" id="learn-diff"><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select>'
    + '</div>'
    + '<div class="chips" id="learn-chips"></div>'
    + '<div class="chat-wrap" id="chat-wrap"></div>'
    + '<div class="chat-input-row">'
    + '<textarea class="textarea flex1" id="chat-input" rows="2" placeholder="Ask anything..."></textarea>'
    + '<button class="btn btn-primary" id="chat-send" onclick="learnSend(null)">Send</button>'
    + '</div></div>';

  document.getElementById('learn-diff').value = USER.level;

  var chipsEl = document.getElementById('learn-chips');
  quick.forEach(function(q) {
    var b = document.createElement('button');
    b.className = 'chip';
    b.textContent = q;
    b.onclick = function(){ learnSend(q); };
    chipsEl.appendChild(b);
  });

  document.getElementById('chat-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); learnSend(null); }
  });

  drawMsgs();
}

function drawMsgs() {
  var wrap = document.getElementById('chat-wrap');
  if (!wrap) return;
  wrap.innerHTML = '';
  learnMsgs.forEach(function(m) {
    var row = document.createElement('div');
    row.className = 'msg ' + m.role;
    var av = document.createElement('div');
    av.className = 'avatar';
    av.textContent = m.role === 'ai' ? 'AI' : 'ME';
    var bub = document.createElement('div');
    bub.className = 'bubble';
    bub.textContent = m.text;
    row.appendChild(av);
    row.appendChild(bub);
    wrap.appendChild(row);
  });
  wrap.scrollTop = wrap.scrollHeight;
}

function showTyping() {
  var wrap = document.getElementById('chat-wrap');
  if (!wrap) return;
  var row = document.createElement('div');
  row.className = 'msg ai';
  row.id = 'typing-row';
  var av = document.createElement('div');
  av.className = 'avatar';
  av.textContent = 'AI';
  var bub = document.createElement('div');
  bub.className = 'typing';
  bub.innerHTML = '<div class="tdot"></div><div class="tdot"></div><div class="tdot"></div>';
  row.appendChild(av);
  row.appendChild(bub);
  wrap.appendChild(row);
  wrap.scrollTop = wrap.scrollHeight;
}

async function learnSend(text) {
  var input = document.getElementById('chat-input');
  var msg = text || (input ? input.value.trim() : '');
  if (!msg) return;
  if (input) input.value = '';
  var isLesson = msg === 'Generate Lesson';
  var topic = document.getElementById('learn-topic').value;
  var diff  = document.getElementById('learn-diff').value;
  var btn   = document.getElementById('chat-send');
  if (btn) btn.disabled = true;

  learnMsgs.push({role:'user', text: isLesson ? 'Generate lesson: ' + topic + ' (' + diff + ')' : msg});
  drawMsgs();
  showTyping();

  try {
    var data = await api('POST', '/learn/generate-lesson', {topic:topic, difficulty:diff, query: isLesson ? null : msg});
    var txt = isLesson
      ? 'LESSON: ' + data.topic + '\n\n' + data.content + '\n\nSUMMARY:\n' + data.summary + '\n\nREAL WORLD EXAMPLE:\n' + data.real_example
      : data.content;
    learnMsgs.push({role:'ai', text:txt});
  } catch(e) {
    learnMsgs.push({role:'ai', text:'Error: ' + e.message});
  }
  drawMsgs();
  if (btn) btn.disabled = false;
}

// ── QUIZ ───────────────────────────────────────────────────────────────────────
var quizState = {q:null, sel:null, score:{c:0, t:0}};

function renderQuiz(c) {
  quizState = {q:null, sel:null, score:{c:0, t:0}};
  c.innerHTML = '<div class="card">'
    + '<div class="card-title">QUIZ AND ASSESSMENT ENGINE</div>'
    + '<div class="card-sub">LLM-generated questions targeting your weak areas.</div>'
    + '<div class="flex gap10 wrap mb16">'
    + '<select class="select" id="quiz-topic">' + topicOpts() + '</select>'
    + '<select class="select" id="quiz-type"><option value="mcq">MCQ</option><option value="short">Short Answer</option><option value="scenario">Scenario</option></select>'
    + '<button class="btn btn-primary" onclick="quizGen()">Generate Question</button>'
    + '</div>'
    + '<div class="score-row">'
    + '<div class="score-pill"><div class="score-label">SESSION SCORE</div><div class="score-val" id="quiz-score" style="color:var(--accent2)">0/0</div></div>'
    + '<div class="score-pill"><div class="score-label">ACCURACY</div><div class="score-val" id="quiz-acc">0%</div></div>'
    + '</div>'
    + '<div id="quiz-area"></div></div>';
}

async function quizGen() {
  quizState.q = null; quizState.sel = null;
  var area  = document.getElementById('quiz-area');
  var topic = document.getElementById('quiz-topic').value;
  var qtype = document.getElementById('quiz-type').value;
  area.innerHTML = spinner();
  try {
    var q = await api('POST', '/quiz/generate', {topic:topic, question_type:qtype, difficulty:USER.level});
    quizState.q = q;
    drawQuizQ(q);
  } catch(e) {
    area.innerHTML = '<div class="error-box">' + e.message + '</div>';
  }
}

function drawQuizQ(q) {
  var area = document.getElementById('quiz-area');
  var html = '';
  if (q.scenario) html += '<div class="scenario-badge">' + q.scenario + '</div>';
  html += '<div class="q-text">Q: ' + q.question + '</div>';
  if (q.options) {
    q.options.forEach(function(opt, i) {
      html += '<div class="opt" id="opt-' + i + '" onclick="quizSubmit(' + i + ')">'
            + '<span class="opt-letter">' + String.fromCharCode(65+i) + '</span>'
            + opt + '</div>';
    });
  }
  if (q.type === 'short') {
    html += '<textarea class="textarea mb8" id="short-ans" rows="3" placeholder="Type your answer..."></textarea>'
          + '<button class="btn btn-primary btn-sm" onclick="quizSubmitShort()">Submit</button>';
  }
  html += '<div id="quiz-fb"></div>';
  area.innerHTML = html;
}

async function quizSubmit(idx) {
  if (quizState.sel !== null) return;
  quizState.sel = idx;
  document.querySelectorAll('.opt').forEach(function(o){ o.classList.add('locked'); });
  var fbEl = document.getElementById('quiz-fb');
  fbEl.innerHTML = spinner();
  try {
    var data = await api('POST', '/quiz/submit', {question_id: quizState.q.question_id, student_answer: String(idx)});
    var ci = parseInt(data.correct_answer);
    if (!isNaN(ci)) {
      var cEl = document.getElementById('opt-' + ci);
      if (cEl) cEl.classList.add('correct');
    }
    if (!data.is_correct) {
      var wEl = document.getElementById('opt-' + idx);
      if (wEl) wEl.classList.add('wrong');
    }
    quizState.score.t++;
    if (data.is_correct) quizState.score.c++;
    document.getElementById('quiz-score').textContent = quizState.score.c + '/' + quizState.score.t;
    document.getElementById('quiz-acc').textContent   = Math.round(quizState.score.c / quizState.score.t * 100) + '%';
    var fb = '<div class="exp-box">' + (data.is_correct ? 'Correct! ' : 'Wrong! ') + data.explanation + '</div>';
    if (data.follow_up) fb += '<div class="follow-box">Follow-up: ' + data.follow_up + '</div>';
    fb += '<button class="btn btn-outline btn-sm mt14" onclick="quizGen()">Next Question</button>';
    fbEl.innerHTML = fb;
  } catch(e) {
    fbEl.innerHTML = '<div class="error-box">' + e.message + '</div>';
  }
}

async function quizSubmitShort() {
  var ans = document.getElementById('short-ans').value.trim();
  if (!ans) return;
  quizState.sel = ans;
  var fbEl = document.getElementById('quiz-fb');
  fbEl.innerHTML = spinner();
  try {
    var data = await api('POST', '/quiz/submit', {question_id: quizState.q.question_id, student_answer: ans});
    quizState.score.t++;
    if (data.is_correct) quizState.score.c++;
    document.getElementById('quiz-score').textContent = quizState.score.c + '/' + quizState.score.t;
    document.getElementById('quiz-acc').textContent   = Math.round(quizState.score.c / quizState.score.t * 100) + '%';
    var fb = '<div class="exp-box">' + (data.is_correct ? 'Correct! ' : 'Wrong! ') + data.explanation + '</div>';
    if (data.follow_up) fb += '<div class="follow-box">Follow-up: ' + data.follow_up + '</div>';
    fb += '<button class="btn btn-outline btn-sm mt14" onclick="quizGen()">Next Question</button>';
    fbEl.innerHTML = fb;
  } catch(e) {
    fbEl.innerHTML = '<div class="error-box">' + e.message + '</div>';
  }
}

// ── LAB ────────────────────────────────────────────────────────────────────────
var labState = {session:null, log:[], done:false, type:'pcr'};

function renderLab(c) {
  labState = {session:null, log:[], done:false, type:'pcr'};
  c.innerHTML = '<div class="card">'
    + '<div class="card-title">VIRTUAL LAB SIMULATOR</div>'
    + '<div class="card-sub">Decision-based experiments. AI responds to every choice.</div>'
    + '<div class="flex gap10 mb18" id="lab-type-row">'
    + '<button class="btn btn-primary btn-sm" onclick="setLab(\'pcr\',this)">PCR</button>'
    + '<button class="btn btn-outline btn-sm" onclick="setLab(\'gel_electrophoresis\',this)">Gel Electrophoresis</button>'
    + '<button class="btn btn-outline btn-sm" onclick="setLab(\'dna_extraction\',this)">DNA Extraction</button>'
    + '</div>'
    + '<button class="btn btn-green mb18" onclick="labStart()">Start Experiment</button>'
    + '<div id="lab-area"></div>'
    + '<div id="lab-log-wrap"></div>'
    + '</div>';
}

function setLab(type, btn) {
  labState.type = type;
  document.querySelectorAll('#lab-type-row .btn').forEach(function(b){
    b.className = 'btn btn-outline btn-sm';
  });
  btn.className = 'btn btn-primary btn-sm';
}

async function labStart() {
  var prevType = labState.type;
  labState = {session:null, log:[], done:false, type: prevType};
  var area = document.getElementById('lab-area');
  area.innerHTML = spinner();
  document.getElementById('lab-log-wrap').innerHTML = '';
  try {
    var data = await api('POST', '/lab/start', {lab_type: labState.type});
    labState.session = data;
    drawLabStep(data);
  } catch(e) {
    area.innerHTML = '<div class="error-box">' + e.message + '</div>';
  }
}

function drawLabStep(step) {
  var area = document.getElementById('lab-area');
  var html = '<div class="lab-scene">' + step.scenario + '</div>';
  html += '<div style="font-size:11px;color:var(--muted);margin-bottom:10px">CHOOSE YOUR NEXT ACTION:</div>';
  step.choices.forEach(function(ch, i) {
    html += '<div class="lab-opt" onclick="labDecide(this)">'
          + '<span style="color:var(--accent3);font-weight:700;min-width:18px">' + String.fromCharCode(65+i) + '.</span>'
          + '<span class="lab-choice-text">' + ch + '</span></div>';
  });
  area.innerHTML = html;
}

async function labDecide(el) {
  var choice = el.querySelector('.lab-choice-text').textContent;
  labState.log.push('You chose: ' + choice);
  var area = document.getElementById('lab-area');
  area.innerHTML = spinner();
  try {
    var data = await api('POST', '/lab/decide', {session_id: labState.session.session_id, choice: choice});
    labState.log.push(data.result + (data.error ? ' | Mistake: ' + data.error : ''));
    if (data.completed) {
      labState.done = true;
      labState.log.push('Complete! Score: ' + (data.score != null ? data.score : 'N/A'));
      area.innerHTML = '<div class="success-box">Lab simulation complete!</div>';
    } else if (data.next_step) {
      labState.session = data.next_step;
      drawLabStep(data.next_step);
    } else {
      area.innerHTML = '';
    }
    drawLabLog();
  } catch(e) {
    area.innerHTML = '<div class="error-box">' + e.message + '</div>';
  }
}

function drawLabLog() {
  var wrap = document.getElementById('lab-log-wrap');
  if (!labState.log.length) return;
  wrap.innerHTML = '<div class="lab-log"><div style="color:var(--accent);font-size:10px;margin-bottom:8px">LAB LOG</div>'
    + labState.log.map(function(l){ return '<div style="margin-bottom:4px">' + l + '</div>'; }).join('')
    + '</div>';
  var logEl = wrap.querySelector('.lab-log');
  if (logEl) logEl.scrollTop = 9999;
}

// ── CAREER ─────────────────────────────────────────────────────────────────────
function renderCareer(c) {
  var roleOpts = ROLES.map(function(r){ return '<option value="' + r.v + '">' + r.l + '</option>'; }).join('');
  c.innerHTML = '<div class="card">'
    + '<div class="card-title">CAREER MENTOR AND SKILL GAP ANALYSIS</div>'
    + '<div class="card-sub">Compare your skills with industry requirements and get a roadmap.</div>'
    + '<div class="flex gap10 mb18">'
    + '<select class="select flex1" id="career-role">' + roleOpts + '</select>'
    + '<button class="btn btn-primary" onclick="careerAnalyze()">Analyze</button>'
    + '</div>'
    + '<div id="career-area"></div></div>';
}

async function careerAnalyze() {
  var role = document.getElementById('career-role').value;
  var area = document.getElementById('career-area');
  area.innerHTML = spinner();
  try {
    var res = await api('POST', '/career/analyze', {target_role: role});
    var sc  = res.readiness_score;
    var col = sc >= 70 ? 'var(--accent2)' : sc >= 40 ? 'var(--accent3)' : 'var(--danger)';
    var html = '<div class="flex gap10 wrap mb18">';
    html += '<div class="readiness-wrap"><div class="readiness-num" style="color:' + col + '">' + sc.toFixed(0) + '%</div><div class="readiness-lbl">INDUSTRY READINESS</div></div>';
    html += '<div class="flex1"><div style="font-size:11px;color:var(--muted);margin-bottom:10px">TOP SKILL GAPS</div>';
    res.skill_gaps.slice(0,5).forEach(function(g) {
      html += '<div class="barchart"><div class="bar-label"><span>' + g.skill + '</span><span style="color:var(--danger)">' + g.gap.toFixed(0) + ' pts gap</span></div>'
            + '<div class="bar-bg"><div class="bar-fill" style="width:' + g.student_score + '%;background:var(--accent3)"></div></div></div>';
    });
    html += '</div></div><div class="divider"></div>';
    html += '<div style="font-size:12px;color:var(--accent);font-weight:700;margin-bottom:14px">CAREER ROADMAP</div>';
    res.roadmap.forEach(function(step, i) {
      html += '<div class="road-step"><div class="road-dot"></div><div><div class="road-num">STEP ' + (i+1) + '</div><div class="road-text">' + step + '</div></div></div>';
    });
    html += '<div class="divider"></div><div class="flex gap10 wrap">';
    html += '<div class="flex1"><div style="font-size:11px;color:var(--accent);margin-bottom:10px">MINI-PROJECTS</div>'
          + res.mini_projects.map(function(p){ return '<div style="font-size:13px;margin-bottom:8px;padding-left:10px;border-left:2px solid var(--accent3);line-height:1.6">' + p + '</div>'; }).join('') + '</div>';
    html += '<div class="flex1"><div style="font-size:11px;color:var(--accent);margin-bottom:10px">CERTIFICATIONS</div>'
          + res.certifications.map(function(c){ return '<div style="font-size:13px;margin-bottom:8px;padding-left:10px;border-left:2px solid var(--accent2);line-height:1.6">' + c + '</div>'; }).join('') + '</div>';
    html += '</div>';
    area.innerHTML = html;
  } catch(e) {
    area.innerHTML = '<div class="error-box">' + e.message + '</div>';
  }
}

// ── ANALYTICS ──────────────────────────────────────────────────────────────────
function renderAnalytics(c) {
  c.innerHTML = '<div class="card">'
    + '<div class="card-title">PERFORMANCE ANALYTICS</div>'
    + '<div class="card-sub">Real-time tracking of accuracy, XP, and topic mastery.</div>'
    + '<div id="analytics-area">' + spinner() + '</div>'
    + '<button class="btn btn-outline btn-sm mt16" onclick="loadAnalytics()">Refresh</button>'
    + '</div>'
    + '<div class="card">'
    + '<div class="card-title">PERSONALIZED LEARNING PATH</div>'
    + '<div class="card-sub">AI generates your 6-week study roadmap.</div>'
    + '<button class="btn btn-primary" onclick="loadPath()">Generate My 6-Week Path</button>'
    + '<div id="path-area"></div></div>';
  loadAnalytics();
}

async function loadAnalytics() {
  var area = document.getElementById('analytics-area');
  if (!area) return;
  area.innerHTML = spinner();
  try {
    var data = await api('GET', '/analytics/dashboard');
    var html = '<div class="stat-grid">'
      + '<div class="stat-card"><div class="stat-num">' + data.total_xp + '</div><div class="stat-lbl">TOTAL XP</div></div>'
      + '<div class="stat-card"><div class="stat-num">' + Math.round(data.overall_accuracy*100) + '%</div><div class="stat-lbl">ACCURACY</div></div>'
      + '<div class="stat-card"><div class="stat-num">' + Math.round(data.industry_readiness) + '%</div><div class="stat-lbl">READINESS</div></div>'
      + '<div class="stat-card"><div class="stat-num" style="font-size:18px">' + USER.level.toUpperCase() + '</div><div class="stat-lbl">LEVEL</div></div>'
      + '</div>';
    if (data.topic_breakdown.length) {
      html += '<div style="font-size:11px;color:var(--accent);margin-bottom:14px">TOPIC ACCURACY</div>';
      data.topic_breakdown.forEach(function(t, i) {
        var col = t.accuracy >= 0.7 ? 'var(--accent2)' : 'var(--danger)';
        html += '<div class="barchart"><div class="bar-label"><span>' + t.topic + '</span><span style="color:' + col + ';font-weight:600">' + Math.round(t.accuracy*100) + '%</span></div>'
              + '<div class="bar-bg"><div class="bar-fill" style="width:' + (t.accuracy*100) + '%;background:' + COLORS[i%COLORS.length] + '"></div></div></div>';
      });
    } else {
      html += '<div style="color:var(--muted);font-size:13px;padding:10px 0">Complete quizzes to see analytics!</div>';
    }
    if (data.weak_topics.length) {
      html += '<div class="divider"></div><div style="font-size:11px;color:var(--danger);margin-bottom:10px">WEAK AREAS</div><div style="margin-bottom:14px">';
      data.weak_topics.forEach(function(t){ html += '<span class="skill-chip chip-bad">' + t + '</span>'; });
      html += '</div>';
      data.improvement_tips.forEach(function(tip){ html += '<div style="font-size:13px;margin-bottom:10px;padding-left:12px;border-left:2px solid var(--accent);line-height:1.7">' + tip + '</div>'; });
    }
    if (data.strong_topics.length) {
      html += '<div class="divider"></div><div style="font-size:11px;color:var(--accent2);margin-bottom:10px">STRONG AREAS</div>';
      data.strong_topics.forEach(function(t){ html += '<span class="skill-chip chip-good">' + t + '</span>'; });
    }
    area.innerHTML = html;
  } catch(e) {
    area.innerHTML = '<div class="error-box">' + e.message + '</div>';
  }
}

async function loadPath() {
  var area = document.getElementById('path-area');
  if (!area) return;
  area.innerHTML = '<div style="margin-top:14px">' + spinner() + '</div>';
  try {
    var data = await api('GET', '/analytics/learning-path');
    if (!data.path || !data.path.weeks) { area.innerHTML = ''; return; }
    var html = '<div style="margin-top:18px">';
    data.path.weeks.forEach(function(w, i) {
      var col = 'hsl(' + (180+i*45) + ',100%,55%)';
      html += '<div class="flex gap10 mb18"><div style="width:4px;background:' + col + ';border-radius:2px;flex-shrink:0"></div><div>';
      html += '<div style="font-size:10px;color:var(--muted);margin-bottom:3px">' + w.week + '</div>';
      html += '<div style="font-size:13px;font-weight:700;margin-bottom:10px">' + w.focus + '</div>';
      if (w.topics) w.topics.forEach(function(t){
        html += '<span style="padding:4px 9px;border-radius:6px;font-size:11px;background:var(--surface2);border:1px solid var(--border);color:var(--muted);margin:2px;display:inline-block">' + t + '</span>';
      });
      html += '</div></div>';
    });
    if (data.path.milestone) {
      html += '<div class="flex gap10" style="align-items:center;padding:14px;background:rgba(0,255,153,0.05);border-radius:10px;border:1px solid rgba(0,255,153,0.2);margin-top:8px">'
            + '<div><div style="font-size:10px;color:var(--muted)">FINAL MILESTONE</div>'
            + '<div style="color:var(--accent2);font-weight:600;font-size:14px;margin-top:3px">' + data.path.milestone + '</div></div></div>';
    }
    html += '</div>';
    area.innerHTML = html;
  } catch(e) {
    area.innerHTML = '<div class="error-box" style="margin-top:14px">' + e.message + '</div>';
  }
}

// ── INIT ───────────────────────────────────────────────────────────────────────
if (TOKEN && USER) { showApp(); }
</script>
</body>
</html>"""

# ── DATABASE ───────────────────────────────────────────────────────────────────
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# ── ENUMS ──────────────────────────────────────────────────────────────────────
class DifficultyLevel(str, Enum):
    beginner="beginner"; intermediate="intermediate"; advanced="advanced"

class BiotechRole(str, Enum):
    researcher="researcher"; lab_technician="lab_technician"; bioinformatician="bioinformatician"
    bioprocess_engineer="bioprocess_engineer"; clinical_associate="clinical_associate"; regulatory_affairs="regulatory_affairs"

class LabType(str, Enum):
    pcr="pcr"; gel_electrophoresis="gel_electrophoresis"; dna_extraction="dna_extraction"

class QuestionType(str, Enum):
    mcq="mcq"; short="short"; scenario="scenario"

# ── MODELS ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id=Column(Integer,primary_key=True,index=True); name=Column(String(100),nullable=False)
    email=Column(String(150),unique=True,index=True,nullable=False); hashed_pw=Column(String(255),nullable=False)
    institution=Column(String(200)); level=Column(SAEnum(DifficultyLevel),default=DifficultyLevel.beginner)
    xp_points=Column(Integer,default=0); created_at=Column(DateTime,default=datetime.utcnow); is_active=Column(Boolean,default=True)
    topic_masteries=relationship("TopicMastery",back_populates="user",cascade="all, delete")
    quiz_results=relationship("QuizResult",back_populates="user",cascade="all, delete")
    lab_logs=relationship("LabLog",back_populates="user",cascade="all, delete")
    career_goal=relationship("CareerGoal",back_populates="user",uselist=False,cascade="all, delete")
    skill_scores=relationship("SkillScore",back_populates="user",cascade="all, delete")

class TopicMastery(Base):
    __tablename__="topic_mastery"
    id=Column(Integer,primary_key=True,index=True); user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    topic_name=Column(String(150),nullable=False); attempts=Column(Integer,default=0); correct=Column(Integer,default=0)
    accuracy=Column(Float,default=0.0); current_level=Column(SAEnum(DifficultyLevel),default=DifficultyLevel.beginner)
    user=relationship("User",back_populates="topic_masteries")

class QuizResult(Base):
    __tablename__="quiz_results"
    id=Column(Integer,primary_key=True,index=True); user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    topic=Column(String(150),nullable=False); question_type=Column(String(20)); question_data=Column(JSON)
    student_answer=Column(Text); correct_answer=Column(Text); is_correct=Column(Boolean)
    score=Column(Float,default=0.0); llm_explanation=Column(Text); attempted_at=Column(DateTime,default=datetime.utcnow)
    user=relationship("User",back_populates="quiz_results")

class LabLog(Base):
    __tablename__="lab_logs"
    id=Column(Integer,primary_key=True,index=True); user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    lab_type=Column(String(100)); session_id=Column(String(36)); decision_chain=Column(JSON)
    outcome=Column(String(50)); score=Column(Float,default=0.0); error_count=Column(Integer,default=0)
    started_at=Column(DateTime,default=datetime.utcnow); completed_at=Column(DateTime,nullable=True)
    user=relationship("User",back_populates="lab_logs")

class CareerGoal(Base):
    __tablename__="career_goals"
    id=Column(Integer,primary_key=True,index=True); user_id=Column(Integer,ForeignKey("users.id"),unique=True,nullable=False)
    target_role=Column(SAEnum(BiotechRole),nullable=False); industry_skills=Column(JSON); roadmap=Column(JSON)
    mini_projects=Column(JSON); certifications=Column(JSON); readiness_score=Column(Float,default=0.0)
    generated_at=Column(DateTime,default=datetime.utcnow)
    user=relationship("User",back_populates="career_goal")

class SkillScore(Base):
    __tablename__="skill_scores"
    id=Column(Integer,primary_key=True,index=True); user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    skill_name=Column(String(150),nullable=False); score=Column(Float,default=0.0); source=Column(String(50))
    updated_at=Column(DateTime,default=datetime.utcnow)
    user=relationship("User",back_populates="skill_scores")

# ── SCHEMAS ────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    name:str; email:EmailStr; password:str; institution:Optional[str]=None; level:DifficultyLevel=DifficultyLevel.beginner

class TokenResponse(BaseModel):
    access_token:str; token_type:str="bearer"

class UserResponse(BaseModel):
    id:int; name:str; email:str; institution:Optional[str]=None; level:str; xp_points:int
    model_config={"from_attributes":True}

class LessonRequest(BaseModel):
    topic:str; difficulty:Optional[DifficultyLevel]=None; query:Optional[str]=None

class LessonResponse(BaseModel):
    topic:str; difficulty:str; content:str; summary:str; real_example:str

class QuizRequest(BaseModel):
    topic:str; question_type:QuestionType=QuestionType.mcq; difficulty:Optional[DifficultyLevel]=None

class QuizQuestion(BaseModel):
    question_id:int; topic:str; type:str; question:str; options:Optional[List[str]]=None; scenario:Optional[str]=None

class QuizSubmit(BaseModel):
    question_id:int; student_answer:str

class QuizFeedback(BaseModel):
    is_correct:bool; correct_answer:str; explanation:str; score_earned:float; follow_up:Optional[str]=None

class LabStartRequest(BaseModel):
    lab_type:LabType

class LabStepResponse(BaseModel):
    session_id:str; step:int; scenario:str; choices:List[str]; is_final:bool=False

class LabDecisionRequest(BaseModel):
    session_id:str; choice:str

class LabDecisionResponse(BaseModel):
    result:str; error:Optional[str]=None; next_step:Optional[LabStepResponse]=None; completed:bool=False; score:Optional[float]=None

class TopicAccuracy(BaseModel):
    topic:str; attempts:int; accuracy:float; level:str

class AnalyticsResponse(BaseModel):
    user_id:int; total_xp:int; overall_accuracy:float; topic_breakdown:List[TopicAccuracy]
    weak_topics:List[str]; strong_topics:List[str]; improvement_tips:List[str]; industry_readiness:float

class CareerRequest(BaseModel):
    target_role:BiotechRole

class SkillGap(BaseModel):
    skill:str; student_score:float; required_score:float; gap:float

class CareerResponse(BaseModel):
    target_role:str; readiness_score:float; skill_gaps:List[SkillGap]; roadmap:List[str]; mini_projects:List[str]; certifications:List[str]

# ── SECURITY ───────────────────────────────────────────────────────────────────
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(p): return pwd_context.hash(p)
def verify_password(p,h): return pwd_context.verify(p,h)

def create_access_token(data):
    to_encode=data.copy(); to_encode["exp"]=datetime.utcnow()+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINS)
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    exc=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid credentials")
    try: payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM]); user_id=int(payload.get("sub"))
    except: raise exc
    user=db.query(User).filter(User.id==user_id).first()
    if not user: raise exc
    return user

# ── GROQ LLM ───────────────────────────────────────────────────────────────────
llm_client = Groq(api_key=GROQ_API_KEY)

def _llm(system, message, max_tokens=1024):
    r = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role":"system","content":system},{"role":"user","content":message}],
        max_tokens=max_tokens, temperature=0.7
    )
    return r.choices[0].message.content

def _llm_json(system, message):
    try:
        raw = _llm(system, message)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        # Find JSON object in response
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            cleaned = cleaned[start:end]
        return json.loads(cleaned)
    except Exception as e:
        print(f"[LLM error] {e}")
        return {}

def llm_lesson(topic, difficulty, name, weak):
    return _llm_json(
        f"You are an expert biotechnology educator. Student: {name} | Level: {difficulty.upper()}\n"
        f"Weak areas: {', '.join(weak) or 'none'}\n"
        'Output ONLY valid JSON: {"content":"lesson text","summary":"3 bullet points","real_example":"1 example"}',
        f"Teach me about: {topic}")

def llm_quiz(topic, difficulty, qtype, wrongs):
    fmts={"mcq":'{"type":"mcq","question":"...","options":["A","B","C","D"],"answer_index":0,"explanation":"..."}',
          "short":'{"type":"short","question":"...","sample_answer":"...","key_points":["..."]}',
          "scenario":'{"type":"scenario","scenario":"...","question":"...","options":["A","B","C","D"],"answer_index":0,"explanation":"..."}'}
    return _llm_json(
        f"You are a biotechnology assessment specialist. Difficulty: {difficulty.upper()} | Topic: {topic}\n"
        f"Recent mistakes: {', '.join(wrongs) or 'none'}\nanswer_index MUST be integer 0-3.\n"
        f"Output ONLY valid JSON: {fmts[qtype]}",
        f"Generate {qtype} question for: {topic}")

def llm_explain(question, correct, student, topic):
    return _llm("You are a biotech tutor. Explain why the student answer is wrong in 2-3 sentences. Be kind.",
                f"Topic:{topic}\nQuestion:{question}\nCorrect:{correct}\nStudent:{student}", max_tokens=250)

def llm_followup(topic, concept):
    return _llm("Generate ONE short follow-up question to reinforce the concept.",
                f"Topic:{topic}. Concept:{concept}", max_tokens=120)

def llm_start_lab(lab_type, level):
    return _llm_json(
        f"You are a virtual lab instructor for {lab_type}. Level: {level.upper()}\n"
        'Output ONLY valid JSON: {"scenario":"lab scene","choices":["A","B","C","D"]}',
        f"Start {lab_type} simulation")

def llm_lab_decision(lab_type, level, choice, step, history):
    chain = " -> ".join([f"Step {d['step']}: {d['choice']}" for d in history])
    return _llm_json(
        f"Lab:{lab_type} Level:{level.upper()} Step:{step} History:{chain}\n"
        'Output ONLY valid JSON: {"result":"what happened","error":null,"scenario":"next situation","choices":["A","B","C","D"],"is_final":false}\n'
        "Set is_final=true when done.",
        f"Student chose: {choice}")

def llm_career(name, role, skills, topics):
    return _llm_json(
        f"Biotech career advisor. Student:{name} | Role:{role}\nSkills:{json.dumps(skills)} | Topics:{json.dumps(topics)}\n"
        'Output ONLY valid JSON: {"industry_required_skills":{"skill":0},"roadmap":["step1","step2","step3","step4","step5"],"mini_projects":["p1","p2","p3"],"certifications":["c1","c2"],"readiness_score":65.0}',
        f"Generate career roadmap for {role}")

def llm_tips(weak, level):
    raw = _llm_json('Generate 3-4 improvement tips. Output ONLY JSON array: ["tip1","tip2","tip3"]',
                    f"Weak:{', '.join(weak)}. Level:{level}")
    if isinstance(raw, list): return raw
    if isinstance(raw, dict):
        for v in raw.values():
            if isinstance(v, list): return v
    return []

def llm_path(level, role, weak, strong):
    return _llm_json(
        f"Biotech curriculum designer. Level:{level} Role:{role} Weak:{weak} Strong:{strong}\n"
        'Output ONLY valid JSON: {"weeks":[{"week":"Week 1-2","focus":"theme","topics":["t1","t2","t3"],"priority":"high"}],"milestone":"goal"}',
        "Generate 6-week learning path")

# ── ANALYTICS ──────────────────────────────────────────────────────────────────
def get_breakdown(db,uid): return [{"topic":m.topic_name,"attempts":m.attempts,"accuracy":round(m.accuracy,3),"level":m.current_level.value} for m in db.query(TopicMastery).filter(TopicMastery.user_id==uid,TopicMastery.attempts>0).all()]
def weak_topics(db,uid):   return [m.topic_name for m in db.query(TopicMastery).filter(TopicMastery.user_id==uid,TopicMastery.attempts>0,TopicMastery.accuracy<WEAK_THRESHOLD).all()]
def strong_topics(db,uid): return [m.topic_name for m in db.query(TopicMastery).filter(TopicMastery.user_id==uid,TopicMastery.accuracy>=STRONG_THRESHOLD).all()]
def overall_acc(db,uid):
    r=db.query(func.sum(func.cast(QuizResult.is_correct,Integer)).label("c"),func.count(QuizResult.id).label("t")).filter(QuizResult.user_id==uid).first()
    return round((r.c or 0)/r.t,3) if r and r.t else 0.0


def readiness(db,uid,role):
    bm=INDUSTRY_BENCHMARKS.get(role,{})
    scores={s.skill_name:s.score for s in db.query(SkillScore).filter(SkillScore.user_id==uid).all()}
    topic_acc={m.topic_name:m.accuracy*100 for m in db.query(TopicMastery).filter(TopicMastery.user_id==uid).all()}
    ratios=[min(scores.get(sk,topic_acc.get(sk,0))/req,1.0) for sk,req in bm.items()]
    return round((sum(ratios)/len(ratios))*100,1) if ratios else 0.0

def skill_gaps(db,uid,role):
    bm=INDUSTRY_BENCHMARKS.get(role,{})
    scores={s.skill_name:s.score for s in db.query(SkillScore).filter(SkillScore.user_id==uid).all()}
    topic_acc={m.topic_name:m.accuracy*100 for m in db.query(TopicMastery).filter(TopicMastery.user_id==uid).all()}
    return sorted([{"skill":sk,"student_score":scores.get(sk,topic_acc.get(sk,0)),"required_score":req,"gap":max(0,req-scores.get(sk,topic_acc.get(sk,0)))} for sk,req in bm.items()],key=lambda x:x["gap"],reverse=True)

def update_mastery(db,uid,topic,correct):
    m=db.query(TopicMastery).filter(TopicMastery.user_id==uid,TopicMastery.topic_name==topic).first()
    if not m: m=TopicMastery(user_id=uid,topic_name=topic,attempts=0,correct=0); db.add(m)
    m.attempts+=1
    if correct: m.correct+=1
    m.accuracy=m.correct/m.attempts
    if m.accuracy>=0.80 and m.attempts>=5:
        if m.current_level==DifficultyLevel.beginner: m.current_level=DifficultyLevel.intermediate
        elif m.current_level==DifficultyLevel.intermediate: m.current_level=DifficultyLevel.advanced
    elif m.accuracy<0.40 and m.attempts>=3:
        if m.current_level==DifficultyLevel.advanced: m.current_level=DifficultyLevel.intermediate
        elif m.current_level==DifficultyLevel.intermediate: m.current_level=DifficultyLevel.beginner
    db.commit()

def add_xp(db,user,pts):
    user.xp_points+=pts
    if user.xp_points>=600: user.level=DifficultyLevel.advanced
    elif user.xp_points>=200: user.level=DifficultyLevel.intermediate
    db.commit()

# ── SESSION STORES ─────────────────────────────────────────────────────────────
_pending:dict={}
_labs:dict={}

# ── FASTAPI APP ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app:FastAPI):
    Base.metadata.create_all(bind=engine); yield

app=FastAPI(title="BioMind AI",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

@app.get("/",response_class=HTMLResponse)
def serve_frontend(): return HTMLResponse(content=FRONTEND_HTML)

@app.post("/auth/register",response_model=UserResponse,status_code=201)
def register(p:UserRegister,db:Session=Depends(get_db)):
    if db.query(User).filter(User.email==p.email).first(): raise HTTPException(400,"Email already registered")
    u=User(name=p.name,email=p.email,hashed_pw=hash_password(p.password),institution=p.institution,level=p.level)
    db.add(u); db.commit(); db.refresh(u); return u

@app.post("/auth/login",response_model=TokenResponse)
def login(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==form.username).first()
    if not u or not verify_password(form.password,u.hashed_pw): raise HTTPException(401,"Invalid credentials")
    return {"access_token":create_access_token({"sub":str(u.id)}),"token_type":"bearer"}

@app.get("/auth/me",response_model=UserResponse)
def me(u:User=Depends(get_current_user)): return u

@app.post("/learn/generate-lesson",response_model=LessonResponse)
def generate_lesson(p:LessonRequest,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    diff=p.difficulty.value if p.difficulty else u.level.value
    data=llm_lesson(p.topic,diff,u.name,weak_topics(db,u.id))
    add_xp(db,u,10)
    return LessonResponse(topic=p.topic,difficulty=diff,content=data.get("content",""),summary=data.get("summary",""),real_example=data.get("real_example",""))

@app.post("/quiz/generate",response_model=QuizQuestion)
def generate_quiz(p:QuizRequest,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    qid=next(_qid_counter); diff=p.difficulty.value if p.difficulty else u.level.value
    wrongs=[r.correct_answer for r in db.query(QuizResult).filter(QuizResult.user_id==u.id,QuizResult.topic==p.topic,QuizResult.is_correct==False).order_by(QuizResult.attempted_at.desc()).limit(3).all()]
    data=llm_quiz(p.topic,diff,p.question_type.value,wrongs)
    _pending[qid]={"topic":p.topic,"type":p.question_type.value,"data":data}
    return QuizQuestion(question_id=qid,topic=p.topic,type=p.question_type.value,question=data.get("question",""),options=data.get("options"),scenario=data.get("scenario"))

@app.post("/quiz/submit",response_model=QuizFeedback)
def submit_quiz(p:QuizSubmit,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    pending=_pending.pop(p.question_id,None)
    if not pending: raise HTTPException(404,"Question not found")
    q=pending["data"]; topic=pending["topic"]
    raw=q.get("answer_index",q.get("sample_answer",""))
    if isinstance(raw,str) and len(raw)==1 and raw.isalpha(): raw=str(ord(raw.upper())-ord("A"))
    correct=str(raw).strip(); student=p.student_answer.strip()
    is_correct=student.lower()==correct.lower()
    explanation=q.get("explanation",""); follow_up=None
    if not is_correct:
        explanation=llm_explain(q.get("question",""),correct,student,topic)
        follow_up=llm_followup(topic,q.get("question",""))
    r=QuizResult(user_id=u.id,topic=topic,question_type=pending["type"],question_data=q,student_answer=student,correct_answer=correct,is_correct=is_correct,score=1.0 if is_correct else 0.0,llm_explanation=explanation)
    db.add(r); db.commit()
    update_mastery(db,u.id,topic,is_correct)
    add_xp(db,u,25 if is_correct else 5)
    return QuizFeedback(is_correct=is_correct,correct_answer=correct,explanation=explanation,score_earned=1.0 if is_correct else 0.0,follow_up=follow_up)

@app.post("/lab/start",response_model=LabStepResponse)
def start_lab(p:LabStartRequest,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    sid=str(uuid.uuid4()); data=llm_start_lab(p.lab_type.value,u.level.value)
    _labs[sid]={"lab_type":p.lab_type.value,"user_id":u.id,"step":1,"decision_chain":[],"error_count":0}
    log=LabLog(user_id=u.id,lab_type=p.lab_type.value,session_id=sid,decision_chain=[],outcome="incomplete",error_count=0)
    db.add(log); db.commit()
    return LabStepResponse(session_id=sid,step=1,scenario=data.get("scenario",""),choices=data.get("choices",[]))

@app.post("/lab/decide",response_model=LabDecisionResponse)
def lab_decide(p:LabDecisionRequest,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    s=_labs.get(p.session_id)
    if not s: raise HTTPException(404,"Lab session not found")
    data=llm_lab_decision(s["lab_type"],u.level.value,p.choice,s["step"],s["decision_chain"])
    if data.get("error"): s["error_count"]+=1
    s["decision_chain"].append({"step":s["step"],"choice":p.choice,"result":data.get("result"),"error":data.get("error")})
    s["step"]+=1; is_final=data.get("is_final",False)
    log=db.query(LabLog).filter(LabLog.session_id==p.session_id).first(); score_val=None
    if log:
        log.decision_chain=s["decision_chain"]; log.error_count=s["error_count"]
        if is_final:
            log.outcome="success" if s["error_count"]==0 else "partial"
            log.score=max(0.0,100.0-(s["error_count"]*15)); log.completed_at=datetime.utcnow(); score_val=log.score
        db.commit()
    if is_final: add_xp(db,u,50 if s["error_count"]==0 else 20); del _labs[p.session_id]
    next_step=None
    if not is_final and data.get("scenario"):
        next_step=LabStepResponse(session_id=p.session_id,step=s["step"],scenario=data["scenario"],choices=data.get("choices",[]))
    return LabDecisionResponse(result=data.get("result",""),error=data.get("error"),next_step=next_step,completed=is_final,score=score_val)

@app.get("/analytics/dashboard",response_model=AnalyticsResponse)
def dashboard(db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    breakdown = get_breakdown(db, u.id)
    weak = weak_topics(db, u.id)
    strong = strong_topics(db, u.id)
    role = u.career_goal.target_role.value if u.career_goal else "researcher"
    try:
        tips = llm_tips(weak, u.level.value) if weak else []
    except:
        tips = []
    return AnalyticsResponse(
        user_id=u.id,
        total_xp=u.xp_points,
        overall_accuracy=overall_acc(db, u.id),
        topic_breakdown=breakdown,
        weak_topics=weak,
        strong_topics=strong,
        improvement_tips=tips,
        industry_readiness=readiness(db, u.id, role)
    )
@app.get("/analytics/learning-path")
def learning_path(db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    role=u.career_goal.target_role.value if u.career_goal else "researcher"
    return {"student":u.name,"level":u.level.value,"path":llm_path(u.level.value,role,weak_topics(db,u.id),strong_topics(db,u.id))}

@app.post("/career/analyze",response_model=CareerResponse)
def career_analyze(p:CareerRequest,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    role=p.target_role.value; gaps=skill_gaps(db,u.id,role); ready=readiness(db,u.id,role)
    topic_acc={t["topic"]:t["accuracy"] for t in get_breakdown(db,u.id)}
    skill_data={s.skill_name:s.score for s in db.query(SkillScore).filter(SkillScore.user_id==u.id).all()}
    rd=llm_career(u.name,role,skill_data,topic_acc)
    goal=db.query(CareerGoal).filter(CareerGoal.user_id==u.id).first()
    if not goal: goal=CareerGoal(user_id=u.id,target_role=p.target_role); db.add(goal)
    goal.target_role=p.target_role; goal.industry_skills=rd.get("industry_required_skills",{})
    goal.roadmap=rd.get("roadmap",[]); goal.mini_projects=rd.get("mini_projects",[])
    goal.certifications=rd.get("certifications",[]); goal.readiness_score=ready; db.commit()
    return CareerResponse(target_role=role,readiness_score=ready,skill_gaps=[SkillGap(**g) for g in gaps],roadmap=goal.roadmap,mini_projects=goal.mini_projects,certifications=goal.certifications)

# ── RUN ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("BioMind AI Platform Starting...")
    print("Open browser: http://localhost:5000")
    print("=" * 50)
    uvicorn.run("biotechpro1:app", host="0.0.0.0", port=5000, reload=True)