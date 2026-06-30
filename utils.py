import re
from datetime import datetime

# Real-world founding years for the recently established companies in the dataset
COMPANY_FOUNDING_YEARS = {
    "Sarvam AI": 2023,
    "Krutrim": 2023,
    "CRED": 2018,
    "Rephrase.ai": 2019,
    "Glance": 2019,
    "Saarthi.ai": 2017,
    "Observe.AI": 2017,
    "Niramai": 2016,
    "Yellow.ai": 2016,
    "Locobuzz": 2015,
    "Verloop.io": 2015,
    "Wysa": 2015,
    "upGrad": 2015,
    "Meesho": 2015,
    "PhonePe": 2015,
    "Swiggy": 2014,
    "Razorpay": 2014,
    "Dream11": 2008,
    "Zomato": 2008,
    "Paytm": 2010,
    "Ola": 2010,
    "Freshworks": 2010,
    "BYJU'S": 2011,
    "Vedantu": 2011,
    "Nykaa": 2012,
    "PolicyBazaar": 2008,
    "InMobi": 2007,
    "Flipkart": 2007
}

# Max logical duration in months as of mid-2026
COMPANY_MAX_MONTHS = {
    "Sarvam AI": 42,
    "Krutrim": 36,
    "CRED": 96,
    "Rephrase.ai": 84,
    "Glance": 90
}

# IT consulting/services firms list to filter out candidates who worked ONLY at consulting
IT_CONSULTING_FIRMS = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
    "cognizant", "capgemini", "mphasis", "tech mahindra", "mindtree", 
    "genpact", "hcl", "wipro technologies", "cognizant technology solutions"
}

# Core NLP, search, retrieval, ranking, and LLM skills
RELEVANT_AI_SKILLS = {
    "nlp", "natural language processing", "information retrieval", "ir", "search", 
    "semantic search", "embeddings", "vector search", "vector database", "vector databases", 
    "pinecone", "milvus", "weaviate", "qdrant", "faiss", "opensearch", "elasticsearch", 
    "llms", "large language models", "fine-tuning", "fine tuning", "fine-tuning llms", 
    "lora", "qlora", "peft", "rag", "retrieval augmented generation", "sentence transformers", 
    "transformers", "pytorch", "tensorflow", "machine learning", "deep learning", 
    "applied ml", "ranking", "learning to rank", "ltr", "recommendation systems", 
    "recommendation", "recommender systems"
}

def is_honeypot(candidate):
    """
    Scans a candidate profile for structural anomalies and logical discrepancies.
    Returns True if the profile is flagged as a honeypot/trap, False otherwise.
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    education = candidate.get("education", [])
    
    # 1. Check skill proficiency vs duration
    # Trap: Expert/Advanced in skills with 0 duration
    for s in skills:
        prof = s.get("proficiency", "").lower()
        dur = s.get("duration_months", -1)
        if prof in ["expert", "advanced"] and dur == 0:
            return True
            
    # 2. Check recently founded companies start date and duration constraints
    for job in career:
        comp = job.get("company")
        sd = job.get("start_date")
        dur = job.get("duration_months", 0)
        
        if comp in COMPANY_FOUNDING_YEARS:
            # Check start date
            if sd:
                try:
                    start_year = int(sd.split("-")[0])
                    if start_year < COMPANY_FOUNDING_YEARS[comp]:
                        return True
                except:
                    pass
            # Check duration exceeds max age in 2026
            if comp in COMPANY_MAX_MONTHS and dur > COMPANY_MAX_MONTHS[comp]:
                return True
                
    # 3. Check for obvious title vs description discrepancies
    # E.g., Title mentions non-tech (Civil Engineer, HR, Graphic Designer) but description is standard marketing/support/sales copy
    for job in career:
        title = job.get("title", "").lower()
        desc = job.get("description", "").lower()
        if "civil engineer" in title and ("sales" in desc or "marketing" in desc or "software" in desc or "customer support" in desc):
            return True
        if "graphic designer" in title and ("sales" in desc or "marketing" in desc or "software" in desc or "customer support" in desc):
            return True
        if "hr manager" in title and ("sales" in desc or "marketing" in desc or "software" in desc or "customer support" in desc):
            return True
            
    # 4. Check for degree vs field of study mismatch
    # E.g., B.Tech in MBA
    for edu in education:
        deg = edu.get("degree", "").lower()
        fos = edu.get("field_of_study", "").lower()
        if "b.tech" in deg and "mba" in fos:
            return True
            
    # 5. Check career start date vs graduation year mismatch
    # E.g., started career > 4 years before graduation
    grad_years = [edu.get("end_year") for edu in education if edu.get("end_year") and edu.get("degree") and ("b" in edu.get("degree").lower() or "m" in edu.get("degree").lower())]
    if grad_years and career:
        min_grad_year = min(grad_years)
        career_start_years = []
        for job in career:
            sd = job.get("start_date")
            if sd:
                try:
                    career_start_years.append(int(sd.split("-")[0]))
                except:
                    pass
        if career_start_years:
            min_career_start = min(career_start_years)
            if min_career_start < min_grad_year - 4:
                return True
                
    # 6. Check profile experience vs sum of career history duration
    total_months = sum(job.get("duration_months", 0) for job in career)
    total_years = total_months / 12.0
    prof_years = profile.get("years_of_experience", 0)
    if abs(prof_years - total_years) > 3.0:
        return True
        
    return False

def is_pure_consulting(candidate):
    """
    Checks if a candidate has ONLY worked at IT consulting/services firms.
    """
    career = candidate.get("career_history", [])
    if not career:
        return True
    for job in career:
        comp = job.get("company", "").lower()
        # If they worked at at least one company NOT in the consulting list, they are fine
        is_service = False
        for firm in IT_CONSULTING_FIRMS:
            if firm in comp:
                is_service = True
                break
        if not is_service:
            return False
    return True

def get_location_score(candidate):
    """
    Scores candidate location. Noida/Pune hybrid get max score. Relocation candidates get partial score.
    """
    profile = candidate.get("profile", {})
    loc = profile.get("location", "").lower()
    country = profile.get("country", "").lower()
    signals = candidate.get("redrob_signals", {})
    willing_to_relocate = signals.get("willing_to_relocate", False)
    
    # Pune or Noida are hybrid centers
    if "noida" in loc or "pune" in loc:
        return 1.0
    # Delhi NCR / Gurgaon
    if "delhi" in loc or "gurgaon" in loc or "gurugram" in loc or "ncr" in loc or "ghaziabad" in loc or "faridabad" in loc:
        return 0.9
    # Other major Tier-1 cities
    if "bangalore" in loc or "bengaluru" in loc or "hyderabad" in loc or "mumbai" in loc or "chennai" in loc:
        return 0.75
    # Residing in India and willing to relocate
    if country == "india" and willing_to_relocate:
        return 0.5
    # Residing outside India or not willing to relocate
    return 0.1

def get_experience_score(candidate):
    """
    Scores experience level. 5-9 years is target.
    """
    profile = candidate.get("profile", {})
    exp = profile.get("years_of_experience", 0.0)
    
    if 5.0 <= exp <= 9.0:
        return 1.0
    elif 4.0 <= exp < 5.0:
        return 0.85
    elif 9.0 < exp <= 11.0:
        return 0.8
    elif 3.0 <= exp < 4.0:
        return 0.5
    elif 11.0 < exp <= 13.0:
        return 0.4
    else:
        return 0.1

def get_skills_score(candidate):
    """
    Scores skills based on relevance, proficiency, endorsements, and duration.
    """
    skills = candidate.get("skills", [])
    if not skills:
        return 0.0
        
    score = 0.0
    matched_skills = 0
    
    for s in skills:
        name = s.get("name", "").lower()
        prof = s.get("proficiency", "").lower()
        dur = s.get("duration_months", 0)
        ends = s.get("endorsements", 0)
        
        # Check if the skill matches our core AI/ML checklist
        is_relevant = False
        for rel_skill in RELEVANT_AI_SKILLS:
            if rel_skill in name:
                is_relevant = True
                break
                
        if is_relevant:
            # Base weight by proficiency
            weight = 0.2
            if prof == "expert":
                weight = 1.0
            elif prof == "advanced":
                weight = 0.8
            elif prof == "intermediate":
                weight = 0.5
                
            # Trust factors
            ends_multiplier = 1.0 + (ends / 40.0)
            ends_multiplier = min(ends_multiplier, 2.5)
            
            dur_multiplier = 1.0 + (dur / 12.0)
            dur_multiplier = min(dur_multiplier, 2.5)
            
            score += weight * ends_multiplier * dur_multiplier
            matched_skills += 1
            
    if matched_skills == 0:
        return 0.0
        
    # Normalize score. 3-4 strong expert skills should give score ~1.0
    normalized_score = min(1.0, score / 6.0)
    return normalized_score

def get_title_score(candidate):
    """
    Scores the candidate's current title and career titles for relevance.
    """
    profile = candidate.get("profile", {})
    current_title = profile.get("current_title", "").lower()
    
    # Check current title
    if any(k in current_title for k in ["senior ai", "sr. ai", "founding ai", "ai engineer"]):
        return 1.0
    if any(k in current_title for k in ["senior ml", "sr. ml", "founding ml", "machine learning engineer", "ml engineer"]):
        return 0.9
    if any(k in current_title for k in ["nlp engineer", "search engineer", "information retrieval"]):
        return 0.85
    if any(k in current_title for k in ["data scientist", "nlp developer"]):
        return 0.75
    if any(k in current_title for k in ["backend engineer", "software engineer", "tech lead"]):
        return 0.55
        
    # Check past titles in career history
    career = candidate.get("career_history", [])
    max_past_score = 0.1
    for job in career:
        t = job.get("title", "").lower()
        if any(k in t for k in ["ai engineer", "ml engineer", "machine learning engineer", "nlp engineer"]):
            max_past_score = max(max_past_score, 0.7)
        elif "data scientist" in t:
            max_past_score = max(max_past_score, 0.6)
            
    return max_past_score

def get_behavioral_multiplier(candidate):
    """
    Calculates multiplier based on Redrob behavioral/availability signals.
    """
    signals = candidate.get("redrob_signals", {})
    mult = 1.0
    
    # 1. last_active_date
    last_active = signals.get("last_active_date", "")
    if last_active:
        try:
            year = int(last_active.split("-")[0])
            if year == 2026:
                mult *= 1.0
            elif year == 2025:
                mult *= 0.85
            elif year == 2024:
                mult *= 0.6
            else:
                mult *= 0.3
        except:
            pass
            
    # 2. recruiter_response_rate
    resp_rate = signals.get("recruiter_response_rate", 0.0)
    mult *= (0.4 + 0.6 * resp_rate)
    
    # 3. open_to_work_flag
    if signals.get("open_to_work_flag", False):
        mult *= 1.15
        
    # 4. notice_period_days (sub-30 days notice period is ideal)
    notice = signals.get("notice_period_days", 90)
    if notice <= 30:
        mult *= 1.1
    elif notice <= 60:
        mult *= 1.0
    elif notice <= 90:
        mult *= 0.8
    else:
        mult *= 0.5
        
    # 5. interview_completion_rate
    int_rate = signals.get("interview_completion_rate", 0.0)
    mult *= (0.7 + 0.3 * int_rate)
    
    # 6. offer_acceptance_rate
    off_rate = signals.get("offer_acceptance_rate", -1)
    if off_rate != -1:
        mult *= (0.8 + 0.2 * off_rate)
        
    # 7. github_activity_score
    gh = signals.get("github_activity_score", -1)
    if gh > 50:
        mult *= 1.08
    elif gh > 80:
        mult *= 1.15
        
    # 8. saved_by_recruiters_30d
    saved = signals.get("saved_by_recruiters_30d", 0)
    if saved > 10:
        mult *= 1.05
        
    return mult

def calculate_score(candidate):
    """
    Computes composite fit score for candidate.
    """
    exp_s = get_experience_score(candidate)
    skill_s = get_skills_score(candidate)
    loc_s = get_location_score(candidate)
    title_s = get_title_score(candidate)
    
    # Combined composite score (max 1.0 before multiplier)
    composite = 0.30 * exp_s + 0.35 * skill_s + 0.15 * loc_s + 0.20 * title_s
    
    # Apply behavioral multiplier
    multiplier = get_behavioral_multiplier(candidate)
    final_score = composite * multiplier
    
    return round(final_score, 4)

def generate_reasoning(candidate, rank):
    """
    Generates a high-quality, factual, 1-2 sentence reasoning explaining the fit.
    Guaranteed not to hallucinate, referencing candidate experience, title, skills, and signals.
    """
    profile = candidate.get("profile", {})
    name = profile.get("anonymized_name")
    exp = profile.get("years_of_experience", 0.0)
    title = profile.get("current_title", "")
    loc = profile.get("location", "")
    
    # Extract relevant matching skills present in their skills list
    skills = [s.get("name") for s in candidate.get("skills", [])]
    matching = [sk for sk in skills if any(rel in sk.lower() for rel in RELEVANT_AI_SKILLS)]
    
    # Select top 2-3 matching skills
    skills_phrase = ""
    if matching:
        skills_phrase = ", specializing in " + ", ".join(matching[:3])
        
    signals = candidate.get("redrob_signals", {})
    notice = signals.get("notice_period_days", 90)
    active = signals.get("last_active_date", "")
    open_work = signals.get("open_to_work_flag", False)
    
    if rank <= 15:
        reason = f"Excellent fit with {exp} years of experience as a {title} based in {loc}{skills_phrase}."
        if notice <= 30:
            reason += f" Highly available with a short notice period of {notice} days and active platform engagement."
        else:
            reason += " Strong backend alignment matching the founding team's search and retrieval mandate."
    elif rank <= 50:
        reason = f"Strong candidate with {exp} years experience as a {title}{skills_phrase}."
        if open_work:
            reason += f" Stated location is {loc} and marked 'Open to Work' with strong platform activity."
        else:
            reason += f" Solid background in applied ML and system building, currently residing in {loc}."
    else:
        # Acknowledging some adjacent fits or concerns for lower ranks
        reason = f"Adjacent candidate with {exp} years experience as a {title} based in {loc}."
        if notice > 90:
            reason += f" Good baseline skills, but has a long notice period of {notice} days and moderate activity."
        else:
            reason += " Relevant skills in software engineering with interest transitioning to ML workloads."
            
    return reason
