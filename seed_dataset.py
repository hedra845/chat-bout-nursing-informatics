import json
from database import get_db_connection

BENCHMARK_DATASET_ENTRIES = [
    {
        "concept_code": "NI-DEF-001",
        "domain": "Core Concepts",
        "concept_name_en": "Nursing Informatics Definition (ANA Model)",
        "concept_name_ar": "تعريف معلوماتية التمريض (نموذج الجمعية الأمريكية للتمريض ANA)",
        "clinical_definition": "The specialty that integrates nursing science with multiple information management and analytical sciences to identify, define, manage, and communicate data, information, knowledge, and wisdom in nursing practice.",
        "clinical_importance": "تمكين الممرضين والممارسين الصحيين من اتخاذ قرارات سريرية مبنية على الأدلة والبراهين وتحسين سلامة وجودة الرعاية.",
        "real_world_example": "استخدام نظم التوثيق السريري الموحد لتحليل أوقات استجابة التمريض للنداءات وتقليل معدل سقوط المرضى في الأجنحة.",
        "standard_mapping": "ANA Nursing Informatics Scope and Standards of Practice",
        "source_reference": "American Nurses Association (ANA) & IMIA-NI"
    },
    {
        "concept_code": "NI-DIKW-002",
        "domain": "Core Concepts",
        "concept_name_en": "DIKW Hierarchy (Data, Information, Knowledge, Wisdom)",
        "concept_name_ar": "هرمية DIKW (بيانات، معلومات، معرفة، حكمة)",
        "clinical_definition": "Framework demonstrating the transformation of discrete, raw clinical facts (Data), into contextualized insights (Information), synthesized clinical patterns (Knowledge), and the ethical, judicious bedside application (Wisdom).",
        "clinical_importance": "يوضح كيف يتحول تسجيل العلامات الحيوية الروتيني إلى قرارات تنقذ حياة المريض.",
        "real_world_example": "البيانات: SpO2 88%، معدل التنفس 28 -> المعلومات: مريض يعاني من نقص أكسجين وتسارع تنفس -> المعرفة: تمييز علامات فشل تنفسي وشيك -> الحكمة: بدء بروتوكول الأكسجين العاجل واستدعاء فريق الاستجابة السريعة (RRT).",
        "standard_mapping": "Graves & Corcoran Nursing Informatics DIKW Model",
        "source_reference": "Handbook of Informatics for Nurses & Healthcare Professionals"
    },
    {
        "concept_code": "NI-TERM-003",
        "domain": "Terminologies",
        "concept_name_en": "NANDA-I, NIC, NOC (The NNN Taxonomy)",
        "concept_name_ar": "تصنيفات NANDA و NIC و NOC التمريضية الموحدة",
        "clinical_definition": "A standardized nursing language triad: NANDA-I provides diagnoses (identifying human responses), NIC classifies nursing interventions, and NOC evaluates patient health outcomes on a Likert scale.",
        "clinical_importance": "توحيد لغة التواصل السريري، وقياس إسهام التمريض المباشر في تعافي المريض داخل السجلات الطبية.",
        "real_world_example": "التشخيص (NANDA): خطر الإصابة بقرح الفراش -> التدخل (NIC): تقليب المريض كل ساعتين واستخدام مرتبة هوائية -> النتيجة (NOC): سلامة الجلد والأنسجة بتقييم 5/5.",
        "standard_mapping": "ISO 18104 (Integration of a Reference Terminology Model for Nursing)",
        "source_reference": "Center for Nursing Classification and Clinical Effectiveness (CNC)"
    },
    {
        "concept_code": "NI-TERM-004",
        "domain": "Terminologies",
        "concept_name_en": "SNOMED CT & ICNP Mapping",
        "concept_name_ar": "معايير SNOMED CT والتصنيف الدولي ICNP",
        "clinical_definition": "Systematized Nomenclature of Medicine Clinical Terms mapped with the International Classification for Nursing Practice to allow seamless multidisciplinary electronic health record interoperability.",
        "clinical_importance": "ضمان تبادل بيانات التمريض مع بقية التخصصات الطبية والمختبرات والأشعة دون فقدان المعنى الدلالي.",
        "real_world_example": "عندما يسجل الممرض تشخيص 'Acute Pain' يظهر للطبيب بنفس المفهوم السريري المكود دولياً مما يمنع الازدواجية في العلاج.",
        "standard_mapping": "SNOMED International & International Council of Nurses (ICN)",
        "source_reference": "ICN & SNOMED Joint Harmonization Agreement"
    },
    {
        "concept_code": "NI-CDSS-005",
        "domain": "Clinical Decision Support",
        "concept_name_en": "Clinical Decision Support Systems & Alert Fatigue",
        "concept_name_ar": "نظم دعم القرار السريري (CDSS) وإجهاد الإنذارات (Alert Fatigue)",
        "clinical_definition": "Interactive clinical software systems that match patient characteristics with a medical knowledge base to provide tailored clinical alerts, reminders, and diagnostic support. Alert fatigue occurs when high volumes of non-critical alerts cause nurses to override or ignore safety warnings.",
        "clinical_importance": "تقليل الأخطاء الدوائية والجرعات الزائدة، مع ضرورة تصميم التنبيهات بذكاء وتصنيفها لمستويات لتجنب تعطيل الممرض.",
        "real_world_example": "ظهور تنبيه أحمر حرج عند محاولة إعطاء دواء Penicillin لمريض مسجل لديه حساسية مفرطة منه، مع إيقاف الأوردر إلكترونياً (Hard Stop).",
        "standard_mapping": "HIMSS CDSS 5 Rights Framework",
        "source_reference": "AHRQ (Agency for Healthcare Research and Quality)"
    },
    {
        "concept_code": "NI-EHR-006",
        "domain": "EHR & Systems",
        "concept_name_en": "BCMA & eMAR (Closed-Loop Medication Administration)",
        "concept_name_ar": "نظام الباركود BCMA وسجل الأدوية الإلكتروني eMAR",
        "clinical_definition": "A technology integration where nurses scan the patient's ID wristband and the medication barcode prior to administration, cross-referencing with the electronic Medication Administration Record (eMAR).",
        "clinical_importance": "تحقيق الحقوق الخمسة لإعطاء الدواء (المريض الصحيح، الدواء، الجرعة، الوقت، الطريقة) ومنع آلاف الوفيات الناتجة عن الأخطاء الدوائية.",
        "real_world_example": "إطلاق جرس تحذيري عند مسح باركود أمبول Heparin 5000 وحدة بينما الأوردر المكتوب هو 1000 وحدة فقط.",
        "standard_mapping": "Five Rights of Medication Administration Integration",
        "source_reference": "Institute for Safe Medication Practices (ISMP)"
    },
    {
        "concept_code": "NI-NMDS-007",
        "domain": "Core Concepts",
        "concept_name_en": "Nursing Minimum Data Set (NMDS)",
        "concept_name_ar": "مجموعة الحد الأدنى من البيانات التمريضية (NMDS)",
        "clinical_definition": "A standardized minimum set of items with uniform definitions and categories concerning the specific dimension of nursing care collected across all healthcare delivery settings.",
        "clinical_importance": "تمكين المقارنة الإحصائية بين المستشفيات المختلفة لتحديد معدلات كفاية التمريض وجودة النتائج العلاجية.",
        "real_world_example": "استخراج تقرير وطني يقارن بين أقسام العناية المركزة في معدلات استشفاء مرضى السكتة الدماغية بناءً على ساعات الرعاية التمريضية المقدمة.",
        "standard_mapping": "Werley and Zorn NMDS Framework",
        "source_reference": "National Center for Health Statistics & ANA"
    },
    {
        "concept_code": "NI-ETHICS-008",
        "domain": "Ethics & HIPAA",
        "concept_name_en": "PHI Protection & Role-Based Access Control (RBAC)",
        "concept_name_ar": "حماية بيانات المريض (PHI) والتحكم في الوصول حسب الدور (RBAC)",
        "clinical_definition": "Legal and informatics safeguards enforcing Protected Health Information privacy under HIPAA, restricting access to patient records solely to clinicians directly assigned to the care team.",
        "clinical_importance": "حماية سرية المريض ومنع التجسس على السجلات أو تسريب الملفات الجنائية والنفسية.",
        "real_world_example": "منع ممرض قسم العظام من فتح الملف الطبي لمريض في قسم النساء والتوليد إلا بطلب إذن طوارئ مع تسجيل محاولة الدخول في سجل التدقيق (Audit Log).",
        "standard_mapping": "HIPAA Privacy and Security Rules (45 CFR Part 160 & 164)",
        "source_reference": "U.S. Department of Health and Human Services (HHS)"
    },
    {
        "concept_code": "NI-ROLES-009",
        "domain": "Core Concepts",
        "concept_name_en": "Nursing Informatics Specialist Roles & Responsibilities",
        "concept_name_ar": "أدوار ومسؤوليات أخصائي معلوماتية التمريض",
        "clinical_definition": "Diverse clinical-technical careers including Clinical Analyst, Chief Nursing Informatics Officer (CNIO), Informatics Nurse Specialist (INS), Systems Educator, Quality & Safety Coordinator, and Telehealth Coordinator.",
        "clinical_importance": "يعتبر ممرض المعلوماتية حلقة الوصل المترجمة بين لغة الممرضين السريرية ولغة مهندسي ومبرمجي الأنظمة الصحية.",
        "real_world_example": "يقوم الـ CNIO بالمشاركة في اختيار نظام الـ EHR الجديد للمستشفى لضمان سهولة توثيق شاشات التمريض وعدم استهلاك وقت طويل على حساب رعاية المرضى.",
        "standard_mapping": "ANA Scope and Standards of Nursing Informatics Practice (2022)",
        "source_reference": "HIMSS Nursing Informatics Workforce Survey"
    },
    {
        "concept_code": "NI-STAND-010",
        "domain": "EHR & Systems",
        "concept_name_en": "Health Level 7 (HL7) & FHIR Standards",
        "concept_name_ar": "معايير HL7 و FHIR للتشغيل البيني للبيانات الصحية",
        "clinical_definition": "International standards for the transfer and exchange of clinical and administrative data between software applications used by various healthcare providers.",
        "clinical_importance": "تمكين المستشفيات والعيادات من قراءة سجلات المريض القادم من مستشفى آخر عبر الـ Cloud فورياً.",
        "real_world_example": "تطبيق هاتف المريض يسحب نتائج تحاليل الدم من معمل خارجي ويعرضها في ملفه الطبي بالمستشفى دون إعادة كتابتها يدوياً.",
        "standard_mapping": "HL7 Version 2/3 & Fast Healthcare Interoperability Resources (FHIR)",
        "source_reference": "Health Level Seven International"
    }
]

def seed_benchmark_dataset():
    conn = get_db_connection()
    cursor = conn.cursor()

    for item in BENCHMARK_DATASET_ENTRIES:
        cursor.execute("""
            INSERT OR REPLACE INTO reference_dataset 
            (concept_code, domain, concept_name_en, concept_name_ar, clinical_definition, clinical_importance, real_world_example, standard_mapping, source_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["concept_code"],
            item["domain"],
            item["concept_name_en"],
            item["concept_name_ar"],
            item["clinical_definition"],
            item["clinical_importance"],
            item["real_world_example"],
            item["standard_mapping"],
            item["source_reference"]
        ))
    
    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(BENCHMARK_DATASET_ENTRIES)} standard Nursing Informatics benchmark dataset entries.")

if __name__ == "__main__":
    seed_benchmark_dataset()
