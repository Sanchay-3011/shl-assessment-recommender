import re
import os
from typing import Any, Dict, List, Optional, Set, Literal
from app.models.schemas import ChatMessage, HiringConstraints, RetrievalQuery, ConversationContext
from app.utils.logger import logger

def expand_query_terms(role: Optional[str], langs: List[str], skills: List[str]) -> List[str]:
    """Expands query terms using curated synonym dictionaries for high-precision retrieval targeting."""
    expansions = []
    role_lower = role.lower() if role else ""
    langs_lower = [l.lower() for l in langs]
    skills_lower = [s.lower() for s in skills]

    # Python Developer
    if "python" in langs_lower or "python" in role_lower:
        expansions.extend(["Software Developer", "Software Engineer", "Programmer", "Coding"])
        
    # Java Developer
    if "java" in langs_lower or "java" in role_lower:
        expansions.extend(["Java", "Spring", "Backend", "JVM", "Software Developer", "Software Engineer"])

    # React Developer
    if "react" in skills_lower or "reactjs" in skills_lower or "react" in role_lower:
        expansions.extend(["ReactJS", "Frontend", "JavaScript", "SPA", "Software Developer", "Software Engineer"])

    # Node.js Developer
    if "node" in skills_lower or "node.js" in skills_lower or "node" in role_lower:
        expansions.extend(["NodeJS", "Backend", "JavaScript", "Software Developer", "Software Engineer"])

    # Data Scientist / ML
    if "data" in role_lower or "scientist" in role_lower or "machine" in role_lower or "learning" in role_lower:
        expansions.extend(["Data Scientist", "Machine Learning", "AI", "Python", "Data Analyst", "Statistical Analysis"])

    # Engineering Manager / Technical Leadership
    if "engineering manager" in role_lower or "technical manager" in role_lower or "engineering director" in role_lower or "head of engineering" in role_lower or "engineering lead" in role_lower or "principal engineer" in role_lower:
        expansions.extend(["Manager", "Director", "Leadership", "Management", "Executive", "People Leadership", "Personality"])

    # Sales Executive / Rep
    if "sales" in role_lower or "sales" in skills_lower:
        expansions.extend(["Sales Representative", "Business Development", "Account Executive", "Sales Executive"])

    # Customer Support
    if "support" in role_lower or "customer" in role_lower or "service" in role_lower:
        expansions.extend(["Customer Service", "Contact Centre", "Call Center", "Customer Support"])

    # Leadership
    if any(w in role_lower for w in ["leadership", "manager", "leader", "management", "director", "executive", "people leader", "supervisor"]):
        if "sales" not in role_lower and "account" not in role_lower:
            expansions.extend(["Manager", "Director", "Executive", "People Leader", "Leadership", "Management"])

    # Graduate
    if "graduate" in role_lower or "entry-level" in role_lower or "junior" in role_lower:
        expansions.extend(["Entry Level", "Graduate", "Intern", "Verify"])

    # Full Stack Developer/Engineer
    if "full stack" in role_lower:
        expansions.extend(["Software Developer", "Software Engineer", "JavaScript", "Java", "Python", "Coding", "Programming"])

    # Backend Engineer
    if "backend" in role_lower:
        expansions.extend(["Software Developer", "Software Engineer", "Java", "Python", "Coding", "Programming", "Backend"])

    # Frontend Engineer
    if "frontend" in role_lower:
        expansions.extend(["Software Developer", "Software Engineer", "JavaScript", "React", "HTML", "CSS", "Coding", "Programming"])

    # QA Engineer
    if "qa" in role_lower or "quality assurance" in role_lower or "tester" in role_lower:
        expansions.extend(["Software Developer", "Software Engineer", "Testing", "Coding", "Quality"])

    # DevOps / Cloud / Infrastructure (check both role AND skills)
    if "devops" in role_lower or "devops" in skills_lower:
        expansions.extend(["Software Developer", "Software Engineer", "Cloud", "Linux", "Docker", "Coding", "Programming"])
    if "cloud" in role_lower or "cloud" in skills_lower or "aws" in role_lower or "aws" in skills_lower or "azure" in role_lower or "azure" in skills_lower:
        expansions.extend(["Cloud", "AWS", "Azure", "Software Developer", "Software Engineer", "Coding", "Programming"])
    if "docker" in role_lower or "docker" in skills_lower:
        expansions.extend(["Docker", "Cloud", "Linux", "Software Developer", "Software Engineer", "Coding"])

    # Rust / niche language roles
    if "rust" in langs_lower:
        expansions.extend(["Software Developer", "Software Engineer", "Coding", "Programming", "Logic"])

    # Finance / Analyst
    if "finance" in role_lower or "analyst" in role_lower or "accounting" in role_lower:
        expansions.extend(["Finance", "Financial", "Accounting", "Numerical", "Analyst"])

    # Healthcare
    if "healthcare" in role_lower or "medical" in role_lower or "nursing" in role_lower:
        expansions.extend(["Healthcare", "Medical", "Nursing", "Verify"])

    # Mobile Developer
    if any(m in skills_lower for m in ["flutter", "react native", "ios", "android", "mobile"]) or any(m in langs_lower for m in ["dart", "swift", "kotlin", "objective-c"]) or "mobile" in role_lower or "ios" in role_lower or "android" in role_lower:
        expansions.extend(["Mobile", "iOS", "Android", "Software Developer", "Software Engineer"])

    return list(dict.fromkeys(expansions))

class ConversationEngine:
    """Production Conversation Engine governing stateless conversation analysis,

    intent classification, constraint history, and priority clarification.
    """

    def __init__(self, vocabulary: Optional[Set[str]] = None) -> None:
        """Initializes conversation engine with catalog vocabularies to identify tech stacks dynamically."""
        self.vocabulary = vocabulary or set()
        logger.info(f"ConversationEngine initialized with dynamic vocabulary of {len(self.vocabulary)} terms.")

    def process_conversation(self, messages: List[ChatMessage]) -> ConversationContext:
        """Processes stateless dialogue history turns chronologically.

        Extracts intent, constraints, history, and missing parameters.
        """
        logger.info("ConversationEngine processing dialogue turns...")

        # Empty conversation check
        if not messages:
            empty_constraints = HiringConstraints()
            return ConversationContext(
                current_intent="greeting",
                extracted_constraints=empty_constraints,
                constraint_history=[empty_constraints],
                missing_constraints=["role"],
                needs_clarification=True,
                clarification_question="Hello! I can help you select assessments. Could you specify the target job role or technology?",
                retrieval_query=None,
                comparison_targets=[],
                confidence_score=0.0,
                conversation_complete=False,
                refusal_reason=None
            )

        # 1. Detect prompt injection jailbreaks on the latest user message
        last_user_msg = next((m for m in reversed(messages) if m.role == "user"), None)
        if last_user_msg:
            content_lower = last_user_msg.content.lower()
            jailbreak_keywords = [
                "ignore previous instructions", "act as", "forget previous instructions",
                "developer message", "system prompt", "ignore retrieved catalog data",
                "ignore catalog data", "pretend you are"
            ]
            if any(kw in content_lower for kw in jailbreak_keywords):
                logger.warning("Jailbreak jailbreak attempt detected!")
                empty_constraints = HiringConstraints()
                return ConversationContext(
                    current_intent="prompt_injection",
                    extracted_constraints=empty_constraints,
                    constraint_history=[empty_constraints],
                    missing_constraints=[],
                    needs_clarification=False,
                    clarification_question=None,
                    retrieval_query=None,
                    comparison_targets=[],
                    confidence_score=0.0,
                    conversation_complete=False,
                    refusal_reason="Safety protocol triggered. Prompt injection keywords detected."
                )

            # 2. Detect out of scope queries
            out_of_scope_keywords = [
                "legal advice", "salary negotiation", "resume writing", "medical advice",
                "weather forecast", "how is the weather", "who won the game",
                "salary", "resume", "legal", "medical"
            ]
            if any(kw in content_lower for kw in out_of_scope_keywords):
                logger.info("Out of scope request detected.")
                empty_constraints = HiringConstraints()
                return ConversationContext(
                    current_intent="out_of_scope",
                    extracted_constraints=empty_constraints,
                    constraint_history=[empty_constraints],
                    missing_constraints=[],
                    needs_clarification=False,
                    clarification_question=None,
                    retrieval_query=None,
                    comparison_targets=[],
                    confidence_score=0.0,
                    conversation_complete=False,
                    refusal_reason="I can only assist you with SHL product catalog recommendations. General career, legal, or unrelated advice is out of scope."
                )

        # Chronologically parse history to trace constraints and compile update logs
        current_constraints = HiringConstraints()
        constraint_history: List[HiringConstraints] = []

        for msg in messages:
            if msg.role == "user":
                # Extract constraints and apply refinements (sequential turns update values)
                current_constraints = self._extract_turn_constraints(msg.content, current_constraints)
                constraint_history.append(current_constraints.model_copy())

        # Determine overall intent based on dialogue keywords and constraints
        last_text = last_user_msg.content.lower() if last_user_msg else ""
        current_intent: Literal["recommend", "compare", "refine_previous_recommendation", "clarify", "greeting", "lookup"] = "clarify"

        # Detect lookup intent: user is asking about a specific named assessment
        # Triggers on phrases like "tell me about X", "what is X", "details on X", "duration of X", "format of X"
        lookup_trigger_phrases = [
            "tell me about", "what is the", "what are the", "details on", "details about",
            "duration of", "format of", "how long is", "what does", "describe the",
            "info on", "information about", "more about", "what is"
        ]
        # Extract quoted or titled assessment name if present (supports single, double, and smart quotes)
        _lookup_assessment_name = None
        import re as _re
        _quoted_match = _re.search(r'["\'\u201c\u201d\u2018\u2019]([^"\'\u201c\u201d\u2018\u2019]+)["\'\u201c\u201d\u2018\u2019]', last_user_msg.content if last_user_msg else "")
        if _quoted_match:
            _lookup_assessment_name = _quoted_match.group(1).strip()
        _is_lookup = (
            any(phrase in last_text for phrase in lookup_trigger_phrases) or
            _quoted_match is not None
        ) and not any(kw in last_text for kw in ["hire", "hiring", "recommend", "suggest", "looking for", "need assessments", "find me"])

        # Determine greeting
        greeting_words = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon"]
        recommendation_keywords = ["recommend", "suggest", "hire", "hiring", "screen", "candidates", "look for", "find", "explore"]
        
        if any(last_text.startswith(gw) for gw in greeting_words) and len(messages) <= 2 and not current_constraints.role:
            current_intent = "greeting"
        # Detect lookup intent BEFORE compare/recommend to avoid misrouting
        elif _is_lookup:
            current_intent = "lookup"
        # Determine comparison
        elif any(kw in last_text for kw in ["compare", "difference between", "versus", "vs"]):
            current_intent = "compare"
        # Determine refinement: if explicit keywords are present, OR if previous turns already extracted a role/tech/skill
        elif (
            any(kw in last_text for kw in ["actually", "instead of", "change", "filter by", "add personality", "exclude"]) or
            (len(constraint_history) > 1 and any(
                h.role is not None or len(h.programming_languages) > 0 or len(h.skills) > 0
                for h in constraint_history[:-1]
            ))
        ):
            current_intent = "refine_previous_recommendation"
        # Determine recommendation if any constraints are present or query is seeking tests/hiring options
        elif (
            current_constraints.role or 
            current_constraints.programming_languages or 
            current_constraints.skills or
            any(kw in last_text for kw in recommendation_keywords)
        ):
            current_intent = "recommend"

        # Formulate comparison targets if comparison intent
        comparison_targets = []
        if current_intent == "compare" and last_user_msg:
            comparison_targets = self._extract_comparison_targets(last_user_msg.content)

        # Determine missing slots and prioritize clarifications
        missing_constraints = []
        needs_clarification = False
        clarification_question = None
        conversation_complete = False

        if current_intent not in ("greeting", "compare", "lookup"):
            # Required slots evaluated in priority order: role > keys > job_level > duration > language > adaptive
            if not current_constraints.role:
                missing_constraints.append("role")
            if not current_constraints.assessment_keys:
                missing_constraints.append("assessment_keys")
            if not current_constraints.job_level:
                missing_constraints.append("job_level")
            if current_constraints.duration is None:
                missing_constraints.append("duration")
            if not current_constraints.language:
                missing_constraints.append("language")
            if not current_constraints.adaptive:
                missing_constraints.append("adaptive")

            # Clarify policy: ask exactly ONE question targeting the highest-priority missing constraint.
            if not current_constraints.role and not current_constraints.programming_languages and not current_constraints.skills:
                needs_clarification = True
                clarification_question = "Could you specify the target job role or technology (e.g. Java, Python, .NET)?"
            elif (current_constraints.programming_languages or current_constraints.skills) and not current_constraints.job_level:
                needs_clarification = True
                clarification_question = "Are you hiring for an entry-level, mid-professional, or senior role?"
            else:
                needs_clarification = False

        # Formulate retrieval query if not clarifying
        retrieval_query = None
        # Store lookup assessment name in context for orchestrator to use
        if current_intent == "lookup":
            retrieval_query = RetrievalQuery(
                query_text=_lookup_assessment_name or (last_user_msg.content if last_user_msg else "Assessment"),
                filters={"__lookup__": _lookup_assessment_name or ""}  # special flag for orchestrator
            )
            conversation_complete = True
            needs_clarification = False

        if not needs_clarification and current_intent in ("recommend", "refine_previous_recommendation"):
            # Build structured query using all extracted constraints
            query_parts = []
            
            # Put technologies and programming languages first to maximize term relevance
            if current_constraints.programming_languages:
                query_parts.extend(current_constraints.programming_languages)
            if current_constraints.skills:
                query_parts.extend(current_constraints.skills)
                
            # Add role name
            if current_constraints.role:
                query_parts.append(current_constraints.role)
                
            # Apply curated synonym expansions
            synonyms = expand_query_terms(
                current_constraints.role,
                current_constraints.programming_languages,
                current_constraints.skills
            )
            for syn in synonyms:
                if syn not in query_parts:
                    query_parts.append(syn)
                    
            if last_user_msg and last_user_msg.content:
                query_parts.append(last_user_msg.content)
                    
            # Expand with general coding test vocabulary if technical context exists
            tech_roles = [
                "software developer", "software engineer", "programmer", "coder", 
                "full stack engineer", "backend engineer", "frontend engineer", 
                "qa engineer", "devops", "data scientist"
            ]
            has_tech_context = (
                len(current_constraints.programming_languages) > 0 or 
                any(s.lower() in ["react", "reactjs", "angular", "vue", "dotnet", ".net", "salesforce", "aws", "docker", "kubernetes", "azure", "cloud", "devops", "linux"] for s in current_constraints.skills) or
                (current_constraints.role and current_constraints.role.lower() in tech_roles)
            )
            if has_tech_context and not current_constraints.programming_languages:
                query_parts.extend(["Programming", "Coding", "Knowledge", "Skills"])
                
            query_text = " ".join(query_parts) if query_parts else "Assessment"

            filters = {}
            if current_constraints.job_level:
                filters["job_level"] = current_constraints.job_level
            if current_constraints.language:
                filters["language"] = current_constraints.language
            if current_constraints.duration is not None:
                filters["duration"] = current_constraints.duration
            if current_constraints.adaptive:
                filters["adaptive"] = current_constraints.adaptive
            if current_constraints.remote:
                filters["remote"] = current_constraints.remote

            retrieval_query = RetrievalQuery(query_text=query_text, filters=filters)
            conversation_complete = True

        # Calculate confidence score (ratio of filled required elements for recommendation)
        filled_slots = 6 - len(missing_constraints)
        base_confidence = float(filled_slots) / 6.0 if current_intent not in ("greeting", "compare") else 0.0
        
        # If role is present, confidence is sufficient (at least 0.6) for recommendation
        if current_constraints.role:
            confidence_score = max(base_confidence, 0.6)
        else:
            confidence_score = base_confidence

        if current_intent == "greeting":
            needs_clarification = True
            clarification_question = "Hello! I can help you select assessments. Could you specify the target job role or technology?"
            confidence_score = 0.0

        return ConversationContext(
            current_intent=current_intent,
            extracted_constraints=current_constraints,
            constraint_history=constraint_history,
            missing_constraints=missing_constraints,
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
            retrieval_query=retrieval_query,
            comparison_targets=comparison_targets,
            confidence_score=confidence_score,
            conversation_complete=conversation_complete,
            refusal_reason=None
        )

    def refine_with_retrieval(self, context: ConversationContext, candidates: List[Any]) -> ConversationContext:
        """Refines the conversation context using retrieval confidence results.

        If retrieval has no close matches, triggers clarification state.
        """
        if context.current_intent in ("recommend", "refine_previous_recommendation"):
            # Low confidence triggers if list is empty, or if maximum scores are low (e.g. 0.0 for mocks)
            if not candidates:
                logger.info("Zero matches found during search. Forcing clarification loop.")
                context.needs_clarification = True
                context.clarification_question = "I couldn't find matching assessments for those criteria. Could you specify a different job role or try broadening your requirements?"
                context.conversation_complete = False
            else:
                context.needs_clarification = False
        return context

    def _extract_turn_constraints(self, text: str, prev: HiringConstraints) -> HiringConstraints:
        """Helper to parse constraints from a single user turn, merging with previous state."""
        text_lower = text.lower()
        res = prev.model_copy()

        # 1. Parse Programming Languages and Technology Skills explicitly
        programming_languages_list = ["python", "java", "c++", "c#", "cobol", "sql", "php", "javascript", "typescript", "html", "css", "kotlin", "swift", "objective-c", "dart", "ruby", "go", "rust"]
        skills_list = ["react", "reactjs", "react native", "flutter", "ios", "android", "mobile", "angular", "vue", "node", "dotnet", ".net", "salesforce", "sap", "aws", "docker", "kubernetes", "git", "agile", "scrum", "geoscience", "wpf", "wcf", "mvc", "mvvm", "spring", "django", "linux", "azure", "cloud", "devops"]

        for lang in programming_languages_list:
            pattern = re.escape(lang)
            if lang in ("c#", "c++", "objective-c"):
                if re.search(r'\b' + pattern + r'|' + pattern + r'\b', text_lower):
                    cap_lang = "Objective-C" if lang == "objective-c" else lang.capitalize()
                    if cap_lang not in res.programming_languages:
                        res.programming_languages.append(cap_lang)
            else:
                if re.search(r'\b' + pattern + r'\b', text_lower):
                    if lang.capitalize() not in res.programming_languages:
                        res.programming_languages.append(lang.capitalize())

        for skill in skills_list:
            pattern = re.escape(skill)
            if skill == ".net":
                if re.search(r'(?:\s|^)\.net\b', text_lower):
                    if ".NET" not in res.skills:
                        res.skills.append(".NET")
            elif skill == "dotnet":
                if re.search(r'\b' + pattern + r'\b', text_lower):
                    if ".NET" not in res.skills:
                        res.skills.append(".NET")
            elif skill == "reactjs":
                if re.search(r'\b' + pattern + r'\b', text_lower):
                    if "React" not in res.skills:
                        res.skills.append("React")
            else:
                if re.search(r'\b' + pattern + r'\b', text_lower):
                    if skill == "react": cap_skill = "React"
                    elif skill == "ios": cap_skill = "iOS"
                    elif skill == "react native": cap_skill = "React Native"
                    else: cap_skill = skill.capitalize()
                    
                    if cap_skill not in res.skills:
                        res.skills.append(cap_skill)

        # Detect leadership context: if strong leadership signals co-occur with engineering terms
        # promote to a leadership role instead of a technical discipline role
        leadership_signals = ["lead teams", "mentor", "strategic", "head of", "people leader",
                              "leadership", "people management", "team lead", "technical lead"]
        has_leadership_context = any(
            re.search(r'\b' + re.escape(signal) + r'\b', text_lower)
            for signal in leadership_signals
        ) if not res.role else False
        has_eng_context = any(
            w in text_lower for w in ["engineer", "engineering", "technical", "technology"]
        )

        generic_roles = [
            # ENGINEERING LEADERSHIP — must come before generic engineering roles
            ("Engineering Manager", r"engineering\s+manager(s)?|engineering\s+director(s)?|head\s+of\s+engineering|technical\s+manager(s)?|principal\s+engineer(s)?|senior\s+engineering\s+lead(s)?|software\s+engineering\s+manager(s)?"),
            ("Data Scientist", r"machine learning|data scientist(s)?|\bdata analyst(s)?\b|\bml\b"),
            ("Backend Engineer", r"backend engineer(s)?|\bbackend\b"),
            ("Frontend Engineer", r"frontend engineer(s)?|\bfrontend\b"),
            ("Full Stack Engineer", r"full\s*stack engineer(s)?"),
            ("Software Engineer", r"software engineer(s)?|\bengineer(s)?\b"),
            ("Software Developer", r"software developer(s)?|\bdeveloper(s)?\b|\bprogrammer(s)?\b|\bcoder(s)?\b|\bdev(s)?\b|\bexpert(s)?\b"),
            ("QA Engineer", r"qa engineer(s)?|\btester(s)?\b|\bquality assurance\b"),
            ("Sales Executive", r"sales executive(s)?|\bsales representative(s)?\b|\bsales agent(s)?\b|\bsales\b"),
            ("Customer Support", r"customer support(s)?|\bcustomer service\b|\bsupport agent(s)?\b|\bsupport\b"),
            ("HR Manager", r"hr manager(s)?|\bhr\b"),
            ("Manager", r"leadership|leader|management|manager(s)?|\bdirector(s)?\b|\bsupervisor(s)?\b")
        ]

        # Apply leadership context override: if no role matched yet but leadership signals
        # co-occur with engineering/technical context, default to Engineering Manager
        if not res.role and has_leadership_context and has_eng_context:
            res.role = "Engineering Manager"
        
        for role_name, pattern in generic_roles:
            if re.search(r'\b' + pattern + r'\b', text_lower):
                # Context switch detector: if a completely new generic role is identified,
                # clear old constraints that belong to the previous role to prevent query pollution (e.g. Automata bleeding)
                if prev.role and prev.role != role_name:
                    logger.info(f"Context Switch Detected: Role changed from '{prev.role}' to '{role_name}'. Clearing sticky constraints.")
                    res.job_level = None
                    res.skills = []
                    res.programming_languages = []
                res.role = role_name
                break

        # 3. Extract Seniority / Job Levels
        level_patterns = {
            "Entry-Level": ["entry-level", "entry level", "junior"],
            "Graduate": ["graduate", "intern"],
            "Mid-Professional": ["mid-professional", "mid-level", "mid", "middle", "intermediate"],
            "Senior": ["senior", "sr"],
            "Manager": ["manager", "lead"],
            "Director": ["director", "head of"],
            "Executive": ["executive"],
            "Supervisor": ["supervisor"]
        }
        for level, keywords in level_patterns.items():
            if any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in keywords):
                res.job_level = level

        # 4. Match Job Role / Technology dynamically using compiled vocabulary, excluding noise/level/language/skill terms
        restricted_role_terms = {
            "intern", "entry-level", "entry", "level", "junior", 
            "mid-professional", "mid-level", "mid", "middle", "intermediate", 
            "senior", "sr", "manager", "lead", "supervisor", "director", 
            "executive", "hire", "hiring", "assessment", "assessments", 
            "test", "tests", "report", "reports", "solution", "solutions",
            "engineer", "engineers", "developer", "developers", "support",
            "executive", "executives", "manager", "managers", "scientist", "scientists",
            "candidate", "candidates", "expert", "experts", "specialist", "specialists",
            "practitioner", "practitioners", "profile", "card", "cards", "sim", "simulation",
            "simulations", "screen", "screener", "screeners", "options", "option", "details",
            "detail", "questionnaire", "questionnaires", "system", "systems", "feedback",
            "difference", "versus", "vs", "compare", "start", "chat", "good", "morning",
            "afternoon", "evening", "hello", "hi", "hey"
        }

        # Split text into clean word terms
        words = set(re.findall(r'\b[A-Za-z0-9+#.-]+\b', text_lower))
        matched_roles = []
        for word in words:
            if word in self.vocabulary and word not in restricted_role_terms and word not in programming_languages_list and word not in skills_list:
                matched_roles.append(word)

        if matched_roles:
            # Sort roles to keep a deterministic list
            matched_roles.sort()
            # We only use dynamic matched roles if we haven't already identified a generic role.
            # We DO NOT dump arbitrary remaining vocabulary words into res.skills to prevent query dilution.
            if not res.role:
                new_role = matched_roles[0].capitalize()
                if prev.role and prev.role != new_role:
                    logger.info(f"Context Switch Detected (Dynamic Role): Role changed from '{prev.role}' to '{new_role}'. Clearing sticky constraints.")
                    res.job_level = None
                    res.skills = []
                    res.programming_languages = []
                res.role = new_role

        # 5. Extract Duration Constraint (e.g., "under 20 minutes" -> 20)
        duration_match = re.search(r'(\d+)\s*(?:minutes|minute|min)', text_lower)
        if duration_match:
            res.duration = int(duration_match.group(1))

        # 6. Extract Preferred Languages
        languages_list = ["english", "spanish", "french", "german", "italian", "chinese", "japanese"]
        for lang in languages_list:
            if lang in text_lower:
                res.language = lang.capitalize()

        # 7. Extract Adaptive requirement
        if "adaptive" in text_lower:
            if any(neg in text_lower for neg in ["no", "exclude", "not"]):
                res.adaptive = "no"
            else:
                res.adaptive = "yes"

        # 8. Extract Remote requirement
        if "remote" in text_lower:
            if any(neg in text_lower for neg in ["no", "exclude", "not"]):
                res.remote = "no"
            else:
                res.remote = "yes"

        # 9. Extract Assessment Keys (Categories) — negation-first approach
        # Detect removals/exclusions BEFORE positive detection so that "remove coding simulations"
        # removes "Simulations" instead of adding it.
        negation_triggers = [
            ("remove", r"\bremove\s+(\w+)"),
            ("exclude", r"\bexclude\s+(\w+)"),
            ("no", r"\bno\s+(\w+)"),
            ("without", r"\bwithout\s+(\w+)"),
        ]
        explicitly_removed = set()
        for neg_type, neg_pattern in negation_triggers:
            for match in re.finditer(neg_pattern, text_lower):
                word_after = match.group(1)
                for cat_name, cat_keywords in {
                    "Ability & Aptitude": ["aptitude", "cognitive", "ability", "reasoning", "analytical", "gsa"],
                    "Personality & Behavior": ["personality", "behavior", "opq", "interpersonal", "soft skills"],
                    "Simulations": ["simulation", "interactive"],
                    "Knowledge & Skills": ["knowledge", "skills", "coding", "technical", "programming"]
                }.items():
                    if word_after in cat_keywords or any(kw.startswith(word_after) for kw in cat_keywords):
                        explicitly_removed.add(cat_name)

        # Remove explicitly removed categories from existing state
        for cat in explicitly_removed:
            if cat in res.assessment_keys:
                res.assessment_keys.remove(cat)

        category_patterns = {
            "Ability & Aptitude": ["aptitude", "cognitive", "ability", "reasoning", "analytical", "gsa"],
            "Personality & Behavior": ["personality", "behavior", "opq", "stakeholder", "work with", "interpersonal", "soft skills"],
            "Simulations": ["simulation", "interactive"],
            "Knowledge & Skills": ["knowledge", "skills", "coding", "technical", "programming"]
        }
        for category, keywords in category_patterns.items():
            if category in explicitly_removed:
                continue
            if any(kw in text_lower for kw in keywords):
                if category not in res.assessment_keys:
                    res.assessment_keys.append(category)

        return res

    def _extract_comparison_targets(self, text: str) -> List[str]:
        """Identifies acronyms or matching assessments to compare.
        
        Returns assessment names, acronyms, or ordinal sentinels
        (__ORDINAL_1__, __ORDINAL_2__) for relative comparisons.
        """
        text_lower = text.lower()
        targets = []

        # 1. Detect ordinal references: "first two", "first and second", "#1 and #2",
        #    "recommendation 1 and 2", "compare the first", "compare #1"
        ordinal_patterns = [
            (r"(?:first|#1|number\s*1|recommendation\s*1|item\s*1)\s*(?:and|,)\s*(?:second|#2|number\s*2|recommendation\s*2|item\s*2)",
             ["__ORDINAL_1__", "__ORDINAL_2__"]),
            (r"(?:first|#1|number\s*1)\s+two", ["__ORDINAL_1__", "__ORDINAL_2__"]),
            (r"(?:compare\s+(?:the\s+)?)?first\s+two", ["__ORDINAL_1__", "__ORDINAL_2__"]),
            (r"(?:compare\s+(?:the\s+)?)?#1\s+and\s+#2", ["__ORDINAL_1__", "__ORDINAL_2__"]),
            (r"(?:compare\s+(?:the\s+)?)?top\s+two", ["__ORDINAL_1__", "__ORDINAL_2__"]),
        ]
        for pattern, sentinels in ordinal_patterns:
            if re.search(pattern, text_lower):
                return sentinels

        # 2. Standard extraction of uppercase or vocabulary words (e.g. OPQ, GSA, Python, Java)
        words = re.findall(r'\b[A-Za-z0-9+#.-]+\b', text)
        for w in words:
            w_norm = w.lower()
            if w_norm in self.vocabulary or (w.isupper() and len(w) >= 3):
                targets.append(w)
        return list(set(targets))
