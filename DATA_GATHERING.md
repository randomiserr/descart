# Data Gathering Guide for Czech Political Advisor MVP

To move from the Mock Data Layer to a real-world application, you need to gather the following datasets and API keys.

## 1. Static Corpus (Laws & Reports)

### Sources
*   **e-Sbírka (Ministry of Interior)**: [https://www.e-sbirka.cz/](https://www.e-sbirka.cz/)
    *   Download XML/PDF versions of key acts:
        *   *Zákon o daních z příjmů* (586/1992 Sb.)
        *   *Zákon o DPH* (235/2004 Sb.)
        *   *Zákon o rozpočtové odpovědnosti* (23/2017 Sb.)
        *   *Zákon o podporovaných zdrojích energie* (165/2012 Sb.)
*   **National Budget Council (NRR)**: [https://unrr.cz/](https://unrr.cz/)
    *   Download the latest "Zpráva o dlouhodobé udržitelnosti veřejných financí".

### Processing
*   Convert documents to text.
*   Chunk them into paragraphs (approx 500-1000 tokens).
*   Store in a Vector Database (e.g., ChromaDB, Pinecone) with metadata: `valid_from`, `valid_to`, `domain`.

## 2. Dynamic Corpus (Budget & Macro)

### A. State Budget (Monitor)
*   **Source**: MFCR Monitor API [https://monitor.statnipokladna.cz/](https://monitor.statnipokladna.cz/)
*   **Data Needed**:
    *   Expenditure by Chapter (Výdaje dle kapitol).
    *   Mandatory Expenditures (Mandatorní výdaje).
*   **Format**: JSON/CSV.

### B. Macroeconomic Indicators (ČSÚ)
*   **Source**: Czech Statistical Office Public Database (VDB) [https://vdb.czso.cz/vdbvo2/faces/en/index.jsf](https://vdb.czso.cz/vdbvo2/faces/en/index.jsf)
*   **Indicators**:
    *   GDP Growth (HDP)
    *   Inflation (CPI)
    *   Average Wage (Průměrná mzda)
    *   Unemployment Rate

### C. Fiscal Data (MFCR)
*   **Source**: Ministry of Finance
*   **Data**:
    *   General Government Debt (Dluh sektoru vládních institucí).
    *   Structural Deficit.

## 3. LLM API Key
*   You will need an API key for the Orchestrator.
*   Recommended: **Google Gemini API** or **OpenAI API**.
*   Set environment variable: `GOOGLE_API_KEY` or `OPENAI_API_KEY`.

## 4. Next Steps
1.  Replace `data/laws.json` with a script that queries your Vector DB.
2.  Replace `data/budget.json` with live calls to Monitor API.
3.  Update `orchestrator.py` to use the real LLM client instead of the mock logic.
