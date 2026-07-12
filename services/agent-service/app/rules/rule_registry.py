from __future__ import annotations


SOURCE_BASIS = {
    "RBI": "RBI financial education and digital banking awareness guidance",
    "SEBI": "SEBI investor education and risk-awareness guidance",
    "IRDAI": "IRDAI policyholder awareness and insurance protection guidance",
    "SBI": "Official SBI product and digital service knowledge",
    "NIVARA": "Nivara product rules for contextual digital adoption journey sequencing",
}


def to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def normalize_goal(goal: str) -> str:
    return goal.strip().lower().replace("_", " ")


def get_financial_metrics(context: dict) -> dict:
    financial = context.get("financial", {})

    income = to_float(financial.get("monthly_income"))
    expenses = to_float(financial.get("monthly_expenses"))
    savings = to_float(financial.get("savings"))
    investments = to_float(financial.get("investments"))
    insurance_coverage = to_float(financial.get("insurance_coverage"))

    expense_cover_months = round(savings / expenses, 2) if expenses > 0 else 0
    expense_ratio = round(expenses / income, 2) if income > 0 else 0
    monthly_surplus = round(income - expenses, 2)

    return {
        "monthly_income": income,
        "monthly_expenses": expenses,
        "savings": savings,
        "investments": investments,
        "insurance_coverage": insurance_coverage,
        "expense_cover_months": expense_cover_months,
        "expense_ratio": expense_ratio,
        "monthly_surplus": monthly_surplus,
    }


def apply_life_event_rules(context: dict) -> list[dict]:
    personal = context.get("personal", {})
    goals = {normalize_goal(goal) for goal in context.get("goals", [])}

    age = int(to_float(personal.get("age")))
    occupation = str(personal.get("occupation", "")).lower()
    marital_status = str(personal.get("marital_status", "")).lower()

    events: list[dict] = []

    if age <= 25 or "student" in occupation or "first" in occupation or "intern" in occupation:
        events.append({
            "rule_id": "LIFE_EARLY_CAREER",
            "life_event": "Early Career",
            "confidence": "medium",
            "reason": "Customer appears to be in an early earning or first-job stage.",
            "source_basis": SOURCE_BASIS["NIVARA"],
        })

    if 26 <= age <= 40:
        events.append({
            "rule_id": "LIFE_GROWTH_STAGE",
            "life_event": "Income Growth Stage",
            "confidence": "medium",
            "reason": "Customer is likely in an income growth and goal-building stage.",
            "source_basis": SOURCE_BASIS["NIVARA"],
        })

    if marital_status == "married":
        events.append({
            "rule_id": "LIFE_FAMILY_RESPONSIBILITY",
            "life_event": "Family Responsibility",
            "confidence": "high",
            "reason": "Customer is married, so family protection and goal planning may be relevant.",
            "source_basis": SOURCE_BASIS["NIVARA"],
        })

    if "home purchase" in goals:
        events.append({
            "rule_id": "LIFE_HOME_PURCHASE",
            "life_event": "Home Purchase Planning",
            "confidence": "high",
            "reason": "Customer selected home purchase as a financial goal.",
            "source_basis": SOURCE_BASIS["NIVARA"],
        })

    if "child education" in goals:
        events.append({
            "rule_id": "LIFE_CHILD_EDUCATION",
            "life_event": "Child Education Planning",
            "confidence": "high",
            "reason": "Customer selected child education as a financial goal.",
            "source_basis": SOURCE_BASIS["NIVARA"],
        })

    if "retirement" in goals or age >= 45:
        events.append({
            "rule_id": "LIFE_RETIREMENT_PLANNING",
            "life_event": "Retirement Planning",
            "confidence": "high",
            "reason": "Customer age or selected goal indicates retirement planning relevance.",
            "source_basis": SOURCE_BASIS["SEBI"],
        })

    return events


def apply_financial_need_rules(context: dict, episodic_memory: list[dict]) -> list[dict]:
    goals = {normalize_goal(goal) for goal in context.get("goals", [])}
    risk_preference = str(context.get("risk_preference", "")).lower()
    consent = context.get("consent", {})
    metrics = get_financial_metrics(context)

    needs: list[dict] = []

    if metrics["monthly_income"] <= 0:
        needs.append({
            "rule_id": "NEED_INCOME_CONTEXT_REQUIRED",
            "need": "Complete Financial Context",
            "priority": "high",
            "reason": "Monthly income is missing, so guidance should begin by completing financial context.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["NIVARA"],
        })

    if metrics["monthly_surplus"] <= 0 and metrics["monthly_income"] > 0:
        needs.append({
            "rule_id": "NEED_URGENT_BUDGET_CONTROL",
            "need": "Budget Stabilization",
            "priority": "critical",
            "reason": "Monthly expenses are equal to or higher than monthly income.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["RBI"],
        })

    if metrics["expense_ratio"] >= 0.7:
        needs.append({
            "rule_id": "NEED_HIGH_EXPENSE_PRESSURE",
            "need": "Cash Flow Discipline",
            "priority": "high",
            "reason": "Monthly expenses consume a high share of income.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["RBI"],
        })
    elif 0.5 <= metrics["expense_ratio"] < 0.7:
        needs.append({
            "rule_id": "NEED_MODERATE_EXPENSE_DISCIPLINE",
            "need": "Expense Discipline",
            "priority": "medium",
            "reason": "Monthly expenses are moderate and should be monitored to protect savings capacity.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["RBI"],
        })

    if metrics["expense_cover_months"] < 3:
        needs.append({
            "rule_id": "NEED_EMERGENCY_FUND_HIGH",
            "need": "Emergency Fund",
            "priority": "high",
            "reason": "Liquid savings cover less than 3 months of expenses.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["RBI"],
        })
    elif 3 <= metrics["expense_cover_months"] < 6:
        needs.append({
            "rule_id": "NEED_EMERGENCY_FUND_STRENGTHEN",
            "need": "Emergency Fund Strengthening",
            "priority": "medium",
            "reason": "Liquid savings cover 3 to 6 months of expenses and can be strengthened.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["RBI"],
        })

    if metrics["monthly_surplus"] > 0 and metrics["savings"] <= 0:
        needs.append({
            "rule_id": "NEED_SAVINGS_HABIT",
            "need": "Savings Habit",
            "priority": "high",
            "reason": "Customer has monthly surplus but no recorded savings.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["RBI"],
        })

    if metrics["insurance_coverage"] <= 0:
        needs.append({
            "rule_id": "NEED_PROTECTION_PLANNING",
            "need": "Protection Planning",
            "priority": "high",
            "reason": "Customer has no recorded insurance coverage.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["IRDAI"],
        })

    if "wealth creation" in goals and metrics["expense_cover_months"] >= 3:
        needs.append({
            "rule_id": "NEED_WEALTH_CREATION_READY",
            "need": "Wealth Creation",
            "priority": "medium",
            "reason": "Customer selected wealth creation and has some emergency coverage.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["SEBI"],
        })

    if "wealth creation" in goals and metrics["expense_cover_months"] < 3:
        needs.append({
            "rule_id": "NEED_INVESTMENT_READINESS_BLOCKED",
            "need": "Investment Readiness",
            "priority": "high",
            "reason": "Emergency fund should be prioritized before higher-risk wealth creation.",
            "evidence": metrics,
            "source_basis": SOURCE_BASIS["SEBI"],
        })

    if risk_preference == "conservative":
        needs.append({
            "rule_id": "NEED_CONSERVATIVE_PRODUCT_SUITABILITY",
            "need": "Capital Protection Preference",
            "priority": "medium",
            "reason": "Customer prefers conservative financial choices.",
            "evidence": {"risk_preference": risk_preference},
            "source_basis": SOURCE_BASIS["SEBI"],
        })

    if risk_preference == "moderate":
        needs.append({
            "rule_id": "NEED_BALANCED_PRODUCT_SUITABILITY",
            "need": "Balanced Growth Planning",
            "priority": "medium",
            "reason": "Customer prefers a balanced risk approach.",
            "evidence": {"risk_preference": risk_preference},
            "source_basis": SOURCE_BASIS["SEBI"],
        })

    if risk_preference == "aggressive":
        needs.append({
            "rule_id": "NEED_RISK_AWARE_GROWTH",
            "need": "Risk-Aware Growth Planning",
            "priority": "medium",
            "reason": "Customer prefers aggressive growth, so risk awareness is important.",
            "evidence": {"risk_preference": risk_preference},
            "source_basis": SOURCE_BASIS["SEBI"],
        })

    if "home purchase" in goals:
        needs.append({
            "rule_id": "NEED_HOME_DOWN_PAYMENT",
            "need": "Home Down Payment Planning",
            "priority": "medium",
            "reason": "Customer selected home purchase as a financial goal.",
            "evidence": {"goal": "home purchase"},
            "source_basis": SOURCE_BASIS["SBI"],
        })

    if "child education" in goals:
        needs.append({
            "rule_id": "NEED_CHILD_EDUCATION_CORPUS",
            "need": "Child Education Corpus",
            "priority": "medium",
            "reason": "Customer selected child education as a goal.",
            "evidence": {"goal": "child education"},
            "source_basis": SOURCE_BASIS["SEBI"],
        })

    if "retirement" in goals:
        needs.append({
            "rule_id": "NEED_RETIREMENT_CORPUS",
            "need": "Retirement Planning",
            "priority": "medium",
            "reason": "Customer selected retirement planning as a goal.",
            "evidence": {"goal": "retirement"},
            "source_basis": SOURCE_BASIS["SEBI"],
        })

    if "tax saving" in goals:
        needs.append({
            "rule_id": "NEED_TAX_SAVING",
            "need": "Tax Saving",
            "priority": "medium",
            "reason": "Customer selected tax saving as a financial goal.",
            "evidence": {"goal": "tax saving"},
            "source_basis": SOURCE_BASIS["SBI"],
        })

    if consent.get("optional_sbi_signals_allowed") is False:
        needs.append({
            "rule_id": "NEED_CONSENT_LIMITED_PERSONALIZATION",
            "need": "Consent-Based Personalization",
            "priority": "low",
            "reason": "Optional SBI signals are not enabled, so recommendations must use only customer-provided context.",
            "evidence": {"optional_sbi_signals_allowed": False},
            "source_basis": SOURCE_BASIS["NIVARA"],
        })

    needs.append({
        "rule_id": "NEED_DIGITAL_ADOPTION_GUIDANCE",
        "need": "Digital Adoption Guidance",
        "priority": "low",
        "reason": "Customer should receive clear next steps to adopt relevant digital financial services.",
        "evidence": {"channel": "digital"},
        "source_basis": SOURCE_BASIS["RBI"],
    })

    needs.append({
        "rule_id": "NEED_FRAUD_AWARENESS_NUDGE",
        "need": "Fraud Awareness",
        "priority": "low",
        "reason": "Customer should be reminded to verify financial products and avoid mis-selling or fraud.",
        "evidence": {"guidance_type": "safety_nudge"},
        "source_basis": SOURCE_BASIS["SEBI"],
    })

    return suppress_repeated_needs(needs, episodic_memory)


def suppress_repeated_needs(needs: list[dict], episodic_memory: list[dict]) -> list[dict]:
    ignored_needs = set()

    for memory in episodic_memory:
        feedback = memory.get("feedback", {})
        if feedback.get("action") in {"ignored", "dismissed"}:
            need = feedback.get("need")
            if need:
                ignored_needs.add(need)

    adjusted_needs = []
    for need in needs:
        if need["need"] in ignored_needs:
            need = {
                **need,
                "priority": "low",
                "memory_adjustment": "Lowered priority because customer previously ignored this need.",
            }
        adjusted_needs.append(need)

    return adjusted_needs


def apply_sbi_mapping_rules(needs: list[dict]) -> list[dict]:
    service_map = {
        "Complete Financial Context": ["Profile Completion", "Consent Settings"],
        "Budget Stabilization": ["Savings Account", "YONO Spend Visibility Journey"],
        "Cash Flow Discipline": ["Savings Account", "Recurring Deposit"],
        "Expense Discipline": ["Savings Account", "Recurring Deposit"],
        "Emergency Fund": ["Savings Account", "Recurring Deposit", "Fixed Deposit"],
        "Emergency Fund Strengthening": ["Recurring Deposit", "Fixed Deposit"],
        "Savings Habit": ["Recurring Deposit", "Savings Account"],
        "Protection Planning": ["SBI Insurance Services"],
        "Investment Readiness": ["Savings Account", "Recurring Deposit"],
        "Wealth Creation": ["SIP / Investment Services", "Mutual Fund Investment Services"],
        "Capital Protection Preference": ["Fixed Deposit", "Recurring Deposit"],
        "Balanced Growth Planning": ["Recurring Deposit", "SIP / Investment Services"],
        "Risk-Aware Growth Planning": ["SIP / Investment Services", "Mutual Fund Investment Services"],
        "Home Down Payment Planning": ["Recurring Deposit", "Fixed Deposit", "Home Loan Readiness Journey"],
        "Child Education Corpus": ["Recurring Deposit", "SIP / Investment Services"],
        "Retirement Planning": ["SIP / Investment Services", "Fixed Deposit", "Retirement Planning Journey"],
        "Tax Saving": ["Tax Saving Deposit", "Eligible Tax Saving Investment Services"],
        "Consent-Based Personalization": ["Consent Settings"],
        "Digital Adoption Guidance": ["YONO Digital Banking Journey"],
        "Fraud Awareness": ["Safe Banking Awareness Journey"],
    }

    recommendations = []

    for need in needs:
        services = service_map.get(need["need"], [])
        recommendations.append({
            "rule_id": f"MAP_{need['rule_id']}",
            "need": need["need"],
            "priority": need["priority"],
            "recommended_services": services,
            "reason": need["reason"],
            "benefit": build_service_benefit(need["need"], services),
            "source_basis": SOURCE_BASIS["SBI"],
            "evidence": need.get("evidence", {}),
        })

    return recommendations


def build_service_benefit(need: str, services: list[str]) -> str:
    if not services:
        return "No direct SBI service mapping is available for this need yet."

    return f"{', '.join(services)} can help the customer take the next digital adoption step for {need}."


def apply_journey_sequence_rules(needs: list[dict], recommendations: list[dict]) -> list[dict]:
    priority_order = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
    }

    sorted_recommendations = sorted(
        recommendations,
        key=lambda item: priority_order.get(item.get("priority", "low"), 4),
    )

    journey_steps = []

    for index, recommendation in enumerate(sorted_recommendations, start=1):
        journey_steps.append({
            "step_number": index,
            "need": recommendation["need"],
            "recommended_services": recommendation["recommended_services"],
            "action": build_next_action(recommendation),
            "priority": recommendation["priority"],
            "reason": recommendation["reason"],
        })

    return journey_steps


def build_next_action(recommendation: dict) -> str:
    need = recommendation["need"]

    action_map = {
        "Complete Financial Context": "Complete missing financial details before deeper personalization.",
        "Budget Stabilization": "Review income and expenses, then start a basic savings discipline journey.",
        "Cash Flow Discipline": "Start a recurring monthly saving habit aligned to surplus income.",
        "Expense Discipline": "Monitor expenses and protect monthly savings capacity.",
        "Emergency Fund": "Build at least 3 months of expense coverage before riskier goals.",
        "Emergency Fund Strengthening": "Increase emergency coverage toward 6 months of expenses.",
        "Savings Habit": "Start a recurring deposit or structured saving habit.",
        "Protection Planning": "Review insurance needs before long-term wealth planning.",
        "Investment Readiness": "Complete emergency fund before moving into investment adoption.",
        "Wealth Creation": "Begin an investment discovery journey aligned with risk preference.",
        "Capital Protection Preference": "Prefer safer deposit-led options before market-linked products.",
        "Balanced Growth Planning": "Explore a balanced mix of savings and investment services.",
        "Risk-Aware Growth Planning": "Explore growth products only with clear risk awareness.",
        "Home Down Payment Planning": "Create a down payment accumulation journey.",
        "Child Education Corpus": "Start a long-term child education corpus journey.",
        "Retirement Planning": "Start retirement corpus planning with suitable long-term products.",
        "Tax Saving": "Explore eligible tax-saving products based on customer suitability.",
        "Consent-Based Personalization": "Enable optional consent only if customer wants richer personalization.",
        "Digital Adoption Guidance": "Use guided digital steps to adopt the recommended SBI service.",
        "Fraud Awareness": "Verify product details and avoid sharing sensitive credentials.",
    }

    return action_map.get(need, "Review this recommendation and choose the next suitable digital action.")