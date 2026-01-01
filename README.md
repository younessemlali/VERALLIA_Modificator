# 🔧 VERALLIA Modificator

**Système automatisé d'enrichissement des contrats XML Pixid pour VERALLIA France**

---

## 📋 Vue d'ensemble

Ce projet automatise le processus de correction des fichiers XML de contrats générés par Osmose pour les rendre conformes aux exigences de la plateforme Pixid.

### Problème résolu

Osmose (ERP) génère des contrats XML incomplets qui manquent 2 informations critiques :
1. **CustomerJobCode** : Code du poste de travail
2. **Cycle horaire** : Code du cycle de travail

Ces informations sont présentes dans les emails de commande Pixid mais ne sont pas extraites et intégrées dans le XML par Osmose.

---

## 🏗️ Architecture
```
┌─────────────┐
│    GMAIL    │ Emails de commande Pixid avec filtre
└──────┬──────┘
       │
       ↓
┌─────────────────────┐
│ GOOGLE APPS SCRIPT  │ Extraction automatique des données
└──────┬──────────────┘
       │
       ├─→ Google Drive (stockage emails)
       │
       ↓
┌─────────────┐
│   GITHUB    │ Stockage des données extraites (JSON)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  STREAMLIT  │ Interface web de correction XML
└─────────────┘
       │
       ↓
   XML corrigé (ISO-8859-1, nom identique)
```

---

## 📂 Structure du projet
```
VERALLIA_Modificator/
├── data/
│   └── commandes_extraites.json    # Données extraites par Google Apps Script
├── streamlit_app/
│   ├── app.py                       # Application Streamlit principale
│   ├── requirements.txt             # Dépendances Python
│   └── utils.py                     # Fonctions utilitaires XML
├── .gitignore
└── README.md
```

---

## 🚀 Installation rapide

### 1. Google Apps Script

1. Ouvrir https://script.google.com
2. Créer un nouveau projet
3. Copier le script fourni
4. Configurer le token GitHub dans le code
5. Créer un déclencheur horaire

### 2. Application Streamlit
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

---

## 🎯 Fonctionnalités

### Google Apps Script
- ✅ Détection automatique des emails de commande Pixid
- ✅ Extraction du code poste de travail (ex: `4FACO2`)
- ✅ Extraction du code cycle horaire (ex: `VA EQUIPE D 5X8`)
- ✅ Transfert automatique vers Google Drive
- ✅ Push des données vers GitHub

### Application Streamlit
- ✅ Interface web intuitive
- ✅ Upload de fichiers XML Osmose
- ✅ Sélection de la commande correspondante
- ✅ Modification automatique des 2 balises
- ✅ Préservation stricte :
  - Encodage ISO-8859-1
  - Nom de fichier original
  - Structure XML complète
- ✅ Téléchargement du XML corrigé

---

## ⚙️ Configuration requise

- **Google Account** avec Gmail
- **GitHub Account**
- **Python 3.8+** (pour Streamlit)
- **Navigateur web moderne**

---

## 🔐 Sécurité

- ⚠️ Ne jamais committer le token GitHub dans le code
- ✅ Limiter les permissions du token GitHub (uniquement `repo`)
- ✅ Configurer une date d'expiration pour le token

---

## 📝 Licence

Projet interne RANDSTAD France - Tous droits réservés

---

## 👥 Auteur

**Younes SEMLALI**  
Randstad France - Intégration Pixid

---

## 📞 Support

Pour toute question ou problème, contacter l'équipe Pixid Randstad.
