"""
Match commentary — varied, atmospheric text templates for match events.
"""
from __future__ import annotations

from src.utils.config import MatchEventType
from src.utils import rng


TEMPLATES: dict[MatchEventType, list[str]] = {
    MatchEventType.GOAL: [
        "GOAL! {player} scores for {club}! The stadium erupts!",
        "What a finish from {player}! {club} hit the net!",
        "{player} slots it home! That's another goal for {club}!",
        "He's done it! {player} finds the back of the net for {club}!",
        "Clinical finish from {player}! {club} celebrate!",
        "The ball ripples the net! {player} makes no mistake for {club}!",
        "{player} with an ice-cold finish! {club} take the lead!",
        "GOLAZO! {player} scores a beauty for {club}!",
        "The fans go wild! {player} has scored for {club}!",
        "A moment of magic from {player}! The net bulges for {club}!",
        "{player} buries it! What a moment for {club}!",
        "Unstoppable! {player} fires in for {club}!",
    ],
    MatchEventType.SHOT_ON_TARGET: [
        "{player} forces a save from the goalkeeper!",
        "Good effort from {player}, but the keeper is equal to it.",
        "{player} tests the keeper with a powerful strike!",
        "A fine save denies {player}!",
        "{player} gets a shot away — saved!",
        "The keeper dives to his right to deny {player}!",
        "Close! {player} strikes it well but the keeper holds firm.",
        "Great reflexes from the keeper to keep out {player}'s effort!",
    ],
    MatchEventType.SHOT_OFF_TARGET: [
        "{player} fires wide! A chance goes begging.",
        "Off target from {player}. That should have been better.",
        "{player} blazes it over the crossbar!",
        "The shot from {player} drifts harmlessly wide.",
        "{player} pulls the trigger but it's off the mark.",
        "Just wide! {player} will be disappointed with that.",
        "{player} drags his shot wide of the far post.",
        "Over the bar from {player}! He'll want that one back.",
    ],
    MatchEventType.YELLOW_CARD: [
        "Yellow card for {player}. The referee reaches for his pocket.",
        "{player} goes into the book. A cynical challenge.",
        "The referee shows {player} a yellow card for that foul.",
        "A caution for {player}. He needs to be careful now.",
        "That's a booking for {player}. He was lucky not to see red.",
        "{player} is booked for a reckless tackle. Tension rising.",
    ],
    MatchEventType.RED_CARD: [
        "RED CARD! {player} is sent off! {club} are down to 10 men!",
        "A straight red for {player}! That's a terrible challenge!",
        "{player} sees red! {club} will have to play the rest with 10!",
        "The referee has no choice! Red card for {player} of {club}!",
    ],
    MatchEventType.CORNER: [
        "Corner kick for {club}.",
        "{club} win a corner. The ball is swung in...",
        "Another corner for {club}. Can they make it count?",
        "{club} have a corner. Players flooding the box.",
    ],
    MatchEventType.INJURY: [
        "{player} goes down holding his leg! The physio is on the pitch.",
        "Bad news for {club} — {player} is injured and can't continue.",
        "{player} limps off in pain. That doesn't look good at all.",
        "Concern for {club} as {player} goes down clutching his {detail}.",
        "The stretcher is called for {player}. He looks in real discomfort.",
        "{player} pulls up suddenly. The {detail} seems to be the problem.",
    ],
    MatchEventType.HALF_TIME: [
        "The referee blows for half time.",
        "That's the half-time whistle. Time for the managers to regroup.",
    ],
    MatchEventType.FULL_TIME: [
        "Full time! {home} {home_goals} - {away_goals} {away}",
        "It's all over! {home} {home_goals} - {away_goals} {away}",
        "The final whistle blows! {home} {home_goals} - {away_goals} {away}",
    ],
    MatchEventType.KICKOFF: [
        "The match kicks off!",
        "We're underway! The referee gets the match started.",
    ],
}

TEMPLATES_AR: dict[MatchEventType, list[str]] = {
    MatchEventType.GOAL: [
        "جووووووول! {player} يسجل لـ {club}! الملعب يهتز!",
        "يا لها من نهاية من {player}! {club} يمزق الشباك!",
        "{player} يسكنها الشباك! هدف آخر لـ {club}!",
        "لقد فعلها! {player} يجد طريق الشباك لـ {club}!",
        "نهاية متقنة من {player}! {club} يحتفلون!",
        "الكرة تمزق الشباك! {player} لا يخطئ لـ {club}!",
        "{player} ينهيها ببرودة أعصاب! {club} يأخذون الأسبقية!",
        "جولازو! {player} يسجل هدفا جميلا لـ {club}!",
        "الجماهير تشتعل! {player} سجل لـ {club}!",
        "لحظة سحرية من {player}! الشباك تهتز لـ {club}!",
        "{player} يسكنها الشباك! يا لها من لحظة لـ {club}!",
        "لا يصد! {player} يطلق قذيفة لـ {club}!",
    ],
    MatchEventType.SHOT_ON_TARGET: [
        "{player} يجبر الحارس على التصدي!",
        "محاولة جيدة من {player}، لكن الحارس كان في الموعد.",
        "{player} يختبر الحارس بتسديدة قوية!",
        "تصدي رائع يحرم {player}!",
        "{player} يسدد — وتصدي!",
        "الحارس يرتمي لليمين ليمنع {player}!",
        "قريبة! {player} يسددها جيدا لكن الحارس صامد.",
        "رد فعل رائع من الحارس ليمنع محاولة {player}!",
    ],
    MatchEventType.SHOT_OFF_TARGET: [
        "{player} يسدد بعيدا! فرصة تضيع.",
        "بعيدة عن المرمى من {player}. كان يجب أن تكون أفضل.",
        "{player} يطيح بها فوق العارضة!",
        "تسديدة من {player} تخرج بسلام بعيدا عن المرمى.",
        "{player} يسدد لكنها بعيدة عن المرمى.",
        "بجوار القائم! {player} سيكون محبطا من ذلك.",
        "{player} يسحب تسديدته بعيدا عن القائم البعيد.",
        "فوق العارضة من {player}! سيتمنى لو أعادها.",
    ],
    MatchEventType.YELLOW_CARD: [
        "بطاقة صفراء لـ {player}. الحكم يخرج البطاقة من جيبه.",
        "{player} يدخل سجل الانذارات. تدخل متهور.",
        "الحكم يشهر البطاقة الصفراء لـ {player} بسبب ذلك الخطأ.",
        "انذار لـ {player}. يجب عليه الحذر الآن.",
        "هذا انذار لـ {player}. كان محظوظا بعدم رؤية البطاقة الحمراء.",
        "{player} يحصل على انذار بسبب تدخل عنيف. التوتر يتصاعد.",
    ],
    MatchEventType.RED_CARD: [
        "بطاقة حمراء! طرد {player}! {club} سيكملون بـ 10 لاعبين!",
        "حمراء مباشرة لـ {player}! يا له من تدخل مروع!",
        "{player} يرى الأحمر! {club} سيلعبون البقية بـ 10!",
        "الحكم ليس لديه خيار! بطاقة حمراء لـ {player} لاعب {club}!",
    ],
    MatchEventType.CORNER: [
        "ركلة ركنية لـ {club}.",
        "{club} يحصل على ركنية. الكرة ستلعب داخل المنطقة...",
        "ركنية أخرى لـ {club}. هل يستغلونها؟",
        "{club} لديهم ركنية. اللاعبون يندفعون داخل منطقة الجزاء.",
    ],
    MatchEventType.INJURY: [
        "{player} يسقط على الأرض ممسكا بساقه! الطاقم الطبي يدخل الملعب.",
        "أخبار سيئة لـ {club} — {player} مصاب ولا يستطيع الإكمال.",
        "{player} يخرج وهو يعرج من الألم. لا يبدو الأمر جيدا على الإطلاق.",
        "قلق في {club} مع سقوط {player} ممسكا بـ {detail}.",
        "المحفة تطلب لـ {player}. يبدو في وضع غير مريح.",
        "{player} يتوقف فجأة. يبدو أن المشكلة في {detail}.",
    ],
    MatchEventType.HALF_TIME: [
        "الحكم يطلق صافرة نهاية الشوط الأول.",
        "صافرة نهاية الشوط الأول. وقت للمدربين لإعادة ترتيب الأوراق.",
    ],
    MatchEventType.FULL_TIME: [
        "نهاية المباراة! {home} {home_goals} - {away_goals} {away}",
        "انتهى كل شيء! {home} {home_goals} - {away_goals} {away}",
        "صافرة النهاية! {home} {home_goals} - {away_goals} {away}",
    ],
    MatchEventType.KICKOFF: [
        "بداية المباراة!",
        "انطلقنا! الحكم يعلن بداية المباراة.",
    ],
}


def generate(event_type: MatchEventType, lang: str = "en", **kwargs) -> str:
    """
    Generate a commentary line for a given event type.
    Accepts keyword args: player, club, detail, home, away, home_goals, away_goals.
    """
    if lang == "ar":
        templates = TEMPLATES_AR.get(event_type, ["{player} — حدث."])
    else:
        templates = TEMPLATES.get(event_type, ["{player} — event."])
    
    template = rng.choice(templates)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template

