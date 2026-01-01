"""
VERALLIA Modificator - Application Streamlit
Interface web pour corriger les fichiers XML Osmose
"""

import streamlit as st
import requests
import json
from datetime import datetime
import utils

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="VERALLIA Modificator",
    page_icon="🔧",
    layout="wide"
)

GITHUB_REPO = "younessemlali/VERALLIA_Modificator"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/data/commandes_extraites.json"

# ============================================================================
# FONCTIONS
# ============================================================================

@st.cache_data(ttl=300)  # Cache 5 minutes
def load_commandes_from_github():
    """Charge les commandes depuis GitHub"""
    try:
        response = requests.get(GITHUB_RAW_URL, timeout=10)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            st.error(f"Erreur chargement GitHub: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Erreur connexion GitHub: {str(e)}")
        return []


def format_commande_display(commande: dict) -> str:
    """Formate l'affichage d'une commande pour le selectbox"""
    numero = commande.get('numeroCommande', 'N/A')
    contrat = commande.get('numeroContrat', 'N/A')
    client = commande.get('client', 'VERALLIA')
    date = commande.get('dateDebut', 'N/A')
    
    return f"Commande {numero} | Contrat {contrat} | {client} | {date}"


# ============================================================================
# INTERFACE
# ============================================================================

# En-tête
st.title("🔧 VERALLIA Modificator")
st.markdown("**Correction automatique des fichiers XML Osmose pour Pixid**")
st.divider()

# Informations
with st.expander("ℹ️ À propos", expanded=False):
    st.markdown("""
    Cette application corrige automatiquement les fichiers XML générés par Osmose
    en ajoutant les informations manquantes requises par Pixid :
    
    1. **CustomerJobCode** : Code du poste de travail (ex: `4FACO2`)
    2. **Cycle horaire** : Code du cycle de travail (ex: `VA EQUIPE D 5X8`)
    
    Les données sont extraites automatiquement des emails de commande Pixid
    via Google Apps Script et stockées sur GitHub.
    """)

# ============================================================================
# ÉTAPE 1 : CHARGER LES DONNÉES GITHUB
# ============================================================================

st.header("📊 Étape 1 : Sélectionner la commande")

# Bouton de rafraîchissement
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Actualiser les commandes", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Chargement des commandes
commandes = load_commandes_from_github()

if not commandes:
    st.warning("⚠️ Aucune commande disponible. Vérifiez que le script Google Apps Script fonctionne.")
    st.stop()

st.success(f"✅ {len(commandes)} commandes chargées depuis GitHub")

# Sélection de la commande
commande_options = {format_commande_display(c): c for c in commandes}
selected_display = st.selectbox(
    "Choisir une commande :",
    options=list(commande_options.keys()),
    help="Sélectionnez la commande correspondant au fichier XML à corriger"
)

selected_commande = commande_options[selected_display]

# Affichage des détails de la commande
with st.expander("📋 Détails de la commande", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Numéro de commande :** `{selected_commande.get('numeroCommande', 'N/A')}`")
        st.markdown(f"**Numéro de contrat :** `{selected_commande.get('numeroContrat', 'N/A')}`")
        st.markdown(f"**Client :** `{selected_commande.get('client', 'N/A')}`")
        st.markdown(f"**Qualification :** `{selected_commande.get('qualification', 'N/A')}`")
    
    with col2:
        st.markdown(f"**Code poste :** `{selected_commande.get('codePoste', 'N/A')}`")
        st.markdown(f"**Code cycle :** `{selected_commande.get('codeCycle', 'N/A')}`")
        st.markdown(f"**Date début :** `{selected_commande.get('dateDebut', 'N/A')}`")
        st.markdown(f"**Extraction :** `{selected_commande.get('dateExtraction', 'N/A')}`")

st.divider()

# ============================================================================
# ÉTAPE 2 : UPLOAD DU FICHIER XML
# ============================================================================

st.header("📁 Étape 2 : Charger le fichier XML Osmose")

uploaded_file = st.file_uploader(
    "Sélectionnez le fichier XML à corriger",
    type=['xml'],
    help="Fichier XML généré par Osmose (encodage ISO-8859-1)"
)

if uploaded_file is not None:
    # Lire le contenu
    xml_content = uploaded_file.read()
    original_filename = uploaded_file.name
    
    # Validation
    is_valid, error_msg = utils.validate_xml(xml_content)
    
    if not is_valid:
        st.error(f"❌ Fichier XML invalide : {error_msg}")
        st.stop()
    
    st.success(f"✅ Fichier chargé : `{original_filename}`")
    
    # Extraction des informations actuelles
    try:
        tree = utils.parse_xml(xml_content)
        current_info = utils.get_contract_info(tree)
        
        with st.expander("🔍 Informations actuelles du XML", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Numéro contrat :** `{current_info['numeroContrat']}`")
                st.markdown(f"**Ressource :** `{current_info['ressource']}`")
            
            with col2:
                st.markdown(f"**CustomerJobCode :** `{current_info['customerJobCodeActuel'] or '❌ VIDE'}`")
                cycle_name = current_info['cycleHoraireActuel']['name']
                cycle_value = current_info['cycleHoraireActuel']['value']
                st.markdown(f"**Cycle (name) :** `{cycle_name or '❌ VIDE'}`")
                st.markdown(f"**Cycle (value) :** `{cycle_value or '❌ VIDE'}`")
    
    except Exception as e:
        st.error(f"Erreur lecture XML : {str(e)}")
        st.stop()
    
    st.divider()
    
    # ========================================================================
    # ÉTAPE 3 : APERÇU DES MODIFICATIONS
    # ========================================================================
    
    st.header("🔄 Étape 3 : Aperçu des modifications")
    
    code_poste = selected_commande.get('codePoste', '')
    code_cycle = selected_commande.get('codeCycle', '')
    
    if not code_poste or not code_cycle:
        st.error("❌ Données manquantes dans la commande sélectionnée")
        st.stop()
    
    # Tableau de comparaison
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📄 Champ")
        st.markdown("**CustomerJobCode**")
        st.markdown("**Cycle (name)**")
        st.markdown("**Cycle (value)**")
    
    with col2:
        st.markdown("### ❌ Avant")
        st.markdown(f"`{current_info['customerJobCodeActuel'] or 'VIDE'}`")
        st.markdown(f"`{current_info['cycleHoraireActuel']['name'] or 'MODELE'}`")
        st.markdown(f"`{current_info['cycleHoraireActuel']['value'] or 'BH'}`")
    
    with col3:
        st.markdown("### ✅ Après")
        st.markdown(f"`{code_poste}`")
        st.markdown(f"`CYCLE`")
        st.markdown(f"`{code_cycle}`")
    
    st.divider()
    
    # ========================================================================
    # ÉTAPE 4 : CORRECTION
    # ========================================================================
    
    st.header("⚡ Étape 4 : Générer le XML corrigé")
    
    if st.button("🔧 Appliquer les corrections", type="primary", use_container_width=True):
        with st.spinner("Correction en cours..."):
            try:
                # Appliquer les corrections
                corrected_xml, stats = utils.apply_corrections(
                    xml_content,
                    code_poste,
                    code_cycle
                )
                
                # Validation du XML corrigé
                is_valid, error_msg = utils.validate_xml(corrected_xml)
                
                if not is_valid:
                    st.error(f"❌ XML corrigé invalide : {error_msg}")
                    st.stop()
                
                # Afficher les résultats
                st.success("✅ Corrections appliquées avec succès !")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("CustomerJobCode", "Modifié" if stats['customerJobCode'] else "Inchangé")
                with col2:
                    st.metric("Cycle horaire", "Modifié" if stats['cycleHoraire'] else "Inchangé")
                
                # Comparaison détaillée
                comparison = utils.compare_xml(xml_content, corrected_xml)
                
                with st.expander("📊 Comparaison détaillée", expanded=False):
                    st.json(comparison)
                
                # Bouton de téléchargement
                st.download_button(
                    label="📥 Télécharger le XML corrigé",
                    data=corrected_xml,
                    file_name=original_filename,  # MÊME NOM, pas de suffixe
                    mime="application/xml",
                    type="primary",
                    use_container_width=True
                )
                
                st.info(f"💾 Le fichier téléchargé aura le même nom : `{original_filename}`")
                st.warning("⚠️ Veillez à remplacer l'ancien fichier par le nouveau avant l'envoi à Pixid")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la correction : {str(e)}")
                st.exception(e)

else:
    st.info("👆 Veuillez charger un fichier XML pour continuer")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    VERALLIA Modificator v1.0 | Randstad France - Intégration Pixid
</div>
""", unsafe_allow_html=True)
