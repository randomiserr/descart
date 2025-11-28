import streamlit as st
import json
from orchestrator import AdvisorOrchestrator

# Page Config
st.set_page_config(
    page_title="AI Politický a Ekonomický Poradce",
    page_icon="🇨🇿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern, minimalistic CSS inspired by Linear, Notion, Vercel
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        background-color: #F8F9FB;
        padding: 2rem 1rem;
    }
    
    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        color: #111827;
        letter-spacing: -0.02em;
    }
    
    p {
        color: #374151;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Header */
    .app-header {
        margin-bottom: 3rem;
    }
    
    .app-title {
        font-size: 2rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.5rem;
        letter-spacing: -0.03em;
    }
    
    .app-subtitle {
        font-size: 0.95rem;
        color: #6B7280;
        font-weight: 400;
    }
    
    /* Input Section */
    .stTextArea textarea {
        border: 1.5px solid #E5E7EB !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-size: 0.95rem !important;
        background: white !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        outline: none !important;
    }
    
    /* Button */
    .stButton button {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2) !important;
        width: 100% !important;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton button:active {
        transform: translateY(0);
    }
    
    /* Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #111827;
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #6B7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Topic Cards */
    .topic-card {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
    }
    
    .topic-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .topic-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .topic-icon {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }
    
    .topic-summary {
        background: #F9FAFB;
        border-left: 3px solid #3B82F6;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #374151;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: #F9FAFB !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        color: #374151 !important;
        transition: all 0.2s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: #F3F4F6 !important;
        border-color: #D1D5DB !important;
    }
    
    .streamlit-expanderContent {
        border: none !important;
        padding: 1rem 0 !important;
    }
    
    /* Detail Sections */
    .detail-section {
        background: #FAFBFC;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    
    .detail-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .detail-content {
        font-size: 0.9rem;
        color: #374151;
        line-height: 1.5;
    }
    
    /* Section Divider */
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #E5E7EB, transparent);
        margin: 3rem 0;
    }
    
    /* Success/Warning Messages */
    .stSuccess {
        background: #ECFDF5 !important;
        border: 1px solid #A7F3D0 !important;
        border-radius: 10px !important;
        color: #065F46 !important;
    }
    
    .stWarning {
        background: #FEF3C7 !important;
        border: 1px solid #FDE68A !important;
        border-radius: 10px !important;
        color: #92400E !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #3B82F6 !important;
    }
    
    /* Debug Section */
    .debug-section {
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Orchestrator
@st.cache_resource
def get_orchestrator():
    return AdvisorOrchestrator()

advisor = get_orchestrator()

# Header
st.markdown('<div class="app-header">', unsafe_allow_html=True)
st.markdown('<div class="app-title">🇨🇿 AI Politický a Ekonomický Poradce</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Analyzujte politické návrhy pomocí reálných dat z rozpočtu, zákonů a aktuálních zpráv</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Input Section
claim_text = st.text_area(
    "",
    height=120,
    placeholder="Zadejte politický program nebo výrok k analýze...\n\nNapř.: 'Zrušíme dotace na obnovitelné zdroje a ušetříme 20 miliard Kč. Investujeme do silnic 50 miliard.'",
    label_visibility="collapsed"
)

if st.button("Analyzovat"):
    if not claim_text:
        st.warning("⚠️ Prosím zadejte text k analýze")
    else:
        with st.spinner("Analyzuji..."):
            try:
                result = advisor.process_request(claim_text)
                
                st.success("✓ Analýza dokončena")
                
                if "topics" in result and len(result["topics"]) > 0:
                    # Metrics Section
                    total_topics = len(result["topics"])
                    total_claims = sum(len(topic.get('claims', [])) for topic in result["topics"])
                    
                    st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{total_topics}</div>
                            <div class="metric-label">Témata</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{total_claims}</div>
                            <div class="metric-label">Tvrzení</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">⚠️</div>
                            <div class="metric-label">Pozornost</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Section Divider
                    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                    
                    # Topics Analysis
                    for idx, topic in enumerate(result["topics"]):
                        topic_name = topic.get('name', f'Téma {idx+1}')
                        overall_analysis = topic.get('overall_analysis', 'Analýza není k dispozici.')
                        
                        st.markdown(f"""
                        <div class="topic-card">
                            <div class="topic-header">
                                <div class="topic-icon">🎯</div>
                                <span>{topic_name}</span>
                            </div>
                            <div class="topic-summary">{overall_analysis}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Detailed Claims
                        claims = topic.get('claims', [])
                        if claims:
                            with st.expander(f"Zobrazit detailní analýzu ({len(claims)} tvrzení)"):
                                for claim_idx, claim in enumerate(claims):
                                    st.markdown(f"**{claim.get('text', 'N/A')}**")
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown(f"""
                                        <div class="detail-section">
                                            <div class="detail-label">Proveditelnost</div>
                                            <div class="detail-content">{claim.get('feasibility', 'N/A')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        st.markdown(f"""
                                        <div class="detail-section">
                                            <div class="detail-label">Fiskální dopad</div>
                                            <div class="detail-content">{claim.get('fiscal_impact', 'N/A')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    with col2:
                                        st.markdown(f"""
                                        <div class="detail-section">
                                            <div class="detail-label">Právní rizika</div>
                                            <div class="detail-content">{claim.get('legal_risks', 'N/A')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        st.markdown(f"""
                                        <div class="detail-section">
                                            <div class="detail-label">Veřejné názory</div>
                                            <div class="detail-content">{claim.get('public_expert_opinion', 'N/A')}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    if claim_idx < len(claims) - 1:
                                        st.markdown("---")
                    
                    # Debug Section
                    st.markdown('<div class="debug-section">', unsafe_allow_html=True)
                    with st.expander("Technické detaily"):
                        st.json(result)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:
                    st.warning("Nepodařilo se vygenerovat strukturovanou analýzu")
                    st.json(result)

            except Exception as e:
                st.error(f"Došlo k chybě: {e}")
                import traceback
                st.code(traceback.format_exc())
