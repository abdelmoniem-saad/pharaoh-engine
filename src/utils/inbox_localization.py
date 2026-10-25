"""Deterministic display translations for saved inbox templates.

The stored message and action metadata remain untouched. Unknown prose is retained
and flagged, never guessed or replaced by a summary. Works on existing saves.
"""
from dataclasses import dataclass
import re
from string import Formatter
from src.utils.localization import get_language


@dataclass(frozen=True)
class MessageDisplay:
    subject: str
    body: str
    has_original_text: bool = False


# English source template -> reviewed Arabic template. Placeholders preserve facts.
CATALOG = {
    "Daily Report — {date}": "التقرير اليومي — {date}",
    "Weekly Training Report": "تقرير التدريب الأسبوعي",
    "Weekly Board Brief": "تقرير الإدارة الأسبوعي",
    "Monthly Financial Report": "التقرير المالي الشهري",
    "Press Conference Report": "تقرير المؤتمر الصحفي",
    "Board Objectives": "أهداف الإدارة",
    "Promise Update": "تحديث الوعود",
    "Ramadan Mubarak": "رمضان مبارك",
    "Season Over!": "انتهى الموسم!",
    "MEDICAL ROOM": "العيادة الطبية",
    "FITNESS WATCH": "متابعة اللياقة",
    "SUSPENDED": "الموقوفون",
    "LOOKING AHEAD": "المواعيد المقبلة",
    "DEVELOPMENT PLANS": "خطط التطوير",
    "Clean bill of health — everyone trained this morning.": "الجميع بصحة جيدة وشاركوا في تدريب هذا الصباح.",
    "{player} — out ~{days}d": "{player} — يغيب نحو {days} يوم",
    "…plus {count} more in treatment": "و{count} لاعبين آخرين يتلقون العلاج",
    "{player} — {fitness}% condition": "{player} — اللياقة {fitness}%",
    "{player} — {count} match(es)": "{player} — الإيقاف {count} مباراة",
    "Next: {home} v {away} ({competition}) — in {days} day(s)": "المباراة المقبلة: {home} ضد {away} ({competition}) — بعد {days} يوم",
    "Next: {home} v {away} ({competition}) — TODAY": "المباراة المقبلة: {home} ضد {away} ({competition}) — اليوم",
    "Contract talks due: {players}": "حان موعد التفاوض على عقود: {players}",
    "{player} has recovered from injury and is available for selection.": "تعافى {player} من الإصابة وأصبح متاحاً للاختيار.",
    "{player} has served their suspension and is available for selection.": "أنهى {player} إيقافه وأصبح متاحاً للاختيار.",
    "{player} Recovered!": "تعافى {player}!",
    "{player} Available": "{player} متاح للاختيار",
    "Weekly board review for {club}": "مراجعة الإدارة الأسبوعية لنادي {club}",
    "League position: {position}/{teams}": "ترتيب الدوري: {position} من {teams}",
    "Expectation: {expectation}": "التوقعات: {expectation}",
    "Confidence: {score}/100 ({level})": "ثقة الإدارة: {score} من ١٠٠ ({level})",
    "Objective Track:": "متابعة الأهداف:",
    "No active board objectives recorded.": "لا توجد أهداف مسجلة للإدارة حالياً.",
    "Board Summary: {a} Achieved, {b} On Track, {c} At Risk, {d} Off Track": "ملخص الإدارة: {a} محقق، {b} على المسار، {c} معرض للخطر، {d} بعيد عن الهدف",
    "Active Promises:": "الوعود الحالية:",
    "{description} (Progress: {progress}/{target}, Deadline Matchday: {deadline})": "{description} (التقدم: {progress} من {target}، الموعد النهائي: الجولة {deadline})",
    "Monthly finances: {net} EGP (Income: {income}, Expenses: {expenses})": "الحساب الشهري: {net} جنيه (الإيرادات: {income}، المصروفات: {expenses})",
    "Monthly finances: {net} EGP (Income: {income}, Expenses: {expenses}) ⚠️": "الحساب الشهري: {net} جنيه (الإيرادات: {income}، المصروفات: {expenses}) ⚠️",
    "Matchday {day} Round-Up": "حصاد الجولة {day}",
    "Results:": "النتائج:",
    "Table Snapshot:": "لمحة عن الترتيب:",
    "Big Results:": "نتائج بارزة:",
    "Goals:": "الأهداف:",
    "{goals} goals scored across {matches} matches ({average} per game)": "سُجل {goals} هدفاً في {matches} مباريات ({average} هدف لكل مباراة)",
    "{club} with a dominant {score} display!": "أداء قوي من {club} بنتيجة {score}!",
    "Possession: {home}% - {away}%": "الاستحواذ: {home}% - {away}%",
    "Shots: {home} ({home_target} on target) vs {away} ({away_target} on target)": "التسديدات: {home} ({home_target} على المرمى) مقابل {away} ({away_target} على المرمى)",
    "Cards: {cards}": "البطاقات: {cards}",
    "{player} was injured ({minute}')": "أُصيب {player} (الدقيقة {minute})",
    "Man of the Match: {player} ({rating})": "رجل المباراة: {player} ({rating})",
    "A comprehensive victory that will delight the fans.": "فوز كبير يسعد الجماهير.",
    "A dominant display from start to finish.": "سيطرة على المباراة من بدايتها إلى نهايتها.",
    "The team showed their class with a ruthless performance.": "أظهر الفريق جودته بأداء حاسم.",
    "A hard-earned three points that keeps the momentum going.": "ثلاث نقاط مستحقة تحافظ على الزخم.",
    "Not always pretty, but the result is what matters.": "لم يكن الأداء ممتعاً دائماً، لكن النتيجة هي الأهم.",
    "A professional performance to take all three points.": "أداء منضبط منح الفريق النقاط الثلاث.",
    "A point gained or two dropped? The debate will rage on.": "نقطة مكتسبة أم نقطتان ضائعتان؟ الجدل مستمر.",
    "The team will feel they could have done more today.": "سيشعر الفريق أنه كان قادراً على تقديم المزيد اليوم.",
    "A fair result in the end, though chances were there.": "نتيجة عادلة في النهاية رغم الفرص المتاحة.",
    "The manager will have plenty to think about after this one.": "أمام المدير الفني الكثير ليراجعه بعد هذه المباراة.",
    "A setback, but there's time to recover.": "تعثر، لكن ما زال هناك وقت للتعويض.",
    "Tough questions will be asked after this defeat.": "تنتظر الفريق أسئلة صعبة بعد هذه الهزيمة.",
    "A performance the players will want to forget quickly.": "أداء سيسعى اللاعبون إلى نسيانه سريعاً.",
    "The dressing room will be a tough place after this.": "أجواء صعبة تنتظر غرفة الملابس.",
    "Serious concerns for the manager after this hammering.": "مخاوف كبيرة لدى المدير الفني بعد هذه الهزيمة الثقيلة.",
    "Offer Sent: {player}": "تم إرسال عرض لضم {player}",
    "Revised Offer Sent: {player}": "تم إرسال عرض معدل لضم {player}",
    "Personal Terms Sent: {player}": "تم إرسال عرض العقد إلى {player}",
    "Fee Agreed: {player}": "تم الاتفاق على مقابل انتقال {player}",
    "Transfer Complete: {player}": "اكتمل انتقال {player}",
    "Wage Rejected: {player}": "رفض {player} عرض الراتب",
    "Deal Collapsed: {player}": "فشلت صفقة {player}",
    "Counter: {player} — {amount} EGP": "عرض مقابل لضم {player} — {amount} جنيه",
    "Offer for {player} from {club}": "عرض لضم {player} من {club}",
    "You submitted a transfer offer of {amount} EGP for {player}.": "قدمت عرض انتقال بقيمة {amount} جنيه لضم {player}.",
    "Valuation guide: {amount} EGP": "القيمة التقديرية: {amount} جنيه",
    "You revised your bid from {old} EGP to {new} EGP.": "عدلت عرضك من {old} إلى {new} جنيه.",
    "You offered {amount} EGP/week to {player}.": "عرضت راتباً أسبوعياً قدره {amount} جنيه على {player}.",
    "{club} have accepted your offer of {amount} EGP for {player}!": "وافق {club} على عرضك بقيمة {amount} جنيه لضم {player}!",
    "You now need to agree personal terms with the player.": "تحتاج الآن إلى الاتفاق على شروط العقد مع اللاعب.",
    "Go to Transfer Market → 📋 Negotiations to offer wages.": "افتح سوق الانتقالات ثم المفاوضات لتقديم عرض الراتب.",
    "Personal terms can be agreed over multiple rounds.": "يمكن الاتفاق على شروط العقد عبر عدة جولات من التفاوض.",
    "{club} have ended negotiations for {player}.": "أنهى {club} مفاوضات انتقال {player}.",
    "Your final offer of {amount} EGP was not enough.": "لم يكن عرضك النهائي البالغ {amount} جنيه كافياً.",
    "Their valuation: {amount} EGP.": "تقييم النادي للاعب: {amount} جنيه.",
    "{club} have rejected your offer of {amount} EGP for {player}.": "رفض {club} عرضك البالغ {amount} جنيه لضم {player}.",
    "They counter-offer: {amount} EGP": "العرض المقابل: {amount} جنيه",
    "(Attempt {attempt}/{max}; {left} attempt(s) left after this)": "المحاولة {attempt} من {max}؛ يتبقى بعدها {left} محاولات",
    "Go to Transfer Market → 📋 Negotiations to respond.": "افتح سوق الانتقالات ثم المفاوضات للرد.",
    "{player} has agreed personal terms!": "وافق {player} على شروط العقد!",
    "Transfer fee: {amount} EGP": "مقابل الانتقال: {amount} جنيه",
    "Weekly wage: {amount} EGP": "الراتب الأسبوعي: {amount} جنيه",
    "The transfer is complete. Welcome to the squad!": "اكتمل الانتقال. أهلاً باللاعب في الفريق!",
    "{player} has rejected your wage offer of {amount} EGP/wk.": "رفض {player} عرض راتبك البالغ {amount} جنيه أسبوعياً.",
    "The player wants at least {amount} EGP/wk.": "يريد اللاعب {amount} جنيه أسبوعياً على الأقل.",
    "The transfer fee ({amount} EGP) is still agreed.": "ما زال الاتفاق على مقابل الانتقال ({amount} جنيه) قائماً.",
    "Go to Transfer Market → 📋 Negotiations to revise your offer.": "افتح سوق الانتقالات ثم المفاوضات لتعديل عرضك.",
    "Keep terms competitive to avoid missing the window.": "قدم شروطاً مناسبة لإتمام الصفقة قبل إغلاق فترة الانتقالات.",
    "{count} Contract(s) Expiring": "{count} عقود تقترب من الانتهاء",
    "The following players have contracts expiring soon:": "عقود اللاعبين الآتية أسماؤهم تقترب من الانتهاء:",
    "{player} ({position}) — {days} days remaining": "{player} ({position}) — يتبقى {days} يوم",
    "Consider renewing their contracts or risk losing them.": "فكر في تجديد عقودهم لتجنب رحيلهم.",
    "{player} Renews Contract!": "جدد {player} عقده!",
    "{player} Rejects Renewal": "رفض {player} تجديد عقده",
    "{player} has agreed a new {years}-year deal worth {amount} EGP/week. The player is delighted.": "وافق {player} على عقد جديد لمدة {years} سنوات براتب {amount} جنيه أسبوعياً. اللاعب سعيد بالاتفاق.",
    "Season {years} Begins!": "بداية موسم {years}!",
    "Welcome to the new season, {manager}. Pre-season is underway.": "مرحباً بالموسم الجديد يا {manager}. بدأت فترة الإعداد.",
    "Egypt Cup Draw Announced": "إعلان قرعة كأس مصر",
    "Egypt Cup {round} Draw": "قرعة كأس مصر — {round}",
    "The {round} draw has been made:": "أُجريت قرعة {round}:",
    "Egypt Cup Champions: {club}": "بطل كأس مصر: {club}",
    "{club} have lifted the Egypt Cup trophy! A magnificent achievement in the knockout tournament.": "تُوج {club} بكأس مصر! إنجاز رائع في البطولة.",
    "Season complete! {club} are champions with {points} points!": "انتهى الموسم! تُوج {club} بطلاً برصيد {points} نقطة!",
    "Welcome to Pharaoh Engine!": "مرحباً بك في محرك الفراعنة!",
    "Welcome, {manager}!": "أهلاً بك يا {manager}!",
    "Your journey as a manager in the Egyptian Premier League begins now. Good luck!": "تبدأ الآن رحلتك مديراً فنياً في الدوري المصري الممتاز. بالتوفيق!",
    "The board expects you to achieve the following this season:": "تنتظر الإدارة منك تحقيق الأهداف التالية هذا الموسم:",
    "Good luck!": "بالتوفيق!",
    "Season Target: {target}": "هدف الموسم: {target}",
    "{target} (critical)": "{target} (حاسم)",
    "Score {goals}+ league goals (medium)": "تسجيل {goals} هدفاً أو أكثر في الدوري (متوسط الأهمية)",
    "{player}: {attribute} +{gain} (now {value})": "{player}: {attribute} +{gain} (أصبحت {value})",
    "{player} picked up a {injury} injury in training! Out for {days} days.": "أُصيب {player} بـ{injury} في التدريب! سيغيب {days} يوماً.",
    "Q: Were you disappointed not to win today?": "س: هل شعرت بخيبة أمل لعدم الفوز اليوم؟",
    "Manager's response: \"The referee cost us the game.\"": "رد المدير الفني: «قرارات الحكم كلفتنا المباراة».",
    "Fans responded positively.": "كان رد فعل الجماهير إيجابياً.",
    "The board were not impressed.": "لم يلق ذلك إعجاب الإدارة.",
    "Community Outreach": "التواصل المجتمعي",
    "The local municipality is organizing a football festival and has invited your players to attend and coach kids.": "تنظم البلدية مهرجاناً لكرة القدم ودعت لاعبيك للمشاركة وتدريب الأطفال.",
    "Your decision: Send some players": "قرارك: إرسال بعض اللاعبين",
    "The event was a huge hit! Players enjoyed connecting with the community. 🏘️": "حققت الفعالية نجاحاً كبيراً! استمتع اللاعبون بالتواصل مع المجتمع. 🏘️",
    "{club} demolish {opponent} in stunning display!": "{club} يكتسح {opponent} بأداء مذهل!",
    "Dominant {club} cruise past {opponent}!": "{club} يتفوق على {opponent} بأداء مسيطر!",
    "{club} send a statement with emphatic victory!": "{club} يوجه رسالة قوية بانتصار كبير!",
    "Ruthless {club} put {opponent} to the sword!": "{club} يحسم المواجهة أمام {opponent} بلا رحمة!",
    "{club} edge past {opponent} in tight affair": "{club} يتجاوز {opponent} في مواجهة متقاربة",
    "Hard-fought victory for {club} against {opponent}": "انتصار صعب لـ{club} على {opponent}",
    "{club} grab all three points against resilient {opponent}": "{club} ينتزع النقاط الثلاث أمام {opponent} العنيد",
    "Late drama as {club} overcome {opponent}": "إثارة متأخرة تمنح {club} الفوز على {opponent}",
    "Honours even as {club} and {opponent} share the spoils": "تعادل بين {club} و{opponent} وتقاسم للنقاط",
    "{club} held to a draw by determined {opponent}": "{opponent} يفرض التعادل على {club}",
    "Neither side can find a winner in tense encounter": "لا غالب ولا مغلوب في مواجهة متوترة",
    "Stalemate between {club} and {opponent}": "تعادل بين {club} و{opponent}",
    "Disappointing day for {club} as {opponent} take the points": "يوم مخيب لـ{club} مع فوز {opponent} بالنقاط",
    "{club} suffer defeat at the hands of {opponent}": "{club} يتلقى الهزيمة أمام {opponent}",
    "Questions for {club} manager after loss to {opponent}": "تساؤلات لمدرب {club} بعد الخسارة أمام {opponent}",
    "{club} fall short against resolute {opponent}": "{club} يعجز عن تجاوز {opponent}",
    "Crisis at {club} after humiliating defeat to {opponent}!": "أزمة في {club} بعد هزيمة ثقيلة أمام {opponent}!",
    "{club} capitulate in shocking loss to {opponent}!": "انهيار {club} في خسارة صادمة أمام {opponent}!",
    "Manager under pressure after {club}'s dismal showing against {opponent}!": "ضغوط على المدرب بعد أداء {club} الضعيف أمام {opponent}!",
    "Nightmare for {club} as {opponent} run riot!": "ليلة صعبة على {club} مع تألق {opponent}!"
}

def _compile(template):
    parts = []
    for literal, field, spec, conversion in Formatter().parse(template):
        parts.append(re.escape(literal))
        if field:
            parts.append("(?P<" + field + ">.+?)")
    return re.compile("^" + "".join(parts) + "$")


def entity_names(conn):
    names = {}
    for table in ("players", "clubs"):
        for row in conn.execute(f"SELECT name, name_ar FROM {table} WHERE name_ar != ''"):
            names[row[0]] = row[1]
    for row in conn.execute("SELECT short_name, name_ar FROM clubs WHERE name_ar != ''"):
        if row[0]:
            names[row[0]] = row[1]
    return names


def localize_message(msg, conn=None, language=None, names=None):
    if (language or get_language()) != "ar":
        return MessageDisplay(msg.subject, visible_body(msg.body))
    names = names if names is not None else entity_names(conn) if conn is not None else {}
    subject, subject_missing = translate_text(msg.subject, names)
    body, body_missing = translate_text(visible_body(msg.body), names)
    return MessageDisplay(subject, body, subject_missing or body_missing)


def visible_body(body):
    # Internal action payloads are parsed from the original message by the UI.
    return "\n".join(line for line in body.splitlines()
        if not re.match(r"^(TRANSFER_OFFER|FEE_AGREED|COUNTER_OFFER|WAGE_REJECTED)\|", line.strip()))


def translate_text(text, names=None, _depth=0):
    names = names or {}
    def values(value, nested=True):
        if nested and _depth < 4:
            value = translate_text(value, names, _depth + 1)[0]
        for source, target in sorted(names.items(), key=lambda pair: len(pair[0]), reverse=True):
            value = value.replace(source, target)
        for source, target in sorted(TERMS.items(), key=lambda pair: len(pair[0]), reverse=True):
            value = re.sub(r"(?<![A-Za-z])" + re.escape(source) + r"(?![A-Za-z])", lambda m: target, value)
        return value
    output, missing = [], False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            output.append("")
            continue
        # Decorative bullets/emoji are independent from the editorial sentence.
        prefix = re.match(r"^[^\w\u0600-\u06ff]+", line)
        prefix = prefix.group(0) if prefix else ""
        prose = line[len(prefix):]
        translated = None
        for candidate in dict.fromkeys((line, prose)):
            for pattern, target in PATTERNS:
                match = pattern.fullmatch(candidate)
                if match:
                    translated_values = {k: values(v) for k,v in match.groupdict().items()}
                    missing |= any(re.search(r"[A-Za-z]{2,}", v) is not None
                                   for k, v in translated_values.items()
                                   if k not in {"manager", "name", "player", "players", "club", "home", "away"})
                    translated = target.format(**translated_values)
                    if candidate == line:
                        prefix = ""
                    break
            if translated is not None:
                break
        if translated is None:
            translated = values(prose, nested=False)
            # Numeric result/player lines are factual data, not untranslated prose.
            remaining = prose
            for name in names:
                remaining = remaining.replace(name, "")
            for term in TERMS:
                remaining = re.sub(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", "", remaining)
            missing |= bool(re.search(r"[A-Za-z]{2,}", remaining))
        output.append(prefix + translated)
    return "\n".join(output), missing


TERMS = {
    "Ecstatic": "سعيد للغاية", "Happy": "سعيد", "Content": "راضٍ", "Unsettled": "قلق", "Unhappy": "غير سعيد", "Furious": "غاضب",
    "wants to leave — no playing time": "يريد الرحيل بسبب غياب المشاركة", "wants more playing time": "يريد مشاركة أكبر",
    "injured": "مصاب", "suspended": "موقوف",
    "Fee": "المقابل المالي", "Personal Terms": "الشروط الشخصية",
    "Untouchable": "راسخة", "Secure": "آمنة", "Uncertain": "مترددة",
    "Under Pressure": "تحت الضغط", "On the Brink": "على حافة الإقالة",
    "Top 4 Finish": "إنهاء الموسم ضمن الأربعة الأوائل", "Top Half Finish": "إنهاء الموسم في النصف الأعلى",
    "Mid-Table Finish": "إنهاء الموسم في وسط الجدول", "high": "مهم", "medium": "متوسط الأهمية", "low": "منخفض الأهمية",
    "Hamstring": "العضلة الخلفية", "Ankle": "الكاحل", "Knee": "الركبة", "Groin": "العضلة الضامة",
    "Calf": "السمانة", "Thigh": "الفخذ", "Shoulder": "الكتف", "Back": "الظهر", "Concussion": "ارتجاج",
    "GK": "حارس", "CB": "قلب دفاع", "LB": "ظهير أيسر", "RB": "ظهير أيمن", "CDM": "ارتكاز",
    "CM": "وسط", "CAM": "وسط هجومي", "LM": "وسط أيسر", "RM": "وسط أيمن", "LW": "جناح أيسر", "RW": "جناح أيمن", "ST": "مهاجم",
    "Finisher": "الهداف", "Playmaker": "صانع اللعب", "Engine": "اللياقة", "Rock": "الصخرة الدفاعية", "Speedster": "السرعة",
    "finisher": "الهداف", "playmaker": "صانع اللعب", "engine": "اللياقة", "rock": "الصخرة الدفاعية", "speedster": "السرعة",
    "conv_st": "التحول لمهاجم", "conv_cdm": "التحول لارتكاز", "conv_cb": "التحول لقلب دفاع", "conv_cm": "التحول لوسط",
    "Stable": "مستقرة",
    "hamstring": "شد في العضلة الخلفية", "ankle": "إصابة في الكاحل", "knee": "إصابة في الركبة",
    "Egyptian Premier League": "الدوري المصري الممتاز", "Egypt Cup": "كأس مصر",
    "TODAY": "اليوم", "Goals": "الأهداف", "Cards": "البطاقات", "Results": "النتائج",
    "Tech": "فنية", "Phys": "بدنية", "Mental": "ذهنية", "Def": "دفاعية",
    "pace": "السرعة", "shooting": "التسديد", "passing": "التمرير", "dribbling": "المراوغة",
    "tackling": "الافتكاك", "marking": "الرقابة", "stamina": "التحمل", "strength": "القوة",
    "heading": "ضربات الرأس", "positioning": "التمركز", "vision": "الرؤية", "composure": "الهدوء",
    "reflexes": "رد الفعل", "handling": "الإمساك", "finishing": "الإنهاء", "crossing": "العرضيات",
    "agility": "الرشاقة", "acceleration": "التسارع", "balance": "التوازن", "jumping": "القفز",
    "work_rate": "معدل العمل", "determination": "الإصرار", "leadership": "القيادة",
    "aggression": "الاندفاع", "anticipation": "التوقع", "decisions": "القرارات",
    "flair": "المهارة", "teamwork": "اللعب الجماعي", "concentration": "التركيز",
    "first_touch": "اللمسة الأولى", "long_shots": "التسديد البعيد", "free_kicks": "الركلات الحرة",
    "penalties": "ركلات الجزاء", "kicking": "الركل", "one_on_one": "الانفرادات",
    "Confident": "واثقة", "Satisfied": "راضية", "Delighted": "سعيدة جداً", "Concerned": "قلقة",
    "Win the League": "الفوز بالدوري", "Title Challenge": "المنافسة على اللقب",
    "Top Half": "النصف الأعلى", "Avoid Relegation": "تجنب الهبوط", "Mid Table": "وسط الجدول",
    "Balanced": "متوازن", "Shooting": "التسديد", "Defending": "الدفاع", "Physical": "بدني",
    "Playmaking": "صناعة اللعب", "Goalkeeping": "حراسة المرمى", "Set Pieces": "الكرات الثابتة",
    "Jan": "يناير", "Feb": "فبراير", "Mar": "مارس", "Apr": "أبريل", "May": "مايو", "Jun": "يونيو",
    "Jul": "يوليو", "Aug": "أغسطس", "Sep": "سبتمبر", "Oct": "أكتوبر", "Nov": "نوفمبر", "Dec": "ديسمبر",
    "EGP/week": "جنيه/أسبوع", "EGP/wk": "جنيه/أسبوع", "EGP": "جنيه", "pts": "نقطة", "GD": "فارق الأهداف",
    "assist": "صناعة", "Round of 32": "دور الـ٣٢", "Round of 16": "دور الـ١٦",
    "Quarter-finals": "ربع النهائي", "Semi-finals": "نصف النهائي", "Final": "النهائي",
}


from src.utils.news_ar import CATALOG as NEWS_CATALOG
CATALOG.update(NEWS_CATALOG)
PATTERNS = [(_compile(source), target) for source, target in CATALOG.items()]


def display_news(text, conn=None):
    """Use the same catalog for live dialogs and archived messages."""
    return translate_text(text, entity_names(conn) if conn else {})[0] if get_language() == 'ar' else text
