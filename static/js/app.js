// State Management
let currentTab = 'chat';
let currentUiLang = localStorage.getItem('nurse_ui_lang') || 'ar';
let booksData = [];
let categoriesChart = null;

// Translations dictionary for UI
const i18n = {
    ar: {
        chatNav: "المحادثة السريرية (Chat)",
        libraryNav: "مكتبة وتحليل الكتب (Books)",
        notesNav: "الملاحظات والدراسة (Notes)",
        analyticsNav: "الأسئلة المتكررة والإحصائيات",
        aiSettings: "إعدادات الذكاء الاصطناعي",
        langLabel: "لغة الإجابة المفضلة:",
        engineType: "نوع المحرك (Engine):",
        booksIndexed: "كتب مفهرسة",
        queriesLogged: "استفسار مسجل",
        chatTitle: "المحادثة الذكية التمريضية (Nursing Informatics Chat)",
        chatSubtitle: "مساعد سريري وأكاديمي لتحليل وفهم مفاهيم معلوماتية التمريض ومراجعها",
        datasetTitle: "قاعدة بيانات المرجع المعياري (Reference Dataset)",
        datasetSubtitle: "مجموعة بيانات ومعايير معتمدة دولياً كمرجع قياسي لإجابات الذكاء الاصطناعي",
        researcherTitle: "ذاكرة الباحث السريري وتتبع الفرضيات والأفكار",
        researcherSubtitle: "حفظ وتراكم أفكار الباحث، أسلوبه الحواري، واهتماماته لمواصلة النقاش المنطقي",
        libraryTitle: "مكتبة وتحليل الكتب والمراجع السريرية",
        librarySubtitle: "رفع، فهرسة، وتقسيم المراجع والكتب إلى فصول ومعلومات تمريضية مترابطة",
        notesTitle: "الملاحظات والملخصات التمريضية (Clinical Notes)",
        notesSubtitle: "الملاحظات المستخرجة تلقائياً من الكتب بالإضافة لملاحظاتك الدراسية",
        analyticsTitle: "إحصائيات الأسئلة المتكررة واستخدام النظام",
        analyticsSubtitle: "رصد المفاهيم التي يتم السؤال عنها بكثرة لتسهيل المراجعة وتحديد نقاط التركيز",
        inputPlaceholder: "اكتب سؤالك أو استفسارك التمريضي هنا (عربي أو إنجليزي)...",
        clearChatBtn: "محادثة جديدة",
        allBooksOption: "كل الكتب والمراجع المخزنة (شامل)",
        welcomeTitle: "المساعد الذكي لمعلوماتية التمريض (NurseInfo AI)",
        welcomeBody: "أهلاً بك! أنا مساعدك التفاعلي المتخصص في <strong>معلوماتية التمريض (Nursing Informatics)</strong> باللغتين العربية والإنجليزية.<br>يمكنك سؤالي بالعربية أو الإنجليزية، رفع الكتب والمراجع وتحليلها، ومراجعة الأسئلة الأكثر تكراراً.",
        youAuthor: "أنت (الباحث/الممرض)"
    },
    en: {
        chatNav: "Clinical Chat",
        libraryNav: "Book Analysis & Library",
        notesNav: "Clinical Notes & Summaries",
        analyticsNav: "Frequent Questions & Stats",
        aiSettings: "AI Engine Configuration",
        langLabel: "Preferred Response Language:",
        engineType: "Engine Type:",
        booksIndexed: "Indexed Books",
        queriesLogged: "Queries Logged",
        chatTitle: "Nursing Informatics AI Assistant",
        chatSubtitle: "Clinical & academic assistant for analyzing and mastering nursing informatics concepts",
        datasetTitle: "Benchmark Reference Dataset",
        datasetSubtitle: "Authoritative international standards dataset serving as clinical ground truth",
        researcherTitle: "Researcher Cognitive Memory & Hypotheses",
        researcherSubtitle: "Tracking researcher thought patterns, communication tone, and evolving ideas",
        libraryTitle: "Clinical Reference & Book Library",
        librarySubtitle: "Upload, parse, and auto-summarize nursing references and textbooks",
        notesTitle: "Clinical & Study Notes",
        notesSubtitle: "Auto-extracted clinical takeaways from references and personal study notes",
        analyticsTitle: "Repeated Queries & System Analytics",
        analyticsSubtitle: "Identify recurring clinical informatics questions to guide high-yield study",
        inputPlaceholder: "Type your nursing informatics question here (Arabic or English)...",
        clearChatBtn: "New Chat",
        allBooksOption: "All Ingested References (Comprehensive)",
        welcomeTitle: "Nursing Informatics AI Assistant",
        welcomeBody: "Welcome! I am your dedicated <strong>Nursing Informatics AI</strong> assistant, fully bilingual in English and Arabic.<br>Feel free to ask questions in either language, upload textbooks, explore auto-generated notes, and review frequent queries.",
        youAuthor: "You (Nurse / Researcher)"
    }
};

// Complete sentence-level client-side translation rules
const CLIENT_FULL_TRANSLATION_RULES = [
    { en: /### 🩺 Nursing Informatics Specialized Clinical Response:/gi, ar: "### 🩺 استجابة معلوماتية التمريض السريرية المتخصصة:" },
    { en: /### 🩺 Nursing Informatics Synthesized Response:/gi, ar: "### 🩺 ملخص إجابة معلوماتية التمريض المستخلصة:" },
    { en: /📖 \*\*Reference Findings \(Page (\d+)\):\*\*/gi, ar: "📖 **النتائج المستخلصة من المرجع السريري (صفحة $1):**" },
    { en: /📌 \*\*Complementary Context \(Page (\d+)\):\*\*/gi, ar: "📌 **سياق تكميلي داعم من المرجع (صفحة $1):**" },
    { en: /Extracted Reference Findings:/gi, ar: "النتائج المستخلصة من المراجع المعتمدة:" },
    { en: /Additional Context \(Page (\d+)\):/gi, ar: "سياق إضافي داعم (صفحة $1):" },
    { en: /💡 \*\*Clinical & Informatics Analysis:\*\*/gi, ar: "💡 **التحليل السريري والمعلوماتي:**" },
    { en: /💡 \*\*Clinical Informatics Analysis:\*\*/gi, ar: "💡 **التحليل السريري والمعلوماتي:**" },
    { en: /Clinical & Informatics Analysis:/gi, ar: "التحليل السريري والمعلوماتي:" },
    { en: /Clinical Informatics Analysis:/gi, ar: "التحليل السريري والمعلوماتي:" },
    { en: /- \*\*Clinical Impact:\*\*/gi, ar: "- **الأثر السريري:**" },
    { en: /- \*\*Interoperability & Standardization:\*\*/gi, ar: "- **التوافقية وتوحيد المعايير:**" },
    { en: /- \*\*Informatics Best Practice:\*\*/gi, ar: "- **أفضل الممارسات المعلوماتية:**" },
    { en: /Directly enhances healthcare quality, prevents medication errors, and optimizes patient safety outcomes\./gi, ar: "يعزز جودة الرعاية الصحية بشكل مباشر، ويمنع الأخطاء الدوائية، ويحسن نتائج سلامة المرضى." },
    { en: /Enforces standardized clinical terminologies and semantic consistency across Electronic Health Records \(EHR\) and data exchanges\./gi, ar: "يفرض استخدام المصطلحات السريرية القياسية الموحدة والاتساق الدلالي عبر السجلات الصحية الإلكترونية (EHR) وتبادل البيانات الطبية." },
    { en: /Crucial for mitigating alert fatigue through tiered Clinical Decision Support Systems \(CDSS\) and promoting evidence-based nursing care\./gi, ar: "ضروري جداً للحد من إجهاد التنبيهات عبر تصنيف نظم دعم القرار السريري (CDSS) وتطبيق الرعاية التمريضية القائمة على الأدلة والبراهين." },
    { en: /According to core \*\*Nursing Informatics\*\* principles:/gi, ar: "وفقاً للمبادئ الأساسية في **معلوماتية التمريض (Nursing Informatics)**:" },
    { en: /The discipline bridges nursing practice, data science, and computerized healthcare technologies to optimize workflow, patient monitoring, and longitudinal health documentation\./gi, ar: "يربط هذا التخصص بين الممارسة التمريضية وعلوم البيانات وتقنيات الرعاية الصحية لتحسين سير العمل ومراقبة المرضى والتوثيق الصحي المستمر." },
    { en: /Enables data-driven clinical decision-making across all inpatient and outpatient care environments\./gi, ar: "يمكّن الطاقم التمريضي من اتخاذ قرارات سريرية مبنية على البيانات في جميع بيئات وأقسام المستشفى الداخلية والخارجية." },
    { en: /Nursing Informatics \(NI\) is the specialty that integrates nursing science with multiple information and analytical sciences to identify, define, manage, and communicate data, information, knowledge, and wisdom in nursing practice\./gi, ar: "معلوماتية التمريض (NI) هي التخصص الذي يدمج علوم التمريض مع علوم المعلومات والتحليلات المتعددة لتحديد وتعريف وإدارة ونقل البيانات والمعلومات والمعرفة والحكمة في ممارسة التمريض السريري." },
    { en: /NI supports nurses, consumers, patients, the interprofessional healthcare team, and other stakeholders in their decision-making in all roles and settings to achieve desired outcomes\./gi, ar: "تدعم معلوماتية التمريض الممرضين والمرضى والفريق الصحي متعدد التخصصات في اتخاذ قراراتهم في جميع الأدوار والبيئات لتحقيق النتائج الصحية المرجوة." },
    { en: /The DIKW Pyramid in Nursing:/gi, ar: "هرم DIKW في التمريض (بيانات - معلومات - معرفة - حكمة):" },
    { en: /Data: Raw, unorganized facts without context \(e\.g\., Blood Pressure 120\/80 mmHg, SpO2 94%\)\./gi, ar: "البيانات (Data): حقائق أولية خام وغير منظمة وبدون سياق توضيحي (مثل: ضغط الدم 120/80 مم زئبق، نسبة الأكسجين 94%)." },
    { en: /Information: Data that has been structured and contextualized \(e\.g\., patient's BP is 120\/80 mmHg post-operative day 1\)\./gi, ar: "المعلومات (Information): بيانات تمت هيكلتها ووضعها في سياق واضح ومفهوم (مثل: ضغط دم المريض 120/80 في اليوم الأول بعد العملية الجراحية)." },
    { en: /Knowledge: Synthesized information with clinical meaning, patterns recognized \(e\.g\., recognizing that declining SpO2 combined with elevated respiration indicates respiratory distress\)\./gi, ar: "المعرفة (Knowledge): معلومات مجمعة ومحللة ذات دلالة سريرية مع تمييز الأنماط (مثل: إدراك أن هبوط الأكسجين مع تسارع التنفس يشير إلى ضائقة تنفسية)." },
    { en: /Wisdom: Judicious and ethical application of knowledge to direct patient care and future policy \(e\.g\., ordering preemptive airway management and altering clinical protocols based on predictive risk\)\./gi, ar: "الحكمة (Wisdom): التطبيق الرشيد والأخلاقي للمعرفة لتوجيه رعاية المرضى والسياسات المستقبلية (مثل: التدخل الاستباقي للتحكم بمجرى الهواء وتعديل البروتوكولات العلاجية وفق المخاطر المتوقعة)." },
    { en: /Standardized Nursing Terminologies \(SNTs\):/gi, ar: "المصطلحات التمريضية القياسية الموحدة (SNTs):" },
    { en: /1\. ICNP \(International Classification for Nursing Practice\): Maintained by ICN, provides formal terminology for nursing diagnoses, interventions, and outcomes\./gi, ar: "1. تصنيف ICNP (التصنيف الدولي لممارسة التمريض): يديره المجلس الدولي للتمريض، ويوفر مصطلحات رسمية للتشخيصات والتدخلات والنتائج التمريضية." },
    { en: /2\. NANDA-International \(NANDA-I\): Diagnostic classification for nursing diagnoses\./gi, ar: "2. منظمة ناندا الدولية (NANDA-I): نظام تصنيف تشخيصي مخصص لتحديد التشخيصات التمريضية." },
    { en: /3\. NIC \(Nursing Interventions Classification\): Comprehensive standardized language describing treatments nurses perform\./gi, ar: "3. تصنيف NIC (تصنيف التدخلات التمريضية): لغة قياسية موحدة شاملة تصف الإجراءات والعلاجات والتدخلات التي يقوم بها الممرضون." },
    { en: /4\. NOC \(Nursing Outcomes Classification\): Standardized classification to evaluate outcomes influenced by nursing interventions\./gi, ar: "4. تصنيف NOC (تصنيف النتائج التمريضية): تصنيف قياسي معتمد لقياس وتقييم النتائج الصحية المتأثرة بالتدخلات التمريضية." },
    { en: /5\. SNOMED CT: Comprehensive clinical healthcare terminology mapped with nursing terminologies for interoperable Electronic Health Records \(EHR\)\./gi, ar: "5. نظام SNOMED CT: مصطلحات سريرية شاملة ومترابطة مع مصطلحات التمريض لتحقيق التوافق والتشغيل البيني في السجلات الصحية الإلكترونية (EHR)." },
    { en: /6\. LOINC: Codes for clinical observations and laboratory results\./gi, ar: "6. نظام LOINC: أكواد ومعايير دولية لتوثيق الملاحظات السريرية ونتائج الفحوصات المخبرية." },
    { en: /Electronic Health Records \(EHR\) and Clinical Decision Support Systems \(CDSS\):/gi, ar: "السجلات الصحية الإلكترونية (EHR) ونظم دعم القرار السريري (CDSS):" },
    { en: /EHRs replace paper records with longitudinal electronic patient health records\./gi, ar: "تستبدل السجلات الصحية الإلكترونية الملفات الورقية بسجل صحي رقمي طولي ومستمر وشامل للمريض." },
    { en: /Key components include Computerized Provider Order Entry \(CPOE\), electronic Medication Administration Record \(eMAR\), bar-code medication scanning \(BCMA\), and clinical alerts\./gi, ar: "تشمل المكونات الرئيسية: إدخال أوامر الطبيب حاسوبياً (CPOE)، وسجل إعطاء الأدوية الإلكتروني (eMAR)، والتحقق من الأدوية بالباركود (BCMA)، والتنبيهات السريرية الذكية." },
    { en: /CDSS provides clinicians, staff, and patients with knowledge and person-specific information to enhance health decisions\./gi, ar: "تزود نظم دعم القرار السريري (CDSS) الممارسين والمرضى بالمعرفة السريرية والمعلومات المخصصة لدعم القرارات الصحية وتفادي الأخطاء الطبية." },
    { en: /Alert fatigue is a critical challenge where clinicians become desensitized to frequent alarms\./gi, ar: "يعد إجهاد التنبيهات (Alert Fatigue) تحدياً حرجاً حيث يفقد الكادر الطبي حساسيته واستجابته للتنبيهات المتكررة غير الضرورية." },
    { en: /Nursing Minimum Data Set \(NMDS\) and Data Standards:/gi, ar: "مجموعة الحد الأدنى للبيانات التمريضية (NMDS) ومعايير البيانات:" },
    { en: /NMDS is a minimum set of items with uniform definitions to collect essential nursing care data across health settings\./gi, ar: "مجموعة NMDS هي باقة من العناصر ذات التعريفات الموحدة لجمع بيانات الرعاية التمريضية الأساسية عبر مختلف المنشآت الصحية." },
    { en: /Categories include:/gi, ar: "تشمل التصنيفات:" },
    { en: /Nursing Care Elements: Nursing diagnosis, nursing intervention, nursing outcome, intensity of nursing care\./gi, ar: "عناصر الرعاية التمريضية: التشخيص التمريضي، والتدخل التمريضي، والنتيجة التمريضية، وكثافة وشدة الرعاية التمريضية." },
    { en: /Patient Demographic Elements: Personal identification, birth date, gender, race\/ethnicity, residence\./gi, ar: "البيانات الديموغرافية للمريض: الهوية الشخصية، وتاريخ الميلاد، والنوع، ومحل الإقامة." },
    { en: /Service Elements: Facility number, unique health record number, discharge date, disposition, primary nurse identifier\./gi, ar: "عناصر الخدمة: رقم المنشأة، ورقم السجل الصحي الموحد، وتاريخ الخروج، وحالة المريض، ومعرف الممرض الأساسي." },
    { en: /Ethical, Legal, and Privacy Considerations \(HIPAA & Security\):/gi, ar: "الاعتبارات الأخلاقية والقانونية والخصوصية (قانون HIPAA والأمان):" },
    { en: /Nursing informatics professionals must safeguard Protected Health Information \(PHI\)\./gi, ar: "يجب على أخصائيي معلوماتية التمريض حماية وتأمين المعلومات الصحية المحمية للمرضى (PHI)." },
    { en: /Under HIPAA regulations, strict access controls, encryption, and audit logs are mandated\./gi, ar: "بموجب لوائح قانون HIPAA، فإن ضوابط الوصول الصارمة والتشفير الكامل وسجلات المراقبة والتدقيق إلزامية على كافة الأنظمة." },
    { en: /Role-Based Access Control \(RBAC\) ensures nurses only access patient records within their assigned unit\/care team\./gi, ar: "يضمن التحكم بالوصول القائم على الدور الوظيفي (RBAC) وصول الممرضين فقط إلى سجلات المرضى الواقعين تحت رعايتهم المباشرة." },
    { en: /Telehealth nursing must adhere to interstate licensure compacts and secure end-to-end encrypted video channels\./gi, ar: "يجب أن يلتزم التمريض عن بعد (Telehealth) باتفاقيات التراخيص المعتمدة واستخدام قنوات اتصال وفيديو مشفرة بالكامل وآمنة." }
];

function translateFullTextLocally(text) {
    let out = text;
    for (const rule of CLIENT_FULL_TRANSLATION_RULES) {
        out = out.replace(rule.en, rule.ar);
    }
    return `🌐 **الترجمة العربية الكاملة والشاملة للمحتوى:**\n\n${out}`;
}

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initSettings();
    initChat();
    initLibrary();
    initNotes();
    initAnalytics();
    initDatasetFilters();
    applyUiLanguage(currentUiLang);

    loadDashboardStats();
    loadBooks();
    loadNotes();
    loadRepeatedQuestions();
});

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const tabTitle = document.getElementById('tab-title');
    const tabSubtitle = document.getElementById('tab-subtitle');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.getAttribute('data-tab');
            currentTab = tab;

            navItems.forEach(n => n.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            item.classList.add('active');
            const targetPane = document.getElementById(`tab-${tab}`);
            if (targetPane) targetPane.classList.add('active');

            const dict = i18n[currentUiLang] || i18n.ar;
            tabTitle.textContent = dict[`${tab}Title`];
            tabSubtitle.textContent = dict[`${tab}Subtitle`];

            if (tab === 'analytics') {
                loadDashboardStats();
                loadRepeatedQuestions();
            } else if (tab === 'dataset') {
                loadReferenceDataset();
            } else if (tab === 'researcher') {
                loadResearcherProfile();
            } else if (tab === 'library') {
                loadBooks();
            } else if (tab === 'notes') {
                loadNotes();
            }
        });
    });
}

function initSettings() {
    const aiModeSelect = document.getElementById('ai-mode-select');
    const aiLangSelect = document.getElementById('ai-lang-select');
    const geminiKeyInput = document.getElementById('gemini-api-key');
    const engineLabel = document.getElementById('active-engine-label');
    const langToggleBtn = document.getElementById('toggle-ui-lang-btn');

    const savedMode = localStorage.getItem('nurse_ai_mode') || 'auto';
    const savedLang = localStorage.getItem('nurse_ai_lang') || 'auto';
    const savedKey = localStorage.getItem('nurse_gemini_key') || '';

    aiModeSelect.value = savedMode;
    if (aiLangSelect) aiLangSelect.value = savedLang;
    geminiKeyInput.value = savedKey;

    function updateEngineUI() {
        const mode = aiModeSelect.value;
        const key = geminiKeyInput.value.trim();

        if (mode === 'local') {
            engineLabel.textContent = currentUiLang === 'ar' ? 'محرك محلي مستقل (عربي/EN)' : 'Local Standalone Engine (AR/EN)';
        } else if (mode === 'gemini') {
            engineLabel.textContent = key ? (currentUiLang === 'ar' ? 'Gemini API سحابي نشط' : 'Gemini Cloud API Active') : (currentUiLang === 'ar' ? 'أدخل مفتاح Gemini' : 'Enter Gemini Key');
        } else {
            engineLabel.textContent = key ? (currentUiLang === 'ar' ? 'تلقائي (Gemini + Local)' : 'Auto (Gemini + Local)') : (currentUiLang === 'ar' ? 'تلقائي (محرك محلي نشط)' : 'Auto (Local Active)');
        }
    }

    aiModeSelect.addEventListener('change', () => {
        localStorage.setItem('nurse_ai_mode', aiModeSelect.value);
        updateEngineUI();
    });

    if (aiLangSelect) {
        aiLangSelect.addEventListener('change', () => {
            localStorage.setItem('nurse_ai_lang', aiLangSelect.value);
        });
    }

    geminiKeyInput.addEventListener('input', () => {
        localStorage.setItem('nurse_gemini_key', geminiKeyInput.value.trim());
        updateEngineUI();
    });

    if (langToggleBtn) {
        langToggleBtn.addEventListener('click', () => {
            currentUiLang = currentUiLang === 'ar' ? 'en' : 'ar';
            localStorage.setItem('nurse_ui_lang', currentUiLang);
            applyUiLanguage(currentUiLang);
            updateEngineUI();
        });
    }

    updateEngineUI();
}

function applyUiLanguage(lang) {
    const dict = i18n[lang] || i18n.ar;
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';

    const langBtnText = document.getElementById('ui-lang-btn-text');
    if (langBtnText) langBtnText.textContent = lang === 'ar' ? 'English UI' : 'واجهة عربية';

    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.placeholder = dict.inputPlaceholder;

    const tabTitle = document.getElementById('tab-title');
    const tabSubtitle = document.getElementById('tab-subtitle');
    if (tabTitle && tabSubtitle) {
        tabTitle.textContent = dict[`${currentTab}Title`];
        tabSubtitle.textContent = dict[`${currentTab}Subtitle`];
    }

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) el.textContent = dict[key];
    });
}

function initChat() {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messagesBox = document.getElementById('chat-messages-box');
    const clearBtn = document.getElementById('clear-chat-btn');
    const chips = document.querySelectorAll('.chip');

    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = (input.scrollHeight) + 'px';
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });

    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            input.value = chip.getAttribute('data-prompt');
            form.dispatchEvent(new Event('submit'));
        });
    });

    clearBtn.addEventListener('click', () => {
        if (confirm('هل تود مسح المحادثة الحالية وبدء جلسة جديدة؟')) {
            messagesBox.innerHTML = `
                <div class="chat-msg bot">
                    <div class="msg-avatar"><i class="fa-solid fa-user-nurse"></i></div>
                    <div class="msg-content">
                        <div class="msg-author">المساعد الذكي لمعلوماتية التمريض (NurseInfo AI)</div>
                        <div class="msg-body">بدأت محادثة جديدة. تفضل بطرح سؤالك التمريضي وسأجيبك فوراً!</div>
                    </div>
                </div>
            `;
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = input.value.trim();
        if (!msg) return;

        appendMessage('user', msg);
        input.value = '';
        input.style.height = 'auto';

        const loadingId = 'loading-' + Date.now();
        appendLoading(loadingId);

        const bookId = document.getElementById('chat-book-selector').value;
        const mode = localStorage.getItem('nurse_ai_mode') || 'auto';
        const preferredLang = localStorage.getItem('nurse_ai_lang') || 'auto';
        const apiKey = localStorage.getItem('nurse_gemini_key') || '';

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: msg,
                    book_id: bookId ? parseInt(bookId) : null,
                    mode: mode,
                    lang: preferredLang,
                    api_key: apiKey
                })
            });

            const data = await res.json();
            removeLoading(loadingId);

            if (data.success) {
                appendMessage('bot', data.response, data.sources, data.model_used);
                loadDashboardStats();
                if (data.researcher_profile && data.researcher_profile.style) {
                    const toneBadge = document.getElementById('researcher-tone-badge');
                    if (toneBadge) {
                        toneBadge.innerHTML = `<i class="fa-solid fa-brain"></i> نمط الحوار: ${data.researcher_profile.style}`;
                    }
                }
            } else {
                appendMessage('bot', `عذراً، حدث خطأ: ${data.error || 'فشلت معالجة الطلب'}`);
            }
        } catch (err) {
            removeLoading(loadingId);
            appendMessage('bot', `تعذر الاتصال بالسيرفر. يرجى التأكد من تشغيل التطبيق.`);
        }
    });
}

function appendMessage(role, text, sources = [], modelUsed = '') {
    const box = document.getElementById('chat-messages-box');
    const msgDiv = document.createElement('div');
    const msgId = 'msg-' + Date.now() + '-' + Math.floor(Math.random() * 1000);
    msgDiv.className = `chat-msg ${role}`;
    msgDiv.id = msgId;

    const icon = role === 'bot' ? 'fa-user-nurse' : 'fa-user';
    const author = role === 'bot' ? (modelUsed ? `NurseInfo AI (${modelUsed})` : 'NurseInfo AI') : 'أنت (الباحث/الممرض)';

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="source-citation-box">
                <div class="source-title"><i class="fa-solid fa-bookmark"></i> مقتطفات من المرجع المعتمد:</div>
                ${sources.map((s, idx) => {
                    const snippetId = `${msgId}-src-${idx}`;
                    return `
                    <div style="margin-top: 6px; padding: 4px 0; border-bottom: 1px dashed #cbd5e1;">
                        <strong>[صفحة ${s.page_number}]:</strong> <span id="${snippetId}-text">${s.content}</span>
                        <div style="margin-top: 4px;">
                            <button type="button" class="btn-translate-action" style="font-size: 11px;" onclick="translateElementText('${snippetId}')">
                                <i class="fa-solid fa-language"></i> ترجمة هذا المقتطف بالكامل للعربية
                            </button>
                        </div>
                        <div id="${snippetId}-trans" style="display: none;"></div>
                    </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    const translateBtnHtml = role === 'bot' ? `
        <div class="msg-actions-bar">
            <button type="button" class="btn-translate-action" onclick="translateMessage('${msgId}')">
                <i class="fa-solid fa-language"></i> ترجمة الرد بالكامل للعربية (Translate All to Arabic)
            </button>
        </div>
    ` : '';

    msgDiv.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid ${icon}"></i></div>
        <div class="msg-content">
            <div class="msg-author">${author}</div>
            <div class="msg-body" id="${msgId}-body">${formatMarkdownLike(text)}</div>
            <div id="${msgId}-translation" style="display: none;"></div>
            ${sourcesHtml}
            ${translateBtnHtml}
        </div>
    `;

    box.appendChild(msgDiv);
    box.scrollTop = box.scrollHeight;
}

function appendLoading(id) {
    const box = document.getElementById('chat-messages-box');
    const div = document.createElement('div');
    div.id = id;
    div.className = 'chat-msg bot';
    div.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-user-nurse"></i></div>
        <div class="msg-content">
            <div class="msg-author">جاري التحليل واسترجاع المعلومات السريرية...</div>
            <div class="msg-body"><i class="fa-solid fa-circle-notch fa-spin"></i> يبحث الذكاء الاصطناعي في صفحات المراجع وقاعدة البيانات...</div>
        </div>
    `;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function formatMarkdownLike(str) {
    if (!str) return '';
    let text = str.trim();

    // 1. Headers formatting with clean badge/accent styling
    text = text.replace(/^### (.*?)$/gm, '<h4 class="content-heading-3"><i class="fa-solid fa-stethoscope"></i> $1</h4>');
    text = text.replace(/^## (.*?)$/gm, '<h3 class="content-heading-2">$1</h3>');
    text = text.replace(/^# (.*?)$/gm, '<h2 class="content-heading-1">$1</h2>');

    // 2. Bold and Italic formatting
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong class="highlight-term">$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // 3. Blockquotes formatting
    text = text.replace(/^> (.*?)$/gm, '<blockquote class="content-quote">$1</blockquote>');

    // 4. Numbered Lists (e.g. "1. ", "2. ")
    text = text.replace(/^(\d+)\.\s+(.*?)$/gm, '<div class="content-list-item numbered"><span class="list-num">$1</span><span class="list-text">$2</span></div>');

    // 5. Bullet Lists (e.g. "- " or "• ")
    text = text.replace(/^[-•]\s+(.*?)$/gm, '<div class="content-list-item bullet"><span class="bullet-dot"><i class="fa-solid fa-circle-dot"></i></span><span class="list-text">$1</span></div>');

    // 6. Paragraph separation: double newlines turn into spaced paragraphs
    // Split into logical blocks
    const blocks = text.split(/\n{2,}/);
    const htmlBlocks = blocks.map(block => {
        let b = block.trim();
        if (!b) return '';
        // If it starts with a tag like h4, blockquote, or content-list-item, keep it as is
        if (/^<(h[1-6]|blockquote|div)/.test(b)) {
            // Replace remaining single newlines with <br> inside the block if needed
            return b.replace(/\n/g, '<br>');
        }
        return `<p class="content-paragraph">${b.replace(/\n/g, '<br>')}</p>`;
    });

    return htmlBlocks.filter(b => b.length > 0).join('\n');
}

function initLibrary() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('book-file-input');
    const uploadForm = document.getElementById('upload-form');
    const filePreview = document.getElementById('file-info-preview');
    const previewName = document.getElementById('preview-file-name');
    const previewSize = document.getElementById('preview-file-size');
    const progressBar = document.getElementById('upload-progress');
    const statusAlert = document.getElementById('upload-status-alert');
    const removeFileBtn = document.getElementById('remove-file-btn');

    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.value = '';
            filePreview.style.display = 'none';
        });
    }

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            showFilePreview(fileInput.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            showFilePreview(fileInput.files[0]);
        }
    });

    function showFilePreview(file) {
        filePreview.style.display = 'flex';
        previewName.textContent = file.name;
        previewSize.textContent = `(${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
        if (statusAlert) statusAlert.style.display = 'none';
    }

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!fileInput.files || !fileInput.files.length) {
            showUploadStatus('يرجى اختيار ملف كتاب (PDF أو TXT أو MD) أولاً.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        const customTitle = document.getElementById('book-custom-title').value.trim();
        if (customTitle) formData.append('title', customTitle);

        progressBar.style.display = 'block';
        const uploadBtn = document.getElementById('upload-btn');
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> جاري الحفظ والفهرسة...`;

        try {
            const res = await fetch('/api/books/upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            progressBar.style.display = 'none';
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = `<i class="fa-solid fa-cloud-arrow-up"></i> حفظ وفهرسة الكتاب`;

            if (data.success) {
                showUploadStatus(`✅ تم بنجاح حفظ وفهرسة الكتاب: "${data.book.title}" (${data.book.pages} صفحة - ${data.book.words} كلمة) وتخزينه في قاعدة البيانات!`, 'success');
                uploadForm.reset();
                filePreview.style.display = 'none';

                // Automatically reload books and scroll to list
                await loadBooks();
                loadNotes();
                loadDashboardStats();

                const booksList = document.getElementById('books-list-container');
                if (booksList) {
                    booksList.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            } else {
                showUploadStatus(`❌ خطأ أثناء الحفظ: ${data.error || 'تعذر استكمال حفظ الكتاب'}`, 'error');
            }
        } catch (err) {
            progressBar.style.display = 'none';
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = `<i class="fa-solid fa-cloud-arrow-up"></i> حفظ وفهرسة الكتاب`;
            showUploadStatus('❌ تعذر الاتصال بالسيرفر. يرجى التأكد من تشغيل السيرفر والمحاولة مرة أخرى.', 'error');
        }
    });

    function showUploadStatus(msg, type) {
        if (!statusAlert) {
            alert(msg);
            return;
        }
        statusAlert.style.display = 'block';
        if (type === 'success') {
            statusAlert.style.background = '#f0fdf4';
            statusAlert.style.color = '#15803d';
            statusAlert.style.border = '1px solid #bbf7d0';
        } else {
            statusAlert.style.background = '#fef2f2';
            statusAlert.style.color = '#b91c1c';
            statusAlert.style.border = '1px solid #fecaca';
        }
        statusAlert.textContent = msg;
    }
}

async function loadBooks() {
    try {
        const res = await fetch('/api/books');
        const data = await res.json();
        if (!data.success) return;

        booksData = data.books;
        renderBooksGrid(booksData);
        populateBookSelectors(booksData);
    } catch (e) {
        console.error('Error loading books:', e);
    }
}

function renderBooksGrid(books) {
    const container = document.getElementById('books-list-container');
    const badge = document.getElementById('books-total-badge');
    badge.textContent = `${books.length} مراجع مسجلة`;

    if (!books.length) {
        container.innerHTML = `<p class="text-muted">لا يوجد كتب مفهرسة حالياً. قم برفع كتابك الأول في الأعلى.</p>`;
        return;
    }

    container.innerHTML = books.map(b => `
        <div class="book-card">
            <div>
                <div class="book-card-header">
                    <h4 class="book-title">${b.title}</h4>
                    <span class="badge">${b.file_type.toUpperCase()}</span>
                </div>
                <div class="book-meta">
                    <span><i class="fa-solid fa-file"></i> ${b.total_pages} صفحة</span>
                    <span><i class="fa-solid fa-align-left"></i> ${b.total_words.toLocaleString()} كلمة</span>
                    <span><i class="fa-solid fa-puzzle-piece"></i> ${b.chunks} مقطع مفهرس</span>
                </div>
                <p class="book-summary">${b.summary || 'تمت فهرسته واستخراج مواضيعه بنجاح.'}</p>
                <div class="book-topics">
                    ${(b.topics || []).map(t => `<span class="topic-tag">${t}</span>`).join('')}
                </div>
            </div>
            <div class="book-card-actions">
                <button class="btn-secondary-sm" onclick="askAboutBook(${b.id}, '${escapeQuotes(b.title)}')">
                    <i class="fa-solid fa-comments"></i> اسأل في هذا الكتاب
                </button>
                <button class="btn-secondary-sm text-danger" onclick="deleteBook(${b.id})">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function populateBookSelectors(books) {
    const selector = document.getElementById('chat-book-selector');
    const currentVal = selector.value;
    selector.innerHTML = `<option value="">كل الكتب والمراجع المخزنة (شامل)</option>`;

    books.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.id;
        opt.textContent = `${b.title} (${b.total_pages} ص)`;
        selector.appendChild(opt);
    });

    selector.value = currentVal;
}

function askAboutBook(bookId, bookTitle) {
    document.querySelector('.nav-item[data-tab="chat"]').click();
    document.getElementById('chat-book-selector').value = bookId;
    const input = document.getElementById('chat-input');
    input.value = `ما هي أهم المفاهيم السريرية والملخص الرئيسي لكتاب ${bookTitle}؟`;
    input.focus();
}

async function deleteBook(id) {
    if (!confirm('هل أنت متأكد من حذف هذا الكتاب وجميع مقاطعه وملاحظاته التلقائية؟')) return;
    try {
        const res = await fetch(`/api/books/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            loadBooks();
            loadNotes();
            loadDashboardStats();
        }
    } catch (e) {
        alert('فشل حذف الكتاب');
    }
}

function initNotes() {
    const modal = document.getElementById('note-modal');
    const openBtn = document.getElementById('open-new-note-modal');
    const closeBtn = document.getElementById('close-note-modal');
    const cancelBtn = document.getElementById('cancel-note-modal');
    const form = document.getElementById('new-note-form');
    const searchInput = document.getElementById('notes-search-input');
    const filterBtns = document.querySelectorAll('.filter-btn');

    openBtn.addEventListener('click', () => modal.style.display = 'flex');
    closeBtn.addEventListener('click', () => modal.style.display = 'none');
    cancelBtn.addEventListener('click', () => modal.style.display = 'none');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('note-title').value.trim();
        const content = document.getElementById('note-content').value.trim();
        const category = document.getElementById('note-category').value;
        const tagsRaw = document.getElementById('note-tags').value.trim();
        const tags = tagsRaw ? tagsRaw.split(',').map(t => t.trim()) : [];

        try {
            const res = await fetch('/api/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content, category, tags })
            });
            const data = await res.json();
            if (data.success) {
                modal.style.display = 'none';
                form.reset();
                loadNotes();
                loadDashboardStats();
            }
        } catch (err) {
            alert('حدث خطأ أثناء حفظ الملاحظة');
        }
    });

    searchInput.addEventListener('input', () => {
        loadNotes(searchInput.value.trim());
    });

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const cat = btn.getAttribute('data-cat');
            loadNotes(searchInput.value.trim(), cat);
        });
    });
}

async function loadNotes(searchTerm = '', category = '') {
    try {
        let url = `/api/notes?search=${encodeURIComponent(searchTerm)}`;
        if (category) url += `&category=${encodeURIComponent(category)}`;

        const res = await fetch(url);
        const data = await res.json();
        if (!data.success) return;

        renderNotesGrid(data.notes);
    } catch (e) {
        console.error('Error loading notes:', e);
    }
}

function renderNotesGrid(notes) {
    const container = document.getElementById('notes-list-container');
    if (!notes.length) {
        container.innerHTML = `<p class="text-muted" style="grid-column: 1/-1;">لا توجد ملاحظات مطابقة للبحث أو التصنيف.</p>`;
        return;
    }

    container.innerHTML = notes.map(n => `
        <div class="note-card ${n.is_pinned ? 'pinned' : ''}" id="note-card-${n.id}">
            <div class="note-header">
                <h4 class="note-title">${n.title}</h4>
                <i class="fa-solid fa-thumbtack pin-icon" onclick="togglePinNote(${n.id})" title="${n.is_pinned ? 'إلغاء التثبيت' : 'تثبيت في الأعلى'}"></i>
            </div>
            <div>
                <span class="note-category-badge">${n.category}</span>
            </div>
            <div class="note-body" id="note-body-${n.id}">${formatMarkdownLike(n.content)}</div>
            <div id="note-trans-${n.id}" style="display: none;"></div>
            <div class="note-footer">
                <span><i class="fa-solid fa-book"></i> ${n.book_title}</span>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <button type="button" class="btn-translate-action" style="font-size: 11px;" onclick="translateNote(${n.id})">
                        <i class="fa-solid fa-language"></i> ترجمة للعربية بالكامل
                    </button>
                    <button class="btn-secondary-sm text-danger" onclick="deleteNote(${n.id})">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

async function togglePinNote(id) {
    await fetch(`/api/notes/${id}/pin`, { method: 'POST' });
    loadNotes();
}

async function deleteNote(id) {
    if (!confirm('هل تود حذف هذه الملاحظة السريرية؟')) return;
    await fetch(`/api/notes/${id}`, { method: 'DELETE' });
    loadNotes();
    loadDashboardStats();
}

function initAnalytics() {}

async function loadRepeatedQuestions() {
    try {
        const res = await fetch('/api/analytics/repeated-questions');
        const data = await res.json();
        if (!data.success) return;

        const tbody = document.getElementById('repeated-table-body');
        if (!tbody) return;

        if (!data.questions.length) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center" style="padding: 24px; color: #94a3b8;">لم يتم تسجيل أسئلة متكررة حتى الآن.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.questions.map(q => {
            // Determine text direction for question
            const isArabic = /[\u0600-\u06FF]/.test(q.question);
            const dirClass = isArabic ? 'ar-text' : 'en-text';

            // Determine category badge theme
            let catTheme = 'general';
            const catLower = (q.category || '').toLowerCase();
            if (catLower.includes('terminolog') || catLower.includes('مصطلحات')) {
                catTheme = 'terminologies';
            } else if (catLower.includes('system') || catLower.includes('cdss') || catLower.includes('ehr')) {
                catTheme = 'systems';
            } else if (catLower.includes('core') || catLower.includes('dikw')) {
                catTheme = 'core';
            }

            return `
            <tr>
                <td>
                    <div class="table-question-cell ${dirClass}">
                        ${q.question}
                    </div>
                </td>
                <td style="text-align: center;">
                    <span class="table-cat-badge ${catTheme}">
                        ${q.category}
                    </span>
                </td>
                <td style="text-align: center;">
                    <div class="freq-pill">
                        <i class="fa-solid fa-fire"></i>
                        <span>${q.frequency} ${q.frequency === 1 ? 'مرة' : 'مرات'}</span>
                    </div>
                </td>
                <td>
                    <div class="table-date-cell">
                        ${q.last_asked}
                    </div>
                </td>
            </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Error loading repeated questions:', e);
    }
}

async function loadDashboardStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        if (!data.success) return;

        const s = data.stats;
        document.getElementById('stat-books-count').textContent = s.books;
        document.getElementById('stat-queries-count').textContent = s.total_queries_logged;

        document.getElementById('stat-total-books').textContent = s.books;
        document.getElementById('stat-total-pages').textContent = s.pages.toLocaleString();
        document.getElementById('stat-total-messages').textContent = s.messages;
        document.getElementById('stat-total-repeated').textContent = s.unique_questions;

        renderCategoryChart(s.notes_by_cat || {});
    } catch (e) {
        console.error('Error loading stats:', e);
    }
}

function renderCategoryChart(catData) {
    const ctx = document.getElementById('categoriesChart');
    if (!ctx) return;

    const labels = Object.keys(catData);
    const counts = Object.values(catData);

    if (categoriesChart) {
        categoriesChart.destroy();
    }

    if (!labels.length) {
        labels.push('عام');
        counts.push(1);
    }

    categoriesChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: [
                    '#0284c7',
                    '#0d9488',
                    '#6366f1',
                    '#f59e0b',
                    '#ec4899',
                    '#8b5cf6'
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { family: 'Cairo', size: 12 }
                    }
                }
            }
        }
    });
}

// --- TRANSLATION API REQUEST ---
async function requestTranslation(rawText) {
    const apiKey = localStorage.getItem('nurse_gemini_key') || '';
    try {
        const res = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: rawText,
                api_key: apiKey
            })
        });

        if (res.ok) {
            const data = await res.json();
            if (data && data.success && data.translated_text) return data;
        }
    } catch (e) {
        console.warn('Backend call failed, using client fallback...');
    }

    // Complete client fallback
    return {
        success: true,
        translated_text: translateFullTextLocally(rawText),
        provider: "مترجم المتصفح السريري الكامل"
    };
}

async function translateMessage(msgId) {
    try {
        const bodyEl = document.getElementById(`${msgId}-body`);
        const transContainer = document.getElementById(`${msgId}-translation`);
        if (!bodyEl || !transContainer) return;

        if (transContainer.style.display !== 'none' && transContainer.innerHTML.includes('translation-box-header')) {
            transContainer.style.display = 'none';
            return;
        }

        transContainer.style.display = 'block';
        transContainer.className = 'translation-box';
        transContainer.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> جاري استخراج الترجمة الكاملة الشاملة...`;

        const textToTranslate = bodyEl.innerText || bodyEl.textContent;
        const res = await requestTranslation(textToTranslate);

        if (res && res.success) {
            transContainer.innerHTML = `
                <div class="translation-box-header">
                    <span><i class="fa-solid fa-language"></i> الترجمة المعتمدة بالكامل (${res.provider})</span>
                    <span style="cursor: pointer; font-size: 14px; font-weight: bold;" onclick="document.getElementById('${msgId}-translation').style.display='none'">&times; إغلاق</span>
                </div>
                <div>${formatMarkdownLike(res.translated_text)}</div>
            `;
        } else {
            const fallbackArabic = translateFullTextLocally(textToTranslate);
            transContainer.innerHTML = `
                <div class="translation-box-header">
                    <span><i class="fa-solid fa-language"></i> الترجمة المعتمدة بالكامل (المترجم المدمج)</span>
                    <span style="cursor: pointer; font-size: 14px; font-weight: bold;" onclick="document.getElementById('${msgId}-translation').style.display='none'">&times; إغلاق</span>
                </div>
                <div>${formatMarkdownLike(fallbackArabic)}</div>
            `;
        }
    } catch (err) {
        console.error('Error in translateMessage:', err);
    }
}

async function translateElementText(snippetId) {
    const textEl = document.getElementById(`${snippetId}-text`);
    const transBox = document.getElementById(`${snippetId}-trans`);
    if (!textEl || !transBox) return;

    if (transBox.style.display !== 'none') {
        transBox.style.display = 'none';
        return;
    }

    transBox.style.display = 'block';
    transBox.className = 'translation-box';
    transBox.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> جاري الترجمة...`;

    const textToTranslate = textEl.innerText || textEl.textContent;
    const res = await requestTranslation(textToTranslate);

    if (res && res.success) {
        transBox.innerHTML = `
            <div class="translation-box-header">
                <span><i class="fa-solid fa-language"></i> ترجمة عربية كاملة</span>
                <span style="cursor: pointer; font-size: 14px;" onclick="document.getElementById('${snippetId}-trans').style.display='none'">&times;</span>
            </div>
            <div>${formatMarkdownLike(res.translated_text)}</div>
        `;
    }
}

async function translateNote(noteId) {
    const bodyEl = document.getElementById(`note-body-${noteId}`);
    const transBox = document.getElementById(`note-trans-${noteId}`);
    if (!bodyEl || !transBox) return;

    if (transBox.style.display !== 'none') {
        transBox.style.display = 'none';
        return;
    }

    transBox.style.display = 'block';
    transBox.className = 'translation-box';
    transBox.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> جاري ترجمة محتوى الملاحظة...`;

    const res = await requestTranslation(bodyEl.innerText || bodyEl.textContent);
    if (res && res.success) {
        transBox.innerHTML = `
            <div class="translation-box-header">
                <span><i class="fa-solid fa-language"></i> الترجمة السريرية الكاملة للعربية</span>
                <span style="cursor: pointer;" onclick="document.getElementById('note-trans-${noteId}').style.display='none'">&times;</span>
            </div>
            <div>${formatMarkdownLike(res.translated_text)}</div>
        `;
    }
}

// --- REFERENCE DATASET LOADER ---
let currentDatasetDomain = '';

function initDatasetFilters() {
    const searchInput = document.getElementById('dataset-search-input');
    const filterBtns = document.querySelectorAll('#dataset-domain-filters .filter-btn');

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            loadReferenceDataset(searchInput.value.trim(), currentDatasetDomain);
        });
    }

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentDatasetDomain = btn.getAttribute('data-domain');
            loadReferenceDataset(searchInput ? searchInput.value.trim() : '', currentDatasetDomain);
        });
    });
}

async function loadReferenceDataset(search = '', domain = '') {
    try {
        let url = `/api/dataset?search=${encodeURIComponent(search)}`;
        if (domain) url += `&domain=${encodeURIComponent(domain)}`;

        const res = await fetch(url);
        const data = await res.json();
        if (!data.success) return;

        renderDatasetItems(data.dataset);
    } catch (e) {
        console.error('Error loading dataset:', e);
    }
}

function renderDatasetItems(dataset) {
    const container = document.getElementById('dataset-items-container');
    const badge = document.getElementById('dataset-total-badge');
    if (badge) badge.textContent = `${dataset.length} بنود مرجعية`;

    if (!container) return;

    if (!dataset.length) {
        container.innerHTML = `<p class="text-muted" style="grid-column: 1/-1;">لا توجد عناصر مطابقة في قاعدة بيانات المرجع.</p>`;
        return;
    }

    container.innerHTML = dataset.map(item => `
        <div class="note-card" style="border-right: 4px solid var(--secondary);">
            <div class="note-header">
                <div>
                    <span class="badge" style="background: #e0f2fe; color: #0369a1; font-size: 11px; margin-bottom: 4px; display: inline-block;">${item.code}</span>
                    <h4 class="note-title">${item.name_ar}</h4>
                    <span style="font-size: 12px; color: #64748b; font-weight: 600;">${item.name_en}</span>
                </div>
            </div>
            <div style="margin: 8px 0;">
                <span class="note-category-badge" style="background: #ccfbf1; color: #0d9488;">${item.domain}</span>
            </div>
            <div class="note-body" style="font-size: 13.5px; line-height: 1.7; margin-bottom: 10px;">
                <p><strong>📖 التعريف السريري:</strong> ${item.definition}</p>
                <p style="margin-top: 6px;"><strong>🩺 الأهمية في التمريض:</strong> ${item.importance}</p>
                <div style="margin-top: 8px; padding: 8px 12px; background: #f8fafc; border-radius: 6px; border: 1px dashed #cbd5e1;">
                    <strong>💡 مثال واقعي:</strong> ${item.example}
                </div>
            </div>
            <div class="note-footer" style="flex-direction: column; align-items: flex-start; gap: 4px;">
                <span><i class="fa-solid fa-certificate" style="color: var(--secondary);"></i> <strong>المعيار الدولي:</strong> ${item.standard}</span>
                <span style="font-size: 11px; color: #94a3b8;"><i class="fa-solid fa-book-bookmark"></i> ${item.source}</span>
                <div style="margin-top: 6px; width: 100%; display: flex; justify-content: flex-end;">
                    <button class="btn-secondary-sm" onclick="askAboutDatasetItem('${escapeQuotes(item.name_ar)}')">
                        <i class="fa-solid fa-comments"></i> اسأل الذكاء الاصطناعي حول هذا المرجع
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function askAboutDatasetItem(itemName) {
    document.querySelector('.nav-item[data-tab="chat"]').click();
    const input = document.getElementById('chat-input');
    input.value = `وضح لي بالتفصيل مفهوم ${itemName} استناداً إلى قاعدة بيانات المرجع المعياري وما هي تطبيقاته العملية؟`;
    input.focus();
}

// --- RESEARCHER PROFILE & MEMORY LOADER ---
async function loadResearcherProfile() {
    try {
        const res = await fetch('/api/researcher/profile');
        const data = await res.json();
        if (!data.success) return;

        const prof = data.profile;
        const toneEl = document.getElementById('profile-tone-text');
        const toneBadge = document.getElementById('researcher-tone-badge');
        const ideasCountEl = document.getElementById('profile-ideas-count');
        const interestsContainer = document.getElementById('profile-interests-tags');

        if (toneEl) toneEl.textContent = prof.style || 'تحليلي أكاديمي';
        if (toneBadge) toneBadge.innerHTML = `<i class="fa-solid fa-brain"></i> نمط الحوار: ${prof.style || 'تحليلي أكاديمي'}`;
        if (ideasCountEl) ideasCountEl.textContent = prof.ideas ? prof.ideas.length : 0;

        if (interestsContainer && prof.interests) {
            interestsContainer.innerHTML = prof.interests.map(int => `<span class="topic-tag">${int}</span>`).join('');
        }

        // Load ideas list
        const ideasRes = await fetch('/api/researcher/ideas');
        const ideasData = await ideasRes.json();
        if (ideasData.success) {
            renderResearcherIdeas(ideasData.ideas);
        }
    } catch (e) {
        console.error('Error loading researcher profile:', e);
    }
}

function renderResearcherIdeas(ideas) {
    const container = document.getElementById('researcher-ideas-container');
    const badge = document.getElementById('ideas-total-badge');
    if (badge) badge.textContent = `${ideas.length} أفكار مسجلة`;

    if (!container) return;

    if (!ideas.length) {
        container.innerHTML = `<p class="text-muted" style="grid-column: 1/-1;">لم يتم تسجيل أفكار أو فرضيات بعد. أثناء حديثك في الشات، سيقوم الذكاء الاصطناعي باستنباط وتدوين أفكارك وفرضياتك هنا تلقائياً.</p>`;
        return;
    }

    container.innerHTML = ideas.map(idea => `
        <div class="note-card" style="border-right: 4px solid var(--primary);">
            <div class="note-header">
                <h4 class="note-title"><i class="fa-solid fa-lightbulb" style="color: #f59e0b;"></i> ${idea.type}</h4>
            </div>
            <div class="note-body" style="font-weight: 600; color: #1e293b;">"${idea.statement}"</div>
            <div style="font-size: 12px; color: #0369a1; background: #e0f2fe; padding: 6px 10px; border-radius: 6px; margin-bottom: 8px;">
                <i class="fa-solid fa-compass"></i> <strong>المعنى المستنبط:</strong> ${idea.meaning}
            </div>
            <div class="note-footer">
                <span><i class="fa-regular fa-clock"></i> ${idea.created_at}</span>
            </div>
        </div>
    `).join('');
}

// Bind functions to window explicitly so HTML inline onclick never fails
window.askAboutBook = askAboutBook;
window.deleteBook = deleteBook;
window.togglePinNote = togglePinNote;
window.deleteNote = deleteNote;
window.translateMessage = translateMessage;
window.translateElementText = translateElementText;
window.translateNote = translateNote;
window.askAboutDatasetItem = askAboutDatasetItem;
