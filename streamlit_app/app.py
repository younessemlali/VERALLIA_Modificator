"""
VERALLIA Modificator - Application Streamlit
Interface web pour corriger les fichiers XML Osmose
Version multi-commandes - Traite tous les contrats d'un fichier XML
"""

import streamlit as st
import requests
import json
from datetime import datetime
import utils
from lxml import etree
import io

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
            data = json.loads(response.text)
            # Filtrer les entrées null ou invalides
            if isinstance(data, list):
                return [c for c in data if c is not None and isinstance(c, dict)]
            return []
        else:
            st.error(f"Erreur chargement GitHub: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Erreur connexion GitHub: {str(e)}")
        return []


def extract_all_order_numbers_from_xml(xml_content: bytes) -> list:
    """Extrait TOUS les numéros de commande du XML"""
    try:
        parser = etree.XMLParser(encoding='iso-8859-1', remove_blank_text=False)
        tree = etree.parse(io.BytesIO(xml_content), parser)
        root = tree.getroot()
        
        # Chercher tous les OrderId
        ns = {'hr': 'http://ns.hr-xml.org/2004-08-02'}
        order_elements = root.findall('.//hr:OrderId/hr:IdValue', ns)
        
        orders = []
        seen = set()
        
        for elem in order_elements:
            if elem.text and elem.text.strip():
                numero = elem.text.strip()
                if numero not in seen:
                    orders.append(numero)
                    seen.add(numero)
        
        return orders
    except Exception as e:
        st.error(f"Erreur extraction numéros commande : {str(e)}")
        return []


def find_commande_by_number(commandes: list, numero_commande: str) -> dict:
    """Trouve une commande par son numéro"""
    for commande in commandes:
        if commande is None:
            continue
        if commande.get('numeroCommande') == numero_commande:
            return commande
    return None


def apply_corrections_multi(xml_content: bytes, commandes_map: dict) -> tuple:
    """
    Applique les corrections pour plusieurs commandes dans le même XML
    
    Args:
        xml_content: Contenu XML original
        commandes_map: Dict {numero_commande: {codePoste, codeCycle}}
    
    Returns:
        (XML corrigé en bytes, nombre de corrections appliquées)
    """
    parser = etree.XMLParser(encoding='iso-8859-1', remove_blank_text=False)
    tree = etree.parse(io.BytesIO(xml_content), parser)
    root = tree.getroot()
    
    ns = {'hr': 'http://ns.hr-xml.org/2004-08-02'}
    
    corrections_applied = 0
    
    # Trouver tous les blocs Assignment
    assignments = root.findall('.//hr:Assignment', ns)
    
    for assignment in assignments:
        # Trouver le OrderId de ce contrat
        order_elem = assignment.find('.//hr:OrderId/hr:IdValue', ns)
        if order_elem is None or not order_elem.text:
            continue
        
        numero_commande = order_elem.text.strip()
        
        # Vérifier si on a les données pour cette commande
        if numero_commande not in commandes_map:
            continue
        
        commande_data = commandes_map[numero_commande]
        code_poste = commande_data['codePoste']
        code_cycle = commande_data['codeCycle']
        
        # Corriger CustomerJobCode
        job_code_elem = assignment.find('.//hr:CustomerJobCode', ns)
        if job_code_elem is not None:
            # La balise existe déjà, mettre à jour
            old_value = job_code_elem.text
            job_code_elem.text = code_poste
            corrections_applied += 1
            print(f"Commande {numero_commande}: CustomerJobCode '{old_value}' → '{code_poste}'")
        else:
            # La balise n'existe pas, il faut la CRÉER
            cust_req = assignment.find('.//hr:CustomerReportingRequirements', ns)
            if cust_req is not None:
                # Chercher ExternalOrderNumber pour insérer AVANT
                external_order = cust_req.find('hr:ExternalOrderNumber', ns)
                
                # CRÉER la balise CustomerJobCode
                job_code_elem = etree.Element('{http://ns.hr-xml.org/2004-08-02}CustomerJobCode')
                job_code_elem.text = code_poste
                job_code_elem.tail = '\n          '  # Formatage avec indentation
                
                if external_order is not None:
                    # Insérer AVANT ExternalOrderNumber
                    index = list(cust_req).index(external_order)
                    cust_req.insert(index, job_code_elem)
                else:
                    # Si pas de ExternalOrderNumber, ajouter à la fin
                    cust_req.append(job_code_elem)
                
                corrections_applied += 1
                print(f"Commande {numero_commande}: CustomerJobCode CRÉÉE → '{code_poste}'")
        
        # Corriger Cycle horaire
        staffing_shift = assignment.find('.//hr:StaffingShift[@shiftPeriod="weekly"]', ns)
        if staffing_shift is not None:
            id_value_elem = staffing_shift.find('.//hr:IdValue', ns)
            if id_value_elem is not None:
                old_name = id_value_elem.get('name', '')
                old_value = id_value_elem.text
                id_value_elem.set('name', 'CYCLE')
                id_value_elem.text = code_cycle
                corrections_applied += 1
                print(f"Commande {numero_commande}: Cycle '{old_name}:{old_value}' → 'CYCLE:{code_cycle}'")
    
    # Convertir en bytes avec encodage ISO-8859-1
    output = io.BytesIO()
    tree.write(
        output,
        encoding='iso-8859-1',
        xml_declaration=True,
        pretty_print=False
    )
    
    return output.getvalue(), corrections_applied


# ============================================================================
# INTERFACE
# ============================================================================

# En-tête
st.title("🔧 VERALLIA Modificator")
st.markdown("**Correction automatique multi-commandes des fichiers XML Osmose pour Pixid**")
st.divider()

# Informations
with st.expander("ℹ️ À propos", expanded=False):
    st.markdown("""
    Cette application corrige automatiquement les fichiers XML générés par Osmose
    en ajoutant les informations manquantes requises par Pixid :
    
    1. **CustomerJobCode** : Code du poste de travail (ex: `4FACO2`)
    2. **Cycle horaire** : Code du cycle de travail (ex: `VA EQUIPE D 5X8`)
    
    **Mode multi-commandes** : L'application traite automatiquement TOUS les contrats
    présents dans un même fichier XML, sans intervention manuelle.
    """)

# Chargement des commandes
commandes = load_commandes_from_github()

if not commandes:
    st.warning("⚠️ Aucune commande disponible. Vérifiez que le script Google Apps Script fonctionne.")
    st.stop()

st.success(f"✅ {len(commandes)} commandes disponibles dans la base de données")

# Bouton de rafraîchissement
if st.button("🔄 Actualiser la base de commandes"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# ============================================================================
# UPLOAD DU FICHIER XML
# ============================================================================

st.header("📁 Charger le fichier XML Osmose")

uploaded_file = st.file_uploader(
    "Sélectionnez le fichier XML à corriger",
    type=['xml'],
    help="Fichier XML généré par Osmose (encodage ISO-8859-1). Peut contenir plusieurs contrats."
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
    
    # ========================================================================
    # DÉTECTION AUTOMATIQUE DE TOUTES LES COMMANDES
    # ========================================================================
    
    st.header("🔍 Analyse du fichier XML")
    
    with st.spinner("Recherche de toutes les commandes dans le fichier..."):
        # Extraire tous les numéros de commande
        all_orders = extract_all_order_numbers_from_xml(xml_content)
        
        if not all_orders:
            st.error("❌ Aucun numéro de commande trouvé dans le XML")
            st.stop()
        
        st.info(f"📋 **{len(all_orders)} commandes détectées** dans le fichier XML")
        
        # Chercher les correspondances
        commandes_trouvees = {}
        commandes_manquantes = []
        
        for numero in all_orders:
            commande = find_commande_by_number(commandes, numero)
            if commande:
                commandes_trouvees[numero] = {
                    'codePoste': commande.get('codePoste'),
                    'codeCycle': commande.get('codeCycle'),
                    'data': commande
                }
            else:
                commandes_manquantes.append(numero)
    
    # Affichage des résultats
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "✅ Commandes trouvées",
            len(commandes_trouvees),
            f"sur {len(all_orders)} total"
        )
    
    with col2:
        st.metric(
            "❌ Commandes manquantes",
            len(commandes_manquantes),
            f"sur {len(all_orders)} total"
        )
    
    # Détails des commandes trouvées
    if commandes_trouvees:
        with st.expander(f"✅ Détails des {len(commandes_trouvees)} commandes trouvées", expanded=True):
            for numero, info in commandes_trouvees.items():
                st.markdown(f"**Commande {numero}** → Poste: `{info['codePoste']}` | Cycle: `{info['codeCycle']}`")
    
    # Détails des commandes manquantes
    if commandes_manquantes:
        with st.expander(f"⚠️ Commandes manquantes ({len(commandes_manquantes)})", expanded=False):
            st.warning("Ces commandes ne seront PAS corrigées car elles n'existent pas dans la base de données :")
            for numero in commandes_manquantes:
                st.markdown(f"- Commande **{numero}**")
            st.info("""
            **Pour corriger ces commandes :**
            1. Vérifiez que les emails sont dans votre label Gmail VERALLIA
            2. Relancez le script Google Apps Script
            3. Actualisez la base de commandes et rechargez le fichier XML
            """)
    
    if not commandes_trouvees:
        st.error("❌ Aucune commande trouvée dans la base de données. Impossible de corriger le fichier.")
        st.stop()
    
    st.divider()
    
    # ========================================================================
    # CORRECTION AUTOMATIQUE
    # ========================================================================
    
    st.header("⚡ Correction automatique")
    
    st.info(f"🔧 **{len(commandes_trouvees)} contrats** seront corrigés dans ce fichier XML")
    
    if st.button("🚀 Appliquer les corrections", type="primary", use_container_width=True):
        with st.spinner(f"Correction de {len(commandes_trouvees)} contrats en cours..."):
            try:
                # Préparer le mapping pour les corrections
                corrections_map = {}
                for numero, info in commandes_trouvees.items():
                    corrections_map[numero] = {
                        'codePoste': info['codePoste'],
                        'codeCycle': info['codeCycle']
                    }
                
                # Appliquer les corrections
                corrected_xml, nb_corrections = apply_corrections_multi(xml_content, corrections_map)
                
                # Validation du XML corrigé
                is_valid, error_msg = utils.validate_xml(corrected_xml)
                
                if not is_valid:
                    st.error(f"❌ XML corrigé invalide : {error_msg}")
                    st.stop()
                
                # Afficher les résultats
                st.success(f"✅ **{len(commandes_trouvees)} contrats traités, {nb_corrections} modifications appliquées !**")
                
                if commandes_manquantes:
                    st.warning(f"⚠️ {len(commandes_manquantes)} contrats non corrigés (commandes manquantes dans la base)")
                
                # Bouton de téléchargement
                st.download_button(
                    label=f"📥 Télécharger le XML corrigé ({len(commandes_trouvees)} contrats)",
                    data=corrected_xml,
                    file_name=original_filename,
                    mime="application/xml",
                    type="primary",
                    use_container_width=True
                )
                
                st.info(f"💾 Le fichier téléchargé aura le même nom : `{original_filename}`")
                st.success("✅ Vous pouvez maintenant envoyer ce fichier à Pixid")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la correction : {str(e)}")
                st.exception(e)

else:
    st.info("👆 Uploadez votre fichier XML pour démarrer le traitement automatique multi-commandes")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    VERALLIA Modificator v3.0 (Mode Multi-Commandes) | Randstad France - Intégration Pixid
</div>
""", unsafe_allow_html=True)
