import os, re, hmac, hashlib, secrets, sqlite3, smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
import streamlit as st

APP_NAME = "DERSON Aviator Lab"
DB_PATH = os.getenv("DERSON_DB_PATH", "derson_aviator_lab.db")
OTP_MINUTES = int(os.getenv("OTP_MINUTES", "10"))
ACTIVATION_MINUTES = int(os.getenv("ACTIVATION_MINUTES", "30"))
st.set_page_config(page_title=APP_NAME, page_icon="🚀", layout="centered")

st.markdown("""
<style>
.stApp {background:linear-gradient(150deg,#08131e,#101d2a 55%,#071018);color:#f4f7fb}
[data-testid="stSidebar"] {background:#0b1520}
.hero {padding:1.2rem 1.35rem;border:1px solid #263b4c;border-radius:20px;background:linear-gradient(135deg,#142b3d,#101720);margin-bottom:1rem}
.hero h1 {margin:0;color:#f4f7fb;font-size:2rem}
.hero p {margin:.45rem 0 0;color:#aebdca}
.flight-panel {position:relative;overflow:hidden;border:1px solid #28465a;border-radius:18px;padding:1.2rem;background:radial-gradient(circle at 80% 10%,#193b51,#0b1723 65%);min-height:145px;margin:.8rem 0}
.flight-track {height:2px;width:140%;background:linear-gradient(90deg,transparent,#28d7ff,#f7b84b,transparent);position:absolute;left:-20%;top:68%;animation:trackmove 3s linear infinite;opacity:.9}
.plane {position:absolute;top:38%;left:8%;font-size:2rem;animation:fly 4s ease-in-out infinite}
.multiplier {font-size:2.3rem;font-weight:800;color:#35e0b2;letter-spacing:.03em}
@keyframes fly {0%{transform:translate(0,15px) rotate(-8deg)}50%{transform:translate(180px,-12px) rotate(-2deg)}100%{transform:translate(350px,-30px) rotate(5deg)}}
@keyframes trackmove {0%{transform:translateX(-8%)}100%{transform:translateX(8%)}}
@media (prefers-reduced-motion: reduce) {.plane,.flight-track{animation:none}}
</style>
""", unsafe_allow_html=True)

def now():
    return datetime.now(timezone.utc)

def db():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS users (
      email TEXT PRIMARY KEY, otp_hash TEXT, otp_expires TEXT,
      email_verified INTEGER DEFAULT 0, activation_hash TEXT,
      activation_expires TEXT, status TEXT DEFAULT 'email_pending',
      created_at TEXT, approved_at TEXT)""")
    c.commit()
    return c

def secret(k, default=""):
    try: return st.secrets.get(k, os.getenv(k, default))
    except Exception: return os.getenv(k, default)

def hash_code(code):
    return hashlib.sha256((secret("CODE_HASH_SALT", "change-this-in-secrets") + code).encode()).hexdigest()

def valid_email(e):
    return bool(re.fullmatch(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+", e.strip()))

def send_email(to, subject, body):
    sender = secret("SMTP_EMAIL")
    password = secret("SMTP_APP_PASSWORD")
    if not sender or not password:
        return False, "E-mail non configuré. Ajoutez SMTP_EMAIL et SMTP_APP_PASSWORD dans les secrets."
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, sender, to
    msg.set_content(body)
    try:
        with smtplib.SMTP(secret("SMTP_HOST", "smtp.gmail.com"), int(secret("SMTP_PORT", "587")), timeout=20) as s:
            s.starttls()
            s.login(sender, password)
            s.send_message(msg)
        return True, "E-mail envoyé."
    except Exception as ex:
        return False, f"Échec d'envoi e-mail : {ex}"

def issue_otp(email):
    code = f"{secrets.randbelow(1000000):06d}"
    expiry = now() + timedelta(minutes=OTP_MINUTES)
    with db() as c:
        c.execute("""INSERT INTO users(email,otp_hash,otp_expires,email_verified,status,created_at)
        VALUES(?,?,?,?,?,?) ON CONFLICT(email) DO UPDATE SET otp_hash=excluded.otp_hash,
        otp_expires=excluded.otp_expires,email_verified=0,status='email_pending'""",
        (email, hash_code(code), expiry.isoformat(), 0, "email_pending", now().isoformat()))
    return send_email(email, f"{APP_NAME} — code de vérification",
        f"Bonjour,\\n\\nVotre code est : {code}\\nIl expire dans {OTP_MINUTES} minutes. Si vous n'avez pas demandé ce code, ignorez cet e-mail.")

def verify_otp(email, code):
    with db() as c:
        r = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not r or not r["otp_hash"] or not r["otp_expires"]: return False, "Demandez d'abord un code."
        if now() > datetime.fromisoformat(r["otp_expires"]): return False, "Code expiré. Demandez-en un nouveau."
        if not hmac.compare_digest(r["otp_hash"], hash_code(code.strip())): return False, "Code incorrect."
        c.execute("UPDATE users SET email_verified=1,status='pending_approval',otp_hash=NULL,otp_expires=NULL WHERE email=?", (email,))
    return True, "E-mail vérifié. Votre demande attend l'approbation de l'administrateur."

def admin_password_ok(p):
    configured = secret("ADMIN_PASSWORD")
    return bool(configured) and hmac.compare_digest(p, configured)

st.markdown(f'<div class="hero"><h1>🚀 {APP_NAME}</h1><p>Analyse statistique • Historique observé • Accès approuvé par l’administrateur</p></div>', unsafe_allow_html=True)
st.warning("Aucune connexion directe à un site de paris n'est activée. Les statistiques décrivent les données saisies et ne garantissent pas le prochain multiplicateur.")

home, access, admin = st.tabs(["🏠 Accueil", "🔐 Accès utilisateur", "🛠️ Administration"])

with home:
    st.subheader("Bienvenue")
    st.markdown("""<div class="flight-panel"><div style="color:#aebdca;font-size:.9rem">ANIMATION DE DÉMONSTRATION · PAS UN RÉSULTAT RÉEL</div><div class="multiplier">2.40x <span style="font-size:.85rem;color:#aebdca;font-weight:500">SIMULATION</span></div><div class="plane">✈️</div><div class="flight-track"></div></div>""", unsafe_allow_html=True)
    st.write("DERSON Aviator Lab est un outil d'analyse de résultats observés, avec une animation illustrative.")
    if st.button("🎬 Lancer la démonstration", use_container_width=True):
        st.info("Démonstration visuelle uniquement : le multiplicateur affiché n'est pas une prédiction du prochain résultat.")
    st.markdown("1. Entrez votre e-mail.\n2. Vérifiez-le avec le code temporaire reçu.\n3. Attendez l'approbation de l'administrateur.\n4. Entrez le code d'activation envoyé après approbation.")
    st.caption("Ne donnez jamais votre mot de passe Gmail à l'application ou à l'administrateur.")

with access:
    st.subheader("Étape 1 — Vérification par e-mail")
    email = st.text_input("Adresse e-mail", placeholder="nom@example.com", key="email").strip().lower()
    a, b = st.columns(2)
    with a:
        if st.button("Envoyer le code e-mail", use_container_width=True):
            if not valid_email(email): st.error("Adresse e-mail invalide.")
            else:
                ok, msg = issue_otp(email)
                st.success("Code envoyé. Vérifiez aussi le dossier Spam.") if ok else st.error(msg)
    with b:
        otp = st.text_input("Code à 6 chiffres", max_chars=6, key="otp")
        if st.button("Vérifier l'e-mail", use_container_width=True):
            if not valid_email(email): st.error("Entrez d'abord une adresse e-mail valide.")
            else:
                ok, msg = verify_otp(email, otp)
                if ok: st.session_state["verified_email"] = email; st.success(msg)
                else: st.error(msg)
    st.divider()
    st.subheader("Étape 2 — Code d'activation")
    activation_email = st.text_input("Adresse vérifiée", value=st.session_state.get("verified_email", ""), key="activation_email").strip().lower()
    activation_code = st.text_input("Code d'activation", type="password", key="activation_code")
    if st.button("Activer l'accès", type="primary", use_container_width=True):
        with db() as c:
            r = c.execute("SELECT * FROM users WHERE email=?", (activation_email,)).fetchone()
            if not r or not r["email_verified"]: st.error("Vérifiez d'abord votre e-mail.")
            elif r["status"] != "approved" or not r["activation_hash"]: st.warning("L'administrateur n'a pas encore approuvé votre accès.")
            elif r["activation_expires"] and now() > datetime.fromisoformat(r["activation_expires"]): st.error("Code expiré. Contactez l'administrateur.")
            elif not hmac.compare_digest(r["activation_hash"], hash_code(activation_code.strip())): st.error("Code d'activation incorrect.")
            else:
                c.execute("UPDATE users SET status='active',activation_hash=NULL,activation_expires=NULL WHERE email=?", (activation_email,))
                st.session_state["active_user"] = activation_email
                st.success("Accès activé !")
    if st.session_state.get("active_user"):
        st.subheader("Tableau de bord")
        st.success(f"Utilisateur autorisé : {st.session_state['active_user']}")
        raw = st.text_area("Collez les multiplicateurs observés", placeholder="1.25, 2.10, 1.04, 5.30")
        if st.button("Analyser les données"):
            vals=[]
            for p in re.split(r"[,;\\s]+", raw.strip()):
                try:
                    v=float(p.lower().replace("x",""))
                    if v>=1: vals.append(v)
                except ValueError: pass
            if len(vals)<2: st.error("Entrez au moins deux valeurs valides.")
            else:
                import statistics
                x,y,z=st.columns(3)
                x.metric("Nombre de valeurs",len(vals)); y.metric("Médiane",f"{statistics.median(vals):.2f}x"); z.metric("Maximum",f"{max(vals):.2f}x")
                st.write(f"Sous 2x : {sum(v<2 for v in vals)} ({sum(v<2 for v in vals)/len(vals):.1%})")
                st.write(f"2x à moins de 10x : {sum(2<=v<10 for v in vals)} ({sum(2<=v<10 for v in vals)/len(vals):.1%})")
                st.write(f"10x ou plus : {sum(v>=10 for v in vals)} ({sum(v>=10 for v in vals)/len(vals):.1%})")
                st.caption("Analyse historique seulement, pas une prédiction garantie.")

with admin:
    st.subheader("Administration")
    if not st.session_state.get("admin_logged_in"):
        p = st.text_input("Mot de passe administrateur", type="password", key="admin_login")
        if st.button("Connexion admin"):
            if admin_password_ok(p): st.session_state["admin_logged_in"]=True; st.rerun()
            else: st.error("Mot de passe incorrect ou ADMIN_PASSWORD non configuré.")
    else:
        if st.button("Déconnexion admin"): st.session_state["admin_logged_in"]=False; st.rerun()
        with db() as c: rows=c.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        if not rows: st.info("Aucune demande pour le moment.")
        for r in rows:
            with st.expander(f"{r['email']} — {r['status']}"):
                st.write(f"E-mail vérifié : {'Oui' if r['email_verified'] else 'Non'}")
                if r["status"]=="pending_approval" and r["email_verified"]:
                    if st.button("Approuver et envoyer le code", key=f"approve_{r['email']}"):
                        code=secrets.token_urlsafe(6).upper().replace("-","").replace("_","")[:8]
                        expiry=now()+timedelta(minutes=ACTIVATION_MINUTES)
                        with db() as c:
                            c.execute("UPDATE users SET activation_hash=?,activation_expires=?,status='approved',approved_at=? WHERE email=?",
                              (hash_code(code),expiry.isoformat(),now().isoformat(),r["email"]))
                        ok,msg=send_email(r["email"],f"{APP_NAME} — code d'activation",
                          f"Bonjour,\\n\\nVotre demande a été approuvée. Votre code d'activation est : {code}\\nIl expire dans {ACTIVATION_MINUTES} minutes. Entrez-le dans l'application.")
                        st.success(f"Code envoyé à {r['email']}.") if ok else st.error(msg)
                        st.rerun()
                elif r["status"]=="approved": st.info("Approuvé, en attente de saisie du code.")
                elif r["status"]=="active": st.success("Utilisateur activé.")
                elif r["status"]=="email_pending": st.info("En attente de vérification de l'e-mail.")
        st.caption("Utilisez un mot de passe administrateur long et unique.")
