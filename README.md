# DERSON Aviator Lab

Prototype Streamlit avec page d'accueil, vérification e-mail par code, demandes d'accès, administration protégée, approbation et code d'activation envoyé par e-mail.

## Lancer
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Secrets à configurer chez l'hébergeur
```toml
SMTP_EMAIL = "votre-adresse-gmail@gmail.com"
SMTP_APP_PASSWORD = "votre-mot-de-passe-d-application-google"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
ADMIN_PASSWORD = "choisir-un-mot-de-passe-admin-long-et-unique"
CODE_HASH_SALT = "une-longue-chaine-aleatoire-et-secrete"
```
Pour Gmail, utiliser un mot de passe d'application Google si disponible, jamais le mot de passe normal de Gmail.

## Important
SQLite convient à une démo ; un hébergeur gratuit peut effacer les fichiers locaux au redémarrage. Pour une vraie utilisation publique, utiliser une base persistante, ajouter une limite de tentatives et une protection anti-abus. Aucun flux en direct de bookmaker n'est connecté et aucune prédiction du prochain multiplicateur n'est garantie. N'intégrez les plateformes de paris qu'avec autorisation explicite.
