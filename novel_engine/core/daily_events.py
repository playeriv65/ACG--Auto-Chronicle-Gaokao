from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from config import Config
from novel_engine.core.person import Person
from novel_engine.core.social_network import SocialNetwork


@dataclass
class DailyEventTemplate:
    scene: str
    template: str
    relation_delta: int
    mood_delta: int
    trust_delta: int = 0
    intimacy_delta: int = 0
    requires_relationship: Optional[str] = None
    min_intimacy: int = 0


class DailyEventGenerator:
    SCENE_CLASSROOM = "教室"
    SCENE_CANTEEN = "食堂"
    SCENE_PLAYGROUND = "操场"
    SCENE_DORMITORY = "宿舍"
    SCENE_OFFICE = "办公室"
    SCENE_CORRIDOR = "走廊"
    SCENE_LIBRARY = "图书馆"

    def __init__(self):
        self.templates = self._build_templates()

    def _build_templates(self) -> Dict[str, List[DailyEventTemplate]]:
        return {
            self.SCENE_CLASSROOM: self._classroom_events(),
            self.SCENE_CANTEEN: self._canteen_events(),
            self.SCENE_PLAYGROUND: self._playground_events(),
            self.SCENE_DORMITORY: self._dormitory_events(),
            self.SCENE_CORRIDOR: self._corridor_events(),
            self.SCENE_LIBRARY: self._library_events(),
        }

    def _classroom_events(self) -> List[DailyEventTemplate]:
        return [
            DailyEventTemplate(
                self.SCENE_CLASSROOM,
                "{p1} 趁老师转身板书，偷偷戳了戳 {p2} 的后背，小声问昨天的作业答案。",
                relation_delta=3,
                mood_delta=2,
                intimacy_delta=2,
            ),
            DailyEventTemplate(
                self.SCENE_CLASSROOM,
                "{p1} 在草稿纸上画了个搞笑小人，传给 {p2}，结果被 {p3} 截胡。",
                relation_delta=5,
                mood_delta=10,
                intimacy_delta=3,
            ),
            DailyEventTemplate(
                self.SCENE_CLASSROOM,
                "课间十分钟，{p1} 和 {p2} 为了最后一道数学题争得面红耳赤，{p3} 在旁边吃瓜看戏。",
                relation_delta=-2,
                mood_delta=-3,
                trust_delta=2,
            ),
            DailyEventTemplate(
                self.SCENE_CLASSROOM,
                "{p1} 今天值日擦黑板，粉笔灰弄得满身都是，{p2} 默默递过去一张纸巾。",
                relation_delta=8,
                mood_delta=5,
                intimacy_delta=5,
            ),
            DailyEventTemplate(
                self.SCENE_CLASSROOM,
                "早自习，{p1} 偷偷在课桌下看小说，被 {p2} 举报给了班主任。",
                relation_delta=-15,
                mood_delta=-10,
            ),
            DailyEventTemplate(
                self.SCENE_CLASSROOM,
                "{p1} 忘记带笔，{p2} 二话不说借了一支，结果是一支快没水的破笔。",
                relation_delta=-3,
                mood_delta=-2,
            ),
            DailyEventTemplate(
                self.SCENE_CLASSROOM,
                "数学课上，{p1} 被点名回答问题，{p2} 在旁边疯狂提示答案。",
                relation_delta=6,
                mood_delta=8,
                intimacy_delta=4,
            ),
            DailyEventTemplate(
                self.SCENE_CLASSROOM,
                "{p1} 的椅子一直在响，{p2} 忍无可忍，用胶带把椅子腿缠了一圈。",
                relation_delta=4,
                mood_delta=3,
            ),
        ]

    def _canteen_events(self) -> List[DailyEventTemplate]:
        return [
            DailyEventTemplate(
                self.SCENE_CANTEEN,
                "食堂排队，{p1} 帮 {p2} 打了饭，结果 {p2} 发现 {p1} 把自己不爱吃的青椒都挑了出来。",
                relation_delta=10,
                mood_delta=8,
                intimacy_delta=6,
            ),
            DailyEventTemplate(
                self.SCENE_CANTEEN,
                "{p1} 和 {p2} 为了最后一个鸡腿展开争夺，最终 {p3} 渔翁得利。",
                relation_delta=-5,
                mood_delta=-3,
            ),
            DailyEventTemplate(
                self.SCENE_CANTEEN,
                "吃饭时，{p1} 发现饭卡没钱了，{p2} 二话不说刷了自己的卡。",
                relation_delta=12,
                mood_delta=5,
                trust_delta=8,
            ),
            DailyEventTemplate(
                self.SCENE_CANTEEN,
                "{p1} 在食堂大声吐槽某个老师，结果老师就坐在后面那桌。{p2} 假装不认识。",
                relation_delta=-8,
                mood_delta=-15,
            ),
            DailyEventTemplate(
                self.SCENE_CANTEEN,
                "{p1} 今天胃口不好，把红烧肉都夹给了 {p2}，{p2} 感动得差点哭了。",
                relation_delta=7,
                mood_delta=6,
                intimacy_delta=4,
            ),
            DailyEventTemplate(
                self.SCENE_CANTEEN,
                "食堂阿姨手抖，{p1} 的菜只剩一半，{p2} 把自己的一份分了过去。",
                relation_delta=9,
                mood_delta=4,
            ),
            DailyEventTemplate(
                self.SCENE_CANTEEN,
                "{p1} 吃饭太快，噎住了，{p2} 赶紧递水，场面一度混乱。",
                relation_delta=5,
                mood_delta=-2,
            ),
        ]

    def _playground_events(self) -> List[DailyEventTemplate]:
        return [
            DailyEventTemplate(
                self.SCENE_PLAYGROUND,
                "体育课自由活动，{p1} 教 {p2} 投篮，{p2} 投了十个进了零个。",
                relation_delta=4,
                mood_delta=3,
                intimacy_delta=3,
            ),
            DailyEventTemplate(
                self.SCENE_PLAYGROUND,
                "跑步测试，{p1} 故意放慢速度等 {p2}，陪 ta 跑完全程。",
                relation_delta=10,
                mood_delta=5,
                intimacy_delta=7,
            ),
            DailyEventTemplate(
                self.SCENE_PLAYGROUND,
                "足球比赛，{p1} 临门一脚踢飞，{p2} 拍了拍 ta 的肩膀说'没事'。",
                relation_delta=6,
                mood_delta=-3,
            ),
            DailyEventTemplate(
                self.SCENE_PLAYGROUND,
                "傍晚操场散步，{p1} 和 {p2} 聊着聊着聊到了未来的梦想，气氛突然变得文艺。",
                relation_delta=8,
                mood_delta=10,
                intimacy_delta=10,
            ),
            DailyEventTemplate(
                self.SCENE_PLAYGROUND,
                "{p1} 在单杠上耍帅，结果手一滑摔了下来，{p2} 笑得直不起腰。",
                relation_delta=-5,
                mood_delta=8,
            ),
            DailyEventTemplate(
                self.SCENE_PLAYGROUND,
                "运动会报名，{p1} 被 {p2} 忽悠报了 3000 米，现在后悔得要死。",
                relation_delta=-3,
                mood_delta=-8,
            ),
        ]

    def _dormitory_events(self) -> List[DailyEventTemplate]:
        return [
            DailyEventTemplate(
                self.SCENE_DORMITORY,
                "熄灯后，{p1} 和 {p2} 躲在被子里打手电筒看小说，被宿管阿姨发现。",
                relation_delta=5,
                mood_delta=-10,
                intimacy_delta=5,
            ),
            DailyEventTemplate(
                self.SCENE_DORMITORY,
                "宿舍夜聊，{p1} 偷偷说自己有喜欢的人，{p2} 瞬间精神了。",
                relation_delta=8,
                mood_delta=5,
                intimacy_delta=12,
            ),
            DailyEventTemplate(
                self.SCENE_DORMITORY,
                "{p1} 的闹钟响了五遍都没醒，{p2} 无奈把 ta 摇醒。",
                relation_delta=-2,
                mood_delta=-3,
            ),
            DailyEventTemplate(
                self.SCENE_DORMITORY,
                "{p1} 偷偷带了零食回宿舍，被 {p2} 和 {p3} 当场抓获并瓜分。",
                relation_delta=6,
                mood_delta=8,
            ),
            DailyEventTemplate(
                self.SCENE_DORMITORY,
                "内务检查，{p1} 的被子叠成狗不理，{p2} 帮忙重新叠成豆腐块。",
                relation_delta=10,
                mood_delta=5,
            ),
            DailyEventTemplate(
                self.SCENE_DORMITORY,
                "{p1} 想家哭了，{p2} 和 {p3} 笨拙地安慰，场面一度温馨。",
                relation_delta=15,
                mood_delta=-5,
                intimacy_delta=15,
            ),
            DailyEventTemplate(
                self.SCENE_DORMITORY,
                "{p1} 打呼噜太响，{p2} 忍无可忍推醒 ta，结果 {p1} 翻个身继续打。",
                relation_delta=-8,
                mood_delta=-10,
            ),
        ]

    def _corridor_events(self) -> List[DailyEventTemplate]:
        return [
            DailyEventTemplate(
                self.SCENE_CORRIDOR,
                "走廊相遇，{p1} 假装没看见 {p2}，其实 ta 近视眼根本没戴眼镜。",
                relation_delta=-3,
                mood_delta=-2,
            ),
            DailyEventTemplate(
                self.SCENE_CORRIDOR,
                "{p1} 抱着一摞作业本差点摔倒，{p2} 眼疾手快扶了一把。",
                relation_delta=7,
                mood_delta=3,
            ),
            DailyEventTemplate(
                self.SCENE_CORRIDOR,
                "下课后走廊拥挤，{p1} 和 {p2} 被撞得撞在一起，额头对额头。",
                relation_delta=5,
                mood_delta=8,
                intimacy_delta=8,
            ),
        ]

    def _library_events(self) -> List[DailyEventTemplate]:
        return [
            DailyEventTemplate(
                self.SCENE_LIBRARY,
                "图书馆里，{p1} 和 {p2} 同时伸手去拿同一本书，手指碰到了一起。",
                relation_delta=8,
                mood_delta=10,
                intimacy_delta=10,
            ),
            DailyEventTemplate(
                self.SCENE_LIBRARY,
                "{p1} 在图书馆写作业，{p2} 悄悄在旁边放了一瓶水。",
                relation_delta=10,
                mood_delta=5,
                intimacy_delta=6,
            ),
            DailyEventTemplate(
                self.SCENE_LIBRARY,
                "{p1} 看书太入迷，闭馆了都没发现，被 {p2} 从书架后面揪出来。",
                relation_delta=4,
                mood_delta=3,
            ),
        ]

    def generate_event(
        self,
        participants: List[Person],
        social_network: SocialNetwork,
        preferred_scene: Optional[str] = None,
    ) -> Optional[Tuple[str, str]]:
        if len(participants) < 2:
            return None

        if preferred_scene and preferred_scene in self.templates:
            scene_templates = self.templates[preferred_scene]
        else:
            scene_templates = random.choice(list(self.templates.values()))

        if not scene_templates:
            return None

        template = random.choice(scene_templates)

        if template.requires_relationship:
            rel = social_network.get_relationship(
                participants[0].name, participants[1].name
            )
            if not rel or rel.relationship_type != template.requires_relationship:
                return None

        if template.min_intimacy > 0:
            rel = social_network.get_relationship(
                participants[0].name, participants[1].name
            )
            if not rel or rel.intimacy < template.min_intimacy:
                return None

        placeholders = {f"p{i + 1}": p.name for i, p in enumerate(participants[:4])}
        while len(placeholders) < 4:
            placeholders[f"p{len(placeholders) + 1}"] = participants[0].name

        event_text = template.template
        for key, value in placeholders.items():
            event_text = event_text.replace("{" + key + "}", value)

        return (
            f"【{template.scene}】{event_text}",
            template.scene,
        )

    def get_event_effects(self, template_index: int, scene: str) -> dict:
        if scene not in self.templates:
            return {}

        templates = self.templates[scene]
        if template_index < 0 or template_index >= len(templates):
            return {}

        template = templates[template_index]
        return {
            "relation_delta": template.relation_delta,
            "mood_delta": template.mood_delta,
            "trust_delta": template.trust_delta,
            "intimacy_delta": template.intimacy_delta,
        }
